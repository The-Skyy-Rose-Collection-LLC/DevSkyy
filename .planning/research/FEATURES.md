# Feature Landscape: Ghost Mannequin AI Imagery Pipeline

**Domain:** AI product photography pipeline for luxury streetwear ecommerce
**Researched:** 2026-04-22
**Milestone:** v1.2 — CSV-Driven Ghost Mannequin Generation
**Confidence:** HIGH

---

## Table Stakes

Features that must exist or the output is unusable, unprofessional, or unshippable to WooCommerce.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Pure RGB-255 white background | WooCommerce product images require clean white; any color cast or shadow residue reads as "cheap budget brand" | Low | Must be enforced programmatically, not eyeballed |
| 3D volume / inflation of techflat | A flat techflat dropped onto white looks like clipart. Ghost mannequin means implied body volume — fabric drape, collar open, sleeve depth | High | This is the core technical problem; Gemini 2.5 Flash Image is the current nano-banana workaround |
| Collar/neckline interior reconstruction | The interior hollow at the neck opening is the single quality signal luxury buyers notice first — collapsed collar = amateur | High | Jerseys and hoodies fail most often here |
| Clean garment segmentation edge | No halo artifacts, no jagged mask edge, no missed pixels from a complex hem or rib knit | Medium | Techflat source makes this easier than model photos |
| SKU-addressable output path | Every output maps to a known SKU and goes to `renders/ghost-mannequin/{sku}-ghost-front.webp` — no ambiguity, no overwriting | Low | Already defined in PROJECT.md |
| STOP AND SHOW cost manifest | No paid API call without user confirmation showing exact SKU list, API, cost estimate per image, total cost | Low | Non-negotiable per project protocol |
| Batch execution from CSV | Script accepts list of SKUs (or "all") and processes in sequence without human per-image intervention | Medium | Feeds from `skyyrose-catalog.csv` via `catalog_loader.py` |
| WebP output at 1200x1200px | WooCommerce renders product thumbnails from source; source must be square, 1200px minimum, WebP for performance (25-35% smaller than JPEG at equivalent quality) | Low | Output to `.webp`, quality 85 |
| Techflat-to-generation input mapping | Know which `data/product-bundles/{name}/techflat-front.jpeg` corresponds to which SKU — 15 name-mismatch cases exist | Medium | Canonical mapping is the SKU→bundle resolver task |
| Failure logging per SKU | When generation fails (API error, content filter, low confidence), log it — don't silently skip | Low | Needed for batch runs of 30 products |
| Review-before-commit gate | Outputs go to `renders/ghost-mannequin/` for human approval; `front_model_image` in CSV is only updated after explicit approval | Low | Prevents bad images going live |

---

## Differentiators

Features that separate a luxury brand's imagery pipeline from a discount streetwear brand running the same Gemini API call.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Garment-type routing | Jersey prompt ≠ hoodie prompt ≠ shorts prompt. Each garment type has different volume cues, collar behavior, and failure modes. Routing by garment type in the CSV yields consistently better output per category | Medium | Add `garment_type` field or derive from product name; drive prompt selection |
| Jersey-specific text/number preservation check | Jerseys with "Black Is Beautiful" text and alternating rose number fills are the hardest garment type. Output QC must verify text readability is not degraded or hallucinated by the generation model | High | Gemini's known weakness with text; post-generation clip check or hash comparison against known text zones |
| Per-SKU confidence scoring and auto-flag | After generation, score the output: background whiteness (pixel sample), edge cleanliness (edge variance), collar depth (center-crop darkness). Flag any SKU below threshold for manual review rather than silently including bad output in the batch | Medium | Avoids bad images reaching the approval queue looking plausible |
| Dry-run / cost preview mode | Run the full pipeline in estimation-only mode: print exactly which SKUs would be processed, which API, what the per-image and total cost estimate is — without calling any API | Low | Critical for large batches; pairs with STOP AND SHOW |
| Retry with alternate prompt on failure | If generation fails or scores below threshold, automatically retry with a simplified fallback prompt before flagging for manual review | Medium | Saves manual re-runs for transient model failures |
| Consistent lighting style across batch | All 30 products shot in the same simulated studio lighting (soft front key, subtle fill). Inconsistency across a 30-product catalog reads as unfinished — luxury brands have a coherent visual language | Medium | Encode lighting direction in every prompt; do not let model choose |
| Background purity validation | Programmatically sample corner pixels and check they are within 5 RGB units of 255,255,255. Reject if not — a grey-white background is a hard failure for a premium brand | Low | PIL/Pillow corner-sample check after generation |
| CSV update tool with approval workflow | CLI command: `approve-ghost {sku}` moves approved file to final path and updates `front_model_image` field in CSV. `reject-ghost {sku}` keeps file in review directory and logs rejection reason | Low | Closes the pipeline loop without manual file management |

---

## Anti-Features

Deliberately out of scope for v1.2. Building these wastes time and creates scope creep.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Back garment generation | Back ghost mannequin requires a separate techflat-back source asset, which most SKUs don't have. Building back generation in v1.2 creates a dependency we can't satisfy | Defer to v1.3 after back techflats are confirmed per-SKU |
| Model composite in this pipeline | Elite Studio compositor handles scene + model compositing. Ghost mannequin is the separate, simpler, white-background studio shot. Merging them adds complexity with no gain | Keep pipelines separate; ghost mannequin is white-bg only |
| Real-time API during web request | Ghost mannequin generation takes 10-60 seconds per image. Do not wire this into any synchronous web path | Batch script only; outputs are static files |
| Automated WooCommerce upload | Uploading generated images to WooCommerce Media Library costs money (API write) and is irreversible. Human review gate must come first | Manual upload after approval; automate in v1.3 if desired |
| Frontend review UI | A web UI for reviewing generated images adds a new system to build and maintain. The filesystem + CLI approval tool is sufficient for a 30-product catalog | CLI approval tool is enough for current catalog size |
| Multi-angle generation (side, back, 3/4) | Multi-angle requires multiple techflat source angles. We have front only. Attempting multi-angle from a single source produces hallucinated geometry | Single-angle (front) only until source assets exist |
| Prompt tuning UI / prompt editor | A UI for editing generation prompts per-SKU is premature. Garment-type routing covers 95% of variation needed at this catalog size | Hard-code garment-type prompt templates; edit in code |
| Automatic style transfer between collections | Cross-collection lighting/style consistency is handled by consistent prompt templates. Do not build automatic style matching — it adds inference cost and unpredictability | Prompt templates enforce style; no additional model pass |

---

## Garment-Type Considerations

This is the most technically important section for SkyyRose's specific catalog.

### Jersey (Black Rose, Signature, Love Hurts collections)

The hardest garment type in the catalog. Specific challenges:

- **Text and number rendering**: "Black Is Beautiful" jerseys have stitched text and alternating rose-fill numbers. Generation models frequently hallucinate or blur text on garments. The output QC step must check that text zones are not degraded.
- **Mesh fabric**: Athletic mesh is semi-transparent and has visible interior. Generation must preserve mesh texture, not fill it as solid fabric.
- **Reflective trim**: Moisture-wicking materials create chromatic aberration (purple/green color fringing) at high-contrast edges under simulated studio light. Prompt must specify matte, non-reflective rendering.
- **Number fill pattern**: The alternating rose fill (front: left=rose, right=plain; back: reversed) is brand-critical. Any hallucination of the number pattern is a reject.
- **Collar type**: V-neck or crew neck jersey collars require interior reconstruction. V-necks are harder — the opening angle is wider and the interior fill more visible.
- **Prompt strategy**: Specify garment type as "athletic mesh jersey", describe collar shape explicitly, reference fabric as "performance mesh, non-reflective, matte finish".

### Hoodie / Sweatshirt

Medium difficulty. Challenges:

- **Hood drape**: The hood should be positioned down and draped naturally. Flat hoods or unnaturally rigid hoods read as cheap.
- **Kangaroo pocket**: Should have visible depth and natural sag, not a flat painted rectangle.
- **Ribbed hem and cuffs**: Rib knit texture is a common AI failure point — models often smooth it into solid color.
- **Thick fabric volume**: Heavier fabric than jersey. The 3D inflation needs more shoulder width and chest depth.
- **Prompt strategy**: Specify "heavyweight fleece hoodie, hood resting on shoulders, kangaroo pocket with natural depth, ribbed cuffs and hem".

### Jogger / Shorts (lower body)

Different pipeline path — lower body garments need a different crop and body positioning reference.

- **Waistband volume**: Elastic waistband must appear to have a waist inside it, not be a flat band.
- **Inseam depth**: Shorts especially need visible inseam depth to read as 3D.
- **Drawstring**: Must render naturally hanging, not floating or missing.
- **Prompt strategy**: Specify "lower body" garment type explicitly. Use "waistband stretched to natural waist width, legs with fabric drape and volume, drawstring hanging naturally".

### Beanie / Hat (accessories)

Easiest garment type but different approach:

- **No body inflation needed**: Beanies need a head form, not a torso.
- **Not a classic ghost mannequin use case**: Invisible head mannequin, or styled on a flat surface.
- **Prompt strategy**: Consider flat-lay or "styled on invisible head" approach rather than standard ghost mannequin prompt.

### Jacket / Outerwear

Highest complexity if present in catalog:

- **Lapels and collar**: Multiple fabric layers, complex collar geometry.
- **Hardware**: Zippers, snaps, and rivets are common AI failure points (hallucinated or misplaced).
- **Lining visibility**: If lining is visible at collar, it must render accurately.

---

## Quality Bar: What "Luxury" Means Technically

The gap between "cheap AI product photo" and "luxury brand product photo" is measurable:

| Quality Signal | Cheap | Luxury |
|----------------|-------|--------|
| Background | Off-white (240-250 RGB), visible gradient or shadow | Pure white (255, 255, 255) ± 3 RGB, no cast |
| Edge quality | Halo artifacts, jagged mask at collar and sleeves | Clean segmentation, no fringing |
| Collar interior | Flattened, filled solid, or missing | Deep hollow, visible interior fabric texture |
| Fabric texture | Smoothed over, AI-softened | Preserved: mesh holes, rib knit pattern, weave visible |
| Volume | Flat, 2D appearance | Clear 3D depth at chest, shoulders, sleeves |
| Text/graphics | Blurred, hallucinated, shifted | Pixel-accurate to source techflat |
| Lighting | Default diffuse, no direction | Consistent soft front key + subtle fill across entire catalog |
| Resolution | Under 1000px, upscaled | 1200x1200px native WebP at 85 quality |
| Consistency | Different look per garment | Unified studio aesthetic across all 30 SKUs |

---

## Batch vs. Single-Product Tradeoffs

| Dimension | Batch (all 30 SKUs) | Single SKU |
|-----------|---------------------|------------|
| Cost control | Highest risk — requires STOP AND SHOW manifest first | Easy to control — one image at a time |
| Speed | All 30 in one run; async where API supports it | Interactive, immediate feedback |
| Error handling | Must capture per-SKU failure without aborting the batch | Immediate retry, no partial-run state |
| Review burden | 30 images to review at once; harder to maintain quality attention | One image; complete review before next |
| Failure mode | One bad techflat mapping silently corrupts N outputs | Failure is immediately visible |
| Recommended use | After all SKU→bundle mappings are verified; after a single-SKU dry run succeeds | For initial testing, new garment types, failed SKUs from batch |

**Recommended approach for v1.2**: Run single-SKU tests for one of each garment type (jersey, hoodie, shorts) before the 30-product batch run. Validate garment-type prompts. Then run batch with full STOP AND SHOW manifest.

---

## Feature Dependencies

```
CSV adapter (catalog_loader.py)
        |
        +-- SKU→bundle resolver (canonical mapping for all 30 products)
                |
                +-- Techflat input loader (reads techflat-front.jpeg per SKU)
                        |
                        +-- Garment-type router (jersey/hoodie/shorts/other → prompt template)
                                |
                                +-- Generation call (Gemini 2.5 Flash Image via nano-banana)
                                        |
                                        +-- Post-generation QC
                                        |     - Background whiteness check (corner pixel sample)
                                        |     - Edge variance check (flag halos)
                                        |     - Collar depth check (center-crop darkness)
                                        |     - Text zone check for jerseys (hash comparison)
                                        |
                                        +-- Output write (renders/ghost-mannequin/{sku}-ghost-front.webp)
                                                |
                                                +-- Review approval gate (human confirms)
                                                        |
                                                        +-- CSV front_model_image update tool
```

---

## MVP Recommendation

For v1.2, build in this order:

1. **SKU→bundle canonical mapping** — blocked on this; nothing else works without it
2. **CSV adapter integration** — `catalog_loader.py` wired into nano-banana; already partially done
3. **Garment-type prompt templates** — jersey / hoodie / lower-body / accessory; 4 templates
4. **Single-SKU dry-run mode** — test one jersey (br-001), one hoodie, one lower-body before batch
5. **STOP AND SHOW cost manifest** — required before any batch API call
6. **Batch generation script** — all 30 SKUs, per-SKU failure logging, no silent skips
7. **Post-generation QC checks** — background whiteness, auto-flag below threshold
8. **CSV update tool** — `approve-ghost {sku}` and `reject-ghost {sku}` CLI commands

Defer:
- Back garment generation (no source assets)
- Jersey text-zone hash comparison (nice-to-have; manual review catches most failures)
- WooCommerce automated upload (requires human review gate to work correctly first)

---

## Sources

- [8 best AI ghost mannequin tools for ecommerce (2026)](https://www.wearview.co/blog/best-ai-ghost-mannequin-tools) — MEDIUM confidence
- [AI Ghost Mannequin Generator for Fashion Ecommerce: 2026 Comparison](https://www.rewarx.com/blogs/ai-ghost-mannequin-generator-fashion-ecommerce-comparison-2026) — MEDIUM confidence
- [Ghost Mannequin AI Workflow — Photta](https://www.photta.app/blog/ai-ghost-mannequin-workflow) — MEDIUM confidence
- [Fix Ghost Mannequin Reflective Athletic Wear Artifacts](https://imageworkindia.com/fix-ghost-mannequin-reflective-athletic-wear-artifacts/) — HIGH confidence (practitioner guide)
- [Automated Ghost Mannequin Workflow for TikTok Shop](https://imageworkindia.com/automated-ghost-mannequin-workflow-tiktok-shop/) — HIGH confidence (practitioner guide)
- [WooCommerce Product Image Size 2026](https://litos.io/blog/woocommerce-product-image-size/) — HIGH confidence (WooCommerce official ecosystem)
- [Shopify Product Image Requirements 2026](https://www.squareshot.com/post/shopify-product-image-requirements) — MEDIUM confidence (platform standards are broadly consistent with WooCommerce)
- PROJECT.md v1.2 requirements — HIGH confidence (canonical for this project)

*Research completed: 2026-04-22*
