from sqlalchemy import Column, String, DateTime, Integer, Enum
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class SourceType(str, enum.Enum):
    LOCAL = "local"
    GITHUB = "github"
    GITLAB = "gitlab"
    GITEE = "gitee"
    GIT = "git"
    ZIP = "zip"

class ProjectStatus(str, enum.Enum):
    INDEXING = "indexing"
    READY = "ready"
    ERROR = "error"

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    source_type = Column(Enum(SourceType), default=SourceType.LOCAL)
    source_url = Column(String, nullable=True)
    local_path = Column(String, nullable=False)
    branch = Column(String, default="main")
    status = Column(Enum(ProjectStatus), default=ProjectStatus.INDEXING)
    file_count = Column(Integer, default=0)
    line_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
