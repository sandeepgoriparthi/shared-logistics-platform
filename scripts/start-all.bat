@echo off
REM Shared Logistics Platform - Full Stack Startup
REM Starts both backend and frontend servers

echo ============================================
echo   Shared Logistics Platform - Full Stack
echo ============================================
echo.
echo Starting Backend (port 8000) and Frontend (port 3000)
echo.

cd /d "%~dp0"

REM Start backend in new window
start "SharedLogistics Backend" cmd /k "start-backend.bat"

REM Wait a moment for backend to initialize
timeout /t 3 /nobreak >nul

REM Start frontend in new window
start "SharedLogistics Frontend" cmd /k "start-frontend.bat"

echo.
echo ============================================
echo   Servers Starting...
echo ============================================
echo.
echo Backend API:  http://localhost:8000
echo API Docs:     http://localhost:8000/docs
echo Frontend:     http://localhost:3000
echo.
echo Close this window or press Ctrl+C to exit.
echo The backend and frontend will continue running in their windows.
echo.
pause
