# agents/render_pipeline/tests/ — Per-tool unit tests

Pytest coverage of the 9 FunctionTool implementations. **Separate from the eval harness** (`agents/render_pipeline/eval/`) — these tests are deterministic, no LLM calls, cheap to run in CI.

## Files

| File | Coverage |
|------|----------|
| `__init__.py` | Package marker |
| `test_tools.py` | All 9 tool functions — happy path + error paths |

## Running tests

```bash
# Cheap unit tests (no API calls, no cost)
.venv-agents/bin/python -m pytest agents/render_pipeline/tests -v

# Specific tool
.venv-agents/bin/python -m pytest agents/render_pipeline/tests/test_tools.py::test_route_engine -v

# Coverage
.venv-agents/bin/python -m pytest agents/render_pipeline/tests --cov=agents.render_pipeline.tools
```

## Test boundaries

These tests verify:

- **Pure logic correctness** — engine routing, path construction, prompt assembly
- **Schema compliance** — Pydantic models accept valid inputs, reject invalid
- **Error paths** — missing dossier → raise `DossierNotFoundError`, vision API down → raise (no silent fallback)
- **State contract** — tools write expected keys to `tool_context.state`

These tests do NOT verify:

- LLM output quality — that's the eval harness
- Provider API contracts — covered by provider client tests in `llm/providers/`
- End-to-end pipeline behavior — covered by ADK eval harness

## Mocking strategy

- **`vision_consensus_fn`** — mock both Gemini + GPT-4o vision clients; assert dual-judge merge logic
- **`generate_image_fn`** — mock the engine dispatch (NB Pro / gpt-image-1.5 / FLUX); assert path construction
- **`qa_tournament_fn`** — mock the 3 judge LLM calls; assert score aggregation + loop recording
- **`load_dossier_fn`** — `tmp_path` fixture with synthetic dossier files

## Conventions

- **Test isolation.** Each test gets its own `tool_context` mock. State doesn't leak between tests.
- **`pytest-asyncio` for async tools.** `@pytest.mark.asyncio` — most tools are sync, but `vision_consensus` + `generate_image` are async.
- **No mock collection failures.** `prometheus_client` was missing from install list (cmem #2567, 2026-05-06) — ensure `requirements.txt` covers all transitive deps before running tests.
- **Pin model strings via `llm.model_ids`.** When asserting model selection in a test, import the constant — don't hardcode `"claude-opus-4-7"` in assertions.

## Don't

- Don't make real API calls in these tests. Cost + flakiness. If you need real-call validation, use the eval harness (`RUN_LIVE_EVALS=1`).
- Don't test LLM output content. Tests assert structural + behavioral invariants, not generated text quality.
- Don't add a test that depends on the dossier filesystem layout from `knowledge-base/products/`. Use `tmp_path` fixtures so tests don't break when dossiers update.
- Don't skip a failing tool test. Each tool is a load-bearing step in the pipeline — a broken tool means broken renders.

## Related

- Tools under test: `agents/render_pipeline/tools/`
- Eval harness (complementary): `agents/render_pipeline/eval/`
- Pytest config: `agents/render_pipeline/conftest.py` (if present, else inherits from repo root)
- ADK framework: `google-adk` in `.venv-agents/`

## Recent learnings

- ADK test collection requires `google-adk[extensions]` (cmem #2670, 2026-05-06) — not just the base `google-adk` package.
- Mock test collection blocked by `prometheus_client` missing (cmem #2567) — add to requirements before running.
