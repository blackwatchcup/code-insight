# API 设计文档

版本：v1.0  
创建日期：2024-01-15

---

## 1. 概述

### 1.1 基本信息

| 项目 | 说明 |
|------|------|
| Base URL | `http://localhost:8000/api` |
| 数据格式 | JSON |
| 字符编码 | UTF-8 |
| 认证方式 | Bearer Token（可选） |

### 1.2 通用响应格式

#### 成功响应

```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

#### 错误响应

```json
{
  "code": 400,
  "message": "错误描述",
  "detail": "详细错误信息"
}
```

### 1.3 错误码定义

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 404 | 资源不存在 |
| 409 | 资源冲突（如项目已存在） |
| 500 | 服务器内部错误 |

---

## 2. 项目管理 API

### 2.1 获取项目列表

**请求**
```
GET /api/projects
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认1 |
| size | int | 否 | 每页数量，默认20 |
| status | string | 否 | 按状态过滤：indexing/ready/error |

**响应**
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": "proj_abc123",
        "name": "my-project",
        "source_type": "github",
        "source_url": "https://github.com/user/my-project",
        "status": "ready",
        "file_count": 150,
        "line_count": 25000,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:35:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "size": 20
  }
}
```

---

### 2.2 创建项目（本地目录）

**请求**
```
POST /api/projects
```

**请求体**
```json
{
  "name": "my-local-project",
  "source_type": "local",
  "local_path": "/path/to/project"
}
```

**响应**
```json
{
  "code": 200,
  "data": {
    "id": "proj_xyz789",
    "name": "my-local-project",
    "source_type": "local",
    "status": "indexing",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

---

### 2.3 URL 导入项目

**请求**
```
POST /api/projects/import
```

**请求体**
```json
{
  "type": "github",
  "url": "https://github.com/user/repo",
  "name": "custom-name",
  "branch": "main",
  "token": "ghp_xxx",
  "depth": 1
}
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是 | 导入类型：github/gitlab/gitee/git/zip |
| url | string | 是 | 项目URL |
| name | string | 否 | 自定义项目名，默认从URL提取 |
| branch | string | 否 | 分支，默认main |
| token | string | 否 | 私有仓库访问Token |
| depth | int | 否 | 克隆深度，默认1（浅克隆） |

**响应**
```json
{
  "code": 200,
  "data": {
    "id": "proj_abc123",
    "name": "repo",
    "source_type": "github",
    "source_url": "https://github.com/user/repo",
    "status": "indexing",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

---

### 2.4 获取项目详情

**请求**
```
GET /api/projects/{project_id}
```

**响应**
```json
{
  "code": 200,
  "data": {
    "id": "proj_abc123",
    "name": "my-project",
    "source_type": "github",
    "source_url": "https://github.com/user/repo",
    "local_path": "/data/projects/proj_abc123",
    "branch": "main",
    "status": "ready",
    "file_count": 150,
    "line_count": 25000,
    "languages": {
      "python": 60,
      "javascript": 30,
      "typescript": 10
    },
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:35:00Z"
  }
}
```

---

### 2.5 删除项目

**请求**
```
DELETE /api/projects/{project_id}
```

**响应**
```json
{
  "code": 200,
  "message": "项目已删除"
}
```

---

### 2.6 重建索引

**请求**
```
POST /api/projects/{project_id}/index
```

**请求体**
```json
{
  "force": false
}
```

**响应**
```json
{
  "code": 200,
  "data": {
    "status": "indexing",
    "message": "索引重建中"
  }
}
```

---

## 3. 问答 API

### 3.1 发起问答

**请求**
```
POST /api/chat
```

**请求体**
```json
{
  "project_id": "proj_abc123",
  "question": "用户登录功能是如何实现的？",
  "mode": "implementation",
  "session_id": "sess_xyz"
}
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| project_id | string | 是 | 项目ID |
| question | string | 是 | 问题内容 |
| mode | string | 否 | 问答模式，默认implementation |
| session_id | string | 否 | 会话ID，用于多轮对话 |

**Mode 取值**
- `implementation` - 实现型（基于代码库）
- `planning` - 规划型（基于LLM知识）
- `hybrid` - 混合型（现状+建议）

**响应**
```json
{
  "code": 200,
  "data": {
    "session_id": "sess_xyz",
    "message_id": "msg_123",
    "answer": "根据代码分析，用户登录实现如下：\n1. 接口定义 [auth.py:45]\n...",
    "references": [
      {
        "file_path": "backend/services/auth.py",
        "line_start": 45,
        "line_end": 68,
        "snippet": "def login(username, password):\n    ..."
      }
    ],
    "mode": "implementation",
    "confidence": 0.85,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

---

### 3.2 流式问答

**请求**
```
POST /api/chat/stream
```

**请求体**：同上

**响应**：Server-Sent Events (SSE)

```
event: start
data: {"session_id": "sess_xyz", "message_id": "msg_123"}

event: token
data: {"token": "根据"}

event: token
data: {"token": "代码"}

event: reference
data: {"file_path": "auth.py", "line_start": 45}

event: done
data: {"message_id": "msg_123", "confidence": 0.85}
```

---

### 3.3 获取对话历史

**请求**
```
GET /api/chat/history/{session_id}
```

**响应**
```json
{
  "code": 200,
  "data": {
    "session_id": "sess_xyz",
    "project_id": "proj_abc123",
    "mode": "implementation",
    "messages": [
      {
        "id": "msg_1",
        "role": "user",
        "content": "用户登录功能是如何实现的？",
        "created_at": "2024-01-15T10:30:00Z"
      },
      {
        "id": "msg_2",
        "role": "assistant",
        "content": "根据代码分析...",
        "references": [...],
        "created_at": "2024-01-15T10:30:05Z"
      }
    ]
  }
}
```

---

## 4. 代码搜索 API

### 4.1 语义搜索

**请求**
```
POST /api/search
```

**请求体**
```json
{
  "project_id": "proj_abc123",
  "query": "用户认证",
  "type": "semantic",
  "filters": {
    "language": "python",
    "file_pattern": "*.py"
  },
  "limit": 10
}
```

**响应**
```json
{
  "code": 200,
  "data": {
    "results": [
      {
        "id": "chunk_123",
        "file_path": "backend/services/auth.py",
        "line_start": 45,
        "line_end": 68,
        "content": "def login(username, password):\n    ...",
        "score": 0.92,
        "metadata": {
          "type": "function",
          "name": "login",
          "language": "python"
        }
      }
    ],
    "total": 5
  }
}
```

---

## 5. 功能分析 API

### 5.1 获取功能列表

**请求**
```
GET /api/features/{project_id}
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| category | string | 否 | 过滤：frontend/backend |
| type | string | 否 | 过滤：page/api/system |

**响应**
```json
{
  "code": 200,
  "data": {
    "project_id": "proj_abc123",
    "frontend": {
      "pages": [
        {
          "id": "feat_1",
          "name": "用户列表",
          "route": "/users",
          "file_path": "src/pages/Users.tsx",
          "functions": [
            "用户列表展示",
            "搜索用户",
            "删除用户"
          ],
          "api_calls": [
            "GET /api/users",
            "DELETE /api/users/:id"
          ]
        }
      ],
      "components": ["DataTable", "SearchInput"]
    },
    "backend": {
      "apis": [
        {
          "id": "api_1",
          "method": "GET",
          "path": "/api/users",
          "description": "获取用户列表",
          "file_path": "backend/api/users.py",
          "line": 25,
          "auth_required": true
        }
      ],
      "system_features": {
        "scheduled_tasks": [
          {
            "name": "cleanup_logs",
            "schedule": "0 0 * * *",
            "description": "每日清理日志"
          }
        ],
        "sso": {
          "enabled": true,
          "providers": ["企业微信", "钉钉"]
        },
        "middleware": ["AuthMiddleware", "CORSMiddleware"],
        "cache": "Redis"
      },
      "models": [
        {
          "name": "User",
          "file_path": "backend/models/user.py",
          "fields": ["id", "username", "email", "created_at"]
        }
      ]
    }
  }
}
```

---

### 5.2 获取功能详情

**请求**
```
GET /api/features/{project_id}/{feature_id}
```

**响应**
```json
{
  "code": 200,
  "data": {
    "id": "feat_1",
    "name": "用户列表",
    "type": "page",
    "category": "frontend",
    "route": "/users",
    "file_path": "src/pages/Users.tsx",
    "line_start": 1,
    "line_end": 150,
    "description": "用户管理列表页面",
    "functions": [
      {
        "name": "用户列表展示",
        "description": "表格形式展示用户数据"
      },
      {
        "name": "搜索用户",
        "description": "按用户名/邮箱搜索"
      },
      {
        "name": "删除用户",
        "description": "删除选中用户"
      }
    ],
    "api_calls": [
      {
        "method": "GET",
        "path": "/api/users",
        "params": ["page", "size", "keyword"]
      },
      {
        "method": "DELETE",
        "path": "/api/users/:id"
      }
    ],
    "components": [
      {
        "name": "DataTable",
        "source": "shared"
      },
      {
        "name": "SearchInput",
        "source": "local"
      }
    ],
    "related_files": [
      "src/services/userService.ts",
      "src/hooks/useUsers.ts"
    ]
  }
}
```

---

## 6. 文档 API

### 6.1 获取文档

**请求**
```
GET /api/docs/{project_id}
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 否 | 文档类型：api/readme/architecture |

**响应**
```json
{
  "code": 200,
  "data": {
    "project_id": "proj_abc123",
    "documents": [
      {
        "id": "doc_1",
        "type": "api",
        "title": "API 文档",
        "content": "# API 文档\n\n## 接口列表...",
        "format": "markdown",
        "created_at": "2024-01-15T10:30:00Z"
      },
      {
        "id": "doc_2",
        "type": "readme",
        "title": "README",
        "content": "# 项目名称\n\n## 快速开始...",
        "format": "markdown",
        "created_at": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

---

### 6.2 生成文档

**请求**
```
POST /api/docs/{project_id}/generate
```

**请求体**
```json
{
  "types": ["api", "readme", "architecture"],
  "overwrite": true
}
```

**响应**
```json
{
  "code": 200,
  "data": {
    "generated": ["api", "readme", "architecture"],
    "documents": [...]
  }
}
```

---

### 6.3 导出文档

**请求**
```
GET /api/docs/{project_id}/export
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是 | 文档类型 |
| format | string | 否 | 导出格式：markdown/pdf/html |

**响应**
- `format=markdown`: 返回 `.md` 文件下载
- `format=pdf`: 返回 `.pdf` 文件下载
- `format=html`: 返回 `.html` 文件下载

---

## 7. 可视化 API

### 7.1 获取流程图

**请求**
```
GET /api/graph/{project_id}/flow
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| entry | string | 否 | 入口函数/模块 |
| depth | int | 否 | 深度限制，默认3 |

**响应**
```json
{
  "code": 200,
  "data": {
    "type": "flowchart",
    "format": "mermaid",
    "content": "graph TD\n  A[用户登录] --> B[验证密码]\n  B --> C[生成Token]\n  ...",
    "nodes": [
      {"id": "A", "label": "用户登录", "file": "auth.py", "line": 45},
      {"id": "B", "label": "验证密码", "file": "auth.py", "line": 52}
    ]
  }
}
```

---

### 7.2 获取架构图

**请求**
```
GET /api/graph/{project_id}/arch
```

**响应**
```json
{
  "code": 200,
  "data": {
    "type": "architecture",
    "format": "mermaid",
    "content": "graph TB\n  subgraph Frontend\n    A[React App]\n  end\n  subgraph Backend\n    B[FastAPI]\n  end\n  A --> B\n  ...",
    "modules": [
      {"name": "Frontend", "type": "react", "files": 50},
      {"name": "Backend", "type": "fastapi", "files": 80}
    ]
  }
}
```

---

### 7.3 获取调用图

**请求**
```
GET /api/graph/{project_id}/call
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| function | string | 否 | 指定函数名 |
| file | string | 否 | 指定文件路径 |

**响应**
```json
{
  "code": 200,
  "data": {
    "type": "call_graph",
    "nodes": [
      {"id": "login", "label": "login()", "file": "auth.py"},
      {"id": "verify_password", "label": "verify_password()", "file": "auth.py"},
      {"id": "generate_token", "label": "generate_token()", "file": "token.py"}
    ],
    "edges": [
      {"from": "login", "to": "verify_password"},
      {"from": "login", "to": "generate_token"}
    ]
  }
}
```

---

## 8. WebSocket API

### 8.1 导入进度

**连接**
```
ws://localhost:8000/ws/import/{project_id}
```

**消息格式**

```json
{
  "event": "progress",
  "data": {
    "stage": "cloning",
    "progress": 30,
    "message": "正在克隆仓库..."
  }
}
```

**事件类型**

| event | 说明 |
|-------|------|
| progress | 进度更新 |
| completed | 导入完成 |
| error | 发生错误 |

**Stage 取值**
- `cloning` - 克隆仓库
- `parsing` - 解析代码
- `indexing` - 建立索引
- `completed` - 完成

---

### 8.2 问答流式

**连接**
```
ws://localhost:8000/ws/chat/{session_id}
```

**发送消息**
```json
{
  "type": "question",
  "data": {
    "project_id": "proj_abc123",
    "question": "用户登录功能是如何实现的？",
    "mode": "implementation"
  }
}
```

**接收消息**
```json
{
  "type": "token",
  "data": {
    "content": "根据"
  }
}
```

---

## 9. 附录

### 9.1 常用请求头

| Header | 说明 |
|--------|------|
| `Content-Type` | `application/json` |
| `Authorization` | `Bearer <token>` |

### 9.2 分页参数

| 参数 | 默认值 | 最大值 |
|------|--------|--------|
| page | 1 | - |
| size | 20 | 100 |
