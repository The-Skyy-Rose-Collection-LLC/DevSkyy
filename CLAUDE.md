# DevSkyy — Claude Config

> Enterprise AI | SkyyRose Luxury Fashion | 54 Agents | **Self-Correcting System**

---

## Protocol (Do This Every Time)

1. **Context7** → `resolve-library-id` → `query-docs` (BEFORE library code)
2. **Serena** → Codebase navigation and symbol lookup
3. **Navigate** → Read first, understand, NO code until clear
4. **Implement** → `Edit` tool (targeted) | `Write` (new only)
5. **Test** → `pytest -v` (MANDATORY after EVERY file touch)
6. **Format** → `isort . && ruff check --fix && black .`
7. **Learn** → After any correction, update this CLAUDE.md ⭐

---

## Verification Commands (Run After Changes)

```bash
# Python
pytest -v && mypy . --ignore-missing-imports && ruff check

# JavaScript
npm test && npm run type-check && npm run lint

# WordPress
wp theme list && curl -I https://skyyrose.co | grep -i content-security-policy

# Full System
pytest -v && npm test && curl http://localhost:8000/health
```

---

## Learnings (Updated Weekly When Claude Makes Mistakes) ⭐

### WordPress

- ❌ **Mistake**: Using `/wp-json/` for WordPress.com API
  - ✅ **Correct**: Use `index.php?rest_route=` instead (WordPress.com requirement)

- ❌ **Mistake**: Assuming page purpose from name
  - ✅ **Correct**: ALWAYS read `wordpress-theme/skyyrose-flagship/PAGES-DOCUMENTATION.md` first

- ❌ **Mistake**: Thinking immersive pages = product catalog
  - ✅ **Correct**: Immersive = 3D storytelling (NOT shopping), Catalog = product grids (FOR shopping)

- ❌ **Mistake**: Editing WordPress files without Serena
  - ✅ **Correct**: Use Serena MCP tools for all WordPress file operations

- ❌ **Mistake**: Referencing skyyrose-2025 theme
  - ✅ **Correct**: Only `skyyrose-flagship` exists (production theme)

### Testing

- ❌ **Mistake**: Skipping tests "just this once"
  - ✅ **Correct**: `pytest -v` after EVERY file touch, no exceptions

- ❌ **Mistake**: Coverage <80%
  - ✅ **Correct**: 90%+ coverage required (use `pytest --cov`)

- ❌ **Mistake**: Writing implementation before tests
  - ✅ **Correct**: TDD workflow: RED (write failing test) → GREEN (minimal impl) → IMPROVE (refactor)

### Architecture

- ❌ **Mistake**: Circular dependencies (api imports core, core imports api)
  - ✅ **Correct**: One-way flow only: `core → adk → security → agents → api`

- ❌ **Mistake**: Using `base_legacy.py` or `operations_legacy.py`
  - ✅ **Correct**: Use `adk/base_super_agent.py` (17 techniques, ADK-based)

- ❌ **Mistake**: Importing from outer layers into inner layers
  - ✅ **Correct**: Inner layers (core, adk) have ZERO dependencies on outer layers

### 3D Development

- ❌ **Mistake**: Using CDN URLs without verification
  - ✅ **Correct**: VERIFY URLs exist first (`curl -I <url>`)

- ❌ **Mistake**: Forgetting to propagate correlation_id
  - ✅ **Correct**: ALWAYS accept `correlation_id` as keyword-only arg and propagate

- ❌ **Mistake**: Hardcoding 3D library versions
  - ✅ **Correct**: Three.js v0.160.0, Babylon.js latest (via CDN)

### Google ADK

- ❌ **Mistake**: Using hyphens in `LlmAgent(name=...)`
  - ✅ **Correct**: Agent names must be valid Python identifiers — use underscores: `skyyrose_content_director`

- ❌ **Mistake**: Asking agent to process a whole collection in one turn
  - ✅ **Correct**: Loop product-by-product with `time.sleep(8)` between calls to avoid 429 rate limits

- ❌ **Mistake**: Writing audit prompts without read-only guard
  - ✅ **Correct**: Prepend `"READ-ONLY AUDIT — do NOT call update_product_field()."` to any audit prompt

- ❌ **Mistake**: Loading multiple `.env` files with `override=False` when one has a placeholder key
  - ✅ **Correct**: Load the authoritative keys file LAST with `override=True` so real keys win

- ❌ **Mistake**: Calling `runner.run()` without pre-creating session
  - ✅ **Correct**: Always call `session_svc.create_session_sync()` before `runner.run()`

- ❌ **Mistake**: Installing ADK deps into the image pipeline venv
  - ✅ **Correct**: Use isolated `.venv-agents/` — ADK drags cloud deps that conflict with `numpy==2.3.5`

### Context7

- ❌ **Mistake**: Writing library code before checking docs
  - ✅ **Correct**: ALWAYS `resolve-library-id` → `query-docs` first

- ❌ **Mistake**: Assuming WordPress/Elementor/WooCommerce APIs haven't changed
  - ✅ **Correct**: Query Context7 for up-to-date docs every time

### Code Quality

- ❌ **Mistake**: Mutating objects directly
  - ✅ **Correct**: Immutability always (use spread: `{...obj, newKey}` not `obj.key = val`)

- ❌ **Mistake**: Using `console.log` or debug statements
  - ✅ **Correct**: Remove all debug output before committing

- ❌ **Mistake**: Hardcoding values (API keys, URLs)
  - ✅ **Correct**: Use environment variables (see `docs/ENV_VARS_REFERENCE.md`)

---

## Critical Rules (Never Break These)

- **NO deletions**, refactor only (preserve git history)
- **Context7 BEFORE any library code** (WordPress, Elementor, WooCommerce, Three.js)
- **Serena for WordPress** file operations (NOT direct file access)
- **pytest AFTER EVERY CHANGE** (no exceptions)
- **90%+ coverage** required (use `pytest --cov`)
- **Update CLAUDE.md** after every correction (self-correcting system)

---

## Quick Reference

### Brand & Health
- **Brand**: `#B76E79` (rose gold) | "Where Love Meets Luxury" | `BrandKit.from_config()`
- **Health**: `/health` `/health/ready` `/health/live` `/metrics`

### Collections & Docs
- **Immersive** (3D): Black Rose (cathedral), Love Hurts (castle), Signature (city tour)
- **Catalog** (shopping): `page-collection-{black-rose,love-hurts,signature}.php`
- **Docs**: `docs/` → CONTRIB, RUNBOOK, ENV_VARS_REFERENCE, MCP_TOOLS, DEPENDENCIES, ARCHITECTURE

---

## When Claude Does Something Wrong

**Self-Correcting Protocol** (Boris Cherny's approach):

1. **Fix the issue** (correct the code, tests, docs)
2. **Add to Learnings** (update this file with ❌ Mistake → ✅ Correct)
3. **Commit both** (code fix + CLAUDE.md update together)
4. **Update multiple times weekly** (living document, not static)

This transforms our codebase into a **self-correcting organism** where mistakes become rules.

---

**v3.1.0** | SkyyRose LLC | Self-Correcting AI System
