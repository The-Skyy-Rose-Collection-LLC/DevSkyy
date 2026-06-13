# services/ml/schemas/ — ML Pipeline Schemas

**Pydantic schemas for image-to-description pipeline.** Validation contracts at the ML boundary.

## Public Surface (`services/ml/schemas/__init__.py`)

| Symbol | Purpose | Source |
|--------|---------|--------|
| `DescriptionRequest` | input — image bytes/URL + style + target audience | `description.py` |
| `DescriptionOutput` | output — full description + bullets + SEO + features | `description.py` |
| `BulletPoint` | structured bullet (text + icon hint) | `description.py` |
| `ExtractedFeatures` | parsed feature dict | `description.py` |
| `MaterialInfo` | material type + composition % | `description.py` |
| `StyleAttributes` | style classification | `description.py` |
| `SEOContent` | meta title + description + keywords | `description.py` |

## Hard Rules

- Pydantic v2 — use `model_config = ConfigDict(frozen=True)` for immutable DTOs
- Validation at the boundary — `DescriptionRequest.model_validate()` on ingest, never trust caller-built objects
- `MaterialInfo.composition` must sum to 100 (validator enforced). Reject input that doesn't sum
- `SEOContent.keywords` is a list of strings, NOT comma-separated string — split at input boundary
- Adding fields: bump model version + provide default to preserve backward compat with cached results

## Consumers

- `services/ml/image_description_pipeline.py` — request/response shape
- `services/ml/prompts/vision_prompts.py` — prompt output must conform to these schemas
- `api/v1/products/descriptions` — endpoint surface uses these as response model


