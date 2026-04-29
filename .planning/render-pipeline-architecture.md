# Render Pipeline Architecture Analysis

**Date:** 2026-04-27  
**Author:** Engineering analysis — DevSkyy AI agent  
**Status:** Decision pending (Path A vs Path B)

---

## Executive Summary

The 3-stage render pipeline (FLUX Kontext Pro → Gemini Flash mask → FLUX Fill Pro) produced **0/4 passes** on the last batch re-run. This is not a tuning failure — it is a **structural mismatch baked into the pipeline design**. Stage 1 was designed to produce a clean, undecorated garment. FLUX Kontext Pro, by design, cannot do that when given a decorated techflat as its conditioning image. Every downstream stage (mask derivation, inpainting) was built on an assumption that is false at runtime.

This document provides a complete file-level audit of each stage, names the root cause precisely, and presents two architecturally distinct solutions with concrete implementation plans. No further patches should be applied until this decision is made.

---

## Stage 1: FLUX Kontext Pro Base Render

### Files
- `skyyrose/elite_studio/synthesis/stages/base_render.py` — orchestration (132 lines)
- `skyyrose/elite_studio/synthesis/prompts/base_prompts.py` — prompt construction (60 lines)

### Intended Behavior

`base_render.py:1-11` states the intent explicitly:

> "Takes a techflat (vector design) + dossier and renders a **clean garment, no decoration**. Stage 3 adds the decoration via masked inpainting."

`base_prompts.py:50-55` reinforces this with explicit text negatives:

> "Render a clean, undecorated version of this garment... with NO logos, NO embroidery, NO patches, NO printed graphics, NO emblems, NO chest decoration, NO sleeve decoration, NO back decoration. The garment surface must be entirely undecorated."

### Actual Behavior

`base_render.py:75-89` constructs the fal.ai API call as:

```python
techflat_url = await client.upload(techflat_path)          # decorated techflat
prompt = build_base_prompt(dossier, view=view)              # text says "no decoration"

arguments = {
    "image_url": techflat_url,                              # image_url IS the conditioning
    "prompt": prompt,
    ...
}
fal_result = await client.subscribe(FLUX_KONTEXT_ENDPOINT, arguments=arguments)
```

FLUX Kontext Pro is an **image-conditioning model**. Its documented design (`base_render.py:7-9`) is: *"Kontext accepts an input image as conditioning and follows it tightly. The techflat IS the silhouette spec — Kontext preserves that."*

The same mechanism that preserves the silhouette **also preserves the decoration painted on that silhouette**. FLUX Kontext attends to spatial visual features in the conditioning image — logos, embroidery, patches, graphic prints are among the most visually prominent features in any techflat. Text negatives ("NO logos") operate at token prediction time, but image conditioning operates at spatial feature extraction time. **Image conditioning dominates**.

**Stage 1 always produces a decorated garment when given a decorated techflat.**

### Evidence

Visual inspection of sg-006 Stage 1 base output (confirmed in prior session): the front view shows the embroidered "SF" chest emblem, windbreaker chevron stripe, and sleeve patch carrier — all from the techflat, none requested in the text prompt.

### What Was Fixed (Prior Session)

`base_prompts.py:13-25` and `base_render.py:76` — added view-direction language and forwarded the `view` kwarg. This was a real bug (back renders showed front view). **This fix is necessary but does not address the decoration-on-Stage-1 root cause.**

---

## Stage 2: Gemini Flash Mask Derivation

### Files
- `skyyrose/elite_studio/synthesis/stages/mask_deriver.py` — full implementation (494 lines)

### Intended Behavior

`mask_deriver.py:1-18` states:

> "Given a Stage 1 base render (clean garment, no decoration) and the dossier, produce a binary mask where WHITE pixels mark the regions authorized for decoration... This is the structural innovation that prevents decoration drift: FLUX Fill in Stage 3 can ONLY paint inside the white pixels."

### Actual Behavior — Three Compounding Problems

#### Problem 1: Semantically Wrong Gemini Prompt (`mask_deriver.py:401-404`)

```python
def _build_mask_prompt(...) -> str:
    return (
        f"You are a fashion product imagery preprocessor. The attached image "
        f"shows a {garment_name} with NO decoration applied yet. ..."   # ← FALSE
    )
```

The prompt tells Gemini the Stage 1 image shows "NO decoration applied yet." But Stage 1 always produces a decorated garment. Gemini is being given a false premise. It will locate bounding boxes for the *decoration regions* correctly, but its analysis of the image is corrupted by the false claim.

In practice this means Gemini locates regions by matching them to the already-present decoration in the image — not by reasoning about where authorized regions should be on a blank garment. For complex SKUs (jerseys, windbreakers), Gemini will generate larger boxes than necessary because the decoration is clearly visible and prominent.

#### Problem 2: Over-coverage Warning Is Silently Dropped (`mask_deriver.py:230-237`)

```python
if coverage > MAX_MASK_AREA_FRAC:      # MAX_MASK_AREA_FRAC = 0.4 (line 62)
    warnings.append(
        f"mask coverage {coverage:.4f} above sanity ceiling {MAX_MASK_AREA_FRAC}"
    )

mask.save(mask_path)                   # ← saved regardless
...
return MaskResult(mask_path=mask_path, ..., warnings=warnings)
```

`MAX_MASK_AREA_FRAC = 0.40` is **warning-only**. The mask is saved and returned. Stage 3 receives it. Nothing in the current pipeline between Stage 2 and Stage 3 blocks execution on over-coverage. The guard added to `scripts/rerun_stage3.py` (prior session) prevents wasting FLUX budget on reruns, but the primary `generate_renders()` path has no equivalent gate.

#### Problem 3: `front-body` Static Template Is 44% Coverage Alone

```python
STATIC_REGION_BOXES: dict[str, tuple] = {
    "front-body": (0.20, 0.20, 0.80, 0.75),   # 60% width × 55% height = 33% area (normalized)
    "left-sleeve":  (0.06, 0.20, 0.24, 0.62),
    "right-sleeve": (0.76, 0.20, 0.94, 0.62),
    ...
}
```

The exact pixel-area coverage for `front-body` on a 1:1 image: `(0.80-0.20) × (0.75-0.20) = 0.60 × 0.55 = 0.33` (33%). With sleeve overlaps, three regions alone push past the 40% ceiling. sg-006 has 7-8 authorized decoration regions — their union was empirically measured at ~75%.

The static template fallback is thus structurally incapable of generating valid masks for complex SKUs.

---

## Stage 3: FLUX Fill Pro Masked Inpainting

### Files
- `skyyrose/elite_studio/synthesis/stages/decoration_inpaint.py` — orchestration (237 lines)
- `skyyrose/elite_studio/synthesis/prompts/decoration_prompts.py` — prompt construction (310 lines)

### Intended Behavior

`decoration_inpaint.py:1-11`:

> "Takes the Stage 1 base render (clean garment, no decoration) + the decoration mask + the dossier, and fills in each authorized decoration region with the correct visual element."

### Actual Behavior

When mask coverage exceeds ~40%, FLUX Fill Pro does not "fill in decoration" — it **regenerates the entire masked region** from scratch. The practical result:

| Mask coverage | Stage 3 behavior |
|---|---|
| < 10% | Surgical: decoration added, surrounding fabric preserved |
| 10–25% | Mixed: mostly additive, some local fabric disruption |
| 25–40% | Marginal: fabric texture and fine details often lost |
| > 40% | Destructive: near-full regeneration of the masked region |

At 75% mask coverage (sg-006 empirical), Stage 3 is effectively running a new generation inside a 75% cutout of the garment. The garment details inside the mask (fabric grain, seam stitching, construction structure) are replaced by FLUX's own hallucination of what that region should look like.

The net result of the current 3-stage pipeline for complex SKUs:

1. Stage 1 produces a decorated garment (wrong — should be clean)
2. Stage 2 generates a 75% mask covering most of the garment (too large)
3. Stage 3 near-fully regenerates the already-correct Stage 1 output (destructive)

**The pipeline is spending FLUX Fill Pro credits to make renders worse than Stage 1 alone.**

### What Stage 3 Gets Right

- `decoration_inpaint.py:103` — View filter correctly selects front/back decoration entries. Not a cause of failures.
- `decoration_prompts.py` — H3 double-negative prompt structure (ONLY-prefix + physics description + technique negative + tonal amplifier + UNIVERSAL_NEGATIVE_SUFFIX) is correctly implemented.
- `decoration_prompts.py` docstring note: violation feedback deliberately avoids naming the violation elements — naming hallucinated content in retry prompts causes it to reappear. This behavioral note is correct and must be preserved.

---

## Root Cause: The Clean-Canvas Assumption

The entire pipeline is built on one architectural assumption:

> **Stage 1 produces a clean, undecorated garment canvas.**

This assumption is structurally false. FLUX Kontext Pro is an image-conditioning model. Its `image_url` parameter is a conditioning signal, not a mask or silhouette guide. The techflat carries decoration. Kontext preserves decoration.

The assumption can only be made true by one of two approaches:

1. **Give Stage 1 a reference image with no decoration** (change the conditioning input)
2. **Treat Stage 1 as a candidate render, not a canvas** (change the pipeline role of Stage 1)

These are Path A and Path B.

---

## Path A: Plain Stage 1 via Silhouette Conditioning

### Concept

Replace the decorated techflat with a silhouette-only (flat-color fill, no logos, no graphics) image as the FLUX Kontext conditioning input. Stage 1 conditioning then carries silhouette, cut, and proportions without decoration. Text negatives at `base_prompts.py:52-54` become effective because the conditioning image no longer fights them.

### Why This Works

FLUX Kontext preserves the structure of its conditioning image. If the conditioning image has no decoration, there is nothing to preserve from the decoration side — only the garment shape remains. The text prompt then controls fabric texture, color, and construction details without fighting image conditioning.

### Implementation Plan

#### Step 1: `scripts/generate_silhouette.py` — new file

```python
"""Generate a flat-color silhouette from a decorated techflat.

Uses Pillow's edge detection + flood fill to isolate the garment
silhouette, then fills the interior with a single flat color matching
the dominant garment color from the dossier.
"""
from PIL import Image, ImageFilter
from pathlib import Path

def generate_silhouette(techflat_path: Path, *, flat_color: tuple[int,int,int]) -> Image.Image:
    """Return a PIL image: white background, garment silhouette in flat_color.
    
    Algorithm:
    1. Load techflat at native resolution.
    2. Apply edge filter (FIND_EDGES) to isolate boundary pixels.
    3. Flood-fill from image corner to isolate background (white → transparent).
    4. Fill garment interior with flat_color.
    5. Return composited result (white bg + flat garment).
    """
    ...
```

**Color extraction helper** — reads `dossier["garment_type_lock"]` for color keywords, maps to RGB.

#### Step 2: `base_render.py` — change conditioning source

```python
# BEFORE (current):
techflat_url = await client.upload(techflat_path)

# AFTER (Path A):
silhouette_image = generate_silhouette(techflat_path, flat_color=_garment_color(dossier))
silhouette_path = out_dir / f"{sku}-{view}-silhouette.png"
silhouette_image.save(silhouette_path)
silhouette_url = await client.upload(silhouette_path)
```

Change `"image_url": techflat_url` → `"image_url": silhouette_url`.

#### Step 3: `mask_deriver.py:401-404` — fix the false premise in the Gemini prompt

```python
# BEFORE:
f"shows a {garment_name} with NO decoration applied yet."

# AFTER:
f"shows a {garment_name} with a clean undecorated surface."
```

(This fix is required for Path A, optional but correct for Path B.)

#### Step 4: `mask_deriver.py:230-237` — hard block on over-coverage

```python
if coverage > MAX_MASK_AREA_FRAC:
    # Hard fail — do not proceed to Stage 3 with an over-large mask.
    raise OverMaskError(
        f"mask coverage {coverage:.3f} exceeds ceiling {MAX_MASK_AREA_FRAC}. "
        f"Review dossier region definitions for {dossier.get('name')}."
    )
```

### Path A Trade-offs

| | Pro | Con |
|---|---|---|
| **Correctness** | Stage 1 → genuinely clean canvas; pipeline design assumption becomes true | Silhouette extraction is non-trivial for complex garments (windbreakers, multiple panels) |
| **Stage 3 quality** | Small masks, surgical inpainting, fabric texture preserved | Fine construction detail (seam stitching, ribs) must come from text prompt alone |
| **Complexity** | No new pipeline stages | New silhouette extraction module; color extraction logic |
| **Failure mode** | Poor silhouette extraction → bad Stage 1 conditioning → poor results | Clearly diagnosable at Stage 1 output review |

---

## Path B: Audit-Driven Targeted Masking

### Concept

Accept that Stage 1 will produce a decorated garment. Treat it as a **candidate render**, not a canvas. Run H4 VisionAuditAgent on Stage 1 output immediately. The audit identifies which specific decoration regions are correct vs. incorrect. Stage 2 generates a mask covering **only the failed regions**. Stage 3 inpaints only the failed regions — a small, surgical mask.

### Why This Works

FLUX Kontext's conditioning on the decorated techflat is often beneficial: the resulting garment has correct construction, fabric, and proportions because the conditioning image carries all of that. The failure mode is specific: decoration is sometimes wrong (wrong color, wrong region, hallucinated elements). If we can identify and mask only the wrong regions, Stage 3 makes targeted corrections instead of regenerating the whole garment.

For SKUs where Stage 1 produces a correct render, the audit passes — zero FLUX Fill budget spent. The pipeline degrades gracefully to a single-stage operation.

### Implementation Plan

#### Step 1: `skyyrose/elite_studio/synthesis/stages/audit_filter.py` — new file

```python
"""Stage 1.5: Post-Stage-1 H4 audit + targeted mask restriction.

Calls VisionAuditAgent on the Stage 1 output. Returns:
  - accepted=True  → Stage 1 passed; skip Stages 2+3
  - accepted=False → violation_regions: list of region names that failed
    These are passed to Stage 2 as an allowlist.
"""
from dataclasses import dataclass

@dataclass
class AuditFilterResult:
    accepted: bool
    violation_regions: list[str]  # empty if accepted=True
    audit_detail: dict            # raw VisionAuditAgent result

async def audit_stage1(
    *,
    stage1_path: Path,
    dossier: dict,
    view: str,
) -> AuditFilterResult:
    ...
```

#### Step 2: `mask_deriver.py` — accept `allowed_regions` parameter

```python
def derive(
    self,
    *,
    image_path: str | Path,
    dossier: dict,
    view: str,
    out_dir: str | Path,
    allowed_regions: list[str] | None = None,   # ← new
) -> MaskResult:
    """When allowed_regions is provided, only those regions are masked."""
    ...
    decoration_entries = filter_decoration_entries(entries, view=view)
    if allowed_regions is not None:
        decoration_entries = [e for e in decoration_entries if e.region in allowed_regions]
    ...
```

#### Step 3: `mask_deriver.py:401-404` — fix the false premise

Same fix as Path A — the Gemini prompt must not claim the image shows "no decoration."

Since Stage 1 is decorated, the corrected Gemini prompt should be:

```python
f"The attached image shows a {garment_name}. Some decoration may or may not "
f"already be present. Identify the precise pixel location of the following "
f"regions on this garment:"
```

#### Step 4: `mask_deriver.py:230-237` — hard block on over-coverage

Same as Path A — over-coverage must block execution, not just warn.

#### Step 5: Primary pipeline orchestrator — wire the audit filter stage

In the main pipeline orchestrator (wherever `render_base` → `derive_mask` → `decoration_inpaint` are called sequentially):

```python
# Stage 1
base_result = await render_base(client=client, techflat_path=..., dossier=dossier, ...)

# Stage 1.5: Audit
audit = await audit_stage1(stage1_path=base_result.output_path, dossier=dossier, view=view)
if audit.accepted:
    return FinalRenderResult(path=base_result.output_path, source="stage1-accepted")

# Stage 2: Targeted mask — only failed regions
mask_result = mask_deriver.derive(
    image_path=base_result.output_path,
    ...,
    allowed_regions=audit.violation_regions,
)

# Gate: block if still over-masked
if mask_result.coverage_frac > MAX_MASK_AREA_FRAC:
    raise OverMaskError(...)

# Stage 3: Surgical inpainting
final = await run_inpainting(...)
```

### Path B Trade-offs

| | Pro | Con |
|---|---|---|
| **Correctness** | Preserves good Stage 1 garment construction; only repairs what's wrong | Pipeline is more complex (4 stages instead of 3 when audit fails) |
| **Cost efficiency** | Zero FLUX Fill spent when Stage 1 passes H4 audit | Extra Gemini Flash Vision call per render (Stage 1.5 audit) |
| **Stage 3 quality** | Small masks (only failed regions) → surgical inpainting preserves fabric | Still reliant on Stage 1 getting garment construction right |
| **Failure mode** | If Stage 1 produces wholesale wrong decoration, audit identifies many regions → mask is still large | Recoverable: fall back to full Stage 3 with guidance escalation |

---

## Recommended Path: B

Path B preserves FLUX Kontext's strongest contribution: accurate garment construction from image conditioning. The techflat is genuinely useful as a conditioning reference for silhouette, fabric weight, cut, and proportions. What the conditioning model struggles with is suppressing decoration — but the decoration it renders is often partially correct. Path B exploits the correct parts and surgically repairs the rest.

Path A requires silhouette extraction, which is a computer vision problem that must be solved well before Stage 1 conditioning improves. A poor silhouette extraction produces worse conditioning than the decorated techflat — trading a known failure mode for an unknown one.

The key insight: **the problem is not that Stage 1 renders decoration. The problem is that Stage 3 then regenerates that decoration destructively because the mask is too large.** Path B directly addresses mask size by making it proportional to actual violations.

**Decision required from Corey before any code is written.** No production test run until the decision is confirmed.

---

## Shared Fixes (Required for Both Paths)

These three changes are correct regardless of which path is chosen.

### Fix 1: `mask_deriver.py:401-404` — Correct the false Gemini premise

```python
# CURRENT (incorrect):
f"shows a {garment_name} with NO decoration applied yet."

# CORRECTED:
f"shows a {garment_name}. Your task is to locate the precise pixel bounds "
f"of the following authorized regions on this garment:"
```

**Why:** Gemini's bounding box output quality depends on its premise about the image. Telling it "no decoration" on a decorated image corrupts its spatial reasoning for region location.

### Fix 2: `mask_deriver.py:230-237` — Hard block on over-coverage

```python
# CURRENT (warning-only):
if coverage > MAX_MASK_AREA_FRAC:
    warnings.append(...)
mask.save(mask_path)     # proceeds regardless
return MaskResult(...)

# CORRECTED:
if coverage > MAX_MASK_AREA_FRAC:
    raise OverMaskError(
        f"Mask coverage {coverage:.3f} exceeds ceiling {MAX_MASK_AREA_FRAC} "
        f"for {dossier.get('name')} {view} view. "
        f"Regions: {[b['region'] for b in boxes]}. "
        f"Either reduce authorized regions or choose Path B audit filtering."
    )
```

**Why:** A warning that doesn't block execution is not a safeguard. The pipeline has already demonstrated it will spend FLUX Fill Pro budget on 75%-masked renders that produce worse output than Stage 1 alone.

### Fix 3: Primary pipeline — H4 Gate on Stage 1 before Stage 2

Even without Path B's targeted masking, the rerun_stage3.py pattern (Gate 1: accept Stage 1 if H4 passes) should be promoted to the primary generation path. Stage 1 sometimes produces a correct render — there is no reason to run Stages 2 and 3 in that case.

```python
# After Stage 1, before Stage 2:
audit = await audit_stage1(stage1_path=base_result.output_path, dossier=dossier, view=view)
if audit.accepted:
    logger.info("stage1 passed H4 audit — skipping stages 2 and 3")
    return FinalRenderResult(path=base_result.output_path, source="stage1-accepted")
# else: proceed to Stage 2
```

---

## Validation Strategy

After the chosen path is implemented:

1. **STOP AND SHOW before any FLUX call.** Confirm the manifest (SKU, view, cost estimate) with explicit `y` before dispatch.

2. **Smoke test — sg-006 front only:**
   - Path A: Inspect silhouette image before Stage 1. Verify Stage 1 output is visually clean. Inspect Stage 2 mask coverage (must be < 40%). Inspect Stage 3 output.
   - Path B: Confirm Stage 1.5 audit JSON is plausible. Confirm `violation_regions` list is correct. Confirm Stage 2 mask covers only those regions. Confirm Stage 3 output fixes only the violation regions.

3. **Cost cap for smoke test:** 2 FLUX Kontext Pro calls + 2 FLUX Fill Pro calls maximum. If smoke test fails twice, stop and re-evaluate.

4. **View parity test — sg-006 back:**
   - After front passes smoke test, run back view.
   - Confirm back view shows back panel only (view fix from prior session).

5. **Multi-SKU batch:**
   - Only after sg-006 front + back pass H4 audit end-to-end.
   - Present full batch manifest + cost before dispatch.

---

## Files to Modify by Path

### Path B (recommended) — Minimum change set

| File | Change | Lines affected |
|---|---|---|
| `synthesis/stages/base_render.py` | No change to Stage 1 itself — view fix already in | — |
| `synthesis/stages/mask_deriver.py` | Fix Gemini false-premise (line 401-404); add `allowed_regions` param (line 152); hard-block over-coverage (line 230-237) | ~30 lines |
| `synthesis/stages/audit_filter.py` | **NEW** — Stage 1.5 H4 audit wrapper (~80 lines) | new file |
| `synthesis/stages/__init__.py` | Export `audit_stage1`, `AuditFilterResult` | ~5 lines |
| Primary pipeline orchestrator | Wire Stage 1.5 between Stage 1 and Stage 2; pass `violation_regions` to Stage 2 | ~20 lines |
| `scripts/rerun_stage3.py` | Remove Gate 1 duplicate (now handled by primary path); keep Gate 2 | ~15 lines removed |

### Path A (alternative) — Additional change set

| File | Change |
|---|---|
| `scripts/generate_silhouette.py` | **NEW** — silhouette extraction (~100 lines) |
| `synthesis/stages/base_render.py` | Generate silhouette before upload; change `image_url` source (~15 lines) |
| `synthesis/prompts/base_prompts.py` | No change (text negatives become more effective automatically) |

---

## Memory Update Protocol

Memory will be updated after:
1. This decision is confirmed by Corey (Path A or Path B)
2. The chosen path is implemented
3. sg-006 front + back pass H4 audit end-to-end
4. No regression on a second SKU (different garment type)

**Not before.** Updating memory to record an architectural choice that hasn't been proven end-to-end would recreate the same drift problem the dossier system was designed to prevent.

Planned memory entries (post-validation):
- `project_render_pipeline.md` — architecture decision record: which path, why, key file:line citations
- `feedback_no_silent_fallback.md` (update) — extend to cover `MAX_MASK_AREA_FRAC` warning-only anti-pattern
