from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Uniprot_Map(Base):
    __tablename__ = 'map_root'
    
    id = Column(Integer, primary_key=True)
    uniprot = Column(String(255))
    reference = Column(String(255))
    xref = Column(String(255))
    
class Resolution(Base):
     __tablename__ = 'map_resolution'
     
     id = Column(Integer, primary_key=True)
     namespace = Column(String(255))
     symbol = Column(String(255))
     