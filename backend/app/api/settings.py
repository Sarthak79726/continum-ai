from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, Optional

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.models.all_models import User

router = APIRouter(prefix="/settings", tags=["Settings"])

class SettingsUpdate(BaseModel):
    ai_provider: Optional[str] = None
    ai_api_key: Optional[str] = None
    ai_model: Optional[str] = None

@router.get("/status")
def get_system_settings_status(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    has_api_key = bool(settings.AI_API_KEY and len(settings.AI_API_KEY.strip()) > 5)
    
    return {
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role
        },
        "ai_engine": {
            "provider": settings.AI_PROVIDER,
            "model": settings.AI_MODEL,
            "embedding_model": settings.EMBEDDING_MODEL,
            "is_api_key_configured": has_api_key,
            "mode": "Live AI API" if has_api_key else "SentenceTransformers / Local Engine",
            "provider_switchable": True
        },
        "storage": {
            "vector_store": "ChromaDB Persistent Store",
            "vector_dir": settings.CHROMA_PERSIST_DIRECTORY,
            "upload_dir": settings.UPLOAD_DIRECTORY,
            "database": "SQLite (SQLAlchemy with PostgreSQL Parity)"
        },
        "app_info": {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "tagline": "Every project should remember what its people know."
        }
    }

@router.put("")
def update_system_settings(
    update_in: SettingsUpdate,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only system administrators can modify platform AI settings."
        )

    if update_in.ai_provider:
        settings.AI_PROVIDER = update_in.ai_provider.lower().strip()
    if update_in.ai_api_key is not None:
        settings.AI_API_KEY = update_in.ai_api_key.strip()
    if update_in.ai_model:
        settings.AI_MODEL = update_in.ai_model.strip()

    return {
        "status": "success",
        "message": "AI Engine settings updated successfully.",
        "ai_provider": settings.AI_PROVIDER,
        "ai_model": settings.AI_MODEL,
        "is_api_key_configured": bool(settings.AI_API_KEY)
    }
