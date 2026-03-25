@echo off
REM ============================================================================
REM SkillScope Unified Backend - Startup Script
REM Runs Login Backend + Nipuni Backend on a single port (8000)
REM ============================================================================

echo.
echo ╔══════════════════════════════════════════════════════════════════════════╗
echo ║                   SKILLSCOPE UNIFIED BACKEND                            ║
echo ║                    Startup Script (Windows Batch)                       ║
echo ╚══════════════════════════════════════════════════════════════════════════╝
echo.

REM Check if Python is installed
python.exe --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo ✅ Python found
python.exe --version
echo.

REM Check if we're in the right directory
if not exist "main.py" (
    echo ❌ main.py not found in current directory
    echo.
    echo Please run this script from the project root directory:
    echo   cd f:\ResearchProjrctafterPP2\Project-Integration
    echo   run_unified_backend.bat
    pause
    exit /b 1
)

echo ✅ Project directory verified
echo.

REM Install dependencies
echo 📦 Installing dependencies...
python.exe -m pip install --quiet -r requirements.txt
if errorlevel 1 (
    echo ⚠️ Warning: Some dependencies may not have installed correctly
) else (
    echo ✅ Dependencies installed successfully
)
echo.

REM Display startup information
echo ═══════════════════════════════════════════════════════════════════════════
echo 🚀 Starting SkillScope Unified Backend...
echo ═══════════════════════════════════════════════════════════════════════════
echo.
echo 📊 Services Running:
echo   • Login Backend (OAuth 2.0, JWT, Admin)
echo   • Skill Validation Backend (Transcripts, Quizzes, Jobs)
echo.
echo 🌐 Access Points:
echo   • Main API: http://localhost:8000
echo   • Swagger UI: http://localhost:8000/docs
echo   • ReDoc: http://localhost:8000/redoc
echo   • Health Check: http://localhost:8000/health
echo.
echo 📍 Route Prefixes:
echo   • Authentication: http://localhost:8000/auth/*
echo   • Skills: http://localhost:8000/skill/*
echo.
echo 🛑 To stop the server: Press Ctrl+C
echo ═══════════════════════════════════════════════════════════════════════════
echo.

REM Run the unified backend
python.exe main.py

REM If Python exits with an error
if errorlevel 1 (
    echo.
    echo ❌ Server exited with an error
    echo.
    echo Common issues:
    echo   • Port 8000 is already in use
    echo   • Database connection failed
    echo   • Missing environment variables
    echo.
    echo Check .env file in:
    echo   • f:\ResearchProjrctafterPP2\Project-Integration\.env (root)
    echo   • f:\ResearchProjrctafterPP2\Project-Integration\login\.env
    echo.
    pause
)
