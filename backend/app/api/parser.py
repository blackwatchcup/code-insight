from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.services.structure_service import StructureService
from app.graph.call_graph import CallGraphBuilder
from app.graph.dependency_graph import DependencyAnalyzer
from app.parsers.factory import ParserFactory

router = APIRouter()


class ParseRequest(BaseModel):
    project_id: int
    force: bool = False


class FileParseRequest(BaseModel):
    file_path: str


class StructureResponse(BaseModel):
    project_path: str
    summary: Dict[str, Any]
    files: List[Dict[str, Any]]


structure_service = StructureService()
call_graph_builder = CallGraphBuilder()
dependency_analyzer = DependencyAnalyzer()


@router.get("/languages")
async def get_supported_languages():
    return {
        "languages": ParserFactory.supported_languages(),
        "extensions": ParserFactory.supported_extensions(),
    }


@router.get("/extensions")
async def get_supported_extensions():
    return {
        "extensions": ParserFactory.supported_extensions(),
        "mapping": {
            ext: ParserFactory.get_language_for_extension(ext)
            for ext in ParserFactory.supported_extensions()
        },
    }


@router.post("/file")
async def parse_file(request: FileParseRequest):
    result = structure_service.extract_file_structure(request.file_path)
    
    if result.error:
        raise HTTPException(status_code=400, detail=result.error)
    
    return {"code": 200, "data": result.to_dict()}


@router.get("/project/{project_id}/structure")
async def get_project_structure(project_id: int):
    from app.services.project_service import ProjectService
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        project_service = ProjectService(db)
        project = project_service.get_project(project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        structure = await structure_service.extract_structure(project.local_path)
        
        return {
            "code": 200,
            "data": {
                "project_path": structure.project_path,
                "summary": {
                    "total_files": structure.summary.total_files,
                    "total_functions": structure.summary.total_functions,
                    "total_classes": structure.summary.total_classes,
                    "total_imports": structure.summary.total_imports,
                    "by_language": structure.summary.by_language,
                },
                "files": [f.to_dict() for f in structure.files[:100]],
            },
        }
    finally:
        db.close()


@router.get("/project/{project_id}/call-graph")
async def get_call_graph(project_id: int):
    from app.services.project_service import ProjectService
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        project_service = ProjectService(db)
        project = project_service.get_project(project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        structure = await structure_service.extract_structure(project.local_path)
        call_graph = call_graph_builder.build(structure.files)
        
        return {
            "code": 200,
            "data": call_graph.to_dict(),
        }
    finally:
        db.close()


@router.get("/project/{project_id}/dependencies")
async def get_dependencies(project_id: int):
    from app.services.project_service import ProjectService
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        project_service = ProjectService(db)
        project = project_service.get_project(project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        structure = await structure_service.extract_structure(project.local_path)
        dep_graph = dependency_analyzer.analyze(structure.files, project.local_path)
        
        circular = dependency_analyzer.find_circular_dependencies(dep_graph)
        most_depended = dependency_analyzer.get_most_depended_on(dep_graph)
        most_dependent = dependency_analyzer.get_most_dependent(dep_graph)
        
        return {
            "code": 200,
            "data": {
                "graph": dep_graph.to_dict(),
                "circular_dependencies": circular,
                "most_depended_on": most_depended,
                "most_dependent": most_dependent,
            },
        }
    finally:
        db.close()


@router.get("/project/{project_id}/summary")
async def get_project_summary(project_id: int):
    from app.services.project_service import ProjectService
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        project_service = ProjectService(db)
        project = project_service.get_project(project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        structure = await structure_service.extract_structure(project.local_path)
        
        call_graph = call_graph_builder.build(structure.files)
        dep_graph = dependency_analyzer.analyze(structure.files, project.local_path)
        
        return {
            "code": 200,
            "data": {
                "project_path": structure.project_path,
                "structure": {
                    "total_files": structure.summary.total_files,
                    "total_functions": structure.summary.total_functions,
                    "total_classes": structure.summary.total_classes,
                    "by_language": structure.summary.by_language,
                },
                "call_graph": {
                    "total_nodes": len(call_graph.nodes),
                    "total_edges": len(call_graph.edges),
                    "entry_points": len(call_graph.entry_points),
                    "leaf_functions": len(call_graph.leaf_functions),
                },
                "dependencies": {
                    "internal_modules": len(dep_graph.internal_modules),
                    "external_modules": len(dep_graph.external_modules),
                    "internal_edges": len(dep_graph.internal_edges),
                    "external_edges": len(dep_graph.external_edges),
                },
            },
        }
    finally:
        db.close()
