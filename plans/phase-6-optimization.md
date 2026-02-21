# Phase 6: 优化与完善 - 执行计划

**目标**：扩展语言支持、性能优化、测试完善  
**任务数**：6个  
**预计时间**：1周  
**分支**：feature/phase-6-optimization  
**依赖**：Phase 1-5 完成

---

## 任务 6.1：多语言扩展

### 描述
添加Java、Go、Rust等语言解析器。

### 执行步骤

1. 创建Java解析器 `app/parsers/java_parser.py`
```python
import tree_sitter_java as tsjava
from tree_sitter import Language, Parser
from app.parsers.base import BaseParser, ParseResult, FunctionInfo, ClassInfo

class JavaParser(BaseParser):
    def __init__(self):
        self.parser = Parser(Language(tsjava.language()))
    
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
    
    def _extract_methods(self, node, content: str) -> list:
        methods = []
        for child in node.children:
            if child.type == "method_declaration":
                methods.append(self._parse_method(child, content))
            # 递归处理类内部的方法
            elif child.type == "class_declaration":
                methods.extend(self._extract_methods(child, content))
        return methods
```

2. 创建Go解析器 `app/parsers/go_parser.py`
```python
import tree_sitter_go as tsgo
from tree_sitter import Language, Parser
from app.parsers.base import BaseParser

class GoParser(BaseParser):
    def __init__(self):
        self.parser = Parser(Language(tsgo.language()))
    
    def get_language(self) -> str:
        return "go"
    
    def parse(self, content: str, file_path: str) -> ParseResult:
        # Go特定的解析逻辑
        pass
```

3. 注册新解析器
```python
# app/parsers/__init__.py
from app.parsers.factory import ParserFactory
from app.parsers.python_parser import PythonParser
from app.parsers.js_parser import JavaScriptParser, TypeScriptParser
from app.parsers.java_parser import JavaParser
from app.parsers.go_parser import GoParser

ParserFactory.register("python", PythonParser)
ParserFactory.register("py", PythonParser)
ParserFactory.register("javascript", JavaScriptParser)
ParserFactory.register("js", JavaScriptParser)
ParserFactory.register("typescript", TypeScriptParser)
ParserFactory.register("ts", TypeScriptParser)
ParserFactory.register("tsx", TypeScriptParser)
ParserFactory.register("java", JavaParser)
ParserFactory.register("go", GoParser)
```

### 验收标准
- [ ] Java文件可解析
- [ ] Go文件可解析
- [ ] 正确注册到工厂

### 提交信息
```
feat(parser): add java and go language parsers
```

---

## 任务 6.2：性能优化

### 描述
优化大型代码库的处理性能。

### 执行步骤

1. 并行解析优化 `app/services/parallel_parser.py`
```python
import asyncio
from concurrent.futures import ProcessPoolExecutor
from typing import List
from pathlib import Path
from app.parsers.factory import ParserFactory

class ParallelParser:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
    
    async def parse_project(self, project_path: str) -> List:
        files = self._collect_files(project_path)
        
        # 使用进程池并行解析
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            loop = asyncio.get_event_loop()
            tasks = [
                loop.run_in_executor(executor, self._parse_file, f)
                for f in files
            ]
            results = await asyncio.gather(*tasks)
        
        return results
    
    def _collect_files(self, project_path: str) -> List[Path]:
        # 收集需要解析的文件
        pass
    
    def _parse_file(self, file_path: Path):
        # 解析单个文件
        pass
```

2. 向量化批处理
```python
# app/rag/embedder.py 优化

class Embedder:
    def __init__(self):
        # ...
        self.batch_size = 100  # 每批处理数量
    
    async def embed_chunks_batch(self, chunks: List[CodeChunk]) -> List[dict]:
        results = []
        
        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i:i + self.batch_size]
            batch_results = self.embed_chunks(batch)
            results.extend(batch_results)
            
            # 避免API限流
            await asyncio.sleep(0.5)
        
        return results
```

3. 增量索引优化
```python
# 只索引变更的文件
class IncrementalIndexer:
    def __init__(self, project_path: str):
        self.hash_cache = self._load_hash_cache()
    
    def get_changed_files(self) -> Dict[str, List[str]]:
        """返回新增、修改、删除的文件列表"""
        pass
    
    async def update_index(self):
        changes = self.get_changed_files()
        
        # 删除旧索引
        for file in changes["deleted"]:
            await self.vector_store.delete_by_file(file)
        
        # 更新修改的文件
        for file in changes["modified"]:
            await self.vector_store.delete_by_file(file)
            await self._index_file(file)
        
        # 索引新文件
        for file in changes["added"]:
            await self._index_file(file)
```

### 验收标准
- [ ] 并行解析提速
- [ ] 批量处理稳定
- [ ] 增量更新正确

### 提交信息
```
perf: optimize parsing and indexing performance
```

---

## 任务 6.3：错误处理

### 描述
完善异常捕获和友好提示。

### 执行步骤

1. 创建自定义异常 `app/core/exceptions.py`
```python
from fastapi import HTTPException

class CodeInsightException(Exception):
    """基础异常"""
    def __init__(self, message: str, code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

class ProjectNotFoundError(CodeInsightException):
    def __init__(self, project_id: str):
        super().__init__(f"项目不存在: {project_id}", "PROJECT_NOT_FOUND")

class ParseError(CodeInsightException):
    def __init__(self, file_path: str, detail: str):
        super().__init__(f"解析文件失败: {file_path}. {detail}", "PARSE_ERROR")

class IndexingError(CodeInsightException):
    def __init__(self, message: str):
        super().__init__(message, "INDEXING_ERROR")

class LLMError(CodeInsightException):
    def __init__(self, message: str):
        super().__init__(message, "LLM_ERROR")

class ImportError(CodeInsightException):
    def __init__(self, message: str):
        super().__init__(message, "IMPORT_ERROR")
```

2. 创建全局异常处理器 `app/core/error_handler.py`
```python
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import CodeInsightException

async def codeinsight_exception_handler(request: Request, exc: CodeInsightException):
    return JSONResponse(
        status_code=400,
        content={
            "code": exc.code,
            "message": exc.message,
            "detail": str(exc)
        }
    )

async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": "服务器内部错误",
            "detail": str(exc) if settings.DEBUG else None
        }
    )
```

3. 注册异常处理器
```python
# app/main.py
from app.core.error_handler import (
    codeinsight_exception_handler,
    generic_exception_handler
)
from app.core.exceptions import CodeInsightException

app.add_exception_handler(CodeInsightException, codeinsight_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)
```

### 验收标准
- [ ] 自定义异常正确
- [ ] 错误信息友好
- [ ] 全局处理器生效

### 提交信息
```
feat(core): add comprehensive error handling
```

---

## 任务 6.4：单元测试

### 描述
为核心模块编写单元测试。

### 执行步骤

1. 创建测试配置
```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
```

2. 测试解析器
```python
# tests/test_parsers.py
import pytest
from app.parsers.python_parser import PythonParser

def test_python_parser_function():
    parser = PythonParser()
    code = '''
def hello(name: str) -> str:
    """Say hello."""
    return f"Hello, {name}!"
'''
    result = parser.parse(code, "test.py")
    
    assert len(result.functions) == 1
    assert result.functions[0].name == "hello"
    assert result.functions[0].return_type == "str"

def test_python_parser_class():
    parser = PythonParser()
    code = '''
class User:
    def __init__(self, name):
        self.name = name
    
    def greet(self):
        return f"Hi, {self.name}"
'''
    result = parser.parse(code, "test.py")
    
    assert len(result.classes) == 1
    assert result.classes[0].name == "User"
```

3. 测试RAG检索
```python
# tests/test_rag.py
import pytest
from app.rag.embedder import Embedder
from app.rag.retriever import Retriever

@pytest.mark.asyncio
async def test_retriever_search():
    # Mock测试
    pass
```

4. 测试问答服务
```python
# tests/test_chat.py
import pytest
from app.services.chat_service import ChatService

@pytest.mark.asyncio
async def test_chat_implementation():
    # 测试实现型问答
    pass

@pytest.mark.asyncio
async def test_chat_planning():
    # 测试规划型问答
    pass
```

### 验收标准
- [ ] 解析器测试覆盖
- [ ] RAG测试覆盖
- [ ] 问答测试覆盖
- [ ] 测试可运行

### 提交信息
```
test: add unit tests for core modules
```

---

## 任务 6.5：使用文档

### 描述
编写用户使用说明文档。

### 执行步骤

1. 创建用户指南 `docs/user-guide.md`
```markdown
# CodeInsight 用户指南

## 快速开始

### 1. 启动服务

```bash
docker-compose up -d
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
验证Docker部署，编写部署脚本。

### 执行步骤

1. 创建部署脚本 `scripts/deploy.sh`
```bash
#!/bin/bash

echo "Starting CodeInsight deployment..."

# 检查环境
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed"
    exit 1
fi

# 创建环境变量文件
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "Please edit .env file with your API keys"
fi

# 构建镜像
echo "Building Docker images..."
docker-compose build

# 启动服务
echo "Starting services..."
docker-compose up -d

# 等待服务启动
echo "Waiting for services to start..."
sleep 10

# 健康检查
echo "Checking service health..."
curl -f http://localhost:8000/health || exit 1

echo "Deployment complete!"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000/docs"
```

2. 创建停止脚本 `scripts/stop.sh`
```bash
#!/bin/bash

echo "Stopping CodeInsight..."
docker-compose down

echo "Services stopped."
```

3. 创建备份脚本 `scripts/backup.sh`
```bash
#!/bin/bash

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

echo "Backing up data..."
cp -r ./data $BACKUP_DIR/

echo "Backup created at $BACKUP_DIR"
```

4. 更新docker-compose
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      backend:
        condition: service_healthy
```

5. 验证测试
```bash
# 运行部署验证
./scripts/deploy.sh

# 测试API
curl http://localhost:8000/health
curl http://localhost:8000/api/projects

# 测试前端
curl http://localhost:3000

# 停止服务
./scripts/stop.sh
```

### 验收标准
- [ ] 部署脚本可用
- [ ] 健康检查正常
- [ ] 服务可正常启动
- [ ] 备份功能正常

### 提交信息
```
chore: add deployment scripts and verification
```

---

## Phase 6 完成标准

- [ ] 多语言支持完整
- [ ] 性能优化完成
- [ ] 错误处理完善
- [ ] 测试覆盖核心模块
- [ ] 文档完整
- [ ] 部署验证通过

---

## 项目完成总结

完成所有Phase后，项目应具备以下能力：

1. **项目导入**：支持多种方式导入代码库
2. **代码解析**：支持Python/JS/TS/Java/Go等语言
3. **智能问答**：三种模式的精准问答
4. **功能分析**：前后端功能自动提取
5. **文档生成**：自动生成API文档和README
6. **可视化**：流程图、架构图、调用图

### 后续优化方向

- [ ] 添加更多语言支持（Rust、Kotlin等）
- [ ] 支持更多LLM后端（本地模型）
- [ ] 添加用户认证和权限管理
- [ ] 支持团队协作功能
- [ ] 添加代码审查建议
- [ ] 支持CI/CD集成
