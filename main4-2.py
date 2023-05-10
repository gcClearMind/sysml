# -*- coding = utf-8 -*-
from py2neo import Graph, Node, Relationship, NodeMatcher
from xml.dom.minidom import parse
import xml.dom.minidom
import configparser
from Generalization import generalization

# 参数中读取不需要读的信息
CONFIG_FILE = 'config.ini'
config = configparser.ConfigParser()
config.read(CONFIG_FILE)
# NoRead = config.get('NoRead', 'name').split()


# 节点、关系列表
NodeList = []
RelationList = []
PackageList = []
NodeDict = {}
U2Sdict = {}
isNode = {}


# XML文件读取
def read_file(file_name):
    DOMTree = xml.dom.minidom.parse(file_name)
    collection = DOMTree.documentElement
    return collection


# 获得UML与SysML之间的映射
def get_map(collection):
    NoRead = config.get('NoRead', 'prefix').split()
    for child in collection.childNodes:
        if child.prefix not in NoRead and child.prefix is not None:
            for key in child.attributes.keys():
                if key.count("base") != 0:
                    element_id = child.attributes[key].value
                    name = child.nodeName
                    U2Sdict[element_id] = name


# 得到包含数据的Data
def get_Data(collection):
    Datas = collection.getElementsByTagName("uml:Model")
    for data in Datas:
        print(data.nodeValue)
        return data


NoRead_NodeType = config.get('NoRead', 'NodeType').split()


def dfs_isNode(node):
    for child in node.childNodes:
        if child.nodeType == 3:
            continue
        if child.hasAttribute("xmi:id") and 'href' not in child.attributes.keys():
            if node.getAttribute("xmi:type") in NoRead_NodeType:
                continue
            childNode = Node()
            child_id = child.getAttribute("xmi:id")
            if child_id in U2Sdict.keys():
                childNode.add_label(U2Sdict[child_id])
            else:
                childNode.add_label(child.getAttribute("xmi:type"))
            childNode["id"] = child_id
            isNode[child_id] = childNode
        if child.hasChildNodes():
            dfs_isNode(child)


def dfs_getAttribute(node, fatherNode=None):
    # if node.attributes is None and not node.hasChildNodes():
    #     print(node)  # todo
    if node.nodeType == 3:
        return
    if node.hasAttribute("xmi:id") and 'href' not in node.attributes.keys():  # 原先是点
        if node.getAttribute("xmi:type") in NoRead_NodeType:
            return
        node_id = node.getAttribute("xmi:id")
        for key in node.attributes.keys():
            if key == "xmi:id":
                continue
            value = node.attributes[key].value
            if value in isNode.keys():  # 关联关系为另一个节点 建立关系
                relation = Relationship(isNode[node_id], key, isNode[value])
                RelationList.append(relation)
            else:
                isNode[node_id][key] = value
        if fatherNode is not None:  # 和上一个节点建立关系
            pre_relation = Relationship(fatherNode, node.nodeName, isNode[node_id])
            RelationList.append(pre_relation)

        for child in node.childNodes:
            dfs_getAttribute(child, isNode[node_id])

    else:
        # if node.attributes is not None:
        #     print()  # todo
        print(node.nodeType)


def test():
    for node in NodeList:
        print(node)
    for relation in RelationList:
        print(relation)


def createNode(graph):
    for node in NodeList:
        graph.create(node)
    for relation in RelationList:
        graph.create(relation)


def find(Data):
    package = Data.getElementsByTagName("packagedElement")
    for e in package:
        if e.getAttribute("xmi:id") == '_16_8_24400562_1521192267753_412535_14212':
            generalization(e)


# 清空图
def ClearGraph(graph):
    graph.run("MATCH(n) DETACH DELETE n")


def create_graph(FILE_NAME):
    Collection = read_file(FILE_NAME)
    get_map(Collection)
    Data = get_Data(Collection)

    Data_id = Data.getAttribute("xmi:id")
    root_node = Node()
    root_node["id"] = Data_id
    root_node.add_label(Data.nodeName)
    isNode[Data_id] = root_node

    dfs_isNode(Data)
    dfs_getAttribute(Data)
    # createRelation()
    # test()
    # # NEO4J链接
    # 本地
    # graph = Graph('bolt://localhost:7687', auth=('neo4j', '12345678'))
    # 服务器
    # graph = Graph('bolt://121.40.183.82:7687', auth=('neo4j', '123456'))
    #
    # ClearGraph(graph)
    # createNode(graph)


if __name__ == "__main__":
    create_graph("MTSDesign_MobileRobot.xml")
