# v2.html Canon Audit — Home Surface
**Brand Guardian · Stage 1c · luxury-mockup-pipeline**
**Date:** 2026-05-25
**Scope:** Home surface primary focus (cover/hero/voice/spread) + full-site sweep for canon ripple
**Target file:** `docs/brand/design-mockups/v2.html`

---

## Violations

| ID | Sev | File:Line | Current State | Canon Source (verbatim) | Required State | Rationale |
|----|-----|-----------|---------------|------------------------|----------------|-----------|
| CV-H-01 | P0 | `v2.html:589` | `forbidden-midnight-1680w.webp` used as home-cover background photo (`<source srcset>`, `<img src>` chain L589-596) | `asset-hierarchy.md` Tier 2 Black Rose entry: "Full-bleed Black Rose hero background — BR-scoped" + "Collection hero marks scope to collection pages. Don't cross-pollinate." | Replace with brand-primary / editorial lifestyle photo (no collection-specific scene). Cover = magazine front; brand, not one collection. | `forbidden-midnight` is a Black Rose Tier 2 asset. Placing it on the brand-primary home cover telegraphs BR as the flagship, displacing all other collections before any user interaction. |
| CV-H-02 | P0 | `v2.html:629,634` | `forbidden-midnight` reused as home-hero background (L629); `alt="Black Rose drop story — Oakland industrial scene"` (L634) confirms slot was scoped as BR editorial, not brand-primary | `asset-hierarchy.md`: same rule as CV-H-01. `feedback_collection_lockup_assets.md` (locked 2026-05-25): "Every collection has a canonical brand-script lockup... scoped to collection pages." Founder feedback: "the hero shouldnt be the same image as the collection" | Replace hero bg with a brand-primary editorial photo (models across collections, or a neutral Oakland-anchored lifestyle scene). Rewrite `alt` to reflect brand scope. | Home hero and home cover sharing the same BR-specific scene creates visual collapse — home, hero, and BR sub-page all look identical. Violates the founder's explicit instruction. |
| CV-H-03 | P0 | `v2.html:649–655` | `br-brand-script.{avif,webp,png}` hero lockup rendered as home-hero centerpiece (`<picture>` inside `.hero__lockup`, L649-655) | `feedback_collection_lockup_assets.md` (locked 2026-05-25): "Black Rose: `br-brand-script.{avif,webp,png}` — `assets/images/hero-overlays/`... collection lockup assets are images, never type-rendered, scoped to their own collection page." `asset-hierarchy.md`: "Tier 2 — Collection hero marks scope to collection pages." | Remove the BR-specific lockup from home-hero. Home hero centerpiece should use the brand-primary monogram (`sr-monogram-rose-gold`, Tier 1) or no lockup at all (tagline-only cover). | BR collection lockup as homepage hero centerpiece misidentifies one collection as the brand identity. Cross-collection visitors land into Black Rose branding before seeing the brand. |
| CV-H-04 | P1 | `v2.html:685,698,709` | Spread tiles 1 (Black Rose), 2 (Love Hurts), 3 (Signature) use collection logo-mark/hero-branding images (`black-rose-logo-hero.webp`, `love-hurts-logo-hero.webp`, `signature-logo-hero.webp`) as tile body images | Founder feedback (verbatim): "each collection card should be a image of the scene i want." `asset-hierarchy.md`: Tier 2 "Collection hero marks scope to collection pages." `collection-stories.md`: each collection has a dedicated hero environment scene (`forbidden-midnight`, `beauty-and-beast`, `luxury-nighttime`) | Tiles 1–3 must use collection scene photos: Black Rose → `forbidden-midnight-*`, Love Hurts → `beauty-and-beast-*`, Signature → `luxury-nighttime-*`. Logo marks belong as overlay lockups over the scene, not as the tile image itself. | Logo marks are identifiers, not scenes. The founder's explicit request is for scene photography as the visual entry point to each collection card. |
| CV-H-05 | P1 | `v2.html:720` | Spread tile 4 (Kids Capsule) uses `skyy-rose-collection-circular-patch.webp` as the tile body image — patch fills the entire tile frame | `feedback_collection_lockup_assets.md` (locked 2026-05-25): "Kids Capsule: `skyy-rose-collection-circular-patch.{avif,webp,jpeg}` — `assets/images/logos/`" — asset is canonical Kids lockup, not a scene photo. Founder feedback: "each collection card should be a image of the scene i want." | Tile 4 requires a Kids Capsule scene photo (does not yet exist — see asset gap below). The circular patch should be rendered as a lockup overlay on top of a scene, mirroring the other three tiles' structure. | Right asset, wrong slot. The patch is the Kids lockup (Tier 2 equivalent), not a scene photograph. Filling the tile frame with it produces a logo-as-hero rather than a scene-as-hero. |

**Violation count by severity: P0 = 3, P1 = 2, P2 = 0**

---

## Full-Site Canon Sweep (Beyond Home Surface)

No additional violations detected in non-home sections of v2.html from the scan:

- **Header / navbar:** No brand mark misuse observed in header markup.
- **BR sub-page (L734+):** `forbidden-midnight` appears again on the Black Rose collection sub-page — this is **correct**. BR-scoped scene on BR page = canon-compliant. Not a violation.
- **Voice section (L668-677):** Quote "Named after a daughter. Built by a father." attributed to "Corey Foster · The Town" — verified as brand-wide canon (not collection-specific copy). No violation.
- **Footer / founder signature:** Not visible in scanned range; no violation detected.

---

## Per-Tile Asset Attribution Table

| Tile | Current Asset | Canon-Correct Asset | Source Rule |
|------|--------------|---------------------|-------------|
| Tile 1 — Black Rose (L685) | `assets/branding/black-rose-logo-hero.webp` | `assets/branding/hero/forbidden-midnight-{480,768,1280,1680}w.webp` | `collection-stories.md` BR hero env; founder: "image of the scene" |
| Tile 2 — Love Hurts (L698) | `assets/branding/love-hurts-logo-hero.webp` | `assets/branding/hero/beauty-and-beast-{480,768,1280,1680}w.webp` | `collection-stories.md` LH hero env; founder: "image of the scene" |
| Tile 3 — Signature (L709) | `assets/branding/signature-logo-hero.webp` | `assets/branding/hero/luxury-nighttime-{480,768,1280,1680}w.webp` | `collection-stories.md` SIG hero env; founder: "image of the scene" |
| Tile 4 — Kids Capsule (L720) | `assets/images/logos/skyy-rose-collection-circular-patch.webp` | **[ASSET GAP]** Kids Capsule hero scene photo does not exist yet. Interim: brand-primary lifestyle photo + circular-patch as overlay lockup | `feedback_collection_lockup_assets.md`: patch = lockup, not scene; `collection-stories.md`: Kids has no dedicated hero env |

---

## Kids Capsule Patch Reconciliation Verdict

**Verdict: Canon asset in wrong slot — not an asset error, an architectural error.**

The `skyy-rose-collection-circular-patch` is the legitimate canonical Kids Capsule lockup per `feedback_collection_lockup_assets.md` (locked 2026-05-25). It is the correct identifier for the Kids Capsule collection.

The violation is structural: the patch fills the entire tile frame as if it were a scene photograph. The correct pattern (matching the other three tiles) is:

1. **Background layer:** collection scene photo (does not exist for Kids Capsule)
2. **Overlay layer:** canonical lockup (`skyy-rose-collection-circular-patch`) at scaled position

**Asset gap:** Kids Capsule has no hero environment equivalent to `forbidden-midnight`, `beauty-and-beast`, or `luxury-nighttime`. Per `collection-stories.md`: "Kids Capsule: no dedicated hero environment (inherits brand primary)."

**Interim fix path:** Use a brand-primary lifestyle photo as the Kids tile background + render the circular patch as a centered overlay at ~40% tile width. This preserves both the "scene photo" intent and the canonical lockup presentation.

**Long-term fix path:** Commission a Kids Capsule hero environment scene and add it to `assets/branding/hero/` following the existing naming pattern (`kids-capsule-{480,768,1280,1680}w.webp`).

---

## ROI Upgrade Proposal

**Selected:** Per-collection palette inheritance via `data-collection` attribute + CSS custom property cascade

**One-line pitch:** Add `data-collection="[slug]"` to each spread tile wrapper — the existing `design-tokens.css` custom property cascade activates instantly, giving each tile its native accent color, background, and font token stack with zero new CSS.

**Implementation:**

```html
<!-- Before (L682) -->
<article class="spread__tile spread__tile--lg">

<!-- After -->
<article class="spread__tile spread__tile--lg" data-collection="black-rose">
```

Repeat for tiles 2 (`data-collection="love-hurts"`), 3 (`data-collection="signature"`), 4 (`data-collection="kids-capsule"`).

**Why this is highest ROI:**

- `design-tokens.css` already contains all four `[data-collection]` selector blocks (confirmed from WordPress theme — ported tokens exist). Zero new CSS required.
- Each tile's accent color, text color, and font-display token cascade automatically to all descendant `.spread__tile-*` elements.
- Black Rose tiles show `--skyyrose-accent: #C0C0C0` (silver). Love Hurts shows `#DC143C` (crimson). Signature shows `#D4AF37` (gold). Kids Capsule shows `#B76E79` (rose gold).
- Distinguishes the four collections visually at the spread level — the brand hierarchy becomes tactile, not just typographic.
- Single-commit scope: 4 HTML attribute additions, no new files.
- `prefers-reduced-motion` safe: CSS custom properties are static, no animation.
- Browser fallback: `:root` default tokens cascade if `data-collection` attribute is absent.

**Constraints check:** self-contained ✓ · production-grade ✓ · prefers-reduced-motion safe ✓ · browser fallback ✓ · single-commit scope ✓

---

**Brand Guardian · Audit complete**
**Canon docs consulted:** `docs/brand/visual-references.md` · `docs/brand/collection-stories.md` · `docs/brand/asset-hierarchy.md` · `docs/CLAUDE.md` · `memory/feedback_brand_visual_references.md` · `memory/feedback_collection_canon_attribution.md` · `memory/feedback_collection_lockup_assets.md`
