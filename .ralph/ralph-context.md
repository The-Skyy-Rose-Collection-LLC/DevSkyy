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

### Phase 2 — COMPLETE
- Interactive walking mascot widget (template-parts/mascot.php)
- Walk-on animation from right side after page load delay
- Idle animations (bounce, breathing via CSS)
- Collection-aware outfit switching via wp_localize_script
- Click to open interaction panel (recommendations, CTA, help)
- Minimize/recall (walks off/on screen)
- Mobile-responsive (smaller, peek from corner)
- Accessibility (aria-label, keyboard dismissible, prefers-reduced-motion)
- Lazy loaded, non-blocking

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
