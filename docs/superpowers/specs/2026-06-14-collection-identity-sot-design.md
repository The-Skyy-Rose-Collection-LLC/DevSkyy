> SUPERSEDED 2026-07-10/11 — fonts now per SOT.md → typography.json (Archivo / Hanken Grotesk / Anton / Cinzel + bespoke collection name-scripts; zero-CDN self-hosted woff2). Font/CDN references below are historical.

# Collection Identity SOT — Design Spec

**Date:** 2026-06-14
**Status:** Design — awaiting founder sign-off before `writing-plans`
**Owner:** Corey Foster (founder canon) · DevSkyy engineering agent (implementation)
**Supersedes:** the hardcoded `COLLECTIONS` dict + per-collection regex in `wordpress-theme/skyyrose-flagship/data/build-collection-sot.py`

---

## 1. Goal

Make each collection's identity — **story, palette, fonts, lockup, products, imagery, copy** — live in **one founder-canon source per collection**, and make every downstream artifact (`design-tokens.css`, the per-collection SOT, the designer hub) a **computed projection** of that source that CI proves matches. Kill the class of bug where collections get "all mixed up" because identity was hand-copied into Python, CSS, and docs that silently diverged.

Founder directive (2026-06-14, verbatim intent): *"this is the time to get it all right… this is what the single source of truth should start from. if it's not this, get rid of it."* and *"as you build, each collection needs its own folder… collection details, website images and copy and products will go into these separate folders so when designers need correct collection details they will have everything right in 1 place."*

## 2. Problem (verified, this session)

- **The SOT already lies about fonts.** `design-tokens.css` (canonical) vs the hardcoded `COLLECTIONS["display_font"]`: 3 of 4 collections drifted (Love Hurts: Yellowtail vs Playfair; Signature: Italiana vs Playfair; Kids: Italiana vs Playfair). Only Black Rose agreed.
- **No custom fonts are real.** `assets/fonts/` self-hosts only Cinzel/Playfair/Cormorant/Inter/Bebas/Barlow/Oswald/Instrument-Serif. The per-collection fonts `design-tokens.css` *names* — Yellowtail, Italiana, UnifrakturMaguntia, Pinyon Script — are **not self-hosted**, so they silently fall back to Playfair/Cinzel at runtime. The custom collection font was never created.
- **`design-tokens.css` palette violates canon:** Black Rose carries a red `#DC143C` secondary (red belongs to Love Hurts); Love Hurts carries a rose-gold `#B76E79` secondary (rose-gold belongs to Signature); Kids carries soft-pink.
- **File ownership is naming-convention-bound.** The builder's trap-list (`other_collection_files`) only flags tree files whose *filename* matches a per-collection regex. A correctly-belonging asset named off-convention is invisible — neither claimed nor flagged. Format siblings of registered assets (`*.avif`/`*.png` of a `*.webp` role) also wrongly appear as traps.
- **Identity is encoded ~5×** (slug, key, regex, accent, font in `COLLECTIONS`) plus the manifest key and `logo-registry` collection field — all hand-maintained, no agreement check.
- **No tests** lock the generator's behavior (project standard is 85%).
- **Canon is scattered:** story in `docs/brand/collection-stories.md`, palette in `design-tokens.css`, fonts split across CSS + the dict, imagery in `visual-manifest.json`, products in the catalog CSV. Designers have no single place per collection.

## 3. Locked canon (the seed)

Reconciled against `docs/brand/collection-stories.md` (story authority — **aligned**, no conflict) and corrected per founder rule "if it's not this, get rid of it."

| Collection | Story seed (full prose → `collection-stories.md`) | Palette (locked) | Lockup (name = image) |
|---|---|---|---|
| **Black Rose** | Defining beauty through the color black. (Collection 02 — The Refusal; armor; "concrete answering back".) | Black `#0A0A0A` · White `#FFFFFF` · Metallic Silver `#C0C0C0` | `images/lockups/black-rose-lockup.webp` |
| **Love Hurts** | Beauty & the Beast told from the **Beast's** POV, through luxury attire. (Collection 03 — The Grief; "rose under glass".) | Red `#DC143C` (+ darker red variants) · White `#FFFFFF` · Black `#0A0A0A` | `images/lockups/love-hurts-lockup.webp` |
| **Signature** | The beginning of it all — where it started. (Collection 01 — The Origin; "Not basics. Blueprints.") | Gold `#D4AF37` · Rose Gold `#B76E79` | `images/lockups/signature-lockup.webp` |
| **Kids Capsule** | The Heir to the throne. (Collection 04 — The Heir; "Luxury runs in the family.") | = Signature (Gold `#D4AF37` · Rose Gold `#B76E79`) | `images/logos/sr-monogram-rose-gold` (no dedicated KC script exists) |

**Purges applied:** Black Rose red secondary; Love Hurts rose-gold secondary + purple/burgundy; Kids soft-pink. Stories.md retains its detailed prose; if any prose color claim conflicts (e.g. LH "deep purple / burgundy"), the canon table above wins and stories.md gets a dated note.

## 4. Architecture

```
data/collections/<slug>/identity.json   ← THE SEED (founder-authored canon, schema-validated)
        │
        ├──► design-tokens.css  [data-collection] blocks   (palette + font stacks — generated, CI-verified)
        ├──► data/collections/<slug>/sot.json              (products + resolved imagery/logos/lockup — generated)
        ├──► data/collections/<slug>/index.html            (designer hub — generated, renders from canonical assets/)
        └──► verify: identity ↔ CSS ↔ self-hosted woff2 ↔ catalog ↔ asset tree   (drift = CI failure)

Masters that stay authoritative for their domain (identity.json references, never duplicates):
  skyyrose-catalog.csv (products) · visual-manifest.json (non-product imagery) · logo-registry.json (logos)
```

**Invariant:** in each folder, only `identity.json` + `copy.md` are hand-edited. `sot.json` + `index.html` carry a DO-NOT-EDIT banner and are regenerated. Identity facts exist once (in `identity.json`); CSS/SOT/HTML are projections proven to match by the verifier.

## 5. Per-collection folder

```
data/collections/<slug>/
├── identity.json   HAND-AUTHORED canon: name, slug, key, story{seed, doc_ref}, palette{named hex},
│                   fonts{script, caps, body}, lockup{ref}, known_orphans[]
├── copy.md         HAND-AUTHORED designer copy: origin / voice / taglines (sliced from collection-stories.md)
├── sot.json        GENERATED: products[] (resolved image paths), imagery roles, logos, lockup block
└── index.html      GENERATED designer hub (see §9)
```

`identity.json` schema (`data/collections/identity.schema.json`) requires: `slug`, `key` (= `slug.replace("-","_")`, validated), `name`, `story.seed`, `story.doc_ref`, `palette` (named color → hex, with at least the canon colors), `fonts.script` / `fonts.caps` / `fonts.body` (each `{family, woff2|null, source}`), `lockup.ref`, optional `known_orphans[]`. `status` enum mirrors the manifest (`verified` | `needs-founder-review`).

The slug list comes from the folder names (or the manifest `collections[]`, cross-checked). No central identity file; the seed lives with each collection.

## 6. Font matches

Eye-matched to the actual lockup letterforms (read this session). **Final pick confirmed via a font-ID specimen check in P1** before self-hosting; the table is the lead recommendation, not an unverified guess.

| Collection | Lockup lettering observed | `fonts.script` (lead → alt) | `fonts.caps` | `fonts.body` | New woff2 to self-host |
|---|---|---|---|---|---|
| Black Rose | heavy flourished luxury brush + bold serif "BLACK" | **Yellowtail** → Pacifico / Kaushan | Cinzel ✅ hosted | Cormorant Garamond ✅ | Yellowtail |
| Love Hurts | glossy dripping graffiti brush | **Kaushan Script** → graffiti OFL | Cinzel ✅ | Cormorant Garamond ✅ | Kaushan Script |
| Signature | formal gold Spencerian + classical serif caps | **Pinyon Script** → Allura / Great Vibes | Cinzel ✅ | Cormorant Garamond ✅ | Pinyon Script |
| Kids Capsule | = Signature | Pinyon Script | Cinzel ✅ | Cormorant Garamond ✅ | — |

- All leads are OFL / open-license → self-host woff2 (latin subset), **zero external CDN**. No paid licensing expected; if a final pick requires payment, STOP-AND-SHOW before acquiring.
- **Retire** the 4 named-but-unhosted fonts (Yellowtail-as-LH mapping, Italiana, UnifrakturMaguntia, unhosted Pinyon) and the cross-contaminated secondaries.
- **Collection names remain lockup images, never type-rendered** (`docs/CLAUDE.md` rule 1). These fonts are the collection's *interior* voice (headings/accents/specimens), not the hero name.

## 7. `design-tokens.css` rebuild

Generate the `[data-collection="<slug>"]` blocks from `identity.json`:
- **Palette** → named tokens reflecting canon (e.g. BR: `--skyyrose-accent` = silver, `--skyyrose-bg` = black, `--skyyrose-text` = white; LH: accent red + `--skyyrose-accent-dark` a red variant; SIG/KC: accent gold + `--skyyrose-secondary` rose-gold). No cross-collection colors.
- **Fonts** → two roles: `--skyyrose-font-script` (display brush/calligraphy) + `--skyyrose-font-caps` (Cinzel) + existing `--skyyrose-font-body` (Cormorant). Replaces the single drift-prone `--skyyrose-font-display`; keep `--skyyrose-font-display` as an alias to `--skyyrose-font-caps` for back-compat where existing CSS references it (audit references in P2).
- Generation lands in a **marked region** of `design-tokens.css` (`/* GENERATED:collection-tokens START */ … END */`) so the hand-authored token sections (`:root` globals, motion, etc.) are untouched. The verifier asserts the marked region matches a fresh generation.
- **Prod serves `.min`** (`project_theme_min_build`): any `design-tokens.css` change MUST run `scripts/build-css.js` (P6) or the change is inert live.

## 8. SOT builder changes (`build-collection-sot.py`)

- Read `identity.json` per folder via the shared validated loader; **delete** `COLLECTIONS`, the per-collection `match` regex, and hardcoded accent/font.
- Emit `sot.json` into each `data/collections/<slug>/` (products with resolved image paths + imagery roles + logos + lockup block), DO-NOT-EDIT banner intact.
- **Orphans = pure set-difference, single global artifact** `data/collections/_orphans.json`:
  `registered = (every manifest entry expanded base × declared formats) ∪ catalog product images ∪ logo files`;
  `orphans = tree − registered − known_orphans`. Naming-independent. Replaces per-collection `other_collection_files` (confirmed **zero code consumers** — safe to remove).
  - Base×formats expansion fixes the format-sibling pollution (siblings of a registered base count as claimed).
- `exists()` honors `IMG_EXTS` preference order (webp before avif) instead of alphabetical glob order (current silent bug).
- Guarded master loads: `with open(..., encoding="utf-8")` + try/except → clear stderr + `sys.exit(2)` (in builder and verifier). Missing/typo'd collection key becomes a **schema validation failure**, not a silent empty block.

## 9. Designer hub (`index.html`, generated)

One self-contained page per collection, opened in a browser, rendering **from the canonical `assets/` tree** (no image duplication — single-asset-tree lock honored, founder-approved "reference + rendered gallery"):
- Lockup image (the collection name-as-image)
- Palette swatches (named canon colors with hex)
- Live font specimens (the self-hosted `@font-face` script/caps/body rendering sample text)
- Product gallery (every SKU's resolved image with name/price/preorder flag)
- Collection copy (rendered from `copy.md`: origin / voice / taglines)

Images referenced by relative path into `assets/`; opening the folder's `index.html` in-repo shows everything. (No physical copies; external handoff is out of scope for this milestone — can be a later `--export` build.)

## 10. Verification & tests

- **Drift gate** (`verify-collection-sot.py`, extended): for each collection assert identity ↔ generated `design-tokens.css` marked region match; every `fonts.*.woff2` path resolves; every catalog SKU present in `sot.json`; every declared `resolved` path is a real file; `_orphans.json` is a subset of the tree and disjoint from `registered`.
- **Golden test:** run the builder against the real masters; compare `sot.json` to a committed golden (locks output shape).
- **Unit tests:** `exists()` extension preference (avif+webp present → webp wins), base×formats expansion, orphan set-difference with `known_orphans` suppression, `slug→key` derivation, `load_identity()` validation (rejects malformed/missing).
- Wire into pre-commit / CI alongside `verify-visual-manifest.py`; repoint `catalog-drift-guard.sh` (which already regenerates the SOT on master edits) at the new builder/output.

## 11. Phased plan

| Phase | Produces | Depends on |
|---|---|---|
| **P0 Canon scaffold** | folder convention · `identity.schema.json` · 4 hand-authored `identity.json` · validated `load_identity()` | — |
| **P1 Fonts** | font-ID specimen confirm → lock picks → self-host 3 OFL woff2 + `@font-face` | P0 |
| **P2 design-tokens rebuild** | generated `[data-collection]` blocks (corrected palettes + 2-role font stacks); retire dead names; reference audit for `--skyyrose-font-display` consumers | P0, P1 |
| **P3 SOT builder** | reads `identity.json`; per-folder `sot.json`; `_orphans.json` set-diff; `exists()` ext-pref + guarded loads | P0 |
| **P4 Designer bundle** | per-folder `copy.md` + generated `index.html` hub | P0/P2/P3 |
| **P5 Verify + tests** | drift gate · golden test · unit tests · CI + catalog-drift-guard wiring | all |
| **P6 Cut-over + delete** | consumer census → **repoint every reference to the new SOT** → **founder walkthrough GATE** → **delete all superseded artifacts**; rebuild `design-tokens.min.css`; update README / `docs/CLAUDE.md` / `.wolf/anatomy.md` | all |
| **P7 Verify + review gate** | full re-verify (drift gate + tests green) · wiring/completeness check (no dangling old refs, all folders+files present) · harden · `/simplify` · `/code-review` · security pass | P6 |

### P6 — cut-over contract (hard cut-over, founder-mandated)

1. **Consumer census (before deleting anything):** grep the whole repo for every reference to the old structure — flat `data/collections/*.json`, the `COLLECTIONS` dict, the per-collection regex, retired font names (`Italiana`, `UnifrakturMaguntia`, unhosted `Pinyon`, `Yellowtail`-as-LH), cross-contaminated secondaries, `other_collection_files`, and any scattered per-collection accent/font literals. Produce a census list (file:line → what it references → repoint target).
   - Known starting set to inspect precisely: `scripts/verify_seo.py`, `scripts/site_auditor.py`, `wordpress-theme/skyyrose-flagship/inc/redirects.php`, `assets/js/mascot.js`, `tests/` references, plus the builder/verifier themselves. (`other_collection_files` confirmed **zero consumers** → safe to drop.)
2. **Repoint:** every live consumer now reads the per-folder SOT (`data/collections/<slug>/sot.json`) or `identity.json`, never the old flat file or the dict.
3. **GATE — founder walkthrough (its own task, STOP before any delete):** walk Corey through the census, the exact deletion list, and the repoint diffs together. **No artifact is deleted without explicit founder sign-off in that walkthrough.** Tracked as a standalone item in `tasks/todo.md` so it is not skipped.
4. **Delete (repoint-first, verified, post-walkthrough):** remove the superseded artifacts only after step 2 proves no live consumer remains AND step 3 sign-off is given — flat `data/collections/<slug>.json`, the `COLLECTIONS` dict + regex, dead `@font-face`/font-family declarations, the contaminated secondary tokens, and any obsolete scripts/docs the census flags. Each deletion is justified by a census entry showing zero remaining references.
5. Rebuild `.min` (prod serves it) and update docs/anatomy in the same phase.

### P7 — verification & review gate (no "done" without this)

- Re-run the full drift gate + test suite from a clean state; capture passing output as proof (never claim done without it).
- **Wiring/completeness check:** all 4 folders exist with all 4 files each; every `sot.json`/`index.html` regenerates idempotently; census shows zero dangling old references; every generated value traces to a master.
- Harden, then run `/simplify` (quality pass) and `/code-review` (correctness) on the diff; address findings.
- Security pass on any new file I/O, HTML generation (escape in `index.html`), and path handling.

## 12. Risks / open items

- **Missing reference asset:** founder named `black-rose-logo-thumb-transparent.png` (not in tree). P1 matches Black Rose font from `images/lockups/black-rose-lockup.webp` instead. Signature's named `signature-logo-hero-transparent.png` resolved to `branding/signature-logo-hero.webp`. Flag if the BR thumb exists elsewhere.
- **`.min` rebuild is mandatory** after the `design-tokens.css` change (prod serves `.min`); P6 owns it. Deploy itself is a separate, gated step.
- **Image-read quota** is one-shot per conversation — font-ID in P1 should batch lockup reads, no retries.
- **Parallel-session / dirty tree:** repo has many active worktrees; land this on a branch with clean scope.
- **Deletion safety (hard cut-over):** "delete all old stuff" is repoint-first — never delete an artifact until the census proves zero live consumers. A deletion with a surviving reference is a regression, not a cleanup. Verify each deletion target against the census, not from memory.
- **No paid API in this milestone.** Font acquisition is OFL download; if any pick needs payment, STOP-AND-SHOW first.

## 13. Non-goals

- No bespoke/commissioned font creation (founder chose faithful OFL matches).
- No physical image copies into folders (single-asset-tree lock); external `--export` bundle deferred.
- No product-catalog changes; the catalog CSV stays the product master.
- No deploy to skyyrose.co within this spec (separate gated step after `.min` rebuild + verify).

## 14. Standing build rules (non-negotiable, founder-mandated)

1. **Authoritative sources only.** Every generated value traces to a master read this session — `identity.json`, `skyyrose-catalog.csv`, `visual-manifest.json`, `logo-registry.json`, `design-tokens.css`, or the on-disk asset tree. No invented paths, fonts, colors, or SKUs. If it can't be traced, it doesn't ship.
2. **The new SOT is the single reference.** After cut-over, everything that references a collection points at `data/collections/<slug>/` (`identity.json` for canon, `sot.json` for resolved products/imagery). No code, doc, or template reads the old flat files or the retired dict.
3. **Hard cut-over, repoint-first.** All superseded artifacts are deleted from the repo — but only after the consumer census proves no live reference remains. Repoint, then delete; verify, never assume.
4. **No "done" without proof.** P7 is mandatory: drift gate + tests green (captured output), wiring/completeness verified, `/simplify` + `/code-review` run and findings addressed. A claim of completion without this gate is invalid.
5. **Production discipline:** zero `TODO`/`FIXME`/placeholder in delivered code; `design-tokens.css` change → rebuild `.min`; escape all output in generated `index.html`; land on a clean branch given live worktrees.
