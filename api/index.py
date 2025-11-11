import os
import sys

from fastapi import FastAPI

from main import app

"""
Vercel serverless function entry point for DevSkyy Platform
"""

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

handler = app
error_msg = None

try:
    # Verify the app is accessible
    _ = app.title
except Exception as e:
    # Fallback minimal app if main app fails to load
    error_msg = str(e)
    fallback_app = FastAPI(title="DevSkyy Fallback")

    @fallback_app.get("/")
    async def fallback_root():
        return {
            "name": "DevSkyy Platform",
            "status": "fallback_mode",
            "error": error_msg,
            "message": "Main application failed to load, running in fallback mode"
        }

    @fallback_app.get("/health")
    async def fallback_health():
        return {
            "status": "degraded",
            "mode": "fallback",
            "error": error_msg
        }

    handler = fallback_app
