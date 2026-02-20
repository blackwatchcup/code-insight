from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class Feature(Base):
    __tablename__ = "features"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
