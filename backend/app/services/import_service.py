import os
import shutil
import tempfile
import uuid
import zipfile
from pathlib import Path
from typing import Optional

import git
import requests
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.project import Project, ProjectStatus, SourceType


class ImportService:
    def __init__(self, db: Session):
        self.db = db

    async def import_from_git(
        self,
        url: str,
        branch: str = "main",
        token: Optional[str] = None,
        depth: int = 1,
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
        
        if actual_branch:
            git.Repo.clone_from(url, project_dir, branch=actual_branch, depth=depth)
        else:
            git.Repo.clone_from(url, project_dir, depth=depth)

        file_count, line_count = self._count_files_and_lines(project_dir)

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
        )

        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)

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
            )

            self.db.add(project)
            self.db.commit()
            self.db.refresh(project)

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
