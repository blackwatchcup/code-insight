# Phase 2: 代码解析引擎 - 执行计划

**目标**：实现多语言代码解析，提取代码结构、调用关系、依赖关系  
**任务数**：8个  
**预计时间**：1.5周  
**分支**：feature/phase-2-parser  
**依赖**：Phase 1 完成

---

## 任务 2.1：Tree-sitter集成

### 描述
集成Tree-sitter多语言解析器，建立解析器框架。

### 执行步骤

1. 安装依赖
```
# requirements.txt
tree-sitter==0.20.4
```

2. 创建解析器基类 `app/parsers/base.py`
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class FunctionInfo:
    name: str
    start_line: int
    end_line: int
    parameters: List[Dict[str, str]]
    return_type: str
    docstring: str
    body: str

@dataclass
class ClassInfo:
    name: str
    start_line: int
    end_line: int
    methods: List[FunctionInfo]
    attributes: List[Dict[str, str]]
    docstring: str

@dataclass
class ImportInfo:
    module: str
    names: List[str]
    alias: str

@dataclass
class ParseResult:
    file_path: str
    language: str
    functions: List[FunctionInfo]
    classes: List[ClassInfo]
    imports: List[ImportInfo]
    variables: List[Dict[str, Any]]
    raw_ast: Any

class BaseParser(ABC):
    @abstractmethod
    def parse(self, content: str, file_path: str) -> ParseResult:
        pass
    
    @abstractmethod
    def get_language(self) -> str:
        pass
```

3. 创建解析器工厂 `app/parsers/factory.py`
```python
from typing import Dict, Type
from app.parsers.base import BaseParser

class ParserFactory:
    _parsers: Dict[str, Type[BaseParser]] = {}
    
    @classmethod
    def register(cls, language: str, parser_class: Type[BaseParser]):
        cls._parsers[language] = parser_class
    
    @classmethod
    def get_parser(cls, language: str) -> BaseParser:
        if language not in cls._parsers:
            raise ValueError(f"Unsupported language: {language}")
        return cls._parsers[language]()
    
    @classmethod
    def supported_languages(cls) -> list:
        return list(cls._parsers.keys())
```

### 验收标准
- [ ] Tree-sitter正确安装
- [ ] 解析器基类定义完整
- [ ] 工厂模式可用

### 提交信息
```
feat(parser): add tree-sitter integration and parser framework
```

---

## 任务 2.2：Python解析器

### 描述
实现Python语言解析器，提取函数、类、导入等信息。

### 执行步骤

1. 创建Python解析器 `app/parsers/python_parser.py`
```python
import tree_sitter_python as tspython
from tree_sitter import Language, Parser
from app.parsers.base import BaseParser, ParseResult, FunctionInfo, ClassInfo, ImportInfo

class PythonParser(BaseParser):
    def __init__(self):
        self.parser = Parser(Language(tspython.language()))
    
    def get_language(self) -> str:
        return "python"
    
    def parse(self, content: str, file_path: str) -> ParseResult:
        tree = self.parser.parse(bytes(content, "utf8"))
        root = tree.root_node
        
        functions = self._extract_functions(root, content)
        classes = self._extract_classes(root, content)
        imports = self._extract_imports(root, content)
        
        return ParseResult(
            file_path=file_path,
            language="python",
            functions=functions,
            classes=classes,
            imports=imports,
            variables=[],
            raw_ast=tree
        )
    
    def _extract_functions(self, node, content: str) -> list:
        functions = []
        for child in node.children:
            if child.type == "function_definition":
                functions.append(self._parse_function(child, content))
        return functions
    
    def _parse_function(self, node, content: str) -> FunctionInfo:
        name = ""
        for child in node.children:
            if child.type == "identifier":
                name = content[child.start_byte:child.end_byte]
                break
        
        return FunctionInfo(
            name=name,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            parameters=self._extract_parameters(node, content),
            return_type=self._extract_return_type(node, content),
            docstring=self._extract_docstring(node, content),
            body=content[node.start_byte:node.end_byte]
        )
```

2. 注册解析器
```python
# app/parsers/__init__.py
from app.parsers.factory import ParserFactory
from app.parsers.python_parser import PythonParser

ParserFactory.register("python", PythonParser)
ParserFactory.register("py", PythonParser)
```

### 验收标准
- [ ] 可解析Python文件
- [ ] 正确提取函数信息
- [ ] 正确提取类信息
- [ ] 正确提取导入信息

### 提交信息
```
feat(parser): add python language parser
```

---

## 任务 2.3：JavaScript/TS解析器

### 描述
实现JavaScript和TypeScript语言解析器。

### 执行步骤

1. 创建JavaScript解析器 `app/parsers/js_parser.py`
```python
import tree_sitter_javascript as tsjs
import tree_sitter_typescript as tstypescript
from tree_sitter import Language, Parser
from app.parsers.base import BaseParser

class JavaScriptParser(BaseParser):
    def __init__(self):
        self.parser = Parser(Language(tsjs.language()))
    
    def get_language(self) -> str:
        return "javascript"
    
    def parse(self, content: str, file_path: str) -> ParseResult:
        tree = self.parser.parse(bytes(content, "utf8"))
        # 解析逻辑...
        pass

class TypeScriptParser(BaseParser):
    def __init__(self):
        self.parser = Parser(Language(tstypescript.language_typescript()))
    
    def get_language(self) -> str:
        return "typescript"
    
    def parse(self, content: str, file_path: str) -> ParseResult:
        # 解析逻辑，包含类型信息
        pass
```

### 验收标准
- [ ] 可解析JS文件
- [ ] 可解析TS文件
- [ ] 提取ES6+语法特性

### 提交信息
```
feat(parser): add javascript and typescript parsers
```

---

## 任务 2.4：代码结构提取

### 描述
整合解析结果，提供统一的代码结构提取接口。

### 执行步骤

1. 创建结构提取服务 `app/services/structure_service.py`
```python
from pathlib import Path
from typing import List, Dict
from app.parsers.factory import ParserFactory
from app.parsers.base import ParseResult

class StructureService:
    def __init__(self):
        self.extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
        }
    
    async def extract_structure(self, project_path: str) -> Dict:
        project_dir = Path(project_path)
        results = []
        
        for file_path in project_dir.rglob("*"):
            if not file_path.is_file():
                continue
            
            ext = file_path.suffix
            if ext not in self.extension_map:
                continue
            
            language = self.extension_map[ext]
            parser = ParserFactory.get_parser(language)
            
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            result = parser.parse(content, str(file_path))
            results.append(result)
        
        return {
            "files": results,
            "summary": self._create_summary(results)
        }
    
    def _create_summary(self, results: List[ParseResult]) -> Dict:
        return {
            "total_files": len(results),
            "total_functions": sum(len(r.functions) for r in results),
            "total_classes": sum(len(r.classes) for r in results),
            "by_language": self._count_by_language(results)
        }
```

### 验收标准
- [ ] 可遍历项目目录
- [ ] 可提取所有代码结构
- [ ] 生成结构摘要

### 提交信息
```
feat(parser): add code structure extraction service
```

---

## 任务 2.5：调用链分析

### 描述
分析函数调用关系，构建调用图。

### 执行步骤

1. 创建调用图分析器 `app/graph/call_graph.py`
```python
from dataclasses import dataclass
from typing import Dict, List, Set

@dataclass
class CallNode:
    id: str
    name: str
    file_path: str
    line: int
    type: str  # function, method

@dataclass
class CallEdge:
    caller: str
    callee: str

class CallGraphBuilder:
    def __init__(self):
        self.nodes: Dict[str, CallNode] = {}
        self.edges: List[CallEdge] = []
        self._defined_functions: Dict[str, CallNode] = {}
    
    def build(self, parse_results: List[ParseResult]) -> Dict:
        # 第一步：收集所有定义的函数
        for result in parse_results:
            self._collect_functions(result)
        
        # 第二步：分析调用关系
        for result in parse_results:
            self._analyze_calls(result)
        
        return {
            "nodes": self.nodes,
            "edges": self.edges
        }
    
    def _collect_functions(self, result: ParseResult):
        for func in result.functions:
            node = CallNode(
                id=f"{result.file_path}:{func.name}",
                name=func.name,
                file_path=result.file_path,
                line=func.start_line,
                type="function"
            )
            self.nodes[node.id] = node
            self._defined_functions[func.name] = node
        
        for cls in result.classes:
            for method in cls.methods:
                node = CallNode(
                    id=f"{result.file_path}:{cls.name}.{method.name}",
                    name=f"{cls.name}.{method.name}",
                    file_path=result.file_path,
                    line=method.start_line,
                    type="method"
                )
                self.nodes[node.id] = node
    
    def _analyze_calls(self, result: ParseResult):
        # 通过AST分析调用表达式
        pass
```

### 验收标准
- [ ] 可识别函数调用
- [ ] 可构建调用图
- [ ] 支持可视化输出

### 提交信息
```
feat(graph): add call graph analysis module
```

---

## 任务 2.6：依赖分析

### 描述
分析模块/包的依赖关系。

### 执行步骤

1. 创建依赖分析器 `app/graph/dependency_graph.py`
```python
from typing import Dict, List, Set
from collections import defaultdict

class DependencyAnalyzer:
    def analyze(self, parse_results: List[ParseResult]) -> Dict:
        # 模块依赖图
        module_deps: Dict[str, Set[str]] = defaultdict(set)
        # 外部依赖
        external_deps: Dict[str, Set[str]] = defaultdict(set)
        
        for result in parse_results:
            module = self._get_module_name(result.file_path)
            
            for imp in result.imports:
                if self._is_internal(imp.module):
                    module_deps[module].add(imp.module)
                else:
                    external_deps[module].add(imp.module)
        
        return {
            "internal": {k: list(v) for k, v in module_deps.items()},
            "external": {k: list(v) for k, v in external_deps.items()}
        }
```

### 验收标准
- [ ] 可分析import依赖
- [ ] 区分内部/外部依赖
- [ ] 生成依赖图

### 提交信息
```
feat(graph): add dependency analysis module
```

---

## 任务 2.7：增量索引

### 描述
实现文件变更检测与增量更新索引。

### 执行步骤

1. 创建增量索引服务 `app/services/incremental_index.py`
```python
import hashlib
from pathlib import Path
from typing import Dict, List

class IncrementalIndexer:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.hash_file = self.project_path / ".codeinsight" / "file_hashes.json"
        self.hashes: Dict[str, str] = self._load_hashes()
    
    def detect_changes(self) -> Dict[str, List[str]]:
        current_hashes = {}
        changes = {
            "added": [],
            "modified": [],
            "deleted": []
        }
        
        for file_path in self.project_path.rglob("*"):
            if not self._should_process(file_path):
                continue
            
            rel_path = str(file_path.relative_to(self.project_path))
            file_hash = self._compute_hash(file_path)
            current_hashes[rel_path] = file_hash
            
            if rel_path not in self.hashes:
                changes["added"].append(rel_path)
            elif self.hashes[rel_path] != file_hash:
                changes["modified"].append(rel_path)
        
        for old_path in self.hashes:
            if old_path not in current_hashes:
                changes["deleted"].append(old_path)
        
        self.hashes = current_hashes
        self._save_hashes()
        
        return changes
    
    def _compute_hash(self, file_path: Path) -> str:
        content = file_path.read_bytes()
        return hashlib.md5(content).hexdigest()
```

### 验收标准
- [ ] 可检测新增文件
- [ ] 可检测修改文件
- [ ] 可检测删除文件

### 提交信息
```
feat(parser): add incremental indexing support
```

---

## 任务 2.8：解析进度与日志

### 描述
实现解析过程的进度反馈和日志记录。

### 执行步骤

1. 创建进度追踪 `app/services/parse_progress.py`
```python
from dataclasses import dataclass
from typing import Optional
from app.core.websocket import manager

@dataclass
class ParseProgress:
    stage: str
    current: int
    total: int
    message: str
    
    @property
    def percentage(self) -> int:
        return int(self.current / self.total * 100) if self.total > 0 else 0

class ProgressTracker:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.progress: Optional[ParseProgress] = None
    
    async def update(self, stage: str, current: int, total: int, message: str):
        self.progress = ParseProgress(stage, current, total, message)
        
        await manager.send_progress(
            self.project_id,
            stage,
            self.progress.percentage,
            message
        )
```

### 验收标准
- [ ] 进度可实时更新
- [ ] WebSocket可推送进度
- [ ] 日志正确记录

### 提交信息
```
feat(parser): add parsing progress tracking and logging
```

---

## Phase 2 完成标准

- [ ] Python解析器可用
- [ ] JavaScript/TS解析器可用
- [ ] 代码结构正确提取
- [ ] 调用图可构建
- [ ] 依赖关系可分析
- [ ] 增量索引可工作
- [ ] 解析进度可追踪

## 下一阶段

完成 Phase 2 后，进入 Phase 3: 功能分析模块
