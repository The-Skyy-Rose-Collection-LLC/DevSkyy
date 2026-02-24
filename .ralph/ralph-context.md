# RALPH — NEW DIRECTIVES

## CONTENT AUTOMATION PIPELINE — LOCK AND LOAD

Get the entire content automation pipeline ready to go. The owner will provide API keys — your job is to make sure:

1. **Every pipeline has a clean config system** — env vars loaded from `.env`, validated on startup, clear error messages if missing
2. **Every agent connection is wired up** — the dashboard UI at devskyy.app must show connection status (green/red) for each service
3. **Every pipeline has a test/dry-run mode** — so we can verify configs work before going live
4. **Document what's needed** — update `docs/ENV_VARS_REFERENCE.md` with every required key, what it does, and where to get it

**Pipelines to lock and load:**
- 3D Pipeline: Tripo3D + Meshy API (text-to-3D, image-to-3D)
- Imagery Pipeline: Gemini, Imagen, HuggingFace Flux (AI fashion models)
- Social Media Pipeline: Instagram, TikTok, X/Twitter, Facebook (auto-post, schedule, analytics)
- LLM Round Table: Claude, GPT-4, Gemini, Llama (Groq), Mistral, Cohere (all 6 competing)
- WordPress Sync: WooCommerce REST API (product sync, media uploads)
- HuggingFace Deploy: 3 Spaces (3d-converter, lora-monitor, virtual-tryon)
- Virtual Try-On: FASHN API
- Payments: Stripe

Build it so that when the keys drop in `.env`, everything just works.

---

## AFTER YOU FINISH THE CURRENT THEME BUILD + DASHBOARD SETUP:

### PHASE C: WORDPRESS BACKEND CONFIGURATION

Go back into WordPress and lock down the backend properly:

- **Navigation Menus:** Register and configure primary, footer, mobile, and collection menus via `register_nav_menus()`. Populate with all pages — Homepage, Collections (Black Rose, Love Hurts, Signature, Kids Capsule), Experiences (The Garden, The Ballroom, The Runway), Pre-Order, About, Contact, Shop, Cart.
- **Product Tags:** Create and assign tags for all products — collection names, product types (hoodie, jogger, crewneck, jacket, dress), limited-edition, bestseller, new-arrival, collab.
- **Product Categories:** Set up WooCommerce categories matching each collection + Kids Capsule. Hierarchical: Shop > Black Rose, Shop > Love Hurts, Shop > Signature, Shop > Kids Capsule.
- **SEO:** Every page and product needs: meta title, meta description, Open Graph tags, Twitter cards, structured data (JSON-LD for Product, Organization, BreadcrumbList). Use `wp_head` hooks. Yoast SEO compatible.
- **Branded Content Flow:** SkyyRose brand voice, tagline ("Where Love Meets Luxury"), brand colors, and collection-specific messaging must be consistent across EVERY page — headers, footers, product descriptions, CTAs, 404 page, empty cart state, checkout. No generic WordPress copy anywhere. The brand DNA must flow through every pixel.

### SCENE IMAGES REMINDER
- MAX 2 scenes per collection for full-screen drakerelated.com-style immersive rooms
- All remaining scenes = theme imagery (hero backgrounds, section backgrounds, collection pages, about page, pre-order atmosphere)
- Every image should appear somewhere in the theme

### PHASE FINAL: ONE SUPER SIGNIFICANT UPGRADE

After everything is built, implement ONE upgrade that hits BOTH:
1. **COSMETIC** — visually stunning, makes people screenshot and share
2. **MEASURABLE** — proven to increase add-to-cart rate, reduce bounce, or drive pre-order signups

Implement across static pages + immersive pages + dashboard. What separates a $10M luxury brand from a template? Build that.
