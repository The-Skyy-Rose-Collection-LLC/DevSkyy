# Interactive Product Cards — Implementation Plan

**Date:** 2026-03-07
**Status:** Draft
**Scope:** WordPress theme (`wordpress-theme/skyyrose-flagship/`)
**Target:** Collection pages (v4 `col-card`) + shop pages (`product-card.php`)

---

## Problem

The current product cards are static HTML with basic CSS hover effects. For a luxury fashion brand competing with drakerelated.com-caliber experiences, the cards need tactile, immersive interactivity — especially on mobile where hover states don't exist.

Research shows: 3D interaction lifts conversions up to 94%, AR makes shoppers 65% more likely to purchase, and scarcity signals lift 8-32% in A/B tests.

### Current State

| Feature | `col-card` (collections) | `product-card.php` (shop) |
|---------|-------------------------|--------------------------|
| Hover lift | `translateY(-8px)` | CSS-only hover overlay |
| Image interaction | `scale(1.04)` zoom | Static |
| Gallery | None (single image) | None |
| Quick actions | Heart + "VIEW PIECE" overlay | Heart, eye, cart overlay |
| Touch/mobile | No touch gestures | No touch gestures |
| 3D effects | None | None |
| Card flip | None | None |
| Loading | `loading="lazy"` only | `loading="lazy"` only |
| Inline purchase | None (link to product page) | None (AJAX add-to-cart on shop) |
| Scarcity signals | None | None |

### Target State

Two complementary card components:

1. **Interactive Product Card (`interactive-product-card.php`)** — 3D rotating showcase with drag-to-rotate between front/back/branding renders, model-viewer upgrade path, conversion layer (sizes, scarcity, quick-buy)
2. **Pre-Order Reveal Card (`preorder-reveal-card.php`)** — Dramatic blur-to-reveal animation with countdown timer and pulsing CTA

Both progressively enhance from static HTML bases.

---

## Architecture

### File Structure

```
wordpress-theme/skyyrose-flagship/
├── assets/
│   ├── css/
│   │   ├── interactive-cards.css          ← NEW: all card interaction styles
│   │   └── interactive-cards.min.css      ← NEW: minified
│   └── js/
│       ├── interactive-cards.js           ← NEW: tilt, carousel, gestures, AJAX
│       └── interactive-cards.min.js       ← NEW: minified
├── template-parts/
│   ├── interactive-product-card.php       ← NEW: 3D rotating card component
│   ├── preorder-reveal-card.php           ← NEW: pre-order countdown reveal card
│   ├── product-card.php                   ← KEEP: existing shop card (unchanged)
│   └── collection-page-v4.php            ← EDIT: swap col-card for interactive card
├── inc/
│   ├── interactive-grid.php               ← NEW: data prep + render helper
│   └── enqueue.php                        ← EDIT: enqueue new assets conditionally
```

### Design Principle: Progressive Enhancement

All interactions layer ON TOP of the existing card markup. Cards remain fully functional with JS disabled — enhanced features are opt-in via `data-*` attributes and CSS classes added by JS.

```
            ┌─────────────────────────────────┐
            │  Layer 4: model-viewer / AR      │  ← JS (when .glb exists)
            ├─────────────────────────────────┤
            │  Layer 3: 3D Tilt / Gyroscope   │  ← JS (requestAnimationFrame)
            ├─────────────────────────────────┤
            │  Layer 2: Drag-Rotate + Gestures│  ← JS (pointer events)
            ├─────────────────────────────────┤
            │  Layer 1: CSS Animations        │  ← CSS (keyframes, transitions)
            ├─────────────────────────────────┤
            │  Layer 0: Static HTML Card      │  ← PHP (accessible base)
            └─────────────────────────────────┘
```

---

## Card HTML Structure

### Interactive Product Card

```html
<article class="ipc" data-product-sku="br-d01"
         data-image-front="..." data-image-back="..." data-image-branding="..."
         data-glb-src="" data-stock="12" data-price="55"
         style="--collection-accent: #C0C0C0; --collection-accent-rgb: 192, 192, 192;">

  <!-- 3D Rotating Container (3 faces at 120° intervals) -->
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
    <div class="ipc__sizes"><!-- size pills rendered by PHP --></div>
    <button class="ipc__buy-btn">Pre-Order Now — $55</button>
  </div>

  <!-- Info -->
  <div class="ipc__info">
    <h3 class="ipc__title">Hockey Jersey (Teal)</h3>
    <div class="ipc__collection-badge">Black Rose</div>
  </div>

  <!-- Quick Actions -->
  <div class="ipc__actions">
    <button class="ipc__wishlist" data-wishlist-id="br-d01" aria-label="Add to wishlist" aria-pressed="false">
      <svg><!-- heart --></svg>
    </button>
    <button class="ipc__share" aria-label="Share">
      <svg><!-- share --></svg>
    </button>
  </div>
</article>
```

### Pre-Order Reveal Card

```html
<article class="prc" data-reveal-at="2026-04-01T00:00:00Z" data-product-sku="br-d01">
  <!-- Blurred product preview -->
  <div class="prc__preview" style="filter: blur(8px);">
    <img src="..." alt="..." loading="lazy">
  </div>

  <!-- Countdown overlay -->
  <div class="prc__countdown">
    <span class="prc__timer">00:00:00</span>
    <p class="prc__tease">Something's coming...</p>
  </div>

  <!-- Revealed state (hidden until timer completes) -->
  <div class="prc__revealed" style="display:none;">
    <img src="..." alt="...">
    <h3 class="prc__title">...</h3>
    <button class="prc__cta">Pre-Order Now — $55</button>
  </div>
</article>
```

---

## Implementation Tasks

### Task 1: Skeleton Loading with Rose-Gold Shimmer

**Files:** `interactive-cards.css`
**Effort:** Small

Replace the abrupt image pop-in with a branded loading skeleton.

```css
/* Shimmer gradient uses brand rose-gold (#B76E79) */
.ipc__face--loading {
    background: linear-gradient(
        110deg,
        #0a0a0a 30%,
        rgba(183, 110, 121, 0.08) 50%,
        #0a0a0a 70%
    );
    background-size: 200% 100%;
    animation: skyyrose-shimmer 1.6s ease-in-out infinite;
}

@keyframes skyyrose-shimmer {
    0%   { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}
```

**How it works:**
- JS adds loading class to each face container
- On `img.onload`, remove the class — image fades in with `opacity` transition
- Respects `prefers-reduced-motion` — falls back to static placeholder

---

### Task 2: CSS 3D Rotating Cube (Drag-to-Rotate)

**Files:** `interactive-product-card.php`, `interactive-cards.js`, `interactive-cards.css`
**Effort:** Medium-Large

The card image area becomes a 3-face rotatable cube. Product renders already exist as `{sku}-render-front.webp`, `{sku}-render-back.webp`, `{sku}-render-branding.webp`.

**CSS setup:**
```css
.ipc__cube {
    position: relative;
    width: 100%;
    aspect-ratio: 3 / 4;
    transform-style: preserve-3d;
    perspective: 1200px;
}

.ipc__face {
    position: absolute;
    inset: 0;
    backface-visibility: hidden;
}

.ipc__face--front   { transform: rotateY(0deg)   translateZ(var(--cube-z)); }
.ipc__face--back    { transform: rotateY(120deg)  translateZ(var(--cube-z)); }
.ipc__face--branding{ transform: rotateY(240deg)  translateZ(var(--cube-z)); }
```

**JS behavior (pointer events — unified mouse + touch):**
```
On pointerdown on .ipc__cube:
  1. Record start position and current rotation
  2. On pointermove: calculate horizontal delta
  3. Map delta to rotation (1px = 0.5deg)
  4. Snap to nearest face at 120° intervals on pointerup (momentum easing)
  5. Use requestAnimationFrame for 60fps rendering
```

**Dot indicators:**
```css
.ipc__dots {
    position: absolute;
    bottom: 12px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    gap: 6px;
    z-index: 3;
}

.ipc__dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.4);
    transition: all 0.3s;
}

.ipc__dot--active {
    background: var(--collection-accent, #B76E79);
    transform: scale(1.3);
}
```

**Fallback:** If only one image exists, cube is disabled — card renders as static image with existing hover zoom.

---

### Task 3: 3D Perspective Tilt

**Files:** `interactive-cards.js`, `interactive-cards.css`
**Effort:** Medium

Card subtly tilts toward the cursor on hover, creating a physical-feeling depth effect.

**CSS setup:**
```css
.ipc {
    transform-style: preserve-3d;
    perspective: 800px;
}

.ipc__cube img {
    transform: translateZ(20px); /* Image floats above card surface */
}

.ipc__collection-badge {
    transform: translateZ(40px); /* Badge floats higher */
}
```

**JS behavior:**
```
On mousemove over .ipc:
  1. Calculate mouse position relative to card center
  2. Map to rotation: max ±8° X, ±6° Y
  3. Apply via requestAnimationFrame for 60fps
  4. Smooth return to flat on mouseleave (300ms ease-out)

On mobile (DeviceOrientation API):
  1. Map gyroscope beta/gamma to ±4° tilt
  2. Throttle to 30fps to save battery
  3. Only activate when card is in viewport (IntersectionObserver)
```

**Performance guard:**
- `prefers-reduced-motion: reduce` → disable entirely
- Cards outside viewport → unobserve, remove listeners
- Use CSS `will-change: transform` only when actively hovering

---

### Task 4: model-viewer Upgrade Path

**Files:** `interactive-product-card.php`, `interactive-cards.js`
**Effort:** Medium

When a `.glb` file exists for a product, the card auto-swaps from CSS 3D to `<model-viewer>`.

**PHP data prep (`inc/interactive-grid.php`):**
```php
$glb_path = "/assets/models/{$sku}.glb";
$glb_src  = file_exists( get_template_directory() . $glb_path )
    ? get_template_directory_uri() . $glb_path
    : '';
```

**JS activation:**
```
On DOMContentLoaded:
  For each .ipc with non-empty data-glb-src:
    1. Hide .ipc__cube
    2. Set model-viewer src to data-glb-src
    3. Show model-viewer element
    4. Add .ipc--3d-active class for CSS adjustments
```

**AR button:** model-viewer's built-in `ar` attribute handles iOS Quick Look and Android Scene Viewer automatically. No extra code needed.

**Status:** GLB files don't exist yet (Hunyuan3D-2.1 GPU duration limit blocked generation). This task builds the infrastructure so cards auto-upgrade when GLBs become available.

---

### Task 5: Conversion Layer (Sizes + Scarcity + Quick-Buy)

**Files:** `interactive-product-card.php`, `interactive-cards.js`, `interactive-cards.css`
**Effort:** Medium

**Size pills:**
```php
<div class="ipc__sizes">
    <?php foreach ( $product['sizes'] as $size ) : ?>
        <button class="ipc__size-pill" data-size="<?php echo esc_attr( $size ); ?>">
            <?php echo esc_html( $size ); ?>
        </button>
    <?php endforeach; ?>
</div>
```

**Scarcity counter:**
```css
.ipc__scarcity {
    font-size: 11px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #DC143C; /* crimson for urgency */
}
```

- JS animates the count on scroll-into-view (counts down from stock to final number)
- `aria-live="polite"` for screen reader updates
- Hidden when stock > 20 (only show for genuine scarcity)

**Quick-buy AJAX:**
- Uses existing `skyyrose_immersive_add_to_cart` action (already registered in immersive-ajax.php)
- Size must be selected first — button disabled until a pill is active
- On success: button text morphs to checkmark → "Added!" → resets after 2s
- Card border flashes with `--collection-accent` glow

---

### Task 6: Wishlist Heart Micro-Animation

**Files:** `interactive-cards.css`, `interactive-cards.js`
**Effort:** Small

Replace the instant fill toggle with a burst animation.

```css
@keyframes heart-burst {
    0%   { transform: scale(1); }
    25%  { transform: scale(1.35); }
    50%  { transform: scale(0.95); }
    100% { transform: scale(1); }
}

.ipc__wishlist--burst svg {
    animation: heart-burst 0.4s ease-out;
    color: #DC143C;
    fill: #DC143C;
}
```

**Enhancements:**
- Particle burst: 6 small SVG circles radiate outward and fade (CSS-only, no canvas)
- Haptic feedback on supported devices (`navigator.vibrate(10)`)
- `aria-pressed="true"` set synchronously for screen readers
- Existing wishlist count in toolbar (`.col-toolbar__wl-num`) updates with scale bounce

---

### Task 7: Touch Gesture System

**Files:** `interactive-cards.js`
**Effort:** Medium

A unified pointer/touch handler for mobile interactions:

| Gesture | Action |
|---------|--------|
| Horizontal drag | Rotate 3D cube between faces |
| Single tap | Open product page |
| Double tap | Toggle model-viewer AR mode (if available) |
| Long press (300ms) | Open quick-view modal (existing) |
| Vertical swipe | Scroll page (don't intercept) |

**Implementation:**
- Use `PointerEvent` API (unified mouse + touch)
- Track `pointerdown` → `pointermove` → `pointerup` with thresholds:
  - Horizontal drag: >30px horizontal delta, <20px vertical delta
  - Long press: >300ms hold with <10px movement
  - Double tap: <300ms between two taps
- `touch-action: pan-y` on card to allow vertical scrolling while capturing horizontal drags
- Passive event listeners for scroll performance

---

### Task 8: Pre-Order Reveal Card

**Files:** `preorder-reveal-card.php`, `interactive-cards.js`, `interactive-cards.css`
**Effort:** Medium

For the pre-order gateway page (`template-preorder-gateway.php`):

**Reveal sequence:**
1. Card starts with `filter: blur(8px)` and `pointer-events: none`
2. Countdown timer overlays the card center
3. On timer completion (or page load if past deadline):
   - Blur removes via 1.2s CSS transition
   - Card scales from 0.9 → 1.0 with spring easing
   - Subtle particle burst via CSS `@keyframes`
4. "Pre-Order Now" CTA pulses with rose-gold glow

```css
.prc__cta {
    animation: pulse-glow 2s ease-in-out infinite;
}

@keyframes pulse-glow {
    0%, 100% { box-shadow: 0 0 0 0 rgba(183, 110, 121, 0.4); }
    50%      { box-shadow: 0 0 20px 4px rgba(183, 110, 121, 0.15); }
}
```

---

### Task 9: Collection Page Integration

**Files:** `collection-page-v4.php`, `inc/interactive-grid.php`
**Effort:** Medium

Replace the `col-card` loop in `collection-page-v4.php` with the new interactive card:

**`inc/interactive-grid.php`:**
```php
function skyyrose_render_interactive_grid( $products, $collection_config ) {
    foreach ( $products as $product ) {
        $sku = $product['sku'];
        // Check for render images
        $renders = array( 'front', 'back', 'branding' );
        $images  = array();
        foreach ( $renders as $view ) {
            $path = "/assets/images/products/{$sku}-render-{$view}.webp";
            if ( file_exists( get_template_directory() . $path ) ) {
                $images[ $view ] = get_template_directory_uri() . $path;
            }
        }

        get_template_part( 'template-parts/interactive-product-card', null, array(
            'product'    => $product,
            'images'     => $images,
            'collection' => $collection_config,
        ) );
    }
}
```

**`collection-page-v4.php` change (lines 340-387):**
Replace the `col-card` foreach loop with:
```php
<div class="ipc-grid">
    <?php skyyrose_render_interactive_grid( $all_products, $col ); ?>
</div>
```

**Grid CSS:**
```css
.ipc-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 24px;
}

@media (max-width: 768px) {
    .ipc-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 480px) {
    .ipc-grid { grid-template-columns: 1fr; }
}
```

---

### Task 10: Performance & Accessibility

**Files:** All new files
**Effort:** Ongoing (baked into each task)

**Performance:**
- All animations use `transform` and `opacity` only (GPU-composited, no layout thrash)
- `will-change: transform` applied only during active interaction, removed after
- IntersectionObserver gates: no JS runs for off-screen cards
- Image preloading limited to visible face + 1 adjacent
- model-viewer only instantiated when `.glb` confirmed via `data-glb-src`
- Total new JS budget: <8KB gzipped
- Total new CSS budget: <3KB gzipped
- Responsive: fewer cards per row on mobile reduces GPU load

**Accessibility:**
- `prefers-reduced-motion: reduce` disables: tilt, rotation animation (instant snap), shimmer, particle burst, scarcity counter animation
- All interactive elements have `aria-label` and keyboard support
- model-viewer has `alt` attribute and built-in keyboard controls
- Size pills keyboard-navigable (arrow keys within group, `role="radiogroup"`)
- Scarcity counter uses `aria-live="polite"`
- Quick-buy button has clear accessible name: "Pre-Order {product} in size {size} — ${price}"
- Focus management: Tab flows through card elements in logical order
- Color contrast: all text meets WCAG AA against `#0a0a0a` background

---

## Conversion Features Summary

| Feature | Implementation | Data Source |
|---------|---------------|-------------|
| Scarcity counter | `data-stock` → JS animates count, CSS color shift | product-catalog.php |
| Size selector | Inline pills from product `sizes` array | product-catalog.php / WC attributes |
| Quick-buy AJAX | Uses existing `skyyrose_immersive_add_to_cart` action | immersive-ajax.php |
| Social proof toasts | Hooks into existing `conversion-engine.css` system | conversion-engine.js |
| AR button | model-viewer `ar` attribute, device-dependent | .glb files (future) |
| Collection accent | CSS `--collection-accent` from parent data | collection config arrays |
| Pre-order reveal | Countdown timer + blur-to-clear animation | `data-reveal-at` timestamp |

---

## Pages Using Interactive Cards

| Page | Card Type | Notes |
|------|-----------|-------|
| `template-collection-black-rose.php` | Interactive | Replaces `col-card` grid |
| `template-collection-love-hurts.php` | Interactive | Same |
| `template-collection-signature.php` | Interactive | Same |
| `template-collection-kids-capsule.php` | Interactive | Same |
| `template-collections.php` | Interactive | All-collections landing |
| `template-immersive-*.php` | Interactive | Products in overlay grid |
| `template-preorder-gateway.php` | Pre-Order Reveal | Different reveal animation |

---

## Enqueue Strategy

**File:** `inc/enqueue.php`

```php
// Only load on pages that use product cards
$interactive_templates = array(
    'template-collection-black-rose.php',
    'template-collection-love-hurts.php',
    'template-collection-signature.php',
    'template-collection-kids-capsule.php',
    'template-collections.php',
    'template-preorder-gateway.php',
);

// Also check immersive templates
foreach ( array( 'black-rose', 'love-hurts', 'signature' ) as $slug ) {
    $interactive_templates[] = "template-immersive-{$slug}.php";
}

if ( is_page_template( $interactive_templates ) || is_shop() || is_product_category() ) {
    wp_enqueue_style(
        'skyyrose-interactive-cards',
        SKYYROSE_ASSETS_URI . '/css/interactive-cards.min.css',
        array(),
        SKYYROSE_VERSION
    );
    wp_enqueue_script(
        'skyyrose-interactive-cards',
        SKYYROSE_ASSETS_URI . '/js/interactive-cards.min.js',
        array(),
        SKYYROSE_VERSION,
        true
    );
}
```

---

## Execution Order & Dependencies

```
Task 1  (Skeleton)        ─────────────────────────────────► Can ship alone
Task 2  (3D Cube)         ─────────────────────────────────► Can ship alone
Task 3  (Tilt)            ─────────────────────────────────► Can ship alone
Task 4  (model-viewer)    ──── depends on Task 2 (swaps cube for viewer)
Task 5  (Conversion)      ──── depends on Task 2 (lives below cube)
Task 6  (Heart Anim)      ─────────────────────────────────► Can ship alone
Task 7  (Touch Gestures)  ──── depends on Task 2 (drag-to-rotate)
Task 8  (Pre-Order Card)  ─────────────────────────────────► Can ship alone
Task 9  (Integration)     ──── depends on Task 2 + 5 (needs card + conversion)
Task 10 (A11y/Perf)       ──── parallel with all (baked into every task)
```

**Recommended implementation waves:**

| Wave | Tasks | Rationale |
|------|-------|-----------|
| Wave 1 | Task 1 + Task 6 | CSS-only, zero risk, immediate visual polish |
| Wave 2 | Task 2 + Task 3 + Task 7 | Core JS interactions (cube + tilt + gestures) |
| Wave 3 | Task 5 + Task 9 | Conversion layer + collection page integration |
| Wave 4 | Task 4 + Task 8 | model-viewer upgrade + pre-order reveal |
| Wave 5 | Task 10 | Final a11y audit + perf profiling |

---

## Testing Plan

### Unit/Integration Tests

| Test | Method |
|------|--------|
| Skeleton appears, then hides on load | Puppeteer: assert loading class removed after img loads |
| Cube rotates to correct face on drag | Puppeteer: simulate pointer sequence, assert `rotateY` value |
| Cube snaps to nearest 120° on release | JSDOM: simulate partial drag, assert snap to 0/120/240 |
| Tilt resets on mouseleave | Puppeteer: assert `transform: none` after mouseleave |
| Size pill selection enables buy button | JSDOM: click pill, assert button not disabled |
| Quick-buy AJAX succeeds | WP test: mock `wp_ajax_skyyrose_immersive_add_to_cart`, assert response |
| Heart burst animation fires | JSDOM: click heart, assert burst class present |
| Touch drag navigates cube | Puppeteer: simulate touch sequence, assert face change |
| Reduced motion disables animations | Puppeteer: set media query, assert no animation classes |
| Keyboard rotates cube | Puppeteer: focus card, press ArrowRight, assert rotation |
| Scarcity hidden when stock > 20 | JSDOM: set `data-stock="50"`, assert `.ipc__scarcity` hidden |
| Pre-order reveal triggers on timer | JSDOM: set past timestamp, trigger init, assert blur removed |
| model-viewer activates when glb exists | JSDOM: set `data-glb-src`, trigger init, assert cube hidden |

### Manual QA Checklist

- [ ] iPhone Safari: drag-rotate cube, long-press quick-view, size selection
- [ ] Android Chrome: same gestures + AR button (if .glb available)
- [ ] Desktop Firefox: tilt, drag-rotate, keyboard navigation
- [ ] Desktop Safari: all interactions
- [ ] Screen reader (VoiceOver): cube face announced, sizes selectable, buy button labeled
- [ ] Slow 3G: skeleton visible for >500ms, no layout shift
- [ ] `prefers-reduced-motion`: all animations disabled, instant face swap

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Drag-rotate conflicts with page scroll | High | `touch-action: pan-y` + strict horizontal delta threshold (>30px H, <20px V) |
| 3D transforms cause repaint storms | Low | Only `transform` + `opacity`; `will-change` scoped to active interaction |
| model-viewer bundle size (90KB) | Medium | Already loaded on immersive pages; lazy-load on collection pages via IntersectionObserver |
| Too many DOM listeners on 20+ cards | Medium | Event delegation on `.ipc-grid` container, not per-card |
| Scarcity counter feels manipulative | Low | Only show for stock ≤ 20; use real inventory data, not fake counts |
| Quick-buy without WooCommerce | Medium | Fallback: button becomes "View Product" link (same as current `col-card__view-btn`) |
| Pre-order timer timezone confusion | Low | Use UTC timestamps in `data-reveal-at`; JS converts to local display |

---

## Dependencies

- **Existing (no new installs):** model-viewer CDN (already loaded), conversion-engine.css, immersive-ajax.php, product-catalog.php
- **New dependencies:** Zero — all interactions are vanilla JS + CSS
- **Assets needed:** Front/back/branding product renders (60+ already exist), GLB files (future, optional)

---

## Not In Scope

- **Video previews on hover** — requires video assets not yet generated
- **AI-powered "complete the look"** — requires recommendation engine (Commerce Agent domain)
- **Infinite scroll / pagination** — collections have ≤14 products, grid is fine
- **WebGL shader effects** — too heavy for product cards, reserved for immersive pages

---

## References

- Current card CSS: `assets/css/collection-v4.css:616-780`
- Current card JS: `assets/js/collection-v4.js` (scroll-reveal, quick-view modal, wishlist)
- Product card template: `template-parts/product-card.php`
- Collection page template: `template-parts/collection-page-v4.php`
- Product renders: `assets/images/products/{sku}-render-{front,back,branding}.webp`
- model-viewer integration: `inc/enqueue.php`, `template-parts/brand-avatar.php`
- Brand colors: `#B76E79` (rose gold), `#0A0A0A` (dark), `#C0C0C0` (silver), `#DC143C` (crimson), `#D4AF37` (gold)
