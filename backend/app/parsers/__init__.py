from app.parsers.factory import ParserFactory
from app.parsers.base import (
    BaseParser,
    ParseResult,
    FunctionInfo,
    ClassInfo,
    ImportInfo,
    VariableInfo,
    ParameterInfo,
    CallInfo,
)
from app.parsers.python_parser import PythonParser
from app.parsers.js_parser import JavaScriptParser
from app.parsers.ts_parser import TypeScriptParser

ParserFactory.register("python", PythonParser, extensions=[".py"])
ParserFactory.register("javascript", JavaScriptParser, extensions=[".js", ".jsx", ".mjs", ".cjs"])
ParserFactory.register("typescript", TypeScriptParser, extensions=[".ts", ".tsx", ".mts", ".cts"])

__all__ = [
    "ParserFactory",
    "BaseParser",
    "ParseResult",
    "FunctionInfo",
    "ClassInfo",
    "ImportInfo",
    "VariableInfo",
    "ParameterInfo",
    "CallInfo",
    "PythonParser",
    "JavaScriptParser",
    "TypeScriptParser",
]
