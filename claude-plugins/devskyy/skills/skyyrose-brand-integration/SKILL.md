---
name: SkyyRose Brand Integration
description: This skill should be used when the user asks about "SkyyRose brand guidelines", "collection aesthetics", "brand DNA", "luxury streetwear style", or mentions BLACK_ROSE, LOVE_HURTS, SIGNATURE collections, rose gold accents, or brand-consistent content generation.
version: 1.0.0
---

# SkyyRose Brand Integration Skill

Use this skill when ensuring brand consistency across all DevSkyy-generated content for SkyyRose.

## When to Use This Skill

Invoke this skill when the user:

- Requests brand-consistent content generation
- Asks about SkyyRose collections (BLACK_ROSE, LOVE_HURTS, SIGNATURE)
- Needs brand guidelines or style specifications
- Wants to apply brand DNA to new products or content
- Mentions "Where Love Meets Luxury" tagline or Oakland roots
- Requests collection-specific aesthetics or colors

## SkyyRose Brand DNA

Located in `orchestration/brand_context.py`:

```python
SKYYROSE_BRAND_DNA = {
    "name": "SkyyRose",
    "tagline": "Where Love Meets Luxury",
    "colors": {
        "primary": "#B76E79",
        "secondary": "#1A1A1A",
        "accent": "#C9A962"
    },
    "style": ["premium", "sophisticated", "bold", "elegant"],
    "collections": {
        "BLACK_ROSE": "dark romantic aesthetic",
        "LOVE_HURTS": "edgy romantic style",
        "SIGNATURE": "clean minimal aesthetic"
    }
}
```

## Brand Application

All agents automatically receive brand context via `self.brand_context`.
Use collection-specific prompts for visual generation, product descriptions, and marketing content.

## File Locations

- **Brand DNA**: `orchestration/brand_context.py`
- **Collection Presets**: `agents/visual_generation.py`
- **Marketing Templates**: `agents/marketing_agent.py`

## References

See `references/` directory for complete brand guidelines, collection mood boards, and voice/tone examples.
