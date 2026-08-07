# SkyyRose V2 release and adoption loop

**Run:** 2026-08-06 (America/Los_Angeles)  
**Owner:** `theme-release-engineer`  
**Scope:** package boundaries, generated artifacts, documentation/examples, previews,
validation, release governance, migrations, adoption, provider routing, and rollback.  
**Current disposition:** **BLOCKED**. The V2 contracts are planning artifacts; no
production theme or deployment target is changed by this loop.

## Release invariant

`PASS` means that one immutable candidate is ready for founder review. It never
authorizes a deployment, upload, paid provider call, protected-branch merge, or
production mutation. Missing, stale, skipped, timed-out, unavailable, or
mixed-candidate evidence is `UNVERIFIED` and fails closed.

The candidate identity is `v2-{git_sha}-{utc_timestamp}`. Every source, generated
artifact, preview, test result, browser trace, screenshot, commerce event, and
review record carries that candidate ID. A source mutation invalidates all proof
bound to the previous candidate and starts a fresh loop.

## Package and generated-artifact boundaries

- **Source:** V2 JSON contracts, Markdown contracts, role-owned source, and the
  canonical theme source. Source changes require an owner, reason, and review.
- **Generated:** minified CSS/JS, schema-derived fixtures, preview readers,
  manifests, screenshots, traces, and reports. Generated output is rebuilt from
  the candidate source; hand edits are rejected by generated-parity checks.
- **Package:** the plugin contains the 22 charters, governed references, Brain
  contracts, runtime overlay, scripts, examples, and visual readers. Runtime
  output, credentials, customer data, coverage files, and local caches are not
  package contents.
- **Examples/previews:** `preview.html`, `contract.json`, and `evidence.json`
  share stable route/section/component/evidence IDs. A reader is documentation,
  not storefront implementation proof.

## Bounded release loop

1. **Inventory:** freeze the worktree, candidate SHA, package manifest, source
   registries, dependency/tool versions, and the changed-file ownership map.
2. **Contract gate:** run `bash scripts/verify.sh`; parse every JSON contract with
   `jq`; check V2 schema shape, commerce state boundaries, motion budgets, proof
   evidence IDs, responsive matrices, and forbidden V2 language.
3. **Build gate:** run the repository's approved build, lint, type, unit, E2E,
   accessibility, performance, translation/RTL, license, dependency,
   generated-parity, and package-content checks. Record command, exit status,
   tool version, environment, timestamp, artifact path, SHA-256, owner, reviewer,
   and applicability for each gate.
4. **Evidence gate:** collect source provenance, 390x844/768x1024/1440x900
   captures, default/loading/empty/error/unavailable/long-content/keyboard/
   reduced-motion/fallback states, keyboard and screen-reader traces, touch and
   cancellation traces, performance telemetry, and WooCommerce commerce truth.
5. **Independent review:** visual QA, accessibility, performance, and security
   reviewers sign the same candidate. The builder and release engineer cannot
   self-approve visual pixels. Any reviewer change invalidates independence.
6. **Decision:** issue exactly `PASS`, `FAIL`, or `BLOCKED` with the evidence
   manifest. `PASS` is founder-review-ready only; `FAIL` returns to the owning
   lane; `BLOCKED` records the external dependency and resumes only after it
   changes.
7. **Archive:** retain the candidate manifest, changelog, migration notes,
   compatibility matrix, exclusions, rollback procedure, reviewer decisions,
   cost ledger, and learning entry. Never overwrite an earlier verdict.

## Required evidence fields

Every evidence record has:

```text
candidate_id, gate_id, command, status, tool_version, environment,
timestamp_utc, artifact_path, artifact_sha256, owner, reviewer, applicability
```

The V2 proof contract additionally requires source citation or explicit
authority, desktop/mobile captures, keyboard/screen-reader result, reduced-motion
and fallback result, performance budget result, and commerce truth for product,
price, inventory, and CTA state. Motion evidence expands this with candidate-
bound source/SKU/variation/rights fields, viewport/state captures, interaction and
cancellation traces, commerce events/idempotency, and independent review.

## Versioning, RFCs, migrations, and support

- Use SemVer for contract and package changes. Patch fixes preserve the contract;
  minor releases add backward-compatible fields; major releases remove or
  reinterpret fields only after an RFC and migration path.
- Each release has a changelog entry, compatibility notes, deprecation owner,
  first/last supported versions, codemod or migration steps, examples, and a
  rollback target. Deprecated fields remain readable for one documented minor
  window unless a security issue requires earlier removal.
- RFCs include motivation, alternatives, affected owners/packages, schema diff,
  accessibility/commerce/security impact, telemetry, rollout, and rollback.
  Contributions require the owning lane, design-system review, independent QA,
  and release-engineer evidence before merge.
- Support owns a reproducible issue template with candidate ID, route, state,
  browser/device, and evidence links. No support response upgrades UNKNOWN to a
  pass without new evidence.

## Adoption, telemetry, routing, and cost controls

- Adoption is measured per candidate and package version: contract validation
  pass rate, generated-parity drift, migrated surfaces, component/state coverage,
  accessibility/performance regression rate, rollback rate, and time-to-first-
  valid-evidence. Telemetry is aggregate and excludes customer data and secrets.
- Provider routing is capability-based and fail-closed. A provider must be
  declared in the candidate manifest with model/tool, purpose, context budget,
  retry ceiling, cost estimate, approval status, and redaction boundary. Keep
  tool definitions discoverable and callable; do not preload unused schemas.
- Context ceilings are measured per role and phase. Retries are bounded (two
  transient retries with preserved evidence); a third failure becomes a recorded
  blocker or returns to the owning lane. Paid providers, credentials, uploads,
  and remote writes require explicit founder approval before execution.
- The learning journal records the failure class, evidence gap, repair, cost,
  routing decision, and prevention rule. It must not retain secrets, customer
  payloads, hidden reasoning, or unapproved provider output.

## Rollback and externally unverified evidence

Rollback is a reversible pointer to the last founder-approved candidate and its
known-good generated artifacts. Before any approved deployment, record the
restore command, package/version, database or content migration reversal,
cache/invalidation steps, owner, observer, and stop condition. This loop never
deploys and cannot attest that rollback works until a candidate-bound rehearsal
provides executable evidence.

As of this run, the following remain externally **UNVERIFIED/BLOCKED**:

- browser-rendered V2 pages and all responsive/state screenshots;
- keyboard, screen-reader, touch, focus restoration, cancellation, and
  reduced-motion traces;
- WebGL/360/provider failure fallbacks and no-WebGL compact behavior;
- Lighthouse/Core Web Vitals, transfer/decode/memory/frame, overflow, and
  touch-target telemetry;
- WooCommerce product/variation/media/price/availability truth, cart and
  checkout idempotency, stock-race reconciliation, block/classic parity, and
  order/account/returns/service ownership traces;
- independent visual QA, accessibility, performance, and security sign-off;
- generated-artifact parity, installability against a clean target, migration
  rehearsal, rollback rehearsal, adoption baseline, and production authorization.

No claim above is upgraded by a successful `jq`, shell syntax, or static reader
check. Those checks establish package integrity only.
