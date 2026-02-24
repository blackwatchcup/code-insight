"""README documentation generator using LLM."""

from typing import Dict

from app.llm.service import LLMService

README_PROMPT = """基于以下项目信息，生成一个专业的README.md文档。

项目名称: {name}
技术栈: {tech_stack}
主要功能: {features}
项目结构: {structure}

要求：
1. 包含项目简介
2. 技术栈说明
3. 快速开始指南
4. 项目结构说明
5. 主要功能列表
6. 使用Markdown格式

请直接输出README内容："""


class ReadmeGenerator:
    """Generate README documentation using LLM."""

    def __init__(self):
        self.llm = LLMService()

    async def generate(self, project_info: Dict) -> str:
        """Generate README from project information."""
        prompt = README_PROMPT.format(
            name=project_info.get("name", "Project"),
            tech_stack=", ".join(project_info.get("tech_stack", [])),
            features="\n".join([f"- {f}" for f in project_info.get("features", [])]),
            structure=project_info.get("structure", ""),
        )

        return await self.llm.generate(
            prompt=prompt, system_prompt="你是一个专业的技术文档撰写专家。"
        )
