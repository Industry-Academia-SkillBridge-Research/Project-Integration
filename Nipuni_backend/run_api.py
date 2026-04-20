#!/usr/bin/env python
"""
Run the FastAPI development server
This script handles the working directory and Python path correctly
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

# Now import and run uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
