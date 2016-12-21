from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Date, Binary, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

DEFINITION_TABLE_NAME = 'pybel_definition'
NAME_TABLE_NAME = 'pybel_name'
DEFINITION_NAMESPACE = 'N'
DEFINITION_ANNOTATION = 'A'

FUNCTION_TABLE_NAME = 'pybel_function'
NODE_TABLE_NAME = 'pybel_node'
EDGE_TABLE_NAME = 'pybel_edge'
MODIFICATION_TABLE_NAME = 'pybel_modification'
PROPERTY_TABLE_NAME = 'pybel_property'
EDGE_PROPERTIES_TABLE_NAME = 'pybel_edge_properties'
EDGE_GRAPH_TABLE_NAME = 'pybel_edge_graphs'
EDGE_ANNOTATIONS_TABLE_NAME = 'pybel_edge_annotations'
NODE_MOD_TABLE_NAME = 'pybel_node_modifications'
GRAPH_TABLE_NAME = 'pybel_graphstore'
CITATION_TABLE_NAME = 'pybel_citation'
EVIDENCE_TABLE_NAME = 'pybel_evidence'

Base = declarative_base()


class Definition(Base):
    """This table represents the metadata for a BEL Namespace or annotation"""
    __tablename__ = DEFINITION_TABLE_NAME

    id = Column(Integer, primary_key=True)
    definitionType = Column(String(1))
    url = Column(String(255))
    author = Column(String(255))
    keyword = Column(String(50), index=True)
    createdDateTime = Column(DateTime)
    pubDate = Column(DateTime, nullable=True)
    copyright = Column(String(255))
    version = Column(String(50))
    contact = Column(String(255))
    names = relationship("Name", cascade='delete, delete-orphan')


class Name(Base):
    """This table represents the one-to-many relationship between a BEL Namespace/annotation, its values
    and their semantic annotations"""
    __tablename__ = NAME_TABLE_NAME

    id = Column(Integer, primary_key=True)
    definition_id = Column(Integer, ForeignKey('{}.id'.format(DEFINITION_TABLE_NAME)), index=True)
    name = Column(String(255))
    encoding = Column(String(50))

    definition = relationship("Definition", back_populates='names')


class AssociationNodeMod(Base):
    __tablename__ = NODE_MOD_TABLE_NAME

    id = Column(Integer, primary_key=True)
    node_id = Column(Integer, ForeignKey('{}.id'.format(NODE_TABLE_NAME)))
    modification_id = Column(Integer, ForeignKey('{}.id'.format(MODIFICATION_TABLE_NAME)))

    node = relationship("Node", back_populates="modifications")
    modification = relationship("Modification", back_populates="nodes")


class Modification(Base):
    __tablename__ = MODIFICATION_TABLE_NAME

    id = Column(Integer, primary_key=True)
    modType = Column(String(255))
    variantString = Column(String(255), nullable=True)
    pmodName_id = Column(ForeignKey('{}.id'.format(NAME_TABLE_NAME)), nullable=True)
    p3Name_id = Column(ForeignKey('{}.id'.format(NAME_TABLE_NAME)), nullable=True)
    p5Name_id = Column(ForeignKey('{}.id'.format(NAME_TABLE_NAME)), nullable=True)
    p3Range = Column(String(255), nullable=True)
    p5Range = Column(String(255), nullable=True)
    pmodName = Column(String(255), nullable=True)
    aminoA = Column(String(3), nullable=True)
    aminoB = Column(String(3), nullable=True)
    position = Column(Integer, nullable=True)

    nodes = relationship("AssociationNodeMod", back_populates="modification")

    pmodNameID = relationship("Name", foreign_keys=[pmodName_id])
    p3NameID = relationship("Name", foreign_keys=[p3Name_id])
    p5NameID = relationship("Name", foreign_keys=[p5Name_id])


class Node(Base):
    __tablename__ = NODE_TABLE_NAME

    id = Column(Integer, primary_key=True)
    function = Column(String(255))
    nodeIdentifier_id = Column(Integer, ForeignKey('{}.id'.format(NAME_TABLE_NAME)), nullable=True)
    nodeHashString = Column(String(255), index=True)
    sha256 = Column(String(255), index=True)
    nodeHashTuple = Column(Binary)

    modifications = relationship("AssociationNodeMod", back_populates="node")


class AssociationEdgeGraph(Base):
    __tablename__ = EDGE_GRAPH_TABLE_NAME

    id = Column(Integer, primary_key=True)
    edge_id = Column(Integer, ForeignKey('{}.id'.format(EDGE_TABLE_NAME)))
    graph_id = Column(Integer, ForeignKey('{}.id'.format(GRAPH_TABLE_NAME)))

    graph = relationship("Graphstore", back_populates="edges")
    edge = relationship("Edge", back_populates="graphs")


class AssociationEdgeAnnotation(Base):
    __tablename__ = EDGE_ANNOTATIONS_TABLE_NAME

    id = Column(Integer, primary_key=True)
    edge_id = Column(Integer, ForeignKey('{}.id'.format(EDGE_TABLE_NAME)))
    annotationName_id = Column(Integer, ForeignKey('{}.id'.format(NAME_TABLE_NAME)))  # nullable=True

    edge = relationship("Edge", back_populates="annotations")


class AssociationEdgeProperty(Base):
    __tablename__ = EDGE_PROPERTIES_TABLE_NAME

    id = Column(Integer, primary_key=True)
    edge_id = Column(Integer, ForeignKey('{}.id'.format(EDGE_TABLE_NAME)))
    attribute_id = Column(Integer, ForeignKey('{}.id'.format(PROPERTY_TABLE_NAME)))

    edge = relationship("Edge", back_populates='attributes')


class Edge(Base):
    __tablename__ = EDGE_TABLE_NAME

    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey('{}.id'.format(NODE_TABLE_NAME)))
    relation = Column(String(50))
    object_id = Column(Integer, ForeignKey('{}.id'.format(NODE_TABLE_NAME)))
    citation_id = Column(Integer, ForeignKey('{}.id'.format(CITATION_TABLE_NAME)), nullable=True)
    supportingText_id = Column(Integer, ForeignKey('{}.id'.format(EVIDENCE_TABLE_NAME)), nullable=True)

    sha256 = Column(String(255), index=True)

    subject = relationship("Node", foreign_keys=[subject_id])
    object = relationship("Node", foreign_keys=[object_id])
    annotations = relationship("AssociationEdgeAnnotation", back_populates="edge")
    attributes = relationship("AssociationEdgeProperty", back_populates="edge")
    graphs = relationship("AssociationEdgeGraph", back_populates="edge")


class Property(Base):
    __tablename__ = PROPERTY_TABLE_NAME

    id = Column(Integer, primary_key=True)
    participant = Column(String(255))
    modifier = Column(String(255))
    relativeKey = Column(String(255), nullable=True)
    propValue = Column(String(255), nullable=True)
    name_id = Column(Integer, ForeignKey('{}.id'.format(NAME_TABLE_NAME)), nullable=True)


class Citation(Base):
    __tablename__ = CITATION_TABLE_NAME

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    citationType = Column(String(100))
    reference = Column(String(100))
    comment = Column(Text, nullable=True)
    journal = Column(Text, nullable=True)
    volume = Column(String(255), nullable=True)
    issue = Column(String(255), nullable=True)
    pages = Column(String(255), nullable=True)
    pmcId = Column(String(255), nullable=True)
    firstauthor = Column(Text, nullable=True)
    authors = Column(Text, nullable=True)
    title = Column(Text, nullable=True)
    pubdate = Column(Date, nullable=True)
    lastauthor = Column(String(255), nullable=True, index=True)
    date = Column(Date, nullable=True)


class Evidence(Base):
    __tablename__ = EVIDENCE_TABLE_NAME

    id = Column(Integer, primary_key=True)
    citation_id = Column(Integer, ForeignKey('{}.id'.format(CITATION_TABLE_NAME)))
    supportingText = Column(Text)
    sha256 = Column(String(255), index=True)


class Graphstore(Base):
    __tablename__ = GRAPH_TABLE_NAME

    id = Column(Integer, primary_key=True)
    description = Column(Text, nullable=True)
    label = Column(String(25), index=True, unique=True)
    graph = Column(Binary)

    edges = relationship("AssociationEdgeGraph", back_populates="graph")
