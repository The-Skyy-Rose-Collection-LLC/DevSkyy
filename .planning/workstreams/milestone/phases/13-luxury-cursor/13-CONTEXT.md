# Phase 13: Luxury Cursor - Context

**Gathered:** 2026-05-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Custom luxury cursor works correctly everywhere — including above modals — and only loads where needed (not on immersive pages where it's hidden via CSS). CURS-01..03 from v1.1 — all `[x]` complete in REQUIREMENTS.md. Implementation in `luxury-cursor.js` + `luxury-cursor.css`, conditionally enqueued via `inc/enqueue.php` template-slug map. Phase 13 scope = verification + closure.

</domain>

<decisions>
## Implementation Decisions

### Verification Approach
- pytest: parse `inc/enqueue.php` template-slug map, assert luxury-cursor is enqueued on expected templates AND NOT on immersive templates (CURS-03).
- pytest: parse `luxury-cursor.css` z-index, assert it exceeds modal z-index ranges (CURS-01).
- Live: post-deploy assert `<script src=".*luxury-cursor.*\.js"` present on front-page + collection-black-rose, absent on immersive pages.
- CURS-02 (cursor pauses/adapts when modal open): functional test deferred to manual visual verification — automatable only via Playwright (out of scope this phase).

### Shipped Files (verified)
- `assets/js/luxury-cursor.js` + `.min.js` + sourcemap — exists
- `assets/css/luxury-cursor.css` — exists (enqueue.php:179-181)
- `inc/enqueue.php:250-253` — conditional enqueue (uses .min when available)
- Template slug map in enqueue.php — immersive templates marked as `'immersive'` slug → cursor NOT enqueued

### Closure
- Mark CURS-01..03 traceability entries with commit references.
- ROADMAP.md Phase 13 success criteria → `[x]`.

### Claude's Discretion
- Whether to add CSS variable parser for z-index extraction vs regex (regex simpler for single token)
- CURS-02 verification depth: PHP code-path assertion vs deferred-to-manual

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `assets/js/luxury-cursor.js` — cursor implementation
- `assets/css/luxury-cursor.css` — cursor styles (z-index control)
- `inc/enqueue.php:103-253` — conditional enqueue logic with template slug map
- `tests/test_a11y_html_integrity.py` (Phase 10) — analog for HTML fixture-based testing
- `scripts/verify_live_structure.py` — extension for cursor-presence assertions

### Established Patterns
- Conditional enqueue via template slug map (front-page, about, immersive, preorder-gateway, collection)
- Use minified asset when available (`$use_min` check)
- Immersive templates explicitly mapped to `'immersive'` slug → cursor disabled

### Integration Points
- `tests/test_luxury_cursor.py` (new) — parses enqueue.php logic
- `scripts/verify_live_structure.py` — adds Assertion for `script[src*='luxury-cursor']`

</code_context>

<specifics>
## Specific Ideas

- Immersive pages intentionally hide cursor (focus on 3D scene). Verification must confirm cursor JS is NOT downloaded on immersive pages — wasted bytes if loaded but hidden.
- Z-index hierarchy: modals/popups in theme typically use 9000-9999. Cursor must exceed 10000 to render above (CURS-01).
- Pre-order gateway: cursor SHOULD load — it's an interactive page, not immersive.

</specifics>

<deferred>
## Deferred Ideas

- Playwright functional test for CURS-02 (modal-open behavior) — defer to v1.3 if cursor regressions surface
- Cursor accessibility opt-out — defer (prefers-reduced-motion already handled)

</deferred>
