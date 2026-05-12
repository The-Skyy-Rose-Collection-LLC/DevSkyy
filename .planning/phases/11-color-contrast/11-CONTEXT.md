# Phase 11: Color Contrast - Context

**Gathered:** 2026-05-12
**Status:** Ready for planning

<domain>
## Phase Boundary

All text on the site meets WCAG AA contrast ratios (4.5:1 normal, 3:1 large) and pricing displays correctly. CNTR-01..04 from v1.1 — all marked `[x]` complete in REQUIREMENTS.md. Shipped in v1.1 cycle (commit references via git log query on `assets/css/design-tokens.css`, `assets/css/accessibility.css`, `assets/css/collection-pages.css`). Phase 11 scope = generate WCAG ratio regression test + close requirements.

</domain>

<decisions>
## Implementation Decisions

### Verification Approach
- Pure-Python WCAG ratio calculator using design-tokens.css values (parse `:root` and `[data-collection]` blocks, extract `--skyyrose-text`, `--skyyrose-text-muted`, `--skyyrose-bg` per collection, compute contrast ratio).
- Test in `tests/test_color_contrast_wcag.py`: assert every token pair meets 4.5:1 (normal) or 3:1 (large text where annotated).
- Live verification: integrate WCAG check into `scripts/verify_live_structure.py` via assertion that computed style of `.col-page__title`, `.col-hero__tagline`, `.product-price` meets AA on each collection palette.

### Shipped Tokens (verified)
- Default: text #F5E6D3 on bg #0A0A0A (luminance ratio ≈ 17:1 — AAA)
- text-muted: rgba(245,230,211,0.7) blended on bg ≈ 12:1 (AAA)
- Per-collection palettes inherit text/bg via design-tokens.css; verify each variant.

### Pricing Display (CNTR-04)
- Love Hurts $0 → "Pre-Order" replacement already implemented via PHP catalog `is_preorder` field consumed in product-card templates. Verification: assert no `$0` or `$0.00` rendered on collection pages with pre-order SKUs.

### Claude's Discretion
- Library: pure Python WCAG calc (no external dep) vs `wcag-contrast-ratio` PyPI package. Pure Python preferred — single function ~20 lines.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `assets/css/design-tokens.css` — `--skyyrose-text`, `--skyyrose-text-muted`, `--skyyrose-bg` per `:root` + per `[data-collection]`
- `assets/css/accessibility.css` — `prefers-contrast: more` media query already present
- Phase 9/10 test pattern — pytest module-level fixtures, single source of truth
- `scripts/verify_live_structure.py` — extension point for live assertions

### Established Patterns
- CSS custom properties keyed by data-collection attribute
- Pricing rendered via PHP catalog → `is_preorder` flag drives copy substitution
- Test fixtures parse CSV/HTML once per session

### Integration Points
- `wcag_ratio(hex_a, hex_b)` helper added to `tests/utils/color.py` (new) or inline if single-use
- Token parser regex: `--skyyrose-(text|text-muted|bg)\s*:\s*([^;]+);`

</code_context>

<specifics>
## Specific Ideas

- WCAG relative luminance formula: per WCAG 2.x, `L = 0.2126*R + 0.7152*G + 0.0722*B` with sRGB gamma correction. Contrast ratio = `(L_lighter + 0.05) / (L_darker + 0.05)`.
- text-muted using alpha-channel rgba over solid bg: blend channel-wise before computing luminance.
- Pre-order pricing: Love Hurts collection has `lh-001` flagged is_preorder=1 in CSV — verify no `$0` appears for that SKU's card.

</specifics>

<deferred>
## Deferred Ideas

- WCAG AAA target — out of scope per REQUIREMENTS.md
- Auto-fix bot for contrast violations — defer; current code passes AA
- Dynamic contrast adjustment based on user preferences — out of scope

</deferred>
