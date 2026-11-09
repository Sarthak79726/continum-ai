Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Starting Continuum AI Platform (Backend + Frontend)" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# Start Backend
Write-Host "Starting FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m uvicorn app.main:app --app-dir ./backend --reload --port 8000"

# Start Frontend
Write-Host "Starting React Frontend on http://localhost:5173..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location frontend; npm run dev"

Write-Host "Both services are launching in separate windows." -ForegroundColor Yellow
Write-Host "Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "Backend API: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "Credentials: demo@continuum.ai / password123" -ForegroundColor Cyan

