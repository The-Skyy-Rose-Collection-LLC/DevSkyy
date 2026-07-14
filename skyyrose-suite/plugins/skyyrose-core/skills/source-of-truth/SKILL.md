---
name: source-of-truth
description: Use before caching, quoting, or acting on ANY product, imagery, or brand fact — resolve it from the canonical source registered in SOT.md, never from memory or a filename. Prevents second-copy drift and wrong-fact defects.
origin: SkyyRose
---

# Source of Truth

Every product, imagery, and brand fact has exactly one canonical home, registered in
`SOT.md` at the repo root and surfaced as root symlinks (`skyyrose-catalog.csv`,
`sot-images.json`, `cerebrum.md`, `anatomy.md`, …). **Memory rots; the canonical file
does not.** Resolving a fact from recollection, a filename, or a second copy is how wrong
facts reach the site — it is what produced the lh-005 fanny-pack (a product resolved from
a non-canonical store). This skill makes "read the SOT first" the reflex before any
product-touching work.

> **Boot first:** read `SOT.md` before caching any product / imagery / brand fact — it
> names the one canonical source for each. Never fork or introduce a second copy of a SOT.

## When to Use

- Before quoting a SKU, price, name, collection, or material — any product fact.
- Before resolving a product image — the manifest is identity, the filename is not.
- Before stating a brand fact (tagline, collection canon, founder voice).
- Before caching any of the above into memory, a render prompt, or page content.

## The canonical map

| Fact | Canonical source | Resolve via |
|------|------------------|-------------|
| Product (SKU, price, name, collection, material) | `skyyrose-catalog.csv` + per-SKU dossier | catalog loader — the CSV, then the dossier |
| Product imagery | `data/sot-images.json` (generated; `make sot-manifest`) | `skyyrose.core.sot_images` — front-first |
| Brand canon | brand canon / `from-interview.md` / `brand.yaml` | read it; do not paraphrase from memory |
| Prior work / "did we solve this?" | `.wolf/buglog.json` + claude-mem | see [[memory-system]] |

Reference products by **name, not SKU** — SKU-first lookups caused br-001 conflations.

## Loop until the fact traces to the SOT

Bounded, like [[drive-to-green]] — ≤5, stop on repeat:

```
1. Need a product/imagery/brand fact.
2. Resolve it through the SOT-registered source (CSV / manifest / canon), never memory.
3. Quote the canonical value (row, dossier line, manifest entry).
4. If the source disagrees with what you assumed → the SOURCE wins; correct and re-check.
```

## Verify from an authoritative source

- **Quote the canonical file, not your memory.** A product fact cites the catalog CSV row
  or dossier; an image cites its `sot-images.json` entry; a brand fact cites the canon.
- **Prove single-source.** Before trusting a fact, confirm there is no second copy feeding
  it — `grep` for duplicate stores; a fork of the catalog/manifest is garbage, and using it
  is a fail-open (see [[fail-closed-audit]], [[dependency-hygiene]]'s single-source rule).
- **Pixels over filenames** for imagery — the manifest resolves identity, then
  [[product-image-fidelity-gate]] eyes-on confirms the garment. A filename never proves it.

## Adversarial pass

- [[adversarial-verification]] — assume the remembered value / filename is WRONG until the
  canonical source confirms it. For anything touching a render or the live site, default to
  "unverified" and resolve through the SOT before proceeding.

## Guardrails · Handoff · Log

- Canonical-sources-only is LOCKED — other stores are garbage; never introduce a second SOT.
- Regenerate generated SOTs the sanctioned way (`make sot-manifest`) — never hand-edit them.
- Product-image work → hand to `skyyrose-design` with [[product-image-fidelity-gate]];
  catalog drift → `skyyrose-core`; log corrections via [[self-learning]] per `CROSS-PLUGIN.md`.
