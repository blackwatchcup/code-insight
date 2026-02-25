from enum import Enum

from sqlalchemy import Column, DateTime, String, Text, JSON
from sqlalchemy.sql import func

from app.core.database import Base


class ChatMode(str, Enum):
    """Chat mode determines how the AI responds."""
    PROJECT = "project"  # RAG-based, uses project codebase context
    FREEFORM = "freeform"  # General chat, no project context


class ChatSession(Base):
    """Tracks chat sessions with metadata."""
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=True)
    project_id = Column(String, index=True, nullable=True)
    chat_mode = Column(String, default="project")  # 'project' or 'freeform'
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    project_id = Column(String, index=True, nullable=True)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)  # Store sources as JSON
    timestamp = Column(DateTime, server_default=func.now(), index=True)
    chat_mode = Column(String, default="project")  # 'project' or 'freeform'
    extra_data = Column(JSON, nullable=True)  # Renamed from 'metadata'
