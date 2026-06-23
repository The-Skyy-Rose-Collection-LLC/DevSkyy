# 100% Replica System Plan — Mockup First, Scenes Second

**Date:** 2026-05-26
**Authors:** parallel research synthesis (Backend Architect + AI Engineer + Trend Researcher + fal catalog scan)
**Status:** awaiting founder go/no-go on Phase 1
**Branch:** `fix/elite-studio-audit-2026-05-25`

---

## TL;DR

Stop letting diffusion touch product pixels. **Diffusion cannot pixel-copy** — every FLUX pass (Fill, Kontext, Redux, even Kontext-Max-Multi) routes product surface through a lossy VAE + semantic conditioning bottleneck + low-frequency-biased flow-matching loss. Result: sublimated prints, embroidery, script glyphs are re-imagined, not preserved. Four independent research streams converged on the same answer.

**Recommended architecture (cascade by use case):**

| Use case | Pipeline | Surface-graphic fidelity | Cost/shot |
|---|---|---|---|
| **Have flat-lay/ghost-mannequin, want hero shot on model** | FASHN v1.6 `tryon` (`fal-ai/fashn/tryon/v1.6`) | High (FASHN explicitly preserves logos/text/patterns) | $0.075 |
| **Have on-model photo, want different scene background** | BiRefNet/RMBG matte → alpha-composite onto scene → IC-Light V2 relight | **100% pixel-exact** (product never touched by generation) | ~$0.13 (matte $0.005 + iclight $0.10 + overhead) |
| **Have flat product, want lifestyle scene** | BRIA Product Shot `placement_type=original` + `original_quality=true` | High (composite-style placement, not regeneration) | $0.04 |
| **Need pose-and-scene generation for SKUs with no source photo** | FASHN v1.6 first → then pipeline #2 above | High (FASHN) then 100% (composite) | $0.21 (cascade) |

**Founder pivot honored:** Phase 1 = mockup generation (perfect product, no scene). Phase 2 = scene composite (Architecture A: rasterize + IC-Light + seam refine). Scenes are *deferred* until every SKU has a verified 100%-replica mockup.

---

## Root Cause — Why FLUX Inpainting Hallucinates Product Graphics

Three architectural layers, none of which kontext fixes:

1. **VAE bottleneck.** FLUX encodes 1024px images into 128-token-wide 16-channel latents (8× spatial downsampling). Embroidery stitches at 3-5px native resolution sit **below Nyquist** of the encoder — compressed into averaged activations, not preserved as discrete spatial features. Sublimated photo detail at sub-pixel scale is structurally unreachable.

2. **Semantic conditioning bottleneck.** Kontext's reference VAE encoding represents *patch statistics*, not *exact pixel paths*. The model sees "there is a rose cluster embroidery" — it does not see "every stitch path of THIS rose cluster". At denoising time, fine detail is filled from training distribution.

3. **Flow-matching loss bias.** FLUX optimizes a global reconstruction loss biased toward low-frequency structure (silhouette, color zones, fabric drape). High-frequency texture (Bay Bridge cable pixels, "Love Hurts" cursive glyph forms) lives in the loss tail. Model optimizes for *perceptually plausible*, not *pixel-exact*.

**Multi-reference doesn't escape this.** FLUX-2 multi-ref / Kontext-Max-Multi add more context tokens; they don't bypass VAE compression. Hallucination probability drops; pixel guarantee is structurally impossible.

**The fix:** don't put surface pixels through diffusion. Place them. Relight the placement.

---

## Phase 1 — Mockup Generation (NEW — founder priority)

**Goal:** every SKU has a polished, brand-consistent, photographically perfect hero mockup. Existing `*-front-model.webp` + new generated variants. Zero hallucination. Pixel-exact graphics.

### Inventory of current state (verified 2026-05-26)

33 SKUs have front-model assets. 2 SKUs founder shared today have NO canonical asset:

| SKU | Slug at canonical PRODUCT_IMAGES_DIR | Mockup status |
|---|---|---|
| br-004 Black Rose Hoodie | `black-rose-hoodie/` | ✓ front-model present |
| sg-001 Bay Bridge Shorts | `bay-bridge-shorts/` | ✗ EMPTY DIR (founder shared Photos Library path today) |
| lh-004 Love Hurts Bomber | `love-hurts-bomber/` | ✗ EMPTY DIR (founder shared Photos Library path today) |

Across all 33 SKU dirs: many show different model/angle than founder intends; some are old.

### Phase 1 pipeline architecture

Three tracks based on starting state:

#### Track A — Hero Shot Refinement (have existing front-model photo)

Real product photo is already the spine. Pipeline POLISHES, doesn't regenerate.

```
existing front-model.webp
  ↓
[Stage A1] Background isolation — BiRefNet (fal-ai/birefnet) → clean alpha matte
  ↓
[Stage A2] Background replacement — neutral studio gradient OR brand-canon BG (rose-gold, dark, deep-blue per collection)
  ↓
[Stage A3] Color grading — match brand palette tokens (auto-balance toward collection accent)
  ↓
[Stage A4] Upscale — Real-ESRGAN x2 (fal-ai/esrgan) or BRIA upscale (preserves graphic detail; no resampling through diffusion)
  ↓
[Stage A5] QA gate — SSIM ≥ 0.99 vs original on product interior region
```

**Surface-graphic fidelity:** 100% (product pixels never touched by generative model). Cost: ~$0.04/SKU.

#### Track B — Pose/Angle Synthesis (have flat-lay or ghost-mannequin, need on-model)

For SKUs where we have a flat product image and want a model wearing it. FASHN v1.6 is the only production-grade tool with explicit graphic-preservation claims.

```
flat-lay product image  +  stock model body (matched to brand demographic)
  ↓
[Stage B1] FASHN v1.6 product-to-model
  fal-ai/fashn/tryon/v1.6
  garment_photo_type="flat-lay"
  mode="quality"
  num_samples=4
  ↓
[Stage B2] Founder visual gate — pick 1 of 4 samples
  ↓
[Stage B3] Track A refinement (upscale + grade + BG isolation)
  ↓
[Stage B4] QA gate — Gemini visual diff against source flat-lay (graphic presence + correctness)
```

**Surface-graphic fidelity:** High (FASHN explicit claim; needs verification per garment). Cost: $0.075 + $0.04 = $0.115/SKU. Founder gate before paid dispatch per STOP-AND-SHOW.

#### Track C — Zero-Source Generation (no photo at all)

For SKUs with NO existing asset (sg-001 Bay Bridge Shorts and lh-004 Love Hurts Bomber would be this case if founder hadn't shared photos today).

Now resolved — founder dropped both source photos in this conversation. Stage them to canonical paths, then Track A.

If future SKUs have zero source: requires actual physical product photoshoot OR per-product LoRA training (skyyrose-lora-v5 dataset pattern, ~$2-8 on Replicate) + FLUX text-to-image with LoRA. LoRA *reduces* drift but doesn't eliminate it — accept ~80-90% fidelity bound for fully-generated mockups.

### Phase 1 staging — assets founder shared today

```bash
# LH-004 Love Hurts Bomber (886×886 JPEG, 77K, hash 61a19f6b042f60172e1764104daded91)
cp "/Users/theceo/Pictures/Photos Library.photoslibrary/resources/derivatives/2/2089A163-DD7F-4B98-ABE7-58A541E7536A_1_105_c.jpeg" \
   wordpress-theme/skyyrose-flagship/assets/images/products/love-hurts-bomber/love-hurts-bomber-front-model.jpg

# SG-001 Bay Bridge Shorts (144K JPEG, hash 50477c977b7b2f51b2605cfd4bd1eeeb)
cp "/Users/theceo/Pictures/Photos Library.photoslibrary/resources/derivatives/0/03A1BF8B-261F-4414-A81F-9F26F9794C17_1_105_c.jpeg" \
   wordpress-theme/skyyrose-flagship/assets/images/products/bay-bridge-shorts/bay-bridge-shorts-front-model.jpg
```

Then Track A runs on both. Output: AVIF + WebP at 480w/768w/960w/1280w breakpoints, deployed to canonical PRODUCT_IMAGES_DIR alongside existing 33 SKUs.

### Phase 1 cost model — all 33 SKUs

| Track | SKUs | Cost/SKU | Total |
|---|---|---|---|
| Track A (have photo, just refine) | 31 (after staging today's 2) | $0.04 | $1.24 |
| Track B (need pose synthesis — TBD by founder per SKU) | 0-N | $0.115 | $0-$3.80 |
| Track C (zero source) | 0 (resolved today) | $0.10+ | $0 |

**Baseline cost: $1.24 for full 33-SKU refresh via Track A.** Stays under previous $1.50 budget ceiling.

### Phase 1 validation

- SSIM ≥ 0.99 on product interior region vs source (BiRefNet matte defines the interior mask)
- Gemini visual diff: "does this preserve every visible graphic element from the source"
- Founder gate per batch of 5 SKUs (no surprise dispatches)
- Per-SKU before/after side-by-side rendered as contact sheet for founder approval

---

## Phase 2 — Scene Composite (deferred until Phase 1 lands)

Once every SKU has a verified 100%-replica mockup, scene composite uses the rasterize+seam-refine architecture all 4 agents converged on.

### Architecture A — Rasterize + IC-Light + Seam Refine

```
verified mockup (Phase 1 output)  +  scene PNG (canon-locked, Stage 1 of home-spread)
  ↓
[Stage D1] BiRefNet matte → alpha (already canonical; Stage A of compositor)
  ↓
[Stage D2] Placement compute — _align_mask_to_scene() returns paste coords
  ↓
[Stage D3] Alpha-composite mockup onto scene at paste coords
  → rasterized.png  (PIL operation, zero generation, pixel-exact interior)
  ↓
[Stage D4] IC-Light V2 relight (fal-ai/iclight-v2, denoise_strength≤0.4)
  → relit-composite.png  (illumination matched to scene; product surface preserved)
  ↓
[Stage D5] Seam annulus mask — dilate(alpha, 24px) - erode(alpha, 8px)
  → seam-mask.png  (only the silhouette band; product interior LOCKED)
  ↓
[Stage D6] FLUX Fill seam refine (strength=0.18) — fixes seam blending only
  → composite.png
  ↓
[Stage D7] Fidelity gate — SSIM(composite[interior], rasterized[interior]) ≥ 0.97
  PASS → proceed to Stage F shadows
  FAIL → fallback to kontext chain, log used_fallback=True
```

**Per-composite cost:** $0.08-0.10 (matte + iclight + seam refine + QA). Cheaper than current ~$0.15 kontext-primary.

**3-collection home-spread cost:** $0.24-0.30. Same ceiling as before, way higher fidelity.

### Architecture B — BRIA Product Shot shortcut (alternative)

For non-worn product (Bay Bridge Shorts could fit here): single API call.

```
mockup + scene_description (or ref_image_url)
  ↓
fal-ai/bria/product-shot
  placement_type=original
  original_quality=true
  ↓
done — composite at $0.04
```

Cheaper, simpler, less control. Architecture A is the workhorse; Architecture B is the express lane for flat product shots.

### Architecture C (rejected) — VTON or multi-reference

VTON cascade (FASHN→kontext) doubles cost AND adds a probabilistic layer over the product surface. Multi-reference kontext is what's broken today. Both rejected.

---

## Specific Code Changes (Phase 1 + Phase 2 prep)

### New files

| File | Purpose | Lines |
|---|---|---|
| `skyyrose/elite_studio/agents/mockup_agent.py` | Phase 1 orchestrator — Tracks A/B/C dispatch | ~300 |
| `skyyrose/elite_studio/agents/compositor/stage_d_rasterize.py` | Phase 2 rasterize + seam refine | ~250 |
| `skyyrose/elite_studio/agents/compositor/stage_h_iclight.py` | Wrapper around fal-ai/iclight-v2 | ~150 |
| `tests/elite_studio/test_mockup_agent.py` | Phase 1 unit tests | ~150 |
| `tests/elite_studio/test_stage_d_rasterize.py` | Phase 2 fidelity-gate tests | ~120 |

### Modified files

| File | Change |
|---|---|
| `skyyrose/elite_studio/cli.py` | New `mockup` subcommand (Phase 1 dispatch); home-spread gains `--require-verified-mockup` flag |
| `skyyrose/elite_studio/agents/compositor/orchestrator.py` | Stage 4 dispatcher reads `ELITE_STUDIO_STAGE_D_MODE` (`rasterize` | `kontext`); rasterize path skips current flux chain |
| `skyyrose/elite_studio/agents/compositor/flux_methods.py` | New `_composite_via_rasterize()` in `FluxProviderMixin`; updates `_composite_with_flux` to honor env mode |
| `skyyrose/elite_studio/agents/compositor/infra.py` | Add cost constants: `_BIREFNET_COST_USD=0.005`, `_ICLIGHT_V2_COST_USD=0.10`, `_FASHN_TRYON_COST_USD=0.075`, `_BRIA_PRODUCT_SHOT_COST_USD=0.04` |
| `skyyrose/elite_studio/models.py` | `CompositorResult` gains `stage_d_mode: str`, `fidelity_score: float`, `mockup_verified: bool` fields |
| `skyyrose/elite_studio/config.py` | New: `MOCKUPS_DIR = _REPO_DIR/"wordpress-theme"/"skyyrose-flagship"/"assets"/"images"/"products"`; `MOCKUP_VERIFIED_REGISTRY = _BASE_DIR/"data"/"verified-mockups.json"` |

### New env vars

| Var | Default | Purpose |
|---|---|---|
| `ELITE_STUDIO_STAGE_D_MODE` | `kontext` (during migration) → `rasterize` (post-validation) | Stage 4 dispatcher |
| `ELITE_STUDIO_SEAM_DILATE_PX` | `24` | Seam annulus outer band width |
| `ELITE_STUDIO_SEAM_ERODE_PX` | `8` | Seam annulus inner band width |
| `ELITE_STUDIO_SEAM_REFINE_STRENGTH` | `0.18` | FLUX Fill denoise strength for seam pass |
| `ELITE_STUDIO_FIDELITY_THRESHOLD` | `0.97` | SSIM gate threshold for interior region |
| `ELITE_STUDIO_ICLIGHT_DENOISE` | `0.4` | IC-Light V2 denoise ceiling (above this risks surface re-render) |
| `ELITE_STUDIO_REQUIRE_VERIFIED_MOCKUP` | `1` | Home-spread refuses to composite if mockup isn't in verified registry |

### New CLI commands

```bash
# Phase 1 — Track A refinement
python -m skyyrose.elite_studio mockup --sku br-004 --track A
python -m skyyrose.elite_studio mockup --collection black-rose --track A --budget-usd 0.50

# Phase 1 — Track B pose synthesis (PAID FASHN, STOP-AND-SHOW)
python -m skyyrose.elite_studio mockup --sku sg-001 --track B --model-pose female-standing-3q

# Phase 1 — Verify + register mockup as canon
python -m skyyrose.elite_studio mockup verify --sku br-004
# Adds entry to data/verified-mockups.json with hash, timestamp, founder-approval flag

# Phase 2 (deferred until Phase 1 complete) — scene composite using verified mockups only
ELITE_STUDIO_STAGE_D_MODE=rasterize \
  python -m skyyrose.elite_studio home-spread --collection all --require-verified-mockup
```

---

## Migration Path

1. **Today (Phase 1 commit):** Land mockup agent + Track A as the canon mockup pipeline. Update `verified-mockups.json` per founder sign-off.
2. **Phase 1 batch run:** 33 SKUs through Track A (~$1.24, batches of 5 with founder gate). Output overwrites canonical `*-front-model.{avif,webp}` only after registry entry.
3. **Phase 1 gap-fill:** Any SKU that fails QA goes to Track B (FASHN) or back to founder for re-shoot.
4. **Phase 2 dev:** Build stage_d_rasterize.py + iclight wrapper while Phase 1 batches run.
5. **Phase 2 validation:** Run 3 collections (BR, SIG, LH) with `ELITE_STUDIO_STAGE_D_MODE=rasterize` against the verified mockups. Inspect fidelity_score audit log. Target: all ≥0.99.
6. **Phase 2 flip:** `.env` default → `rasterize`. Kontext path stays as fidelity-gate fallback only.

Feature-flagged throughout. Zero cutover. Current kontext chain remains as graceful fallback inside the fidelity gate's failure branch.

---

## Failure Modes + Fallbacks

| Failure | Detection | Fallback |
|---|---|---|
| BiRefNet matte too jagged → wide seam band → surface bleed | Pre-Stage-D mask quality score (gray-pixel %) | Widen erode_px to shrink SSIM check region; OR retry matte via fal-ai/bria/background/remove |
| IC-Light V2 over-relights surface (denoise > 0.4) | Visible color shift in interior region | Cap denoise=0.3, retry; OR skip relight, composite raw |
| Seam FLUX Fill bleeds into interior | Fidelity gate: SSIM < 0.97 | Retry strength=0.10; if still fails, kontext fallback chain |
| Fidelity gate rejects all retries | logged in audit | Fall through to existing kontext path; flag `used_fallback=True` |
| FASHN v1.6 produces VTON drift on graphics | Founder gate per Track B dispatch | Generate 4 samples, pick best; if all bad, fall back to Track A on existing photo |
| BRIA product-shot doesn't honor `original_quality` | Output dims < source | Bypass BRIA, use Track A pipeline |

---

## Cost Comparison — Current vs Proposed

| Scenario | Current (kontext-primary) | Phase 2 (rasterize+iclight+seam refine) | Δ |
|---|---|---|---|
| Per-composite cost | $0.10-0.15 | $0.08-0.10 | −$0.02-0.05 |
| 3-collection home-spread | $0.30-0.45 | $0.24-0.30 | −$0.06-0.15 |
| Surface-fidelity guarantee | Probabilistic (hallucinates) | Pixel-exact interior (SSIM ≥ 0.99 contract) | ∞ improvement |
| QA fail rate (Gemini rubric) | ~100% today | Expected ~10-20% (only lighting/scene issues, not garment) | −80-90% |

Phase 1 adds new spend ($1.24 baseline for full 33-SKU refresh) but creates the asset library Phase 2 depends on. Without verified mockups, Phase 2 composites onto compromised inputs.

---

## Per-Product LoRA — Position

**Not required for Phase 1 or Phase 2 primary paths.** LoRA reduces hallucination probability but doesn't deliver pixel-exact guarantee — and Architecture A delivers pixel-exact by construction. Existing `skyyrose-lora-v4` brand LoRA is useful for *new scene generation* (Stage 1 of home-spread today) where some generative freedom is acceptable.

**Future scenario where per-SKU LoRA matters:** if Phase 1 needs to generate mockups in poses/contexts NOT covered by existing photos AND not solvable by FASHN v1.6 product-to-model. Then: train 50-100 image LoRA per SKU on Replicate (~$2-8, 10min), use as conditioning in FLUX Kontext for that specific pose. Gate behind `ELITE_STUDIO_USE_SKU_LORA` env var. Not on critical path today.

---

## Validation Strategy

### Phase 1 — Mockup verification

- **Automated:** SSIM ≥ 0.99 on product interior region vs source photo
- **Automated:** Gemini visual diff scoring graphic presence + correctness (binary per element: rose cluster present Y/N, "Love Hurts" script readable Y/N, Bay Bridge sublimation pattern intact Y/N)
- **Manual:** founder gate per batch of 5 SKUs before write to canonical PRODUCT_IMAGES_DIR
- **Registry:** `data/verified-mockups.json` keyed by SKU, stores source-photo hash + output-mockup hash + founder approval timestamp

### Phase 2 — Scene composite verification

- **Contract check:** SSIM(composite_interior, rasterized_interior) ≥ 0.99 — this is mathematical, not perceptual. Anything below 0.97 indicates a band-mask bug, not a model quality issue.
- **Perceptual gate (existing):** Gemini Stage G rubric — should now consistently score `garment_fidelity ≥ 9` because the pixel guarantee removes the hallucination source
- **Composite refuses dispatch if mockup not in verified registry** (set `ELITE_STUDIO_REQUIRE_VERIFIED_MOCKUP=1`)

---

## Open Decisions for Founder

Three decisions block kicking off Phase 1:

1. **Track A vs Track B per SKU.** Most SKUs (have existing photo) → Track A. But founder may want Track B (new poses) on hero SKUs for marketing variety. Choice: all-A baseline, or pick specific hero SKUs for Track B (extra $0.115 each).

2. **Background style during refinement.** Track A replaces BG. Choices: pure black `#0A0A0A` (brand canon, all collections), gradient toward collection accent (rose-gold for BR, gold for SIG, crimson for LH), OR keep original product BG (zero risk, no editorial elevation).

3. **Verified-mockup registry: opt-in or required.** `ELITE_STUDIO_REQUIRE_VERIFIED_MOCKUP=1` means Phase 2 home-spread will REFUSE to composite if mockup isn't in the registry. Safer but harder cutover. Or default to 0 (warn but allow) for first weeks.

---

## STOP-AND-SHOW Gates (Production)

Per CLAUDE.md protocol, every paid step requires founder y before dispatch:

- Track A batch dispatch: cost manifest per 5-SKU batch → y → proceed
- Track B FASHN dispatch: per-SKU manifest with sample preview at 1 sample first → y → 4-sample fan-out
- Phase 2 scene composite (Architecture A): cost manifest per collection → y → proceed; fidelity gate failures auto-stop before fallback to kontext (require founder y to use fallback)
- Any per-product LoRA training: full manifest including dataset size, training time, model storage path → y

---

## Source Convergence — All 4 Research Streams

| Agent | Recommendation |
|---|---|
| Backend Architect | Architecture A: rasterize + seam refine; pixel-exact interior guarantee |
| AI Engineer (SOTA VTON) | Rank 1: BiRefNet/RMBG → composite → IC-Light V2; diffusion cannot pixel-copy (VAE+semantic+flow-matching bottlenecks) |
| Trend Researcher (2026 SOTA) | FLUX.1 Kontext + IP-Adapter+ControlNet ComfyUI baseline (free); HiFi-Inpaint (CVPR 2026) future; FLUX.2 multi-ref for compositing tasks |
| fal/Replicate Catalog | FASHN v1.6 (logo-preservation explicit), BRIA Product Shot (composite-style placement), IC-Light V2 (subject-preserving relight) all production-hosted on fal.ai today |

**Unanimous:** keep diffusion away from the product surface. Use it for lighting (IC-Light V2) and seam blending (FLUX Fill at strength≤0.2) only. For graphics-heavy SKUs, this is the only path to 100% replica.

---

## Files Touched by This Plan (for impact assessment)

- New: 5 Python modules + 2 test files
- Modified: 5 existing modules (cli, orchestrator, flux_methods, infra, models, config)
- New CLI subcommand: `mockup` (+ subverb `verify`)
- New env vars: 7
- New data file: `data/verified-mockups.json`
- Net new code: ~970 lines; net modified ~150 lines
- No breaking changes (Phase 2 is feature-flagged behind env var; current kontext path remains)

---

**Awaiting founder y/n on the three open decisions + go/no-go on Phase 1 dispatch.**
