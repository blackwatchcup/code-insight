"""Architecture diagram generator based on feature tree."""

from typing import Dict, List

from app.analysis.feature_tree import FeatureCategory, FeatureNode, FeatureTree


class ArchGenerator:
    """Generate architecture diagrams from feature tree."""

    def __init__(self):
        pass

    async def generate(self, feature_tree: FeatureTree) -> Dict:
        """Generate architecture diagram from feature tree."""
        modules = self._extract_modules(feature_tree)

        # 自动生成架构图
        mermaid_code = self._auto_generate(modules)

        return {
            "type": "architecture",
            "format": "mermaid",
            "content": mermaid_code,
            "modules": modules,
        }

    def _extract_modules(self, feature_tree: FeatureTree) -> List[Dict]:
        """Extract modules from feature tree."""
        modules = []

        # 提取前端模块
        for child in feature_tree.frontend.children:
            self._collect_modules_from_node(child, modules, "frontend")

        # 提取后端模块
        for child in feature_tree.backend.children:
            self._collect_modules_from_node(child, modules, "backend")

        return modules

    def _collect_modules_from_node(self, node: FeatureNode, modules: List[Dict], category: str):
        """Recursively collect modules from a node."""
        if node.children:
            for child in node.children:
                self._collect_modules_from_node(child, modules, category)
        else:
            modules.append(
                {
                    "name": node.name,
                    "type": category,
                    "category": node.type.value,
                    "description": node.description,
                }
            )

    def _auto_generate(self, modules: List[Dict]) -> str:
        """Generate Mermaid code from modules."""
        lines = ["graph TB"]

        # 前端子图
        frontend_modules = [m for m in modules if m["type"] == "frontend"]
        if frontend_modules:
            lines.append("    subgraph Frontend[前端]")
            for m in frontend_modules[:10]:  # 限制数量
                node_id = f"f_{m['name'].replace(' ', '_').replace('.', '')}"
                lines.append(f"        {node_id}[{m['name']}]")
            lines.append("    end")

        # 后端子图
        backend_modules = [m for m in modules if m["type"] == "backend"]
        if backend_modules:
            lines.append("    subgraph Backend[后端]")
            for m in backend_modules[:10]:
                node_id = f"b_{m['name'].replace(' ', '_').replace('.', '')}"
                lines.append(f"        {node_id}[{m['name']}]")
            lines.append("    end")

        # 数据库
        lines.append("    DB[(数据库)]")

        # 添加连接
        if frontend_modules and backend_modules:
            lines.append("    Frontend --> Backend")
        if backend_modules:
            lines.append("    Backend --> DB")

        return "\n".join(lines)
