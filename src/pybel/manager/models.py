import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Sequence, Text, Table, Date, Binary, \
    UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

DEFINITION_TABLE_NAME = 'pybel_cache_definitions'
DEFINITION_ENTRY_TABLE_NAME = 'pybel_cache_entries'
DEFINITION_NAMESPACE = 'N'
DEFINITION_ANNOTATION = 'A'

NAMESPACE_TABLE_NAME = 'pybel_namespaces'
NAMESPACE_ENTRY_TABLE_NAME = 'pybel_namespaceEntries'
ANNOTATION_TABLE_NAME = 'pybel_annotations'
ANNOTATION_ENTRY_TABLE_NAME = 'pybel_annotationEntries'

NETWORK_TABLE_NAME = 'pybel_network'

OWL_TABLE_NAME = 'Owl'
OWL_ENTRY_TABLE_NAME = 'OwlEntry'

CITATION_TABLE_NAME = 'pybel_citation'
EVIDENCE_TABLE_NAME = 'pybel_evidence'
EDGE_PROPERTY_TABLE_NAME = 'pybel_edgeProperty'
NODE_TABLE_NAME = 'pybel_node'
MODIFICATION_TABLE_NAME = 'pybel_modification'
EDGE_TABLE_NAME = 'pybel_edge'

Base = declarative_base()

NAMESPACE_DOMAIN_TYPES = {"BiologicalProcess", "Chemical", "Gene and Gene Products", "Other"}
"""See: https://wiki.openbel.org/display/BELNA/Custom+Namespaces"""

CITATION_TYPES = {"Book", "PubMed", "Journal", "Online Resource", "Other"}
"""See: https://wiki.openbel.org/display/BELNA/Citation"""


class Namespace(Base):
    __tablename__ = NAMESPACE_TABLE_NAME
    id = Column(Integer, primary_key=True)

    url = Column(String(255))
    keyword = Column(String(8), index=True)
    name = Column(String(255))
    domain = Column(String(255))
    # domain = Column(Enum(*NAMESPACE_DOMAIN_TYPES, name='namespaceDomain_types'))
    species = Column(String(255), nullable=True)
    description = Column(String(255), nullable=True)
    version = Column(String(255), nullable=True)
    created = Column(DateTime)
    query_url = Column(Text, nullable=True)

    author = Column(String(255))
    license = Column(String(255), nullable=True)
    contact = Column(String(255), nullable=True)

    citation = Column(String(255))
    citation_description = Column(String(255), nullable=True)
    citation_version = Column(String(255), nullable=True)
    citation_published = Column(Date, nullable=True)
    citation_url = Column(String(255), nullable=True)

    entries = relationship('NamespaceEntry', back_populates="namespace")

    def __repr__(self):
        return 'Namespace({})'.format(self.keyword)


class NamespaceEntry(Base):
    __tablename__ = NAMESPACE_ENTRY_TABLE_NAME
    id = Column(Integer, primary_key=True)

    name = Column(String(255), nullable=False)
    encoding = Column(String(8), nullable=True)

    namespace_id = Column(Integer, ForeignKey(NAMESPACE_TABLE_NAME + '.id'), index=True)
    namespace = relationship('Namespace', back_populates='entries')

    def __repr__(self):
        return 'NamespaceEntry({}, {})'.format(self.name, self.encoding)


edge_annotations_relationship = Table(
    'pybel_edge_annotations', Base.metadata,
    Column('edge_id', Integer, ForeignKey(EDGE_TABLE_NAME + '.id')),
    Column('annotation_id', Integer, ForeignKey(ANNOTATION_ENTRY_TABLE_NAME + '.id'))
)


class Annotation(Base):
    """This table represents the metadata for a BEL Namespace or annotation"""
    __tablename__ = ANNOTATION_TABLE_NAME

    id = Column(Integer, primary_key=True)

    url = Column(String(255))
    keyword = Column(String(50), index=True)
    type = Column(String(255))
    description = Column(String(255), nullable=True)
    usage = Column(Text, nullable=True)
    version = Column(String(255), nullable=True)
    created = Column(DateTime)

    name = Column(String(255))
    author = Column(String(255))
    license = Column(String(255), nullable=True)
    contact = Column(String(255), nullable=True)

    citation = Column(String(255))
    citation_description = Column(String(255), nullable=True)
    citation_version = Column(String(255), nullable=True)
    citation_published = Column(Date, nullable=True)
    citation_url = Column(String(255), nullable=True)

    entries = relationship('AnnotationEntry', back_populates="annotation")

    def __repr__(self):
        return 'Annotation({})'.format(self.keyword)


class AnnotationEntry(Base):
    __tablename__ = ANNOTATION_ENTRY_TABLE_NAME
    id = Column(Integer, primary_key=True)

    name = Column(String(255), nullable=False)
    label = Column(String(255), nullable=True)

    annotation_id = Column(Integer, ForeignKey(ANNOTATION_TABLE_NAME + '.id'), index=True)
    annotation = relationship('Annotation', back_populates='entries')

    edges = relationship(
        "Edge",
        secondary=edge_annotations_relationship,
        back_populates="annotations"
    )

    def __repr__(self):
        return 'AnnotationEntry({}, {})'.format(self.name, self.label)


owl_relationship = Table(
    'owl_relationship', Base.metadata,
    Column('left_id', Integer, ForeignKey('OwlEntry.id'), primary_key=True),
    Column('right_id', Integer, ForeignKey('OwlEntry.id'), primary_key=True)
)


class Owl(Base):
    __tablename__ = OWL_TABLE_NAME

    id = Column(Integer, Sequence('Owl_id_seq'), primary_key=True)
    iri = Column(Text, unique=True)

    entries = relationship("OwlEntry", back_populates='owl')

    def __repr__(self):
        return "Owl(iri={})>".format(self.iri)


class OwlEntry(Base):
    __tablename__ = OWL_ENTRY_TABLE_NAME

    id = Column(Integer, Sequence('OwlEntry_id_seq'), primary_key=True)

    entry = Column(String(255))
    encoding = Column(String(50))

    owl_id = Column(Integer, ForeignKey('Owl.id'), index=True)
    owl = relationship('Owl', back_populates='entries')

    children = relationship('OwlEntry',
                            secondary=owl_relationship,
                            primaryjoin=id == owl_relationship.c.left_id,
                            secondaryjoin=id == owl_relationship.c.right_id)

    def __repr__(self):
        return 'OwlEntry({}:{})'.format(self.owl, self.entry)


class Network(Base):
    __tablename__ = NETWORK_TABLE_NAME
    id = Column(Integer, primary_key=True)

    name = Column(String(255), index=True)
    version = Column(String(255))

    authors = Column(Text, nullable=True)
    contact = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    copyright = Column(String(255), nullable=True)
    disclaimer = Column(String(255), nullable=True)
    licenses = Column(String(255), nullable=True)

    created = Column(DateTime, default=datetime.datetime.utcnow)
    blob = Column(Binary)

    __table_args__ = (
        UniqueConstraint("name", "version"),
    )


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


edge_properties_relationship = Table(
    'pybel_edge_properties', Base.metadata,
    Column('edge_id', Integer, ForeignKey(EDGE_TABLE_NAME + '.id')),
    Column('property_id', Integer, ForeignKey(EDGE_PROPERTY_TABLE_NAME + '.id'))
)


class EdgeProperty(Base):
    __tablename__ = EDGE_PROPERTY_TABLE_NAME
    id = Column(Integer, primary_key=True)

    participant = Column(String(255))
    modifier = Column(String(255))
    relativeKey = Column(String(255), nullable=True)
    propValue = Column(String(255), nullable=True)
    name_id = Column(Integer, ForeignKey(NAMESPACE_ENTRY_TABLE_NAME + '.id'), nullable=True)

    edges = relationship(
        "Edge",
        secondary=edge_properties_relationship,
        back_populates="properties"
    )


node_modifications_relationship = Table(
    'pybel_node_modifications', Base.metadata,
    Column('node_id', Integer, ForeignKey(NODE_TABLE_NAME + '.id')),
    Column('modification_id', Integer, ForeignKey(MODIFICATION_TABLE_NAME + '.id'))
)


class Node(Base):
    __tablename__ = NODE_TABLE_NAME
    id = Column(Integer, primary_key=True)

    type = Column(String(255))
    nodeIdentifier_id = Column(Integer, ForeignKey(NAMESPACE_ENTRY_TABLE_NAME + '.id'), nullable=True, index=True)
    nodeKeyString = Column(String(255))
    sha256 = Column(String(255), index=True)

    modifications = relationship(
        "Modification",
        secondary=node_modifications_relationship,
        back_populates="nodes")


class Modification(Base):
    __tablename__ = MODIFICATION_TABLE_NAME
    id = Column(Integer, primary_key=True)

    modType = Column(String(255))
    variantString = Column(String(255), nullable=True)
    pmodName_id = Column(ForeignKey(NAMESPACE_ENTRY_TABLE_NAME + '.id'), nullable=True, index=True)
    p3Name_id = Column(ForeignKey(NAMESPACE_ENTRY_TABLE_NAME + '.id'), nullable=True, index=True)
    p5Name_id = Column(ForeignKey(NAMESPACE_ENTRY_TABLE_NAME + '.id'), nullable=True, index=True)
    p3Range = Column(String(255), nullable=True)
    p5Range = Column(String(255), nullable=True)
    pmodName = Column(String(255), nullable=True)
    aminoA = Column(String(3), nullable=True)
    aminoB = Column(String(3), nullable=True)
    position = Column(Integer, nullable=True)

    pmodNameID = relationship("NamespaceEntry", foreign_keys=[pmodName_id])
    p3NameID = relationship("NamespaceEntry", foreign_keys=[p3Name_id])
    p5NameID = relationship("NamespaceEntry", foreign_keys=[p5Name_id])

    nodes = relationship(
        "Node",
        secondary=node_modifications_relationship,
        back_populates="modifications"
    )


class Edge(Base):
    __tablename__ = EDGE_TABLE_NAME
    id = Column(Integer, primary_key=True)

    subject_id = Column(Integer, ForeignKey(NODE_TABLE_NAME + '.id'), index=True)
    relation = Column(String(50))
    object_id = Column(Integer, ForeignKey(NODE_TABLE_NAME + '.id'), index=True)
    citation_id = Column(Integer, ForeignKey(CITATION_TABLE_NAME + '.id'), nullable=True, index=True)
    supportingText_id = Column(Integer, ForeignKey(EVIDENCE_TABLE_NAME + '.id'), nullable=True, index=True)
    sha256 = Column(String(255), index=True)

    subject = relationship("Node", foreign_keys=[subject_id])
    object = relationship("Node", foreign_keys=[object_id])

    properties = relationship(
        "EdgeProperty",
        secondary=edge_properties_relationship,
        back_populates="edges"
    )

    annotations = relationship(
        "AnnotationEntry",
        secondary=edge_annotations_relationship,
        back_populates="edges"
    )
