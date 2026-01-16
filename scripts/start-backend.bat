@echo off
REM Shared Logistics Platform - Backend Startup Script
REM Starts the FastAPI backend server on port 8000

echo ============================================
echo   Shared Logistics Platform - Backend
echo ============================================
echo.

cd /d "%~dp0\.."

REM Check if virtual environment exists
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -e ".[dev]"
)

echo.
echo Starting FastAPI backend server on http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.

uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
