from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user
from app.services.project_service import ProjectService
from app.services.import_service import ImportService
from app.models.project import Project
from app.models.user import User

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

@router.get("/", tags=["Projects"])
async def list_projects(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    try:
        project_service = ProjectService(db)
        
        # If user is authenticated and not admin, only show their projects
        if current_user and not current_user.is_admin():
            projects, total = project_service.list_projects_by_owner(
                owner_id=current_user.id,
                page=page,
                page_size=page_size
            )
        else:
            # Admin or no auth: show all projects
            projects, total = project_service.list_projects(page, page_size)
        
        return {"code": 200, "data": {"items": [p.to_dict() for p in projects], "total": total}}
    except Exception as e:
        # Return empty list if database has issues
        return {"code": 200, "data": {"items": [], "total": 0}}

@router.post("/", tags=["Projects"])
async def create_project(
    request: CreateProjectRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    if request.source_type != "local":
        raise HTTPException(400, "Use /import endpoint for URL imports")
    
    project_service = ProjectService(db)
    owner_id = current_user.id if current_user else None
    project = await project_service.create_from_local(
        name=request.name,
        local_path=request.local_path,
        owner_id=owner_id
    )
    return {"code": 200, "data": project.to_dict()}

@router.post("/import", tags=["Projects"])
async def import_project(
    request: ImportProjectRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    import_service = ImportService(db)
    owner_id = current_user.id if current_user else None
    
    if request.type == "zip":
        project = await import_service.import_from_zip(request.url, request.name, owner_id)
    else:
        project = await import_service.import_from_git(
            url=request.url,
            branch=request.branch,
            token=request.token,
            depth=request.depth,
            name=request.name,
            owner_id=owner_id
        )
    
    return {"code": 200, "data": project.to_dict()}

@router.get("/{project_id}", tags=["Projects"])
async def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    
    # Check access permission
    if current_user and not current_user.is_admin():
        if project.owner_id != current_user.id:
            raise HTTPException(403, "Access denied")
    
    return {"code": 200, "data": project.to_dict()}

@router.delete("/{project_id}", tags=["Projects"])
async def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    
    if not project:
        raise HTTPException(404, "Project not found")
    
    # Check access permission
    if current_user and not current_user.is_admin():
        if project.owner_id != current_user.id:
            raise HTTPException(403, "Access denied")
    
    success = project_service.delete_project(project_id)
    if not success:
        raise HTTPException(404, "Project not found")
    return {"code": 200, "data": {"message": "Project deleted"}}
