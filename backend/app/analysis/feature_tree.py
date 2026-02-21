from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid


class FeatureType(str, Enum):
    PAGE = "page"
    API = "api"
    SYSTEM = "system"
    COMPONENT = "component"
    MODEL = "model"
    FUNCTION = "function"
    ROUTE = "route"


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
    metadata: Dict[str, Any] = field(default_factory=dict)
    
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
    
    def add_child(self, child: 'FeatureNode'):
        self.children.append(child)
    
    def find_by_id(self, node_id: str) -> Optional['FeatureNode']:
        if self.id == node_id:
            return self
        
        for child in self.children:
            found = child.find_by_id(node_id)
            if found:
                return found
        
        return None
    
    def find_by_type(self, feature_type: FeatureType) -> List['FeatureNode']:
        results = []
        
        if self.type == feature_type:
            results.append(self)
        
        for child in self.children:
            results.extend(child.find_by_type(feature_type))
        
        return results
    
    def count_children(self) -> Dict[str, int]:
        counts = {}
        
        for child in self.children:
            type_name = child.type.value
            if type_name not in counts:
                counts[type_name] = 0
            counts[type_name] += 1
            
            child_counts = child.count_children()
            for k, v in child_counts.items():
                if k not in counts:
                    counts[k] = 0
                counts[k] += v
        
        return counts


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
    
    def find_feature(self, feature_id: str) -> Optional[FeatureNode]:
        result = self.frontend.find_by_id(feature_id)
        if result:
            return result
        
        return self.backend.find_by_id(feature_id)
    
    def get_summary(self) -> Dict:
        frontend_counts = self.frontend.count_children()
        backend_counts = self.backend.count_children()
        
        return {
            "project_id": self.project_id,
            "frontend": {
                "total": sum(frontend_counts.values()),
                "by_type": frontend_counts
            },
            "backend": {
                "total": sum(backend_counts.values()),
                "by_type": backend_counts
            }
        }


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
        frontend = self._build_frontend_tree(routes, page_functions, api_calls)
        backend = self._build_backend_tree(apis, system_features, models)
        
        return FeatureTree(
            project_id=self.project_id,
            frontend=frontend,
            backend=backend
        )
    
    def _build_frontend_tree(
        self,
        routes: List,
        page_functions: Dict,
        api_calls: Dict
    ) -> FeatureNode:
        root = FeatureNode(
            id=self._generate_id(),
            name="前端功能",
            type=FeatureType.COMPONENT,
            category=FeatureCategory.FRONTEND,
            description="前端应用功能模块"
        )
        
        routes_node = FeatureNode(
            id=self._generate_id(),
            name="路由配置",
            type=FeatureType.ROUTE,
            category=FeatureCategory.FRONTEND,
            description="前端路由配置"
        )
        
        for route in routes:
            route_node = self._create_route_node(route)
            routes_node.add_child(route_node)
        
        root.add_child(routes_node)
        
        pages_node = FeatureNode(
            id=self._generate_id(),
            name="页面功能",
            type=FeatureType.PAGE,
            category=FeatureCategory.FRONTEND,
            description="页面交互功能"
        )
        
        for file_path, functions in page_functions.items():
            page_node = FeatureNode(
                id=self._generate_id(),
                name=self._extract_page_name(file_path),
                type=FeatureType.PAGE,
                category=FeatureCategory.FRONTEND,
                file_path=file_path,
                description=f"页面: {file_path}"
            )
            
            for func in functions:
                func_node = FeatureNode(
                    id=self._generate_id(),
                    name=func.name,
                    type=FeatureType.FUNCTION,
                    category=FeatureCategory.FRONTEND,
                    file_path=file_path,
                    line_start=func.line,
                    description=func.description,
                    metadata={
                        "handler": func.handler,
                        "function_type": func.type
                    }
                )
                page_node.add_child(func_node)
            
            pages_node.add_child(page_node)
        
        root.add_child(pages_node)
        
        api_calls_node = FeatureNode(
            id=self._generate_id(),
            name="API调用",
            type=FeatureType.API,
            category=FeatureCategory.FRONTEND,
            description="前端API调用"
        )
        
        for file_path, calls in api_calls.items():
            for call in calls:
                call_node = FeatureNode(
                    id=self._generate_id(),
                    name=f"{call.method} {call.path}",
                    type=FeatureType.API,
                    category=FeatureCategory.FRONTEND,
                    file_path=file_path,
                    line_start=call.line,
                    description=f"调用: {call.method} {call.path}",
                    metadata={
                        "method": call.method,
                        "path": call.path,
                        "function_name": call.function_name
                    }
                )
                api_calls_node.add_child(call_node)
        
        root.add_child(api_calls_node)
        
        return root
    
    def _build_backend_tree(
        self,
        apis: List,
        system_features: List,
        models: List
    ) -> FeatureNode:
        root = FeatureNode(
            id=self._generate_id(),
            name="后端功能",
            type=FeatureType.COMPONENT,
            category=FeatureCategory.BACKEND,
            description="后端应用功能模块"
        )
        
        apis_node = FeatureNode(
            id=self._generate_id(),
            name="API接口",
            type=FeatureType.API,
            category=FeatureCategory.BACKEND,
            description="后端API接口"
        )
        
        for api in apis:
            api_node = FeatureNode(
                id=self._generate_id(),
                name=f"{api.method} {api.path}",
                type=FeatureType.API,
                category=FeatureCategory.BACKEND,
                file_path=api.file_path,
                line_start=api.line,
                description=api.description or f"API: {api.method} {api.path}",
                metadata={
                    "method": api.method,
                    "path": api.path,
                    "handler": api.handler,
                    "auth_required": api.auth_required,
                    "params": api.params
                }
            )
            apis_node.add_child(api_node)
        
        root.add_child(apis_node)
        
        system_node = FeatureNode(
            id=self._generate_id(),
            name="系统功能",
            type=FeatureType.SYSTEM,
            category=FeatureCategory.BACKEND,
            description="系统级功能"
        )
        
        for feature in system_features:
            feature_node = FeatureNode(
                id=self._generate_id(),
                name=feature.name,
                type=FeatureType.SYSTEM,
                category=FeatureCategory.BACKEND,
                file_path=feature.file_path,
                line_start=feature.line,
                description=feature.description,
                metadata={
                    "feature_type": feature.type.value if hasattr(feature.type, 'value') else str(feature.type),
                    "framework": feature.framework if hasattr(feature, 'framework') else "",
                    "config": feature.config if hasattr(feature, 'config') else {}
                }
            )
            system_node.add_child(feature_node)
        
        root.add_child(system_node)
        
        models_node = FeatureNode(
            id=self._generate_id(),
            name="数据模型",
            type=FeatureType.MODEL,
            category=FeatureCategory.BACKEND,
            description="数据模型定义"
        )
        
        for model in models:
            model_node = FeatureNode(
                id=self._generate_id(),
                name=model.name,
                type=FeatureType.MODEL,
                category=FeatureCategory.BACKEND,
                file_path=model.file_path,
                line_start=model.line,
                description=f"数据模型: {model.name}",
                metadata={
                    "table_name": model.table_name,
                    "model_type": model.model_type,
                    "fields_count": len(model.fields)
                }
            )
            
            for field in model.fields:
                field_node = FeatureNode(
                    id=self._generate_id(),
                    name=field.name,
                    type=FeatureType.MODEL,
                    category=FeatureCategory.BACKEND,
                    description=f"字段: {field.name} ({field.type})",
                    metadata={
                        "field_type": field.type,
                        "nullable": field.nullable,
                        "primary_key": field.primary_key
                    }
                )
                model_node.add_child(field_node)
            
            models_node.add_child(model_node)
        
        root.add_child(models_node)
        
        return root
    
    def _create_route_node(self, route) -> FeatureNode:
        route_node = FeatureNode(
            id=self._generate_id(),
            name=route.name or route.path,
            type=FeatureType.ROUTE,
            category=FeatureCategory.FRONTEND,
            file_path=route.file_path,
            line_start=route.line,
            description=f"路由: {route.path}",
            metadata={
                "path": route.path,
                "component": route.component
            }
        )
        
        if hasattr(route, 'children') and route.children:
            for child in route.children:
                child_node = self._create_route_node(child)
                route_node.add_child(child_node)
        
        return route_node
    
    def _extract_page_name(self, file_path: str) -> str:
        import os
        filename = os.path.basename(file_path)
        return filename.replace('.tsx', '').replace('.ts', '').replace('.jsx', '').replace('.js', '')
    
    def _generate_id(self) -> str:
        return str(uuid.uuid4())[:8]
