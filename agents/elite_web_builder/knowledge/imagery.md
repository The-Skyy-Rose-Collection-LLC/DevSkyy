# Imagery Agent — Knowledge Reference

**Single source of truth for every product:** `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`

The Imagery sub-agent orchestrates the 10-agent Elite Studio pipeline at `skyyrose/elite_studio/agents/` plus the Nano Banana V4 CLI at `scripts/nano-banana-run.py`. Read `knowledge/canonical_catalog.md` for how to pull SKU data; read this doc for how to turn SKU data into images.

---

## Pipelines (pick the right one for the deliverable)

### 1. Nano Banana `produce` — product front / back / branding

Primary workhorse for catalog product shots. Engine chain GPT-Image → Gemini Pro → FLUX Pro with per-attempt QA scoring.

```bash
PYTHONPATH=. .venv-imagery/bin/python scripts/nano-banana-run.py produce \
    --style {on-model,flat-lay} \
    --views front,back,branding \
    --sku br-001 \
    --max-cost 5.00
```

- **Styles:** `on-model` (default, invisible-form ghost mannequin) or `flat-lay` (top-down on collection-specific surface).
- **Views:** `front`, `back`, `branding` (lifestyle hero with model).
- **Output:** `wordpress-theme/skyyrose-flagship/assets/images/products/{sku}-{view}-render.webp`.
- **Budget ceiling:** `--max-cost` halts before any SKU×view that would cross the running USD sum.

### 2. Compositor Agent (6-stage) — lifestyle / immersive scenes

Places a subject INTO an immersive collection scene. Use when you need "model wearing the product in The Garden / Ballroom / Runway."

```python
from skyyrose.elite_studio.agents.compositor_agent import CompositorAgent
# Stages: BRIA RMBG 2.0 → Claude Opus → IC-Light → FLUX Fill → GPS shadows → Gemini Pro QA
```

Config at `skyyrose/elite_studio/config.py`. QA gate: score ≥ 80 promotes, 50–79 warns, < 50 auto-rejects.

### 3. Master Orchestrator — concept → live product

For full product launches where you start from a concept (not a CSV row) and want images + metadata + WP deploy in one run. See `pipelines/skyyrose_master_orchestrator.py::quick_launch()`.

### 4. FLUX Orchestrator (7-stage luxury) — hero / editorial

`pipelines/flux_orchestrator.py` + `pipelines/skyyrose_luxury_pipeline.py`. For hero banners, landing-page heroes, lookbook spreads.

### 5. Upscaling — 4x for print / banner

HuggingFace Space `damBruh/skyyrose-flux-upscaler`. Invoke via `skyyrose/elite_studio/agents/upscaling_agent.py`.

---

## Style guide (every render)

- **Color fidelity:** Reference `inc/brand-colors.php` constants. Never drift from rose gold `#B76E79`, gold `#D4AF37`, crimson `#DC143C`, silver `#C0C0C0`.
- **Text legibility:** Every letter must be character-perfect. "Black is Beautiful" is NEVER "Black S Beautiful".
- **Patch placement:** If `branding_spec` in CSV says "bottom-left chest", patch goes bottom-left chest. Not centered. Not mirrored. Not omitted.
- **Collection mood:** Black Rose = dark authoritative monochrome silver. Love Hurts = warm baroque crimson. Signature = Bay Area golden hour. Kids Capsule = joyful premium (never pastel/cartoonish).

---

## STOP-AND-SHOW protocol

**Every paid dispatch** (GPT-Image, Gemini Pro, FLUX Pro, FASHN, HuggingFace paid Space) must emit:

```
Action      : nano-banana produce --style flat-lay
SKUs        : 30 (full catalog)
Variants    : front only
Cost est    : $1.63 (flux-pro $0.60 + gpt-image $1.04)
Max ceiling : $5.00
Log         : logs/flatlay-regen-<ts>.log

Proceed? [y/N]
```

Wait for explicit "y" before dispatching. The `agents/elite_web_builder/triggers.py::trigger_pipeline()` helper enforces this when called with `paid=True`.

---

## Reject handling

- QA score < 50 → auto-reject → file lands in `.../products/_rejected/`.
- 50–79 → "NEEDS REVIEW" → file saved to main dir but marked `passed=False` in the log.
- ≥ 80 → PASS → promoted into the main products dir.

Never promote a `_rejected/` file without owner confirmation.

---

## Integration with the theme

Front renders are consumed by `skyyrose_get_product_display_image($product)` in `inc/product-catalog.php`. Precedence: `image` → `front_model_image` → `back_image` → `back_model_image`. If all four CSV columns are empty, the theme falls back to `assets/images/placeholder-product.jpg`.

For SKUs with real photos (`br-007`, `lh-003`, `kids-001`, `kids-002`), populate the `render_source_override` CSV column with the real filename and the pipeline will skip AI regen.
