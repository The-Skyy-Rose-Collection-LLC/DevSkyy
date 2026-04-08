# Immersive Worlds — Implementation Status

## Architecture

**Target:** `wordpress-theme/skyyrose-flagship/` — vanilla Three.js via CDN + PHP templates.
**Site:** `skyyrose.co` (WordPress/WooCommerce).
**Fallback:** Existing `immersive.js` hotspot system for non-WebGL browsers.

### Three.js Stack (Production)
- **Three.js r160** via jsdelivr CDN (9 add-on scripts)
- Add-ons: OrbitControls, GLTFLoader, DRACOLoader, RGBELoader, EffectComposer, RenderPass, UnrealBloomPass, ShaderPass, CopyShader
- Enqueued conditionally per-template in `inc/enqueue-features.php` at priority 65

### Load Chain
```
threejs (CDN r160)
  └─ 9 add-on scripts
       └─ experience-base.js (SkyyRoseExperience base class)
            └─ luxury-animations.js (shared animation utilities)
                 └─ {collection}-experience.js (per-collection scene)
                      └─ init-3d.js (orchestrator: lazy load, visibility, cleanup)
```

### File Map
```
assets/js/
  immersive-world.js              ← Core world engine (existing, kept as fallback)
  immersive-wc-bridge.js          ← WooCommerce ↔ Three.js data bridge
  experiences/
    experience-base.js            ← SkyyRoseExperience base class
    blackrose-experience.js       ← Gothic moonlit garden (763 lines)
    lovehurts-experience.js       ← Beast's cathedral (702 lines)
    signature-experience.js       ← Golden Gate runway (528 lines)
    luxury-animations.js          ← Shared animation utilities
    mannequin-bust.js             ← 3D mannequin display
    init-3d.js                    ← Initialization orchestrator

inc/
  enqueue.php                     ← Global asset loading
  enqueue-engines.php             ← skyyrose_enqueue_engine() helper
  enqueue-features.php            ← Collection experience enqueue (priority 65)
  immersive-ajax.php              ← AJAX: get-product-by-sku, get-collection, add-to-cart

template-immersive-black-rose.php ← 2D fallback rooms + world config
template-immersive-love-hurts.php
template-immersive-signature.php
```

## The 3 Worlds

### 1. Black Rose — "The Bay Bridge"
- **Bridge:** BAY BRIDGE (Oakland/East Bay) — NOT Golden Gate
- **Vibe:** Street luxury. "Luxury Grows from Concrete." Night/twilight.
- **Products (11):**
  - br-001: Crewneck, br-002: Joggers, br-003: BLACK is Beautiful Jersey
  - br-004: Hoodie, br-005: Hoodie Sig Ed, br-006: Sherpa Jacket, br-007: Basketball Shorts
  - br-008–011: Jersey Series (SF, LAST OAKLAND, THE BAY, THE ROSE)
- **Scene:** Gothic moonlit garden, iron gazebos, rose topiaries, moonbeams
- **Particles:** Black rose petals, fog, city bokeh

### 2. Love Hurts — "The Beast's Cathedral"
- **Theme:** Beauty and the Beast from the BEAST's perspective
- **Vibe:** Gothic romance, enchanted rose under glass dome, candlelight
- **Products (4):**
  - lh-002: Joggers, lh-003: Basketball Shorts, lh-004: Varsity Jacket, lh-006: The Fannie
- **Scene:** Cathedral with stained glass, enchanted rose shrine, thorned corridors
- **Particles:** Crimson petals, candle flicker, dust beams, heartbeat pulse

### 3. Signature — "The Golden Gate Runway"
- **Bridge:** GOLDEN GATE BRIDGE (SF side) — NOT Bay Bridge
- **Vibe:** High fashion + Bay Area. Golden hour, fog through cables.
- **Products (13):**
  - sg-001: Bay Bridge Shorts, sg-002: Stay Golden Shirt, sg-003: Stay Golden Shorts
  - sg-004: Signature Hoodie, sg-005: Bay Bridge Shirt, sg-006: Mint & Lavender Hoodie
  - sg-007: Signature Beanie, sg-009: Sherpa Jacket, sg-010: Bridge Series Shorts
  - sg-011: Original Label Tee White, sg-012: Original Label Tee Orchid
  - sg-013: Mint & Lavender Crewneck, sg-014: Mint & Lavender Sweatpants
- **Scene:** Golden Gate with fashion runway, golden hour fog, water reflections
- **Particles:** Golden hour flare, fog, water sparkle

## SkyyRose Avatar Easter Egg
- **Character:** Little Black girl, Pixar quality, curly afro, big brown eyes
- **Reference:** `source-products/brand-assets/skyyrose-avatar-reference.jpeg`
- **Mascot sprites:** `assets/images/mascot/skyyrose-mascot-*.png` (7 poses + idle)
- Hidden in each world → find all 3 → "Hi! I'm SkyyRose!"
- Different outfit per world
- Walks onto screen as full-body character (NOT a chatbot widget)

## Progressive Enhancement
- **Level 0** (no JS): Static scene image + product links (SSR from PHP)
- **Level 1** (no WebGL): Existing `immersive.js` hotspot system with 2D rooms
- **Level 2** (WebGL): Full Three.js experience with per-collection scenes
- **Level 3** (WebGL + gyroscope): Mobile tilt-to-explore

## Quality Gates (Completed Apr 4, 2026)
- [x] Experience base class with RAF lifecycle (isRunning, dispose, cancelAnimationFrame)
- [x] Proper event listener cleanup (stored bound refs)
- [x] Canvas removal + forceContextLoss on dispose
- [x] GLTFLoader guarded against missing add-ons
- [x] prefers-reduced-motion support (static render, skip animations)
- [x] Safari 12 compat (no optional chaining)
- [x] init-3d.js owns initialization (no dual-init from experience files)
- [x] Three.js polling has retry limit (5s max)
- [x] No console.log in production handlers
- [x] All AJAX handlers nonce-verified with rate limiting

## Deleted SKUs (DO NOT USE)
- lh-001, lh-005, br-d01–d04, sg-d01–d04, sg-008 — purged from all production files
