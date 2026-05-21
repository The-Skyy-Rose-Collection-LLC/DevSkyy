# services/ml/prompts/ — Vision Model Prompt Templates

**Centralized prompt templates for vision-language models.** Single source of truth — every vision call uses these constants.

## Public Surface (`services/ml/prompts/__init__.py`)

| Symbol | Purpose | Source |
|--------|---------|--------|
| `DESCRIPTION_PROMPTS` | dict keyed by description style (`luxury`, `technical`, `minimal`, etc.) | `vision_prompts.py` |
| `BULLET_POINTS_PROMPT` | product bullet-list generation | `vision_prompts.py` |
| `FEATURE_EXTRACTION_PROMPT` | structured feature extraction (materials, style, fit) | `vision_prompts.py` |
| `SEO_PROMPT` | SEO meta description + title generation | `vision_prompts.py` |
| `TAGS_PROMPT` | tag extraction for taxonomy | `vision_prompts.py` |
| `get_description_prompt(style)` | accessor with style validation | `vision_prompts.py` |
| `get_feature_prompt()` | accessor for feature prompt | `vision_prompts.py` |

## Hard Rules

- **All vision model calls MUST use prompts from this module** — never inline prompts in service code. Inlining defeats brand-voice consistency
- Prompts encode SkyyRose brand voice — changes here ripple to every product description, SEO meta, and feature list across the catalog
- Brand-voice canon lives at `knowledge-base/seed/from-interview.md` (founder voice). Prompts must respect tone: garment-as-protagonist, no urgency timers, no related-products copy
- New prompt types: add the constant + accessor + `__all__` entry. Update CLAUDE.md table

## Consumers

- `services/ml/image_description_pipeline.py` — pulls `DESCRIPTION_PROMPTS`
- `services/ml/visual_feature_extractor.py` — pulls `FEATURE_EXTRACTION_PROMPT`
- `agents/core/content/*` — SEO and tag generation


<claude-mem-context>

</claude-mem-context>