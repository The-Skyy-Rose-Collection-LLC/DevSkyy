# DevSkyy MCP Server - Quick Start Guide (Repository Snapshot Notice)

> NOTE: This documentation describes the full MCP server product. This repository snapshot contains only main.py and many MCP-related modules may be missing. main.py uses conditional imports and will operate with reduced functionality if optional modules (mcp server, agents, redis, etc.) are not present.

## ⚡ Quick Start - One-Click Installation (Recommended)

The following is applicable for the full DevSkyy distribution. For this lightweight snapshot, many endpoints and installers referenced below may not be available until you have the full codebase and dependencies installed.

### Local manual startup (snapshot-robust)

To run the FastAPI app from this snapshot (preferred):

```bash
# Recommended: start the app using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000
```

Notes:
- main.py's guarded imports mean that features like the MCP gateway, Redis-backed caching, and Claude/Anthropic integrations may be disabled at runtime if dependencies aren't installed.
- Running `python main.py` will attempt to start uvicorn as configured by the script. For reliability, use `uvicorn main:app` which points at the app object defined in this file.

### Environment variables (minimum useful set for snapshot)

```bash
export ENVIRONMENT=development
export PORT=8000
export LOG_LEVEL=INFO
# Optional for certain features
export REDIS_URL=redis://localhost:6379
export SECRET_KEY=dev-only-insecure-key-DO-NOT-USE-IN-PRODUCTION
```

### Quick verification

```bash
uvicorn main:app --reload
# Visit http://localhost:8000/health
```

If the response indicates `"status": "healthy"`, the main app is running. Other advanced features (MCP, Claude integrations, WordPress automation) require the respective modules and configuration to be present.

---

## Why this note
main.py is written to gracefully handle missing optional components and will log warnings when features aren't available. The full MCP experience requires the complete codebase and dependencies.
