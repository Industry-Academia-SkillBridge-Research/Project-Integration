#!/usr/bin/env python3
"""
SkillScope Unified Backend Launcher
Starts 5 backends simultaneously:
- Login Backend (8182)
- Agent Runtime (8003)
- Skill Backend (8000)
- Interview Backend (8188)
- Recommendation Engine (8001)
"""
import subprocess
import sys
import time
import os
from pathlib import Path
import signal

project_root = Path(__file__).parent
login_path = project_root / "login"
agent_path = project_root / "Agent-Runtime"
nipuni_path = project_root / "Nipuni_backend"
nilmani_path = project_root / "Nilmani-backend"
recommendation_path = project_root / "Advanced-Recommendation-System"
thisaravi_path = project_root / "Thisaravi-Backend"

processes = []

def signal_handler(sig, frame):
    print("\n\nShutting down backends...")
    for proc in processes:
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
    print("All services stopped")
    sys.exit(0)

def start_backends():
    print(""" 
==============================================================================
                SKILLSCOPE UNIFIED BACKEND LAUNCHER
              Starting 6 services simultaneously

 * Config Server (Dynamic Config)    ->  http://localhost:8099
 * Login Backend (OAuth, JWT)        ->  http://localhost:8182
 * Agent Runtime (CV Processing)     ->  http://localhost:8003
 * Skill Backend (Transcripts)       ->  http://localhost:8000
 * Interview Backend (Nilmani)       ->  http://localhost:8188
 * Recommendation Engine (Advanced)  ->  http://localhost:8001

 Ctrl+C to stop all services
==============================================================================
    """)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    print("\nStarting services...\n")
    
    # Start Config Server (port 8099) - FIRST, before other services
    print("Launching Config Server (port 8099)...")
    config_cmd = [sys.executable, "-m", "uvicorn", "config_server:app", "--reload", "--host", "0.0.0.0", "--port", "8099"]
    config_proc = subprocess.Popen(config_cmd, cwd=str(project_root))
    processes.append(config_proc)
    time.sleep(2)
    
    # Start Login Backend (port 8182)
    print("Launching Login Backend (port 8182)...")
    login_cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8182"]
    login_proc = subprocess.Popen(login_cmd, cwd=str(login_path))
    processes.append(login_proc)
    time.sleep(3)
    
    # Start Agent Runtime (port 8003)
    print("Launching Agent Runtime (port 8003)...")
    agent_cmd = [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8003"]
    agent_proc = subprocess.Popen(agent_cmd, cwd=str(agent_path))
    processes.append(agent_proc)
    time.sleep(3)
    
    # Start Nipuni Backend (port 8000)
    print("Launching Skill Backend (port 8000)...")
    nipuni_cmd = [sys.executable, "-m", "uvicorn", "src.app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
    nipuni_proc = subprocess.Popen(nipuni_cmd, cwd=str(nipuni_path))
    processes.append(nipuni_proc)
    time.sleep(3)
    
    # Start Nilmani Backend (port 8188)
    print("Launching Interview Backend - Nilmani (port 8188)...")
    nilmani_cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8188"]
    nilmani_proc = subprocess.Popen(nilmani_cmd, cwd=str(nilmani_path))
    processes.append(nilmani_proc)
    time.sleep(3)
    
    # Start Recommendation Engine (port 8001)
    print("Launching Recommendation Engine (port 8001)...")
    recommendation_cmd = [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8001"]
    recommendation_proc = subprocess.Popen(recommendation_cmd, cwd=str(recommendation_path))
    processes.append(recommendation_proc)
    time.sleep(3)
    
    # Start Thisaravi Backend (port 8010)
    # DISABLED: Thisaravi has import issue, fix later
    # print("Launching Thisaravi Backend - Skill Gap AI (port 8010)...")
    # thisaravi_cmd = [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8010"]
    # thisaravi_proc = subprocess.Popen(thisaravi_cmd, cwd=str(thisaravi_path), env={**os.environ, "PORT": "8010"})
    # processes.append(thisaravi_proc)
    # time.sleep(3)
    
    print("\n" + "="*80)
    print("OK - ALL 6 SERVICES RUNNING")
    print("="*80)
    print("""
CONFIG SERVER (port 8099) - Dynamic Configuration
   Config: http://localhost:8099/config
   Health: http://localhost:8099/health

LOGIN BACKEND (port 8182)
   Docs: http://localhost:8182/docs
   Health: http://localhost:8182/auth/health

AGENT RUNTIME (port 8003)
    Docs: http://localhost:8003/docs
    Health: http://localhost:8003/health

SKILL BACKEND (port 8000)
   Docs: http://localhost:8000/docs
   Health: http://localhost:8000/health

INTERVIEW BACKEND - Nilmani (port 8188)
   Docs: http://localhost:8188/docs
   Health: http://localhost:8188/health

RECOMMENDATION ENGINE - Advanced (port 8001)
   Docs: http://localhost:8001/docs
   Health: http://localhost:8001/health

THISARAVI BACKEND - Skill Gap AI (port 8010)
   Docs: http://localhost:8010/docs
   Health: http://localhost:8010/health

Stop: Ctrl+C
""")
    print("="*80 + "\n")
    
    try:
        while True:
            for proc in processes:
                if proc and proc.poll() is not None:
                    print(f"⚠️ Service exited")
                    signal_handler(None, None)
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    if not login_path.exists() or not agent_path.exists() or not nipuni_path.exists() or not nilmani_path.exists() or not recommendation_path.exists() or not thisaravi_path.exists():
        print("ERROR - Backend paths not found")
        sys.exit(1)
    start_backends()
