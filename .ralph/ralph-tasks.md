# Ralph Tasks — Composite Products Into Scenes

## INSTRUCTIONS
- Use the 6-stage compositor pipeline for ALL compositing
- Agent: `skyyrose/elite_studio/agents/compositor_agent.py`
- Config: `skyyrose/elite_studio/config.py`
- Pipeline: BRIA RMBG → Opus Prompt → IC-Light → FLUX Fill → Shadows → Gemini QA
- Output composites to `assets/scenes/{collection}/`
- Naming: `{scene-name}-v2-{sku}.webp`
- Skip any that already exist as v2 composites
- Mark tasks [x] when done

## EXISTING v2 COMPOSITES (SKIP THESE)
- Black Rose: br-001, br-002, br-004, br-006 (4 done)
- Love Hurts: lh-001, lh-003, lh-005 (3 done)
- Signature: sg-005, sg-007, sg-011, sg-012 (4 done)

---

## Black Rose — 4 products remaining
Scene: `assets/scenes/black-rose/black-rose-rooftop-garden-v2.webp`

- [x] br-003 (Baseball Jerseys) into rooftop garden
- [x] br-005 (Hoodie+Jogger Set) into rooftop garden
- [x] br-007 (Shorts) into rooftop garden
- [x] br-008 (Dress) into rooftop garden

## Love Hurts — 2 products remaining
Scene: `assets/scenes/love-hurts/love-hurts-cathedral-rose-chamber-v2.webp`

- [x] lh-002 (Joggers) into cathedral
- [x] lh-004 (Varsity Jacket) into cathedral

## Signature — 7 products remaining
Scene: `assets/scenes/signature/signature-golden-gate-showroom-v2.webp`

- [x] sg-002 (Mint Tee) into showroom
- [x] sg-003 (Crop Hoodie) into showroom
- [x] sg-004 (Mint Hoodie) into showroom
- [x] sg-006 (Tie-Dye Crewneck) into showroom
- [x] sg-008 (Beanie Green) into showroom
- [x] sg-009 (Sherpa Jacket) into showroom
- [x] sg-010 (Bridge Shorts+Tees) into showroom

## Product Source Images
Base: `skyyrose/assets/images/source-products/`
- br-003: `black-rose/br-003-jersey-black-front.jpeg`
- br-005: `black-rose/br-004-005-hoodie-jogger-order-sheet.jpg`
- br-007: `black-rose/br-007-shorts-front.jpeg`
- br-008: `black-rose/br-008-dress-front.jpg`
- lh-002: `love-hurts/lh-002-joggers-white.jpeg`
- lh-004: `love-hurts/lh-004-joggers-black.jpeg`
- sg-002: `signature/sg-002-mint-tee-front.jpg`
- sg-003: `signature/sg-003-crop-hoodie-coral.jpg`
- sg-004: `signature/sg-004-mint-hoodie.jpeg`
- sg-006: `signature/sg-006-tiedye-crewneck.jpg`
- sg-008: product render in `assets/images/products/sg-008-front-model.webp`
- sg-009: `signature/sg-009-sherpa-jacket-open.jpeg`
- sg-010: `signature/sg-010-bridge-shorts-bay-bridge.jpeg`

## Product Renders (use these for compositing)
Base: `wordpress-theme/skyyrose-flagship/assets/images/products/`
All 24 SKUs have render-front, render-back, render-branding .webp files.

---

## SkyyRose Avatar Easter Egg

Reference: `skyyrose/assets/images/source-products/brand-assets/skyyrose-avatar-reference.jpeg`
Sprites: `wordpress-theme/skyyrose-flagship/assets/images/mascot/skyyrose-mascot-*.png`
Character: Little Black girl, Pixar quality, curly afro, big brown eyes.

### Composite avatar into each world scene
- [x] Composite `skyyrose-mascot-love-hurts.png` into Love Hurts cathedral scene (hidden spot — behind a column or pew)
- [x] Composite `skyyrose-mascot-black-rose.png` into Black Rose rooftop scene (hidden spot — behind a planter or railing)
- [x] Composite `skyyrose-mascot-signature.png` into Signature showroom scene (hidden spot — behind a garment rack or table)

### Add discovery logic to immersive-world.js
- [x] Add avatar as a clickable hotspot in each world (small, partially hidden)
- [x] On click: avatar animates (wave/spin CSS class), show "You found SkyyRose!" toast
- [x] Track found worlds in localStorage key `skyyrose-found-worlds`
- [x] All 3 found → fullscreen intro overlay: "Hi! I'm SkyyRose!" with mascot reference image
- [x] Add avatar CSS to `assets/css/immersive-world.css` (sprite positioning, idle animation keyframes, found animation)
