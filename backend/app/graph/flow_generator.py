"""Flow chart generator using LLM to create Mermaid diagrams."""

from typing import Dict, List

from app.llm.service import LLMService

FLOW_PROMPT = """基于以下代码，生成一个清晰的执行流程图。

代码：
```{language}
{code}
```

要求：
1. 使用Mermaid flowchart TD语法
2. 节点使用中文描述
3. 包含关键步骤和判断分支
4. 节点ID使用简洁的字母

请直接输出Mermaid代码，不要包含```mermaid标记："""


class FlowGenerator:
    def __init__(self):
        self.llm = LLMService()

    async def generate_from_function(self, code: str, language: str = "python") -> Dict:
        """Generate a flowchart from function code."""
        prompt = FLOW_PROMPT.format(code=code, language=language)

        messages = [
            {"role": "system", "content": "你是一个专业的流程图生成专家。"},
            {"role": "user", "content": prompt},
        ]

        mermaid_code = await self.llm.generate(
            prompt=prompt, system_prompt="你是一个专业的流程图生成专家。"
        )

        # 清理输出
        mermaid_code = mermaid_code.strip()
        if mermaid_code.startswith("```"):
            mermaid_code = mermaid_code.split("\n", 1)[1]
        if mermaid_code.endswith("```"):
            mermaid_code = mermaid_code.rsplit("```", 1)[0]

        return {
            "type": "flowchart",
            "format": "mermaid",
            "content": mermaid_code,
            "nodes": self._extract_nodes(mermaid_code),
        }

    def _extract_nodes(self, mermaid_code: str) -> List[Dict]:
        """Extract node definitions from Mermaid code."""
        import re

        nodes = []

        # 提取节点定义
        pattern = r"(\w+)\[([^\]]+)\]"
        for match in re.finditer(pattern, mermaid_code):
            nodes.append({"id": match.group(1), "label": match.group(2)})

        return nodes
