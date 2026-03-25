# ============================================================================
# SkillScope Unified Backend - Startup Script (PowerShell)
# Runs Login Backend + Nipuni Backend on a single port (8000)
# ============================================================================

# Elegant header
Write-Host @"

╔══════════════════════════════════════════════════════════════════════════╗
║                   SKILLSCOPE UNIFIED BACKEND                            ║
║                  Startup Script (PowerShell)                            ║
╚══════════════════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

# Check if Python is installed
try {
    $pythonVersion = python.exe --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "`nPlease install Python 3.8+ from https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "main.py")) {
    Write-Host "❌ main.py not found in current directory" -ForegroundColor Red
    Write-Host "`nPlease run this script from the project root directory:" -ForegroundColor Yellow
    Write-Host "  cd 'f:\ResearchProjrctafterPP2\Project-Integration'" -ForegroundColor Cyan
    Write-Host "  .\run_unified_backend.ps1" -ForegroundColor Cyan
    Read-Host "`nPress Enter to exit"
    exit 1
}

Write-Host "✅ Project directory verified" -ForegroundColor Green
Write-Host ""

# Install dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
python.exe -m pip install --quiet -q -r requirements.txt 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "⚠️  Some dependencies may not have installed correctly" -ForegroundColor Yellow
}

Write-Host ""

# Display startup information
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "🚀 Starting SkillScope Unified Backend..." -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Write-Host "📊 Services Running:" -ForegroundColor Cyan
Write-Host "   • Login Backend (OAuth 2.0, JWT, Admin)" -ForegroundColor White
Write-Host "   • Skill Validation Backend (Transcripts, Quizzes, Jobs)" -ForegroundColor White
Write-Host ""

Write-Host "🌐 Access Points:" -ForegroundColor Cyan
Write-Host "   • Main API: http://localhost:8000" -ForegroundColor Yellow
Write-Host "   • Swagger UI: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "   • ReDoc: http://localhost:8000/redoc" -ForegroundColor Yellow
Write-Host "   • Health Check: http://localhost:8000/health" -ForegroundColor Yellow
Write-Host ""

Write-Host "📍 Route Prefixes:" -ForegroundColor Cyan
Write-Host "   • Authentication: http://localhost:8000/auth/*" -ForegroundColor Yellow
Write-Host "   • Skills: http://localhost:8000/skill/*" -ForegroundColor Yellow
Write-Host ""

Write-Host "🛑 To stop the server: Press Ctrl+C" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Run the unified backend
python.exe main.py

# If Python exits with an error
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ Server exited with an error" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "   • Port 8000 is already in use" -ForegroundColor White
    Write-Host "   • Database connection failed" -ForegroundColor White
    Write-Host "   • Missing environment variables" -ForegroundColor White
    Write-Host ""
    Write-Host "Check .env file in:" -ForegroundColor Cyan
    Write-Host "   • f:\ResearchProjrctafterPP2\Project-Integration\.env (root)" -ForegroundColor Yellow
    Write-Host "   • f:\ResearchProjrctafterPP2\Project-Integration\login\.env" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
}
