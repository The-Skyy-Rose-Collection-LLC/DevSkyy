# Roadmap: SkyyRose WordPress

## Milestones

- ✅ **v1.0 Production Armor** — Phases 1-8 (shipped 2026-03-10)
- ✅ **v1.1 WordPress Quality & Accessibility** — Phases 9-13 (shipped 2026-03-11)
- 📋 **v1.2 Imagery Pipeline — CSV-Driven Product Photography** — Phases 14-18 (in progress)

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

<details>
<summary>✅ v1.1 WordPress Quality & Accessibility (Phases 9-13) — SHIPPED 2026-03-11</summary>

- [x] **Phase 9: Collection & Product Data** — Pre-order filtering, product catalog sync, hero banners (completed 2026-03-11)
- [x] **Phase 10: Accessibility HTML & ARIA** — ARIA errors, button types, skip nav, image loading (completed 2026-03-11)
- [x] **Phase 11: Color Contrast** — WCAG AA contrast fixes, pre-order price display (completed 2026-03-11)
- [x] **Phase 12: Responsive & Typography** — 320px overflow, 44px touch targets, fluid type tokens (completed 2026-03-11)
- [x] **Phase 13: Luxury Cursor** — z-index supremacy, modal pause/resume, conditional loading (completed 2026-03-11)

</details>

**v1.2 Imagery Pipeline — CSV-Driven Product Photography (Phases 14-18)**

- [ ] **Phase 14: Catalog Foundation** — CSV adapter, bundle resolver, broken reader fixes, garment_type_lock column, techflat labeling, preflight audit. Zero API calls.
- [ ] **Phase 15: Ghost Mannequin Agent + QA** — LangGraph agent, 2-step pipeline, garment-type routing, response classifier, retry logic, spend cap, background validator.
- [x] **Phase 16: 3D-Replica Architect & Purge** — 3D-first pipeline (Meshy → headless Blender → Gemini 2.0 RAS) + hallucinated-asset purge. Shipped 2026-04-24, ahead of Phases 14/15. Original "Jersey OCR Gate" plan was dropped — see Phase 16 note below.
- [ ] **Phase 17: Review & Approval CLI** — approve/reject CLI commands, approved/ structural gate, CSV atomic write.
- [ ] **Phase 18: Full Batch + WooCommerce Upload** — Run all 28 in-scope garment SKUs, batch WooCommerce upload after 100% approval.

## Phase Details

### Phase 9: Collection & Product Data
**Goal**: Every collection page shows its own correct hero banner and only the products that belong to it
**Depends on**: Nothing (independent quick wins with immediate user-visible impact)
**Requirements**: DATA-01, DATA-02, DATA-03
**Success Criteria** (what must be TRUE):
  1. The Black Rose collection page displays the Black Rose hero banner (not Love Hurts)
  2. Pre-order products (br-004, br-005, br-006, br-d01-d04, lh-001, sg-001, sg-d01) do not appear on live collection catalog grids
  3. Every product in the catalog grid belongs to the collection it appears under (no cross-collection leaks)
**Plans:** 2/2 plans complete

Plans:
- [x] 09-01-PLAN.md -- Verify pre-order filter and cross-collection integrity via CSV integrity test (DATA-02, DATA-03)
- [x] 09-02-PLAN.md -- Verify Black Rose hero asset on live + close stale DATA-01 requirement (DATA-01)

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
**Plans:** 2/2 plans complete

Plans:
- [ ] 12-01-PLAN.md -- Fix horizontal overflow at 320px and touch targets to 44x44px minimum (RESP-02, RESP-03)
- [ ] 12-02-PLAN.md -- Replace hardcoded font sizes with clamp()/design tokens and enforce typography hierarchy (RESP-01, RESP-04)

### Phase 13: Luxury Cursor
**Goal**: The custom luxury cursor works correctly everywhere including above modals and only loads where needed
**Depends on**: Phase 10 (modal/popup HTML structure must be finalized before z-index fixes)
**Requirements**: CURS-01, CURS-02, CURS-03
**Success Criteria** (what must be TRUE):
  1. When a modal or popup is open, the luxury cursor renders above it (not hidden behind)
  2. The cursor pauses its animation or adapts its behavior while a modal is active
  3. On immersive pages where the cursor is CSS-hidden, the luxury-cursor JS file is not loaded at all (no wasted bandwidth)
**Plans:** 1/1 plans complete

Plans:
- [ ] 13-01-PLAN.md -- Fix z-index supremacy, add modal-aware pause/resume, verify conditional loading (CURS-01, CURS-02, CURS-03)

---

### Phase 14: Catalog Foundation
**Goal**: Every imagery pipeline reads from a single, validated CSV adapter and every in-scope SKU has a verified techflat-front before any API call is made
**Depends on**: Nothing (first phase of v1.2 — zero API calls, zero cost)
**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04, INFRA-05, INFRA-06, INFRA-07
**Success Criteria** (what must be TRUE):
  1. `from skyyrose.core.catalog_loader import read_catalog_rows` works in nano-banana, Elite Studio compositor, and FLUX orchestrator without import errors
  2. `python scripts/preflight_audit.py` exits 0 and writes `SKIPPED.json` listing only sg-007 and lh-005 as out-of-scope — all 28 in-scope garment SKUs resolve bundle + techflat-front
  3. `skyyrose-catalog.csv` contains a `garment_type_lock` column with a non-empty value for every in-scope SKU
  4. All techflat source files for in-scope SKUs are single-view images (no compound sheets) and filenames follow the standard before pipeline intake
  5. `/simplify` — code simplification pass after phase implementation
  6. `/verification-loop` — automated verification loop confirming all success criteria pass
**Plans:** 3 plans

Plans:
- [ ] 14-01-PLAN.md — Add garment_type_lock CSV column, Wave 0 tests, nano_banana package marker (INFRA-04)
- [ ] 14-02-PLAN.md — Fix 3 broken readers: nano_banana.catalog shim, renders/config.py, fashion/context.py (INFRA-01, INFRA-02, INFRA-03)
- [ ] 14-03-PLAN.md — Preflight audit script + SKIPPED.json (INFRA-05, INFRA-06, INFRA-07)

### Phase 15: Ghost Mannequin Agent + QA
**Goal**: The ghost mannequin LangGraph agent can generate a validated, white-background front shot for any single in-scope garment SKU without crashing, overspending, or silently returning a broken image
**Depends on**: Phase 14 (catalog adapter and preflight audit must pass before any generation run)
**Requirements**: GM-01, GM-02, GM-03, GM-04, GM-05, GM-06, QA-01, QA-02, QA-04
**Success Criteria** (what must be TRUE):
  1. Running `python -m skyyrose.elite_studio.agents.ghost_mannequin_agent --sku sg-001 --dry-run` prints a full cost manifest (SKU, API, per-image cost, total cost) and exits without making any API call
  2. Running the agent against one non-jersey garment SKU produces `renders/ghost-mannequin/{sku}-ghost-front.webp` at 1200x1200px with all four corner pixels within 5 RGB units of (255, 255, 255)
  3. A simulated 429 response triggers exponential backoff retry; a simulated safety block immediately flags the SKU to `failures.json` without retrying
  4. sg-007, lh-005, and any SKU not resolved by the bundle resolver are silently skipped with their reason written to `failures.json` — no exception raised, no abort
  5. A run that would exceed the configured spend cap halts before the cap-crossing API call and exits with a clear message showing amount spent and amount remaining
  6. `/simplify` — code simplification pass after phase implementation
  7. `/verification-loop` — automated verification loop confirming all success criteria pass
**Plans**: TBD

### Phase 16: 3D-Replica Architect & Purge ✅ (completed 2026-04-24)
**Goal**: The image generation pipeline produces high-fidelity professional renders by digitizing techflats into 3D (.glb) replicas, scaffolding them via headless Blender, and synthesizing final shots with Gemini 2.0 RAS — and all hallucinated/invalid catalog assets are purged.
**Depends on**: Nothing (independent architectural upgrade — shipped ahead of Phases 14/15)
**Requirements**: THREE-01, PURGE-01, CLI-01, VISION-01, ROTATE-01, GRAPH-01 (see `phases/16-3d-replica-architect-purge/16-VALIDATION.md`)
**Success Criteria** (what was TRUE at sign-off):
  1. `ThreeDAgent.generate_replica` produces a `.glb` model + scaffolded render + final synthesized image for any in-scope SKU
  2. The `three_d_node` is wired into the LangGraph builder behind the `enable_3d` flag and replaces the standard generator when active
  3. `purge_hallucinations.py` identifies and removes invalid/hallucinated assets (32 removed in initial run)
  4. Gemini API key rotation handles 429 rate limits without operator intervention
  5. Full UAT (`16-UAT.md`) and validation suite (`16-VALIDATION.md`) run green — 34 tests pass across 6 files
**Plans:** Complete — see `phases/16-3d-replica-architect-purge/16-SUMMARY.md`

> **Note — Original Phase 16 ("Jersey OCR Gate") was dropped.** The original plan to add a Gemini-Vision OCR verification node for jersey SKUs (br-003, br-008, br-009, br-010, br-011, br-012) was superseded by the 3D-Replica architecture, which produces verifiable text/number rendering through scaffold-grounded synthesis rather than post-hoc OCR. **Requirement QA-03 is no longer in scope** for v1.2 — Phase 18's jersey SKU run no longer depends on a separate OCR gate. (`REQUIREMENTS.md` still lists QA-03 as Pending and should be reconciled in a follow-up doc-only pass.)

### Phase 17: Review & Approval CLI
**Goal**: The user can approve or reject each generated image from the command line, and approved images are atomically committed back to the CSV with zero risk of data corruption
**Depends on**: Phase 15 (review directory and output files must exist before approval tooling is needed)
**Requirements**: REV-01, REV-02, REV-03, REV-04
**Success Criteria** (what must be TRUE):
  1. Running `approve-ghost {sku}` on an image not yet in `renders/ghost-mannequin/approved/` moves it there, updates `front_model_image` in the CSV, and writes an approval timestamp — the CSV row count after update equals the row count before
  2. Running the CSV update tool when `approved/{sku}-ghost-front.webp` does not exist exits with code 1 and a clear error — no CSV modification occurs
  3. Running `reject-ghost {sku} "{reason}"` leaves the file in the review directory, writes the reason to `rejections.json`, and makes no CSV change
  4. Interrupting `approve-ghost` mid-write (simulated via SIGINT after temp file creation) leaves the original CSV intact — the atomic `os.replace()` pattern prevents partial writes
  5. `/simplify` — code simplification pass after phase implementation
  6. `/verification-loop` — automated verification loop confirming all success criteria pass
**Plans**: TBD

### Phase 18: Full Batch + WooCommerce Upload
**Goal**: All 28 in-scope garment SKUs have a ghost mannequin front image approved by the user and uploaded to WooCommerce — with an explicit confirmation gate before any production write occurs
**Depends on**: Phase 15, Phase 17 (agent complete, approval CLI ready). The original Phase 16 jersey OCR-gate dependency was dropped — see Phase 16 note above. Jersey SKU verification is now handled by the 3D-Replica scaffold-grounded synthesis instead of a separate OCR node.
**Requirements**: UPLOAD-01
**Success Criteria** (what must be TRUE):
  1. Running the batch agent against all 28 in-scope SKUs completes without unhandled exceptions — every SKU either produces an output file or has a logged entry in `failures.json`
  2. Before any WooCommerce API write, a STOP AND SHOW manifest is displayed listing every SKU, target product ID, and image path — the upload does not proceed until the user types "y"
  3. After confirmed upload, each approved product's WooCommerce image field reflects the new ghost mannequin image (verified via WooCommerce REST API GET response)
  4. Any SKU without a corresponding `approved/{sku}-ghost-front.webp` is excluded from the upload manifest entirely — the upload tool cannot be coerced into uploading unapproved files
  5. `/simplify` — code simplification pass after phase implementation
  6. `/verification-loop` — automated verification loop confirming all success criteria pass
**Plans**: TBD

## Progress

**Execution Order:**
v1.0: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8
v1.1: 9 → 10 → 11 → 12 → 13
v1.2: 14 → 15 → 17 → 18 ; Phase 16 (3D-Replica Architect & Purge) shipped independently 2026-04-24 — original "Jersey OCR Gate" plan was dropped, no phantom dependency for Phase 18

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
| 9. Collection & Product Data | v1.1 | 2/2 | Complete   | 2026-05-12 |
| 10. Accessibility HTML & ARIA | v1.1 | 2/2 | Complete | 2026-03-11 |
| 11. Color Contrast | v1.1 | 2/2 | Complete | 2026-03-11 |
| 12. Responsive & Typography | v1.1 | 2/2 | Complete | 2026-03-11 |
| 13. Luxury Cursor | v1.1 | 1/1 | Complete | 2026-03-11 |
| 14. Catalog Foundation | v1.2 | 0/3 | Not started | - |
| 15. Ghost Mannequin Agent + QA | v1.2 | 0/TBD | Not started | - |
| 16. 3D-Replica Architect & Purge | v1.2 | Shipped | Complete | 2026-04-24 |
| 17. Review & Approval CLI | v1.2 | 0/TBD | Not started | - |
| 18. Full Batch + WooCommerce Upload | v1.2 | 0/TBD | Not started | - |
