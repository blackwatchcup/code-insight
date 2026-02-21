# Phase 1: 基础框架 - 执行计划

**目标**：搭建项目基础框架，实现项目导入功能  
**任务数**：10个  
**预计时间**：1.5周  
**分支**：feature/phase-1-foundation

---

## 任务 1.1：创建项目结构

### 描述
初始化完整的项目目录结构，包括前端、后端、文档等目录。

### 执行步骤

1. 创建后端目录结构
```
code-insight/backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   └── __init__.py
│   ├── core/
│   │   └── __init__.py
│   ├── models/
│   │   └── __init__.py
│   ├── parsers/
│   │   └── __init__.py
│   ├── analysis/
│   │   └── __init__.py
│   ├── rag/
│   │   └── __init__.py
│   ├── llm/
│   │   └── __init__.py
│   ├── graph/
│   │   └── __init__.py
│   ├── docs/
│   │   └── __init__.py
│   └── services/
│       └── __init__.py
├── tests/
│   └── __init__.py
├── requirements.txt
└── Dockerfile
```

2. 创建前端目录结构
```
code-insight/frontend/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── components/
│   ├── pages/
│   ├── services/
│   ├── hooks/
│   ├── stores/
│   ├── types/
│   └── utils/
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
└── Dockerfile
```

3. 创建根目录配置文件
```
code-insight/
├── docker-compose.yml
├── .env.example
└── README.md
```

### 验收标准
- [ ] 所有目录和 __init__.py 文件已创建
- [ ] requirements.txt 包含基础依赖
- [ ] package.json 包含基础依赖
- [ ] 项目结构符合架构设计

### 提交信息
```
feat: initialize project structure
```

---

## 任务 1.2：后端FastAPI框架

### 描述
搭建FastAPI后端基础框架，配置路由、中间件、异常处理。

### 执行步骤

1. 创建 `app/main.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="CodeInsight API",
    version="1.0.0"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 健康检查
@app.get("/health")
async def health():
    return {"status": "ok"}

# 注册路由
# from app.api import projects, chat, search, features, docs, graph
# app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
```

2. 创建 `app/core/config.py` 配置管理
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "CodeInsight"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./data/codeinsight.db"
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    OPENAI_API_KEY: str = ""
    
    class Config:
        env_file = ".env"

settings = Settings()
```

3. 创建基础路由 `app/api/projects.py`
```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_projects():
    return {"projects": []}
```

### 验收标准
- [ ] 访问 /health 返回 200
- [ ] 访问 /docs 可查看API文档
- [ ] 配置管理正常工作

### 提交信息
```
feat(api): setup fastapi framework with basic configuration
```

---

## 任务 1.3：前端React框架

### 描述
搭建React前端基础框架，使用Vite + TypeScript + TailwindCSS。

### 执行步骤

1. 初始化Vite项目
```bash
npm create vite@latest frontend -- --template react-ts
```

2. 安装依赖
```bash
npm install react-router-dom zustand axios
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

3. 配置 TailwindCSS
```javascript
// tailwind.config.js
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: { extend: {} },
  plugins: [],
}
```

4. 创建基础页面结构
```typescript
// src/App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Projects } from './pages/Projects'

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Projects />} />
      </Routes>
    </BrowserRouter>
  )
}
```

5. 创建API服务
```typescript
// src/services/api.ts
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

export { api }
```

### 验收标准
- [ ] npm run dev 可启动开发服务器
- [ ] 页面正常显示
- [ ] TailwindCSS 样式生效

### 提交信息
```
feat(ui): setup react frontend with vite and tailwindcss
```

---

## 任务 1.4：Docker配置

### 描述
创建Dockerfile和docker-compose.yml，实现容器化部署。

### 执行步骤

1. 创建后端Dockerfile
```dockerfile
# code-insight/backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. 创建前端Dockerfile
```dockerfile
# code-insight/frontend/Dockerfile
FROM node:20-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

3. 创建docker-compose.yml
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
      
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
```

### 验收标准
- [ ] docker-compose up 可启动服务
- [ ] 前端可访问 http://localhost:3000
- [ ] 后端API可访问 http://localhost:8000/docs

### 提交信息
```
chore(docker): add dockerfile and docker-compose configuration
```

---

## 任务 1.5：项目导入API - 本地目录

### 描述
实现本地目录导入功能，支持选择本地文件夹路径导入项目。

### 执行步骤

1. 创建数据模型 `app/models/project.py`
```python
from sqlalchemy import Column, String, DateTime, Integer, Enum
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class SourceType(str, enum.Enum):
    LOCAL = "local"
    GITHUB = "github"
    GITLAB = "gitlab"
    GITEE = "gitee"
    GIT = "git"
    ZIP = "zip"

class ProjectStatus(str, enum.Enum):
    INDEXING = "indexing"
    READY = "ready"
    ERROR = "error"

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    source_type = Column(Enum(SourceType), default=SourceType.LOCAL)
    source_url = Column(String, nullable=True)
    local_path = Column(String, nullable=False)
    branch = Column(String, default="main")
    status = Column(Enum(ProjectStatus), default=ProjectStatus.INDEXING)
    file_count = Column(Integer, default=0)
    line_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

2. 创建项目服务 `app/services/project_service.py`
```python
import os
import shutil
import uuid
from pathlib import Path
from app.models.project import Project, SourceType, ProjectStatus
from app.core.config import settings

class ProjectService:
    def __init__(self):
        self.projects_dir = Path(settings.DATA_DIR) / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_from_local(self, name: str, local_path: str) -> Project:
        project_id = str(uuid.uuid4())[:8]
        project_dir = self.projects_dir / project_id
        
        # 复制目录
        shutil.copytree(local_path, project_dir)
        
        project = Project(
            id=project_id,
            name=name,
            source_type=SourceType.LOCAL,
            source_url=local_path,
            local_path=str(project_dir),
            status=ProjectStatus.INDEXING
        )
        
        return project
```

3. 创建API路由 `app/api/projects.py`
```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.project_service import ProjectService

router = APIRouter()
project_service = ProjectService()

class CreateProjectRequest(BaseModel):
    name: str
    source_type: str = "local"
    local_path: str

@router.post("/")
async def create_project(request: CreateProjectRequest):
    if request.source_type != "local":
        raise HTTPException(400, "Use /import endpoint for URL imports")
    
    project = await project_service.create_from_local(
        name=request.name,
        local_path=request.local_path
    )
    return {"code": 200, "data": project}
```

### 验收标准
- [ ] POST /api/projects 可创建本地项目
- [ ] 项目目录正确复制到数据目录
- [ ] 数据库记录正确创建

### 提交信息
```
feat(api): add local directory project import endpoint
```

---

## 任务 1.6：项目导入API - URL

### 描述
实现URL导入功能，支持GitHub/GitLab/Gitee/Git/ZIP导入。

### 执行步骤

1. 创建导入服务 `app/services/import_service.py`
```python
import os
import uuid
import zipfile
import tempfile
from pathlib import Path
from typing import Optional
import git
import requests
from app.models.project import Project, SourceType, ProjectStatus
from app.core.config import settings

class ImportService:
    def __init__(self):
        self.projects_dir = Path(settings.DATA_DIR) / "projects"
        
    async def import_from_git(
        self, 
        url: str, 
        branch: str = "main",
        token: Optional[str] = None,
        depth: int = 1
    ) -> Project:
        project_id = str(uuid.uuid4())[:8]
        project_dir = self.projects_dir / project_id
        
        # 处理带Token的URL
        if token and "github.com" in url:
            url = url.replace("github.com", f"{token}@github.com")
        
        # 克隆仓库
        git.Repo.clone_from(
            url, 
            project_dir, 
            branch=branch, 
            depth=depth
        )
        
        project = Project(
            id=project_id,
            name=self._extract_name(url),
            source_type=self._detect_source_type(url),
            source_url=url,
            local_path=str(project_dir),
            branch=branch,
            status=ProjectStatus.INDEXING
        )
        
        return project
    
    async def import_from_zip(self, url: str) -> Project:
        project_id = str(uuid.uuid4())[:8]
        project_dir = self.projects_dir / project_id
        
        # 下载ZIP
        response = requests.get(url, stream=True)
        with tempfile.NamedTemporaryFile(suffix=".zip") as tmp:
            for chunk in response.iter_content(chunk_size=8192):
                tmp.write(chunk)
            tmp.flush()
            
            # 解压
            with zipfile.ZipFile(tmp.name, 'r') as zip_ref:
                zip_ref.extractall(project_dir)
        
        # 处理嵌套目录
        self._flatten_directory(project_dir)
        
        project = Project(
            id=project_id,
            name=self._extract_name(url),
            source_type=SourceType.ZIP,
            source_url=url,
            local_path=str(project_dir),
            status=ProjectStatus.INDEXING
        )
        
        return project
    
    def _extract_name(self, url: str) -> str:
        return url.rstrip("/").split("/")[-1].replace(".git", "")
    
    def _detect_source_type(self, url: str) -> SourceType:
        if "github.com" in url:
            return SourceType.GITHUB
        elif "gitlab.com" in url:
            return SourceType.GITLAB
        elif "gitee.com" in url:
            return SourceType.GITEE
        return SourceType.GIT
```

2. 创建导入API `app/api/projects.py`
```python
class ImportProjectRequest(BaseModel):
    type: str  # github, gitlab, gitee, git, zip
    url: str
    name: Optional[str] = None
    branch: str = "main"
    token: Optional[str] = None
    depth: int = 1

@router.post("/import")
async def import_project(request: ImportProjectRequest):
    import_service = ImportService()
    
    if request.type == "zip":
        project = await import_service.import_from_zip(request.url)
    else:
        project = await import_service.import_from_git(
            url=request.url,
            branch=request.branch,
            token=request.token,
            depth=request.depth
        )
    
    if request.name:
        project.name = request.name
        
    return {"code": 200, "data": project}
```

### 验收标准
- [ ] 可导入GitHub公开仓库
- [ ] 可导入私有仓库（带Token）
- [ ] 可下载并解压ZIP文件
- [ ] 支持分支选择

### 提交信息
```
feat(api): add url import for git repos and zip files
```

---

## 任务 1.7：WebSocket进度推送

### 描述
实现WebSocket实时推送导入/索引进度。

### 执行步骤

1. 创建WebSocket管理器 `app/core/websocket.py`
```python
from fastapi import WebSocket
from typing import Dict, Set
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, project_id: str):
        await websocket.accept()
        if project_id not in self.active_connections:
            self.active_connections[project_id] = set()
        self.active_connections[project_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, project_id: str):
        self.active_connections[project_id].discard(websocket)
    
    async def send_progress(self, project_id: str, stage: str, progress: int, message: str):
        if project_id not in self.active_connections:
            return
        
        data = {
            "event": "progress",
            "data": {
                "stage": stage,
                "progress": progress,
                "message": message
            }
        }
        
        for connection in self.active_connections[project_id]:
            await connection.send_json(data)

manager = ConnectionManager()
```

2. 添加WebSocket路由 `app/main.py`
```python
from app.core.websocket import manager

@app.websocket("/ws/import/{project_id}")
async def websocket_import(websocket: WebSocket, project_id: str):
    await manager.connect(websocket, project_id)
    try:
        while True:
            await websocket.receive_text()
    except:
        manager.disconnect(websocket, project_id)
```

3. 在导入服务中发送进度
```python
from app.core.websocket import manager

class ImportService:
    async def import_from_git(self, url: str, ..., project_id: str):
        await manager.send_progress(project_id, "cloning", 0, "开始克隆仓库...")
        # 克隆操作...
        await manager.send_progress(project_id, "cloning", 100, "克隆完成")
        
        await manager.send_progress(project_id, "parsing", 0, "开始解析代码...")
        # 解析操作...
```

### 验收标准
- [ ] WebSocket连接可建立
- [ ] 进度消息可实时推送
- [ ] 连接断开正常处理

### 提交信息
```
feat(api): add websocket for import progress notification
```

---

## 任务 1.8：前端项目管理页

### 描述
创建前端项目管理页面，包括项目列表和导入界面。

### 执行步骤

1. 创建项目列表页 `src/pages/Projects.tsx`
```tsx
import { useEffect, useState } from 'react'
import { api } from '@/services/api'

interface Project {
  id: string
  name: string
  source_type: string
  status: string
  created_at: string
}

export function Projects() {
  const [projects, setProjects] = useState<Project[]>([])
  
  useEffect(() => {
    fetchProjects()
  }, [])
  
  const fetchProjects = async () => {
    const res = await api.get('/projects')
    setProjects(res.data.data.items)
  }
  
  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">项目列表</h1>
        <button className="btn btn-primary">导入项目</button>
      </div>
      
      <div className="grid grid-cols-3 gap-4">
        {projects.map(project => (
          <div key={project.id} className="card p-4">
            <h3 className="font-semibold">{project.name}</h3>
            <p className="text-sm text-gray-500">{project.source_type}</p>
            <span className="badge">{project.status}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
```

2. 创建导入对话框 `src/components/ImportDialog.tsx`
```tsx
import { useState } from 'react'

type ImportType = 'local' | 'github' | 'gitlab' | 'zip'

export function ImportDialog({ onClose }: { onClose: () => void }) {
  const [type, setType] = useState<ImportType>('github')
  const [url, setUrl] = useState('')
  
  const handleImport = async () => {
    if (type === 'local') {
      // 本地导入
    } else {
      await api.post('/projects/import', { type, url })
    }
    onClose()
  }
  
  return (
    <div className="modal">
      <div className="modal-content">
        <h2>导入项目</h2>
        
        <div className="tabs">
          <button onClick={() => setType('github')}>GitHub</button>
          <button onClick={() => setType('gitlab')}>GitLab</button>
          <button onClick={() => setType('local')}>本地目录</button>
          <button onClick={() => setType('zip')}>ZIP</button>
        </div>
        
        {type !== 'local' && (
          <input 
            placeholder="输入仓库URL" 
            value={url}
            onChange={e => setUrl(e.target.value)}
          />
        )}
        
        <button onClick={handleImport}>导入</button>
      </div>
    </div>
  )
}
```

### 验收标准
- [ ] 项目列表正确显示
- [ ] 导入对话框可打开
- [ ] 可通过URL导入项目
- [ ] 导入进度实时显示

### 提交信息
```
feat(ui): add project management page with import dialog
```

---

## 任务 1.9：数据库模型设计

### 描述
设计并实现完整的数据库模型。

### 执行步骤

1. 创建数据库配置 `app/core/database.py`
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

2. 创建模型文件
- `app/models/project.py` - 项目模型
- `app/models/file.py` - 文件模型
- `app/models/chat.py` - 对话模型
- `app/models/feature.py` - 功能模型

3. 创建数据库初始化 `app/core/init_db.py`
```python
from app.core.database import engine
from app.models import Base

def init_db():
    Base.metadata.create_all(bind=engine)
```

### 验收标准
- [ ] 数据库文件正确创建
- [ ] 所有表结构正确
- [ ] 可正常CRUD操作

### 提交信息
```
feat(api): add database models and initialization
```

---

## 任务 1.10：配置管理

### 描述
实现完整的配置管理系统。

### 执行步骤

1. 更新 `app/core/config.py`
```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "CodeInsight"
    DEBUG: bool = True
    VERSION: str = "1.0.0"
    
    # 数据库
    DATABASE_URL: str = "sqlite:///./data/codeinsight.db"
    
    # 存储路径
    DATA_DIR: str = "./data"
    PROJECTS_DIR: str = "./data/projects"
    CHROMA_DIR: str = "./data/chroma"
    
    # LLM配置
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"
    CLAUDE_API_KEY: str = ""
    
    # 向量配置
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    
    # 解析配置
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    SUPPORTED_EXTENSIONS: list = [
        ".py", ".js", ".ts", ".tsx", ".jsx",
        ".java", ".go", ".rs", ".vue"
    ]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

2. 创建 `.env.example`
```env
DEBUG=true
DATABASE_URL=sqlite:///./data/codeinsight.db
DATA_DIR=./data

OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4

CLAUDE_API_KEY=sk-xxx
```

### 验收标准
- [ ] 环境变量正确加载
- [ ] .env文件生效
- [ ] 配置项可访问

### 提交信息
```
feat(config): add comprehensive configuration management
```

---

## Phase 1 完成标准

- [ ] 后端FastAPI可启动
- [ ] 前端React可启动
- [ ] Docker可一键部署
- [ ] 本地项目可导入
- [ ] URL项目可导入
- [ ] 导入进度可实时查看
- [ ] 项目列表可显示

## 下一阶段

完成 Phase 1 后，进入 Phase 2: 代码解析引擎
