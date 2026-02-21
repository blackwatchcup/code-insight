# CodeInsight智能代码问答系统 - 实施设计方案

**日期**: 2026-02-21  
**版本**: v1.0  
**状态**: 已批准

---

## 概述

本文档定义了CodeInsight智能代码问答系统的完整实施方案，基于渐进式开发策略，分三个阶段实现核心功能：基础框架 → 代码解析引擎 → RAG智能问答。

**核心目标**: 让用户能够导入项目后，通过自然语言提问获得关于代码功能、结构的智能回答。

---

## 第一部分：整体架构设计

### 1.1 系统架构

```
前端 (React + TS + Tailwind)
    ↓
后端 API (FastAPI)
    ↓
├── 项目管理服务
├── 代码解析引擎
│   ├── Python解析器
│   └── JS/TS解析器
├── 向量存储 (ChromaDB)
└── LLM服务 (OpenAI/Claude)
```

### 1.2 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| 后端 | FastAPI + Python 3.11 | API服务 |
| 前端 | React 18 + TypeScript + TailwindCSS | 用户界面 |
| 代码解析 | Tree-sitter | 多语言代码解析 |
| 向量存储 | ChromaDB | 代码向量化存储 |
| 数据库 | SQLite | 元数据存储 |
| LLM | OpenAI API / Claude API | 智能问答 |

### 1.3 核心流程

1. 用户导入项目 → 后端复制代码到数据目录
2. 触发代码解析 → 提取结构信息（函数、类、依赖）
3. 代码向量化 → 存入ChromaDB
4. 用户提问 → RAG检索相关代码片段 → LLM生成答案
5. 前端实时显示进度和结果

---

## 第二部分：阶段1 - 基础框架实现 (第1-4天)

### 2.1 后端核心功能

**任务清单**:
- ✅ FastAPI框架已搭建
- 🔄 完善项目导入API（本地目录 + URL）
- 🔄 数据库模型优化（Project, File, Chat等）
- 🔄 WebSocket进度推送完善
- 🔄 配置管理系统

**数据模型**:

```python
# Project模型
class Project:
    id: str
    name: str
    source_type: str  # local, github, gitlab, gitee, git, zip
    source_url: str
    local_path: str
    branch: str
    status: str  # indexing, ready, error
    file_count: int
    line_count: int
    created_at: datetime
    updated_at: datetime

# File模型
class File:
    id: str
    project_id: str
    file_path: str
    language: str
    functions: JSON
    classes: JSON
    imports: JSON
    line_count: int

# Chat模型
class ChatSession:
    id: str
    project_id: str
    question: str
    answer: str
    mode: str  # implementation, planning, hybrid
    context: JSON
    created_at: datetime
```

### 2.2 前端核心功能

**页面结构**:
```
/                    # 项目列表页
/projects/import     # 项目导入页
/projects/{id}       # 项目详情页
/projects/{id}/chat  # 智能问答页
```

**核心组件**:
- ProjectList: 项目列表展示
- ImportDialog: 项目导入对话框
- ProjectDetail: 项目详情展示
- ChatInterface: 智能问答界面
- ProgressBar: 解析进度显示

### 2.3 优先级排序

**P0（必须）**:
- 项目导入功能（本地 + URL）
- 数据库模型（Project, File, Chat）
- 基础前端页面（列表、导入、详情）
- WebSocket进度推送

**P1（重要）**:
- 配置管理系统
- 错误处理和日志
- Docker优化

**P2（优化）**:
- UI美化
- 性能优化

---

## 第三部分：阶段2 - 代码解析引擎实现 (第5-9天)

### 3.1 Tree-sitter集成

**解析器架构**:
```python
class BaseParser(ABC):
    @abstractmethod
    def parse(self, content: str, file_path: str) -> ParseResult
    
class PythonParser(BaseParser):
    # 提取: 函数、类、方法、导入、变量、注释
    
class TypeScriptParser(BaseParser):
    # 提取: 函数、类、接口、类型、导入
```

**提取信息**:
- 函数信息: name, parameters, return_type, docstring, body
- 类信息: name, methods, attributes, docstring
- 导入信息: module, names, alias
- 位置信息: start_line, end_line, file_path

### 3.2 代码结构提取

**文件类型支持**:
- `.py` - Python
- `.js` - JavaScript
- `.ts` - TypeScript
- `.tsx` - TypeScript React
- `.jsx` - JavaScript React

**结构摘要**:
```json
{
  "total_files": 50,
  "total_functions": 200,
  "total_classes": 30,
  "by_language": {
    "python": 20,
    "typescript": 30
  }
}
```

### 3.3 高级分析功能

**调用链分析**:
- 函数调用关系图
- 调用深度分析
- 循环依赖检测

**依赖关系分析**:
- 模块依赖图
- 区分内部/外部依赖
- 依赖冲突检测

**增量索引**:
- 文件变更检测（MD5哈希）
- 只重新解析修改的文件
- 删除已移除文件的索引

### 3.4 向量化处理

**代码分块策略**:
```python
# 按函数/类分块
def chunk_code(parse_result):
    chunks = []
    for func in parse_result.functions:
        chunks.append({
            "content": func.body,
            "metadata": {
                "type": "function",
                "name": func.name,
                "file": parse_result.file_path,
                "lines": f"{func.start_line}-{func.end_line}",
                "language": parse_result.language
            }
        })
    return chunks
```

**向量化流程**:
1. 代码分块（按函数/类）
2. 调用OpenAI Embedding API
3. 存储到ChromaDB（向量 + 元数据）
4. 建立索引加速检索

**优先级排序**:

**P0（必须）**:
- Python解析器
- JavaScript/TypeScript解析器
- 代码结构提取
- 基础向量化

**P1（重要）**:
- 调用链分析
- 依赖分析
- 增量索引

**P2（优化）**:
- 性能优化
- 错误恢复
- 解析结果缓存

---

## 第四部分：阶段3 - RAG智能问答实现 (第10-13天)

### 4.1 向量检索系统

**ChromaDB集成**:
```python
# 初始化
client = chromadb.Client()
collection = client.create_collection("code_chunks")

# 添加向量
collection.add(
    embeddings=[embedding],
    documents=[code_chunk],
    metadatas=[metadata],
    ids=[chunk_id]
)

# 检索
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=5
)
```

**检索策略**:
- **语义检索**: 使用向量相似度（余弦相似度）
- **关键词检索**: 文件名、函数名匹配
- **混合检索**: 结合语义和关键词（权重: 0.7 + 0.3）

### 4.2 问答系统

**问题理解**:
```python
def classify_question(question: str) -> str:
    # 实现型: "这个功能是如何实现的？"
    if any(kw in question for kw in ["如何实现", "怎么工作", "代码"]):
        return "implementation"
    
    # 规划型: "如何添加新功能？"
    elif any(kw in question for kw in ["如何添加", "怎么扩展", "怎么实现"]):
        return "planning"
    
    # 混合型: "项目整体架构是什么？"
    else:
        return "hybrid"
```

**上下文构建**:
```python
def build_context(question: str, project_id: str) -> str:
    # 1. 检索相关代码片段
    chunks = retrieve_relevant_code(question, project_id, top_k=5)
    
    # 2. 构建上下文
    context = "以下是相关的代码片段:\n\n"
    for i, chunk in enumerate(chunks, 1):
        context += f"[{i}] {chunk['metadata']['file']}:{chunk['metadata']['lines']}\n"
        context += f"```{chunk['metadata']['language']}\n{chunk['content']}\n```\n\n"
    
    return context
```

**Prompt模板**:
```
你是一个代码助手，帮助用户理解代码库。基于以下代码片段回答问题。

代码上下文:
{context}

用户问题: {question}

请提供清晰、准确的回答，并在适当的地方引用代码片段。如果问题需要修改代码，请提供具体的实施步骤。
```

### 4.3 三种问答模式

**实现型问答**:
- 问题: "用户认证是如何实现的？"
- 回答: 返回具体代码 + 解释实现逻辑
- 代码引用: 可点击跳转到代码位置

**规划型问答**:
- 问题: "如何添加新的编程语言支持？"
- 回答: 返回实施计划 + 步骤指南
- 相关代码: 展示现有实现作为参考

**混合型问答**:
- 问题: "项目的整体架构是什么？"
- 回答: 返回概览 + 关键组件说明
- 可视化: 架构图或流程图

### 4.4 对话管理

**会话历史**:
```python
class ChatSession:
    id: str
    project_id: str
    messages: List[Message]
    created_at: datetime
    
class Message:
    role: str  # user, assistant
    content: str
    code_refs: List[CodeRef]  # 代码引用
    timestamp: datetime
```

**多轮对话**:
```python
def chat_with_context(session_id: str, question: str):
    # 1. 获取会话历史
    history = get_session_history(session_id)
    
    # 2. 结合历史构建上下文
    context = build_context_with_history(question, history)
    
    # 3. 调用LLM
    answer = llm.generate(context, question)
    
    # 4. 保存到历史
    save_message(session_id, question, answer)
    
    return answer
```

**优先级排序**:

**P0（必须）**:
- 基础RAG检索
- 单轮问答
- 实现型问答

**P1（重要）**:
- 多轮对话
- 三种问答模式
- 代码引用跳转

**P2（优化）**:
- 检索质量优化
- 响应速度优化
- 答案质量评估

---

## 第五部分：API接口设计

### 5.1 项目管理 API

```http
POST   /api/v1/projects
请求: { "name": "my-project", "source_type": "local", "local_path": "/path/to/project" }
响应: { "code": 200, "data": { "id": "abc123", "status": "indexing" } }

POST   /api/v1/projects/import
请求: { "type": "github", "url": "https://github.com/user/repo", "branch": "main" }
响应: { "code": 200, "data": { "id": "def456", "status": "indexing" } }

GET    /api/v1/projects
响应: { "code": 200, "data": { "items": [...], "total": 10 } }

GET    /api/v1/projects/{id}
响应: { "code": 200, "data": { "id": "abc123", "name": "my-project", ... } }

DELETE /api/v1/projects/{id}
响应: { "code": 200, "message": "Project deleted" }

POST   /api/v1/projects/{id}/reindex
响应: { "code": 200, "data": { "status": "indexing" } }
```

### 5.2 代码解析 API

```http
POST   /api/v1/parser/parse/{project_id}
响应: { "code": 200, "data": { "status": "parsing" } }

GET    /api/v1/parser/status/{project_id}
响应: { 
  "code": 200, 
  "data": { 
    "status": "parsing", 
    "progress": 50,
    "message": "Parsing Python files..."
  } 
}

GET    /api/v1/parser/structure/{project_id}
响应: { 
  "code": 200, 
  "data": { 
    "total_files": 50,
    "total_functions": 200,
    "total_classes": 30,
    "by_language": { "python": 20, "typescript": 30 }
  } 
}

GET    /api/v1/parser/call-graph/{project_id}
响应: { "code": 200, "data": { "nodes": [...], "edges": [...] } }

GET    /api/v1/parser/dependencies/{project_id}
响应: { "code": 200, "data": { "internal": {...}, "external": {...} } }
```

### 5.3 智能问答 API

```http
POST   /api/v1/chat/query
请求: { 
  "project_id": "abc123",
  "question": "这个项目的主要功能是什么？",
  "mode": "hybrid",
  "session_id": "optional"
}
响应: { 
  "code": 200, 
  "data": { 
    "answer": "...",
    "code_refs": [
      { "file": "main.py", "lines": "10-20", "content": "..." }
    ],
    "session_id": "xyz789"
  } 
}

GET    /api/v1/chat/sessions?project_id=abc123
响应: { "code": 200, "data": { "items": [...] } }

GET    /api/v1/chat/sessions/{id}
响应: { "code": 200, "data": { "messages": [...] } }

DELETE /api/v1/chat/sessions/{id}
响应: { "code": 200, "message": "Session deleted" }
```

### 5.4 WebSocket 端点

```javascript
// 导入进度
const ws = new WebSocket('ws://localhost:8000/ws/import/{project_id}');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // data: { event: "progress", data: { stage, progress, message } }
};

// 解析进度
const ws = new WebSocket('ws://localhost:8000/ws/parse/{project_id}');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // data: { event: "progress", data: { stage, progress, message } }
};
```

### 5.5 统一响应格式

**成功响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    // 实际数据
  }
}
```

**错误响应**:
```json
{
  "code": 400,
  "message": "Invalid request parameters",
  "error": {
    "type": "ValidationError",
    "details": "name is required"
  }
}
```

**HTTP状态码**:
- 200: 成功
- 201: 创建成功
- 400: 请求参数错误
- 404: 资源不存在
- 500: 服务器内部错误

---

## 第六部分：实施计划与验收标准

### 6.1 总体时间规划

| 阶段 | 时间 | 主要任务 | 里程碑 |
|------|------|----------|--------|
| Phase 1 | 第1-4天 | 基础框架 | 可导入项目，前后端通信正常 |
| Phase 2 | 第5-9天 | 代码解析引擎 | 可解析代码，提取结构信息 |
| Phase 3 | 第10-13天 | RAG智能问答 | 可通过自然语言提问获得答案 |
| 集成测试 | 第14天 | 端到端测试 | 整体流程流畅无阻 |

### 6.2 关键里程碑

**里程碑1（第4天）**:
- ✅ 可以通过前端导入项目（本地目录 + GitHub URL）
- ✅ 后端API可正常响应（/health, /api/v1/projects）
- ✅ WebSocket实时推送导入进度
- ✅ 前端可查看项目列表和详情
- ✅ Docker容器可正常启动

**里程碑2（第9天）**:
- ✅ 可以解析Python代码（提取函数、类、导入）
- ✅ 可以解析JavaScript/TypeScript代码
- ✅ 代码已向量化存储到ChromaDB
- ✅ 可查看代码结构统计（文件数、函数数、类数）
- ✅ 可查看调用图和依赖关系

**里程碑3（第13天）**:
- ✅ 可以通过自然语言提问
- ✅ 获得基于代码的智能回答
- ✅ 支持多轮对话
- ✅ 代码引用可点击跳转
- ✅ 支持三种问答模式

### 6.3 验收标准

**功能验收**:
1. ✅ 导入一个真实项目（如CodeInsight项目本身）
2. ✅ 自动解析并提取代码结构
3. ✅ 提问"这个项目的主要功能是什么？"获得准确回答
4. ✅ 提问"如何添加新的编程语言支持？"获得实施建议
5. ✅ 提问"用户认证是如何实现的？"获得具体代码解释

**性能验收**:
- 项目导入时间 < 30秒（1000个文件）
- 代码解析时间 < 2分钟（1000个文件）
- 向量化时间 < 5分钟（1000个函数/类）
- 问答响应时间 < 5秒

**稳定性验收**:
- API响应成功率 > 99%
- 前端页面无崩溃
- WebSocket连接稳定
- 错误处理完善

### 6.4 风险管理

**技术风险**:
- Tree-sitter解析器兼容性问题 → 提前测试多种代码格式
- ChromaDB性能问题 → 设计合理的索引策略
- LLM API限制 → 实现请求限流和重试机制

**进度风险**:
- 功能复杂度超出预期 → 优先实现P0功能，P1/P2功能可后续迭代
- 第三方依赖问题 → 准备备选方案（如不同的LLM提供商）

### 6.5 后续优化方向

**Phase 4（未来）**:
- 可视化功能（架构图、流程图）
- 更多编程语言支持（Go, Rust, Java等）
- 代码质量分析
- 性能优化（缓存、并行处理）
- 部署优化（Kubernetes、云服务）

---

## 附录

### A. 技术栈详情

**后端依赖**:
```
fastapi==0.109.0
uvicorn==0.27.0
sqlalchemy==2.0.25
pydantic==2.5.3
pydantic-settings==2.1.0
tree-sitter==0.20.4
tree-sitter-python==0.20.4
tree-sitter-javascript==0.20.1
tree-sitter-typescript==0.20.3
chromadb==0.4.22
openai==1.10.0
python-git==2024.1.1
```

**前端依赖**:
```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "react-router-dom": "^6.21.3",
  "zustand": "^4.5.0",
  "axios": "^1.6.5",
  "tailwindcss": "^3.4.1"
}
```

### B. 环境配置

**.env文件**:
```env
# 应用配置
DEBUG=true
APP_NAME=CodeInsight
VERSION=1.0.0

# 数据库
DATABASE_URL=sqlite:///./data/codeinsight.db

# 存储路径
DATA_DIR=./data
PROJECTS_DIR=./data/projects
CHROMA_DIR=./data/chroma

# LLM配置
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4
EMBEDDING_MODEL=text-embedding-3-small

# 解析配置
MAX_FILE_SIZE=10485760
SUPPORTED_EXTENSIONS=.py,.js,.ts,.tsx,.jsx
```

### C. 开发规范

**Git提交规范**:
```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式
refactor: 重构
test: 测试
chore: 构建/工具
```

**分支管理**:
```
main - 主分支
develop - 开发分支
feature/phase-N-name - 功能分支
hotfix/xxx - 紧急修复
```

---

## 批准记录

**设计批准人**: 用户  
**批准日期**: 2026-02-21  
**下一步**: 执行writing-plans技能，创建详细的实施计划

---

**文档结束**
