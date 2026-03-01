import asyncio
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.parsers.base import ParseResult
from app.parsers.factory import ParserFactory


@dataclass
class StructureSummary:
    total_files: int = 0
    total_functions: int = 0
    total_classes: int = 0
    total_imports: int = 0
    total_variables: int = 0
    total_calls: int = 0
    by_language: Dict[str, int] = field(default_factory=dict)
    by_directory: Dict[str, int] = field(default_factory=dict)
    errors: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class ProjectStructure:
    project_path: str
    files: List[ParseResult] = field(default_factory=list)
    summary: StructureSummary = field(default_factory=StructureSummary)


class StructureService:
    def __init__(self, max_file_size: int = 10 * 1024 * 1024):
        self.max_file_size = max_file_size
        self.skip_dirs = {
            "node_modules",
            ".git",
            "__pycache__",
            ".venv",
            "venv",
            "dist",
            "build",
            ".next",
            ".nuxt",
            "coverage",
            ".pytest_cache",
            ".mypy_cache",
            "egg-info",
        }
        self.skip_extensions = {
            ".pyc",
            ".pyo",
            ".pyd",
            ".so",
            ".dll",
            ".dylib",
            ".exe",
            ".bin",
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".ico",
            ".svg",
            ".woff",
            ".woff2",
            ".ttf",
            ".eot",
            ".mp3",
            ".mp4",
            ".avi",
            ".mov",
            ".zip",
            ".tar",
            ".gz",
            ".rar",
            ".7z",
            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".ppt",
            ".pptx",
            ".lock",
            ".sum",
        }

    async def extract_structure(
        self,
        project_path: str,
        progress_callback: Optional[callable] = None,
    ) -> ProjectStructure:
        project_dir = Path(project_path)
        if not project_dir.exists():
            raise ValueError(f"Project path does not exist: {project_path}")

        files = []
        summary = StructureSummary()

        all_files = list(self._iter_source_files(project_dir))
        total_files = len(all_files)

        for idx, file_path in enumerate(all_files):
            if progress_callback:
                await progress_callback(
                    stage="parsing",
                    current=idx + 1,
                    total=total_files,
                    message=f"Parsing {file_path.relative_to(project_dir)}",
                )

            result = await self._parse_file(file_path)
            files.append(result)

            if result.error:
                summary.errors.append(
                    {
                        "file": str(file_path),
                        "error": result.error,
                    }
                )
            else:
                summary.total_functions += len(result.functions)
                summary.total_classes += len(result.classes)
                summary.total_imports += len(result.imports)
                summary.total_variables += len(result.variables)
                summary.total_calls += len(result.calls)

                lang = result.language
                summary.by_language[lang] = summary.by_language.get(lang, 0) + 1

                rel_dir = str(file_path.parent.relative_to(project_dir))
                if rel_dir == ".":
                    rel_dir = "<root>"
                summary.by_directory[rel_dir] = summary.by_directory.get(rel_dir, 0) + 1

        summary.total_files = len(files)

        return ProjectStructure(
            project_path=str(project_dir),
            files=files,
            summary=summary,
        )

    def _iter_source_files(self, project_dir: Path):
        for root, dirs, files in os.walk(project_dir):
            dirs[:] = [d for d in dirs if d not in self.skip_dirs and not d.startswith(".")]

            for file in files:
                file_path = Path(root) / file

                if file.startswith("."):
                    continue

                ext = file_path.suffix.lower()
                if ext in self.skip_extensions:
                    continue

                if not ParserFactory.is_supported(ext):
                    continue

                try:
                    if file_path.stat().st_size > self.max_file_size:
                        continue
                except OSError:
                    continue

                yield file_path

    async def _parse_file(self, file_path: Path) -> ParseResult:
        ext = file_path.suffix.lower()
        try:
            parser = ParserFactory.get_parser_by_extension(ext)

            if not parser:
                return ParseResult(
                    file_path=str(file_path),
                    language="unknown",
                    error=f"No parser for extension: {ext}",
                )

            content = file_path.read_text(encoding="utf-8", errors="ignore")
            result = parser.parse(content, str(file_path))
            return result
        except Exception as e:
            return ParseResult(
                file_path=str(file_path),
                language="unknown",
                error=str(e),
            )

    def extract_file_structure(self, file_path: str) -> ParseResult:
        path = Path(file_path)
        if not path.exists():
            return ParseResult(
                file_path=file_path,
                language="unknown",
                error=f"File does not exist: {file_path}",
            )

        ext = path.suffix.lower()
        parser = ParserFactory.get_parser_by_extension(ext)

        if not parser:
            return ParseResult(
                file_path=file_path,
                language="unknown",
                error=f"No parser for extension: {ext}",
            )

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            result = parser.parse(content, file_path)
            return result
        except Exception as e:
            return ParseResult(
                file_path=file_path,
                language=parser.get_language(),
                error=str(e),
            )

    def get_supported_languages(self) -> List[str]:
        return ParserFactory.supported_languages()

    def get_supported_extensions(self) -> List[str]:
        return ParserFactory.supported_extensions()
