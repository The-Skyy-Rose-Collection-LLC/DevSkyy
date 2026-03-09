# Ralph Tasks — Immersive Worlds Build

## INSTRUCTIONS
- Update this file AFTER EVERY ITERATION with progress
- Mark tasks [x] when complete, [/] when in progress, [ ] when pending
- Add notes about what was done and any decisions made
- NEVER DELETE THIS FILE
- Read `IMMERSIVE-WORLDS-PLAN.md` and `.ralph/ralph-context.md` EVERY iteration
- Pre-order products (br-d01–d04, sg-d01, sg-d02) are EXCLUDED from all phases

---

## PHASE 0: Asset Inventory & Gap Analysis

- [x] Audit existing product renders in `wordpress-theme/skyyrose-flagship/assets/images/products/`
  - **ACTUAL: 372 files** across current SKUs + pre-order + sources + references
  - Verified each CURRENT product for: front-model, back-model, branding + render-front, render-back, render-branding
  - **COMPLETE (no gaps in core trio):** br-001, br-002, br-003, br-004, br-005, br-006, br-008, lh-002, lh-003, lh-004, lh-005, sg-002, sg-009, sg-010, sg-011, sg-012 (16/24 SKUs)
  - **GAPS FOUND (19 missing files across 8 SKUs):**
    - `br-007` (Shorts): MISSING render-front, render-back, render-branding (has front-model, back-model, branding)
    - `lh-001` (Fannie Pack): MISSING back-model, render-front, render-back, render-branding (has front-model, branding)
    - `sg-003` (Crop Hoodie): MISSING render-front, render-back, render-branding (has front-model, back-model, branding)
    - `sg-004` (Mint Hoodie): MISSING render-front, render-back, render-branding (has front-model, back-model, branding)
    - `sg-005` (Bay Rose Set): MISSING render-front (has render-back, render-branding, front-model, back-model, branding)
    - `sg-006` (Tie-Dye Crewneck): MISSING branding (has render-front, render-back, render-branding, front-model, back-model)
    - `sg-007` (Beanie Black): MISSING back-model (has front-model, branding, render-front, render-back, render-branding)
    - `sg-008` (Beanie Green): MISSING render-front, render-back, render-branding (has front-model, back-model, branding)
  - **ORPHAN FILES:** sg-001 has 9 files but sg-001 is NOT a current SKU
  - **NOTE:** sg-008 has misnamed crop-hoodie files (sg-008-crop-hoodie.webp, sg-008-crop-hoodie-back.webp) — sg-008 is Beanie, not crop hoodie
  - **NON-PRODUCT FILES:** patches (3), references (2), pre-order designs (br-d02–d04, sg-d01–d04), po-* pre-order renders, techflats, source jpgs
- [x] Audit existing scenes in `assets/scenes/{collection}/`
  - **TOTALS: Black Rose: 21 files, Love Hurts: 26 files (+ 1 dome jpg), Signature: 16 files = 63 total**

  ### BLACK ROSE — 21 files (5 base scenes)
  - **HERO: `black-rose-rooftop-garden-v2`** (.png + .webp) — ✅ PRODUCTION READY
    - Bay Bridge lit up ✓, night ✓, concrete floor ✓, black rose planters ✓, fog ✓, pendant lights ✓
    - Has: depth map, pipeline-v1, 4 v2-composites, 4 lookbooks
  - `black-rose-moonlit-courtyard` (.jpg + .png + .webp) — Gothic courtyard, statues, fountains, black rose topiary. NO Bay Bridge.
  - `black-rose-iron-gazebo-garden` (.png + .webp) — Iron gazebo in rose garden, aerial view. NO Bay Bridge.
  - `black-rose-marble-rotunda` (.png + .webp) — Indoor marble rotunda, black tree, crimson accents. NO Bay Bridge.
  - `black-rose-white-rose-grotto` (.png + .webp) — Underground grotto, white roses, marble pedestal. NO Bay Bridge.
  - **v2 Composites (4/8 products done):** br-001 ✓, br-002 ✓, br-004 ✓, br-006 ✓
  - **MISSING composites:** br-003 (Jerseys), br-005 (Set), br-007 (Shorts), br-008 (Dress)
  - **Depth maps:** hero only — need 4 more for other scenes
  - **VERDICT:** Hero matches key notes perfectly. Other 4 scenes map to world plan stages (courtyard→gazebo→rotunda→grotto) but lack Oakland-specific anchors. Acceptable as progression into "hidden gardens." Need composites for 4 products + depth maps for 4 scenes.

  ### LOVE HURTS — 26 files (7 base scenes — MOST COMPLETE)
  - **HERO: `love-hurts-cathedral-rose-chamber-v2`** (.png + .webp) — ✅ PRODUCTION READY
    - Gothic cathedral ✓, enchanted rose under glass dome ✓, stained glass crimson ✓, candelabras ✓, petals ✓, products placed ✓
    - Has: depth map, pipeline-v1, 3 v2-composites, 3 lookbooks
  - `love-hurts-gothic-ballroom` — Dark ballroom, enchanted rose dome, shattered items, blue moonlight. "Beast danced alone" ✓
  - `love-hurts-crimson-throne-room` — Beast figure in cape (back turned), ornate throne, petal-covered floor. Beast's POV ✓
  - `love-hurts-enchanted-rose-shrine` — Beast in crimson cape gazing at rose in golden frame. Private grief ✓
  - `love-hurts-giant-rose-staircase` — Massive rose growing from baroque staircase, thorny vines. Ascension ✓
  - `love-hurts-reflective-ballroom` — Mirror floor, rose reflected, stained glass dome. Self-reflection ✓
  - `love-hurts-enchanted-rose-dome.jpg` (57KB) + 3 dome reference jpgs (49-66KB each) — TOO SMALL for production
  - **ALL 7 world scenes match the scroll plan exactly:**
    - 0.0–0.15: cathedral-rose-chamber ✓ | 0.15–0.30: gothic-ballroom ✓ | 0.30–0.45: crimson-throne-room ✓
    - 0.45–0.55: enchanted-rose-shrine ✓ | 0.55–0.70: giant-rose-staircase ✓ | 0.70–0.85: reflective-ballroom ✓
    - 0.85–1.0: enchanted-rose-dome (exists but LOW-RES — needs high-quality regeneration)
  - **v2 Composites (3/5 products done):** lh-001 ✓, lh-003 ✓, lh-005 ✓
  - **MISSING composites:** lh-002 (Joggers), lh-004 (Varsity Jacket)
  - **Depth maps:** hero only — need 6 more for other scenes
  - **CRITICAL:** Scenes 4+5 show Beast silhouette — matches "from BEAST's perspective" perfectly ✓
  - **VERDICT:** Best-covered collection. All 7 stages exist. Need composites for 2 products + 6 depth maps + high-res dome scene.

  ### SIGNATURE — 16 files (2 base scenes — LEAST COMPLETE)
  - **HERO: `signature-golden-gate-showroom-v2`** (.png + .webp) — ✅ PRODUCTION READY
    - Golden Gate Bridge (red/orange) visible through windows ✓, golden hour ✓, marble showroom ✓, fog ✓
    - Has: depth map, pipeline-v1, 4 v2-composites, 4 lookbooks
  - `signature-waterfront-runway` (.png + .webp) — Waterfront runway platform, golden light, products on pedestals.
    - **KEY NOTES ISSUE:** Bridge in background appears to be Bay Bridge, NOT Golden Gate. May need regeneration.
  - **v2 Composites (4/11 products done):** sg-005 ✓, sg-007 ✓, sg-011 ✓, sg-012 ✓
  - **MISSING composites:** sg-002, sg-003, sg-004, sg-006, sg-008, sg-009, sg-010 (7 products!)
  - **Depth maps:** hero only — need 1+ more
  - **World plan needs 5 scenes** (showroom→runway→bridge walkway→fog pier→sunset deck) — **MISSING 3 scene backgrounds**
  - **VERDICT:** Least complete. Only 2/5 stages exist. Need 3 new scene backgrounds + 7 composites + depth maps.

  ### SUMMARY — What Needs Work Before Phase 1
  | Collection | Base Scenes | Match Key Notes? | Composites Done | Composites Needed | Depth Maps |
  |-----------|------------|-----------------|----------------|------------------|-----------|
  | Black Rose | 5/5 | Hero ✓, others partial | 4/8 | 4 more | 1/5 |
  | Love Hurts | 7/7 (dome low-res) | ALL match ✓ | 3/5 | 2 more | 1/7 |
  | Signature | 2/5 | Hero ✓, runway questionable | 4/11 | 7 more | 1/2 |

  **Phase 1 Decision:** Hero scenes (v2) are strong for all 3. But:
  - Phase 1 task says "Generate 1 hero scene per collection" — heroes ALREADY EXIST and pass visual QA
  - The real gaps are: depth maps, missing product composites, and Signature's missing 3 scenes
  - Love Hurts dome scene needs high-res regeneration for the climax stage
- [ ] Fill render gaps for any current products missing render variants
  - Read `HANDOFF.md` for rendering-critical details (rose fill patterns, text placement, patches)
  - Use `gemini-2.5-flash-image` as primary, `FLUX.2-pro` for editorial quality
  - Script: `scripts/nano-banana-vton.py` | Venv: `.venv-imagery/`

---

## PHASE 1: Scene Regeneration (KEY NOTES EMPHASIS)

Regenerate ALL scene backgrounds to nail the specific world narratives.
Use Opus to craft prompts → Gemini 3 Pro (`gemini-3-pro-image-preview`) or FLUX.2 Pro for generation.
Output: `assets/scenes/{collection}/` replacing or versioning existing backgrounds.

### 1A: Black Rose — "The Bay Bridge" (Oakland/East Bay)

**KEY NOTES:**
- BAY BRIDGE visible (Oakland/East Bay side — NOT Golden Gate)
- Street luxury — concrete, iron, urban grit meets elegance
- "Luxury Grows from Concrete" — the tagline IS the vibe
- East Bay pride — Oakland skyline, waterfront, industrial beauty
- Night/twilight mood — city lights, fog rolling in from the bay
- Black roses growing from cracks, iron, concrete

**Generate 1 hero scene:**
- [ ] Oakland rooftop garden at night, Bay Bridge lit up in background, black rose garden with iron planters and concrete floor, city lights below, fog from bay, luxury meets street — wide panoramic composition with MULTIPLE natural product placement locations (hooks, surfaces, mannequins, display ledges, draped on railings)

### 1B: Love Hurts — "The Beast's Cathedral"

**THE STORY: Beauty and the Beast — told from the BEAST's perspective.**
The enchanted rose under the glass dome is THE symbol — his countdown, his hope, his curse.
Beast's castle — gothic cathedral, thorns, candlelight, crimson, isolation.
NO Belle visible — HIS world, HIS perspective.

**Products (5 — ONLY these):**
- lh-001: Fannie Pack
- lh-002: Joggers (White + Black)
- lh-003: Shorts
- lh-004: Varsity Jacket
- lh-005: Bomber/Varsity Jacket

**Generate 1 hero scene:**
- [ ] Beast's grand cathedral chamber — enchanted rose under glass dome as centerpiece, gothic architecture, stained glass with crimson light, vaulted ceilings, candlelight, thorned rose vines on stone columns, scattered petals on marble floor, Beast's throne in shadow — wide composition with MULTIPLE natural product placement spots (draped on throne, hung on iron candelabras, laid on stone altar, displayed on carved pedestals, folded on cathedral pew)

### 1C: Signature — "The Golden Gate Runway"

**KEY NOTES:**
- GOLDEN GATE BRIDGE (San Francisco side — NOT Bay Bridge)
- High fashion meets Bay Area — bridge between street and luxury
- Golden hour lighting, fog through cables, cinematic

**Products (11 — ONLY these):**
- sg-002: Mint Tee
- sg-003: Crop Hoodie
- sg-004: Mint Hoodie
- sg-005: Bay Rose Set
- sg-006: Tie-Dye Crewneck
- sg-007: Beanie (Black)
- sg-008: Beanie (Forest Green)
- sg-009: Sherpa Jacket
- sg-010: Bridge Shorts + Matching Tees
- sg-011: Premium Tee (White)
- sg-012: Premium Tee (Orchid)

**Generate 1 hero scene:**
- [ ] Golden Gate showroom/runway — luxury space overlooking Golden Gate Bridge at golden hour, fog, fashion displays — wide composition with natural product placement spots throughout

### 1D: Quality Gate

- [ ] ALL regenerated scenes pass through Gemini 3 Pro visual QA
- [ ] Verify key notes are present in each scene (bridge visible? right bridge? mood correct?)
- [ ] Generate depth maps for each scene (`-depth-enhanced.png` for parallax)
- [ ] Regenerate any scenes that fail QA with refined prompts

---

## PHASE 2: Scene Compositing (Products INTO Scenes)

Agent: `skyyrose/elite_studio/agents/compositor_agent.py`
Pipeline: BRIA RMBG → Opus Prompt → IC-Light → FLUX Fill → Shadows → Gemini QA

### 2A: ONE Hero Scene Per Collection

Generate 1 scene per collection that perfectly captures the world's vision.
Then composite ALL of that collection's products into the scene — placed at
different natural locations throughout (hung on hooks, draped on furniture,
worn by figures, laid on surfaces, displayed on racks). The 6-stage pipeline
(BRIA → Opus → IC-Light → FLUX Fill → Shadows → Gemini QA) ensures each
product looks like it BELONGS there — correct lighting, shadows, perspective.

- [ ] **Black Rose** — 1 scene, 8 products: br-001, br-002, br-003, br-004, br-005, br-006, br-007, br-008
- [ ] **Love Hurts** — 1 scene, 5 products: lh-001, lh-002, lh-003, lh-004, lh-005
- [ ] **Signature** — 1 scene, 11 products: sg-002, sg-003, sg-004, sg-005, sg-006, sg-007, sg-008, sg-009, sg-010, sg-011, sg-012

### 2B: Run Compositor Pipeline

- [ ] Run 6-stage compositor for each scene×product combo
  - Skip combos that already have passing v2 composites
  - Rate limit: `COMPOSITOR_STAGE_DELAY = 2` seconds between stages
  - Output to `editorial-staging/{collection}/` then copy finals to `assets/scenes/`
- [ ] All outputs must pass Gemini QA gate (Stage 6)
  - Re-run failures with adjusted Opus prompts
- [ ] Organize finals: `{scene-name}-{sku}.webp` naming convention

---

## PHASE 3: Love Hurts World (BUILD FIRST)

Theme: Beauty and the Beast from BEAST's perspective. Gothic cathedral, enchanted rose dome.

### 3A: World Config JSON

- [ ] Create Love Hurts world config for `<script id="world-config">`:
  ```
  {
    "collection": "love-hurts",
    "scenes": [cathedral, ballroom, throne, shrine, staircase, reflective, dome],
    "layers": [{ scene image, depth map, z-position, parallax factor }...],
    "products": [{ sku, name, price, image, position, scene }...],
    "camera": { waypoints along spline through 7 scenes },
    "particles": { crimson petals, candle flicker, dust beams, heartbeat pulse },
    "narrative": [{ scroll %, text, position }...],
    "audio": { cathedral echo, music box, heartbeat, dripping water },
    "avatar": { position, sprite, trigger }
  }
  ```
- [ ] Map scroll progress (0→1) to camera waypoints through 7 scenes
  - 0.0–0.15: Cathedral rose chamber (enchanted rose intro)
  - 0.15–0.30: Gothic ballroom (Beast danced alone)
  - 0.30–0.45: Crimson throne room (isolation, power)
  - 0.45–0.55: Enchanted rose shrine (tenderness, private grief)
  - 0.55–0.70: Giant rose staircase (ascension, thorns thicken)
  - 0.70–0.85: Reflective ballroom (self-reflection, beauty in decay)
  - 0.85–1.0: Enchanted rose dome (climax — last petal falls)
- [ ] Define narrative text panels — Beast's inner monologue:
  - "She never saw the thorns I grew to protect myself..."
  - "Every petal that falls is a day closer to forever alone..."
  - "The ballroom remembers her laughter. I remember the silence after."
  - "Love doesn't hurt. Loving without being seen hurts."
  - "The rose was never the curse. Hope was."
- [ ] Map products to interactive hotspot positions within each scene
  - Products appear as floating cards that reveal on hover/scroll proximity

### 3B: PHP Template

- [ ] Update `template-immersive-love-hurts.php`:
  - [ ] Add `<div id="world-canvas">` container for Three.js
  - [ ] Add `<script type="application/json" id="world-config">` with config from 3A
  - [ ] Output composited scene images as data for parallax layers
  - [ ] Keep existing room data arrays as fallback for non-WebGL browsers
  - [ ] Use `skyyrose_immersive_product()` helper for product data

### 3C: CSS

- [ ] Create `assets/css/immersive-world.css`:
  - World canvas: full viewport, fixed position behind content
  - Narrative panels: glassmorphism overlays, crimson accents, triggered by scroll
  - Product hotspot cards: hover reveal with price + "Add to Cart"
  - Loading screen: enchanted rose petal animation
  - Mobile responsive breakpoints
- [ ] Register in `inc/enqueue.php` for immersive templates

### 3D: Verify & Test

- [ ] `php -l template-immersive-love-hurts.php`
- [ ] `node --check assets/js/immersive-world.js`
- [ ] Test with wp-playground skill
- [ ] Verify fallback works when WebGL disabled
- [ ] Fix all errors before moving on

---

## PHASE 4: Black Rose World

Theme: BAY BRIDGE (Oakland/East Bay). Street luxury. "Luxury Grows from Concrete."

### 4A: World Config JSON

- [ ] Create Black Rose config:
  - 5 scenes: rooftop-garden → courtyard → gazebo → rotunda → grotto
  - Products: br-001 through br-008 (current only, no pre-order)
  - Particles: black rose petals, fog from water, city light bokeh
  - Audio: bay water, distant BART, urban night ambience
  - Camera path: rooftop overlooking Bay Bridge → descent through garden scenes → grotto reveal
  - Narrative: Oakland story — concrete to luxury, streets to roses, East Bay pride
  - Scroll deeper = deeper into Oakland's hidden gardens

### 4B: PHP Template

- [ ] Update `template-immersive-black-rose.php` with world canvas + config
- [ ] Map 8 current products to scene positions

### 4C: Verify & Test

- [ ] Syntax checks (php -l, node --check)
- [ ] wp-playground test
- [ ] Fix all errors

---

## PHASE 5: Signature World

Theme: GOLDEN GATE BRIDGE (SF). Fashion runway over the bay.

### 5A: World Config JSON

- [ ] Create Signature config:
  - 5 scenes: showroom → runway → bridge walkway → fog pier → sunset deck
  - Products: sg-002 through sg-012 (11 products)
  - Particles: golden hour lens flare, fog through cables, water sparkle
  - Audio: bay wind, foghorn, runway beat, seagulls
  - Camera path: showroom → out to bridge → walkway → pier → sunset finale
  - Narrative: Bridge between street and luxury, Bay Area fashion capital

### 5B: PHP Template + Verify

- [ ] Update `template-immersive-signature.php`
- [ ] Syntax checks + wp-playground test
- [ ] Fix all errors

---

## PHASE 6: SkyyRose Avatar Easter Egg

Hidden animated character across ALL 3 worlds.

### 6A: Sprite Setup

- [ ] Use existing mascot PNGs at `assets/images/mascot/skyyrose-mascot-*.png` (7 poses)
- [ ] Create CSS sprite animation keyframes (idle: breathing, blinking, weight shift)
- [ ] Define hidden positions in each world (tucked behind scene elements)
- [ ] Different outfit per world (LH tee / Oakland jersey / Signature tee)

### 6B: Discovery Logic

- [ ] Add to `immersive-world.js`:
  - Raycasting hit detection for avatar sprite
  - Found animation: waves, giggles, spins
  - Track discoveries in localStorage
  - All 3 found → full-screen intro: "Hi! I'm SkyyRose!" with character animation

### 6C: Verify

- [ ] Test discovery flow across all 3 worlds
- [ ] Verify localStorage persistence
- [ ] Test mobile touch interaction

---

## PHASE 7: Audio & Polish

- [ ] Create `assets/js/world-audio.js` — Howler.js audio manager
  - Lazy load after user interaction (Chrome autoplay policy)
  - Per-world ambient tracks + scroll-triggered sound effects
  - Volume fade based on scroll position
- [ ] Create `assets/js/world-particles.js` — particle system presets per collection
- [ ] Mobile gyroscope support (DeviceOrientationEvent for tilt-to-explore)
- [ ] Performance optimization: LOD, texture compression, lazy loading
- [ ] Final cross-browser testing

---

## REFERENCE: Pipeline Priority

1. **Compositor Agent** — scene compositing (products INTO scenes)
2. **Nano Banana** — standalone product renders (model shots)
3. **FLUX Orchestrator** — end-to-end product launch (generate → CDN → WP)

## REFERENCE: Key Files

- Engine: `wordpress-theme/skyyrose-flagship/assets/js/immersive-world.js`
- Fallback: `assets/js/immersive.js` (existing 2D hotspot system)
- Templates: `template-immersive-{black-rose,love-hurts,signature}.php`
- Enqueue: `inc/enqueue.php` (world script registered)
- Products: `skyyrose_immersive_product()` in `inc/wc-product-functions.php`
- Scenes: `assets/scenes/{collection}/`
- Source images: `skyyrose/assets/images/source-products/`
- Compositor: `skyyrose/elite_studio/agents/compositor_agent.py`
- Config: `skyyrose/elite_studio/config.py`
- Nano Banana: `scripts/nano-banana-vton.py`
- Plan: `wordpress-theme/skyyrose-flagship/IMMERSIVE-WORLDS-PLAN.md`
- Handoff: `skyyrose/assets/images/source-products/HANDOFF.md`

## REFERENCE: Product Source Photos (for rendering & compositing)

Base path: `skyyrose/assets/images/source-products/`

### Black Rose Collection (`black-rose/`)
| SKU | Product | Source Files |
|-----|---------|-------------|
| br-001 | Crewneck | `br-001-crewneck-front.jpeg`, `br-001-crewneck-front-hq.png` |
| br-002 | Joggers | `br-002-joggers-front.jpeg` |
| br-003 | Baseball Jerseys | `br-003-jersey-black-front.jpeg`, `br-003-jersey-giants-front.jpeg`, `br-003-jersey-white-front.jpeg`, `br-003-oakland-jersey-front.jpeg`, `br-003-oakland-jersey-back.jpeg` |
| br-004 | Hoodie (rose sleeve) | `br-004-hoodie-front.jpeg`, `br-004-005-hoodie-jogger-order-sheet.jpg`, `br-004-hoodie-jogger-set-specs.jpg` |
| br-005 | Hoodie+Jogger Set | `br-004-005-hoodie-jogger-order-sheet.jpg`, `br-004-hoodie-jogger-white-order-sheet.jpg` |
| br-006 | Sherpa Jacket | `br-006-sherpa-jacket-front.jpeg`, `br-006-sherpa-jacket-back.jpeg`, `br-006-sherpa-jacket-open.jpeg` |
| br-007 | Shorts | `br-007-shorts-front.jpeg`, `br-007-shorts-back-detail.jpeg`, `br-007-shorts-back-hanger.jpeg`, `br-007-shorts-side.jpeg` |
| br-008 | Dress | `br-008-dress-front.jpg` |

### Love Hurts Collection (`love-hurts/`)
| SKU | Product | Source Files |
|-----|---------|-------------|
| lh-001 | Fannie Pack | `lh-001-fannie-front.jpeg`, `lh-001-fannie-back.jpeg`, `lh-001-fannie-angled.jpeg` |
| lh-002 | Joggers (White+Black) | `lh-002-joggers-white.jpeg`, `lh-002-joggers-white-alt.jpeg` |
| lh-003 | Shorts | `lh-003-shorts-front.jpeg`, `lh-003-shorts-back.jpeg`, `lh-003-shorts-techflat-allover.jpg`, `lh-003-shorts-techflat-v1.jpg` |
| lh-004 | Varsity Jacket | `lh-004-joggers-black.jpeg` (NOTE: filename mismatch — this is the varsity jacket ref) |
| lh-005 | Bomber/Varsity | `lh-005-bomber-front.jpeg`, `lh-005-bomber-interior.jpeg`, `lh-005-varsity-jacket-techflat.jpg`, `lh-005-varsity-jacket-white-techflat.jpg`, `lh-005-varsity-purple-techflat.jpg` |

### Signature Collection (`signature/`)
| SKU | Product | Source Files |
|-----|---------|-------------|
| sg-002 | Mint Tee | `sg-002-mint-tee-front.jpg` |
| sg-003 | Crop Hoodie | `sg-003-crop-hoodie-coral.jpg` |
| sg-004 | Mint Hoodie | `sg-004-mint-hoodie.jpeg` |
| sg-005 | Bay Rose Set | `sg-005-bay-rose-combo-real.jpg`, `sg-005-bay-rose-set-techflat.jpg`, `sg-005-bay-rose-tee-blue.jpeg`, `sg-005-bay-rose-tee-purple.jpeg` |
| sg-006 | Tie-Dye Crewneck | `sg-006-tiedye-crewneck.jpg` |
| sg-009 | Sherpa Jacket | `sg-009-sherpa-jacket-open.jpeg`, `sg-009-sherpa-jacket-embroidery-closeup.jpeg`, `sg-009-sherpa-jacket-lining-detail.jpeg` |
| sg-010 | Bridge Shorts | `sg-010-bridge-shorts-bay-bridge.jpeg`, `sg-010-bridge-shorts-golden-gate.jpeg` |
| sg-011 | Premium Tee (White) | `sg-011-premium-tee-white.jpeg`, `sg-011-012-tees-with-tags.jpg` |
| sg-012 | Premium Tee (Orchid) | `sg-012-premium-tee-orchid.jpeg`, `sg-011-012-tees-with-tags.jpg` |
| sg-007 | Beanie (Black) | Real product photo in `assets/images/products/` |
| sg-008 | Beanie (Forest Green) | Real product photo in `assets/images/products/` |

### Brand Assets (`brand-assets/`)
| Asset | File | Notes |
|-------|------|-------|
| Authentication Patches | `patch-mlb-baseball.jpeg`, `patch-nfl-football.jpeg`, `patch-nba-basketball.jpeg`, `patch-hockey-championship.jpeg` | Sleeve patches for BR jerseys |
| Brand Art | `rose-from-concrete-art.jpg` | "Luxury Grows from Concrete" art |
| Tags & Labels | `skyyrose-tags-labels.jpg` | Product tag reference |
| **SkyyRose Avatar** | **`skyyrose-avatar-reference.jpeg`** | **THE character reference — little Black girl, Pixar quality, curly afro, big brown eyes** |

## REFERENCE: SkyyRose Avatar / Mascot Sprites

Base path: `wordpress-theme/skyyrose-flagship/assets/images/mascot/`

| File | Use |
|------|-----|
| `skyyrose-mascot-reference.png` | Master reference pose |
| `skyyrose-mascot-homepage.png` | Homepage idle pose |
| `skyyrose-mascot-black-rose.png` | Black Rose world outfit |
| `skyyrose-mascot-love-hurts.png` | Love Hurts world outfit |
| `skyyrose-mascot-signature.png` | Signature world outfit |
| `skyyrose-mascot-preorder.png` | Pre-order page pose |
| `skyyrose-mascot-404.png` | 404 page pose |
| `skyy-idle.png` | Idle animation frame |
| `mascot-fallback.svg` | SVG fallback |

**Avatar reference image**: `skyyrose/assets/images/source-products/brand-assets/skyyrose-avatar-reference.jpeg`
Character: Little Black girl, Pixar quality, curly afro, big brown eyes. Changes outfit per world.
Hidden in each world → find all 3 → full-screen intro: "Hi! I'm SkyyRose!"
