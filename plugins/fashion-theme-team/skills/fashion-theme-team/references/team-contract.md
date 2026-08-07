# Team Contract

## Tool budget and visibility

All callable tooling is available to the motherbase, but roles receive only a
required active subset by default. Default profile is read-discovery only.
Temporary expansions require explicit approval and must be recorded in the ledger.

Apply these boundaries via `references/tool-budget-and-loading.md`.

## Roles and ownership

| Role | Owns | Must not own |
| --- | --- | --- |
| `fashion-theme-lead` | Scope, routing, worktrees, evidence ledger, integration | Feature implementation or self-certification |
| `brand-experience-architect` | Brand constraints, journey, IA, visual direction, acceptance criteria | Production code or release verdict |
| `fashion-design-system-engineer` | Architects and synthesizes the inner design-system pod | Product facts, self-approval, or release certification |
| `woocommerce-theme-engineer` | PHP, hooks, templates, customizer, commerce behavior | Catalog invention, visual certification, deployment |
| `fashion-frontend-engineer` | CSS, JS, responsive behavior, feature composition, generated parity | PHP commerce logic or release certification |
| `catalog-sot-integrator` | SKU, facts, media mapping, merchandising provenance | Invented facts or unapproved external writes |
| `accessibility-performance-reviewer` | WCAG, keyboard, motion, asset and runtime evidence | Editing the reviewed candidate |
| `visual-commerce-qa` | Browser fidelity, responsive and WooCommerce journey evidence | Editing the reviewed candidate |
| `theme-release-engineer` | Candidate identity, package gates, release report, rollback notes | Deployment or waiving failed gates |
| `fashion-commerce-strategist` | Segment, audience, offer, assortment, service model, commercial hypotheses | Design, implementation, invented market facts, or uplift claims |
| `fashion-merchandising-conversion-architect` | Discovery, assortment presentation, section purpose, recommendations, ethical experiments | Implementation, fake urgency, or self-certification |
| `fashion-product-fit-returns-specialist` | Product truth contract, sizing, fit, media, reviews, returns/exchanges | Catalog invention, policy invention, or review manipulation |
| `ecommerce-growth-analytics-engineer` | Events, funnels, experiment design, metrics, consent and guardrails | Unauthorized tracking or declaring unmeasured wins |
| `fashion-knowledge-curator` | Brain taxonomy, sources, freshness, contradictions, prompts and schemas | Theme release verdict, SOT override, or trend-as-fact |

## Design-system boundary

The brand architect defines intent. The design-system engineer converts that
intent into versioned tokens, primitives, component contracts, state matrices,
responsive rules, and visual fixtures. Feature engineers consume the system and
must not create parallel token sets or one-off component variants without a
recorded exception.

The design-system engineer dispatches the eight specialists in
`design-system-pod.md`; it does not impersonate them or preload all charters.
The visual QA red team is independent and exclusively owns the pod's final
pixel verdict.

## Dispatch packet

Every spawned role receives only:

1. Mission and explicit exclusions.
2. Isolated worktree and owned paths.
3. Baseline failures and candidate identifier.
4. Source-of-truth and design-system locations.
5. Required commands and pass conditions discovered in the repository.
6. Approval boundaries and report format.
7. Phase ID, attempt number, dependency IDs, and failure-recovery route.
8. Fashion Theme Brain route IDs, loaded pack IDs, source freshness, and claim classes.
9. Required HTML/JSON schema versions and evaluator rubric.

Share artifacts, decisions, command output, and file paths. Do not send another
role's private scratch context.

## Handoff packet

Every role returns candidate/worktree identity, files read and changed, commands
with exit status, evidence paths, remaining gaps, and a claim no broader than
the evidence supports. Visual and architecture handoffs contain `preview.html`,
`contract.json`, and `evidence.json`; stable IDs and requirements must agree across
the rendered and machine contracts.

## Execution state model

Phases use `PENDING`, `READY`, `ACTIVE`, `HANDOFF_PENDING`, `INTEGRATING`,
`REVIEWING`, `PASSED`, `FAILED`, `BLOCKED`, or `SUPERSEDED`. Legal progress is:

`PENDING -> READY -> ACTIVE -> HANDOFF_PENDING -> INTEGRATING -> REVIEWING -> PASSED`

Any active state may move to `FAILED` or `BLOCKED`; a corrected attempt receives
a new attempt number. Candidate mutation after review supersedes the old review.
The ledger records phase ID, dependencies, owner, worktree, owned paths,
baseline, candidate, attempt, timestamps, outputs, blockers, and next authority.

## Gate verdicts

- `PASS`: all applicable gates passed against one identified candidate.
- `FAIL`: an applicable gate produced a reproducible defect.
- `BLOCKED`: evidence requires missing authority, credentials, environment, or source material.
- `NOT_APPLICABLE`: gate is outside approved scope, with rationale.

Deferred work is not a pass. Static checks do not replace browser or commerce
journey evidence.

## Four-thread scheduler

Thread 1 remains the lead. Three worker slots are selected by satisfied
dependencies, critical-path priority, non-overlapping paths, and reviewer
independence. Waves are discovery, system, implementation, integration,
independent review, and release. Swap only after a checkpointed handoff. A role
never reviews its own output.

## Evidence discipline

Every role return requires claim-bound evidence:

- deterministic artifact plus eyes-on review, or
- deterministic artifact plus authoritative documentation and executable repository evidence.

Claims missing this evidence remain `BLOCKED`.
