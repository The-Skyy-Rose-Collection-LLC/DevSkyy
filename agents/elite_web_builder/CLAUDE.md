# agents/elite_web_builder/ — Full-stack AI web development agency

Multi-provider, self-healing, self-learning, hallucination-free agent system. Built on Google ADK with Ralph-tui execution loop. **Independent runtime** — has its own `.venv`, `requirements.txt`, `pyproject.toml`, `conftest.py`. Not a SuperAgent or CoreAgent — a complete agency that consumes them.

## Director pattern (canonical entry point)

```python
from agents.elite_web_builder.director import Director

director = Director.from_config(config_path="config/provider_routing.json")
report = await director.execute_prd(prd_text)
```

The `Director`:
1. Parses PRD → user stories with dependency graph
2. Assigns each story to a specialist agent via `ModelRouter`
3. Reviews output before marking story green
4. Runs `VerificationLoop` (8 gates) after each story
5. Triggers `self_healer.py` on failures
6. Maintains the learning journal (JSONL append-only)

## Architecture

```
elite_web_builder/
├── run.py                  Entry point — loads .env, kicks Director.execute_prd()
├── director.py             Project Director — story breakdown, assignment, review
├── triggers.py             Webhook + event dispatch
├── prd.md                  Default PRD (overridable via --prd flag)
├── requirements.txt        Isolated deps (anthropic, openai, google-genai, pydantic)
├── pyproject.toml          Package metadata (v0.1.0)
├── conftest.py             Pytest config — shared across tests/
│
├── agents/                 14 specialist agents (frontend, backend, a11y, perf, etc.) — see agents/CLAUDE.md
├── core/                   11 infrastructure modules (CostTracker, ModelRouter, VerificationLoop) — see core/CLAUDE.md
├── config/                 provider_routing.json + model preferences — see config/CLAUDE.md
├── templates/              Project scaffolds — see templates/CLAUDE.md
├── tools/                  Lighthouse runner, screenshot diff, type/spacing/contrast checkers
├── knowledge/              13 .md files — canonical brand/product/WP/photography knowledge
├── tests/                  26 pytest files — agent-by-agent + integration coverage
├── evals/                  Eval harness (golden output comparison)
├── instincts/              Behavioral patterns (auto-applied corrections)
├── custom_instincts/       Project-specific overrides
├── output/                 Generated PHP/CSS/JS — gitignored, treat as ephemeral
```

## Environment setup

**Primary key file:** `DevSkyy/.env.elite-web-builder` (gitignored — each dev keeps their own copy)

**Required API keys** (verified before expensive imports in `run.py`):
- `ANTHROPIC_API_KEY` — Director + Frontend + Backend
- `GEMINI_API_KEY` — Design System + Performance
- `OPENAI_API_KEY` — SEO Content

**Workspace runtime:** Python 3.11+ via `.venv/` (created per-project; does NOT use `.venv-agents/` like ADK render_pipeline). Run from this directory: `cd agents/elite_web_builder && .venv/bin/python run.py`.

## CLI

```bash
.venv/bin/python run.py                    # Full PRD execution
.venv/bin/python run.py --dry-run          # Planning only (no agent execution, no cost)
.venv/bin/python run.py --prd custom.md    # Custom PRD file
```

## VerificationLoop — 8 gates

After every story, `VerificationLoop.report.all_green` must be True or the story self-heals. Gates are ordered cheap-first:

| # | Gate | Tool |
|---|------|------|
| 1 | BUILD | Build runner (npm/composer/whatever the project uses) |
| 2 | TYPES | Type checker (tsc/mypy/PHPStan) |
| 3 | LINT | ESLint / Ruff / PHPCS |
| 4 | TESTS | pytest / vitest / phpunit |
| 5 | SECURITY | Semgrep |
| 6 | A11Y | axe-core + Lighthouse a11y |
| 7 | PERF | Lighthouse perf |
| 8 | DIFF | Screenshot diff |

Order is intentional — don't reorder without understanding cost implications. A failure on gate N skips gates N+1..8 and triggers self-heal.

## Self-healing flow

Failed story → `self_healer.py` retries with **a different specialist agent** (e.g., frontend story failed → re-route to a senior frontend agent or to backend if the issue was actually backend). Outcome recorded in `learning_journal.py` (JSONL at `data/agent-learning/elite-web-builder/`).

Per cmem #5478 (2026-05-19): this self-healing implementation **predates** `agents/core/base.py SelfHealingMixin`. Eventual consolidation target is the agents/core one — but Elite Web Builder still uses its own copy for now.

## Conventions

- **Director-only orchestration.** Specialist agents in `agents/` produce structured outputs; they don't call LLMs directly. All LLM calls go through `core/provider_adapters.py` → `ModelRouter.call_with_fallback()`.
- **`CostTracker.record()` mandatory** on every LLM call. `core/cost_tracker.py:_PRICING` is the single source of truth for model costs (12 models, updated Feb 2026).
- **`AgentSpec` constants only.** `agents/<role>.py` files export exactly one `*_SPEC = AgentSpec(...)` — no classes, no functions.
- **Two hard frontend rules** (in `frontend_dev.py` system prompt verbatim): (1) CSS uses `var(--*)` only, never hardcoded hex; (2) no `@import` in CSS — use enqueue dependencies.
- **`output/` is gitignored.** Never commit generated files. Treat as ephemeral build artifact space.
- **Knowledge files are catalog-aware.** `core/ground_truth.py` reads the SkyyRose catalog at runtime (not import time) — supports hot catalog updates without Director restart.

## Don't

- Don't add specialist logic to `core/`. Specialist agents live in `agents/<role>.py`.
- Don't bypass `provider_adapters.py` to call Anthropic/OpenAI/Google SDKs directly. Routing + cost tracking + fallback all happen there.
- Don't add a new specialist role without: (1) `AgentRole` enum entry in `agents/base.py`, (2) `<role>.py` spec file, (3) registration in `director.py`.
- Don't commit `.env.elite-web-builder`. Gitignored on purpose; share via secrets manager.
- Don't run from repo root. Elite Web Builder is its own runtime — `cd agents/elite_web_builder/` first.
- Don't reuse Elite Web Builder's self-healer for new agent code. New code uses `agents/core/base.py SelfHealingMixin`. This dir's healer is legacy slated for migration.

## Related

- Brand canon (SoT, established 2026-04-18 cmem #1171): `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` + `knowledge-base/seed/from-interview.md`
- Universal self-healing target: `agents/core/base.py` `SelfHealingMixin` (consolidation goal)
- Ralph driver: `core/ralph_integration.py` (Ralph task → `Director.execute_prd()`)
- Output directory (gitignored): `agents/elite_web_builder/output/`
- Learning journal: `data/agent-learning/elite-web-builder/*.jsonl`

## Recent learnings

- Elite Web Builder agent structure mapped (cmem #3219, 2026-05-08): 14 specialist agents + 11 core infra modules.
- CostTracker spread across multiple modules in Elite Studio + Web Builder (cmem #2313, 2026-05-06) — consolidation pending.
- Director pattern + render_pipeline human-gated learning loop + SubAgent ALIASES documented in cmem #5478 (2026-05-19).
- Brand SoT established 2026-04-18 — catalog CSV + interview doc.
- File migration complete (cmem #964, 2026-04-17) — 72 enforcement-context references remain to audit.
