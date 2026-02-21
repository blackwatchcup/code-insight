import os
import shutil
import uuid
from pathlib import Path
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from app.models.project import Project, SourceType, ProjectStatus
from app.core.config import settings

class ProjectService:
    def __init__(self, db: Session):
        self.db = db
    
    async def create_from_local(
        self,
        name: str,
        local_path: str,
        owner_id: Optional[str] = None
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
        skip_dirs = {".git", ".github", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
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
        self,
        owner_id: str,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[list, int]:
        query = self.db.query(Project).filter(
            Project.owner_id == owner_id
        ).order_by(Project.created_at.desc())
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
