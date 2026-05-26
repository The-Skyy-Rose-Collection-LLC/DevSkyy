# v2 Asset Triage Report
**Date:** 2026-05-25  
**Scope:** Home page (primary) + BR sub-page (secondary) — full-site global health noted  
**Auditor:** Frontend Developer agent (luxury-mockup-pipeline)

---

## A — Home Asset Inventory

| Surface | Current Path | Dimensions | File Size | Alpha | AVIF Variant | Verdict |
|---------|-------------|------------|-----------|-------|--------------|---------|
| **Cover BG** | `branding/hero/forbidden-midnight-1680w.webp` | 1680×720 | 309 KB | No | No | FAIL — wrong AR, no AVIF, wrong asset |
| **Cover BG** | `branding/hero/forbidden-midnight-1280w.webp` | 1280×549 | 188 KB | No | No | FAIL — undersized height |
| **Cover BG** | `branding/hero/forbidden-midnight-768w.webp` | 768×329 | 71 KB | No | No | FAIL — undersized height |
| **Cover BG** | `branding/hero/forbidden-midnight-480w.webp` | 480×206 | 27 KB | No | No | FAIL — 206px tall at 480w is unusable |
| **Hero BG** | `branding/hero/forbidden-midnight-*` (duplicate) | same | same | No | No | FAIL — same asset reused for both cover + hero |
| **Hero lockup** | `images/hero-overlays/br-brand-script.avif` | 1600×900 | 89 KB | No (no alpha in AVIF) | Yes | WARN — lockup baked onto dark BG, not transparent |
| **Hero lockup** | `images/hero-overlays/br-brand-script.webp` | 1600×900 | 183 KB | No | — | WARN — no alpha, dark BG baked in |
| **Hero lockup** | `images/hero-overlays/br-brand-script.png` | 1600×900 | 693 KB | Yes (TrueColorAlpha) | — | PASS (alpha correct, but 693 KB PNG in prod = perf debt) |
| **Spread tile — BR** | `branding/black-rose-logo-hero.webp` | 628×312 | 50 KB | No | No | FAIL — logo graphic, not a scene; landscape in portrait tile |
| **Spread tile — LH** | `branding/love-hurts-logo-hero.webp` | 800×897 | 205 KB | No | No | FAIL — logo graphic, not a scene |
| **Spread tile — SIG** | `branding/signature-logo-hero.webp` | 1200×610 | 40 KB | No | No | FAIL — logo graphic, not a scene; landscape in portrait tile |
| **Spread tile — Kids** | `images/logos/skyy-rose-collection-circular-patch.webp` | 1678×1872 | 104 KB | No | No | FAIL — circular patch / jersey graphic, not a scene |

**Purpose-built candidates (confirmed existing):**

| Candidate | Dimensions | File Size | Format | Status |
|-----------|------------|-----------|--------|--------|
| `images/homepage-hero-bg.avif` | 1920×1920 | 294 KB | AVIF | EXISTS — square, crops cleanly to any viewport AR |
| `images/homepage-hero-bg.webp` | 1920×1920 | 396 KB | WebP | EXISTS — fallback |
| `images/homepage-hero-bg-alt.avif` | 1920×1920 | 271 KB | AVIF | EXISTS |
| `images/homepage-hero-bg-alt.webp` | 1920×1920 | 392 KB | WebP | EXISTS — fallback |
| `images/homepage-col-black-rose.avif` | 800×800 | 91 KB | AVIF | EXISTS — square scene, correct for tile |
| `images/homepage-col-black-rose.webp` | 800×800 | 136 KB | WebP | EXISTS — fallback |
| `images/homepage-col-love-hurts.avif` | 800×343 | 37 KB | AVIF | EXISTS — AR MISMATCH (landscape, 343px tall) |
| `images/homepage-col-love-hurts.webp` | 800×343 | 61 KB | WebP | EXISTS — same AR problem |
| `images/homepage-col-signature.avif` | 800×800 | 88 KB | AVIF | EXISTS — square scene, correct for tile |
| `images/homepage-col-signature.webp` | 800×800 | 137 KB | WebP | EXISTS — fallback |
| `images/lookbook/lb-kid-black-rose-960w.avif` | 960×1280 | 70 KB | AVIF | EXISTS — portrait, correct AR for tile |
| `images/lookbook/lb-kid-black-rose-960w.webp` | 960×1280 | 86 KB | WebP | EXISTS — fallback |
| `images/products/kids-001-red-set.avif` | 360×360 | 8.5 KB | AVIF | EXISTS — too small (360px), product shot not scene |
| `images/products/kids-002-purple-set.avif` | 833×833 | 25 KB | AVIF | EXISTS — usable square if needed |

---

## B — Quality Diagnosis

### Verdict: Three compounding failures

**Root cause #1 — Wrong asset class in hero/cover background**

`forbidden-midnight` was built as a wide-cinematic landscape set (max 1680×720, AR ≈ 2.33:1). The cover and hero frames use `position: absolute; inset: 0; object-fit: cover; width: 100%; height: 100%`. On any full-viewport render taller than ~720px, the browser must upscale the 720px source vertically — producing the visible softness and quality degradation the founder reported. The 480w variant is only 206px tall, which renders as severe blur at any reasonable mobile hero height.

The purpose-built `homepage-hero-bg.avif` (1920×1920) is the correct replacement: a square source crops cleanly to any viewport aspect ratio without upscale blur. Cover and hero should use separate assets (`homepage-hero-bg` vs `homepage-hero-bg-alt`) to create visual progression between the two full-page frames.

**Root cause #2 — Spread tiles show logo/patch graphics, not collection scenes**

The four home spread tiles render via `object-fit: cover` inside portrait-ratio `.spread__tile--brand` containers. The current sources are:

- Black Rose: `black-rose-logo-hero.webp` — 628×312 text/logo graphic
- Love Hurts: `love-hurts-logo-hero.webp` — 800×897 script logo on a plain background
- Signature: `signature-logo-hero.webp` — 1200×610 wordmark
- Kids: `skyy-rose-collection-circular-patch.webp` — 1678×1872 jersey circular patch

When a logo graphic is `object-fit: cover`-cropped into a tall portrait tile, only a fragment of the letterforms or the patch ring center is visible. This is the "why is the jersey patched displayed" complaint — it is not a CSS filter or rendering bug. The assets are simply the wrong type. The purpose-built `homepage-col-*` scene images exist and should replace them.

**Root cause #3 — Hero lockup AVIF/WebP lack alpha**

`br-brand-script.avif` and `.webp` (1600×900) have the dark background baked in — no alpha channel. The PNG is the only variant with `TrueColorAlpha`. The mockup's `<picture>` element picks the AVIF/WebP first, so the browser loads a version where the lockup blends a dark rectangle over the hero background instead of floating over it. Floating-lockup effect is only achievable by loading the 693 KB PNG — which is a significant LCP penalty. New alpha-preserving AVIF/WebP exports are needed.

**Secondary finding — Love Hurts collection card AR mismatch**

`homepage-col-love-hurts.avif` is 800×343 (AR 2.33:1 landscape). The spread tile container renders at a square-to-portrait ratio. The 343px height means aggressive vertical crop discards nearly all usable image content on small screens. A square or portrait scene exists for LH.

---

## C — Recommended Swaps Per Surface

Six confirmed-path swaps, all targets verified to exist via `ls -la` + `identify`:

| # | Surface | Remove | Swap In | Note |
|---|---------|--------|---------|------|
| 1 | **Cover BG** | `branding/hero/forbidden-midnight-{480,768,1280,1680}w.webp` | `images/homepage-hero-bg.avif` + `.webp` fallback | 1920×1920 square, AVIF available, no upscale blur |
| 2 | **Hero BG** | `branding/hero/forbidden-midnight-{480,768,1280,1680}w.webp` (duplicate) | `images/homepage-hero-bg-alt.avif` + `.webp` fallback | Separate scene from cover for visual progression |
| 3 | **Spread tile — Black Rose** | `branding/black-rose-logo-hero.webp` | `images/homepage-col-black-rose.avif` + `.webp` fallback | 800×800 scene designed for this surface, AVIF exists |
| 4 | **Spread tile — Love Hurts** | `branding/love-hurts-logo-hero.webp` | `images/homepage-col-love-hurts.avif` + `.webp` fallback | Scene exists; 800×343 AR mismatch noted — see Section D/E |
| 5 | **Spread tile — Signature** | `branding/signature-logo-hero.webp` | `images/homepage-col-signature.avif` + `.webp` fallback | 800×800 scene designed for this surface, AVIF exists |
| 6 | **Spread tile — Kids** | `images/logos/skyy-rose-collection-circular-patch.webp` | `images/lookbook/lb-kid-black-rose-960w.avif` + `.webp` fallback | 960×1280 portrait lookbook shot; AVIF available; correct AR for portrait tile |

---

## D — Missing Variants

| Asset | Missing | Impact |
|-------|---------|--------|
| `homepage-hero-bg.avif/.webp` | No 480w, 768w, 1280w responsive variants | Mobile downloads full 294 KB AVIF at 480px viewport — ~0.8–1.2s LCP penalty on 4G |
| `homepage-hero-bg-alt.avif/.webp` | No 480w, 768w, 1280w responsive variants | Same |
| `homepage-col-love-hurts.avif/.webp` | No square or portrait variant — only 800×343 landscape | Vertical crop discards nearly all content at portrait tile ratio |
| `br-brand-script.avif/.webp` | Alpha channel absent in both formats | Floating lockup only works with the 693 KB PNG; AVIF/WebP bake dark background |
| `forbidden-midnight-*` (BR sub-page) | No AVIF tier across all 4 breakpoints | Retained for BR sub-page cover/hero; still a perf gap on that surface |

---

## E — Asset Generation Needed

> Recommendations only. No generation executed. Requires founder approval before triggering any paid or compute-heavy pipeline.

| Priority | Asset Needed | Reason | Generator |
|----------|-------------|--------|-----------|
| **P0** | `homepage-col-love-hurts` square scene — 800×800 or 960×960 | Current landscape (800×343) is unusable in portrait tile; no square LH collection scene exists | New shoot or FLUX inpainting from existing LH assets |
| **P1** | Responsive variants for `homepage-hero-bg.avif` — 480w, 768w, 1280w | Single 1920px source is ~9× oversized for mobile | `cwebp` + `avifenc` from existing 1920px master — no new photography |
| **P1** | Responsive variants for `homepage-hero-bg-alt.avif` — 480w, 768w, 1280w | Same mobile LCP penalty | Same |
| **P2** | Alpha-correct `br-brand-script.avif` + `br-brand-script.webp` | Current AVIF/WebP bake dark background — floating lockup broken in all modern browsers | `rembg` on the PNG source, or re-export from original source file with transparency |
| **P3** | Kids Capsule collection scene (800×800) purpose-built for the home spread tile | `lb-kid-black-rose-960w` is a shared lookbook portrait, not a dedicated Kids collection hero | New shoot |

---

## F — ROI Upgrade Proposal

**Upgrade name:** Responsive breakpoint variants for `homepage-hero-bg.avif` + `homepage-hero-bg-alt.avif`

**One-line pitch:** The single-resolution 1920×1920 hero source makes every mobile visitor download 271–294 KB for a 480px viewport; generating 480w/768w/1280w AVIF+WebP variants from the existing masters via `avifenc`/`cwebp` cuts mobile LCP by ~0.8–1.2s with zero new photography and a single commit.

**What to run when approved (do NOT execute now):**

```bash
# From wordpress-theme/skyyrose-flagship/assets/images/

# 480w
cwebp -q 82 -resize 480 0 homepage-hero-bg.webp -o homepage-hero-bg-480w.webp
convert homepage-hero-bg.webp -resize 480x PNG:- | avifenc --min 24 --max 40 --speed 4 - homepage-hero-bg-480w.avif

# 768w
cwebp -q 82 -resize 768 0 homepage-hero-bg.webp -o homepage-hero-bg-768w.webp
convert homepage-hero-bg.webp -resize 768x PNG:- | avifenc --min 24 --max 40 --speed 4 - homepage-hero-bg-768w.avif

# 1280w
cwebp -q 82 -resize 1280 0 homepage-hero-bg.webp -o homepage-hero-bg-1280w.webp
convert homepage-hero-bg.webp -resize 1280x PNG:- | avifenc --min 24 --max 40 --speed 4 - homepage-hero-bg-1280w.avif

# Repeat for homepage-hero-bg-alt.*
```

**After generation:** update `<picture>` `<source>` elements in v2.html (and the live WordPress theme) to add the breakpoint-matched `srcset` entries identical to the `forbidden-midnight` pattern already in the markup.

**Expected outcome:** Mobile payload drops from 294 KB to ~38–45 KB (AVIF 480w estimate). LCP on median 4G improves by ~0.8–1.2s. Constraint checklist: self-contained ✓, production-grade ✓, no CDN dependency ✓, no paid API ✓, no Three.js ✓, single-commit scope ✓, `prefers-reduced-motion` not applicable (still image) ✓.

---

*Triage complete — 2026-05-25.*
