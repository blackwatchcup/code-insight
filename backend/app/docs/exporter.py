"""Document exporter supporting Markdown, HTML and PDF formats."""

from pathlib import Path
from typing import Literal

try:
    import markdown

    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False


class DocumentExporter:
    """Export documentation in various formats."""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(self, content: str, filename: str, format: Literal["markdown", "html"]) -> str:
        """Export document in specified format."""
        if format == "markdown":
            return self._export_markdown(content, filename)
        elif format == "html":
            return self._export_html(content, filename)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_markdown(self, content: str, filename: str) -> str:
        """Export as Markdown file."""
        path = self.output_dir / f"{filename}.md"
        path.write_text(content, encoding="utf-8")
        return str(path)

    def _export_html(self, content: str, filename: str) -> str:
        """Export as HTML file."""
        if not MARKDOWN_AVAILABLE:
            raise RuntimeError("markdown library not installed. Install with: pip install markdown")

        html_content = markdown.markdown(content, extensions=["tables", "fenced_code", "toc"])

        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{filename}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }}
        pre {{
            background: #f5f5f5;
            padding: 15px;
            overflow-x: auto;
            border-radius: 4px;
        }}
        code {{
            background: #f5f5f5;
            padding: 2px 5px;
            border-radius: 3px;
        }}
        pre code {{
            background: none;
            padding: 0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background: #4a5568;
            color: white;
        }}
        h1, h2, h3 {{
            color: #2d3748;
            margin-top: 30px;
        }}
        a {{
            color: #3182ce;
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>"""

        path = self.output_dir / f"{filename}.html"
        path.write_text(full_html, encoding="utf-8")
        return str(path)
