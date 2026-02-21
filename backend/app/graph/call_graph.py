from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional
from collections import defaultdict

from app.parsers.base import ParseResult, FunctionInfo, ClassInfo


@dataclass(frozen=True)
class CallNode:
    id: str
    name: str
    file_path: str
    line: int
    type: str
    class_name: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "file_path": self.file_path,
            "line": self.line,
            "type": self.type,
            "class_name": self.class_name,
        }


@dataclass(frozen=True)
class CallEdge:
    caller: str
    callee: str
    line: int
    file_path: str

    def to_dict(self) -> Dict:
        return {
            "caller": self.caller,
            "callee": self.callee,
            "line": self.line,
            "file_path": self.file_path,
        }


@dataclass
class CallGraph:
    nodes: Dict[str, CallNode] = field(default_factory=dict)
    edges: List[CallEdge] = field(default_factory=list)
    entry_points: List[str] = field(default_factory=list)
    leaf_functions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "edges": [e.to_dict() for e in self.edges],
            "entry_points": self.entry_points,
            "leaf_functions": self.leaf_functions,
            "stats": {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "entry_points": len(self.entry_points),
                "leaf_functions": len(self.leaf_functions),
            },
        }


class CallGraphBuilder:
    def __init__(self):
        self.nodes: Dict[str, CallNode] = {}
        self.edges: List[CallEdge] = []
        self._defined_functions: Dict[str, CallNode] = {}
        self._function_by_file: Dict[str, List[str]] = defaultdict(list)
        self._callers: Dict[str, Set[str]] = defaultdict(set)
        self._callees: Dict[str, Set[str]] = defaultdict(set)

    def build(self, parse_results: List[ParseResult]) -> CallGraph:
        self.nodes = {}
        self.edges = []
        self._defined_functions = {}
        self._function_by_file = defaultdict(list)
        self._callers = defaultdict(set)
        self._callees = defaultdict(set)

        for result in parse_results:
            self._collect_functions(result)

        for result in parse_results:
            self._analyze_calls(result)

        entry_points = self._find_entry_points()
        leaf_functions = self._find_leaf_functions()

        return CallGraph(
            nodes=self.nodes,
            edges=self.edges,
            entry_points=entry_points,
            leaf_functions=leaf_functions,
        )

    def _collect_functions(self, result: ParseResult):
        file_path = result.file_path

        for func in result.functions:
            if func.is_method:
                continue

            node_id = f"{file_path}:{func.name}"
            node = CallNode(
                id=node_id,
                name=func.name,
                file_path=file_path,
                line=func.start_line,
                type="function",
            )
            self.nodes[node_id] = node
            self._defined_functions[func.name] = node
            self._function_by_file[file_path].append(node_id)

        for cls in result.classes:
            for method in cls.methods:
                method_name = f"{cls.name}.{method.name}"
                node_id = f"{file_path}:{method_name}"
                node = CallNode(
                    id=node_id,
                    name=method.name,
                    file_path=file_path,
                    line=method.start_line,
                    type="method",
                    class_name=cls.name,
                )
                self.nodes[node_id] = node
                self._defined_functions[method_name] = node
                self._function_by_file[file_path].append(node_id)

    def _analyze_calls(self, result: ParseResult):
        file_path = result.file_path

        for call in result.calls:
            if not call.caller:
                continue

            caller_id = self._find_caller_id(call.caller, file_path)
            if not caller_id:
                continue

            callee_node = self._resolve_callee(call.callee, file_path)
            if callee_node:
                edge = CallEdge(
                    caller=caller_id,
                    callee=callee_node.id,
                    line=call.line,
                    file_path=file_path,
                )
                self.edges.append(edge)
                self._callers[callee_node.id].add(caller_id)
                self._callees[caller_id].add(callee_node.id)

    def _find_caller_id(self, caller_name: str, file_path: str) -> Optional[str]:
        if "." in caller_name:
            node_id = f"{file_path}:{caller_name}"
            if node_id in self.nodes:
                return node_id

        for node_id in self._function_by_file.get(file_path, []):
            node = self.nodes.get(node_id)
            if node and node.name == caller_name:
                return node_id

        if caller_name in self._defined_functions:
            return self._defined_functions[caller_name].id

        return None

    def _resolve_callee(self, callee_name: str, file_path: str) -> Optional[CallNode]:
        if "." in callee_name:
            parts = callee_name.split(".", 1)
            class_name = parts[0]
            method_name = parts[1]
            method_full_name = f"{class_name}.{method_name}"

            if method_full_name in self._defined_functions:
                return self._defined_functions[method_full_name]

        if callee_name in self._defined_functions:
            return self._defined_functions[callee_name]

        return None

    def _find_entry_points(self) -> List[str]:
        entry_points = []
        for node_id in self.nodes:
            if node_id not in self._callers or len(self._callers[node_id]) == 0:
                entry_points.append(node_id)
        return entry_points

    def _find_leaf_functions(self) -> List[str]:
        leaf_functions = []
        for node_id in self.nodes:
            if node_id not in self._callees or len(self._callees[node_id]) == 0:
                leaf_functions.append(node_id)
        return leaf_functions

    def get_callers(self, function_id: str) -> List[str]:
        return list(self._callers.get(function_id, set()))

    def get_callees(self, function_id: str) -> List[str]:
        return list(self._callees.get(function_id, set()))

    def get_call_chain(self, function_id: str, depth: int = 5) -> Dict:
        chain = {
            "function": function_id,
            "callers": [],
            "callees": [],
        }

        visited = set()

        def traverse_callers(fid: str, current_depth: int):
            if current_depth >= depth or fid in visited:
                return
            visited.add(fid)

            for caller_id in self._callers.get(fid, set()):
                chain["callers"].append({
                    "id": caller_id,
                    "depth": current_depth,
                })
                traverse_callers(caller_id, current_depth + 1)

        def traverse_callees(fid: str, current_depth: int):
            if current_depth >= depth or fid in visited:
                return
            visited.add(fid)

            for callee_id in self._callees.get(fid, set()):
                chain["callees"].append({
                    "id": callee_id,
                    "depth": current_depth,
                })
                traverse_callees(callee_id, current_depth + 1)

        visited.clear()
        traverse_callers(function_id, 0)
        visited.clear()
        traverse_callees(function_id, 0)

        return chain
