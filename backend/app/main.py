import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
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
from app.api.employees import router as employees_router
from app.api.sources import router as sources_router
from app.api.conflicts import router as conflicts_router
from app.api.ask_ai import router as ask_ai_router

logger = logging.getLogger("continuum.security")

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

# Security Headers Pure ASGI Middleware
SECURITY_HEADERS = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"x-xss-protection", b"1; mode=block"),
    (b"referrer-policy", b"strict-origin-when-cross-origin"),
    (b"content-security-policy", b"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' http: https:;")
]

class SecurityHeadersMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(SECURITY_HEADERS)
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)

app.add_middleware(SecurityHeadersMiddleware)

# CORS Configuration with strict origin allowlist
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_security_checks():
    settings.validate_production_security()

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception on {request.method} {request.url.path}: {exc}")
    if settings.ENVIRONMENT == "production":
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred."}
        )
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
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
app.include_router(employees_router, prefix=settings.API_V1_STR)
app.include_router(sources_router, prefix=settings.API_V1_STR)
app.include_router(conflicts_router, prefix=settings.API_V1_STR)
app.include_router(ask_ai_router, prefix=settings.API_V1_STR)

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
