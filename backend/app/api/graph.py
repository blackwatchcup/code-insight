"""Graph API endpoints for visualization."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.analysis.feature_tree import FeatureTree
from app.core.database import get_db
from app.graph.arch_generator import ArchGenerator
from app.graph.call_graph import CallGraphBuilder
from app.graph.call_graph_visualizer import CallGraphVisualizer
from app.graph.flow_generator import FlowGenerator
from app.models.file import File
from app.models.project import Project
from app.services.structure_service import StructureService

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/{project_id}/flow")
async def get_flowchart(
    project_id: str,
    file_path: Optional[str] = None,
    function_name: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Generate a flowchart for a function."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 如果未指定文件，使用第一个解析的文件
    if not file_path:
        file = db.query(File).filter(File.project_id == project_id).first()
        if not file:
            raise HTTPException(status_code=404, detail="No files found in project")
        file_path = file.path

    # 读取文件内容
    from pathlib import Path

    full_path = Path(project.path) / file_path
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    code = full_path.read_text(encoding="utf-8")

    # 检测语言
    language = "python"
    if file_path.endswith((".js", ".jsx", ".ts", ".tsx")):
        language = "javascript"

    generator = FlowGenerator()
    result = await generator.generate_from_function(code, language)

    return {"data": result}


@router.get("/{project_id}/architecture")
async def get_architecture(project_id: str, db: Session = Depends(get_db)):
    """Get architecture diagram from LLM-generated analysis."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 使用LLM生成的架构描述
    architecture = getattr(project, 'architecture', None)
    if architecture:
        # 返回LLM生成的架构描述
        return {
            "data": {
                "type": "architecture",
                "format": "markdown",
                "content": architecture,
                "source": "llm"
            }
        }

    # 如果没有架构信息，返回提示
    return {
        "data": {
            "type": "architecture",
            "format": "text",
            "content": "暂无架构信息。请点击\"重新分析\"按钮触发项目分析，或等待项目导入分析完成。",
            "source": "none"
        }
    }


@router.get("/{project_id}/analysis")
async def get_project_analysis(project_id: str, db: Session = Depends(get_db)):
    """Get complete project analysis including architecture, data flow, APIs, etc."""
    import json
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = {
        "project_id": project_id,
        "project_name": project.name,
        "project_summary": project.project_summary,
        "architecture": getattr(project, 'architecture', None),
        "data_flow": getattr(project, 'data_flow', None),
        "tech_stack": json.loads(project.tech_stack) if project.tech_stack else [],
        "features_detail": None,
        "api_info": None,
        "key_modules": None,
    }

    # 解析JSON字段
    try:
        features_detail = getattr(project, 'features_detail', None)
        if features_detail:
            result["features_detail"] = json.loads(features_detail)
    except (json.JSONDecodeError, TypeError):
        pass

    try:
        api_info = getattr(project, 'api_info', None)
        if api_info:
            result["api_info"] = json.loads(api_info)
    except (json.JSONDecodeError, TypeError):
        pass

    try:
        key_modules = getattr(project, 'key_modules', None)
        if key_modules:
            result["key_modules"] = json.loads(key_modules)
    except (json.JSONDecodeError, TypeError):
        pass

    return {"data": result}

    # 如果都没有，返回提示信息
    return {
        "data": {
            "type": "architecture",
            "format": "text",
            "content": "暂无架构信息。请先导入项目并等待分析完成，或手动触发项目分析。",
            "source": "none"
        }
    }


@router.get("/{project_id}/callgraph")
async def get_call_graph(project_id: str, format: str = "json", db: Session = Depends(get_db)):
    """Get call graph visualization."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 获取解析结果
    structure_service = StructureService()
    parse_results = structure_service.get_parse_results(project_id, db)

    if not parse_results:
        raise HTTPException(status_code=404, detail="No parse results found")

    # 构建调用图
    builder = CallGraphBuilder()
    call_graph = builder.build(parse_results)

    # 可视化
    visualizer = CallGraphVisualizer()
    if format == "mermaid":
        result = {"content": visualizer.to_mermaid(call_graph)}
    elif format == "json":
        result = visualizer.to_json(call_graph)
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use 'json' or 'mermaid'")

    return {"data": result}
