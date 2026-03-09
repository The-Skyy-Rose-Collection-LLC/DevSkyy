# Immersive Worlds Build Plan

## Goal
Replace 2D image-map immersive experiences with Three.js-powered 3D worlds that make drakerelated.com look like pre-schoolers.

## Target: WordPress Theme (skyyrose-flagship)
NOT Next.js. All code goes in the WordPress theme as vanilla JS + PHP templates.

## What Drake Does (and why it's basic)
- Static 2D room images with CSS-positioned hotspot dots
- Point-and-click navigation between rooms (page loads)
- No 3D, no animation, no parallax, no audio, no scroll effects
- Built on Shopify Oxygen (React SSR) — glorified image map

## What We Already Have
- `immersive.js` — existing hotspot/panel/room-nav system (keep as fallback)
- `template-immersive-{black-rose,love-hurts,signature}.php` — existing templates
- 60+ AI-generated scene images in `assets/scenes/`
- `skyyrose_immersive_product()` helper function for product data
- Product images in `assets/images/products/`
- 89 source product files in `skyyrose/assets/images/source-products/`
- SkyyRose avatar reference: `source-products/brand-assets/skyyrose-avatar-reference.jpeg`
- Existing mascot PNGs in `assets/images/mascot/` (7 poses)

## The 3 Worlds

### 1. Black Rose World — "The Bay Bridge"
- **Bridge:** BAY BRIDGE (Oakland/East Bay side) — NOT Golden Gate
- **Vibe:** Street luxury. "Luxury Grows from Concrete." East Bay pride.
- **Scene images to use:**
  - `black-rose-rooftop-garden-v2.png` (main background)
  - `black-rose-moonlit-courtyard.jpg`
  - `black-rose-iron-gazebo-garden.png`
  - `black-rose-marble-rotunda.png`
  - `black-rose-white-rose-grotto.png`
- **Products (current collection):**
  - br-001: Crewneck
  - br-002: Joggers
  - br-003: Baseball Jerseys (3 colorways: black, Giants, Oakland A's)
  - br-004: Hoodie (rose sleeve art) — CURRENT, just added
  - br-005: Hoodie+Jogger Set
  - br-006: Sherpa Jacket
  - br-007: Shorts
  - br-008: Dress
- **Products (pre-order):**
  - br-d01: Hockey Jersey (Teal)
  - br-d02: Football Jersey (Red #80)
  - br-d03: Football Jersey (White #32)
  - br-d04: Basketball Jersey
- **Particles:** Black rose petals, fog from water, city light bokeh
- **Sound:** Bay water, distant BART, urban night

### 2. Love Hurts World — "The Beast's Cathedral"
- **Theme:** Beauty and the Beast from the BEAST's perspective
- **Vibe:** Gothic romance. Isolation, thorns, pain of love. Enchanted rose under glass dome.
- **Scene images to use:**
  - `love-hurts-cathedral-rose-chamber.png` (main — enchanted rose dome centerpiece)
  - `love-hurts-gothic-ballroom.png`
  - `love-hurts-crimson-throne-room.png`
  - `love-hurts-enchanted-rose-shrine.png`
  - `love-hurts-giant-rose-staircase.png`
  - `love-hurts-reflective-ballroom.png`
  - `enchanted-rose-dome-*.jpg` (3 dome photos)
- **Products (current):**
  - lh-001: Fannie Pack ($65, pre-order)
  - lh-002: Joggers (White + Black)
  - lh-003: Shorts
  - lh-004: Joggers (Black)
  - lh-005: Bomber/Varsity Jacket
- **Products (pre-order):**
  - Slide Sandal (Love Hurts design)
- **Particles:** Crimson rose petals, candle flicker, dust in light beams, heartbeat pulse
- **Sound:** Cathedral echo, slowed music box (B&B melody), heartbeat, dripping water
- **Narrative:** Scroll deeper = deeper into Beast's story. Thorns get thicker. Rose loses petals.

### 3. Signature World — "The Golden Gate Runway"
- **Bridge:** GOLDEN GATE BRIDGE (San Francisco side)
- **Vibe:** High fashion meets Bay Area. Bridge between street and luxury.
- **Scene images to use:**
  - `signature-golden-gate-showroom.png` (main)
  - `signature-waterfront-runway.png`
- **Products (current):**
  - sg-002: Mint Tee
  - sg-003: Crop Hoodie
  - sg-004: Mint Hoodie
  - sg-005: Bay Rose Set
  - sg-006: Tie-Dye Crewneck
  - sg-007: Beanie (Black) $25
  - sg-008: Beanie (Forest Green) $25
  - sg-009: Sherpa Jacket
  - sg-010: Bridge Shorts (2 colorways) + Matching Tees — PRE-ORDER
  - sg-011: Premium Tee (White)
  - sg-012: Premium Tee (Orchid)
  - sg-013: Cycling Jersey (Gold)
  - sg-014: Cycling Jersey (Silver)
- **Products (pre-order):**
  - sg-d01: Windbreaker Set
  - sg-d02: Collection Shorts
  - Slide Sandal (SR Monogram + Black Rose designs)
- **Particles:** Golden hour lens flare, fog through bridge cables, water sparkle
- **Sound:** Bay wind, foghorn, runway beat, seagulls

## SkyyRose Avatar Easter Egg — THE CROWN JEWEL
- **Character:** Little Black girl, Pixar quality, big curly afro, big brown eyes
- **Reference image:** `source-products/brand-assets/skyyrose-avatar-reference.jpeg`
- **Existing mascot PNGs:** `assets/images/mascot/skyyrose-mascot-*.png`
- **Behavior:**
  - Hidden in each of the 3 worlds — user explores to find her
  - Found → she animates to life (waves, giggles, spins)
  - Find all 3 → full-screen intro: "Hi! I'm SkyyRose!" — her debut
  - Changes outfit per world (Love Hurts tee / Oakland jersey / Signature tee)
  - Idle: breathing, blinking, shifting weight, playing with hair
  - Interaction: waving, pointing at products, dancing
- **Implementation (phased):**
  - Phase 1: Use existing mascot PNGs as animated sprites (CSS keyframes)
  - Phase 2: Generate 3D GLB model via Meshy/Tripo3D from reference → rig in Mixamo
  - Phase 3: Full Three.js AnimationMixer with bone animations

## Technical Architecture (WordPress)

### Files to Create
```
assets/js/
  three.min.js              ← Three.js R172 (CDN fallback)
  immersive-world.js        ← Core world engine (vanilla JS)
  immersive-world.min.js    ← Minified
  world-particles.js        ← Particle systems per collection
  world-audio.js            ← Howler.js-based audio manager
  world-avatar.js           ← SkyyRose avatar easter egg logic

assets/css/
  immersive-world.css       ← World UI: narrative panels, product cards, loading
  immersive-world.min.css
```

### Files to Modify
```
inc/enqueue.php             ← Register Three.js + world scripts conditionally
template-immersive-*.php    ← Output world config as JSON, load world engine
```

### How It Works
1. PHP template outputs `<script type="application/json" id="world-config">` with scene data
2. `immersive-world.js` reads the config, initializes Three.js Canvas
3. Scene images become textured planes at different depths (parallax layers)
4. Products placed as interactive 3D cards with raycasting for clicks
5. Scroll drives camera along a spline path through the scene
6. Particles, audio, and narrative text trigger at scroll waypoints
7. Avatar hidden in scene, clickable when found
8. Falls back to existing `immersive.js` if WebGL unavailable

### Three.js Loading Strategy
- Load Three.js from CDN with local fallback: `three.module.min.js` (R172)
- Use ES module imports in the world script
- Feature-detect WebGL: no WebGL = graceful fallback to 2D immersive
- Lazy-load audio (Howler.js) only after user interaction (Chrome autoplay policy)

### Progressive Enhancement
- Level 0 (no JS): Static scene image + product links (SSR from PHP)
- Level 1 (no WebGL): Existing immersive.js hotspot system
- Level 2 (WebGL): Full Three.js world experience
- Level 3 (WebGL + gyroscope): Mobile tilt-to-explore

## Build Order
1. **Love Hurts** first — most emotional narrative, Beast's Cathedral, best proof of concept
2. **Black Rose** second — Bay Bridge urban scene
3. **Signature** third — Golden Gate runway
4. **Avatar** across all 3 — after worlds are built

## Session Handoff Notes
- Context7 for Three.js docs before writing: `resolve-library-id` → `query-docs`
- The existing `immersive.js` is ~400 lines of vanilla JS — study its patterns
- `skyyrose_immersive_product()` function in `inc/wc-product-functions.php` provides product data
- All scene images already in `assets/scenes/{collection}/`
- Product images in `assets/images/products/`
- The tagline at line 204 of CollectionExperience.tsx says "Where Love Meets Luxury" — WRONG, fix to "Luxury Grows from Concrete."
