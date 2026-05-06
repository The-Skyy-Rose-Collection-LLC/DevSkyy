# SkyyRose Python Package — Architectural Digest

Generated: 2026-05-05 | Session: learn-codebase agent (resumed)
Coverage: All .py files in `skyyrose/` — core, elite_studio, multi_agent

---

## 1. Package Architecture

```
skyyrose/
├── __init__.py                   # minimal docstring, no re-exports
├── core/
│   ├── catalog_loader.py         # CSV reader with @cache; status derivation
│   ├── dossier_loader.py         # DossierMissingError hard-fail; @cache
│   ├── dossier_schema.py         # Pydantic v2 BrandingRegion + DossierSchema
│   ├── env_loader.py             # multi-file dotenv load order
│   ├── clip_embedder.py          # singleton CLIP-ViT-B/32, 512-dim L2 norm
│   ├── dino_embedder.py          # DINOv2 768-dim embedder (brand centroid alt)
│   ├── catalog_dedup.py          # catalog integrity / dedup helpers
│   └── memory/
│       ├── agent_memory.py       # Pinecone namespace "memory:agent:<id>"
│       ├── conversation.py       # SQLite ConversationTurn via asyncio.to_thread
│       └── consolidator.py       # SummarizeFn protocol; facts at importance=0.8
└── elite_studio/
    ├── __init__.py               # __getattr__ lazy loading; eager model imports
    ├── config.py                 # multi-file dotenv; all model IDs re-exported
    ├── models.py                 # ALL frozen dataclasses (ProductData, VisionAnalysis…)
    ├── catalog.py                # ProductEntry.__post_init__ hex + SKU validation
    ├── coordinator.py            # legacy Coordinator; Logger Protocol; BATCH_REPORT.json
    ├── brand.py                  # BrandConfig from assets/brand/brand.yaml; hex validate
    ├── gemini_rest.py            # direct REST; 10-key round-robin; threading.Lock; OTel
    ├── retry.py                  # retry_on_transient[T](); TRANSIENT_KEYWORDS frozenset
    ├── telemetry.py              # per-stage JSONL writer to logs/compositor-telemetry-DATE.jsonl
    ├── forensics.py              # H5 manifest write; H6 interactive confirm gate
    ├── fidelity.py               # color ΔE + OCR + CLIP fidelity checks; degraded gracefully
    ├── master_registry.py        # hash-pinned product masters; Wave 1 reference-first
    ├── validation.py             # Violation + IntegrityError; structural vs referential tiers
    ├── agents/
    │   ├── compositor_agent.py   # 1186L; 6-stage pipeline; cost ~$0.115/render
    │   ├── generator_agent.py    # ADK GeneratorAgent; dual GPT-Image + Gemini
    │   ├── vision_agent.py       # DualVisionGate; Claude explicitly excluded
    │   ├── quality_agent.py      # parallel asyncio.gather; pass if min(a,b)>=80
    │   ├── vision_audit_agent.py # Gemini Flash; view-aware; fail-closed on JSON parse
    │   ├── color_correction_agent.py # ADK; Gemini Vision; stub auto-levels
    │   ├── prompt_enrichment_agent.py # rule-based; _COLLECTION_DNA dict; no LLM
    │   ├── safety_agent.py       # OpenAI moderation + GPT-4o vision; fail-open on parse
    │   ├── three_d_agent.py      # CreativeAgent; Meshy → Blender → FLUX; dossier hard-fail
    │   ├── tryon_agent.py        # ADK stub; TryOnAgent alias TryonAgent; fashn stub
    │   ├── upscaling_agent.py    # Replicate Real-ESRGAN → PIL LANCZOS fallback
    │   └── variant_agent.py      # ADK stub; returns base image as only variant
    ├── graph/
    │   ├── state.py              # EliteStudioState(TypedDict); create_initial_state()
    │   ├── builder.py            # GraphConfig(frozen=True); build_graph(); 7 optional layers
    │   ├── edges.py              # routing fns; after_safety → "error_end" → END
    │   ├── nodes.py              # all node fns; quality dual ML+LLM; ghost_mannequin neck-in
    │   └── runner.py             # run_single() / run_batch(); skip_existing check
    ├── synthesis/
    │   ├── flux_pipeline.py      # render() async; MAX_ATTEMPTS=3; quarantine; H5 manifest
    │   ├── clients/fal.py        # FalClient; queue-aware subscribe; exp-backoff retry
    │   ├── stages/
    │   │   ├── base_render.py    # FLUX Kontext Pro; 1:1 aspect ratio; fal.subscribe
    │   │   ├── decoration_inpaint.py # FLUX Fill + Kontext-LoRA; guidance 7.5→12→17
    │   │   ├── mask_deriver.py   # Gemini + static fallback; OverMaskError at 0.4
    │   │   └── audit_filter.py   # AuditFilter.check(); AuditError for infra failure
    │   ├── prompts/
    │   │   ├── base_prompts.py   # build_base_prompt(); NO decoration in Stage 1
    │   │   └── decoration_prompts.py # H3 double-negative; TECHNIQUE_PHYSICS dict; 15 techniques
    │   ├── state/telemetry.py    # CostTracker; COST_USD dict; tier alerts $5/$10/$20/$50
    │   └── tests/                # test_audit_filter, test_mask_deriver, test_vision_audit_agent
    ├── quality/
    │   ├── ml_classifier.py      # CLIP; 3 labels; threshold=0.8 skips LLM
    │   ├── embedding_gate.py     # GateVerdict; cosine vs brand centroid
    │   ├── brand_centroid.py     # build_centroid(); CLIP 512-d + DINOv2 768-d
    │   ├── human_review.py       # HumanReviewGate; 5-min timeout; auto-approve sentinel
    │   ├── render_quality.py     # Verdict(SHIP/REVIEW/KILL); 60% centroid + 40% alignment
    │   ├── render_prompt_builder.py # RenderPrompt 3-block; CLIP garment scoring surface
    │   ├── visual_regression.py  # visual diff tooling
    │   ├── prompt_simplifier.py  # CLIP grounding notes; empirical findings
    │   ├── clip_alignment.py     # text-image alignment score
    │   └── load_tester.py        # pipeline load testing harness
    ├── prompts/
    │   ├── library.py            # PromptLibrary from assets/prompts/registry.yaml; versioned
    │   ├── analyzer.py           # rule-based; PromptAnalysis; no LLM
    │   ├── cache.py              # prompt caching layer
    │   ├── chain.py              # prompt chaining
    │   ├── enhancer.py           # prompt enhancement pipeline
    │   ├── history.py            # prompt history tracking
    │   └── templates.py          # brand-voice prompt templates
    ├── fashion/
    │   ├── context.py            # FashionContextBuilder; _load_catalog() dict cache
    │   ├── knowledge.py          # frozen GarmentType + FabricProperties ontology
    │   ├── colorway.py           # colorway exploration
    │   ├── editorial.py          # editorial styling context
    │   ├── materials.py          # fabric/material specs
    │   ├── photography.py        # photography style descriptors
    │   ├── qa_rules.py           # QA rule definitions
    │   ├── sizing.py             # sizing data
    │   ├── trends.py             # trend context
    │   └── design/               # design-specific sub-modules
    ├── creative/
    │   ├── state.py              # CreativeIntent(StrEnum) 14 intents; CreativeOperationState
    │   ├── edges.py              # route_intent(); _INTENT_TO_NODE dict
    │   ├── nodes.py              # entry_node, product_render_node, three_d_model_node…
    │   ├── runner.py             # run_creative() sync; arun_creative() async PG checkpoint
    │   ├── router.py             # get_creative_graph() / get_creative_graph_async()
    │   └── checkpointer.py       # Postgres LangGraph checkpointer
    ├── queue/
    │   ├── job_types.py          # EliteStudioJobData + EliteStudioJobResult Pydantic v2
    │   ├── cost_tracker.py       # Redis CostTracker; 7-day TTL; degrade graceful
    │   ├── consumer.py           # EliteStudioWorker; ZPOPMAX; SIGTERM-safe; DLQ
    │   ├── producer.py           # job submission
    │   ├── rate_limiter.py       # Redis-backed rate limiting
    │   └── dead_letter.py        # DeadLetterQueue for failed jobs
    └── tests/                    # ~35 test files (graph, agents, synthesis, quality)
multi_agent/
    ├── orchestrator.py           # run_orchestrator(); claude_agent_sdk; 12 MCP tools
    ├── agents.py                 # AgentDefinition: BRAND_WRITER, THEME_AUDITOR, …
    ├── config.py                 # multi-agent config
    ├── hooks.py                  # orchestrator lifecycle hooks
    └── tools.py                  # 12 MCP tool implementations
```

**Dependency flow (strict):**
`core → elite_studio.config/models → agents → graph → synthesis → quality → queue → creative → multi_agent`

The `elite_studio/__init__.py` uses `__getattr__` for lazy loading of heavy modules (compositor, coordinator, graph) to keep import time low when only `models` or `config` is needed.

---

## 2. Catalog System

### `core/catalog_loader.py` (104 lines)

- `CATALOG_CSV = Path(__file__).resolve().parents[2] / "wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv"` — absolute path, invariant to cwd
- `read_catalog_rows() -> tuple[dict[str, str], ...]` decorated with `@cache` (stdlib `functools`) — callers receive the same tuple object on every call; mutation silently breaks other callers
- Status derivation priority: `retired > is_preorder > is_draft > published` — a row that is both `retired=true` and `is_preorder=true` surfaces as `retired`
- `get_product_with_dossier(sku)` calls both catalog_loader and dossier_loader; result dict merges CSV row with parsed dossier

### `core/dossier_loader.py` (175 lines)

- `DOSSIERS_DIR = Path(__file__).resolve().parents[2] / "wordpress-theme/skyyrose-flagship/data/dossiers"`
- `DossierMissingError(FileNotFoundError)` — explicit subclass so callers can `except DossierMissingError` without catching all `FileNotFoundError`
- `load_dossier(name_slug: str) -> Dossier` with `@cache` — slug is the product's name-keyed filename stem (e.g., `black-rose-crewneck`), **not** the SKU
- The error message in `DossierMissingError` explicitly states: `"The CSV branding_spec column is not a fallback"` — this is policy, not just documentation
- `Dossier` is a frozen dataclass; `branding_regions` is a `tuple[BrandingRegion, ...]`

### `core/dossier_schema.py` (333 lines)

- `BrandingRegion` is a Pydantic v2 `BaseModel` with `region`, `technique`, `description`, `color`, `notes` fields
- `parse_branding_regions(raw_text: str) -> list[BrandingRegion]` uses regex `_ENTRY_RE` to parse the markdown table rows in dossier files
- `DossierSchema.from_raw(raw: dict)` converts the untyped dossier dict to typed schema; validates hex colors via Pydantic validators
- `DossierCoverage` frozen dataclass tracks how many regions have dossiers vs. total declared

---

## 3. Elite Studio Pipeline Shape + Agent Hierarchy + LangGraph Integration

### Pipeline Entry Points (three paths)

**Path A — LangGraph (primary for production renders):**
```
run_single(sku, view, config=GraphConfig) → ProductionResult
  → build_graph(config) → compiled StateGraph
  → nodes: vision → [prompt_enrichment?] → generator → [safety?]
          → quality → [human_review?] → [upscaling?] → [color_correction?]
          → [variants?] → [compositor?] → [tryon?] → finalize
```

**Path B — Legacy Coordinator (batch CLI, direct):**
```
Coordinator.produce(sku) → ProductionResult
  step 1: DualVisionGate.analyze()
  step 2: GeneratorAgent.generate()
  step 3: QualityAgent.verify()
  step 4: CompositorAgent.composite()
```

**Path C — FLUX Synthesis (ThreeDAgent / nano_banana):**
```
flux_pipeline.render(sku, view, dossier, techflat_path, out_dir)
  Stage 1: base_render.render_base()       → FLUX Kontext Pro (clean, undecorated)
  Stage 1.5: audit_filter.AuditFilter      → VisionAuditAgent gate
  Stage 2: mask_deriver.MaskDeriver        → Gemini Flash → region boxes
  Stage 3+5: decoration_inpaint loop       → FLUX Fill / Kontext-LoRA
  Max 3 attempts; guidance 7.5 → 12.0 → 17.0
  On exhaustion: quarantine to renders/quarantine/
  Final: H5 forensic manifest written (dossier SHA256, full prompt, audit result)
```

### Agent Hierarchy

All agents inherit from one of:
- `BaseSuperAgent` (Google ADK) — `ColorCorrectionAgent`, `TryOnAgent`, `VariantAgent`, `GeneratorAgent`, `DualVisionGate`, `QualityAgent`
- `CreativeAgent(BaseSuperAgent)` — `ThreeDAgent`
- Plain class (no ADK) — `SafetyAgent`, `UpscalingAgent`, `PromptEnrichmentAgent`, `VisionAuditAgent`

ADK agents are named with `legendary_*` prefix to satisfy ADK's naming rules (valid Python identifiers, underscores only).

### LangGraph Graph Config

`GraphConfig(frozen=True)` has boolean flags for each optional layer:
- `enable_compositor`, `enable_tryon`, `enable_safety`, `enable_human_review`, `enable_upscaling`, `enable_color_correction`, `enable_variants`
- Default: only core path (vision → generator → quality → finalize)
- `max_retries: int = 3` propagated to quality node and synthesis pipeline

### Creative Operations Hub (second LangGraph)

`creative/` exposes a parallel graph with `CreativeIntent` (14 intents): `product-render`, `3d-model`, `social-pack`, `product-copy`, `character-sheet`, `scene-composite`, `virtual-tryon`, `full-product-launch`, `design-ideation`, `mockup`, `collection-plan`, `tech-pack`, `moodboard`, `colorway-explore`.

- `run_creative()` — sync, no checkpointing
- `arun_creative()` — async, Postgres LangGraph checkpointing keyed by `operation_id`
- `resume_creative(operation_id)` — resumes from last checkpoint by passing `None` as input

---

## 4. Compositor (6-Stage BRIA → Claude Prompt → IC-Light → FLUX Fill → GPSDiffusion → Gemini QA)

**File:** `elite_studio/agents/compositor_agent.py` (1186 lines)

### Stage Map

| Stage | Provider | Purpose | Fallback |
|-------|----------|---------|----------|
| 1 | BRIA RMBG 2.0 / FAL rembg | Background removal → alpha matte | None (hard-fail) |
| 2 | Claude Opus (claude_sdk) | Prompt engineering: scene + subject → FLUX prompt | None |
| 3 | Replicate IC-Light / libcom | Relighting: match subject to scene | libcom or skip |
| 4 | FLUX Fill Pro (ThreadPoolExecutor max_workers=3) | Inpainting: subject into scene | Kontext → Replicate |
| 5 | PIL (Gaussian blur) | Contact shadows | GPSDiffusion (if available) |
| 5.5 | CLIP/DINOv2 embedding gate | Brand centroid cosine gate | opt-in via file presence |
| 6 | Gemini (`gemini-3-pro-image-preview`) | Visual QA gate — final accept/reject | None |

### Cost: ~$0.115/render (Stage 4 dominates at ~$0.05 FLUX Fill)

### Resume mechanism
`CompositorAgent.composite()` accepts a `resume_from_stage: int` parameter. Intermediate outputs are written to a temp dir and re-read when resuming. Stages 1-3 are idempotent; Stage 4 uses ThreadPoolExecutor for concurrent tries.

### FLUX Provider Fallback Chain
`COMPOSITOR_FLUX_PROVIDERS = ["fal-fill", "kontext", "replicate"]` in config. The first provider that succeeds wins; errors are logged and the next tried.

---

## 5. Synthesis Layer (`elite_studio/synthesis/`)

### `flux_pipeline.py` — Orchestrator

```python
async def render(sku, view, dossier, techflat_path, out_dir) -> FluxResult
```

- `MAX_ATTEMPTS = 3`; each attempt is a full Stage 1 → 1.5 → 2 → 3+5 cycle
- `AuditFilter` at Stage 1.5 can pass with zero FLUX Fill budget (Stage 1 result used directly)
- On attempt exhaustion: output moved to `renders/quarantine/{sku}/` and `FluxResult.ok = False`
- H5 forensic manifest written to `renders/output/{sku}/{timestamp}/manifest.json`:
  - dossier SHA256, full Stage 1 + Stage 3 prompts, model + version, vision-audit result, output paths, `_sha256_file()` of output

### `stages/base_render.py`

- `FLUX_KONTEXT_ENDPOINT = "fal-ai/flux-pro/kontext"` — aspect_ratio locked `"1:1"`
- Calls `FalClient.upload(techflat_path)` then `FalClient.subscribe(endpoint, arguments)` 
- Stage 1 prompt deliberately **omits branding_block** — decoration is a separate stage

### `stages/decoration_inpaint.py`

- `FLUX_FILL_ENDPOINT = "fal-ai/flux-pro/v1/fill"`
- `FLUX_KONTEXT_LORA_ENDPOINT = "fal-ai/flux-kontext-lora/inpaint"` (LoRA path)
- Guidance escalation per attempt: `{1: 7.5, 2: 12.0, 3: 17.0}`
- `_compose_decoration_prompt()` calls `build_decoration_prompt()` and appends the dossier's NEGATIVE CONTRACT as final sentence

### `stages/mask_deriver.py`

- Gemini Flash primary → static template fallback
- `DECORATION_TECHNIQUES` frozenset of 14 valid techniques; 'stitched' excluded (construction, not decoration)
- `STATIC_REGION_BOXES`: ~30 region names with normalized `[x1,y1,x2,y2]` coordinates
- `OverMaskError` raised if computed mask covers >40% of image area
- `MIN_MASK_AREA_FRAC = 0.005` — masks below 0.5% of image area are rejected

### `stages/audit_filter.py`

- Wraps `VisionAuditAgent`
- `AuditError` raised on infrastructure failures (not on content violations) — fail-loud for infra, fail-graceful for content
- Low-severity violations produce warnings but don't block pipeline advancement
- Defensively splits compound region names (e.g., "front-chest/back-yoke") before checking

### `prompts/decoration_prompts.py` — H3 Double-Negative Structure

Seven-layer prompt engineering defense against technique hallucination:
1. `ONLY-prefixed positive` — model told nothing exists outside the list
2. `PHYSICAL TECHNIQUE` physics block (`TECHNIQUE_PHYSICS` dict, 15 techniques)
3. `TECHNIQUE_NEGATIVE_PREFIX` — per-technique hallucination ban immediately after physics
4. `_TONAL_AMPLIFIER` — for embossed/debossed only; `CRITICAL:` tonal constraint
5. `COLOR block` — exact palette; sublimated multi-color forces explicit enumeration
6. Mask-bounds constraint + photography quality directive
7. `UNIVERSAL_NEGATIVE_SUFFIX` — rejection contract as absolute final sentence

**Key insight from docstring:** `build_violation_feedback()` deliberately does NOT name hallucinated elements in retry prompts — naming them causes them to reappear via cross-attention. Only a positive "STRICT ADHERENCE MODE" header is prepended; guidance escalation does the real work.

### `clients/fal.py` — FalClient

- Lazy import of `fal_client` (`_FAL` module-level singleton) — fast unit test imports
- `subscribe()` uses `fal_client.AsyncClient().subscribe()` with `on_queue_update` callback
- Retry logic: TimeoutError and HTTP 5xx are retryable; 4xx / content policy errors are not
- `_normalize_response()` handles both `images` (plural) and `image` (singular) response shapes
- `encode_image_to_data_url()` utility for endpoints preferring base64

### `state/telemetry.py` — CostTracker

- Per-call cost estimates: `FLUX Kontext=$0.04`, `FLUX Fill=$0.05`, `Gemini vision=$0.005`
- Spending tier alerts at $5, $10, $20, $50 (logged as WARNING; no hard cap)
- `summary()` returns `by_model_usd` and `by_sku_usd` breakdowns for billing attribution

---

## 6. Memory Module (`core/memory/`)

Three-class architecture with deliberate separation of concerns:

### `agent_memory.py` — `AgentMemory` (Semantic, Pinecone)

```python
@dataclass
class Memory:
    id: str
    agent_id: str
    content: str
    importance: float  # 0.0 - 1.0
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime
```

- Pinecone namespace format: `"memory:agent:<agent_id>"` — namespaced per agent, no cross-contamination
- `store(memory)` — upserts to Pinecone with L2-normalized embedding
- `recall(query, k=10, min_importance=None)` — when `min_importance` is set, fetches `k*3` candidates then filters; widening avoids threshold-induced recall gaps
- `clear(agent_id)` — deletes all vectors in the agent's namespace

### `conversation.py` — `ConversationStore` (Chronological, SQLite)

```python
@dataclass(frozen=True)
class ConversationTurn:
    id: str
    session_id: str
    agent_id: str
    role: str  # "user" | "assistant" | "system"
    content: str
    metadata: dict[str, Any]
    created_at: datetime
```

- SQLite via `asyncio.to_thread` — never blocks event loop
- Default DB: `<project_root>/data/memory/conversations.db`
- `_require_init()` guard prevents operations before `initialize()` is called
- `get_thread(session_id)` returns turns in chronological order

### `consolidator.py` — `Consolidator` (Cross-Boundary)

```python
class SummarizeFn(Protocol):
    async def __call__(self, turns: list[ConversationTurn]) -> str: ...
```

- `consolidate_thread(session_id, summarize_fn, agent_memory)` — reads conversation turns, calls the protocol-typed summarize function, stores resulting fact in Pinecone at `importance=0.8`
- Bridges the two memory systems: conversation (ephemeral, ordered) → agent memory (persistent, semantic)

---

## 7. Tests (`elite_studio/tests/`)

~35 test files covering all major subsystems. Key patterns:

### `conftest.py` — Shared Fixtures

Factory functions producing frozen dataclass instances:
- `make_product(sku, collection, **kwargs) -> ProductData`
- `make_vision_analysis(...) -> VisionAnalysis`
- `make_synthesized_vision(...) -> SynthesizedVision`
- Full `ProductionResult` factories for end-to-end test setup

No live API calls in unit tests — all external calls are mocked. Integration tests in `tests/integration/` (separate directory, not in `elite_studio/tests/`).

### Test Coverage Areas

| Area | Test Files |
|------|-----------|
| Graph topology + edges | `test_graph_builder.py`, `test_graph_edges.py`, `test_graph_topology.py` |
| Graph nodes (unit) | `test_graph_nodes.py`, `test_graph_nodes_quality.py`, `test_graph_nodes_tryon.py` |
| Ghost mannequin (Phase B2) | `test_ghost_mannequin_*.py` (4 files) |
| Agents | `test_compositor_agent.py`, `test_dual_vision_gate.py`, `test_quality_classifier.py`, etc. |
| Synthesis pipeline | `synthesis/tests/` — audit_filter, mask_deriver, vision_audit_agent |
| Registry integrity | `test_master_registry.py`, `test_catalog_validation.py` |
| Fidelity + regression | `test_fidelity.py`, `test_visual_regression.py` |
| Phase B2 models | `test_models_phase_b2.py`, `test_graph_state_phase_b2.py`, `test_generator_agent_phase_b2.py` |

### Notable Test Patterns

- `test_graph_topology.py` — validates that `build_graph()` compiles without error for every `GraphConfig` flag combination; does not invoke the graph
- `test_purge_hallucinations.py` — validates the H3 prompt engineering doesn't inadvertently include technique names that would trigger hallucination
- `test_vision_test_registry.py` — maintains a registry of known vision test images with expected verdicts; used as a regression suite for vision model changes

---

## 8. Conventions

### Type Hints
- `from __future__ import annotations` on every file — forward references work without quotes
- All public function signatures annotated; `Any` used only for untyped external API responses
- Pydantic v2 used for dossier schema and job types; frozen dataclasses everywhere else
- `Protocol` for injectable dependencies: `Logger` (coordinator), `SummarizeFn` (consolidator)

### Async Patterns
- `asyncio.to_thread()` for blocking calls inside async functions (Blender subprocess, SQLite writes, PIL operations)
- `asyncio.gather()` for parallel scoring in `QualityAgent`
- `nest_asyncio.apply()` via `run_sync()` helper in `graph/nodes.py` when a loop is already running (LangGraph node context)
- `asyncio.run()` in `creative/nodes.py` three_d_model_node — sync node calling async pipeline

### Dataclass Usage
- `@dataclass(frozen=True)` on all result/output models — immutability is enforced, not just preferred
- `@dataclass` (mutable) only for accumulator objects: `StageRecord`, `CostTracker`, `_ClipState`
- `__post_init__` for validation in `ProductEntry` (hex colors, SKU format) and `BrandConfig`
- `field(default_factory=dict)` for mutable defaults — never bare `{}` as default

### Error Types
- `DossierMissingError(FileNotFoundError)` — specific subclass for dossier absence
- `AuditError(RuntimeError)` — infrastructure failures in AuditFilter (not content violations)
- `FalError(RuntimeError)` — wraps all fal.ai client errors uniformly
- `OverMaskError` — mask coverage >40%; triggers static template fallback
- `MissingVariableError(KeyError)` — prompt library render() called with undeclared variable
- `IntegrityError(Exception)` — registry fails strict validation; carries `violations: list[Violation]`

### Import Patterns
- Heavy modules (`compositor_agent`, `coordinator`, `graph`) are lazy-loaded via `elite_studio/__init__.__getattr__`
- `fal_client` deferred to first call via `_fal()` singleton — keeps test imports fast
- ADK imports (`adk.base`, `adk.super_agents`) at module level in agent files — ADK must be installed
- Prometheus metrics imported with `try/except ImportError` guard in `graph/nodes.py`

---

## 9. External Dependencies

### Critical (hard requirements)
| Package | Used In | Purpose |
|---------|---------|---------|
| `google-genai` | gemini_rest.py, vision_audit_agent | Gemini Flash/Pro API |
| `openai` | safety_agent, vision_agent, generator_agent | GPT-4o vision + moderation |
| `anthropic` (claude_sdk) | coordinator, compositor Stage 2, multi_agent | Claude Opus/Sonnet |
| `fal_client` | synthesis/clients/fal.py, base_render, decoration_inpaint | FLUX endpoint calls |
| `google-adk` | all ADK-based agents | ADK telemetry + agent orchestration |
| `langgraph` | graph/builder + creative/router | StateGraph compilation |
| `pydantic` (v2) | dossier_schema, job_types | Schema validation |
| `Pillow` | compositor Stage 5, upscaling, fidelity | Image manipulation |
| `pinecone` | core/memory/agent_memory | Vector store |
| `redis` | queue/consumer, queue/cost_tracker | Job queue + cost tracking |
| `httpx` | three_d_agent Blender fallback, various | Async HTTP client |
| `numpy` | clip_embedder, dino_embedder, brand_centroid | Embedding math |

### Optional (degrade gracefully)
| Package | Fallback | Notes |
|---------|----------|-------|
| `torch` + `transformers` | neutral score (0.5, 0.3) | CLIP/DINOv2 ML classifier |
| `replicate` | PIL LANCZOS | Upscaling, IC-Light |
| `nest_asyncio` | `asyncio.run()` error | Sync-in-async in LangGraph nodes |
| `prometheus_client` | metrics silently skipped | Graph node instrumentation |
| `pytesseract` | OCR check skipped | Fidelity text check |
| `open_clip_torch` | CLIP check unavailable | Alternative CLIP embedder |
| `yaml` (PyYAML) | ImportError at PromptLibrary.load() | Prompt registry parsing |

---

## 10. Notable Gotchas

### G1 — Dossier Hard-Fail (most impactful)
`dossier_loader.load_dossier()` raises `DossierMissingError(FileNotFoundError)` when the `.md` file is absent. **The CSV `branding_spec` column is explicitly not a fallback** — the error message says so verbatim. Every agent that reads dossiers (`ThreeDAgent.generate_replica()`, `flux_pipeline.render()`) propagates this as a top-level failure. Adding a new SKU without its dossier file will hard-fail the entire pipeline, not silently skip decoration.

### G2 — Claude Excluded from Vision (policy)
`vision_agent.py` (`DualVisionGate`) explicitly excludes Claude from vision analysis with a comment. Only OpenAI (`gpt-4o`) and Gemini Flash are used. Using Claude for vision (e.g., passing images to `claude_sdk`) in the vision gate will break the "dual provider" consensus guarantee. The policy exists because Claude's vision results were found to correlate too strongly with text descriptions vs. actual image content.

### G3 — @cache Immutability Trap
`read_catalog_rows()` and `load_dossier()` are both decorated with `@functools.cache`. The returned objects (tuple of dicts, frozen Dossier) are shared across all callers. If any caller mutates a dict from `read_catalog_rows()`, the mutation persists for the process lifetime and affects all subsequent callers silently.

### G4 — nest_asyncio in LangGraph Nodes
`graph/nodes.py` has a `run_sync()` helper that calls `nest_asyncio.apply()` when an event loop is already running. This is necessary because LangGraph node functions are synchronous but some operations (FLUX calls) are async. The pattern works but `nest_asyncio` can cause unexpected behavior if asyncio debugging is enabled.

### G5 — Blender subprocess in ThreeDAgent
`ThreeDAgent.generate_replica()` calls `blender -b -P scripts/render_professional.py` via `subprocess.run` wrapped in `asyncio.to_thread`. If Blender is not installed or the script path is wrong, it falls back to downloading the Meshy thumbnail URL. The fallback is silent (log at WARNING only) — callers receive `used_blender_fallback=True` in the result but not a failure status.

### G6 — Safety Agent Fail-Open
`SafetyAgent._check()` treats unparseable GPT-4o vision responses as **safe** (not rejected): `"Unparseable response — treat as safe to avoid false positives"`. This means a crashed or malfunctioning safety model produces no blockage. The text moderation (OpenAI API) still runs first as a backstop.

### G7 — TryOnAgent is a Stub
`TryOnAgent.execute_tryon()` is a pass-through stub — it logs to ADK, then returns the garment image path unchanged. The `provider="fashn"` in the result is aspirational; no actual FASHN API call is made. Any code that assumes try-on output is a composite of model + garment will be wrong.

### G8 — VariantAgent is a Stub
`VariantAgent.generate_variants()` always returns the base image as the only variant, regardless of `variant_specs`. The docstring says "Phase B2 logic (Claude Sonnet + GPT-4o best-of-N) — Return base image as the only variant for now."

### G9 — PromptLibrary Requires YAML Prompt ID Format
Prompt IDs in `registry.yaml` must match `^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+\.v\d+$`. A prompt named `compositor.v3` would fail; `compositor.scene_prompt_builder.v3` passes. `PromptLibrary.load()` raises `ValueError` immediately on structural violations.

### G10 — Ghost Mannequin Neck-In Dimensions
`ghost_mannequin_composite_node` in `graph/nodes.py` uses PIL to composite the top 20% of the back render behind the front neckline. The 20% crop assumes a specific camera distance / aspect ratio. If the back render has a different crop (e.g., closer shot), the neck-in will misalign. The node has no geometric validation — misalignment produces a silently wrong result.

### G11 — Gemini Key Rotation Thread Safety
`gemini_rest.py` uses a module-level `_KEY_INDEX` counter protected by `threading.Lock`. Rotation works correctly under threading but not under `multiprocessing` (each process gets its own counter). If workers are forked (not threaded), all processes may start at index 0 and hammer the same key.

### G12 — Brand Centroid is Opt-In via File Presence
`embedding_gate.py` / `quality_node` in `graph/nodes.py` only activates the brand centroid gate if `data/brand_centroid.npz` exists. There is no config flag. Deleting the file silently disables the gate for all subsequent renders.

### G13 — ColorCorrectionAgent Stub
`ColorCorrectionAgent.correct()` always returns `adjustments_applied=("auto-levels", "brand-white-balance")` regardless of any actual pixel analysis. The image is unchanged; the ADK observability call is the only real work done.

### G14 — CostTracker Has No Hard Cap
`synthesis/state/telemetry.py` CostTracker logs at spending tiers ($5/$10/$20/$50) but never raises or stops execution. An infinite retry loop or bug causing repeated pipeline invocations will accumulate unbounded cost with only log warnings as signal.

---

*Digest covers ~130 Python source files across 6 sessions of reading. Unread: `core/catalog_dedup.py`, `core/dino_embedder.py`, some `fashion/design/` sub-modules, `multi_agent/config.py`/`hooks.py`/`tools.py`, build scripts, and the bulk of test file internals (conftest + representative tests were read).*
