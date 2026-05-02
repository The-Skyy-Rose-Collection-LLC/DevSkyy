# Pipeline Architecture

> Three independent pipelines. Each has one job. Don't merge them.

## Why three

Earlier iterations tried to use a single "render pipeline" for everything,
which produced prompts mixing garment description with Oakland brand voice
and got middling results on every dimension. Splitting by use case keeps
each pipeline measurable and tunable.

## Pipeline 1 — Product Cards & Galleries

**Job:** clean product photography for the storefront. Front view, back
view, accessory hero. The garment is the only subject.

**Used in:** product cards on collection pages, gallery thumbnails on
single-product pages, search result thumbs.

**Inputs:**
- A SKU row from `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`
- Reference product photo (tech-flat or real product shot)

**Outputs:**
- `renders/gated/<sku>/<sku>-<view>-attemptN.png`
- `tasks/gated-render-log.json`

**Generator:** nano-banana (Gemini 2.5 Flash Image / Pro Image)

**Prompt builder:** `skyyrose.elite_studio.quality.render_prompt_builder`
- GARMENT block: `"front view of a black hoodie on a model"` (CLIP-friendly, the SCORING surface)
- SCENE block: studio backdrop with collection-accent lighting (Pipeline 1 has no Oakland scenes)
- FIDELITY block: copy-reference-exactly directives

**Quality gate:** `skyyrose.elite_studio.quality.render_quality.evaluate_render`
- DINOv2 brand centroid (image-vs-centroid cosine, threshold ~0.39)
- CLIP text-image alignment (text-vs-image, threshold ~0.20)
- Resolution check (>= 512px both axes)
- Verdict: SHIP / REVIEW / KILL

**Entry point:** `python3 scripts/pipeline_product_renders.py`

---

## Pipeline 2 — AI Model Generation (Lifestyle / Editorial)

**Job:** model wearing the product in a brand-aligned scene. Oakland
industrial nights, golden hour by the bay, crimson neon for Love Hurts,
clean Oakland street for Kids. This is where the brand voice lives.

**Used in:** hero sections on collection pages, landing-page heroes,
social media editorial, marketing campaigns.

**Inputs:**
- A completed Pipeline-1 product render (the garment is already perfect)
- A scene reference

**Outputs:**
- `renders/output/<sku>-branding/<sku>-stage[1..6].png`
- Audit log JSON alongside

**Generator stages:** the 6-stage compositor pipeline
1. BRIA RMBG 2.0 — alpha matte extraction
2. Claude Opus — FLUX prompt synthesis from dossier
3. IC-Light v2 — relight subject to match scene
4. FLUX Fill Pro — inpaint subject into scene
5. PIL gaussian / GPSDiff — contact shadows
6. Gemini structured QA — final visual rubric

**Quality gate:** stage 5.5 embedding gate (just shipped) + stage 6 Gemini QA

**Entry point:** `skyyrose/elite_studio/agents/compositor_agent.py`
(callable via `CompositorAgent().composite(sku, scene_name, ...)`)

**Cost per render:** ~$0.115 (vs Pipeline 1's ~$0.025)

---

## Pipeline 3 — Brand Copy & Marketing Text

**Job:** product descriptions, collection blurbs, email subject lines,
social copy, ad headlines. No images, only text.

**Used in:** product description fields in WooCommerce, Klaviyo email
campaigns, paid social ads, SEO meta descriptions.

**Inputs:**
- Product / collection / brand context (from catalog + dossier)
- Voice guidelines + length constraints
- Channel-specific tone (email vs ad vs WP product page)

**Outputs:**
- Markdown / plain text strings
- Pushed to WooCommerce / Klaviyo / ad platforms via their APIs

**Generator:** Claude Opus / Sonnet via the multi-agent orchestrators in
`orchestration/brand_*.py`

**Quality gate:** none yet — currently relies on human review.
Future: brand-voice classifier (fine-tuned or zero-shot Constitutional AI).

**Entry point:** scattered across `orchestration/brand_context.py`,
`orchestration/brand_integration.py`, `orchestration/brand_learning.py`.
Not yet consolidated into one CLI.

---

## What NOT to do

- **Don't put model/scene language in Pipeline 1.** Product cards are
  garment-only. Adding "Oakland industrial" to a product-card prompt
  pollutes the SCORING surface and makes the renders less consistent.
- **Don't put studio language in Pipeline 2.** Editorial shots need scene
  context to do their job. Stripping it gets you back to product-card
  output, defeating the point.
- **Don't merge the gates.** Pipeline 1's gate (DINOv2 + alignment)
  measures "is this on-brand product photography." Pipeline 2's gate
  (Gemini structured QA) measures "is this a good editorial shot of a
  model in a scene." Different criteria, different thresholds.

## Quick reference

| | Pipeline 1 | Pipeline 2 | Pipeline 3 |
|---|---|---|---|
| Output | Product photo | Editorial shot | Marketing text |
| Subject | Garment | Model in scene | (no image) |
| Generator | nano-banana | Compositor 6-stage | Claude / orchestrators |
| Cost/run | ~$0.025 | ~$0.115 | ~$0.005 |
| Gate | DINOv2 + CLIP align | Gemini QA + centroid | (manual review) |
| CLI | `scripts/pipeline_product_renders.py` | `agents/compositor_agent.py` | (none yet) |
