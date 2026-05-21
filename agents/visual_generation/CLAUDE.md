# agents/visual_generation/ — Multi-provider visual generation router

Pre-elite_studio multi-provider image + video generation router. Older code path — production imagery now runs through `skyyrose/elite_studio/` and `agents/core/imagery/`. Kept for direct multi-provider access where you need raw provider selection without the elite-studio pipeline.

## Surface (from `__init__.py`)

| Symbol | Source | Role |
|--------|--------|------|
| `VisualProvider` | `visual_generation.py` | StrEnum: GOOGLE_IMAGEN, GOOGLE_VEO, HF_FLUX, REPLICATE_LORA |
| `GenerationType` | `visual_generation.py` | StrEnum: IMAGE, VIDEO, EDIT, UPSCALE |
| `AspectRatio` | `visual_generation.py` | StrEnum: SQUARE, PORTRAIT, LANDSCAPE, WIDE, TALL |
| `ImageQuality` | `visual_generation.py` | StrEnum: DRAFT, STANDARD, HD, ULTRA |
| `GenerationRequest`, `GenerationResult` | `visual_generation.py` | Pydantic models — input/output contract |
| `SKYYROSE_BRAND_DNA` | `visual_generation.py` | Brand-context dict injected into every prompt |
| `GoogleImagenClient`, `GoogleVeoClient`, `HuggingFaceFluxClient`, `ReplicateLoRAClient` | `visual_generation.py` | Per-provider clients |
| `VisualGenerationRouter`, `create_visual_router` | `visual_generation.py` | Multi-provider router |
| `ConversationEditor` | `conversation_editor.py` | Multi-turn image editing via conversation context |

## Files

```
visual_generation/
├── __init__.py             re-exports the canonical surface
├── visual_generation.py    main module — providers, router, brand DNA, request/result types
├── conversation_editor.py  multi-turn edit (e.g. "make it darker", "add a smoke effect")
├── gemini_native.py        Gemini native image gen (Nano Banana family) — direct client
├── prompt_optimizer.py     prompt rewriting for better image quality
├── reference_manager.py    reference image management for img-to-img workflows
```

## Provider mapping

| `VisualProvider` value | Client | Backing API | Use case |
|------------------------|--------|-------------|----------|
| `GOOGLE_IMAGEN` | `GoogleImagenClient` | GCP Vertex AI (Imagen 3) | Photoreal product imagery |
| `GOOGLE_VEO` | `GoogleVeoClient` | GCP Vertex AI (Veo) | Video generation |
| `HF_FLUX` | `HuggingFaceFluxClient` | HuggingFace Inference API (FLUX) | Art-style + brand creative |
| `REPLICATE_LORA` | `ReplicateLoRAClient` | Replicate (LoRA fine-tunes) | Brand-trained LoRA models |

Nano Banana (gemini-2.5-flash-image / -3.1 / -3-pro) lives in `gemini_native.py` — its own direct client, not routed through `VisualGenerationRouter`.

## Brand DNA injection

`SKYYROSE_BRAND_DNA` is a frozen dict injected into every prompt by the router:

```python
SKYYROSE_BRAND_DNA = {
    "tagline": "Luxury Grows from Concrete.",
    "collections": ["Signature", "Black Rose", "Love Hurts", "Kids Capsule"],
    "color_tokens": {"rose_gold": "#B76E79", "dark": "#0A0A0A", ...},
    "founder_voice": "...",  # see project memory project_founder_voice.md
}
```

When generating brand imagery without the elite_studio pipeline, the router merges DNA into the prompt so output stays on-brand. Per project memory: name-first product referencing, no urgency timers, garment-as-protagonist.

## Conversation editor (`conversation_editor.py`)

Multi-turn editing surface for iterative refinement:

```python
from agents.visual_generation import ConversationEditor

editor = ConversationEditor(initial_image_path="...")
result = await editor.refine("Make the lighting moodier")
result = await editor.refine("Add subtle film grain")
# Each call uses prior result as reference; converges toward operator intent
```

Useful for one-off creative work; production pipelines should use `render_pipeline/` (deterministic) or `elite_studio/` (multi-agent QA).

## Relationship to other generation paths

| Path | Use when |
|------|----------|
| `agents/visual_generation/` (this) | Direct provider access, one-off creative, multi-provider routing |
| `agents/render_pipeline/` (ADK) | Catalog-driven product renders with QA tournament + learning loops |
| `agents/core/imagery/` (CoreAgent) | New code path — self-healing, sub-agent registry, batch-friendly |
| `skyyrose/elite_studio/` | Canonical multi-agent pipeline (planned SaaS) — composes the above |

**For new code, prefer `agents/core/imagery/` or the elite_studio pipeline.** This module is the older direct-access path.

## Conventions

- **Async clients.** All provider clients are async — use `async with` context managers.
- **Pydantic models.** `GenerationRequest` + `GenerationResult` enforce schema at boundaries.
- **Brand DNA via the router.** Don't pass brand context inline — let `VisualGenerationRouter` merge it from `SKYYROSE_BRAND_DNA`.
- **`gemini_native.py` is direct.** Bypasses the router (Nano Banana is the canonical generation engine; routing through abstraction adds latency without value).
- **Cost tracking via the router.** `GenerationResult.cost_usd` is populated — log it for telemetry.

## Don't

- Don't use this module for catalog-driven product renders. Use `agents/render_pipeline/` — it has QA tournament + dossier compliance + learning loops.
- Don't bypass `SKYYROSE_BRAND_DNA` when generating brand imagery. Brand-off output ships fast and is hard to retract.
- Don't add a new provider without:
  1. New `VisualProvider` enum value
  2. New client class implementing the shared interface
  3. Router registration in `VisualGenerationRouter._providers`
  4. Cost entry (input/output prices, fields on `GenerationResult`)
- Don't write video to disk without an explicit path argument. Veo outputs are large — operators should choose where they go.

## Related

- New CoreAgent path: `agents/core/imagery/`
- ADK render pipeline: `agents/render_pipeline/`
- Multi-agent canonical: `skyyrose/elite_studio/`
- Nano Banana model IDs: `llm/model_ids.py` (`NANO_BANANA_*`)
- Brand canon: `knowledge-base/seed/from-interview.md`
- Founder voice register: project memory `project_founder_voice.md`

## Recent learnings

- This module is one of four parallel image-gen entry points (cmem #3146, 2026-05-08). Canonical going forward is `skyyrose/elite_studio` + `agents/core/imagery`.
- `gemini_native.py` bypasses the router on purpose — Nano Banana is the canonical engine; abstraction overhead isn't justified there.
