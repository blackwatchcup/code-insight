from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.graph.call_graph import CallGraphBuilder
from app.graph.dependency_graph import DependencyAnalyzer
from app.parsers.factory import ParserFactory
from app.services.structure_service import StructureService

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


def _build_dependency_tree(dep_graph: Any) -> Dict[str, Any]:
    internal_modules = dep_graph.internal_modules
    external_modules = dep_graph.external_modules
    module_imports = dep_graph.module_imports or {}
    module_imported_by = dep_graph.module_imported_by or {}

    internal_names = sorted(internal_modules.keys())
    external_names = sorted(external_modules.keys())

    internal_children: List[Dict[str, Any]] = []
    for module in internal_names:
        imports = sorted(set(module_imports.get(module, [])))
        internal_imports = [name for name in imports if name in internal_modules]
        external_imports = [name for name in imports if name in external_modules]

        children: List[Dict[str, Any]] = []

        if internal_imports:
            children.append(
                {
                    "id": f"group:internal-imports:{module}",
                    "name": "内部依赖",
                    "type": "group",
                    "children": [
                        {
                            "id": f"internal-ref:{module}:{target}",
                            "name": target,
                            "type": "internal_dependency",
                            "children": [],
                        }
                        for target in internal_imports
                    ],
                }
            )

        if external_imports:
            children.append(
                {
                    "id": f"group:external-imports:{module}",
                    "name": "外部依赖",
                    "type": "group",
                    "children": [
                        {
                            "id": f"external-ref:{module}:{target}",
                            "name": target,
                            "type": "external_dependency",
                            "children": [],
                        }
                        for target in external_imports
                    ],
                }
            )

        internal_children.append(
            {
                "id": f"internal:{module}",
                "name": module,
                "type": "internal_module",
                "meta": {
                    "imports_count": len(imports),
                    "internal_imports": len(internal_imports),
                    "external_imports": len(external_imports),
                },
                "children": children,
            }
        )

    external_children: List[Dict[str, Any]] = []
    for module in external_names:
        imported_by = sorted(set(module_imported_by.get(module, [])))

        external_children.append(
            {
                "id": f"external:{module}",
                "name": module,
                "type": "external_module",
                "meta": {"imported_by_count": len(imported_by)},
                "children": [
                    {
                        "id": f"used-by:{module}",
                        "name": "被内部模块引用",
                        "type": "group",
                        "children": [
                            {
                                "id": f"used-by:{module}:{source}",
                                "name": source,
                                "type": "used_by_module",
                                "children": [],
                            }
                            for source in imported_by
                        ],
                    }
                ]
                if imported_by
                else [],
            }
        )

    return {
        "id": "dependency-root",
        "name": "依赖关系",
        "type": "root",
        "meta": {
            "internal_modules": len(internal_names),
            "external_modules": len(external_names),
        },
        "children": [
            {
                "id": "group:internal",
                "name": "内部模块",
                "type": "group",
                "meta": {"count": len(internal_names)},
                "children": internal_children,
            },
            {
                "id": "group:external",
                "name": "外部依赖",
                "type": "group",
                "meta": {"count": len(external_names)},
                "children": external_children,
            },
        ],
    }


@router.get("/languages", tags=["Parser"])
async def get_supported_languages():
    return {
        "languages": ParserFactory.supported_languages(),
        "extensions": ParserFactory.supported_extensions(),
    }


@router.get("/extensions", tags=["Parser"])
async def get_supported_extensions():
    return {
        "extensions": ParserFactory.supported_extensions(),
        "mapping": {
            ext: ParserFactory.get_language_for_extension(ext)
            for ext in ParserFactory.supported_extensions()
        },
    }


@router.post("/file", tags=["Parser"])
async def parse_file(request: FileParseRequest):
    result = structure_service.extract_file_structure(request.file_path)

    if result.error:
        raise HTTPException(status_code=400, detail=result.error)

    return {"code": 200, "data": result.to_dict()}


@router.get("/project/{project_id}/structure", tags=["Parser"])
async def get_project_structure(project_id: str):
    from app.core.database import SessionLocal
    from app.services.project_service import ProjectService

    db = SessionLocal()
    try:
        project_service = ProjectService(db)
        project = project_service.get_project(project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        structure = await structure_service.extract_structure(str(project.local_path))

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


@router.get("/project/{project_id}/call-graph", tags=["Parser"])
async def get_call_graph(project_id: str):
    from app.core.database import SessionLocal
    from app.services.project_service import ProjectService

    db = SessionLocal()
    try:
        project_service = ProjectService(db)
        project = project_service.get_project(project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        structure = await structure_service.extract_structure(str(project.local_path))
        call_graph = call_graph_builder.build(structure.files)

        return {
            "code": 200,
            "data": call_graph.to_dict(),
        }
    finally:
        db.close()


@router.get("/project/{project_id}/dependencies", tags=["Parser"])
async def get_dependencies(project_id: str):
    from app.core.database import SessionLocal
    from app.services.project_service import ProjectService

    db = SessionLocal()
    try:
        project_service = ProjectService(db)
        project = project_service.get_project(project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        structure = await structure_service.extract_structure(str(project.local_path))
        dep_graph = dependency_analyzer.analyze(structure.files, str(project.local_path))

        circular = dependency_analyzer.find_circular_dependencies(dep_graph)
        most_depended = dependency_analyzer.get_most_depended_on(dep_graph)
        most_dependent = dependency_analyzer.get_most_dependent(dep_graph)

        return {
            "code": 200,
            "data": {
                "graph": dep_graph.to_dict(),
                "dependency_tree": _build_dependency_tree(dep_graph),
                "circular_dependencies": circular,
                "most_depended_on": most_depended,
                "most_dependent": most_dependent,
            },
        }
    finally:
        db.close()


@router.get("/project/{project_id}/summary", tags=["Parser"])
async def get_project_summary(project_id: str):
    from app.core.database import SessionLocal
    from app.services.project_service import ProjectService

    db = SessionLocal()
    try:
        project_service = ProjectService(db)
        project = project_service.get_project(project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        structure = await structure_service.extract_structure(str(project.local_path))

        call_graph = call_graph_builder.build(structure.files)
        dep_graph = dependency_analyzer.analyze(structure.files, str(project.local_path))

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
