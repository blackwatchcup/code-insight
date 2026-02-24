"""Docs API endpoints for documentation generation."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.analysis.api_extractor import APIExtractor
from app.core.database import get_db
from app.docs.api_doc import APIDocGenerator
from app.docs.exporter import DocumentExporter
from app.docs.readme_gen import ReadmeGenerator
from app.models.project import Project
from app.services.structure_service import StructureService

router = APIRouter(prefix="/docs", tags=["docs"])


@router.get("/{project_id}/api")
async def get_api_documentation(project_id: str, db: Session = Depends(get_db)):
    """Generate API documentation."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 获取API端点
    structure_service = StructureService()
    apis = structure_service.get_api_endpoints(project_id, db)

    if not apis:
        raise HTTPException(status_code=404, detail="No API endpoints found")

    # 生成文档
    generator = APIDocGenerator()
    markdown = generator.generate(apis)

    return {"data": {"content": markdown, "type": "markdown"}}


@router.post("/{project_id}/readme")
async def generate_readme(project_id: str, db: Session = Depends(get_db)):
    """Generate README documentation."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 收集项目信息
    project_info = {
        "name": project.name,
        "tech_stack": [],  # 可以从解析结果中提取
        "features": [],  # 可以从功能树中提取
        "structure": "",  # 可以从目录结构生成
    }

    # 从功能树获取功能列表
    structure_service = StructureService()
    feature_tree = structure_service.get_feature_tree(project_id, db)
    if feature_tree:
        # 提取前端功能
        for child in feature_tree.frontend.children:
            project_info["features"].append(f"前端: {child.name}")
        # 提取后端功能
        for child in feature_tree.backend.children:
            project_info["features"].append(f"后端: {child.name}")

    # 生成README
    generator = ReadmeGenerator()
    readme = await generator.generate(project_info)

    return {"data": {"content": readme, "type": "markdown"}}


@router.post("/{project_id}/export")
async def export_document(
    project_id: str,
    doc_type: Literal["api", "readme"],
    format: Literal["markdown", "html"],
    db: Session = Depends(get_db),
):
    """Export documentation to file."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 生成文档内容
    if doc_type == "api":
        structure_service = StructureService()
        apis = structure_service.get_api_endpoints(project_id, db)
        if not apis:
            raise HTTPException(status_code=404, detail="No API endpoints found")

        generator = APIDocGenerator()
        content = generator.generate(apis)
        filename = f"{project.name}_api"
    elif doc_type == "readme":
        project_info = {
            "name": project.name,
            "tech_stack": [],
            "features": [],
            "structure": "",
        }

        structure_service = StructureService()
        feature_tree = structure_service.get_feature_tree(project_id, db)
        if feature_tree:
            for child in feature_tree.frontend.children:
                project_info["features"].append(f"前端: {child.name}")
            for child in feature_tree.backend.children:
                project_info["features"].append(f"后端: {child.name}")

        generator = ReadmeGenerator()
        content = await generator.generate(project_info)
        filename = f"{project.name}_README"
    else:
        raise HTTPException(status_code=400, detail="Invalid document type")

    # 导出文件
    exporter = DocumentExporter(f"output/{project_id}")
    file_path = exporter.export(content, filename, format)

    return {"data": {"file_path": file_path, "format": format}}
