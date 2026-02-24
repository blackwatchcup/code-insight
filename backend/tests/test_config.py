import os

import pytest

from app.core.config import Settings, get_settings


class TestSettings:
    def test_default_values(self):
        settings = Settings()
        assert settings.APP_NAME == "CodeInsight"
        assert settings.DEBUG is True
        assert settings.VERSION == "1.0.0"
        assert settings.API_PREFIX == "/api/v1"

    def test_database_url_default(self):
        settings = Settings()
        assert settings.DATABASE_URL == "sqlite:///./data/codeinsight.db"

    def test_storage_paths(self):
        settings = Settings()
        assert settings.DATA_DIR == "./data"
        assert settings.PROJECTS_DIR == "./data/projects"
        assert settings.CHROMA_DIR == "./data/chroma"

    def test_llm_config_defaults(self):
        settings = Settings()
        assert settings.OPENAI_API_KEY == ""
        assert settings.OPENAI_MODEL == "gpt-4"
        assert settings.CLAUDE_API_KEY == ""

    def test_embedding_config_defaults(self):
        settings = Settings()
        assert settings.EMBEDDING_MODEL == "text-embedding-3-small"
        assert settings.CHUNK_SIZE == 500
        assert settings.CHUNK_OVERLAP == 50

    def test_parser_config_defaults(self):
        settings = Settings()
        assert settings.MAX_FILE_SIZE == 10 * 1024 * 1024
        expected_extensions = [
            ".py",
            ".js",
            ".ts",
            ".tsx",
            ".jsx",
            ".java",
            ".go",
            ".rs",
            ".vue",
        ]
        assert settings.SUPPORTED_EXTENSIONS == expected_extensions

    def test_cors_config_defaults(self):
        settings = Settings()
        assert "http://localhost:3000" in settings.CORS_ORIGINS
        assert "http://localhost:5173" in settings.CORS_ORIGINS
        assert settings.CORS_ALLOW_CREDENTIALS is True

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("APP_NAME", "TestApp")
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("CHUNK_SIZE", "1000")
        settings = Settings()
        assert settings.APP_NAME == "TestApp"
        assert settings.DEBUG is False
        assert settings.CHUNK_SIZE == 1000


class TestGetSettings:
    def test_get_settings_returns_settings_instance(self):
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_caching(self):
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
