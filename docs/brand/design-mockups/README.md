# Design Mockups

Static HTML design references. Not production code. Standalone, self-contained, no build step.

## Files

| File | Status | Purpose |
|------|--------|---------|
| `v2.html` | **Erased 2026-06-10** | Magazine-as-site direction (locked 2026-05-25). Removed by founder — it still used wrong/pre-OAI imagery. Recover from git history if the composition reference is ever needed; spec survives at `docs/superpowers/specs/2026-05-25-v2-mockup-design.md`. Any successor mockup must source product imagery from validated OAI Image 2 renders only. |
| [`collection-designs.html`](./collection-designs.html) | Superseded | First-pass v1 design from earlier session. Kept for historical reference. Visual direction did not survive the brand-canon recalibration. |

## Imagery rule for future mockups

Product imagery in any mockup must come from validated OAI Image 2 renders (see
`feedback_imagery_engine_oai2` / `scripts/oai_render/`). No nano-banana output, no
pre-2026-06 AI product assets. Brand chrome (lockups from `assets/images/hero-overlays/`,
monogram, hero photography from `assets/branding/hero/`) remains canonical.

## Production translation

Design references are not the production site. When a visual direction is approved, a
separate spec + plan cycle translates it into WordPress theme templates under
`wordpress-theme/skyyrose-flagship/template-*.php`.
