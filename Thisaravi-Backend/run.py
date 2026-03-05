import subprocess
import time
import sys
import os

def main():
    print("Starting Skill Gap Analysis App...")

    # 1. Start Backend
    print("Launching Backend API (FastAPI)...")
    # Using sys.executable ensures we use the same python interpreter (venv aware)
    backend_process = subprocess.Popen(
        [sys.executable, "main.py"],
        cwd=os.getcwd(),
        env=os.environ.copy()
    )

    # Wait a moment for backend to initialize
    time.sleep(2)

    # 2. Start Frontend
    print("Starting Frontend UI (Streamlit)...")
    frontend_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "ui.py"],
        cwd=os.getcwd(),
        env=os.environ.copy()
    )

    # 3. Start Feedback UI
    print("Starting Feedback Portal (Streamlit port 8502)...")
    feedback_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "feedback_ui.py", "--server.port", "8502"],
        cwd=os.getcwd(),
        env=os.environ.copy()
    )

    # 4. Start Evolution Dashboard
    print("Starting Evolution Dashboard (Streamlit port 8503)...")
    evolution_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "evolution_ui.py", "--server.port", "8503"],
        cwd=os.getcwd(),
        env=os.environ.copy()
    )

    print("App Running! Press Ctrl+C to stop.")
    print("  API (Swagger): http://localhost:8010/docs")
    print("  Main UI:       http://localhost:8501")
    print("  Feedback:      http://localhost:8502")
    print("  Evolution:     http://localhost:8503")

    try:
        # Keep main process alive while children run
        while True:
            if backend_process.poll() is not None:
                print("Backend exited unexpectedly.")
                break
            if frontend_process.poll() is not None:
                print("Frontend exited unexpectedly.")
                break
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        backend_process.terminate()
        frontend_process.terminate()
        feedback_process.terminate()
        evolution_process.terminate()
        backend_process.wait()
        frontend_process.wait()
        feedback_process.wait()
        evolution_process.wait()
        print("All services stopped.")

if __name__ == "__main__":
    main()
