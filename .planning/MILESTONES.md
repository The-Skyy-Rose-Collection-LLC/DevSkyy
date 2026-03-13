# Milestones

## v1.1 WordPress Quality & Accessibility (Shipped: 2026-03-11)

**Phases:** 9-13 (5 phases) | **Plans:** 9 | **Commits:** 47 | **Files changed:** 53

**Key accomplishments:**
- Pre-order products filtered from catalog grids; products.csv synced to 32-product PHP catalog with correct flags
- 43 buttons given explicit `type` attributes across 12 theme files; duplicate enqueue handle collision resolved
- Fixed empty modal headings with `aria-hidden`, ARIA attributes, skip-link target, and image loading attributes
- 20+ WCAG AA contrast failures fixed across 3 CSS files; pre-order $0.00 pricing replaced with "Pre-Order"
- 320px horizontal overflow fixed and 44x44px touch targets enforced across 7 CSS files
- 80+ hardcoded px font sizes replaced with fluid `--text-*` design tokens across 11 CSS files
- Luxury cursor z-index raised to 2147483647; MutationObserver modal pause/resume added; immersive exclusion verified

**Known Gaps:**
- DATA-01: Black Rose hero banner image — code is correct in git, pending CDN cache purge after deploy

---

## v1.0 Production Armor (Shipped: 2026-03-10)

**Phases completed:** 8 phases, 11 plans, 0 tasks

**Key accomplishments:**
- 4-layer armor chain: git hooks -> CI -> PR protection -> deploy verification
- Husky v9 + lint-staged routing 6 tools across Python/JS/TS/PHP
- WordPress build pipeline: webpack + clean-css producing 99 minified files + source maps
- CI enforcement: 17 continue-on-error removed, 5 required status checks, minification drift detection
- Single-command deploy: build -> rsync/lftp -> maintenance mode -> cache flush -> 6-page content verification
- 26 requirements satisfied, 44 must-haves verified, 4 E2E flows complete

