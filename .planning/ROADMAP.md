# Roadmap: SkyyRose WordPress

## Milestones

- :white_check_mark: **v1.0 Production Armor** - Phases 1-8 (shipped 2026-03-10)
- :construction: **v1.1 WordPress Quality & Accessibility** - Phases 9-13 (in progress)

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

<details>
<summary>v1.0 Production Armor (Phases 1-8) - SHIPPED 2026-03-10</summary>

- [x] **Phase 1: CI Failure Triage & Fix** - Remove 17 continue-on-error directives and fix the underlying failures they mask
- [x] **Phase 2: Husky Foundation** - Replace broken Husky v4 config with working v9 setup at monorepo root
- [x] **Phase 3: Pre-commit Hook Checks** - Wire up lint, type-check, PHP syntax, and fast tests on staged files
- [x] **Phase 4: PR Branch Protection** - Block merges to main unless all CI checks pass
- [x] **Phase 5: WordPress Build Pipeline** - Full minification of all JS and CSS theme files via single build command
- [x] **Phase 6: WordPress CI Integration** - CI validates PHP syntax, build output, and minification drift for theme files
- [x] **Phase 7: Deploy Core** - Transfer built theme to production via rsync/SSH with maintenance mode safety
- [x] **Phase 8: Deploy Verification & Orchestration** - Health checks, single-command pipeline, and dry-run mode

### Phase 1: CI Failure Triage & Fix
**Goal**: The CI pipeline produces hard failures on real problems -- no check is silently swallowed
**Depends on**: Nothing (first phase)
**Requirements**: CI-01, CI-02
**Success Criteria** (what must be TRUE):
  1. Running the CI pipeline on main with a deliberately broken lint rule causes the workflow to fail (red status), not warn
  2. All existing CI workflow runs on main pass green without any continue-on-error directives present
  3. A commit with a Python type error (mypy) or a JS lint error (ESLint) fails CI within the appropriate job
**Plans:** 2/2 plans complete

Plans:
- [x] 01-01: Fix underlying lint/format/type/test failures
- [x] 01-02: Remove all 17 continue-on-error directives

### Phase 2: Husky Foundation
**Goal**: Git hooks infrastructure is installed and functional at the monorepo root
**Depends on**: Nothing (independent of Phase 1)
**Requirements**: HOOK-07
**Success Criteria** (what must be TRUE):
  1. Running `git commit` on a staged file triggers a pre-commit hook
  2. The broken Husky v4 `husky.hooks` block is removed from package.json
  3. A `.husky/pre-commit` file exists and is executable
**Plans:** 1/1 plans complete

Plans:
- [x] 02-01: Initialize Husky v9, create hooks and verification script

### Phase 3: Pre-commit Hook Checks
**Goal**: Every commit is checked for lint, type, syntax, and test errors on staged files before it reaches the remote
**Depends on**: Phase 2
**Requirements**: HOOK-01, HOOK-02, HOOK-03, HOOK-04, HOOK-05, HOOK-06, HOOK-08
**Success Criteria** (what must be TRUE):
  1. Committing a staged JS file with an ESLint error blocks the commit
  2. Committing a staged Python file with a Ruff/Black/isort violation blocks the commit
  3. Committing a staged PHP file with a syntax error blocks the commit
  4. Committing a staged TypeScript file with a type error blocks the commit
  5. All pre-commit checks complete in under 30 seconds
**Plans:** 2/2 plans complete

Plans:
- [x] 03-01: Create lint-staged config, PHP lint wrapper, and wire pre-commit hook
- [x] 03-02: Create verification scripts and validate all HOOK requirements

### Phase 4: PR Branch Protection
**Goal**: No code reaches main without passing all CI checks via a pull request
**Depends on**: Phase 1
**Requirements**: PR-01, PR-02
**Success Criteria** (what must be TRUE):
  1. A PR with a failing CI check cannot be merged
  2. A PR whose branch is behind main cannot be merged until updated
  3. Agents can still create PRs and merge them when CI passes
**Plans:** 1/1 plans complete

Plans:
- [x] 04-01: Configure GitHub branch protection and required status checks

### Phase 5: WordPress Build Pipeline
**Goal**: All WordPress theme assets are minified from source via a single build command
**Depends on**: Nothing
**Requirements**: BUILD-01, BUILD-02, BUILD-03, BUILD-04
**Success Criteria** (what must be TRUE):
  1. `npm run build` produces .min.js files for all 43 JS source files
  2. `npm run build` produces .min.css files for all 55+ CSS source files
  3. Source maps (.map files) are generated alongside minified output
  4. A single `npm run build` command produces all minified output
**Plans:** 1/1 plans complete

Plans:
- [x] 05-01: Rewrite webpack config with dynamic entry discovery

### Phase 6: WordPress CI Integration
**Goal**: CI catches PHP errors and stale minified files in the WordPress theme before merge
**Depends on**: Phase 1, Phase 5
**Requirements**: CI-03, CI-04, CI-05
**Success Criteria** (what must be TRUE):
  1. A PHP syntax error in any theme file causes CI to fail
  2. CI runs `npm run build` and the build step passes
  3. Editing a source file without rebuilding causes CI to fail with drift error
**Plans:** 1/1 plans complete

Plans:
- [x] 06-01: Add wordpress-theme CI job

### Phase 7: Deploy Core
**Goal**: Built theme files can be transferred to production safely
**Depends on**: Phase 5
**Requirements**: DEPLOY-01, DEPLOY-02, DEPLOY-03, DEPLOY-07
**Success Criteria** (what must be TRUE):
  1. Deploy script transfers theme files via rsync over SSH
  2. Live site enters maintenance mode before file transfer
  3. Maintenance mode is disabled and cache flushed after transfer
  4. If deploy fails mid-transfer, maintenance mode is still disabled
**Plans:** 1/1 plans complete

Plans:
- [x] 07-01: Create deploy-theme.sh with rsync/lftp, maintenance mode, and trap safety

### Phase 8: Deploy Verification & Orchestration
**Goal**: Deploys are verified against the live site and triggered with a single command
**Depends on**: Phase 7
**Requirements**: DEPLOY-04, DEPLOY-05, DEPLOY-06
**Success Criteria** (what must be TRUE):
  1. After deploy, script verifies page content -- not just HTTP 200
  2. A single command runs full pipeline: build, transfer, verify
  3. Dry-run mode shows what would be transferred without deploying
**Plans:** 2/2 plans complete

Plans:
- [x] 08-01: Create verify-deploy.sh with deep content verification
- [x] 08-02: Create deploy-pipeline.sh with --dry-run support

</details>

### v1.1 WordPress Quality & Accessibility (In Progress)

**Milestone Goal:** Fix all accessibility errors, optimize responsive design, fix product placement, and polish the luxury cursor -- making the live site flawless.

- [ ] **Phase 9: Collection & Product Data** - Fix hero banners, product-to-collection assignments, and pre-order separation
- [x] **Phase 10: Accessibility HTML & ARIA** - Fix all HTML validation and ARIA errors in theme templates and enqueue (completed 2026-03-11)
- [x] **Phase 11: Color Contrast** - Bring all text to WCAG AA contrast ratios and fix price display (completed 2026-03-11)
- [ ] **Phase 12: Responsive & Typography** - Fix font scaling, layout overflow, touch targets, and type hierarchy across devices
- [ ] **Phase 13: Luxury Cursor** - Fix z-index conflicts with modals and conditional loading

## Phase Details

### Phase 9: Collection & Product Data
**Goal**: Every collection page shows its own correct hero banner and only the products that belong to it
**Depends on**: Nothing (independent quick wins with immediate user-visible impact)
**Requirements**: DATA-01, DATA-02, DATA-03
**Success Criteria** (what must be TRUE):
  1. The Black Rose collection page displays the Black Rose hero banner (not Love Hurts)
  2. Pre-order products (br-004, br-005, br-006, br-d01-d04, lh-001, sg-001, sg-d01) do not appear on live collection catalog grids
  3. Every product in the catalog grid belongs to the collection it appears under (no cross-collection leaks)
**Plans:** 2 plans

Plans:
- [ ] 09-01-PLAN.md -- Filter pre-orders from catalog grids and sync product data (DATA-02, DATA-03)
- [ ] 09-02-PLAN.md -- Diagnose and fix Black Rose hero banner (DATA-01)

### Phase 10: Accessibility HTML & ARIA
**Goal**: The theme's rendered HTML passes validation with zero ARIA errors and correct semantic structure
**Depends on**: Phase 9 (correct product data means templates render final HTML for a11y fixes)
**Requirements**: A11Y-01, A11Y-02, A11Y-03, A11Y-04, A11Y-05, A11Y-06, A11Y-07, A11Y-08, A11Y-09
**Success Criteria** (what must be TRUE):
  1. No duplicate element IDs appear in any page's rendered HTML (verified via Ally plugin or DOM inspection)
  2. Every button element has an explicit type attribute and every empty link has a descriptive aria-label
  3. Skip navigation link at the top of each page scrolls to the main content area when activated
  4. All form inputs (radio buttons, text fields, search) have associated labels or aria-label attributes
  5. Hero images load immediately (loading="eager") and below-fold images defer (loading="lazy")
**Plans:** 2/2 plans complete

Plans:
- [ ] 10-01-PLAN.md -- Fix button type attributes, enqueue handle collision, and duplicate IDs (A11Y-01, A11Y-02, A11Y-08)
- [ ] 10-02-PLAN.md -- Fix empty headings, empty links, ARIA attributes, form labels, skip nav, and image loading (A11Y-03, A11Y-04, A11Y-05, A11Y-06, A11Y-07, A11Y-09)

### Phase 11: Color Contrast
**Goal**: All text on the site meets WCAG AA contrast ratios and pricing displays correctly
**Depends on**: Phase 10 (HTML structure must be final before CSS contrast tuning)
**Requirements**: CNTR-01, CNTR-02, CNTR-03, CNTR-04
**Success Criteria** (what must be TRUE):
  1. Narrative subtext on dark backgrounds is readable (opacity/color adjusted to hit 4.5:1 contrast)
  2. Small text (10-12px) on interactive cards meets 4.5:1 minimum contrast ratio
  3. Love Hurts pre-order products display "Pre-Order" instead of "$0.00" pricing
  4. Running a contrast checker tool on any page produces zero AA failures for text elements
**Plans:** 2/2 plans complete

Plans:
- [ ] 11-01-PLAN.md -- Fix WCAG AA contrast in collection-v4, interactive-cards, and collections CSS (CNTR-01, CNTR-02, CNTR-03)
- [ ] 11-02-PLAN.md -- Replace $0 pricing with Pre-Order label for pre-order products (CNTR-04)

### Phase 12: Responsive & Typography
**Goal**: The site looks and works correctly across all screen sizes from 320px mobile to desktop
**Depends on**: Phase 11 (contrast fixes may adjust font sizes/weights that affect responsive layout)
**Requirements**: RESP-01, RESP-02, RESP-03, RESP-04
**Success Criteria** (what must be TRUE):
  1. Viewing any page at 320px viewport width shows no horizontal scrollbar and no content overflow
  2. All clickable/tappable elements on mobile are at least 44x44px touch targets
  3. Heading sizes and body text scale smoothly from mobile (320px) through tablet (768px) to desktop (1440px+)
  4. Typography hierarchy (h1 > h2 > h3 > body > small) is visually consistent across all page templates
**Plans**: TBD

Plans:
- [ ] 12-01: TBD

### Phase 13: Luxury Cursor
**Goal**: The custom luxury cursor works correctly everywhere including above modals and only loads where needed
**Depends on**: Phase 10 (modal/popup HTML structure must be finalized before z-index fixes)
**Requirements**: CURS-01, CURS-02, CURS-03
**Success Criteria** (what must be TRUE):
  1. When a modal or popup is open, the luxury cursor renders above it (not hidden behind)
  2. The cursor pauses its animation or adapts its behavior while a modal is active
  3. On immersive pages where the cursor is CSS-hidden, the luxury-cursor JS file is not loaded at all (no wasted bandwidth)
**Plans**: TBD

Plans:
- [ ] 13-01: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 9 -> 10 -> 11 -> 12 -> 13

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. CI Failure Triage & Fix | v1.0 | 2/2 | Complete | 2026-03-08 |
| 2. Husky Foundation | v1.0 | 1/1 | Complete | 2026-03-09 |
| 3. Pre-commit Hook Checks | v1.0 | 2/2 | Complete | 2026-03-09 |
| 4. PR Branch Protection | v1.0 | 1/1 | Complete | 2026-03-09 |
| 5. WordPress Build Pipeline | v1.0 | 1/1 | Complete | 2026-03-09 |
| 6. WordPress CI Integration | v1.0 | 1/1 | Complete | 2026-03-09 |
| 7. Deploy Core | v1.0 | 1/1 | Complete | 2026-03-09 |
| 8. Deploy Verification & Orchestration | v1.0 | 2/2 | Complete | 2026-03-10 |
| 9. Collection & Product Data | v1.1 | 0/2 | Planned | - |
| 10. Accessibility HTML & ARIA | 2/2 | Complete    | 2026-03-11 | - |
| 11. Color Contrast | 2/2 | Complete   | 2026-03-11 | - |
| 12. Responsive & Typography | v1.1 | 0/? | Not started | - |
| 13. Luxury Cursor | v1.1 | 0/? | Not started | - |
