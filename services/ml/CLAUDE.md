# services/ml/ — ML Service Clients & Orchestration

**External ML provider clients + pipeline orchestration + queue + watermarking.** Backs all ML-heavy work (image enhancement, vision analysis, 3D, generation).

## Public Surface (`services/ml/__init__.py`)

| Group | Symbols | Source |
|-------|---------|--------|
| Replicate client | `ReplicateClient`, `ReplicateConfig`, `ReplicateError`, `ReplicatePrediction`, `ReplicatePredictionStatus`, `ReplicateRateLimitError`, `ReplicateTimeoutError` | `replicate_client.py` |
| Gemini client (optional) | `GeminiClient`, `GeminiConfig`, `GeminiError`, `GeminiModel`, `GeminiRateLimitError`, `GeminiContentFilterError`, `AspectRatio`, `ImageSize`, `ImageInput`, `ImageGenerationRequest`, `ImageGenerationResponse`, `GeneratedImage`, `VisionAnalysisResponse` | `gemini_client.py` |
| Pipeline orchestrator | `PipelineOrchestrator`, `PipelineJob`, `PipelineResult`, `PipelineEvent`, `PipelineError`, `PipelineStage`, `PipelineStatus`, `ProcessingProfile`, `StageCheckpoint` | `pipeline_orchestrator.py` |
| Processing queue | `ProcessingQueue`, `Job`, `JobStatus`, `TaskType`, `FallbackChain`, `QueueMetrics`, `ProcessingQueueError` | `processing_queue.py` |
| Watermark service | `WatermarkService`, `WatermarkResult`, `WatermarkDetectionResult`, `WatermarkError`, `WatermarkPayload` | `watermark_service.py` |

## Subpackages

- `enhancement/` — background removal, upscaling, lighting normalization, format optimization, authenticity validation
- `prompts/` — vision model prompt templates (description, SEO, tags, features)
- `schemas/` — Pydantic schemas for image-to-description pipeline

## Hard Rules

- **`GeminiClient` is optional** — if `google-genai` package missing, `GeminiClient = None` (`__init__.py:73-77`). Every consumer MUST guard: `if GeminiClient is None: raise RuntimeError(...)`
- **All paid ML calls go through `ProcessingQueue` with `FallbackChain`** — never invoke `ReplicateClient` / `GeminiClient` directly from agent or API handler. Queue provides retry, rate-limit handling, cost tracking, and fallback to alt providers
- **STOP-AND-SHOW gate enforced** — any handler dispatching to Gemini / Replicate must surface SKU + cost estimate before dispatch (`CLAUDE.md STOP-AND-SHOW protocol`)
- Pipeline orchestrator uses **stage checkpoints** — `StageCheckpoint` enables resume after partial failure. Long-running jobs MUST checkpoint after each stage
- Watermark payload is invisible (steganographic) — do not log payload bytes, only detection results
- Pipeline jobs are **idempotency-keyed by `job_id`** — re-submitting the same `PipelineJob` returns existing result, not a new run

## Consumers

- `api/v2/elite_studio/*` — async ML jobs via `PipelineOrchestrator`
- `api/v1/clothing_3d/*` — `IdempotencyCache.get_or_run()` wraps queue dispatch
- `agents/core/imagery/*` — long-running batch generation via queue
- `skyyrose/elite_studio/*` — canonical imagery pipeline


