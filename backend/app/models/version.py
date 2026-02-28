from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Version(Base):
    __tablename__ = "versions"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    version_number = Column(String, nullable=False)  # e.g., "1.0.0", "1.0.1"
    description = Column(Text, nullable=True)
    commit_hash = Column(String, nullable=True)  # Git commit hash if applicable
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    
    # Snapshot information
    file_count = Column(Integer, default=0)
    line_count = Column(Integer, default=0)
    
    # Relationship
    project = relationship("Project", backref="versions")
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "version_number": self.version_number,
            "description": self.description,
            "commit_hash": self.commit_hash,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
            "file_count": self.file_count,
            "line_count": self.line_count,
        }
