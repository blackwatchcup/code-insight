"""API documentation generator."""

from typing import Dict, List

from app.analysis.api_extractor import APIEndpoint


class APIDocGenerator:
    """Generate API documentation from extracted endpoints."""

    def generate(self, apis: List[APIEndpoint]) -> str:
        """Generate markdown documentation for API endpoints."""
        lines = ["# API 文档\n"]

        # 按模块分组
        grouped = self._group_by_module(apis)

        for module, module_apis in grouped.items():
            lines.append(f"## {module}\n")

            for api in module_apis:
                lines.append(f"### {api.method} {api.path}\n")

                if api.description:
                    lines.append(f"{api.description}\n")

                lines.append(f"- **文件位置**: `{api.file_path}:{api.line}`")
                lines.append(f"- **认证**: {'需要' if api.auth_required else '不需要'}")

                if api.tags:
                    lines.append(f"- **标签**: {', '.join(api.tags)}")

                if api.request_body:
                    lines.append(f"- **请求体**: `{api.request_body}`")

                if api.response_model:
                    lines.append(f"- **响应模型**: `{api.response_model}`")

                lines.append("")

                if api.params:
                    lines.append("**参数**\n")
                    lines.append("| 名称 | 类型 | 必填 | 说明 |")
                    lines.append("|------|------|------|------|")
                    for param in api.params:
                        param_name = param.get("name", "")
                        param_type = param.get("type", "")
                        param_required = "是" if param.get("required") else "否"
                        param_desc = param.get("description", "")
                        lines.append(
                            f"| {param_name} | {param_type} | {param_required} | {param_desc} |"
                        )
                    lines.append("")

                lines.append("---\n")

        return "\n".join(lines)

    def _group_by_module(self, apis: List[APIEndpoint]) -> Dict[str, List[APIEndpoint]]:
        """Group API endpoints by module/path prefix."""
        grouped = {}
        for api in apis:
            module = self._extract_module(api.path)
            if module not in grouped:
                grouped[module] = []
            grouped[module].append(api)
        return grouped

    def _extract_module(self, path: str) -> str:
        """Extract module name from API path."""
        parts = path.strip("/").split("/")
        if len(parts) > 1:
            # 根据路径前缀分组
            if parts[0] in ["api", "v1", "v2"]:
                return parts[0].title() + " " + (parts[1].title() if len(parts) > 1 else "")
            return parts[0].title()
        return "Default"
