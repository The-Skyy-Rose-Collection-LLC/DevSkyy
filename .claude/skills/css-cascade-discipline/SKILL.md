---
name: css-cascade-discipline
description: CSS cascade, specificity, and selector-weight discipline for large legacy stylesheets (50+ plain-CSS files, no build-time scoping). Use whenever adding, changing, or reviewing CSS in skyyrose-flagship or any multi-file plain-CSS codebase — especially color/typography overrides, new component styles, or "the style isn't applying" debugging.
---

# CSS Cascade Discipline

Plain-CSS codebases have no scoping compiler. Every new rule fights every existing rule. This skill exists because a shipped fix (`#719`) was silently defeated: `.hero-cta-primary { color: var(--void,#050505) }` (specificity 0,1,0) lost to a scoped reset `.homepage-v2 a { color: inherit }` (0,1,1) — white-on-white CTA in production while the "fix" sat in the served file.

## Specificity math (memorize)

`(inline, id, class/attr/pseudo-class, element)` — compare left to right, first difference wins. Ties → later in source order wins (across files: later-enqueued file wins).

- `.hero-cta-primary` → (0,1,0)
- `.homepage-v2 a` → (0,1,1) — class + ELEMENT beats a lone class for that element
- `.hero-cta.hero-cta-primary` → (0,2,0) — the standard escalation
- `[data-collection="love-hurts"] .v7card__add` → (0,2,0); attribute selectors count as class-weight

## Before writing ANY override rule

1. **Find the competition.** Grep every stylesheet the page loads for rules that could set the same property on the same element: the element's classes, its tag scoped under ancestors (`.section-scope a`, `.page-class button`), and `*` resets. In skyyrose-flagship, the known scoped resets are in `homepage-v2.css` (`.homepage-v2 a { color: inherit }`), `main.css` and `commercial-polish.css` (`* { … !important }` inside `@media print` — inactive on screen, don't panic-match them).
2. **Compute both weights.** Your rule must beat the strongest competitor OR come later at equal weight. When targeting an element (`a`, `button`, `input`) under a scoped reset, you need ≥ (0,1,1): double-class the component (`.x.x-variant`) or scope it (`.page-scope .x-variant`).
3. **Never solve with `!important`.** It wins today and creates the next un-overridable fight. Escalate specificity structurally instead.
4. **Custom-property fallbacks don't fix cascade losses.** `var(--token, #literal)` protects against a missing token, NOT against a competing selector. Diagnose which failure you actually have before choosing the fix.

## Verifying a CSS fix actually applied (live)

`getComputedStyle` probes lie to you in three specific ways:

- **Transitions mask inline probes**: `el.style.color = 'red'` read synchronously returns the transition's t=0 value when the element has `transition: all`. Set `el.style.setProperty('transition','none','important')` first.
- **CSSOM walkers**: `CSSStyleRule.cssRules` is always truthy (CSS nesting API) — `if (r.cssRules) walk(...); continue;` skips every style rule. Check `r.selectorText && r.style` FIRST, recurse `r.cssRules` separately.
- **Browser/CDN cache**: the page's CSSOM may be a stale copy even after deploy. Verify the RULE TEXT in the page's own CSSOM (`r.style.cssText`), not just the file fetched by curl — curl gets a fresh edge copy, the browser may not.

Decisive experiment when a declaration mysteriously loses: set `color: red !important` ON THE RULE via CSSOM. If red applies, cascade defeat confirmed — hunt the winner by weight, not by vibes.

## Landing a scoped reset safely (the other direction)

Adding a rule like `.my-section a { color: inherit }` retroactively beats every (0,1,0) component rule inside that section. Before landing one: grep for component classes used inside the section that style the same property at (0,1,0) and pre-escalate them. A scoped reset without this census is a time bomb.

## skyyrose-flagship specifics

- Production serves `.min` — after ANY css edit: `cd wordpress-theme && npm run build`, verify the fingerprint in the `.min` output, not just source.
- Load order = enqueue order in `inc/enqueue.php`. A later-enqueued file wins specificity ties against an earlier one.
- Prefer scoping new component rules under the template's body/section class (e.g. `.homepage-v2 .hero-strip`) — both for weight and for blast-radius control.
