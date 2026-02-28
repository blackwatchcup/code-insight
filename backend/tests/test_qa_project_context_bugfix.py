"""
Property-based tests for chat project context integration bugfix.

This test file contains bug condition exploration tests that verify the expected
behavior when chat_mode="project" and project_id is provided.

**CRITICAL**: Task 1 tests are EXPECTED TO FAIL on unfixed code - failure confirms bug exists.
"""
import sys
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from hypothesis import given, strategies as st

sys.modules["chromadb"] = MagicMock()

from app.rag.database_chat_history import DatabaseChatHistoryManager
from app.rag.qa_service import QAService, QAType
from app.rag.retriever import RetrievalResult


class TestBugConditionExploration:
    """
    **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
    
    Bug Condition Exploration Tests - Property 1: Fault Condition
    
    These tests encode the EXPECTED behavior and will FAIL on unfixed code.
    Failure confirms the bug exists. After the fix is implemented, these tests
    should PASS, validating the fix.
    
    Bug Condition: chat_mode="project" AND project_id IS NOT NULL AND project_id != ""
    Expected Behavior: LLM prompt SHALL include project metadata (name, source_type, 
                       file_count, line_count, status)
    """

    @pytest.mark.asyncio
    @given(
        project_id=st.text(min_size=1, max_size=50).filter(lambda x: x.strip() != ""),
        question=st.sampled_from([
            "What is this project about?",
            "What does this project do?",
            "What technologies does this project use?",
            "How many files are in this project?",
            "What is the project structure?",
            "Explain the project architecture",
        ])
    )
    async def test_property_project_context_in_prompt(self, project_id, question):
        """
        **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
        
        Property-Based Test: For ALL inputs where chat_mode="project" and 
        project_id is not null/empty, the LLM prompt MUST include project metadata.
        
        This test uses hypothesis to generate many test cases automatically.
        
        EXPECTED TO FAIL on unfixed code - failure confirms bug exists.
        """
        # Setup mocks
        llm = Mock()
        retriever = Mock()
        db = Mock()
        
        # Mock project data
        mock_project = Mock()
        mock_project.name = "Test Project"
        mock_project.source_type = Mock(value="local")
        mock_project.file_count = 42
        mock_project.line_count = 1337
        mock_project.status = Mock(value="ready")
        mock_project.branch = "main"
        
        # Mock ProjectService
        mock_project_service = Mock()
        mock_project_service.get_project.return_value = mock_project
        
        # Capture the prompt that gets sent to LLM
        captured_prompt = None
        
        async def capture_generate(prompt, history=None):
            nonlocal captured_prompt
            captured_prompt = prompt
            return "This is a test answer"
        
        llm.generate = AsyncMock(side_effect=capture_generate)
        
        # Mock retriever to return some code context
        retriever.retrieve.return_value = [
            RetrievalResult(
                id="1",
                content="def hello(): pass",
                score=0.9,
                metadata={"file_path": "test.py", "start_line": 1}
            )
        ]
        
        # Create QA service with database session
        service = QAService(llm, retriever, db=db)
        service.project_service = mock_project_service
        
        # Execute the answer method with project mode and project_id
        response = await service.answer(
            question=question,
            project_id=project_id,
            chat_mode="project",
            qa_type=QAType.IMPLEMENTATION,
        )
        
        # Verify the response was generated
        assert response is not None
        assert captured_prompt is not None
        
        # BUG CONDITION CHECK: The prompt SHOULD contain project metadata
        # On unfixed code, this will FAIL because project context is not added
        
        # The prompt should contain a project information section
        # This is the EXPECTED behavior that is currently missing
        has_project_section = (
            "Project Information" in captured_prompt or 
            "Project:" in captured_prompt or
            "项目信息" in captured_prompt or
            "Project Name" in captured_prompt
        )
        
        assert has_project_section, (
            f"Bug confirmed for project_id='{project_id}': "
            f"No project information section found in prompt. "
            f"Expected behavior: prompt should include project metadata section. "
            f"Actual: prompt only contains code context. "
            f"Prompt preview: {captured_prompt[:200]}..."
        )

    @pytest.mark.asyncio
    async def test_concrete_bug_example_missing_project_name(self):
        """
        **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
        
        Concrete counterexample: answer() with project_id='code-insight' 
        does not include project name in prompt.
        
        This test demonstrates a specific failing case.
        EXPECTED TO FAIL on unfixed code.
        """
        # Setup mocks
        llm = Mock()
        retriever = Mock()
        db = Mock()
        
        # Mock project data
        mock_project = Mock()
        mock_project.name = "CodeInsight"
        mock_project.source_type = Mock(value="github")
        mock_project.file_count = 100
        mock_project.line_count = 5000
        mock_project.status = Mock(value="ready")
        mock_project.branch = "main"
        
        # Mock ProjectService
        mock_project_service = Mock()
        mock_project_service.get_project.return_value = mock_project
        
        # Capture the prompt
        captured_prompt = None
        
        async def capture_generate(prompt, history=None):
            nonlocal captured_prompt
            captured_prompt = prompt
            return "This is a test answer"
        
        llm.generate = AsyncMock(side_effect=capture_generate)
        
        # Mock retriever
        retriever.retrieve.return_value = [
            RetrievalResult(
                id="1",
                content="def main(): pass",
                score=0.9,
                metadata={"file_path": "main.py", "start_line": 1}
            )
        ]
        
        # Create QA service with database session
        service = QAService(llm, retriever, db=db)
        service.project_service = mock_project_service
        
        # Execute with concrete values that trigger bug condition
        response = await service.answer(
            question="What is this project about?",
            project_id="code-insight",
            chat_mode="project",
        )
        
        # Verify response exists
        assert response is not None
        assert captured_prompt is not None
        
        # BUG CHECK: The prompt should contain project metadata
        # On unfixed code, this will FAIL
        assert "Project" in captured_prompt and ("Name" in captured_prompt or "name" in captured_prompt), (
            "Bug confirmed: Project name field not found in prompt. "
            f"Counterexample: answer(project_id='code-insight', chat_mode='project') "
            f"does not include project metadata in LLM context. "
            f"Prompt was: {captured_prompt[:300]}..."
        )

    @pytest.mark.asyncio
    async def test_concrete_bug_example_missing_file_count(self):
        """
        **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
        
        Concrete counterexample: answer() with project_id='test-project' 
        does not include file_count in prompt.
        
        EXPECTED TO FAIL on unfixed code.
        """
        # Setup mocks
        llm = Mock()
        retriever = Mock()
        db = Mock()
        
        # Mock project data
        mock_project = Mock()
        mock_project.name = "Test Project"
        mock_project.source_type = Mock(value="local")
        mock_project.file_count = 75
        mock_project.line_count = 3500
        mock_project.status = Mock(value="ready")
        mock_project.branch = "develop"
        
        # Mock ProjectService
        mock_project_service = Mock()
        mock_project_service.get_project.return_value = mock_project
        
        captured_prompt = None
        
        async def capture_generate(prompt, history=None):
            nonlocal captured_prompt
            captured_prompt = prompt
            return "This is a test answer"
        
        llm.generate = AsyncMock(side_effect=capture_generate)
        
        retriever.retrieve.return_value = [
            RetrievalResult(
                id="1",
                content="class App: pass",
                score=0.85,
                metadata={"file_path": "app.py", "start_line": 1}
            )
        ]
        
        service = QAService(llm, retriever, db=db)
        service.project_service = mock_project_service
        
        # Execute with bug condition
        response = await service.answer(
            question="How many files are in this project?",
            project_id="test-project",
            chat_mode="project",
        )
        
        assert response is not None
        assert captured_prompt is not None
        
        # BUG CHECK: Should contain file count information
        has_file_count = (
            "file_count" in captured_prompt.lower() or
            "files:" in captured_prompt.lower() or
            "文件数" in captured_prompt or
            "File Count" in captured_prompt
        )
        
        assert has_file_count, (
            "Bug confirmed: file_count not found in prompt. "
            f"Counterexample: answer(project_id='test-project', "
            f"question='How many files...') does not include file statistics. "
            f"Prompt was: {captured_prompt[:300]}..."
        )

    @pytest.mark.asyncio
    async def test_concrete_bug_example_missing_source_type(self):
        """
        **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
        
        Concrete counterexample: answer() with project_id='my-app' 
        does not include source_type in prompt.
        
        EXPECTED TO FAIL on unfixed code.
        """
        # Setup mocks
        llm = Mock()
        retriever = Mock()
        db = Mock()
        
        # Mock project data
        mock_project = Mock()
        mock_project.name = "My App"
        mock_project.source_type = Mock(value="gitlab")
        mock_project.file_count = 50
        mock_project.line_count = 2000
        mock_project.status = Mock(value="ready")
        mock_project.branch = "main"
        
        # Mock ProjectService
        mock_project_service = Mock()
        mock_project_service.get_project.return_value = mock_project
        
        captured_prompt = None
        
        async def capture_generate(prompt, history=None):
            nonlocal captured_prompt
            captured_prompt = prompt
            return "This is a test answer"
        
        llm.generate = AsyncMock(side_effect=capture_generate)
        
        retriever.retrieve.return_value = [
            RetrievalResult(
                id="1",
                content="import React from 'react'",
                score=0.92,
                metadata={"file_path": "index.tsx", "start_line": 1}
            )
        ]
        
        service = QAService(llm, retriever, db=db)
        service.project_service = mock_project_service
        
        # Execute with bug condition
        response = await service.answer(
            question="What type of project is this?",
            project_id="my-app",
            chat_mode="project",
        )
        
        assert response is not None
        assert captured_prompt is not None
        
        # BUG CHECK: Should contain source type information
        has_source_type = (
            "source_type" in captured_prompt.lower() or
            "source type" in captured_prompt.lower() or
            "type:" in captured_prompt.lower() or
            "来源类型" in captured_prompt or
            "Source Type" in captured_prompt
        )
        
        assert has_source_type, (
            "Bug confirmed: source_type not found in prompt. "
            f"Counterexample: answer(project_id='my-app', "
            f"question='What type of project...') does not include source_type metadata. "
            f"Prompt was: {captured_prompt[:300]}..."
        )


class TestPreservationProperties:
    """
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

    Preservation Property Tests - Property 2: Preservation

    These tests verify that non-buggy inputs continue to work as expected
    on UNFIXED code. They establish baseline behavior that must be preserved
    after the fix is implemented.

    EXPECTED TO PASS on unfixed code - confirms baseline behavior to preserve.
    """

    @pytest.mark.asyncio
    @given(
        project_id=st.one_of(st.none(), st.just(""), st.text(min_size=1, max_size=50)),
        question=st.text(min_size=1, max_size=200)
    )
    async def test_property_freeform_mode_uses_freeform_prompt(self, project_id, question):
        """
        **Validates: Requirements 3.1**

        Property: For ALL inputs where chat_mode="freeform", the system MUST
        use FREEFORM_PROMPT and NOT perform RAG retrieval, regardless of project_id.

        This test verifies baseline behavior on unfixed code.
        EXPECTED TO PASS on unfixed code.
        """
        # Setup mocks
        llm = Mock()
        retriever = Mock()

        captured_prompt = None

        async def capture_generate(prompt, history=None):
            nonlocal captured_prompt
            captured_prompt = prompt
            return "This is a freeform answer"

        llm.generate = AsyncMock(side_effect=capture_generate)

        # Retriever should NOT be called in freeform mode
        retriever.retrieve = Mock(return_value=[])

        service = QAService(llm, retriever)

        # Execute in freeform mode
        response = await service.answer(
            question=question,
            project_id=project_id,
            chat_mode="freeform",
        )

        # Verify response exists
        assert response is not None
        assert captured_prompt is not None

        # PRESERVATION CHECK: Freeform mode must use FREEFORM_PROMPT
        # This is the baseline behavior that must be preserved
        assert "You are a helpful AI assistant" in captured_prompt, (
            f"Preservation violation: Freeform mode should use FREEFORM_PROMPT. "
            f"Prompt was: {captured_prompt[:200]}..."
        )

        # PRESERVATION CHECK: RAG retrieval should NOT occur in freeform mode
        retriever.retrieve.assert_not_called()

    @pytest.mark.asyncio
    @given(
        question=st.text(min_size=1, max_size=200)
    )
    async def test_property_project_mode_without_project_id_uses_rag(self, question):
        """
        **Validates: Requirements 3.2, 3.3**

        Property: For ALL inputs where chat_mode="project" but project_id is None,
        the system MUST perform RAG retrieval but NOT add project metadata.

        This test verifies baseline behavior on unfixed code.
        EXPECTED TO PASS on unfixed code.
        """
        # Setup mocks
        llm = Mock()
        retriever = Mock()

        captured_prompt = None

        async def capture_generate(prompt, history=None):
            nonlocal captured_prompt
            captured_prompt = prompt
            return "This is a project mode answer"

        llm.generate = AsyncMock(side_effect=capture_generate)

        # Mock retriever to return code context
        retriever.retrieve.return_value = [
            RetrievalResult(
                id="1",
                content="def example(): pass",
                score=0.85,
                metadata={"file_path": "example.py", "start_line": 1}
            )
        ]

        service = QAService(llm, retriever)

        # Execute in project mode WITHOUT project_id
        response = await service.answer(
            question=question,
            project_id=None,
            chat_mode="project",
        )

        # Verify response exists
        assert response is not None
        assert captured_prompt is not None

        # PRESERVATION CHECK: RAG retrieval should occur
        retriever.retrieve.assert_called_once()

        # PRESERVATION CHECK: Code context should be in prompt
        assert "def example(): pass" in captured_prompt or "example.py" in captured_prompt, (
            f"Preservation violation: RAG context should be in prompt. "
            f"Prompt was: {captured_prompt[:300]}..."
        )

        # PRESERVATION CHECK: Should use project mode prompts (not freeform)
        assert "You are a helpful AI assistant" not in captured_prompt, (
            "Preservation violation: Should not use FREEFORM_PROMPT in project mode"
        )

    @pytest.mark.asyncio
    async def test_concrete_freeform_mode_no_rag(self):
        """
        **Validates: Requirements 3.1**

        Concrete test: Freeform mode with project_id should NOT use RAG.

        EXPECTED TO PASS on unfixed code.
        """
        # Setup mocks
        llm = Mock()
        retriever = Mock()

        captured_prompt = None

        async def capture_generate(prompt, history=None):
            nonlocal captured_prompt
            captured_prompt = prompt
            return "Freeform answer"

        llm.generate = AsyncMock(side_effect=capture_generate)
        retriever.retrieve = Mock(return_value=[])

        service = QAService(llm, retriever)

        # Execute freeform mode even with project_id
        response = await service.answer(
            question="Hello, how are you?",
            project_id="test-project",
            chat_mode="freeform",
        )

        assert response is not None

        # PRESERVATION: Freeform mode should NOT call retriever
        retriever.retrieve.assert_not_called()

        # PRESERVATION: Should use FREEFORM_PROMPT
        assert "You are a helpful AI assistant" in captured_prompt

    @pytest.mark.asyncio
    async def test_concrete_project_mode_empty_project_id_uses_rag(self):
        """
        **Validates: Requirements 3.2, 3.3**

        Concrete test: Project mode with empty project_id should use RAG
        but not add project metadata.

        EXPECTED TO PASS on unfixed code.
        """
        # Setup mocks
        llm = Mock()
        retriever = Mock()

        captured_prompt = None

        async def capture_generate(prompt, history=None):
            nonlocal captured_prompt
            captured_prompt = prompt
            return "Project mode answer"

        llm.generate = AsyncMock(side_effect=capture_generate)

        retriever.retrieve.return_value = [
            RetrievalResult(
                id="1",
                content="class MyClass: pass",
                score=0.9,
                metadata={"file_path": "myclass.py", "start_line": 1}
            )
        ]

        service = QAService(llm, retriever)

        # Execute with empty project_id
        response = await service.answer(
            question="What is MyClass?",
            project_id="",
            chat_mode="project",
        )

        assert response is not None

        # PRESERVATION: RAG should be called
        retriever.retrieve.assert_called_once()

        # PRESERVATION: Code context should be present
        assert "class MyClass: pass" in captured_prompt or "myclass.py" in captured_prompt

    @pytest.mark.asyncio
    @given(
        question=st.text(min_size=1, max_size=200),
        chat_mode=st.sampled_from(["project", "freeform"])
    )
    async def test_property_confidence_calculation_unchanged(self, question, chat_mode):
        """
        **Validates: Requirements 3.5**

        Property: For ALL inputs, confidence calculation logic MUST remain unchanged.

        EXPECTED TO PASS on unfixed code.
        """
        # Setup mocks
        llm = Mock()
        retriever = Mock()

        async def mock_generate(prompt, history=None):
            return "Test answer with [1] citation"

        llm.generate = AsyncMock(side_effect=mock_generate)

        # Mock retriever with specific scores
        retriever.retrieve.return_value = [
            RetrievalResult(
                id="1",
                content="code1",
                score=0.8,
                metadata={"file_path": "file1.py", "start_line": 1}
            ),
            RetrievalResult(
                id="2",
                content="code2",
                score=0.9,
                metadata={"file_path": "file2.py", "start_line": 1}
            ),
        ]

        service = QAService(llm, retriever)

        # Execute
        response = await service.answer(
            question=question,
            project_id="test" if chat_mode == "project" else None,
            chat_mode=chat_mode,
        )

        # PRESERVATION: Confidence should be calculated
        assert response.confidence >= 0.0
        assert response.confidence <= 1.0

        # PRESERVATION: For project mode with sources, confidence should be > 0
        if chat_mode == "project":
            assert response.confidence > 0.0, (
                "Preservation violation: Confidence calculation changed"
            )

    @pytest.mark.asyncio
    async def test_concrete_history_management_unchanged(self):
        """
        **Validates: Requirements 3.4**

        Concrete test: Chat history management should work as before.

        EXPECTED TO PASS on unfixed code.
        """
        # Setup mocks
        llm = Mock()
        retriever = Mock()
        history_manager = Mock(spec=DatabaseChatHistoryManager)

        async def mock_generate(prompt, history=None):
            return "Answer"

        llm.generate = AsyncMock(side_effect=mock_generate)
        retriever.retrieve.return_value = []

        # Mock history manager methods
        history_manager.get_or_create_session = Mock()
        history_manager.get_context_for_llm = Mock(return_value=None)
        history_manager.add_message = Mock()
        history_manager.update_session_title = Mock()

        service = QAService(llm, retriever, history_manager=history_manager)

        # Execute with session_id
        response = await service.answer(
            question="Test question",
            project_id=None,
            chat_mode="freeform",
            session_id="test-session",
        )

        assert response is not None

        # PRESERVATION: History manager methods should be called
        history_manager.get_or_create_session.assert_called_once()
        history_manager.add_message.assert_called()
        history_manager.update_session_title.assert_called_once()

    @pytest.mark.asyncio
    async def test_concrete_citation_extraction_unchanged(self):
        """
        **Validates: Requirements 3.5**

        Concrete test: Citation extraction should work as before.

        EXPECTED TO PASS on unfixed code.
        """
        # Setup mocks
        llm = Mock()
        retriever = Mock()

        async def mock_generate(prompt, history=None):
            return "Answer with [1] and [2] citations"

        llm.generate = AsyncMock(side_effect=mock_generate)
        retriever.retrieve.return_value = [
            RetrievalResult(
                id="1",
                content="code",
                score=0.8,
                metadata={"file_path": "file.py", "start_line": 1}
            )
        ]

        service = QAService(llm, retriever)

        # Execute
        response = await service.answer(
            question="Test",
            project_id="test",
            chat_mode="project",
        )

        # PRESERVATION: Citations should be extracted
        assert response.citations is not None
        assert isinstance(response.citations, list)

