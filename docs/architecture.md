# 系统架构设计

版本：v1.0  
创建日期：2024-01-15

---

## 1. 整体架构

### 1.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户界面层                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ 项目管理  │ │ 代码问答  │ │ 功能分析  │ │ 文档中心  │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│                        React + TypeScript                       │
└─────────────────────────────────────────────────────────────────┘
                              │ HTTP / WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        API 网关层                               │
│                    FastAPI + 中间件                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 认证 │ 限流 │ 日志 │ CORS │ 错误处理 │                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        业务服务层                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ 项目服务  │ │ 解析服务  │ │ 问答服务  │ │ 文档服务  │          │
│  │          │ │          │ │          │ │          │          │
│  │ - 导入   │ │ - AST解析 │ │ - RAG检索 │ │ - 生成   │          │
│  │ - 索引   │ │ - 调用分析 │ │ - LLM调用 │ │ - 导出   │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        核心引擎层                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ 代码解析  │ │ 功能分析  │ │ 向量检索  │ │ LLM服务  │          │
│  │ 引擎     │ │ 引擎     │ │ 引擎     │ │         │          │
│  │          │ │          │ │          │ │         │          │
│  │Tree-sitter│ │ 路由解析  │ │ ChromaDB │ │OpenAI   │          │
│  │ 多语言   │ │ 特征识别  │ │ Embedding│ │Claude   │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        数据存储层                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ 元数据库  │ │ 向量存储  │ │ 文件存储  │ │ 缓存    │          │
│  │ SQLite   │ │ ChromaDB │ │ 本地文件  │ │ Redis   │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 技术栈分层

| 层级 | 技术 | 职责 |
|------|------|------|
| 前端 | React + TypeScript + TailwindCSS | 用户界面、交互逻辑 |
| API层 | FastAPI | RESTful API、WebSocket |
| 解析层 | Tree-sitter + AST分析 | 代码结构解析 |
| 检索层 | ChromaDB + LangChain | 向量存储、语义检索 |
| LLM层 | OpenAI / Claude API | 智能问答、文档生成 |
| 存储层 | SQLite / PostgreSQL | 元数据、索引数据 |

---

## 2. 模块设计

### 2.1 后端模块结构

```
backend/
├── app/
│   ├── main.py                 # 应用入口
│   ├── core/                   # 核心配置
│   │   ├── config.py          # 配置管理
│   │   ├── security.py        # 安全相关
│   │   └── logging.py         # 日志配置
│   │
│   ├── api/                    # API路由
│   │   ├── projects.py        # 项目管理API
│   │   ├── chat.py            # 问答API
│   │   ├── search.py          # 搜索API
│   │   ├── features.py        # 功能分析API
│   │   ├── docs.py            # 文档API
│   │   └── graph.py           # 图表API
│   │
│   ├── models/                 # 数据模型
│   │   ├── project.py         # 项目模型
│   │   ├── file.py            # 文件模型
│   │   ├── chat.py            # 对话模型
│   │   └── feature.py         # 功能模型
│   │
│   ├── parsers/                # 代码解析器
│   │   ├── base.py            # 解析器基类
│   │   ├── python_parser.py   # Python解析
│   │   ├── js_parser.py       # JavaScript解析
│   │   ├── ts_parser.py       # TypeScript解析
│   │   └── factory.py         # 解析器工厂
│   │
│   ├── analysis/               # 功能分析模块
│   │   ├── frontend_analyzer.py   # 前端分析
│   │   ├── backend_analyzer.py    # 后端分析
│   │   ├── route_parser.py        # 路由解析
│   │   ├── api_extractor.py       # API提取
│   │   └── feature_detector.py    # 系统功能检测
│   │
│   ├── rag/                    # RAG检索模块
│   │   ├── embedder.py        # 向量化
│   │   ├── retriever.py       # 检索器
│   │   └── indexer.py         # 索引管理
│   │
│   ├── llm/                    # LLM服务模块
│   │   ├── base.py            # LLM基类
│   │   ├── openai_service.py  # OpenAI服务
│   │   ├── claude_service.py  # Claude服务
│   │   └── prompts.py         # Prompt模板
│   │
│   ├── graph/                  # 知识图谱模块
│   │   ├── call_graph.py      # 调用图
│   │   ├── dependency_graph.py # 依赖图
│   │   └── flow_generator.py  # 流程图生成
│   │
│   ├── docs/                   # 文档生成模块
│   │   ├── api_doc.py         # API文档
│   │   ├── readme_gen.py      # README生成
│   │   └── exporter.py        # 导出器
│   │
│   └── services/               # 业务服务
│       ├── project_service.py # 项目服务
│       ├── chat_service.py    # 问答服务
│       └── import_service.py  # 导入服务
│
├── tests/                      # 测试
├── requirements.txt            # 依赖
└── Dockerfile                  # Docker配置
```

### 2.2 前端模块结构

```
frontend/
├── src/
│   ├── main.tsx               # 入口文件
│   ├── App.tsx                # 应用组件
│   │
│   ├── components/            # 组件
│   │   ├── ui/               # 基础UI组件
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   └── Modal.tsx
│   │   │
│   │   ├── chat/             # 问答组件
│   │   │   ├── ChatInput.tsx
│   │   │   ├── ChatMessage.tsx
│   │   │   └── ModeSelector.tsx
│   │   │
│   │   ├── features/         # 功能分析组件
│   │   │   ├── FeatureTree.tsx
│   │   │   ├── APITable.tsx
│   │   │   └── SystemFeatures.tsx
│   │   │
│   │   └── graph/            # 图表组件
│   │       ├── MermaidChart.tsx
│   │       └── CallGraph.tsx
│   │
│   ├── pages/                 # 页面
│   │   ├── Projects.tsx      # 项目管理
│   │   ├── Chat.tsx          # 代码问答
│   │   ├── Features.tsx      # 功能分析
│   │   ├── Search.tsx        # 代码搜索
│   │   ├── Docs.tsx          # 文档中心
│   │   └── Graph.tsx         # 可视化
│   │
│   ├── services/              # API服务
│   │   ├── api.ts            # API客户端
│   │   ├── project.ts        # 项目API
│   │   ├── chat.ts           # 问答API
│   │   └── websocket.ts      # WebSocket
│   │
│   ├── hooks/                 # 自定义Hooks
│   │   ├── useChat.ts        # 问答Hook
│   │   └── useProject.ts     # 项目Hook
│   │
│   ├── stores/                # 状态管理
│   │   ├── projectStore.ts   # 项目状态
│   │   └── chatStore.ts      # 问答状态
│   │
│   ├── types/                 # 类型定义
│   │   ├── project.ts
│   │   ├── chat.ts
│   │   └── feature.ts
│   │
│   └── utils/                 # 工具函数
│       ├── format.ts
│       └── highlight.ts
│
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── Dockerfile
```

---

## 3. 数据流设计

### 3.1 项目导入流程

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  前端    │────▶│  API层   │────▶│ 导入服务 │────▶│ Git/文件 │
│ 上传URL  │     │ 验证参数 │     │ 创建任务 │     │ 克隆/复制│
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                                                          │
      ┌───────────────────────────────────────────────────┘
      ▼
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ 解析服务 │────▶│Tree-sitter│────▶│ 功能分析 │────▶│ 向量索引 │
│ 遍历文件 │     │ AST解析   │     │ 提取功能 │     │ Embedding│
└──────────┘     └──────────┘     └──────────┘     └──────────┘
      │                                                 │
      └─────────────────────────────────────────────────┘
                              │
                              ▼
                        ┌──────────┐
                        │  完成    │
                        │ 通知前端 │
                        └──────────┘
```

### 3.2 问答处理流程

```
┌──────────┐
│ 用户提问 │
└────┬─────┘
     │
     ▼
┌──────────┐     ┌──────────────────────────────┐
│ 模式判断 │     │ implementation │ planning │ hybrid │
└────┬─────┘     └──────────────────────────────┘
     │
     ├─── implementation ────────────────────────┐
     │                                          ▼
     │                                 ┌──────────────┐
     │                                 │  RAG检索     │
     │                                 │ 相似度>0.7?  │
     │                                 └──────┬───────┘
     │                                        │
     │                              ┌────────┴────────┐
     │                              │ Yes             │ No
     │                              ▼                 ▼
     │                     ┌──────────────┐  ┌──────────────┐
     │                     │ 组装上下文   │  │ 返回"未找到" │
     │                     └──────┬───────┘  └──────────────┘
     │                            │
     ├─── planning ───────────────┼────────────────────┐
     │                            │                    ▼
     │                            │           ┌──────────────┐
     │                            │           │ 直接使用LLM  │
     │                            │           │ 行业知识     │
     │                            │           └──────┬───────┘
     │                            │                  │
     ├─── hybrid ─────────────────┼──────────────────┤
     │                            │                  │
     │                            ▼                  ▼
     │                     ┌──────────────┐  ┌──────────────┐
     │                     │ 现状分析     │  │ 改进建议     │
     │                     └──────┬───────┘  └──────┬───────┘
     │                            │                  │
     └────────────────────────────┴──────────────────┘
                                  │
                                  ▼
                         ┌──────────────┐
                         │  LLM生成     │
                         │  回答+引用   │
                         └──────────────┘
```

### 3.3 功能分析流程

```
┌─────────────────────────────────────────────────────────────┐
│                      代码库文件                              │
└─────────────────────────────────────────────────────────────┘
                           │
           ┌───────────────┴───────────────┐
           ▼                               ▼
┌─────────────────────┐          ┌─────────────────────┐
│     前端文件        │          │     后端文件        │
│  .tsx .vue .jsx    │          │  .py .js .ts .go   │
└─────────┬───────────┘          └─────────┬───────────┘
          │                                │
          ▼                                ▼
┌─────────────────────┐          ┌─────────────────────┐
│   前端解析器        │          │   后端解析器        │
├─────────────────────┤          ├─────────────────────┤
│ • 路由配置解析      │          │ • API路由提取       │
│ • 组件事件分析      │          │ • Service类识别     │
│ • API调用识别       │          │ • 中间件检测        │
│ • 页面功能提取      │          │ • 定时任务检测      │
└─────────┬───────────┘          │ • SSO检测          │
          │                      │ • 数据模型提取      │
          │                      └─────────┬───────────┘
          │                                │
          └───────────────┬────────────────┘
                          ▼
                 ┌─────────────────────┐
                 │    功能树构建       │
                 │  前端功能 + 后端功能 │
                 └─────────────────────┘
```

---

## 4. 数据模型设计

### 4.1 核心实体

```python
# 项目模型
class Project:
    id: str                    # 项目ID
    name: str                  # 项目名称
    source_type: str           # local | github | git | zip
    source_url: str | None     # 来源URL
    local_path: str            # 本地存储路径
    branch: str                # 分支
    status: str                # indexing | ready | error
    created_at: datetime
    updated_at: datetime
    file_count: int            # 文件数量
    line_count: int            # 代码行数

# 文件模型
class CodeFile:
    id: str
    project_id: str
    path: str                  # 相对路径
    language: str              # 编程语言
    content_hash: str          # 内容哈希
    ast_data: dict             # AST数据
    functions: list            # 函数列表
    classes: list              # 类列表
    imports: list              # 导入列表

# 功能模型
class Feature:
    id: str
    project_id: str
    type: str                  # page | api | system
    category: str              # frontend | backend
    name: str                  # 功能名称
    description: str           # 描述
    location: str              # 文件位置
    line_start: int
    line_end: int
    related_files: list        # 关联文件
    children: list             # 子功能

# 对话模型
class ChatSession:
    id: str
    project_id: str
    mode: str                  # implementation | planning | hybrid
    created_at: datetime
    messages: list

class ChatMessage:
    id: str
    session_id: str
    role: str                  # user | assistant
    content: str
    references: list           # 引用的代码位置
    created_at: datetime
```

### 4.2 向量存储模型

```python
# 代码片段向量
class CodeEmbedding:
    id: str
    project_id: str
    file_id: str
    chunk_type: str            # function | class | file
    content: str               # 原始代码
    embedding: list[float]     # 向量
    metadata: dict             # 元数据
    # - file_path
    # - line_start
    # - line_end
    # - language
    # - name (函数名/类名)
```

---

## 5. 接口设计

### 5.1 API 概览

| 模块 | 端点 | 方法 | 说明 |
|------|------|------|------|
| 项目 | `/api/projects` | GET | 项目列表 |
| 项目 | `/api/projects` | POST | 创建项目 |
| 项目 | `/api/projects/import` | POST | URL导入 |
| 项目 | `/api/projects/{id}` | GET | 项目详情 |
| 项目 | `/api/projects/{id}` | DELETE | 删除项目 |
| 问答 | `/api/chat` | POST | 发起问答 |
| 问答 | `/api/chat/stream` | POST | 流式问答 |
| 搜索 | `/api/search` | POST | 代码搜索 |
| 功能 | `/api/features/{project_id}` | GET | 功能列表 |
| 文档 | `/api/docs/{project_id}` | GET | 获取文档 |
| 文档 | `/api/docs/{project_id}/generate` | POST | 生成文档 |
| 图表 | `/api/graph/{project_id}/flow` | GET | 流程图 |
| 图表 | `/api/graph/{project_id}/arch` | GET | 架构图 |

### 5.2 WebSocket 接口

| 端点 | 用途 |
|------|------|
| `/ws/import/{project_id}` | 导入进度推送 |
| `/ws/chat/{session_id}` | 问答流式响应 |

---

## 6. 部署架构

### 6.1 Docker 部署

```yaml
# docker-compose.yml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
      
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

### 6.2 目录挂载

| 容器路径 | 宿主机路径 | 用途 |
|----------|------------|------|
| `/app/data/projects` | `./data/projects` | 上传的代码库 |
| `/app/data/chroma` | `./data/chroma` | 向量数据库 |
| `/app/data/logs` | `./data/logs` | 日志文件 |

---

## 7. 扩展性设计

### 7.1 语言扩展

通过 Tree-sitter 的语言绑定，支持扩展新语言：

```python
# 添加新语言解析器
LANGUAGE_PARSERS = {
    "python": PythonParser,
    "javascript": JavaScriptParser,
    "typescript": TypeScriptParser,
    # 扩展：
    "java": JavaParser,
    "go": GoParser,
    "rust": RustParser,
}
```

### 7.2 LLM 扩展

支持多种 LLM 后端：

```python
# 添加新 LLM 服务
LLM_SERVICES = {
    "openai": OpenAIService,
    "claude": ClaudeService,
    # 扩展：
    "azure": AzureOpenAIService,
    "local": LocalLLMService,  # Ollama 等
}
```

---

## 8. 安全设计

### 8.1 数据安全

- API Key 等敏感信息通过环境变量注入
- 私有仓库 Token 加密存储
- 代码库本地存储，不上传云端

### 8.2 访问控制

- API 可配置认证（可选）
- 限流保护

---

## 9. 性能优化

### 9.1 索引优化

- 增量索引：只更新变更文件
- 并行解析：多进程解析代码
- 批量向量化：批量 Embedding 生成

### 9.2 查询优化

- 向量索引优化（HNSW）
- 缓存热点查询结果
- 流式响应减少等待感
