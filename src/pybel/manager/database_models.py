from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Date, Table, Binary, Text, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

DEFINITION_TABLE_NAME = 'pybel_cache_definition'
CONTEXT_TABLE_NAME = 'pybel_cache_context'
DEFINITION_NAMESPACE = 'N'
DEFINITION_ANNOTATION = 'A'

FUNCTION_TABLE_NAME = 'pybel_function'
TERM_TABLE_NAME = 'pybel_term'
STATEMENT_TABLE_NAME = 'pybel_statement'
MODIFICATION_TABLE_NAME = 'pybel_modification'
EDGEPROPERTY_TABLE_NAME = 'pybel_property'
STATEMENT_PROPERTIES_TABLE_NAME = 'pybel_statement_properties'
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
    contexts = relationship("Context", cascade='delete, delete-orphan')


class Context(Base):
    """This table represents the one-to-many relationship between a BEL Namespace/annotation, its values, and their semantic annotations"""
    __tablename__ = CONTEXT_TABLE_NAME

    id = Column(Integer, primary_key=True)
    definition_id = Column(Integer, ForeignKey('{}.id'.format(DEFINITION_TABLE_NAME)), index=True)
    context = Column(String(255))
    encoding = Column(String(50))


class BELFunction(Base):
    __tablename__ = FUNCTION_TABLE_NAME

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)


class BELModification(Base):
    __tablename__ = MODIFICATION_TABLE_NAME

    id = Column(Integer, primary_key=True)
    modType = Column(String(255))


class BELTerm(Base):
    __tablename__ = TERM_TABLE_NAME

    # ToDO: Unique für function+nsContext_id
    graphKey = Column(String(255), index=True, primary_key=True)
    function = Column(String(255))
    nsContext_id = Column(Integer, ForeignKey('{}.id'.format(CONTEXT_TABLE_NAME)), nullable=True)

    __table_args__ = (UniqueConstraint('function', 'nsContext_id', name='_function_context_uc'),)
    # ToDo: Add Modification key
    #modification_id = Column(Integer, ForeignKey('{}.id'.format(MODIFICATION_TABLE_NAME)))


class BELStatementPropertyAssociation(Base):
    __tablename__ = STATEMENT_PROPERTIES_TABLE_NAME

    id = Column(Integer, primary_key=True)
    statement_id = Column(Integer, ForeignKey('{}.id'.format(STATEMENT_TABLE_NAME)))
    property_id = Column(Integer, ForeignKey('{}.id'.format(EDGEPROPERTY_TABLE_NAME)))

    property = relationship("BELEdgeProperty", back_populates="statements")
    statement = relationship("BELStatement", back_populates="properties")


class BELStatement(Base):
    __tablename__ = STATEMENT_TABLE_NAME

    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey('{}.graphKey'.format(TERM_TABLE_NAME)))
    relation = Column(String(50))
    object_id = Column(Integer, ForeignKey('{}.graphKey'.format(TERM_TABLE_NAME)))
    citation_id = Column(Integer, ForeignKey('{}.id'.format(CITATION_TABLE_NAME)), nullable=True)
    subject = relationship("BELTerm", foreign_keys=[subject_id])
    object = relationship("BELTerm", foreign_keys=[object_id])
    properties = relationship("BELStatementPropertyAssociation", back_populates="statement")
    #properties = relationship("BELEdgeProperty",
    #                          secondary=association_table,
    #                          backref="statements")


class BELEdgeProperty(Base):
    __tablename__ = EDGEPROPERTY_TABLE_NAME

    id = Column(Integer, primary_key=True)
    propKey = Column(String(255), nullable=True)
    relativeKey = Column(String(255), nullable=True)
    propValue = Column(String(255))
    statements = relationship("BELStatementPropertyAssociation", back_populates="property")


class BELCitation(Base):
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
