import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PageFunction:
    name: str
    type: str
    description: str
    line: int
    handler: str
    file_path: str = ""
    params: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "line": self.line,
            "handler": self.handler,
            "file_path": self.file_path,
            "params": self.params,
        }


class FrontendAnalyzer:
    CLICK_PATTERNS = [
        r"onClick=\{([^}]+)\}",
        r"onClick=\{\s*\(\s*\)\s*=>\s*([^}]+)\}",
        r'@click="([^"]+)"',
        r"handleClick\w*\s*[=(]",
        r"onPress=\{([^}]+)\}",
    ]

    SUBMIT_PATTERNS = [
        r"onSubmit=\{([^}]+)\}",
        r'@submit="([^"]+)"',
        r"handleSubmit\w*\s*[=(]",
        r"onSubmit=\{\s*async\s*\([^)]*\)\s*=>\s*([^}]+)\}",
    ]

    FETCH_PATTERNS = [
        (r'(fetch|axios|request)\s*\(\s*["\']([^"\']+)["\']', "fetch"),
        (r'api\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', "api"),
        (r'useQuery\(["\']([^"\']+)["\']', "query"),
        (r'useMutation\(["\']([^"\']+)["\']', "mutation"),
        (r'\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', "method"),
    ]

    NAVIGATION_PATTERNS = [
        r'navigate\(["\']([^"\']+)["\']',
        r'router\.push\(["\']([^"\']+)["\']',
        r'history\.push\(["\']([^"\']+)["\']',
        r'Link\s+to=["\']([^"\']+)["\']',
        r'<Link\s+href=["\']([^"\']+)["\']',
    ]

    STATE_PATTERNS = [
        r"useState<(\w+)>\s*\(\s*([^)]*)\)",
        r"const\s+\[(\w+),\s*set(\w+)\]\s*=\s*useState",
        r"useSelector\(([^)]+)\)",
        r"useStore\(([^)]+)\)",
    ]

    NAME_MAP = {
        "delete": "删除",
        "remove": "移除",
        "edit": "编辑",
        "update": "更新",
        "save": "保存",
        "submit": "提交",
        "cancel": "取消",
        "add": "新增",
        "create": "创建",
        "search": "搜索",
        "filter": "筛选",
        "export": "导出",
        "import": "导入",
        "load": "加载",
        "fetch": "获取",
        "refresh": "刷新",
        "reset": "重置",
        "copy": "复制",
        "download": "下载",
        "upload": "上传",
        "login": "登录",
        "logout": "登出",
        "register": "注册",
        "toggle": "切换",
        "select": "选择",
        "close": "关闭",
        "open": "打开",
        "show": "显示",
        "hide": "隐藏",
        "expand": "展开",
        "collapse": "折叠",
        "sort": "排序",
        "paginate": "分页",
        "navigate": "导航",
    }

    def extract_functions(self, content: str, file_path: str) -> List[PageFunction]:
        functions = []

        functions.extend(self._extract_clicks(content, file_path))
        functions.extend(self._extract_submits(content, file_path))
        functions.extend(self._extract_fetches(content, file_path))
        functions.extend(self._extract_navigations(content, file_path))
        functions.extend(self._extract_states(content, file_path))

        return functions

    def _extract_clicks(self, content: str, file_path: str) -> List[PageFunction]:
        functions = []
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            for pattern in self.CLICK_PATTERNS:
                matches = re.findall(pattern, line)
                for match in matches:
                    handler = match if isinstance(match, str) else match[0]
                    name = self._infer_function_name(handler)

                    functions.append(
                        PageFunction(
                            name=name,
                            type="click",
                            description=f"按钮点击: {handler}",
                            line=i,
                            handler=handler,
                            file_path=file_path,
                        )
                    )

        return functions

    def _extract_submits(self, content: str, file_path: str) -> List[PageFunction]:
        functions = []
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            for pattern in self.SUBMIT_PATTERNS:
                matches = re.findall(pattern, line)
                for match in matches:
                    handler = match if isinstance(match, str) else match[0]
                    name = self._infer_function_name(handler)

                    functions.append(
                        PageFunction(
                            name=name,
                            type="submit",
                            description=f"表单提交: {handler}",
                            line=i,
                            handler=handler,
                            file_path=file_path,
                        )
                    )

        return functions

    def _extract_fetches(self, content: str, file_path: str) -> List[PageFunction]:
        functions = []
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            for pattern, fetch_type in self.FETCH_PATTERNS:
                matches = re.findall(pattern, line)
                for match in matches:
                    if isinstance(match, tuple):
                        if fetch_type == "fetch":
                            method = match[0].upper()
                            path = match[1]
                        elif fetch_type == "api":
                            method = match[0].upper()
                            path = match[1]
                        elif fetch_type == "method":
                            method = match[0].upper()
                            path = match[1]
                        else:
                            method = "GET"
                            path = match[0]
                    else:
                        method = "GET"
                        path = match

                    name = self._infer_function_name(path)

                    functions.append(
                        PageFunction(
                            name=f"{name}数据获取",
                            type="fetch",
                            description=f"API调用: {method} {path}",
                            line=i,
                            handler=f"{method} {path}",
                            file_path=file_path,
                            params=[path],
                        )
                    )

        return functions

    def _extract_navigations(self, content: str, file_path: str) -> List[PageFunction]:
        functions = []
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            for pattern in self.NAVIGATION_PATTERNS:
                matches = re.findall(pattern, line)
                for match in matches:
                    path = match if isinstance(match, str) else match[0]

                    functions.append(
                        PageFunction(
                            name="页面导航",
                            type="navigation",
                            description=f"导航到: {path}",
                            line=i,
                            handler=f"navigate({path})",
                            file_path=file_path,
                            params=[path],
                        )
                    )

        return functions

    def _extract_states(self, content: str, file_path: str) -> List[PageFunction]:
        functions = []
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            for pattern in self.STATE_PATTERNS:
                matches = re.findall(pattern, line)
                for match in matches:
                    if isinstance(match, tuple):
                        state_name = (
                            match[0] if match[0] else match[1] if len(match) > 1 else "state"
                        )
                    else:
                        state_name = match

                    functions.append(
                        PageFunction(
                            name=f"{state_name}状态管理",
                            type="state",
                            description=f"状态定义: {state_name}",
                            line=i,
                            handler=f"useState({state_name})",
                            file_path=file_path,
                        )
                    )

        return functions

    def _infer_function_name(self, handler: str) -> str:
        handler_lower = handler.lower()

        for key, name in self.NAME_MAP.items():
            if key in handler_lower:
                return name

        if handler.startswith("handle"):
            return handler.replace("handle", "").replace("Handle", "")

        if handler.startswith("on"):
            return handler.replace("on", "").replace("On", "")

        return handler

    def analyze_page(self, content: str, file_path: str) -> Dict:
        functions = self.extract_functions(content, file_path)

        summary = {"total_functions": len(functions), "by_type": {}, "file_path": file_path}

        for func in functions:
            if func.type not in summary["by_type"]:
                summary["by_type"][func.type] = 0
            summary["by_type"][func.type] += 1

        return {"functions": functions, "summary": summary}
