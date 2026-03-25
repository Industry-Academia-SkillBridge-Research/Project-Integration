# 🚀 SkillScope Unified Backend - Setup & Usage Guide

## Overview

The **Unified Backend** combines both the Login Backend and Nipuni Backend into a single FastAPI application running on port **8000**.

Instead of running two separate servers:
```bash
❌ BEFORE (Annoying - 2 commands)
terminal1> cd login && python -m uvicorn app.main:app --reload --port 8182
terminal2> cd Nipuni_backend/src && python -m uvicorn app.main:app --reload --port 8000
```

Now you run ONE command:
```bash
✅ AFTER (Simple - 1 command)
python main.py
# OR
.\run_unified_backend.ps1
```

---

## 📋 Quick Start

### Step 1: Prerequisites
- **Python 3.8+** installed and in PATH
- **MySQL** running locally (port 3306)
- Environment variables configured (`.env` file in root)

### Step 2: Run Unified Backend

#### Option A: PowerShell (Recommended for Windows)
```powershell
cd f:\ResearchProjrctafterPP2\Project-Integration
.\run_unified_backend.ps1
```

#### Option B: Batch Script (Windows CMD)
```batch
cd f:\ResearchProjrctafterPP2\Project-Integration
run_unified_backend.bat
```

#### Option C: Python Direct
```bash
cd f:\ResearchProjrctafterPP2\Project-Integration
python main.py
```

### Step 3: Access the API

| Resource | URL |
|----------|-----|
| **Main API** | http://localhost:8000 |
| **Swagger Docs** | http://localhost:8000/docs |
| **ReDoc** | http://localhost:8000/redoc |
| **Health Check** | http://localhost:8000/health |

---

## 🗂️ Architecture

The unified backend combines routes from both services with proper prefixing:

```
┌─────────────────────────────────────────────────────────────┐
│         SkillScope Unified Backend (Port 8000)              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  LOGIN BACKEND ROUTES (/auth/*)                             │
│  ├── /auth/login/google          - Google OAuth login       │
│  ├── /auth/google/callback       - OAuth callback           │
│  ├── /auth/me                    - Get current user         │
│  ├── /auth/logout                - Logout                   │
│  ├── /auth/health                - Auth health check        │
│  ├── /admin/*                    - Admin management         │
│  └── /candidate/*                - Candidate data           │
│                                                              │
│  SKILL VALIDATION ROUTES (/skill/*)                         │
│  ├── /skill/transcript/*         - Upload & parse transcripts
│  ├── /skill/skills/*             - Skill management         │
│  ├── /skill/quiz/*               - Quiz generation & scoring
│  ├── /skill/jobs/*               - Job recommendations      │
│  ├── /skill/profile/*            - Student profile          │
│  ├── /skill/admin/*              - Admin functions          │
│  └── /skill/xai/*                - Explainable AI           │
│                                                              │
│  HEALTH & STATUS                                            │
│  ├── /                           - API info                 │
│  └── /health                     - Unified health check     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Configuration

### Environment Variables (.env)

The unified backend reads from the root `.env` file:

```env
# Database Configuration
DATABASE_URL=mysql+pymysql://root:root@localhost:3306/oauth_users

# JWT Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Google OAuth
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret

# URLs
FRONTEND_URL=http://localhost:8080
BACKEND_URL=http://localhost:8000

# Environment
ENVIRONMENT=development
```

### MySQL Setup

The unified backend automatically:
1. ✅ Creates all tables for Login Backend
2. ✅ Creates all tables for Nipuni Backend
3. ✅ Initializes storage directories

**No manual migration needed!**

---

## 📊 API Endpoints

### Authentication (From Login Backend)

```bash
# Login with Google
GET /auth/login/google

# Get current user
GET /auth/me
Headers: Authorization: Bearer <token>

# Logout
GET /auth/logout

# Admin endpoints
POST /admin/create-admin
GET /admin/users
PUT /admin/users/{user_id}
DELETE /admin/users/{user_id}

# Candidate data
POST /candidate/upload-cv
GET /candidate/me
PUT /candidate/{candidate_id}/analysis
```

### Skills & Transcripts (From Nipuni Backend)

```bash
# Upload transcript
POST /skill/transcript/upload
Content-Type: multipart/form-data

# Get claimed skills
GET /skill/skills/claimed?student_id=123

# Generate quiz
POST /skill/quiz/generate
{
    "skills": ["Python", "SQL"],
    "difficulty": "intermediate"
}

# Job recommendations
GET /skill/jobs/recommendations?student_id=123

# User profile
GET /skill/profile/{student_id}

# XAI explanations
POST /skill/xai/explain
{
    "prediction": {...},
    "model": "neural_network"
}
```

---

## 🔍 Testing the APIs

### Using Swagger UI
1. Open http://localhost:8000/docs
2. Endpoints are grouped by Authentication and Skill Validation
3. Click "Try it out" to test any endpoint

### Using cURL

```bash
# Health check
curl http://localhost:8000/health

# Get API info
curl http://localhost:8000/

# Swagger JSON schema
curl http://localhost:8000/openapi.json
```

### Using Python

```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# Get API info
response = requests.get("http://localhost:8000/")
print(response.json())
```

---

## 🛠️ Troubleshooting

### Issue: Port 8000 already in use

```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (Windows)
taskkill /PID <PID> /F

# Or use a different port (edit main.py)
```

### Issue: Database connection failed

```bash
# Check MySQL is running
mysql -u root -p

# Verify .env DATABASE_URL
cat .env | findstr DATABASE_URL

# Check credentials
mysql -u root -ptharusha2001 -h localhost
```

### Issue: Missing dependencies

```bash
# Reinstall all dependencies
python -m pip install -r requirements.txt --force-reinstall

# Or update pip first
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Issue: Google OAuth not working

```bash
# Verify credentials in .env
echo %GOOGLE_CLIENT_ID%
echo %GOOGLE_CLIENT_SECRET%

# Check redirect URI in Google Cloud Console matches
# http://localhost:8000/auth/google/callback
```

---

## 📈 Development

### Hot Reload
The unified backend runs with `--reload` enabled. Changes to files automatically reload the server.

### Debugging
Enable detailed logging:
```python
# In main.py, change log_level
uvicorn.run(..., log_level="debug")
```

### Adding New Endpoints

To add endpoints to the unified backend:

1. **For Login Backend routes:**
   - Edit files in `login/app/routes/`
   - They're automatically included in unified backend

2. **For Skill Backend routes:**
   - Edit files in `Nipuni_backend/src/app/routes/`
   - They're automatically included with `/skill` prefix

3. **Restart** the unified backend to see changes

---

## 📦 Deployment

### Production Checklist

- [ ] Update `.env` with production values
- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Change `SECRET_KEY` to a secure random string
- [ ] Update CORS origins for frontend domain
- [ ] Set `https_only=True` for sessions
- [ ] Use production ASGI server (Gunicorn, etc.)

### Running with Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

---

## 📚 API Documentation

### Module Separation
While both services run on port 8000, they maintain clear logical separation:

```
/auth/*              → Login Backend (OAuth, JWT, admin)
/skill/*             → Nipuni Backend (transcripts, quizzes, jobs)
```

### Combined Health Checks
```bash
curl http://localhost:8000/health
# Returns status of both services
```

---

## 🔄 Migration from Separate Backends

If you were running separate backends before:

### Before (Old Way)
```bash
# Terminal 1
cd login
python -m uvicorn app.main:app --reload --port 8182

# Terminal 2
cd Nipuni_backend/src
python -m uvicorn app.main:app --reload --port 8000

# Frontend configuration needed both ports
```

### After (New Way)
```bash
# Single Terminal
python main.py

# Single port: 8000
# All routes under /auth/* or /skill/*
# Frontend updated to use http://localhost:8000
```

### Update Frontend URLs

If your frontend was configured for both ports, update to single port:

```typescript
// OLD: Multiple ports
const authAPI = "http://localhost:8182/auth";
const skillAPI = "http://localhost:8000/skill";

// NEW: Single port
const authAPI = "http://localhost:8000/auth";
const skillAPI = "http://localhost:8000/skill";
```

---

## 📞 Support

### Common Commands

```bash
# Check Python version
python --version

# Check if port is available
netstat -ano | findstr :8000

# Install requirements in current env
python -m pip install -r requirements.txt

# View logs
# See terminal output while running

# Test connection
curl -I http://localhost:8000/health
```

---

## ✅ Success Indicators

You'll know it's working when you see:

```
╔══════════════════════════════════════════════════════════════════════════╗
║                   SKILLSCOPE UNIFIED BACKEND                            ║
║                    Startup Script (PowerShell)                          ║
╚══════════════════════════════════════════════════════════════════════════╝

✅ Python found: Python 3.13.3
✅ Project directory verified

📦 Installing dependencies...
✅ Dependencies installed successfully

═══════════════════════════════════════════════════════════════════════════
🚀 Starting SkillScope Unified Backend...
═══════════════════════════════════════════════════════════════════════════

📊 Services Running:
   • Login Backend (OAuth 2.0, JWT, Admin)
   • Skill Validation Backend (Transcripts, Quizzes, Jobs)

🌐 Access Points:
   • Main API: http://localhost:8000
   • Swagger UI: http://localhost:8000/docs
   • ReDoc: http://localhost:8000/redoc
   • Health Check: http://localhost:8000/health

📍 Route Prefixes:
   • Authentication: http://localhost:8000/auth/*
   • Skills: http://localhost:8000/skill/*

🛑 To stop the server: Press Ctrl+C
═══════════════════════════════════════════════════════════════════════════
```

---

**Version:** 3.0.0  
**Last Updated:** March 25, 2026  
**Maintainer:** SkillScope Development Team
