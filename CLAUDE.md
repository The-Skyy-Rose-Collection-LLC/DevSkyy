# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

### Development Workflow
```bash
# Complete setup (first time)
make setup                    # Installs both backend and frontend dependencies
cp .env.example .env         # Then configure with your API keys

# Run development servers
make run                     # Backend: Python main.py (http://localhost:8000)
make frontend-dev            # Frontend: npm run dev (http://localhost:5173)
make run-prod               # Production: Uvicorn with 4 workers

# Testing
make test                   # Run pytest on tests/
pytest tests/test_agents.py -v    # Run specific test file
make test-coverage          # Run with coverage report

# Code quality
make format                 # Black + isort formatting
make lint                   # Flake8 + black --check + isort --check
make type-check             # Mypy type checking
make pre-commit             # Run all checks before committing

# Deployment validation
make prod-check             # Run production_safety_check.py
python3 production_safety_check.py  # Manual safety check

# Docker
make docker-build           # Build image: devskyy-platform:latest
make docker-run             # docker-compose up -d
make docker-stop            # docker-compose down
```

### Frontend Specific
```bash
cd frontend
npm install                 # Install dependencies
npm run dev                 # Development server (Vite)
npm run build               # Production build
npm run lint                # ESLint
npm run format              # Prettier
```

## High-Level Architecture

### Multi-Layer Agent System

**DevSkyy uses a sophisticated 3-tier agent orchestration architecture:**

1. **Core Intelligence Layer** (`agent/modules/`)
   - `claude_sonnet_intelligence_service.py` - Primary reasoning engine using Claude Sonnet 4.5
   - `multi_model_ai_orchestrator.py` - Routes requests to optimal AI model (Claude/GPT-4/Gemini)
   - `openai_intelligence_service.py` - OpenAI GPT integration

2. **Specialized Agent Layer** (50+ agents)
   - Each agent is self-contained with domain expertise
   - Agents communicate through `agent_assignment_manager.py` which routes tasks
   - Agents can call other agents but must go through the assignment manager

3. **Integration Layer**
   - `wordpress_integration_service.py` - REST API integration
   - `wordpress_direct_service.py` - Direct database access (Paramiko SSH)
   - `woocommerce_integration_service.py` - E-commerce operations

### Critical Architecture Patterns

#### Agent Communication Flow
```
Client Request
    ↓
FastAPI Endpoint (main.py)
    ↓
AgentAssignmentManager.assign_task()
    ↓
Specialized Agent (e.g., ecommerce_agent.py)
    ↓
Multi-Model Orchestrator (selects Claude/GPT-4/Gemini)
    ↓
External API / WordPress / Database
```

#### Self-Healing System
- **Scanner** (`agent/modules/scanner.py`) - Detects issues in code/websites
- **Fixer** (`agent/modules/fixer.py`) - Applies fixes for common issues
- **Universal Self-Healing Agent** - Advanced auto-repair with multi-language support
- **Enhanced Autofix** - Context-aware fixes using AI reasoning

#### Continuous Learning Loop
- `continuous_learning_background_agent.py` runs 24/7 in background
- Analyzes patterns, failures, and successes
- Updates agent behaviors without code changes
- Stores learnings in MongoDB for persistence

### WordPress Integration Architecture

**Three parallel integration methods** (intentional redundancy for reliability):

1. **REST API** (`wordpress_integration_service.py`)
   - Standard WordPress REST API v2
   - Authentication via Application Passwords
   - Best for: Content, posts, pages, media

2. **Direct Database** (`wordpress_direct_service.py`)
   - SSH + Paramiko connection to server
   - Direct MySQL queries via command line
   - Best for: Bulk operations, migrations, emergency fixes

3. **WordPress Plugin** (`wordpress-plugin/`)
   - Custom plugin: "Skyy Rose AI Agents"
   - Provides webhooks and extended endpoints
   - Best for: Real-time events, custom actions

**Important**: Always prefer REST API first, fall back to direct access only when necessary.

### Frontend Architecture

**React + TypeScript with luxury e-commerce focus:**

- `frontend/src/components/` - 20+ components
  - `ModernWordPressDashboard.jsx` - Main WordPress control panel
  - `LuxuryThemeBuilder.jsx` - Visual theme editor
  - `AgentDashboard.jsx` - Agent monitoring UI
  - `AutomationDashboard.jsx` - Automation controls

**Component Communication:**
- Uses React Context for global state (no Redux)
- WebSocket connections for real-time agent status
- REST API calls to backend via Axios

### Database Schema Pattern

**MongoDB Collections** (defined implicitly in code):
- `agents` - Agent configurations and status
- `tasks` - Task queue and history
- `products` - E-commerce products
- `orders` - Order processing
- `customers` - Customer data
- `learnings` - Continuous learning storage
- `cache` - Performance caching layer

**Important**: The codebase uses Motor (async MongoDB driver). All database operations must be async/await.

## Key Development Patterns

### Agent Development

When creating a new agent:

1. **Create agent file** in `agent/modules/new_agent.py`
2. **Define class** inheriting base patterns (see `ecommerce_agent.py` as template)
3. **Register in main.py** - Add try/except import block around line 10-150
4. **Add to assignment manager** - Update `agent_assignment_manager.py` routing logic
5. **Create tests** in `tests/test_agents.py`

**Agent Template Structure:**
```python
class NewAgent:
    def __init__(self, api_key: str, mongodb_uri: str):
        self.api_key = api_key
        self.db = AsyncMongoClient(mongodb_uri)
        self.ai = ClaudeSonnetIntelligence()  # or MultiModelOrchestrator

    async def perform_task(self, task_data: dict) -> dict:
        # 1. Validate input
        # 2. Query AI/external services
        # 3. Store results in MongoDB
        # 4. Return structured response
        pass
```

### Error Handling Convention

**All agents use try/except with graceful fallbacks:**

```python
try:
    from agent.modules.complex_agent import ComplexAgent
except Exception:
    ComplexAgent = None

    def create_complex_agent(*args, **kwargs):
        return {"status": "unavailable"}
```

This allows the platform to start even if optional dependencies are missing.

### Environment Variables

**Required (in .env):**
- `ANTHROPIC_API_KEY` - Claude Sonnet access (primary AI)
- `MONGODB_URI` - Database connection string

**Optional but recommended:**
- `OPENAI_API_KEY` - GPT-4 for multi-model orchestration
- `META_ACCESS_TOKEN` - Facebook/Instagram automation
- `ELEVENLABS_API_KEY` - Voice/audio generation
- `WORDPRESS_URL` - Default WordPress site
- `WORDPRESS_USERNAME` / `WORDPRESS_PASSWORD` - Application password

### Testing Strategy

**Test files mirror module structure:**
- `tests/test_main.py` - FastAPI endpoint tests
- `tests/test_agents.py` - Agent functionality tests

**Run single test:**
```bash
pytest tests/test_agents.py::test_specific_function -v
```

**Mock external services** (AI APIs, WordPress) in tests to avoid costs and ensure speed.

## Important Implementation Details

### FastAPI Middleware Stack

In `main.py`, middleware is configured in specific order (bottom to top execution):

1. **TrustedHostMiddleware** - Security (prevent host header attacks)
2. **CORSMiddleware** - Cross-origin configuration
3. **Custom error handlers** - Graceful error responses

### Async/Await Requirements

**Critical**: This codebase is heavily async. When adding new functionality:

- Use `async def` for any function doing I/O (database, API calls, file operations)
- Use `await` when calling async functions
- Use `motor` for MongoDB (not pymongo)
- Use `aiofiles` for file operations (not standard open())

### Performance Optimization

The platform uses **multi-level caching**:

1. **Redis cache** (`cache_manager.py`) - For frequent queries
2. **Memory cache** - In-process caching for session data
3. **Database indexes** - MongoDB indexes for common queries

**When adding database queries**, always consider indexing needs.

### Security Considerations

**Authentication flow:**
1. JWT tokens generated by `auth_manager.py`
2. Tokens validated on each request
3. Role-based access control (RBAC) for different agent permissions

**API key storage:**
- Never commit keys to git
- Use environment variables exclusively
- Validate all external inputs (Pydantic models)

## Deployment Architecture

### Production Stack

```
User Request
    ↓
Nginx (Reverse Proxy + SSL)
    ↓
Uvicorn (4 workers)
    ↓
FastAPI Application (main.py)
    ↓
MongoDB (Database)
Redis (Cache)
```

### Pre-Deployment Checklist

Run `python3 production_safety_check.py` which validates:
- Environment variables are set
- No debug mode enabled
- All security headers configured
- No hardcoded secrets
- Database connections work
- Required files present

### CI/CD Pipeline

**GitHub Actions** (`.github/workflows/`):
- `ci.yml` - Run tests, linting, type-checking on every push
- `deploy.yml` - Automated deployment to production (on main branch)

## Common Development Tasks

### Adding a New API Endpoint

1. Add route in `main.py` (around line 500+)
2. Use Pydantic models from `models.py` for request/response validation
3. Add error handling with appropriate HTTP status codes
4. Update API documentation (auto-generated by FastAPI)
5. Add tests in `tests/test_main.py`

### Integrating a New AI Model

1. Create service file in `agent/modules/` (e.g., `gemini_intelligence_service.py`)
2. Update `multi_model_ai_orchestrator.py` to include new model
3. Add model selection logic based on task type
4. Update environment variables for API keys
5. Test with fallback mechanisms

### Adding WordPress Functionality

1. Check if REST API supports the feature (most common)
2. Add method to `wordpress_integration_service.py`
3. If REST API insufficient, add to `wordpress_direct_service.py`
4. For custom functionality, extend `wordpress-plugin/` PHP code
5. Test all three integration paths for consistency

## Architecture Decision Records

### Why Multiple WordPress Integration Methods?

**Decision**: Maintain three parallel integration systems (REST API, Direct DB, Plugin)

**Rationale**:
- REST API can be rate-limited or disabled by hosting
- Direct access allows emergency operations when REST fails
- Plugin provides custom endpoints not available in core WordPress
- Redundancy ensures 99.9% uptime for critical operations

### Why Claude Sonnet as Primary AI?

**Decision**: Use Claude Sonnet 4.5 as primary intelligence, orchestrate to others

**Rationale**:
- Superior reasoning for complex business logic
- Better at following structured instructions for agent tasks
- Excellent at code analysis and generation (self-healing)
- GPT-4 used for specific tasks (creative content, certain APIs)
- Cost-effective for bulk operations with quality maintenance

### Why Async Throughout?

**Decision**: Async/await pattern for all I/O operations

**Rationale**:
- Platform handles 10,000+ concurrent users
- Long-running AI operations must not block other requests
- Background agents run continuously without blocking
- Database operations are naturally async with Motor
- Better resource utilization on multi-core systems

## Troubleshooting Guide

### "Module not found" errors on startup
- Check if optional dependency - platform should start anyway with fallbacks
- If required module, run `make install` or `pip install -r requirements.txt`

### MongoDB connection timeouts
- Verify `MONGODB_URI` in .env
- Check if MongoDB service is running
- Test connection: `mongosh "$MONGODB_URI"`

### Frontend can't reach backend
- Backend runs on `http://localhost:8000` (check `make run` output)
- Frontend expects backend at that URL (configured in `frontend/vite.config.js`)
- Check CORS settings in `main.py` if running on different domain

### AI API rate limits
- Multi-model orchestrator automatically falls back to alternative models
- Check logs for which model is being used
- Increase delays in `multi_model_ai_orchestrator.py` if needed

### Tests failing
- Run `make clean` to remove cached files
- Ensure MongoDB is running for integration tests
- Check if test environment variables are set (tests use separate .env.test)

## References

- FastAPI Documentation: https://fastapi.tiangolo.com
- Claude API Docs: https://docs.anthropic.com
- WordPress REST API: https://developer.wordpress.org/rest-api/
- MongoDB Motor: https://motor.readthedocs.io
