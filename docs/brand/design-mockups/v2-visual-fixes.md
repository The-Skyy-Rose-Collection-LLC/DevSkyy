> SUPERSEDED 2026-07-10/11 — fonts now per SOT.md → typography.json (Archivo / Hanken Grotesk / Anton / Cinzel + bespoke collection name-scripts; zero-CDN self-hosted woff2). Font/CDN references below are historical.

# v2.html Visual Fix Spec

**Source:** `docs/brand/design-mockups/v2.html`
**Date:** 2026-05-25
**Auditor:** UI Designer Agent

---

## FIX-01 — F04 Spread Grid: Dead Cell + Wrong Image Treatment for Brand Marks

**File:Line:** `v2.html` CSS `.spread__grid` + `.spread__tile--lg` + `.spread__tile-img` (lines ~410–460)

**Observable Symptom:** The 4-tile home spread has an empty bottom-right cell (column 3, row 2 is always vacant). Logo/brand-mark assets are rendered with `object-fit: cover` — a 2:1 landscape logo (`black-rose-logo-hero.webp` 628×312) filling a tall portrait tile crops to a blurry centred band. Tiles read as "huge" because the mark bleeds edge-to-edge with no neutral frame.

**Root Cause:** Three-column grid (`1.4fr 1fr 1fr`) + large tile spanning `grid-row: 1/3` on column 1 leaves only 4 auto-place slots for 3 tiles (cols 2–3 row 1 = 2 slots, col 2 row 2 = 1 slot, col 3 row 2 = empty). Brand-mark assets are not photography; `object-fit: cover` is wrong for non-bleed logo display.

**Fix:**

```css
/* BEFORE */
.spread__grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr 1fr;
  gap: var(--space-4);
  aspect-ratio: 16 / 9;
  max-height: 80vh;
}
.spread__tile--lg { grid-row: 1 / 3; }
.spread__tile-img {
  width: 100%; height: 100%;
  object-fit: cover;
  opacity: 0.85;
}

/* AFTER */
.spread__grid {
  display: grid;
  grid-template-columns: 1.6fr 1fr;   /* 2-column: large + stack */
  gap: var(--space-4);
  aspect-ratio: 16 / 9;
  max-height: 80vh;
}
.spread__tile--lg { grid-row: 1 / 4; } /* spans all 3 rows on left */

/* Brand-mark tiles: contain with neutral frame */
.spread__tile--brand .spread__tile-img {
  object-fit: contain;
  padding: 24px;
  background: var(--sr-charcoal, #1a1a1a);
  opacity: 1;
}

/* Photography tiles: cover as before */
.spread__tile--photo .spread__tile-img {
  object-fit: cover;
  opacity: 0.85;
}
```

```html
<!-- BEFORE: all tiles share one class -->
<div class="spread__tile spread__tile--lg">...</div>
<div class="spread__tile">...</div>
<div class="spread__tile">...</div>
<div class="spread__tile">...</div>

<!-- AFTER: differentiate brand-mark tiles -->
<div class="spread__tile spread__tile--lg spread__tile--photo">...</div>
<div class="spread__tile spread__tile--brand">...</div>   <!-- logo -->
<div class="spread__tile spread__tile--brand">...</div>   <!-- logo -->
<div class="spread__tile spread__tile--brand">...</div>   <!-- patch -->
```

**Why it elevates professionalism:** Kith editorial spreads frame brand marks with breathing room on matte backgrounds — the mark is the subject, not fill material. Eliminating the dead cell removes the most visually destabilising artefact in the spread: an irregular white/black void that reads as a layout error, not intentional whitespace.

---

## FIX-02 — F08 BR Spread: Portrait Product Tiles Using Wrong Assets

**File:Line:** `v2.html` `.br-spread` + four tile `<img>` src attributes (lines ~620–660)

**Observable Symptom:** F08 uses `aspect-ratio: 3/4` portrait product tiles, but the assets supplied are all logo/monogram marks — not product photography. `black-rose-logo-hero.webp` (628×312 landscape) inside a 3:4 portrait tile loses ~60% of its height to cropping. The monogram (`black-rose-monogram-sr.jpg` 886×886) fills correctly but reads as a stamp, not a product.

**Root Cause:** No actual product photography exists in the asset inventory at `docs/brand/design-mockups/` for the BR mockup tiles. The tiles are structurally sound (3:4 portrait is correct for product cards) but the wrong asset class is being placed in them.

**Fix (treatment-only — no new photography):**

```css
/* BEFORE */
.br-spread .spread__tile { grid-row: auto; aspect-ratio: 3 / 4; }
.br-spread .spread__tile-img { object-fit: cover; opacity: 0.85; }

/* AFTER: brand-mark treatment for all BR tiles until product photography is available */
.br-spread .spread__tile { grid-row: auto; aspect-ratio: 3 / 4; }
.br-spread .spread__tile-img {
  object-fit: contain;
  padding: 32px 24px;
  background: linear-gradient(160deg, #111 60%, #1c1c1c 100%);
  opacity: 1;
}

/* Add a subtle label beneath each tile to signal placeholder state */
.br-spread .spread__tile::after {
  content: attr(data-sku);
  position: absolute;
  bottom: 12px;
  left: 0; right: 0;
  text-align: center;
  font-family: var(--ff-ui, 'Bebas Neue', sans-serif);
  font-size: 10px;
  letter-spacing: 0.2em;
  color: rgba(255,255,255,0.35);
}
.br-spread .spread__tile { position: relative; }
```

**Why it elevates professionalism:** Fear of God product pages use stark near-black backgrounds with centred marks when photography isn't ready — this signals intentional editorial restraint rather than a broken layout. The `data-sku` ghost label makes the placeholder intent visible to reviewers without appearing in final production.

---

## FIX-03 — Hero Lockup: Compounded Shadow on br-brand-script.webp

**File:Line:** `v2.html` `.hero__lockup img` (line ~310)

**Observable Symptom:** `br-brand-script.webp` (1600×900) has baked-in dimensional depth treatment — the script letterforms have internal shadow/emboss rendering inside the asset. The CSS `filter: drop-shadow(0 6px 24px rgba(0,0,0,0.6))` adds a second shadow at 24px blur, creating muddy feathered edges and a doubled-depth illusion. On dark hero backgrounds, the outer blur blends into the background, making the letterforms read as unsharp.

**Root Cause:** `filter: drop-shadow()` with `blur-radius: 24px` and `alpha: 0.6` is too aggressive for an asset that already carries its own depth. The two shadow layers compound rather than sum cleanly.

**Fix:**

```css
/* BEFORE */
.hero__lockup img {
  width: clamp(280px, 50vw, 720px);
  height: auto;
  filter: drop-shadow(0 6px 24px rgba(0,0,0,0.6));
  transition: transform var(--dur-reveal) var(--ease-out);
}

/* AFTER */
.hero__lockup img {
  width: clamp(280px, 50vw, 720px);
  height: auto;
  filter: drop-shadow(0 2px 10px rgba(0,0,0,0.35));   /* ambient only — no depth */
  transition: transform var(--dur-reveal) var(--ease-out);
}
```

**Why it elevates professionalism:** Palm Angels uses brand-script lockups with zero additional shadow — the mark stands alone. Reducing to an ambient ambient-only drop-shadow (2px offset, 10px blur, 35% alpha) lifts the mark off the surface without duplicating the asset's own dimensional treatment. The letterforms read with intended sharpness.

---

## FIX-04 — BR Page Hero Lockup: Spec/Code Sizing Mismatch

**File:Line:** `v2.html` `.hero__lockup img` (line ~310) — applies to both homepage and BR page sections identically

**Observable Symptom:** The design spec (`docs/superpowers/specs/2026-05-25-v2-mockup-design.md` line 104) states the BR hero lockup should occupy "~60% of hero width — larger than homepage hero — this is BR's home turf." Code uses `clamp(280px, 50vw, 720px)` for both contexts. The BR lockup reads the same scale as the homepage lockup, losing the editorial "this is the feature" hierarchy.

**Root Cause:** No `.br-page`-scoped override was added. The spec's 60% intent was not implemented.

**Fix:**

```css
/* BEFORE: same clamp for both contexts */
.hero__lockup img {
  width: clamp(280px, 50vw, 720px);
}
.hero__lockup.is-visible img { transform: scale(1.03); }

/* AFTER: BR page gets its own scope */
.hero__lockup img {
  width: clamp(280px, 50vw, 720px);     /* homepage default */
}
.hero__lockup.is-visible img {
  transform: scale(1.03);               /* homepage default */
}

/* BR page override — per spec line 104 */
.br-page .hero__lockup img {
  width: clamp(320px, 60vw, 880px);
}
.br-page .hero__lockup.is-visible img {
  transform: scale(1.04);              /* spec: 1.0 → 1.04 for BR */
}
```

**Why it elevates professionalism:** Giving the BR lockup 20% more width on its own page creates the editorial hierarchy the spec intended — it communicates "you are on Black Rose territory" with the same visual language Culture Kings uses to differentiate hero treatments per collection drop.

---

## FIX-05 — Hover States: Timid Scale vs Premium Lift

**File:Line:** `v2.html` `.spread__tile:hover` (line ~465)

**Observable Symptom:** Current hover is `transform: scale(1.015)` + a 2px rose-gold ring at 50% alpha. At 1.5% scale, the motion is perceptible but reads as a browser default rather than a deliberate interaction gesture. The ring at 50% alpha disappears against dark tile edges. On an editorial luxury mockup reviewed by a founder, this reads "template."

**Root Cause:** `scale(1.015)` is below the threshold of intentional luxury micro-interaction (~4px Y lift is the minimum for perceived intentionality). The ring opacity is too low to register as a selection indicator.

**Fix:**

```css
/* BEFORE */
.spread__tile {
  overflow: hidden;
  transition: transform var(--dur-snappy) var(--ease-out),
              box-shadow var(--dur-snappy) var(--ease-out);
}
.spread__tile:hover {
  transform: scale(1.015);
  box-shadow: 0 0 0 2px rgba(var(--sr-rose-gold-rgb), 0.5);
}

/* AFTER */
.spread__tile {
  overflow: hidden;
  transition: transform var(--dur-snappy) var(--ease-out),
              box-shadow var(--dur-snappy) var(--ease-out);
}
.spread__tile:hover {
  transform: translateY(-4px);
  box-shadow:
    0 12px 36px rgba(0,0,0,0.4),
    inset 0 0 0 1px rgba(var(--sr-rose-gold-rgb), 0.7);
}

/* Focus state — keyboard parity with hover (accessibility) */
.spread__tile:focus-visible {
  outline: none;
  transform: translateY(-4px);
  box-shadow:
    0 12px 36px rgba(0,0,0,0.4),
    inset 0 0 0 2px var(--sr-rose-gold);
}
```

**Why it elevates professionalism:** `translateY(-4px)` + directional shadow creates physical lift — the card appears to come off the surface, establishing a clear Z-axis. Kith product grids use this pattern. Moving from `scale` to `translateY` also prevents neighbouring tiles from jumping due to scale's origin-relative expansion. The inset ring at 70% alpha reads clearly against both dark and charcoal tile backgrounds. Adding `:focus-visible` closes the accessibility gap entirely (WCAG 2.4.7).

---

## FIX-06 — Voice Quote: Line-Height Risk at 72px Playfair Italic

**File:Line:** `v2.html` `.voice__quote` (line ~360)

**Observable Symptom:** `line-height: 1.1` on `font-size: clamp(36px, 6vw, 72px)` italic Playfair Display at max clamp produces 79.2px line-height on 72px glyphs. Playfair italic has pronounced ascenders/descenders — at 72px, a two-line quote will have descenders from line 1 visually merging with ascenders from line 2. If the quote wraps (likely on any screen below ~1800px wide), the two lines collide.

**Root Cause:** `line-height: 1.1` is appropriate for compressed display faces (Bebas Neue, Oswald) but too tight for Playfair Display Italic's glyph geometry.

**Fix:**

```css
/* BEFORE */
.voice__quote {
  font-family: var(--ff-voice);
  font-style: italic;
  font-size: clamp(36px, 6vw, 72px);
  line-height: 1.1;
}

/* AFTER */
.voice__quote {
  font-family: var(--ff-voice);
  font-style: italic;
  font-size: clamp(36px, 6vw, 72px);
  line-height: 1.25;   /* minimum safe for Playfair italic multi-line */
}
```

**Why it elevates professionalism:** Fear of God editorial type consistently uses 1.2–1.3 leading on high-x-height italic display faces. Tight leading on a display face at 72px is not an editorial choice here — it's a glyph collision risk. 1.25 is the minimum that gives Playfair italic the air it needs without losing the compressed luxury feel.

---

## FIX-07 — Spread Section Title: Hierarchy Collapse vs 96px Masthead

**File:Line:** `v2.html` `.spread__title` (line ~420)

**Observable Symptom:** `.spread__title` maxes at 42px (`clamp(24px, 3vw, 42px)`) while the masthead `.cover__title` reaches 96px. At a 2.3:1 ratio, the spread title reads as supporting text rather than a section anchor. On the BR spread, "THE CONCRETE COLLECTION" at 42px next to a 96px masthead creates a hierarchy gap — one element is "display type," the other reads as a label.

**Root Cause:** The spread title's clamp max was not calibrated relative to the masthead. A luxury editorial layout typically maintains a 1.5:1 to 2:1 secondary-to-primary ratio, not 2.3:1+.

**Fix:**

```css
/* BEFORE */
.spread__title {
  font-family: var(--ff-editorial);
  font-size: clamp(24px, 3vw, 42px);
  letter-spacing: 0.18em;
  color: var(--sr-gold);
}

/* AFTER */
.spread__title {
  font-family: var(--ff-editorial);
  font-size: clamp(32px, 4vw, 56px);   /* max 56px → 1.7:1 ratio vs 96px masthead */
  letter-spacing: 0.14em;              /* tighten slightly at larger size */
  color: var(--sr-gold);
}
```

**Why it elevates professionalism:** The Oaklandish brand site maintains strict secondary type hierarchy — section anchors are 55–65% of hero type, never below 40%. At 56px the spread title reads as a deliberate section statement. The letter-spacing reduction from `0.18em` to `0.14em` is also necessary at larger sizes — wider tracking at larger point sizes reads as forced formality rather than editorial confidence.

---

## FIX-08 — Hero Inner: Redundant min-height Creates Layout Double-Stack

**File:Line:** `v2.html` `.hero__inner` (line ~295)

**Observable Symptom:** `.hero` has `min-height: 100vh` AND `.hero__inner` has `min-height: 100vh`. On viewport-height constrained screens the inner element forces the hero to double its expected height — the hero becomes 200vh tall on any browser that respects both. Content below the hero is pushed off-screen on first load.

**Root Cause:** Redundant `min-height` declarations on parent-child relationship. The outer `.hero` flex container with `min-height: 100vh` already ensures full viewport height; the inner's `min-height: 100vh` is additive, not scoped.

**Fix:**

```css
/* BEFORE */
.hero__inner {
  position: relative;
  z-index: 3;
  width: 100%;
  max-width: 1440px;
  margin: 0 auto;
  padding: var(--space-24) var(--space-8);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 100vh;   /* REMOVE — parent already enforces this */
}

/* AFTER */
.hero__inner {
  position: relative;
  z-index: 3;
  width: 100%;
  max-width: 1440px;
  margin: 0 auto;
  padding: var(--space-24) var(--space-8);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  /* min-height removed — .hero already has min-height: 100vh */
}
```

**Why it elevates professionalism:** A double-height hero on first scroll is the most jarring layout failure a founder can see in a browser review. Removing the redundant `min-height` ensures the above-fold editorial composition scrolls to the next section at exactly 100vh — the cinematic "turn the page" pacing the magazine-as-site concept requires.

---

## FIX-09 — Missing Transition on Spread Tile Image Opacity

**File:Line:** `v2.html` `.spread__tile-img` (line ~468)

**Observable Symptom:** `.spread__tile-img` has `opacity: 0.85` in default state with no declared transition on `opacity`. The parent `.spread__tile` has a transition on `transform` and `box-shadow` only. On hover, if an image-level brightness or opacity change is intended, it snaps without easing.

**Root Cause:** The `transition` property on `.spread__tile` does not include `opacity`, and `.spread__tile-img` has no transition declaration of its own.

**Fix:**

```css
/* BEFORE */
.spread__tile-img {
  width: 100%; height: 100%;
  object-fit: cover;
  opacity: 0.85;
  transition: opacity var(--dur-snappy);  /* declared but parent hover doesn't change img opacity */
}

/* AFTER */
.spread__tile-img {
  width: 100%; height: 100%;
  object-fit: cover;
  opacity: 0.85;
  transition: opacity var(--dur-snappy) var(--ease-out),
              transform var(--dur-snappy) var(--ease-out);
}
.spread__tile:hover .spread__tile-img {
  opacity: 1;                             /* full opacity on parent hover */
}
```

**Why it elevates professionalism:** The 0.85 → 1.0 opacity transition on hover creates a subtle "activation" feel — the tile wakes up when touched. Without the transition, opacity change (if ever added) would snap. Declaring it now costs nothing and future-proofs the interaction.

---

## FIX-10 — Spread Reveal Stagger: CSS Custom Property Not Inherited

**File:Line:** `v2.html` `.spread__tile` reveal stagger (line ~475)

**Observable Symptom:** If `.spread__tile` elements use `--delay` for stagger via `transition-delay: var(--delay, 0ms)`, the custom property must be set inline or via nth-child. If neither is present, all tiles animate simultaneously — defeating the stagger intent.

**Root Cause:** The CSS declares `transition-delay: var(--delay, 0ms)` but the HTML tiles have no `style="--delay: Xms"` attributes and no `:nth-child` rules set the property.

**Fix:**

```css
/* AFTER: nth-child stagger (no inline style changes needed in HTML) */
.spread__tile:nth-child(1) { --delay: 0ms; }
.spread__tile:nth-child(2) { --delay: 80ms; }
.spread__tile:nth-child(3) { --delay: 160ms; }
.spread__tile:nth-child(4) { --delay: 240ms; }
```

**Why it elevates professionalism:** Simultaneous reveal of 4 tiles reads as a loading flash. Staggered reveal at 80ms intervals reads as deliberate choreography — the editorial rhythm Kith and Fear of God use for collection grid entrances.

---

## FIX-11 — Voice Section: Missing Accessible Quotation Markup

**File:Line:** `v2.html` `.voice__quote` (line ~375)

**Observable Symptom:** The large pull-quote renders as a `<p>` or `<div>`. Screen readers announce this as body text, not a quotation. The quote is attributed to the founder — this requires semantic `<blockquote>` + `<cite>`.

**Root Cause:** Semantic HTML not applied to the voice section.

**Fix:**

```html
<!-- BEFORE -->
<p class="voice__quote">"Hurts is the bloodline that raised me."</p>
<p class="voice__attribution">— Corey Foster, Founder</p>

<!-- AFTER -->
<blockquote class="voice__quote">
  <p>"Hurts is the bloodline that raised me."</p>
  <footer class="voice__attribution">
    <cite>Corey Foster, Founder</cite>
  </footer>
</blockquote>
```

```css
/* Ensure blockquote reset — browsers add default margin */
.voice__quote {
  margin: 0;
  padding: 0;
}
```

**Why it elevates professionalism:** WCAG 1.3.1 (Info and Relationships) requires semantic markup to convey meaning programmatically. `<blockquote>` + `<cite>` communicates "this is a quoted statement with an attributed source" to all user agents. It also improves structured data quality for eventual Google rich snippets.

---

## Summary — Top 5 Fixes Ranked by Impact

**1. FIX-01 — F04 Grid Dead Cell + Brand Mark Treatment**
Problem: 3-column grid leaves one cell permanently empty; `object-fit: cover` crops logos to unrecognisable blurs.
Fix: Restructure to 2-column layout; add `.spread__tile--brand` class with `object-fit: contain`, 24px padding, and charcoal background.

**2. FIX-08 — Hero Inner Redundant min-height**
Problem: Parent + child both declare `min-height: 100vh` — hero doubles to 200vh, pushing all below-fold content off-screen on first load.
Fix: Remove `min-height: 100vh` from `.hero__inner`; parent `.hero` already enforces the constraint.

**3. FIX-03 — Compounded Shadow on br-brand-script.webp**
Problem: `drop-shadow(0 6px 24px rgba(0,0,0,0.6))` stacks on top of the asset's own baked-in depth treatment — letterforms read as unsharp and muddy.
Fix: Reduce to `drop-shadow(0 2px 10px rgba(0,0,0,0.35))` — ambient only, no duplicated depth.

**4. FIX-05 — Hover States: Timid Scale vs Premium Lift**
Problem: `scale(1.015)` + 50% alpha ring reads as a browser default, not a luxury interaction.
Fix: Replace with `translateY(-4px)` + `box-shadow: 0 12px 36px rgba(0,0,0,0.4), inset 0 0 0 1px rgba(var(--sr-rose-gold-rgb), 0.7)` — physical card lift.

**5. FIX-04 — BR Hero Lockup Spec/Code Mismatch**
Problem: Spec mandates 60vw for BR's own page; both pages use the same 50vw clamp — BR reads as a homepage section, not its own territory.
Fix: Add `.br-page .hero__lockup img { width: clamp(320px, 60vw, 880px); transform: scale(1.04); }`.
