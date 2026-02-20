from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class File(Base):
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"))
    path = Column(String, nullable=False)
    language = Column(String, nullable=True)
    line_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
