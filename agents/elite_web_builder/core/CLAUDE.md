# agents/elite_web_builder/core/ — Elite Web Builder shared infrastructure

11 infrastructure modules shared by all specialist agents and the Director. Handles cost, provider routing, quality gates, self-healing, and Ralph integration. Do not add domain logic here — this layer is pure machinery.

## Key files

- `cost_tracker.py` — `CostTracker`: per-story token accounting. `_PRICING` dict maps 12 models to `(input_per_1M, output_per_1M)` tuples (updated Feb 2026, covers Anthropic/OpenAI/Google/xAI). `tracker.record(story_id, provider, model, input_tokens, output_tokens)` — called by every LLM invocation in Director.
- `model_router.py` — `ModelRouter`: provider health + model selection. `ProviderStatus(Enum)` — HEALTHY/DEGRADED/UNHEALTHY. `ProviderConfig` is `frozen=True` dataclass. `router.resolve(role)` → `RouteResult`. `call_with_fallback(role, fn, ...)` async — tries primary provider, falls through on failure. `_ULTIMATE_FALLBACK = ("google", GEMINI_VISION_MODEL)` — last resort if all providers degrade.
- `verification_loop.py` — `VerificationLoop`: post-story quality gate. `Gate(Enum)` with 8 values: BUILD / TYPES / LINT / TESTS / SECURITY / A11Y / PERF / DIFF. `report.all_green` is True only if all 8 gates pass or are explicitly skipped. Failure triggers `self_healer.py`.
- `gate_checkers.py` — implementations for each `Gate` value: build runner, type checker, ESLint, pytest, Semgrep, axe-core, Lighthouse, screenshot diff.
- `self_healer.py` — retries failed stories with a different specialist agent; records outcome in `learning_journal.py`.
- `learning_journal.py` — JSONL append-only log of story outcomes and win rates. Persisted to `data/agent-learning/elite-web-builder/`.
- `ground_truth.py` — canonical brand/product facts injected into all specialist agent contexts. Reads from `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` and `knowledge-base/seed/from-interview.md`.
- `output_writer.py` — writes generated PHP/CSS/JS files to `agents/elite_web_builder/output/` (gitignored).
- `ralph_integration.py` — entry point for Ralph-driven builds; translates Ralph task descriptions into `Director.execute_prd()` calls.
- `provider_adapters.py` — thin async wrappers over Anthropic, OpenAI, Google APIs. All LLM calls go through here — never call provider SDKs directly from specialist agents.
- `runtime.py` — event loop management, concurrency limits, timeout enforcement for parallel story execution.

## Conventions

- Every LLM call must: (1) go through `provider_adapters.py`, (2) have its tokens recorded via `CostTracker.record()`, (3) use `ModelRouter.call_with_fallback()` — never call a provider SDK directly from a specialist agent.
- `_PRICING` in `cost_tracker.py` is the single source of truth for model costs — update it when Anthropic/OpenAI/Google change pricing. Do not hardcode costs elsewhere.
- `Gate` enum order in `verification_loop.py` is intentional (cheap gates first) — BUILD before TESTS, TYPES before LINT. Do not reorder gates without understanding cost implications.
- `ground_truth.py` reads CSV at runtime, not at import time — allows hot catalog updates without restarting Director.

## Don't

- Don't add specialist agent logic (frontend, SEO, imagery) to any file in `core/` — those belong in `agents/elite_web_builder/agents/`.
- Don't update `_PRICING` without verifying the new rates against the provider's official pricing page.
- Don't skip `report.all_green` check — `verification_loop.py` must pass before a story is marked complete.
- Don't commit files to `output/` — it is gitignored; treat it as ephemeral build artifact space.

## Related

- `agents/elite_web_builder/director.py` — Director that orchestrates these modules
- `agents/elite_web_builder/agents/` — specialist agents that call into `provider_adapters.py` + `cost_tracker.py`
- `data/agent-learning/elite-web-builder/` — persisted learning journal JSONL files
- `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` — catalog read by `ground_truth.py`
