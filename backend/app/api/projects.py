from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.project_service import ProjectService
from app.services.import_service import ImportService
from app.models.project import Project

router = APIRouter()

class CreateProjectRequest(BaseModel):
    name: str
    source_type: str = "local"
    local_path: str

class ImportProjectRequest(BaseModel):
    type: str
    url: str
    name: Optional[str] = None
    branch: str = "main"
    token: Optional[str] = None
    depth: int = 1

@router.get("/")
async def list_projects(page: int = 1, page_size: int = 10, db: Session = Depends(get_db)):
    project_service = ProjectService(db)
    projects, total = project_service.list_projects(page, page_size)
    return {"code": 200, "data": {"items": [p.to_dict() for p in projects], "total": total}}

@router.post("/")
async def create_project(request: CreateProjectRequest, db: Session = Depends(get_db)):
    if request.source_type != "local":
        raise HTTPException(400, "Use /import endpoint for URL imports")
    
    project_service = ProjectService(db)
    project = await project_service.create_from_local(
        name=request.name,
        local_path=request.local_path
    )
    return {"code": 200, "data": project.to_dict()}

@router.post("/import")
async def import_project(request: ImportProjectRequest, db: Session = Depends(get_db)):
    import_service = ImportService(db)
    
    if request.type == "zip":
        project = await import_service.import_from_zip(request.url, request.name)
    else:
        project = await import_service.import_from_git(
            url=request.url,
            branch=request.branch,
            token=request.token,
            depth=request.depth,
            name=request.name
        )
    
    return {"code": 200, "data": project.to_dict()}

@router.get("/{project_id}")
async def get_project(project_id: str, db: Session = Depends(get_db)):
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return {"code": 200, "data": project.to_dict()}

@router.delete("/{project_id}")
async def delete_project(project_id: str, db: Session = Depends(get_db)):
    project_service = ProjectService(db)
    success = project_service.delete_project(project_id)
    if not success:
        raise HTTPException(404, "Project not found")
    return {"code": 200, "data": {"message": "Project deleted"}}
