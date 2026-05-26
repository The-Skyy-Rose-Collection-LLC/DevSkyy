# v2 Amplitude Audit — SkyyRose Homepage Mockup

**Auditor**: ArchitectUX (luxury-mockup-pipeline, refine mode)
**Target**: `docs/brand/design-mockups/v2.html`
**Date**: 2026-05-25
**Constraint flags**: no_three_js · no_cdn_dependencies · no_modify_target

---

## A — Live Homepage vs Mockup: Amplitude Gaps

Elements present in `front-page.php` + `homepage-v2.css/js` that are **absent from the 4-frame mockup**:

| # | Element | Live Source | Mockup Status |
|---|---------|-------------|---------------|
| 1 | **Press strip** | `front-page.php:42–52` — 5 press features (Maxim, CEO Weekly, SF Post, Best of Best Review, The Blox) | Missing entirely |
| 2 | **Marquee ticker** | `front-page.php:55–65` — 8 scrolling labels (Black Rose, Love Hurts, Signature, Oakland Made, Gender Neutral, Limited Edition, Luxury Streetwear, Built Different) | Missing entirely |
| 3 | **Founder story block** | `front-page.php:68–72` — `homepage-story-founder.webp` + editorial copy | Missing entirely |
| 4 | **Lookbook strip** | `front-page.php:75–79` — 5 lookbook images (`lb-black-rose-football`, `lb-black-rose-hockey`, `lb-love-hurts-varsity`, `lb-rose-hoodie-beanie`, `lb-kid-black-rose`, 480w+960w avif/webp) | Missing entirely |
| 5 | **Mobile parallax** | `homepage-v2.css` — `.parallax` + `data-parallax-speed` system disabled via `@media (prefers-reduced-motion)` override that fires too broadly on iOS | Present in code, broken on mobile — hero reads flat |
| 6 | **Vignette depth system** | `homepage-v2.css` — radial gradient vignette framing hero content | Film grain present (`grain-overlay` canvas, opacity 0.035) but no bottom/corner vignette; hero content has no depth separation from BG |

---

## B — The Five Amplitude Patterns: What v2 Is Missing

Mapped from `docs/brand/visual-references.md`:

| Reference | Their Signature Move | v2 Gap |
|-----------|---------------------|--------|
| **Kith** | Monogram-led editorial; product photography at cinematic depth-of-field | Mockup hero uses brand-script lockup with no environmental depth. No DOF in any tile. |
| **Oaklandish** | Civic pride copy integrated as design element; city-grid typography | No Oakland/origin text woven into layout. "Luxury Grows from Concrete." tagline exists but floats without typographic architecture. |
| **Culture Kings** | Drop density — multiple product stories packed into one scroll; energy through rhythm | 4-tile spread uses logos on charcoal. No product energy. Empty grid feels like a brand deck, not a drop. |
| **Fear of God** | Cinematic full-bleed photography; models at scale; silence as design tool | Hero image is 800×600 compressed PNG recycled 4× across sections. No cinematic silence — the recycled asset kills the mood. |
| **Palm Angels** | Sport heritage close-up; embroidery and patch detail as hero moments | Patches are rendered as floating 64×64 icons (`.hero__patches`, v2.html:469–481) — the opposite of close-up hero treatment. Either go macro or remove. |

---

## C — Image Quality: Root-Cause Analysis

**Finding**: All full-bleed image sections in v2 share a single recycled asset.

### Root Cause 1 — Single Asset Used 4×
`forbidden-midnight-1680w.webp` appears as background at:
- Line 589: cover section photo
- Line 629: homepage hero `background-image`
- Line 734: Black Rose sub-page cover photo
- Line 774: Black Rose hero background

**Effect**: Every "distinct" section looks identical. Section hierarchy collapses.

### Root Cause 2 — Wrong Brand Lockup on Homepage Hero
Lines 649–656 load `hero-overlays/br-brand-script.*` (the Black Rose collection typographic overlay) as the homepage hero lockup. This makes the homepage hero visually indistinguishable from the BR collection page. The correct homepage asset is `branding/sr-primary-hero.webp` or `branding/sr-monogram-clouds-wide.webp`.

### Root Cause 3 — Collection Cards Show Logos, Not Scenes
`.spread__tile--brand` CSS (v2.html:425–433) hardcodes:
```css
object-fit: contain;
padding: var(--space-8);
background: var(--charcoal);
opacity: 1;
```
All 4 tiles use this class with logo files (`black-rose-logo-hero.webp`, `love-hurts-logo-hero.webp`, `signature-logo-hero.webp`, `skyy-rose-collection-circular-patch.webp`). The result is a logo showcase, not an editorial collection grid.

### Root Cause 4 — Scene Assets Exist but Are Unreferenced
The following per-collection scene images are deployed to the theme but are **never referenced in v2.html**:
- `assets/images/homepage-col-black-rose.{avif,webp}`
- `assets/images/homepage-col-love-hurts.{avif,webp}`
- `assets/images/homepage-col-signature.{avif,webp}`
- `assets/images/immersive/scene-love-hurts-cathedral.{avif,webp}`

The fix is a CSS class swap and `<img>` src replacement — no new assets required.

---

## D — Top 8 Amplitude Additions (Ranked T1–T3)

### T1 — Must Ship (blocking amplitude)

| # | Addition | Why | Files to Touch |
|---|----------|-----|----------------|
| D1 | **Replace collection card images with scene assets** | Single highest-impact fix. Swap `object-fit: contain` + logo src → `object-fit: cover` + `homepage-col-*.avif`. Grid goes from brand deck → editorial drop. | v2.html:683–728, CSS `.spread__tile--brand` |
| D2 | **Grid: `repeat(4, 1fr)` equal columns** | Founder explicit: "4 evenly aligned sections." Remove `1.4fr 1fr 1fr` + `grid-row: 1/3` spanning. Every collection equal weight. | v2.html:404, 424 |
| D3 | **Homepage hero: swap lockup to SR primary** | Replace `br-brand-script.*` with `branding/sr-primary-hero.webp`. Homepage must not look like the BR page. | v2.html:649–656 |
| D4 | **Remove `.hero__patches` block** | Lines 469–481: 4 floating 64×64 patch icons in the BR hero frame. Remove or defer to a product detail context. Founder called this out directly. | v2.html:469–481 |

### T2 — High-impact momentum adds

| # | Addition | Why | Files to Touch |
|---|----------|-----|----------------|
| D5 | **Add press strip** | Social proof above the fold. Maxim + CEO Weekly + SF Post signal legitimacy instantly. Mirrors live `front-page.php:42–52`. | New section, CSS strip pattern |
| D6 | **Add marquee ticker** | Culture Kings DNA — drop energy, rhythm. 8 labels cycling. `font-family: 'Bebas Neue'`, `letter-spacing: 0.15em`. Mirrors live `front-page.php:55–65`. | New section |
| D7 | **Cover section: unique hero image** | Cover (F01) and Hero (F02) both use `forbidden-midnight-1680w.webp`. Cover needs its own full-bleed editorial image — one of the lookbook frames or `sr-monogram-clouds-wide.webp` as environmental BG. | v2.html:589 |

### T3 — Depth and atmosphere

| # | Addition | Why | Files to Touch |
|---|----------|-----|----------------|
| D8 | **Vignette depth system on hero** | Radial gradient `rgba(0,0,0,0.6)` at bottom third + corner — separates hero copy from BG. Makes `sr-primary-hero.webp` lockup readable at any brightness. 4 CSS lines. | v2.html hero section, inline or new rule |

---

## E — ROI Upgrade Proposal: Cinematic Letterbox Reveal

**Category**: reveal_animation
**Upgrade name**: `hero-letterbox-reveal`

### What it is
On page load, the hero image enters through a cinematic letterbox: two black bars (`::before` / `::after` pseudo-elements) slide from top and bottom, revealing the full-bleed image in ~800ms. As bars retract, the SR monogram lockup fades up with `opacity: 0 → 1` (200ms delay after bars clear).

### Implementation (no CDN, no Three.js, pure CSS + 12 lines JS)

```css
/* hero-letterbox-reveal.css */
.hero {
  overflow: hidden;
  position: relative;
}

.hero::before,
.hero::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  height: 50%;
  background: var(--sr-dark, #0a0a0a);
  transform: scaleY(1);
  transform-origin: top;
  transition: transform 0.8s cubic-bezier(0.76, 0, 0.24, 1);
  z-index: 10;
}

.hero::before { top: 0; transform-origin: top; }
.hero::after  { bottom: 0; transform-origin: bottom; }

.hero.is-revealed::before,
.hero.is-revealed::after {
  transform: scaleY(0);
}

.hero__lockup {
  opacity: 0;
  transition: opacity 0.4s ease 0.7s;
}

.hero.is-revealed .hero__lockup {
  opacity: 1;
}

@media (prefers-reduced-motion: reduce) {
  .hero::before,
  .hero::after { display: none; }
  .hero__lockup { opacity: 1; }
}
```

```js
// 12 lines — fire after DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
  const hero = document.querySelector('.hero');
  if (!hero) return;
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      hero.classList.add('is-revealed');
    });
  });
});
```

### Why this upgrade, not the other 6 options

- **No layout risk**: pseudo-element overlay — zero impact on existing DOM structure, grid, or text reflow
- **Highest perceived-quality ratio**: cinematic association (FOG / Fear of God ref) from ~20 lines of code
- **`prefers-reduced-motion` safe**: skips entirely when the user has that preference set
- **Pairs with D3** (SR primary lockup): the reveal is meaningless with the wrong image; fixing the lockup makes this upgrade 10× more effective
- **Persistent effect**: every page load delivers the moment — not a one-time onboarding animation

### Expected amplitude delta
Hero goes from static loaded image → cinematic entrance. Closest comp: Fear of God editorial site load. Matches the brief's "ordinary page vs extraordinary website" gap directly.

---

## Summary Table

| Issue | Location | Fix Type | Tier |
|-------|----------|----------|------|
| Collection cards show logos not scenes | v2.html:683–728 | CSS class swap + src replace | T1 |
| Uneven 3-col grid | v2.html:404, 424 | CSS `repeat(4, 1fr)` | T1 |
| BR lockup on homepage hero | v2.html:649–656 | Asset swap | T1 |
| Jersey patches floating in BR hero | v2.html:469–481 | Remove block | T1 |
| Press strip missing | (absent) | New section | T2 |
| Marquee missing | (absent) | New section | T2 |
| Cover + hero share same image | v2.html:589 | Asset swap | T2 |
| No vignette on hero | (absent) | 4-line CSS | T3 |
| Cinematic letterbox reveal | (absent) | 20-line CSS + 12-line JS | ROI |
