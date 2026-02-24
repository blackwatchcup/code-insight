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
    """Generate architecture diagram from feature tree."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 获取功能树
    structure_service = StructureService()
    feature_tree = structure_service.get_feature_tree(project_id, db)

    if not feature_tree:
        raise HTTPException(status_code=404, detail="Feature tree not found")

    generator = ArchGenerator()
    result = await generator.generate(feature_tree)

    return {"data": result}


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
