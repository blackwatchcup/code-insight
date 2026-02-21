from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class File(Base):
    __tablename__ = "files"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"))
    path = Column(String, nullable=False)
    language = Column(String, nullable=True)
    line_count = Column(Integer, default=0)
    content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationship
    project = relationship("Project", back_populates="files")
