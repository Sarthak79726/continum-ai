@echo off
echo ========================================================
echo Starting Continuum AI Platform (Backend + Frontend)
echo ========================================================

echo 1. Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "Continuum AI Backend" cmd /k "python -m uvicorn app.main:app --app-dir ./backend --reload --port 8000"

echo 2. Starting Vite React Frontend on http://localhost:5173 ...
start "Continuum AI Frontend" cmd /k "cd frontend && npm run dev"

echo ========================================================
echo Both services are launching!
echo Backend API: http://127.0.0.1:8000/docs
echo Frontend App: http://localhost:5173
echo Demo Login: demo@continuum.ai / password123
echo ========================================================
pause

