# agents/render_pipeline/eval/ — ADK eval harness

ADK-format eval harness for the full 9-step render pipeline. Uses `google.adk.evaluation` to compare pipeline output against golden expectations stored in `render_pipeline.evalset.json`.

## Files

| File | Purpose |
|------|---------|
| `__init__.py` | Package marker |
| `render_pipeline.evalset.json` | Golden eval set — input SKUs + expected output shape / score thresholds |
| `test_config.json` | Eval runtime config — model versions, judge thresholds, retry policy |
| `test_render_pipeline.py` | pytest entry point that loads evalset + invokes pipeline + asserts |

## ADK evalset format

`render_pipeline.evalset.json` follows the standard ADK eval schema:

```json
{
  "evals": [
    {
      "id": "br-001-front-baseline",
      "input": { "sku": "br-001", "view": "front" },
      "expected": {
        "engine": "nano_banana_pro",         // engine routing should land here
        "tournament_score_min": 0.85,        // QA tournament must clear this
        "output_path_pattern": "renders/output/br-001/front/.+\\.png"
      },
      "tolerance": { "tournament_score": 0.05 }
    }
  ]
}
```

## Running evals

```bash
# Direct pytest (cheapest — uses recorded responses where available)
.venv-agents/bin/python -m pytest agents/render_pipeline/eval -v

# Live (real API calls — costs money)
RUN_LIVE_EVALS=1 .venv-agents/bin/python -m pytest agents/render_pipeline/eval -v

# Via ADK CLI
adk eval agents/render_pipeline --evalset agents/render_pipeline/eval/render_pipeline.evalset.json
```

## Eval dimensions

The harness asserts on:

1. **Engine routing** — does `route_engine_fn` pick the expected engine for this SKU? (Catalog override compliance)
2. **Layer separation** — does `articulate_layer0_fn` only write Layer 0, leaving Layers 3 + 2 untouched? (Verified by parsing the final prompt)
3. **Tournament score** — does `qa_tournament_fn` clear the minimum score? (Within tolerance)
4. **Output path shape** — does `generate_image_fn` write to the expected path pattern?
5. **Synthesis schema compliance** — does `SynthesisAgent` produce a valid `RenderResult` Pydantic model?

## Conventions

- **Golden set lives in evalset.json.** Adding a new SKU + view to test means editing the JSON, not the Python.
- **Tolerance values are explicit.** `tournament_score` varies run-to-run with LLM variability; `tolerance: 0.05` accommodates noise. Don't tighten without understanding the judge variance.
- **Live evals gated.** `RUN_LIVE_EVALS=1` is required to actually spend money. CI runs offline against cached responses.
- **Per-SKU records.** Each eval entry has a unique `id` (e.g. `br-001-front-baseline`) — these become row keys in eval-result CSVs for tracking regression over time.
- **Test config is environmental.** `test_config.json` pins model versions and judge thresholds; don't hardcode these in `test_render_pipeline.py`.

## Don't

- Don't run live evals in CI without an explicit budget cap. A full evalset run on the canonical 33-SKU catalog at 1-2 refine iterations = ~$15-25.
- Don't update golden expected values to make a failing test pass. The eval is the contract — if output drifted, investigate root cause (engine swap? prompt drift? judge change?).
- Don't add evals that don't validate something the pipeline should preserve. Each new eval entry should test a regression case or a load-bearing invariant.
- Don't share eval state across runs. Each invocation is independent; `InMemorySessionService` ensures isolation.

## Related

- Pipeline under test: `agents/render_pipeline/agent.py` (root_agent)
- ADK eval framework: `google.adk.evaluation`
- Result types: `agents/render_pipeline/agent.py` `RenderResult` Pydantic model
- Adaptive learning consumes eval results: `agents/render_pipeline/learning/`
- Cost tracking: instrumented via ADK telemetry; aggregate via `learning/recorder.py`

## Recent learnings

- ADK eval harness is the upstream-recommended way to test SequentialAgent pipelines — don't write parallel pytest equivalents.
- Tournament score variability is real (judge LLM noise) — tolerance is intentional, not technical debt.


<claude-mem-context>

</claude-mem-context>