# Ralph Loop Context — FULL STACK CUSTOM THEME DEVELOPER

## Context added at 2026-02-24T17:00:00.000Z

## YOUR ROLE

Senior full-stack luxury web developer. Examine EVERY page. Upgrade EVERYTHING. Deploy to production.

---

## COLLECTION-SPECIFIC LOGOS

Each collection landing page MUST display its own collection logo in the header/hero — NOT the generic SkyyRose logo. These are now in `assets/branding/`:

- **BLACK ROSE**: `assets/branding/black-rose-logo.png` — Hyper-realistic glowing black rose on dark background. Use as the collection hero mark on `template-collection-black-rose.php` and `template-immersive-black-rose.php`
- **LOVE HURTS**: `assets/branding/love-hurts-logo.jpg` — Love Hurts collection wordmark/emblem. Use on `template-collection-love-hurts.php` and `template-immersive-love-hurts.php`
- **SIGNATURE**: `assets/branding/signature-logo.jpg` — Signature Collection logo with rose detail. Use on `template-collection-signature.php` and `template-immersive-signature.php`
- **SkyyRose Main**: `assets/branding/skyyrose-logo-animated.gif` — Animated rose gold SR monogram (41MB — MUST optimize to <2MB WebM/MP4/WebP sprite before use). Use on the homepage and pre-order page ONLY.

Every static collection page header should show: [Collection Logo] + [Collection Name] + [Tagline]
- BLACK ROSE: "Where Darkness Blooms"
- LOVE HURTS: "Passion Forged in Fire"
- SIGNATURE: "Timeless Luxury"

---

## SIGNATURE COLLECTION SCENES

The correct Signature scene images are at:
- `assets/scenes/signature/signature-waterfront-runway.png` — Bay Bridge waterfront, black marble platform, gold-lit LED display frames, glass orb case, stepped pedestals
- `assets/scenes/signature/signature-golden-gate-showroom.png` — Golden Gate sunset showroom, floor-to-ceiling windows, marble interior, gold LED trim, clothing racks

Use THESE as Signature immersive backgrounds. The props in these images are the hotspot locations.

---

## DIRECTIVE 1: EXAMINE EVERY PAGE

Read every template. Upgrade each one with modern 2026 UI/UX.

Pages: `front-page.php`, `header.php`, `footer.php`, all `template-collection-*.php`, all `template-immersive-*.php`, `template-about.php`, `template-contact.php`, `template-preorder-gateway.php`, `page-wishlist.php`, `woocommerce/single-product.php`, `woocommerce/archive-product.php`, `woocommerce/cart/cart.php`, `woocommerce/checkout/form-checkout.php`, `404.php`, `skyyrose/index.html`, `skyyrose/explore-*.html`, `skyyrose/collections.html`, `skyyrose/preorder.html`

---

## DIRECTIVE 2: MODERN UI/UX — SAME COLORS

Colors (DO NOT CHANGE): Rose Gold `#B76E79` | Gold `#D4AF37` | Crimson `#8B0000` | Dark `#0A0A0A` | Bone `#F5F5F5`

Apply globally: scroll-driven animations, smooth page transitions, micro-interactions, fluid clamp typography, editorial whitespace, glassmorphism, gradient overlays, rose-gold shimmer skeletons, staggered grid entrances, parallax depth, smooth scroll, luxury cursor, dark moody aesthetic.

---

## DIRECTIVE 3: SEAMLESS FLOW — STATIC → INTERACTIVE → PRE-ORDER

Homepage → Collection Landing → Product Gallery → Immersive 3D → Pre-Order. Every step flows. No dead ends.

Exclusive Incentive Popup: triggers on pre-order page (3s), exit intent, 60s idle. Email + phone signup. "Join the Inner Circle." 30-day cooldown cookie.

Page transitions: zoom-in to 3D, pullback to collection, slide-up to pre-order. Staggered entrances. Breadcrumbs always visible.

---

## DIRECTIVE 4: AI MODELS IN SKYYROSE BRANDING

Generate AI fashion models for product cards, homepage, collection heroes, about page, pre-order page. 100% replica garments on diverse Bay Area models. Use Gemini or HuggingFace. Always feed original product photo as reference.

Original photos in `assets/3d-models/{collection}/` (see progress.txt for full mapping).

---

## DIRECTIVE 5: 3D HOTSPOTS — PRODUCTS ON PROPS

Products ON props = clickable hotspots. Click → product card with AI model + pre-order CTA + collection link.

---

## DIRECTIVE 6: DEPLOY

WordPress → skyyrose.co | Next.js frontend → Vercel | Showroom → verify on localhost:3000

---

## DIRECTIVE 7: PRE-ORDER PAGE — THE MONEY PAGE (TOP PRIORITY)

`template-preorder-gateway.php` + `skyyrose/preorder.html` — This is the HIGHLIGHT REEL. Built to CONVERT. Combines static luxury design + interactive elements. Showcases ALL 3 collections in one cinematic scroll.

### Header
- Center the animated SkyyRose rose gold logo: `assets/branding/skyyrose-logo-animated.gif`
- **OPTIMIZE FIRST**: 41MB GIF → convert to WebM/MP4 (<2MB) or WebP sprite with CSS animation. Cannot ship 41MB to production.
- Below logo: "Where Love Meets Luxury" in Playfair Display
- Below tagline: "Exclusive Pre-Order Access" in gold (#D4AF37)

### Page Structure — Highlight Reel (scroll = story)

**Section 1: Hero (full viewport)**
- Optimized animated SR logo centered
- "Be First. Be Exclusive." headline
- Countdown timer or "Coming Soon" pulse
- CTA: "Reserve Your Pieces" → scrolls to product selection

**Section 2: BLACK ROSE Spotlight**
- Dark gothic mood, #B76E79 accent
- Collection-specific logo (`assets/branding/black-rose-logo.png`) in section header
- Left: best AI model in Black Rose hero piece | Right: 3-4 product thumbnails
- Collection story text
- Interactive: parallax on scroll, product tilt on hover
- CTA: "Pre-Order Black Rose" + "Explore Full Collection" → `/collections/black-rose`

**Section 3: LOVE HURTS Spotlight**
- Red/black passion mood, #8B0000 accent
- Collection logo (`assets/branding/love-hurts-logo.jpg`) in section header
- Mirrored layout (products left, model right)
- Interactive: hover reveals product detail flyout
- CTA: "Pre-Order Love Hurts" + "Explore Full Collection" → `/collections/love-hurts`

**Section 4: SIGNATURE Spotlight**
- Gold editorial luxury, #D4AF37 accent
- Collection logo (`assets/branding/signature-logo.jpg`) in section header
- Use Signature scene image as background (`assets/scenes/signature/signature-golden-gate-showroom.png`)
- Interactive: mini parallax depth layers or 3D preview
- CTA: "Pre-Order Signature" + "Explore Full Collection" → `/collections/signature`

**Section 5: The Selection (interactive)**
- ALL products from ALL 3 collections in filterable grid
- Filter tabs: ALL | BLACK ROSE | LOVE HURTS | SIGNATURE
- Product cards: AI model image, name, price, size selector, "Add to Pre-Order"
- Running total: "Your Pre-Order: X items — $XXX"
- Animated add-to-order micro-interaction

**Section 6: Exclusive Incentives**
- "Join the Inner Circle" — inline form (not popup, this is the dedicated section)
- Benefits: early access, exclusive discounts, limited drops, behind-the-scenes, first dibs on restocks
- Email + phone signup
- Social proof counter: "X people have already joined"
- Trust: "No spam. Unsubscribe anytime."

**Section 7: Pre-Order Form / Checkout**
- Selected items summary with thumbnails
- Name, email, phone
- Size confirmation per item
- Deposit option: "Hold your spot with $XX"
- Full payment option
- Estimated ship date
- CTA: "Complete Pre-Order" — big, bold, gold

**Section 8: Footer CTA**
- "Don't miss the drop" urgency
- Final email capture for scrollers who didn't buy
- Links to all 3 collection pages + immersive experiences

### Pre-Order Page Rules:
- Every section = different collection mood, flows as one scroll
- Scroll-driven reveals between sections
- Dark luxury throughout, each section brings its accent color
- Interactive elements: tilt, parallax, hover reveals — subtle but engaging
- Mobile: single column, sticky "Pre-Order" bar at bottom
- FAST loading: lazy load below-fold, skeleton loaders
- The animated logo sets the luxury tone immediately

---

## AFTER EACH ITERATION

1. Test: `npm test` and `pytest -v`
2. Build: `cd frontend && npm run build`
3. Commit: `feat:`, `fix:`, `style:`, `perf:`
4. Deploy: push for Vercel + update WordPress
5. Append to `.ralph/progress.txt`
