import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class APICallInfo:
    method: str
    path: str
    file_path: str
    line: int
    function_name: str
    params: List[str] = field(default_factory=list)
    request_body: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "method": self.method,
            "path": self.path,
            "file_path": self.file_path,
            "line": self.line,
            "function_name": self.function_name,
            "params": self.params,
            "request_body": self.request_body,
            "headers": self.headers
        }


class APICallAnalyzer:
    PATTERNS = [
        (r'fetch\(\s*["\']([^"\']+)["\']', 'GET', 'fetch'),
        (r'fetch\(\s*["\']([^"\']+)["\']\s*,\s*\{[^}]*method:\s*["\'](\w+)["\']', None, 'fetch-method'),
        (r'axios\.(\w+)\(\s*["\']([^"\']+)["\']', None, 'axios'),
        (r'api\.(\w+)\(\s*["\']([^"\']+)["\']', None, 'api'),
        (r'request\.(\w+)\(\s*["\']([^"\']+)["\']', None, 'request'),
        (r'\$(?:get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']', None, 'jquery'),
        (r'useQuery\(\s*\[["\']([^"\']+)["\']', 'GET', 'react-query'),
        (r'useMutation\(\s*\[["\']([^"\']+)["\']', 'POST', 'react-query'),
        (r'queryClient\.fetchQuery\(\s*\[["\']([^"\']+)["\']', 'GET', 'react-query'),
        (r'swr\(\s*["\']([^"\']+)["\']', 'GET', 'swr'),
        (r'useSWR\(\s*["\']([^"\']+)["\']', 'GET', 'swr'),
        (r'http\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']', None, 'http'),
        (r'(\w+)\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']', None, 'instance'),
    ]
    
    BASE_URL_PATTERNS = [
        r'baseURL\s*[:=]\s*["\']([^"\']+)["\']',
        r'BASE_URL\s*[:=]\s*["\']([^"\']+)["\']',
        r'API_URL\s*[:=]\s*["\']([^"\']+)["\']',
    ]
    
    def __init__(self):
        self.base_urls: Dict[str, str] = {}
    
    def analyze(self, content: str, file_path: str) -> List[APICallInfo]:
        calls = []
        lines = content.split('\n')
        
        self._extract_base_urls(content)
        
        for i, line in enumerate(lines, 1):
            for pattern, default_method, pattern_type in self.PATTERNS:
                matches = re.findall(pattern, line, re.IGNORECASE)
                for match in matches:
                    api_call = self._process_match(match, default_method, pattern_type, file_path, i, lines)
                    if api_call:
                        calls.append(api_call)
        
        return calls
    
    def _extract_base_urls(self, content: str):
        for pattern in self.BASE_URL_PATTERNS:
            matches = re.findall(pattern, content)
            for match in matches:
                self.base_urls['default'] = match
    
    def _process_match(
        self, 
        match, 
        default_method: Optional[str], 
        pattern_type: str,
        file_path: str,
        line_num: int,
        lines: List[str]
    ) -> Optional[APICallInfo]:
        if isinstance(match, tuple):
            if pattern_type == 'fetch-method':
                path = match[0]
                method = match[1].upper()
            elif pattern_type in ['axios', 'api', 'request', 'http']:
                method = match[0].upper()
                path = match[1]
            elif pattern_type == 'instance':
                instance = match[0]
                method = match[1].upper()
                path = match[2]
            elif pattern_type == 'jquery':
                method = self._extract_jquery_method(lines[line_num - 1])
                path = match
            else:
                method = default_method or 'GET'
                path = match[0] if isinstance(match, tuple) else match
        else:
            method = default_method or 'GET'
            path = match
        
        if not path:
            return None
        
        path = self._normalize_path(path)
        function_name = self._extract_function_context(lines, line_num - 1)
        params = self._extract_params(lines[line_num - 1])
        request_body = self._extract_request_body(lines, line_num - 1)
        
        return APICallInfo(
            method=method,
            path=path,
            file_path=file_path,
            line=line_num,
            function_name=function_name,
            params=params,
            request_body=request_body
        )
    
    def _normalize_path(self, path: str) -> str:
        path = path.strip('"\'')
        path = re.sub(r'\$\{[^}]+\}', ':param', path)
        path = re.sub(r'\$\{[^}]+\}', ':param', path)
        path = re.sub(r'`([^`]+)`', r'\1', path)
        
        if path.startswith('${') or path.startswith('`'):
            return path
        
        if not path.startswith('/') and not path.startswith('http'):
            path = '/' + path
        
        return path
    
    def _extract_function_context(self, lines: List[str], current_index: int) -> str:
        for i in range(current_index, -1, -1):
            line = lines[i]
            
            func_match = re.search(r'(?:async\s+)?function\s+(\w+)', line)
            if func_match:
                return func_match.group(1)
            
            arrow_match = re.search(r'const\s+(\w+)\s*=\s*(?:async\s*)?\(', line)
            if arrow_match:
                return arrow_match.group(1)
            
            method_match = re.search(r'(\w+)\s*\([^)]*\)\s*\{', line)
            if method_match:
                return method_match.group(1)
        
        return "anonymous"
    
    def _extract_params(self, line: str) -> List[str]:
        params = []
        
        param_patterns = [
            r'params:\s*\{([^}]+)\}',
            r'query:\s*\{([^}]+)\}',
            r'data:\s*\{([^}]+)\}',
            r'body:\s*\{([^}]+)\}',
        ]
        
        for pattern in param_patterns:
            matches = re.findall(pattern, line)
            for match in matches:
                param_names = re.findall(r'(\w+)\s*:', match)
                params.extend(param_names)
        
        return params
    
    def _extract_request_body(self, lines: List[str], current_index: int) -> Optional[str]:
        for i in range(current_index, min(current_index + 10, len(lines))):
            line = lines[i]
            
            if 'body:' in line or 'data:' in line:
                body_match = re.search(r'(?:body|data):\s*(\{[^}]+\})', line)
                if body_match:
                    return body_match.group(1)
        
        return None
    
    def _extract_jquery_method(self, line: str) -> str:
        if '$.post' in line or '$.ajax' in line and 'POST' in line:
            return 'POST'
        if '$.put' in line or '$.ajax' in line and 'PUT' in line:
            return 'PUT'
        if '$.delete' in line or '$.ajax' in line and 'DELETE' in line:
            return 'DELETE'
        if '$.patch' in line or '$.ajax' in line and 'PATCH' in line:
            return 'PATCH'
        return 'GET'
    
    def analyze_file(self, content: str, file_path: str) -> Dict:
        calls = self.analyze(content, file_path)
        
        summary = {
            "total_calls": len(calls),
            "by_method": {},
            "unique_paths": set(),
            "file_path": file_path
        }
        
        for call in calls:
            if call.method not in summary["by_method"]:
                summary["by_method"][call.method] = 0
            summary["by_method"][call.method] += 1
            summary["unique_paths"].add(call.path)
        
        summary["unique_paths"] = list(summary["unique_paths"])
        
        return {
            "calls": calls,
            "summary": summary
        }
    
    def get_api_endpoints(self, calls: List[APICallInfo]) -> Dict[str, List[APICallInfo]]:
        endpoints: Dict[str, List[APICallInfo]] = {}
        
        for call in calls:
            key = f"{call.method} {call.path}"
            if key not in endpoints:
                endpoints[key] = []
            endpoints[key].append(call)
        
        return endpoints
