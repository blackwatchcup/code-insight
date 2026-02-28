import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class SourceType(str, enum.Enum):
    LOCAL = "local"
    GITHUB = "github"
    GITLAB = "gitlab"
    GITEE = "gitee"
    GIT = "git"
    ZIP = "zip"


class ProjectStatus(str, enum.Enum):
    PENDING = "pending"
    INDEXING = "indexing"
    ANALYZING = "analyzing"
    READY = "ready"
    COMPLETED = "completed"
    ERROR = "error"
    FAILED = "failed"


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    owner_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    source_type = Column(Enum(SourceType), default=SourceType.LOCAL)
    source_url = Column(String, nullable=True)
    local_path = Column(String, nullable=False)
    branch = Column(String, default="main")
    status = Column(Enum(ProjectStatus), default=ProjectStatus.INDEXING)
    file_count = Column(Integer, default=0)
    line_count = Column(Integer, default=0)
    # 项目上下文字段 - 用于智能聊天
    readme_content = Column(String, nullable=True)  # README文件内容
    project_summary = Column(String, nullable=True)  # LLM生成的项目摘要
    tech_stack = Column(String, nullable=True)  # 技术栈（JSON数组字符串）
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="projects")
    files = relationship("File", back_populates="project", cascade="all, delete-orphan")
    chats = relationship("Chat", back_populates="project", cascade="all, delete-orphan")
    features = relationship("Feature", back_populates="project", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert project to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "owner_id": self.owner_id,
            "source_type": self.source_type.value if self.source_type else None,
            "source_url": self.source_url,
            "local_path": self.local_path,
            "branch": self.branch,
            "status": self.status.value if self.status else None,
            "file_count": self.file_count,
            "line_count": self.line_count,
            "readme_content": self.readme_content,
            "project_summary": self.project_summary,
            "tech_stack": self.tech_stack,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
