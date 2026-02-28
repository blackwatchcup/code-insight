from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.version_service import VersionService

router = APIRouter()


class CreateVersionRequest(BaseModel):
    version_number: str
    description: Optional[str] = None
    commit_hash: Optional[str] = None


class CompareVersionsRequest(BaseModel):
    version_id_1: str
    version_id_2: str


@router.post("/{project_id}/versions", tags=["Versions"])
async def create_version(
    project_id: str,
    request: CreateVersionRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Create a new version snapshot for a project."""
    version_service = VersionService(db)
    owner_id = current_user.id if current_user else None

    try:
        version = version_service.create_version(
            project_id=project_id,
            version_number=request.version_number,
            description=request.description,
            commit_hash=request.commit_hash,
            created_by=owner_id,
        )
        return {"code": 200, "data": version.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{project_id}/versions", tags=["Versions"])
async def list_versions(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """List all versions for a project."""
    version_service = VersionService(db)
    versions = version_service.list_versions(project_id)
    return {"code": 200, "data": [v.to_dict() for v in versions]}


@router.get("/{project_id}/versions/{version_id}", tags=["Versions"])
async def get_version(
    project_id: str,
    version_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Get a specific version by ID."""
    version_service = VersionService(db)
    version = version_service.get_version(version_id)

    if not version or version.project_id != project_id:
        raise HTTPException(status_code=404, detail="Version not found")

    return {"code": 200, "data": version.to_dict()}


@router.delete("/{project_id}/versions/{version_id}", tags=["Versions"])
async def delete_version(
    project_id: str,
    version_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Delete a version."""
    version_service = VersionService(db)
    version = version_service.get_version(version_id)

    if not version or version.project_id != project_id:
        raise HTTPException(status_code=404, detail="Version not found")

    success = version_service.delete_version(version_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete version")

    return {"code": 200, "data": {"message": "Version deleted"}}


@router.post("/{project_id}/versions/compare", tags=["Versions"])
async def compare_versions(
    project_id: str,
    request: CompareVersionsRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Compare two versions of a project."""
    version_service = VersionService(db)

    try:
        diff = version_service.compare_versions(
            project_id=project_id,
            version_id_1=request.version_id_1,
            version_id_2=request.version_id_2,
        )
        return {"code": 200, "data": diff}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class CreateVersionFromGitRequest(BaseModel):
    commit_hash: str
    version_number: str
    description: Optional[str] = None
    created_by: Optional[str] = None


class CompareGitVersionsRequest(BaseModel):
    commit_hash_1: str
    commit_hash_2: str


@router.post("/{project_id}/versions/from-git", tags=["Versions"])
async def create_version_from_git(
    project_id: str,
    request: CreateVersionFromGitRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Create a version from a specific git commit."""
    version_service = VersionService(db)
    owner_id = current_user.id if current_user else None

    try:
        version = version_service.create_version_from_git_commit(
            project_id=project_id,
            commit_hash=request.commit_hash,
            version_number=request.version_number,
            description=request.description,
            created_by=owner_id,
        )
        return {"code": 200, "data": version.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{project_id}/versions/compare-git", tags=["Versions"])
async def compare_git_versions(
    project_id: str,
    request: CompareGitVersionsRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Compare two git commits of a project."""
    version_service = VersionService(db)

    try:
        diff = version_service.compare_git_versions(
            project_id=project_id,
            commit_hash_1=request.commit_hash_1,
            commit_hash_2=request.commit_hash_2,
        )
        return {"code": 200, "data": diff}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
