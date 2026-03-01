import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Boolean
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
    # 注意：以下字段是新添加的，可能需要数据库迁移
    # 为了兼容现有数据库，在代码中处理字段不存在的情况
    architecture = Column(String, nullable=True)  # 项目架构描述
    # 新增：LLM生成的详细分析字段
    data_flow = Column(String, nullable=True)  # 数据流程描述（Markdown格式）
    features_detail = Column(String, nullable=True)  # 功能点详细分析（JSON格式）
    api_info = Column(String, nullable=True)  # API信息（JSON格式，包含提取的API和LLM生成的描述）
    key_modules = Column(String, nullable=True)  # 关键模块分析（JSON格式）
    is_git_repo = Column(Boolean, default=False)  # 是否为Git仓库
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
            "architecture": getattr(self, 'architecture', None),
            "data_flow": getattr(self, 'data_flow', None),
            "features_detail": getattr(self, 'features_detail', None),
            "api_info": getattr(self, 'api_info', None),
            "key_modules": getattr(self, 'key_modules', None),
            "is_git_repo": self.is_git_repo,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
