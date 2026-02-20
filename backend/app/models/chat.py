from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"))
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
