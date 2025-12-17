# DevSkyy Codebase Index

> **Version**: 3.0.0
> **Last Updated**: 2025-12-17
> **Architecture**: Dual-stack monorepo (Python + TypeScript)

## Overview

DevSkyy is a production-grade AI orchestration platform for luxury fashion e-commerce automation, designed for the SkyyRose brand with WordPress/WooCommerce integration.

**Core Statistics:**
- Python Code: ~11,494 lines
- TypeScript Code: ~4,501 lines
- Total Root Python Files: ~3,112 lines

---

## Technology Stack

### Backend (Python 3.11+)
| Technology | Version | Purpose |
|------------|---------|---------|
| FastAPI | 0.104+ | Web framework |
| Uvicorn | ASGI | Production server |
| SQLAlchemy | 2.0+ | ORM |
| PostgreSQL | 15 | Database |
| Redis | 7 | Caching |
| Celery | 5.3+ | Task queue |

### Security
- JWT/OAuth2 with HS512 (15-minute access tokens)
- AES-256-GCM encryption (NIST SP 800-38D)
- Argon2id password hashing
- PBKDF2-HMAC-SHA256 key derivation (600k iterations)

### LLM Providers (6 integrated)
| Provider | Models |
|----------|--------|
| OpenAI | GPT-4o, GPT-4o-mini, o1-preview |
| Anthropic | Claude models |
| Google | GenAI models |
| Mistral | Mistral models |
| Cohere | Cohere models |
| Groq | Groq API |

### Frontend (TypeScript)
| Technology | Version | Purpose |
|------------|---------|---------|
| Vite | 7.2+ | Build tool |
| Three.js | 0.182+ | 3D graphics |
| React | 19+ | UI framework |
| Vue | 3.5+ | Alternative UI |
| Jest | 30+ | Testing |

### Infrastructure
- Docker multi-stage builds
- Nginx Alpine reverse proxy
- Prometheus + Grafana monitoring
- Loki + Promtail logging

---

## Directory Structure

### Core Application

| Directory | Purpose |
|-----------|---------|
| `/runtime/` | Tool registry, execution, and context management |
| `/llm/` | LLM provider clients & routing logic |
| `/agents/` | Specialized agent implementations (Tripo 3D, Fashn try-on, WordPress assets) |
| `/orchestration/` | Domain routing, LLM orchestration, brand context |
| `/api/` | FastAPI route handlers & endpoints |
| `/security/` | Enterprise security infrastructure (18 modules) |
| `/wordpress/` | WordPress REST API integration |
| `/database/` | SQLAlchemy ORM & database models |
| `/mcp/` | Model Context Protocol server |
| `/adk/` | Application Development Kit |

### Frontend (TypeScript)

| Directory | Purpose |
|-----------|---------|
| `/src/` | Main SDK & services |
| `/src/collections/` | 5 immersive 3D experiences |
| `/src/services/` | Agent, OpenAI, ThreeJS services |
| `/src/config/` | Configuration modules |
| `/src/utils/` | Utility functions |
| `/src/types/` | TypeScript type definitions |

### Configuration & Build

| Directory | Purpose |
|-----------|---------|
| `/config/` | TypeScript, testing (Jest), Nginx, Vite configs |
| `/templates/elementor/` | 13 pre-built Elementor JSON templates |
| `/scripts/` | Development & deployment utilities |
| `/docker/` | Alternative Docker configurations |
| `/docs/` | Project documentation |
| `/tests/` | Test suite (pytest + Jest) |

---

## Entry Points

### Python
| File | Purpose |
|------|---------|
| `main_enterprise.py` | Primary FastAPI application |
| `base.py` | SuperAgent base class, core abstractions |
| `operations.py` | Business operations layer |
| `devskyy_mcp.py` | MCP integration |

### TypeScript
| File | Purpose |
|------|---------|
| `src/index.ts` | Main SDK export, DevSkyy class |
| `src/services/AgentService.ts` | Agent lifecycle management |
| `src/services/OpenAIService.ts` | OpenAI API integration |
| `src/services/ThreeJSService.ts` | Three.js rendering |

---

## API Endpoints

```
/api/v1/agents     → Agent management
/api/v1/webhooks   → Event webhook system
/api/v1/auth       → JWT/OAuth2 authentication
/api/v1/gdpr       → GDPR compliance
/health            → Health check
```

---

## Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Python project metadata & dependencies |
| `package.json` | Node.js dependencies & scripts |
| `.mcp.json` | Model Context Protocol configuration |
| `Dockerfile` | Multi-stage Docker build |
| `docker-compose.yml` | Full stack orchestration |
| `Makefile` | Unified development commands |
| `.github/workflows/ci.yml` | GitHub Actions CI/CD |
| `tsconfig.json` | TypeScript compilation |
| `.pre-commit-config.yaml` | Git pre-commit hooks |

---

## Test Structure

### Python (`/tests/`)
```
tests/
├── test_agents.py           # Agent tests
├── test_adk.py              # ADK tests
├── test_gdpr.py             # GDPR compliance (14 tests)
├── test_llm.py              # LLM provider tests
├── test_runtime.py          # Tool registry tests
├── test_security.py         # Security tests
├── test_wordpress.py        # WordPress tests
├── security/
│   └── test_vulnerability_scanner.py
└── conftest.py              # Pytest fixtures
```

### TypeScript
```
src/collections/__tests__/CollectionExperiences.test.ts
config/testing/jest.config.cjs
```

---

## 3D Collection Experiences

| Collection | Theme | Atmosphere |
|------------|-------|------------|
| BlackRoseExperience | Gothic rose garden | Dark, silver moonlight, fog |
| SignatureExperience | Luxury outdoor | Golden hour, butterflies |
| LoveHurtsExperience | Gothic castle ballroom | Candlelight, stained glass |
| ShowroomExperience | Virtual showroom | Spotlights, orbit controls |
| RunwayExperience | Fashion runway | Catwalk, lighting rigs |

---

## Security Modules

```
security/
├── aes256_gcm_encryption.py      # NIST SP 800-38D compliant
├── jwt_oauth2_auth.py            # RFC 7519, RFC 6749
├── api_security.py               # API protection
├── pii_protection.py             # PII masking
├── input_validation.py           # Input sanitization
├── vulnerability_scanner.py      # CVE detection
├── vulnerability_remediation.py  # Auto-remediation
├── dependency_scanner.py         # Dependency audit
├── code_analysis.py              # SAST
├── ssrf_protection.py            # SSRF prevention
├── rate_limiting.py              # Request throttling
├── security_middleware.py        # FastAPI middleware
├── security_monitoring.py        # Security events
├── security_testing.py           # Security tests
├── advanced_auth.py              # Multi-factor auth
├── key_management.py             # Key storage/rotation
├── csp_middleware.py             # Content Security Policy
└── infrastructure_security.py    # Infra hardening
```

---

## Makefile Commands

### Build & Run
```bash
make install       # Install production deps
make dev           # Install dev deps
make build         # Build Python package
make docker-build  # Build Docker image
make docker-run    # Run Docker image
```

### Testing
```bash
make test          # Python tests
make test-cov      # With coverage
make ts-test       # TypeScript tests
make test-all      # All tests
make ci            # Full CI pipeline
```

### Code Quality
```bash
make lint          # Ruff + MyPy
make format        # isort + ruff + black
make lint-all      # All linters
make format-all    # All formatters
```

### 3D Demos
```bash
make demo-black-rose   # Gothic rose garden
make demo-signature    # Luxury outdoor
make demo-love-hurts   # Castle ballroom
make demo-showroom     # Virtual showroom
make demo-runway       # Fashion runway
```

---

## Architecture Patterns

### SuperAgent Pattern
All agents follow Plan → Retrieve → Execute → Validate → Emit workflow:
```python
class SuperAgent(ABC):
    async def run(request, context):
        plan = await _plan(request, context)
        retrieval = await _retrieve(request, plan, context)
        results = await _execute_step(step, retrieval, context)
        validation = await _validate(results, context)
        return await _emit(results, validation, context)
```

### Tool Registry Pattern
```python
registry = ToolRegistry()
spec = ToolSpec(name, description, category)
registry.register(spec, handler_function)
result = await registry.execute(tool_name, params, context)
```

### LLM Routing
- Tournament-style routing: Multiple LLM providers compete
- Domain-based routing: Different LLMs for different tasks
- Brand context injection: SkyyRose context automatically included

---

## WordPress Integration

- REST API Client with async support
- Elementor template generation with BrandKit
- WooCommerce product management
- Media management and optimization
- Custom shortcode generation
- BrandKit colors: obsidian, roseGold, ivory, silver, crimson

---

## Monitoring Stack

| Service | Port | Purpose |
|---------|------|---------|
| Prometheus | 9090 | Metrics collection |
| Grafana | 3000 | Dashboard visualization |
| Loki | 3100 | Log aggregation |
| Promtail | - | Log shipping |

---

## Quick Start

```bash
# Clone & setup
git clone https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy.git
cd DevSkyy
make dev

# Run locally
uvicorn main_enterprise:app --reload   # Backend
npm run dev                             # Frontend

# Testing
make test-all

# 3D Demos
make demo-black-rose
```

---

## Environment Variables

```bash
# LLM Providers
OPENAI_API_KEY="sk-..."
ANTHROPIC_API_KEY="sk-ant-..."

# WordPress
WP_SITE_URL="https://your-site.com"
WP_USERNAME="admin"
WP_APP_PASSWORD="xxxx xxxx xxxx xxxx"

# Security
JWT_SECRET_KEY="your-secret"
ENCRYPTION_MASTER_KEY="base64-32byte-key"
```
