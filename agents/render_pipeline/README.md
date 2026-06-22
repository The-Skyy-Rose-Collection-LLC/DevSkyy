# RenderPipeline — Google ADK Agent

End-to-end product-render pipeline for SkyyRose SKUs, built as a Google ADK
SequentialAgent with 9 sub-agents and an iterative refinement LoopAgent.

## Quickstart

```bash
# 1. Set up isolated agents venv (per CLAUDE.md numpy isolation requirement)
python3 -m venv .venv-agents
source .venv-agents/bin/activate
pip install google-adk pydantic anthropic openai google-genai fal-client pytest pytest-asyncio

# 2. Set API keys (or source .env files in repo root)
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_API_KEY=...
export FAL_KEY=...

# 3. Run on a single SKU (interactive STOP-AND-SHOW gate)
python -m agents.render_pipeline.cli --sku br-001 --view front

# 4. Run programmatically (skip the interactive gate)
STOP_CONFIRM=y python -m agents.render_pipeline.cli --sku br-001
```

## Architecture

```
SequentialAgent (root)
│
├── 1. LoadDossierAgent          gemini-2.5-flash       (dispatch)
├── 2. ResolveSourceAgent        gemini-2.5-flash       (dispatch)
├── 3. VisionConsensusAgent      gemini-2.5-flash       (dispatch)
│        └─ tool: gemini-3-flash-preview + gpt-4o vision in parallel
├── 4. RouteEngineAgent          gemini-2.5-flash       (dispatch)
│        └─ catalog engine_override → vision-driven fallback
├── 5. ArticulateLayer0Agent     claude-sonnet-4-6      (Layer 0 only)
├── 6. BuildPromptAgent          gemini-2.5-flash       (assembler)
├── 7. GenerateImageAgent        gemini-2.5-flash       (dispatch — PAID)
│        └─ NB Pro / GPT-image-1.5 / FLUX-pro routed
├── 8. QAAndRefineLoop           LoopAgent(max_iter=2)
│        ├── QaTournamentAgent   gemini-2.5-flash       (PAID — 3 judges)
│        ├── ScoreReasonerAgent  gemini-3-pro-preview   (F5 classifier)
│        ├── StopChecker         (escalates on pass/abort)
│        └── RefineImageAgent    gemini-2.5-flash       (PAID — Kontext)
└── 9. SynthesisAgent            claude-opus-4-7        (Pydantic RenderResult)
```

**5 model providers, each in its best-fit role.** See `agent.py` for verified
model assignments.

## Continuous learning

3 append-only JSONL loops at `data/agent-learning/`:

| Loop | Records | Surfaces |
|------|---------|----------|
| 1 — Engine winrate | every QA tournament | Per-SKU `engine_override` proposals |
| 2 — Template A/B | every render | Winning prompt templates |
| 3 — Failure modes | scores < 50 | Dossier amendment candidates |

Run weekly: `python -m agents.render_pipeline.learning.proposals` →
generates `data/agent-learning/proposals.md`.

## Tests

```bash
# Mock-based unit tests — always runs, no paid calls, no google-adk required
pytest agents/render_pipeline/tests/ -v

# Live integration eval — gated by EVAL_LIVE=1, ~$0.20/run
EVAL_LIVE=1 STOP_CONFIRM=y pytest agents/render_pipeline/eval/ -v
```

## Layer architecture (load-bearing for "identical to my products")

```
Final prompt = Layer 0 (Sonnet-written rendering directives)
             + Layer 3 (VERBATIM dossier positives — garment_type_lock + branding_block)
             + Layer 2 (VERBATIM dossier negatives — negative_block)
```

Sonnet 4.6 writes ONLY Layer 0 (engine-specific rendering style). It cannot
touch the dossier text. The "identical to my products" guarantee comes from
Layers 3 + 2 going UNTOUCHED from author to generator.

F4 finding (verified): this structure scores 88/100 first-attempt on br-001
with no contradictions and no defect-loop hallucination.

## Cost reality (per-SKU full run)

| Step | Cost |
|------|------|
| Dual vision describe | ~$0.010 (cached after 1st run per SKU) |
| Sonnet Layer 0 | ~$0.005 |
| Engine routing + dispatch (Flash) | ~$0.001 |
| Image generation (NB Pro / GPT-image / FLUX) | $0.04 – $0.08 |
| 3-judge QA tournament | ~$0.10 |
| ScoreReasoner (Gemini-3-pro) | ~$0.005 |
| Refinement (conditional, Kontext) | $0.04 |
| Opus synthesis | ~$0.05 |
| **Total per SKU** | **~$0.20 – $0.32** |

Full 33-SKU catalog run: ~$7–11. Less than two coffees.

## See also

- `DESIGN.md` — the architectural design document with verified F1-F7 findings
- `agents/render_pipeline/learning/__init__.py` — continuous-learning subsystem
- `tasks/multi-sku-validation-*.json` — empirical validation data
