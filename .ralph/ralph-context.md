# RALPH — DIRECTIVE STATUS

## SKYYROSE BRAND AVATAR — IMPLEMENTATION STATUS

**Status:** Phase 1 complete (admin tooling + static placements). Phase 2 in progress (interactive walking mascot).

### Phase 1 — COMPLETE
- Admin mascot management page at `/admin/mascot` (pose/collection/product generation)
- API route at `/api/mascot` (job queue, prompt building, simulated processing)
- WordPress Kids Capsule template mascot section (primary placement)
- WordPress 404 page mascot integration (fun error state)
- Mascot CSS with animations and responsive/reduced-motion support
- Sidebar navigation entry, conditional CSS enqueue

### Phase 2 — NEEDS REWORK

The walking mascot widget needs to be rebuilt with this EXACT behavior:

**DEFAULT STATE (minimized):** A small circular avatar of her FACE ONLY — like a profile picture bubble — sits in the bottom-right corner. Subtle breathing/pulse animation. This is what the customer sees on page load.

**ON CLICK:** Her full animated body WALKS OUT from behind the bubble. The face bubble expands/transitions into her full-body character stepping out onto the screen. She stands next to a chat panel and can:
- Greet the customer with a wave animation
- Open a chat/interaction panel where she "talks" to the customer
- Recommend products based on the current page/collection
- Guide to pre-order, collection pages, or help
- Show different outfits per collection page she's on

**ON MINIMIZE:** She waves goodbye and walks BACK behind the bubble, which shrinks back to the face-only circle.

**KEY:** The face bubble is ALWAYS visible (like a chatbot icon). The full body only appears when clicked. This is NOT a traditional chatbot — it's an animated brand character that walks, waves, and interacts.

**CRITICAL:** The full-body mascot images MUST be generated first. Without full-body images in multiple poses (standing, walking left, walking right, waving, idle), the widget cannot work. PRIORITIZE mascot image generation.

### Pending — VERIFY BOTH IMAGERY PIPELINES THEN GENERATE

**YOU HAVE TWO GENERATION PIPELINES. VERIFY BOTH BEFORE GENERATING.**

**Pipeline 1: Visual Generation** (`agents/visual_generation/`):
- `VisualGenerationRouter` — Google Imagen 3, Google Veo 2, HuggingFace FLUX.1, Replicate LoRA, Tripo3D, FASHN
- `reference_manager.py` — character consistency (feed mascot reference so she stays 100% identical)
- `prompt_optimizer.py` — brand-aware prompts with `SKYYROSE_BRAND_DNA`
- `GenerationType.EXACT_PRODUCT` + `REPLICATE_LORA` — exact product replica clothing
- `conversation_editor.py` — iterate/refine generated images
- `gemini_native.py` — native Gemini integration

**Pipeline 2: Elite Web Builder** (`agents/elite_web_builder/`):
- Multi-provider LLM with fallback chains and health tracking
- `provider_adapters.py` — Anthropic (Claude Opus/Sonnet/Haiku), Google (Gemini 3 Pro/Flash), OpenAI (GPT-4o), xAI (Grok-3)
- `model_router.py` — role-based routing with auto-fallback when provider is unhealthy
- `config/provider_routing.json` — route config (director→Opus, frontend→Sonnet, SEO→GPT-4o, QA→Grok)

**VERIFY EVERY PROVIDER** — test connections, confirm API keys load from `.env`, run dry test generations, fix broken connections. Then use best provider per task:

**Then generate:**
- Full-body mascot from waist-up reference (100% identical face/hair/style)
- Sprite sheets for walk cycle and idle animations
- Product-wearing variants for each collection piece (100% replica clothing)

**Reference image:** `assets/branding/mascot/skyyrose-mascot-reference.png` (exists)

---

## PREVIOUS DIRECTIVES — STATUS

- Phase A (WordPress Theme): COMPLETE
- Phase B (Admin Dashboard): COMPLETE (21 pages)
- Phase C (WordPress backend config): Partially implemented
- Phase Final (Super significant upgrade): 11 conversion engines deployed
- Content automation pipelines: API routes ready
- Immersive rooms: Max 2 scenes per collection implemented
- Facebook SDK: App ID 860288763161770 (pending wp_enqueue_script)

---

## NEW DIRECTIVE: PRODUCTS — USE THE MAPPER + SET UP PRE-ORDERS

**Product data source:** `assets/2d-25d-assets/product_image_mappings.json` — this is the canonical product list with WordPress CDN image URLs and all product variants. USE THIS as the single source of truth for all products.

Also reference: `skyyrose/assets/data/product-content.json` — full product catalog with descriptions, social copy, SEO meta for all 27 products.

**Set up ALL products for pre-order in WooCommerce:**
- Every product should be listed as a WooCommerce product with status = "pre-order" (not purchasable yet, but browsable and reservable)
- Use WooCommerce product type: Simple Product with custom pre-order status
- Add pre-order badge/ribbon on all product cards ("Pre-Order Now", "Coming Soon", "Reserve Yours")
- Pre-order CTA button instead of "Add to Cart" — links to pre-order flow
- Pre-order pricing visible (original price + "Pre-Order Price" with early access discount)
- Pre-order counter showing limited numbered pieces remaining
- Sync product data from the mapper JSON into WooCommerce via the WordPress REST API
- Categories, tags, images, descriptions all pulled from the product data files

---

## NEW DIRECTIVE: HUGGINGFACE ML INFRASTRUCTURE

Set up a proper ML pipeline on HuggingFace so we can generate 100% of our own content — social media posts, website imagery, ad creatives, product shots, mascot variants, fashion model photos, video content, ANYTHING we need on demand.

### What to build/verify on HuggingFace (user: `damBruh`):

1. **SkyyRose LoRA Model** — Fine-tuned model trained on our actual product photos (`assets/2d-25d-assets/`, `assets/3d-models/`) so it generates 100% accurate replicas of our clothing. Use `scripts/upload_lora_dataset_to_hf.py` and `scripts/training/hf_train_brand_voice.py`. The LoRA must know every product in every collection.

2. **Mascot Consistency Model** — Train or configure a model that keeps the brand mascot (`assets/branding/mascot/skyyrose-mascot-reference.png`) 100% identical across all generations — face, hair, skin, style. Use IP-Adapter, InstantID, or similar character consistency technique.

3. **Brand Voice Model** — Fine-tuned text model for SkyyRose brand voice. Generates on-brand copy for social media captions, product descriptions, ad headlines, email campaigns, collection narratives. "Where Love Meets Luxury" tone across everything.

4. **Content Generation Spaces** — Verify/create HuggingFace Spaces that the dashboard can call via API:
   - Product photography generation (model wearing our clothes)
   - Social media content (carousel posts, stories, reels thumbnails)
   - Ad creatives (Facebook/Instagram/TikTok ad formats)
   - Website hero/banner imagery
   - Email header graphics
   - Mascot pose/outfit generation

5. **Existing Spaces** — Verify these still work:
   - `damBruh/skyyrose-3d-converter` — 3D model format conversion
   - `damBruh/skyyrose-lora-training-monitor` — training progress tracking
   - `damBruh/skyyrose-virtual-tryon` — FASHN virtual try-on

6. **Dataset Management** — Ensure training datasets are properly organized on HF:
   - Product photos dataset (all collections, all angles)
   - Brand assets dataset (logos, scenes, mascot references)
   - Round Table elite results (`scripts/export_round_table_to_hf.py`)

7. **Wire into Dashboard** — The devskyy.app admin dashboard must have a HuggingFace management page showing:
   - Model training status (LoRA progress, brand voice training)
   - Space health (online/offline/building)
   - Generation queue (pending/processing/completed jobs)
   - One-click content generation for any use case above

The goal: drop a prompt into the dashboard → get production-ready brand content out. No manual Photoshop. No stock photos. 100% SkyyRose, 100% on-brand, 100% generated.
