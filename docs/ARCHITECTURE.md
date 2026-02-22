# Architecture Reference

**Version**: 3.2.0
**Last Updated**: 2026-02-22

Complete architectural reference for the DevSkyy platform including dependency flow, codebase structure, and project phases.

---

## Dependency Flow (One-Way, No Cycles)

**Critical Rule**: Dependencies flow in ONE DIRECTION ONLY. Outer layers never import inner layers.

```
core/ (auth + registry) ← ZERO dependencies on outer layers
    ↓
adk/ (Agent Development Kit)
    ↓
security/ (implementations)
    ↓
agents/ (use adk.base, not legacy base.py)
    ↓
api/, services/
```

### Layer Responsibilities

| Layer | Purpose | Depends On | Never Depends On |
|-------|---------|------------|------------------|
| **core/** | Auth types, models, interfaces | Nothing | adk, security, agents, api |
| **adk/** | Agent Development Kit base classes | core | agents, api, services |
| **security/** | Security implementations (AES-256-GCM, JWT, audit) | core, adk | agents, api, services |
| **agents/** | AI agents and orchestration | core, adk, security | api, services (circular imports forbidden) |
| **api/**, **services/** | API endpoints, business logic | core, adk, security, agents | Nothing (top layer) |

---

## Codebase Structure

```
DevSkyy/
├── main_enterprise.py          # FastAPI entry point (47+ endpoints)
├── devskyy_mcp.py              # MCP server (13 tools)
│
├── core/                       # ⭐ Layer 1: Zero dependencies
│   ├── auth/                   # Auth types, models, interfaces
│   └── registry/               # Service registry for dependency injection
│
├── adk/                        # ⭐ Layer 2: Agent Development Kit
│   └── (symlink to sdk/python/adk)
│
├── security/                   # ⭐ Layer 3: Security implementations
│   ├── encryption.py           # AES-256-GCM encryption
│   ├── jwt.py                  # JWT token management
│   └── audit_log.py            # Security audit logging
│
├── agents/                     # ⭐ Layer 4: AI Agents
│   ├── base_super_agent.py    # Enhanced base (17 techniques, ADK-based)
│   ├── base_legacy.py          # ❌ Deprecated, use ADK
│   └── operations_legacy.py   # ❌ Deprecated
│
├── api/                        # ⭐ Layer 5: API Layer
│   └── v1/                     # REST endpoints
│       ├── gdpr/               # GDPR compliance
│       └── webhooks/           # Webhook handlers
│
├── services/                   # ⭐ Layer 5: Business Logic
│   ├── ai_image_enhancement.py # FLUX, SD3, RemBG
│   └── ...                     # Other services
│
├── llm/                        # LLM Router
│   ├── providers/              # 6 providers (OpenAI, Anthropic, Google, Cohere, Mistral, Groq)
│   ├── router.py               # Intelligent routing
│   └── round_table.py          # Multi-agent consensus
│
├── wordpress-theme/            # WordPress Theme
│   └── skyyrose-flagship/      # Production theme (v3.2.0)
│       ├── template-immersive-*.php   # Immersive 3D storytelling pages
│       ├── template-collection-*.php  # Collection catalog pages (shopping)
│       ├── template-preorder-gateway.php # Pre-order gateway
│       ├── elementor/widgets/         # Custom Elementor widgets
│       ├── inc/                       # Theme modules (enqueue, security, etc.)
│       └── woocommerce/               # WooCommerce templates
│
├── frontend/                   # Frontend Dashboard (Next.js)
│   ├── components/3d/          # LuxuryProductViewer (React Three Fiber)
│   ├── lib/animations/         # luxury-transitions.ts (Framer Motion)
│   └── app/                    # Next.js App Router
│
├── tests/                      # Test Suite
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── e2e/                    # End-to-end tests (1200+ tests)
│
├── docs/                       # Documentation
│   ├── CONTRIB.md              # Contributor guide
│   ├── RUNBOOK.md              # Operations runbook
│   ├── ENV_VARS_REFERENCE.md   # Environment variables
│   ├── MCP_TOOLS.md            # MCP tools catalog
│   ├── DEPENDENCIES.md         # Dependency reference
│   └── ARCHITECTURE.md         # This file
│
└── .claude/                    # Claude Code Configuration
    └── rules/                  # Code standards, testing, git workflow
```

---

## Project Phases

### Phase 1: Foundation (v1.0.0) ✅ Complete
- Core FastAPI backend
- Basic authentication
- Initial agent framework
- SQLite database

### Phase 2: Architecture Refactor (v1.3.1) ✅ Complete
- Root cleanup: `base.py`, `operations.py` → `agents/`
- Test organization: test files → `tests/integration/`
- Service registry: `core/registry/` for dependency injection
- Updated imports: agents use `base_legacy` until ADK migration
- **Dependency Flow Established**: One-way, no cycles

### Phase 3: ML & MCP Integration (v2.0.0) ✅ Complete
- MCP server (13 tools)
- RAG pipeline (ChromaDB, LlamaIndex)
- 6 LLM providers
- Round-table consensus
- Agent orchestration

### Phase 4: Production Hardening (v2.5.0) ✅ Complete
- PostgreSQL production database
- Redis caching
- Prometheus monitoring
- Sentry error tracking
- Security audit (OWASP compliance)

### Phase 5: WordPress Enhancement (v3.0.0) ✅ Complete
- 108 packages installed (39 JS/TS + 69 WordPress)
- `LuxuryProductViewer` component (React Three Fiber)
- Luxury animations library (Framer Motion)
- AI image enhancement (FLUX, SD3, RemBG)
- WordPress theme: `skyyrose-flagship`

### Phase 6: Production Theme Build (v3.2.0) ✅ Complete
- Full theme rebuild: 30,000+ lines of production code
- 4 collections: Black Rose, Love Hurts, Signature, Kids Capsule
- 3 immersive storytelling scenes (cathedral, castle, city tour)
- Pre-order gateway with checkout integration
- Full WooCommerce template overrides (archive, single, cart, checkout)
- Design system: Inter + Playfair Display, dark luxury palette
- Luxury Cursor, Cinematic Mode, Wishlist, Toast notifications
- Backend modules: enqueue, theme-setup, customizer, woocommerce, security, template-functions, ajax-handlers

---

## Key Architectural Patterns

### 1. Error Handling Pattern

```python
class ToolError(DevSkyError):
    def __init__(
        self,
        tool: str,
        reason: str,
        *,
        correlation_id: str | None = None
    ):
        super().__init__(f"Tool {tool} failed: {reason}")
        self.tool = tool
        self.correlation_id = correlation_id
```

**Rules**:
- Always accept `correlation_id` as keyword-only argument
- Always propagate `correlation_id` through call chain
- Use specific error types (not generic `Exception`)

### 2. Async Function Pattern

```python
async def process(
    data: InputModel,
    *,
    correlation_id: str | None = None
) -> OutputModel:
    """Process data with optional correlation ID for tracing."""
    try:
        result = await perform_operation(data)
        return OutputModel(result=result)
    except Exception as e:
        raise ProcessingError(
            "Processing failed",
            correlation_id=correlation_id
        ) from e
```

**Rules**:
- All async functions accept `correlation_id`
- Use Pydantic models for input/output
- Type hints on all parameters and returns
- Proper exception chaining with `from e`

### 3. Pydantic Model Pattern

```python
from pydantic import BaseModel, Field

class ProductInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    price: float = Field(..., gt=0)
    description: str | None = None

class ProductOutput(BaseModel):
    id: str
    name: str
    price: float
    created_at: datetime
```

**Rules**:
- Pydantic for all API inputs/outputs
- Use `Field()` for validation constraints
- Optional fields use `| None` (not `Optional[]`)
- Validate at system boundaries

---

## Security Architecture

### Encryption
- **Algorithm**: AES-256-GCM
- **Key Management**: AWS Secrets Manager (prod), `.env` (dev)
- **Implementation**: `security/encryption.py`

### Authentication
- **Method**: JWT + OAuth2
- **Token Storage**: HttpOnly cookies
- **Refresh Tokens**: Rotating refresh tokens
- **Implementation**: `core/auth/`, `security/jwt.py`

### Authorization
- **Model**: Role-Based Access Control (RBAC)
- **Roles**: admin, developer, user, readonly
- **Implementation**: `core/auth/models.py`

### Audit Logging
- **What**: All API calls, auth events, data mutations
- **Where**: `security/audit_log.py`
- **Storage**: PostgreSQL audit table, Sentry breadcrumbs

### GDPR Compliance
- **Endpoints**: `/api/v1/gdpr/export`, `/api/v1/gdpr/delete`
- **Implementation**: `api/v1/gdpr/`
- **Data Handling**: Encryption at rest, data minimization

---

## Performance Architecture

### Caching Strategy

| Layer | Technology | TTL | Use Case |
|-------|-----------|-----|----------|
| **L1: In-Memory** | Python dict | 5 min | Hot data, embeddings |
| **L2: Redis** | Redis | 15 min | Session data, query results |
| **L3: Database** | PostgreSQL | ∞ | Persistent storage |

### Async I/O
- **Framework**: FastAPI (async/await)
- **Database**: asyncpg (PostgreSQL), aiosqlite (SQLite)
- **HTTP**: httpx, aiohttp
- **File I/O**: aiofiles

### Connection Pooling
- **Database**: SQLAlchemy pool (size=10, max_overflow=20)
- **Redis**: Connection pool (max_connections=50)
- **HTTP**: httpx connection pool

---

## WordPress Theme Architecture

### Theme Structure (skyyrose-flagship v3.2.0)

```
skyyrose-flagship/
├── style.css                          # Theme header (v3.2.0)
├── functions.php                      # Bootstrap: constants + inc/ loader
├── inc/                               # Modular backend
│   ├── theme-setup.php                # Theme supports, menus, sidebars
│   ├── enqueue.php                    # Script/style registration
│   ├── enqueue-brand-styles.php       # Brand identity styles
│   ├── customizer.php                 # Live Preview Customizer
│   ├── template-functions.php         # Collection/product helpers
│   ├── woocommerce.php                # WooCommerce integration
│   ├── elementor.php                  # Elementor integration
│   ├── security.php                   # CSP headers, nonce helpers
│   ├── accessibility-seo.php          # A11y + SEO enhancements
│   ├── ajax-handlers.php              # AJAX endpoints
│   ├── wishlist-functions.php         # Wishlist functionality
│   └── class-wishlist-widget.php      # Wishlist sidebar widget
├── front-page.php                     # Homepage
├── template-homepage-luxury.php       # Luxury homepage template
├── template-immersive-black-rose.php  # Immersive: Gothic cathedral
├── template-immersive-love-hurts.php  # Immersive: Romantic castle
├── template-immersive-signature.php   # Immersive: Oakland/SF city tour
├── template-collection-black-rose.php # Catalog: Black Rose products
├── template-collection-love-hurts.php # Catalog: Love Hurts products
├── template-collection-signature.php  # Catalog: Signature products
├── template-collection-kids-capsule.php # Catalog: Kids Capsule products
├── template-preorder-gateway.php      # Pre-order gateway page
├── template-about.php                 # About page
├── template-contact.php               # Contact page
├── template-parts/                    # Reusable template parts
│   ├── cinematic-toggle.php           # Cinematic mode toggle
│   ├── product-card.php               # Product card component
│   ├── toast-notification.php         # Toast notification
│   └── wishlist-button.php            # Wishlist button
├── elementor/widgets/                 # Custom Elementor widgets
│   └── three-viewer.php              # Three.js 3D viewer widget
├── woocommerce/                       # WooCommerce template overrides
│   ├── archive-product.php            # Product archive
│   ├── content-product.php            # Product loop item
│   ├── single-product.php             # Single product page
│   ├── cart/cart.php                   # Cart page
│   └── checkout/form-checkout.php     # Checkout form
├── assets/css/                        # Stylesheets
│   ├── design-tokens.css              # CSS custom properties
│   ├── brand-variables.css            # Brand color system
│   ├── luxury-theme.css               # Base luxury styling
│   ├── luxury-cursor.css              # Custom cursor
│   ├── cinematic-mode.css             # Cinematic mode
│   ├── collections.css                # Collection pages
│   ├── immersive.css                  # Immersive pages
│   ├── front-page.css                 # Homepage
│   ├── woocommerce.css                # WooCommerce overrides
│   └── preorder-gateway.css           # Pre-order page
├── assets/js/                         # JavaScript
│   ├── navigation.js                  # Nav + mobile menu
│   ├── luxury-cursor.js               # Custom cursor effect
│   ├── cinematic-mode.js              # Cinematic mode toggle
│   ├── collections.js                 # Collection interactions
│   ├── immersive.js                   # Immersive page logic
│   ├── front-page.js                  # Homepage scripts
│   ├── preorder-gateway.js            # Pre-order form
│   ├── woocommerce.js                 # WooCommerce enhancements
│   └── contact.js                     # Contact form
└── theme.json                         # Block editor configuration
```

### Key Distinction

- **Immersive Pages** (`template-immersive-*.php`): 3D storytelling, NOT shopping
- **Catalog Pages** (`template-collection-*.php`): Product grids, FOR shopping

### Collections

| Collection | Immersive Template | Catalog Template |
|-----------|-------------------|------------------|
| **Black Rose** | `template-immersive-black-rose.php` (Gothic cathedral) | `template-collection-black-rose.php` |
| **Love Hurts** | `template-immersive-love-hurts.php` (Romantic castle) | `template-collection-love-hurts.php` |
| **Signature** | `template-immersive-signature.php` (Oakland/SF tour) | `template-collection-signature.php` |
| **Kids Capsule** | -- | `template-collection-kids-capsule.php` |

### Design System

- **Fonts**: Inter (body) + Playfair Display (headings)
- **Colors**: `#0A0A0A` (background), `#111111` (cards), `#B76E79` (rose gold), `#D4AF37` (gold)
- **Features**: Luxury Cursor, Cinematic Mode, Pre-order Gateway, Wishlist

---

## Deployment Architecture

### Backend (Render)
- **Service**: Web Service
- **Region**: US East (Ohio)
- **Runtime**: Python 3
- **Start Command**: `uvicorn main_enterprise:app --host 0.0.0.0 --port $PORT`
- **Health Check**: `/health`

### Frontend (Vercel)
- **Framework**: Next.js
- **Region**: Global (CDN)
- **Build**: `npm run build`
- **Deploy**: Automatic on push to `main`

### WordPress Theme (WordPress.com)
- **Manual Upload**: ZIP file via WordPress.com dashboard
- **WP-CLI**: `wp theme install skyyrose-flagship.zip --activate --force`
- **Cache**: Clear after deployment (60s propagation)

### Database (Render PostgreSQL)
- **Version**: PostgreSQL 15
- **Plan**: Starter (1 GB RAM, 1 GB storage)
- **Backups**: Daily automated backups

### Caching (Render Redis)
- **Version**: Redis 7
- **Plan**: Starter (25 MB)
- **Eviction**: LRU (Least Recently Used)

---

## Testing Architecture

### Test Organization

```
tests/
├── unit/                       # Fast, isolated tests
│   ├── test_auth.py
│   ├── test_agents.py
│   └── test_utils.py
├── integration/                # API, database tests
│   ├── test_api.py
│   ├── test_wordpress.py
│   └── test_woocommerce.py
└── e2e/                        # End-to-end tests
    ├── checkout.spec.ts
    └── admin.spec.ts
```

### Coverage Requirements

| Module | Minimum Coverage | Notes |
|--------|-----------------|-------|
| **core/** | 90%+ | Critical infrastructure |
| **agents/** | 85%+ | AI logic |
| **api/** | 90%+ | All endpoints |
| **services/** | 80%+ | Business logic |
| **utils/** | 85%+ | Helper functions |
| **UI components/** | 70%+ | React components |

### Test Execution

```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov --cov-report=html

# Run specific test types
pytest tests/unit/ -v           # Unit tests only
pytest tests/integration/ -v    # Integration tests only
pytest tests/e2e/ -v            # E2E tests only
```

---

## Monitoring Architecture

### Metrics (Prometheus)
- **Endpoint**: `/metrics`
- **Metrics**: Request count, latency, error rate, cache hit rate
- **Scrape Interval**: 15 seconds

### Error Tracking (Sentry)
- **DSN**: Configured in `.env`
- **Environment**: dev/staging/prod
- **Release**: Git commit SHA
- **Breadcrumbs**: Audit logs, user actions

### Health Checks
- **Overall**: `/health` (200 = healthy)
- **Readiness**: `/health/ready` (database, Redis connected)
- **Liveness**: `/health/live` (process running)

---

## Scaling Architecture

### Horizontal Scaling
- **Backend**: Multiple Render instances behind load balancer
- **Redis**: Redis Cluster (when needed)
- **Database**: Read replicas (when needed)

### Vertical Scaling
- **Backend**: Increase Render plan (2 GB → 4 GB → 8 GB RAM)
- **Database**: Increase PostgreSQL plan (1 GB → 4 GB → 8 GB)

### Caching Strategy
- **L1**: In-memory Python dict (hot data)
- **L2**: Redis (session data, query results)
- **L3**: PostgreSQL (persistent storage)
- **CDN**: Vercel Edge Network (static assets)

---

**See Also**:
- [CONTRIB.md](CONTRIB.md) - Development workflow
- [RUNBOOK.md](RUNBOOK.md) - Operations guide
- [DEPENDENCIES.md](DEPENDENCIES.md) - Dependency reference
- [MCP_TOOLS.md](MCP_TOOLS.md) - MCP tools catalog

**Document Owner**: DevSkyy Platform Team
**Next Review**: When architecture changes
