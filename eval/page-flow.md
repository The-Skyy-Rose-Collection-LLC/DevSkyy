# Eval — Page Flow & Information Architecture

> Stub. This file is populated during Phase 1.5 (Site IA / nav / menu redesign). For each WP page, it documents:
> - Where users arrive from (entry sources)
> - Where they go next (intended exit paths)
> - Primary CTA on the page
> - Secondary CTAs
> - Empty / error states
> - Conversion criteria

## Schema (filled in Phase 1.5)

```yaml
page: <slug>
url: /<slug>
template: <template-file>
entry_sources:
  - source: <referrer>
    expected_traffic: <%>
primary_cta:
  label: <text>
  destination: <url>
  conversion_criterion: <observable>
secondary_ctas: [...]
exit_paths: [...]
empty_state: <description>
error_state: <description>
brand_voice_target: <which collection — or 'cross-collection neutral'>
```

## Pages to populate (29 total → 27 after duplicate deletion)

(See `tasks/pr-action-plan.md` and the master plan for the full per-page list. Phase 1.5 fills this in.)

---

## Phase 1.5 deliverables

1. Mega menu walker → ensure top-level nav exposes: Shop (mega) / Experiences / Drop / About / Search
2. Mobile drawer → matches mega menu IA
3. Breadcrumbs → JSON-LD on every interior page
4. Footer → 3-column (Shop / About / Legal)
5. Sticky header → scroll-aware
6. Page-flow doc → every page has entry sources, primary CTA, exit paths documented

---

## Acceptance

- A first-time customer can find a drop within 2 clicks from any page
- Every page has exactly one primary CTA, no decision paralysis
- Breadcrumb JSON-LD validates in Google Rich Results Test
- Mobile drawer covers 100vh, dismisses on outside tap, traps focus when open
