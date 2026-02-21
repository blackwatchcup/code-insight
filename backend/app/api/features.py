from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from app.services.feature_service import FeatureService
from app.services.project_service import ProjectService
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/{project_id}", tags=["Features"])
async def get_features(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if current_user and not current_user.is_admin():
        if project.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    feature_service = FeatureService(db)
    tree = await feature_service.get_feature_tree(project_id, str(project.local_path))
    
    return {"code": 200, "data": tree.to_dict()}


@router.get("/{project_id}/summary", tags=["Features"])
async def get_feature_summary(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if current_user and not current_user.is_admin():
        if project.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    feature_service = FeatureService(db)
    tree = await feature_service.get_feature_tree(project_id, str(project.local_path))
    
    return {"code": 200, "data": tree.get_summary()}


@router.get("/{project_id}/frontend", tags=["Features"])
async def get_frontend_features(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if current_user and not current_user.is_admin():
        if project.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    feature_service = FeatureService(db)
    features = await feature_service.get_frontend_features(str(project.local_path))
    
    return {"code": 200, "data": features}


@router.get("/{project_id}/backend", tags=["Features"])
async def get_backend_features(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if current_user and not current_user.is_admin():
        if project.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    feature_service = FeatureService(db)
    features = await feature_service.get_backend_features(str(project.local_path))
    
    return {"code": 200, "data": features}


@router.get("/{project_id}/apis", tags=["Features"])
async def get_api_endpoints(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if current_user and not current_user.is_admin():
        if project.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    feature_service = FeatureService(db)
    apis = await feature_service.get_api_endpoints(str(project.local_path))
    
    return {"code": 200, "data": apis}


@router.get("/{project_id}/models", tags=["Features"])
async def get_data_models(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if current_user and not current_user.is_admin():
        if project.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    feature_service = FeatureService(db)
    models = await feature_service.get_data_models(str(project.local_path))
    
    return {"code": 200, "data": models}


@router.get("/{project_id}/system", tags=["Features"])
async def get_system_features(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if current_user and not current_user.is_admin():
        if project.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    feature_service = FeatureService(db)
    features = await feature_service.get_system_features(str(project.local_path))
    
    return {"code": 200, "data": features}
