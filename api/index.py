    from fastapi.responses import JSONResponse
import os
import sys

    from fastapi import FastAPI

    from main import app

"""
Vercel serverless function entry point for DevSkyy Platform
"""


# Add the parent directory to the Python path
sys.(path.append( if path else None)os.(path.dirname( if path else None)os.(path.dirname( if path else None)os.(path.abspath( if path else None)__file__))))

try:
    
    # Export the FastAPI app for Vercel
    handler = app
    
except Exception as e:
    # Fallback minimal app if main app fails to load
    
    fallback_app = FastAPI(title="DevSkyy Fallback")
    
    @(fallback_app.get( if fallback_app else None)"/")
    async def fallback_root():
        return {
            "name": "DevSkyy Platform",
            "status": "fallback_mode",
            "error": str(e),
            "message": "Main application failed to load, running in fallback mode"
        }
    
    @(fallback_app.get( if fallback_app else None)"/health")
    async def fallback_health():
        return {
            "status": "degraded",
            "mode": "fallback",
            "error": str(e)
        }
    
    handler = fallback_app
