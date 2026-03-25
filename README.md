# SkillScope - Explainable Employability Analysis Platform

[![Python 3.13](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.129-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-Latest-blue.svg)](https://react.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Running the System](#running-the-system)
- [Service Endpoints](#service-endpoints)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Documentation](#documentation)

---

## 🎯 Overview

**SkillScope** is a research-grade AI-powered platform that provides **explainable employability analysis** for students and professionals. The system analyzes skill gaps, recommends personalized learning paths, and generates capstone projects to bridge the gap between current skills and target job requirements.

### Key Features

- 🤖 **AI-Powered Skill Gap Analysis** - Identifies missing skills using LLMs
- 📊 **Explainable AI (XAI)** - Transparent reasoning for recommendations via SHAP
- 🎓 **Interview Preparation** - Personalized interview training and practice
- 🔗 **Graph-Based Recommendations** - GNN-powered skill & project recommendations
- 👤 **User Profile Management** - OAuth 2.0 authentication with Google
- 📄 **CV Analysis** - Automatic CV parsing and skill extraction
- 🌐 **Scalable Backend** - 7 microservices running simultaneously

---

## 🏗️ Architecture

SkillScope uses a **microservices architecture** with a unified launcher:

```
┌─────────────────────────────────────────────────────┐
│  Frontend (React + TypeScript + Vite)               │
│  🌐 http://localhost:8080                           │
└──────────┬──────────────────────────────────────────┘
           │
     ┌─────v──────────┐
     │ Config Server  │
     │ :8099          │
     └─────┬──────────┘
           │
    ┌──────┴──────────────────┬──────────────┬──────────┬──────────┐
    │                         │              │          │          │
    v                         v              v          v          v
┌────────────┐         ┌────────────┐  ┌─────────┐ ┌────────┐ ┌──────────┐
│  Login     │         │  Agent     │  │ Skill   │ │Interview│ │Recommend-│
│  Backend   │         │  Runtime   │  │ Backend │ │ Backend │ │ation     │
│  :8182     │         │  :8002     │  │ :8000   │ │:8188    │ │Engine    │
│            │         │            │  │         │ │         │ │  :8001   │
└────────────┘         └────────────┘  └─────────┘ └────────┘ └──────────┘
     │                      │              │          │          │
     └──────────────────────┼──────────────┼──────────┼──────────┘
                            │              │          │
                    ┌───────v─────────┐    │          │
                    │  MySQL Database │    │          │
                    │  oauth_users    │    │          │
                    └─────────────────┘    │          │
                                           v          v
                                    ┌──────────────────────────┐
                                    │  Neo4j Graph Database    │
                                    │  (Cloud Instance)        │
                                    └──────────────────────────┘

┌──────────────────────────────────────────────┐
│  Thisaravi Backend (Skill Gap AI)            │
│  Port 8010 - Self-Evolving Feedback Loop     │
└──────────────────────────────────────────────┘
```

### Services Overview

| Service | Port | Purpose |
|---------|------|---------|
| Config Server | 8099 | Dynamic service configuration discovery |
| Login Backend | 8182 | OAuth 2.0, JWT authentication, user management |
| Agent Runtime | 8002 | CV parsing, skill extraction, LLM integration |
| Skill Backend | 8000 | Transcripts, quizzes, recommendations |
| Interview Backend | 8188 | Interview preparation, Nilmani training |
| Recommendation Engine | 8001 | GNN model, course recommendations |
| **Thisaravi Backend** | **8010** | **Skill gap analysis with self-evolving prompts** |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.13.3** or higher
- **Node.js 18+**
- **MySQL 8.0+** (with `oauth_users` database)
- **Neo4j** (cloud instance or local)
- **Google OAuth credentials**

### 1-Minute Setup

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install Frontend dependencies
cd NewFrontend
bun install
# or npm install

# 3. Start all backends (from root directory)
cd ..
python main.py

# 4. Start frontend dev server (from NewFrontend)
cd NewFrontend
bun dev
# or npm run dev

# 5. Open browser
# Frontend: http://localhost:8080
```

---

## 📦 Installation

### Step 1: Clone & Navigate

```bash
git clone <repository-url>
cd Project-Integration
```

### Step 2: Create Python Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.\.venv\Scripts\Activate.ps1

# Activate (macOS/Linux)
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Install all service dependencies (no version pinning)
pip install -r requirements.txt

# This includes:
# - Web Framework: FastAPI, Uvicorn
# - Auth: Authlib, Python-Jose, PassLib
# - Database: SQLAlchemy, Neo4j, PyMySQL
# - LLM: OpenAI, Google GenAI, Langchain
# - ML: PyTorch, Scikit-learn, XGBoost
# - And more (76 total packages)
```

### Step 4: Configure Environment

Create a `.env` file at the root (template provided):

```bash
# Database
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/oauth_users
NEO4J_URI=neo4j+s://YOUR_INSTANCE.databases.neo4j.io
NEO4J_USER=your_neo4j_user
NEO4J_PASSWORD=your_neo4j_password

# OAuth
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret

# LLM
GEMINI_API_KEY=your_api_key
OLLAMA_BASE_URL=http://127.0.0.1:11434
```

### Step 5: Setup Frontend

```bash
cd NewFrontend

# Install with Bun (recommended, faster)
bun install

# Or with npm
npm install

cd ..
```

---

## ▶️ Running the System

### Option 1: Run ALL Services (Recommended)

```bash
# Activate virtual environment first
.\.venv\Scripts\Activate.ps1

# Start all 7 backends + config server
python main.py
```

**Output:**
```
==============================================================================
                SKILLSCOPE UNIFIED BACKEND LAUNCHER
              Starting 7 services simultaneously

 * Config Server (Dynamic Config)    ->  http://localhost:8099
 * Login Backend (OAuth, JWT)        ->  http://localhost:8182
 * Agent Runtime (CV Processing)     ->  http://localhost:8002
 * Skill Backend (Transcripts)       ->  http://localhost:8000
 * Interview Backend (Nilmani)       ->  http://localhost:8188
 * Recommendation Engine (Advanced)  ->  http://localhost:8001
 * Thisaravi Backend (Skill Gap AI)  ->  http://localhost:8010

 Ctrl+C to stop all services
==============================================================================
```

### Option 2: Run Individual Services

```bash
# Terminal 1: Config Server
cd Project-Integration
python -m uvicorn config_server:app --reload --host 0.0.0.0 --port 8099

# Terminal 2: Login Backend
cd login
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8182

# Terminal 3: Agent Runtime
cd Agent-Runtime
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8002

# Terminal 4: Skill Backend
cd Nipuni_backend/src
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 5: Interview Backend
cd Nilmani-backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8188

# Terminal 6: Recommendation Engine
cd Advanced-Recommendation-System
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001

# Terminal 7: Thisaravi Backend
cd Thisaravi-Backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8010

# Terminal 8: Frontend
cd NewFrontend
bun dev
```

### Option 3: Run Frontend Only (with existing backends)

```bash
cd NewFrontend
bun dev
# Opens: http://localhost:8080
```

---

## 🔌 Service Endpoints

### Config Server (8099)
```
GET  /config              - Get all service configuration
GET  /config/{service}    - Get specific service URL
GET  /health              - Health check
```

### Login Backend (8182)
```
GET  /docs                - API Documentation
POST /auth/register       - Register new user
POST /auth/login          - Login with username/password
GET  /auth/login/google   - Initiate Google OAuth
GET  /auth/callback       - OAuth callback handler
GET  /auth/health         - Health check
```

### Agent Runtime (8002)
```
GET  /docs                - API Documentation
POST /analyze-cv          - Analyze CV file
GET  /candidates/{id}     - Get candidate profile
POST /extract-skills      - Extract skills from text
GET  /health              - Health check
```

### Skill Backend (8000)
```
GET  /docs                - API Documentation
GET  /transcripts         - Get user transcripts
POST /quiz/submit         - Submit quiz answers
GET  /health              - Health check
```

### Interview Backend (8188)
```
GET  /docs                - API Documentation
GET  /interview/topics    - List interview topics
POST /practice/start      - Start interview practice
GET  /health              - Health check
```

### Recommendation Engine (8001)
```
GET  /docs                - API Documentation
POST /recommendations/skills - Get skill recommendations
GET  /courses             - Browse courses
GET  /health              - Health check
```

### Thisaravi Backend (8010)
```
GET  /docs                - API Documentation
POST /analyze             - Skill gap analysis
GET  /jobs-by-role        - Browse jobs by role
GET  /search-jobs         - Search job listings
GET  /health              - Health check
```

---

## ⚙️ Configuration

### Environment Variables

All configuration is centralized in `.env` at the root:

```bash
# Database
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/oauth_users
NEO4J_URI=neo4j+s://instance.databases.neo4j.io
NEO4J_USER=user
NEO4J_PASSWORD=password

# Authentication
SECRET_KEY=your-super-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Google OAuth
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxx

# Frontend & API URLs
FRONTEND_URL=http://localhost:8080
BACKEND_URL=http://localhost:8182
RECOMMENDATION_API_BASE_URL=http://localhost:8001

# LLM Configuration
GEMINI_API_KEY=your-key
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=mistral

# OpenAI (optional)
OPENAI_API_KEY=sk-xxx

# Application
ENVIRONMENT=development
DEBUG=true
```

### Frontend Configuration

The frontend automatically discovers service URLs from the config server at startup. If the config server is down, it falls back to default URLs defined in [NewFrontend/src/api/fallbackConfig.ts](NewFrontend/src/api/fallbackConfig.ts).

---

## 📁 Project Structure

```
Project-Integration/
├── .env                                # Centralized environment config
├── requirements.txt                    # All Python dependencies
├── main.py                             # Unified launcher (all 7 services)
├── config_server.py                    # Dynamic config provider
│
├── login/                              # Login Backend (OAuth, JWT)
│   ├── app/
│   │   └── config.py
│   └── main.py
│
├── Agent-Runtime/                      # CV Analysis & Skill Extraction
│   ├── main.py
│   ├── config/settings.py
│   └── database/
│
├── Nipuni_backend/                     # Skill Backend (Transcripts, Quizzes)
│   ├── src/app/
│   │   ├── main.py
│   │   └── config.py
│   └── db.py
│
├── Nilmani-backend/                    # Interview Backend
│   ├── app/
│   │   └── main.py
│   └── app/core/config.py
│
├── Advanced-Recommendation-System/     # GNN Recommendations
│   ├── main.py
│   ├── config/settings.py
│   └── models/
│
├── Thisaravi-Backend/                  # Skill Gap Analysis (Self-Evolving)
│   ├── main.py
│   ├── feedback/
│   ├── datasets/
│   └── clients/
│
├── NewFrontend/                        # React + TypeScript Frontend
│   ├── src/
│   │   ├── services/
│   │   │   ├── configService.ts
│   │   │   ├── api.ts
│   │   │   └── nilmaniService.ts
│   │   ├── hooks/useConfig.ts
│   │   └── components/
│   ├── package.json
│   └── vite.config.ts
│
├── login/app/                          # Database models & routes
├── config/                             # Config files per service
├── docs/                               # Documentation
└── README.md                           # This file
```

---

## 🐛 Troubleshooting

### Issue: "Connection refused" on port 8182

**Solution:** Ensure all backends are running:
```bash
python main.py
```

### Issue: "DATABASE_URL is not set"

**Solution:** Verify `.env` exists in root and contains DATABASE_URL:
```bash
cat .env | findstr DATABASE_URL
```

### Issue: "Neo4j connection failed"

**Solution:** Check Neo4j credentials in `.env`:
```bash
# Verify these are correct
NEO4J_URI=neo4j+s://YOUR_INSTANCE.databases.neo4j.io
NEO4J_USER=your_user
NEO4J_PASSWORD=your_password
```

### Issue: "CORS error" on frontend

**Solution:** The frontend should auto-discover service URLs from config server:
```bash
# Verify config server is running (port 8099)
curl http://localhost:8099/config
```

### Issue: OAuth login redirects to wrong port

**Solution:** Update `.env`:
```bash
GOOGLE_CLIENT_ID=your_correct_id
GOOGLE_CLIENT_SECRET=your_correct_secret
BACKEND_URL=http://localhost:8182
```

### Issue: Frontend still shows old ports

**Solution:** Clear browser cache and restart frontend:
```bash
cd NewFrontend
bun dev  # Or npm run dev
```

### Issue: MySQL connection error

**Solution:** Ensure MySQL is running and `oauth_users` database exists:
```bash
# Create database if missing
mysql -u root -p
> CREATE DATABASE oauth_users CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Issue: Dependency conflicts

**Solution:** Reinstall with fresh virtual environment:
```bash
deactivate
rmdir .venv /s
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 📚 Documentation

- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Detailed setup instructions
- **[ADMIN_SYSTEM_GUIDE.md](ADMIN_SYSTEM_GUIDE.md)** - Admin & system configuration
- **[Advanced-Recommendation-System/README.md](Advanced-Recommendation-System/README.md)** - GNN model docs
- **[Agent-Runtime/README.md](Agent-Runtime/README.md)** - CV analysis pipeline
- **[NewFrontend/README.md](NewFrontend/README.md)** - Frontend development

---

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/your-feature`
2. Commit changes: `git commit -am 'Add feature'`
3. Push branch: `git push origin feature/your-feature`
4. Submit pull request

---

## 📝 License

This project is part of a research initiative. See LICENSE file for details.

---

## 👨‍💼 Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review relevant service documentation
3. Check service health endpoints: `http://localhost:PORT/health`
4. Review logs in terminal output

---

## 🎯 Quick Commands Reference

```bash
# Start everything
python main.py

# Start frontend only
cd NewFrontend && bun dev

# Check service health
curl http://localhost:8099/health     # Config server
curl http://localhost:8182/health     # Login backend
curl http://localhost:8002/health     # Agent runtime
curl http://localhost:8000/health     # Skill backend
curl http://localhost:8188/health     # Interview backend
curl http://localhost:8001/health     # Recommendation
curl http://localhost:8010/health     # Thisaravi

# View API docs
http://localhost:8182/docs            # Login API
http://localhost:8002/docs            # Agent API
# ... (other services also have /docs)

# Get service configuration
curl http://localhost:8099/config

# Stop all services
# Ctrl+C in the main.py terminal
```

---

**Happy coding! 🚀**
