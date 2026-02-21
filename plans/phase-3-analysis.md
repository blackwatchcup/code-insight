# Phase 3: 功能分析模块 - 执行计划

**目标**：实现前后端功能自动分析，提取页面、API、系统功能等  
**任务数**：8个  
**预计时间**：1.5周  
**分支**：feature/phase-3-analysis  
**依赖**：Phase 2 完成

---

## 任务 3.1：前端路由解析

### 描述
解析前端路由配置，提取页面路由信息。

### 执行步骤

1. 创建路由解析器 `app/analysis/route_parser.py`
```python
import re
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class RouteInfo:
    path: str
    component: str
    file_path: str
    name: str
    children: List['RouteInfo']

class RouteParser:
    # React Router 路由模式
    REACT_ROUTE_PATTERNS = [
        r'<Route\s+path=["\']([^"\']+)["\'].*?element=\{<([^>]+)\/>\}',
        r'path:\s*["\']([^"\']+)["\'].*?element:\s*<([^>]+)',
    ]
    
    # Vue Router 路由模式
    VUE_ROUTE_PATTERNS = [
        r'path:\s*["\']([^"\']+)["\'].*?component:\s*(\w+)',
        r'path:\s*["\']([^"\']+)["\'].*?name:\s*["\']([^"\']+)["\']',
    ]
    
    def parse_react_router(self, content: str, file_path: str) -> List[RouteInfo]:
        routes = []
        for pattern in self.REACT_ROUTE_PATTERNS:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                routes.append(RouteInfo(
                    path=match[0],
                    component=match[1],
                    file_path=file_path,
                    name=match[1].replace("Page", "").replace("View", ""),
                    children=[]
                ))
        return routes
    
    def parse_vue_router(self, content: str, file_path: str) -> List[RouteInfo]:
        routes = []
        for pattern in self.VUE_ROUTE_PATTERNS:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                routes.append(RouteInfo(
                    path=match[0],
                    component=match[1] if len(match) > 1 else "",
                    file_path=file_path,
                    name=match[1] if len(match) > 1 else match[0],
                    children=[]
                ))
        return routes
    
    def detect_framework(self, content: str) -> str:
        if 'react-router' in content or 'React Router' in content:
            return 'react'
        if 'vue-router' in content or 'createRouter' in content:
            return 'vue'
        if 'next/router' in content or 'useRouter' in content:
            return 'nextjs'
        return 'unknown'
    
    def parse(self, content: str, file_path: str) -> List[RouteInfo]:
        framework = self.detect_framework(content)
        
        if framework == 'react':
            return self.parse_react_router(content, file_path)
        elif framework == 'vue':
            return self.parse_vue_router(content, file_path)
        
        return []
```

### 验收标准
- [ ] 可解析React Router配置
- [ ] 可解析Vue Router配置
- [ ] 可识别Next.js路由
- [ ] 提取路由路径和组件

### 提交信息
```
feat(analysis): add frontend route parser
```

---

## 任务 3.2：前端页面功能提取

### 描述
提取页面中的功能点，如按钮操作、表单提交等。

### 执行步骤

1. 创建功能提取器 `app/analysis/frontend_analyzer.py`
```python
import re
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class PageFunction:
    name: str
    type: str  # click, submit, load, etc.
    description: str
    line: int
    handler: str

class FrontendAnalyzer:
    # 按钮点击事件模式
    CLICK_PATTERNS = [
        r'onClick=\{([^}]+)\}',
        r'@click="([^"]+)"',
        r'handleClick\w*\s*[=(]',
    ]
    
    # 表单提交模式
    SUBMIT_PATTERNS = [
        r'onSubmit=\{([^}]+)\}',
        r'@submit="([^"]+)"',
        r'handleSubmit\w*\s*[=(]',
    ]
    
    # 数据获取模式
    FETCH_PATTERNS = [
        r'(fetch|axios|request)\s*\(\s*["\']([^"\']+)["\']',
        r'useQuery\(["\']([^"\']+)["\']',
        r'useMutation\(["\']([^"\']+)["\']',
    ]
    
    def extract_functions(self, content: str, file_path: str) -> List[PageFunction]:
        functions = []
        
        # 提取点击事件
        functions.extend(self._extract_clicks(content, file_path))
        
        # 提取表单提交
        functions.extend(self._extract_submits(content, file_path))
        
        # 提取数据加载
        functions.extend(self._extract_fetches(content, file_path))
        
        return functions
    
    def _extract_clicks(self, content: str, file_path: str) -> List[PageFunction]:
        functions = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            for pattern in self.CLICK_PATTERNS:
                matches = re.findall(pattern, line)
                for match in matches:
                    functions.append(PageFunction(
                        name=self._infer_function_name(match),
                        type="click",
                        description=f"按钮点击: {match}",
                        line=i,
                        handler=match
                    ))
        
        return functions
    
    def _infer_function_name(self, handler: str) -> str:
        """从处理函数推断功能名称"""
        name_map = {
            'delete': '删除',
            'edit': '编辑',
            'save': '保存',
            'submit': '提交',
            'cancel': '取消',
            'add': '新增',
            'create': '创建',
            'update': '更新',
            'search': '搜索',
            'filter': '筛选',
            'export': '导出',
            'import': '导入',
        }
        
        handler_lower = handler.lower()
        for key, name in name_map.items():
            if key in handler_lower:
                return name
        
        return handler
```

### 验收标准
- [ ] 可提取点击事件
- [ ] 可提取表单提交
- [ ] 可提取数据获取
- [ ] 推断功能名称

### 提交信息
```
feat(analysis): add frontend page function extractor
```

---

## 任务 3.3：前端API调用分析

### 描述
分析前端代码中的API调用，识别调用的后端接口。

### 执行步骤

1. 创建API调用分析器 `app/analysis/api_call_analyzer.py`
```python
import re
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class APICallInfo:
    method: str
    path: str
    file_path: str
    line: int
    function_name: str
    params: List[str]

class APICallAnalyzer:
    # fetch/axios 调用模式
    PATTERNS = [
        # fetch
        (r'fetch\(["\']([^"\']+)["\']', 'GET'),
        # axios.get
        (r'axios\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']', None),
        # api.get
        (r'api\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']', None),
        # request
        (r'request\(\s*\{[^}]*url:\s*["\']([^"\']+)["\'][^}]*method:\s*["\'](\w+)["\']', None),
    ]
    
    def analyze(self, content: str, file_path: str) -> List[APICallInfo]:
        calls = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            for pattern, default_method in self.PATTERNS:
                matches = re.findall(pattern, line)
                for match in matches:
                    if isinstance(match, tuple):
                        if len(match) == 2:
                            method = match[0].upper() if match[0] else default_method
                            path = match[1]
                        else:
                            method = default_method or 'GET'
                            path = match[0]
                    else:
                        method = default_method or 'GET'
                        path = match
                    
                    calls.append(APICallInfo(
                        method=method,
                        path=self._normalize_path(path),
                        file_path=file_path,
                        line=i,
                        function_name=self._extract_function_context(lines, i-1),
                        params=self._extract_params(line)
                    ))
        
        return calls
    
    def _normalize_path(self, path: str) -> str:
        """规范化API路径"""
        # 移除引号
        path = path.strip('"\'')
        # 处理模板字符串
        path = re.sub(r'\$\{[^}]+\}', ':param', path)
        return path
```

### 验收标准
- [ ] 可识别fetch调用
- [ ] 可识别axios调用
- [ ] 提取HTTP方法和路径
- [ ] 关联所在函数

### 提交信息
```
feat(analysis): add frontend API call analyzer
```

---

## 任务 3.4：后端API提取

### 描述
提取后端API路由定义，包括路径、方法、参数等。

### 执行步骤

1. 创建API提取器 `app/analysis/api_extractor.py`
```python
import re
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class APIEndpoint:
    method: str
    path: str
    handler: str
    file_path: str
    line: int
    description: str
    auth_required: bool
    params: List[Dict]

class APIExtractor:
    # FastAPI 路由装饰器
    FASTAPI_PATTERNS = [
        r'@(router|app)\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
    ]
    
    # Flask 路由装饰器
    FLASK_PATTERNS = [
        r'@app\.route\(["\']([^"\']+)["\'].*methods\s*=\s*\[([^\]]+)\]',
    ]
    
    # Express 路由
    EXPRESS_PATTERNS = [
        r'(app|router)\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
    ]
    
    def extract_from_fastapi(self, content: str, file_path: str) -> List[APIEndpoint]:
        endpoints = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            for pattern in self.FASTAPI_PATTERNS:
                matches = re.findall(pattern, line, re.IGNORECASE)
                for match in matches:
                    method = match[1].upper()
                    path = match[2]
                    
                    # 查找处理函数
                    handler = self._find_handler(lines, i)
                    
                    # 检查是否需要认证
                    auth_required = self._check_auth(lines, i)
                    
                    endpoints.append(APIEndpoint(
                        method=method,
                        path=path,
                        handler=handler,
                        file_path=file_path,
                        line=i,
                        description=self._extract_docstring(lines, i),
                        auth_required=auth_required,
                        params=self._extract_params(lines, i)
                    ))
        
        return endpoints
```

### 验收标准
- [ ] 可提取FastAPI路由
- [ ] 可提取Flask路由
- [ ] 识别HTTP方法
- [ ] 识别认证要求

### 提交信息
```
feat(analysis): add backend API extractor
```

---

## 任务 3.5：系统功能识别

### 描述
识别系统级功能，如定时任务、SSO、中间件等。

### 执行步骤

1. 创建系统功能检测器 `app/analysis/feature_detector.py`
```python
import re
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class SystemFeature:
    type: str  # scheduled_task, sso, middleware, cache, mq
    name: str
    description: str
    file_path: str
    line: int
    config: Dict

class SystemFeatureDetector:
    FEATURE_PATTERNS = {
        "scheduled_tasks": {
            "patterns": [
                r'@scheduler\.task',
                r'@celery\.task',
                r'APScheduler',
                r'cron\.schedule',
                r'node-cron',
            ],
            "extract": r'@scheduler\.task.*?def\s+(\w+)',
        },
        "sso": {
            "patterns": [
                r'flask_sso',
                r'django-allauth',
                r'authlib',
                r'python-saml',
                r'passport-saml',
                r'passport-oauth2',
            ],
            "extract": None,
        },
        "middleware": {
            "patterns": [
                r'@middleware',
                r'class\s+\w+Middleware',
                r'app\.use\(',
                r'add_middleware',
            ],
            "extract": r'class\s+(\w+Middleware)',
        },
        "cache": {
            "patterns": [
                r'redis',
                r'memcached',
                r'cachetools',
            ],
            "extract": None,
        },
        "message_queue": {
            "patterns": [
                r'celery',
                r'rabbitmq',
                r'kafka',
                r'bull',
            ],
            "extract": None,
        }
    }
    
    def detect(self, content: str, file_path: str) -> List[SystemFeature]:
        features = []
        lines = content.split('\n')
        
        for feature_type, config in self.FEATURE_PATTERNS.items():
            for pattern in config["patterns"]:
                matches = list(re.finditer(pattern, content, re.IGNORECASE))
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    
                    name = feature_type
                    if config.get("extract"):
                        name_match = re.search(config["extract"], content[match.start():])
                        if name_match:
                            name = name_match.group(1)
                    
                    features.append(SystemFeature(
                        type=feature_type,
                        name=name,
                        description=self._describe_feature(feature_type, name),
                        file_path=file_path,
                        line=line_num,
                        config={}
                    ))
        
        return features
```

### 验收标准
- [ ] 可检测定时任务
- [ ] 可检测SSO配置
- [ ] 可检测中间件
- [ ] 可检测缓存和消息队列

### 提交信息
```
feat(analysis): add system feature detector
```

---

## 任务 3.6：数据模型提取

### 描述
提取数据模型定义，如ORM模型。

### 执行步骤

1. 创建模型提取器 `app/analysis/model_extractor.py`
```python
import re
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class ModelField:
    name: str
    type: str
    nullable: bool
    primary_key: bool
    description: str

@dataclass
class DataModel:
    name: str
    file_path: str
    line: int
    fields: List[ModelField]
    table_name: str

class ModelExtractor:
    def extract_sqlalchemy(self, content: str, file_path: str) -> List[DataModel]:
        models = []
        
        # 查找类定义
        class_pattern = r'class\s+(\w+)\(.*Model.*\):'
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            class_start = match.start()
            
            # 提取类体
            class_body = self._extract_class_body(content, class_start)
            
            # 提取字段
            fields = self._extract_fields(class_body)
            
            models.append(DataModel(
                name=class_name,
                file_path=file_path,
                line=content[:class_start].count('\n') + 1,
                fields=fields,
                table_name=self._extract_table_name(class_body, class_name)
            ))
        
        return models
    
    def extract_prisma(self, content: str, file_path: str) -> List[DataModel]:
        # Prisma schema 解析
        pass
    
    def extract_typeorm(self, content: str, file_path: str) -> List[DataModel]:
        # TypeORM 实体解析
        pass
```

### 验收标准
- [ ] 可提取SQLAlchemy模型
- [ ] 可提取Prisma模型
- [ ] 可提取TypeORM实体
- [ ] 识别字段和类型

### 提交信息
```
feat(analysis): add data model extractor
```

---

## 任务 3.7：功能树数据结构

### 描述
设计并实现功能点树形数据结构。

### 执行步骤

1. 创建功能树模型 `app/models/feature_tree.py`
```python
from typing import List, Optional
from dataclasses import dataclass, field
from enum import Enum

class FeatureType(str, Enum):
    PAGE = "page"
    API = "api"
    SYSTEM = "system"
    COMPONENT = "component"
    MODEL = "model"

class FeatureCategory(str, Enum):
    FRONTEND = "frontend"
    BACKEND = "backend"

@dataclass
class FeatureNode:
    id: str
    name: str
    type: FeatureType
    category: FeatureCategory
    description: str = ""
    file_path: str = ""
    line_start: int = 0
    line_end: int = 0
    children: List['FeatureNode'] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "category": self.category.value,
            "description": self.description,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "children": [c.to_dict() for c in self.children],
            "metadata": self.metadata
        }

@dataclass
class FeatureTree:
    project_id: str
    frontend: FeatureNode
    backend: FeatureNode
    
    def to_dict(self) -> dict:
        return {
            "project_id": self.project_id,
            "frontend": self.frontend.to_dict(),
            "backend": self.backend.to_dict()
        }
```

2. 创建功能树构建器 `app/analysis/feature_tree_builder.py`
```python
from app.models.feature_tree import FeatureTree, FeatureNode, FeatureType, FeatureCategory

class FeatureTreeBuilder:
    def __init__(self, project_id: str):
        self.project_id = project_id
    
    def build(
        self,
        routes: List,
        page_functions: Dict,
        api_calls: Dict,
        apis: List,
        system_features: List,
        models: List
    ) -> FeatureTree:
        # 构建前端功能树
        frontend = self._build_frontend_tree(routes, page_functions, api_calls)
        
        # 构建后端功能树
        backend = self._build_backend_tree(apis, system_features, models)
        
        return FeatureTree(
            project_id=self.project_id,
            frontend=frontend,
            backend=backend
        )
```

### 验收标准
- [ ] 数据结构完整
- [ ] 支持序列化
- [ ] 可递归遍历

### 提交信息
```
feat(analysis): add feature tree data structure
```

---

## 任务 3.8：功能分析API

### 描述
提供功能分析查询API接口。

### 执行步骤

1. 创建API路由 `app/api/features.py`
```python
from fastapi import APIRouter, Depends
from app.services.feature_service import FeatureService

router = APIRouter()
feature_service = FeatureService()

@router.get("/{project_id}")
async def get_features(project_id: str):
    tree = await feature_service.get_feature_tree(project_id)
    return {"code": 200, "data": tree.to_dict()}

@router.get("/{project_id}/frontend")
async def get_frontend_features(project_id: str):
    tree = await feature_service.get_feature_tree(project_id)
    return {"code": 200, "data": tree.frontend.to_dict()}

@router.get("/{project_id}/backend")
async def get_backend_features(project_id: str):
    tree = await feature_service.get_feature_tree(project_id)
    return {"code": 200, "data": tree.backend.to_dict()}

@router.get("/{project_id}/{feature_id}")
async def get_feature_detail(project_id: str, feature_id: str):
    feature = await feature_service.get_feature(project_id, feature_id)
    return {"code": 200, "data": feature}
```

### 验收标准
- [ ] API可正常访问
- [ ] 返回正确数据
- [ ] 支持过滤查询

### 提交信息
```
feat(api): add feature analysis API endpoints
```

---

## Phase 3 完成标准

- [ ] 前端路由可解析
- [ ] 页面功能可提取
- [ ] API调用可分析
- [ ] 后端API可提取
- [ ] 系统功能可识别
- [ ] 数据模型可提取
- [ ] 功能树可构建
- [ ] API可正常访问

## 下一阶段

完成 Phase 3 后，进入 Phase 4: RAG问答系统
