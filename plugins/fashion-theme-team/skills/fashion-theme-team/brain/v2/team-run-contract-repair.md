# V2 Contract Repair Change Log

**Run:** 2026-08-06 · contract repair lane  
**Scope:** V2 machine plan, imagery plan, and local schema only. No production theme files or verify scripts changed.

- Removed urgency-widget permissions from campaign and coming-soon routes; release status is static and terms-first.
- Replaced generic merchandising wording with a verified alternate path that requires catalog relationship, source SKU, reason, availability, and checkout recovery proof.
- Added identity-backed collection accent, dark-accent, lockup, hero-status, and non-shippable media fields for Black Rose, Love Hurts, Signature, and Kids Capsule.
- Added canonical token/font source map, drift rule, shot manifest contract, SOT/rights references, fail-closed provenance fields, and review expiry.
- Added route-bound 390/768/1440 responsive contracts, seven required runtime states, ten CTA states, one-showpiece motion budgets, cancellation/reduced-motion rules, rhythm limits, and acceptance evidence IDs to all 28 pages.
- Added local v2-page-plan.schema.json and set the plan’s $schema to it.

## Checks

- jq empty for plan and schema: PASS.
- JSON Schema Draft 2020-12 validation: PASS (28 pages).
- Assigned-file forbidden-term scan: PASS.
- Runtime/browser captures, accessibility traces, token-drift scans, and independent visual QA remain UNVERIFIED by design.

