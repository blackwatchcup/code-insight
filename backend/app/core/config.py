from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "CodeInsight"
    DEBUG: bool = True
    VERSION: str = "1.0.0"

    DATABASE_URL: str = "sqlite:///./data/codeinsight.db"

    DATA_DIR: Path = Path("./data")
    PROJECTS_DIR: Path = Path("./data/projects")
    CHROMA_DIR: str = "./data/chroma"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "deepseek-chat"
    OPENAI_BASE_URL: str = "https://api.deepseek.com"
    CLAUDE_API_KEY: str = ""

    anythingllm_base_url: str = "http://localhost:3001"
    anythingllm_api_key: str = ""
    anythingllm_timeout: int = 120
    anythingllm_workspace_prefix: str = "codeinsight"
    chat_backend: str = "anythingllm"

    EMBEDDING_MODEL: str = "local"
    EMBEDDING_BASE_URL: Optional[str] = None
    EMBEDDING_USE_LOCAL: bool = True
    EMBEDDING_DIM: int = 384
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    MAX_FILE_SIZE: int = 10 * 1024 * 1024
    SUPPORTED_EXTENSIONS: list = [
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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
