import logging
import os
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

from app.core.config import settings
from app.llm.service import LLMConfig, LLMService
from app.rag.database_chat_history import DatabaseChatHistoryManager
from app.rag.embedder import CodeChunk, CodeEmbedder, EmbeddingConfig
from app.rag.qa_service import QAResponse, QAService, QAType
from app.rag.retriever import SemanticRetriever
from app.rag.vector_store import ChromaStore, VectorStoreConfig

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(
        self,
        embedding_config: Optional[EmbeddingConfig] = None,
        vector_store_config: Optional[VectorStoreConfig] = None,
        llm_config: Optional[LLMConfig] = None,
    ):
        self.embedding_config = embedding_config or EmbeddingConfig(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.EMBEDDING_BASE_URL,
            model_name=settings.EMBEDDING_MODEL,
            use_local=settings.EMBEDDING_USE_LOCAL,
            embedding_dim=settings.EMBEDDING_DIM,
        )
        self.vector_store_config = vector_store_config or VectorStoreConfig(
            persist_directory=settings.CHROMA_DIR
        )
        self.llm_config = llm_config or LLMConfig(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            model=settings.OPENAI_MODEL,
        )

        self.embedder = CodeEmbedder(self.embedding_config)
        self.vector_store = ChromaStore(self.vector_store_config)
        self.retriever = SemanticRetriever(self.embedder, self.vector_store)
        self.llm = LLMService(self.llm_config)
        self.history_manager = DatabaseChatHistoryManager()
        self.qa_service = QAService(self.llm, self.retriever, self.history_manager)

    async def index_project(
        self, project_id: str, project_path: str, file_extensions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        if file_extensions is None:
            file_extensions = [".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go"]

        indexed_files = 0
        indexed_chunks = 0
        errors = []

        try:
            self.vector_store.delete_by_project(project_id)
        except Exception as e:
            logger.warning(f"Could not delete existing project data: {e}")

        project_path = Path(project_path)
        if not project_path.exists():
            return {"success": False, "error": f"Project path does not exist: {project_path}"}

        documents = []
        for ext in file_extensions:
            for file_path in project_path.rglob(f"*{ext}"):
                try:
                    relative_path = file_path.relative_to(project_path)
                    content = file_path.read_text(encoding="utf-8", errors="ignore")

                    chunks = self.embedder.chunk_code(content, str(relative_path))

                    for chunk in chunks:
                        documents.append(
                            {
                                "id": f"{project_id}:{chunk.id}",
                                "content": chunk.content,
                                "metadata": {
                                    "project_id": project_id,
                                    "file_path": str(relative_path),
                                    "start_line": chunk.start_line,
                                    "end_line": chunk.end_line,
                                    "file_extension": ext,
                                },
                            }
                        )

                    indexed_files += 1
                    indexed_chunks += len(chunks)

                except Exception as e:
                    errors.append(f"Error processing {file_path}: {str(e)}")

        if documents:
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                batch = documents[i : i + batch_size]
                try:
                    embeddings = self.embedder.embed_batch([d["content"] for d in batch])
                    self.vector_store.add_documents(batch, embeddings)
                except Exception as e:
                    errors.append(f"Error indexing batch {i}: {str(e)}")

        return {
            "success": True,
            "project_id": project_id,
            "indexed_files": indexed_files,
            "indexed_chunks": indexed_chunks,
            "errors": errors[:10],
        }

    async def ask(
        self,
        question: str,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        qa_type: Optional[QAType] = None,
        top_k: int = 5,
        chat_mode: str = "project",
    ) -> QAResponse:
        return await self.qa_service.answer(
            question=question,
            qa_type=qa_type,
            project_id=project_id,
            session_id=session_id,
            top_k=top_k,
            chat_mode=chat_mode,
        )

    async def ask_stream(
        self,
        question: str,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        qa_type: Optional[QAType] = None,
        top_k: int = 5,
        chat_mode: str = "project",
    ) -> AsyncGenerator[str, None]:
        async for chunk in self.qa_service.answer_stream(
            question=question,
            qa_type=qa_type,
            project_id=project_id,
            session_id=session_id,
            top_k=top_k,
            chat_mode=chat_mode,
        ):
            yield chunk

    def list_sessions(
        self,
        project_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List all chat sessions."""
        return self.history_manager.list_sessions(project_id, limit, offset)

    def delete_session(self, session_id: str) -> bool:
        """Delete a chat session and all its messages."""
        return self.history_manager.delete_session(session_id)

    def search(
        self,
        query: str,
        project_id: Optional[str] = None,
        top_k: int = 5,
        threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        results = self.retriever.retrieve(
            query=query, top_k=top_k, project_id=project_id, threshold=threshold
        )
        return [r.to_dict() for r in results]

    def get_chat_history(
        self, session_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        history = self.history_manager.get_history(session_id, limit)
        return history

    def clear_chat_history(self, session_id: str) -> None:
        self.history_manager.clear_history(session_id)

    def delete_project_index(self, project_id: str) -> Dict[str, Any]:
        try:
            self.vector_store.delete_by_project(project_id)
            return {"success": True, "project_id": project_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_documents": self.vector_store.count(),
            "active_sessions": len(self.history_manager.get_session_ids()),
        }


_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
