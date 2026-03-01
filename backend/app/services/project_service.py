import os
import shutil
import uuid
from pathlib import Path
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.project import Project, ProjectStatus, SourceType
from app.services.project_context_service import ProjectContextService
from app.llm.service import LLMService


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
        
        # 创建项目时不设置architecture字段，避免数据库错误
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

        # 不再自动生成项目上下文信息，改为用户手动触发
        # 这样可以大幅提升项目创建速度
        # 用户可以通过点击"分析项目"按钮来触发完整分析
        try:
            # 只读取README文件，不执行LLM分析
            readme_path = project_dir / "README.md"
            if readme_path.exists():
                try:
                    with open(readme_path, "r", encoding="utf-8", errors="ignore") as f:
                        project.readme_content = f.read()
                        self.db.commit()
                except Exception:
                    pass
        except Exception as e:
            print(f"读取README文件失败: {e}")

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

        # 优先使用生成的项目摘要
        description = project.project_summary or ""
        
        # 如果没有生成的摘要，使用数据库中的README内容
        if not description and project.readme_content:
            description = project.readme_content
        
        # 如果数据库中也没有README内容，尝试从文件系统读取README.md文件
        if not description:
            readme_path = Path(project.local_path) / "README.md"
            if readme_path.exists():
                try:
                    with open(readme_path, "r", encoding="utf-8", errors="ignore") as f:
                        description = f.read()
                except Exception:
                    pass
            
            # 如果README.md为空，返回空字符串
            # 不再使用默认描述
            if not description:
                description = ""

        # 优先使用生成的架构描述，处理字段不存在的情况
        architecture = ""
        try:
            architecture = project.architecture or ""
        except AttributeError:
            # 数据库表中可能还没有architecture字段
            pass
        
        # 如果没有生成的架构描述，返回空字符串
        # 不再使用默认架构信息

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
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Updating project {project_id} with source_type: {project.source_type}")
            logger.info(f"Project local path: {project.local_path}")
            logger.info(f"Project source URL: {project.source_url}")

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
                logger.info(f"Git pull output: {pull_result.stdout}")
                if pull_result.stderr:
                    logger.warning(f"Git pull stderr: {pull_result.stderr}")
                logger.info(f"Git pull return code: {pull_result.returncode}")

                # If pull failed, don't raise exception, just log it and continue
                # This is to avoid 500 errors when git pull fails due to local changes or network issues
                if pull_result.returncode != 0:
                    error_msg = pull_result.stderr.strip() or pull_result.stdout.strip() or "Unknown git error"
                    logger.warning(f"Git pull failed but continuing with project update: {error_msg}")
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
                    logger.warning(f"Failed to clear some items from project directory: {e}")

                # Copy from source path
                shutil.copytree(source_path, project_dir, dirs_exist_ok=True)
                logger.info("Copy completed successfully")
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

            # 重新生成项目上下文信息（全面分析）
            try:
                llm_service = LLMService()
                context_service = ProjectContextService(self.db, llm_service)
                
                # 重新读取README文件
                readme_path = project_dir / "README.md"
                if readme_path.exists():
                    try:
                        with open(readme_path, "r", encoding="utf-8", errors="ignore") as f:
                            project.readme_content = f.read()
                    except Exception:
                        pass
                else:
                    project.readme_content = None
                
                # 清除旧的摘要和分析数据
                project.project_summary = None
                project.tech_stack = None
                try:
                    project.architecture = None
                    project.data_flow = None
                    project.features_detail = None
                    project.api_info = None
                    project.key_modules = None
                except AttributeError:
                    # 某些字段可能不存在
                    pass
                
                # 使用新的全面分析方法，生成：项目摘要、架构、数据流程、功能点、API信息等
                await context_service.generate_project_analysis(project.id)
                
                self.db.commit()
                self.db.refresh(project)
                logger.info(f"项目分析完成: {project.name}")
            except Exception as e:
                logger.error(f"重新生成项目分析失败: {e}")
                # 即使生成失败，也要提交其他更新
                self.db.commit()
                self.db.refresh(project)

            logger.info(f"Project updated successfully: {project.name} ({update_message})")
            return project

        except Exception as e:
            logger.error(f"Error updating project: {str(e)}")
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
                encoding='utf-8',
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
