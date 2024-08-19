from datetime import datetime

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
    res = graph.run(url)
    return res


def getRdf(m):
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
    g.add((ontology, DCTERMS.issued, Literal(datetime.now().date(), datatype=XSD.date)))
    for key in m.keys():
        properties = m.get(key)
        block_class = OSLC_NEO.Block
        g.add((block_class, RDF.type, RDFS.Class))
        g.add((block_class, RDFS.isDefinedBy, OSLC_NEO))
        g.add((block_class, RDFS.label, Literal("SysML", datatype=XSD.string)))
        g.add((block_class, RDFS.comment, Literal("The Neo4j of SysML resource.", datatype=XSD.string)))
        for property in properties:

def getVab():
    graph = Graph('bolt://localhost:11003', auth=('neo4j', '12345678'))
    name = "Blocks:Block"

    properties = getProperty(name, graph)
    m = {name: properties}
    g = getRdf(m)


if __name__ == "__main__":
    getVab()
