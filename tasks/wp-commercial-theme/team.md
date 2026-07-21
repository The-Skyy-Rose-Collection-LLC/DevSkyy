# WP Commercial Theme Team — skyyrose.co

Goal: every page aesthetically aligned with commercial WordPress theme standards
(headers aligned, heroes visually sound) AND Lighthouse ≥90 all four categories,
mobile + desktop. Award-grade finish.

## Roster (5 specialists)

| Name | Role | Agent type | Owns |
|------|------|-----------|------|
| **Atlas** | Theme Architect | wp-theme-dev | Template hierarchy, functions.php, inc/ modules, enqueue map, .min build integrity |
| **Pixel** | Visual Design Lead | wp-frontend | Headers, heroes, spacing, typography canon, brand alignment per page |
| **Bolt** | Performance Engineer | general-purpose | Lighthouse perf: LCP/CLS/TBT, asset weight, render-blocking, image sizing |
| **Access** | A11y + SEO Auditor | Accessibility Auditor | Lighthouse a11y/SEO/best-practices categories, WCAG 2.2 AA, schema |
| **Sentinel** | QA Verifier | theme-heal-verifier-style | Independent re-verification: fresh curls, fresh Lighthouse, Playwright eyes-on. Never trusts a fixer's self-report |

## Operating rules
- Fix SOURCE then rebuild .min (`npm run build` from wordpress-theme/). Verify BOTH.
- Deploy only from main checkout (17 gitignored riders — clean-tree deploy deletes them).
- Deploy = standing auth AFTER clean sweep + manifest shown. Paid/WC/media writes still need y.
- Product imagery: SOT-only (data/sot-images.json), eyes-on garment↔SKU gate before any image touches the site.
- No `--amend`/`reset` — shared worktree; new commits only.
- Every claim verified by a method that can fail. Sentinel re-derives, never trusts.

## State
- pages.txt — 20 URLs covering every distinct template (30 published pages total; 2nd wave audits template-siblings post-fix)
- baseline/summary.csv — Lighthouse scores (mobile+desktop per URL)
- architecture-census.md — Atlas output
- visual-audit.md — Pixel output
- fix-log.md — applied fixes per iteration
