# agents/render_pipeline/learning/ — Three adaptive learning loops

Records render pipeline outcomes into structured loops that drive future improvement. Per cmem #5478 (2026-05-19), this is the **human-gated learning loop** — automated capture, manual review before weights update.

## Files

| File | Role |
|------|------|
| `LOOP.md` | Specification for the three learning loops (canonical doc, read first) |
| `recorder.py` | Writes loop events to JSONL — append-only, never mutate prior records |
| `proposals.py` | Reads accumulated records → proposes adjustments → human review queue |
| `__init__.py` | Re-exports `record_loop_event`, `propose_adjustments` |

## Three loops

| Loop | Records | Drives |
|------|---------|--------|
| **Loop 1 — Tournament quality** | QA tournament scores per (engine, SKU, view) | Engine routing preferences in catalog `engine_override` |
| **Loop 2 — Prompt drift** | Layer 0 articulation outputs + tournament score correlation | `ArticulateLayer0Agent` system prompt refinement |
| **Loop 3 — Refinement effectiveness** | Pre-refine vs post-refine tournament scores | RefineImageAgent system prompt + max_iterations tuning |

## Recording

Every `qa_tournament_fn` invocation records to all three loops:

```python
from agents.render_pipeline.learning.recorder import record_loop_event

record_loop_event(
    loop_id="loop_1_tournament_quality",
    sku="br-001",
    view="front",
    engine="nano_banana_pro",
    tournament_score=0.91,
    judge_breakdown={"gpt-5.5-pro": 0.92, "gemini-3.1-pro": 0.89, "opus-4-7": 0.93},
    timestamp=datetime.now(UTC).isoformat(),
)
```

JSONL records land in `data/render-learning/<loop_id>.jsonl` (gitignored, append-only).

## Proposal flow (human-gated)

```bash
# Read accumulated records, propose adjustments
python -m agents.render_pipeline.learning.proposals --loop loop_1 --since 7d

# Output: proposed catalog engine_override updates for review
# Operator reviews → manually applies via catalog CSV edit (NOT auto-applied)
```

**Proposals are advisory.** The pipeline does NOT auto-update the catalog or system prompts. Per project policy, learning-driven changes go through human review:

1. `recorder.py` captures events automatically (no gate)
2. `proposals.py` synthesizes recommendations on demand
3. Operator reviews + applies (catalog CSV edit, agent prompt edit, etc.)
4. Re-run evals (`agents/render_pipeline/eval/`) to verify the change

This avoids the failure mode of automated systems drifting catalog data without provenance.

## Conventions

- **JSONL append-only.** Never edit prior records. Corrections go in as new records with a `correction_of` field pointing back.
- **UTC timestamps.** `datetime.now(UTC).isoformat()` — no local time, no naive datetimes.
- **Loop IDs are strings (`"loop_1_tournament_quality"`)** — keeps logs greppable. Adding a new loop requires updating LOOP.md + recorder + proposals.
- **No PII in records.** SKUs, engines, scores only. No customer data, no operator IDs.
- **Schema versioning.** Each record has `schema_version: int`. Bump when changing the shape; readers must handle old versions (don't break historical analysis).

## Don't

- Don't bypass `recorder.py` to write directly to the JSONL files. The recorder enforces schema + timestamp + UTC.
- Don't auto-apply proposals. Per the human-gated policy, proposals are advisory only.
- Don't mutate prior records. Append-only — historical analysis depends on the log being immutable.
- Don't add a new loop without specifying it in LOOP.md first. The doc is the contract; code must match.
- Don't run proposals on stale data. `--since 7d` is the default freshness window — older data may not reflect current model behavior.

## Related

- Spec doc: `LOOP.md` (read this first when working in this dir)
- Caller: `agents/render_pipeline/tools/qa_tournament.py` (records to all 3 loops on every invocation)
- JSONL destination: `data/render-learning/<loop_id>.jsonl` (gitignored)
- Eval harness consumes loop data: `agents/render_pipeline/eval/`
- Catalog override applied by humans after review: `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` `engine_override` column

## Recent learnings

- Human-gated learning loop is the chosen model (cmem #5478, 2026-05-19) — never auto-apply.
- Three loops capture engine routing, prompt drift, and refinement effectiveness independently — orthogonal signals.
- JSONL append-only is the right shape for ML telemetry — immutable history beats DB writes for this use case.
