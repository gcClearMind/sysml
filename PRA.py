from py2neo import Graph, Node, Relationship, NodeMatcher
import numpy as np
import networkx as nx

# 连接到Neo4j数据库
graph = Graph("bolt://localhost:7687", auth=("neo4j", "12345678"))

# 获取知识图谱中的节点和关系
def get_graph_from_neo4j():
    nodes = graph.run("MATCH (n) RETURN id(n) AS id, labels(n) AS labels, n AS node").data()
    relationships = graph.run("MATCH (n)-[r]->(m) RETURN id(n) AS source, type(r) AS rel_type, id(m) AS target").data()

    # 构建NetworkX图
    G = nx.DiGraph()
    for node in nodes:
        node_id = node["id"]
        labels = node["labels"][0]  # 取第一个标签
        G.add_node(node_id, labels=labels)

    for rel in relationships:
        source = rel["source"]
        target = rel["target"]
        rel_type = rel["rel_type"]
        G.add_edge(source, target, rel_type=rel_type)

    return G

# 计算RWR
def compute_rwr(graph, seed_node, restart_prob=0.15, max_iter=100, tol=1e-6):
    n = len(graph.nodes)
    adjacency_matrix = nx.adjacency_matrix(graph, weight=None).todense()
    teleport_matrix = np.zeros((n, n))
    teleport_matrix[seed_node] = 1.0

    rwr_vector = np.ones(n) / n
    for _ in range(max_iter):
        prev_rwr = rwr_vector.copy()
        rwr_vector = (1 - restart_prob) * adjacency_matrix.T.dot(rwr_vector) + restart_prob * teleport_matrix
        if np.linalg.norm(rwr_vector - prev_rwr) < tol:
            break

    return rwr_vector

# 计算PRA路径权重
def compute_pra(graph, seed_node, target_node, rwr_result):
    paths = list(nx.all_simple_paths(graph, seed_node, target_node))
    path_weights = []
    for path in paths:
        weight = sum(rwr_result[node] for node in path)
        path_weights.append((path, weight))

    # 按权重排序路径
    path_weights.sort(key=lambda x: x[1], reverse=True)
    return path_weights

# 主函数
def main():
    # 从Neo4j中获取图数据
    G = get_graph_from_neo4j()

    # 获取节点ID映射
    node_ids = list(G.nodes)
    seed_node = node_ids[0]  # 假设种子节点是第一个节点
    target_node = node_ids[1]  # 假设目标节点是第二个节点

    # 计算RWR
    rwr_result = compute_rwr(G, seed_node)

    # 输出RWR结果
    for node_id, score in zip(node_ids, rwr_result):
        print(f"Node {node_id}: {score}")

    # 计算PRA路径权重
    pra_result = compute_pra(G, seed_node, target_node, rwr_result)
    print("PRA路径权重：", pra_result)

if __name__ == "__main__":
    main()