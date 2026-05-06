# DevSkyy — Scripts, Tests & Entry Points Digest

> Generated: 2026-05-05 | Branch: feat/v2-phase-0-5
> Scope: scripts/, tests/e2e-wp/, tests/integration/, conftest.py, main_enterprise.py, devskyy_mcp.py

---

## 1. Top-Level Entry Points

### `main_enterprise.py` (400 lines)

FastAPI application. Startup sequence via `@asynccontextmanager lifespan`:
1. Configure logging
2. Initialize Sentry DSN
3. `db_manager.initialize()` — database pool
4. OpenTelemetry tracing setup
5. On shutdown: `db_manager.close()` → `close_checkpointer()`

**Routers:** 30+ prefixed at `/api/v1` and `/api/v2` (agents, products, analytics, auth, events, 3d, search, collections, websocket, billing, tenant, graphql, etc.)

**Middleware LIFO registration order** (last registered → runs first):
```
security_headers → rate_limit → timing → correlation_id → billing → tenant
```
`tenant` registered last → executes first, wrapping `billing`. This is intentional: tenant resolution must precede billing decisions.

**CORS origins allowed:** `localhost:3000`, `localhost:8000`, `skyyrose.co`, `devskyy.vercel.app`, `*.vercel.app`, `*.devskyy.app`

**Docs disabled in production** (`ENVIRONMENT != "development"`).

**CQRS patterns:** `ProductEventHandler` with `event_store.Event`. GraphQL layer uses `MultiTierCache` (L1 TTLCache + L2) and DataLoader for N+1 prevention.

---

### `devskyy_mcp.py` (79 lines)

Thin entry point only. Pattern:
```python
from mcp_tools import mcp
# reads DEVSKYY_API_KEY — warns if missing, does not abort
mcp.run()  # stdio transport, 21 tools in banner
```
All tool implementations live in the `mcp_tools/` package. Never add logic here.

---

### `conftest.py` (56 lines)

Adds `PROJECT_ROOT` and `sdk/python` to `sys.path`. No fixtures.

**Critical conditional exclusion:** If `import wordpress` fails, pytest ignores 30+ test globs:
```
tests/api/**, tests/orchestration/**, tests/wordpress/**,
tests/services/test_three_d*, tests/services/test_search*,
tests/integration/test_woocommerce*, ...
```
This is a deliberate short-circuit while the `wordpress` module is being rebuilt. Running the test suite without the module installed will silently skip most of the surface area.

---

## 2. Deploy Pipeline

### `scripts/deploy-theme.sh` (705 lines) — primary deploy script

**Hot-swap atomic deploy** (default since 2026-04-11):
```bash
# Remote sequence
mv "$LIVE_PATH" "${LIVE_PATH}.old.${SWAP_ID}"   # microsecond gap
mv "$STAGE_PATH" "$LIVE_PATH"                     # goes live
```
Old maintenance-mode pattern (60s window) is replaced. Pass `--with-maintenance` only for DB migrations.

**Phase timing** (bash 3.2 compatible — no associative arrays):
```bash
printf -v "PHASE_STARTED_$1" '%s' "$(date +%s)"
local -n _started="PHASE_STARTED_$1"   # indirect reference via ${!var}
```

**Concurrency lock** (PID + noclobber):
```bash
(set -o noclobber; echo "$$" > "$DEPLOY_LOCK_FILE") 2>/dev/null
# stale PID reclaimed via kill -0 check
```

**Compression:** zstd if available, else uncompressed tar. The archive excludes `node_modules`, `.git`, `*.log`.

**Credential hygiene:** `SSHPASS` env var set just-in-time, unset immediately after scp.

**Auto-rollback:** if `verify_live()` fails, restores `.old.$SWAP_ID`:
```bash
mv "$LIVE_PATH" "${LIVE_PATH}.failed.$SWAP_ID"
mv "${LIVE_PATH}.old.${SWAP_ID}" "$LIVE_PATH"
```

**Backup retention:** keeps 2 most recent `.old.*` backups:
```bash
ls -1dt "${LIVE_PATH}.old."* | tail -n +3 | xargs rm -rf
```

**Verify gate (`verify_live()`):** curl with cache-buster `?deploy_verify=$ts`, asserts:
- HTTP 200
- Response size ≥ 50 KB
- Absence of PHP error strings: `Fatal error`, `Parse error`, `Call to undefined`, `There has been a critical error`

Override target via `PUBLIC_URL` env var.

---

### `scripts/deploy-pipeline.sh` (178 lines) — 3-step orchestrator

```
npm build → deploy-theme.sh → verify-deploy.sh
```
`--dry-run`: build runs, deploy shows manifest only, verify is skipped.

---

### `scripts/verify-deploy.sh` (218 lines) — post-deploy health checks

11 checks as `"name|path|content_marker"` pipe-separated array. curl with `--retry 2`, cache-buster. Collects all failures (not fail-fast). Controlled by `WORDPRESS_URL` env var.

---

### `scripts/theme-build.sh` (538 lines) — asset build pipeline

7-step pipeline:
1. **clean** — removes dist/
2. **css** — delegates to `build-css.js`
3. **js** — webpack if `webpack.config.js` present, else terser fallback
4. **php-lint** — delegates to `php-lint.sh`
5. **js-lint** — eslint
6. **verify** — sanity checks on outputs
7. **manifest** — JSON with per-file md5 (8 chars) + sizes

Modes: `full | css | js | lint | verify | manifest | clean | watch | production`

`production` mode strips source maps. macOS uses `md5 -q` with `md5sum` fallback.

---

## 3. Measurement Scripts

### `scripts/measurement/verify-all-grants.js` — sequential dispatcher

Runs 6 verifiers in order. Exit code policy:
- All PASS → 0
- Any FAIL → 1
- Some SKIP (missing env) → 2

---

### `scripts/measurement/verify-google-service-account.js`

JWT token issuance only — cheapest verifier, always run first. Uses `createJwtClient()` from `_lib/google-jwt.js`.

---

### `scripts/measurement/verify-ga4.js`

**GOTCHA:** Property format must be `"properties/12345678"` (numeric), NOT `"G-XXXXXX"` (tracking ID). The GA4 Data API rejects the `G-` format.

---

### `scripts/measurement/verify-gsc.js`

`searchAnalytics/query`, 28-day range. `siteUrl` must be URL-encoded in the request path.

---

### `scripts/measurement/verify-gtm.js`

**GOTCHA:** `GTM_CONTAINER_ID` env var must be the **public slug** (`GTM-XXXX`), NOT the internal numeric container ID. The script fetches all containers under `GTM_ACCOUNT_ID`, finds the match by `publicId`, then uses `match.containerId` for API calls.

---

### `scripts/measurement/verify-meta.js`

Graph API v21.0 `debug_token`. Asserts: `is_valid=true`, `type` contains `SYSTEM_USER`, scopes ⊇ `{ads_read, business_management}`. Uses native `fetch` (no `google-auth-library`).

---

### `scripts/measurement/verify-sentry.js`

`GET sentry.io/api/0/organizations/{slug}/projects/`. Asserts both `skyyrose-co` and `devskyy-app` projects exist.

---

## 4. Generation Scripts (Nano Banana 2)

Package root: `scripts/nano_banana/`

### `cli.py` (764 lines) — 7 subcommands

| Subcommand | Purpose |
|---|---|
| `dry-run` | Validate catalog + routing, no generation |
| `generate` | Sync generation for 1 SKU |
| `generate-async` | Async generation for 1 SKU |
| `composite` | Run compositor agent on existing render |
| `verify-generate` | Generate then tournament-judge |
| `produce` | V4 legacy sequential multi-SKU |
| `produce-async` | Staged async multi-SKU (current default) |

Batch timeouts: 300s (single SKU), 600s (collection), 1800s (full catalog).

Logo/patch bundle refs excluded from prompts — confirmed deliberate: "they cause hallucinated text."

CLIP alignment scoring opt-in via `--clip` flag (lazy import to avoid 600MB model load).

---

### `config.py` (138 lines) — `PipelineConfig` dataclass

Two presets:
- `production()`: `max_attempts=3`, `qa_auto_approve=80`
- `fast()`: `max_attempts=1`, `prefer_cost_efficiency=True`, `qa_auto_approve=65`

Output dir hardcoded to WP theme assets: `wordpress-theme/skyyrose-flagship/assets/images/products/`

Rate limits: `gemini_rpm=10`, `openai_rpm=7`, `fal_rpm=10`

**Dead field:** `gpt_image_model` declared in `PipelineConfig` but never consumed by `router.py` or `generate.py`.

---

### `router.py` (241 lines) — model routing

`route_product(sku, view)` → `[primary_RouteDecision, fallback_RouteDecision]`

Routing logic by view content:
| Condition | Primary engine |
|---|---|
| branding view | Gemini Pro (material physics) |
| text/logos present | GPT Image 1.5 (96%+ text accuracy) |
| complex fabric | Gemini Pro |
| accessories / plain | FLUX 2 Pro |
| default | FLUX 2 Pro |

`estimate_batch_cost()` iterates products × views, sums primary engine costs.

---

### `generate.py` — per-provider generation functions

One clean function per provider: `generate_gemini()`, `generate_gpt_image()`, `generate_flux()`.

No retry logic inside — callers handle retries.

Gemini function signature:
```python
def generate_gemini(client, source_path, prompt, *, model=GEMINI_FAST,
                    aspect_ratio="3:4", enhanced=False, extra_refs=None) -> bytes | None
```
Returns WebP bytes on success, `None` on failure.

Model constants (from `llm/model_ids.py`):
- `GEMINI_FAST` = `gemini-2.5-flash-image` (NB1)
- `GEMINI_NB2` = `gemini-3.1-flash-image-preview` (NB2, with thinking)
- `GEMINI_PRO` = `gemini-3-pro-image-preview` (NB Pro, 4K)
- `GPT_IMAGE_MODEL` = `gpt-image-1.5`
- `FLUX_MODEL` = `black-forest-labs/FLUX.2-pro`

---

### `tournament.py` (3-judge architecture)

**Vision judges** (parallel): GPT-5.5-Pro + Gemini 3.1 Pro Preview — each scores 7 axes (0-100): `garment_type`, `color_accuracy`, `text_accuracy`, `logo_accuracy`, `construction_accuracy`, `no_hallucinations`, `overall`.

**Synthesis judge** (sequential after vision): Claude Opus 4.7 — text-only, reads vision reports + DNA spec, produces final verdict + rationale + hallucination veto. Intentionally NOT given images.

**Aggregate score rule:**
```
TournamentResult.aggregate_score = synthesis_overall  (when Opus ran)
                                  = vision_pair_mean  (fallback)
```
The `vision_pair_mean` is exposed on `TournamentResult` as a sanity check, not the canonical score.

**Error handling:** `_exception_repr()` guards against empty `TimeoutError.__str__()`. `SKIP_SUFFIXES` excludes failed judges from the vision mean calculation (no zero-averaging).

---

### `spec_builder.py` (157 lines) — dossier-first spec building

Three functions:
1. `build_judge_spec_from_dossier(dossier)` — verbatim multi-section spec (PRODUCT, GARMENT TYPE LOCK, BRANDING, NEGATIVE, SCENE)
2. `build_dna_from_sku(sku)` — hard-fails on missing dossier (`DossierMissingError` — no fallback allowed)
3. `augment_prompt_with_dossier_negatives(prompt, dossier)` — appends `dossier.negative_block` as `"DO NOT RENDER (authored canonical negatives)"`

Canonical dossier text is passed verbatim to tournament judges. The old Gemini-vision-inferred DNA path is retired.

---

### `catalog.py` (237 lines) — source image resolution

Source priority:
1. Bundle product photo
2. `source_map` techflat entry
3. CSV override
4. `source_map` webp entry
5. Glob fallback (excludes `-front-model`/`-back-model`/`-branding`/`-composite` suffixes)

`find_back_source()`: auto-crops right half when `width > height * 1.1` (2-panel techflat detection via PIL).

`load_specs()` reads `data/product-specs.json`.

---

## 5. Sync Scripts

### `scripts/sync_brand_to_php.py`

Reads `assets/brand/brand.yaml` → emits `inc/brand.generated.php` via `skyyrose.elite_studio.brand.BrandConfig`. The generated PHP file must not be edited by hand — it will be overwritten on next sync.

---

### `scripts/launch/sync_products.py`

Phase 2 WooCommerce REST API v3 sync via `httpx`. Paginated product fetch (100/page). Builds WooCommerce payload from CSV row including attributes (Size, Color), meta fields (`_skyyrose_preorder`, `_skyyrose_edition_size`), and image association via `scripts/launch/sku_image_map.json`.

**Hardcoded category IDs:**
```python
CATEGORY_MAP = {"signature": 19, "black-rose": 20, "love-hurts": 18}
```
Kids Capsule is created dynamically if absent (`ensure_kids_category()`).

`SITE_URL`, `WC_KEY`, `WC_SECRET` are overridable via env vars at runtime.

---

## 6. _lib Shared Utilities

### `scripts/_lib/script-utils.js`

Zero npm dependencies, ESM module.

- `PROJECT_ROOT` — resolved 2 levels up from `_lib/`
- `utcTimestamp()` — ISO 8601 UTC string
- `pathToSlug(filepath)` — file path → kebab slug
- `deriveTaskId(filepath)` — deterministic task ID from path
- `run(cmd)` — executes shell command, returns `{stdout, status}`

---

### `scripts/measurement/_lib/google-jwt.js`

- `createJwtClient(scope)` — parses `GOOGLE_SERVICE_ACCOUNT_JSON`, creates `new JWT({email, key, scopes})` from `google-auth-library`
- `readGaxiosError(err)` — normalizes gaxios errors to `{status, data}`

**GOTCHA:** Vercel often mangles multi-line JSON pastes for `GOOGLE_SERVICE_ACCOUNT_JSON`. The key value must be pasted as a single-line JSON string with escaped newlines (`\n`).

---

### `scripts/measurement/_lib/format.js`

Exit code constants: `EXIT_PASS=0`, `EXIT_FAIL=1`, `EXIT_MISSING_ENV=2`

TTY-aware color helpers: `pass()`, `fail()`, `missing()`, `requireEnv()`

`requireEnv(name)` — exits with `EXIT_MISSING_ENV` if env var absent.

---

## 7. Playwright Suite (`tests/e2e-wp/`)

**Status: Scaffold only — zero spec files written.**

Infrastructure present:
- `package.json`: `@playwright/test@1.59.1`, requires Node ≥ 18
- `playwright-report/index.html`: HTML reporter output from last run
- `test-results/.last-run.json`: last run metadata

No `*.spec.ts` or `*.spec.js` files exist. The suite is ready to accept specs but has none.

---

## 8. Integration Tests (`tests/integration/`)

Two test styles coexist (not all files are standard pytest):

### Standard pytest + asyncio

**`test_event_projections.py`** (180 lines)
- CQRS `ProductEventHandler` with event store
- Patches at `"database.db.DatabaseManager"` (not `"core.database..."`— the dot-path matters)
- Field whitelist rejects `hashed_password`
- Unknown event types are silently ignored (no exception)

**`test_graphql_cache.py`** (442 lines)
- **Bug test captured:** `test_cache_invalidate_uses_matching_key_length` — invalidation used `[:16]` while `set()` used `[:32]`, causing silent no-op cache invalidations
- DataLoader parallel aliases → single batch call (N+1 prevention verified)
- Same-second pagination requests → separate cache keys (timestamp included)

**`test_security_ops_agent.py`** (227 lines)
- `SecurityOpsAgent(repo_path)` — real-world tests gated by `--run-integration` flag
- `pip-audit` and `npm audit` are mocked in unit mode
- Tests Dependabot alert parsing

### Manual asyncio runners (not standard pytest)

**`test_api_endpoints.py`** (215 lines)
- `APITester` class with manual `asyncio.run()` entry
- Tests: `/health`, `/api/v1/agents`, round-table providers, WebSocket connections
- Graceful skip if `httpx` or `websockets` not installed

**`test_hybrid_integration.py`** (409 lines)
- Manual `asyncio.run()` entry
- Tests: SDK imports, FASHN worker stub (`status="failed"`, `stub=True`), Approach A backward compat, Approach C HTTP stubs

---

## 9. Conventions

### Python
- Every top-level package dir requires `__init__.py` (enforced by `mypy.ini`: `namespace_packages = False`)
- Line length: 100 chars (black + ruff + isort)
- Formatters: `isort . && ruff check --fix && black .`
- Type annotations on all function signatures
- `logging` module, never `print()` in non-CLI code

### Bash
- Phase timing via `printf -v "VAR_$1"` + `${!var}` indirection (bash 3.2, no associative arrays)
- Concurrency locks via `set -o noclobber` + PID file
- Homebrew PHP path explicit: `/opt/homebrew/bin/php` (macOS subshell PATH gotcha)
- Flag-like arguments rejected: `case "$arg" in -*) continue ;; esac`

### JavaScript
- ESM modules throughout `scripts/`
- Zero npm dependencies in `_lib/` utilities
- Exit codes: 0=PASS, 1=FAIL, 2=MISSING_ENV (verifier contract)

### Deploy
- Hot-swap atomic rename is the default (no maintenance mode)
- `PUBLIC_URL` env var overrides verify target
- Auto-rollback on verify failure
- Keep 2 most recent `.old.*` backups

### Nano Banana
- Output dir hardcoded to WP theme assets — do not pass arbitrary output paths
- Logo/patch refs excluded from generation prompts (hallucinated text risk)
- Dossier is mandatory — `build_dna_from_sku()` hard-fails on missing dossier, no fallback
- Layer 2 negatives appended to generation prompt as canonical text (no separate negative_prompt API surface)
- Model IDs imported from `llm/model_ids.py` — never hardcode elsewhere
- 3-judge tournament: aggregate = Opus synthesis score when Opus ran, vision mean otherwise

### 6-step per-edit workflow
```
Step 1: implement
Step 2: scripts/verify-impl.js      → writes eval/verify-impl/<task-id>.md
Step 3: /simplify
Step 4: scripts/post-simplify-verify.js  → re-lint + load-bearing pattern check
Step 5: refine
Step 6: scripts/kb-distill.js       → writes knowledge-base entry (pattern/lesson/decision)
```

---

## 10. Notable Gotchas

### G1 — GA4 Property ID Format
`verify-ga4.js` requires `"properties/12345678"` format, NOT the `"G-XXXXXX"` tracking ID. The GA4 Data API v1beta silently rejects the G- format.

### G2 — GTM Container ID vs Public Slug
`GTM_CONTAINER_ID` env var must be the public slug (`GTM-XXXX`), not the internal numeric ID. The script resolves the numeric ID at runtime by listing containers and matching `publicId`.

### G3 — Google Service Account JSON on Vercel
Multi-line private key JSON is commonly mangled by Vercel's env var paste UI. Must paste as single-line with `\n` escaped newlines. `readGaxiosError()` in `google-jwt.js` normalizes the resulting errors.

### G4 — GraphQL Cache Key Length Mismatch (bug, now tested)
`MultiTierCache` had `invalidate()` using `[:16]` but `set()` using `[:32]` for key hashes. Invalidations were silent no-ops. Captured in `test_graphql_cache.py::test_cache_invalidate_uses_matching_key_length`.

### G5 — conftest.py Silent Test Exclusion
If `import wordpress` fails, 30+ test globs are removed from collection with no warning. Running `pytest` on a fresh checkout without the `wordpress` module gives a passing green run that actually skipped most of the suite.

### G6 — LIFO Middleware Order in FastAPI
`app.add_middleware(TenantMiddleware)` registered last → runs first. Middleware wraps billing. Adding new middleware in the wrong position changes the execution order.

### G7 — Atomic Swap Backup Expiry
Deploy script retains only 2 `.old.*` backups. If two deploys fail in close succession, the oldest rollback target is deleted automatically.

### G8 — smoke-test.sh Stale URL
`scripts/smoke-test.sh` hardcodes `WORDPRESS_URL="${WORDPRESS_URL:-https://skyyrose.com}"`. The live domain is `skyyrose.co`. Override with `WORDPRESS_URL=https://skyyrose.co bash scripts/smoke-test.sh` or patch the default.

### G9 — WooCommerce Category IDs Hardcoded
`scripts/launch/sync_products.py` has `CATEGORY_MAP = {"signature": 19, "black-rose": 20, "love-hurts": 18}`. These IDs are site-specific and will break on a fresh WooCommerce install.

### G10 — post-simplify-verify.js Exit 2 = G3 Escalation
Two consecutive failures of the post-simplify verify step triggers exit code 2, which signals the G3 escalation path. State is tracked in `.simplify-consecutive.json`. Reset by a passing run.

### G11 — Opus 4.7 API Constraints
`tournament.py` documents that Opus 4.7 has NO `budget_tokens` parameter and NO `temperature`/`top_p`/`top_k`. These were removed from the API. Passing them causes 400 errors.

### G12 — Dead PipelineConfig Field
`gpt_image_model` is declared in `PipelineConfig` but never read by `router.py` or `generate.py`. Setting it has no effect. Do not add routing logic that depends on it without also updating the router.

### G13 — e2e-wp Suite Has No Specs
`tests/e2e-wp/` contains only Playwright infrastructure (package.json, reporter config). There are zero spec files. Any CI gate on this suite will pass vacuously.

### G14 — Dossier Hard-Fail (No Silent Fallback)
`build_dna_from_sku()` raises `DossierMissingError` if the dossier file is absent. There is no fallback to Gemini-vision-inferred DNA. Adding a new SKU to the catalog without a `data/dossiers/{name-slug}.md` file will abort the pipeline at spec-building time.
