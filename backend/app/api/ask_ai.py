from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.models.all_models import User
from app.schemas.all_schemas import AskProjectAIRequest, AskProjectAIResponse
from app.services.ai_engine.ask_project_ai import ask_ai_service

router = APIRouter(prefix="/ai", tags=["Ask Your Project AI"])

@router.post("/ask", response_model=AskProjectAIResponse)
def ask_project_ai(
    req: AskProjectAIRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Project-aware conversational assistant answering incoming developer continuity
    questions grounded in project documents, commits, PRs, APIs, and decisions.
    """
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    res = ask_ai_service.answer_question(
        project_id=req.project_id,
        question=req.question,
        role_scope=req.role_scope or "BACKEND",
        employee_id=req.employee_id,
        db=db
    )
    return res

