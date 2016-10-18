from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Uniprot_Map(Base):
    __tablename__ = 'pybelmap_root'
    
    id = Column(Integer, primary_key=True)
    uniprot = Column(String(255), index=True)
    reference = Column(String(255))
    xref = Column(String(255))
    
class Resolution(Base):
     __tablename__ = 'pybelmap_resolution'
     
     id = Column(Integer, primary_key=True)
     namespace = Column(String(255))
     namespaceID = Column(String(255))
     symbol = Column(String(255))
     
     
class Namespace(Base):
    __tablename__ = 'pybelmap_namespace'
    
    id = Column(Integer, primary_key=True)
    url = Column(String(255))
    author = Column(String(255))
    keyword = Column(String(50), index=True)
    pubDate = Column(DateTime, nullable=True)
    copyright = Column(String(255))
    version = Column(Integer)
    contact = Column(String(255))
    names = relationship("Namespace_Name")
    
class Namespace_Name(Base):
    __tablename__ = 'pybelmap_name'
    
    id = Column(Integer, primary_key=True)
    namespace_id = Column(Integer, ForeignKey('pybelmap_namespace.id'), index=True)
    name = Column(String(255))
    encoding = Column(String(50))