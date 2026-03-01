from typing import Optional

import git
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.project import Project
from app.models.user import User
from app.services.import_service import ImportService
from app.services.project_service import ProjectService

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
    current_user: Optional[User] = Depends(get_current_user),
):
    try:
        project_service = ProjectService(db)

        # If user is authenticated and not admin, only show their projects
        if current_user and not current_user.is_admin():
            projects, total = project_service.list_projects_by_owner(
                owner_id=current_user.id, page=page, page_size=page_size
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
    current_user: Optional[User] = Depends(get_current_user),
):
    if request.source_type != "local":
        raise HTTPException(400, "Use /import endpoint for URL imports")

    project_service = ProjectService(db)
    owner_id = current_user.id if current_user else None
    project = await project_service.create_from_local(
        name=request.name, local_path=request.local_path, owner_id=owner_id
    )
    return {"code": 200, "data": project.to_dict()}


@router.post("/import", tags=["Projects"])
async def import_project(
    request: ImportProjectRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    import_service = ImportService(db)
    owner_id = current_user.id if current_user else None

    try:
        if request.type == "zip":
            project = await import_service.import_from_zip(request.url, request.name, owner_id)
        else:
            project = await import_service.import_from_git(
                url=request.url,
                branch=request.branch,
                token=request.token,
                depth=request.depth,
                name=request.name,
                owner_id=owner_id,
            )

        return {"code": 200, "data": project.to_dict()}
    except git.exc.GitCommandError as e:
        raise HTTPException(400, f"Git clone failed: {str(e)}. Please check if the repository URL is correct and the branch exists.")
    except Exception as e:
        raise HTTPException(400, f"Import failed: {str(e)}")


@router.get("/{project_id}", tags=["Projects"])
async def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
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
    current_user: Optional[User] = Depends(get_current_user),
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


@router.patch("/{project_id}/status", tags=["Projects"])
async def update_project_status(
    project_id: str,
    status: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)

    if not project:
        raise HTTPException(404, "Project not found")

    # Check access permission
    if current_user and not current_user.is_admin():
        if project.owner_id != current_user.id:
            raise HTTPException(403, "Access denied")

    from app.models.project import ProjectStatus

    try:
        new_status = ProjectStatus(status)
        project.status = new_status
        db.commit()
        return {"code": 200, "data": {"message": "Status updated"}}
    except ValueError:
        raise HTTPException(400, "Invalid status value")


@router.get("/{project_id}/info", tags=["Projects"])
async def get_project_info(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    # Check access permission
    if current_user and not current_user.is_admin():
        if project.owner_id != current_user.id:
            raise HTTPException(403, "Access denied")

    try:
        info = project_service.get_project_info(project_id)
        return {"code": 200, "data": info}
    except Exception as e:
        raise HTTPException(500, f"Failed to get project info: {str(e)}")


@router.post("/{project_id}/update", tags=["Projects"])
async def update_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    # Check access permission
    if current_user and not current_user.is_admin():
        if project.owner_id != current_user.id:
            raise HTTPException(403, "Access denied")

    try:
        updated_project = await project_service.update_project(project_id)
        return {"code": 200, "data": updated_project.to_dict()}
    except Exception as e:
        raise HTTPException(500, f"Failed to update project: {str(e)}")


@router.post("/{project_id}/analyze", tags=["Projects"])
async def analyze_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """触发项目重新分析
    
    生成或更新项目的全面分析信息，包括：
    - 项目摘要
    - 技术栈分析
    - 架构描述
    - 数据流程
    - 功能点分析
    - API信息
    - 关键模块
    """
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    # Check access permission
    if current_user and not current_user.is_admin():
        if project.owner_id != current_user.id:
            raise HTTPException(403, "Access denied")

    try:
        from app.llm.service import LLMService
        from app.services.project_context_service import ProjectContextService
        
        llm_service = LLMService()
        context_service = ProjectContextService(db, llm_service)
        
        # 执行全面分析
        results = await context_service.generate_project_analysis(project_id)
        
        # 刷新项目数据
        db.refresh(project)
        
        return {
            "code": 200, 
            "data": {
                "message": "项目分析完成",
                "project": project.to_dict(),
                "analysis_results": {
                    "tech_stack_count": len(results.get("tech_stack", [])),
                    "has_architecture": bool(results.get("architecture")),
                    "has_summary": bool(results.get("project_summary")),
                    "has_data_flow": bool(results.get("data_flow")),
                    "api_count": len(results.get("api_info", {}).get("apis", [])),
                    "modules_count": len(results.get("key_modules", {}).get("modules", [])),
                }
            }
        }
    except Exception as e:
        import logging
        logging.error(f"分析项目失败: {e}")
        raise HTTPException(500, f"Failed to analyze project: {str(e)}")


@router.post("/{project_id}/git/initialize", tags=["Projects"])
async def initialize_git_repo(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    # Check access permission
    if current_user and not current_user.is_admin():
        if project.owner_id != current_user.id:
            raise HTTPException(403, "Access denied")

    try:
        initialized = await project_service.initialize_git_repo(project_id)
        return {"code": 200, "data": {"initialized": initialized}}
    except Exception as e:
        raise HTTPException(500, f"Failed to initialize git repo: {str(e)}")


@router.get("/{project_id}/git/branches", tags=["Projects"])
async def get_git_branches(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    # Check access permission
    if current_user and not current_user.is_admin():
        if project.owner_id != current_user.id:
            raise HTTPException(403, "Access denied")

    try:
        branches = await project_service.get_git_branches(project_id)
        return {"code": 200, "data": {"branches": branches}}
    except Exception as e:
        raise HTTPException(500, f"Failed to get git branches: {str(e)}")


@router.get("/{project_id}/git/commits", tags=["Projects"])
async def get_git_commits(
    project_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    # Check access permission
    if current_user and not current_user.is_admin():
        if project.owner_id != current_user.id:
            raise HTTPException(403, "Access denied")

    try:
        commits = await project_service.get_git_commits(project_id, limit)
        return {"code": 200, "data": {"commits": commits}}
    except Exception as e:
        raise HTTPException(500, f"Failed to get git commits: {str(e)}")


# Checkout git commit endpoint that accepts commit_hash in request body
class CheckoutRequest(BaseModel):
    commit_hash: str


@router.post("/{project_id}/git/checkout", tags=["Projects"])
async def checkout_git_version(
    project_id: str,
    request: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    # Check access permission
    if current_user and not current_user.is_admin():
        if project.owner_id != current_user.id:
            raise HTTPException(403, "Access denied")

    try:
        success = await project_service.checkout_git_version(project_id, request.commit_hash)
        return {"code": 200, "data": {"success": success}}
    except Exception as e:
        raise HTTPException(500, f"Failed to checkout git version: {str(e)}")
