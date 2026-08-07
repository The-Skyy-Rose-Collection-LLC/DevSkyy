# Fashion Design System Team

This pod operates inside Seat 12 of the SkyyRose Theme Team. Its job is to turn brand direction into a versioned, testable, non-generic design system that covers the complete commerce funnel.

## Operating model

The `fashion-design-system-engineer` is the architect and dispatcher. Specialists are called only for their lane and return compact artifacts; their full instructions are not preloaded into the architect's context. All tools remain callable. No agent loads more than three skill instruction sets at once.

Every specialist starts by reading `.wolf/memory.md`, this document, the active surface contract, and only the canonical sources needed for its lane. Framework/API claims require authenticated official documentation. Visual claims require fresh rendered evidence. A skip, timeout, stale capture, or unavailable source is `UNVERIFIED`.

## Inner team

| Agent | Owns | Required artifact |
|---|---|---|
| `fashion-brand-systems-researcher` | audience, cultural context, competitor differentiation, brand recognition devices, product/imagery provenance | Brand evidence brief + logo-off hypotheses |
| `fashion-token-foundations-engineer` | primitive/semantic/component tokens, themes, modes, density, contrast, type/spacing scales, token build and drift | Token graph + source-of-truth/drift report |
| `fashion-typography-layout-director` | type roles, editorial grid, composition grammar, image ratios, responsive transformations, RTL | Typography/composition specification |
| `fashion-component-commerce-engineer` | component APIs, anatomy, variants, commerce patterns, state machines, data contracts, framework implementation guidance | Component inventory + state/variant matrices |
| `fashion-motion-responsive-engineer` | interaction grammar, motion tokens, responsive behavior, reduced motion, touch/WebGL fallbacks, performance budgets | Motion/responsive behavior matrix |
| `fashion-accessibility-content-engineer` | WCAG, keyboard/screen-reader behavior, focus, contrast, content design, errors, localization, RTL | Accessibility/content acceptance matrix |
| `fashion-designops-governance-engineer` | package architecture, docs, examples, versioning, migrations, release policy, telemetry, adoption and cost controls | Governance/release/adoption plan |
| `fashion-visual-qa-red-team` | screenshot diffs, browser states, anti-generic score, logo-off test, accessibility/performance evidence, adversarial rejection | Independent PASS/REJECT evidence report |

## End-to-end capability contract

The pod covers the layers expected in an elite production design system:

1. Research and ground truth: brand canon, audience, jobs, product SOT, visual references, competitive whitespace, decision records, provenance, freshness.
2. Foundations: color, typography, spacing, sizing, radii, borders, elevation, z-index, motion, breakpoints, grids, iconography, imagery, modes, themes, density, localization, RTL.
3. Token engineering: primitive to semantic to component graph; schema, naming, aliases, platform transforms, validation, deprecation, migration, generated-artifact drift.
4. Composition: page templates, editorial rhythm, responsive transformation, content hierarchy, product protagonism, image crop and art direction, utility-page inheritance.
5. Components: anatomy, slots, variants, sizes, states, accessibility contract, content rules, interaction/data contracts, WooCommerce flows, framework adapters, escape hatches.
6. Content design: voice, labels, validation, errors, empty/loading/success states, localization expansion, pricing/stock clarity, ethical conversion patterns.
7. Interaction and motion: state transitions, focus/keyboard behavior, gesture/touch behavior, motion tokens, narrative choreography, reduced-motion equivalence, no scroll-jacking.
8. Accessibility and inclusion: WCAG 2.2 AA floor, contrast calculations, non-color cues, keyboard and screen-reader journeys, zoom/reflow, touch targets, forced colors, language/RTL.
9. Performance: CSS/JS/font/image budgets, LCP/CLS/INP attribution, progressive enhancement, lazy loading, mobile and no-WebGL fallbacks.
10. Tooling and developer experience: source packages, generated outputs, linting, type safety, component docs, examples, scaffolds, codemods, CI, screenshot baselines, local preview.
11. Governance: ownership, RFCs, contribution review, semantic versioning, changelog, deprecation windows, migrations, adoption metrics, support policy, release rollback.
12. Verification and learning: deterministic gates, browser journeys, screenshot diff, Lighthouse, contrast/type/spacing checks, independent review, failure classification, bounded repair loop, learning journal.
13. Security and trust: dependency/source provenance, secrets checks, safe rendering/escaping, CSP compatibility, permission boundaries, supply-chain review.
14. Cost and routing: capability-based model/tool routing, budget ledger, paid-action approval, context budgets, retry ceilings, fail-closed escalation.

## Elite Web Builder capability mapping

The supplied `elite_web_builder_hardened_1.zip` is integrated by capability, not treated as unquestioned authority:

| Archive capability | Pod owner |
|---|---|
| `ground_truth.py`, Context7 bridge | Architect + Brand Systems Researcher |
| design-system/accessibility/frontend/performance/QA/SEO specialists | Corresponding pod specialists |
| provider adapters and model router | DesignOps & Governance |
| verification loop, gate checkers, self-healer, Ralph integration | Visual QA Red Team + DesignOps |
| learning journal | DesignOps, with session notes in `.wolf/memory.md` |
| cost tracker and provider routing config | DesignOps & Governance |
| contrast, type-scale, spacing-scale tools | Token Foundations + Accessibility |
| Lighthouse and screenshot diff | Motion/Responsive + Visual QA Red Team |
| WordPress/Shopify scaffolds | Component Commerce + DesignOps; canonical theme architecture still wins |
| performance/WCAG/security/WordPress knowledge | Relevant specialist, verified against current official docs before use |

Archive code cannot override SkyyRose canon, repository instructions, approval boundaries, or existing verified pipelines. Duplicate capabilities are adapted behind one owner instead of creating competing systems.

## Pipeline and hard gates

1. Architect creates the work order and dispatch map.
2. Brand researcher produces evidence and recognition hypotheses.
3. Foundations, typography/layout, and component/commerce work in parallel against the same canon.
4. Motion/responsive and accessibility/content complete behavior and state coverage.
5. DesignOps packages docs, versioning, tooling, migration, and adoption controls.
6. Architect synthesizes `docs/design/<surface>-design-system.md` and scores readiness.
7. Visual QA Red Team independently renders and attempts to reject it.
8. Builder handoff occurs only after all required artifacts exist, distinctiveness is at least 85/100, every category is at least 70%, zero anti-generic instant fails remain, and the independent verdict is PASS.

The builder and architect may repair findings, but neither may issue the final visual approval.

## Definition of complete

A design system is complete only when foundations, components, patterns, content, accessibility, performance, documentation, governance, versioning, browser evidence, and adoption/migration paths are present for the requested scope. A polished homepage with default cart, checkout, account, search, error, or empty states is incomplete.
