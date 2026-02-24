from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Chat(Base):
    __tablename__ = "chats"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"))
    title = Column(String, nullable=True)
    mode = Column(String, default="hybrid")  # implementation, planning, hybrid
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationship
    project = relationship("Project", back_populates="chats")
