import os
import re
import shutil
import tempfile
import uuid
import zipfile
import logging
from pathlib import Path
from typing import Optional, Tuple

import git
import requests
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.project import Project, ProjectStatus, SourceType

logger = logging.getLogger(__name__)


class ImportService:
    def __init__(self, db: Session):
        self.db = db

    async def get_remote_branches(
        self, url: str, token: Optional[str] = None
    ) -> list[str]:
        """获取远程仓库的分支列表"""
        try:
            if "github.com" in url:
                match = re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$", url)
                if match:
                    owner, repo = match.groups()
                    api_url = f"https://api.github.com/repos/{owner}/{repo}/branches"
                    headers = {}
                    if token:
                        headers["Authorization"] = f"token {token}"
                    
                    logger.info(f"使用GitHub API获取分支: {api_url}")
                    import httpx
                    async with httpx.AsyncClient() as client:
                        response = await client.get(api_url, headers=headers)
                        if response.status_code == 200:
                            branches_data = response.json()
                            branches = [b["name"] for b in branches_data]
                            unique_branches = sorted(set(branches))
                            logger.info(f"成功获取到 {len(unique_branches)} 个分支: {unique_branches}")
                            return unique_branches
                        else:
                            logger.warning(f"GitHub API返回状态码: {response.status_code}")
                            raise Exception(f"GitHub API error: {response.status_code}")
            
            logger.info("尝试使用git clone获取分支")
            if token and "github.com" in url:
                url = url.replace("github.com", f"{token}@github.com")

            temp_dir = Path(tempfile.gettempdir()) / f"temp_git_branches_{uuid.uuid4().hex[:8]}"
            try:
                logger.info(f"开始获取远程分支: {url}")
                
                repo = git.Repo.clone_from(
                    url,
                    temp_dir,
                    depth=1,
                    no_single_branch=True
                )
                
                branches = [ref.name.split('/')[-1] for ref in repo.references if ref.name.startswith('refs/remotes/origin/')]
                unique_branches = sorted(set(branches))
                logger.info(f"成功获取到 {len(unique_branches)} 个分支: {unique_branches}")
                return unique_branches
            finally:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as e:
            logger.error(f"获取远程分支失败: {e}")
            logger.error(f"错误类型: {type(e).__name__}")
            logger.info("返回默认分支列表: ['main', 'master']")
            return ['main', 'master']

    async def import_from_git(
        self,
        url: str,
        branch: str = "main",
        token: Optional[str] = None,
        depth: int = 0,  # 0 means full clone
        name: Optional[str] = None,
        owner_id: Optional[str] = None,
    ) -> Project:
        if not name:
            name = self._extract_name(url)
        
        # 使用项目名称作为目录名（清理特殊字符）
        project_dir_name = self._sanitize_directory_name(name)
        projects_dir = Path(settings.PROJECTS_DIR)
        projects_dir.mkdir(parents=True, exist_ok=True)
        
        # 确保目录名唯一
        project_dir = self._get_unique_directory(projects_dir, project_dir_name)
        
        project_id = project_dir.name

        if token and "github.com" in url:
            url = url.replace("github.com", f"{token}@github.com")

        actual_branch = self._get_default_branch(url, branch)
        
        # 不使用depth参数，克隆完整的仓库
        if actual_branch:
            git.Repo.clone_from(url, project_dir, branch=actual_branch)
        else:
            git.Repo.clone_from(url, project_dir)

        file_count, line_count = self._count_files_and_lines(project_dir)
        readme_content = self._read_readme(project_dir)
        tech_stack = self._detect_tech_stack(project_dir)

        # Git导入的项目肯定是Git仓库
        is_git_repo = True
        
        # 创建项目时不设置architecture字段，避免数据库错误
        project = Project(
            id=project_id,
            name=name,
            owner_id=owner_id,
            source_type=self._detect_source_type(url),
            source_url=url,
            local_path=str(project_dir),
            branch=branch,
            status=ProjectStatus.READY,
            file_count=file_count,
            line_count=line_count,
            readme_content=readme_content,
            tech_stack=tech_stack,
            is_git_repo=is_git_repo,
        )

        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)

        # 不再在导入时自动执行完整分析，改为用户手动触发
        # 这样可以大幅提升导入速度
        # 用户可以通过点击"分析项目"按钮来触发完整分析
        logger.info(f"项目 {project.name} 导入完成，未执行自动分析")

        return project

    async def import_from_zip(
        self, url: str, name: Optional[str] = None, owner_id: Optional[str] = None
    ) -> Project:
        if not name:
            name = self._extract_name(url)
        
        # 使用项目名称作为目录名（清理特殊字符）
        project_dir_name = self._sanitize_directory_name(name)
        projects_dir = Path(settings.PROJECTS_DIR)
        projects_dir.mkdir(parents=True, exist_ok=True)
        
        # 确保目录名唯一
        project_dir = self._get_unique_directory(projects_dir, project_dir_name)
        
        project_id = project_dir.name

        response = requests.get(url, stream=True)
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            for chunk in response.iter_content(chunk_size=8192):
                tmp.write(chunk)
            tmp.flush()
            tmp_path = tmp.name

        try:
            with zipfile.ZipFile(tmp_path, "r") as zip_ref:
                zip_ref.extractall(project_dir)

            self._flatten_directory(project_dir)

            file_count, line_count = self._count_files_and_lines(project_dir)
            readme_content = self._read_readme(project_dir)
            tech_stack = self._detect_tech_stack(project_dir)

            # 检查是否为Git仓库
            is_git_repo = (project_dir / ".git").exists()

            # 创建项目时不设置architecture字段，避免数据库错误
            project = Project(
                id=project_id,
                name=name,
                owner_id=owner_id,
                source_type=SourceType.ZIP,
                source_url=url,
                local_path=str(project_dir),
                status=ProjectStatus.READY,
                file_count=file_count,
                line_count=line_count,
                readme_content=readme_content,
                tech_stack=tech_stack,
                is_git_repo=is_git_repo,
            )

            self.db.add(project)
            self.db.commit()
            self.db.refresh(project)

            # 不再在导入时自动执行完整分析，改为用户手动触发
            # 这样可以大幅提升导入速度
            # 用户可以通过点击"分析项目"按钮来触发完整分析
            logger.info(f"项目 {project.name} 导入完成，未执行自动分析")

            return project
        finally:
            os.unlink(tmp_path)

    def _extract_name(self, url: str) -> str:
        return url.rstrip("/").split("/")[-1].replace(".git", "")

    def _sanitize_directory_name(self, name: str) -> str:
        """Sanitize project name to use as directory name."""
        import re
        # Remove or replace invalid characters
        name = re.sub(r'[<>:"/\\|?*]', '_', name)
        # Remove leading/trailing whitespace
        name = name.strip()
        # Limit length
        name = name[:50]
        # Ensure it's not empty
        if not name:
            name = "project"
        return name

    def _get_unique_directory(self, base_dir: Path, dir_name: str) -> Path:
        """Get a unique directory path by appending numbers if necessary."""
        counter = 1
        unique_name = dir_name
        
        while (base_dir / unique_name).exists():
            unique_name = f"{dir_name}_{counter}"
            counter += 1
        
        return base_dir / unique_name

    def _get_default_branch(self, url: str, preferred_branch: str = "main") -> Optional[str]:
        try:
            from git import Repo
            repo = Repo.clone_from(url, Path(tempfile.gettempdir()) / f"temp_git_check_{uuid.uuid4().hex[:8]}", depth=1, branch=preferred_branch)
            repo.git.clear_cache()
            shutil.rmtree(repo.working_dir, ignore_errors=True)
            return preferred_branch
        except Exception:
            pass
        
        for branch in ["master", "main", "develop", "dev"]:
            if branch == preferred_branch:
                continue
            try:
                from git import Repo
                temp_dir = Path(tempfile.gettempdir()) / f"temp_git_check_{uuid.uuid4().hex[:8]}"
                repo = Repo.clone_from(url, temp_dir, depth=1, branch=branch)
                shutil.rmtree(temp_dir, ignore_errors=True)
                return branch
            except Exception:
                continue
        
        return None

    def _detect_source_type(self, url: str) -> SourceType:
        if "github.com" in url:
            return SourceType.GITHUB
        elif "gitlab.com" in url:
            return SourceType.GITLAB
        elif "gitee.com" in url:
            return SourceType.GITEE
        return SourceType.GIT

    def _count_files_and_lines(self, directory: Path):
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

    def _flatten_directory(self, project_dir: Path):
        items = list(project_dir.iterdir())
        if len(items) == 1 and items[0].is_dir():
            single_dir = items[0]
            for item in single_dir.iterdir():
                item.rename(project_dir / item.name)
            single_dir.rmdir()

    def _read_readme(self, directory: Path) -> Optional[str]:
        """Read README file content from project directory."""
        readme_names = ["README.md", "README.rst", "README.txt", "README", "readme.md"]
        for name in readme_names:
            readme_path = directory / name
            if readme_path.exists():
                try:
                    content = readme_path.read_text(encoding="utf-8", errors="ignore")
                    # 限制README内容长度，避免过大
                    if len(content) > 50000:
                        content = content[:50000] + "\n... (truncated)"
                    return content
                except Exception:
                    pass
        return None

    def _detect_tech_stack(self, directory: Path) -> Optional[str]:
        """Detect technology stack from project files."""
        tech_indicators = {
            "Python": ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile"],
            "JavaScript": ["package.json"],
            "TypeScript": ["tsconfig.json"],
            "Go": ["go.mod"],
            "Java": ["pom.xml", "build.gradle"],
            "Rust": ["Cargo.toml"],
            "Vue": ["vue.config.js"],
            "React": [],  # 需要从package.json判断
            "Django": [],  # 需要从requirements.txt判断
            "FastAPI": [],  # 需要从requirements.txt判断
        }
        
        detected = set()
        
        # 检查配置文件
        for tech, files in tech_indicators.items():
            for file in files:
                if (directory / file).exists():
                    detected.add(tech)
        
        # 检查package.json中的依赖
        package_json = directory / "package.json"
        if package_json.exists():
            try:
                import json
                with open(package_json, "r", encoding="utf-8") as f:
                    pkg = json.load(f)
                    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                    if "react" in deps or "react-dom" in deps:
                        detected.add("React")
                    if "vue" in deps:
                        detected.add("Vue")
                    if "next" in deps:
                        detected.add("Next.js")
                    if "express" in deps:
                        detected.add("Express")
            except Exception:
                pass
        
        # 检查requirements.txt中的依赖
        requirements = directory / "requirements.txt"
        if requirements.exists():
            try:
                content = requirements.read_text(encoding="utf-8", errors="ignore").lower()
                if "django" in content:
                    detected.add("Django")
                if "fastapi" in content:
                    detected.add("FastAPI")
                if "flask" in content:
                    detected.add("Flask")
            except Exception:
                pass
        
        import json
        return json.dumps(list(detected)) if detected else None
