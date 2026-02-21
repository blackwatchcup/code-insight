from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

class Settings(BaseSettings):
    APP_NAME: str = "CodeInsight"
    DEBUG: bool = True
    VERSION: str = "1.0.0"
    
    DATABASE_URL: str = "sqlite:///./data/codeinsight.db"
    
    DATA_DIR: Path = Path("./data")
    PROJECTS_DIR: Path = Path("./data/projects")
    CHROMA_DIR: str = "./data/chroma"
    
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"
    CLAUDE_API_KEY: str = ""
    
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    
    MAX_FILE_SIZE: int = 10 * 1024 * 1024
    SUPPORTED_EXTENSIONS: list = [
        ".py", ".js", ".ts", ".tsx", ".jsx",
        ".java", ".go", ".rs", ".vue"
    ]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
