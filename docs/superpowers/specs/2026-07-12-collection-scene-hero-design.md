# Collection Scene Hero — Design Spec

- **Date:** 2026-07-12
- **Status:** Design approved (brainstorm) → pending written-spec review → writing-plans
- **Author:** DevSkyy engineering agent (with founder Corey Foster)
- **Scope:** Upgrade the shared collection-page hero into a cinematic, palette-driven **scene hero** across all four collections. Black Rose leads with the founder's "Oakland After Dark" render.

---

## 1. Problem / Goal

The founder generated a cinematic render — a night penthouse over the real Bay Bridge ("Oakland After Dark") — and wants it implemented as a **cinematic hero / entry**: a big atmospheric scene at the top of a collection page, then scroll into the normal product grid to shop.

A first prototype (a horizontal-scroll "walk the pieces" band, `docs/design-mockups/black-rose-preorder-horizontal.html`) was rejected — it fought the theme's grain with a bespoke full-viewport takeover. The founder chose a **bespoke scene hero**, then widened scope to **all collections**.

**Goal:** one reusable, per-collection **scene-hero** component that replaces the current `col-hero`, applied to all four collections, each tuned by its own palette / lockup / copy / mood, with Black Rose carrying the new render. Ships now on existing verified backdrops; bespoke per-collection renders swap in later.

---

## 2. Approach

Upgrade — do **not** fork. The shared hero in `template-parts/collection/page.php` already serves all four collections data-driven (backdrop via `skyyrose_sot_hero($slug)`, lockup via `skyyrose_sot_lockup($slug)`, copy via `skyyrose_get_collection_content($slug)`). We:

1. **Extract** the hero markup out of `page.php` into an isolated partial `template-parts/collection/scene-hero.php` (one file, all collections, data-driven). `page.php` calls it in place of the current inline `<section class="col-hero">`.
2. **Add a living-night scene layer** (starfield, night-cycle grade, parallax, faint bridge-light shimmer) behind the existing content, driven by a small JS engine + palette CSS vars.
3. **Route Black Rose's backdrop** to the Oakland After Dark render via the SOT (`identity.json` → regenerate `sot.json`). Love Hurts + Signature keep their current verified backdrops; the treatment adapts by palette.
4. **Kids Capsule** gets a distinct **teaser-video** variant (bright/playful, launch-mode, no shop CTA) — not the living-night image treatment.

Rationale: least code that honors "cinematic hero," keeps the unified layout unified, and stays SOT-compliant (one asset swap through `identity.json`, never hand-editing generated `sot.json`).

**Rejected alternatives:** (A) asset-swap only — too small for "bespoke"; (C-per-collection) four separate bespoke heroes — more code, drifts from the unified layout. The chosen path is one upgraded component × four data sets.

---

## 3. Architecture & Integration

```
template-collection-<slug>.php
  → get_template_part('template-parts/collection/page', …, ['slug'=>…])
      → page.php
          → [NEW] get_template_part('template-parts/collection/scene-hero', …, ['slug'=>…, 'c'=>$c, …])
          → (unchanged) #shop product grid, cross-nav, #experience, story, features, footer
```

- **`scene-hero.php`** (new, isolated): renders the scene. Inputs: `slug`, resolved `$c` content, `skyyrose_sot_hero($slug)`, `skyyrose_sot_lockup($slug)`, palette (see §4). One clear job: the hero. Testable in isolation; consumers depend only on the same args `page.php` already computes.
- **`page.php`**: loses ~50 lines of inline hero markup, gains one `get_template_part`. The kids-capsule special-case note already living here moves into `scene-hero.php`.
- **No new template registration.** Collection templates already resolve to the collection CSS/JS bundle; we extend that bundle, not add a slug.

**Data flow (per collection):** slug → `$c` (copy, lockup fallback), `skyyrose_sot_hero` (backdrop), `skyyrose_sot_lockup` (canonical lockup), palette accent (from `data/collections/<slug>/identity.json`). The scene-hero emits palette as CSS custom properties (`--scene-accent`, `--scene-grade-*`) + a `data-scene-mood` attribute (`night` | `video`) that the JS engine reads.

---

## 4. The Scene-Hero Component

**Layers (back → front):**
1. **Backdrop** — collection `hero_backdrop` (BR = render), full-bleed `object-fit:cover`, responsive `srcset`, slow ken-burns + scroll parallax. `fetchpriority=high` (LCP).
2. **Living night** (`data-scene-mood="night"`, BR/LH/SIG): starfield `<canvas>` over the sky band; night-cycle grade overlay tinted by palette (BR cold silver/blue, LH crimson, SIG gold), ~7s cycle; faint bridge/city light shimmer (a drifting specular sweep — no pixel-precise path, forgiving of any backdrop); vignette; legibility scrim tuned so the lockup stays crisp.
3. **Content** (unchanged semantics, reused): eyebrow (`hero_badge`), **canonical lockup image** (`skyyrose_sot_lockup` — hero title is always a lockup image, never type-rendered), tagline + subtitle, CTA group (**Shop the Collection → `#shop`**, secondary **View 3D Experience → `#experience`**), scroll hint. Screen-reader `<h1>` carries the collection name.

**Per-collection tuning:**

| Collection | Mood | Backdrop | Accent grade |
|---|---|---|---|
| black-rose | night | Oakland After Dark render (NEW) | silver `#C0C0C0` / cold blue |
| love-hurts | night | **`love-hurts-beast-room-*` (NEW render, §5a)** | crimson `#DC143C` / `#9B0F2E` |
<!-- LH voice: told from the Beast's perspective (founder canon 2026-07-12). See §10.4. -->
| signature | night | `luxury-nighttime-*` (existing) | gold `#D4AF37` / rose-gold `#B76E79` |
| kids-capsule | video | teaser video (TBD, §7) | rose-gold `#B76E79`; **no shop CTA**, launch-mode copy |

**JS engine** (`assets/js/collection-scene-hero.js`): reads `data-scene-mood`. `night` → starfield + night-cycle + parallax. `video` → mounts the teaser `<video>` (autoplay/muted/loop/playsinline) with the poster as fallback; no canvas. `prefers-reduced-motion` → static backdrop/poster only, no cycle/parallax/starfield/video-autoplay; all content fully visible. Reuse the proven engine from the rejected prototype (starfield, night-cycle STATES, parallax) — port, don't reinvent.

---

## 5. Black Rose backdrop — the render

- **Source:** the founder's Playground render (`~/Downloads/OpenAI Playground 2026-07-11 at 22.49.28.png`, 1536×1024).
- **Asset set:** `assets/scenes/black-rose/oakland-after-dark-{768,1280,1536}w.webp` (source res caps ≈1536w — no upscale) + a preload poster. Follows the existing `hero_bg_base` + width-suffix `srcset` convention.
- **SOT wiring:** set `imagery.hero_backdrop` in `data/collections/black-rose/identity.json` to the new scene → regenerate `sot.json` via the collection SOT build (`build-collection-sot.py`). Never hand-edit `sot.json`.
- **Full render (not the horizon crop):** as a mood hero the staged jerseys read as lifestyle context; the fidelity gate is satisfied by §6 (decorative, no SKU claim). Keep `forbidden-midnight` available as an alternate/fallback, not deleted.

---

## 5a. Love Hurts backdrop — the renders

Founder-provided 2026-07-12 (two renders, source 1672×941):

- **Primary hero (desktop):** `LoveHurts-pre-order.png` → the Beast's enchanted chamber (chandelier, stained-glass roses, fireplace, the dying rose under glass, the **FANNIE** waist-bag = lh-005 staged, sunset balcony). Asset: `assets/branding/hero/love-hurts-beast-room-{480,768,1280,1600}w.webp` + full-res source `assets/scenes/love-hurts/love-hurts-beast-room.webp`.
- **Secondary (portrait / mobile art-direction + rose motif):** the enchanted-rose close-up (heart-cloud sky, falling petals, candle). Asset: `love-hurts-enchanted-rose-{480,768,1280,1600}w.webp`. Served via an art-directed `<picture>` source on narrow viewports (rose stays centered) and reusable as the LH rose motif.
- **SOT wiring:** set `imagery.hero_backdrop` in `data/collections/love-hurts/identity.json` → `branding/hero/love-hurts-beast-room` → regenerate `sot.json`. Keep `beauty-and-beast-*` as alternate/fallback, not deleted.
- **Fidelity:** the FANNIE bag is **lifestyle staging of lh-005**, not a product card; the shoppable lh-005 image stays SOT-resolved in the grid. The render sells mood, not the SKU.

## 6. Fidelity / SOT

- Scene backdrops (incl. the render) are **decorative atmosphere**, `aria-hidden`, and represent **no SKU**. Staged garments in the render are lifestyle context, not product cards.
- **Every shoppable image stays SOT-resolved** in the `#shop` grid (`skyyrose.core.sot_images` / theme resolver) — unchanged by this work.
- No AI-approximated garment ever stands in for a catalog product. The product-image fidelity gate holds because products are never sourced from the hero.

---

## 7. Assets & Dependencies

- **Ready now:** BR render + **LH bespoke renders (provided 2026-07-12, WebP sets generated, §5a)**; SIG uses existing `luxury-nighttime` until a bespoke render arrives.
- **Dependency — Kids Capsule teaser video:** no KC video exists (`assets/video/` has only `preorder-hero.*`). KC scene hero is **blocked** on a teaser video asset (founder-provided or a separately-gated generation). Until then, KC keeps its current launch-mode hero; the `video` branch ships behind an asset-present check so KC never renders an empty `<video>`. (Ref: recent KC teaser reveal work, bug-225.)
- **Future (out of scope):** bespoke Oakland-caliber renders for LH/SIG (each a founder-gated paid asset), swapped via the same SOT `hero_backdrop` path with zero code change.

---

## 8. Accessibility, Performance, Build

- **A11y:** decorative layers `aria-hidden`; real `<h1>` screen-reader text; CTAs are real `<a>` links (keyboard); focus-visible states; `prefers-reduced-motion` fully honored.
- **Perf:** backdrop `fetchpriority=high` + responsive `srcset`; starfield capped by area; single rAF loop; video lazy + `preload=metadata`; no layout shift (fixed hero height, `width/height` on images).
- **Build:** new `assets/css/collection-scene-hero.css` + `assets/js/collection-scene-hero.js`; enqueue on all collection slugs (extend the existing collection bundle in `inc/enqueue.php` — verify the collection-slug mapping). **Rebuild `.min`** (`npm run build` from `wordpress-theme/`) — production serves `.min`; verify source **and** `.min`.
- **Deploy:** committing the render asset + code is local. **Deploy to skyyrose.co is STOP-AND-SHOW** (theme sweep clean + manifest shown first). Post-deploy: cache-busted `curl` + Playwright eyes-on (mobile + desktop) per verification matrix.

---

## 9. Success Criteria / Verification

- [ ] All four collection pages render the scene hero; BR shows the Oakland After Dark render; LH/SIG show their backdrops with the living-night treatment; KC shows the teaser-video variant (or current hero if video absent) with **no shop CTA**.
- [ ] Hero content (lockup, eyebrow, tagline, CTAs) uses **verified canon strings** per §3–§4; lockup is the canonical image.
- [ ] `#shop` grid, cross-nav, `#experience`, story, footer unchanged and functional.
- [ ] `prefers-reduced-motion`: static, no motion, content fully visible.
- [ ] `.min` rebuilt; source + min verified; PHP lints clean (`npm run lint:php`).
- [ ] SOT: no hardcoded product image literals introduced; hero backdrops resolve via `skyyrose_sot_hero`.
- [ ] Playwright eyes-on (mobile + desktop) on each collection page after deploy.

---

## 10. Open Questions

1. **KC teaser video** — source? (founder-provided file, or a separately-gated generation). Blocks only the KC variant; BR/LH/SIG ship independently.
2. **`forbidden-midnight`** — keep as BR poster/reduced-motion fallback, or fully retire? (Default: keep, don't delete.)
3. **Motion intensity** — confirm the night-cycle + starfield amount at first implementation review (easy to dial down).
4. **Love Hurts voice (founder canon 2026-07-12):** the LH hero is **told from the Beast's perspective** — first-person, the Beast narrating his own story. The current `hero_tagline` "They called me Beast. They were right." already narrates from the Beast and holds as the display line; update `love-hurts` `hero_tagline` (`inc/collection-content.php`) + `docs/brand/collection-stories.md` only if the founder supplies a new exact Beast-POV string. This canon lens applies to LH copy site-wide, not just the hero.
