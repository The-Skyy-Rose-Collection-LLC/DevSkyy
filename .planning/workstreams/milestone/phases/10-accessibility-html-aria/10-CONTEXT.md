# Phase 10: Accessibility HTML & ARIA - Context

**Gathered:** 2026-05-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Theme rendered HTML must pass validation with zero ARIA errors and correct semantic structure. Phase covers A11Y-01..09 from v1.1 requirements — REQUIREMENTS.md marks all 9 items `[x]` complete. The implementation shipped in commit `923455187 fix: Phase 1 — accessibility + performance critical fixes` and was reinforced in `dfc4e1e94 feat(theme): v4.1.0 — production build system, security hardening, WCAG 2.2`. Phase 10 task = generate regression-prevention verification (a11y test suite + post-deploy assertion), close the requirement formally in REQUIREMENTS.md/ROADMAP.md.

</domain>

<decisions>
## Implementation Decisions

### Verification Pattern (matches Phase 9)
- Extend `scripts/verify_live_structure.py` with ARIA assertions per A11Y-01..09
- Add `tests/test_a11y_html_integrity.py` for pre-deploy validation using BeautifulSoup against captured HTML samples (no live curls in unit tests)
- Skip-nav link presence (A11Y-07): assert `<a href="#main"` or `<a class="skip-link"` in header.php output
- Empty heading guard (A11Y-03): assert no `<h[1-6]>\s*</h[1-6]>` in serialized DOM
- Aria-hidden focusable (A11Y-05): assert all `[aria-hidden="true"]` ancestors of `<a>/<button>/<input>` have `tabindex="-1"`

### Existing Shipped Code
- `inc/accessibility-fix.php` (227 lines): regex-based DOM rewriter — adds aria-hidden to empty headings, tabindex="-1" to aria-hidden focusable elements, fixes empty link aria-labels. Hooked via WP filter on rendered output.
- `assets/css/accessibility.css` (294 lines): `.screen-reader-text`, focus-visible styles, skip-link visibility.
- `header.php`: skip-nav `<a class="skip-link" href="#main">Skip to content</a>` present.

### Closure
- Mark A11Y-01..09 traceability table entries as `Complete (v1.1)` referencing commits 923455187 + dfc4e1e94 + 8ad0df313 (v6.2.0 collection page rebuild that re-applied a11y patterns).
- Update ROADMAP.md Phase 10 success criteria to `[x]` with commit references.

### Claude's Discretion
- BeautifulSoup vs lxml for HTML parsing (BeautifulSoup is project-standard per scrapling usage)
- Whether to wire axe-core via Playwright (deferred to v1.3 — out of scope, REQUIREMENTS.md says target is WCAG AA not AAA)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `inc/accessibility-fix.php` — already implements DOM-rewriting filter
- `assets/css/accessibility.css` — screen-reader/focus styles
- `header.php` — skip-link wired
- `scripts/verify_live_structure.py` — Phase 9 extended this with hero asset assertions; same Assertion dataclass pattern
- `tests/test_collection_data_integrity.py` — Phase 9 reference for new pytest module

### Established Patterns
- WP filter hooks for output rewriting (`add_filter('the_content', ...)`, `add_filter('post_class', ...)`)
- Verification scripts use `Assertion(name, css, expect_min, expect_max)` dataclass per existing structure
- Tests use pytest with module-level fixtures parsing CSV/HTML once per session

### Integration Points
- `inc/enqueue.php` — accessibility-fix.php is wired via `require_once` chain in functions.php
- `scripts/verify_live_structure.py` — extension point: add A11Y-prefixed assertions
- `tests/` — pytest auto-discovers test_*.py files

</code_context>

<specifics>
## Specific Ideas

- A11Y verification must run against SERIALIZED rendered HTML, not the WP filter callback in isolation — that's why live curl + BeautifulSoup is the right vehicle.
- Skip-nav functional test: assert `<a class="skip-link">` exists AND its `href` matches an element ID present in the same page (`#main`, `#content`, etc).
- Duplicate ID guard (A11Y-02): aggregate all `id="..."` attribute values and assert no duplicates per page.

</specifics>

<deferred>
## Deferred Ideas

- WCAG AAA compliance — out of scope per REQUIREMENTS.md
- Axe-core / Playwright integration — defer to v1.3 if a11y regressions surface
- Auto-fix bot — defer, manual fix sufficient at current cadence

</deferred>
