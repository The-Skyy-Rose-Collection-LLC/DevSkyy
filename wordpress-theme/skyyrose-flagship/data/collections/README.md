# Per-Collection Source of Truth (`data/collections/`)

**One folder per collection. Open it to find everything for that collection in one place — identity (story · palette · fonts · lockup), copy, every product + image already resolved to the ONE correct file, and a browser-openable designer hub.**

This exists because collection identity used to be spread across Python (hardcoded
`COLLECTIONS` dicts), CSS (`design-tokens.css`), docs, and three masters that don't
cross-check — so the wrong file/font/color kept getting grabbed and the collections
drifted "all mixed up". Now identity lives in ONE hand-authored file per collection,
and everything else is a generated, CI-verified projection of it.

## Folder layout

```
data/collections/
├── identity.schema.json        JSON Schema — the canon contract (validates every identity.json)
├── _orphans.json               GENERATED — tree image files registered to NO master (audit list)
└── <slug>/                     one per collection: black-rose, love-hurts, signature, kids-capsule
    ├── identity.json           HAND-AUTHORED CANON — story.seed + doc_ref · palette (named hex) ·
    │                           fonts {script, caps, body} · lockup.ref · known_orphans[]
    ├── copy.md                 HAND-AUTHORED — designer copy, verbatim from collection-stories.md
    ├── sot.json                GENERATED — products + resolved imagery/logos/lockup
    └── index.html              GENERATED — designer hub (lockup, palette swatches, live font
                                specimens, product gallery, copy); open in a browser
```

## Hand-authored vs generated

- **Edit ONLY** `identity.json` and `copy.md`. They are the canon seed.
- `sot.json` and `index.html` carry a DO-NOT-EDIT banner — they are regenerated from canon.
- Identity facts exist once (in `identity.json`); `design-tokens.css`, `sot.json`, and
  `index.html` are computed from it, and the verifier proves they match.

## The pipeline

```
identity.json ──> gen-design-tokens.py   ──> assets/css/design-tokens.css  ([data-collection] region)
              ├─> build-collection-sot.py ──> <slug>/sot.json + _orphans.json
              └─> gen-collection-hub.py   ──> <slug>/index.html

verify-collection-sot.py  ── drift gate: identity ↔ design-tokens region ↔ woff2 ↔ catalog ↔ asset tree
```

Run all three generators after editing any `identity.json` (the `catalog-drift-guard`
hook does this automatically on master edits). Then `verify-collection-sot.py` (CI /
pre-commit gate) — exits non-zero on missing SKUs, stale tokens, unresolved fonts, or
any role pointing at a missing file.

## How to use it (designers / agents)

- **Collection identity?** `<slug>/identity.json` — palette (named colors), fonts (script/caps/body), story seed, lockup.
- **A collection's lockup?** `<slug>/sot.json` → `lockup.canonical` (the name-as-image) / `lockup.display_webp.resolved` for web. `lockup.svg_master` only for infinite scale; `lockup.source_art` never placed directly.
- **A product image?** `<slug>/sot.json` → `products[].images.{image,front_model_image,back_image,back_model_image}.resolved`.
- **A scene / hero / lookbook / patch?** `<slug>/sot.json` → `imagery`.
- **Everything at a glance?** open `<slug>/index.html` in a browser.
- **Unregistered files?** `_orphans.json` (global) — tree images in no master. Audit before use; promote a legit one by registering it in `visual-manifest.json` or adding it to a collection's `identity.json` `known_orphans[]`.

## Masters (authoritative sources)

| Domain | Master |
|--------|--------|
| Collection identity (story/palette/fonts/lockup) | `data/collections/<slug>/identity.json` |
| Products | `data/skyyrose-catalog.csv` |
| Non-product imagery | `data/visual-manifest.json` |
| Logos / monograms | `data/logo-registry.json` |
| Palette + font CSS tokens | `assets/css/design-tokens.css` (generated from identity) |

Per-collection fonts are self-hosted woff2 in `assets/fonts/` (Pacifico, Kaushan
Script, Pinyon Script, Grand Hotel + Cinzel/Hanken Grotesk), zero external CDN. The collection NAME is
always the lockup image; the fonts are interior heading/accent voice.

## Known data bugs surfaced (fix in the catalog CSV)

- Some jersey SKUs declare a `back_image` whose file does not exist — listed in each
  SOT's `unresolved_product_images` and reported (non-fatal) by the verifier.
