# SENIOR DEVELOPER PROMPT: AI Model Generation for WordPress Theme Development

**Priority**: HIGH | **Sprint**: Current | **Team**: Creative Engineering + WordPress
**Date**: 2026-02-20 | **Author**: DevSkyy Platform Team

---

## Objective

Build an automated pipeline that generates **AI fashion models wearing SkyyRose garments**, then integrates the output into the `skyyrose-flagship` WordPress theme for product pages, collection templates, and immersive 3D experiences.

We already have the infrastructure. This prompt connects the dots.

---

## What We Have (Use These — Do NOT Rebuild)

### Virtual Try-On (FASHN)
- **Agent**: `agents/fashn_agent.py` — `fashn_virtual_tryon` + `fashn_create_model` tools
- **API**: `api/virtual_tryon.py` — Full REST endpoints at `/virtual-tryon/`
- **Model Generation**: `POST /virtual-tryon/models/generate` — Creates AI fashion models (gender, ethnicity, pose)
- **Try-On**: `POST /virtual-tryon/generate` — Overlays garment onto model image
- **Batch**: `POST /virtual-tryon/batch` — Up to 10 concurrent generations
- **Cost**: $0.075/image | Output: 576x864 (configurable)

### 3D Asset Generation
- **Agent**: `agents/tripo_agent.py` — Text-to-3D and Image-to-3D with brand DNA
- **Pipeline**: `ai_3d/generation_pipeline.py` — TRELLIS → Meshy → Tripo3D fallback chain
- **Output**: GLB (web) + USDZ (iOS AR) | 50K-200K polygons | 2048px textures

### Image Enhancement
- **Upscaling**: `services/ml/enhancement/upscaling.py` — Real-ESRGAN 2x/4x via Replicate
- **Background Removal**: `services/ml/enhancement/background_removal.py` — RemBG
- **Watermarking**: `services/ml/watermark_service.py` — Invisible DCT steganography
- **Color Grading**: `services/ai_image_enhancement.py` — Rose gold tint (#B76E79 blend)
- **Virtual Photoshoot**: `imagery/virtual_photoshoot.py` — Multi-angle, lighting presets, brand backgrounds

### Brand System
- **Injector**: `orchestration/brand_context.py` — `BrandContextInjector.get_system_prompt()`
- **API**: `api/brand.py` — `GET /brand`, `GET /brand/collections`, `GET /brand/colors`
- **Prompts**: `services/ml/prompts/vision_prompts.py` — Luxury description templates

### WordPress Theme
- **Theme**: `wordpress-theme/skyyrose-flagship/`
- **3D Viewer Widget**: `elementor/widgets/three-viewer.php` — GLB/GLTF in Elementor
- **WooCommerce**: `inc/woocommerce.php` — Product templates with 3D model support
- **Scene Manager**: `assets/js/three/scene-manager.js` — Three.js rendering
- **Hotspot System**: `assets/js/three/hotspot-system.js` — Interactive product markers

### Workflow Orchestration (NEW — just shipped)
- **Module**: `sdk/python/adk/workflow_agents.py`
- **Pattern**: Google ADK SequentialAgent + ParallelAgent + LoopAgent
- **Zero LLM orchestration tokens** — deterministic pipeline flow
- **Pipelines**: `create_product_launch_pipeline()`, `create_content_creation_pipeline()`

---

## What We Need Built

### Phase 1: AI Model Generation Service (Week 1-2)

Create `services/ai_model_generation.py` that orchestrates the full pipeline:

```
Input: product_sku, collection, garment_category
  │
  ├─ Step 1: Fetch product image from WooCommerce (flat-lay / ghost mannequin)
  │
  ├─ Step 2: Generate AI fashion models via FASHN
  │    ├─ 3 diverse models per product (vary gender, ethnicity, body type)
  │    ├─ Poses: STANDING_FRONT, THREE_QUARTER, WALKING, LIFESTYLE
  │    └─ Use `POST /virtual-tryon/models/generate`
  │
  ├─ Step 3: Virtual try-on — dress each model in the garment
  │    ├─ Use `POST /virtual-tryon/batch` for concurrent processing
  │    ├─ GarmentCategory mapping: hoodie→OUTERWEAR, tee→TOPS, etc.
  │    └─ Quality mode: QUALITY (not FAST) for theme assets
  │
  ├─ Step 4: Enhancement pipeline (per image)
  │    ├─ Upscale to 2x (Real-ESRGAN) for retina displays
  │    ├─ Apply rose gold color grading via LuxuryImageEnhancer
  │    ├─ Background removal → composite on brand backgrounds
  │    │    ├─ WHITE (e-commerce / WooCommerce product pages)
  │    │    ├─ BLACK (collection hero banners)
  │    │    └─ SKYYROSE_PINK (marketing / social media)
  │    └─ Embed invisible watermark (product_id + generation_date)
  │
  ├─ Step 5: Generate variants for WordPress
  │    ├─ Product thumbnail (600x600)
  │    ├─ Product gallery (1200x1600)
  │    ├─ Collection hero (1920x1080)
  │    ├─ Mobile hero (750x1000)
  │    └─ Social share (1080x1080)
  │
  └─ Output: { sku, model_images[], variants{}, metadata }
```

**Technical Requirements**:
- Use the existing `ProductAssetPipeline` pattern from `orchestration/asset_pipeline.py`
- Rate limit: `time.sleep(8)` between FASHN batch calls to avoid 429s
- Redis cache with 7-day TTL (same as existing asset pipeline)
- Correlation ID propagation on every async call
- All agent names must use underscores (no hyphens) per ADK naming rules

### Phase 2: WordPress Theme Integration (Week 2-3)

#### 2A: Product Page AI Model Gallery

In `wordpress-theme/skyyrose-flagship/`, create a WooCommerce product gallery that shows AI models wearing the product alongside flat-lay shots.

**File**: `inc/ai-model-gallery.php`

```php
// Hook into WooCommerce product gallery
// After default product images, inject AI model images
// Fetch from custom meta: _skyyrose_ai_models (JSON array of image URLs)
// Display as swipeable carousel with caption: "See it on a model"
// Lazy-load with IntersectionObserver for performance
// Mobile: stack vertically with touch swipe
// Desktop: thumbnail strip below main image
```

**Product Meta Box** (`inc/admin/ai-model-metabox.php`):
```php
// Admin metabox on product edit screen
// "AI Model Images" section
// Button: "Generate AI Models" → triggers async API call
// Progress indicator with WebSocket updates
// Preview generated images before publishing
// Save as _skyyrose_ai_models post meta
```

#### 2B: Collection Template Enhancement

Update the three collection templates to use AI model hero images:

- `template-collection-black-rose.php` — Dark, dramatic AI model shots
- `template-collection-love-hurts.php` — Emotional, editorial AI model shots
- `template-collection-signature.php` — Clean, minimal AI model shots

Each template should:
1. Pull hero AI model image from collection taxonomy meta
2. Display full-bleed hero with parallax scroll
3. Below hero: product grid where each product thumbnail is an AI model shot (not flat-lay)
4. On hover: swap to flat-lay product image for detail

#### 2C: Immersive 3D Scene Integration

For the Love Hurts "Enchanted Ballroom" scene and other immersive experiences:

1. Place AI model images on in-scene mannequins/pedestals as texture maps
2. Use `hotspot-system.js` to make AI model images interactive
3. Click hotspot → modal with:
   - AI model wearing the product (full resolution)
   - "Try It On Yourself" button → virtual try-on with user's photo
   - "Add to Cart" with size selector
   - 360 rotation view (if 3D model available)

---

## Phase 3: ADK Workflow Pipeline (Week 3-4)

Wire this into the new ADK Workflow Agents system. Create a new pipeline in `sdk/python/adk/workflow_agents.py`:

```python
def create_ai_model_generation_pipeline() -> SequentialAgent:
    """
    AI Model Generation Pipeline for WordPress theme assets.

    Flow:
      1. Commerce worker (fetch product data + images from WooCommerce)
      2. ParallelAgent: Generate 3 diverse AI fashion models
      3. ParallelAgent: Virtual try-on (3 models × garment)
      4. ParallelAgent: Enhancement (upscale + color grade + watermark)
      5. Operations worker (upload to WordPress media library)
      6. Analytics worker (log generation metrics + cost tracking)
    """
```

This replaces manual orchestration with zero-overhead deterministic flow.

---

## Brand Compliance (Non-Negotiable)

Every generated image MUST pass these checks before it touches WordPress:

| Check | Requirement | Validator |
|-------|-------------|-----------|
| **Color Accuracy** | Rose gold (#B76E79) present in grading | `LuxuryImageEnhancer` |
| **Resolution** | Minimum 1200px on longest edge | PIL size check |
| **Watermark** | Invisible DCT watermark embedded | `WatermarkService.embed_watermark()` |
| **Brand Context** | `BrandContextInjector` used for all prompts | `orchestration/brand_context.py` |
| **Diversity** | Min 3 models with varied representation | FASHN model params |
| **Quality Gate** | 95% fidelity score minimum | `quality_gate.py` |
| **No Hallucinations** | AI model must actually wear the correct garment | Manual QA + hash comparison |
| **File Naming** | `{sku}_{collection}_{model_id}_{variant}.webp` | Pipeline output |
| **Format** | WebP for web, PNG for print/admin | Format optimizer |

---

## Environment Variables Required

```bash
# Already configured (verify they're active):
FASHN_API_KEY=           # FASHN virtual try-on + model generation
FASHN_API_BASE_URL=https://api.fashn.ai/v1
TRIPO_API_KEY=           # 3D model generation (for Phase 2C)
HF_TOKEN=                # HuggingFace (fallback 3D)

# New (add to .env.production):
AI_MODEL_GENERATION_CONCURRENCY=3    # Max concurrent FASHN calls
AI_MODEL_CACHE_TTL_DAYS=7            # Redis cache duration
AI_MODEL_OUTPUT_DIR=./generated_assets/ai_models
AI_MODEL_QUALITY_THRESHOLD=0.95      # Minimum fidelity score
WORDPRESS_MEDIA_UPLOAD_ENDPOINT=     # WP REST API for media upload
```

---

## API Endpoints to Implement

```
POST   /ai-models/generate/{sku}           # Generate AI models for a product
POST   /ai-models/generate/collection/{id} # Generate for entire collection
GET    /ai-models/status/{job_id}          # Job status
GET    /ai-models/{sku}                    # Get generated images for product
DELETE /ai-models/{sku}                    # Remove generated images
POST   /ai-models/regenerate/{sku}         # Regenerate with new models
GET    /ai-models/metrics                  # Generation stats + cost tracking
```

---

## Testing Requirements

Per CLAUDE.md — TDD is mandatory. Write tests FIRST.

```bash
# Required test files:
tests/services/test_ai_model_generation.py    # Unit tests for generation service
tests/api/test_ai_models_api.py               # API endpoint tests
tests/integration/test_model_to_wordpress.py  # WordPress upload integration
tests/test_workflow_ai_model_pipeline.py      # ADK pipeline tests

# Coverage requirement: 90%+
pytest --cov=services.ai_model_generation --cov-report=term-missing
```

---

## Acceptance Criteria

- [ ] `POST /ai-models/generate/{sku}` returns 3 diverse AI model images within 120 seconds
- [ ] Each image passes brand compliance checks (color, watermark, resolution, quality gate)
- [ ] Images auto-upload to WordPress media library via REST API
- [ ] WooCommerce product pages display "See it on a model" gallery
- [ ] Collection templates use AI model hero images with parallax
- [ ] Immersive 3D scenes show AI models on hotspot-interactive mannequins
- [ ] ADK workflow pipeline runs end-to-end with zero orchestration tokens
- [ ] All tests pass at 90%+ coverage
- [ ] Cost per product: < $1.00 (3 models × 3 try-ons × $0.075 + enhancement)
- [ ] Total pipeline latency: < 3 minutes per product

---

## File Tree (What Gets Created)

```
services/
  ai_model_generation.py              # Core generation service (Phase 1)

api/
  ai_models.py                        # REST endpoints (Phase 1)

sdk/python/adk/
  workflow_agents.py                   # Add create_ai_model_generation_pipeline() (Phase 3)

wordpress-theme/skyyrose-flagship/
  inc/
    ai-model-gallery.php              # Product gallery integration (Phase 2A)
    admin/
      ai-model-metabox.php            # Admin generation UI (Phase 2A)
  assets/
    js/
      ai-model-gallery.js             # Frontend carousel + lazy load (Phase 2A)
    css/
      ai-model-gallery.css            # Gallery styles (Phase 2A)

tests/
  services/test_ai_model_generation.py
  api/test_ai_models_api.py
  integration/test_model_to_wordpress.py
  test_workflow_ai_model_pipeline.py
```

---

## References

| Resource | Path |
|----------|------|
| FASHN Agent | `agents/fashn_agent.py` |
| Virtual Try-On API | `api/virtual_tryon.py` |
| Tripo3D Agent | `agents/tripo_agent.py` |
| 3D Generation Pipeline | `ai_3d/generation_pipeline.py` |
| Virtual Photoshoot | `imagery/virtual_photoshoot.py` |
| Brand Context | `orchestration/brand_context.py` |
| Asset Pipeline | `orchestration/asset_pipeline.py` |
| Image Enhancement | `services/ai_image_enhancement.py` |
| Upscaling Service | `services/ml/enhancement/upscaling.py` |
| Watermark Service | `services/ml/watermark_service.py` |
| Vision Prompts | `services/ml/prompts/vision_prompts.py` |
| ADK Workflow Agents | `sdk/python/adk/workflow_agents.py` |
| WordPress Theme | `wordpress-theme/skyyrose-flagship/` |
| 3D Viewer Widget | `wordpress-theme/skyyrose-flagship/elementor/widgets/three-viewer.php` |
| Hotspot System | `wordpress-theme/skyyrose-flagship/assets/js/three/hotspot-system.js` |
| 3D Pipeline Docs | `docs/3D_GENERATION_PIPELINE.md` |
| Theme Structure | `wordpress-theme/skyyrose-flagship/THEME-STRUCTURE.md` |
| CLAUDE.md | `CLAUDE.md` (read before every PR) |

---

**Ship it. Every model wears SkyyRose. Every pixel bleeds rose gold.**

*— DevSkyy Platform Team*
