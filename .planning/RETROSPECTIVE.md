# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

---

## Milestone: v1.1 — WordPress Quality & Accessibility

**Shipped:** 2026-03-11
**Phases:** 5 (9-13) | **Plans:** 9 | **Commits:** 47 | **Timeline:** 2 days

### What Was Built
- WCAG AA accessibility compliance: 43 buttons typed, ARIA attrs, skip nav, image loading, contrast floor
- Pre-order product filtering from catalog grids; 32-product catalog synced between PHP and CSV
- WCAG AA contrast fixes (20+ CSS selectors) + pre-order "$0.00" → "Pre-Order" price display
- Mobile-first responsive layout (320px) with 44px touch targets and fluid clamp() typography tokens
- Luxury cursor rendered above all modals via z-index max, modal-aware pause/resume via MutationObserver

### What Worked
- Wave-based parallel execution — Phases 10 and 11 each ran 2 plans in parallel with zero conflicts
- Sequential wave ordering where needed — Phase 12 correctly serialized Plans 01/02 to avoid CSS merge conflicts
- Defense-in-depth pattern — pre-order price fix applied at 3 layers (WC filter + catalog fallback + template guard)
- Reading before writing — planner discovered existing correct code (PHP enqueue exclusion, hero image paths in git)
- Design token adoption — leveraging `brand-variables.css` clamp() tokens rather than inventing new scales

### What Was Inefficient
- Phase 9 plan count mismatch — plan estimated 31 products, catalog had 32; caught in verification not planning
- Continuation agent hallucination on 09-02 — after checkpoint approval, agent invented a new failure scenario; required manual SUMMARY.md correction
- CDN cache issue for Black Rose homepage card — image replaced locally, but gitignored; still requires deploy + purge to go live
- DATA-01 never fully closed (live site verification pending CDN) — carried as known gap into milestone completion

### Patterns Established
- `min(N px, 100%)` in grid `minmax()` for overflow-safe responsive grids
- `min-height: 44px` + `display: inline-flex; align-items: center` for touch targets on text links
- z-index 2147483647 as cursor supremacy (max 32-bit int, ends the arms race)
- MutationObserver on `document.body` subtree for modal detection (attribute changes: class, aria-hidden, inert, open)
- Removing 480px breakpoint font-size overrides when parent already has clamp() — overrides defeat the purpose

### Key Lessons
1. **Read before writing** — 2 of 5 plans required 0 code changes because the planner first verified existing code was already correct. Saves time and avoids regressions.
2. **Defense-in-depth for PHP/WC dual paths** — any fix affecting WooCommerce output must also cover the fallback catalog path, since some deploys don't have WC active.
3. **Continuation agents need explicit task tables** — the 09-02 hallucination happened because the continuation prompt lacked the completed-tasks table from the checkpoint return.
4. **Gitignored assets need separate deploy tracking** — binary assets outside git need explicit note in STATE.md that they require manual rsync deploy.

### Cost Observations
- Model mix: ~60% Opus (orchestrator + planner), ~40% Sonnet (executor + verifier)
- Sessions: 1 long session with context compaction
- Notable: Wave parallelization cut wall-clock time significantly — phases 11 ran 2 plans concurrently in <10 min total

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Key Change |
|-----------|--------|-------|------------|
| v1.0 | 8 | 11 | Established GSD workflow from scratch |
| v1.1 | 5 | 9 | First milestone with parallel waves; research disabled for CSS-heavy work |

### Top Lessons (Cross-Milestone)

1. **Extend, don't replace** — both v1.0 (CI) and v1.1 (CSS/PHP) succeeded by building on existing infrastructure, not rewriting it.
2. **Automated verification catches more than code review** — verifiers consistently caught issues (wrong product counts, stale CSS overrides) that planning missed.
