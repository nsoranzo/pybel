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
GRAPH_TABLE_NAME = 'pybel_graphstore'
CITATION_TABLE_NAME = 'pybel_citation'

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
    """This table represents the one-to-many relationship between a BEL Namespace/annotation, its values, and their semantic annotations"""
    __tablename__ = NAME_TABLE_NAME

    id = Column(Integer, primary_key=True)
    definition_id = Column(Integer, ForeignKey('{}.id'.format(DEFINITION_TABLE_NAME)), index=True)
    name = Column(String(255))
    encoding = Column(String(50))

    definition = relationship("Definition", back_populates='names')


class Modification(Base):
    __tablename__ = MODIFICATION_TABLE_NAME

    id = Column(Integer, primary_key=True)
    modType = Column(String(255))


class Node(Base):
    __tablename__ = NODE_TABLE_NAME

    id = Column(Integer, primary_key=True)
    function = Column(String(255))
    nodeIdentifier_id = Column(Integer, ForeignKey('{}.id'.format(NAME_TABLE_NAME)), nullable=True)
    # modification_id = Column(Integer, ForeignKey('{}.id'.format(MODIFICATION_TABLE_NAME)))
    nodeHash = Column(String(255), index=True)

    # __table_args__ = (UniqueConstraint('function', 'nodeIdentifier_id', name='_function_name_uc'),)
    # ToDo: Add Modification key
    #modification_id = Column(Integer, ForeignKey('{}.id'.format(MODIFICATION_TABLE_NAME)))


class AssociationEdgeProperty(Base):
    __tablename__ = EDGE_PROPERTIES_TABLE_NAME

    id = Column(Integer, primary_key=True)
    edge_id = Column(Integer, ForeignKey('{}.id'.format(EDGE_TABLE_NAME)))
    property_id = Column(Integer, ForeignKey('{}.id'.format(PROPERTY_TABLE_NAME)))

    property = relationship("Property", back_populates="statements")
    edge = relationship("Edge", back_populates="properties")


class Edge(Base):
    __tablename__ = EDGE_TABLE_NAME

    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey('{}.id'.format(NODE_TABLE_NAME)))
    relation = Column(String(50))
    object_id = Column(Integer, ForeignKey('{}.id'.format(NODE_TABLE_NAME)))
    citation_id = Column(Integer, ForeignKey('{}.id'.format(CITATION_TABLE_NAME)), nullable=True)
    supportingText = Column(Text, nullable=True)

    subject = relationship("Node", foreign_keys=[subject_id])
    object = relationship("Node", foreign_keys=[object_id])
    properties = relationship("AssociationEdgeProperty", back_populates="edge")
    #properties = relationship("Property",
    #                          secondary=association_table,
    #                          backref="statements")


class Property(Base):
    __tablename__ = PROPERTY_TABLE_NAME

    id = Column(Integer, primary_key=True)
    propKey = Column(String(255), nullable=True)
    relativeKey = Column(String(255), nullable=True)
    propValue = Column(String(255))
    statements = relationship("AssociationEdgeProperty", back_populates="property")


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


class PyBELGraphStore(Base):
    __tablename__ = GRAPH_TABLE_NAME

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=True)
    label = Column(String(25))
    graph = Column(Binary)
