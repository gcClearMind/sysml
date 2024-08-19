from rdflib import Graph, Literal, RDF, RDFS, Namespace, URIRef
from rdflib.namespace import OWL, DCTERMS, XSD

# 创建一个Graph
g = Graph()

# 定义命名空间
OSLC_NEO = Namespace("http://localhost:8080/neo4j/neo4j-vocab#")
g.bind("oslc_neo", OSLC_NEO)

# 定义本体
ontology = URIRef("http://localhost:8080/neo4j/neo4j-vocab#")
g.add((ontology, RDF.type, OWL.Ontology))
g.add((ontology, DCTERMS.title, Literal("The neo4j of sysml Vocabulary", datatype=XSD.string)))
g.add((ontology, RDFS.label, Literal("The neo4j of sysml Vocabulary", datatype=XSD.string)))
g.add((ontology, DCTERMS.description,
       Literal("All vocabulary URIs defined in the OSLC Neo4j namespace.", datatype=RDF.XMLLiteral)))
g.add((ontology, Namespace("http://purl.org/vocab/vann/").preferredNamespacePrefix,
       Literal("oslc_neo", datatype=XSD.string)))
g.add((ontology, DCTERMS.source, URIRef("http://localhost:8080/neo4j/neo4j-vocab#")))
g.add((ontology, DCTERMS.issued, Literal("2024-06-25", datatype=XSD.date)))

# 定义类
block_class = OSLC_NEO.Block
g.add((block_class, RDF.type, RDFS.Class))
g.add((block_class, RDFS.isDefinedBy, OSLC_NEO))
g.add((block_class, RDFS.label, Literal("SysML", datatype=XSD.string)))
g.add((block_class, RDFS.comment, Literal("The Neo4j of SysML resource.", datatype=XSD.string)))

# 定义属性
properties = {
    "id": "The identifier of a resource describing a node of neo4j.",
    "name": "The name of a resource describing a node of neo4j.",
    "XmiType": "The xmi:type of a resource describing a node of neo4j.",
    "XmiId": "The xmi:id of a resource describing a node of neo4j.",
    "visibility": "The visibility of a resource describing a node of neo4j."
}

for prop, comment in properties.items():
    prop_ref = OSLC_NEO[prop]
    g.add((prop_ref, RDF.type, RDF.Property))
    g.add((prop_ref, RDFS.isDefinedBy, OSLC_NEO))
    g.add((prop_ref, RDFS.label, Literal(prop, datatype=XSD.string)))
    g.add((prop_ref, RDFS.comment, Literal(comment, datatype=XSD.string)))

# 将Graph序列化为Turtle格式并保存到文件
g.serialize(destination="output.rdf", format="turtle")

print("RDF文件已生成并保存为output.rdf")
# -*- coding = utf-8 -*-
# @Time : 2024/8/19 13:00
# @Author : Clear Mind
# @File : 1.py.py
# @Software: PyCharm
