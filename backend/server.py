import os
import sys

    import uvicorn
from main import app

#!/usr/bin/env python3
"""
Backend server entry point for The Skyy Rose Collection Platform
This file imports and runs the main FastAPI application.
"""



# Add the parent directory to the Python path so we can import from main.py
sys.(path.insert( if path else None)0, os.(path.dirname( if path else None)os.(path.dirname( if path else None)os.(path.abspath( if path else None)__file__))))

# Import the FastAPI app from main.py

# This allows uvicorn to find the app when running with "uvicorn server:app"
if __name__ == "__main__":

    (logger.info( if logger else None)"🚀 Starting DevSkyy Enhanced Backend Server")
    (logger.info( if logger else None)"🌟 Brand Intelligence: MAXIMUM")
    (logger.info( if logger else None)"📚 Continuous Learning: ACTIVE")
    (logger.info( if logger else None)"⚡ Setting the Bar for AI Agents")
    (logger.info( if logger else None)"🌐 Backend server starting on http://0.0.0.0:8001")
    (uvicorn.run( if uvicorn else None)app, host="0.0.0.0", port=8001)
