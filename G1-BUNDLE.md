---
name: G1 Phase 0 Review Bundle (Skyyrose V2 Build)
phase: 0
gate: G1
last_updated: 2026-05-03
last_updated_by: agents-orchestrator
plan_source: /Users/theceo/.claude/plans/merry-shimmying-moonbeam.md
---

# G1 STOP — Phase 0 Review Bundle

**Status:** Phase 0 deliverables complete. Awaiting your review at G1 before any code touches customer surfaces.

**Plan:** `/Users/theceo/.claude/plans/merry-shimmying-moonbeam.md` (unified V2 + WP plan, Phase 0 scope only).

**Branch:** `hotfix/p0-pdp-500-and-brand-violations` — 56 commits ahead of `main`, 2 behind. Phase 0 work landed in 6 atomic commits on top of 5 prior hotfix commits already deployed to skyyrose.co.

---

## What you're looking at

This bundle answers three questions, in order:

1. **Did Phase 0 ship its deliverables?** Yes — see § "Deliverables landed" below.
2. **Is anything still broken or unsafe?** Two items need your manual action; everything else is green. See § "Open items".
3. **What does Phase 1 look like?** Next planning cycle, after you approve. See § "After G1".

If you want the one-line verdict: **Phase 0 is done; sign off and we move to Phase 0.5 measurement provisioning.**

---

## Hotfix branch — production state alongside Phase 0

The Phase 0 work was layered on a live hotfix branch that had already shipped 5 fixes to `skyyrose.co`. So the production site is in a known-good state right now, independent of Phase 0:

| Surface | HTTP | Notes |
|---------|------|-------|
| `skyyrose.co/` | 200 | Homepage healthy |
| `skyyrose.co/product/black-rose-crewneck/` | 301 | PDPs no longer 500ing — redirect to canonical URL works |
| `skyyrose.co/cart/` | 200 | Cart functional |

The hotfix commits already on this branch (and live):
- 5dd55c187 — replace "Bay Area" with "Oakland" / "The Town" per brand canon
- ee151109a — remove broken countdown timers; fix landing CTAs
- 2208d3d08 — define `SKYYROSE_FREE_SHIPPING_THRESHOLD` constant
- 303904676 — `/collections/{slug}/` → `/collection-{slug}/` 301 redirects
- (one more upstream — check `git log --oneline main..HEAD | tail`)

Phase 0 commits stack on top of these without touching customer-facing PHP.

---

## Deliverables landed (commits 295a1bd0d → 4947e1cb0)

### A. Source-of-truth persistence
- `docs/SKYYROSE_V2_MASTER_PLAN.md` (V2 master plan as-pasted)
- `docs/SKYYROSE_WORDPRESS_PLAN.md` (WP plan as-pasted)
- `docs/PLAN_INDEX.md` (cross-reference)

### B. Eval rubric files (17 total in `eval/`)
V2 Phase 0 (6): `templates.md`, `integrations.md`, `marketplace.md`, `shocking.md`, `brand.md`, `page-flow.md`
WP foundation (7): `brand-story.md`, `banned-elements.md` (17 banned defaults), `luxury-references.md`, `premium-feel.md`, `commercial-protocols.md`, `design-system.json` (root, schema-bound), `critique/current-site-audit.md`
Phase 0 governance (4): `cost-cap-policy.md`, `agent-skill-inventory.md`, `silent-disable-audit.md`, `measurement-access-requests.md`, `blocking-prerequisites.md`

### C. Knowledge base scaffold
- `knowledge-base/README.md` — schema, integration map across 4 prior memory systems (OpenWolf / Serena / GSD / claude-mem)
- `knowledge-base/lessons/anti-patterns.md` — **16 anti-patterns seeded** (WP §1.5 Layer 5 + AP-16 glob-fishing from this session)
- `knowledge-base/decisions/` — **3 ADRs** (0001 V2 locked decisions, 0002 cost-cap hybrid, 0003 imagery-as-launch-blocker)
- `knowledge-base/seed/` — **5 cross-system indices** (`from-claude-mem.md`, `from-gsd.md`, `from-interview.md` ← **PRIMARY brand canon**, `from-openwolf.md`, `from-serena.md`)
- `knowledge-base/patterns/` — empty (populated by every loop hereafter via `kb-distill.js`)

### D. Per-edit toolchain (4 scripts, `scripts/`)
- `verify-impl.js` — Step 2 of 6-step workflow (canonical-source cross-check)
- `kb-distill.js` — Step 6 (writes `knowledge-base/patterns/<domain>/<slug>.md`)
- `post-simplify-verify.js` — Step 4 (4-check revert protocol)
- `_lib/script-utils.js` — shared utilities (PROJECT_ROOT, utcTimestamp, run, deriveTaskId)

### E. Design system primitives (10 files, `wordpress-theme/skyyrose-flagship/template-parts/components/`)
`button.php`, `input.php`, `form.php`, `card-product.php`, `card-editorial.php`, `card-info.php`, `figure.php`, `quote.php`, `modal.php`, `drawer.php`. PHPCS WordPress-standard clean. Helpers (`skyyrose_build_attr_string`, `skyyrose_sanitize_class_list`) in `inc/template-functions.php`.

### F. Per-directory AGENTS.md files
93 `AGENTS.md` files across the repo enforce V2 §0.4 scope rules.

### G. Knowledge graph (`graphify-out/`)
Full corpus graph built across `.planning/`, `.serena/memories/`, `.wolf/`, `knowledge-base/`, `docs/`, `tasks/lessons.md`, `wordpress-theme/skyyrose-flagship/inc/`, `wordpress-theme/skyyrose-flagship/template-parts/`. `graph.json` + `GRAPH_REPORT.md` tracked; intermediate caches gitignored.

### H. Cost-cap policy (binding contract)
`eval/cost-cap-policy.md` supersedes both `CLAUDE.md` STOP-AND-SHOW and V2 §1.3 in isolation. **Rule:** any single paid call >$1 → STOP-AND-SHOW; ≤$1 → autonomous up to per-service threshold (Anthropic $25, Pinecone $10, FASHN 30 calls, AIDesigner 50 gens). Per-API table enumerates every paid endpoint with policy side.

### I. Silent-disable audit
`eval/silent-disable-audit.md` documents 8 instances of "configured but silently disabled" anti-pattern surfaced during MCP investigation. **5 fixed** (S1, S2, S5, MCP key gotcha, scopes regression). 2 require your manual action (S3 WP password rotation, S4 aidesigner OAuth click-through).

---

## Open items (your hands needed)

Two items block exit from "Phase 0 fully closed" but don't block starting Phase 0.5 planning:

| ID | Item | Action needed | Risk if skipped |
|----|------|---------------|-----------------|
| **S3** | WP application password sat in plaintext in `~/.claude.json` | Rotate via `wp-admin/profile.php → Application Passwords → Revoke + regenerate` | Medium — credential is on local disk only, but rotate before next deploy |
| **S4** | aidesigner MCP returns 401 | Click through OAuth in browser when prompted by `mcp__aidesigner__authenticate` | Low — CLI path (`npx @aidesigner/agent-skills`) works via `AIDESIGNER_API_KEY` in `.env` regardless |

Both tracked in `eval/silent-disable-audit.md` with reproduction + resolution status.

---

## Verification status (V2 §0.3 checks)

- ✅ All 17 eval rubric files have YAML frontmatter (`/verification-loop` clean after cost-cap-policy.md fix in commit 4a4766f26)
- ✅ KB has 16 lessons + 3 decisions + 5 seed indices (exceeds V2 Phase 0 floor of 10/5)
- ✅ 3 self-testing scripts (`verify-impl.js`, `post-simplify-verify.js`, `kb-distill.js`) pass `--self-test`; `_lib/script-utils.js` is a shared utility module imported by the other three (no own `--self-test` path)
- ✅ PHPCS WordPress-standard 0 errors / 0 warnings on 10 component primitives
- ✅ `npm run lint:md` passes on all eval files
- ✅ Live skyyrose.co healthy (homepage + PDP redirect + cart all return expected HTTP)

---

## What `/simplify` and `/verification-loop` caught

- **/simplify** (commit 5ee5a9398) — 4 HIGH bugs in PHP primitives (form/drawer/modal slot escape paths, input.php name mismatch, card-product trailing-dash, allowed_svg dedup); MED refactors to extract attr-string + class-list helpers across all 10 primitives; JS toolchain duplication eliminated via `_lib/script-utils.js`.
- **/verification-loop** (commit 4a4766f26) — `eval/cost-cap-policy.md` was missing YAML frontmatter; added with `name`, `specified_by`, `phase`, `last_updated`, `last_updated_by`, `authority` fields. Doc now indexable.

---

## After G1 — Phase 0.5 preview

If you sign off on G1, the next planning cycle (per the per-phase protocol in the plan file) will produce a fresh Phase 0.5 plan informed by:

1. **Measurement access requests packet** (`eval/measurement-access-requests.md`) — already generated; you'd action the grants in one sitting.
2. **Prerequisite checks** — Stripe, FASHN, Pinecone, Anthropic, WP REST, Vercel, Pusher, GLB rig (V2 §5.0 prereq for 5.6/5.8).
3. **Baseline capture** — 10 KPIs from WP §9, weekly cron, `/admin/measurement` dashboard on devskyy.app.
4. **Critique completion** — fill KPI baseline columns in `eval/critique/current-site-audit.md`.

No code touches customer surfaces in Phase 0.5 either; that starts at Phase 1 (admin cleanup via WP REST API only).

---

## How to review

Three review styles, pick whichever fits:

**Quick (5 min)** — read this file, then skim:
- `eval/silent-disable-audit.md` (audit findings)
- `knowledge-base/seed/from-interview.md` (brand canon)
- `eval/cost-cap-policy.md` (binding cost rule)

**Medium (20 min)** — add:
- `eval/critique/current-site-audit.md` (live site verdict)
- `knowledge-base/decisions/0003-imagery-as-launch-blocker.md` (Phase 5 reorder rationale)
- `git log --oneline 295a1bd0d^..HEAD` (6 Phase 0 commits)

**Deep (60+ min)** — add:
- All 17 `eval/*.md` rubric files
- `knowledge-base/lessons/anti-patterns.md` (16 entries including AP-16 glob-fishing)
- `wordpress-theme/skyyrose-flagship/template-parts/components/` (10 primitives)
- `graphify-out/GRAPH_REPORT.md` (corpus topology)

---

## Sign-off

To exit G1 and authorize Phase 0.5 planning:

> "G1 approved. Plan Phase 0.5."

To request changes:

> List specific items in `eval/silent-disable-audit.md` resolution-status table format, or pick a deliverable file and annotate.

To rotate scope:

> Re-enter plan mode for a fresh plan in any direction.
