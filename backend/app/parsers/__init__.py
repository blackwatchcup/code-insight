from app.parsers.base import (
    BaseParser,
    CallInfo,
    ClassInfo,
    FunctionInfo,
    ImportInfo,
    ParameterInfo,
    ParseResult,
    VariableInfo,
)
from app.parsers.factory import ParserFactory
from app.parsers.go_parser import GoParser
from app.parsers.java_parser import JavaParser
from app.parsers.js_parser import JavaScriptParser
from app.parsers.python_parser import PythonParser
from app.parsers.ts_parser import TypeScriptParser

ParserFactory.register("python", PythonParser, extensions=[".py"])
ParserFactory.register("javascript", JavaScriptParser, extensions=[".js", ".jsx", ".mjs", ".cjs"])
ParserFactory.register("typescript", TypeScriptParser, extensions=[".ts", ".tsx", ".mts", ".cts"])
ParserFactory.register("java", JavaParser, extensions=[".java"])
ParserFactory.register("go", GoParser, extensions=[".go"])

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
    "JavaParser",
    "GoParser",
]
