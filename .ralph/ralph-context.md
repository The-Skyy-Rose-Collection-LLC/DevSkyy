# Ralph Loop Context — FULL STACK CUSTOM THEME DEVELOPER

## Context added at 2026-02-24T16:55:00.000Z

## YOUR ROLE

Senior full-stack luxury web developer. Examine EVERY page. Upgrade EVERYTHING. Deploy to production.

---

## IMMEDIATE FIX: SIGNATURE COLLECTION SCENES

The Signature collection scenes have been updated. The CORRECT scene images are now at:

- `assets/scenes/signature/signature-waterfront-runway.png` — Bay Bridge waterfront, black marble platform floating over water, gold-lit LED display frames with hanging garments, glass orb display case, stepped marble pedestals, city skyline and Bay Bridge at night, reflective wet marble floor, warm gold ambient lighting
- `assets/scenes/signature/signature-golden-gate-showroom.png` — Golden Gate Bridge sunset showroom, floor-to-ceiling panoramic windows, black marble interior with gold LED trim lighting, clothing racks on left and right walls, marble pedestal displays, center display table, dramatic sunset sky with pink/orange/purple clouds, reflective marble floor

These are the REAL Signature scenes. Use THESE as the backgrounds for the Signature immersive experience. Update:
1. `template-immersive-signature.php` — use these as the scene backgrounds
2. `skyyrose/assets/js/config.js` — update the signature image paths
3. `skyyrose/explore-signature.html` — use these for the 3D deep dive

The props visible in these scenes are the ACTUAL hotspot locations:
**Waterfront Runway scene:**
- Glass orb display case (left) → sg-009 Red Rose Beanie + sg-010 Lavender Beanie
- Stepped marble pedestals (left row) → sg-006 Cotton Candy Tee + sg-007 Cotton Candy Shorts (folded/stacked)
- Gold-lit display frame (center, hanging white garment) → sg-002 Stay Golden Tee
- Gold-lit display frame (center, hanging dark garment) → sg-004 Signature Hoodie
- Gold-lit display frame (right) → sg-008 Crop Hoodie
- Stepped marble pedestals (right row) → sg-005 Signature Shorts + sg-001 Bay Set
- Marble platform edge displays → sg-011 + sg-012 Original Label Tees

**Golden Gate Showroom scene:**
- Left wall clothing rack → sg-004 Hoodie + sg-003 Pink Smoke Crewneck (hanging)
- Right wall clothing rack → sg-008 Crop Hoodie + sg-002 Stay Golden Tee (hanging)
- Center marble display table → sg-001 Bay Set (featured)
- Left marble pedestal → sg-009 Red Rose Beanie
- Right marble pedestal → sg-010 Lavender Beanie
- Left wall shelf (lower) → sg-005 Signature Shorts + sg-006 Cotton Candy Tee (folded)
- Right wall display → sg-007 Cotton Candy Shorts + sg-011 + sg-012 Label Tees

---

## DIRECTIVE 1: EXAMINE EVERY PAGE

Read every template in `wordpress-theme/skyyrose-flagship/` and `skyyrose/`. Understand current state. Upgrade each one.

Pages to touch:
- `front-page.php` — Homepage
- `header.php` / `footer.php` — Global chrome
- `template-collection-black-rose.php` — Black Rose catalog
- `template-collection-love-hurts.php` — Love Hurts catalog
- `template-collection-signature.php` — Signature catalog
- `template-collection-kids-capsule.php` — Kids Capsule catalog
- `template-immersive-black-rose.php` — Black Rose 3D
- `template-immersive-love-hurts.php` — Love Hurts 3D
- `template-immersive-signature.php` — Signature 3D
- `template-about.php` — Brand Story
- `template-contact.php` — Contact
- `template-preorder-gateway.php` — Pre-order
- `page-wishlist.php` — Wishlist
- `woocommerce/single-product.php` — Product detail
- `woocommerce/archive-product.php` — Shop
- `woocommerce/cart/cart.php` — Cart
- `woocommerce/checkout/form-checkout.php` — Checkout
- `404.php` — Error page
- `skyyrose/index.html` — Showroom
- `skyyrose/explore-*.html` — 3D deep dives
- `skyyrose/collections.html` — Showroom collections
- `skyyrose/preorder.html` — Showroom preorder

---

## DIRECTIVE 2: MODERN UI/UX — SAME COLORS

Keep the brand palette. Modernize everything else.

Colors (DO NOT CHANGE):
- Rose Gold: `#B76E79`
- Gold: `#D4AF37`
- Crimson: `#8B0000`
- Dark: `#0A0A0A`
- Bone: `#F5F5F5`

Modern upgrades globally:
- Scroll-driven animations (IntersectionObserver reveals)
- Smooth page transitions (crossfade, no hard flashes)
- Micro-interactions on every clickable element
- Fluid clamp-based typography
- Generous editorial whitespace
- Glassmorphism (frosted panels, blurred backdrops)
- Subtle gradient overlays and ambient glows
- Rose-gold shimmer loading skeletons
- Staggered grid entrance animations
- Parallax depth layers on scroll
- Smooth scroll globally
- Enhanced luxury cursor states
- Dark moody luxury aesthetic always

---

## DIRECTIVE 3: SEAMLESS FLOW — STATIC → INTERACTIVE → PRE-ORDER

The entire site = ONE continuous luxury experience. No dead ends. No jarring transitions.

### Customer journey (every step flows into the next):

**Homepage** → scroll reveals each collection as a chapter with teaser + CTA
↓
**Collection Landing Page** → hero + "Enter the Experience" CTA + full product gallery below
↓
**Full Product Gallery** → editorial masonry grid, AI model product cards, sticky "Pre-Order Now" CTA
↓
**Immersive 3D Scene** → products on props as hotspots, click = product card with "Pre-Order" CTA
↓
**Pre-Order Gateway** → VIP conversion page + exclusive incentive popup

### Exclusive Incentive Popup

Triggers: first visit to pre-order (3s delay), exit intent, 60s idle on collection page

Content:
- "Join the Inner Circle" / "Unlock Exclusive Access"
- Early access, limited drops, exclusive discounts, behind-the-scenes
- Email + optional phone for SMS
- Collection interest checkboxes
- CTA: "Get My Exclusive Access"
- Success: "Welcome to the Inner Circle" animation
- 30-day cookie/localStorage cooldown

Design: full-screen backdrop blur, centered card with gradient border, rose gold accent, scale+fade entrance, X/click-outside/ESC dismiss, mobile bottom sheet

### Page transitions:
- Collection → 3D: zoom-in effect
- 3D → collection: smooth pullback
- Any → pre-order: slide-up reveal
- Staggered card entrances (50ms each)
- Breadcrumbs always: Home > Collection > Product
- "Continue your journey" prompts between sections

---

## DIRECTIVE 4: AI MODELS IN SKYYROSE BRANDING — EVERYWHERE

Generate AI fashion models for ALL website content using Gemini (`build/generate-fashion-models.js`) or HuggingFace Spaces.

### Where AI models go:

1. **Product Cards** — AI model WEARING the product (100% replica garment)
2. **Homepage Hero** — Models in SkyyRose branded looks for each collection teaser
3. **Collection Landing Heroes** — Cinematic model shots per collection mood
4. **About Page** — Editorial lifestyle shots, Oakland/Bay Area community
5. **Pre-Order Page** — Models in upcoming drops, "Be the first" imagery
6. **3D Scene Hotspot Modals** — Model wearing the product when you click a hotspot

### AI Generation Rules:
- ALWAYS feed original product photo as reference input
- Garment on model = 100% REPLICA (same colors, embroidery, logos, fabric, details)
- Diverse models: different genders, body types, ethnicities — Bay Area representation
- Collection moods:
  - BLACK ROSE: gothic, moody, cathedral/garden, silver moonlight
  - LOVE HURTS: passionate, raw, Oakland streets, dramatic red lighting
  - SIGNATURE: editorial, high fashion, Bay Area skyline, golden hour
- All branded with subtle SkyyRose logo
- High-res PNG output

### Original product photos (reference inputs):

**BLACK ROSE** (`assets/3d-models/black-rose/`):
br-001 Crewneck: `PhotoRoom_000_20230616_170635.png` | br-002 Joggers: `PhotoRoom_003_20230616_170635.jpeg` | br-003 Jersey: `5A8946B1-B51F-4144-BCBB-F028462077A0.jpg` | br-004 Hoodie: `Photo Dec 18 2023, 6 09 21 PM (1).png` | br-006 Sherpa: `The BLACK Rose Sherpa.jpg` + `The BLACK Rose Sherpa Back.jpg` | br-008 Hooded Dress: `Womens Black Rose Hooded Dress.jpeg`

**LOVE HURTS** (`assets/3d-models/love-hurts/`):
lh-001 Fannie: `The FANNIE Pack.jpg` | lh-002 Joggers: `_Love Hurts Collection_ Sincerely Hearted Joggers (Black).jpg` | lh-003 Shorts: `PhotoRoom_002_20221110_201626.png` | lh-004 Varsity: `Men windbreaker jacket (1).png`

**SIGNATURE** (`assets/3d-models/signature/`):
sg-001 Bay Set: `Photo Sep 20 2022, 7 56 54 PM.jpg` | sg-002 Stay Golden Tee: `Stay Golden Tee.jpg` | sg-003 Pink Smoke Crewneck: `The Pink Smoke Crewneck.jpg` | sg-004 Hoodie: `_Signature Collection_ Hoodie.jpg` | sg-005 Shorts: `The Signature Shorts.jpg` | sg-006 Cotton Candy Tee: `_Signature Collection_ Cotton Candy Tee.jpg` | sg-007 Cotton Candy Shorts: `_Signature Collection_ Cotton Candy Shorts.jpg` | sg-008 Crop Hoodie: `_Signature Collection_ Crop Hoodie front.jpg` | sg-009 Red Rose Beanie: `Signature Collection Red Rose Beanie.jpg` | sg-010 Lavender Beanie: `_Signature Collection_ Lavender Rose Beanie.jpg` | sg-011 Label Tee White: `_Signature Collection_ Original Label Tee (White).jpg` | sg-012 Label Tee Orchid: `_Signature Collection_ Original Label Tee (Orchid).jpg`

---

## DIRECTIVE 5: 3D HOTSPOTS — PRODUCTS ON PROPS

Products go ON the props visible in the scene images, not floating in air.

Product on prop = the clickable hotspot. Product image = 100% replica.
Click → product card with AI model + description + pre-order CTA + collection link.

**THE GARDEN (Black Rose):**
Stone bench → br-006 Sherpa | Rose arbor → br-001 Crewneck | Gothic mirror → br-008 Hooded Dress | Stone steps → br-002 Joggers | Iron gate → br-004 Hoodie | Pedestal → br-003 Jersey

**THE BALLROOM (Love Hurts):**
Velvet chaise → lh-004 Varsity | Gold frame → lh-002 Joggers | Marble table → lh-001 Fannie | Dress rack → lh-003 Shorts

**THE RUNWAY (Signature) — see scene images above for exact prop locations**

---

## DIRECTIVE 6: DEPLOY TO PRODUCTION

### WordPress Theme → skyyrose.co
1. Test templates locally
2. Push to repo
3. Deploy to WordPress.com / skyyrose.co
4. Verify: `curl -I https://skyyrose.co | grep content-security-policy`
5. Test WooCommerce cart/checkout

### Next.js Frontend → Vercel (DevSkyy)
1. `cd frontend && npm run build` — zero errors
2. Deploy: `vercel deploy --prod` or push to trigger auto-deploy
3. Verify routes: /admin, /collections/[slug], /login
4. Check health: `/api/monitoring/health`

### Showroom → localhost:3000
1. `npm run dev` — verify rooms, hotspots, modals
2. `node api/assistant.js` — verify Claude assistant on :3001
3. `npm run verify` — 82-check production verification

### Post-Deploy:
- [ ] All pages load, no console errors
- [ ] AI model images display everywhere
- [ ] Pre-order flow works end-to-end
- [ ] Incentive popup triggers and captures email
- [ ] WooCommerce cart + checkout works
- [ ] Mobile responsive all pages
- [ ] 3D scenes load with correct scene images
- [ ] All hotspots interactive
- [ ] Collection links route correctly
- [ ] No broken images, no 404s, no dead ends

---

## AFTER EACH ITERATION

1. Test: `npm test` and `pytest -v`
2. Build: `cd frontend && npm run build`
3. Commit: `feat:`, `fix:`, `style:`, `perf:`
4. Deploy: push for Vercel + update WordPress
5. Append to `.ralph/progress.txt`
