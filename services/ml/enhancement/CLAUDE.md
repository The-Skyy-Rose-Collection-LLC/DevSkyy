# services/ml/enhancement/ — Image Enhancement Pipeline

**ML-powered image enhancement.** Background removal, upscaling, lighting normalization, format optimization, authenticity validation.

## Public Surface (`services/ml/enhancement/__init__.py`)

| Group | Symbols | Source |
|-------|---------|--------|
| Background removal | `BackgroundRemovalService`, `BackgroundRemovalResult`, `BackgroundType` | `background_removal.py` |
| Upscaling | `UpscalingService`, `UpscaleResult` | `upscaling.py` |
| Lighting normalization | `LightingNormalizationService`, `LightingResult`, `LightingNormalizationError`, `ColorPreservationError`, `LightingIntensity` | `lighting_normalization.py` |
| Format optimization | `FormatOptimizer`, `FormatOptimizationResult`, `ImageVariant`, `OutputFormat` | `format_optimizer.py` |
| Authenticity validation | `AuthenticityValidator`, `AuthenticityReport`, `ValidationResult` | `authenticity_validator.py` |

## CRITICAL CONSTRAINT (`__init__.py:11-12`)

**Enhancement MUST NOT modify product logos, branding, labels, text, colors, or physical features.** This is a hard authenticity contract. `AuthenticityValidator` exists to catch violations — every enhancement run that touches a product image MUST be followed by `AuthenticityValidator.validate()` before the result is released to the catalog.

## Hard Rules

- Order matters: **background removal → lighting → upscale → format**. Lighting changes after upscale produce posterization. Format conversion after lighting locks compression artifacts
- `LightingNormalizationService` raises `ColorPreservationError` when adjustment would shift brand colors beyond tolerance — catch and fail the pipeline, do not swallow
- `AuthenticityValidator` is **mandatory final stage** for any product imagery touched by enhancement. Skipping it violates brand canon
- Format optimization produces multiple `ImageVariant`s (different sizes + formats) — never write all variants to canonical URL, attach via `srcset` or asset version manager
- All services are async; backgrounds (rembg / Replicate) are network-bound

## Consumers

- `services/ml/pipeline_orchestrator.py` — invokes enhancement stages in `ProcessingProfile`
- `skyyrose/elite_studio/*` — final stage of canonical imagery pipeline
- `agents/core/imagery/*` — single-image enhancement requests


