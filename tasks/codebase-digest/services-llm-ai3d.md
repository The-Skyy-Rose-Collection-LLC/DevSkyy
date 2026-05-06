# DevSkyy Services / LLM / AI-3D / Monitoring — Codebase Digest

_Generated 2026-05-05. Covers: `llm/` (29 files), `services/` (~45 files), `ai_3d/` (8 files + 3 providers), `monitoring/` (6 files)._

---

## 1. Module Map

### llm/
| File | Role |
|------|------|
| `base_client.py` | Abstract `BaseLLMClient` — async httpx, exponential backoff, circuit breaker |
| `unified_client.py` | `UnifiedLLMClient` — wraps all providers behind single `generate()` |
| `router.py` | `LLMRouter` — routing strategies (ROUND_ROBIN, COST_OPTIMIZED, PERFORMANCE, FAILOVER) |
| `round_table.py` | `LLMRoundTable` v2.0.0 — parallel generation + Bayesian A/B + Claude judge + Neon DB |
| `judge.py` | `CreativeJudge` — BRAND_DNA(45%) + EXECUTION_QUALITY(35%) + PROMPT_QUALITY(20%) |
| `statistical_analyzer.py` | Welch's t-test, Cohen's d, Cliff's delta, Bayesian Monte Carlo (10k samples) |
| `providers/anthropic.py` | Claude adapter (tool use, vision, streaming) |
| `providers/openai.py` | GPT-4o/o1 adapter (tool use, vision, streaming) |
| `providers/google.py` | Gemini adapter (multimodal, grounding) |
| `providers/mistral.py` | Mistral adapter |
| `providers/cohere.py` | Cohere adapter |
| `providers/groq.py` | Groq adapter (low-latency) |
| `cache.py` | Redis-backed LLM response cache — SHA-256 keyed, TTL configurable |
| `cost_tracker.py` | Per-model cost accounting (USD), persisted to DB |
| `token_counter.py` | Token counting utilities for cost estimation |
| `streaming.py` | `AsyncStreamingAggregator` — merges parallel `StreamChunk` sequences |
| `tool_executor.py` | `ToolCallExecutor` — executes structured tool calls from LLM responses |
| `context_manager.py` | Sliding-window context truncation for long conversations |
| `prompt_templates.py` | Jinja2-based prompt templates per task type |
| `retry_handler.py` | Standalone retry with per-exception configurable retryable set |
| `circuit_breaker.py` | Shared circuit breaker (5 failures → OPEN, 60s HALF_OPEN) |
| `schemas.py` | Pydantic models: `Message`, `CompletionResponse`, `StreamChunk`, `ToolCall` |
| `config.py` | Provider API key loading + model alias table |
| `__init__.py` | Public API re-exports |
| `enums.py` | `LLMProvider`, `MessageRole`, `ResponseFormat` enums |
| `exceptions.py` | `LLMError`, `RateLimitError`, `ContextLengthExceeded`, `ProviderUnavailable` |
| `validators.py` | Input/output schema validation |
| `metrics.py` | Per-provider latency/cost/error counters |

### services/
| Directory / File | Role |
|-----------------|------|
| `ai_image_enhancement.py` | Orchestration wrapper for the ml/enhancement sub-pipeline |
| `approval_queue_manager.py` | Human-in-the-loop approval gate with timeout/escalation |
| `image_deduplication.py` | Perceptual hashing dedup across uploaded product images |
| `image_ingestion.py` | Ingest images from URL/upload, validate, queue for processing |
| `rag_anything_service.py` | RAG pipeline wrapping LangChain retrievers; uses `structlog` |
| `analytics/event_collector.py` | Clickstream/domain event producer |
| `analytics/alert_engine.py` | Threshold/anomaly alerting with JSONB context storage |
| `analytics/alert_notifier.py` | Multi-channel alert delivery (email, Slack, PagerDuty) |
| `analytics/rollup_scheduler.py` | Periodic aggregation jobs (hourly/daily/weekly) |
| `competitive/competitor_analysis.py` | Price/product competitive intelligence (vision stub) |
| `competitive/schemas.py` | Pydantic models for competitive data |
| `notifications/email_notifications.py` | SMTP email delivery |
| `storage/r2_client.py` | Cloudflare R2 async client |
| `storage/schemas.py` | Storage object metadata models |
| `storage/version_manager.py` | Asset versioning with restore capability |
| `ml/__init__.py` | Module init + `get_service()` singletons |
| `ml/gemini_client.py` | Gemini multimodal client — enum: `FLASH_2_0`, `FLASH_2_5`, `PRO_2_5`, `FLASH_IMAGE`, `PRO_IMAGE` |
| `ml/image_description_pipeline.py` | 3-stage pipeline: describe → extract → optimize |
| `ml/pipeline_orchestrator.py` | 6-stage checkpoint/resume pipeline: INGEST→VALIDATE→BG_REMOVAL→LIGHTING→UPSCALE→FORMAT→COMPLETE |
| `ml/processing_queue.py` | `deque`-based async queue with DLQ and `DEFAULT_FALLBACK_CHAINS` |
| `ml/replicate_client.py` | Replicate async client (polling model) |
| `ml/watermark_service.py` | DCT steganography on blue channel (`WATERMARK_MAGIC = b"DSKY"`) |
| `ml/visual_feature_extractor.py` | CLIP/ViT feature extraction for similarity search |
| `ml/enhancement/authenticity_validator.py` | 3-gate QA: dHash ≥95%, Delta-E ≤2.0, edge similarity ≥85% |
| `ml/enhancement/background_removal.py` | BRIA RMBG + PIL compositing (SOLID_COLOR/CUSTOM_IMAGE are TODO stubs) |
| `ml/enhancement/upscaling.py` | Real-ESRGAN upscaling (HF Inference API) |
| `ml/enhancement/format_optimizer.py` | WebP/AVIF conversion with quality tuning |
| `ml/enhancement/lighting_normalization.py` | GFPGAN (face model — wrong model for clothing) |
| `ml/prompts/vision_prompts.py` | 5 brand-wired prompt templates (luxury, casual, technical, minimal, storytelling) |
| `ml/schemas/description.py` | `VisionModel` enum (`GEMINI_PRO`, `GEMINI_FLASH`) + `DescriptionOutput` |
| `three_d/provider_interface.py` | `I3DProvider` Protocol + `ThreeDRequest`/`ThreeDResponse` + `OutputFormat`/`QualityLevel` enums |
| `three_d/provider_factory.py` | `ThreeDProviderFactory` — circuit breaker per provider, health cache TTL 30s, weighted selection |
| `three_d/gemini_provider.py` | `GeminiImageProvider` — image generation (not true 3D; lies about GLB output) |
| `three_d/huggingface_provider.py` | TRELLIS/TripoSR/InstantMesh/ShapE/Hunyuan3D via Gradio (sync calls inside async) |
| `three_d/replicate_provider.py` | Wonder3D (image→3D) + ShapE (text→3D) via Replicate |
| `three_d/tripo_provider.py` | Thin adapter over `agents.tripo_agent` private methods |

### ai_3d/
| File | Role |
|------|------|
| `generation_pipeline.py` | `ThreeDGenerationPipeline` — 5 stages: preprocess→select→generate→validate→enhance |
| `model_generator.py` | `AI3DModelGenerator` — HuggingFace path or 7-stage local pipeline |
| `quality_enhancer.py` | `ModelQualityEnhancer` — mesh repair + optimization + texture upscale + PBR materials |
| `resilience.py` | `CircuitBreaker` + `RetryStrategy` + `GracefulDegradation` + `ResilientAPIClient` |
| `virtual_photoshoot.py` | `VirtualPhotoshootGenerator` — pyrender/trimesh scenes, social crops, web-optimized WebP |
| `providers/huggingface.py` | `HuggingFace3DClient` — async httpx, rate limit semaphore(5), 2s inter-call delay, TRELLIS preferred |
| `providers/meshy.py` | `MeshyClient` — image→3D / text→3D / retexture; meshy-5 API; polls SUCCEEDED |
| `providers/tripo.py` | `TripoClient` — image→3D / text→3D; Pydantic input validation + XSS sanitization |

### monitoring/
| File | Role |
|------|------|
| `__init__.py` | Empty |
| `ab_comparison.py` | `ABComparisonTracker` — QC scores in Redis sorted sets, p50/p95/win_rate stats |
| `elite_studio_metrics.py` | Prometheus counters/histograms/gauges for Elite Studio pipeline |
| `prometheus_metrics.py` | Full MCP server Prometheus instrumentation (15 metrics, `@monitored_tool` decorator) |
| `metrics_server.py` | Standalone HTTP server (`/metrics`, `/health`, `/`) on port 9090 |
| `stream_processor.py` | `StreamProcessor` — Kafka consumer, in-memory aggregations, Redis flush |

---

## 2. Key Abstractions

### LLM Layer
- **`BaseLLMClient`** (abstract): `generate()`, `stream()`, `count_tokens()`, `close()` — all providers implement this. Retry and circuit breaker live here.
- **`LLMProvider` enum**: 7 values including `LLAMA` which maps to xAI/Grok (not Meta Llama). Naming mismatch is a live bug.
- **`LLMRoundTable`**: parallel N-provider generation → `StatisticalAnalyzer` winner selection → optional Claude judge audit → Neon DB scoring. The most complex LLM subsystem.
- **`CreativeJudge`**: weighs BRAND_DNA(45%), EXECUTION_QUALITY(35%), PROMPT_QUALITY(20%). Brand DNA checks read from `knowledge-base/seed/from-interview.md`.

### Services Layer
- **Module singleton pattern**: every service module exposes `_service: T | None = None` + `get_service()` factory. No DI container.
- **`PipelineOrchestrator`**: 6-stage checkpoint/resume image pipeline. Checkpoints stored in DB. Resumable after crash.
- **`AuthenticityValidator`**: final QA gate before auto-publish. Three independent image comparison checks, all must pass.
- **`I3DProvider` Protocol**: unified interface for all 3D backends in `services/three_d/`. Runtime-checkable via `isinstance`.

### AI-3D Layer
- **Dual abstraction**: `ai_3d/` providers (HuggingFace3DClient, MeshyClient, TripoClient) are direct API clients. `services/three_d/` providers wrap them with circuit breakers and factory routing. The two layers are parallel and non-unified — there is no shared parent.
- **`ResilientAPIClient`** (`ai_3d/resilience.py`): stacks circuit breaker → retry → graceful degradation in correct order.
- **`VirtualPhotoshootGenerator`**: uses pyrender (preferred) → trimesh fallback for headless rendering. Generates hero image, social crops (6 platforms), and 4 WebP sizes.

### Monitoring Layer
- **Two metric registries**: `prometheus_metrics.py` registers at module import time (global). `elite_studio_metrics.py` uses lazy `_make_counter/histogram/gauge` with duplicate-registration guards. `prometheus_metrics.py` imports Elite Studio metrics at bottom to merge both into a single Prometheus scrape.
- **`StreamProcessor`**: Kafka consumer with FIFO `OrderedDict` dedup (10k entries), dispatch table, per-event-type memory caps, Redis flush every 60s.
- **`ABComparisonTracker`**: Redis sorted sets per provider:model pair, capped at 10k entries. Degrades gracefully when Redis is unavailable.

---

## 3. Data Flow

### Image Generation Pipeline
```
Ingest (URL/upload)
  → image_ingestion.py: validate + store to R2
  → processing_queue.py: enqueue job
  → pipeline_orchestrator.py: INGEST→VALIDATE→BG_REMOVAL→LIGHTING→UPSCALE→FORMAT→COMPLETE
      BG_REMOVAL: services/ml/enhancement/background_removal.py (BRIA RMBG via HF)
      LIGHTING: services/ml/enhancement/lighting_normalization.py (GFPGAN — wrong model)
      UPSCALE: services/ml/enhancement/upscaling.py (Real-ESRGAN via HF)
      FORMAT: services/ml/enhancement/format_optimizer.py (WebP/AVIF)
  → authenticity_validator.py: dHash + Delta-E + edge similarity gate
  → approval_queue_manager.py: auto-publish if all 3 pass, else human review
```

### 3D Generation Pipeline
```
ThreeDGenerationPipeline (ai_3d/generation_pipeline.py)
  → ImagePreprocessor: bg removal + resize to 1024×1024
  → Provider selection: HF_TOKEN→TRELLIS | MESHY_API_KEY→Meshy | TRIPO_API_KEY→Tripo
  → _generate_with_retries(): per-provider retry + cross-provider fallback
  → ModelFidelityValidator.validate(): 95% gate (imagery.model_fidelity)
  → ModelQualityEnhancer.enhance() if fidelity fails: mesh repair → optimize → texture upscale → PBR

PARALLEL PATH (services/three_d/provider_factory.py):
  → ThreeDProviderFactory: weighted + circuit-breaker selection
      gemini (120), tripo (100), replicate (80), huggingface (60)
  → I3DProvider.generate_from_image() / generate_from_text()
```

### LLM Request Flow
```
Client → UnifiedLLMClient.generate()
  → LLMRouter: pick strategy (ROUND_ROBIN | COST_OPTIMIZED | PERFORMANCE | FAILOVER)
  → BaseLLMClient.generate(): retry → circuit breaker → provider API
  → LLMCache: check/store Redis
  → CostTracker: log token costs
  → StreamingAggregator (if streaming): merge chunks

ROUND TABLE PATH:
  → LLMRoundTable: asyncio.gather() all providers
  → StatisticalAnalyzer: Welch's t-test + Bayesian Monte Carlo → winner
  → CreativeJudge (Claude): BRAND_DNA + EXECUTION + PROMPT score
  → Neon DB: store result + scores
```

---

## 4. Configuration & Environment

| Env Var | Used By | Purpose |
|---------|---------|---------|
| `OPENAI_API_KEY` | llm/providers/openai.py | OpenAI access |
| `ANTHROPIC_API_KEY` | llm/providers/anthropic.py | Claude access |
| `GOOGLE_API_KEY` | llm/providers/google.py, services/ml/gemini_client.py | Gemini access; loaded from `.env.hf` |
| `MISTRAL_API_KEY` | llm/providers/mistral.py | Mistral access |
| `COHERE_API_KEY` | llm/providers/cohere.py | Cohere access |
| `GROQ_API_KEY` | llm/providers/groq.py | Groq access |
| `XAI_API_KEY` | llm/providers/groq.py (LLMProvider.LLAMA path) | xAI/Grok — mislabeled as LLAMA |
| `MESHY_API_KEY` | ai_3d/providers/meshy.py, config.py | Meshy 3D API |
| `TRIPO3D_API_KEY` / `TRIPO_API_KEY` | ai_3d/providers/tripo.py | Tripo 3D API (tries both) |
| `HUGGINGFACE_API_KEY` / `HF_TOKEN` | ai_3d/providers/huggingface.py | HuggingFace Inference API |
| `REPLICATE_API_TOKEN` | services/ml/replicate_client.py, services/three_d/replicate_provider.py | Replicate |
| `REDIS_URL` | llm/cache.py, monitoring/ab_comparison.py, monitoring/stream_processor.py | Redis |
| `NEON_DATABASE_URL` | llm/round_table.py | Neon PostgreSQL for scoring |
| `R2_ACCOUNT_ID` / `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` | services/storage/r2_client.py | Cloudflare R2 |
| `METRICS_PORT` | monitoring/metrics_server.py | Prometheus scrape port (default 9090) |
| `WATERMARK_MAGIC` | services/ml/watermark_service.py | 4-byte steganography magic (default `b"DSKY"`) |

---

## 5. Quality Gates & Thresholds

| Gate | Location | Threshold | Action on Fail |
|------|----------|-----------|----------------|
| Model fidelity | `ai_3d/generation_pipeline.py` + `imagery.model_fidelity` | 95% (`MINIMUM_FIDELITY_SCORE`) | Trigger `ModelQualityEnhancer` |
| Perceptual hash similarity | `services/ml/enhancement/authenticity_validator.py` | dHash ≥ 95% | NEEDS_REVIEW or FAILED |
| Color accuracy | `services/ml/enhancement/authenticity_validator.py` | Delta-E CIE76 ≤ 2.0 | NEEDS_REVIEW or FAILED |
| Edge similarity | `services/ml/enhancement/authenticity_validator.py` | NCC ≥ 85% | NEEDS_REVIEW or FAILED |
| Auto-publish gate | `services/ml/enhancement/authenticity_validator.py` | All 3 pass + `requires_human_review=False` | Route to approval queue |
| LLM circuit breaker | `llm/circuit_breaker.py`, `ai_3d/resilience.py`, `services/three_d/provider_factory.py` | 5 failures → OPEN | Block requests, 60s reset |
| A/B win rate | `monitoring/ab_comparison.py` | ≥ 0.8 | Tracked; no enforcement |

---

## 6. Identified Bugs

### CRITICAL
1. **`services/ml/image_description_pipeline.py:147`** — references `GeminiModel.GEMINI_PRO` but `GeminiModel` enum in `gemini_client.py` has no `GEMINI_PRO` member (valid: `FLASH_2_0`, `FLASH_2_5`, `PRO_2_5`, `FLASH_IMAGE`, `PRO_IMAGE`). The correct enum is `VisionModel.GEMINI_PRO` in `schemas/description.py`. Raises `AttributeError` at runtime.
2. **`services/ml/enhancement/lighting_normalization.py`** — `DEFAULT_LIGHTING_MODEL = "tencentarc/gfpgan:..."`. GFPGAN is a face restoration model, not a product lighting model. Product shots will receive face-biased restoration instead of lighting correction. All clothing renders are silently processed incorrectly.
3. **`services/three_d/huggingface_provider.py`** — All Gradio `client.predict()` calls are **synchronous** inside `async def` methods. Blocks the asyncio event loop entirely during every 3D generation (typically 30–120s). Must be wrapped in `asyncio.get_event_loop().run_in_executor()`.

### HIGH
4. **`services/ml/gemini_client.py`** — `GeminiModel.FLASH_IMAGE = "gemini-2.5-flash-preview-native-audio-dialog"` — the model ID string appears to be an audio model identifier, not an image generation model.
5. **`services/three_d/gemini_provider.py`** — `output_format=OutputFormat.GLB` is claimed but actual output is a PNG. `model_url` in `ThreeDResponse` is a base64 data URI, not a URL. Downstream consumers expecting a GLB file path will fail.
6. **`services/three_d/tripo_provider.py`** — calls `agent._tool_generate_from_text()` and `agent._tool_generate_from_image()` (private methods) on `TripoAssetAgent`. Any refactor of those internals silently breaks this provider with no type-checker warning.
7. **`services/three_d/huggingface_provider.py`** — INSTANTMESH and HUNYUAN3D enum variants both silently fall back to TRELLIS. Their individual implementations are not wired. Users requesting these models receive TRELLIS output without warning.
8. **`ai_3d/model_generator.py`** — `trimesh.Scene.save_image()` requires an OpenGL context. Fails with an exception in all headless/CI environments. The exception is caught and a placeholder is returned, masking the failure.
9. **`ai_3d/model_generator.py`** — local pipeline's point cloud → mesh step uses `trimesh.convex_hull()`. Convex hull of a depth-derived point cloud produces a blob, not clothing geometry. This is structurally unfit for garment 3D modeling.

### MEDIUM
10. **`services/ml/watermark_service.py`** — `scipy.fftpack` imported inside DCT methods, not at module level. Runtime `ImportError` if scipy is not installed, surfacing only when a watermark operation is attempted.
11. **`services/ml/enhancement/background_removal.py`** — `SOLID_COLOR` and `CUSTOM_IMAGE` compositing are `TODO` stubs. Always returns transparent PNG regardless of `background_type` setting.
12. **`services/ai_image_enhancement.py`** — `input_path.glob("*.{jpg,jpeg,png}")`. Python `pathlib.glob()` does not support brace expansion. Silently matches zero files.
13. **`services/notifications/email_notifications.py`** — `async def send_email()` uses synchronous `smtplib.SMTP`. Blocks the asyncio event loop on every email send.
14. **`services/analytics/alert_engine.py`** — JSONB context stored via `str(trigger.context).replace("'", '"')`. Breaks on any dict value containing a double-quote. Should use `json.dumps()`.
15. **`services/analytics/alert_notifier.py` vs `alert_engine.py`** — `AlertSeverity` enum has 5 levels in `alert_notifier.py` vs 3 in `alert_engine.py`. Severity values not in the 3-level set will trigger a `KeyError` when the notifier looks up routing rules.
16. **`services/competitive/competitor_analysis.py:_extract_attributes`** — always returns defaults; no vision model is called despite the docstring implying one is.
17. **`services/image_ingestion.py:_queue_for_processing`** — generates a UUID `job_id` but never submits it to `ProcessingQueue`. Jobs are silently dropped.

---

## 7. Architectural Patterns

### Singleton Services
Every service module uses the pattern:
```python
_service: ServiceType | None = None

def get_service() -> ServiceType:
    global _service
    if _service is None:
        _service = ServiceType(...)
    return _service
```
Consequence: no dependency injection; testing requires monkey-patching globals. No lazy teardown.

### Dual 3D Abstraction (PARALLEL, NOT UNIFIED)
- `ai_3d/providers/` — direct API clients (`HuggingFace3DClient`, `MeshyClient`, `TripoClient`) used by `ThreeDGenerationPipeline`
- `services/three_d/` — factory-routed `I3DProvider` implementations with circuit breakers, used by the MCP server tools directly

These two stacks share no code and are not aware of each other. The `services/three_d/tripo_provider.py` wraps `agents/tripo_agent.py`, while `ai_3d/providers/tripo.py` is a standalone `TripoClient`. A request routed through the services factory takes a different code path than one routed through the pipeline.

### Structlog vs Logging
Only two modules use `structlog`: `ai_3d/model_generator.py` and `ai_3d/virtual_photoshoot.py`. All other modules use `logging.getLogger(__name__)`. Mixed logging makes log aggregation inconsistent — structured fields from structlog entries will be missing from modules using the standard logger.

### Correlation ID Convention
All public service methods accept an optional `correlation_id: str | None = None` parameter and propagate it to log records and downstream calls. Not enforced at the abstract level — some providers omit it.

### Circuit Breaker Configuration
Three independent circuit breaker implementations with identical behavior:
- `llm/circuit_breaker.py` — for LLM providers
- `ai_3d/resilience.py::CircuitBreaker` — for 3D providers in the pipeline
- `services/three_d/provider_factory.py::CircuitBreakerState` — for 3D providers in the factory

All use 5-failure threshold, 60s timeout, 2-success HALF_OPEN recovery. No shared base class.

---

## 8. External Dependencies

| Service | Client | Used In |
|---------|--------|---------|
| Anthropic | `anthropic` SDK | llm/providers/anthropic.py |
| OpenAI | `openai` SDK | llm/providers/openai.py |
| Google Gemini | `google-genai` SDK | llm/providers/google.py, services/ml/gemini_client.py |
| Mistral | `mistralai` SDK | llm/providers/mistral.py |
| Cohere | `cohere` SDK | llm/providers/cohere.py |
| Groq | `groq` SDK | llm/providers/groq.py |
| HuggingFace Inference API | `httpx` (async) | ai_3d/providers/huggingface.py |
| HuggingFace Gradio Spaces | `gradio_client` (sync) | services/three_d/huggingface_provider.py |
| Meshy AI | `httpx` (async) | ai_3d/providers/meshy.py |
| Tripo3D | `httpx` (async) | ai_3d/providers/tripo.py |
| Replicate | `httpx` (async, polling) | services/ml/replicate_client.py, services/three_d/replicate_provider.py |
| Cloudflare R2 | `boto3` / `aiobotocore` | services/storage/r2_client.py |
| Redis | `redis` (sync) | llm/cache.py, monitoring/ab_comparison.py, monitoring/stream_processor.py |
| Neon PostgreSQL | `asyncpg` | llm/round_table.py |
| Kafka | `confluent_kafka` | monitoring/stream_processor.py |
| Prometheus | `prometheus_client` | monitoring/prometheus_metrics.py, monitoring/elite_studio_metrics.py |
| trimesh | `trimesh` | ai_3d/model_generator.py, ai_3d/quality_enhancer.py, ai_3d/virtual_photoshoot.py |
| pyrender | `pyrender` | ai_3d/virtual_photoshoot.py (optional, preferred for headless rendering) |
| PIL/Pillow | `PIL` | ai_3d/quality_enhancer.py, services/ml/enhancement/* |
| scipy | `scipy.fftpack` | services/ml/watermark_service.py (lazy import) |

---

## 9. Testing Gaps

- **`image_description_pipeline.py`**: `GeminiModel.GEMINI_PRO` bug would be caught immediately by any integration test that calls the pipeline end-to-end.
- **`background_removal.py`**: No tests for `SOLID_COLOR` / `CUSTOM_IMAGE` compositing paths — both are dead stubs.
- **`image_ingestion.py`**: `_queue_for_processing` never submits to queue — a test asserting queue depth would catch this.
- **`huggingface_provider.py` (services/three_d)**: Synchronous Gradio calls inside async methods cannot be caught by unit tests unless the event loop is monitored for blocking.
- **`alert_engine.py` + `alert_notifier.py`**: Mismatched `AlertSeverity` enums — any test that routes a HIGH or CRITICAL alert through both modules would raise `KeyError`.
- **`stream_processor.py`**: `process_event()` (public sync-injection API) is testable without Kafka — good candidate for unit tests covering dedup, dispatch, and memory caps.
- **`authenticity_validator.py`**: Edge check fallback returns `1.0` (silently passes) on exception — should be explicitly tested.

---

## 10. Cross-Cutting Concerns

### Logging
- Standard: `logging.getLogger(__name__)` — 90% of modules
- Structured: `structlog.get_logger(__name__)` — `ai_3d/model_generator.py`, `ai_3d/virtual_photoshoot.py`
- No unified log formatter or handler configuration at the library level — depends on the application entry point

### Error Handling
- All provider clients catch `Exception` broadly and return `None` — callers must null-check all results
- `MaxRetriesExceededError` and `CircuitBreakerError` are properly typed in `ai_3d/resilience.py`
- `core.errors.production_errors` module provides typed errors (`ConfigurationError`, `RateLimitError`, `ExternalServiceError`) — used in `ai_3d/providers/` and `services/three_d/`
- `services/` modules mostly use bare `except Exception as e: logger.exception(...)` with `return None`

### Async Consistency
- `ai_3d/providers/`: all async via `httpx.AsyncClient` — correct
- `services/three_d/huggingface_provider.py`: sync Gradio inside async — blocks event loop
- `services/notifications/email_notifications.py`: sync `smtplib` inside async — blocks event loop
- `monitoring/stream_processor.py`: `consumer.poll()` is sync inside `async` loop — mitigated by `await asyncio.sleep(0)` yield before each poll

### Security
- `ai_3d/providers/tripo.py`: `ImageGenerationRequest` and `TextGenerationRequest` Pydantic models include XSS pattern checks on prompts — the most security-conscious provider
- `services/competitive/competitor_analysis.py`: URL validation delegates to a shared allowlist checker
- `monitoring/stream_processor.py`: memory caps on all dicts, FIFO dedup with OrderedDict to prevent replay attacks
- No SSRF protection at the services layer for Replicate/HuggingFace URLs returned from provider APIs

---

## 11. Integration Points (How Modules Connect)

```
api/ai_3d_endpoints.py
  └→ ai_3d/generation_pipeline.py (ThreeDGenerationPipeline)
       └→ ai_3d/providers/{huggingface,meshy,tripo}.py

agents/{tripo_agent,meshy_agent}.py
  └→ services/three_d/provider_factory.py (ThreeDProviderFactory)
       └→ services/three_d/{tripo,replicate,huggingface,gemini}_provider.py

orchestration/asset_pipeline.py
  └→ services/ml/pipeline_orchestrator.py (PipelineOrchestrator)
       └→ services/ml/enhancement/{background_removal,lighting_normalization,upscaling,format_optimizer}.py
       └→ services/ml/enhancement/authenticity_validator.py

skyyrose/elite_studio/
  └→ services/ml/gemini_client.py (vision)
  └→ monitoring/elite_studio_metrics.py (Prometheus)
  └→ monitoring/ab_comparison.py (provider A/B Redis)

orchestration/threed_round_table.py
  └→ agents/tripo_agent.py (TripoAssetAgent)
  └→ services/three_d/provider_factory.py

llm/round_table.py
  └→ llm/providers/*.py (all 6 providers)
  └→ llm/judge.py (CreativeJudge via Anthropic)
  └→ llm/statistical_analyzer.py (winner selection)

monitoring/prometheus_metrics.py
  ← devskyy_mcp.py (imports on startup, calls initialize_metrics())
  ← monitoring/metrics_server.py (serves /metrics on :9090)
  ← monitoring/elite_studio_metrics.py (co-registered at bottom of prometheus_metrics.py)

monitoring/stream_processor.py
  ← analytics/event_collector.py (produces events)
  → Redis (analytics:page_views, analytics:revenue, analytics:product_interest, analytics:search_queries)
```

---

_Digest covers 100% of target files. All bugs listed in Section 6 are identified-only — no fixes applied._
