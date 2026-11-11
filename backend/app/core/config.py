import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "Continuum AI"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = "development"  # development, staging, production

    DATABASE_URL: str = "sqlite:///./continuum_ai.db"

    JWT_SECRET_KEY: str = "continuum-ai-super-secret-key-change-in-production-2025"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes short-lived access token
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7      # 7 days rotating refresh session
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 15
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_MINUTES: int = 15

    # AI Configuration
    AI_PROVIDER: str = "demo"  # options: demo, gemini, openai, anthropic, groq, ollama
    AI_API_KEY: str = ""
    AI_MODEL: str = "gemini-1.5-flash"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    CHROMA_PERSIST_DIRECTORY: str = "./chroma_data"
    UPLOAD_DIRECTORY: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 20 * 1024 * 1024  # 20 MB

    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"
    }

    def validate_production_security(self):
        """Enforces security standards in staging and production environments."""
        if self.ENVIRONMENT.lower() in ["production", "staging"]:
            insecure_defaults = [
                "continuum-ai-super-secret-key-change-in-production-2025",
                "secret", "changeme", "password"
            ]
            if (
                self.JWT_SECRET_KEY in insecure_defaults
                or "change-in-production" in self.JWT_SECRET_KEY.lower()
                or "change-me" in self.JWT_SECRET_KEY.lower()
                or len(self.JWT_SECRET_KEY) < 32
            ):
                raise RuntimeError(
                    "CRITICAL SECURITY FAILURE: Insecure or default JWT_SECRET_KEY detected in production. "
                    "You must provide a high-entropy secret key of at least 32 characters via environment variable."
                )

            if "*" in self.CORS_ORIGINS:
                raise RuntimeError(
                    "CRITICAL SECURITY FAILURE: Wildcard '*' CORS origin is forbidden in production mode with credentials enabled. "
                    "Specify exact allowed origins via CORS_ORIGINS environment variable."
                )

            # Automatically ensure Render domains are allowed for unified service
            render_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
            if render_host:
                render_origin = f"https://{render_host}"
                if render_origin not in self.CORS_ORIGINS:
                    self.CORS_ORIGINS.append(render_origin)

settings = Settings()

# Ensure required directories exist
os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)
os.makedirs(settings.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
os.makedirs("./data/sample_documents", exist_ok=True)

