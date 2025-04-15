import os

from flask import Flask, jsonify, request
from flask_cors import CORS
from neo4j import GraphDatabase
from neo4j.graph import Node, Relationship, Path
from py2neo import Neo4jError, Graph

from backend.add import ClearGraph
from infer import run_inference  # 你可以自定义这个推理脚本
from main6 import create_graph
from flask import Flask, request, jsonify
from py2neo import Graph
from collections import defaultdict

app = Flask(__name__)
CORS(app)

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "12345678"))

@app.route('/labels', methods=['GET'])
def get_labels():
    with driver.session() as session:
        query = "CALL db.labels()"
        result = session.run(query)
        labels = [record["label"] for record in result]
        return jsonify({"labels": labels})

@app.route('/relations', methods=['GET'])
def get_relations():
    with driver.session() as session:
        query = "CALL db.relationshipTypes()"
        result = session.run(query)
        relations = [record["relationshipType"] for record in result]
        return jsonify({"relations": relations})

@app.route('/filter_nodes', methods=['POST'])
def filter_nodes():
    node_types = request.json.get('nodeTypes')
    query = """
    MATCH (n)
    WHERE ANY(label IN labels(n) WHERE label IN $types)
    OPTIONAL MATCH (n)-[r]-(m)
    RETURN n, r, m
    """
    result = run_neo4j_query(query, {"types": node_types})
    print(result)
    return jsonify(result)

@app.route('/filter_edges', methods=['POST'])
def filter_edges():
    edge_types = request.json.get('edgeTypes')
    query = """
    MATCH (a)-[r]->(b)
    WHERE type(r) IN $types
    RETURN a, r, b
    """
    result = run_neo4j_query(query, {"types": edge_types})
    return jsonify(result)



@app.route('/graph', methods=['GET'])
def get_graph():
    limit = int(request.args.get('limit', 100))
    query = """
        MATCH (n) limit $limit
        OPTIONAL MATCH (n)-[r]-(m)
        RETURN n, r, m
        """
    result = run_neo4j_query(query, {"limit": limit})
    print(result)
    return jsonify(result)


@app.route('/infer_path', methods=['POST'])
def infer_path():
    start_label = request.json.get('startLabel')
    end_label = request.json.get('endLabel')

    # 查询图谱中的路径
    query = f"""
        MATCH path = (n:{start_label})-[r*2..3]-(m:{end_label})
         WHERE ALL(rel IN r WHERE NOT type(rel) IN ['packagedElement', 'packageImport', 'importedPackage','client','supplier'])
         AND NONE(node IN nodes(path)[1..-1] WHERE node:{start_label} OR node:{end_label})
         RETURN path
    """
    results = graph.run(query)

    swrl_list = set()
    swrl_map = defaultdict(list)

    for record in results:
        path = record['path']
        swrl = getSWRL(path)  # 使用getSWRL函数生成规则
        if swrl in swrl_list:
            swrl_map[swrl].append(path)
        else:
            swrl_list.add(swrl)
            swrl_map[swrl].append(path)

    path_descriptions = []
    for key, paths in swrl_map.items():
        description = {
            'rule': key,
            'paths': [show_path(path) for path in paths]  # 使用show_path函数返回路径描述
        }
        path_descriptions.append(description)

    return jsonify({'pathDescriptions': path_descriptions})


# 获取路径推理规则（如果需要）
def getSWRL(path):
    nodes = path.nodes
    relationships = path.relationships

    res = []
    cur = None
    now = None
    start = None
    end = None

    for i, node in enumerate(nodes):
        node_props = dict(node)
        labels = list(node.labels)
        xmiType = node_props.get('xmi:type')

        now = f"individual{chr(ord('A') + i)}"

        label = None
        if len(labels) == 1:
            label = labels[0]
        else:
            for s in labels:
                if s != xmiType:
                    label = s
                    break

        if i == 0:
            start = now
            res.append(f"{label}(?{now})")
        else:
            rel = relationships[i - 1]
            rel_type = rel.__class__.__name__
            end_id = rel.end_node.identity

            if end_id == node.identity:
                res.append(f"{rel_type}(?{cur}, ?{now})")
            else:
                res.append(f"{rel_type}(?{now}, ?{cur})")

            res.append(f"{label}(?{now})")

            if i == len(nodes) - 1:
                end = now

        cur = now

    rule = " ^ ".join(res) + f" -> relation(?{start}, ?{end})"
    return rule

def show_path(path):
    path_repr = []
    for node in path.nodes:
        labels = list(node.labels)
        props = dict(node)
        node_name = props.get('name', 'Unnamed')
        node_str = f"[{'|'.join(labels)}] {node_name}"
        path_repr.append(node_str)

    return " -> ".join(path_repr)

def run_neo4j_query(cypher_query, params=None):
    if params is None:
        params = {}

    output = {"nodes": [], "links": []}

    try:
        with driver.session() as session:
            result = session.run(cypher_query, params)

            # 节点和关系处理缓存
            seen_nodes = {}
            links = []
            seen_rel_ids = set()

            for record in result:
                for value in record.values():
                    # 处理节点
                    if isinstance(value, Node):
                        node_id = value.id
                        if node_id not in seen_nodes:
                            seen_nodes[node_id] = {
                                "id": node_id,
                                "labels": list(value.labels),
                                "name": value.get("name", ""),
                                "properties": dict(value.items())  # ✅ 节点属性
                            }

                    # 处理关系
                    elif isinstance(value, Relationship):
                        rel_id = value.id
                        if rel_id not in seen_rel_ids:
                            seen_rel_ids.add(rel_id)

                            links.append({
                                "source": value.start_node.id,
                                "target": value.end_node.id,
                                "relation": value.type,
                                "properties": dict(value.items())  # ✅ 关系属性
                            })

                    # 处理路径
                    elif isinstance(value, Path):
                        # 处理路径中的节点
                        for node in value.nodes:
                            node_id = node.id
                            if node_id not in seen_nodes:
                                seen_nodes[node_id] = {
                                    "id": node_id,
                                    "labels": list(node.labels),
                                    "name": node.get("name", ""),
                                    "properties": dict(node.items())
                                }

                        # 处理路径中的关系
                        for rel in value.relationships:
                            rel_id = rel.id
                            if rel_id not in seen_rel_ids:
                                seen_rel_ids.add(rel_id)

                                links.append({
                                    "source": rel.start_node.id,
                                    "target": rel.end_node.id,
                                    "relation": rel.type,
                                    "properties": dict(rel.items())
                                })

                    # 其他类型处理（打印可选）
                    else:
                        print(f"未处理的类型: {value}")

            # ✅ 输出节点和链接
            output["nodes"] = list(seen_nodes.values())
            output["links"] = links

    except Neo4jError as e:
        app.logger.error(f"Neo4j query failed: {e}")
        output = {"error": str(e)}

    except Exception as e:
        app.logger.error(f"Unexpected error: {e}")
        output = {"error": str(e)}

    return output


@app.route('/graph_node', methods=['GET'])
def get_single_node():
    node_id = request.args.get('id')
    print(node_id)
    if not node_id:
        print("node id not provided")
        return jsonify({'nodes': [], 'links': []})

    query = """
            MATCH (n)
            WHERE last(split(elementId(n), ":")) = $node_id
            OPTIONAL MATCH (n)-[r]-(m)
            RETURN n, r, m
            """
    print("node id  provided")
    result = run_neo4j_query(query, {"node_id": node_id})
    print(result)
    return jsonify(result)


UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'xml'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

graph = Graph('bolt://localhost:7687', auth=('neo4j', '12345678'))


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'message': '没有检测到文件！'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': '没有选择文件！'}), 400
    if not file.filename.lower().endswith('.xml'):
        return jsonify({'message': '仅支持 XML 文件'}), 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    try:
        # ClearGraph(graph)
        create_graph(filepath, graph)
        return jsonify({'message': '模型导入成功！'})
    except Exception as e:
        return jsonify({'message': f'导入失败：{str(e)}'}), 500



if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=11003)
