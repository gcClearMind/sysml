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
        return data


NoRead_NodeName = config.get('NoRead', 'NodeName').split()
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
            childNode["xmi:id"] = child_id
            isNode[child_id] = childNode
        if child.hasChildNodes():
            dfs_isNode(child)


def dfs_getAttribute(node, fatherNodeId = None):
    if node.nodeType == 3:
        return
    if node.hasAttribute("xmi:id") and 'href' not in node.attributes.keys():  # 原先是点
        if node.getAttribute("xmi:type") in NoRead_NodeType:  # 扩展和关系因为冗余性不读取
            return
        node_id = node.getAttribute("xmi:id")
        # 属性读取
        for key in node.attributes.keys():
            if key == "xmi:id":
                continue
            value = node.attributes[key].value
            if value in isNode.keys():  # 关联关系为另一个节点 建立关系
                relation = Relationship(isNode[node_id], key, isNode[value])
                RelationList.append(relation)
            else:
                isNode[node_id][key] = value
        # 和上一个节点建立关系
        if fatherNodeId is not None:
            pre_relation = Relationship(isNode[fatherNodeId], node.nodeName, isNode[node_id])
            RelationList.append(pre_relation)
        # 与儿子节点交互
        for child in node.childNodes:
            dfs_getAttribute(child, node_id)

    else:   # 处理不是点的属性和链接
        if node.nodeName in NoRead_NodeName or node.hasAttribute("href"):
            return
        if node.hasAttribute("xmi:idref") and node.getAttribute("xmi:idref") in isNode.keys():
            relation = Relationship(isNode[fatherNodeId], node.nodeName, isNode[node.getAttribute("xmi:idref")])
            RelationList.append(relation)
        else:
            for child in node.childNodes:
                if child.nodeType == 3:  # 文本类
                    if child.nodeValue.count("/n/t") != 0:
                        continue
                    # print(node.nodeName, child.nodeValue)
                    isNode[fatherNodeId][node.nodeName] = child.nodeValue


def test():
    for node in NodeList:
        print(node)
    for relation in RelationList:
        print(relation)


def createNode(graph):
    for key in isNode.keys():
        graph.create(isNode[key])
    for relation in RelationList:
        graph.create(relation)


def find(node):
    if node.nodeType == 3:
        return

    if node.getAttribute("xmi:id") == '_16_8_24400562_1516347342392_171582_11816':
        print(111)
        for child in node.childNodes:
            print(child)
    for child in node.childNodes:
        find(child)


# 清空图
def ClearGraph(graph):
    graph.run("MATCH(n) DETACH DELETE n")


def create_graph(FILE_NAME):
    Collection = read_file(FILE_NAME)
    get_map(Collection)
    Data = get_Data(Collection)

    Data_id = Data.getAttribute("xmi:id")
    root_node = Node()
    root_node["xmi:id"] = Data_id
    root_node.add_label(Data.nodeName)
    isNode[Data_id] = root_node

    dfs_isNode(Data)
    # find(Data)
    dfs_getAttribute(Data)

    # test()
    # # NEO4J链接
    # 本地
    # graph = Graph('bolt://localhost:7687', auth=('neo4j', '12345678'))
    # 服务器
    graph = Graph('bolt://1 21.40.183.82:7687', auth=('neo4j', '123456'))
    #
    ClearGraph(graph)
    createNode(graph)


if __name__ == "__main__":
    create_graph("雷达软件系统.xml")
