# Interactive Product Cards — Implementation Plan

**Design doc**: `docs/plans/2026-03-07-interactive-product-cards-design.md`
**Theme**: `wordpress-theme/skyyrose-flagship/`
**Status**: Ready to implement

---

## Files to Create

| # | File | Purpose |
|---|------|---------|
| 1 | `inc/interactive-grid.php` | PHP module — enqueue logic, `wp_localize_script()`, render helper |
| 2 | `assets/css/interactive-cards.css` | Card styles — 3D cube, glassmorphism, conversion layer, responsive grid |
| 3 | `assets/js/interactive-cards.js` | Card behavior — drag-to-rotate, model-viewer swap, AJAX quick-buy, scarcity |
| 4 | `template-parts/interactive-product-card.php` | Card HTML template part (3D cube + model-viewer + conversion UI) |
| 5 | `assets/css/preorder-reveal.css` | Pre-order reveal variant styles — blur, countdown, particle burst |
| 6 | `assets/js/preorder-reveal.js` | Pre-order reveal behavior — countdown timer, blur removal, CTA pulse |
| 7 | `template-parts/preorder-reveal-card.php` | Pre-order card HTML template part |

## Files to Modify

| # | File | Changes |
|---|------|---------|
| 8 | `inc/enqueue.php` | Add `skyyrose_enqueue_interactive_cards()` hook + defer handles |
| 9 | `functions.php` | Require `inc/interactive-grid.php` |

---

## Step-by-Step Implementation

### Phase 1: Foundation — PHP Module + Enqueue Wiring

#### Step 1: Create `inc/interactive-grid.php`

**What**: PHP module that provides the `skyyrose_render_interactive_grid()` helper function and the `skyyrose_enqueue_interactive_cards()` enqueue callback.

**Implementation details**:
- Define `skyyrose_enqueue_interactive_cards()`:
  - Check `skyyrose_get_current_template_slug()` against target slugs: `'collection-v4'`, `'immersive'`, `'preorder-gateway'`, `'collection'`
  - Enqueue `interactive-cards.css` (dep: `skyyrose-design-tokens`) and `interactive-cards.js` (no deps, deferred)
  - On `preorder-gateway` slug, also enqueue `preorder-reveal.css` + `preorder-reveal.js`
  - Call `wp_localize_script( 'skyyrose-interactive-cards', 'skyyRoseCards', [...] )` with:
    - `ajaxUrl` → `admin_url( 'admin-ajax.php' )`
    - `nonce` → `wp_create_nonce( 'skyyrose-immersive-nonce' )` (reuse existing action)
    - `assetsUri` → `SKYYROSE_ASSETS_URI`
    - `wcActive` → `class_exists( 'WooCommerce' )`
- Define `skyyrose_render_interactive_grid( $collection_slug, $options = [] )`:
  - Calls `skyyrose_get_collection_products( $collection_slug )` from `product-catalog.php`
  - Filters to `published === true` products
  - Loops products, calling `get_template_part( 'template-parts/interactive-product-card', null, $product_args )` for each
  - Wraps in `<section class="ipc-grid ipc-grid--{$collection_slug}">` container
  - `$options` supports: `'card_type' => 'preorder'` to switch to `preorder-reveal-card` template
- Define `skyyrose_render_preorder_grid()`:
  - Calls `skyyrose_get_preorder_products()`
  - Loops by collection, renders each product with `get_template_part( 'template-parts/preorder-reveal-card', null, $args )`
  - Wraps in `<section class="ipc-grid ipc-grid--preorder">`

**Data flow**: `product-catalog.php` → `interactive-grid.php` → `interactive-product-card.php` template part

```
★ Why this step first: The PHP module must exist before any template or JS can reference it.
  It establishes the data pipeline and conditional loading — no CSS/JS loads on pages that
  don't need it, keeping the payload lean.
```

#### Step 2: Wire into `inc/enqueue.php`

**What**: Register the new enqueue function at priority 35 (after template styles at 20, model-viewer at 28, size-guide at 30).

**Changes to `inc/enqueue.php`**:
```php
// Interactive Product Cards — 3D rotating cards on collection + immersive + preorder pages.
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_interactive_cards', 35 );
```

**Also add to `$defer_handles` array** in `skyyrose_defer_scripts()`:
```php
'skyyrose-interactive-cards',
'skyyrose-preorder-reveal',
```

**Why priority 35**: After model-viewer (28) and size-guide (30), so `google-model-viewer` is already registered as a dependency if needed. Before cross-sell engine (40) and analytics beacon (50).

#### Step 3: Require in `functions.php`

**What**: Add `require_once SKYYROSE_DIR . '/inc/interactive-grid.php';` in the includes section.

**Position**: After the existing `require_once` for `inc/product-catalog.php` (since `interactive-grid.php` depends on catalog functions).

---

### Phase 2: Interactive Product Card (CSS 3D + Template)

#### Step 4: Create `assets/css/interactive-cards.css`

**What**: All visual styles for the interactive product card component.

**CSS architecture** (BEM, using `ipc` prefix):
```
.ipc-grid           — CSS grid container: 1-col mobile, 2-col tablet, 3-col desktop
.ipc                — Card article: perspective(1200px), position relative
.ipc__cube          — 3D cube container: transform-style preserve-3d, will-change transform
.ipc__face          — Each face: position absolute, backface-visibility hidden
.ipc__face--front   — rotateY(0deg) translateZ(calc(var(--card-width) / 2))
.ipc__face--back    — rotateY(120deg) translateZ(...)
.ipc__face--branding — rotateY(240deg) translateZ(...)
.ipc__3d            — model-viewer element: hidden by default, full card fill
.ipc__conversion    — Bottom overlay: glassmorphism panel
.ipc__scarcity      — Scarcity bar: gradient green→crimson based on --stock-pct
.ipc__sizes         — Size pill container: inline-flex, gap
.ipc__size-pill     — Individual pill: border, hover/selected state with accent
.ipc__buy-btn       — Full-width CTA button: rose-gold gradient, pulse animation
.ipc__info          — Title + collection badge
.ipc__actions       — Wishlist + share floating buttons
```

**Key design tokens to use**:
- `--glass-bg`, `--glass-blur`, `--glass-border` for glassmorphism panels
- `--color-rose-gold` for accent glow and CTA
- `--color-crimson` for low-stock scarcity
- `--color-gold` for price display
- Collection accent via `--collection-accent` CSS custom property (set by parent grid)

**Collection accent mapping** (set on `.ipc-grid--{slug}`):
- `black-rose`: `#B76E79` (rose gold)
- `love-hurts`: `#DC143C` (crimson)
- `signature`: `#D4AF37` (gold)

**Responsive breakpoints**:
- `< 640px`: 1 column, card max-width 100%
- `640px–1023px`: 2 columns
- `≥ 1024px`: 3 columns

**Accessibility**:
- `prefers-reduced-motion: reduce` → disable auto-rotate, entrance animations, cube transitions use `opacity` instead of `transform`
- Focus-visible outlines on all interactive elements
- High-contrast mode: solid borders replace glow effects

#### Step 5: Create `template-parts/interactive-product-card.php`

**What**: PHP template part that renders the card HTML structure from the design doc.

**Accepts via `$args`**:
- Product data from catalog (`sku`, `name`, `price`, `collection`, `image`, `front_model_image`, `back_image`, `sizes`, `edition_size`, `is_preorder`, `published`)
- Additional: `glb_src` (empty string if no GLB file), `stock` (integer, defaults to `edition_size`)

**Data attribute mapping** (PHP → HTML):
```
$args['sku']               → data-product-sku
$args['image']             → data-image-front (uses skyyrose_product_image_uri())
$args['back_image']        → data-image-back
$args['front_model_image'] → data-image-branding (the 3D render view)
$args['glb_src']           → data-glb-src (checked against assets/models/{sku}.glb)
$args['edition_size']      → data-stock
$args['price']             → data-price
```

**GLB file detection**: Check `file_exists( SKYYROSE_DIR . '/assets/models/' . $sku . '.glb' )` — if true, set `data-glb-src` to the URI. This is the progressive enhancement path.

**Template structure** (matches design doc HTML exactly):
1. `<article class="ipc" ...>` with all data-* attributes
2. `.ipc__cube` with 3 `.ipc__face` divs (front/back/branding), each with lazy `<img>`
3. `<model-viewer class="ipc__3d" style="display:none">` (hidden, JS activates)
4. `.ipc__conversion` with scarcity counter, size pills from `$sizes` array, buy button
5. `.ipc__info` with title and collection badge
6. `.ipc__actions` with wishlist and share buttons

**Size pills**: Split `$args['sizes']` by `|`, render each as `<button class="ipc__size-pill" data-size="{size}">{size}</button>`. Skip if `sizes === 'One Size'` (render as text instead).

**Buy button text logic**:
- `is_preorder === true` → "Pre-Order Now — $XX"
- else → "Add to Cart — $XX"

```
★ Why front_model_image as "branding" face: The 3D product renders show the garment on a
  mannequin — this is the most aspirational view and works as the "branding" rotation stop.
  The raw product photo is "front", the back flat-lay is "back".
```

---

### Phase 3: Interactive Cards JavaScript

#### Step 6: Create `assets/js/interactive-cards.js`

**What**: Client-side behavior for all interactive product cards on the page.

**Module structure** (IIFE, no build step — matches theme convention):
```javascript
(function() {
  'use strict';

  // 1. IntersectionObserver — activate cards when scrolled into view
  // 2. Drag-to-rotate handler (pointer events for touch + desktop)
  // 3. model-viewer activation (check data-glb-src)
  // 4. Scarcity counter animation
  // 5. Size pill selection
  // 6. AJAX quick-buy
})();
```

**Detailed behavior**:

1. **IntersectionObserver** (threshold: 0.15)
   - Cards start with `opacity: 0; transform: translateY(40px)`
   - On intersection: add `.ipc--visible` class → CSS transitions to `opacity: 1; translateY(0)`
   - Also triggers scarcity counter animation on first view

2. **Drag-to-rotate** (Pointer Events API)
   - `pointerdown` on `.ipc__cube` → track start X position
   - `pointermove` → calculate delta X, update `--rotate-y` CSS custom property
   - Snap to nearest 120° interval on `pointerup` (front=0°, back=120°, branding=240°)
   - Use `requestAnimationFrame` for smooth rotation
   - Touch support: `touch-action: none` on the cube element
   - `setPointerCapture()` for reliable drag across card boundaries

3. **model-viewer activation**
   - On page load, query all `.ipc[data-glb-src]` where value is non-empty
   - For each: set `<model-viewer>.src`, remove `style="display:none"`, hide `.ipc__cube`
   - model-viewer is already loaded via `skyyrose_enqueue_model_viewer()` at priority 28

4. **Scarcity counter**
   - Read `data-stock` attribute
   - Animate count from 0 → stock value over 1.2s (easing: ease-out)
   - Set `--stock-pct` CSS variable (stock / 250 * 100) for scarcity bar color
   - Update `aria-live="polite"` region

5. **Size pill selection**
   - Click handler on `.ipc__size-pill` → toggle `.ipc__size-pill--selected`
   - Only one size selected per card (radio behavior)
   - Update hidden `data-selected-size` on the card article

6. **AJAX quick-buy**
   - Click `.ipc__buy-btn` → read `data-product-sku`, `data-selected-size`, `data-price`
   - Validate size selected (if applicable — skip for "One Size")
   - POST to `skyyRoseCards.ajaxUrl` with action `skyyrose_immersive_add_to_cart`
   - Pass: `sku`, `attribute_pa_size`, `quantity: 1`, `nonce`
   - On success: button text → "Added!", brief rose-gold flash animation
   - On error: button text → error message, revert after 2s
   - Reuse existing `skyyrose_immersive_add_to_cart` AJAX handler (already in `inc/immersive-ajax.php`)

```
★ Why reuse the immersive add-to-cart handler: immersive-ajax.php already handles SKU→ID
  resolution, variation matching for sizes, and cart fragment updates. Zero new PHP needed
  for the purchase flow — just wire the JS to the same endpoint.
```

---

### Phase 4: Pre-Order Reveal Variant

#### Step 7: Create `assets/css/preorder-reveal.css`

**What**: Styles for the dramatic pre-order card reveal animation.

**Key CSS**:
- `.prc` (preorder-reveal-card) extends `.ipc` base styles
- `.prc--locked` state: `filter: blur(8px); pointer-events: none; transform: scale(0.9)`
- `.prc__countdown` overlay: centered, large monospace timer digits, glassmorphism backdrop
- `.prc--revealed` transition: `filter: blur(0); transform: scale(1)` over 0.8s cubic-bezier
- `.prc__particles` — CSS-only particle burst via `@keyframes`:
  - 12 pseudo-element particles (6 via `.prc__particles::before/after` + 6 via child spans)
  - Each particle: small circle, random trajectory via CSS custom properties, fade out
  - Rose-gold (`#B76E79`) and gold (`#D4AF37`) particle colors
- `.prc__buy-btn` CTA: pulsing `box-shadow` animation with rose-gold glow
- Dark dramatic background: `--color-page-bg` with extra overlay

#### Step 8: Create `template-parts/preorder-reveal-card.php`

**What**: PHP template for the pre-order reveal card variant.

**Differences from interactive-product-card.php**:
- Wraps in `<article class="prc prc--locked" ...>` (starts locked)
- Includes `.prc__countdown` overlay with `<time>` element
- Includes `.prc__particles` container (12 `<span>` elements for particle burst)
- CTA text: "Pre-Order Now" with pulsing glow
- No drag-to-rotate (simpler — just front image with blur reveal)
- Reads `data-reveal-time` from `get_option( 'skyyrose_preorder_deadline' )` or defaults to "already revealed"

**Data attributes**:
- `data-reveal-time` — ISO 8601 timestamp for countdown target
- `data-product-sku`, `data-price`, `data-stock` — same as interactive card

#### Step 9: Create `assets/js/preorder-reveal.js`

**What**: Countdown timer + reveal animation logic.

**Behavior**:
1. On load: query all `.prc[data-reveal-time]`
2. For each card:
   - Parse `data-reveal-time` as Date
   - If past → immediately call `revealCard(card)`
   - If future → start `setInterval(1000)` countdown:
     - Update `.prc__countdown` with days/hours/min/sec
     - On zero → call `revealCard(card)`
3. `revealCard(card)`:
   - Remove `.prc--locked`, add `.prc--revealed`
   - Trigger `.prc__particles` animation (add `.prc__particles--active`)
   - Enable `pointer-events`
   - After 2s: remove particle elements (cleanup)

---

### Phase 5: Integration + Polish

#### Step 10: Update `inc/enqueue.php` — Register defer handles

**What**: Add the two new script handles to the `$defer_handles` array.

**Changes**: In `skyyrose_defer_scripts()`, add:
```php
'skyyrose-interactive-cards',
'skyyrose-preorder-reveal',
```

This ensures both scripts get the `defer` attribute for non-blocking page load.

#### Step 11: Update `functions.php` — Require the new module

**What**: Add `require_once SKYYROSE_DIR . '/inc/interactive-grid.php';`

**Position**: After the line that requires `inc/product-catalog.php`.

---

## Integration Points (Future Steps — Not in This Plan)

These are noted for awareness but NOT implemented in this plan:

- **Template replacement**: Replace `get_template_part('template-parts/product-card')` calls in collection templates with `skyyrose_render_interactive_grid()`. This is a separate task to avoid breaking existing pages.
- **Pre-order gateway**: Replace the current product grid in `template-preorder-gateway.php` with `skyyrose_render_preorder_grid()`.
- **Immersive scenes**: Replace hotspot panel product cards with interactive cards in overlay grids.
- **Minification**: Run the CSS/JS through the existing minification pipeline to generate `.min.css` / `.min.js` files.

---

## Dependency Graph

```
functions.php
  └── requires inc/interactive-grid.php
        └── uses inc/product-catalog.php (skyyrose_get_product_catalog, etc.)
        └── registers enqueue callback

inc/enqueue.php
  └── skyyrose_enqueue_interactive_cards() at priority 35
        ├── interactive-cards.css (dep: skyyrose-design-tokens)
        ├── interactive-cards.js (deferred, localized with skyyRoseCards)
        ├── preorder-reveal.css (conditional: preorder-gateway only)
        └── preorder-reveal.js (conditional: preorder-gateway only)

Template parts
  ├── template-parts/interactive-product-card.php
  │     └── reads $args from skyyrose_render_interactive_grid()
  └── template-parts/preorder-reveal-card.php
        └── reads $args from skyyrose_render_preorder_grid()

AJAX (existing — no changes)
  └── inc/immersive-ajax.php → skyyrose_immersive_add_to_cart action
```

---

## Testing Checklist

- [ ] Cards render on collection-v4 pages with correct product data
- [ ] Drag-to-rotate works on desktop (mouse) and mobile (touch)
- [ ] Card snaps to nearest 120° face on release
- [ ] model-viewer activates when `.glb` file exists in `assets/models/`
- [ ] model-viewer stays hidden when no `.glb` exists (CSS 3D fallback works)
- [ ] Size pills select/deselect correctly (radio behavior)
- [ ] Quick-buy AJAX adds to WooCommerce cart with correct SKU + size
- [ ] Scarcity counter animates on scroll into view
- [ ] `prefers-reduced-motion` disables animations
- [ ] Pre-order reveal countdown counts down correctly
- [ ] Pre-order reveal triggers at zero with particle burst
- [ ] Already-past deadlines show revealed cards immediately
- [ ] Cards are keyboard-navigable (tab through pills, buttons)
- [ ] `aria-live` updates for scarcity counter
- [ ] Responsive: 1→2→3 columns at breakpoints
- [ ] No JS errors when WooCommerce is deactivated (graceful degradation)
- [ ] Assets only load on target pages (not homepage, about, etc.)
