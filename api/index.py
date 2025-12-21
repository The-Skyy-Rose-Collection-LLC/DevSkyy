"""
DevSkyy API Handler
===================
Serverless ASGI handler for Vercel deployment.

This module wraps the FastAPI application (main_enterprise.py) with Mangum,
which converts ASGI applications to AWS Lambda-compatible handlers.
Vercel's Python runtime uses Lambda-compatible handlers for serverless functions.
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import main_enterprise
sys.path.insert(0, str(Path(__file__).parent.parent))

# Primary handler: FastAPI with Mangum (ASGI wrapper for serverless)
try:
    from mangum import Mangum

    from main_enterprise import app as fastapi_app

    # Wrap FastAPI app with Mangum for serverless deployment
    app = Mangum(fastapi_app, lifespan="off")

except ImportError as e:
    print(f"Error: Could not import FastAPI app: {e}")
    print("Using fallback mock API...")

    # Fallback handler for when FastAPI import fails
    import json
    from http.server import BaseHTTPRequestHandler
    from urllib.parse import urlparse

    class Handler(BaseHTTPRequestHandler):
        """Fallback HTTP handler with mock data"""

        MOCK_AGENTS = [
            {
                "id": "commerce-001",
                "type": "commerce",
                "name": "Commerce Agent",
                "description": "E-commerce operations",
                "status": "ready",
            },
            {
                "id": "creative-001",
                "type": "creative",
                "name": "Creative Agent",
                "description": "Visual content generation",
                "status": "ready",
            },
            {
                "id": "marketing-001",
                "type": "marketing",
                "name": "Marketing Agent",
                "description": "Marketing content",
                "status": "ready",
            },
        ]

        def do_GET(self):
            parsed_url = urlparse(self.path)
            path = parsed_url.path

            if path == "/":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                response = {
                    "status": "ok",
                    "message": "DevSkyy API (Fallback Mode)",
                    "note": "Using mock data - FastAPI not available",
                }
                self.wfile.write(json.dumps(response).encode())

            elif path == "/api/v1/agents":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(self.MOCK_AGENTS).encode())

            elif path.startswith("/api/v1/agents/"):
                agent_id = path.split("/")[-1]
                agent = next((a for a in self.MOCK_AGENTS if a["id"] == agent_id), None)
                if agent:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(agent).encode())
                else:
                    self.send_response(404)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Agent not found"}).encode())

            else:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Not found"}).encode())

        def log_message(self, format, *args):
            """Suppress default logging"""
            pass

    app = Handler
