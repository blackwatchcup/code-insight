from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

from app.parsers.base import ImportInfo, ParseResult


@dataclass(frozen=True)
class ModuleNode:
    name: str
    file_path: str
    is_external: bool

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "file_path": self.file_path,
            "is_external": self.is_external,
        }


@dataclass(frozen=True)
class DependencyEdge:
    source: str
    target: str
    imports: List[str]
    is_external: bool

    def to_dict(self) -> Dict:
        return {
            "source": self.source,
            "target": self.target,
            "imports": self.imports,
            "is_external": self.is_external,
        }


@dataclass
class DependencyGraph:
    internal_modules: Dict[str, ModuleNode] = field(default_factory=dict)
    external_modules: Dict[str, ModuleNode] = field(default_factory=dict)
    internal_edges: List[DependencyEdge] = field(default_factory=list)
    external_edges: List[DependencyEdge] = field(default_factory=list)
    module_imports: Dict[str, List[str]] = field(default_factory=dict)
    module_imported_by: Dict[str, List[str]] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "internal_modules": {k: v.to_dict() for k, v in self.internal_modules.items()},
            "external_modules": {k: v.to_dict() for k, v in self.external_modules.items()},
            "internal_edges": [e.to_dict() for e in self.internal_edges],
            "external_edges": [e.to_dict() for e in self.external_edges],
            "stats": {
                "internal_modules": len(self.internal_modules),
                "external_modules": len(self.external_modules),
                "internal_edges": len(self.internal_edges),
                "external_edges": len(self.external_edges),
            },
        }


class DependencyAnalyzer:
    def __init__(self, project_path: str = ""):
        self.project_path = Path(project_path) if project_path else None
        self._internal_modules: Set[str] = set()
        self._module_file_map: Dict[str, str] = {}

    def analyze(self, parse_results: List[ParseResult], project_path: str = "") -> DependencyGraph:
        self.project_path = Path(project_path) if project_path else self.project_path
        self._internal_modules = set()
        self._module_file_map = {}

        internal_modules: Dict[str, ModuleNode] = {}
        external_modules: Dict[str, ModuleNode] = {}
        internal_edges: List[DependencyEdge] = []
        external_edges: List[DependencyEdge] = []
        module_imports: Dict[str, List[str]] = defaultdict(list)
        module_imported_by: Dict[str, List[str]] = defaultdict(list)

        for result in parse_results:
            module_name = self._get_module_name(result.file_path)
            self._internal_modules.add(module_name)
            self._module_file_map[module_name] = result.file_path

            internal_modules[module_name] = ModuleNode(
                name=module_name,
                file_path=result.file_path,
                is_external=False,
            )

        for result in parse_results:
            source_module = self._get_module_name(result.file_path)

            for imp in result.imports:
                target_module = self._normalize_import(imp.module)
                is_external = not self._is_internal(target_module)

                if is_external:
                    if target_module not in external_modules:
                        external_modules[target_module] = ModuleNode(
                            name=target_module,
                            file_path="",
                            is_external=True,
                        )

                    edge = DependencyEdge(
                        source=source_module,
                        target=target_module,
                        imports=imp.names,
                        is_external=True,
                    )
                    external_edges.append(edge)
                    module_imports[source_module].append(target_module)
                    module_imported_by[target_module].append(source_module)
                else:
                    edge = DependencyEdge(
                        source=source_module,
                        target=target_module,
                        imports=imp.names,
                        is_external=False,
                    )
                    internal_edges.append(edge)
                    module_imports[source_module].append(target_module)
                    module_imported_by[target_module].append(source_module)

        return DependencyGraph(
            internal_modules=internal_modules,
            external_modules=external_modules,
            internal_edges=internal_edges,
            external_edges=external_edges,
            module_imports=dict(module_imports),
            module_imported_by=dict(module_imported_by),
        )

    def _get_module_name(self, file_path: str) -> str:
        path = Path(file_path)

        if self.project_path:
            try:
                rel_path = path.relative_to(self.project_path)
                parts = list(rel_path.parts)

                if parts and parts[-1] in ("__init__.py", "__init__.ts", "__init__.js"):
                    parts = parts[:-1]
                elif parts:
                    parts[-1] = parts[-1].rsplit(".", 1)[0]

                return ".".join(parts)
            except ValueError:
                pass

        name = path.stem
        if name in ("__init__", "index"):
            name = path.parent.name
        return name

    def _normalize_import(self, module: str) -> str:
        module = module.lstrip(".")
        module = module.lstrip("/")
        return module.split("/")[0] if "/" in module else module

    def _is_internal(self, module: str) -> bool:
        if module in self._internal_modules:
            return True

        for internal in self._internal_modules:
            if internal.startswith(module) or module.startswith(internal):
                return True

        return False

    def get_imports(self, module: str) -> List[str]:
        return list(self._module_imports.get(module, []))

    def get_imported_by(self, module: str) -> List[str]:
        return list(self._module_imported_by.get(module, []))

    def find_circular_dependencies(self, graph: DependencyGraph) -> List[List[str]]:
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: List[str]):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for edge in graph.internal_edges:
                if edge.source == node:
                    neighbor = edge.target
                    if neighbor not in visited:
                        cycle = dfs(neighbor, path.copy())
                        if cycle:
                            cycles.append(cycle)
                    elif neighbor in rec_stack:
                        cycle_start = path.index(neighbor)
                        cycle = path[cycle_start:] + [neighbor]
                        cycles.append(cycle)

            rec_stack.remove(node)
            return None

        for module in graph.internal_modules:
            if module not in visited:
                dfs(module, [])

        return cycles

    def get_dependency_depth(self, graph: DependencyGraph, module: str) -> int:
        visited = set()

        def dfs(node: str, depth: int) -> int:
            if node in visited:
                return depth
            visited.add(node)

            max_depth = depth
            for edge in graph.internal_edges:
                if edge.source == node:
                    neighbor = edge.target
                    if neighbor in graph.internal_modules:
                        d = dfs(neighbor, depth + 1)
                        max_depth = max(max_depth, d)

            return max_depth

        return dfs(module, 0)

    def get_most_depended_on(self, graph: DependencyGraph, limit: int = 10) -> List[Dict]:
        counts = defaultdict(int)
        for edge in graph.internal_edges:
            counts[edge.target] += 1

        sorted_modules = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [{"module": m, "count": c} for m, c in sorted_modules]

    def get_most_dependent(self, graph: DependencyGraph, limit: int = 10) -> List[Dict]:
        counts = defaultdict(int)
        for edge in graph.internal_edges:
            counts[edge.source] += 1

        sorted_modules = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [{"module": m, "count": c} for m, c in sorted_modules]
