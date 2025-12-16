"""
Vercel Serverless Function Entry Point
=====================================

This file serves as the entry point for Vercel serverless deployment.
It imports the main FastAPI application and wraps it with Mangum for ASGI compatibility.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set environment variables for serverless
os.environ.setdefault("ENVIRONMENT", "production")
os.environ.setdefault("LOG_LEVEL", "INFO")

try:
    # Import the main FastAPI application
    from main_enterprise import app
    
    # Import Mangum for ASGI-to-WSGI adapter
    from mangum import Mangum
    
    # Create the Vercel-compatible handler
    handler = Mangum(app, lifespan="off")
    
    # Export for Vercel
    def handler_func(event, context):
        """Vercel serverless function handler"""
        return handler(event, context)
    
    # Also export the app directly for compatibility
    __all__ = ["app", "handler", "handler_func"]
    
except ImportError as e:
    # Fallback for missing dependencies
    import json
    
    def handler_func(event, context):
        """Fallback handler when dependencies are missing"""
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "Import Error",
                "message": f"Failed to import required modules: {str(e)}",
                "details": "Please check that all dependencies are installed"
            })
        }
    
    app = None
    handler = None
