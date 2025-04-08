from py2neo import Graph


def get_node_name(node):
    # 尝试获取节点的 'name' 属性
    name = node.get('name')
    if name:
        return name + f'-node_{node.identity}'
    # 如果 'name' 属性不存在，检查标签
    labels = list(node.labels)
    non_uml_labels = [label for label in labels if not label.startswith('uml:')]
    if non_uml_labels:
        return non_uml_labels[0] + f'-node_{node.identity}'
    elif labels:
        return labels[0] + f'-node_{node.identity}'
    else:
        return "Unknown" + f'-node_{node.identity}'


# 连接Neo4j数据库
graph = Graph("bolt://localhost:7687", auth=("neo4j", "12345678"))

# 查询所有节点及其关系
query_all = """
MATCH (fromNode)-[r]->(toNode) 
WHERE not type(r)  IN ['packagedElement', 'packageImport', 'importedPackage', 'client','supplier']
RETURN fromNode, type(r) AS relationship, toNode
"""

# 执行查询
results = graph.run(query_all)
triples = set()
# 打开文件以写入三元组
for record in results:
    from_node = record["fromNode"]
    to_node = record["toNode"]
    head = get_node_name(from_node)
    tail = get_node_name(to_node)
    relation = record["relationship"]
    triples.add((head, relation, tail))

output_file = "triples_with_all.txt"
with open(output_file, "w", encoding="utf-8") as file:
    for triple in triples:
        file.write(f"{triple[0]}\t{triple[1]}\t{triple[2]}\n")
print(f"去重后的三元组已成功导出至 {output_file} 文件。共导出 {len(triples)} 条三元组。")

query_local = """
MATCH (fromNode)-[r:Satisfy]->(toNode) 
MATCH (n1)-[*2..4]-(n2)
WHERE n1 = fromNode OR n1 = toNode
WITH DISTINCT n2
RETURN collect(id(n2)) as nodes_id_list
"""

resultsd = graph.run(query_local)
triples = set()
nodes_ids = []
for record in resultsd:
    nodes_ids = record["nodes_id_list"]
print(nodes_ids)
query_tp2 = \
        f"""
            MATCH (n1)-[r]->(n2)
            WHERE id(n1) IN {nodes_ids} AND id(n2) IN {nodes_ids} AND (not type(r)  IN ['packagedElement', 
            'packageImport', 'importedPackage', 'client','supplier'])
             RETURN n1, type(r) AS relationship, n2
        """
result_node2 = graph.run(query_tp2)
for record3 in result_node2:
    triples.add((get_node_name(record3["n1"]), record3["relationship"], get_node_name(record3["n2"])))

output_file2 = "triples_with_local.txt"
with open(output_file2, "w", encoding="utf-8") as file:
    for triple in triples:
        file.write(f"{triple[0]}\t{triple[1]}\t{triple[2]}\n")
print(f"去重后的三元组已成功导出至 {output_file2} 文件。共导出 {len(triples)} 条三元组。")

