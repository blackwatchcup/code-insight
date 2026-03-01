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

# 注册解析器，添加错误处理
try:
    ParserFactory.register("python", PythonParser, extensions=[".py"])
except Exception as e:
    print(f"Warning: Failed to register Python parser: {e}")

try:
    ParserFactory.register("javascript", JavaScriptParser, extensions=[".js", ".jsx", ".mjs", ".cjs"])
except Exception as e:
    print(f"Warning: Failed to register JavaScript parser: {e}")

try:
    ParserFactory.register("typescript", TypeScriptParser, extensions=[".ts", ".tsx", ".mts", ".cts"])
except Exception as e:
    print(f"Warning: Failed to register TypeScript parser: {e}")

try:
    ParserFactory.register("java", JavaParser, extensions=[".java"])
except Exception as e:
    print(f"Warning: Failed to register Java parser: {e}")

try:
    ParserFactory.register("go", GoParser, extensions=[".go"])
except Exception as e:
    print(f"Warning: Failed to register Go parser: {e}")

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
