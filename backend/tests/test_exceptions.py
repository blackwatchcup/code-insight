import pytest

from app.core.exceptions import (
    CodeInsightException,
    ProjectNotFoundError,
    ProjectAlreadyExistsError,
    InvalidProjectSourceError,
    ParseError,
    UnsupportedLanguageError,
    LLMError,
    ValidationError,
)


class TestCodeInsightException:
    def test_base_exception(self):
        exc = CodeInsightException(message="Test error", code="TEST_ERROR")
        assert exc.message == "Test error"
        assert exc.code == "TEST_ERROR"
        assert exc.status_code == 400

    def test_exception_to_dict(self):
        exc = CodeInsightException(
            message="Test error",
            code="TEST_ERROR",
            details={"field": "test"},
        )
        d = exc.to_dict()
        assert d["message"] == "Test error"
        assert d["code"] == "TEST_ERROR"
        assert d["details"]["field"] == "test"


class TestProjectExceptions:
    def test_project_not_found(self):
        exc = ProjectNotFoundError("proj_123")
        assert exc.code == "PROJECT_NOT_FOUND"
        assert exc.status_code == 404
        assert "proj_123" in exc.message
        assert exc.details["project_id"] == "proj_123"

    def test_project_already_exists(self):
        exc = ProjectAlreadyExistsError("my-project")
        assert exc.code == "PROJECT_ALREADY_EXISTS"
        assert exc.status_code == 409
        assert exc.details["project_name"] == "my-project"


class TestParseExceptions:
    def test_parse_error(self):
        exc = ParseError("test.py", "Syntax error")
        assert exc.code == "PARSE_ERROR"
        assert exc.status_code == 400
        assert "test.py" in exc.message
        assert exc.details["file_path"] == "test.py"
        assert exc.details["reason"] == "Syntax error"

    def test_unsupported_language(self):
        exc = UnsupportedLanguageError("ruby", "test.rb")
        assert exc.code == "UNSUPPORTED_LANGUAGE"
        assert "ruby" in exc.message
        assert exc.details["language"] == "ruby"


class TestValidationExceptions:
    def test_validation_error(self):
        exc = ValidationError("name", "Cannot be empty")
        assert exc.code == "VALIDATION_ERROR"
        assert "name" in exc.message
        assert exc.details["field"] == "name"
        assert exc.details["reason"] == "Cannot be empty"


class TestLLMExceptions:
    def test_llm_error(self):
        exc = LLMError("API timeout", model="gpt-4")
        assert exc.code == "LLM_ERROR"
        assert "API timeout" in exc.message
        assert exc.details["model"] == "gpt-4"
