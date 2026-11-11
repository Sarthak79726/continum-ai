import os
import json
from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator

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

    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        """Allows CORS_ORIGINS to be configured as a JSON array string, comma-separated string, or Python list."""
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            if v.startswith("[") and v.endswith("]"):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, (list, tuple, set)):
            return [str(item).strip() for item in v if str(item).strip()]
        return v

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"
    }

    def model_post_init(self, __context):
        persistent_dir = os.environ.get("PERSISTENT_STORAGE_PATH") or os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")
        if persistent_dir:
            try:
                os.makedirs(persistent_dir, exist_ok=True)
            except Exception:
                pass
            if self.DATABASE_URL == "sqlite:///./continuum_ai.db":
                self.DATABASE_URL = f"sqlite:///{os.path.join(persistent_dir, 'continuum_ai.db').replace(os.sep, '/')}"
            if self.CHROMA_PERSIST_DIRECTORY == "./chroma_data":
                self.CHROMA_PERSIST_DIRECTORY = os.path.join(persistent_dir, "chroma_data").replace(os.sep, '/')
            if self.UPLOAD_DIRECTORY == "./uploads":
                self.UPLOAD_DIRECTORY = os.path.join(persistent_dir, "uploads").replace(os.sep, '/')

    def validate_production_security(self):
        """Enforces security standards in staging and production environments."""
        if self.ENVIRONMENT.lower() in ["production", "staging"]:
            import secrets
            import logging
            logger = logging.getLogger("continuum.security")

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

            if isinstance(self.CORS_ORIGINS, str):
                self.CORS_ORIGINS = [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

            if "*" in self.CORS_ORIGINS:
                raise RuntimeError(
                    "CRITICAL SECURITY FAILURE: Wildcard '*' CORS origin is forbidden in production mode with credentials enabled. "
                    "Specify exact allowed origins via CORS_ORIGINS environment variable."
                )

            # Automatically ensure Render and Railway domains are allowed for unified service
            render_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
            if render_host:
                render_origin = f"https://{render_host}"
                if render_origin not in self.CORS_ORIGINS:
                    self.CORS_ORIGINS.append(render_origin)

            railway_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN") or os.environ.get("RAILWAY_STATIC_URL")
            if railway_domain:
                railway_origin = railway_domain if railway_domain.startswith("http") else f"https://{railway_domain}"
                if railway_origin not in self.CORS_ORIGINS:
                    self.CORS_ORIGINS.append(railway_origin)

settings = Settings()

# Ensure required directories exist
os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)
os.makedirs(settings.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
os.makedirs("./data/sample_documents", exist_ok=True)

