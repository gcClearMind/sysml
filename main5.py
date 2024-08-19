# -*- coding = utf-8 -*-
from py2neo import Graph, Node, Relationship
from xml.dom.minidom import parse
import xml.dom.minidom
import configparser

# 参数中读取不需要读的信息
CONFIG_FILE = 'config.ini'
config = configparser.ConfigParser()
config.read(CONFIG_FILE)

# 节点、关系列表
NodeList = []
RelationList = []
NodeDict = {}
U2Sdict = {}
isNode = {}


# XML文件读取
def read_file(file_name):
    DOMTree = xml.dom.minidom.parse(file_name)
    collection = DOMTree.documentElement
    return collection


NoRead_prefix = config.get('NoRead', 'prefix').split()
NoRead_NodeName = config.get('NoRead', 'NodeName').split()
NoRead_NodeType = config.get('NoRead', 'NodeType').split()


# 获得UML与SysML之间的映射
def get_map(collection):
    for child in collection.childNodes:
        if child.prefix not in NoRead_prefix and child.prefix is not None:
            for key in child.attributes.keys():
                if key.count("base") != 0:
                    element_id = child.attributes[key].value
                    name = child.nodeName
                    # 一个实体可能包含多个标签
                    if element_id not in U2Sdict.keys():
                        label_list = [name]
                        U2Sdict[element_id] = label_list
                    else:
                        U2Sdict[element_id].append(name)


def get_map_relation(collection):
    for child in collection.childNodes:
        if child.prefix not in NoRead_prefix and child.prefix is not None:
            node_id = ''
            for key in child.attributes.keys():
                if key.count("base") != 0:
                    node_id = child.attributes[key].value
                    break
            for key in child.attributes.keys():
                if key == 'xmi:id' or key.count("base") != 0 or node_id not in isNode.keys():
                    continue
                else:
                    value = child.attributes[key].value
                    if value in isNode.keys():  # 关联关系为另一个节点 建立关系
                        relation = Relationship(isNode[node_id], key, isNode[value])
                        RelationList.append(relation)
                    else:
                        isNode[node_id][key] = value

            for this_child in child.childNodes:
                if this_child.nodeType == 3:  # 文本类
                    continue
                elif node_id not in isNode.keys():
                    continue
                else:
                    for v in this_child.childNodes:
                        if v.nodeValue.count("/n/t") != 0:
                            continue
                        else:
                            isNode[node_id][v.nodeName] = v.nodeValue


# 得到包含数据的Data
def get_Data(collection):
    Datas = collection.getElementsByTagName("uml:Model")
    for data in Datas:
        return data


# 获取节点
def dfs_isNode(node):
    for child in node.childNodes:
        # 去除间隔
        if child.nodeType == 3:
            continue
        if child.hasAttribute("xmi:id") and 'href' not in child.attributes.keys():
            if child.getAttribute("xmi:type") in NoRead_NodeType or child.nodeName in NoRead_NodeName:
                continue
            childNode = Node()
            child_id = child.getAttribute("xmi:id")
            # todo chuli
            # 将uml类也录入其中
            childNode.add_label(child.getAttribute("xmi:type"))
            # 录入使用到的sysml类
            if child_id in U2Sdict.keys():
                for label in U2Sdict[child_id]:
                    childNode.add_label(label)
            # else:
            #     childNode.add_label(child.getAttribute("xmi:type"))
            childNode["xmi:id"] = child_id
            isNode[child_id] = childNode
        # 有子节点
        if child.hasChildNodes():
            if child.getAttribute("xmi:type") in NoRead_NodeType or child.nodeName in NoRead_NodeName:
                continue
            dfs_isNode(child)


# 获取节点间的关系
def dfs_getAttribute(node, fatherNodeId=None):
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

    else:  # 处理不是点的属性和链接
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


# 测试用
def test():
    for node in NodeList:
        print(node)
    for relation in RelationList:
        print(relation)


# 创建节点
def createNode(graph):
    for key in isNode.keys():
        graph.create(isNode[key])
    for relation in RelationList:
        graph.create(relation)


# 清空图
def ClearGraph(graph):
    graph.run("MATCH(n) DETACH DELETE n")


# 初始化
def init():
    NodeList.clear()
    RelationList.clear()
    NodeDict.clear()
    U2Sdict.clear()
    isNode.clear()


def create_graph(FILE_NAME, graph):
    init()
    Collection = read_file(FILE_NAME)
    get_map(Collection)
    Data = get_Data(Collection)
    # 放入根节点
    Data_id = Data.getAttribute("xmi:id")
    root_node = Node()
    root_node["xmi:id"] = Data_id
    root_node.add_label(Data.nodeName)
    isNode[Data_id] = root_node

    dfs_isNode(Data)
    # find(Data)
    dfs_getAttribute(Data)
    get_map_relation(Collection)
    # test()

    # 输入图谱
    createNode(graph)


def creat_all():    
    #  NEO4J链接
    # 本地
    graph = Graph('bolt://localhost:7687', auth=('neo4j', '12345678'))
    # 服务器
    # graph = Graph('bolt://120.26.15.210:7687', auth=('neo4j', '123456'))
    #
    ClearGraph(graph)
    # create_graph("雷达软件系统.xml", graph)
    # create_graph("MTSDesign_MobileRobot.xml", graph)
    create_graph("hybrid sport utility vehicle.xml", graph)
    # create_graph("InvertedPendulum.xml", graph)
    # create_graph("Sample_BDD1.xml", graph)


if __name__ == "__main__":
    creat_all()
