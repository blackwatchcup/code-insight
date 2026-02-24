import pytest

from app.parsers import JavaScriptParser, ParserFactory, PythonParser, TypeScriptParser


class TestParserFactory:
    def test_register_python_parser(self):
        assert "python" in ParserFactory.supported_languages()
        parser = ParserFactory.get_parser("python")
        assert isinstance(parser, PythonParser)

    def test_register_javascript_parser(self):
        assert "javascript" in ParserFactory.supported_languages()
        parser = ParserFactory.get_parser("javascript")
        assert isinstance(parser, JavaScriptParser)

    def test_register_typescript_parser(self):
        assert "typescript" in ParserFactory.supported_languages()
        parser = ParserFactory.get_parser("typescript")
        assert isinstance(parser, TypeScriptParser)

    def test_get_parser_by_extension(self):
        parser = ParserFactory.get_parser_by_extension("py")
        assert parser is not None
        assert parser.get_language() == "python"

        parser = ParserFactory.get_parser_by_extension(".ts")
        assert parser is not None
        assert parser.get_language() == "typescript"

    def test_unsupported_language(self):
        with pytest.raises(ValueError):
            ParserFactory.get_parser("unknown")

    def test_supported_extensions(self):
        extensions = ParserFactory.supported_extensions()
        assert "py" in extensions
        assert "js" in extensions
        assert "ts" in extensions
        assert "tsx" in extensions


class TestPythonParser:
    @pytest.fixture
    def parser(self):
        return PythonParser()

    def test_parse_simple_function(self, parser):
        code = '''
def hello(name: str) -> str:
    """Say hello."""
    return f"Hello, {name}!"
'''
        result = parser.parse(code, "test.py")

        assert result.language == "python"
        assert result.error is None
        assert len(result.functions) == 1
        assert result.functions[0].name == "hello"
        assert result.functions[0].return_type == "str"
        assert len(result.functions[0].parameters) == 1
        assert result.functions[0].parameters[0].name == "name"
        assert result.functions[0].parameters[0].type_annotation == "str"

    def test_parse_class(self, parser):
        code = '''
class Calculator:
    """A simple calculator."""
    
    def __init__(self, value: int = 0):
        self.value = value
    
    def add(self, x: int) -> int:
        return self.value + x
'''
        result = parser.parse(code, "test.py")

        assert len(result.classes) == 1
        assert result.classes[0].name == "Calculator"
        assert len(result.classes[0].methods) == 2
        assert result.classes[0].methods[0].name == "__init__"
        assert result.classes[0].methods[1].name == "add"

    def test_parse_imports(self, parser):
        code = """
import os
from typing import List, Dict
from collections import defaultdict as dd
"""
        result = parser.parse(code, "test.py")

        assert len(result.imports) == 3
        assert result.imports[0].module == "os"
        assert result.imports[1].module == "typing"
        assert "List" in result.imports[1].names
        assert "Dict" in result.imports[1].names

    def test_parse_decorated_function(self, parser):
        code = """
@app.route("/api")
@cache.memoize(timeout=60)
def get_data():
    return {"data": "value"}
"""
        result = parser.parse(code, "test.py")

        assert len(result.functions) == 1
        assert result.functions[0].name == "get_data"
        assert len(result.functions[0].decorators) == 2

    def test_parse_async_function(self, parser):
        code = '''
async def fetch_data(url: str) -> dict:
    """Fetch data from URL."""
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
'''
        result = parser.parse(code, "test.py")

        assert len(result.functions) == 1
        assert result.functions[0].name == "fetch_data"
        assert result.functions[0].is_async is True


class TestJavaScriptParser:
    @pytest.fixture
    def parser(self):
        return JavaScriptParser()

    def test_parse_function(self, parser):
        code = """
function greet(name) {
    return `Hello, ${name}!`;
}
"""
        result = parser.parse(code, "test.js")

        assert result.language == "javascript"
        assert len(result.functions) == 1
        assert result.functions[0].name == "greet"

    def test_parse_arrow_function(self, parser):
        code = """
const add = (a, b) => a + b;
const multiply = (a, b) => {
    return a * b;
};
"""
        result = parser.parse(code, "test.js")

        assert len(result.functions) >= 1

    def test_parse_class(self, parser):
        code = """
class Person {
    constructor(name) {
        this.name = name;
    }
    
    greet() {
        return `Hello, ${this.name}`;
    }
}
"""
        result = parser.parse(code, "test.js")

        assert len(result.classes) == 1
        assert result.classes[0].name == "Person"
        assert len(result.classes[0].methods) >= 1

    def test_parse_imports(self, parser):
        code = """
import React from 'react';
import { useState, useEffect } from 'react';
import * as utils from './utils';
"""
        result = parser.parse(code, "test.js")

        assert len(result.imports) >= 1


class TestTypeScriptParser:
    @pytest.fixture
    def parser(self):
        return TypeScriptParser()

    def test_parse_function_with_types(self, parser):
        code = """
function add(a: number, b: number): number {
    return a + b;
}
"""
        result = parser.parse(code, "test.ts")

        assert result.language == "typescript"
        assert len(result.functions) == 1
        assert result.functions[0].name == "add"
        assert result.functions[0].return_type == "number"

    def test_parse_interface(self, parser):
        code = """
interface User {
    id: number;
    name: string;
    email?: string;
}
"""
        result = parser.parse(code, "test.ts")

        assert len(result.classes) >= 1
        assert result.classes[0].name == "User"

    def test_parse_class_with_types(self, parser):
        code = """
class Calculator {
    private value: number;
    
    constructor(initialValue: number = 0) {
        this.value = initialValue;
    }
    
    add(x: number): number {
        return this.value + x;
    }
}
"""
        result = parser.parse(code, "test.ts")

        assert len(result.classes) == 1
        assert result.classes[0].name == "Calculator"
