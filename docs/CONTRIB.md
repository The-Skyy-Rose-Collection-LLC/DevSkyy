# DevSkyy Contributor Guide

**Version**: 3.2.0
**Last Updated**: 2026-02-22
**Status**: Complete
**Source of Truth**: `package.json`, `.env.example`

Welcome to the DevSkyy platform! This guide will help you set up your development environment, understand our workflow, and contribute effectively to the codebase.

---

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Development Workflow](#development-workflow)
3. [Testing Requirements](#testing-requirements)
4. [Code Quality Standards](#code-quality-standards)
5. [WordPress Theme Development](#wordpress-theme-development)
6. [Architecture Guidelines](#architecture-guidelines)
7. [Available Tools & Skills](#available-tools--skills)
8. [Troubleshooting](#troubleshooting)

---

## Development Environment Setup

### Prerequisites

**Required Software:**
- **Python**: 3.11-3.12 (3.13-3.14 supported, 3.15+ not yet tested)
- **Node.js**: 22.0.0+ (required by package.json engines)
- **npm**: 10.0.0+ (required by package.json engines)
- **PostgreSQL**: 15+ (production), SQLite works for development
- **Redis**: 7+ (optional but recommended for caching)
- **Git**: 2.30+

**Verify Prerequisites:**
```bash
python --version    # Should be 3.11.x or 3.12.x
node --version      # Should be v22.x.x or higher
npm --version       # Should be 10.x.x or higher
psql --version      # Should be 15.x or higher
redis-cli --version # Should be 7.x.x or higher
git --version       # Should be 2.30.x or higher
```

### Quick Start

1. **Clone Repository**
   ```bash
   git clone https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy.git
   cd DevSkyy
   ```

2. **Install Python Dependencies**
   ```bash
   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate

   # Install in editable mode with all dependencies
   pip install -e ".[all]"

   # Or install specific groups:
   # pip install -e ".[dev,api,mcp,ml]"
   ```

3. **Install Node.js Dependencies**
   ```bash
   npm install
   ```

4. **Configure Environment Variables**
   ```bash
   # Copy example files
   cp .env.example .env
   cp .env.wordpress.example .env.wordpress
   cp mcp_servers/.env.example mcp_servers/.env

   # Generate security keys (CRITICAL)
   python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(64))" >> .env
   python -c "import secrets, base64; print('ENCRYPTION_MASTER_KEY=' + base64.b64encode(secrets.token_bytes(32)).decode())" >> .env

   # Add at least one AI provider API key
   echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" >> .env
   # or OPENAI_API_KEY, GOOGLE_AI_API_KEY, etc.
   ```

   **See [ENV_VARS_REFERENCE.md](ENV_VARS_REFERENCE.md) for complete environment variable documentation.**

5. **Set Up Database**
   ```bash
   # For development (SQLite - default)
   # DATABASE_URL already set in .env to sqlite+aiosqlite:///./devskyy.db

   # For production (PostgreSQL - recommended)
   # Update DATABASE_URL in .env:
   # DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/devskyy

   # Run migrations
   alembic upgrade head
   ```

6. **Start Development Server**
   ```bash
   # Backend (Python FastAPI)
   uvicorn main_enterprise:app --reload --host 0.0.0.0 --port 8000

   # Frontend (Node.js/TypeScript) - in separate terminal
   npm run dev

   # MCP Server - in separate terminal
   cd mcp_servers
   python devskyy_mcp.py
   ```

7. **Verify Installation**
   ```bash
   # Check backend health
   curl http://localhost:8000/health
   # Expected: {"status": "healthy", "version": "3.2.0", ...}

   # Check API docs
   open http://localhost:8000/docs

   # Check frontend
   open http://localhost:3000
   ```

---

## Development Workflow

### Core Protocol (MANDATORY)

Every development task MUST follow this protocol (from `CLAUDE.md`):

1. **Context7** → `resolve-library-id` → `query-docs` (BEFORE library code)
2. **Serena** → Codebase navigation and symbol lookup
3. **Navigate** → Read first, understand, NO code until clear
4. **Implement** → Use targeted edits (`Edit` tool or `str_replace`)
5. **Test** → `pytest -v` (MANDATORY after EVERY change)
6. **Format** → `isort . && ruff check --fix && black .`

**Example Workflow:**
```bash
# 1. Context7: Get up-to-date docs (before coding)
# Use MCP tools: resolve-library-id → query-docs for libraries

# 2. Serena: Navigate codebase
# Use MCP tools: find_symbol, get_symbols_overview, search_for_pattern

# 3. Navigate: Understand existing code
# Read relevant files using Read tool

# 4. Implement: Make targeted changes
# Use Edit tool for precise modifications

# 5. Test: MANDATORY
pytest -v

# 6. Format: Code quality
isort .
ruff check --fix .
black .

# Frontend equivalent:
npm run lint:fix
npm run type-check
npm test
```

### Git Workflow

**Branch Naming:**
```
feature/add-agent-orchestration
fix/wordpress-api-401-error
refactor/cleanup-base-agent
docs/update-contributing-guide
chore/upgrade-dependencies
```

**Commit Message Format:**
```
<type>: <description>

<optional body>

<optional footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code restructuring (no functional changes)
- `docs`: Documentation updates
- `test`: Test additions/modifications
- `chore`: Maintenance tasks (deps, config)
- `perf`: Performance improvements
- `ci`: CI/CD changes

**Examples:**
```bash
git commit -m "feat: add WordPress product sync agent"
git commit -m "fix: resolve CORS issue in API endpoints"
git commit -m "refactor: extract auth logic to core module"
```

**Note:** Attribution is disabled globally via `~/.claude/settings.json`. No need to add `Co-Authored-By` tags.

### Pre-Commit Protocol (MANDATORY)

Before EVERY commit, run these checks:

**Python (Backend):**
```bash
# 1. Format imports
isort .

# 2. Fix linting issues
ruff check --fix .

# 3. Format code
black .

# 4. Type check
mypy . --ignore-missing-imports

# 5. Run tests (MANDATORY)
pytest -v

# Combined command:
isort . && ruff check --fix . && black . && pytest -v
```

**TypeScript/JavaScript (Frontend):**
```bash
# 1. Fix linting
npm run lint:fix

# 2. Format code
npm run format

# 3. Type check
npm run type-check

# 4. Run tests (MANDATORY)
npm test

# Combined command (use precommit script):
npm run precommit
```

**Automated Pre-Commit Hook:**
```bash
# Install pre-commit (optional but recommended)
pip install pre-commit
pre-commit install

# This will run checks automatically before each commit
```

### Pull Request Workflow

**Creating a PR:**

1. **Ensure your branch is up-to-date**
   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. **Run full test suite**
   ```bash
   pytest -v --cov  # Python
   npm run test:ci  # JavaScript
   ```

3. **Create PR with comprehensive description**
   ```bash
   # Use GitHub CLI (recommended)
   gh pr create --title "feat: Add agent orchestration" --body "
   ## Summary
   - Implemented multi-agent orchestration framework
   - Added round-table consensus mechanism
   - Integrated with MCP server

   ## Test plan
   - [ ] Unit tests pass (pytest -v)
   - [ ] Integration tests pass
   - [ ] Manual testing completed
   - [ ] Documentation updated

   ## Related Issues
   Closes #123

   🤖 Generated with Claude Code
   "
   ```

4. **Address review feedback**
   - Make requested changes
   - Re-run tests
   - Push updates (no need to amend, create new commits)

**Reviewing PRs:**
- Check code quality (linting, formatting, types)
- Verify tests exist and pass
- Test functionality locally if complex
- Ensure documentation is updated
- Check for security issues (secrets, input validation)

---

## Testing Requirements

### Test-Driven Development (TDD)

DevSkyy enforces strict TDD workflow for all new features and bug fixes:

**TDD Cycle (RED → GREEN → IMPROVE):**

1. **Write Test First (RED)**
   ```python
   # tests/test_agent_orchestrator.py
   def test_agent_orchestration_returns_consensus():
       """Test that agent orchestration returns consensus result."""
       orchestrator = AgentOrchestrator()
       result = await orchestrator.orchestrate(
           task="Analyze sales data",
           agents=["analyst", "data_scientist"]
       )
       assert result.status == "success"
       assert result.consensus is not None
   ```

2. **Run Test - Should FAIL**
   ```bash
   pytest tests/test_agent_orchestrator.py -v
   # Expected: FAILED (function not implemented yet)
   ```

3. **Write Minimal Implementation (GREEN)**
   ```python
   # agents/orchestrator.py
   class AgentOrchestrator:
       async def orchestrate(self, task: str, agents: list[str]):
           # Minimal implementation to pass test
           return OrchestrationResult(
               status="success",
               consensus={"result": "placeholder"}
           )
   ```

4. **Run Test - Should PASS**
   ```bash
   pytest tests/test_agent_orchestrator.py -v
   # Expected: PASSED
   ```

5. **Refactor (IMPROVE)**
   - Improve implementation
   - Add error handling
   - Optimize performance
   - Keep tests passing

6. **Verify Coverage**
   ```bash
   pytest --cov=agents --cov-report=html
   open htmlcov/index.html
   # Minimum: 80% coverage required
   ```

### Test Types

**1. Unit Tests** - Individual functions/methods
```python
# tests/unit/test_auth.py
def test_jwt_token_generation():
    token = generate_jwt(user_id="123")
    assert token is not None
    assert decode_jwt(token)["user_id"] == "123"
```

**2. Integration Tests** - API endpoints, database
```python
# tests/integration/test_api.py
async def test_create_product_endpoint(client):
    response = await client.post(
        "/api/v1/products",
        json={"name": "Test Product", "price": 99.99}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Product"
```

**3. E2E Tests** - Critical user flows (Playwright)
```typescript
// tests/e2e/checkout.spec.ts
test('user can complete checkout', async ({ page }) => {
  await page.goto('/products')
  await page.click('[data-testid="add-to-cart"]')
  await page.click('[data-testid="checkout"]')
  await page.fill('[name="email"]', 'test@example.com')
  await page.click('[data-testid="place-order"]')
  await expect(page.locator('.order-confirmation')).toBeVisible()
})
```

### Test Organization

```
tests/
├── unit/                  # Fast, isolated tests
│   ├── test_auth.py
│   ├── test_agents.py
│   └── test_utils.py
├── integration/           # API, database tests
│   ├── test_api.py
│   ├── test_wordpress.py
│   └── test_woocommerce.py
├── e2e/                   # End-to-end tests
│   ├── checkout.spec.ts
│   └── admin.spec.ts
└── conftest.py            # Pytest fixtures
```

### Running Tests

**Python Tests:**
```bash
# Run all tests
pytest -v

# Run specific test file
pytest tests/unit/test_auth.py -v

# Run specific test function
pytest tests/unit/test_auth.py::test_jwt_token_generation -v

# Run with coverage
pytest --cov=core --cov=agents --cov-report=html

# Run integration tests only
pytest tests/integration/ -v

# Run tests matching pattern
pytest -k "auth" -v
```

**JavaScript Tests:**
```bash
# Run all tests
npm test

# Run in watch mode (TDD)
npm run test:watch

# Run with coverage
npm run test:coverage

# Run specific test file
npm test -- src/__tests__/auth.test.ts

# Run collection tests
npm run test:collections
```

### Coverage Requirements

**Minimum Coverage: 80%**

| Module | Minimum Coverage | Notes |
|--------|-----------------|-------|
| Core modules | 90%+ | Auth, security, database |
| Agents | 85%+ | SuperAgents, orchestration |
| API endpoints | 90%+ | All endpoints covered |
| Services | 80%+ | Business logic |
| Utils | 85%+ | Helper functions |
| UI components | 70%+ | React components |

**Check Coverage:**
```bash
# Python
pytest --cov --cov-report=term-missing
pytest --cov --cov-report=html  # Open htmlcov/index.html

# JavaScript
npm run test:coverage  # Open coverage/lcov-report/index.html
```

---

## Code Quality Standards

### Python Code Quality

**Tools:**
- **Black**: Code formatter (line length: 100)
- **Ruff**: Fast linter (replaces flake8, isort)
- **MyPy**: Static type checker
- **isort**: Import sorter

**Configuration:**
```bash
# Format code
black .

# Sort imports
isort .

# Lint and fix
ruff check --fix .

# Type check
mypy . --ignore-missing-imports
```

**Code Style:**
```python
# Good: Type hints, docstrings, error handling
async def process_order(
    order_id: str,
    *,
    correlation_id: str | None = None
) -> OrderResult:
    """
    Process an order with the given order ID.

    Args:
        order_id: Unique order identifier
        correlation_id: Optional correlation ID for tracing

    Returns:
        OrderResult containing processing status and details

    Raises:
        OrderNotFoundError: If order doesn't exist
        PaymentFailedError: If payment processing fails
    """
    try:
        order = await get_order(order_id)
        return await process_payment(order, correlation_id=correlation_id)
    except Exception as e:
        raise OrderProcessingError(f"Failed to process order: {order_id}") from e
```

**File Organization:**
- 200-400 lines typical
- 800 lines maximum
- High cohesion, low coupling
- Organize by feature/domain

### TypeScript/JavaScript Code Quality

**Tools:**
- **Prettier**: Code formatter
- **ESLint**: Linter
- **TypeScript**: Type checker

**Configuration:**
```bash
# Lint and fix
npm run lint:fix

# Format code
npm run format

# Type check
npm run type-check
```

**Code Style:**
```typescript
// Good: Immutability, type safety, error handling
interface User {
  id: string
  name: string
  email: string
}

async function updateUser(
  userId: string,
  updates: Partial<User>
): Promise<User> {
  try {
    const user = await getUser(userId)

    // Immutable update (CRITICAL)
    return { ...user, ...updates }

    // WRONG: user.name = updates.name (mutation!)
  } catch (error) {
    throw new Error('Failed to update user', { cause: error })
  }
}
```

**Immutability (CRITICAL):**
```typescript
// WRONG - Mutation
user.name = "John"
items.push(newItem)
state.count++

// CORRECT - Immutable
const updatedUser = { ...user, name: "John" }
const updatedItems = [...items, newItem]
const updatedState = { ...state, count: state.count + 1 }
```

**Input Validation (Zod):**
```typescript
import { z } from 'zod'

const userSchema = z.object({
  email: z.string().email(),
  age: z.number().min(18),
  name: z.string().min(1)
})

function registerUser(data: unknown) {
  const validated = userSchema.parse(data) // Throws if invalid
  return createUser(validated)
}
```

### Quality Checklist

Before committing code:

- [ ] **Functions**: <50 lines each
- [ ] **Files**: <800 lines (ideally 200-400)
- [ ] **Nesting**: <4 levels deep
- [ ] **No `console.log`**: Remove debug statements
- [ ] **No hardcoded values**: Use environment variables/config
- [ ] **Immutable patterns**: No direct mutations
- [ ] **Type hints**: All functions typed (Python & TypeScript)
- [ ] **Docstrings**: All public functions documented
- [ ] **Error handling**: Try/catch with user-friendly messages
- [ ] **Tests**: 80%+ coverage
- [ ] **Linting**: No linting errors
- [ ] **Formatting**: Code formatted (Black/Prettier)

---

## WordPress Theme Development

### Theme Structure

The production WordPress theme is **skyyrose-flagship** (located at `wordpress-theme/skyyrose-flagship/`).

**Important:** There is NO `skyyrose-2025` theme. All references should use `skyyrose-flagship`.

### Required Reading

Before working on WordPress theme, review these files:

1. **wordpress-theme/skyyrose-flagship/style.css** - Theme header (version, requirements)
2. **wordpress-theme/skyyrose-flagship/functions.php** - Bootstrap and inc/ loader
3. **wordpress-theme/skyyrose-flagship/inc/** - Backend modules (enqueue, security, woocommerce, etc.)
4. **docs/ARCHITECTURE.md** - WordPress Theme Architecture section

### Development Workflow

1. **Local Development Setup**
   ```bash
   # Using WordPress.com Local
   cd wordpress-theme/skyyrose-flagship

   # Or using wp-env (Docker-based)
   npm run wp-env start
   ```

2. **Install Dependencies**
   ```bash
   npm install  # Node.js dependencies for build tools
   ```

3. **Make Changes**
   - Edit PHP templates in `wordpress-theme/skyyrose-flagship/`
   - Edit CSS in `wordpress-theme/skyyrose-flagship/assets/css/`
   - Edit JavaScript in `wordpress-theme/skyyrose-flagship/assets/js/`
   - Backend modules in `wordpress-theme/skyyrose-flagship/inc/`
   - Elementor widgets in `wordpress-theme/skyyrose-flagship/elementor/widgets/`
   - WooCommerce templates in `wordpress-theme/skyyrose-flagship/woocommerce/`

4. **Test Changes**
   ```bash
   # Run PHP linting
   composer run-script phpcs

   # Run JavaScript linting
   npm run lint

   # Manual testing in browser
   open http://localhost:8882
   ```

5. **Package Theme**
   ```bash
   # Create deployment package
   cd wordpress-theme/skyyrose-flagship
   zip -r skyyrose-flagship-deploy.zip . \
     -x "*.git*" \
     -x "*.DS_Store" \
     -x "node_modules/*" \
     -x "*.log"
   ```

### WordPress.com Deployment

1. **Create Deployment Package**
   ```bash
   cd wordpress-theme/skyyrose-flagship
   zip -r ../skyyrose-flagship-$(date +%Y%m%d-%H%M%S).zip . \
     -x "*.git*" -x "*.DS_Store" -x "node_modules/*"
   ```

2. **Upload to WordPress.com**
   - Go to WordPress.com > Themes
   - Click "Upload Theme"
   - Select ZIP file
   - **IMPORTANT**: Choose "Replace current with uploaded" (not "Activate as new theme")

3. **Post-Deployment**
   - Clear cache: WordPress.com > Settings > Performance > Clear Cache
   - Wait 60 seconds for cache propagation
   - Test site: https://skyyrose.co
   - Verify 3D models load correctly
   - Check console for errors (should be <10)

### Theme Features (v3.2.0)

- **4 Collections**: Black Rose, Love Hurts, Signature, Kids Capsule
- **3 Immersive Scenes**: Gothic cathedral, romantic castle, Oakland/SF city tour
- **Pre-order Gateway**: Integrated pre-order checkout flow
- **WooCommerce Compatible**: Full template overrides (archive, single, cart, checkout)
- **Elementor Widget**: Three.js 3D viewer
- **Luxury UX**: Custom cursor, cinematic mode, wishlist, toast notifications
- **Design System**: Inter + Playfair Display fonts, dark luxury palette
- **Responsive Design**: Mobile-first approach
- **Performance Optimized**: Lazy loading, deferred scripts
- **Accessibility Ready**: WCAG compliant (accessibility-seo.php module)
- **Security Enhanced**: CSP headers, nonce helpers (security.php module)

### Common Theme Tasks

**Add New Elementor Widget:**
```php
// elementor/widgets/my-widget.php
// See existing: elementor/widgets/three-viewer.php
```

**Add Custom WooCommerce Template:**
```php
// woocommerce/single-product.php (override WooCommerce default)
// Copy from WooCommerce plugin and customize
```

**Add New Collection Catalog Page:**
```php
// Create template-collection-{name}.php at theme root
// Follow pattern in template-collection-black-rose.php
```

---

## Architecture Guidelines

### Dependency Flow (One-Way, No Cycles)

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

**Rules:**
- Core modules have NO dependencies on outer layers
- Agents use `adk/` base classes (not `agents/base_legacy.py`)
- Security uses `core.auth` types and interfaces
- Services depend on core, security, agents (never the reverse)

### Codebase Structure

```
DevSkyy/
├── main_enterprise.py        # FastAPI entry point (47+ endpoints)
├── devskyy_mcp.py            # MCP server (13 tools)
├── core/
│   ├── auth/                 # Auth types, models, interfaces (zero deps)
│   └── registry/             # Service registry (dependency injection)
├── agents/
│   ├── base_super_agent.py   # Enhanced base (17 techniques, ADK-based)
│   ├── base_legacy.py        # Legacy (deprecated, use ADK)
│   └── operations_legacy.py  # Legacy (deprecated)
├── adk/                      # Agent Development Kit (symlink to sdk/python/adk)
├── llm/                      # 6 providers, router, round_table
├── security/                 # AES-256-GCM, JWT, audit_log (uses core.auth)
├── api/v1/                   # REST, GDPR, webhooks
├── wordpress-theme/          # SkyyRose WordPress theme
│   └── skyyrose-flagship/    # Main theme directory
├── frontend/
│   ├── components/3d/        # LuxuryProductViewer (React Three Fiber)
│   └── lib/animations/       # luxury-transitions.ts (Framer Motion)
├── services/
│   └── ai_image_enhancement.py  # AI image processing (FLUX, SD3, RemBG)
└── tests/
    ├── unit/                 # Unit tests
    ├── integration/          # Integration tests
    └── e2e/                  # End-to-end tests
```

### Key Patterns

**Error Handling:**
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

**Async Functions with Correlation IDs:**
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

**Pydantic Models:**
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

---

## Available Tools & Skills

### MCP Tools (DevSkyy)

| Tool | Purpose | Example |
|------|---------|---------|
| `agent_orchestrator` | Invoke SuperAgents | Multi-agent consensus |
| `rag_query` | Query RAG pipeline | Knowledge retrieval |
| `rag_ingest` | Ingest documents | Document processing |
| `brand_context` | SkyyRose DNA | Brand guidelines |
| `product_search` | Search products | Product discovery |
| `order_management` | Manage orders | Order operations |
| `wordpress_sync` | Sync to WordPress | WP/WooCommerce integration |
| `3d_generate` | Generate 3D models | 3D asset creation |
| `analytics_query` | Query metrics | Analytics data |
| `cache_ops` | Cache management | Cache operations |
| `health_check` | System health | Health monitoring |
| `tool_catalog` | List available tools | Tool discovery |
| `llm_route` | Route LLM requests | LLM selection |

### Skills (Available via Skill Tool)

**Development Skills:**
- `agent-builder` - Create new AI agents
- `api-endpoint-generator` - Generate FastAPI endpoints
- `database-migration` - Create Alembic migrations
- `3d-generation` - 3D model generation

**Operations Skills:**
- `deploy` - Production deployment
- `wordpress-ops` - WordPress/WooCommerce operations
- `mcp-health` - MCP server diagnostics
- `incident-response` - Production incident response

**Quality Skills:**
- `code-review` - Code analysis
- `security-hardening` - Security audit
- `performance-audit` - Performance optimization
- `tdd-workflow` - Test-driven development

**Documentation Skills:**
- `update-docs` - Update documentation
- `ralph-tui-prd` - Generate PRDs

### Agent Support

**Specialized Agents (Use with Task Tool):**
- `planner` - Implementation planning for complex features
- `architect` - System design and architectural decisions
- `tdd-guide` - Test-driven development enforcer
- `code-reviewer` - Code review for quality/security
- `security-reviewer` - Security vulnerability detection
- `build-error-resolver` - Fix build/type errors
- `e2e-runner` - Playwright E2E testing
- `refactor-cleaner` - Dead code cleanup
- `doc-updater` - Documentation generation

**Usage Example:**
```python
# Use planner agent for complex features
# Before starting implementation
Task(
    subagent_type="planner",
    prompt="Plan implementation for multi-agent orchestration system",
    description="Create implementation plan"
)

# Use code-reviewer agent after writing code
Task(
    subagent_type="code-reviewer",
    prompt="Review auth module for security and quality",
    description="Code review"
)
```

---

## Troubleshooting

### Common Issues

**Database Connection Failed**
```bash
# Check DATABASE_URL format
echo $DATABASE_URL

# PostgreSQL format:
# postgresql+asyncpg://user:password@host:port/database

# SQLite format:
# sqlite+aiosqlite:///./path/to/db.db

# Test connection
python -c "from sqlalchemy import create_engine; import os; e = create_engine(os.getenv('DATABASE_URL')); e.connect()"
```

**Import Errors**
```bash
# Reinstall in editable mode
pip install -e ".[all]"

# Verify installation
python -c "import core, agents, security, api"
```

**Tests Failing**
```bash
# Clear pytest cache
pytest --cache-clear

# Reinstall test dependencies
pip install -e ".[dev]"

# Run single test with verbose output
pytest tests/test_auth.py::test_jwt -vv
```

**Type Check Errors**
```bash
# Check mypy configuration
cat pyproject.toml | grep -A 20 "\[tool.mypy\]"

# Ignore third-party errors
mypy . --ignore-missing-imports
```

**WordPress Theme Not Loading**
```bash
# Check theme is activated
wp theme list

# Check for PHP errors
tail -f /path/to/wordpress/wp-content/debug.log

# Verify file permissions
chmod -R 755 wordpress-theme/skyyrose-flagship
```

**Theme Assets Not Loading**
```bash
# Check CSP headers
curl -I https://skyyrose.co | grep -i content-security-policy

# Check theme stylesheet
curl -I https://skyyrose.co/wp-content/themes/skyyrose-flagship/style.css

# Check browser console for errors
# Should be <10 errors after deployment
```

### Getting Help

**Resources:**
- **GitHub Issues**: https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/issues
- **Documentation**: `/docs` directory
- **CLAUDE.md**: Project-specific instructions
- **Skills**: Use `/help` in Claude Code CLI

**Support Contacts:**
- **Platform Team**: support@devskyy.com
- **Security Issues**: security@devskyy.com

---

## Quick Reference

### Daily Development Commands

```bash
# Start development environment
source .venv/bin/activate        # Activate virtual environment
uvicorn main_enterprise:app --reload  # Start backend
npm run dev                       # Start frontend (separate terminal)

# Run tests (before each commit)
pytest -v                         # Python tests
npm test                          # JavaScript tests

# Format code
isort . && ruff check --fix . && black .  # Python
npm run lint:fix && npm run format        # JavaScript

# Type check
mypy . --ignore-missing-imports   # Python
npm run type-check                # TypeScript
```

### Pre-Commit Checklist

- [ ] Code formatted (Black/Prettier)
- [ ] Imports sorted (isort)
- [ ] Linting passed (Ruff/ESLint)
- [ ] Type check passed (MyPy/tsc)
- [ ] Tests passed (pytest/jest)
- [ ] Coverage ≥80%
- [ ] No `console.log` or debug statements
- [ ] Environment variables used (no hardcoded values)
- [ ] Documentation updated

### NPM Scripts Quick Reference (28 scripts, from package.json)

See [SCRIPTS_REFERENCE.md](SCRIPTS_REFERENCE.md) for complete documentation.

| Category | Script | Purpose |
|----------|--------|---------|
| **Development** | `npm run dev` | Start dev server with hot reload (nodemon + ts-node) |
| | `npm run build` | Compile TypeScript (`tsc --project config/typescript/tsconfig.json`) |
| | `npm run build:watch` | Compile TypeScript in watch mode |
| | `npm run start` | Run compiled production build (`node dist/index.js`) |
| **Testing** | `npm test` | Run all tests (`jest --config config/testing/jest.config.cjs`) |
| | `npm run test:watch` | TDD watch mode |
| | `npm run test:coverage` | Tests with coverage report |
| | `npm run test:ci` | CI mode (coverage, no watch) |
| | `npm run test:collections` | Test 3D collection components only |
| **Quality** | `npm run lint` | Check linting errors (ESLint) |
| | `npm run lint:fix` | Auto-fix linting errors |
| | `npm run format` | Format code (Prettier) |
| | `npm run format:check` | Verify formatting |
| | `npm run type-check` | TypeScript type checking (`tsc --noEmit`) |
| **Pre-commit** | `npm run precommit` | Run lint + type-check + test:ci |
| **Demos** | `npm run demo:collections` | List available 3D demos |
| | `npm run demo:black-rose` | Gothic rose garden 3D experience |
| | `npm run demo:signature` | Luxury outdoor 3D experience |
| | `npm run demo:love-hurts` | Gothic castle 3D experience |
| | `npm run demo:showroom` | Virtual showroom 3D experience |
| | `npm run demo:runway` | Fashion runway 3D experience |
| **Maintenance** | `npm run clean` | Remove dist/ and coverage/ |
| | `npm run prepare` | Auto-build after npm install |
| | `npm run security:audit` | Check for security vulnerabilities |
| | `npm run security:fix` | Auto-fix security vulnerabilities |
| | `npm run deps:update` | Update dependencies |
| | `npm run deps:check` | Check for outdated packages |

### Environment Variables Quick Reference (from .env.example)

See [ENV_VARS_REFERENCE.md](ENV_VARS_REFERENCE.md) for complete documentation.

| Category | Variable | Required | Purpose |
|----------|----------|----------|---------|
| **Security** | `JWT_SECRET_KEY` | Production | JWT signing (64+ chars, generate with script) |
| | `ENCRYPTION_MASTER_KEY` | Production | AES-256-GCM encryption (base64 32-byte key) |
| **Database** | `DATABASE_URL` | Yes | DB connection (SQLite dev, PostgreSQL prod) |
| **AI/ML** | `OPENAI_API_KEY` | 1 required | OpenAI provider |
| | `ANTHROPIC_API_KEY` | 1 required | Anthropic provider |
| | `GOOGLE_AI_API_KEY` | Optional | Google AI provider |
| **Payments** | `STRIPE_API_KEY` | E-commerce | Stripe secret key |
| | `STRIPE_WEBHOOK_SECRET` | E-commerce | Stripe webhook verification |
| **WordPress** | `WORDPRESS_URL` | WP features | WordPress site URL |
| | `WOOCOMMERCE_KEY` | WP features | WooCommerce API key |
| **3D Pipeline** | `HF_TOKEN` | 3D features | HuggingFace token |
| | `TRIPO_API_KEY` | 3D fallback | Tripo3D API key |
| | `FASHN_API_KEY` | Try-on | FASHN virtual try-on |
| **Infra** | `REDIS_URL` | Optional | Redis caching |
| | `SENTRY_DSN` | Optional | Error tracking |
| | `CORS_ORIGINS` | Production | Allowed CORS origins |

---

**Document Owner**: DevSkyy Platform Team
**Next Review**: When workflow or tools change
**Last Updated**: 2026-02-22

---

## Additional Resources

- **RUNBOOK.md** - Production deployment and operations
- **ENV_VARS_REFERENCE.md** - Complete environment variable reference
- **SCRIPTS_REFERENCE.md** - NPM scripts documentation
- **CLAUDE.md** - Project-specific Claude Code instructions
- **.claude/rules/** - Coding standards, testing, git workflow, etc.
- **WordPress Theme** - wordpress-theme/skyyrose-flagship/ (see style.css, functions.php)

Welcome to the team! Happy coding! 🚀
