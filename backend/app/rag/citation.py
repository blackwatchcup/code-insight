import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Citation:
    file: str
    line: int
    content: Optional[str] = None
    end_line: Optional[int] = None

    def to_markdown(self) -> str:
        if self.end_line and self.end_line != self.line:
            return f"[{self.file}:{self.line}-{self.end_line}]({self.file}#L{self.line})"
        return f"[{self.file}:{self.line}]({self.file}#L{self.line})"

    def to_dict(self) -> Dict:
        return {
            "file": self.file,
            "line": self.line,
            "end_line": self.end_line,
            "content": self.content,
        }


class CitationExtractor:
    FILE_LINE_PATTERN = re.compile(r"\[([^\]:]+):(\d+)(?:-(\d+))?\]\([^\)]+\)")

    FILE_LINE_SIMPLE_PATTERN = re.compile(r"(?:^|\s)([^\s:]+\.py):(\d+)(?::(\d+))?(?:\s|$)")

    def extract(self, text: str) -> List[Citation]:
        citations = []

        for match in self.FILE_LINE_PATTERN.finditer(text):
            file_path = match.group(1)
            line = int(match.group(2))
            end_line = int(match.group(3)) if match.group(3) else None

            citations.append(Citation(file=file_path, line=line, end_line=end_line))

        for match in self.FILE_LINE_SIMPLE_PATTERN.finditer(text):
            file_path = match.group(1)
            line = int(match.group(2))
            end_line = int(match.group(3)) if match.group(3) else None

            citation = Citation(file=file_path, line=line, end_line=end_line)

            if citation not in citations:
                citations.append(citation)

        return citations

    def format_citation(
        self,
        file_path: str,
        start_line: int,
        end_line: Optional[int] = None,
        content: Optional[str] = None,
    ) -> str:
        citation = Citation(file=file_path, line=start_line, end_line=end_line, content=content)
        return citation.to_markdown()

    def add_citations_to_answer(self, answer: str, sources: List[Dict]) -> str:
        if not sources:
            return answer

        citation_section = "\n\n**Sources:**\n"
        for source in sources:
            file_path = source.get("file_path", source.get("file", ""))
            start_line = source.get("start_line", source.get("line", 1))
            end_line = source.get("end_line")

            citation = self.format_citation(file_path, start_line, end_line)
            citation_section += f"- {citation}\n"

        return answer + citation_section

    def extract_code_snippets(self, text: str, code_files: Dict[str, List[str]]) -> List[Dict]:
        snippets = []

        code_block_pattern = re.compile(r"```(\w+)?\n(.*?)```", re.DOTALL)

        for match in code_block_pattern.finditer(text):
            language = match.group(1) or "unknown"
            code = match.group(2).strip()

            snippets.append(
                {"language": language, "code": code, "start": match.start(), "end": match.end()}
            )

        return snippets
