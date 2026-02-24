from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ParameterInfo:
    name: str
    type_annotation: str = ""
    default_value: str = ""


@dataclass(frozen=True)
class FunctionInfo:
    name: str
    start_line: int
    end_line: int
    parameters: List[ParameterInfo] = field(default_factory=list)
    return_type: str = ""
    docstring: str = ""
    body: str = ""
    decorators: List[str] = field(default_factory=list)
    is_async: bool = False
    is_method: bool = False


@dataclass(frozen=True)
class ClassInfo:
    name: str
    start_line: int
    end_line: int
    methods: List[FunctionInfo] = field(default_factory=list)
    attributes: List[Dict[str, str]] = field(default_factory=list)
    docstring: str = ""
    base_classes: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ImportInfo:
    module: str
    names: List[str] = field(default_factory=list)
    alias: str = ""
    is_from_import: bool = True


@dataclass(frozen=True)
class VariableInfo:
    name: str
    type_annotation: str = ""
    value: str = ""
    line: int = 0
    scope: str = "module"


@dataclass(frozen=True)
class CallInfo:
    caller: str
    callee: str
    line: int
    arguments: List[str] = field(default_factory=list)


@dataclass
class ParseResult:
    file_path: str
    language: str
    functions: List[FunctionInfo] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)
    imports: List[ImportInfo] = field(default_factory=list)
    variables: List[VariableInfo] = field(default_factory=list)
    calls: List[CallInfo] = field(default_factory=list)
    raw_ast: Any = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "language": self.language,
            "functions": [
                {
                    "name": f.name,
                    "start_line": f.start_line,
                    "end_line": f.end_line,
                    "parameters": [
                        {"name": p.name, "type": p.type_annotation, "default": p.default_value}
                        for p in f.parameters
                    ],
                    "return_type": f.return_type,
                    "docstring": f.docstring,
                    "is_async": f.is_async,
                    "is_method": f.is_method,
                }
                for f in self.functions
            ],
            "classes": [
                {
                    "name": c.name,
                    "start_line": c.start_line,
                    "end_line": c.end_line,
                    "methods": [
                        {"name": m.name, "start_line": m.start_line, "end_line": m.end_line}
                        for m in c.methods
                    ],
                    "base_classes": c.base_classes,
                    "docstring": c.docstring,
                }
                for c in self.classes
            ],
            "imports": [
                {
                    "module": i.module,
                    "names": i.names,
                    "alias": i.alias,
                    "is_from_import": i.is_from_import,
                }
                for i in self.imports
            ],
            "variables": [
                {"name": v.name, "type": v.type_annotation, "line": v.line} for v in self.variables
            ],
            "calls": [{"caller": c.caller, "callee": c.callee, "line": c.line} for c in self.calls],
            "error": self.error,
        }


class BaseParser(ABC):
    @abstractmethod
    def parse(self, content: str, file_path: str) -> ParseResult:
        pass

    @abstractmethod
    def get_language(self) -> str:
        pass

    def get_supported_extensions(self) -> List[str]:
        return []

    def can_parse(self, file_path: str) -> bool:
        ext = file_path.rsplit(".", 1)[-1] if "." in file_path else ""
        return ext.lower() in [e.lstrip(".") for e in self.get_supported_extensions()]
