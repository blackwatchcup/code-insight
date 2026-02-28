import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional

from app.llm.service import LLMService
from app.rag.database_chat_history import DatabaseChatHistoryManager
from app.rag.citation import Citation, CitationExtractor
from app.rag.retriever import RetrievalResult, SemanticRetriever


class QAType(str, Enum):
    IMPLEMENTATION = "implementation"
    PLANNING = "planning"
    HYBRID = "hybrid"


class ChatMode(str, Enum):
    """Chat mode determines how the AI responds."""
    PROJECT = "project"  # RAG-based, uses project codebase context
    FREEFORM = "freeform"  # General chat, no project context


@dataclass
class QAResponse:
    answer: str
    qa_type: QAType
    sources: List[RetrievalResult] = field(default_factory=list)
    citations: List[Citation] = field(default_factory=list)
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "qa_type": self.qa_type.value,
            "sources": [s.to_dict() for s in self.sources],
            "citations": [c.to_dict() for c in self.citations],
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


IMPLEMENTATION_PROMPT = """You are a code analysis expert. Answer the user's question about code implementation based on the provided context.

Context from codebase:
{context}

User Question: {question}

Instructions:
1. Answer based on the provided code context
2. Include specific file references and line numbers when available
3. Explain the implementation details clearly
4. If the context is insufficient, say so honestly

Answer:"""

PLANNING_PROMPT = """You are a software architect. Help the user plan features or changes based on the existing codebase structure.

Context from codebase:
{context}

User Question: {question}

Instructions:
1. Analyze the existing code structure
2. Suggest implementation approach
3. Identify potential impacts on existing code
4. Recommend best practices
5. List files that may need modification

Answer:"""

HYBRID_PROMPT = """You are a senior developer helping to understand and plan code changes. Combine implementation details with architectural guidance.

Context from codebase:
{context}

User Question: {question}

Instructions:
1. Explain the current implementation
2. Provide architectural context
3. Suggest improvements or changes
4. Include specific code references
5. Consider maintainability and scalability

Answer:"""


PROJECT_SUMMARY_PROMPT = """You are a software architect. Analyze the provided codebase context and create a comprehensive project summary.

Context from codebase:
{context}

Instructions:
1. Provide a high-level overview of the project's purpose and main functionality
2. Identify the technology stack (languages, frameworks, libraries)
3. Describe the overall architecture and key components
4. List main features and capabilities
5. Note any important patterns or design decisions
6. Include specific file references where relevant

Project Summary:"""


FREEFORM_PROMPT = """You are a helpful AI assistant. Have a natural conversation with the user.

User Message: {question}

Instructions:
1. Respond naturally and helpfully
2. Be concise but thorough
3. If the user asks about code, provide general guidance
4. Be friendly and professional

Answer:"""


class QAService:
    IMPLEMENTATION_KEYWORDS = [
        "how is",
        "how does",
        "implement",
        "implementation",
        "function",
        "method",
        "class",
        "what does",
        "where is",
        "show me",
        "explain the code",
    ]

    PLANNING_KEYWORDS = [
        "how to add",
        "how to implement",
        "how do i",
        "create new",
        "add feature",
        "extend",
        "modify",
        "refactor",
        "best way to",
        "architecture",
    ]

    def __init__(
        self,
        llm: LLMService,
        retriever: SemanticRetriever,
        history_manager: Optional[DatabaseChatHistoryManager] = None,
        citation_extractor: Optional[CitationExtractor] = None,
    ):
        self.llm = llm
        self.retriever = retriever
        self.history_manager = history_manager or DatabaseChatHistoryManager()
        self.citation_extractor = citation_extractor or CitationExtractor()

    async def answer(
        self,
        question: str,
        qa_type: Optional[QAType] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        top_k: int = 5,
        chat_mode: str = "project",
    ) -> QAResponse:
        # Get or create session
        if session_id:
            self.history_manager.get_or_create_session(
                session_id=session_id,
                project_id=project_id,
                chat_mode=chat_mode,
            )

        # For free-form mode, skip RAG retrieval
        if chat_mode == "freeform":
            prompt = FREEFORM_PROMPT.format(context="", question=question)
            sources: List[RetrievalResult] = []
            context = ""
        else:
            if qa_type is None:
                qa_type = self.detect_qa_type(question)

            sources = self.retriever.retrieve(question, top_k=top_k, project_id=project_id)
            context = self._build_context(sources)
            prompt = self._get_prompt(qa_type, context, question)

        history = None
        if session_id:
            history = self.history_manager.get_context_for_llm(session_id)

        answer = await self.llm.generate(prompt, history=history)

        citations = self.citation_extractor.extract(answer)

        if session_id:
            # Update session title from first user message
            self.history_manager.update_session_title(session_id, question)
            
            self.history_manager.add_message(
                session_id, 
                "user", 
                question, 
                project_id=project_id,
                chat_mode=chat_mode,
            )
            sources_dict = [s.to_dict() for s in sources]
            self.history_manager.add_message(
                session_id, 
                "assistant", 
                answer, 
                project_id=project_id,
                sources=sources_dict,
                chat_mode=chat_mode,
            )

        confidence = self._calculate_confidence(sources, answer)

        return QAResponse(
            answer=answer,
            qa_type=qa_type or QAType.HYBRID,
            sources=sources,
            citations=citations,
            confidence=confidence,
        )

    async def answer_stream(
        self,
        question: str,
        qa_type: Optional[QAType] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        top_k: int = 5,
        chat_mode: str = "project",
    ) -> AsyncGenerator[str, None]:
        # Get or create session
        if session_id:
            self.history_manager.get_or_create_session(
                session_id=session_id,
                project_id=project_id,
                chat_mode=chat_mode,
            )

        # For free-form mode, skip RAG retrieval
        if chat_mode == "freeform":
            prompt = FREEFORM_PROMPT.format(context="", question=question)
            sources: List[RetrievalResult] = []
        else:
            if qa_type is None:
                qa_type = self.detect_qa_type(question)

            sources = self.retriever.retrieve(question, top_k=top_k, project_id=project_id)
            context = self._build_context(sources)
            prompt = self._get_prompt(qa_type, context, question)

        history = None
        if session_id:
            history = self.history_manager.get_context_for_llm(session_id)

        full_answer = ""
        async for chunk in self.llm.generate_stream(prompt, history=history):
            full_answer += chunk
            yield chunk

        if session_id:
            # Update session title from first user message
            self.history_manager.update_session_title(session_id, question)
            
            self.history_manager.add_message(
                session_id, 
                "user", 
                question, 
                project_id=project_id,
                chat_mode=chat_mode,
            )
            sources_dict = [s.to_dict() for s in sources]
            self.history_manager.add_message(
                session_id, 
                "assistant", 
                full_answer, 
                project_id=project_id,
                sources=sources_dict,
                chat_mode=chat_mode,
            )

    def detect_qa_type(self, question: str) -> QAType:
        question_lower = question.lower()

        impl_count = sum(1 for kw in self.IMPLEMENTATION_KEYWORDS if kw in question_lower)
        plan_count = sum(1 for kw in self.PLANNING_KEYWORDS if kw in question_lower)

        if impl_count > plan_count:
            return QAType.IMPLEMENTATION
        elif plan_count > impl_count:
            return QAType.PLANNING
        else:
            return QAType.HYBRID

    def _build_context(self, sources: List[RetrievalResult]) -> str:
        if not sources:
            return "No relevant code context found."

        context_parts = []
        for i, source in enumerate(sources, 1):
            file_info = source.metadata.get("file_path", source.metadata.get("file", "unknown"))
            line_info = source.metadata.get("start_line", source.metadata.get("line", ""))

            context_parts.append(
                f"[{i}] File: {file_info}"
                f"{f', Line: {line_info}' if line_info else ''}\n"
                f"```\n{source.content}\n```\n"
            )

        return "\n".join(context_parts)

    def _get_prompt(self, qa_type: QAType, context: str, question: str) -> str:
        prompts = {
            QAType.IMPLEMENTATION: IMPLEMENTATION_PROMPT,
            QAType.PLANNING: PLANNING_PROMPT,
            QAType.HYBRID: HYBRID_PROMPT,
        }

        template = prompts.get(qa_type, HYBRID_PROMPT)
        return template.format(context=context, question=question)

    def _calculate_confidence(self, sources: List[RetrievalResult], answer: str) -> float:
        if not sources:
            return 0.0

        avg_score = sum(s.score for s in sources) / len(sources)

        has_citations = len(self.citation_extractor.extract(answer)) > 0

        base_confidence = avg_score * 0.7

        if has_citations:
            base_confidence += 0.2

        if len(sources) >= 3:
            base_confidence += 0.1

        return min(base_confidence, 1.0)

    async def generate_project_summary(
        self,
        project_id: str,
        top_k: int = 20,
    ) -> QAResponse:
        """Generate a comprehensive summary of the project."""
        # Retrieve a broad set of code chunks from the project
        sources = self.retriever.retrieve(
            "project overview main features architecture components",
            top_k=top_k,
            project_id=project_id,
        )
        
        context = self._build_context(sources)
        prompt = PROJECT_SUMMARY_PROMPT.format(context=context)
        
        answer = await self.llm.generate(prompt)
        
        confidence = self._calculate_confidence(sources, answer)
        
        return QAResponse(
            answer=answer,
            qa_type=QAType.HYBRID,
            sources=sources,
            citations=[],
            confidence=confidence,
            metadata={"type": "project_summary", "project_id": project_id},
        )

