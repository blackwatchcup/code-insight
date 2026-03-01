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
from app.analysis.api_extractor import APIExtractor

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

文件结构:
{file_structure}

技术栈详情:
{tech_stack_detail}

请生成一个包含以下内容的摘要（使用中文）：
1. 项目的主要目的和功能（2-3句话）
2. 核心技术架构
3. 主要功能模块
4. 项目特点和亮点

摘要（不超过500字）:"""

    # 用于生成技术栈分析的提示词
    TECH_STACK_PROMPT = """你是一个技术栈分析专家。请根据以下项目信息分析项目使用的技术栈。

项目名称: {name}
文件结构:
{file_structure}

请分析项目使用的主要技术栈，包括：
1. 编程语言
2. 框架
3. 库和依赖
4. 工具和平台

请以JSON格式返回，格式如下：
{{
  "languages": ["Python", "TypeScript"],
  "frameworks": ["FastAPI", "React"],
  "libraries": ["SQLAlchemy", "Pydantic"],
  "tools": ["Git", "Docker"]
}}

只返回JSON，不要有其他内容:"""

    # 用于生成功能点分析的提示词
    FEATURES_PROMPT = """你是一个功能分析专家。请根据以下项目信息分析项目的主要功能点。

项目名称: {name}
技术栈: {tech_stack}
文件结构:
{file_structure}

请分析项目的主要功能点，包括：
1. 核心功能
2. API接口
3. 前后端功能
4. 其他重要功能

请以JSON格式返回，格式如下：
{{
  "core_features": ["项目管理", "代码分析"],
  "api_endpoints": ["/api/v1/projects", "/api/v1/chat/ask"],
  "frontend_features": ["项目列表", "智能聊天"],
  "backend_features": ["代码解析", "LLM集成"]
}}

只返回JSON，不要有其他内容:"""

    # 用于生成架构描述的提示词
    ARCHITECTURE_PROMPT = """你是一个专业的软件架构师。请根据以下项目信息生成一个详细的项目架构描述。

项目名称: {name}
技术栈: {tech_stack}
文件结构:
{file_structure}

README内容:
{readme}

技术栈详情:
{tech_stack_detail}

功能点分析:
{features_detail}

请生成一个包含以下内容的架构描述（使用中文，Markdown格式）：
1. 技术栈分析
2. 系统架构图（使用ASCII艺术）
3. 架构说明（各模块职责）
4. 数据流分析
5. 关键模块和组件

架构描述:"""

    # 用于生成数据流程的提示词
    DATA_FLOW_PROMPT = """你是一个专业的系统架构师。请根据以下项目信息分析项目的数据流程。

项目名称: {name}
技术栈: {tech_stack}
架构描述:
{architecture}

功能点分析:
{features_detail}

API信息:
{api_info}

请分析项目中的数据流程，包括：
1. 用户请求如何进入系统
2. 数据在各层之间的流转
3. 数据如何被处理和存储
4. 响应如何返回给用户
5. 关键的数据转换点

请使用中文，Markdown格式，包含ASCII流程图。
数据流程描述:"""

    # 用于生成关键模块分析的提示词
    KEY_MODULES_PROMPT = """你是一个专业的软件架构师。请根据以下项目信息分析项目的关键模块。

项目名称: {name}
技术栈: {tech_stack}
文件结构:
{file_structure}

功能点分析:
{features_detail}

请分析项目的关键模块，对于每个模块，包括：
1. 模块名称
2. 模块职责
3. 关键文件
4. 依赖关系
5. 重要的类或函数

请以JSON格式返回，格式如下：
{{
  "modules": [
    {{
      "name": "API层",
      "responsibility": "处理HTTP请求和响应",
      "key_files": ["app/api/projects.py", "app/api/chat.py"],
      "dependencies": ["服务层", "数据库"],
      "key_components": ["ProjectRouter", "ChatRouter"]
    }}
  ]
}}

只返回JSON，不要有其他内容:"""

    # 用于生成API描述的提示词
    API_DESCRIPTION_PROMPT = """你是一个API文档专家。请根据以下提取的API信息，生成更详细的API描述。

项目名称: {name}
技术栈: {tech_stack}
提取的API列表:
{extracted_apis}

请为每个API生成更详细的描述，包括：
1. API的用途和功能
2. 请求参数说明
3. 响应格式说明
4. 使用示例（如果适用）

请以JSON格式返回，格式如下：
{{
  "apis": [
    {{
      "method": "GET",
      "path": "/api/projects",
      "description": "获取项目列表",
      "purpose": "获取所有项目的分页列表",
      "params": [
        {{"name": "page", "type": "int", "description": "页码"}}
      ],
      "response": {{"type": "Project[]", "description": "项目列表"}}
    }}
  ],
  "api_groups": {{
    "项目管理": ["/api/projects", "/api/projects/{{id}}"],
    "聊天功能": ["/api/chat/ask"]
  }}
}}

只返回JSON，不要有其他内容:"""

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
        # 延迟导入以避免循环导入
        from app.services.project_service import ProjectService
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

    async def analyze_tech_stack(self, project_id: str) -> Dict[str, List[str]]:
        """分析项目技术栈"""
        project = self.project_service.get_project(project_id)
        if not project:
            return {}

        file_structure = self.get_file_structure(project_id)
        if not file_structure:
            return {}

        prompt = self.TECH_STACK_PROMPT.format(
            name=project.name,
            file_structure=file_structure
        )

        try:
            response = await self.llm.generate(prompt)
            # 解析JSON响应
            tech_stack_data = self._parse_json_response(response)
            return tech_stack_data
        except Exception as e:
            logger.error(f"分析技术栈失败: {e}")
            return {}

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """解析LLM返回的JSON响应，支持多种格式"""
        response = response.strip()
        
        # 移除可能的markdown代码块
        if response.startswith("```"):
            lines = response.split("\n")
            # 移除第一行(```json或```)和最后一行(```)
            if len(lines) > 2:
                response = "\n".join(lines[1:-1])
            elif len(lines) == 2:
                response = lines[1]
        
        # 尝试找到JSON对象的开始和结束
        start_idx = response.find("{")
        end_idx = response.rfind("}")
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = response[start_idx:end_idx + 1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # 如果还是失败，尝试直接解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning(f"无法解析JSON响应: {response[:200]}...")
            return {}

    async def analyze_features(self, project_id: str) -> Dict[str, List[str]]:
        """分析项目功能点"""
        project = self.project_service.get_project(project_id)
        if not project:
            return {}

        file_structure = self.get_file_structure(project_id)
        if not file_structure:
            return {}

        tech_stack = []
        if project.tech_stack:
            try:
                tech_stack = json.loads(project.tech_stack)
            except (json.JSONDecodeError, TypeError):
                pass

        prompt = self.FEATURES_PROMPT.format(
            name=project.name,
            tech_stack=", ".join(tech_stack) if tech_stack else "未知",
            file_structure=file_structure
        )

        try:
            response = await self.llm.generate(prompt)
            # 解析JSON响应
            features_data = self._parse_json_response(response)
            return features_data
        except Exception as e:
            logger.error(f"分析功能点失败: {e}")
            return {}

    async def generate_architecture(self, project_id: str) -> Optional[str]:
        """使用LLM生成项目架构描述"""
        project = self.project_service.get_project(project_id)
        if not project:
            logger.error(f"项目不存在: {project_id}")
            return None

        logger.info(f"开始为项目 {project.name} 生成架构描述...")

        # 分析技术栈
        logger.info("正在分析技术栈...")
        tech_stack_data = await self.analyze_tech_stack(project_id)
        logger.info(f"技术栈分析结果: {bool(tech_stack_data)}")
        
        # 分析功能点
        logger.info("正在分析功能点...")
        features_data = await self.analyze_features(project_id)
        logger.info(f"功能点分析结果: {bool(features_data)}")

        # 准备数据
        tech_stack = []
        if project.tech_stack:
            try:
                tech_stack = json.loads(project.tech_stack)
            except (json.JSONDecodeError, TypeError):
                pass

        file_structure = self.get_file_structure(project_id)
        tech_stack_detail = json.dumps(tech_stack_data, ensure_ascii=False, indent=2)
        features_detail = json.dumps(features_data, ensure_ascii=False, indent=2)

        logger.info(f"准备生成架构描述 - 技术栈: {len(tech_stack)}项, 文件结构: {bool(file_structure)}")

        prompt = self.ARCHITECTURE_PROMPT.format(
            name=project.name,
            tech_stack=", ".join(tech_stack) if tech_stack else "未知",
            file_count=project.file_count,
            line_count=project.line_count,
            readme=project.readme_content or "（无README文件）",
            file_structure=file_structure or "（无法获取文件结构）",
            tech_stack_detail=tech_stack_detail,
            features_detail=features_detail
        )

        logger.info(f"架构描述提示词长度: {len(prompt)} 字符")

        try:
            logger.info("正在调用 LLM 生成架构描述...")
            architecture = await self.llm.generate(prompt)
            if architecture:
                logger.info(f"架构描述生成成功，长度: {len(architecture)} 字符")
                return architecture
            else:
                logger.warning("LLM 返回了空的架构描述")
                return None
        except Exception as e:
            logger.error(f"生成架构描述失败: {e}", exc_info=True)
            return None

    async def generate_project_summary(self, project_id: str) -> Optional[str]:
        """使用LLM生成项目摘要"""
        project = self.project_service.get_project(project_id)
        if not project:
            return None

        # 分析技术栈
        tech_stack_data = await self.analyze_tech_stack(project_id)
        # 保存技术栈到数据库
        if tech_stack_data:
            all_tech = []
            for key, value in tech_stack_data.items():
                all_tech.extend(value)
            project.tech_stack = json.dumps(all_tech)

        # 分析功能点
        features_data = await self.analyze_features(project_id)

        # 生成架构描述
        architecture = await self.generate_architecture(project_id)
        if architecture:
            # 尝试设置architecture字段，处理字段不存在的情况
            try:
                project.architecture = architecture
                # 保存架构描述到数据库
                self.db.commit()
                self.db.refresh(project)
            except AttributeError:
                # 数据库表中可能还没有architecture字段
                pass
            except Exception as e:
                logger.error(f"保存架构描述失败: {e}")

        # 准备数据
        tech_stack = []
        if project.tech_stack:
            try:
                tech_stack = json.loads(project.tech_stack)
            except (json.JSONDecodeError, TypeError):
                pass

        file_structure = self.get_file_structure(project_id)
        tech_stack_detail = json.dumps(tech_stack_data, ensure_ascii=False, indent=2)

        prompt = self.SUMMARY_PROMPT.format(
            name=project.name,
            tech_stack=", ".join(tech_stack) if tech_stack else "未知",
            file_count=project.file_count,
            line_count=project.line_count,
            readme=project.readme_content or "（无README文件）",
            file_structure=file_structure or "（无法获取文件结构）",
            tech_stack_detail=tech_stack_detail
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

    def extract_apis_from_code(self, project_id: str) -> List[Dict[str, Any]]:
        """从代码文件中提取API信息"""
        project = self.project_service.get_project(project_id)
        if not project or not project.local_path:
            return []

        project_path = Path(project.local_path)
        if not project_path.exists():
            return []

        extractor = APIExtractor()
        all_endpoints = []

        # 支持的API文件路径
        api_dirs = ["api", "routes", "routers", "controllers", "src/api", "app/api"]
        api_patterns = ["*api*.py", "*route*.py", "*router*.py", "*controller*.py",
                        "*api*.js", "*route*.js", "*router*.js", "*controller*.js",
                        "*api*.ts", "*route*.ts", "*router*.ts", "*controller*.ts"]

        # 搜索API文件
        api_files = []
        for api_dir in api_dirs:
            dir_path = project_path / api_dir
            if dir_path.exists():
                for pattern in api_patterns:
                    api_files.extend(dir_path.rglob(pattern))

        # 也搜索根目录下的API文件
        for pattern in api_patterns:
            api_files.extend(project_path.glob(pattern))

        # 去重
        api_files = list(set(api_files))

        # 提取API
        for file_path in api_files[:50]:  # 限制文件数量
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                if len(content) > 100000:  # 跳过过大的文件
                    continue
                
                relative_path = str(file_path.relative_to(project_path))
                endpoints = extractor.extract(content, relative_path)
                
                for endpoint in endpoints:
                    all_endpoints.append(endpoint.to_dict())
            except Exception as e:
                logger.warning(f"提取API失败 {file_path}: {e}")

        return all_endpoints

    async def generate_data_flow(self, project_id: str) -> Optional[str]:
        """生成数据流程描述"""
        project = self.project_service.get_project(project_id)
        if not project:
            return None

        # 获取架构描述
        architecture = getattr(project, 'architecture', None) or ""
        
        # 获取功能点
        features_detail = getattr(project, 'features_detail', None) or "{}"
        
        # 获取API信息
        api_info = getattr(project, 'api_info', None) or "{}"

        tech_stack = []
        if project.tech_stack:
            try:
                tech_stack = json.loads(project.tech_stack)
            except (json.JSONDecodeError, TypeError):
                pass

        prompt = self.DATA_FLOW_PROMPT.format(
            name=project.name,
            tech_stack=", ".join(tech_stack) if tech_stack else "未知",
            architecture=architecture or "（无架构描述）",
            features_detail=features_detail,
            api_info=api_info
        )

        try:
            data_flow = await self.llm.generate(prompt)
            return data_flow
        except Exception as e:
            logger.error(f"生成数据流程失败: {e}")
            return None

    async def analyze_key_modules(self, project_id: str) -> Dict[str, Any]:
        """分析关键模块"""
        project = self.project_service.get_project(project_id)
        if not project:
            return {}

        file_structure = self.get_file_structure(project_id, max_depth=4)
        if not file_structure:
            return {}

        tech_stack = []
        if project.tech_stack:
            try:
                tech_stack = json.loads(project.tech_stack)
            except (json.JSONDecodeError, TypeError):
                pass

        features_detail = getattr(project, 'features_detail', None) or "{}"

        prompt = self.KEY_MODULES_PROMPT.format(
            name=project.name,
            tech_stack=", ".join(tech_stack) if tech_stack else "未知",
            file_structure=file_structure,
            features_detail=features_detail
        )

        try:
            response = await self.llm.generate(prompt)
            modules_data = self._parse_json_response(response)
            return modules_data
        except Exception as e:
            logger.error(f"分析关键模块失败: {e}")
            return {}

    async def generate_api_description(
        self, 
        project_id: str, 
        extracted_apis: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """生成API描述"""
        project = self.project_service.get_project(project_id)
        if not project:
            return {}

        if not extracted_apis:
            return {"apis": [], "api_groups": {}}

        tech_stack = []
        if project.tech_stack:
            try:
                tech_stack = json.loads(project.tech_stack)
            except (json.JSONDecodeError, TypeError):
                pass

        # 限制API数量，避免提示词过长
        apis_to_describe = extracted_apis[:30]
        extracted_apis_json = json.dumps(apis_to_describe, ensure_ascii=False, indent=2)

        prompt = self.API_DESCRIPTION_PROMPT.format(
            name=project.name,
            tech_stack=", ".join(tech_stack) if tech_stack else "未知",
            extracted_apis=extracted_apis_json
        )

        try:
            response = await self.llm.generate(prompt)
            api_data = self._parse_json_response(response)
            return api_data
        except Exception as e:
            logger.error(f"生成API描述失败: {e}")
            # 返回提取的原始API信息
            return {
                "apis": extracted_apis,
                "api_groups": {}
            }

    async def generate_project_analysis(self, project_id: str) -> Dict[str, Any]:
        """生成完整的项目分析 - 整合所有分析步骤
        
        这是主要的分析方法，在项目导入或重新索引时调用。
        它会生成：
        1. 技术栈分析
        2. 功能点分析
        3. 架构描述
        4. 项目摘要
        5. 数据流程
        6. 关键模块
        7. API信息
        
        Args:
            project_id: 项目ID
            
        Returns:
            包含所有分析结果的字典
        """
        project = self.project_service.get_project(project_id)
        if not project:
            logger.error(f"项目不存在: {project_id}")
            return {"error": "项目不存在"}

        logger.info(f"开始分析项目: {project.name} ({project_id})")
        results = {
            "project_id": project_id,
            "project_name": project.name,
        }

        # 1. 分析技术栈
        logger.info("正在分析技术栈...")
        tech_stack_data = {}
        try:
            tech_stack_data = await self.analyze_tech_stack(project_id)
        except Exception as e:
            logger.warning(f"技术栈分析失败: {e}")
            tech_stack_data = {}
        
        if tech_stack_data and isinstance(tech_stack_data, dict):
            all_tech = []
            for key, value in tech_stack_data.items():
                if isinstance(value, list):
                    all_tech.extend(value)
            if all_tech:
                project.tech_stack = json.dumps(all_tech, ensure_ascii=False)
                results["tech_stack"] = all_tech
                logger.info(f"技术栈分析完成: {len(all_tech)} 项技术")

        # 2. 分析功能点
        logger.info("正在分析功能点...")
        features_data = {}
        try:
            features_data = await self.analyze_features(project_id)
        except Exception as e:
            logger.warning(f"功能点分析失败: {e}")
            features_data = {}
        
        if features_data and isinstance(features_data, dict):
            features_json = json.dumps(features_data, ensure_ascii=False, indent=2)
            results["features"] = features_data
            try:
                project.features_detail = features_json
            except Exception:
                logger.warning("无法保存 features_detail 字段，可能数据库表需要更新")
            logger.info("功能点分析完成")

        # 3. 生成架构描述
        logger.info("正在生成架构描述...")
        architecture = None
        try:
            architecture = await self.generate_architecture(project_id)
            logger.info(f"架构描述生成结果: {bool(architecture)}")
        except Exception as e:
            logger.warning(f"架构描述生成失败: {e}", exc_info=True)
            architecture = None
        
        if architecture:
            results["architecture"] = architecture
            logger.info(f"准备保存架构描述，长度: {len(architecture)} 字符")
            try:
                project.architecture = architecture
                logger.info("架构描述已设置到 project 对象")
            except Exception as e:
                logger.warning(f"无法保存 architecture 字段: {e}")
            logger.info("架构描述处理完成")
        else:
            logger.warning("架构描述为空，跳过保存")

        # 4. 生成项目摘要
        logger.info("正在生成项目摘要...")
        tech_stack = []
        if project.tech_stack:
            try:
                tech_stack = json.loads(project.tech_stack)
            except (json.JSONDecodeError, TypeError):
                pass

        file_structure = self.get_file_structure(project_id)
        tech_stack_detail = json.dumps(tech_stack_data, ensure_ascii=False, indent=2)

        prompt = self.SUMMARY_PROMPT.format(
            name=project.name,
            tech_stack=", ".join(tech_stack) if tech_stack else "未知",
            file_count=project.file_count,
            line_count=project.line_count,
            readme=project.readme_content or "（无README文件）",
            file_structure=file_structure or "（无法获取文件结构）",
            tech_stack_detail=tech_stack_detail
        )

        try:
            summary = await self.llm.generate(prompt)
            project.project_summary = summary
            results["project_summary"] = summary
            logger.info("项目摘要生成完成")
        except Exception as e:
            logger.error(f"生成项目摘要失败: {e}")

        # 5. 提取API信息
        logger.info("正在提取API信息...")
        extracted_apis = self.extract_apis_from_code(project_id)
        if extracted_apis:
            logger.info(f"从代码中提取到 {len(extracted_apis)} 个API")
            
            # 生成API描述
            api_description = await self.generate_api_description(project_id, extracted_apis)
            api_info_json = json.dumps(api_description, ensure_ascii=False, indent=2)
            results["api_info"] = api_description
            try:
                project.api_info = api_info_json
            except Exception:
                logger.warning("无法保存 api_info 字段，可能数据库表需要更新")
            logger.info("API信息生成完成")

        # 6. 分析关键模块
        logger.info("正在分析关键模块...")
        modules_data = await self.analyze_key_modules(project_id)
        if modules_data:
            modules_json = json.dumps(modules_data, ensure_ascii=False, indent=2)
            results["key_modules"] = modules_data
            try:
                project.key_modules = modules_json
            except Exception:
                logger.warning("无法保存 key_modules 字段，可能数据库表需要更新")
            logger.info("关键模块分析完成")

        # 7. 生成数据流程
        logger.info("正在生成数据流程...")
        data_flow = await self.generate_data_flow(project_id)
        if data_flow:
            results["data_flow"] = data_flow
            try:
                project.data_flow = data_flow
            except Exception:
                logger.warning("无法保存 data_flow 字段，可能数据库表需要更新")
            logger.info("数据流程生成完成")

        # 保存所有更改
        try:
            self.db.commit()
            self.db.refresh(project)
            logger.info(f"项目分析完成并保存: {project.name}")
        except Exception as e:
            logger.error(f"保存项目分析结果失败: {e}")
            # 尝试只保存基本字段
            try:
                self.db.rollback()
                # 重新尝试只保存基本字段
                project.tech_stack = results.get("tech_stack", [])
                project.project_summary = results.get("project_summary", "")
                self.db.commit()
                logger.info(f"项目基本分析结果已保存: {project.name}")
            except Exception as e2:
                logger.error(f"保存项目基本分析结果也失败: {e2}")
                self.db.rollback()

        return results
