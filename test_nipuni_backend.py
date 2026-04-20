#!/usr/bin/env python3
"""
Quick test to verify Nipuni backend can start
Run this BEFORE running the full unified launcher
"""
import subprocess
import sys
import time
from pathlib import Path

project_root = Path(__file__).parent
nipuni_path = project_root / "Nipuni_backend"

print("\n" + "="*80)
print("Testing Nipuni Backend Startup")
print("="*80 + "\n")

print(f"Working Directory: {nipuni_path}")
print(f"Directory exists: {nipuni_path.exists()}")
print(f"src/app/main.py exists: {(nipuni_path / 'src' / 'app' / 'main.py').exists()}\n")

# Try to start the backend
print("Starting Nipuni Backend (port 8000)...")
print("Command: python -m uvicorn src.app.main:app --reload --port 8000\n")

cmd = [sys.executable, "-m", "uvicorn", "src.app.main:app", "--reload", "--port", "8000"]
try:
    proc = subprocess.Popen(cmd, cwd=str(nipuni_path), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print("Process started with PID:", proc.pid)
    print("\nWaiting 5 seconds for startup...\n")
    time.sleep(5)
    
    if proc.poll() is None:
        print("✓ Backend is running!")
        print("\nTest endpoint: curl http://localhost:8000/health")
        print("Swagger UI: http://localhost:8000/docs")
        print("ML API docs: http://localhost:8000/api/readiness/health")
        print("\nPress Ctrl+C to stop the server...")
        
        try:
            proc.wait()
        except KeyboardInterrupt:
            print("\nStopping backend...")
            proc.terminate()
            proc.wait(timeout=5)
    else:
        print("✗ Backend exited immediately!")
        stdout, stderr = proc.communicate()
        print("\nSTDOUT:")
        print(stdout)
        print("\nSTDERR:")
        print(stderr)
        sys.exit(1)
        
except Exception as e:
    print(f"✗ Error starting backend: {e}")
    sys.exit(1)

print("\n" + "="*80)
print("Test Complete")
print("="*80)
