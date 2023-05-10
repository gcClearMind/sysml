from py2neo import Graph, Node, Relationship, NodeMatcher
from xml.dom.minidom import parse
import xml.dom.minidom
import configparser


# 清空图
def ClearGraph(graph):
    graph.run("MATCH(n) DETACH DELETE n")


node1 = Node()
node1.add_label("x1")
node2 = Node()
node2.add_label("X2")

relation = Relationship(node1, "re", node2)

node1["sss"] = "112312as"

graph = Graph('bolt://localhost:7687', auth=('neo4j', '12345678'))

ClearGraph(graph)

graph.create(node1)
graph.create(node2)
graph.create(relation)