# Phase 6: 优化与完善 - 执行计划

**目标**：扩展语言支持、完善错误处理、补充测试、补充文档、部署验证
**任务数**：6个
**预计时间**：1周
**分支**：feature/phase-6-optimization
**依赖**：Phase 1-5 完成

**当前状态分析**:
- ✅ Phase 1-5 已完成（44/50 任务）
- ⚠️ Java/Go/Rust 解析器已配置但未实现
- ⚠️ 缺少统一的错误处理模块
- ⚠️ 部分核心模块缺少单元测试
- ⚠️ 部署脚本不完善
- ⚠️ 用户使用文档缺失

---

## 任务 6.1：多语言扩展

### 描述
添加Java、Go、Rust等语言解析器。

**当前状态**:
- ✅ 配置文件已支持扩展名 (.java, .go, .rs)
- ❌ Java解析器文件不存在
- ❌ Go解析器文件不存在
- ❌ Rust解析器文件不存在
- ❌ 解析器未注册到工厂

### 执行步骤

#### 步骤 1: 安装 tree-sitter 语言绑定
```bash
cd backend
pip install tree-sitter-java tree-sitter-go tree-sitter-rust
```

#### 步骤 2: 创建Java解析器 `app/parsers/java_parser.py`

参考 PythonParser 的实现结构，创建 JavaParser：

```python
from typing import List
from tree_sitter import Language, Parser
import tree_sitter_java as tsjava
from app.parsers.base import BaseParser, ParseResult, FunctionInfo, ClassInfo

class JavaParser(BaseParser):
    def __init__(self):
        try:
            language = Language(tsjava.language())
            self.parser = Parser(language)
        except Exception as e:
            raise ImportError(f"Failed to initialize Java parser: {e}")

    def get_language(self) -> str:
        return "java"

    def parse(self, content: str, file_path: str) -> ParseResult:
        tree = self.parser.parse(bytes(content, "utf8"))
        root = tree.root_node

        functions = self._extract_methods(root, content)
        classes = self._extract_classes(root, content)
        imports = self._extract_imports(root, content)

        return ParseResult(
            file_path=file_path,
            language="java",
            functions=functions,
            classes=classes,
            imports=imports,
            variables=[],
            raw_ast=tree
        )

    def _extract_methods(self, node, content: str) -> List[FunctionInfo]:
        """提取Java方法声明"""
        methods = []
        for child in node.children:
            if child.type == "method_declaration":
                methods.append(self._parse_method(child, content))
            # 递归处理类内部的方法
            elif child.type == "class_declaration":
                methods.extend(self._extract_methods(child, content))
        return methods

    def _extract_classes(self, node, content: str) -> List[ClassInfo]:
        """提取Java类声明"""
        classes = []
        for child in node.children:
            if child.type == "class_declaration":
                classes.append(self._parse_class(child, content))
        return classes

    def _extract_imports(self, node, content: str) -> List[str]:
        """提取import语句"""
        imports = []
        for child in node.children:
            if child.type == "import_declaration":
                imports.append(content[child.start_byte:child.end_byte].strip())
        return imports

    def _parse_method(self, node, content: str) -> FunctionInfo:
        """解析方法信息"""
        # 实现方法解析逻辑
        return FunctionInfo(
            name="",
            return_type="",
            parameters=[],
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            docstring=""
        )

    def _parse_class(self, node, content: str) -> ClassInfo:
        """解析类信息"""
        # 实现类解析逻辑
        return ClassInfo(
            name="",
            methods=[],
            properties=[],
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            docstring=""
        )
```

#### 步骤 3: 创建Go解析器 `app/parsers/go_parser.py`

```python
from typing import List
from tree_sitter import Language, Parser
import tree_sitter_go as tsgo
from app.parsers.base import BaseParser, ParseResult, FunctionInfo

class GoParser(BaseParser):
    def __init__(self):
        try:
            language = Language(tsgo.language())
            self.parser = Parser(language)
        except Exception as e:
            raise ImportError(f"Failed to initialize Go parser: {e}")

    def get_language(self) -> str:
        return "go"

    def parse(self, content: str, file_path: str) -> ParseResult:
        tree = self.parser.parse(bytes(content, "utf8"))
        root = tree.root_node

        functions = self._extract_functions(root, content)
        classes = []  # Go 没有类，但有 struct
        imports = self._extract_imports(root, content)

        return ParseResult(
            file_path=file_path,
            language="go",
            functions=functions,
            classes=classes,
            imports=imports,
            variables=[],
            raw_ast=tree
        )

    def _extract_functions(self, node, content: str) -> List[FunctionInfo]:
        """提取Go函数"""
        functions = []
        for child in node.children:
            if child.type in ["function_declaration", "method_declaration"]:
                functions.append(self._parse_function(child, content))
        return functions

    def _extract_imports(self, node, content: str) -> List[str]:
        """提取import语句"""
        imports = []
        for child in node.children:
            if child.type == "import_declaration":
                imports.append(content[child.start_byte:child.end_byte].strip())
        return imports

    def _parse_function(self, node, content: str) -> FunctionInfo:
        """解析函数信息"""
        return FunctionInfo(
            name="",
            return_type="",
            parameters=[],
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            docstring=""
        )
```

#### 步骤 4: 注册新解析器

更新 `app/parsers/__init__.py`:

```python
from app.parsers.java_parser import JavaParser
from app.parsers.go_parser import GoParser

# 注册Java解析器
ParserFactory.register("java", JavaParser, extensions=[".java"])

# 注册Go解析器
ParserFactory.register("go", GoParser, extensions=[".go"])
```

### 验收标准
- [ ] Java解析器文件已创建 (`app/parsers/java_parser.py`)
- [ ] Go解析器文件已创建 (`app/parsers/go_parser.py`)
- [ ] Java文件可以正确解析
- [ ] Go文件可以正确解析
- [ ] 解析器已注册到工厂
- [ ] 单元测试通过

### 提交信息
```
feat(parser): add java and go language parsers
```

---

## 任务 6.2：性能优化

### 描述
优化大型代码库的处理性能。

**当前状态**:
- ✅ 已有基础 Embedder 类
- ✅ 已有增量索引服务 `IncrementalIndexer`
- ⚠️ 批量 Embedding 未充分利用
- ⚠️ 缺少并行解析优化
- ⚠️ 向量检索可优化

### 执行步骤

#### 步骤 1: 优化 Embedding 批量处理

更新 `app/rag/embedder.py`，添加批量处理优化：

```python
from typing import List
import asyncio

class CodeEmbedder:
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config or EmbeddingConfig()
        # ... 现有代码 ...

    async def embed_chunks_batch_async(
        self,
        chunks: List[CodeChunk],
        batch_size: int = 50,
        delay: float = 0.1
    ) -> List[List[float]]:
        """异步批量 Embedding，支持限流"""
        results = []

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [chunk.content for chunk in batch]

            # 批量生成
            batch_embeddings = self.embed_batch(texts)
            results.extend(batch_embeddings)

            # 避免API限流
            if i + batch_size < len(chunks):
                await asyncio.sleep(delay)

        return results
```

#### 步骤 2: 优化向量检索性能

更新 `app/rag/retriever.py`：

```python
from typing import List, Optional

class SemanticRetriever:
    def __init__(self, embedder: CodeEmbedder, vector_store):
        self.embedder = embedder
        self.vector_store = vector_store
        self._cache = {}  # 简单的查询缓存

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        project_id: Optional[str] = None,
        min_score: float = 0.5
    ) -> List[RetrievalResult]:
        """带缓存和最小相似度阈值的检索"""
        # 检查缓存
        cache_key = f"{query}:{top_k}:{project_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # 生成查询向量
        query_embedding = self.embedder.embed(query)

        # 检索
        results = self.vector_store.search(
            query_embedding,
            top_k=top_k * 2,  # 获取更多候选
            project_id=project_id
        )

        # 过滤低分结果
        filtered_results = [
            r for r in results
            if r.score >= min_score
        ][:top_k]

        # 缓存结果
        self._cache[cache_key] = filtered_results

        return filtered_results

    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()
```

#### 步骤 3: 添加解析性能监控

创建 `app/services/performance_monitor.py`：

```python
import time
from dataclasses import dataclass
from typing import Dict, Optional
from collections import defaultdict

@dataclass
class PerformanceMetric:
    operation: str
    duration: float
    file_count: int
    timestamp: float

class PerformanceMonitor:
    def __init__(self):
        self._metrics: Dict[str, list] = defaultdict(list)

    def start_operation(self, operation: str) -> str:
        """开始监控一个操作"""
        return f"{operation}_{time.time()}"

    def end_operation(
        self,
        operation_id: str,
        file_count: int = 0
    ) -> PerformanceMetric:
        """结束操作并记录指标"""
        operation = operation_id.rsplit('_', 1)[0]
        end_time = time.time()
        duration = end_time - float(operation_id.rsplit('_', 1)[1])

        metric = PerformanceMetric(
            operation=operation,
            duration=duration,
            file_count=file_count,
            timestamp=end_time
        )

        self._metrics[operation].append(metric)
        return metric

    def get_average_time(self, operation: str) -> Optional[float]:
        """获取平均执行时间"""
        metrics = self._metrics.get(operation, [])
        if not metrics:
            return None
        return sum(m.duration for m in metrics) / len(metrics)

    def get_statistics(self, operation: str) -> Dict:
        """获取详细统计"""
        metrics = self._metrics.get(operation, [])
        if not metrics:
            return {}

        durations = [m.duration for m in metrics]
        file_counts = [m.file_count for m in metrics]

        return {
            "operation": operation,
            "count": len(metrics),
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "total_files": sum(file_counts),
            "avg_files_per_op": sum(file_counts) / len(file_counts) if file_counts else 0
        }

    def get_all_statistics(self) -> Dict:
        """获取所有操作的统计"""
        return {
            op: self.get_statistics(op)
            for op in self._metrics.keys()
        }
```

#### 步骤 4: 优化大型项目解析

更新 `app/services/structure_service.py`，添加内存管理：

```python
class StructureService:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.parser_factory = ParserFactory()
        self.max_memory_files = 100  # 限制同时处理的文件数

    async def parse_project_async(
        self,
        on_progress: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """异步解析项目，支持内存管理"""
        files = self._collect_code_files()
        total_files = len(files)

        results = {
            "files": [],
            "languages": defaultdict(int),
            "total_lines": 0
        }

        # 分批处理
        for i in range(0, total_files, self.max_memory_files):
            batch = files[i:i + self.max_memory_files]

            # 解析批次
            batch_results = await self._parse_batch(batch)

            # 更新结果
            results["files"].extend(batch_results)
            for file_result in batch_results:
                results["languages"][file_result.language] += 1
                results["total_lines"] += file_result.line_count

            # 进度回调
            if on_progress:
                progress = min(100, (i + len(batch)) / total_files * 100)
                on_progress(progress, f"已解析 {i + len(batch)}/{total_files} 文件")

            # 释放内存
            import gc
            gc.collect()

        return results
```

### 验收标准
- [ ] Embedding 批量处理优化完成
- [ ] 向量检索支持缓存和阈值过滤
- [ ] 性能监控模块可用
- [ ] 大型项目解析支持内存管理
- [ ] 性能基准测试通过

### 提交信息
```
perf: optimize embedding, retrieval and parsing performance
```

---

## 任务 6.3：错误处理

### 描述
完善异常捕获和友好提示。

**当前状态**:
- ❌ 缺少统一的自定义异常模块
- ❌ 缺少全局异常处理器
- ⚠️ 各服务模块错误处理不一致
- ⚠️ 缺少详细的错误日志

### 执行步骤

#### 步骤 1: 创建自定义异常模块 `app/core/exceptions.py`

```python
from typing import Optional, Any

class CodeInsightException(Exception):
    """基础异常类"""

    def __init__(
        self,
        message: str,
        code: str = "UNKNOWN_ERROR",
        status_code: int = 400,
        details: Optional[dict] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details
        }


# ========== 项目相关异常 ==========

class ProjectNotFoundError(CodeInsightException):
    """项目不存在"""

    def __init__(self, project_id: str):
        super().__init__(
            message=f"项目不存在: {project_id}",
            code="PROJECT_NOT_FOUND",
            status_code=404,
            details={"project_id": project_id}
        )


class ProjectAlreadyExistsError(CodeInsightException):
    """项目已存在"""

    def __init__(self, project_name: str):
        super().__init__(
            message=f"项目已存在: {project_name}",
            code="PROJECT_ALREADY_EXISTS",
            status_code=409,
            details={"project_name": project_name}
        )


class InvalidProjectSourceError(CodeInsightException):
    """无效的项目来源"""

    def __init__(self, source_type: str, reason: str):
        super().__init__(
            message=f"无效的项目来源: {source_type}",
            code="INVALID_PROJECT_SOURCE",
            status_code=400,
            details={"source_type": source_type, "reason": reason}
        )


# ========== 解析相关异常 ==========

class ParseError(CodeInsightException):
    """代码解析失败"""

    def __init__(self, file_path: str, reason: str, details: Optional[dict] = None):
        super().__init__(
            message=f"解析文件失败: {file_path}",
            code="PARSE_ERROR",
            status_code=400,
            details={"file_path": file_path, "reason": reason, **(details or {})}
        )


class UnsupportedLanguageError(CodeInsightException):
    """不支持的语言"""

    def __init__(self, language: str, file_path: str):
        super().__init__(
            message=f"不支持的语言: {language}",
            code="UNSUPPORTED_LANGUAGE",
            status_code=400,
            details={"language": language, "file_path": file_path}
        )


class UnsupportedFileExtensionError(CodeInsightException):
    """不支持的文件扩展名"""

    def __init__(self, extension: str, file_path: str):
        super().__init__(
            message=f"不支持的文件类型: {extension}",
            code="UNSUPPORTED_EXTENSION",
            status_code=400,
            details={"extension": extension, "file_path": file_path}
        )


# ========== 索引相关异常 ==========

class IndexingError(CodeInsightException):
    """索引错误"""

    def __init__(self, reason: str, project_id: Optional[str] = None):
        super().__init__(
            message=f"索引失败: {reason}",
            code="INDEXING_ERROR",
            status_code=500,
            details={"reason": reason, "project_id": project_id}
        )


class EmbeddingError(CodeInsightException):
    """Embedding 生成错误"""

    def __init__(self, reason: str):
        super().__init__(
            message=f"向量生成失败: {reason}",
            code="EMBEDDING_ERROR",
            status_code=500,
            details={"reason": reason}
        )


# ========== LLM相关异常 ==========

class LLMError(CodeInsightException):
    """LLM 服务错误"""

    def __init__(self, reason: str, model: Optional[str] = None):
        super().__init__(
            message=f"LLM 服务错误: {reason}",
            code="LLM_ERROR",
            status_code=500,
            details={"reason": reason, "model": model}
        )


class LLMRateLimitError(CodeInsightException):
    """LLM API 限流"""

    def __init__(self, model: str):
        super().__init__(
            message=f"LLM API 调用频率超限",
            code="LLM_RATE_LIMIT",
            status_code=429,
            details={"model": model}
        )


class LLMQuotaExceededError(CodeInsightException):
    """LLM 配额用尽"""

    def __init__(self, model: str):
        super().__init__(
            message=f"LLM API 配额已用尽",
            code="LLM_QUOTA_EXCEEDED",
            status_code=429,
            details={"model": model}
        )


# ========== 导入相关异常 ==========

class ImportError(CodeInsightException):
    """项目导入错误"""

    def __init__(self, url: str, reason: str):
        super().__init__(
            message=f"项目导入失败: {reason}",
            code="IMPORT_ERROR",
            status_code=400,
            details={"url": url, "reason": reason}
        )


class CloneError(CodeInsightException):
    """Git 克隆错误"""

    def __init__(self, url: str, reason: str):
        super().__init__(
            message=f"Git 克隆失败: {reason}",
            code="CLONE_ERROR",
            status_code=400,
            details={"url": url, "reason": reason}
        )


class ValidationError(CodeInsightException):
    """验证错误"""

    def __init__(self, field: str, reason: str):
        super().__init__(
            message=f"验证失败: {field} - {reason}",
            code="VALIDATION_ERROR",
            status_code=400,
            details={"field": field, "reason": reason}
        )
```

#### 步骤 2: 创建全局异常处理器 `app/core/error_handler.py`

```python
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import CodeInsightException
from app.core.config import settings

logger = logging.getLogger(__name__)


async def codeinsight_exception_handler(request: Request, exc: CodeInsightException):
    """处理自定义异常"""

    # 记录错误日志
    logger.error(
        f"CodeInsightException: {exc.code} - {exc.message}",
        extra={
            "code": exc.code,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "code": exc.code,
            "message": exc.message,
            "details": exc.details if settings.DEBUG or exc.status_code < 500 else {}
        }
    )


async def http_exception_handler(request: Request, exc):
    """处理 HTTP 异常"""

    status_code = getattr(exc, "status_code", 500)
    detail = getattr(exc, "detail", str(exc))

    logger.warning(
        f"HTTP Exception: {status_code} - {detail}",
        extra={"path": request.url.path, "method": request.method}
    )

    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "code": f"HTTP_{status_code}",
            "message": detail,
            "details": {}
        }
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """处理通用异常"""

    # 记录完整堆栈
    logger.exception(
        f"Unhandled Exception: {type(exc).__name__} - {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method
        }
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "code": "INTERNAL_ERROR",
            "message": "服务器内部错误，请稍后重试",
            "details": {
                "error_type": type(exc).__name__,
                "error": str(exc) if settings.DEBUG else None
            } if settings.DEBUG else {}
        }
    )
```

#### 步骤 3: 注册异常处理器到 `app/main.py`

```python
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.exceptions import CodeInsightException
from app.core.error_handler import (
    codeinsight_exception_handler,
    http_exception_handler,
    generic_exception_handler
)

app = FastAPI(title=settings.APP_NAME, version=settings.VERSION)

# 注册异常处理器
app.add_exception_handler(CodeInsightException, codeinsight_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)
```

#### 步骤 4: 更新各服务模块使用统一异常

示例：更新 `app/services/project_service.py`

```python
from app.core.exceptions import (
    ProjectNotFoundError,
    ProjectAlreadyExistsError,
    InvalidProjectSourceError,
    ValidationError
)

class ProjectService:
    def get_project(self, project_id: str):
        """获取项目"""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ProjectNotFoundError(project_id)
        return project

    def create_project(self, name: str, source_type: str, **kwargs):
        """创建项目"""
        # 验证项目名
        if not name or len(name.strip()) == 0:
            raise ValidationError("name", "项目名不能为空")

        # 检查是否已存在
        existing = self.db.query(Project).filter(Project.name == name).first()
        if existing:
            raise ProjectAlreadyExistsError(name)

        # 验证来源类型
        if source_type not in ["local", "github", "git", "zip"]:
            raise InvalidProjectSourceError(
                source_type,
                "支持的类型: local, github, git, zip"
            )

        # ... 继续创建逻辑
```

### 验收标准
- [ ] 自定义异常模块已创建
- [ ] 全局异常处理器已注册
- [ ] 各服务模块使用统一异常
- [ ] 错误日志记录完整
- [ ] 前端能正确展示错误信息

### 提交信息
```
feat(core): add comprehensive error handling system
```

---

## 任务 6.4：单元测试

### 描述
为核心模块编写单元测试。

**当前状态**:
- ✅ 已有 `test_parsers.py` - 解析器测试完善
- ✅ 已有 `test_rag.py` - RAG模块测试完善
- ✅ 已有 `test_config.py`, `test_auth.py`, `test_projects_api.py` 等
- ❌ 缺少错误处理模块测试
- ❌ 缺少性能监控测试
- ❌ 缺少集成测试
- ⚠️ 测试覆盖率未达标（需要验证）

### 执行步骤

#### 步骤 1: 创建测试配置 `tests/conftest.py`（如不存在）

```python
import pytest
from unittest.mock import Mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# 测试数据库引擎
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def mock_llm_service():
    """Mock LLM 服务"""
    llm = Mock()
    llm.generate = Mock(return_value="Test response")
    return llm


@pytest.fixture
def sample_python_code():
    """示例 Python 代码"""
    return '''
def calculate_sum(a: int, b: int) -> int:
    """Calculate the sum of two numbers."""
    return a + b

class Calculator:
    """Simple calculator class."""

    def __init__(self):
        self.result = 0

    def add(self, x: int) -> None:
        """Add a number to result."""
        self.result += x
'''


@pytest.fixture
def sample_javascript_code():
    """示例 JavaScript 代码"""
    return '''
function greet(name) {
    return `Hello, ${name}!`;
}

class Calculator {
    constructor() {
        this.result = 0;
    }

    add(x) {
        this.result += x;
    }
}
'''
```

#### 步骤 2: 创建错误处理测试 `tests/test_exceptions.py`

```python
import pytest
from app.core.exceptions import (
    CodeInsightException,
    ProjectNotFoundError,
    ProjectAlreadyExistsError,
    ParseError,
    UnsupportedLanguageError,
    LLMError,
    ValidationError
)


class TestCodeInsightException:
    def test_base_exception(self):
        exc = CodeInsightException(message="Test error", code="TEST_ERROR")
        assert exc.message == "Test error"
        assert exc.code == "TEST_ERROR"
        assert exc.status_code == 400

    def test_exception_to_dict(self):
        exc = CodeInsightException(
            message="Test error",
            code="TEST_ERROR",
            details={"field": "test"}
        )
        d = exc.to_dict()
        assert d["message"] == "Test error"
        assert d["code"] == "TEST_ERROR"
        assert d["details"]["field"] == "test"


class TestProjectExceptions:
    def test_project_not_found(self):
        exc = ProjectNotFoundError("proj_123")
        assert exc.code == "PROJECT_NOT_FOUND"
        assert exc.status_code == 404
        assert "proj_123" in exc.message
        assert exc.details["project_id"] == "proj_123"

    def test_project_already_exists(self):
        exc = ProjectAlreadyExistsError("my-project")
        assert exc.code == "PROJECT_ALREADY_EXISTS"
        assert exc.status_code == 409
        assert exc.details["project_name"] == "my-project"


class TestParseExceptions:
    def test_parse_error(self):
        exc = ParseError("test.py", "Syntax error")
        assert exc.code == "PARSE_ERROR"
        assert exc.status_code == 400
        assert "test.py" in exc.message
        assert exc.details["file_path"] == "test.py"
        assert exc.details["reason"] == "Syntax error"

    def test_unsupported_language(self):
        exc = UnsupportedLanguageError("ruby", "test.rb")
        assert exc.code == "UNSUPPORTED_LANGUAGE"
        assert "ruby" in exc.message
        assert exc.details["language"] == "ruby"


class TestValidationExceptions:
    def test_validation_error(self):
        exc = ValidationError("name", "Cannot be empty")
        assert exc.code == "VALIDATION_ERROR"
        assert "name" in exc.message
        assert exc.details["field"] == "name"
        assert exc.details["reason"] == "Cannot be empty"


class TestLLMExceptions:
    def test_llm_error(self):
        exc = LLMError("API timeout", model="gpt-4")
        assert exc.code == "LLM_ERROR"
        assert "API timeout" in exc.message
        assert exc.details["model"] == "gpt-4"
```

#### 步骤 3: 创建性能监控测试 `tests/test_performance.py`

```python
import pytest
import time
from app.services.performance_monitor import PerformanceMonitor, PerformanceMetric


class TestPerformanceMonitor:
    def test_monitor_initialization(self):
        monitor = PerformanceMonitor()
        assert monitor._metrics == {}

    def test_track_operation(self):
        monitor = PerformanceMonitor()

        operation_id = monitor.start_operation("parse")
        time.sleep(0.1)
        metric = monitor.end_operation(operation_id, file_count=10)

        assert isinstance(metric, PerformanceMetric)
        assert metric.operation == "parse"
        assert metric.duration >= 0.1
        assert metric.file_count == 10

    def test_get_average_time(self):
        monitor = PerformanceMonitor()

        for _ in range(3):
            op_id = monitor.start_operation("test")
            metric = monitor.end_operation(op_id, file_count=5)

        avg = monitor.get_average_time("test")
        assert avg is not None
        assert avg > 0

    def test_get_statistics(self):
        monitor = PerformanceMonitor()

        for i in range(3):
            op_id = monitor.start_operation("parse")
            monitor.end_operation(op_id, file_count=10)

        stats = monitor.get_statistics("parse")
        assert stats["operation"] == "parse"
        assert stats["count"] == 3
        assert stats["avg_duration"] > 0
        assert stats["total_files"] == 30

    def test_get_all_statistics(self):
        monitor = PerformanceMonitor()

        monitor.start_operation("parse")
        monitor.end_operation("parse_12345", file_count=10)

        monitor.start_operation("embed")
        monitor.end_operation("embed_12346", file_count=5)

        all_stats = monitor.get_all_statistics()
        assert "parse" in all_stats
        assert "embed" in all_stats
```

#### 步骤 4: 创建集成测试 `tests/test_integration.py`

```python
import pytest
from app.parsers import ParserFactory
from app.services.structure_service import StructureService
from app.rag.embedder import CodeEmbedder
from pathlib import Path


class TestParserIntegration:
    def test_full_parse_workflow(self, sample_python_code):
        """测试完整的解析工作流"""
        parser = ParserFactory.get_parser("python")
        result = parser.parse(sample_python_code, "test.py")

        assert result.language == "python"
        assert len(result.functions) == 1
        assert len(result.classes) == 1

    def test_multi_language_parsing(self, sample_python_code, sample_javascript_code):
        """测试多语言解析"""
        py_parser = ParserFactory.get_parser("python")
        js_parser = ParserFactory.get_parser("javascript")

        py_result = py_parser.parse(sample_python_code, "test.py")
        js_result = js_parser.parse(sample_javascript_code, "test.js")

        assert py_result.language == "python"
        assert js_result.language == "javascript"


class TestEmbeddingIntegration:
    def test_embedder_with_parser(self, sample_python_code):
        """测试 Embedder 与 Parser 集成"""
        parser = ParserFactory.get_parser("python")
        embedder = CodeEmbedder()

        result = parser.parse(sample_python_code, "test.py")

        for func in result.functions:
            embedding = embedder.embed(func.name)
            assert len(embedding) > 0
            assert isinstance(embedding, list)

    def test_batch_embedding_integration(self):
        """测试批量 Embedding"""
        embedder = CodeEmbedder()
        codes = [
            "def func1(): pass",
            "def func2(): pass",
            "class MyClass: pass"
        ]

        embeddings = embedder.embed_batch(codes)

        assert len(embeddings) == 3
        assert all(len(e) > 0 for e in embeddings)


@pytest.mark.integration
class TestFullWorkflow:
    def test_parse_and_embed_workflow(self, sample_python_code):
        """测试从解析到嵌入的完整流程"""
        # 1. 解析
        parser = ParserFactory.get_parser("python")
        parse_result = parser.parse(sample_python_code, "test.py")

        # 2. 提取函数和类
        functions = parse_result.functions
        classes = parse_result.classes

        # 3. 生成 Embedding
        embedder = CodeEmbedder()

        function_embeddings = []
        for func in functions:
            content = f"{func.name}\n{func.docstring}"
            emb = embedder.embed(content)
            function_embeddings.append(emb)

        # 验证
        assert len(function_embeddings) == len(functions)
        assert all(len(e) > 0 for e in function_embeddings)
```

#### 步骤 5: 运行测试并生成覆盖率报告

```bash
cd backend

# 安装覆盖率工具
pip install pytest-cov

# 运行测试并生成覆盖率
pytest --cov=app --cov-report=html --cov-report=term

# 查看详细覆盖率报告
# 打开 htmlcov/index.html
```

### 验收标准
- [ ] 错误处理模块测试已创建 (`tests/test_exceptions.py`)
- [ ] 性能监控测试已创建 (`tests/test_performance.py`)
- [ ] 集成测试已创建 (`tests/test_integration.py`)
- [ ] 所有测试通过 (`pytest` 返回 0)
- [ ] 测试覆盖率 ≥ 70%
- [ ] 关键模块覆盖率 ≥ 80%

### 提交信息
```
test: add comprehensive unit and integration tests
```

---

## 任务 6.5：使用文档

### 描述
编写用户使用说明文档。

**当前状态**:
- ✅ 已有 API 设计文档 (`docs/api-design.md`)
- ✅ 已有架构设计文档 (`docs/architecture.md`)
- ✅ 已有 README.md（基础版）
- ❌ 缺少用户指南
- ❌ 缺少开发者指南
- ⚠️ README 需要更详细

### 执行步骤

#### 步骤 1: 创建用户指南 `docs/user-guide.md`

```markdown
# CodeInsight 用户指南

## 目录

1. [快速开始](#快速开始)
2. [导入项目](#导入项目)
3. [代码问答](#代码问答)
4. [功能分析](#功能分析)
5. [可视化图表](#可视化图表)
6. [文档生成](#文档生成)
7. [常见问题](#常见问题)

---

## 快速开始

### 系统要求

- Docker 20.10+
- Docker Compose 2.0+
- 现代浏览器（Chrome, Firefox, Safari, Edge 最新版）

### 启动服务

```bash
# 克隆仓库
git clone https://github.com/your-org/code-insight.git
cd code-insight

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 访问界面

启动完成后，访问以下地址：

- **前端界面**: http://localhost:3000
- **后端 API**: http://localhost:8000/docs
- **API 文档**: http://localhost:8000/redoc

---

## 导入项目

### 支持的导入方式

CodeInsight 支持三种方式导入代码库：

#### 1. GitHub 仓库

支持公开和私有仓库。

**步骤**:
1. 点击首页的 "导入项目" 按钮
2. 选择 "GitHub URL" 选项
3. 输入仓库地址（如：`https://github.com/user/repo`）
4. （可选）配置分支名称（默认 `main`）
5. （可选）输入访问 Token（私有仓库）
6. 点击 "开始导入"

#### 2. Git 仓库

支持任意 Git 远程仓库。

**步骤**:
1. 选择 "Git URL" 选项
2. 输入仓库地址
3. （可选）配置用户名和密码
4. 点击 "开始导入"

#### 3. 本地目录

导入本地已有的代码库。

**步骤**:
1. 选择 "本地目录" 选项
2. 浏览并选择项目文件夹
3. 输入项目名称
4. 点击 "开始导入"

#### 4. ZIP 文件

导入压缩包形式的代码库。

**步骤**:
1. 选择 "ZIP 文件" 选项
2. 选择或上传 ZIP 文件
3. 输入项目名称
4. 点击 "开始导入"

### 导入状态

导入过程中，你可以实时查看进度：

- **克隆中**: 从远程仓库拉取代码
- **解析中**: 分析代码结构
- **索引中**: 生成向量索引
- **完成**: 导入成功
- **错误**: 导入失败，查看错误详情

### 支持的语言

- Python (.py)
- JavaScript (.js, .jsx)
- TypeScript (.ts, .tsx)
- Java (.java)
- Go (.go)
- Rust (.rs)
- Vue (.vue)

---

## 代码问答

### 问答模式

CodeInsight 提供三种智能问答模式：

#### 1. 实现型问答 (Implementation)

**用途**: 了解代码实现细节

**示例问题**:
- "用户登录功能是如何实现的？"
- "show me the `calculate_tax` function"
- "数据库连接在哪里初始化的？"

**特点**:
- 严格基于代码库回答
- 包含代码位置引用
- 适合查看具体实现

#### 2. 规划型问答 (Planning)

**用途**: 规划新功能或改进

**示例问题**:
- "如何添加用户认证功能？"
- "如何优化数据库查询性能？"
- "我想添加一个导出功能，应该怎么设计？"

**特点**:
- 基于 LLM 行业知识
- 提供最佳实践建议
- 适合架构设计

#### 3. 混合型问答 (Hybrid)

**用途**: 理解现状并获取改进建议

**示例问题**:
- "当前项目的架构有什么优缺点？"
- "这个功能可以如何优化？"
- "分析代码质量并给出改进建议"

**特点**:
- 结合代码库分析和行业知识
- 提供现状描述和改进建议
- 适合代码审查

### 使用技巧

**精准提问**:
- ✅ "用户登录的验证逻辑在哪里？"
- ❌ "用户登录"

**指定上下文**:
- ✅ "在 `UserService` 中，如何处理用户不存在的情况？"
- ❌ "如何处理用户不存在？"

**追问细化**:
- "能再详细说明一下吗？"
- "有相关的代码示例吗？"
- "这个函数的返回值是什么？"

---

## 功能分析

### 功能树视图

功能分析模块会自动提取项目的前后端功能，并以树形结构展示：

#### 前端功能

- **路由信息**: 页面路由配置
- **页面功能**: 按钮点击、表单提交、数据加载
- **组件依赖**: 组件间的引用关系
- **API 调用**: 前端调用的后端接口

#### 后端功能

- **API 端点**: RESTful API 列表
- **数据模型**: ORM 模型定义
- **服务类**: 业务逻辑层
- **系统功能**: 定时任务、中间件、缓存等

### 功能详情

点击任意功能节点，可以查看：

- **位置信息**: 文件路径和行号
- **依赖关系**: 调用和被调用关系
- **相关文件**: 关联的其他文件
- **代码片段**: 核心实现代码

---

## 可视化图表

### 流程图

展示业务流程和逻辑流向。

**生成方式**:
1. 进入 "可视化" 页面
2. 选择 "流程图"
3. 输入入口函数或模块
4. 调整深度参数

**支持的格式**:
- Mermaid（文本格式）
- 可导出为 PNG/SVG

### 架构图

展示项目整体架构和模块关系。

**展示内容**:
- 前端模块
- 后端模块
- 模块间依赖
- 技术栈

### 调用图

展示函数调用关系。

**功能**:
- 查看函数调用链
- 识别循环调用
- 分析复杂度

---

## 文档生成

### 自动生成文档

CodeInsight 可以自动生成以下文档：

1. **API 文档**: 后端 API 接口文档
2. **README**: 项目说明文档
3. **架构文档**: 系统架构设计文档

### 生成步骤

1. 进入项目详情页
2. 点击 "生成文档" 按钮
3. 选择要生成的文档类型
4. 等待生成完成
5. 预览或下载文档

### 文档格式

- **Markdown**: 源码友好的格式
- **HTML**: 网页可读格式
- **PDF**: 可打印格式

---

## 常见问题

### Q: 导入项目很慢怎么办？

**A**:
- 对于大型项目，首次导入需要较长时间（10-30分钟）
- 可以使用浅克隆（depth=1）加速
- 建议使用 Git URL 而非 ZIP 文件

### Q: 问答不准确怎么办？

**A**:
- 尝试使用更具体的问题
- 检查是否选择了正确的问答模式
- 确认代码库已完整索引
- 可以使用追问来细化问题

### Q: 支持哪些编程语言？

**A**: 目前支持 Python、JavaScript、TypeScript、Java、Go、Rust、Vue。未来会支持更多语言。

### Q: 代码会上传到云端吗？

**A**: 不会。所有代码和处理都在本地完成，确保数据安全。

### Q: 可以离线使用吗？

**A**: 可以。CodeInsight 支持完全离线运行，但 LLM 功能需要网络连接（可使用本地 LLM）。

### Q: 如何更新已导入的项目？

**A**: 目前需要删除项目后重新导入。未来将支持增量更新。

---

## 技术支持

如有问题或建议，请：

- 提交 Issue: https://github.com/your-org/code-insight/issues
- 查看文档: docs/api-design.md
- 联系支持: support@example.com
```

#### 步骤 2: 创建开发者指南 `docs/developer-guide.md`

```markdown
# CodeInsight 开发者指南

## 目录

1. [开发环境搭建](#开发环境搭建)
2. [项目结构](#项目结构)
3. [开发流程](#开发流程)
4. [测试](#测试)
5. [构建与部署](#构建与部署)
6. [贡献指南](#贡献指南)

---

## 开发环境搭建

### 系统要求

- Python 3.11+
- Node.js 18+
- Git
- Docker（可选）

### 后端开发

#### 1. 设置虚拟环境

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

#### 3. 配置环境变量

创建 `backend/.env` 文件：

```env
DEBUG=True
DATABASE_URL=sqlite:///./data/codeinsight.db

# LLM 配置（可选）
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=deepseek-chat
OPENAI_BASE_URL=https://api.deepseek.com

# Embedding 配置
EMBEDDING_MODEL=local
EMBEDDING_USE_LOCAL=True
```

#### 4. 初始化数据库

```bash
python -m app.core.init_db
```

#### 5. 启动开发服务器

```bash
uvicorn app.main:app --reload --port 8000
```

访问 http://localhost:8000/docs 查看 API 文档。

### 前端开发

#### 1. 安装依赖

```bash
cd frontend
npm install
```

#### 2. 配置环境变量

创建 `frontend/.env.development` 文件：

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

#### 3. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:5173

---

## 项目结构

### 后端结构

```
backend/
├── app/
│   ├── api/              # API 路由
│   │   ├── projects.py   # 项目管理 API
│   │   ├── chat.py      # 问答 API
│   │   └── ...
│   ├── parsers/          # 代码解析器
│   │   ├── base.py      # 解析器基类
│   │   ├── python_parser.py
│   │   └── ...
│   ├── rag/             # RAG 模块
│   │   ├── embedder.py  # 向量化
│   │   ├── retriever.py # 检索器
│   │   └── ...
│   ├── analysis/         # 功能分析
│   │   ├── frontend_analyzer.py
│   │   └── ...
│   ├── graph/           # 图表生成
│   │   └── ...
│   ├── docs/            # 文档生成
│   │   └── ...
│   ├── llm/             # LLM 服务
│   │   └── service.py
│   ├── services/        # 业务逻辑
│   ├── models/          # 数据模型
│   └── core/           # 核心配置
├── tests/               # 测试
└── requirements.txt
```

### 前端结构

```
frontend/
├── src/
│   ├── components/      # React 组件
│   │   ├── features/   # 功能分析组件
│   │   ├── mermaid/    # 图表组件
│   │   └── ...
│   ├── pages/          # 页面组件
│   ├── services/       # API 服务
│   ├── stores/         # 状态管理
│   ├── types/          # TypeScript 类型
│   └── main.tsx
└── package.json
```

---

## 开发流程

### 代码风格

#### Python

遵循 PEP 8 规范，使用 black 格式化：

```bash
cd backend
black .
isort .
```

#### TypeScript

使用 ESLint 和 Prettier：

```bash
cd frontend
npm run lint
```

### 添加新功能

#### 1. 添加新解析器

```python
# app/parsers/newlang_parser.py
from app.parsers.base import BaseParser

class NewLangParser(BaseParser):
    def get_language(self) -> str:
        return "newlang"

    def parse(self, content: str, file_path: str) -> ParseResult:
        # 实现解析逻辑
        pass
```

注册解析器：

```python
# app/parsers/__init__.py
from app.parsers.newlang_parser import NewLangParser
ParserFactory.register("newlang", NewLangParser, extensions=[".nl"])
```

#### 2. 添加新 API 端点

```python
# app/api/newfeature.py
from fastapi import APIRouter, Depends
from app.services.new_service import NewService

router = APIRouter(prefix="/newfeature", tags=["New Feature"])

@router.get("/")
async def get_items(service: NewService = Depends()):
    return service.get_all()

@router.post("/")
async def create_item(data: ItemCreate, service: NewService = Depends()):
    return service.create(data)
```

在 `app/main.py` 中注册：

```python
from app.api import newfeature

app.include_router(newfeature.router)
```

---

## 测试

### 运行后端测试

```bash
cd backend

# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_parsers.py

# 运行并生成覆盖率
pytest --cov=app --cov-report=html
```

### 运行前端测试

```bash
cd frontend

# 运行测试
npm test

# 类型检查
npm run typecheck
```

---

## 构建与部署

### 构建 Docker 镜像

```bash
# 构建后端
docker build -t codeinsight-backend ./backend

# 构建前端
docker build -t codeinsight-frontend ./frontend

# 构建所有服务
docker-compose build
```

### 部署

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

---

## 贡献指南

### 提交规范

遵循 Conventional Commits 规范：

- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

示例：

```bash
git commit -m "feat(parser): add Rust language support"
git commit -m "fix(api): handle null values in project creation"
```

### Pull Request 流程

1. Fork 仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 代码审查

- 确保所有测试通过
- 代码风格一致
- 添加必要的文档和注释
- 更新相关文档
```

#### 步骤 3: 更新 README.md

```markdown
# CodeInsight

<div align="center">

本地代码库智能分析与知识问答系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![Docker](https://img.shields.io/badge/docker-latest-blue.svg)](https://www.docker.com/)

</div>

## ✨ 功能特点

### 🧠 智能代码分析
- **多语言支持**: Python、JavaScript、TypeScript、Java、Go、Rust、Vue
- **深度解析**: 自动提取函数、类、API、路由等代码结构
- **依赖分析**: 构建调用图和依赖关系图

### 💬 AI 问答系统
- **三种问答模式**:
  - 实现型：基于代码库回答
  - 规划型：基于行业知识建议
  - 混合型：现状分析+改进建议
- **代码引用**: 精确的代码位置引用
- **流式响应**: 实时获取回答

### 📊 功能可视化
- **功能树**: 前后端功能自动提取和展示
- **架构图**: 项目架构可视化
- **流程图**: 业务流程图生成
- **调用图**: 函数调用关系图

### 📝 文档生成
- **API 文档**: 自动生成 API 接口文档
- **README**: 自动生成项目说明文档
- **架构文档**: 自动生成系统架构文档
- **多格式导出**: Markdown、HTML、PDF

### 🔒 隐私安全
- **本地处理**: 所有代码和分析在本地完成
- **数据安全**: 代码不上传到云端
- **可选 LLM**: 支持本地 LLM 后端

## 🚀 快速开始

### Docker 方式（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/your-org/code-insight.git
cd code-insight

# 2. 启动服务
docker-compose up -d

# 3. 访问应用
open http://localhost:3000
```

### 手动安装

#### 后端

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python -m app.core.init_db

# 启动服务
uvicorn app.main:app --reload
```

#### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问 http://localhost:5173

## 📖 文档

- **[用户指南](docs/user-guide.md)**: 完整的使用说明
- **[开发者指南](docs/developer-guide.md)**: 开发和贡献指南
- **[API 文档](docs/api-design.md)**: API 接口说明
- **[架构设计](docs/architecture.md)**: 系统架构文档

## 🎯 使用场景

### 开发者
- 快速理解新项目的代码结构
- 查找特定功能的实现位置
- 代码审查和重构建议

### 技术团队
- 新成员快速上手培训
- 代码知识库积累
- 技术文档自动化

### 项目经理
- 了解项目整体架构
- 功能模块依赖关系
- 技术债务识别

## 🔧 配置

### 环境变量

创建 `.env` 文件：

```env
# 应用配置
DEBUG=False
APP_NAME=CodeInsight

# 数据库
DATABASE_URL=sqlite:///./data/codeinsight.db

# LLM 配置
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=deepseek-chat
OPENAI_BASE_URL=https://api.deepseek.com

# Embedding 配置
EMBEDDING_MODEL=local
EMBEDDING_USE_LOCAL=True
```

### 支持的语言

| 语言 | 扩展名 | 状态 |
|------|--------|------|
| Python | .py | ✅ |
| JavaScript | .js, .jsx, .mjs | ✅ |
| TypeScript | .ts, .tsx, .mts | ✅ |
| Java | .java | 🚧 |
| Go | .go | 🚧 |
| Rust | .rs | 🚧 |
| Vue | .vue | ✅ |

## 🧪 测试

```bash
# 后端测试
cd backend
pytest

# 前端测试
cd frontend
npm test
```

## 🤝 贡献

欢迎贡献！请查看 [贡献指南](docs/developer-guide.md#贡献指南)。

### 贡献方式
- 报告 Bug
- 提出新功能建议
- 提交 Pull Request
- 改进文档

## 📝 许可证

本项目采用 [MIT 许可证](LICENSE)。

## 📧 联系方式

- Issue: https://github.com/your-org/code-insight/issues
- 邮件: support@example.com

---

<div align="center">

如果这个项目对你有帮助，请给它一个 ⭐️

Made with ❤️ by CodeInsight Team

</div>
```

### 验收标准
- [ ] 用户指南已创建 (`docs/user-guide.md`)
- [ ] 开发者指南已创建 (`docs/developer-guide.md`)
- [ ] README.md 已更新
- [ ] 文档内容完整、清晰
- [ ] 所有示例代码可运行

### 提交信息
```
docs: add comprehensive user and developer guides
```

### 2. 访问界面

打开浏览器访问 http://localhost:3000

### 3. 导入项目

点击"导入项目"按钮，选择导入方式：
- GitHub URL
- 本地目录
- ZIP文件

## 功能说明

### 代码问答

支持三种问答模式：
1. **实现型**：基于代码库回答
2. **规划型**：基于行业知识建议
3. **混合型**：现状分析+改进建议

### 功能分析

自动分析项目的前后端功能...

### 文档生成

自动生成项目文档...
```

2. 创建开发文档 `docs/developer-guide.md`
```markdown
# 开发者指南

## 本地开发环境

### 后端

```bash
cd code-insight/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 前端

```bash
cd code-insight/frontend
npm install
npm run dev
```

## 项目结构

...

## API文档

详见 docs/api-design.md
```

3. 更新README
```markdown
# CodeInsight

本地代码库智能检测与知识问答系统

## 功能特点

- 多语言代码解析
- 智能问答（三种模式）
- 功能自动分析
- 文档自动生成

## 快速开始

```bash
docker-compose up -d
```

## 文档

- [用户指南](docs/user-guide.md)
- [API文档](docs/api-design.md)
- [开发者指南](docs/developer-guide.md)

## 许可证

MIT
```

### 验收标准
- [ ] 用户指南完整
- [ ] 开发指南完整
- [ ] README更新

### 提交信息
```
docs: add user guide and developer documentation
```

---

## 任务 6.6：部署验证

### 描述
验证 Docker 部署，编写部署脚本。

**当前状态**:
- ✅ 已有基础 `docker-compose.yml`
- ✅ 已有后端 Dockerfile
- ✅ 已有前端 Dockerfile
- ❌ 缺少部署脚本
- ❌ 缺少健康检查配置
- ❌ 缺少备份脚本
- ❌ 缺少生产环境配置

### 执行步骤

#### 步骤 1: 创建部署脚本 `scripts/deploy.sh`

```bash
#!/bin/bash

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Docker
check_docker() {
    log_info "检查 Docker 环境..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi

    log_info "Docker 环境检查通过"
}

# 检查环境变量
check_env() {
    log_info "检查环境变量..."

    if [ ! -f .env ]; then
        log_warn ".env 文件不存在，从 .env.example 创建..."

        if [ ! -f .env.example ]; then
            log_error ".env.example 文件不存在"
            exit 1
        fi

        cp .env.example .env
        log_warn "请编辑 .env 文件，配置必要的环境变量（如 API Keys）"
        log_warn "编辑后重新运行部署脚本"

        exit 0
    fi

    log_info "环境变量检查通过"
}

# 创建必要目录
create_directories() {
    log_info "创建必要目录..."

    mkdir -p ./data/projects
    mkdir -p ./data/chroma
    mkdir -p ./data/logs
    mkdir -p ./backups

    log_info "目录创建完成"
}

# 停止现有服务
stop_services() {
    log_info "停止现有服务..."

    if docker-compose ps -q &> /dev/null; then
        docker-compose down
    elif docker compose ps -q &> /dev/null 2>&1; then
        docker compose down
    fi

    log_info "服务已停止"
}

# 构建镜像
build_images() {
    log_info "构建 Docker 镜像..."

    # 优先使用 docker compose（新版）
    if docker compose version &> /dev/null; then
        docker compose build --no-cache
    else
        docker-compose build --no-cache
    fi

    log_info "镜像构建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."

    if docker compose version &> /dev/null; then
        docker compose up -d
    else
        docker-compose up -d
    fi

    log_info "服务已启动"
}

# 等待服务就绪
wait_for_services() {
    log_info "等待服务就绪..."

    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -sf http://localhost:8000/health &> /dev/null; then
            log_info "后端服务已就绪"
            break
        fi

        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done

    echo ""

    if [ $attempt -eq $max_attempts ]; then
        log_error "服务启动超时"
        return 1
    fi

    # 等待前端
    if curl -sf http://localhost:3000 &> /dev/null; then
        log_info "前端服务已就绪"
    fi
}

# 健康检查
health_check() {
    log_info "执行健康检查..."

    # 检查后端
    if curl -sf http://localhost:8000/health > /dev/null; then
        log_info "✓ 后端健康检查通过"
    else
        log_error "✗ 后端健康检查失败"
        return 1
    fi

    # 检查前端
    if curl -sf http://localhost:3000 > /dev/null; then
        log_info "✓ 前端健康检查通过"
    else
        log_error "✗ 前端健康检查失败"
        return 1
    fi

    # 检查 API
    API_STATUS=$(curl -sf -o /dev/null -w "%{http_code}" http://localhost:8000/api/projects)
    if [ "$API_STATUS" = "200" ]; then
        log_info "✓ API 健康检查通过"
    else
        log_warn "✗ API 返回状态码: $API_STATUS"
    fi
}

# 显示部署信息
show_info() {
    echo ""
    echo "========================================="
    echo "   CodeInsight 部署完成"
    echo "========================================="
    echo ""
    echo "访问地址:"
    echo "  前端界面:  http://localhost:3000"
    echo "  后端 API:  http://localhost:8000"
    echo "  API 文档:  http://localhost:8000/docs"
    echo ""
    echo "管理命令:"
    echo "  查看日志:  docker-compose logs -f"
    echo "  停止服务:  ./scripts/stop.sh"
    echo "  重启服务:  docker-compose restart"
    echo ""
    echo "========================================="
}

# 主流程
main() {
    echo ""
    log_info "开始 CodeInsight 部署..."
    echo ""

    check_docker
    check_env
    create_directories
    stop_services
    build_images
    start_services
    wait_for_services
    health_check

    if [ $? -eq 0 ]; then
        show_info
    else
        log_error "部署失败，请查看日志"
        docker-compose logs
        exit 1
    fi
}

main "$@"
```

#### 步骤 2: 创建停止脚本 `scripts/stop.sh`

```bash
#!/bin/bash

set -e

GREEN='\033[0;32m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_info "停止 CodeInsight 服务..."

# 使用 docker compose 或 docker-compose
if docker compose version &> /dev/null; then
    docker compose down
else
    docker-compose down
fi

log_info "服务已停止"
```

#### 步骤 3: 创建备份脚本 `scripts/backup.sh`

```bash
#!/bin/bash

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# 创建备份
create_backup() {
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_DIR="./backups/backup_${TIMESTAMP}"

    log_info "创建备份: $BACKUP_DIR"

    mkdir -p "$BACKUP_DIR"

    # 备份数据库
    if [ -f ./data/codeinsight.db ]; then
        log_info "备份数据库..."
        cp ./data/codeinsight.db "$BACKUP_DIR/"
    fi

    # 备份项目数据
    if [ -d ./data/projects ]; then
        log_info "备份项目数据..."
        # 使用 tar 压缩
        tar -czf "$BACKUP_DIR/projects.tar.gz" -C ./data projects 2>/dev/null || true
    fi

    # 备份向量数据
    if [ -d ./data/chroma ]; then
        log_info "备份向量数据..."
        tar -czf "$BACKUP_DIR/chroma.tar.gz" -C ./data chroma 2>/dev/null || true
    fi

    # 备份配置
    if [ -f .env ]; then
        log_info "备份配置文件..."
        cp .env "$BACKUP_DIR/"
    fi

    # 创建备份清单
    cat > "$BACKUP_DIR/manifest.txt" << EOF
备份时间: $(date)
备份版本: $(git rev-parse HEAD 2>/dev/null || echo "unknown")
备份内容:
EOF

    ls -lh "$BACKUP_DIR" >> "$BACKUP_DIR/manifest.txt"

    log_info "备份完成: $BACKUP_DIR"
}

# 清理旧备份
cleanup_old_backups() {
    log_info "清理旧备份（保留最近 7 天）..."

    find ./backups -type d -name "backup_*" -mtime +7 -exec rm -rf {} \; 2>/dev/null || true

    log_info "清理完成"
}

main() {
    echo ""
    log_info "开始数据备份..."
    echo ""

    create_backup
    cleanup_old_backups

    echo ""
    log_info "备份流程完成"
    echo ""
}

main "$@"
```

#### 步骤 4: 更新 `docker-compose.yml`

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: codeinsight-backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./backend/logs:/app/logs
    env_file:
      - ./backend/.env
    environment:
      - PYTHONUNBUFFERED=1
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
    networks:
      - codeinsight-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      container_name: codeinsight-frontend
    ports:
      - "3000:80"
    depends_on:
      backend:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    restart: unless-stopped
    networks:
      - codeinsight-network

networks:
  codeinsight-network:
    driver: bridge

volumes:
  codeinsight-data:
```

#### 步骤 5: 创建生产环境配置 `docker-compose.prod.yml`

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: codeinsight-backend-prod
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./backend/logs:/app/logs
    env_file:
      - .env.production
    environment:
      - PYTHONUNBUFFERED=1
      - DEBUG=False
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: always
    networks:
      - codeinsight-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        - VITE_API_BASE_URL=/api
    container_name: codeinsight-frontend-prod
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      backend:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    restart: always
    networks:
      - codeinsight-network

  # 可选：使用 Nginx 反向代理
  nginx:
    image: nginx:alpine
    container_name: codeinsight-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - frontend
      - backend
    restart: always
    networks:
      - codeinsight-network
    profiles:
      - nginx

networks:
  codeinsight-network:
    driver: bridge
```

#### 步骤 6: 创建部署验证脚本 `scripts/verify.sh`

```bash
#!/bin/bash

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS="${GREEN}✓${NC}"
FAIL="${RED}✗${NC}"

log_test() {
    local test_name=$1
    local result=$2
    echo -e "$result $test_name"
}

echo ""
echo "========================================="
echo "   CodeInsight 部署验证"
echo "========================================="
echo ""

# 1. 检查 Docker 容器运行状态
echo "1. 检查容器运行状态..."
BACKEND_RUNNING=$(docker ps -q --filter "name=codeinsight-backend" | wc -l)
FRONTEND_RUNNING=$(docker ps -q --filter "name=codeinsight-frontend" | wc -l)

if [ "$BACKEND_RUNNING" -gt 0 ]; then
    log_test "后端容器运行中" "$PASS"
else
    log_test "后端容器运行中" "$FAIL"
fi

if [ "$FRONTEND_RUNNING" -gt 0 ]; then
    log_test "前端容器运行中" "$PASS"
else
    log_test "前端容器运行中" "$FAIL"
fi

echo ""

# 2. 健康检查
echo "2. 执行健康检查..."

if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    log_test "后端健康检查" "$PASS"
else
    log_test "后端健康检查" "$FAIL"
fi

if curl -sf http://localhost:3000 > /dev/null 2>&1; then
    log_test "前端健康检查" "$PASS"
else
    log_test "前端健康检查" "$FAIL"
fi

echo ""

# 3. API 功能测试
echo "3. API 功能测试..."

# 测试项目列表 API
PROJECTS_STATUS=$(curl -sf -o /dev/null -w "%{http_code}" http://localhost:8000/api/projects 2>&1)
if [ "$PROJECTS_STATUS" = "200" ]; then
    log_test "获取项目列表 API" "$PASS"
else
    log_test "获取项目列表 API (状态码: $PROJECTS_STATUS)" "$FAIL"
fi

# 测试健康检查 API
HEALTH_STATUS=$(curl -sf -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>&1)
if [ "$HEALTH_STATUS" = "200" ]; then
    log_test "健康检查 API" "$PASS"
else
    log_test "健康检查 API (状态码: $HEALTH_STATUS)" "$FAIL"
fi

echo ""

# 4. 数据持久化检查
echo "4. 检查数据持久化..."

if [ -d ./data/projects ]; then
    log_test "项目数据目录" "$PASS"
else
    log_test "项目数据目录" "$FAIL"
fi

if [ -d ./data/chroma ]; then
    log_test "向量数据目录" "$PASS"
else
    log_test "向量数据目录" "$FAIL"
fi

if [ -f ./data/codeinsight.db ]; then
    log_test "数据库文件" "$PASS"
else
    log_test "数据库文件" "$FAIL"
fi

echo ""

# 5. 日志检查
echo "5. 检查应用日志..."

BACKEND_LOGS=$(docker logs codeinsight-backend 2>&1 | tail -n 10)
if echo "$BACKEND_LOGS" | grep -q "Application startup complete"; then
    log_test "后端启动日志" "$PASS"
else
    log_test "后端启动日志" "$WARN (可能还在启动中)"
fi

echo ""
echo "========================================="
echo "   验证完成"
echo "========================================="
echo ""
```

#### 步骤 7: 创建 `.env.example` 文件

```env
# 应用配置
APP_NAME=CodeInsight
DEBUG=True
VERSION=1.0.0

# 数据库
DATABASE_URL=sqlite:///./data/codeinsight.db

# 目录配置
DATA_DIR=./data
PROJECTS_DIR=./data/projects
CHROMA_DIR=./data/chroma

# LLM 配置
OPENAI_API_KEY=
OPENAI_MODEL=deepseek-chat
OPENAI_BASE_URL=https://api.deepseek.com

CLAUDE_API_KEY=

# Embedding 配置
EMBEDDING_MODEL=local
EMBEDDING_BASE_URL=
EMBEDDING_USE_LOCAL=True
EMBEDDING_DIM=384

# 索引配置
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# 文件配置
MAX_FILE_SIZE=10485760

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
```

#### 步骤 8: 执行部署验证

```bash
# 1. 给脚本添加执行权限
chmod +x scripts/*.sh

# 2. 执行部署
./scripts/deploy.sh

# 3. 等待部署完成后，执行验证
./scripts/verify.sh

# 4. 测试基本功能
curl http://localhost:8000/health
curl http://localhost:8000/api/projects

# 5. 如果需要停止
./scripts/stop.sh
```

### 验收标准
- [ ] 部署脚本可执行 (`scripts/deploy.sh`)
- [ ] 停止脚本可执行 (`scripts/stop.sh`)
- [ ] 备份脚本可执行 (`scripts/backup.sh`)
- [ ] 验证脚本可执行 (`scripts/verify.sh`)
- [ ] 健康检查正常
- [ ] 服务可正常启动和停止
- [ ] 数据持久化工作正常
- [ ] 备份功能正常
- [ ] 生产环境配置可用 (`docker-compose.prod.yml`)
- [ ] 所有验证测试通过

### 提交信息
```
chore: add comprehensive deployment scripts and verification
```

---

## Phase 6 完成标准

### 任务 6.1：多语言扩展
- [x] Java 解析器已创建并注册
- [x] Go 解析器已创建并注册
- [ ] Java/Go 文件可正确解析
- [ ] 单元测试通过
- [ ] 文档已更新

### 任务 6.2：性能优化
- [x] Embedding 批量处理优化完成
- [x] 向量检索支持缓存和阈值过滤
- [ ] 性能监控模块可用
- [ ] 大型项目解析支持内存管理
- [ ] 性能基准测试通过

### 任务 6.3：错误处理
- [x] 自定义异常模块已创建
- [x] 全局异常处理器已注册
- [x] 各服务模块使用统一异常
- [ ] 错误日志记录完整
- [ ] 前端能正确展示错误信息

### 任务 6.4：单元测试
- [x] 错误处理模块测试已创建
- [x] 性能监控测试已创建
- [x] 集成测试已创建
- [ ] 所有测试通过
- [ ] 测试覆盖率 ≥ 70%
- [ ] 关键模块覆盖率 ≥ 80%

### 任务 6.5：使用文档
- [x] 用户指南已创建 (`docs/user-guide.md`)
- [x] 开发者指南已创建 (`docs/developer-guide.md`)
- [x] README.md 已更新
- [ ] 文档内容完整、清晰
- [ ] 所有示例代码可运行

### 任务 6.6：部署验证
- [x] 部署脚本可执行 (`scripts/deploy.sh`)
- [x] 停止脚本可执行 (`scripts/stop.sh`)
- [x] 备份脚本可执行 (`scripts/backup.sh`)
- [x] 验证脚本可执行 (`scripts/verify.sh`)
- [ ] 健康检查正常
- [ ] 服务可正常启动和停止
- [ ] 数据持久化工作正常
- [ ] 备份功能正常
- [ ] 生产环境配置可用

---

## 项目完成总结

完成所有 Phase 后，项目应具备以下能力：

### 核心功能
1. **项目导入**：支持 GitHub/Git/ZIP/本地目录导入
2. **代码解析**：支持 Python/JS/TS/Java/Go 等语言
3. **智能问答**：三种模式的精准问答（实现型/规划型/混合型）
4. **功能分析**：前后端功能自动提取和展示
5. **文档生成**：自动生成 API 文档、README、架构文档
6. **可视化**：流程图、架构图、调用图
7. **性能优化**：批量处理、缓存、并行解析
8. **错误处理**：统一的异常处理和友好的错误提示
9. **部署支持**：完整的部署脚本和验证流程

### 技术亮点
- **多语言解析器**：基于 Tree-sitter 的可扩展解析器架构
- **智能问答**：结合 RAG 和 LLM 的混合问答系统
- **高性能**：支持批量 Embedding、缓存优化、增量索引
- **易部署**：完整的 Docker 支持，一键部署
- **隐私安全**：本地处理，代码不上传云端

---

## 后续优化方向

### 短期（3个月内）
- [ ] 完善 Java/Go/Rust 解析器功能
- [ ] 添加更多单元测试，提升覆盖率到 80%+
- [ ] 优化大型项目的解析性能
- [ ] 添加增量更新功能
- [ ] 改进前端 UI/UX

### 中期（6个月内）
- [ ] 添加用户认证和权限管理
- [ ] 支持团队协作功能
- [ ] 添加代码审查建议
- [ ] 支持 CI/CD 集成
- [ ] 添加插件系统

### 长期（12个月内）
- [ ] 支持更多语言（Rust、Kotlin、C# 等）
- [ ] 支持更多 LLM 后端（本地模型、Azure OpenAI 等）
- [ ] 添加代码搜索功能（语义搜索 + 正则搜索）
- [ ] 添加代码重构建议
- [ ] 支持多租户部署
- [ ] 添加 SaaS 版本

---

## 质量指标

### 代码质量
- 测试覆盖率 ≥ 70%
- 关键模块覆盖率 ≥ 80%
- 所有 Linter 检查通过
- 无 High/Critical 级别的安全问题

### 性能指标
- 1000 个文件的项目解析时间 < 5 分钟
- API 响应时间 P95 < 2 秒
- 问答响应时间 < 5 秒

### 用户体验
- 所有 API 有完整文档
- 用户指南覆盖所有功能
- 错误提示友好清晰
- 部署流程简单可重复

---

## 附录

### 文件清单

**新增文件**:
- `app/parsers/java_parser.py` - Java 解析器
- `app/parsers/go_parser.py` - Go 解析器
- `app/core/exceptions.py` - 自定义异常
- `app/core/error_handler.py` - 全局异常处理器
- `app/services/performance_monitor.py` - 性能监控
- `tests/test_exceptions.py` - 异常测试
- `tests/test_performance.py` - 性能测试
- `tests/test_integration.py` - 集成测试
- `tests/conftest.py` - 测试配置
- `docs/user-guide.md` - 用户指南
- `docs/developer-guide.md` - 开发者指南
- `scripts/deploy.sh` - 部署脚本
- `scripts/stop.sh` - 停止脚本
- `scripts/backup.sh` - 备份脚本
- `scripts/verify.sh` - 验证脚本
- `docker-compose.prod.yml` - 生产环境配置
- `.env.example` - 环境变量示例

**修改文件**:
- `plans/phase-6-optimization.md` - Phase 6 计划（本文件）
- `docs/task-progress.md` - 任务进度
- `backend/app/parsers/__init__.py` - 注册新解析器
- `backend/app/main.py` - 注册异常处理器
- `README.md` - 更新主文档

### 参考资料

- [Tree-sitter 文档](https://tree-sitter.github.io/tree-sitter/)
- [FastAPI 最佳实践](https://fastapi.tiangolo.com/tutorial/)
- [React 性能优化](https://react.dev/learn/render-and-commit)
- [Docker 最佳实践](https://docs.docker.com/develop/dev-best-practices/)
- [pytest 文档](https://docs.pytest.org/en/stable/)
