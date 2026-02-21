# 本地代码库智能检测与知识问答系统 - 需求文档

版本：v1.0  
创建日期：2024-01-15  
最后更新：2024-01-15

---

## 1. 项目概述

### 1.1 项目名称

**CodeInsight** - 本地代码库智能检测与知识问答系统

### 1.2 项目目标

构建一个基于 LLM 的智能代码分析平台，帮助开发者：

1. 快速理解陌生代码库
2. 基于代码库进行精准问答
3. 自动提取项目功能点
4. 生成项目文档和可视化图表

### 1.3 目标用户

- 需要快速上手新项目的开发者
- 需要维护遗留代码的工程师
- 需要生成项目文档的技术团队
- 需要进行代码审查的团队

---

## 2. 核心功能需求

### 2.1 项目导入

#### 2.1.1 导入方式

| 方式 | 说明 | 技术实现 |
|------|------|----------|
| 本地目录 | 选择本地文件夹路径 | os.walk 遍历 |
| GitHub | `https://github.com/user/repo` | GitPython 克隆 |
| GitHub (私有) | 带Token的URL | Token认证 |
| GitLab | `https://gitlab.com/user/repo` | GitPython 克隆 |
| Gitee | `https://gitee.com/user/repo` | GitPython 克隆 |
| 任意Git | `git://` 或 `https://xxx.git` | GitPython 克隆 |
| ZIP压缩包 | 远程ZIP URL下载 | requests + zipfile |

#### 2.1.2 导入功能

- 支持指定分支（默认 main）
- 支持浅克隆（depth参数）
- 导入进度实时反馈（WebSocket）
- 支持大文件过滤（.gitignore 规则）

#### 2.1.3 导入参数

```json
{
  "type": "github" | "git" | "local" | "zip",
  "url": "https://github.com/user/repo",
  "branch": "main",
  "token": "ghp_xxx",
  "depth": 1,
  "local_path": "/path/to/project"
}
```

---

### 2.2 问答系统

#### 2.2.1 问答模式

系统支持三种问答模式：

| 模式 | 名称 | 回答策略 | 适用场景 |
|------|------|----------|----------|
| `implementation` | 实现型 | **严格基于项目已有代码回答**，无法回答时明确说明 | 理解当前系统、排查问题、学习代码 |
| `planning` | 规划型 | **基于LLM行业知识回答**，不依赖代码库 | 架构设计、技术选型、最佳实践咨询 |
| `hybrid` | 混合型 | **先说明现状，再提供改进建议** | 功能优化、重构规划、技术升级 |

#### 2.2.2 实现型问答规则

1. **只使用 RAG 检索到的代码片段作为上下文**
2. **相关性阈值**：相似度低于 0.7 时，返回"项目中未找到相关信息"
3. **引用溯源**：每个回答必须标注 `[来源: file_path:行号]`
4. **拒绝幻觉**：禁止使用 LLM 通用知识进行推测

#### 2.2.3 规划型问答规则

1. 不使用代码库上下文
2. 直接使用 LLM 的行业知识
3. 提供最佳实践和行业标准建议

#### 2.2.4 混合型问答规则

1. 先检索并说明当前实现状态
2. 再基于 LLM 知识提供改进建议
3. 明确区分"现状"和"建议"

#### 2.2.5 问答示例

**问题**：用户登录应该怎么实现？

**实现型回答**：
```
根据当前项目代码，登录功能已实现如下：
- 认证接口：POST /api/auth/login [来源: backend/services/auth.py:45]
- 密码验证：bcrypt哈希比对 [来源: backend/services/auth.py:52-58]
- Token生成：JWT RS256算法 [来源: backend/services/token_service.py:23]

当前项目暂未实现SSO单点登录。
```

**规划型回答**：
```
用户登录的行业标准实现建议：

1. 认证方式选择：
   - Session + Cookie：传统Web应用
   - JWT Token：前后端分离/API服务
   - OAuth2.0：第三方登录集成

2. 安全措施：
   - 密码哈希：bcrypt 或 argon2
   - 防护机制：登录限流、验证码、密码强度检测
   - Token安全：短期有效、刷新机制

3. 推荐扩展：
   - SSO单点登录（SAML/OIDC）
   - 双因素认证（2FA）
   - 设备绑定与异常登录检测
```

**混合型回答**：
```
📍 当前实现状态：
- 已有基础账号密码登录 [来源: auth.py:45-68]
- JWT Token机制已实现 [来源: token_service.py]
- 密码使用bcrypt哈希存储 [来源: auth.py:52]

💡 改进建议：
1. 添加登录限流（推荐 Redis + 令牌桶算法）
2. 考虑集成SSO单点登录（当前未实现）
3. 增加双因素认证选项
4. 添加登录日志和异常检测
```

---

### 2.3 功能分析

#### 2.3.1 前端功能分析

**识别维度**：

| 维度 | 解析方式 | 提取内容 |
|------|----------|----------|
| 路由/页面 | 解析路由配置文件 | 路由路径、页面名称、权限要求 |
| 页面功能 | 组件+事件分析 | 按钮操作、表单提交、数据展示 |
| API调用 | 请求代码分析 | 调用的后端接口、参数格式 |
| 组件 | 组件定义解析 | 公共组件、业务组件清单 |

**前端功能树示例**：

```
📱 前端功能
├── 🏠 首页 (/)
│   ├── 功能：数据概览展示
│   ├── 组件：Dashboard, Statistics
│   └── API：GET /api/overview
│
├── 👤 用户管理
│   ├── 列表页 (/users)
│   │   ├── 功能：用户列表、搜索、筛选
│   │   └── API：GET /api/users
│   │
│   └── 详情页 (/users/:id)
│       ├── 功能：查看/编辑用户信息
│       └── API：GET/PUT /api/users/:id
│
└── 🔐 认证模块
    ├── 登录页 (/login)
    └── 注册页 (/register)
```

#### 2.3.2 后端功能分析

**识别维度**：

| 类别 | 识别方式 | 示例 |
|------|----------|------|
| API接口 | 路由装饰器解析 | `@router.get("/users")` |
| 系统功能 | 框架特征识别 | 中间件、定时任务、SSO、缓存 |
| 数据模型 | ORM模型解析 | SQLAlchemy, Prisma, GORM |
| 业务服务 | Service类分析 | 核心业务逻辑封装 |

**后端功能清单示例**：

```
⚙️ 后端功能
│
├── 📡 API接口 (23个)
│   ├── 认证模块 /api/auth
│   │   ├── POST   /login          用户登录
│   │   ├── POST   /logout         用户登出
│   │   └── POST   /refresh        Token刷新
│   │
│   └── 用户模块 /api/users
│       ├── GET    /               用户列表
│       ├── POST   /               创建用户
│       └── DELETE /:id            删除用户
│
├── 🔧 系统功能
│   ├── ⏰ 定时任务 (3个)
│   │   ├── cleanup_logs          每日清理日志
│   │   ├── sync_data             每小时数据同步
│   │   └── send_notifications    每5分钟通知推送
│   │
│   ├── 🔐 SSO单点登录
│   │   ├── 协议：OAuth 2.0
│   │   └── 提供商：企业微信、钉钉
│   │
│   ├── 🛡️ 中间件 (5个)
│   │   ├── AuthMiddleware        认证校验
│   │   ├── CORSMiddleware        跨域处理
│   │   ├── RateLimitMiddleware   请求限流
│   │   ├── LoggingMiddleware     日志记录
│   │   └── ErrorMiddleware       异常处理
│   │
│   └── 📦 缓存 (Redis)
│
└── 💾 数据模型 (12个)
    ├── User              用户表
    ├── Role              角色表
    └── Permission        权限表
```

#### 2.3.3 系统功能识别规则

```python
SYSTEM_FEATURES = {
    "scheduled_tasks": {
        "python": ["@scheduler.task", "@celery.task", "APScheduler", "schedule"],
        "nodejs": ["cron.schedule", "node-cron", "agenda.schedule", "bull"],
    },
    "sso": {
        "python": ["flask_sso", "django-allauth", "authlib", "python-saml"],
        "nodejs": ["passport-saml", "passport-oauth2", "openid-client"],
    },
    "middleware": {
        "patterns": ["@middleware", "Middleware", "app.use(", "add_middleware"],
    },
    "cache": {
        "libraries": ["redis", "memcached", "cachetools", "lru_cache"],
    },
    "message_queue": {
        "libraries": ["celery", "rabbitmq", "kafka", "bull", "bullmq"],
    },
    "file_storage": {
        "libraries": ["boto3", "minio", "oss2", "aws-sdk", "@aws-sdk"],
    },
    "database": {
        "orm": ["sqlalchemy", "prisma", "typeorm", "gorm", "sequelize"],
    }
}
```

---

### 2.4 文档生成

#### 2.4.1 文档类型

| 类型 | 内容 | 输出格式 |
|------|------|----------|
| API文档 | 接口列表、参数说明、响应格式 | Markdown / OpenAPI |
| 架构文档 | 系统架构、模块划分、技术栈 | Markdown |
| README | 项目说明、快速开始、配置说明 | Markdown |
| 流程文档 | 关键业务流程描述 | Markdown + 流程图 |

#### 2.4.2 图表生成

| 图表类型 | 用途 | 技术实现 |
|----------|------|----------|
| 流程图 | 关键函数执行流程 | LLM → Mermaid语法 |
| 架构图 | 模块/组件关系 | LLM → Mermaid语法 |
| 调用图 | 函数调用链 | AST分析 → 可视化 |
| 依赖图 | 包/模块依赖关系 | import分析 → 可视化 |

---

### 2.5 代码搜索

#### 2.5.1 搜索类型

- **语义搜索**：基于向量相似度的代码片段搜索
- **关键词搜索**：基于文件名、函数名的搜索
- **结构搜索**：按类、函数、模块过滤

#### 2.5.2 搜索结果

- 代码片段预览
- 文件路径和行号
- 相似度评分

---

## 3. 技术栈

### 3.1 后端技术

| 组件 | 技术 | 版本 | 用途 |
|------|------|------|------|
| Web框架 | FastAPI | 0.104+ | RESTful API |
| 代码解析 | Tree-sitter | 0.20+ | 多语言AST解析 |
| 向量存储 | ChromaDB | 0.4+ | 代码向量检索 |
| LLM集成 | LangChain | 0.1+ | LLM应用框架 |
| ORM | SQLAlchemy | 2.0+ | 数据库操作 |
| 任务队列 | Celery | 5.3+ | 异步任务处理 |

### 3.2 前端技术

| 组件 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 框架 | React | 18+ | UI框架 |
| 构建 | Vite | 5.0+ | 构建工具 |
| 语言 | TypeScript | 5.0+ | 类型安全 |
| 样式 | TailwindCSS | 3.4+ | CSS框架 |
| UI组件 | shadcn/ui | - | 组件库 |
| 图表 | Mermaid.js | 10+ | 流程图渲染 |
| 状态 | Zustand | 4+ | 状态管理 |

### 3.3 基础设施

| 组件 | 技术 | 用途 |
|------|------|------|
| 容器 | Docker | 应用容器化 |
| 编排 | Docker Compose | 多容器管理 |
| 数据库 | PostgreSQL / SQLite | 元数据存储 |
| 缓存 | Redis | 可选，用于缓存 |

---

## 4. 非功能需求

### 4.1 性能需求

| 指标 | 要求 |
|------|------|
| 代码库规模 | 支持 10-50 万行代码 |
| 解析速度 | 1万行/分钟（首次索引） |
| 搜索响应 | < 2秒 |
| 问答响应 | < 10秒（流式输出） |

### 4.2 部署需求

- 支持 Docker 容器化部署
- 支持本地单机运行
- 支持服务器部署

### 4.3 安全需求

- API Key 等敏感信息不硬编码
- 私有仓库Token加密存储
- 用户数据本地存储，不上传云端

---

## 5. 交互界面

### 5.1 主要页面

| 页面 | 功能 |
|------|------|
| 项目管理 | 项目列表、导入项目、项目详情 |
| 代码问答 | 三种模式问答、对话历史 |
| 功能分析 | 前后端功能树、功能详情 |
| 代码搜索 | 语义搜索、结果展示 |
| 文档中心 | 文档列表、文档预览、导出 |
| 可视化 | 流程图、架构图、调用图 |

### 5.2 问答界面设计

```
┌─────────────────────────────────────────────────────────┐
│  💬 代码问答                                             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  问答模式：  ● 实现型  ○ 规划型  ○ 混合型               │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 用户登录功能是如何实现的？                        │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  [发送]                                                 │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  🤖 回答：                                              │
│                                                         │
│  根据代码分析，用户登录实现如下：                        │
│  1. 接口定义 [auth.py:45]                              │
│  2. 密码验证 [auth.py:52-58]                           │
│  ...                                                    │
│                                                         │
│  📎 引用文件：                                          │
│  - backend/services/auth.py                            │
│  - backend/services/token_service.py                   │
└─────────────────────────────────────────────────────────┘
```

---

## 6. 里程碑规划

| 阶段 | 时间 | 主要交付物 |
|------|------|------------|
| Phase 1 | 1-2周 | 基础框架、项目导入 |
| Phase 2 | 1-2周 | 代码解析引擎 |
| Phase 3 | 1-2周 | 功能分析模块 |
| Phase 4 | 2-3周 | RAG问答系统 |
| Phase 5 | 1-2周 | 可视化与文档 |
| Phase 6 | 1周 | 优化与完善 |

---

## 7. 附录

### 7.1 术语表

| 术语 | 说明 |
|------|------|
| AST | 抽象语法树 |
| RAG | 检索增强生成 |
| LLM | 大语言模型 |
| Embedding | 向量嵌入 |
| SSO | 单点登录 |

### 7.2 参考文档

- [Tree-sitter 文档](https://tree-sitter.github.io/tree-sitter/)
- [LangChain 文档](https://python.langchain.com/)
- [ChromaDB 文档](https://www.trychroma.com/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
