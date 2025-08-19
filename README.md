DevSkyy Agent
An AI-powered, auto-fixing, self-healing dev agent for The Skyy Rose Collection.

Runs every hour
Fixes HTML, CSS, JS, PHP errors
Optimizes Divi layout blocks
Auto-commits fixes to GitHub
FastAPI Server
The agent workflow is exposed through a FastAPI application in main.py. The /run endpoint triggers a scan, applies fixes, commits them, and schedules the next run.

Running
Start the server locally with:

uvicorn main:app --host 0.0.0.0 --port 8000
On Replit, the included .replit file runs this command automatically.
