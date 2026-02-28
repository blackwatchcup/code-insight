import os
import shutil
import uuid
from pathlib import Path
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.project import Project, ProjectStatus, SourceType


class ProjectService:
    def __init__(self, db: Session):
        self.db = db

    async def create_from_local(
        self, name: str, local_path: str, owner_id: Optional[str] = None
    ) -> Project:
        if not os.path.exists(local_path):
            raise ValueError(f"Local path does not exist: {local_path}")

        if not os.path.isdir(local_path):
            raise ValueError(f"Local path is not a directory: {local_path}")

        project_id = str(uuid.uuid4())[:8]

        projects_dir = Path(settings.PROJECTS_DIR)
        projects_dir.mkdir(parents=True, exist_ok=True)

        project_dir = projects_dir / project_id
        shutil.copytree(local_path, project_dir)

        file_count, line_count = self._count_files_and_lines(project_dir)

        project = Project(
            id=project_id,
            name=name,
            owner_id=owner_id,
            source_type=SourceType.LOCAL,
            source_url=local_path,
            local_path=str(project_dir),
            status=ProjectStatus.READY,
            file_count=file_count,
            line_count=line_count,
        )

        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)

        return project

    def _count_files_and_lines(self, directory: Path) -> Tuple[int, int]:
        file_count = 0
        line_count = 0

        for ext in settings.SUPPORTED_EXTENSIONS:
            for file_path in directory.rglob(f"*{ext}"):
                if self._should_skip_path(file_path, directory):
                    continue
                file_count += 1
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        line_count += sum(1 for _ in f)
                except Exception:
                    pass

        return file_count, line_count

    def _should_skip_path(self, file_path: Path, base_path: Path) -> bool:
        skip_dirs = {
            ".git",
            ".github",
            "node_modules",
            "__pycache__",
            ".venv",
            "venv",
            "dist",
            "build",
        }
        relative = file_path.relative_to(base_path)
        return any(part in skip_dirs for part in relative.parts)

    def get_project(self, project_id: str):
        return self.db.query(Project).filter(Project.id == project_id).first()

    def list_projects(self, page: int = 1, page_size: int = 10) -> Tuple[list, int]:
        query = self.db.query(Project).order_by(Project.created_at.desc())
        total = query.count()
        offset = (page - 1) * page_size
        projects = query.offset(offset).limit(page_size).all()
        return projects, total

    def list_projects_by_owner(
        self, owner_id: str, page: int = 1, page_size: int = 10
    ) -> Tuple[list, int]:
        query = (
            self.db.query(Project)
            .filter(Project.owner_id == owner_id)
            .order_by(Project.created_at.desc())
        )
        total = query.count()
        offset = (page - 1) * page_size
        projects = query.offset(offset).limit(page_size).all()
        return projects, total

    def delete_project(self, project_id: str) -> bool:
        project = self.get_project(project_id)
        if not project:
            return False

        if project.local_path and os.path.exists(project.local_path):

            def on_rm_error(func, path, exc_info):
                import stat

                os.chmod(path, stat.S_IWRITE)
                func(path)

            try:
                shutil.rmtree(project.local_path, onerror=on_rm_error)
            except Exception as e:
                import logging

                logging.warning(f"Failed to delete project directory: {e}")

        self.db.delete(project)
        self.db.commit()
        return True

    def get_project_info(self, project_id: str) -> dict:
        project = self.get_project(project_id)
        if not project:
            raise ValueError("Project not found")

        # 尝试读取README.md文件
        readme_path = Path(project.local_path) / "README.md"
        description = ""
        if readme_path.exists():
            try:
                with open(readme_path, "r", encoding="utf-8", errors="ignore") as f:
                    description = f.read()
            except Exception:
                pass

        # 如果README.md为空，使用默认描述
        if not description:
            description = "本地代码仓库智能分析和知识问答系统。CodeInsight 是一个强大的代码分析工具，能够智能分析本地代码仓库，提供代码结构可视化、依赖关系分析、功能提取等功能，并支持基于代码的智能问答。"

        # 生成实际架构的markdown描述
        architecture = """# 系统架构

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│                     │     │                     │     │                     │
│   前端应用          │────▶│   后端API           │────▶│   数据库            │
│   React + TypeScript│     │   FastAPI + Python  │     │   SQLite            │
│   TailwindCSS       │◀────│                     │◀────│                     │
│                     │     │                     │     │                     │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
          ▲                          ▲                          ▲
          │                          │                          │
          ▼                          ▼                          ▼
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│                     │     │                     │     │                     │
│   代码解析模块       │     │   功能分析模块       │     │   向量存储          │
│   Python/JS/TS/Go   │     │   API提取/特征检测  │     │   嵌入式向量        │
│   Java解析器        │     │                     │     │                     │
│                     │     │                     │     │                     │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
          ▲                          ▲                          ▲
          │                          │                          │
          └──────────────────────────┼──────────────────────────┘
                                     │
                                     ▼
                            ┌─────────────────────┐
                            │                     │
                            │   智能问答模块      │
                            │   LLM集成          │
                            │   RAG技术          │
                            │                     │
                            └─────────────────────┘
```

## 架构说明

1. **前端应用**：
   - 使用React + TypeScript构建用户界面
   - TailwindCSS用于样式设计
   - 提供项目管理、代码分析、智能问答等功能

2. **后端API**：
   - FastAPI框架提供RESTful API
   - Python实现核心业务逻辑
   - 处理前端请求，返回分析结果

3. **数据库**：
   - SQLite存储项目信息、聊天记录等数据
   - 轻量级设计，易于部署

4. **代码解析模块**：
   - 支持多种编程语言的解析器
   - 提取代码结构、函数、类等信息
   - 生成代码依赖关系图

5. **功能分析模块**：
   - API提取与分析
   - 特征检测与提取
   - 代码质量评估

6. **向量存储**：
   - 存储代码嵌入向量
   - 支持相似性搜索
   - 为RAG技术提供基础

7. **智能问答模块**：
   - 集成LLM模型
   - 基于RAG技术提供代码相关问答
   - 支持上下文理解和多轮对话

## 数据流

1. 用户通过前端上传或导入项目
2. 后端接收项目并进行解析
3. 解析模块分析代码结构和依赖关系
4. 功能分析模块提取项目特征和API
5. 向量存储模块将代码转换为向量并存储
6. 用户通过前端发起智能问答请求
7. 后端使用RAG技术检索相关代码片段
8. LLM基于检索结果生成回答
9. 前端展示回答给用户
"""

        return {
            "description": description,
            "architecture": architecture
        }
