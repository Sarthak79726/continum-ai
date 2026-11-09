import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "Continuum AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    DATABASE_URL: str = "sqlite:///./continuum_ai.db"

    JWT_SECRET_KEY: str = "continuum-ai-super-secret-key-change-in-production-2025"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # AI Configuration
    AI_PROVIDER: str = "demo"  # options: demo, gemini, openai, anthropic, groq, ollama
    AI_API_KEY: str = ""
    AI_MODEL: str = "gemini-1.5-flash"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    CHROMA_PERSIST_DIRECTORY: str = "./chroma_data"
    UPLOAD_DIRECTORY: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 20 * 1024 * 1024  # 20 MB

    CORS_ORIGINS: List[str] = ["*"]

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"
    }

settings = Settings()

# Ensure required directories exist
os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)
os.makedirs(settings.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
os.makedirs("./data/sample_documents", exist_ok=True)

