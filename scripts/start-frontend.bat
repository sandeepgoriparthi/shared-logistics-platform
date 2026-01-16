@echo off
REM Shared Logistics Platform - Frontend Startup Script
REM Starts the Next.js frontend server on port 3000

echo ============================================
echo   Shared Logistics Platform - Frontend
echo ============================================
echo.

cd /d "%~dp0\..\frontend"

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing dependencies...

    REM Try pnpm first, then npm
    where pnpm >nul 2>nul
    if %errorlevel% equ 0 (
        pnpm install
    ) else (
        npm install
    )
)

echo.
echo Starting Next.js frontend on http://localhost:3000
echo.

REM Try pnpm first, then npm
where pnpm >nul 2>nul
if %errorlevel% equ 0 (
    pnpm dev
) else (
    npm run dev
)
