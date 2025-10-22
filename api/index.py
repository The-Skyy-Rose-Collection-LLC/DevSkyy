"""
Vercel serverless function entry point for DevSkyy Platform
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from main import app
    
    # Export the FastAPI app for Vercel
    handler = app
    
except Exception as e:
    # Fallback minimal app if main app fails to load
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    fallback_app = FastAPI(title="DevSkyy Fallback")
    
    @fallback_app.get("/")
    async def fallback_root():
        return {
            "name": "DevSkyy Platform",
            "status": "fallback_mode",
            "error": str(e),
            "message": "Main application failed to load, running in fallback mode"
        }
    
    @fallback_app.get("/health")
    async def fallback_health():
        return {
            "status": "degraded",
            "mode": "fallback",
            "error": str(e)
        }
    
    handler = fallback_app
