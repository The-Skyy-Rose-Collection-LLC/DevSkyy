# agents/elite_web_builder/knowledge/ — Canonical knowledge files (13 .md)

Plain Markdown documents that the `Director` injects into specialist agent contexts via `core/ground_truth.py`. **Source-of-truth for facts** that specialist agents must respect across all stories.

## Inventory

| File | Audience | Content |
|------|----------|---------|
| `canonical_catalog.md` | All agents | Curated subset of SkyyRose catalog facts (collections, founder, brand tagline) |
| `competitor_intel.md` | competitor_scout, seo_content | Positioning analysis, SWOT, key competitor sites |
| `ecommerce_photography.md` | imagery, ecommerce_photography | Photography style guide, lighting setups, garment angles |
| `garment_3d.md` | garment_3d, imagery | 3D model briefs for Tripo/Meshy — material specs, mesh density |
| `performance_budgets.md` | performance | Core Web Vitals targets, bundle size budgets, image size caps |
| `photo_generation.md` | imagery, ecommerce_photography | AI photo generation prompt patterns, brand visual DNA |
| `security_checklist.md` | accessibility, qa, backend_dev | OWASP Top 10 mapped to WordPress + Next.js |
| `shopify_themes.md` | theme_builder | Shopify Liquid + sections + JSON templates reference |
| `social_media.md` | social_media, seo_content | Per-platform image specs (IG, TikTok, X), OG card specs |
| `wcag_checklist.md` | accessibility | WCAG 2.2 AA criteria with code examples |
| `wordpress.md` | theme_builder, backend_dev, frontend_dev | WordPress block-theme + hook patterns, theme.json schema |
| `wordpress_deployment.md` | backend_dev, qa | WordPress.com deploy mechanics (SFTP, hot-swap, verification) |

## Loading pattern

`core/ground_truth.py` reads these files at runtime (NOT at import time — supports hot-edit of knowledge without Director restart):

```python
from agents.elite_web_builder.core.ground_truth import GroundTruth

gt = GroundTruth()
context = gt.context_for_role(AgentRole.FRONTEND_DEV)
# Injects canonical_catalog.md + wordpress.md + wcag_checklist.md + performance_budgets.md
# Per-role mapping defined in ground_truth.py
```

## Conventions

- **Markdown only.** No HTML, no Jinja templates. Files are read as plain text.
- **Catalog facts pull from the CSV at runtime.** `canonical_catalog.md` is a curated summary; full source-of-truth is `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`. When the CSV changes, regenerate the summary.
- **Files map to specialist roles.** Adding a new knowledge file requires updating `core/ground_truth.py` to route it to the right roles.
- **No competitor PII or unverified claims.** `competitor_intel.md` is positioning + public data only — no scraped private content.
- **Cite primary sources.** When stating a WCAG criterion or a CWV threshold, link to the spec (`https://www.w3.org/TR/WCAG22/`, `https://web.dev/vitals/`).

## Don't

- Don't put role-specific code or templates here. This is for facts + standards only — templates go to `agents/elite_web_builder/templates/`.
- Don't paste massive doc blocks (>2KB per file). Specialist agents have token budgets — knowledge files should be lean and reference primary sources for depth.
- Don't add a knowledge file without wiring it into `ground_truth.py:context_for_role()` — orphan files don't reach agents.
- Don't put SkyyRose product copy here. Product copy lives in dossiers (`knowledge-base/products/<sku>/`) and is loaded by the imagery + content agents directly.

## Related

- Loader: `agents/elite_web_builder/core/ground_truth.py`
- Catalog SoT (read at runtime by GroundTruth): `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`
- Brand canon: `knowledge-base/seed/from-interview.md`
- Founder voice: project memory `project_founder_voice.md`
- Per-SKU dossiers: `knowledge-base/products/<sku>/` (separate from knowledge files — consumed by imagery/content agents)

## Recent learnings

- Brand SoT established 2026-04-18 (cmem #1171) — `canonical_catalog.md` is the Elite Web Builder summary; CSV is the authoritative source.
- File contents kept lean intentionally — specialist agents have token budgets, and `ground_truth.py` may inject multiple knowledge files into a single prompt.
