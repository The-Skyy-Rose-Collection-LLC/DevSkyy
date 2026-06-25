---
adr_id: "0001"
title: "V2 Locked Decisions — Page-Level and Architectural"
status: accepted
date: 2026-05-03
deciders: "Corey Foster (founder), DevSkyy engineering agent"
context: |
  The V2 Master Plan (docs/SKYYROSE_V2_MASTER_PLAN.md) defines two tables of decisions that are considered
  locked for the V2 build phase. Section §1.1 covers page-level decisions — which WordPress pages are in
  scope and what their implementation approach is. Section §1.2 covers architectural decisions — platform,
  integration, and system-level choices that all future work must conform to.

  These decisions exist to prevent scope creep, avoid re-litigating resolved questions, and give the
  engineering agent a clear constraint set to work within. "Locked" means: do not re-evaluate these during
  the V2 build unless the founder explicitly approves a revision. Open a new ADR if a locked decision must
  change.
decision: |
  The locked decisions from V2 §1.1 and §1.2 are ingested verbatim below and are operative for all V2 work.
  Any code, plan, or architecture that contradicts a row in these tables is out of bounds and must be
  corrected before merging.
consequences:
  positive:
    - Eliminates re-litigation of resolved questions (saves loops)
    - Gives the engineering agent a clear boundary for autonomous decisions
    - Provides a single authoritative reference for "what V2 is building"
  negative:
    - Rigid — if requirements change, this ADR must be explicitly updated
    - Some decisions (e.g., avatar rig-check, WebXR fallback) require dependencies outside the current team
  neutral:
    - Page implementations that are "carry-forward from v1" still need to be verified before V2 launch
    - Cost thresholds in §1.3 are superseded by eval/cost-cap-policy.md (see ADR 0002)
related_decisions:
  - "[adr: 0002]"
cross_refs:
  - "[v2: §1.1]"
  - "[v2: §1.2]"
  - "[v2: §1.3]"
  - "[wp: §1.5]"
  - "[serena: canonical_catalog_source_of_truth]"
  - "[serena: production_audit_findings]"
---

# V2 Locked Decisions — Page-Level and Architectural

## §1.1 — Page-Level Locked Decisions

Source: `docs/SKYYROSE_V2_MASTER_PLAN.md §1.1`

| Page / Template | Decision |
|-----------------|----------|
| `page-faq.php` | New page. Content from WP §4.x. Style: collection-palette awareness, accordion component. |
| `page-faq-2.php` | Variant FAQ layout. Scope TBD in Phase 1. |
| `page-shipping-returns.php` | New page. Plain editorial layout with SkyyRose brand tokens. |
| `page-shipping-returns-2.php` | Variant layout. Scope TBD in Phase 1. |
| `page-terms-of-service.php` | New page. Plain editorial layout. Legal text from founder. |
| `page-privacy-policy.php` | New page. Plain editorial layout. Legal text from founder. |
| `woocommerce/cart.php` | Override carried forward from v1 (holo card style preserved). Verify parity with WC 8.x in V2 smoke test. |
| `woocommerce/checkout.php` | Override carried forward from v1. Verify Stripe Checkout integration in V2 smoke test. |
| `template-collection-*.php` | Carry-forward from v1 with V2 refinements from WP §3.x. Collections: Signature, Black Rose, Love Hurts, Kids Capsule. |
| `template-immersive-*.php` | Carry-forward from v1. Love Hurts immersive refactored to single cathedral scene (cmem #1276). Black Rose remains 2-room. Verify rig-check before V2 launch. |
| `template-landing-*.php` | Carry-forward from v1. Three variants: black-rose, love-hurts, signature. |
| `template-style-quiz.php` | New V2 page. Scope and content defined in WP §5.x. |

**Constraint:** No new top-level page templates may be added to V2 scope without founder approval. New
template requests go to `tasks/todo.md` as proposals, not implementation tasks.

---

## §1.2 — Architectural Locked Decisions

Source: `docs/SKYYROSE_V2_MASTER_PLAN.md §1.2`

| Domain | Decision |
|--------|----------|
| **Platform** | WordPress.com Business plan (skyyrose.co) is the production store for V2. No migration to self-hosted WP. No headless-WP pivot. This is locked. |
| **Long-running work** | WordPress.com constraints (no wp-cli, SFTP deploy only, no direct DB access) are accepted. All automation must work within these constraints. No workarounds that require SSH command execution. |
| **FASHN cost cap** | FASHN virtual try-on is approved for use in V2 but governed by the cost-cap hybrid policy (see ADR 0002). Every FASHN call >$1 requires STOP-AND-SHOW confirmation. Batch runs require a manifest approved before execution. |
| **Pinecone cadence** | The `skyyrose-catalog` Pinecone index (Standard plan, us-west-2, dim=1024, cosine) is re-indexed on catalog changes only — not on every deploy. Index-on-change is the operative policy. |
| **Avatar rig-check** | The Skyy avatar (`assets/models/skyy.glb`) currently has 0 bones and 0 animations. Before any immersive template goes to V2 production launch, a rig-check gate must confirm idle + walk clips exist. No avatar animation work is in scope for V2 Phase 0–1; this is a Phase 2+ deliverable. |
| **Marketplace author URI** | The ThemeForest author URI is `https://themeforest.net/user/skyyrose` (or equivalent at time of submission). This string is frozen for V2 commercial release — do not change without founder approval. |
| **Drop queue** | The product drop / waitlist queue uses WebSocket for live count updates on the front-page portal rings. The WebSocket endpoint (`/ws/drop-queue`) is the canonical delivery mechanism — no polling fallback. |
| **WebXR fallback** | Immersive templates use Three.js `WebXRManager` for AR/VR. The fallback for unsupported browsers is a static product grid (not a reduced-functionality 3D view). This is the accepted degradation path. |
| **Eval failures** | If an eval score (fidelity gate, brand centroid gate) falls below threshold, the pipeline halts and logs to `.wolf/buglog.json`. No auto-retry on eval failure — a failing eval requires human review before re-running. |
| **Rollback strategy** | The hot-swap deploy (`scripts/deploy-theme.sh`) retains the previous theme directory as `.old.$swap_id` for 24 hours. Rollback is manual via SFTP. Automated rollback (bug-060) is a known gap — it is documented but not blocking V2 launch. |

**Constraint:** If any architectural decision above conflicts with a specific WP §N.x implementation spec,
the implementation spec is authoritative for that page/component. The architectural decisions govern platform
and system-level choices; WP §N.x governs component-level choices.

---

## How to Propose a Change to a Locked Decision

1. Open `tasks/todo.md` and add a proposal item with the ADR ID and the proposed change.
2. Write a brief rationale (1 paragraph) — what changed and why the original decision no longer holds.
3. Get explicit founder approval (verbal or in chat).
4. Open a new ADR (0003+) that supersedes the relevant row in this one.
5. Mark the superseded row in the §1.1 or §1.2 table with `[superseded by adr: NNNN]`.

Never silently violate a locked decision and rely on it going unnoticed. The V2 critique loop (WP §1.2)
includes an explicit check: "Does any implementation contradict a locked decision?"
