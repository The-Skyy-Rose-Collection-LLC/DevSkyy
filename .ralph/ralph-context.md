# RALPH — DIRECTIVE PRIORITIES

## ARCHITECTURE — READ THIS FIRST

| System | URL | Stack | Purpose |
|--------|-----|-------|---------|
| **skyyrose.co** | skyyrose.co | WordPress PHP (`wordpress-theme/skyyrose-flagship/`) | Customer-facing flagship website |
| **devskyy.app** | devskyy.app | Next.js (`frontend/`) | Internal admin dashboard |

**PRIORITY ORDER:** skyyrose.co FIRST, devskyy.app SECOND. The website is what customers see. The dashboard supports it.

---

## DIRECTIVE 1: SKYYROSE.CO — WORDPRESS FLAGSHIP (HIGHEST PRIORITY)

### 1A. Connect Conversion Engines to Dashboard Analytics

The 11 conversion engines are BUILT and WORKING in the WordPress theme. But they do NOT send events anywhere.

**DO THIS:**
- In `assets/js/analytics-beacon.js` — wire up event relay to POST to `https://devskyy.app/api/conversion`
- Every engine should fire events via the beacon: `hotspot_click`, `room_transition`, `panel_open`, `add_to_cart`, `product_view`, `scroll_depth`, `time_on_page`, `exit_intent`, `social_proof_click`, `floating_cta_click`
- The `/api/conversion` endpoint on devskyy.app already accepts `{ events: [{ event, timestamp, page, source, data }] }`
- Batch events (send every 5 seconds or on page unload via `navigator.sendBeacon`)

### 1B. WordPress Backend Config (Phase C — PARTIALLY DONE)

- **Menus**: Set up primary nav via `register_nav_menus()` + `wp_nav_menu()`
- **Categories**: Create WooCommerce product categories matching collections
- **Tags**: Add product tags (limited-edition, best-seller, new-arrival, pre-order, collaboration)
- **SEO**: Add proper `<title>`, `<meta description>`, Open Graph tags to all templates
- **Branded content flow**: Ensure "Where Love Meets Luxury" flows throughout

### 1C. Facebook SDK Integration

**App ID:** `860288763161770` — Add to `inc/enqueue.php` or `inc/facebook-sdk.php` with wp_enqueue_script + Facebook Pixel.

### 1D. Products — Pre-Order Setup

**Product data source:** `skyyrose/assets/data/product-content.json` — the REAL canonical catalog with 20 products (br-001→008, lh-001→004, sg-001→010).

Also reference: `assets/2d-25d-assets/product_image_mappings.json` for WordPress CDN image URLs.

**WAIT for user to specify which products are pre-order vs ready-to-sell.**

---

## DIRECTIVE 2: DEVSKYY.APP — DASHBOARD (SECOND PRIORITY)

### 2A. Fix Broken Dashboard Pages — sidebar has 15+ dead links
### 2B. Fix Imagery Page — currently 100% simulated mock data
### 2C. Start Queue Worker — BullMQ exists but never starts
### 2D. Connect Tripo + Meshy 3D Clients to pipeline page

---

## DIRECTIVE 3: BRAND MASCOT

Face bubble (default) → click → full body walks out → chat panel. Verify both imagery pipelines first. Reference: `assets/branding/mascot/skyyrose-mascot-reference.png`

---

## DIRECTIVE 4: HUGGINGFACE ML (user: damBruh)

LoRA model, mascot consistency, brand voice, content Spaces, verify existing Spaces.
