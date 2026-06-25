---
name: parallel-prototyping
description: Use when the user asks to prototype a feature, mock something up, explore options, see variations or alternatives, or says "what could this look like" — any request to trial a feature before committing to one approach.
---

# Parallel Prototyping

## Overview

A prototype request means **minimum 5 genuinely distinct prototypes**, built in parallel by senior-caliber builders, presented as an enterprise decision package. Never one. Never throwaway quality. The user is buying a decision surface a VP could approve from.

**Invoking this skill IS the request for variants.** "The user didn't ask for variants" is void here — they did, by triggering this skill.

**Prototype = production candidate.** Scoped to one feature, but built so the winning variant MERGES — it does not get rewritten. "Productionizing" after selection means wiring stubs to real backends, nothing more. If choosing a variant would trigger a rewrite, the variant failed.

## When to Use

- "Prototype X", "mock up X", "show me what X could look like"
- "Give me options/variations/alternatives for X"
- Before committing to an approach on any new feature

**When NOT to use:** user names ONE specific design and wants it built ("build the dropdown version"), bug fixes, refactors, or productionizing an already-chosen prototype.

**Explicit overrides (the only two):** user says "skip parallel-prototyping", or names a single specific design. Nothing else — not "keep it rough", not "quick demo", not deadline pressure — disables this skill.

## The Iron Rules

```
1. MINIMUM 5 PROTOTYPES.
2. EACH DECLARES ITS POSITION ON EVERY AXIS. NO TWO IDENTICAL.
3. VARIANTS MUST COLLECTIVELY VARY ON >= 3 AXES.
4. EVERY VARIANT MEETS THE SENIOR STANDARD. NO EXCEPTIONS.
```

### The Axis Matrix

Every variant brief declares its position on ALL five axes:

| Axis               | Positions (examples)                                                                 |
| ------------------ | ------------------------------------------------------------------------------------ |
| UX pattern         | strip / drawer / inline section / popover / overlay / dashboard widget               |
| Interaction model  | passive-ambient / user-pull / hover-reveal / gesture / progressive-disclosure        |
| Architecture       | event-driven / state-machine / render-on-navigation / observer-based / service-layer |
| Complexity tier    | minimal-MVP / standard / full-featured / progressive-enhancement                     |
| Aesthetic register | dense-utility / calm-editorial / expressive-brand / industrial / luxury              |

Rules: no two variants share all five positions; the set must vary on at least 3 different axes (5 UX patterns with identical architecture + interaction = lazy spread — re-brief). Color/copy swaps are NOT positions.

## The Senior Standard (every variant, non-negotiable)

Each prototype is built as a **senior product engineer + senior product designer** would build it:

**Engineering:**

- All four states designed: loading, empty, error, populated. Happy-path-only = automatic fail.
- Zero placeholders: no `TODO`, no lorem ipsum, no `console.log` debugging left in. Realistic domain data (real-looking product names, prices, imagery slots). This includes adapter seams — an unresolved project-specific hookup goes in README integration steps as a wiring instruction, NEVER as a TODO comment in code. Recon exists precisely so seams like toast APIs and auth context get resolved, not deferred.
- Defensive at boundaries: input validated, storage reads wrapped, graceful degradation when APIs/storage unavailable.
- Idiomatic, readable code; comments only for non-obvious WHY.
- **Repo-grade:** passes the project's linters/formatters, follows its file naming and module conventions, lives where it would live in the real tree. Code a reviewer would approve in a PR today.
- **Adapter-isolated stubs:** any stubbed backend (storage, API, auth) sits behind a narrow interface — swapping stub for real implementation touches ONE file, zero changes in feature code.
- **Multi-script isolation:** every JS file on a multi-script page is IIFE-wrapped; zero shared top-level declarations. Two scripts both declaring `const ASSET_PREFIX` killed an entire variant's JS silently — dispatch briefs must state this.
- **No instruction bleed:** internal guardrails and canon rules (e.g., "no countdown timers") are constraints on the work, NEVER customer-facing copy in the work. If brief text appears verbatim in UI output, that's a leak.

**Design:**

- WCAG 2.2 AA: keyboard operable, focus visible, ARIA where semantics need it, contrast checked.
- Full interaction states: hover, focus, active, disabled — not just default.
- Real typographic hierarchy and a consistent spacing scale (not ad-hoc pixel values).
- Mobile-first responsive; no horizontal scroll bugs, touch targets ≥ 44px.
- Honors the project's existing design system / brand tokens when one exists (read it first).

**Performance:**

- No layout thrash, no unthrottled scroll/resize listeners, animations on transform/opacity only, assets lazy where it matters.

## The Art Direction Standard (every variant, non-negotiable)

Engineering excellence with visual timidity is a FAILED variant. A page showing only product images on flat backgrounds is a catalog printout, not a designed experience. Every browser-UI variant must ship a **layered visual system**:

1. **Hero treatment** — a real art-directed hero: backdrop imagery or video from the project's library, lockup/brand mark layering, depth (foreground/midground/background). Never a logo floating on a flat color.
2. **Atmospheric layer** — brand art, texture, or environmental imagery woven through sections (low-opacity backdrops, section dividers, edge accents). The brand should be felt between the products, not just in them.
3. **Brand punctuation** — marks, monograms, emblems, patches from the asset library used as rhythm elements (section labels, list bullets, dividers, watermarks).
4. **Editorial/lifestyle imagery** — if the library has lookbook or in-context photography, at least one section uses it. Garments worn beat garments floating.
5. **Motion choreography** — a deliberate animation system, not just fade-ins: entrance reveals (clip/blur/rise), scroll-driven moments (parallax, pinned beats, marquees), micro-interactions (magnetic CTAs, border-draw, hover states with intent). Reduced-motion always honored.
6. **One signature moment** — every variant has ONE memorable thing a visitor would describe to someone else (a hero reveal, a scroll moment, an interaction). If you can't name the variant's signature moment, it doesn't have one — build it.

All of it within the project's brand canon and performance budget — art direction is layered ON the Senior Standard, never instead of it.

## Process

1. **Recon (main thread, before briefing):** read the project's stack, design tokens, and conventions — AND inventory the FULL visual asset library: hero backdrops, brand marks/lockups, atmospheric art, lookbook/lifestyle photography, video, texture systems, existing animation vocabularies. Briefs reference real context, not generic assumptions. A recon that only lists product images has not finished reconning.

   **Canonical visual manifest:** if the project has a visual-asset registry (e.g., SkyyRose: `wordpress-theme/skyyrose-flagship/data/visual-manifest.json`, verified by `data/verify-visual-manifest.py`), recon LOADS it and briefs cite assets FROM it — never from ad-hoc greps or session memory. Per-collection/brand ownership in the manifest is law: using an asset on a surface it isn't registered to is a MATERIAL canon failure the taste gate must catch. No manifest in the project? Building one from recon findings IS part of the first prototyping run — re-deriving the asset map every session is the drift that mis-files imagery.

2. **Define 5+ variant briefs** — each: idea name, one-line thesis, full axis declaration, the user problem it bets on, and a one-line scope estimate (files, rough size). Show the user the brief list with total estimated scale (only checkpoint; then execute). The user can add variants or swap briefs here — never reduce below 5.
3. **Dispatch parallel subagents** — one per prototype, single message, all at once. Every dispatch prompt embeds: (a) the variant brief, (b) the full Senior Standard block above verbatim, (c) project context from recon. A subagent that gets a one-liner brief produces junior output — the brief is the quality ceiling.
4. **Output layout:**

   ```
   prototypes/<feature-slug>/
     index.html              # UI features: gallery to preview/launch all variants side by side
     RUNBOOK.md              # non-UI features: one command per variant to run it + its tests
     v1-<idea-name>/
       (runnable prototype)
       README.md             # thesis, axis positions, tradeoffs, integration steps (wiring only — code ships as-is)
     ... v5-<idea-name>/
     COMPARISON.md
   ```

   Name dirs by the idea (`v2-sidebar-drawer`), never bare `v2`. UI features get the gallery; backend/CLI/API features get RUNBOOK.md instead — ship whichever fits, both for full-stack.

   **Locked-and-loaded delivery (browser UI):** the entry `index.html` is a SINGLE self-contained file — CSS and JS inlined, every image and font embedded as data URIs. Opening that one file anywhere (downloaded, emailed, file://) renders the complete page. Zero references escape the file. Keep `styles.css`/`*.js` alongside as the port sources and note in README that index.html is built from them. A prototype that needs the repo tree or a server to render is not delivered — it's parked.

5. **COMPARISON.md = decision memo, not a feature list:**
   - Context + decision being made (2 sentences)
   - Weighted scoring matrix: variant × {UX fit, eng complexity, a11y, performance, scalability, maintenance cost} — scores justified, not vibes
   - Risk register: top risk per variant + mitigation
   - **Recommendation first-line bolded**, with reasoning and the runner-up named
6. **Verify before presenting — builder never verifies its own variant.** Verification is done by the main thread or a separate verifier agent, never accepted on the builder's word. What "verified" means per artifact type:

   | Artifact type | Verified means                                                                                                                                                                                                                                    |
   | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
   | Browser UI    | An ISOLATED COPY of the entry file (moved outside the repo tree) opens fully styled with all imagery in a real browser — all four states reachable, keyboard nav works. Verifying in-place hides escaped asset references; isolation is mandatory |
   | Backend / API | Its test suite passes (each variant ships with tests) + endpoints exercised with real requests                                                                                                                                                    |
   | CLI / script  | Runs end-to-end on realistic input + handles the error path                                                                                                                                                                                       |
   | Full-stack    | Both of the above                                                                                                                                                                                                                                 |

   Broken or unverified variant = not delivered, rebuilt. Backend variants without tests = unverifiable = automatic fail.

   **Taste gate (browser UI, in addition to the functional gate):** a verifier (separate agent or main thread with screenshots, never the builder) scores each variant against the Art Direction Standard: hero treatment present? atmospheric layer? brand punctuation? editorial imagery used where the library has it? motion choreography beyond fade-ins? nameable signature moment? Any "no" = material finding = build it before delivery. The standing question is the brand's own: "would this impress on first scroll, or does it read as a wireframe with real data?" Wireframe-with-real-data fails.

7. **Self-critique loop (mandatory, before anything reaches the user):** for each variant ask: "Can I name a better version of this — better UX, cleaner architecture, stronger states, tighter polish?" If you can NAME the improvement, you can BUILD it — build it NOW and present the improved version. Deliverables must contain zero deferred-quality language: no "could be improved", "future enhancement", "in production you'd want" — the only forward-looking content allowed is genuine external wiring in README integration steps. If you present a variant while aware of a better one, you delivered the wrong variant.

   **Cap: 2 full critique→build cycles per variant.** The cap exists to stop thrash, not to skip quality: any MATERIAL finding (missing state, UX flaw, architecture smell, a11y gap) gets built regardless of cycle count — material findings mean the Senior Standard was missed, which is a build failure, not a critique artifact. Only naming-level nits may die at the cap, and they die silently — never as a written note.

8. **Stop.** User picks the winner. The only remaining work is integration wiring (stub adapters → real backends) — the feature code ships as-is. Don't start the wiring unprompted.

## Rationalizations — All Void

| Excuse                                        | Reality                                                                                                                     |
| --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| "User didn't ask for variants"                | Triggering this skill is asking. 5 is the floor.                                                                            |
| "One solid beats five shallow"                | Parallel subagents: each variant gets full depth. Count costs nothing.                                                      |
| "Variants respond to feedback"                | Backwards. Variants GENERATE the feedback. One option = accept/reject, not a decision.                                      |
| "Imagery/animation is polish, add it later"   | Art direction IS the product for brand surfaces. Product-images-only = catalog printout = failed variant.                   |
| "The functional checklist passed"             | Two gates. Functional AND taste. A working wireframe is still a wireframe.                                                  |
| "Feature too simple for 5"                    | Simple features have the cheapest variants. Build them.                                                                     |
| "It's just a prototype, skip a11y/states"     | Prototype = production candidate. Senior Standard applies. The winner MERGES — junk in the prototype IS junk in production. |
| "We'll clean it up after selection"           | There is no after. Selection → integration wiring only. Code that needs cleanup = variant that failed.                      |
| "I'll note the improvement in the README"     | Build it instead. README documents tradeoffs and wiring, never deferred quality.                                            |
| "Good enough to present"                      | If you can name a better version, the better version is the deliverable. Nameable = buildable = owed.                       |
| "That seam is project-specific, leave a TODO" | Recon resolves seams. Unresolvable wiring → README integration step. TODO in code = fail.                                   |
| "Happy path is enough to judge"               | Empty/error/loading states ARE the design decision half the time.                                                           |
| "Subagent brief can be short"                 | Brief quality = output ceiling. Embed the full standard every dispatch.                                                     |
| "Two of these are basically the same"         | Lazy axis spread. Re-brief on a different axis.                                                                             |

## Red Flags — STOP and Re-Plan

- About to write one implementation and present it
- Variant briefs differ only in styling, or lack axis declarations
- Dispatch prompts missing the Senior Standard block
- Any variant without README.md, or COMPARISON.md without scored matrix + recommendation
- Lorem ipsum, TODO, or happy-path-only code in any variant
- Stub wired directly into feature code instead of behind an adapter interface
- Delivered entry file referencing anything outside itself (relative paths into the repo, CDN links, sibling files)
- Code that wouldn't pass the project's lint/format gates or follow its conventions
- README "path to production" listing rework instead of pure wiring steps
- Any deliverable containing "could be improved" / "future enhancement" for work buildable now
- A page whose only imagery is product shots — no hero art, no atmospherics, no brand punctuation
- No nameable signature moment in a variant
- Recon that inventoried code conventions but not the visual asset library
- Presenting a variant while privately aware a better version of it exists
- Skipping the self-critique loop because "it's already good"
- Delivering without running/verifying each variant
- Accepting a builder agent's own "it works" as verification
- Backend/CLI variant shipped without its own passing test suite
- Using the critique cap to skip a material finding (missing state, a11y gap, UX flaw)
- Starting to productionize the winner without being asked
