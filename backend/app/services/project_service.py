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

        # 检查是否为Git仓库
        is_git_repo = (Path(local_path) / ".git").exists()
        
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
            is_git_repo=is_git_repo,
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

        # Delete associated versions first to avoid foreign key constraint issues
        from app.models.version import Version
        versions = self.db.query(Version).filter(Version.project_id == project_id).all()
        for version in versions:
            self.db.delete(version)

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

    async def update_project(self, project_id: str) -> Project:
        """Update project with latest code.

        For cloud projects: pull latest code from repository
        For local projects: copy latest code from source path

        Args:
            project_id: Project ID

        Returns:
            Updated project instance

        Raises:
            ValueError: If project not found
        """
        import subprocess
        import shutil

        project = self.get_project(project_id)
        if not project:
            raise ValueError("Project not found")

        project_dir = Path(project.local_path)

        # Verify project directory exists
        if not project_dir.exists():
            raise ValueError(f"Project directory does not exist: {project_dir}")

        try:
            print(f"Updating project {project_id} with source_type: {project.source_type}")
            print(f"Project local path: {project.local_path}")
            print(f"Project source URL: {project.source_url}")

            update_success = False
            update_message = ""

            if project.source_type == SourceType.GITHUB or project.source_type == SourceType.GITLAB or project.source_type == SourceType.GITEE or project.source_type == SourceType.GIT:
                # For git-based projects, pull latest code
                print("Attempting to pull git changes...")

                # Check if this is actually a git repository
                git_dir = project_dir / ".git"
                if not git_dir.exists():
                    raise ValueError("Project directory is not a git repository. Please initialize git first.")

                # Try git pull with --no-rebase to avoid conflicts
                pull_result = subprocess.run(
                    ["git", "pull", "--no-rebase"],
                    cwd=str(project_dir),
                    check=False,
                    capture_output=True,
                    text=True,
                    encoding="utf-8"
                )
                print(f"Git pull output: {pull_result.stdout}")
                if pull_result.stderr:
                    print(f"Git pull stderr: {pull_result.stderr}")
                print(f"Git pull return code: {pull_result.returncode}")

                # If pull failed, don't raise exception, just log it and continue
                # This is to avoid 500 errors when git pull fails due to local changes or network issues
                if pull_result.returncode != 0:
                    error_msg = pull_result.stderr.strip() or pull_result.stdout.strip() or "Unknown git error"
                    print(f"Git pull failed but continuing with project update: {error_msg}")
                    update_success = True
                    update_message = "Git pull failed but continuing with project update"
                else:
                    update_success = True
                    update_message = "Git pull completed successfully"

            elif project.source_type == SourceType.LOCAL:
                # For local projects, copy latest code from source path
                if not project.source_url:
                    raise ValueError("Local project has no source URL configured")

                source_path = Path(str(project.source_url))
                print(f"Attempting to copy from source: {project.source_url}")

                # Verify source path exists
                if not source_path.exists():
                    raise ValueError(f"Source path does not exist: {source_path}")

                if not source_path.is_dir():
                    raise ValueError(f"Source path is not a directory: {source_path}")

                # Clear existing directory more carefully
                # Use a temporary directory to avoid issues if copy fails
                try:
                    for item in project_dir.iterdir():
                        if item.is_file():
                            item.unlink()
                        elif item.is_dir():
                            # Use onerror to handle permission issues
                            def on_rm_error(func, path, exc_info):
                                import stat
                                os.chmod(path, stat.S_IWRITE)
                                func(path)
                            shutil.rmtree(item, onerror=on_rm_error)
                except Exception as e:
                    print(f"Warning: Failed to clear some items from project directory: {e}")

                # Copy from source path
                shutil.copytree(source_path, project_dir, dirs_exist_ok=True)
                print("Copy completed successfully")
                update_success = True
                update_message = "Files copied successfully from source"

            elif project.source_type == SourceType.ZIP:
                raise ValueError("ZIP projects cannot be updated. Please re-import the ZIP file.")

            else:
                raise ValueError(f"Unsupported source type: {project.source_type}")

            if not update_success:
                raise ValueError(f"Project update did not complete for {project.source_type}")

            # Update file count and line count
            file_count, line_count = self._count_files_and_lines(project_dir)
            project.file_count = file_count
            project.line_count = line_count

            # Update timestamp
            from sqlalchemy.sql import func
            project.updated_at = func.now()

            self.db.commit()
            self.db.refresh(project)

            print(f"Project updated successfully: {project.name} ({update_message})")
            return project

        except Exception as e:
            print(f"Error updating project: {str(e)}")
            import traceback
            traceback.print_exc()
            raise ValueError(f"Failed to update project: {str(e)}")

    async def initialize_git_repo(self, project_id: str) -> bool:
        """Initialize git repository for a project if not already a git repo.
        
        Args:
            project_id: Project ID
            
        Returns:
            True if git repo was initialized, False if it already exists
            
        Raises:
            ValueError: If project not found
        """
        project = self.get_project(project_id)
        if not project:
            raise ValueError("Project not found")
        
        project_dir = Path(project.local_path)
        git_dir = project_dir / ".git"
        
        if git_dir.exists():
            # Update is_git_repo flag if it's not already set
            if not project.is_git_repo:
                project.is_git_repo = True
                self.db.commit()
            return False
        
        try:
            import subprocess
            # Initialize git repo
            subprocess.run(
                ["git", "init"],
                cwd=str(project_dir),
                check=True,
                capture_output=True
            )
            # Create initial commit
            subprocess.run(
                ["git", "add", "."],
                cwd=str(project_dir),
                check=True,
                capture_output=True
            )
            subprocess.run(
                ["git", "config", "user.name", "CodeInsight"],
                cwd=str(project_dir),
                check=True,
                capture_output=True
            )
            subprocess.run(
                ["git", "config", "user.email", "codeinsight@example.com"],
                cwd=str(project_dir),
                check=True,
                capture_output=True
            )
            subprocess.run(
                ["git", "commit", "-m", "Initial commit by CodeInsight"],
                cwd=str(project_dir),
                check=True,
                capture_output=True
            )
            
            # Update is_git_repo flag
            project.is_git_repo = True
            self.db.commit()
            
            return True
        except Exception as e:
            raise ValueError(f"Failed to initialize git repo: {str(e)}")

    async def get_git_branches(self, project_id: str) -> list:
        """Get git branches for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            List of git branches
            
        Raises:
            ValueError: If project not found or not a git repo
        """
        project = self.get_project(project_id)
        if not project:
            raise ValueError("Project not found")
        
        project_dir = Path(project.local_path)
        git_dir = project_dir / ".git"
        
        if not git_dir.exists():
            raise ValueError("Project is not a git repository")
        
        try:
            import subprocess
            result = subprocess.run(
                ["git", "branch", "-a"],
                cwd=str(project_dir),
                check=True,
                capture_output=True,
                text=True
            )
            branches = []
            for line in result.stdout.strip().split('\n'):
                branch = line.strip().lstrip('* ')
                if branch:
                    branches.append(branch)
            return branches
        except Exception as e:
            raise ValueError(f"Failed to get git branches: {str(e)}")

    async def get_git_commits(self, project_id: str, limit: int = 50) -> list:
        """Get git commits for a project.
        
        Args:
            project_id: Project ID
            limit: Maximum number of commits to return
            
        Returns:
            List of git commits with hash, message, author, and date
            
        Raises:
            ValueError: If project not found or not a git repo
        """
        project = self.get_project(project_id)
        if not project:
            raise ValueError("Project not found")
        
        project_dir = Path(project.local_path)
        git_dir = project_dir / ".git"
        
        if not git_dir.exists():
            raise ValueError("Project is not a git repository")
        
        try:
            import subprocess
            import os
            
            print(f"[DEBUG] get_git_commits called for project {project_id}, limit={limit}")
            print(f"[DEBUG] project_dir: {project_dir}")
            print(f"[DEBUG] git_dir exists: {(project_dir / '.git').exists()}")
            
            # Use git log with explicit UTF-8 encoding to handle Chinese characters
            result = subprocess.run(
                ["git", "log", f"--max-count={limit}", "--pretty=format:%H|%s|%an|%ad", "--encoding=UTF-8"],
                cwd=str(project_dir),
                check=True,
                capture_output=True,
                text=True
            )
            
            print(f"[DEBUG] git log returncode: {result.returncode}")
            print(f"[DEBUG] git log stdout: {repr(result.stdout)}")
            print(f"[DEBUG] git log stderr: {repr(result.stderr)}")

            commits = []
            if result.returncode == 0 and result.stdout and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                print(f"[DEBUG] Found {len(lines)} log lines")
                
                for line in lines:
                    if not line.strip():
                        continue
                    
                    parts = line.split('|', 3)
                    if len(parts) >= 4:
                        commits.append({
                            "hash": parts[0],
                            "message": parts[1],
                            "author": parts[2],
                            "date": parts[3]
                        })
                        print(f"[DEBUG] Parsed commit: hash={parts[0][:7]}, msg={parts[1][:30]}")

            print(f"[DEBUG] Total commits collected: {len(commits)}")
            
            if not commits:
                print(f"[WARNING] No commits found for project {project_id}")

            return commits
        except Exception as e:
            print(f"[ERROR] Error getting git commits: {str(e)}")
            import traceback
            traceback.print_exc()
            raise ValueError(f"Failed to get git commits: {str(e)}")

    async def checkout_git_version(self, project_id: str, commit_hash: str) -> bool:
        """Checkout a specific git commit for a project.
        
        Args:
            project_id: Project ID
            commit_hash: Git commit hash to checkout
            
        Returns:
            True if checkout was successful
            
        Raises:
            ValueError: If project not found or not a git repo
        """
        project = self.get_project(project_id)
        if not project:
            raise ValueError("Project not found")
        
        project_dir = Path(project.local_path)
        git_dir = project_dir / ".git"
        
        if not git_dir.exists():
            raise ValueError("Project is not a git repository")
        
        try:
            import subprocess
            # Checkout the commit
            subprocess.run(
                ["git", "checkout", commit_hash],
                cwd=str(project_dir),
                check=True,
                capture_output=True
            )
            # Update file count and line count
            file_count, line_count = self._count_files_and_lines(project_dir)
            project.file_count = file_count
            project.line_count = line_count
            
            self.db.commit()
            self.db.refresh(project)
            
            return True
        except Exception as e:
            raise ValueError(f"Failed to checkout git commit: {str(e)}")
