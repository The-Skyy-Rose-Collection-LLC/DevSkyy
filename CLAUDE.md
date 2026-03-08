# DevSkyy — Claude Config

> SkyyRose Luxury Fashion | Self-Correcting System

## Protocol

1. **Context7** → `resolve-library-id` → `query-docs` BEFORE any library code
2. **Serena** → Codebase navigation, symbol lookup, WordPress file ops
3. Read first, understand, then `Edit` (targeted) or `Write` (new only)
4. `pytest -v` after EVERY change — 90%+ coverage (`pytest --cov`)
5. Format: `isort . && ruff check --fix && black .`
6. After corrections → add Learnings entry below

## Verify

```bash
cd /Users/theceo/DevSkyy && pytest tests/ -v && mypy . --ignore-missing-imports && ruff check
npm run type-check && npm run lint
curl -I https://skyyrose.co | grep -i content-security-policy
```

## Critical Rules

- Context7 BEFORE any library code (WordPress, Three.js, WooCommerce)
- Serena for WordPress file ops (not direct access)
- TDD: RED → GREEN → IMPROVE
- No deletions — refactor only (preserve git history)
- Immutability: `{...obj, key}` not `obj.key = val`
- No console.log, no hardcoded secrets — use env vars
- Files <800 lines, functions <50 lines
- Deps flow one-way: `core → adk → security → agents → api`
- Generic errors to clients, detailed logs server-side only
- Validate inputs with Zod at system boundaries
- Git: `<type>: <description>` (feat, fix, refactor, docs, test, chore)

## Agents

Use parallel Task execution for independent ops.

| Agent | When |
|-------|------|
| planner | Complex features |
| tdd-guide | New features, bug fixes |
| code-reviewer | After writing code |
| security-reviewer | Before commits |
| build-error-resolver | Build failures |

## Learnings

### WordPress
- API: `index.php?rest_route=` NOT `/wp-json/`
- Read templates before assuming purpose; Immersive = 3D storytelling, Catalog = product grids
- Only `skyyrose-flagship` theme exists

### Security
- Validate backend URLs against allowlist; block `169.254.x.x`, `file://`, `gopher://`
- Cap in-memory tracking with LRU eviction (`OrderedDict.popitem(last=False)`)
- Whitelist config keys before `**unpacking`

### Architecture
- Use `adk/base_super_agent.py` (not legacy files)
- DataLoaders → `api/graphql/dataloaders/` (not `core/`)
- `strawberry.argument()`: only `description`, `name`, `deprecation_reason`
- Use `schema.execute()` for GraphQL unit tests

### Mocking
- Import deps at module level so `patch("module.Class")` works
- Fixed in: `core/cqrs/command_bus.py`, `grpc_server/product_service.py`

### Google ADK
- Agent names: underscores only (valid Python identifiers)
- Loop per-product with `time.sleep(8)` to avoid 429s
- Prepend `"READ-ONLY AUDIT"` to audit prompts
- Load authoritative keys LAST with `override=True`
- `session_svc.create_session_sync()` before `runner.run()`
- Use `.venv-agents/` (ADK conflicts with numpy)

### Vercel
- `rootDirectory` set → reads that dir's `vercel.json`, not root
- Use npm not pnpm (ERR_INVALID_THIS on Node 22+)

### Hooks
- macOS: canonicalize paths (`/tmp` → `/private/tmp`)
- Use `${VAR:-default}` for testable paths
- Reject flag-like targets: `case "$target" in -*) exit 0 ;; esac`

### Cache
- `cache_invalidate` and main key must use same hash length (fixed `multi_tier_cache.py:295`)
- Integration tests → `tests/integration/` (not `tests/api/`)

## Brand

- Colors: `#B76E79` rose gold, `#0A0A0A` dark, `#C0C0C0` silver, `#DC143C` crimson, `#D4AF37` gold
- Tagline: "Luxury Grows from Concrete."
- Immersive (3D): Black Rose, Love Hurts, Signature
- Catalog: `template-collection-{black-rose,love-hurts,signature,kids-capsule}.php`
- Health: `/health` `/health/ready` `/health/live` `/metrics`
- Arch maps: `docs/ARCHITECTURE.md`

## Self-Correction

1. Fix the issue → 2. Add Learnings entry → 3. Commit both together
