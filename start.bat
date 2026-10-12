@echo off
title NE-SHIELD: AI-Powered Landslide Early Warning System (ISRO Bhuvan + GSI)
color 0B

echo ===============================================================================
echo   NE-SHIELD: REAL-TIME AI LANDSLIDE EARLY WARNING & DISASTER MONITORING
echo   North Eastern Region (Assam, Meghalaya, Sikkim, Nagaland, Arunachal, Manipur, Mizoram, Tripura)
echo ===============================================================================
echo.

REM 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Python detected.
echo [1/3] Initializing NE-SHIELD Backend & Live Telemetry Schedulers...
echo.

REM 2. Start Frontend dev server in separate background window if npm exists
where npm >nul 2>&1
if %errorlevel% equ 0 (
    if exist "frontend\package.json" (
        echo [2/3] Starting Modern React GIS Frontend in background...
        start "NE-SHIELD Frontend" /min cmd /c "cd frontend && npm run dev"
    )
)

REM 3. Open Web Browser directly to the Static GIS Command Center
echo [3/3] Opening Live Command Center in your default web browser...
start "" "http://localhost:8000/static/index.html"

echo.
echo ===============================================================================
echo   Command Center:  http://localhost:8000/static/index.html
echo   Root URL:        http://localhost:8000/
echo   Swagger API:     http://localhost:8000/docs
echo   React Frontend:  http://localhost:5173/
echo ===============================================================================
echo.
echo Starting FastAPI & ISRO Bhuvan Telemetry Ingestion...
echo (Press CTRL+C anytime to stop server)
echo.

python run_backend.py
pause
