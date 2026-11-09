from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import engine, Base, SessionLocal
from app.core.security import get_password_hash
from app.models.all_models import User, UserRole

# Import API Routers
from app.api.auth import router as auth_router
from app.api.projects import router as projects_router
from app.api.documents import router as documents_router
from app.api.analysis import router as analysis_router
from app.api.knowledge import router as knowledge_router
from app.api.evidence import router as evidence_router
from app.api.tasks import router as tasks_router
from app.api.graph import router as graph_router
from app.api.handovers import router as handovers_router
from app.api.reviews import router as reviews_router
from app.api.team import router as team_router
from app.api.analytics import router as analytics_router
from app.api.demo import router as demo_router
from app.api.settings import router as settings_router

# Initialize DB tables and seed default admin
Base.metadata.create_all(bind=engine)

def seed_default_admin():
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.email == "demo@continuum.ai").first()
        if not admin_user:
            admin_user = User(
                name="Continuum Demo Admin",
                email="demo@continuum.ai",
                password_hash=get_password_hash("password123"),
                role=UserRole.ADMIN.value,
                is_active=True
            )
            db.add(admin_user)
            db.commit()
    finally:
        db.close()

seed_default_admin()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Intelligent Knowledge Handover & Project Continuity Platform"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routes under /api
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(projects_router, prefix=settings.API_V1_STR)
app.include_router(documents_router, prefix=settings.API_V1_STR)
app.include_router(analysis_router, prefix=settings.API_V1_STR)
app.include_router(knowledge_router, prefix=settings.API_V1_STR)
app.include_router(evidence_router, prefix=settings.API_V1_STR)
app.include_router(tasks_router, prefix=settings.API_V1_STR)
app.include_router(graph_router, prefix=settings.API_V1_STR)
app.include_router(handovers_router, prefix=settings.API_V1_STR)
app.include_router(reviews_router, prefix=settings.API_V1_STR)
app.include_router(team_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(demo_router, prefix=settings.API_V1_STR)
app.include_router(settings_router, prefix=settings.API_V1_STR)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

# Serve frontend static assets if built in container
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))
if os.path.exists(frontend_dist):
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api"):
            return {"error": "Not Found"}
        target_file = os.path.join(frontend_dist, full_path)
        if os.path.isfile(target_file):
            return FileResponse(target_file)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
