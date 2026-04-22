# Technology Stack: Ghost Mannequin AI Pipeline

**Project:** SkyyRose v1.2 — Ghost Mannequin Batch Generation
**Researched:** 2026-04-22
**Dimension:** Stack
**Confidence:** HIGH (core models), MEDIUM (prompt engineering specifics)

---

## The Core Decision

Ghost mannequin from a techflat is a two-stage problem:

1. **Shape reconstruction** — inflate a flat 2D garment image into a 3D-looking worn form with realistic drape, collar depth, and sleeve volume
2. **Background isolation** — pure white studio output, no model visible, no artifacts

The existing stack already has both ingredients. The recommendation is to use them in sequence rather than bolt on a third-party SaaS ghost mannequin service.

---

## Recommended Stack

### Stage 1 — Background Removal (Techflat Alpha Matte)

| Technology | Version | Purpose | Confidence |
|------------|---------|---------|------------|
| **BRIA RMBG 2.0** | 2.0 (current) | Remove flat techflat background, produce clean alpha matte | HIGH |

**Why:** Already in the Elite Studio compositor pipeline at Stage 1. 90% accuracy on photorealistic images (vs. BiRefNet 85%, vs. removal.ai 97%) — the gap to commercial is acceptable for techflats which have clean, solid, or gradient backgrounds. Available via `fal_client` at `fal-ai/bria/background/remove` ($0.008/image on fal.ai). No new dependency.

**What NOT to use:** rembg (older, less accurate on complex fabric edges), SAM2 (overkill for flat techflats with simple backgrounds, requires manual prompting). BRIA RMBG is already wired and validated.

---

### Stage 2 — 3D Shape Generation (Techflat → Ghost Mannequin)

| Technology | Version | Purpose | Confidence |
|------------|---------|---------|------------|
| **Gemini 2.5 Flash Image** (`gemini-2.5-flash-image`) | Production (GA Oct 2025) | Primary generation: techflat → ghost mannequin shape | HIGH |
| **FLUX Fill Pro** (`black-forest-labs/flux-fill-pro`) | Current | Fallback for collar/neck inpainting when Gemini output needs correction | MEDIUM |
| **FLUX.1 Kontext [pro]** (`fal-ai/flux-pro/kontext`) | Current | Secondary fallback for instruction-based local edits | MEDIUM |

**Primary: Gemini 2.5 Flash Image**

This is the right choice because:
- Already used in nano-banana-vton.py as the primary model — proven, integrated, no new auth
- Supports multi-image input (up to 14 reference images) — send techflat + brand reference in one call
- Supports image editing via text prompt: "transform this flat garment techflat into a ghost mannequin studio shot on a pure white background, showing natural 3D drape and collar depth"
- $0.039/image (1290 output tokens at $30/M) — cheapest viable option in the existing stack
- Spatial 3D understanding confirmed for garment reconstruction in production use (Oct 2025 GA)
- Speed: 1-2 seconds per image at 1024x1024

**When Gemini output needs collar/neck refinement:**

Use FLUX Fill Pro via Replicate for targeted inpainting of the neck/collar region specifically. FLUX Fill Pro maintains texture consistency and lighting context across edits. Already used as a fallback in Elite Studio compositor Stage 4.

**When the whole garment needs local instruction edits:**

Use FLUX.1 Kontext [pro] via `fal_client` at $0.04/image. Kontext performs surgical instruction-based edits ("make the collar opening deeper and more circular, natural shadow inside") without touching the rest of the image. Available via `fal-ai/flux-pro/kontext`.

**Do NOT use:**
- IDM-VTON / CatVTON — these are virtual try-on models that require a person reference image. Ghost mannequin does not use a person; these models are designed for the wrong task. IDM-VTON also requires 14.62 GB VRAM and 6.6s/image — not suited for batch scripts.
- FASHN product-to-model endpoint — converts flat-lays into *on-model* shots (adds a person), not ghost mannequin. Opposite of what's needed.
- Photoroom Ghost Mannequin API — SaaS-only, requires Enterprise plan for 2K+ output, ghost mannequin parameters are limited (`ghostMannequin.mode: ai.auto`), no Python SDK with full control, pricing opaque. Adds a new vendor dependency when Gemini already handles this.
- Dedicated ghost mannequin SaaS (WearView, Photta, Snappyit) — all closed-API, per-image pricing ~$0.25-$1.00+, no batch scripting control, no integration with existing catalog pipeline. Gemini at $0.039 beats all of them.

---

### Stage 3 — QA Gate (Output Validation)

| Technology | Version | Purpose | Confidence |
|------------|---------|---------|------------|
| **Gemini Flash** (`gemini-2.5-flash` text model) | Current | QA: confirm ghost mannequin output meets criteria | HIGH |

**Why:** Already used in Elite Studio compositor Stage 6 for visual QA. Call the text model with the output image and a structured prompt: "Does this image show: 1) garment on invisible mannequin with no visible person, 2) pure white background, 3) realistic 3D drape, 4) collar/neck area filled naturally? Answer YES/NO for each." Free inference step (text output only), no additional cost.

**Reject criteria:** mannequin visible, colored background, flat/un-inflated appearance, neck area hallucinated (wrong fabric, tags, anatomical content).

---

### Stage 4 — Background Guarantee (Pure White Enforcement)

| Technology | Version | Purpose | Confidence |
|------------|---------|---------|------------|
| **Pillow (PIL)** | 10.x (already in .venv/) | Composite alpha-matte cut garment onto solid #FFFFFF canvas | HIGH |

**Why:** Gemini generation may produce near-white or off-white backgrounds. After generation, re-apply the BRIA alpha matte from Stage 1 to the generated image and composite onto a guaranteed `#FFFFFF` canvas. Pure programmatic, zero cost, zero latency. Already in `.venv/` via `requirements-imagery.txt`.

This is a known trick from the Elite Studio pipeline and eliminates background color drift entirely.

---

## Full Pipeline (Batch Script)

```
techflat image (PNG/JPG)
    ↓
[Stage 1] BRIA RMBG 2.0 (fal.ai)       → alpha matte + clean garment cutout
    ↓
[Stage 2] Gemini 2.5 Flash Image         → ghost mannequin generation (primary)
           │ REJECT (collar fail)
           └→ FLUX Fill Pro (Replicate)  → neck/collar inpaint patch
    ↓
[Stage 3] Gemini Flash QA                → pass/fail structured check
           │ FAIL
           └→ log SKU to review queue, skip output write
    ↓
[Stage 4] PIL composite on #FFFFFF       → pure white background guarantee
    ↓
renders/ghost-mannequin/{sku}-ghost-front.webp
```

---

## Prompt Engineering (Ghost Mannequin Specific)

### Gemini Stage 2 Prompt Template

```
You are a professional product photographer. Transform this flat garment techflat into a
ghost mannequin studio product photograph.

Requirements:
- Pure white background (#FFFFFF), no shadows beneath garment
- Garment appears to be worn by an invisible person — 3D filled shape with natural drape
- Collar/neckline shows interior depth — hollow opening, no mannequin neck visible
- Sleeves have natural 3D volume, not flat
- Fabric texture, all text, numbers, logos, and patches preserved exactly as shown in the source
- Studio lighting: soft, even, no harsh shadows, slight highlight on fabric texture
- Straight-on front view, garment centered, vertical orientation
- No mannequin, no person, no hands, no styling props visible

Input garment type: {garment_type}
```

### Jersey-Specific Additions (Black Rose collection, jerseys with text/numbers)

```
CRITICAL: Preserve all jersey text, numbers, team patches, and embroidery exactly.
Do not hallucinate or alter any text. The jersey number and lettering must be identical to the source.
Fabric: athletic mesh/satin. The interior neck area shows athletic mesh fabric, not cotton.
```

**Why this matters:** Gemini's spatial model understands garment structure well but has known weakness with exact text reproduction on back-of-jersey shots (confirmed in project memory). Explicit "preserve text exactly, do not hallucinate" instruction is required. Front shots are significantly more reliable for jersey text.

### Collar Fill Inpainting (FLUX Fill Pro fallback)

When Gemini collar fails, mask the collar opening region specifically:
- Mask: circular/oval region inside collar line, expanding 20px beyond collar edge to include seam context
- Prompt: `"hollow inner collar, {fabric_type} fabric texture, natural shadow inside collar, no mannequin neck, no skin"`
- Do NOT mask the entire neck area — give the model fabric context pixels

---

## Cost Manifest (30 Products, Single Pass)

| Stage | Tool | Cost/Image | 30 Products | Notes |
|-------|------|-----------|-------------|-------|
| Stage 1 | BRIA RMBG 2.0 (fal.ai) | ~$0.008 | ~$0.24 | Approximate fal.ai rate |
| Stage 2 | Gemini 2.5 Flash Image | $0.039 | $1.17 | Some may need fallback |
| Stage 2b | FLUX Fill Pro (Replicate) | ~$0.04 | $0–$0.40 | 0–10 collar fails estimated |
| Stage 3 | Gemini Flash QA | ~$0.001 | ~$0.03 | Text tokens only |
| Stage 4 | PIL | $0 | $0 | Local compute |
| **Total** | | | **~$1.50–$1.85** | Full batch, 30 products |

STOP AND SHOW this manifest before executing any batch run. This is the CLAUDE.md confirmed protocol.

---

## Integration with Existing Python Stack

All tools are reachable with existing dependencies:

```python
# Already in .venv/ — no new installs required
import fal_client          # BRIA RMBG 2.0, FLUX Fill Pro, FLUX Kontext
from google import genai   # Gemini 2.5 Flash Image, Gemini Flash QA
from PIL import Image      # Stage 4 composite
import httpx               # Replicate fallback if needed
```

Entry point pattern: follow `scripts/nano-banana-vton.py` — CLI args for `--sku`, `--all`, `--dry-run`. Output to `renders/ghost-mannequin/{sku}-ghost-front.webp`.

---

## Alternatives Considered and Rejected

| Category | Rejected Option | Why Rejected |
|----------|----------------|--------------|
| Generation | IDM-VTON | Requires person reference image — wrong task type. 14.6 GB VRAM requirement |
| Generation | CatVTON | Same problem — virtual try-on, not ghost mannequin. Requires person |
| Ghost mannequin SaaS | Photoroom API | Enterprise-only for 2K+, opaque pricing, no batch control, new vendor |
| Ghost mannequin SaaS | WearView/Photta | Closed API, $0.25–$1.00/image, no integration path with catalog pipeline |
| On-model | FASHN product-to-model | Converts to on-model (adds person) — wrong output for ghost mannequin |
| Background removal | rembg | Lower accuracy than BRIA on fine fabric edges |
| Background removal | SAM2 | Requires manual point/box prompts, not suited for batch |
| Collar fill | Photoshop Firefly | Not automatable via Python API in batch context |

---

## Sources

- [Gemini 2.5 Flash Image — GA announcement](https://developers.googleblog.com/en/gemini-2-5-flash-image-now-ready-for-production-with-new-aspect-ratios/)
- [Gemini image generation docs](https://ai.google.dev/gemini-api/docs/image-generation)
- [Gemini prompting best practices](https://developers.googleblog.com/en/how-to-prompt-gemini-2-5-flash-image-generation-for-the-best-results/)
- [BRIA RMBG 2.0 benchmarks](https://blog.bria.ai/benchmarking-blog/brias-new-state-of-the-art-remove-background-2.0-outperforms-the-competition)
- [BRIA RMBG 2.0 on fal.ai](https://fal.ai/models/fal-ai/bria/background/remove)
- [FLUX.1 Kontext on fal.ai](https://fal.ai/models/fal-ai/flux-pro/kontext)
- [FLUX Fill Pro on Replicate](https://replicate.com/black-forest-labs/flux-fill-pro)
- [Photoroom Ghost Mannequin API](https://docs.photoroom.com/image-editing-api-plus-plan/ghost-mannequin)
- [FASHN product-to-model](https://fashn.ai/products/api)
- [Ghost mannequin neck joint prompt guide](https://imageworkindia.com/generative-fill-prompt-ghost-mannequin-neck-joint/)
- [VITON model comparison (FASHN blog)](https://fashn.ai/blog/comparing-the-top-4-open-source-virtual-try-on-viton-models)
- [FLUX clothes inpainting workflow](https://civitai.com/models/967161/flux-or-sdxl-auto-clothes-inpainting)

---
*Research completed: 2026-04-22 | Milestone: v1.2 Ghost Mannequin Pipeline*
