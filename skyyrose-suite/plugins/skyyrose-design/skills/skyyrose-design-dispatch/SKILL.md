---
name: skyyrose-design-dispatch
description: Handoff router for skyyrose-design. Use when a design/build task needs copy, backend, or verification owned by another SkyyRose plugin — tells you when and where to hand off.
---

# skyyrose-design — Dispatch / Handoff

`skyyrose-design` owns imagery (gpt-image-2 composition), frontend, Three.js/immersive, WP/WooCommerce theming, accessibility, and layout. Hand off along the suite graph (`CROSS-PLUGIN.md`): **design → qa** for verification, back to **market** for copy, to **core** for backend.

## When to hand off

| The task also needs… | Hand off to | Example |
|----------------------|-------------|---------|
| Verification/review of a built artifact (theme code, component, render) | `skyyrose-qa` | A built page or render → `skyyrose-qa:verification-loop` / `:audit` before it ships. **Always verify built artifacts before launch.** |
| Marketing copy, product descriptions, SEO meta | `skyyrose-market` | A landing page needs headline + body copy → `skyyrose-market:content-engine`. |
| Backend/API/data behind the UI | `skyyrose-core` | A 3D configurator needs a pricing endpoint → `skyyrose-core:fastapi-patterns`. |
| A regression appeared after a build | `skyyrose-qa:drive-to-green` | Theme change broke a page → self-heal loop. |

## Guardrails
- **Paid renders (gpt-image-2) are STOP-AND-SHOW** — print Action/SKU/Source/Cost, wait for `y`; `ready_to_render` flips only after `y`.
- Canonical engine = OpenAI Image 2 (`gpt-image-2`); product images never use fal.ai image models.
- Product/garment facts resolve through the catalog CSV + per-SKU dossiers; brand canon (collections, palettes, The Five) is locked.
