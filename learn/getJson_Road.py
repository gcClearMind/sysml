import json
from py2neo import Graph
from collections import defaultdict
import configparser
import os
import re


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

        if not label and labels:
            label = labels[0]

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


def parse_swrl_rule(rule):
    """
    解析 SWRL 规则，返回节点和关系信息
    输入: uml:Operation(?individualC)
    输出: {'nodes': {...}, 'relations': [...]}
    """
    nodes = {}
    relations = []

    # 分割前件和后件
    rule_parts = rule.split("->")
    if len(rule_parts) != 2:
        print(f"无法解析规则（没有 -> ）: {rule}")
        return None

    preconditions = rule_parts[0].strip().split("^")

    # 改进正则：支持冒号、点、连字符等
    node_pattern = re.compile(r"([\w:\-\.]+)\(\?(\w+)\)")
    rel_pattern = re.compile(r"([\w:\-\.]+)\(\?(\w+), \?(\w+)\)")

    for condition in preconditions:
        condition = condition.strip()

        # 关系
        rel_match = rel_pattern.match(condition)
        if rel_match:
            rel_type, source, target = rel_match.groups()
            relations.append({
                'rel_type': rel_type,
                'source': source,
                'target': target
            })
            continue

        # 节点
        node_match = node_pattern.match(condition)
        if node_match:
            label, var = node_match.groups()
            nodes[var] = label
            continue

        print(f"无法识别的前件元素: {condition}")

    return {
        'nodes': nodes,
        'relations': relations
    }


def generalize_rule_and_check_with_counts(graph, swrl_rule):
    """
    把SWRL路径的头尾节点标签泛化，统计路径结构匹配的标签对，以及每个标签对的路径条数
    :param graph: Neo4j图对象
    :param swrl_rule: 一条SWRL规则字符串
    """
    print(f"\n分析规则: {swrl_rule}")

    # 解析SWRL规则（前件）
    parsed = parse_swrl_rule(swrl_rule)
    if not parsed:
        print("无法解析SWRL规则！")
        return

    relations = parsed['relations']

    if not relations:
        print("规则中没有关系结构！")
        return

    # 假设规则链只有一条主要的关系链
    # 可以扩展为多步路径（[*..n]），这里只处理单步或常规路径
    rel_conditions = []
    for rel in relations:
        rel_type = rel['rel_type']
        source = rel['source']
        target = rel['target']
        # 不加节点标签，泛化查询
        rel_conditions.append(f"({source})-[:`{rel_type}`]->({target})")

    match_clause = "MATCH " + ", ".join(rel_conditions)

    # 获取头尾节点（你规则里一般是A和B）
    var_names = list(parsed['nodes'].keys())
    if len(var_names) < 2:
        print("规则节点太少，无法分析")
        return

    start_var = var_names[0]
    end_var = var_names[-1]

    return_clause = (
        f"RETURN labels({start_var}) AS from_labels, "
        f"labels({end_var}) AS to_labels, "
        f"count(*) AS path_count "
        f"ORDER BY path_count DESC"
    )

    cypher_query = f"{match_clause} {return_clause}"

    print(f"执行查询: {cypher_query}")

    try:
        results = graph.run(cypher_query).data()

        if not results:
            print("⚠️ 没有任何符合这个结构的实体对")
        else:
            print("✅ 该路径结构匹配的实体标签对和路径数量：")
            for record in results:
                from_labels = record['from_labels']
                to_labels = record['to_labels']
                count = record['path_count']
                print(f"  {from_labels} --> {to_labels} : {count} 条路径")

    except Exception as e:
        print(f"执行查询时出错: {e}")


def main():
    # === 读取配置文件 ===
    config = configparser.ConfigParser()
    config.read('Initialization.properties')

    uri = config.get('neo4j', 'uri', fallback="bolt://localhost:7687")
    user = config.get('neo4j', 'user', fallback="neo4j")
    password = config.get('neo4j', 'password', fallback="12345678")

    # === 连接 Neo4j ===
    graph = Graph(uri, auth=(user, password))

    file_path = "data/path/output_pca.json"  # 改为 JSON 格式文件路径
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    start_label = "Requirement"
    end_label = "Block"
    path_len = 4

    relation_type = "relation"  # 规则后件的目标关系名称

    SWRL_list = set()
    swrl_map = defaultdict(list)

    query = (

        f"MATCH path = (n:{start_label})-[r*2..{path_len}]-(m:{end_label})"
        f" WHERE ALL(rel IN r WHERE NOT type(rel) IN ['packagedElement', 'packageImport', 'importedPackage']) "
        f" AND NONE(node IN nodes(path)[1..-1] WHERE node:Block OR node:Requirement)"
        f" RETURN path"

    )

    results = graph.run(query)

    id_counter = 0
    sum_paths = 0

    output_data = []  # 用于存储 JSON 格式的输出数据

    for record in results:
        path = record['path']
        swrl = getSWRL(path)
        sum_paths += 1

        if swrl in SWRL_list:
            swrl_map[swrl].append(path)
        else:
            SWRL_list.add(swrl)
            swrl_map[swrl].append(path)

    # 将数据转化为 JSON 格式
    for key, paths in swrl_map.items():
        id_counter += 1
        rule_data = {
            'id': id_counter,
            'rule': key,
            'count': len(paths),
            'paths': []  # 存储路径表示的列表
        }

        for path in paths:
            path_data = {
                'path_representation': show_path(path)
            }
            rule_data['paths'].append(path_data)

        output_data.append(rule_data)

    # 将数据写入 JSON 文件
    with open(file_path, 'w', encoding='utf-8') as writer:
        json.dump(output_data, writer, ensure_ascii=False, indent=4)

    print(f"写入完成，共处理路径数：{sum_paths}")
    for key in swrl_map.keys():
        generalize_rule_and_check_with_counts(graph, key)

if __name__ == "__main__":
    main()
