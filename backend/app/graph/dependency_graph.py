import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set
from xml.etree import ElementTree as ET

from app.parsers.base import ImportInfo, ParseResult


@dataclass(frozen=True)
class ModuleNode:
    name: str
    file_path: str
    is_external: bool
    version: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "file_path": self.file_path,
            "is_external": self.is_external,
            "version": self.version,
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

        manifest_deps = self._extract_manifest_dependencies()
        for dep, version in manifest_deps.items():
            if not dep or self._is_internal(dep):
                continue
            if dep not in external_modules:
                external_modules[dep] = ModuleNode(
                    name=dep,
                    file_path="",
                    is_external=True,
                    version=version,
                )
            elif version and not external_modules[dep].version:
                external_modules[dep] = ModuleNode(
                    name=dep,
                    file_path="",
                    is_external=True,
                    version=version,
                )

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
        if module.startswith("@") and "/" in module:
            parts = module.split("/")
            if len(parts) >= 2:
                return "/".join(parts[:2])
        return module.split("/")[0] if "/" in module else module

    def _is_internal(self, module: str) -> bool:
        if module in self._internal_modules:
            return True

        for internal in self._internal_modules:
            if internal.startswith(module) or module.startswith(internal):
                return True

        return False

    def _extract_manifest_dependencies(self) -> Dict[str, str]:
        if not self.project_path:
            return {}

        deps: Dict[str, str] = {}

        skip_dirs = {
            ".git",
            "node_modules",
            "dist",
            "build",
            "__pycache__",
            ".venv",
            "venv",
            "target",
            "out",
            "coverage",
        }

        for file_path in self.project_path.rglob("*"):
            if not file_path.is_file():
                continue

            if any(part in skip_dirs for part in file_path.parts):
                continue

            file_name = file_path.name.lower()

            if file_name == "package.json":
                self._merge_dependency_versions(deps, self._extract_from_package_json(file_path))
            elif file_name.startswith("requirements") and file_name.endswith(".txt"):
                self._merge_dependency_versions(deps, self._extract_from_requirements(file_path))
            elif file_name == "pyproject.toml":
                self._merge_dependency_versions(deps, self._extract_from_pyproject(file_path))
            elif file_name == "go.mod":
                self._merge_dependency_versions(deps, self._extract_from_go_mod(file_path))
            elif file_name == "pom.xml":
                self._merge_dependency_versions(deps, self._extract_from_pom_xml(file_path))

        normalized: Dict[str, str] = {}
        for dep, version in deps.items():
            normalized_name = self._normalize_import(dep)
            if not normalized_name:
                continue
            existing = normalized.get(normalized_name)
            if not existing:
                normalized[normalized_name] = version

        return normalized

    def _merge_dependency_versions(self, target: Dict[str, str], incoming: Dict[str, str]):
        for name, version in incoming.items():
            if not name:
                continue
            if name not in target or (version and not target[name]):
                target[name] = version

    def _extract_from_package_json(self, file_path: Path) -> Dict[str, str]:
        deps: Dict[str, str] = {}
        try:
            package_json = json.loads(file_path.read_text(encoding="utf-8", errors="ignore"))
            for key in (
                "dependencies",
                "devDependencies",
                "peerDependencies",
                "optionalDependencies",
            ):
                value = package_json.get(key, {})
                if isinstance(value, dict):
                    for name, ver in value.items():
                        if isinstance(name, str):
                            deps[name.strip()] = str(ver).strip() if ver is not None else ""
        except Exception:
            pass
        return deps

    def _extract_from_requirements(self, file_path: Path) -> Dict[str, str]:
        deps: Dict[str, str] = {}
        try:
            for line in file_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                cleaned = line.strip()
                if not cleaned or cleaned.startswith("#"):
                    continue
                if cleaned.startswith("-r") or cleaned.startswith("--requirement"):
                    continue
                match = re.match(r"^([A-Za-z0-9_.\-]+)(.*)$", cleaned)
                if not match:
                    continue
                pkg = match.group(1).strip()
                version = match.group(2).strip()
                if pkg:
                    deps[pkg] = version
        except Exception:
            pass
        return deps

    def _extract_from_pyproject(self, file_path: Path) -> Dict[str, str]:
        deps: Dict[str, str] = {}
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            matches = re.findall(
                r'"([A-Za-z0-9_.\-]+)(?:\[[^\]]+\])?(\s*[<>=!~].*?)?"',
                text,
            )
            for name, ver in matches:
                if name and name.lower() not in {"python", "setuptools", "wheel"}:
                    deps[name] = (ver or "").strip()
        except Exception:
            pass
        return deps

    def _extract_from_go_mod(self, file_path: Path) -> Dict[str, str]:
        deps: Dict[str, str] = {}
        try:
            for line in file_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                cleaned = line.strip()
                if not cleaned or cleaned.startswith("module ") or cleaned.startswith("go "):
                    continue
                if cleaned.startswith("require "):
                    parts = cleaned.split()
                    if len(parts) >= 3:
                        deps[parts[1].strip()] = parts[2].strip()
                    elif len(parts) >= 2:
                        deps[parts[1].strip()] = ""
        except Exception:
            pass
        return deps

    def _extract_from_pom_xml(self, file_path: Path) -> Dict[str, str]:
        deps: Dict[str, str] = {}
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            ns = ""
            if root.tag.startswith("{"):
                ns = root.tag.split("}")[0] + "}"

            for dep in root.findall(f".//{ns}dependency"):
                artifact = dep.find(f"{ns}artifactId")
                group = dep.find(f"{ns}groupId")
                version = dep.find(f"{ns}version")
                artifact_text = (artifact.text or "").strip() if artifact is not None else ""
                group_text = (group.text or "").strip() if group is not None else ""
                version_text = (version.text or "").strip() if version is not None else ""
                if artifact_text:
                    name = f"{group_text}:{artifact_text}" if group_text else artifact_text
                    deps[name] = version_text
        except Exception:
            pass
        return deps

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
