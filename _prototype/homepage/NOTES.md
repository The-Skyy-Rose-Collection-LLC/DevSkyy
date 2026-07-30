# Homepage section prototype — THROWAWAY

**Question:** What should each section of the SkyyRose homepage look like?

24 variants — 3 per section across 8 sections. Delete this directory once the verdicts below are
folded into `front-page.php`.

## Run it

```bash
cd _prototype/homepage && python3 -m http.server 8899
# → http://localhost:8899/
```

Bottom bar switches section and variant. `←/→` variant, `↑/↓` section. Every state is a URL:
`?section=chooser&variant=B` — paste one back to name a winner exactly.

## The variants

| Section | A | B | C |
|---|---|---|---|
| **hero** | Logo field behind the monolith | Ticker-clamped specimen | Masthead poster — marquee is the nav |
| **ticker** | Hairline seam | Counter-scrolling shear band | Vertical slat assembly |
| **chooser** | Count-led index | Swipe-through rooms | Expanding blades |
| **drop** | Full-bleed proclamation | Inline manifest rail | Split card, object + spec sheet |
| **receipts** | Asymmetric proof mosaic | Logo wall + struck award seal | Editorial dispatch index |
| **origin** | Split portrait + cut-in | Full-bleed testimony | Ledger letter, tap-open |
| **letter** | Sealed object — tap to break | Letterhead spread | Keepsake board — flip the backs |
| **close** | Numbered utility ledger | Closing statement, capture in the line | Scrolling outro, docked concierge bar |

Fixed across all hero variants (founder direction, not a variable): the 720×1280 portrait video
stays **centered and `contain`** — never cover-cropped, because cropping cuts off the outfit that
is the point of the shot. What varies is how marquee, type and CTA relate to it.

## Verification — run 2026-07-29

| Check | Result |
|---|---|
| All 8 sections + index + tokens serve | **200** each `[repro]` |
| 3 named variants per section | **24/24** `[repro]` |
| Cut fonts (Playfair/Cormorant/Bebas/Great Vibes/Alex Brush/Bungee Shade/Oswald/Space Mono) | **0** |
| Crimson `#DC143C` used as text colour | **0** (3.63:1 on black — fills/glows only) |
| Rogue blacks `#08080A` / `#050505` | **0** — one black, `#0A0A0A` |
| Broken asset references | **0** (the lone `%23g` flag is `url(#g)` inside a data-URI SVG — its own filter id, not a file) |
| Leaked into production | **No** — `_prototype/` is outside `wordpress-theme/skyyrose-flagship/`, so it cannot deploy |

Judged in the theme's **real** self-hosted woff2 (Archivo, Cinzel, Anton, Hanken Grotesk, Pinyon,
and the bespoke SkyyRose Black Rose Script / Love Hurts Graffiti) and the **real** brand logos —
a layout judged in a fallback stack has not been judged.

## Known gaps

- **Kids Capsule has no logo asset.** None of the 29 files in `assets/branding/` matches
  `*kid*` / `*capsule*` / `*kc*`. Variants set it in Grand Hotel type. Collection names are lockup
  IMAGES by canon, so this needs real artwork before production.
- Hero video here is the 15s loop (913 KB webm). Full-length alternatives sit in the scratchpad:
  65s at 4.11 MB (crf 36) and 2.67 MB (crf 42).

## Harness bug found and fixed

A `<template>`'s inline `<script>` **does** execute on clone-insert — template content lives in an
inert document, so its scripts are never flagged "already started" and the clone is a fresh
element. The harness originally *also* re-created each script after insertion (a pattern lifted
from a DOMParser bundler, where scripts genuinely are inert), so every variant's script ran
**twice** and every listener double-bound. Symptom in `close.html`: one submit event, handler ran
twice — pass 1 cleared the field, pass 2 saw it empty and painted an error, so a valid email
produced "Enter an email address to join."

Fixed by deleting the re-creation step. Do not reintroduce it.

## Verdicts — LOCKED 2026-07-29

| Section | Winner | Why / what to steal from the others |
|---|---|---|
| hero | **C** | Masthead poster, marquee-as-nav. Video stays portrait/contain per founder direction (never cover-cropped). |
| ticker | **B** | Counter-scrolling shear band. |
| chooser | **B, modified** | Swipe-through rooms as the base — but re-driven as true horizontal scroll-snap (not B's original mechanism), and each room gets a real "Enter <Collection>" button wired to its live `/collection-*/` URL. Reuse `collections-world` engine's per-collection scene stills as room backgrounds where it doesn't cost an extra asset pipeline. This supersedes `docs/homepage-rebuild-spec.md` Act III's hover-expand blade-accordion — founder's live direction overrides the earlier draft spec. |
| drop | **A** | Full-bleed proclamation. |
| receipts | **B** | Logo wall + struck award seal. |
| origin | **B** | Full-bleed testimony. |
| letter | **C** | Keepsake board, flip the backs. Layer in the 3D walking child mascot (rigged 2026-07-29, `skyy_child_rigged_hero.glb`) here — this is Kids Capsule's one emotional/memorable moment, not duplicated into the chooser's KC room (keeps 3D cost to one section). |
| close | **B** | Closing statement, capture in the line. |

Winners get **rewritten** into `front-page.php`, not pasted — this code was written under prototype
constraints (no tests, no error handling, no abstractions). Production also reconciles against
`docs/homepage-rebuild-spec.md` §3 (token mapping), §4 (motion spec), §5 (SOT image slot rules),
§6 (file/version/build plan) — those sections still apply; only Acts I and III's exact mechanism
are superseded by the verdicts above.

Once the production fold is built and verified, delete this `_prototype/homepage/` directory.
