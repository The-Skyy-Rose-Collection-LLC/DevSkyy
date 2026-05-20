# agents/elite_web_builder/tests/ — pytest suite (25 test files)

Comprehensive coverage of the Elite Web Builder runtime. Tests live with the package (not in `DevSkyy/tests/`) because Elite Web Builder is an **independent runtime** with its own `.venv`, requirements, and conftest.

## Inventory by concern

**Director + execution flow:**
- `test_director.py` — `Director` story breakdown + assignment + review
- `test_execute_prd.py` — End-to-end `Director.execute_prd()` with mocked agents
- `test_agent_runtime.py` — `core/runtime.py` event loop + concurrency + timeouts
- `test_triggers_dispatch.py` — Webhook + event dispatch from `triggers.py`

**Provider + cost layer (`core/`):**
- `test_provider_adapters.py` — Anthropic/OpenAI/Google async wrappers
- `test_model_router.py` — `ModelRouter.resolve()` + `call_with_fallback()` + `ProviderStatus` transitions
- `test_cost_tracker.py` — `CostTracker.record()` + `_PRICING` lookups + per-story aggregation

**Quality gates (`core/verification_loop.py` + `core/gate_checkers.py`):**
- `test_verification_loop.py` — `VerificationLoop.report.all_green` logic + gate ordering
- `test_gate_checkers.py` — 8 gate implementations (BUILD/TYPES/LINT/TESTS/SECURITY/A11Y/PERF/DIFF)
- `test_self_healer.py` — Retry-with-different-specialist heal cycle

**Tools (`tools/`):**
- `test_tools.py` — Shared tool helpers
- `test_lighthouse_runner.py` — Lighthouse CI invocation + result parsing
- `test_screenshot_diff.py` — Image diff + threshold logic
- `test_template_scaffold.py` — Project scaffold generator

**Specialists (`agents/`):**
- `test_base_agents.py` — `AgentSpec` / `AgentRole` / `AgentCapability` invariants
- `test_specialist_agents.py` — 13 specialist `*_SPEC` constants — schema + system_prompt presence
- `test_new_specs.py` — Smoke test that new specs follow the contract

**Integrations:**
- `test_context7_bridge.py` — Context7 MCP wrapper (`tools/context7_bridge.py`)
- `test_ralph_integration.py` — Ralph task → Director translation
- `test_ground_truth.py` — Knowledge file loading + role mapping
- `test_learning_journal.py` — JSONL append-only log + win-rate aggregation
- `test_output_writer.py` — Generated PHP/CSS/JS file routing
- `test_integration.py` — Cross-module integration (Director + ModelRouter + VerificationLoop)

## Running tests

```bash
cd agents/elite_web_builder
.venv/bin/python -m pytest                  # Full suite
.venv/bin/python -m pytest -x               # Stop at first failure
.venv/bin/python -m pytest tests/test_director.py -v
.venv/bin/python -m pytest -m "not slow"    # Skip slow integration tests
```

`conftest.py` (in the parent `agents/elite_web_builder/` directory) provides:
- Fake provider adapters (no real API calls)
- Sample PRD fixtures
- `CostTracker` fixture with frozen `_PRICING`
- `tmp_path` shaped for output writer tests

## Conventions

- **No real API calls.** Tests mock `provider_adapters.py` — `pytest --override-ini` and `.env.elite-web-builder.test` provide stub keys. If you need real-call tests, mark them `@pytest.mark.live` and gate behind `RUN_LIVE_TESTS=1`.
- **Fixtures over inline setup.** Shared fixtures live in `conftest.py`. Inline construction of `Director` / `CostTracker` is OK only for explicitly state-sensitive cases.
- **Async tests use `pytest-asyncio`.** Mark with `@pytest.mark.asyncio` — the conftest sets `asyncio_mode = "auto"` so the decorator is optional, but explicit is preferred for readability.
- **Snapshot tests for agent prompts.** `test_specialist_agents.py` snapshots the rendered system prompt for each specialist — when intentionally updating a system prompt, regenerate snapshots in the same commit.
- **Coverage target ≥ 85%.** Matches the project-wide testing rule. Verified in CI via `pytest --cov`.

## Don't

- Don't make real LLM calls in CI tests. Cost adds up; rate limits trigger. Use mocked adapters or the `@pytest.mark.live` gate.
- Don't put repo-wide tests here. This dir is for Elite Web Builder code only. Cross-cutting tests live in `DevSkyy/tests/`.
- Don't disable a gate test (`test_gate_checkers.py`) to make CI green. If a gate is genuinely broken, fix the gate or remove it from `Gate` enum — don't silently skip.
- Don't import from `DevSkyy/agents/` (e.g. `from agents.commerce_agent import ...`) — Elite Web Builder has its own `agents/` package which takes import priority. Repo-root agents are intentionally NOT reachable from within this runtime.

## Related

- Conftest: `agents/elite_web_builder/conftest.py`
- Runtime under test: `agents/elite_web_builder/director.py`, `agents/elite_web_builder/core/`, `agents/elite_web_builder/agents/`
- Pytest config: `agents/elite_web_builder/pyproject.toml` `[tool.pytest.ini_options]`
- Coverage report: `agents/elite_web_builder/.coverage` (gitignored)
