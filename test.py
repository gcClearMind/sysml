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


def get_node_label(node):
    # 获取节点主要标签（首选非 'uml:' 开头标签）
    labels = list(node.labels)
    non_uml_labels = [label for label in labels if not label.startswith('uml:')]

    if non_uml_labels:
        return non_uml_labels[0]
    elif labels:
        return labels[0]
    else:
        return "Unknown"


# 连接Neo4j数据库
graph = Graph("bolt://localhost:7687", auth=("neo4j", "12345678"))

# 查询所有节点及其关系
query = """
MATCH path = (n:Block)-[r*2..6]-(m:Requirement)
WHERE ALL(rel IN r WHERE NOT type(rel) IN ['packagedElement', 'packageImport', 'importedPackage', 'client', 'supplier'])
  AND NONE(node IN nodes(path)[1..-1] WHERE node:Block OR node:Requirement)
WITH nodes(path) AS ns, relationships(path) AS rs
UNWIND range(0, size(rs)-1) AS idx
RETURN ns[idx] AS fromNode, type(rs[idx]) AS relationship, ns[idx+1] AS toNode
"""

# 执行查询
results = graph.run(query)

# 三元组集合，自动去重
triples = set()
num = 0
# 处理查询结果
for record in results:
    from_node = record["fromNode"]
    to_node = record["toNode"]

    head = get_node_name(from_node)
    tail = get_node_name(to_node)
    relation = record["relationship"]

    head_label = get_node_label(from_node)
    tail_label = get_node_label(to_node)

    # 添加主三元组
    triples.add((head, relation, tail))

    # 添加 is 关系
    triples.add((head, 'is', head_label))
    triples.add((tail, 'is', tail_label))
    num += 2
# 写入文件
output_file = "triples_with_labels_dedup.txt"
with open(output_file, "w", encoding="utf-8") as file:
    for triple in triples:
        file.write(f"{triple[0]}\t{triple[1]}\t{triple[2]}\n")

print(f"去重后的三元组已成功导出至 {output_file} 文件。共导出 {len(triples)} 条三元组。 {num}")