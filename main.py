from py2neo import Graph, Node, Relationship, NodeMatcher
from xml.dom.minidom import parse
import xml.dom.minidom
import configparser

# XML文件读取
DOMTree = xml.dom.minidom.parse("Sample_BDD1.xml")
collection = DOMTree.documentElement
if collection.hasAttribute("xmi:version"):
    print(collection.getAttribute("xmi:version"))
# 获得UML与SysML之间的映射
U2Sdict = {}
children = collection.childNodes
for child in children:
    NodeName = child.nodeName
    if NodeName.count("Block") != 0 or NodeName.count("additional_stereotypes") != 0:
        for key in child.attributes.keys():
            if key.count("base") != 0:
                element_id = child.attributes[key].value
                name = child.localName
                U2Sdict[element_id] = name

# 参数中读取不需要读的信息
CONFIG_FILE = 'config.ini'
config = configparser.ConfigParser()
config.read(CONFIG_FILE)
# NoRead = config.get('NoRead', 'name').split()
forbidden = config.get('NoRead', 'forbidden')

# 得到包含数据的XML
Datas = collection.getElementsByTagName("uml:Model")
Data = ''
for tempData in Datas:
    if tempData.hasAttribute("name") and tempData.getAttribute("name") == "Data":
        Data = tempData
        break
packagedElements = Data.getElementsByTagName("packagedElement")
package = ''
for temp in packagedElements:
    if temp.hasAttribute("xmi:type") and temp.getAttribute("xmi:type") == "uml:Package" \
            and not temp.hasAttribute(forbidden):
        package = temp
        break
elements = package.getElementsByTagName("packagedElement")

# 创建所有节点
NodeList = []
NodeDict = {}
for element in elements:
    if element.getAttribute("xmi:type") == 'uml:Association':
        continue
    else:  # Class and DataType
        node = Node()
        element_id = ""
        for key in element.attributes.keys():
            if key == 'xmi:id':
                element_id = element.attributes[key].value
                node.add_label(U2Sdict[element_id])
                node["id"] = element.attributes[key].value
            # elif key == 'xmi:type':
            #     # node.add_label(element.attributes[key].value)
            #     continue
            else:
                node[key] = element.attributes[key].value
        # print(node)
        NodeList.append(node)
        NodeDict[element_id] = node

# 遍历所有节点在XML上的位置，创造节点间的关系节点
RelationList = []
for element in elements:
    if element.getAttribute("xmi:type") == 'uml:Association':
        continue
    else:  # Class and DataType
        father_id = element.getAttribute("xmi:id")
        relations = element.getElementsByTagName("ownedAttribute")
        for relation in relations:
            child_id = relation.getAttribute("type")
            rel = U2Sdict[relation.getAttribute("xmi:id")]
            node = Node()
            node.add_label(rel)
            for key in relation.attributes.keys():
                if key == "type" or key == "association":
                    continue
                elif key == "xmi:id":
                    node["id"] = relation.attributes[key].value
                else:
                    node[key] = relation.attributes[key].value
            NodeList.append(node)
            Neo4j_relation_father = Relationship(NodeDict[father_id], "own", node)
            RelationList.append(Neo4j_relation_father)
            Neo4j_relation_child = Relationship(node, "type", NodeDict[child_id])
            RelationList.append(Neo4j_relation_child)
# # 测试
# for node in NodeList:
#     print(node)
# for relation in RelationList:
#     print(relation)

# NEO4j 连接
graph = Graph('bolt://localhost:7687', auth=('neo4j', '12345678'))

# 创建节点
for node in NodeList:
    # print(node)
    graph.create(node)

# 创建关系
for relation in RelationList:
    # print(relation)
    graph.create(relation)

