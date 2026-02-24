import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class APIEndpoint:
    method: str
    path: str
    handler: str
    file_path: str
    line: int
    description: str = ""
    auth_required: bool = False
    params: List[Dict] = field(default_factory=list)
    request_body: Optional[str] = None
    response_model: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "method": self.method,
            "path": self.path,
            "handler": self.handler,
            "file_path": self.file_path,
            "line": self.line,
            "description": self.description,
            "auth_required": self.auth_required,
            "params": self.params,
            "request_body": self.request_body,
            "response_model": self.response_model,
            "tags": self.tags,
        }


class APIExtractor:
    FASTAPI_PATTERNS = [
        r'@(router|app)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
        r'@(router|app)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']\s*,\s*([^)]+)\)',
    ]

    FLASK_PATTERNS = [
        r'@app\.route\(["\']([^"\']+)["\'].*methods\s*=\s*\[([^\]]+)\]',
        r'@(\w+)\.route\(["\']([^"\']+)["\'].*methods\s*=\s*\[([^\]]+)\]',
    ]

    EXPRESS_PATTERNS = [
        r'(app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
    ]

    SPRING_PATTERNS = [
        r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)\s*\(["\']([^"\']+)["\']',
    ]

    AUTH_INDICATORS = [
        "Depends(get_current_user)",
        "Depends(get_current_user_required)",
        "@login_required",
        "@require_auth",
        "auth_required",
        "current_user",
        "jwt_required",
        "OAuth2",
        "HTTPBearer",
    ]

    def extract_from_fastapi(self, content: str, file_path: str) -> List[APIEndpoint]:
        endpoints = []
        lines = content.split("\n")

        router_prefix = self._extract_router_prefix(content)

        for i, line in enumerate(lines, 1):
            for pattern in self.FASTAPI_PATTERNS:
                matches = re.findall(pattern, line, re.IGNORECASE)
                for match in matches:
                    if len(match) >= 3:
                        method = match[1].upper() if match[1] else "GET"
                        path = match[2]

                        if router_prefix and not path.startswith(router_prefix):
                            path = router_prefix + path

                        handler = self._find_handler(lines, i)
                        description = self._extract_docstring(lines, i)
                        auth_required = self._check_auth(lines, i)
                        params = self._extract_fastapi_params(lines, i)
                        request_body = self._extract_request_body_type(lines, i)
                        response_model = self._extract_response_model(line)
                        tags = self._extract_tags(line)

                        endpoints.append(
                            APIEndpoint(
                                method=method,
                                path=path,
                                handler=handler,
                                file_path=file_path,
                                line=i,
                                description=description,
                                auth_required=auth_required,
                                params=params,
                                request_body=request_body,
                                response_model=response_model,
                                tags=tags,
                            )
                        )

        return endpoints

    def extract_from_flask(self, content: str, file_path: str) -> List[APIEndpoint]:
        endpoints = []
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            for pattern in self.FLASK_PATTERNS:
                matches = re.findall(pattern, line, re.IGNORECASE)
                for match in matches:
                    if len(match) >= 2:
                        if len(match) == 2:
                            path = match[0]
                            methods_str = match[1]
                        else:
                            path = match[1]
                            methods_str = match[2]

                        methods = re.findall(r'["\'](\w+)["\']', methods_str)
                        if not methods:
                            methods = ["GET"]

                        handler = self._find_handler(lines, i)
                        description = self._extract_docstring(lines, i)
                        auth_required = self._check_auth(lines, i)

                        for method in methods:
                            endpoints.append(
                                APIEndpoint(
                                    method=method.upper(),
                                    path=path,
                                    handler=handler,
                                    file_path=file_path,
                                    line=i,
                                    description=description,
                                    auth_required=auth_required,
                                )
                            )

        return endpoints

    def extract_from_express(self, content: str, file_path: str) -> List[APIEndpoint]:
        endpoints = []
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            for pattern in self.EXPRESS_PATTERNS:
                matches = re.findall(pattern, line, re.IGNORECASE)
                for match in matches:
                    if len(match) >= 3:
                        method = match[1].upper()
                        path = match[2]

                        handler = self._find_js_handler(lines, i)
                        description = self._extract_js_comment(lines, i)

                        endpoints.append(
                            APIEndpoint(
                                method=method,
                                path=path,
                                handler=handler,
                                file_path=file_path,
                                line=i,
                                description=description,
                            )
                        )

        return endpoints

    def extract_from_spring(self, content: str, file_path: str) -> List[APIEndpoint]:
        endpoints = []
        lines = content.split("\n")

        method_map = {
            "GetMapping": "GET",
            "PostMapping": "POST",
            "PutMapping": "PUT",
            "DeleteMapping": "DELETE",
            "PatchMapping": "PATCH",
            "RequestMapping": "GET",
        }

        for i, line in enumerate(lines, 1):
            for pattern in self.SPRING_PATTERNS:
                matches = re.findall(pattern, line)
                for match in matches:
                    annotation = match[0]
                    path = match[1]
                    method = method_map.get(annotation, "GET")

                    handler = self._find_java_method(lines, i)
                    description = self._extract_java_doc(lines, i)

                    endpoints.append(
                        APIEndpoint(
                            method=method,
                            path=path,
                            handler=handler,
                            file_path=file_path,
                            line=i,
                            description=description,
                        )
                    )

        return endpoints

    def detect_framework(self, content: str) -> str:
        if "fastapi" in content.lower() or "APIRouter" in content:
            return "fastapi"
        if "flask" in content.lower() or "@app.route" in content:
            return "flask"
        if "express" in content.lower() or "app.get" in content or "router.get" in content:
            return "express"
        if "@RestController" in content or "@Controller" in content or "@GetMapping" in content:
            return "spring"
        return "unknown"

    def extract(self, content: str, file_path: str) -> List[APIEndpoint]:
        framework = self.detect_framework(content)

        if framework == "fastapi":
            return self.extract_from_fastapi(content, file_path)
        elif framework == "flask":
            return self.extract_from_flask(content, file_path)
        elif framework == "express":
            return self.extract_from_express(content, file_path)
        elif framework == "spring":
            return self.extract_from_spring(content, file_path)

        return []

    def _extract_router_prefix(self, content: str) -> str:
        match = re.search(r'include_router\([^,]+,\s*prefix\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)

        match = re.search(r'APIRouter\([^)]*prefix\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)

        return ""

    def _find_handler(self, lines: List[str], start_index: int) -> str:
        for i in range(start_index, min(start_index + 10, len(lines))):
            line = lines[i]
            match = re.search(r"async\s+def\s+(\w+)|def\s+(\w+)", line)
            if match:
                return match.group(1) or match.group(2)
        return "anonymous"

    def _find_js_handler(self, lines: List[str], start_index: int) -> str:
        for i in range(start_index, min(start_index + 5, len(lines))):
            line = lines[i]
            match = re.search(r"(?:async\s+)?function\s+(\w+)|(?:async\s+)?\(([^)]*)\)\s*=>", line)
            if match:
                return match.group(1) or "arrow_function"
        return "anonymous"

    def _find_java_method(self, lines: List[str], start_index: int) -> str:
        for i in range(start_index, min(start_index + 5, len(lines))):
            line = lines[i]
            match = re.search(r"public\s+\w+\s+(\w+)\s*\(", line)
            if match:
                return match.group(1)
        return "anonymous"

    def _extract_docstring(self, lines: List[str], start_index: int) -> str:
        for i in range(start_index, min(start_index + 10, len(lines))):
            line = lines[i].strip()
            if line.startswith('"""') or line.startswith("'''"):
                docstring = line.strip('"""').strip("'''")
                if docstring:
                    return docstring

                if i + 1 < len(lines):
                    return lines[i + 1].strip()

        return ""

    def _extract_js_comment(self, lines: List[str], start_index: int) -> str:
        for i in range(start_index - 1, max(0, start_index - 5), -1):
            line = lines[i].strip()
            if line.startswith("//"):
                return line[2:].strip()
            if line.startswith("*"):
                return line[1:].strip()
            if line.startswith("/*"):
                return line[2:].strip("*/").strip()

        return ""

    def _extract_java_doc(self, lines: List[str], start_index: int) -> str:
        for i in range(start_index - 1, max(0, start_index - 10), -1):
            line = lines[i].strip()
            if line.startswith("*") and not line.startswith("*/"):
                return line[1:].strip()
            if line.startswith("/**"):
                return line[3:].strip("*/").strip()

        return ""

    def _check_auth(self, lines: List[str], start_index: int) -> bool:
        for i in range(start_index, min(start_index + 15, len(lines))):
            line = lines[i]
            for indicator in self.AUTH_INDICATORS:
                if indicator in line:
                    return True
        return False

    def _extract_fastapi_params(self, lines: List[str], start_index: int) -> List[Dict]:
        params = []

        for i in range(start_index, min(start_index + 15, len(lines))):
            line = lines[i]

            path_param_match = re.search(r"(\w+):\s*(?:str|int|float)", line)
            if path_param_match:
                params.append({"name": path_param_match.group(1), "type": "path", "required": True})

            query_param_match = re.search(r"(\w+):\s*(?:Optional\[)?(\w+)(?:\])?\s*=\s*(.+)", line)
            if query_param_match:
                params.append(
                    {
                        "name": query_param_match.group(1),
                        "type": "query",
                        "required": "Optional" not in line,
                    }
                )

        return params

    def _extract_request_body_type(self, lines: List[str], start_index: int) -> Optional[str]:
        for i in range(start_index, min(start_index + 15, len(lines))):
            line = lines[i]
            match = re.search(r"data:\s*(\w+)|body:\s*(\w+)|request:\s*(\w+)", line)
            if match:
                return match.group(1) or match.group(2) or match.group(3)
        return None

    def _extract_response_model(self, line: str) -> Optional[str]:
        match = re.search(r"response_model\s*=\s*(\w+)", line)
        if match:
            return match.group(1)
        return None

    def _extract_tags(self, line: str) -> List[str]:
        match = re.search(r"tags\s*=\s*\[([^\]]+)\]", line)
        if match:
            tags_str = match.group(1)
            return re.findall(r'["\']([^"\']+)["\']', tags_str)
        return []

    def get_api_summary(self, endpoints: List[APIEndpoint]) -> Dict:
        summary = {
            "total_endpoints": len(endpoints),
            "by_method": {},
            "by_auth": {"required": 0, "optional": 0},
            "paths": [],
        }

        for endpoint in endpoints:
            if endpoint.method not in summary["by_method"]:
                summary["by_method"][endpoint.method] = 0
            summary["by_method"][endpoint.method] += 1

            if endpoint.auth_required:
                summary["by_auth"]["required"] += 1
            else:
                summary["by_auth"]["optional"] += 1

            summary["paths"].append(f"{endpoint.method} {endpoint.path}")

        return summary
