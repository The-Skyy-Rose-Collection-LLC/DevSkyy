# Design System Contract

## Census before creation

Locate existing token sources, component APIs, CSS conventions, theme settings,
generated assets, documentation, and consumers. Extend the canonical system;
never create a parallel one.

## Required architecture

- Reference primitives -> semantic tokens -> component tokens -> collection/campaign overrides.
- Stable names, one-way aliases, owners, lifecycle state, introduced/replaced versions, consumers, and removal plan.
- Canonical outputs for the repository's CSS, JSON, TypeScript, PHP, or `theme.json` consumers.
- Components consume semantics instead of raw primitives when a semantic exists.

## Component baseline

Cover navigation, editorial modules, product cards, media galleries, prices,
badges, swatches, sizes, fit guidance, stock, quantity, filters, sorting, search,
forms, notices, drawers, cart, checkout-adjacent, account, feedback, and page
compositions. Contracts include anatomy, slots, variants, events, content limits,
accessibility, responsive behavior, invalid combinations, and all applicable
default/hover/focus/active/selected/disabled/loading/empty/error/success/sale/
low-stock/sold-out/unavailable states.

## Governance and evidence

Maintain token registry, component manifest/dependency graph, rendered examples,
visual fixture manifest, adoption map/metrics, changelog, compatibility policy,
deprecation ledger, and release notes. Exceptions require owner, rationale,
affected surfaces, accessibility impact, migration plan, and expiry. Detect raw
visual values and unauthorized variants automatically where tooling allows.

Fixtures bind deterministic data, assets, fonts, viewport, state, collection
theme, animation state, timestamp rule, and candidate ID. Define responsive,
typography, icon, imagery, motion, composition, and quality budgets centrally.
