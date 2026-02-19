# DevSkyy v3.1.0

**Autonomous Fashion-Specific WordPress/Elementor Theme-Building Platform**

[![CI](https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/actions/workflows/ci.yml/badge.svg)](https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 🌹 **SkyyRose** - Where Love Meets Luxury | [skyyrose.co](https://skyyrose.co)

## 🌐 Production URLs

- **Frontend**: https://app.devskyy.app
- **API**: https://api.devskyy.app
- **API Docs**: https://api.devskyy.app/docs

## Overview

DevSkyy is a production-grade AI orchestration platform designed for luxury fashion e-commerce automation. It powers the SkyyRose brand with specialized agents for WordPress/WooCommerce management, immersive 3D collection experiences, virtual try-on, and autonomous theme building.

### Key Features

- **Multi-Agent Architecture**: SuperAgent base class with deterministic tool calling
- **Tool Runtime**: Centralized ToolRegistry with schema validation, permissions, and execution tracking
- **6 LLM Providers**: OpenAI, Anthropic, Google, Mistral, Cohere, Groq with tournament-style routing
- **Enterprise Security**: AES-256-GCM encryption, JWT/OAuth2, Argon2id password hashing
- **WordPress Integration**: REST API client, Elementor template generation, WooCommerce products
- **3D Asset Pipeline**: Tripo3D integration for 3D model generation with retry logic
- **Virtual Try-On**: FASHN API integration for fashion visualization
- **Immersive 3D Experiences**: Five collection-specific Three.js environments

## 3D Collection Experiences

DevSkyy includes five immersive Three.js-powered collection landing pages:

| Collection | Environment | Atmosphere |
|------------|-------------|------------|
| **BLACK ROSE** | Gothic rose garden | Dark ambient, silver moonlight, fog effects |
| **SIGNATURE** | Luxury outdoor setting | Golden hour, butterflies, brand elements |
| **LOVE HURTS** | Gothic castle ballroom | Candlelight, stained glass, enchanted rose |
| **Showroom** | Virtual showroom | Spotlights, product displays, orbit controls |
| **Runway** | Fashion runway | Catwalk, lighting rigs, camera systems |

Preview demos locally:

```bash
make demo-black-rose    # Gothic rose garden
make demo-signature     # Outdoor luxury
make demo-love-hurts    # Castle ballroom
make demo-showroom      # Virtual showroom
make demo-runway        # Fashion runway
```

## Requirements

- **Python**: 3.11 or 3.12 (recommended)
  - ⚠️ Python 3.14+ has compatibility issues with some dependencies (Cohere SDK, Pydantic V1)
- **PostgreSQL**: 15+ (for Round Table persistence)
- **Redis**: 7+ (optional, for caching)
- **Node.js**: 22+ (required by package.json engines)

## Installation

```bash
# Clone repository
git clone https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy.git
cd DevSkyy

# Verify Python version (must be 3.11 or 3.12)
python --version

# Install Python + TypeScript dependencies
make dev

# Or install separately
pip install -e ".[dev]"
npm install

# Verify dependencies
python scripts/verify_dependencies.py
```

## Quick Start

```python
from runtime.tools import get_tool_registry
from agents import TripoAssetAgent, FashnTryOnAgent
from wordpress import ElementorBuilder, BrandKit

# Initialize tool registry
registry = get_tool_registry()

# Create 3D asset agent
tripo = TripoAssetAgent(registry=registry)
result = await tripo.run({
    "action": "generate_from_description",
    "product_name": "Heart aRose Bomber",
    "collection": "BLACK_ROSE",
    "garment_type": "bomber",
})

# Generate Elementor template
builder = ElementorBuilder()
template = builder.generate_home_page(
    hero_title="SkyyRose",
    hero_subtitle="Where Love Meets Luxury",
)
template.to_file("home.json")
```

## Architecture

DevSkyy is organized into 8 core components with clear dependency boundaries:

### Component Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    HTTP/WebSocket Layer                      │
│                   (FastAPI + ASGI)                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Security Layer                            │
│         (JWT, OAuth2, Rate Limiting, Audit)                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌────────────┬──────────────┬──────────────┬─────────────────┐
│  API       │  Agents      │  MCP         │  Orchestration  │
│  Routes    │  (54 agents) │  Servers     │  (RAG/LLM)      │
└────────────┴──────────────┴──────────────┴─────────────────┘
                            ↓
┌────────────┬──────────────┬──────────────┬─────────────────┐
│  Services  │  LLM         │  Database    │  Integrations   │
│  (ML/3D)   │  Providers   │  (Postgres)  │  (WP/Stripe)    │
└────────────┴──────────────┴──────────────┴─────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Core Layer                                │
│   (Auth Types, Logging, Caching, Validation, Utilities)    │
└─────────────────────────────────────────────────────────────┘
```

### 1. **Core** - Foundation Layer
   - **Zero dependencies** on outer layers (api, agents, services)
   - `core/auth/` - Authentication types, models, interfaces
   - `core/registry/` - Service registry for dependency injection
   - `core/runtime/` - Tool registry, input validation

### 2. **Security** - Authentication & Encryption
   - AES-256-GCM encryption (NIST SP 800-38D)
   - JWT + OAuth2 implementation (uses `core/auth` interfaces)
   - Argon2id password hashing (OWASP recommended)
   - Audit logging, rate limiting, zero-trust architecture

### 3. **Database** - Data Access Layer
   - Async SQLAlchemy + repository pattern
   - PostgreSQL 15+ with connection pooling
   - Alembic migrations
   - Repository interfaces defined in `core/repositories`

### 4. **LLM** - Multi-Provider Router
   - **6 Providers**: OpenAI, Anthropic, Google, Mistral, Cohere, Groq
   - Tournament-style routing for consensus
   - Provider abstraction via `core/llm/interfaces`
   - Cost optimization and fallback handling

### 5. **Orchestration** - RAG & Workflows
   - RAG pipeline (ChromaDB + Pinecone)
   - Context management and query rewriting
   - Workflow orchestration (LangGraph, CrewAI)
   - Brand context injection

### 6. **Services** - Business Logic
   - **ML Services**: Stable Diffusion, ControlNet, DreamBooth
   - **3D Services**: Tripo3D, Meshy, Replicate
   - **Analytics**: User behavior, product insights
   - **Media Pipeline**: Image processing, CDN management

### 7. **Agents** - AI Orchestration
   - **54 specialized agents** using EnhancedSuperAgent base
   - **17 prompt techniques** (CoT, ReAct, ToT, Self-Refine, etc.)
   - **ADK Integration**: Multi-framework support (Google ADK, PydanticAI, CrewAI)
   - Agent capabilities: 3D generation, virtual try-on, WordPress automation

### 8. **API** - REST & WebSocket Endpoints
   - **47+ endpoints** (FastAPI)
   - GDPR compliance endpoints
   - Webhook handlers (Stripe, WooCommerce)
   - Admin dashboard
   - MCP server integration (13 tools)

### Dependency Flow Rules

```
Core (no deps)
  ↓
Security, Database, LLM
  ↓
Orchestration, Services
  ↓
Agents
  ↓
API
```

**One-way dependencies**: Lower layers never import upper layers. Horizontal dependencies use interfaces + dependency injection via `ServiceRegistry`.

See [docs/architecture/SYSTEM_ARCHITECTURE.md](docs/architecture/SYSTEM_ARCHITECTURE.md) for detailed diagrams.

## Test Coverage

- **Unit Tests**: 150+ tests (fast, isolated)
- **Integration Tests**: 40+ tests (multi-component)
- **E2E Tests**: 8 tests (critical user flows)
- **Overall Coverage**: 85%+

```bash
# Run test suite
pytest tests/unit -v          # Unit tests (<1s each)
pytest tests/integration -v   # Integration tests (<10s each)
pytest tests/e2e -v           # E2E tests (<60s each)

# Generate coverage report
pytest --cov=. --cov-report=html --cov-report=term-missing
```

See [docs/testing/COVERAGE_MATRIX.md](docs/testing/COVERAGE_MATRIX.md) for feature → test mappings.

## File Structure

```
DevSkyy/
├── core/                   # Foundation layer (zero outer dependencies)
│   ├── auth/              # Auth types, models, interfaces
│   ├── registry/          # Service registry for DI
│   └── runtime/           # Tool registry, validation
├── security/              # Encryption, JWT, audit
├── database/              # SQLAlchemy, repositories
├── llm/                   # LLM provider router (6 providers)
├── orchestration/         # RAG, workflows, context
├── services/              # Business logic (ML, 3D, analytics)
├── agents/                # 54 AI agents
│   ├── base_super_agent.py  # EnhancedSuperAgent (17 techniques)
│   └── */                 # Specialized agents
├── api/                   # FastAPI endpoints
│   └── v1/               # REST API routes
├── integrations/          # External services (WordPress, Stripe)
├── src/                   # TypeScript SDK
│   ├── collections/       # 3D experiences (Three.js)
│   └── services/          # Frontend services
├── tests/                 # Test suite (1200+ tests)
│   ├── unit/             # Fast, isolated tests
│   ├── integration/      # Multi-component tests
│   └── e2e/              # End-to-end flows
├── docs/                  # Documentation
│   ├── architecture/      # System design, data flow
│   └── testing/          # Coverage matrix
├── scripts/               # Utility scripts
├── main_enterprise.py     # FastAPI app (47+ endpoints)
└── devskyy_mcp.py        # MCP server (13 tools)
```

## Configuration

Set environment variables for API credentials:

```bash
# LLM Providers
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="..."

# WordPress
export WP_SITE_URL="https://your-site.com"
export WP_USERNAME="admin"
export WP_APP_PASSWORD="xxxx xxxx xxxx xxxx"

# WooCommerce
export WC_CONSUMER_KEY="ck_..."
export WC_CONSUMER_SECRET="cs_..."

# 3D Generation
export TRIPO_API_KEY="..."
export FASHN_API_KEY="..."

# Security
export JWT_SECRET_KEY="your-secret-key"
export ENCRYPTION_MASTER_KEY="base64-encoded-32-byte-key"
```

## Development

```bash
# Install all dependencies (Python + TypeScript)
make dev

# Run all tests
make test-all      # Python + TypeScript

# Run tests by language
make test          # Python only (pytest)
make ts-test       # TypeScript only (jest)

# Format all code
make format-all    # Python + TypeScript

# Lint all code
make lint-all      # Python + TypeScript

# Run full CI pipeline locally
make ci

# TypeScript specific
make ts-build      # Compile TypeScript
make ts-type-check # Type checking only
```

## Security

- **Encryption**: AES-256-GCM with NIST SP 800-38D compliance
- **Key Derivation**: PBKDF2-HMAC-SHA256 with 600,000 iterations
- **Password Hashing**: Argon2id (OWASP recommended)
- **JWT**: HS512 with short-lived access tokens (15 min)
- **Token Security**: Rotation, blacklisting, rate limiting

## API Documentation

### Tool Registry

```python
from runtime.tools import ToolRegistry, ToolSpec, ToolCategory

registry = ToolRegistry()

# Register a tool
spec = ToolSpec(
    name="my_tool",
    description="Does something",
    category=ToolCategory.CONTENT,
)
registry.register(spec, my_handler_function)

# Execute tool
result = await registry.execute("my_tool", {"param": "value"}, context)
```

### SuperAgent Workflow

All agents follow the Plan → Retrieve → Execute → Validate → Emit workflow:

```python
from agents.base_super_agent import EnhancedSuperAgent
from adk.base import AgentConfig

class MyAgent(SuperAgent):
    async def _plan(self, request, context):
        return [PlanStep(...)]

    async def _retrieve(self, request, plan, context):
        return RetrievalContext(...)

    async def _execute_step(self, step, retrieval_context, context):
        return ExecutionResult(...)

    async def _validate(self, results, context):
        return ValidationResult(...)

    async def _emit(self, results, validation, context):
        return {"status": "success", ...}
```

### Elementor Templates

```python
from wordpress.elementor import ElementorBuilder, PageSpec, PageType

# Using builder directly
builder = ElementorBuilder()
template = builder.generate_home_page(hero_title="Welcome")

# Using PageSpec
spec = PageSpec(
    page_type=PageType.COLLECTION,
    title="New Arrivals",
    slug="new-arrivals",
)
template = generate_template(spec)
```

## Brand Design Tokens

The platform uses the SkyyRose brand kit design tokens:

```typescript
const SKYYROSE_BRAND_KIT = {
  colors: {
    obsidian: '#0d0d0d',    // Primary dark
    roseGold: '#d4af37',    // Accent gold
    ivory: '#f5f5f0',       // Light background
    silver: '#c0c0c0',      // Metallic accent
    crimson: '#dc143c',     // Love Hurts red
    candlelight: '#ff9933', // Warm accent
  },
  typography: {
    heading: 'Playfair Display',
    body: 'Montserrat',
  },
};
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

**The Skyy Rose Collection LLC**
🌹 Where Love Meets Luxury
Oakland, California

[skyyrose.co](https://skyyrose.co)
