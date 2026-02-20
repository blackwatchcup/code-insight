import os
import uuid
import zipfile
import tempfile
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
import git
import requests
from app.models.project import Project, SourceType, ProjectStatus
from app.core.config import settings

class ImportService:
    def __init__(self, db: Session):
        self.db = db
        
    async def import_from_git(
        self, 
        url: str, 
        branch: str = "main",
        token: Optional[str] = None,
        depth: int = 1,
        name: Optional[str] = None
    ) -> Project:
        project_id = str(uuid.uuid4())[:8]
        projects_dir = Path(settings.PROJECTS_DIR)
        projects_dir.mkdir(parents=True, exist_ok=True)
        project_dir = projects_dir / project_id
        
        if token and "github.com" in url:
            url = url.replace("github.com", f"{token}@github.com")
        
        git.Repo.clone_from(
            url, 
            project_dir, 
            branch=branch, 
            depth=depth
        )
        
        if not name:
            name = self._extract_name(url)
        
        file_count, line_count = self._count_files_and_lines(project_dir)
        
        project = Project(
            id=project_id,
            name=name,
            source_type=self._detect_source_type(url),
            source_url=url,
            local_path=str(project_dir),
            branch=branch,
            status=ProjectStatus.INDEXING,
            file_count=file_count,
            line_count=line_count,
        )
        
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        
        return project
    
    async def import_from_zip(self, url: str, name: Optional[str] = None) -> Project:
        project_id = str(uuid.uuid4())[:8]
        projects_dir = Path(settings.PROJECTS_DIR)
        projects_dir.mkdir(parents=True, exist_ok=True)
        project_dir = projects_dir / project_id
        
        response = requests.get(url, stream=True)
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            for chunk in response.iter_content(chunk_size=8192):
                tmp.write(chunk)
            tmp.flush()
            tmp_path = tmp.name
        
        try:
            with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                zip_ref.extractall(project_dir)
            
            self._flatten_directory(project_dir)
            
            if not name:
                name = self._extract_name(url)
            
            file_count, line_count = self._count_files_and_lines(project_dir)
            
            project = Project(
                id=project_id,
                name=name,
                source_type=SourceType.ZIP,
                source_url=url,
                local_path=str(project_dir),
                status=ProjectStatus.INDEXING,
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
        skip_dirs = {".git", ".github", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
        relative = file_path.relative_to(base_path)
        return any(part in skip_dirs for part in relative.parts)
    
    def _flatten_directory(self, project_dir: Path):
        items = list(project_dir.iterdir())
        if len(items) == 1 and items[0].is_dir():
            single_dir = items[0]
            for item in single_dir.iterdir():
                item.rename(project_dir / item.name)
            single_dir.rmdir()
