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

The 11 conversion engines (CIE, Aurora, Pulse, Magnetic Obsidian, Cross-Sell, Personalization, Gamification, Momentum, Velocity, Social Proof, Analytics Beacon) are BUILT and WORKING in the WordPress theme. But they do NOT send events anywhere.

**DO THIS:**
- In `assets/js/analytics-beacon.js` — wire up event relay to POST to `https://devskyy.app/api/conversion`
- Every engine should fire events via the beacon: `hotspot_click`, `room_transition`, `panel_open`, `add_to_cart`, `product_view`, `scroll_depth`, `time_on_page`, `exit_intent`, `social_proof_click`, `floating_cta_click`
- The `/api/conversion` endpoint on devskyy.app already accepts `{ events: [{ event, timestamp, page, source, data }] }`
- Batch events (send every 5 seconds or on page unload via `navigator.sendBeacon`)

### 1B. WordPress Backend Config (Phase C — PARTIALLY DONE)

- **Menus**: Set up primary nav (Home, Collections dropdown [Signature, Love Hurts, Black Rose, Kids Capsule], Pre-Order, About, Contact) via `register_nav_menus()` + `wp_nav_menu()`
- **Categories**: Create WooCommerce product categories matching collections (signature-collection, love-hurts, black-rose, kids-capsule)
- **Tags**: Add product tags (limited-edition, best-seller, new-arrival, pre-order, collaboration)
- **SEO**: Add proper `<title>`, `<meta description>`, Open Graph tags to all templates. Use collection-specific SEO copy.
- **Branded content flow**: Ensure brand voice ("Where Love Meets Luxury") appears consistently in footer tagline, meta descriptions, 404 page, email templates

### 1C. Facebook SDK Integration

**App ID:** `860288763161770`

Add to `inc/enqueue.php` or a new `inc/facebook-sdk.php`:
```php
function skyyrose_enqueue_facebook_sdk() {
    wp_enqueue_script(
        'facebook-sdk',
        'https://connect.facebook.net/en_US/sdk.js',
        array(),
        null,
        true
    );
    wp_localize_script('facebook-sdk', 'skyyroseFB', array(
        'appId' => '860288763161770',
        'version' => 'v18.0',
    ));
}
add_action('wp_enqueue_scripts', 'skyyrose_enqueue_facebook_sdk');
```

Also add the FB init script and Facebook Pixel for conversion tracking.

### 1D. Products — Pre-Order Setup

**Product data source:** `assets/2d-25d-assets/product_image_mappings.json` — canonical product list with WordPress CDN image URLs.

Also reference: `skyyrose/assets/data/product-content.json` — full product catalog with descriptions, social copy, SEO meta.

**Set up products in WooCommerce:**
- List products as WooCommerce Simple Products
- Add pre-order badge/ribbon on product cards ("Pre-Order Now", "Coming Soon", "Reserve Yours")
- Pre-order CTA button instead of "Add to Cart" — links to pre-order flow
- Pre-order pricing visible (original price + early access discount)
- Pre-order counter showing limited numbered pieces remaining
- Categories, tags, images, descriptions pulled from the product data files
- **WAIT for user to specify which products are pre-order vs ready-to-sell before setting status**

---

## DIRECTIVE 2: DEVSKYY.APP — DASHBOARD (SECOND PRIORITY)

### 2A. Fix Broken Dashboard Pages

The sidebar has 15+ links pointing to pages that DON'T EXIST. Either build them or remove from sidebar:
- `/admin/round-table` — BUILD (LLM Round Table management)
- `/admin/agents` — BUILD (agent status/health)
- `/admin/3d-pipeline` — EXISTS but needs Tripo client connection
- `/admin/assets` — BUILD or remove
- `/admin/pipeline` — EXISTS
- `/admin/qa` — EXISTS
- `/admin/tasks` — BUILD or remove
- `/admin/jobs` — BUILD (connect to BullMQ queue system)
- `/admin/mascot` — BUILD (mascot management)
- `/admin/monitoring` — BUILD or remove
- `/admin/autonomous` — BUILD or remove
- `/admin/wordpress` — EXISTS
- `/admin/vercel` — EXISTS
- `/admin/huggingface` — EXISTS
- `/admin/settings` — EXISTS

### 2B. Fix Imagery Page — Currently 100% Simulated

`frontend/app/admin/imagery/page.tsx` is pure mock data. Wire it to REAL providers:
- Connect to `agents/visual_generation/` Python pipeline via API route
- Use real Gemini, Imagen 3, HuggingFace FLUX providers
- Show actual generated images, not placeholder gradients
- Download/Regenerate buttons must work

### 2C. Start the Queue Worker

`frontend/lib/queue/queues.ts` and `frontend/lib/queue/worker.ts` exist but the worker NEVER STARTS.
- Add `startWorkers()` call to Next.js startup or create a separate worker process
- Requires `REDIS_URL` env var (default: `redis://localhost:6379`)

### 2D. Connect Tripo 3D Client + Meshy API

`frontend/lib/tripo/client.ts` is real but not hooked to any page.
- Wire it into `/admin/3d-pipeline` page
- Also add Meshy API as a second 3D provider (new API key available)

---

## DIRECTIVE 3: BRAND MASCOT — SKYYROSE AVATAR

**Status:** Phase 1 complete (admin tooling). Phase 2 needs rework.

### Widget Behavior (for skyyrose.co WordPress site):

**DEFAULT STATE (minimized):** A small circular avatar of her FACE ONLY — like a profile picture bubble — sits in the bottom-right corner. Subtle breathing/pulse animation. This is what the customer sees on page load.

**ON CLICK:** Her full animated body WALKS OUT from behind the bubble. The face bubble expands/transitions into her full-body character stepping out onto the screen. She stands next to a chat panel and can:
- Greet the customer with a wave animation
- Open a chat/interaction panel where she "talks" to the customer
- Recommend products based on the current page/collection
- Guide to pre-order, collection pages, or help
- Show different outfits per collection page she's on

**ON MINIMIZE:** She waves goodbye and walks BACK behind the bubble, which shrinks back to the face-only circle.

**CRITICAL:** Full-body mascot images MUST be generated first. Without full-body images in multiple poses (standing, walking left, walking right, waving, idle), the widget cannot work.

### Image Generation — VERIFY BOTH PIPELINES FIRST

**Pipeline 1: Visual Generation** (`agents/visual_generation/`):
- `VisualGenerationRouter` — Google Imagen 3, Veo 2, HuggingFace FLUX.1, Replicate LoRA, Tripo3D, FASHN
- `reference_manager.py` — character consistency
- `prompt_optimizer.py` — brand-aware prompts with `SKYYROSE_BRAND_DNA`

**Pipeline 2: Elite Web Builder** (`agents/elite_web_builder/`):
- Multi-provider LLM (Claude Opus/Sonnet/Haiku, Gemini 3 Pro/Flash, GPT-4o, Grok-3)
- `model_router.py` — fallback chains, health tracking

**VERIFY EVERY PROVIDER** — test connections, confirm API keys load from `.env`, fix broken connections. Then generate:
- Full-body mascot from waist-up reference (100% identical face/hair/style)
- Sprite sheets for walk cycle and idle animations
- Product-wearing variants per collection

**Reference image:** `assets/branding/mascot/skyyrose-mascot-reference.png`

---

## DIRECTIVE 4: HUGGINGFACE ML INFRASTRUCTURE

HuggingFace user: `damBruh`

1. **SkyyRose LoRA Model** — Fine-tuned on product photos for 100% accurate clothing replicas
2. **Mascot Consistency Model** — IP-Adapter/InstantID for identical mascot across generations
3. **Brand Voice Model** — On-brand copy generation ("Where Love Meets Luxury" tone)
4. **Content Generation Spaces** — Product photography, social media, ad creatives, hero/banner imagery, mascot poses
5. **Verify Existing Spaces**: `damBruh/skyyrose-3d-converter`, `damBruh/skyyrose-lora-training-monitor`, `damBruh/skyyrose-virtual-tryon`
6. **Wire into Dashboard** — HuggingFace management page on devskyy.app

---

## PREVIOUS WORK STATUS

- Phase A (WordPress Theme): COMPLETE
- Phase B (Admin Dashboard): COMPLETE (21 pages, but 15 are stubs/broken links)
- Phase C (WordPress backend config): PARTIALLY DONE — menus, tags, categories, SEO still needed
- Phase Final (Conversion engines): 11 engines deployed in theme JS, but NOT connected to analytics API
- Immersive rooms: Built with drakerelated.com-style (4 rooms each, Black Rose + Love Hurts)
- Facebook SDK: App ID 860288763161770 (NOT YET INTEGRATED)

---

## CRITICAL BUGS FIXED

1. **Circular import in `adk/base.py`** — FIXED (lazy import). Verify: `python3 -c "from sdk.python.adk.base import BaseDevSkyyAgent; print('OK')"`
2. **In-memory only analytics** — `/api/conversion` loses all data on restart. Needs database persistence.
3. **Imagery dashboard is 100% fake** — `frontend/app/admin/imagery/page.tsx` shows simulated data only.
