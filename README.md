DevSkyy Agent
An AI-powered, auto-fixing, self-healing dev agent for The Skyy Rose Collection.

## Enhanced Auto-Fix Features 🤖

The DevSkyy platform now includes advanced auto-fix capabilities:

### Automated Code Fixes
- **Python Enhancement**: Type hints, docstrings, PEP8 formatting, f-string optimization
- **JavaScript Modernization**: ES6+ features, arrow functions, strict mode
- **Security Scanning**: Hardcoded secrets detection and warnings
- **Project Structure**: Missing __init__.py files, configuration improvements
- **Performance Optimization**: Code pattern improvements and suggestions

### Branch Management
- **Automatic Branch Creation**: Creates dedicated branches for fixes
- **Smart Commit Messages**: Detailed commit messages with fix categorization
- **Git Integration**: Seamless integration with existing Git workflow

### Available Endpoints
- `POST /autofix/enhanced` - Full enhanced auto-fix with branch management
- `POST /autofix/quick` - Quick fix without branch creation  
- `POST /autofix/session` - Customizable auto-fix session
- `GET /autofix/status` - Get auto-fix status and capabilities
- `POST /run/enhanced` - Enhanced DevSkyy workflow

## Traditional Features
Runs every hour
Fixes HTML, CSS, JS, PHP errors
Optimizes Divi layout blocks
Auto-commits fixes to GitHub

## FastAPI Server
The agent workflow is exposed through a FastAPI application in main.py. The /run endpoint triggers a scan, applies fixes, commits them, and schedules the next run.

## Running
Start the server locally with:

uvicorn main:app --host 0.0.0.0 --port 8000

On Replit, the included .replit file runs this command automatically.
