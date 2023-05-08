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


# XML文件读取
def read_file(file_name):
    DOMTree = xml.dom.minidom.parse(file_name)
    collection = DOMTree.documentElement
    return collection


# 获得UML与SysML之间的映射
def get_map(collection):
    NoRead = config.get('NoRead-prefix', 'name').split()
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


# 创建目录结构
def get_package(root_package, fatherNode=None):
    node = Node()
    if fatherNode is None:
        node.add_label(root_package.nodeName)
    else:
        node.add_label('Package')
    for key in root_package.attributes.keys():
        if key == "xmi:id":
            node["id"] = root_package.attributes[key].value
        else:
            node[key] = root_package.attributes[key].value
    NodeList.append(node)
    if fatherNode is not None:
        Relation = Relationship(fatherNode, 'contain', node)
        RelationList.append(Relation)

    for child in root_package.childNodes:
        # 递归遍历树得到子节点
        if child.nodeName == 'packagedElement' and 'href' not in child.attributes.keys():
            if child.getAttribute("xmi:type") == 'uml:Package':
                PackageList.append(child)
                get_package(child, node)
            # 关系与节点处理
            elif child.getAttribute("xmi:type") == 'uml:Association' or 'uml:Profile':
                continue
            # 创造叶子节点
            else:
                childNode = Node()
                child_id = ""
                for key in child.attributes.keys():
                    if key == 'xmi:id':
                        child_id = child.attributes[key].value
                        if child_id in U2Sdict.keys():
                            childNode.add_label(U2Sdict[child_id])
                        else:
                            childNode.add_label(child.getAttribute("xmi:type"))
                        childNode["id"] = child.attributes[key].value
                    else:
                        childNode[key] = child.attributes[key].value
                NodeList.append(childNode)
                NodeDict[child_id] = childNode
                packageRelation = Relationship(node, 'contain', childNode)
                RelationList.append(packageRelation)


def get_profile(root_profile, fatherNode=None):
    node = Node()
    if fatherNode is None:
        node.add_label(root_profile.nodeName)
    else:
        node.add_label('Profile')
    for key in root_profile.attributes.keys():
        if key == "xmi:id":
            node["id"] = root_profile.attributes[key].value
        else:
            node[key] = root_profile.attributes[key].value
    NodeList.append(node)
    if fatherNode is not None:
        Relation = Relationship(fatherNode, 'contain', node)
        RelationList.append(Relation)
    for child in root_profile.childNodes:
        # 递归遍历树得到子节点
        if child.nodeName == 'packagedElement' and 'href' not in child.attributes.keys():
            if child.getAttribute("xmi:type") == 'uml:Profile':
                PackageList.append(child)
                get_package(child, node)
            # 关系与节点处理
            elif child.getAttribute("xmi:type") == 'uml:Extension' or 'uml:Package':
                continue
            # 创造叶子节点
            else:
                childNode = Node()
                child_id = ""
                for key in child.attributes.keys():
                    if key == 'xmi:id':
                        child_id = child.attributes[key].value
                        if child_id in U2Sdict.keys():
                            childNode.add_label(U2Sdict[child_id])
                        else:
                            childNode.add_label(child.getAttribute("xmi:type"))
                        childNode["id"] = child.attributes[key].value
                    else:
                        childNode[key] = child.attributes[key].value
                NodeList.append(childNode)
                NodeDict[child_id] = childNode
                packageRelation = Relationship(node, 'contain', childNode)
                RelationList.append(packageRelation)


# 创建点与点的关系
def createRelation():
    for package in PackageList:
        for element in package.childNodes:
            if element.nodeName != 'packagedElement':
                continue
            if element.getAttribute("xmi:type") == ('uml:Association' or 'uml:Package'):
                continue
            else:
                father_id = element.getAttribute("xmi:id")
                for child in element.childNodes:
                    if child.nodeName != ('ownedAttribute' or 'ownedBehavior'):
                        continue
                    # 可以映射为sysml的节点
                    # todo 有一种关系为role
                    if child.getAttribute("type") in U2Sdict.keys():
                        child_id = child.getAttribute("type")

                        if child.getAttribute("xmi:id") in U2Sdict.keys():
                            rel = U2Sdict[child.getAttribute("xmi:id")]
                        else:
                            rel = child.getAttribute("xmi:type")
                        node = Node()
                        node.add_label(rel)
                        for key in child.attributes.keys():
                            if key == "type" or key == "association":
                                continue
                            elif key == "xmi:id":
                                node["id"] = child.attributes[key].value
                            else:
                                node[key] = child.attributes[key].value
                        NodeList.append(node)
                        Neo4j_relation_father = Relationship(NodeDict[father_id], "own", node)
                        RelationList.append(Neo4j_relation_father)
                        Neo4j_relation_child = Relationship(node, "type", NodeDict[child_id])
                        RelationList.append(Neo4j_relation_child)
                    # 不可以映射为sysml的节点
                    else:
                        child_id = child.getAttribute("xmi:id")
                        node = Node()
                        if child_id in U2Sdict.keys():
                            rel = U2Sdict[child_id]
                        else:
                            rel = child.getAttribute("xmi:type")
                        node.add_label(rel)
                        for key in child.attributes.keys():
                            if key == 'xmi:id':
                                node["id"] = child.attributes[key].value
                            else:
                                node[key] = child.attributes[key].value
                        NodeList.append(node)
                        NodeDict[child_id] = node
                        # todo rel 可能有更优解
                        Neo4j_relation = Relationship(NodeDict[father_id], rel, node)
                        RelationList.append(Neo4j_relation)


# 测试
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
    # find(Data)
    get_package(Data)
    get_profile(Data)
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
