"""智能聊天服务 - 模拟OpenCode的动态数据获取流程"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional

from sqlalchemy.orm import Session

from app.llm.service import LLMService
from app.rag.retriever import SemanticRetriever
from app.rag.database_chat_history import DatabaseChatHistoryManager
from app.services.project_context_service import ProjectContextService

logger = logging.getLogger(__name__)


class SmartChatMode(str, Enum):
    """智能聊天模式"""
    SMART = "smart"  # 智能模式：动态分析需要什么数据
    FULL_CONTEXT = "full_context"  # 完整上下文模式：使用所有可用上下文
    CODE_ONLY = "code_only"  # 仅代码模式：只使用RAG检索的代码
    DOCUMENTATION = "documentation"  # 文档模式：只使用README和摘要


@dataclass
class SmartChatResponse:
    """智能聊天响应"""
    answer: str
    mode: SmartChatMode
    context_used: List[str] = field(default_factory=list)
    data_needs: Dict[str, Any] = field(default_factory=dict)
    sources: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "mode": self.mode.value,
            "context_used": self.context_used,
            "data_needs": self.data_needs,
            "sources": self.sources,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


class SmartChatService:
    """智能聊天服务 - 实现类似OpenCode的智能问答流程"""

    # 智能回答的系统提示
    SMART_SYSTEM_PROMPT = """你是一个专业的代码分析助手。你正在帮助用户理解一个代码项目。

你的回答应该：
1. 基于提供的项目上下文和代码准确回答问题
2. 如果引用代码，请注明文件路径和行号
3. 如果上下文不足以回答问题，请诚实地说明
4. 使用清晰、专业的语言
5. 适当使用代码块和列表来组织回答

请用中文回答。"""

    # 智能回答的用户提示模板
    SMART_ANSWER_PROMPT = """{context}

用户问题: {question}

请基于以上项目信息和代码上下文，准确回答用户的问题。"""

    def __init__(
        self,
        db: Session,
        llm: Optional[LLMService] = None,
        retriever: Optional[SemanticRetriever] = None,
    ):
        self.db = db
        self.llm = llm or LLMService()
        self.retriever = retriever
        self.context_service = ProjectContextService(db, self.llm)
        self.history_manager = DatabaseChatHistoryManager()

    async def smart_chat(
        self,
        question: str,
        project_id: str,
        session_id: Optional[str] = None,
        mode: SmartChatMode = SmartChatMode.SMART,
        top_k: int = 5,
    ) -> SmartChatResponse:
        """
        智能聊天主入口
        
        流程：
        1. 分析用户问题，确定需要什么数据
        2. 收集所需的数据（README、摘要、代码等）
        3. 构建智能上下文
        4. 调用LLM生成回答
        """
        # 获取或创建会话
        if session_id:
            self.history_manager.get_or_create_session(
                session_id=session_id,
                project_id=project_id,
                chat_mode="smart",
            )

        # 根据模式决定如何获取数据
        if mode == SmartChatMode.SMART:
            data_needs = await self.context_service.analyze_data_needs(
                project_id, question
            )
        elif mode == SmartChatMode.FULL_CONTEXT:
            data_needs = {
                "needs": ["readme", "summary", "code", "structure", "tech_stack"],
                "search_keywords": [question],
            }
        elif mode == SmartChatMode.CODE_ONLY:
            data_needs = {
                "needs": ["code"],
                "search_keywords": [question],
            }
        elif mode == SmartChatMode.DOCUMENTATION:
            data_needs = {
                "needs": ["readme", "summary"],
                "search_keywords": [],
            }
        else:
            data_needs = {"needs": ["readme", "summary", "code"], "search_keywords": [question]}

        # 收集代码结果（如果需要）
        code_results = []
        if "code" in data_needs.get("needs", []) and self.retriever:
            search_keywords = data_needs.get("search_keywords", [question])
            # 使用原始问题或提取的关键词进行搜索
            for keyword in search_keywords[:3]:  # 最多使用3个关键词
                results = self.retriever.retrieve(
                    keyword, top_k=top_k, project_id=project_id
                )
                for r in results:
                    if r not in code_results:
                        code_results.append(r)
            code_results = code_results[:top_k * 2]  # 限制总结果数

        # 构建上下文
        context = self.context_service.build_smart_context(
            project_id=project_id,
            data_needs=data_needs.get("needs", []),
            search_keywords=data_needs.get("search_keywords", []),
            code_results=[r.to_dict() for r in code_results] if code_results else None,
        )

        # 获取历史对话
        history = None
        if session_id:
            history = self.history_manager.get_context_for_llm(session_id)

        # 构建提示
        prompt = self.SMART_ANSWER_PROMPT.format(
            context=context,
            question=question,
        )

        # 调用LLM
        answer = await self.llm.generate(
            prompt=prompt,
            system_prompt=self.SMART_SYSTEM_PROMPT,
            history=history,
        )

        # 保存对话历史
        if session_id:
            self.history_manager.update_session_title(session_id, question)
            self.history_manager.add_message(
                session_id,
                "user",
                question,
                project_id=project_id,
                chat_mode="smart",
            )
            self.history_manager.add_message(
                session_id,
                "assistant",
                answer,
                project_id=project_id,
                chat_mode="smart",
            )

        # 计算置信度
        confidence = self._calculate_confidence(code_results, answer)

        return SmartChatResponse(
            answer=answer,
            mode=mode,
            context_used=data_needs.get("needs", []),
            data_needs=data_needs,
            sources=[r.to_dict() for r in code_results[:5]],
            confidence=confidence,
            metadata={
                "project_id": project_id,
                "session_id": session_id,
            },
        )

    async def smart_chat_stream(
        self,
        question: str,
        project_id: str,
        session_id: Optional[str] = None,
        mode: SmartChatMode = SmartChatMode.SMART,
        top_k: int = 5,
    ) -> AsyncGenerator[str, None]:
        """
        流式智能聊天
        """
        # 获取或创建会话
        if session_id:
            self.history_manager.get_or_create_session(
                session_id=session_id,
                project_id=project_id,
                chat_mode="smart",
            )

        # 分析数据需求
        if mode == SmartChatMode.SMART:
            data_needs = await self.context_service.analyze_data_needs(
                project_id, question
            )
        elif mode == SmartChatMode.FULL_CONTEXT:
            data_needs = {
                "needs": ["readme", "summary", "code", "structure", "tech_stack"],
                "search_keywords": [question],
            }
        elif mode == SmartChatMode.CODE_ONLY:
            data_needs = {
                "needs": ["code"],
                "search_keywords": [question],
            }
        else:
            data_needs = {
                "needs": ["readme", "summary", "code"],
                "search_keywords": [question],
            }

        # 收集代码结果
        code_results = []
        if "code" in data_needs.get("needs", []) and self.retriever:
            search_keywords = data_needs.get("search_keywords", [question])
            for keyword in search_keywords[:3]:
                results = self.retriever.retrieve(
                    keyword, top_k=top_k, project_id=project_id
                )
                for r in results:
                    if r not in code_results:
                        code_results.append(r)
            code_results = code_results[:top_k * 2]

        # 构建上下文
        context = self.context_service.build_smart_context(
            project_id=project_id,
            data_needs=data_needs.get("needs", []),
            code_results=[r.to_dict() for r in code_results] if code_results else None,
        )

        # 获取历史对话
        history = None
        if session_id:
            history = self.history_manager.get_context_for_llm(session_id)

        # 构建提示
        prompt = self.SMART_ANSWER_PROMPT.format(
            context=context,
            question=question,
        )

        # 流式生成
        full_answer = ""
        async for chunk in self.llm.generate_stream(
            prompt=prompt,
            system_prompt=self.SMART_SYSTEM_PROMPT,
            history=history,
        ):
            full_answer += chunk
            yield chunk

        # 保存对话历史
        if session_id:
            self.history_manager.update_session_title(session_id, question)
            self.history_manager.add_message(
                session_id,
                "user",
                question,
                project_id=project_id,
                chat_mode="smart",
            )
            self.history_manager.add_message(
                session_id,
                "assistant",
                full_answer,
                project_id=project_id,
                chat_mode="smart",
            )

    async def generate_project_summary(self, project_id: str) -> Optional[str]:
        """生成项目摘要（如果不存在）"""
        return await self.context_service.generate_project_summary(project_id)

    def _calculate_confidence(
        self, 
        code_results: List[Any], 
        answer: str
    ) -> float:
        """计算回答的置信度"""
        if not code_results:
            return 0.3  # 无代码上下文，低置信度

        # 基于检索结果数量和相似度
        avg_score = sum(r.score for r in code_results) / len(code_results)
        
        # 检查答案中是否引用了代码
        has_references = any(
            "文件" in answer or "file" in answer.lower() or "```" in answer
        )

        confidence = avg_score * 0.6
        
        if has_references:
            confidence += 0.2
        
        if len(code_results) >= 3:
            confidence += 0.1
        
        if len(code_results) >= 5:
            confidence += 0.1

        return min(confidence, 1.0)
