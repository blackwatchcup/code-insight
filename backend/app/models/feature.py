from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Feature(Base):
    __tablename__ = "features"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"))
    name = Column(String, nullable=False)
    type = Column(String, nullable=True)  # frontend, backend, api, etc.
    description = Column(Text, nullable=True)
    file_paths = Column(JSON, default=[])  # List of file paths
    created_at = Column(DateTime, server_default=func.now())

    # Relationship
    project = relationship("Project", back_populates="features")
