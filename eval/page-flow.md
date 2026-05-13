---
name: IA / Navigation / Menu User-Journey Rubric
specified_by: [v2: §5 Phase 1.5]
phase: 0
test_command: node scripts/measurement/run-page-flow-eval.js  # PHASE 0.5 DELIVERABLE — script does not exist yet; running it will exit 1 with a 'Phase 0.5 not started' message until the runner is built. See scripts/measurement/README.md.
pass_threshold: Drop reachable in ≤ 2 clicks from any page; mobile drawer keyboard-navigable; breadcrumb JSON-LD validates
last_updated: 2026-05-03
last_updated_by: eval-harness (Phase 0)
---

# Page Flow / IA Eval Rubric

> **PLACEHOLDER STATUS:** This rubric's per-page user-journey rows are populated by Phase 1.5 (Site IA / navigation / menu redesign). Phase 0 establishes the schema and pass thresholds; Phase 1.5 fills in the rows.

## Pass criteria (set in Phase 0)

| Criterion | Method | Threshold |
|-----------|--------|-----------|
| Drop reachable from any page | Click-path audit via Chrome MCP | ≤ 2 clicks |
| Mobile drawer keyboard-navigable | Tab cycle through nav; Esc closes | All elements reachable; cycle complete; Esc closes drawer |
| Breadcrumb JSON-LD validates | Submit a representative page URL to schema.org validator | 0 errors |
| Active state on current page | Visual inspection per page | Active state visually distinct, accessible |
| Mega menu hover/focus | Hover + keyboard trigger | Both work; focus ring visible on keyboard activation |
| Footer completeness | Audit footer per page | Every legal page linked; social present; newsletter capture present; contact email visible |
| Header accessibility | Screen reader pass | Logo has aria-label; nav has role="navigation"; current page has aria-current |
| Sticky header behavior | Scroll test | Fades in shadow at scroll > 100px; logo compacts |

## Per-page row format (populated Phase 1.5)

```yaml
---
page: <slug>
arrival_paths:
  - source: <page slug or external>
    intent: <what the customer is here to do>
next_actions:
  - target: <slug>
    visibility: <obvious | discoverable | hidden>
    importance: <primary | secondary | tertiary>
primary_cta: <one-line>
secondary_ctas:
  - <one-line>
clicks_to_drop_page: <integer>
mobile_drawer_pass: <bool>
breadcrumb_jsonld_pass: <bool>
last_evaluated: <YYYY-MM-DD>
status: <PASS | FAIL | PENDING>
---

<prose: customer journey rationale, friction points, design decisions>
```

## Surfaces to populate (per V2 §6)

All 27 final pages get a row in Phase 1.5. The current 29 → 27 page transition (after deleting `faq-2` + `shipping-returns-2` per V2 §1.1) is the basis for the row count.

## Test command

```bash
node scripts/measurement/run-page-flow-eval.js
```

Reads all per-page rows; exits 0 on PASS (all required pages present + all pass thresholds met) or 1 on FAIL.

## Phase 1.5 entry note

When Phase 1.5 begins, this file is populated by the UX Architect agent + `wordpress-pro` agent working in sequenced handoff. The first deliverable of Phase 1.5 is filling every row in this file; the second is building the IA changes that match the rows.
