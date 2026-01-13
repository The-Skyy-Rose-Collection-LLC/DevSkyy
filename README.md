# DevSkyy v3.0.0

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
- **Node.js**: 18+ (for frontend dashboard)

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

```
DevSkyy/
├── runtime/               # Tool registry and execution
│   └── tools.py           # ToolRegistry, ToolSpec, ToolCallContext
├── base.py                # SuperAgent base class
├── llm/                   # LLM provider clients
│   ├── providers.py       # OpenAI, Anthropic, Google, Mistral, Cohere, Groq
│   ├── router.py          # Multi-provider routing
│   └── tournament.py      # Tournament-style LLM consensus
├── orchestration/         # Domain routing and context
│   ├── llm_clients.py     # Official SDK-based LLM clients
│   ├── domain_router.py   # Task-based LLM routing
│   └── brand_context.py   # SkyyRose brand context injection
├── security/              # Enterprise security
│   ├── aes256_gcm_encryption.py
│   ├── jwt_oauth2_auth.py
│   └── argon2_password_hashing.py
├── agents/                # Super Agents
│   ├── fashn_agent.py     # Virtual try-on (FASHN API)
│   ├── tripo_agent.py     # 3D generation (Tripo3D)
│   └── wordpress_asset_agent.py
├── wordpress/             # WordPress integration
│   ├── client.py          # REST API client
│   ├── elementor.py       # Template builder with BrandKit
│   ├── media.py           # Media management
│   └── products.py        # WooCommerce products
├── src/                   # TypeScript SDK
│   ├── collections/       # 3D Collection Experiences
│   │   ├── BlackRoseExperience.ts
│   │   ├── SignatureExperience.ts
│   │   ├── LoveHurtsExperience.ts
│   │   ├── ShowroomExperience.ts
│   │   └── RunwayExperience.ts
│   └── services/          # Three.js, Agent, OpenAI services
├── templates/elementor/   # Elementor JSON templates
├── demo/                  # 3D experience demo pages
└── tests/                 # Python test suite (pytest)
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
from base import SuperAgent, AgentConfig

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
