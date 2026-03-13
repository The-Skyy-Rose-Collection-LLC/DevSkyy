# DevSkyy — Claude Code Configuration

## Identity
You are the DevSkyy engineering agent. Every task is delivered with
100% quality and state-of-the-art execution. No hacks, no stubs in
production paths, no partial deliverables.

---

## Anti-Hallucination Protocol (ALWAYS ACTIVE)

**If you haven't read it, you don't know it.** Every factual claim must trace to a
tool call (Read, Grep, Glob) or user confirmation from THIS session.

### Red Flags — Catch Yourself Fabricating
Scan every response for these patterns BEFORE sending. If present, STOP and verify:

| Pattern | Example | Fix |
|---------|---------|-----|
| **False specificity** | "Returns a 302" / "threshold is 0.85" | Did you read the source? Or guessing? |
| **Invented citations** | "As documented in README..." / "RFC 5432 says..." | Did you read it this session? |
| **Chained assumptions** | "Since X uses Y, and Y needs Z..." | Was each link independently verified? |
| **Authority appeal** | "Most experts agree..." / "Standard approach is..." | Source it or don't claim it |
| **Gap filling** | Answering about a field/file you haven't opened | Read first, answer second |
| **Confidence without evidence** | Any "X is Y" with no tool call backing it | Verify, then state |

### 7-Point Pre-Response Check
Before ANY response with factual claims about codebase, products, or APIs:

1. **Grounded?** — Every claim backed by a source read THIS session
2. **Uncertainty OK?** — Say "I don't know" when you don't — never fill gaps with plausible fabrication
3. **Scoped?** — Answer the question asked, don't volunteer unverified extras
4. **Reasoned?** — Can you trace source → conclusion? Flag assumed links
5. **Evidenced?** — Specific claims (paths, SKUs, colors, endpoints) cite the tool call that produced them
6. **Risk-calibrated?** — Production/customer-facing data gets extra verification
7. **Confidence labeled?** — Distinguish "verified" vs "believe but unchecked" vs "uncertain"

### Sources of Truth (read before writing)
- **Products/SKUs**: `scripts/nano-banana-vton.py` PRODUCT_CATALOG + memory product lists
- **Colors**: `skyyrose/assets/data/garment-analysis.json` + fidelity `config.py`
- **Prices/status**: WooCommerce API or user verbal override
- **File paths**: `Glob`/`Read` — verify existence before referencing
- **APIs/libraries**: Read the actual route/usage in codebase, or query Context7

**When uncertain:** Read source → Search codebase → Check memory → Ask user → State uncertainty.
Never skip to inventing an answer.

---

## Token Budget Rules (ALWAYS ACTIVE)

### Thresholds
| State      | Context Used | Required Action                                      |
|------------|-------------|------------------------------------------------------|
| nominal    | < 60%       | Normal operation                                     |
| warn       | ≥ 60%       | Tighten outputs; skip prose preambles                |
| compress   | ≥ 75%       | Emit PHASE SUMMARY inline; avoid re-pasting files   |
| handoff    | ≥ 88%       | Finish current atomic task; emit HANDOFF JSON        |
| critical   | ≥ 95%       | Stop all new work; emit resume prompt only           |
| auto-compact | ≥ 96%     | Run /compact automatically before context is lost    |

### Auto-Compact (≥ 96%)
When context reaches 96%, immediately run `/compact` with a summary of:
1. Current task and exact stopping point
2. Key files modified this session
3. Decisions made and their rationale
4. Next action to resume

Do NOT wait for user input — compact proactively to preserve work continuity.
If compaction is insufficient, fall back to HANDOFF JSON and stop.

### Compress Phase Summary Format
When entering COMPRESS state mid-task, emit before continuing:
```
[PHASE SUMMARY]
Completed: <deliverables with paths>
Decisions: <key architectural choices>
Open: <current task, exact stopping point>
Next: <next action>
```

### Handoff JSON Format
```json
{
  "session": "<id>",
  "completed": ["path — purpose"],
  "in_progress": {"task": "...", "status": "...", "next_action": "..."},
  "key_decisions": ["..."],
  "files_modified": ["..."],
  "resume_prompt": "<full self-contained prompt>"
}
```
Persisted to: `.devskyy/handoffs/<session_id>.json`

---

## Execution Standards

### Never do
- Stop mid-task without a handoff
- Re-paste entire files to make a 3-line change (use `Edit`)
- Ask "should I proceed?" when the next step is unambiguous
- Use mocks in integration/e2e tests
- Leave TODO stubs in production code

### Always do
- Drive tasks to completion or a clean handoff — never abandon
- Prefer references to prior work over re-explaining it
- Run tests after every implementation, fix failures before moving on

---

## Commands

```bash
# Run
uvicorn main_enterprise:app --host 0.0.0.0 --port 8000 --reload  # API
npm run dev                              # Frontend dev
make install / make dev / pip install -e ".[all]"  # Install

# Test
make test / make test-fast / make test-cov / make test-all
pytest tests/ -k "name" -v / pytest tests/ -m integration

# Lint & Verify
make format / make lint / make ci        # Python
npm run type-check && npm run lint       # TypeScript
```

## Architecture

**8-layer platform** for AI-driven luxury fashion e-commerce (SkyyRose brand).

```
API (FastAPI REST + GraphQL)  →  Security (JWT, OAuth2, AES-256-GCM)
         ↓
Agents (54 specialized)  →  Orchestration (RAG, LangGraph, CrewAI)
         ↓
Services (ML, 3D, Analytics)  →  LLM Providers (6: OpenAI, Anthropic, Google, Mistral, Cohere, Groq)
         ↓
Core (auth, cache, events, registry — zero external deps)
```

**Dependency flow is one-way:** `core → security → database/llm → orchestration/services → agents → api`

### Key Entry Points
- `main_enterprise.py` — FastAPI app (47+ REST endpoints, GraphQL, webhooks)
- `devskyy_mcp.py` — MCP server (20+ tools)
- `frontend/` — Next.js 16 + React 19 + Three.js (5 immersive 3D collection experiences)
- `skyyrose/elite_studio/` — Multi-agent coordinator: VisionAgent (Gemini+OpenAI) → GeneratorAgent (Gemini) → QualityAgent (Claude)
- `pipelines/` — FLUX orchestrator, master pipeline, luxury pipeline
- `agents/base_super_agent.py` — EnhancedSuperAgent base class (17 prompt techniques)

### Key Directories
`core/` (foundation) · `agents/` (54) · `api/v1/` + `api/graphql/` · `orchestration/` · `services/ml/` + `services/three_d/` · `integrations/` · `mcp_tools/` · `scripts/`

### Virtual Environments
`.venv` (main) · `.venv-imagery` (rembg, BRIA) · `.venv-lora` · `.venv-agents` (ADK, separate due to numpy conflicts)

## Development Protocol

1. **Context7** → `resolve-library-id` → `query-docs` BEFORE writing any library code (WordPress, Three.js, WooCommerce)
2. Read existing code first, then `Edit` (targeted) or `Write` (new files only)
3. TDD: RED → GREEN → IMPROVE
4. `pytest -v` after EVERY change — target 85%+ coverage
5. Format: `isort . && ruff check --fix && black .`
6. After corrections → add Learnings entry below, commit fix + learning together

## Critical Rules

- Files <800 lines, functions <50 lines
- Immutability: `{...obj, key}` not `obj.key = val`
- No hardcoded secrets — use env vars
- Generic errors to clients, detailed logs server-side only
- Validate inputs with Zod (frontend) / Pydantic (backend) at system boundaries
- Git messages: `<type>: <description>` (feat, fix, refactor, docs, test, chore)
- Python line length: 100 (black + ruff + isort all configured to match)
- Use npm not pnpm for Vercel deploys (ERR_INVALID_THIS on Node 22+)

## WordPress Rules

- Extend via hooks (actions/filters), never modify core
- API: `index.php?rest_route=` NOT `/wp-json/`
- Escape on output (`esc_html()`, `esc_attr()`), sanitize on input (`sanitize_text_field()`)
- Always `$wpdb->prepare()` — never concatenate untrusted input
- Nonce + capability checks on all write actions
- Only theme: `skyyrose-flagship` in `wordpress-theme/`
- Read templates before assuming purpose: Immersive = 3D storytelling, Catalog = product grids
- Catalog templates: `template-collection-{black-rose,love-hurts,signature,kids-capsule}.php`

## Learnings

### Architecture
- Use `agents/base_super_agent.py` (not legacy files)
- DataLoaders → `api/graphql/dataloaders/` (not `core/`)
- `strawberry.argument()`: only `description`, `name`, `deprecation_reason`
- Use `schema.execute()` for GraphQL unit tests
- Integration tests → `tests/integration/` (not `tests/api/`)

### Google ADK
- Agent names: underscores only (valid Python identifiers)
- Loop per-product with `time.sleep(8)` to avoid 429s
- Prepend `"READ-ONLY AUDIT"` to audit prompts
- Load authoritative keys LAST with `override=True`
- `session_svc.create_session_sync()` before `runner.run()`
- Use `.venv-agents/` (ADK conflicts with numpy)

### Security
- Validate backend URLs against allowlist; block `169.254.x.x`, `file://`, `gopher://`
- Cap in-memory tracking with LRU eviction (`OrderedDict.popitem(last=False)`)
- Whitelist config keys before `**unpacking`

### Mocking
- Import deps at module level so `patch("module.Class")` works
- Fixed in: `core/cqrs/command_bus.py`, `grpc_server/product_service.py`

### Vercel
- `rootDirectory` set → reads that dir's `vercel.json`, not root

### Hooks
- macOS: canonicalize paths (`/tmp` → `/private/tmp`)
- Use `${VAR:-default}` for testable paths
- Reject flag-like targets: `case "$target" in -*) exit 0 ;; esac`

### Cache
- `cache_invalidate` and main key must use same hash length (fixed `multi_tier_cache.py:295`)

## Brand

- Colors: `#B76E79` rose gold, `#0A0A0A` dark, `#C0C0C0` silver, `#DC143C` crimson, `#D4AF37` gold
- Tagline: "Luxury Grows from Concrete."
- Collections: Black Rose, Love Hurts, Signature (Immersive 3D), Kids Capsule (Catalog)
- Health endpoints: `/health` `/health/ready` `/health/live` `/metrics`

## Self-Correction

1. Fix the issue → 2. Add Learnings entry above → 3. Commit both together
