# Product Masters Registry

Canonical, locked reference imagery for every SkyyRose SKU. One master per SKU. Immutable.

## Contract

Every downstream visual asset (compositor renders, marketing variants, ad creative) **must**
derive from a master in this directory — never from a generated variant or a scratch file in
`editorial-staging/`.

Enforcement is **soft** in Wave 1 (telemetry-only). Hard enforcement lands in Wave 2 once
every live SKU has a master registered.

## Layout

```
assets/product-masters/
├── manifest.json           # The registry — one entry per SKU, hash-pinned
├── README.md               # This file
├── <sku>.webp              # Master image (photograph, CAD render, or 3D-model render)
└── <sku>-alpha.png         # Optional alpha matte (background-removed subject)
```

## manifest.json schema

```json
{
  "version": 1,
  "generated_at": "ISO-8601 UTC",
  "masters": {
    "br-001": {
      "sku": "br-001",
      "master_path": "br-001.webp",
      "master_hash": "sha256:...",
      "master_source": "photograph",
      "collection": "black-rose",
      "alpha_path": "br-001-alpha.png",
      "alpha_hash": "sha256:...",
      "color_spec": {"primary": "#0A0A0A", "accents": ["#B76E79"]},
      "text_spec": ["SKYY ROSE"],
      "photographed_at": "2026-03-08T14:22:00Z",
      "locked_at_version": "v3.2.0",
      "notes": ""
    }
  }
}
```

## master_source values

| Value                 | When to use                                                              |
|-----------------------|--------------------------------------------------------------------------|
| `photograph`          | Physical product photographed against a neutral background               |
| `cad_render`          | Rendered from a CAD file or tech pack (pre-order SKUs without samples)   |
| `3d_model`            | Deterministic render from a 3D model (Meshy, Polycam, etc.)              |
| `generative_locked`   | One-time generative output — locked by hash, never regenerated           |

## Registering a master (Python)

```python
from skyyrose.elite_studio.master_registry import Manifest

m = Manifest.load()
m.register(
    sku="br-001",
    master_path="br-001.webp",
    master_source="photograph",
    collection="black-rose",
    alpha_path="br-001-alpha.png",
    color_spec={"primary": "#0A0A0A", "accents": ["#B76E79"]},
    text_spec=["SKYY ROSE"],
    photographed_at="2026-03-08T14:22:00Z",
    locked_at_version="v3.2.0",
)
m.save()
```

Duplicates raise `ValueError` unless `overwrite=True`. A SKU once locked should stay locked;
use `overwrite` only when re-photographing a product for a new season.

## Verifying a master

```python
m = Manifest.load()
ok = m.verify("br-001", "editorial-staging/black-rose/br-001-hero.webp")
```

Returns `True` iff the file's SHA-256 matches the registered `master_hash`.

## Never

- Never edit `manifest.json` by hand — always use `Manifest.save()`.
- Never mark a generative-AI output as `master_source: photograph`.
- Never delete a master file without bumping the manifest version and retiring the SKU.
