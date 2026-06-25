# Phase 12: Responsive & Typography - Context

**Gathered:** 2026-05-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Site looks and works correctly across all screen sizes from 320px mobile to desktop. RESP-01..04 from v1.1 — all `[x]` complete in REQUIREMENTS.md. Shipped via design-tokens.css `clamp()`-based fluid typography + per-component @media queries. Phase 12 scope = generate responsive regression test suite + close requirements.

</domain>

<decisions>
## Implementation Decisions

### Verification Approach
- Pure-Python test parsing design-tokens.css `clamp()` values, asserting each text-* token has 3 clamp arguments (min, preferred, max) and min ≥ 0.75rem (12px floor).
- Touch-target audit: parse interactive selectors from theme CSS files (.btn, .skyyrose-cta, .col-card a), assert computed min height/width ≥ 44px in mobile @media blocks.
- No horizontal-overflow test: capture HTML fixture, parse with BeautifulSoup, flag any element with explicit width > 100vw or fixed width > 320px without overflow handling.
- Live verification: openwolf designqc captures at 320px, 768px, 1280px breakpoints — visual diff against baseline (optional, deferred if costly).

### Shipped Tokens (verified)
- Type scale uses `clamp(min, preferred, max)`: --text-3xl: clamp(1.875rem, 2.8vw, 2.25rem)
- Decorative type tokens: --text-decorative-* with proper vw scaling
- @media (max-width: 768px) and (max-width: 480px) breakpoints standard

### Closure
- Mark RESP-01..04 traceability entries with commit references (8ad0df313 v6.2.0 collection page rebuild covers most of this).
- ROADMAP.md Phase 12 success criteria → `[x]` with commit refs.

### Claude's Discretion
- Whether to wire Playwright/openwolf designqc into the phase test suite (likely too costly for autonomous run — defer)
- Library choice for CSS parsing (regex sufficient for clamp/media-query extraction)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `assets/css/design-tokens.css` — type scale, spacing scale, clamp-based fluid sizing
- Page-specific CSS files with @media queries (.col-page, .lp-hero, etc.)
- `tests/test_color_contrast_wcag.py` (Phase 11) — analog for CSS token parsing
- `scripts/verify_live_structure.py` — extension for breakpoint assertions

### Established Patterns
- Fluid typography via clamp()
- 768px = tablet boundary, 480px = mobile narrow
- Touch targets sized via design-tokens (--touch-target-min: 44px assumed)

### Integration Points
- `tests/test_responsive_tokens.py` (new)
- design-tokens.css parser regex: `--text-[a-z0-9-]+\s*:\s*clamp\(([^)]+)\)`

</code_context>

<specifics>
## Specific Ideas

- 320px is the absolute floor (small mobile, iPhone SE 1st gen) — every page must render without horizontal scroll at 320px.
- Touch target audit on actual interactive elements (CTAs, nav links, form inputs, product card links) — not decorative spans/divs.
- Typography hierarchy: assert h1 > h2 > h3 > body in computed font-size order per breakpoint.

</specifics>

<deferred>
## Deferred Ideas

- Playwright visual regression — defer until pixel-perfect verification needed
- Container queries — defer until browser support reaches AA target
- AAA contrast at all breakpoints — out of scope per REQUIREMENTS.md

</deferred>
