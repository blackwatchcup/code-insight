import re
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class RouteInfo:
    path: str
    component: str
    file_path: str
    name: str
    children: List['RouteInfo'] = field(default_factory=list)
    line: int = 0
    
    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "component": self.component,
            "file_path": self.file_path,
            "name": self.name,
            "line": self.line,
            "children": [c.to_dict() for c in self.children]
        }


class RouteParser:
    REACT_ROUTE_PATTERNS = [
        (r'<Route\s+path=["\']([^"\']+)["\'].*?element=\{<([^>]+)\s*/?>\}', 'react-jsx'),
        (r'path:\s*["\']([^"\']+)["\']\s*,\s*element:\s*<(\w+)', 'react-object'),
        (r'<Route[^>]*path=["\']([^"\']+)["\'][^>]*>', 'react-simple'),
    ]
    
    VUE_ROUTE_PATTERNS = [
        (r'path:\s*["\']([^"\']+)["\']\s*,\s*component:\s*(\w+)', 'vue-component'),
        (r'path:\s*["\']([^"\']+)["\']\s*,\s*name:\s*["\']([^"\']+)["\']', 'vue-name'),
    ]
    
    NEXTJS_PATTERNS = [
        (r'pages/(\w+)\.tsx?', 'nextjs-pages'),
        (r'app/(\w+)/page\.tsx?', 'nextjs-app'),
    ]
    
    def parse_react_router(self, content: str, file_path: str) -> List[RouteInfo]:
        routes = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            for pattern, pattern_type in self.REACT_ROUTE_PATTERNS:
                matches = re.findall(pattern, line, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        path = match[0]
                        component = match[1] if len(match) > 1 else ""
                    else:
                        path = match
                        component = ""
                    
                    name = self._extract_route_name(component or path)
                    
                    routes.append(RouteInfo(
                        path=path,
                        component=component,
                        file_path=file_path,
                        name=name,
                        line=i,
                        children=[]
                    ))
        
        return self._build_route_tree(routes)
    
    def parse_vue_router(self, content: str, file_path: str) -> List[RouteInfo]:
        routes = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            for pattern, pattern_type in self.VUE_ROUTE_PATTERNS:
                matches = re.findall(pattern, line, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        path = match[0]
                        component_or_name = match[1] if len(match) > 1 else ""
                    else:
                        path = match
                        component_or_name = ""
                    
                    name = self._extract_route_name(component_or_name or path)
                    
                    routes.append(RouteInfo(
                        path=path,
                        component=component_or_name,
                        file_path=file_path,
                        name=name,
                        line=i,
                        children=[]
                    ))
        
        return routes
    
    def detect_framework(self, content: str) -> str:
        content_lower = content.lower()
        
        if 'react-router' in content_lower or 'reactrouter' in content_lower:
            return 'react'
        if 'createBrowserRouter' in content or 'BrowserRouter' in content:
            return 'react'
        if 'vue-router' in content_lower or 'createrouter' in content_lower:
            return 'vue'
        if 'next/router' in content or 'useRouter' in content:
            return 'nextjs'
        if 'next/navigation' in content:
            return 'nextjs'
        
        return 'unknown'
    
    def parse(self, content: str, file_path: str) -> List[RouteInfo]:
        framework = self.detect_framework(content)
        
        if framework == 'react':
            return self.parse_react_router(content, file_path)
        elif framework == 'vue':
            return self.parse_vue_router(content, file_path)
        elif framework == 'nextjs':
            return self._parse_nextjs_routes(content, file_path)
        
        return []
    
    def _parse_nextjs_routes(self, content: str, file_path: str) -> List[RouteInfo]:
        routes = []
        
        if '/pages/' in file_path or '\\pages\\' in file_path:
            match = re.search(r'pages[\\/](\w+)\.tsx?', file_path)
            if match:
                page_name = match.group(1)
                routes.append(RouteInfo(
                    path=f'/{page_name}' if page_name != 'index' else '/',
                    component=page_name,
                    file_path=file_path,
                    name=page_name,
                    children=[]
                ))
        
        if '/app/' in file_path or '\\app\\' in file_path:
            match = re.search(r'app[\\/](\w+)[\\/]page\.tsx?', file_path)
            if match:
                page_name = match.group(1)
                routes.append(RouteInfo(
                    path=f'/{page_name}',
                    component=f'{page_name}Page',
                    file_path=file_path,
                    name=page_name,
                    children=[]
                ))
        
        return routes
    
    def _extract_route_name(self, identifier: str) -> str:
        name = identifier.replace('Page', '').replace('View', '').replace('Component', '')
        name = re.sub(r'([A-Z])', r' \1', name).strip()
        return name if name else identifier
    
    def _build_route_tree(self, routes: List[RouteInfo]) -> List[RouteInfo]:
        root_routes = []
        child_map: Dict[str, List[RouteInfo]] = {}
        
        for route in routes:
            if route.path == '/' or not route.path.startswith('/'):
                root_routes.append(route)
            else:
                parent_path = '/'.join(route.path.split('/')[:-1]) or '/'
                if parent_path not in child_map:
                    child_map[parent_path] = []
                child_map[parent_path].append(route)
        
        for route in root_routes:
            if route.path in child_map:
                route.children = child_map[route.path]
        
        return root_routes
