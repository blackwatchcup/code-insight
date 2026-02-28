"""项目上下文管理服务 - 管理README、项目摘要等上下文信息"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.llm.service import LLMService
from app.models.project import Project
from app.services.project_service import ProjectService

logger = logging.getLogger(__name__)


class ContextType(str, Enum):
    """上下文类型"""
    README = "readme"
    PROJECT_SUMMARY = "project_summary"
    TECH_STACK = "tech_stack"
    CODE_CONTEXT = "code_context"
    FILE_STRUCTURE = "file_structure"


@dataclass
class ProjectContext:
    """项目上下文数据"""
    project_id: str
    project_name: str
    readme_content: Optional[str] = None
    project_summary: Optional[str] = None
    tech_stack: List[str] = field(default_factory=list)
    file_count: int = 0
    line_count: int = 0
    source_type: Optional[str] = None
    branch: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_prompt_context(self) -> str:
        """将上下文转换为可用于LLM提示的格式"""
        parts = [
            "=== 项目信息 ===",
            f"项目名称: {self.project_name}",
        ]

        if self.source_type:
            parts.append(f"来源类型: {self.source_type}")
        if self.branch:
            parts.append(f"分支: {self.branch}")
        
        parts.append(f"文件数: {self.file_count}")
        parts.append(f"代码行数: {self.line_count}")

        if self.tech_stack:
            parts.append(f"技术栈: {', '.join(self.tech_stack)}")

        parts.append("=" * 40)

        if self.project_summary:
            parts.append("\n=== 项目摘要 ===")
            parts.append(self.project_summary)
            parts.append("=" * 40)

        if self.readme_content:
            parts.append("\n=== README ===")
            # 限制README长度
            readme = self.readme_content
            if len(readme) > 8000:
                readme = readme[:8000] + "\n... (内容过长，已截断)"
            parts.append(readme)
            parts.append("=" * 40)

        return "\n".join(parts)


class ProjectContextService:
    """项目上下文管理服务"""

    # 用于生成项目摘要的提示词
    SUMMARY_PROMPT = """你是一个专业的软件架构师。请根据以下项目信息生成一个简洁但全面的项目摘要。

项目名称: {name}
技术栈: {tech_stack}
文件数: {file_count}
代码行数: {line_count}

README内容:
{readme}

请生成一个包含以下内容的摘要（使用中文）：
1. 项目的主要目的和功能（2-3句话）
2. 核心技术架构
3. 主要功能模块
4. 项目特点和亮点

摘要（不超过500字）:"""

    # 用于分析用户问题需要什么数据的提示词
    DATA_NEEDS_PROMPT = """你是一个代码分析专家。用户想要了解一个代码项目的信息。

项目信息:
- 名称: {project_name}
- 技术栈: {tech_stack}

用户问题: {question}

请分析用户的问题，确定需要提供哪些信息才能准确回答。从以下选项中选择需要的信息类型（可以多选）：

可选信息类型：
1. readme - 项目的README文档内容
2. summary - 项目的整体摘要
3. code - 相关的代码片段（需要指定搜索关键词）
4. structure - 项目的文件结构
5. features - 项目的功能特性列表
6. apis - 项目的API接口信息

请以JSON格式返回，格式如下：
{{
    "needs": ["readme", "summary", ...],
    "search_keywords": ["keyword1", "keyword2"],  // 如果需要code，提供搜索关键词
    "reason": "简要说明为什么需要这些信息"
}}

只返回JSON，不要有其他内容:"""

    def __init__(self, db: Session, llm: Optional[LLMService] = None):
        self.db = db
        self.project_service = ProjectService(db)
        self.llm = llm or LLMService()

    def get_context(self, project_id: str) -> Optional[ProjectContext]:
        """获取项目的完整上下文"""
        project = self.project_service.get_project(project_id)
        if not project:
            return None

        tech_stack = []
        if project.tech_stack:
            try:
                tech_stack = json.loads(project.tech_stack)
            except (json.JSONDecodeError, TypeError):
                tech_stack = []

        return ProjectContext(
            project_id=project.id,
            project_name=project.name,
            readme_content=project.readme_content,
            project_summary=project.project_summary,
            tech_stack=tech_stack,
            file_count=project.file_count,
            line_count=project.line_count,
            source_type=project.source_type.value if project.source_type else None,
            branch=project.branch,
        )

    async def generate_project_summary(self, project_id: str) -> Optional[str]:
        """使用LLM生成项目摘要"""
        project = self.project_service.get_project(project_id)
        if not project:
            return None

        # 如果已有摘要且README没变化，直接返回
        if project.project_summary:
            return project.project_summary

        tech_stack = []
        if project.tech_stack:
            try:
                tech_stack = json.loads(project.tech_stack)
            except (json.JSONDecodeError, TypeError):
                pass

        prompt = self.SUMMARY_PROMPT.format(
            name=project.name,
            tech_stack=", ".join(tech_stack) if tech_stack else "未知",
            file_count=project.file_count,
            line_count=project.line_count,
            readme=project.readme_content or "（无README文件）",
        )

        try:
            summary = await self.llm.generate(prompt)
            # 保存摘要到数据库
            project.project_summary = summary
            self.db.commit()
            self.db.refresh(project)
            return summary
        except Exception as e:
            logger.error(f"生成项目摘要失败: {e}")
            return None

    async def analyze_data_needs(
        self, 
        project_id: str, 
        question: str
    ) -> Dict[str, Any]:
        """分析用户问题需要什么数据"""
        context = self.get_context(project_id)
        if not context:
            return {"needs": [], "search_keywords": [], "reason": "项目不存在"}

        prompt = self.DATA_NEEDS_PROMPT.format(
            project_name=context.project_name,
            tech_stack=", ".join(context.tech_stack) if context.tech_stack else "未知",
            question=question,
        )

        try:
            response = await self.llm.generate(prompt)
            # 解析JSON响应
            # 尝试提取JSON部分
            response = response.strip()
            if response.startswith("```"):
                # 移除markdown代码块
                lines = response.split("\n")
                response = "\n".join(lines[1:-1] if len(lines) > 2 else lines)
            
            result = json.loads(response)
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"解析数据需求分析结果失败: {e}, 原始响应: {response}")
            # 返回默认需求
            return {
                "needs": ["readme", "summary", "code"],
                "search_keywords": [question],
                "reason": "无法解析，使用默认需求"
            }
        except Exception as e:
            logger.error(f"分析数据需求失败: {e}")
            return {
                "needs": ["readme", "summary"],
                "search_keywords": [],
                "reason": f"分析失败: {str(e)}"
            }

    def get_file_structure(self, project_id: str, max_depth: int = 3) -> Optional[str]:
        """获取项目的文件结构"""
        project = self.project_service.get_project(project_id)
        if not project or not project.local_path:
            return None

        project_path = Path(project.local_path)
        if not project_path.exists():
            return None

        # 跳过的目录
        skip_dirs = {
            ".git", ".github", "node_modules", "__pycache__", 
            ".venv", "venv", "dist", "build", ".idea", ".vscode",
            "target", "bin", "obj"
        }

        # 支持的扩展名
        supported_extensions = {
            ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go",
            ".rs", ".vue", ".md", ".json", ".yaml", ".yml", ".toml"
        }

        lines = []
        
        def walk_dir(path: Path, prefix: str = "", depth: int = 0):
            if depth > max_depth:
                return
            
            try:
                items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            except PermissionError:
                return

            for i, item in enumerate(items):
                if item.name.startswith(".") and item.name not in [".env.example"]:
                    continue
                if item.name in skip_dirs:
                    continue

                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                next_prefix = "    " if is_last else "│   "

                if item.is_dir():
                    lines.append(f"{prefix}{current_prefix}{item.name}/")
                    walk_dir(item, prefix + next_prefix, depth + 1)
                elif item.suffix in supported_extensions:
                    lines.append(f"{prefix}{current_prefix}{item.name}")

        lines.append(f"{project.name}/")
        walk_dir(project_path)

        return "\n".join(lines[:200])  # 限制行数

    def build_smart_context(
        self,
        project_id: str,
        data_needs: List[str],
        search_keywords: Optional[List[str]] = None,
        code_results: Optional[List[Dict]] = None,
    ) -> str:
        """根据数据需求构建智能上下文"""
        context = self.get_context(project_id)
        if not context:
            return "项目不存在"

        parts = []

        # 按需添加各种上下文
        if "readme" in data_needs and context.readme_content:
            parts.append("=== README 文档 ===")
            readme = context.readme_content
            if len(readme) > 8000:
                readme = readme[:8000] + "\n... (内容过长，已截断)"
            parts.append(readme)
            parts.append("")

        if "summary" in data_needs and context.project_summary:
            parts.append("=== 项目摘要 ===")
            parts.append(context.project_summary)
            parts.append("")

        if "structure" in data_needs:
            structure = self.get_file_structure(project_id)
            if structure:
                parts.append("=== 项目结构 ===")
                parts.append(structure)
                parts.append("")

        if "tech_stack" in data_needs and context.tech_stack:
            parts.append("=== 技术栈 ===")
            parts.append(", ".join(context.tech_stack))
            parts.append("")

        if "code" in data_needs and code_results:
            parts.append("=== 相关代码 ===")
            for i, result in enumerate(code_results[:5], 1):
                file_path = result.get("metadata", {}).get("file_path", "unknown")
                content = result.get("content", "")
                parts.append(f"[{i}] {file_path}")
                parts.append(f"```")
                parts.append(content[:2000])  # 限制每个代码块长度
                parts.append("```")
                parts.append("")

        # 添加基础项目信息作为前缀
        header = context.to_prompt_context()
        
        if parts:
            return f"{header}\n\n" + "\n".join(parts)
        return header
