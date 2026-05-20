<claude-mem-context>

</claude-mem-context>

# agents/product_generation/ — Product generation pipeline placeholder

Stub directory for the planned automated product generation pipeline. No implementation exists yet.

## Key files

- `devskyy_fidelity/` — empty; planned location for fidelity assets and generation artifacts

## Conventions

- When implementing: product generation must source SKU data from `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` — never from memory or hard-coded values.
- Image generation calls (FASHN, FLUX, Gemini) require STOP AND SHOW confirmation before dispatch — see project `CLAUDE.md`.
- Fidelity assets in `devskyy_fidelity/` should not be committed to the repo — add to `.gitignore` when the directory is populated.

## Don't

- Don't add generation scripts here that call paid APIs without the STOP AND SHOW gate.
- Don't hard-code SKUs or product data — always load from the catalog CSV at runtime.

## Related

- `skyyrose/elite_studio/` — current canonical imagery hub for product image generation
- `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` — authoritative product catalog
- `scripts/nano_banana/` — existing product image generation scripts
- `.planning/ROADMAP.md` — tracks when product generation work is scheduled
