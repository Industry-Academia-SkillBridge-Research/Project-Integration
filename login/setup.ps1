# Quick Start Script for Backend Setup
# This script helps set up the backend environment

Write-Host "🚀 SkillBridge Backend Setup" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found. Creating from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✅ .env file created. Please update it with your credentials." -ForegroundColor Green
    Write-Host ""
    Write-Host "Required updates in .env:" -ForegroundColor Yellow
    Write-Host "  1. DATABASE_URL - Your MySQL connection string" -ForegroundColor White
    Write-Host "  2. SECRET_KEY - Generate using: python -c 'import secrets; print(secrets.token_hex(32))'" -ForegroundColor White
    Write-Host "  3. GOOGLE_CLIENT_ID - From Google Cloud Console" -ForegroundColor White
    Write-Host "  4. GOOGLE_CLIENT_SECRET - From Google Cloud Console" -ForegroundColor White
    Write-Host ""
    Write-Host "Press Enter after updating .env file..." -ForegroundColor Cyan
    Read-Host
}

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "✅ Virtual environment created." -ForegroundColor Green
} else {
    Write-Host "✅ Virtual environment already exists." -ForegroundColor Green
}

Write-Host ""
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

Write-Host "✅ Virtual environment activated." -ForegroundColor Green
Write-Host ""

# Install dependencies
Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "  1. Make sure MySQL is running" -ForegroundColor White
Write-Host "  2. Create database: CREATE DATABASE oauth_users;" -ForegroundColor White
Write-Host "  3. Update .env with your credentials" -ForegroundColor White
Write-Host "  4. Run: python -m uvicorn app.main:app --reload" -ForegroundColor White
Write-Host ""
Write-Host "🔗 Resources:" -ForegroundColor Cyan
Write-Host "  - API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - Setup Guide: ../SETUP_GUIDE.md" -ForegroundColor White
Write-Host ""
