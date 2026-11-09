from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.models.all_models import User
from app.services.sample_data.generator import load_sample_dataset, purge_sample_dataset

router = APIRouter(prefix="/demo", tags=["Demonstration Dataset"])

@router.post("/load", status_code=status.HTTP_201_CREATED)
def load_demo(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Initializes the synthetic demonstration project:
    'SMART CAMPUS MANAGEMENT SYSTEM' (Departing lead developer: Rahul)
    Loads 4 realistic documents (.pdf, .txt, .csv, .docx),
    runs vector indexing in ChromaDB, and performs structured AI reconstruction.
    """
    proj = load_sample_dataset(db, current_user)
    return {
        "status": "success",
        "message": "Sample demonstration project 'Smart Campus Management System (DEMO)' loaded successfully.",
        "project_id": proj.id,
        "project_name": proj.name
    }

@router.delete("/purge")
def purge_demo(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Removes the synthetic demonstration project and clears its vector index.
    """
    purge_sample_dataset(db, current_user)
    return {
        "status": "success",
        "message": "Demonstration dataset removed."
    }

