# agents/core/imagery/ — Imagery & 3D domain CoreAgent

`ImageryCoreAgent` — all visual asset generation: photos, virtual try-on (VTON), 3D models. Extends `CoreAgent` (`core_type = CoreAgentType.IMAGERY`). **Five native sub-agents** covering 4 vendors + HF Spaces orchestration. No SDK sub-agents (everything runs through provider APIs, not Claude SDK tool use).

## Sub-agent map

| Sub-agent | Module | Vendor | Failover |
|-----------|--------|--------|----------|
| `gemini_image` | `sub_agents/gemini_image.py` | Google Gemini native image gen (Nano Banana 2, gpt-image-2 not used here) | n/a (Gemini-only) |
| `fashn_vton` | `sub_agents/fashn_vton.py` | FASHN AI virtual try-on | FASHN → WeShopAI → IDM-VTON failover chain |
| `tripo_3d` | `sub_agents/tripo_3d.py` | Tripo3D API (.ai and .com regions, separate keys) | falls back to `meshy_3d` if down |
| `meshy_3d` | `sub_agents/meshy_3d.py` | Meshy 3D API | falls back to `tripo_3d` if down |
| `hf_spaces` | `sub_agents/hf_spaces.py` | HuggingFace Spaces orchestration + quota management | manages quota across all HF-backed providers |

## Key files

- `__init__.py` — re-exports `ImageryCoreAgent` (guarded import for graceful fallback)
- `agent.py` — `ImageryCoreAgent(CoreAgent)`: registers all 5 sub-agents via `_register_sub_agents()` using `importlib.import_module` (each registration wrapped in try/except so missing providers don't break startup)
- `agent.py:_get_legacy_imagery()` / `_get_legacy_product()` — lazy fallback to `SkyyRoseImageryAgent` / `SkyyRoseProductAgent` for tasks the sub-agents don't match

## Self-healing — provider failover

The imagery domain is failover-heavy because individual 3D + VTON providers go down regularly. `ImageryCoreAgent` defines three healing patterns:

1. **Provider failover** — if Tripo returns 5xx/timeout → diagnose as `PROVIDER_DOWN` → route to Meshy. Same for VTON: FASHN → WeShopAI → IDM-VTON.
2. **Quality gate** — output quality below threshold (cmem #5466) → diagnose as `DATA_QUALITY` → auto-retry with different params (e.g. higher steps, different seed).
3. **Quota management** — HF Spaces rate-limit hit → `hf_spaces` sub-agent tracks usage across providers and rotates accounts. Tripo has `.ai` and `.com` regions with separate keys (per project memory).

## STOP AND SHOW gates

All paid API calls require confirmation per project policy:

- FASHN (tryon, product-to-model, edit, model-create, image-to-video) — cost varies $0.075-$1.20+ per call
- Gemini image generation (Nano Banana 2, Pro) — per-image cost
- Tripo3D — per-model cost (single SKU spike record exists)
- Meshy — per-model cost

Sub-agents must surface `Action / SKU / Source / Cost / Confirm` before dispatch. The legacy `skyyrose_imagery_agent.py` already implements this — sub-agents in this dir delegate when appropriate.

## Conventions

- **Sub-agent registration via `importlib`** so a missing provider package doesn't break the whole core. `agent.py:48-65` shows the pattern — each import wrapped in try/except, logs at debug level.
- **`SKIPPED.json` is sacred.** Phase 14 preflight produces `renders/ghost-mannequin/SKIPPED.json` listing accessories deferred to v1.3 flat-lay pipeline. Imagery sub-agents MUST respect this list.
- **No silent fallback on missing dossier.** Per project memory feedback: 3D pipeline hard-fails if SKU dossier missing; CSV `branding_spec` is NOT an acceptable fallback.
- **Reference products by name, not SKU.** SKU-first referencing was the upstream cause of br-001 conflations (project feedback).
- **All async.** Provider calls go through async clients; sub-agents are `async def execute(self, task, **kwargs)`.
- **`structlog` for logging.** Logs include `correlation_id`, `sku`, `provider`, `cost_usd` for tracing imagery cost across the pipeline.

## Don't

- Don't call FASHN / Tripo / Meshy APIs directly from outside this domain. Other cores must go through `ImageryCoreAgent` or delegate to `SkyyRoseImageryAgent` (legacy fallback).
- Don't add a new 3D provider without registering it in `_register_sub_agents()` AND adding the failover edge in the heal cycle.
- Don't bypass `hf_spaces` for HuggingFace-backed providers — quota tracking lives there and double-spend will exhaust accounts.
- Don't lower the quality threshold to make a flaky provider "work" — fix the provider or fail over. Quality threshold is the canary, not the obstacle.
- Don't skip dossier check. If the SKU dossier is missing → hard-fail with a clear error, not a CSV-spec fallback.

## Related

- `agents/core/base.py` — `CoreAgent`, `CoreAgentType`, `SelfHealingMixin`
- `agents/skyyrose_imagery_agent.py` — legacy fallback (called by `_get_legacy_imagery`)
- `agents/fashn_agent.py`, `agents/tripo_agent.py`, `agents/meshy_agent.py` — older standalone agents wrapped by these sub-agents
- `orchestration/asset_pipeline.py` — `ProductAssetPipeline` composes this core for batch processing
- `orchestration/threed_round_table.py` — multi-judge 3D quality vote (separate from text Round Table in `llm/`)
- Canonical catalog: `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`
- `renders/ghost-mannequin/SKIPPED.json` — Phase 14 skip list (2 accessories deferred to v1.3)
- Dossiers: `knowledge-base/products/<sku>/` (Corey-authored, never ML-drafted)

## Recent learnings

- ImageryCore was previously empty stub — now documented covering all 5 sub-agents (cmem #5466 2026-05-19).
- 3D pipeline architecture confirmed (cmem #3346, 2026-05-11): tripo_agent + meshy_agent + fashn_agent are the underlying clients; sub-agents wrap them with self-healing + quality gates.
- Tripo `.ai` vs `.com` regions need separate API keys — `hf_spaces` quota tracker handles routing.
- Quality gate threshold lives in `validation_scoring.py` (parent `agents/core/`). Adjusting it is an architectural decision, not a per-task knob.
