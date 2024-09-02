from datetime import datetime

import py2neo
import rdflib
from py2neo import Graph, Node, Relationship
from xml.dom.minidom import parse
import xml.dom.minidom
import configparser
from rdflib import Graph, Literal, RDF, RDFS, Namespace, URIRef
from rdflib.namespace import OWL, DCTERMS, XSD


def getProperty(name, graph):
    url = "match (n:`" + name + "`)" \
                                " with keys(n) as k unwind k as ks " \
                                "with distinct ks as kt with collect(kt) as list  " \
                                "return list"
    result = graph.run(url).data()
    if result:
        return result[0]["list"]
    else:
        return []  # 或者处理空结果的情况

def changeProperty(property):
    spd = ':'
    if spd not in property:
        return property
    i = 0
    result = ''
    while i < len(property):
        if property[i] == spd:
            i += 1
            if i < len(property):
                result += property[i].upper()
                i += 1
        else:
            result += property[i]
            i += 1
    return result


def getRdf(m):
    # 创建一个Graph
    g = rdflib.Graph()

    # 定义命名空间
    OSLC_NEO = Namespace("http://localhost:8080/neo4j/neo4j-vocab#")
    g.bind("oslc_neo", OSLC_NEO)

    # 定义本体
    ontology_uri = URIRef("http://localhost:8080/neo4j/neo4j-vocab#")
    ontology = ontology_uri
    g.add((ontology, RDF.type, OWL.Ontology))
    g.add((ontology, DCTERMS.title, Literal("The neo4j of sysml Vocabulary")))
    g.add((ontology, RDFS.label, Literal("The neo4j of sysml Vocabulary")))
    g.add((ontology, DCTERMS.description,
           Literal("All vocabulary URIs defined in the OSLC Neo4j namespace.", datatype=RDF.XMLLiteral)))
    g.add((ontology, Namespace("http://purl.org/vocab/vann/").preferredNamespacePrefix,
           Literal("oslc_neo")))
    g.add((ontology, DCTERMS.source, ontology_uri))
    g.add((ontology, DCTERMS.issued, Literal(datetime.now().date(), datatype=URIRef(XSD.date))))
    for key in m.keys():
        properties = m.get(key)

        block_class = OSLC_NEO["Block"]
        g.add((block_class, RDF.type, RDFS.Class))
        g.add((block_class, RDFS.isDefinedBy, ontology_uri))
        g.add((block_class, RDFS.label, Literal("SysML")))
        g.add((block_class, RDFS.comment, Literal("The Neo4j of SysML resource.")))
        i = 0
        for property in properties:
            NewProperty = changeProperty(property)
            propertyOntology = OSLC_NEO[NewProperty]
            g.add((propertyOntology, RDF.type, RDF.Property))
            g.add((propertyOntology, RDFS.isDefinedBy, ontology_uri))
            g.add((propertyOntology, RDFS.label, Literal(property)))
            comment = "The " + property + " of a resource describing a node of neo4j."
            g.add((propertyOntology, RDFS.comment, Literal(comment)))
    return g


def getVab():
    graph = py2neo.Graph('bolt://localhost:7687', auth=('neo4j', '12345678'))
    name = "Blocks:Block"

    properties = getProperty(name, graph)
    m = {name: properties}
    # print(m)
    g = getRdf(m)
    print(g.serialize(format='turtle'))


if __name__ == "__main__":
    getVab()
