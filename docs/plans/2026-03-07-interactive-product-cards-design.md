# Interactive Product Cards — Design Document

**Date**: 2026-03-07
**Platform**: WordPress theme (skyyrose-flagship)
**Approach**: Progressive Enhancement — CSS 3D Rotating Showcase + model-viewer upgrade path

---

## Problem

SkyyRose product cards are static images in a grid. No interactivity, no 3D, no conversion optimization on the card surface. The existing `product-card.php` has hover actions (wishlist, quick-view, add-to-cart) but no 3D rotation, no AR, no scarcity signals, and no inline purchasing.

Research shows: 3D interaction lifts conversions up to 94%, AR makes shoppers 65% more likely to purchase, and scarcity signals lift 8-32% in A/B tests.

## Solution

A new `interactive-product-card.php` template part that progressively enhances:

1. **2D Base** — Luxury glassmorphism card with collection-accent glow
2. **CSS 3D** — Drag-to-rotate between front/back/branding product renders (CSS perspective + rotateY)
3. **model-viewer Upgrade** — When `.glb` file exists, card auto-swaps to `<model-viewer>` with spin, zoom, AR
4. **Conversion Layer** — Size pills, scarcity counter, quick-buy AJAX, social proof integration

### Pre-Order Variant

Separate `preorder-reveal-card.php` with a "Grand Reveal" interaction:
- Card starts blurred/locked with countdown timer
- Timer completion triggers dramatic unfold animation with particle burst
- Reveals product with pre-order CTA

---

## Architecture

```
PHP (inc/interactive-grid.php)
  ├── Reads product-catalog.php for data
  ├── Checks for .glb files in assets/models/
  ├── Passes data via wp_localize_script()
  └── Enqueues JS/CSS conditionally (collection + immersive pages)

Template Part (template-parts/interactive-product-card.php)
  ├── Renders card HTML with data-* attributes
  ├── 3 image faces: front, back, branding (data-image-front, -back, -branding)
  ├── model-viewer element (hidden, activated by JS when .glb exists)
  ├── Conversion UI: size pills, scarcity, quick-buy button
  └── Collection-aware accent via --collection-accent CSS var

JavaScript (assets/js/interactive-cards.js)
  ├── Drag-to-rotate handler (pointer events, not mouse events — touch + desktop)
  ├── CSS 3D face switching (front → back → branding at 120 degree intervals)
  ├── model-viewer activation (checks data-glb-src, swaps if available)
  ├── Scarcity counter animation (counts down from data-stock)
  ├── AJAX add-to-cart (size selection → skyyrose_immersive_add_to_cart action)
  └── IntersectionObserver for scroll-triggered card entrance animations

CSS (assets/css/interactive-cards.css)
  ├── Card container: preserve-3d, perspective(1200px)
  ├── 3 faces positioned via rotateY(0/120/240deg) translateZ()
  ├── Glassmorphism: backdrop-filter blur(24px), rgba overlay
  ├── Collection accent glow: box-shadow with var(--collection-accent)
  ├── Scarcity bar: gradient from green → crimson based on stock %
  ├── Size pills: inline flex, accent color on selection
  ├── Quick-buy button: full-width CTA at card bottom
  └── Responsive: 1-col mobile, 2-col tablet, 3-col desktop
```

---

## Card HTML Structure

```html
<article class="ipc" data-product-sku="br-d01"
         data-image-front="..." data-image-back="..." data-image-branding="..."
         data-glb-src="" data-stock="12" data-price="55">

  <!-- 3D Rotating Container -->
  <div class="ipc__cube">
    <div class="ipc__face ipc__face--front">
      <img src="..." alt="..." loading="lazy">
    </div>
    <div class="ipc__face ipc__face--back">
      <img src="..." alt="..." loading="lazy">
    </div>
    <div class="ipc__face ipc__face--branding">
      <img src="..." alt="..." loading="lazy">
    </div>
  </div>

  <!-- model-viewer (hidden until .glb available) -->
  <model-viewer class="ipc__3d" src="" poster="..."
    camera-controls auto-rotate shadow-intensity="0.4"
    ar ar-modes="webxr scene-viewer quick-look"
    style="display:none">
  </model-viewer>

  <!-- Conversion Layer -->
  <div class="ipc__conversion">
    <div class="ipc__scarcity">Only <span class="ipc__stock-count">12</span> left</div>
    <div class="ipc__sizes"><!-- size pills --></div>
    <button class="ipc__buy-btn">Pre-Order Now — $55</button>
  </div>

  <!-- Info -->
  <div class="ipc__info">
    <h3 class="ipc__title">Hockey Jersey (Teal)</h3>
    <div class="ipc__collection-badge">Black Rose</div>
  </div>

  <!-- Quick Actions (wishlist, share) -->
  <div class="ipc__actions">
    <button class="ipc__wishlist" aria-label="Add to wishlist">...</button>
    <button class="ipc__share" aria-label="Share">...</button>
  </div>
</article>
```

---

## Conversion Features

| Feature | Implementation | Data Source |
|---------|---------------|-------------|
| Scarcity counter | `data-stock` → JS animates count, CSS color gradient | product-catalog.php |
| Size selector | Inline pills from product `sizes` array | product-catalog.php |
| Quick-buy AJAX | Uses existing `skyyrose_immersive_add_to_cart` action | immersive-ajax.php |
| Social proof toasts | Hooks into existing `conversion-engine.css` system | conversion-engine.js |
| AR button | model-viewer `ar` attribute, device-dependent | model-viewer CDN |
| Collection accent | CSS `--collection-accent` from parent `.collection--{slug}` | collections.css |

---

## Pre-Order Reveal Variant

Separate component for the pre-order gateway page:

- Card starts with `filter: blur(8px)` and `pointer-events: none`
- Countdown timer overlays the card center
- When timer hits zero (or on page load if past deadline): blur removes via CSS transition, card scales from 0.9 to 1.0, subtle particle burst via CSS `@keyframes`
- "Pre-Order Now" CTA pulses with rose-gold glow
- Different visual language from collection cards (darker, more dramatic)

---

## Pages Using Interactive Cards

| Page | Card Type | Notes |
|------|-----------|-------|
| `template-immersive-black-rose.php` | Interactive (replaces hotspot panel) | Products shown as 3D cards in overlay grid |
| `template-immersive-love-hurts.php` | Interactive | Same |
| `template-immersive-signature.php` | Interactive | Same |
| `template-collection-black-rose.php` | Interactive (replaces static grid) | Full 3D card grid |
| `template-collection-love-hurts.php` | Interactive | Same |
| `template-collection-signature.php` | Interactive | Same |
| `template-preorder-gateway.php` | Pre-Order Reveal variant | Different reveal animation |

---

## Dependencies

- **Existing**: model-viewer CDN (already loaded), conversion-engine.css (already loaded), immersive-ajax.php (already registered)
- **New**: Zero new npm/CDN dependencies
- **Assets needed**: Front/back/branding product renders (exist for most products), GLB files (future, optional)

---

## Performance

- Cards lazy-load via IntersectionObserver (no 3D transforms until in viewport)
- model-viewer only instantiated when `.glb` file confirmed via `data-glb-src`
- CSS `will-change: transform` on card container for GPU compositing
- Responsive: fewer cards per row on mobile reduces GPU load
- `prefers-reduced-motion` respected: disables auto-rotate and entrance animations

---

## Accessibility

- All images have alt text from product catalog
- Size pills are keyboard-navigable (arrow keys within group)
- model-viewer has `alt` attribute and keyboard controls
- Scarcity counter uses `aria-live="polite"` for screen reader updates
- Quick-buy button has clear accessible name with product + price
- Focus management: tab order flows naturally through card elements
