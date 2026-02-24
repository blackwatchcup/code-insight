import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

sys.modules["chromadb"] = MagicMock()

from app.rag.chat_history import ChatHistoryManager, ChatMessage
from app.rag.citation import Citation, CitationExtractor
from app.rag.embedder import CodeChunk, CodeEmbedder, EmbeddingConfig
from app.rag.qa_service import QAResponse, QAService, QAType


class TestCodeEmbedder:
    def test_embedder_initialization(self):
        config = EmbeddingConfig(model_name="text-embedding-ada-002")
        embedder = CodeEmbedder(config)
        assert embedder.config.model_name == "text-embedding-ada-002"

    def test_embed_single_code(self):
        embedder = CodeEmbedder(EmbeddingConfig())
        code = "def hello():\n    print('hello')"
        with patch.object(embedder, "_get_embedding", return_value=[0.1] * 1536):
            embedding = embedder.embed(code)
            assert len(embedding) == 1536
            assert all(x == 0.1 for x in embedding)

    def test_embed_batch_codes(self):
        embedder = CodeEmbedder(EmbeddingConfig())
        codes = ["def func1(): pass", "def func2(): pass", "class MyClass: pass"]
        with patch.object(embedder, "_get_embedding", return_value=[0.1] * 1536):
            embeddings = embedder.embed_batch(codes)
            assert len(embeddings) == 3
            assert all(len(e) == 1536 for e in embeddings)

    def test_chunk_code(self):
        embedder = CodeEmbedder(EmbeddingConfig(chunk_size=500))
        long_code = "def func():\n    pass\n" * 100
        chunks = embedder.chunk_code(long_code)
        assert len(chunks) > 1
        for chunk in chunks:
            assert isinstance(chunk, CodeChunk)

    def test_count_tokens(self):
        embedder = CodeEmbedder(EmbeddingConfig())
        code = "def hello(): pass"
        count = embedder.count_tokens(code)
        assert count > 0


class TestChromaStore:
    def test_store_initialization(self):
        from app.rag.vector_store import VectorStoreConfig

        config = VectorStoreConfig(persist_directory="./test_chroma")
        assert config.persist_directory == "./test_chroma"

    def test_add_documents_interface(self):
        from app.rag.vector_store import VectorStoreConfig

        assert VectorStoreConfig is not None

    def test_query_interface(self):
        from app.rag.vector_store import VectorStoreConfig

        config = VectorStoreConfig()
        assert config.collection_name == "code_embeddings"


class TestSemanticRetriever:
    def test_retriever_initialization(self):
        from app.rag.retriever import SemanticRetriever

        embedder = Mock(spec=CodeEmbedder)
        store = Mock()
        retriever = SemanticRetriever(embedder, store)
        assert retriever.embedder == embedder
        assert retriever.store == store

    def test_retrieve_relevant_code(self):
        from app.rag.retriever import RetrievalResult, SemanticRetriever

        embedder = Mock(spec=CodeEmbedder)
        embedder.embed.return_value = [0.1] * 1536
        store = Mock()
        store.query.return_value = {
            "ids": [["1", "2"]],
            "documents": [["def hello(): pass", "class Test: pass"]],
            "metadatas": [[{"file": "test.py", "line": 1}, {"file": "test.py", "line": 5}]],
            "distances": [[0.1, 0.2]],
        }
        retriever = SemanticRetriever(embedder, store)
        results = retriever.retrieve("how to say hello", top_k=2)
        assert len(results) == 2
        assert all(isinstance(r, RetrievalResult) for r in results)

    def test_retrieve_with_threshold(self):
        from app.rag.retriever import SemanticRetriever

        embedder = Mock(spec=CodeEmbedder)
        embedder.embed.return_value = [0.1] * 1536
        store = Mock()
        store.query.return_value = {
            "ids": [["1", "2"]],
            "documents": [["def hello(): pass", "class Test: pass"]],
            "metadatas": [[{"file": "test.py"}, {"file": "test.py"}]],
            "distances": [[0.1, 0.9]],
        }
        retriever = SemanticRetriever(embedder, store)
        results = retriever.retrieve("query", top_k=2, threshold=0.5)
        assert len(results) == 1


class TestLLMService:
    def test_llm_initialization(self):
        from app.llm.service import LLMConfig, LLMService

        config = LLMConfig(model="gpt-4", api_key="test-key")
        service = LLMService(config)
        assert service.config.model == "gpt-4"

    @pytest.mark.asyncio
    async def test_generate_response(self):
        from app.llm.service import LLMConfig, LLMService

        service = LLMService(LLMConfig(api_key="test-key"))
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is a response"

        with patch.object(
            service._async_client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            response = await service.generate("What is this code?")
            assert response == "This is a response"


class TestQAService:
    def test_qa_service_initialization(self):
        from app.rag.qa_service import QAService

        llm = Mock()
        retriever = Mock()
        service = QAService(llm, retriever)
        assert service.llm == llm
        assert service.retriever == retriever

    @pytest.mark.asyncio
    async def test_implementation_qa(self):
        from app.rag.qa_service import QAService
        from app.rag.retriever import RetrievalResult

        llm = Mock()
        llm.generate = AsyncMock(return_value="This function prints hello")
        retriever = Mock()
        retriever.retrieve.return_value = [
            RetrievalResult(id="1", content="def hello(): print('hello')", score=0.9, metadata={})
        ]
        service = QAService(llm, retriever)
        response = await service.answer(
            "What does hello function do?", qa_type=QAType.IMPLEMENTATION
        )
        assert isinstance(response, QAResponse)
        assert response.answer == "This function prints hello"

    @pytest.mark.asyncio
    async def test_planning_qa(self):
        from app.rag.qa_service import QAService
        from app.rag.retriever import RetrievalResult

        llm = Mock()
        llm.generate = AsyncMock(return_value="To add a new feature, you need to...")
        retriever = Mock()
        retriever.retrieve.return_value = []
        service = QAService(llm, retriever)
        response = await service.answer("How to add a new feature?", qa_type=QAType.PLANNING)
        assert response.qa_type == QAType.PLANNING

    @pytest.mark.asyncio
    async def test_hybrid_qa(self):
        from app.rag.qa_service import QAService
        from app.rag.retriever import RetrievalResult

        llm = Mock()
        llm.generate = AsyncMock(return_value="Based on the code structure...")
        retriever = Mock()
        retriever.retrieve.return_value = [
            RetrievalResult(id="1", content="def func(): pass", score=0.8, metadata={})
        ]
        service = QAService(llm, retriever)
        response = await service.answer("Explain the architecture", qa_type=QAType.HYBRID)
        assert response.qa_type == QAType.HYBRID

    def test_detect_qa_type(self):
        from app.rag.qa_service import QAService

        llm = Mock()
        retriever = Mock()
        service = QAService(llm, retriever)

        impl_result = service.detect_qa_type("How is the login function implemented?")
        assert impl_result == QAType.IMPLEMENTATION

        plan_result = service.detect_qa_type("I want to create new feature")
        assert plan_result == QAType.PLANNING

        hybrid_result = service.detect_qa_type("What is this code about?")
        assert hybrid_result in [QAType.HYBRID, QAType.IMPLEMENTATION]


class TestChatHistory:
    def test_history_manager_initialization(self):
        manager = ChatHistoryManager()
        assert manager.histories == {}

    def test_add_message(self):
        manager = ChatHistoryManager()
        manager.add_message("session-1", "user", "Hello")
        manager.add_message("session-1", "assistant", "Hi there!")
        history = manager.get_history("session-1")
        assert len(history) == 2
        assert history[0].role == "user"
        assert history[1].role == "assistant"

    def test_get_history_limit(self):
        manager = ChatHistoryManager()
        for i in range(20):
            manager.add_message("session-1", "user", f"Message {i}")
        history = manager.get_history("session-1", limit=10)
        assert len(history) == 10

    def test_clear_history(self):
        manager = ChatHistoryManager()
        manager.add_message("session-1", "user", "Hello")
        manager.clear_history("session-1")
        assert len(manager.get_history("session-1")) == 0

    def test_get_context_for_llm(self):
        manager = ChatHistoryManager()
        manager.add_message("session-1", "user", "What is this?")
        manager.add_message("session-1", "assistant", "This is a test")
        context = manager.get_context_for_llm("session-1")
        assert isinstance(context, list)
        assert len(context) == 2


class TestCitationTracing:
    def test_citation_extraction(self):
        extractor = CitationExtractor()
        answer = "The `hello` function (see [file.py:10](file.py#L10)) prints hello"
        citations = extractor.extract(answer)
        assert len(citations) == 1
        assert citations[0].file == "file.py"
        assert citations[0].line == 10

    def test_citation_format(self):
        citation = Citation(file="test.py", line=5, content="def func(): pass")
        formatted = citation.to_markdown()
        assert "[test.py:5]" in formatted
        assert "test.py#L5" in formatted

    def test_citation_to_dict(self):
        citation = Citation(file="test.py", line=5, content="def func(): pass")
        d = citation.to_dict()
        assert d["file"] == "test.py"
        assert d["line"] == 5
