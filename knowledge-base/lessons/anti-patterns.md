---
title: "Anti-Patterns: Confirmed Failure Modes (Phase 0 Seed)"
domain: meta
what_was_tried: "Multiple patterns that caused rework, cost overruns, or data loss across Milestones v1.0–v1.2 and V2 Phase 0"
why_it_failed: "See per-entry evidence below — each anti-pattern has at least one real incident as proof"
better_alternative: "See per-entry replacement guidance"
how_to_recognize_this_trap: "See per-entry signals"
loop_count_to_recover: 3
cross_refs:
  - "[wp: §1.5]"
  - "[v2: §0.3]"
  - "[serena: CRITICAL_WORKFLOW_DIRECTIVE]"
  - "[serena: error_handling_protocol]"
  - "[planning: research/PITFALLS.md]"
  - "[wolf: cerebrum.md:63]"
  - "[cmem #581]"
  - "[cmem #852]"
  - "[cmem #1185]"
---

# Anti-Patterns: Confirmed Failure Modes

15 anti-patterns seeded from WP §1.5 Layer 5, `tasks/lessons.md`, `.serena/memories/CRITICAL_WORKFLOW_DIRECTIVE.md`,
`.planning/RETROSPECTIVE.md`, `.wolf/cerebrum.md` Do-Not-Repeat, and bugfix claude-mem observations.

Each entry: **what it looks like** / **why it fails** / **the replacement** / **how to recognize it**.

---

## AP-01: Wrong Source Data Driving Everything Downstream

**What it looks like:**
The pipeline reads product specs from a convenient JSON file instead of the authoritative CSV. Images pass QA.
Code ships. Users see wrong products.

**Why it fails:**
QA measured image quality, not product identity. The scoring function returned 100 for beautifully rendered
images of the wrong garment. The error was invisible until a manual review caught a Black Rose Crewneck with
4 extra decorations that didn't exist.

**Evidence:**
Scorched-earth rebuild, April 2026: 16,950 lines deleted. Root cause was `prompts/library.py` reading from
`data/product-specs.json` instead of the CSV's `branding_spec` column. [cmem #581]

**Replacement:**
Always trace the data path from generation prompt back to `data/skyyrose-catalog.csv`. Every `branding_spec`
reference must go through `skyyrose.core.dossier_loader.get_product_with_dossier(sku)` (Python) or
`skyyrose_get_product($sku)` (PHP). The pipeline hard-fails on a missing dossier — there is no fallback.

**Signal:**
A QA score that looks suspiciously high on a first run; any pipeline that reads from `overrides/` JSON files
(retired 2026-04-25); any code that constructs a branding spec from memory or a non-CSV source.

**Cross-refs:** `[cmem #581]`, `[cmem #608]`, `[serena: canonical_catalog_source_of_truth]`,
`[wolf: cerebrum.md:72]`, `[planning: research/PITFALLS.md]`

---

## AP-02: Creating a Second Source of Truth for Product Data

**What it looks like:**
A second catalog file, manifest, or override JSON appears alongside the CSV. Code is updated to read from it
for "convenience." The two sources drift immediately.

**Why it fails:**
Every catalog integrity bug traces back to a second source of truth being created. String comparison against
directory names instead of normalized SKU identifiers is the most common form: em dashes vs hyphens, ALL CAPS
vs title case, curly quotes vs straight. 17 of 30 products had directory names that didn't match CSV names.

**Evidence:**
`catalog.yaml` → `manifest.json` → `overrides/{sku}.json` — three generations of secondary sources, each
causing a new class of integrity bugs before being retired. [cmem #852], [cmem #444]

**Replacement:**
Exactly four read paths exist, all pointing at the same CSV:
- PHP: `skyyrose_get_product_catalog()` in `inc/product-catalog.php`
- Python: `from skyyrose.core.catalog_loader import read_catalog_rows`
- Nano Banana: `from nano_banana.catalog import load_catalog`
- Elite Studio: `from skyyrose.elite_studio.catalog import Catalog`

Never create a fifth.

**Signal:**
Any new `.yaml`, `.json`, or `.toml` file in a data/ directory that contains product names, SKUs, or prices;
any `grep -r "catalog.yaml"` hit in non-archived code.

**Cross-refs:** `[cmem #723]`, `[cmem #852]`, `[serena: canonical_catalog_source_of_truth]`,
`[wolf: cerebrum.md:1]`

---

## AP-03: Moving Forward with Unfixed Errors

**What it looks like:**
A TypeScript error, ruff violation, or failing test is acknowledged but deferred. The task continues. By the
next session, the error is forgotten or entangled with new code.

**Why it fails:**
TypeScript errors compound. A type error in a shared utility propagates to every consumer. Ruff violations
trigger pre-commit hooks and block the entire commit. The cost of fixing a deferred error is always higher
than fixing it immediately.

**Evidence:**
`CRITICAL_WORKFLOW_DIRECTIVE.md` (Serena memory, 2025-12-25): "DO NOT MOVE ON UNTIL ALL ERRORS ARE FIXED."
The 4-step error protocol (Acknowledge → Fix → Harden → Verify) was codified after repeated instances of
this pattern causing cascading failures. [serena: CRITICAL_WORKFLOW_DIRECTIVE]

**Replacement:**
Stop. Fix the error. Verify the fix with the relevant test command. Only then continue.
Anti-patterns to explicitly reject: `continue-on-error: true` in CI, skipping failing tests, "will fix later."

**Signal:**
Any session that ends with an open lint violation; any commit where `--no-verify` is used without explicit
user request; any PR that lands with known failing tests.

**Cross-refs:** `[serena: CRITICAL_WORKFLOW_DIRECTIVE]`, `[serena: error_handling_protocol]`,
`[wp: §1.2]`, `[v2: §0.3]`

---

## AP-04: Calling External APIs Without Checking Cost First

**What it looks like:**
A loop is written to regenerate all 33 SKUs with FASHN or Gemini. It runs. The bill arrives.

**Why it fails:**
Batch AI generation calls can cost $10–$50 for a single catalog run. Paid API calls are irreversible — there
is no undo. The harm is immediate.

**Evidence:**
The cost-cap hybrid policy (`eval/cost-cap-policy.md`) was written specifically because of instances where
autonomous API calls caused unexpected charges. The STOP-AND-SHOW protocol is mandatory for any call >$1.
[v2: §1.3]

**Replacement:**
Before any paid API call: show the manifest (action, SKU, source file path, estimated cost). Wait for
explicit "y" or "yes". For calls ≤$1, autonomous execution is allowed up to session thresholds ($25
Anthropic, 50 AIDesigner gens, 30 FASHN calls, $10 Pinecone). See `eval/cost-cap-policy.md`.

**Signal:**
Any loop over SKU lists that calls FASHN, Gemini image gen, FLUX, GPT-Image, or AIDesigner; any function
named `batch_*` or `generate_all_*` that touches a paid endpoint.

**Cross-refs:** `[v2: §1.3]`, `[adr: 0002]`, `[serena: user_expectations]`

---

## AP-05: Deploying to Production Without Dry-Run Verification

**What it looks like:**
`scripts/deploy-theme.sh` is run directly on `main` to "save time." The site breaks. Rollback is manual.

**Why it fails:**
The deploy is atomic but not instant — there is a swap window. CSS/JS changes can break all pages silently
if assets are cached. The `verify_live()` function only checks the homepage HTTP status; JS breakage is
invisible at that level.

**Evidence:**
7 bugs were filed against `deploy-theme.sh` in a single day (bug-058 through bug-065), covering preflight
scope, concurrency, rollback retention, asset integrity verification, and credential exposure. [wolf: buglog bug-058–064]

**Replacement:**
Always run `npm run deploy:dry` first to preview. Run `npm run lint:php` before any deploy. Use
`--with-maintenance` only for DB migrations. After deploy, verify at least 4 URLs: homepage, shop, cart,
and one collection page.

**Signal:**
Any deploy that skips the dry-run; any deploy that follows a PHP template change without a lint pass; any
deploy on a branch that hasn't been verified on staging.

**Cross-refs:** `[serena: wordpress_deployment_status]`, `[wolf: buglog bug-058]`, `[cmem #959]`

---

## AP-06: Implicit Namespace Packages (Missing `__init__.py`)

**What it looks like:**
A new top-level Python package directory is created without an `__init__.py`. Tests pass locally. CI fails
with a cryptic "Source file found twice under different module names" mypy error.

**Why it fails:**
`mypy.ini` has `namespace_packages = False`. Without `__init__.py`, mypy can resolve the same `.py` file
under two module names (e.g., `preflight` and `renders.preflight`). This silently blocks commits via
pre-commit hooks.

**Evidence:**
Cerebrum Do-Not-Repeat entry (2026-04-15): "Never create `agents/base_super_agent.py` as a flat file — it
silently shadows the package directory." The same principle applies to any new top-level dir. [wolf: cerebrum.md:17]

**Replacement:**
Every top-level package directory MUST contain `__init__.py` (one-line docstring minimum). Add it in the
same commit as the directory — there is no valid reason to defer this.

**Signal:**
A new directory under root that contains `.py` files but no `__init__.py`; a mypy error mentioning "found
twice"; any `import` that works in isolation but fails under pre-commit.

**Cross-refs:** `[wolf: cerebrum.md:17]`, `[cmem #886]`

---

## AP-07: Using `wc_get_products()` in Templates for Catalog Data

**What it looks like:**
A PHP template calls `wc_get_products(['status' => 'publish', 'category' => 'black-rose'])` to build
a product list. It works in dev. In production, WooCommerce returns 0 products because WC isn't fully
initialized when the template renders.

**Why it fails:**
`wc_get_products()` is a live WooCommerce database query — it hits the DB on every page load, returns
results based on WC's internal product status (not the catalog CSV), and can return stale data if
products haven't been synced. The theme's `inc/product-catalog.php` helper exists specifically to avoid this.

**Evidence:**
bug-091 (2026-04-27): `front-page.php` used `wc_get_products()` for per-collection counts.
bug-092 (2026-04-27): `template-preorder-gateway.php` used fake SKU arrays instead of the catalog helper.
[wolf: cerebrum.md:88]

**Replacement:**
Use `skyyrose_get_collection_products($collection_slug)` from `inc/product-catalog.php`. It reads from the
canonical in-memory catalog array, not the WC database. For the preorder gateway, use
`skyyrose_get_product_catalog()` and filter by `is_preorder`.

**Signal:**
Any `wc_get_products(` call in a template file; any hardcoded SKU array in a PHP template.

**Cross-refs:** `[wolf: buglog bug-091]`, `[wolf: buglog bug-092]`, `[wolf: cerebrum.md:88]`,
`[serena: canonical_catalog_source_of_truth]`

---

## AP-08: Reading Library Docs from Memory Instead of Context7

**What it looks like:**
Code is written using a library API based on the agent's training knowledge. The API has changed, or the
version constraint is different. The code fails at runtime with an `AttributeError` or missing method.

**Why it fails:**
Training data for frequently-updated libraries (LangGraph, Pydantic v2, FastAPI, WooCommerce REST, google-genai)
goes stale quickly. A single context window of docs prevents most "wrong API signature" bugs.

**Evidence:**
V2 Master Plan §0.3: "MANDATORY — EVERY TASK: Before writing ANY code that touches an external library or API
→ Context7: resolve-library-id → Context7: query-docs → verify signatures → THEN code." [v2: §0.3]

**Replacement:**
`mcp__claude_ai_Context7__resolve-library-id` → `mcp__claude_ai_Context7__query-docs` before writing any
external library usage. This is non-negotiable per the V2 Operating Contract.

**Signal:**
Any code block that uses httpx, Pydantic, LangGraph, FastAPI, WooCommerce REST, voyageai, or google-genai
without a preceding Context7 call in the same session.

**Cross-refs:** `[v2: §0.3]`, `[serena: user_expectations]`, `[serena: coding_standards]`

---

## AP-09: Installing ADK / google-adk into the Main `.venv/`

**What it looks like:**
`pip install google-adk` is run inside `.venv/` to test an agent. The NumPy version conflicts. Elite Studio
imports break. Two hours of dependency untangling follow.

**Why it fails:**
`google-adk` has a numpy version constraint that conflicts with the imagery pipeline dependencies already
installed in `.venv/`. The main venv is shared by Nano Banana and Elite Studio — breaking it breaks
every pipeline.

**Evidence:**
Cerebrum Do-Not-Repeat (2026-04-24): "Never install google-adk into the main .venv/ — use .venv-agents/."
CLAUDE.md explicitly states: "Use `.venv-agents/` (ADK conflicts with numpy)." [wolf: cerebrum.md:84]

**Replacement:**
```bash
python3 -m venv .venv-agents
source .venv-agents/bin/activate
pip install google-adk
```
Never install it anywhere else. Never reference `.venv-imagery/` — it was never created.

**Signal:**
Any `pip install google-adk` command that doesn't first activate `.venv-agents/`; any numpy ImportError
in `.venv/` after a new package install.

**Cross-refs:** `[wolf: cerebrum.md:84]`, `[wolf: cerebrum.md:92]`

---

## AP-10: Modifying `innerHTML` Instead of Using DOM Construction

**What it looks like:**
A JavaScript function that injects dynamic content uses `element.innerHTML = '<div>' + data + '</div>'`.
It works. It also creates an XSS vector if `data` contains user-controlled input.

**Why it fails:**
`innerHTML` is an XSS sink. Even in a WordPress theme context where direct user-controlled strings are rare,
the pattern is banned by the CLAUDE.md security rules and the Content Security Policy header. The CSP already
has `unsafe-inline` as an open issue (production_audit_findings.md).

**Evidence:**
CLAUDE.md Critical Rules: "No `innerHTML` in JS — use `createElement` + `textContent`."
production_audit_findings.md open issue: ~30 `console.log` in frontend + CSP `unsafe-inline`. [serena: production_audit_findings]

**Replacement:**
```javascript
const el = document.createElement('div');
el.textContent = data;  // or el.setAttribute() for attributes
parent.appendChild(el);
```

**Signal:**
Any `innerHTML =` assignment in theme JS files; any dynamic string that includes template literals injected
via innerHTML.

**Cross-refs:** `[serena: production_audit_findings]`, `[serena: coding_standards]`

---

## AP-11: Skipping the PHP Lint Before WordPress Theme Commits

**What it looks like:**
A PHP template is edited and committed without running `npm run lint:php`. The PHPCS violation is caught
by the deploy script's preflight check after the deploy begins, rolling back mid-deploy.

**Why it fails:**
The deploy script runs `vendor/bin/phpcs` as a preflight gate. A lint failure mid-deploy leaves the site in
a known-good state (the swap hasn't happened yet), but wastes deploy time and creates noise in deploy logs.
PHPCS runs are slow (~30s) — catching violations before the deploy is always cheaper.

**Evidence:**
`tasks/lessons.md`: "`php-lint.sh` needs explicit Homebrew PHP path (`/opt/homebrew/bin/php`) — lint-staged
subshell doesn't inherit brew paths." PHPCS compliance section in CLAUDE.md: run before every commit.

**Replacement:**
```bash
cd wordpress-theme/skyyrose-flagship
vendor/bin/phpcs --standard=.phpcs.xml -s .
# Auto-fix: vendor/bin/phpcbf --standard=.phpcs.xml .
```

**Signal:**
Any PHP template commit without a preceding lint run; any PHP PHPCS violation in a PR; any `--no-verify`
flag used on a PHP commit.

**Cross-refs:** `[cmem #924]`, `[serena: coding_standards]`, `[wolf: buglog bug-012]`

---

## AP-12: Hardcoding SKUs in PHP Templates

**What it looks like:**
A template file contains an array like `['br-001', 'br-002', 'br-003']` to render a product grid. The catalog
grows or a SKU is retired. The template is silently out of sync.

**Why it fails:**
Hardcoded SKU arrays are a second source of truth — see AP-02. The product grid template part already
supports reading from `product-catalog.php` by passing a collection slug. Any hardcoded array is
immediately obsolete the first time the catalog changes.

**Evidence:**
bug-092: `template-preorder-gateway.php` had fake SKU arrays and was missing `kids-capsule` collection.
`tasks/lessons.md`: "Product grid template part pulls from `product-catalog.php` by SKU array — if SKU
not in catalog, card is silently skipped." [wolf: buglog bug-092]

**Replacement:**
```php
$products = skyyrose_get_collection_products( 'black-rose' );
// or for preorder:
$catalog = skyyrose_get_product_catalog();
$preorder = array_filter( $catalog, fn($p) => $p['is_preorder'] );
```

**Signal:**
Any PHP array literal containing strings that look like SKU codes (`br-`, `sg-`, `lh-`, `kids-`); any
hardcoded product count like `$count = 4`.

**Cross-refs:** `[wolf: buglog bug-092]`, `[serena: canonical_catalog_source_of_truth]`,
`[wolf: cerebrum.md:88]`

---

## AP-13: Trusting X-Tenant-ID Header Without Verification

**What it looks like:**
Middleware reads `X-Tenant-ID` from the request header and uses it to scope all database queries. Any HTTP
client can set this header to any tenant ID.

**Why it fails:**
This is a complete tenant spoofing vulnerability. Before the 2026-05 hotfix, any HTTP client could access
any tenant's data by setting the header. The vulnerability existed at full production scale.

**Evidence:**
`[cmem #1185]`: "Tenant middleware: JWT claim extraction without verification (pre-fix state)."
`[cmem #1193]`: "Tenant spoofing vulnerability fixed: X-Tenant-ID now HMAC-verified."
`[cmem #1278]`: "TenantMiddleware security hardening: X-Tenant-ID requires internal service token." [serena: SECURITY_CRITICAL_ISSUE_RESOLVED]

**Replacement:**
`X-Tenant-ID` must be accompanied by an HMAC-signed `X-Tenant-Signature` header using the shared internal
service token. The middleware validates the signature before trusting the tenant claim. See
`core/middleware/tenant.py` for the current implementation.

**Signal:**
Any middleware that reads `X-Tenant-ID` without calling the HMAC verification function; any test that sets
`X-Tenant-ID` without a corresponding signature.

**Cross-refs:** `[cmem #1185]`, `[cmem #1193]`, `[cmem #1195]`, `[cmem #1278]`,
`[serena: SECURITY_CRITICAL_ISSUE_RESOLVED]`

---

## AP-14: Formatter Wars (ruff vs black conflict on assert wrapping)

**What it looks like:**
A Python file is formatted with `black`. Pre-commit runs `ruff`. Ruff auto-fixes the `assert` statement
wrapping in a way that makes black reformat it differently. The file oscillates between two states. Commit
is blocked.

**Why it fails:**
ruff and black have a known disagreement on how to wrap assert statements with long messages. Running them
in the wrong order produces an infinite loop of reformatting.

**Evidence:**
`tasks/lessons.md` (Tooling Drift & Formatter Wars category): "ruff and black disagree on assert wrapping
— run `isort → ruff --fix → black` in that order to converge."

**Replacement:**
Always format in this exact order:
```bash
isort . && ruff check --fix && black .
```
Never run black before ruff. Never run ruff --fix after black.

**Signal:**
A pre-commit hook failure that alternates between a ruff violation and a black reformat on the same line;
any assert statement with a long message string.

**Cross-refs:** `[serena: coding_standards]`

---

## AP-15: Writing Stubs, TODOs, or Partial Implementations in Production Files

**What it looks like:**
A function is written with `raise NotImplementedError("TODO: implement later")` or a `# TODO: wire this up`
comment in a file that will be committed to main.

**Why it fails:**
TODOs in committed code become permanent technical debt. `NotImplementedError` crashes production if the
code path is reached. The project mandate is production-grade on first commit — not draft quality.

**Evidence:**
CLAUDE.md Output Quality: "Every output delivered in this project is production-ready. Not a draft. Not a
proof of concept. Not 'good enough for now.'" Code checklist: "No `TODO`, `FIXME`, `pass`, or
`raise NotImplementedError` in delivered code." [serena: coding_standards]

**Replacement:**
If implementation cannot be completed in the current session, do not commit the stub. Stage the work in
a feature branch, complete the implementation, verify with tests, then commit. A failing test that documents
the requirement is better than a stub that pretends the feature exists.

**Signal:**
Any `TODO`, `FIXME`, `NotImplementedError`, or `pass` in a non-test Python file destined for main; any
TypeScript function that returns `undefined` without being explicitly typed as `Optional`; any PHP function
with an empty body.

**Cross-refs:** `[serena: coding_standards]`, `[serena: CRITICAL_WORKFLOW_DIRECTIVE]`, `[v2: §0.3]`

---

## AP-16: Glob Fishing Instead of Consulting Canonical Source

**What it looks like:**
The agent runs `grep -rn "X" .` or `find . -name "*Y*"` six times across the repo to locate definitions, behaviors, or data that have a *known canonical source*. The agent burns tokens reading files that turn out to be derivatives, archives, or stale copies of the canonical source.

**Why it fails:**
Every project of meaningful size has multiple representations of the same concept — a data file, three readers in different languages, four documentation references, a test fixture, an archived migration. Grepping reads them all and forces the agent to deduplicate manually, often picking the wrong one. The canonical source exists; failing to consult it first is a self-inflicted token wound and a correctness risk (e.g., reading a stale fixture, then writing code against it).

**Evidence:**
Corey, KB seed interview, 2026-05-03: "Identify verified source first, then execute with verified production code — no token-wasting glob fishing." `MEMORY.md` "CANONICAL CATALOG SOURCE": the catalog CSV is the only legitimate product data; reading anything else risks acting on retired-but-still-on-disk artifacts. AP-01 (Wrong Source Data Driving Everything Downstream) is the bug-shaped form of this anti-pattern; AP-16 is the prevention. [interview: from-interview.md §3 E1]

**Replacement:**
Before any task, name the canonical source(s) you'll consult in one sentence. Examples:
- Touching product data → `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` (+ `data/dossiers/{slug}.md` if rendering-related)
- Touching brand canon → `eval/brand-story.md` + `knowledge-base/seed/from-interview.md`
- Touching architecture → `knowledge-base/decisions/` + `docs/adr/`
- Touching locked decisions → `docs/SKYYROSE_V2_MASTER_PLAN.md` §1.1
- Touching per-page intent → `docs/SKYYROSE_WORDPRESS_PLAN.md` §6
- Touching catalog reader code → `inc/product-catalog.php` (PHP) / `skyyrose/core/catalog_loader.py` (Python)

If you cannot name the canonical source for what you're touching, **stop and ask** — do not start grepping.

**Signal:**
- Three or more `grep` / `find` / `Glob` calls in sequence with broad patterns (`-rn .`, `**/*`)
- Reading more than 5 files just to figure out what the canonical version of a concept is
- The same concept getting "discovered" in multiple sessions because the previous discovery wasn't recorded

**Cross-refs:** `[interview: from-interview.md §3]`, `[wp: §1.5]`, `[v2: §0.3 Step 0]`, `AP-01` (Wrong Source Data), `AP-02` (Second Source of Truth)
