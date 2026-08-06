# SOT Component Map

Use this map before searching the repository for product or visual truth. It
routes a task to a component owner; it does not duplicate the source data in
[SOT.md](../../SOT.md).

## Read path

```text
task domain + component
        |
        v
SOT.md registry -> owner/source -> generated consumers -> matching guard
```

## Component contracts

| Domain | Component | Canonical source | Owner / consumer boundary | Guard |
|---|---|---|---|---|
| `wordpress-theme/skyyrose-flagship` | product catalog | `data/skyyrose-catalog.csv` | `skyyrose.core.catalog_loader`; downstream sync stays a consumer | `scripts/validate_catalog_consistency.py` |
| `wordpress-theme/skyyrose-flagship` | product narrative | `data/dossiers/<name>.md` | founder-authored garment truth, resolved by dossier loaders | catalog consistency + dossier checks |
| `wordpress-theme/skyyrose-flagship` | product imagery | `data/sot-images.json` | `skyyrose.core.sot_images.resolve_image()` | SOT-image and no-ad-hoc-imagery tests |
| `wordpress-theme/skyyrose-flagship` | non-product imagery | `data/visual-manifest.json` | theme visual resolver / manifest consumers | `data/verify-visual-manifest.py` |
| `wordpress-theme/skyyrose-flagship` | collection identity | `data/collections/<slug>/identity.json` | `data/build-collection-sot.py` produces collection views | `data/verify-collection-sot.py` |
| `wordpress-theme/skyyrose-flagship` | lookbook | `scripts/lookbook-manifest.json` plus declared collection SOTs | `scripts/sot/lookbook.py`; root `build-lookbook-*.py` scripts are compatibility-only | `lookbook_sot_current`, `lookbook_html_current` |
| brand | structured identity | `assets/brand/brand.yaml` | `scripts/sync_brand_to_php.py` generates PHP consumer | brand sync checks |
| brand | typography | `data/brand/typography.json` | `data/gen-design-tokens.py` generates token CSS | token generator verifier |

## Rules that keep scans small

- Start at the exact source in the table; do not recursively search `assets/`,
  `docs/archive/`, or old scripts for a competing truth.
- A generated consumer is never edited to correct truth. Update its declared
  source, regenerate through the component owner, and run its guard.
- Add a new component only by registering its source, owner, generated outputs,
  and a failure-on-drift guard in the same change.
- Root scripts may preserve a public command, but implementation belongs under
  the component package that owns its domain.
