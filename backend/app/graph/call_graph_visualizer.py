"""Call graph visualizer for converting call graphs to Mermaid or JSON."""

from typing import Dict, List

from app.graph.call_graph import CallGraph


class CallGraphVisualizer:
    """Visualize call graphs in Mermaid format or JSON for frontend."""

    def to_mermaid(self, call_graph: CallGraph) -> str:
        """Convert call graph to Mermaid diagram."""
        nodes = call_graph.nodes
        edges = call_graph.edges

        lines = ["graph TD"]

        # 添加节点
        for node_id, node in nodes.items():
            label = node.name
            if node.type == "method":
                label = f"{node.class_name}.{node.name}" if node.class_name else node.name
            lines.append(f'    {self._safe_id(node_id)}["{label}"]')

        # 添加边
        for edge in edges:
            lines.append(f"    {self._safe_id(edge.caller)} --> {self._safe_id(edge.callee)}")

        return "\n".join(lines)

    def to_json(self, call_graph: CallGraph) -> Dict:
        """Convert call graph to JSON format for frontend rendering."""
        nodes = []
        edges = []

        for node_id, node in call_graph.nodes.items():
            label = node.name
            if node.type == "method" and node.class_name:
                label = f"{node.class_name}.{node.name}"

            nodes.append(
                {
                    "id": node_id,
                    "label": label,
                    "file": node.file_path,
                    "line": node.line,
                    "type": node.type,
                    "class_name": node.class_name,
                }
            )

        for i, edge in enumerate(call_graph.edges):
            edges.append(
                {
                    "id": f"e{i}",
                    "source": edge.caller,
                    "target": edge.callee,
                    "file": edge.file_path,
                    "line": edge.line,
                }
            )

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "entry_points": call_graph.entry_points,
                "leaf_functions": call_graph.leaf_functions,
            },
        }

    def _safe_id(self, id: str) -> str:
        """Make node ID safe for Mermaid by replacing special characters."""
        return (
            id.replace(":", "_")
            .replace("/", "_")
            .replace(".", "_")
            .replace("-", "_")
            .replace("@", "_")
        )
