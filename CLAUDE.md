# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application

```bash
# Development mode with auto-reload
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Production mode with multiple workers
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# With Docker
docker-compose up -d
```

### Testing

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_agents.py -v

# Run with coverage
pytest --cov=agent --cov=security --cov=api tests/

# Run production safety check (comprehensive validation)
python production_safety_check.py
```

### Security & Dependencies

```bash
# Security audit (check for vulnerabilities)
pip-audit

# Update dependencies safely
pip install --upgrade -r requirements.txt

# Check code quality
black . && flake8 . && mypy agent/
```

### Database Operations

```bash
# The platform uses SQLAlchemy with async support
# Default: SQLite (auto-created at ./devskyy.db)
# Production: PostgreSQL or MySQL via DATABASE_URL env var

# Database is auto-initialized on startup (startup_sqlalchemy.py)
# No manual migration commands needed for development
```

## Architecture Overview

### Enterprise Platform Structure (v5.1)

DevSkyy is a **FastAPI-based enterprise AI platform** with a **54-agent ecosystem**. The platform underwent a major upgrade from v4.0 to v5.1, transforming from Grade B (52/100) to Grade A- (90/100) enterprise-ready status.

**Key Architectural Components:**

1. **Agent System** (`agent/`)
   - **Base Agent** (`agent/modules/base_agent.py`): All agents inherit from BaseAgent class
   - **Agent Registry** (`agent/registry.py`): Dynamic agent discovery and registration
   - **Agent Orchestrator** (`agent/orchestrator.py`): Coordinates multi-agent workflows
   - **Security Manager** (`agent/security_manager.py`): Agent-level security enforcement

2. **Enterprise Security Layer** (`security/`)
   - **JWT Authentication** (`jwt_auth.py`): OAuth2 with access/refresh tokens, 5 RBAC roles
   - **AES-256-GCM Encryption** (`encryption.py`): Field-level encryption, PBKDF2 key derivation
   - **Input Validation** (`input_validation.py`): SQL/XSS/Command injection prevention

3. **API v1** (`api/v1/`)
   - **agents.py**: REST endpoints for all 54 agents (execute, status, capabilities)
   - **auth.py**: Authentication endpoints (login, register, refresh, logout)
   - **webhooks.py**: Webhook subscription management
   - **monitoring.py**: Health checks, metrics, performance tracking

4. **Webhook System** (`webhooks/webhook_system.py`)
   - Event-driven architecture with 15+ event types
   - HMAC signature authentication
   - Exponential backoff retry logic

5. **Observability** (`monitoring/observability.py`)
   - Metrics collection (counters, gauges, histograms)
   - Health monitoring with component-level checks
   - Performance tracking (P50/P95/P99 percentiles)

### Agent Organization

**Backend Agents** (`agent/modules/backend/`):
- Core: Scanner V2, Fixer V2, Security, Performance
- AI: Claude Sonnet, OpenAI, Multi-Model AI Orchestrator
- Specialized: 40+ domain-specific agents

**Frontend Agents** (`agent/modules/frontend/`):
- WordPress Theme Builder (Divi/Elementor)
- Fashion Computer Vision
- Social Media Automation
- Landing Page Generator
- Personalized Renderer

**E-commerce Subsystem** (`agent/ecommerce/`):
- Product Manager, Inventory Optimizer, Pricing Engine
- ML-powered forecasting and optimization

**ML Models** (`agent/ml_models/`):
- Base ML Engine with continuous learning
- Fashion-specific ML (trend prediction, style classification)

### Critical Architecture Patterns

1. **Agent Discovery & Registration**
   - Agents are auto-discovered at startup via `registry.discover_and_register_all_agents()`
   - Uses file introspection to find agent classes
   - Registers with orchestrator for task routing

2. **Security Architecture**
   - **ALL** API v1 endpoints require JWT authentication (except `/auth/login`, `/auth/register`)
   - Tokens must use UTC timestamps (`datetime.now(timezone.utc)`) - NOT naive datetime
   - RBAC enforced via `@require_role` decorators
   - Middleware stack: CORS → Input Validation → Performance Tracking → Auth

3. **Database Pattern**
   - Async SQLAlchemy with `async_session_maker`
   - Auto-initialization in `startup_sqlalchemy.py`
   - Supports SQLite (dev), PostgreSQL/MySQL (production)
   - Connection via `DATABASE_URL` environment variable

4. **Agent Execution Flow**
   ```
   User Request → API Endpoint → JWT Auth → Agent Registry Lookup
   → Orchestrator → Agent.execute_core_function() → Response
   ```

5. **Webhook Event Flow**
   ```
   Event Trigger → webhook_manager.emit_event() → HMAC Signing
   → HTTP POST to subscribers → Retry on failure → Track delivery
   ```

## Important Files & Their Purpose

### Core Application Files

- **`main.py`**: FastAPI application with all routers, middleware, startup logic
  - Registers API v1 routers (auth, agents, webhooks, monitoring)
  - Configures middleware (CORS, validation, performance tracking)
  - Runs health checks and agent discovery at startup

- **`database.py`**: SQLAlchemy async engine and session management
- **`startup_sqlalchemy.py`**: Database initialization and WordPress integration
- **`config.py`**: Application configuration from environment variables

### Agent System Core

- **`agent/orchestrator.py`**:
  - Routes tasks to appropriate agents
  - Manages agent lifecycle
  - Provides health status

- **`agent/registry.py`**:
  - Auto-discovers agents from `agent/modules/backend/` and `agent/modules/frontend/`
  - Maintains agent metadata (capabilities, version, status)
  - Handles agent registration with orchestrator

- **`agent/security_manager.py`**:
  - Enforces security policies for agent operations
  - Validates agent inputs
  - Manages agent permissions

### Enterprise v5.1 Additions

- **`security/jwt_auth.py`**:
  - **CRITICAL**: Uses UTC timestamps for token creation/validation
  - Default users: admin@devskyy.com (super_admin), developer@devskyy.com (developer)
  - Access tokens: 30 min expiry, Refresh tokens: 7 days

- **`security/encryption.py`**:
  - AES-256-GCM encryption for sensitive fields
  - Key derivation from `ENCRYPTION_MASTER_KEY` env var

- **`monitoring/observability.py`**:
  - Global instances: `metrics_collector`, `health_monitor`, `performance_tracker`
  - Used by middleware to track all HTTP requests

- **`webhooks/webhook_system.py`**:
  - Global instance: `webhook_manager`
  - Call `webhook_manager.emit_event()` to trigger webhooks

## Environment Configuration

### Required Variables

```bash
# Security (CRITICAL - Generate secure keys)
JWT_SECRET_KEY=your-secret-key-32-chars-min
ENCRYPTION_MASTER_KEY=your-base64-encoded-key

# AI Models (Required for agents)
ANTHROPIC_API_KEY=sk-ant-your-key
OPENAI_API_KEY=sk-your-key  # Optional but recommended

# Database (Optional - defaults to SQLite)
DATABASE_URL=postgresql://user:pass@localhost:5432/devskyy
```

### Optional Variables

```bash
# WordPress Integration
WORDPRESS_URL=https://your-site.com
WORDPRESS_API_KEY=your-api-key

# Features
META_ACCESS_TOKEN=your-token      # Social media automation
ELEVENLABS_API_KEY=your-key       # Voice/audio features
```

## Key Development Patterns

### Adding a New Agent

1. Create agent file in `agent/modules/backend/` or `agent/modules/frontend/`
2. Inherit from `BaseAgent` (defined in `agent/modules/base_agent.py`)
3. Implement `execute_core_function()` method
4. Agent will be auto-discovered at startup by registry
5. Add REST endpoint in `api/v1/agents.py` if needed

### Adding API Endpoints

1. Add to appropriate router in `api/v1/`
2. Use `Depends(get_current_active_user)` for authentication
3. Use `Depends(require_role("role_name"))` for RBAC
4. Return FastAPI responses with proper status codes

### Emitting Webhook Events

```python
from webhooks.webhook_system import webhook_manager, WebhookEvent

await webhook_manager.emit_event(
    event_type=WebhookEvent.AGENT_COMPLETED,
    data={"agent": "scanner", "status": "success"}
)
```

### Recording Metrics

```python
from monitoring.observability import metrics_collector

# Increment counter
metrics_collector.increment_counter("agent_executions", labels={"agent": "scanner"})

# Set gauge
metrics_collector.set_gauge("active_agents", 5)

# Record timing
metrics_collector.record_histogram("operation_duration_ms", 150.5)
```

## Production Deployment Notes

1. **ALWAYS use UTC timestamps** for JWT tokens - naive datetime will cause token expiration issues
2. **Set strong keys**: `JWT_SECRET_KEY` and `ENCRYPTION_MASTER_KEY` must be cryptographically secure
3. **Use PostgreSQL or MySQL** in production (set `DATABASE_URL`)
4. **Run with multiple workers**: `uvicorn main:app --workers 4`
5. **Enable SSL/TLS**: Use reverse proxy (nginx) with Let's Encrypt certificates
6. **Monitor health endpoint**: `/api/v1/monitoring/health` for liveness/readiness probes

## Security Notes

- Platform achieved **ZERO vulnerabilities** (Grade A+ security)
- All dependencies are audited via Dependabot and GitHub Actions
- JWT tokens use HS256 algorithm with secure key derivation
- Input validation middleware runs on ALL requests
- RBAC roles: `super_admin`, `admin`, `developer`, `api_user`, `read_only`

## Documentation References

- **Production Deployment**: `PRODUCTION_DEPLOYMENT.md`
- **Enterprise Upgrade Details**: `ENTERPRISE_UPGRADE_COMPLETE.md`
- **API Integration Guide**: `ENTERPRISE_API_INTEGRATION.md`
- **Quick Reference**: `QUICK_REFERENCE.md`
- **Security Reports**: `FINAL_SECURITY_STATUS.md`, `ZERO_VULNERABILITIES_ACHIEVED.md`

## API Documentation

When server is running, visit:
- Interactive API docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc
