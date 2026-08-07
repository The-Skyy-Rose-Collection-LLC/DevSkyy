# Fashion Theme Team Plugin Audit

Status: implemented, validated, installed, and enabled

## Recovered source role

The persisted role is `fashion-theme-architect` from Claude team session
`session-5db8882f`. No standalone `fashion-theme-developer` agent definition was
found in project agents, global agents, or installed plugin caches.

Its proven scope covered the commercial WooCommerce funnel from homepage through
account, source-of-truth catalog usage, customizer support, design and motion
work, source/minified asset parity, and final theme verification. The primary
gap is separation of duties: one role owned architecture, implementation, QA,
and release reporting.

## Proposed plugin

Name: `fashion-theme-team`

Destination: personal Codex marketplace, unless the founder requests a
repository/team marketplace instead.

### Team roles

1. `fashion-theme-lead`: intake, scope, routing, worktree ownership, evidence ledger, and final handoff.
2. `brand-experience-architect`: brand rules, information architecture, conversion journey, visual direction, and acceptance criteria.
3. `fashion-design-system-engineer`: tokens, typography, spacing, primitives, components, states, responsive rules, motion, documentation, and visual fixtures.
4. `woocommerce-theme-engineer`: PHP templates, hooks, checkout/account/cart behavior, customizer, and WordPress security conventions.
5. `fashion-frontend-engineer`: CSS, JavaScript, responsive behavior, motion, component states, and source/minified asset parity.
6. `catalog-sot-integrator`: product facts, imagery, SKU mapping, merchandising data, and no-hallucination source enforcement.
7. `accessibility-performance-reviewer`: WCAG, reduced motion, keyboard behavior, asset budgets, Core Web Vitals risks, and fallback paths.
8. `visual-commerce-qa`: browser screenshots, responsive visual fidelity, WooCommerce journey tests, and regression evidence.
9. `theme-release-engineer`: package integrity, lint/build gates, immutable evidence, changelog, rollback notes, and deployment readiness report.

### End-to-end workflow

1. Lead inventories the target theme and captures an immutable baseline.
2. Architect produces the experience contract and falsifiable acceptance gates.
3. Lead creates isolated worktrees and dispatches only required specialists.
4. Implementation roles build in parallel without overlapping file ownership.
5. Lead integrates completed changes into a candidate snapshot.
6. Independent reviewers run accessibility, performance, visual, commerce, and security gates.
7. Release engineer produces candidate-bound evidence and a pass/fail report.
8. Human approval remains mandatory for commit, merge, deployment, paid APIs, or production changes.

### Plugin contents

- `.codex-plugin/plugin.json`
- `agents/` with the nine role charters
- `skills/fashion-theme-team/SKILL.md` as the orchestrator entrypoint
- `hooks.json` for session-note and evidence reminders
- `scripts/preflight.sh`, `scripts/verify.sh`, and `scripts/report.sh`
- Personal marketplace entry at `~/.agents/plugins/marketplace.json`

### Validation contract

- Codex plugin manifest validation passes.
- Team orchestration skill validation passes.
- Every referenced command and repository path is discovered before use.
- Team dry run proves role routing without editing or deploying a theme.
- No role may self-certify its own implementation as release-ready.
- Deployment and paid external calls remain fail-closed without explicit approval.

## Approval checkpoint

Founder approved the personal plugin. The final scope contains nine roles after
adding dedicated design-system ownership.

## Motherbase hardening - 2026-08-05

Plugin version `0.1.0+codex.20260806063558` closes the autonomous-control, SkyyRose canon, design-system governance, full-theme coverage, WooCommerce state-matrix, and proof-quality gaps identified by the four resident role audits. All source and installed-cache validation gates passed. No theme code, production service, remote branch, catalog, or deployment target was changed.
