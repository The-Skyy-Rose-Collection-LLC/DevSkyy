# SOT-Only Product Imagery — Policy & Enforcement

**Locked 2026-06-23 (founder directive).** Status: mechanism shipped; consumer backlog open + guarded.

> **The rule:** the SOT is the *only* reference for product imagery. Every surface —
> WordPress, the dashboard, Claude Code / Desktop, subagents, pipelines, skills,
> plugins, MCP tools — resolves a SKU's image through the SOT, never through a
> hardcoded path, a fabricated placeholder, or a guessed filename.

## What "the SOT" is

- **Master:** `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` columns
  `front_model_image`, `back_model_image`, `back_image`, `image`.
- **Generated view:** `data/collections/<slug>/sot.json` (`products[].images`), built by
  `data/build-collection-sot.py`.
- **Resolver (the authority):** `skyyrose/core/sot_images.py` —
  `resolve_image(sku, role)`, `has_render(sku)`, `build_manifest()`, `write_manifest()`.
- **Manifest for non-Python surfaces:** `data/sot-images.json` (`{sku: {front, back, packshot}}`),
  regenerated via `make sot-manifest`.

## The fallback rule (front-first)

`role="front"` → `front_model_image` → `image` (flat packshot last). `role="back"` →
`back_model_image` → `back_image`. `role="packshot"` → `image`. This mirrors the WP theme's
`template-parts/product-card-holo.php` exactly. **Never show the flat `image` packshot as the
default front** — that is the "flatlay" bug (the dead `product-card-expand` bundler bound cards
to `image`, producing wrong/flatlay previews; fixed 2026-06-23).

## How to consume

| Surface | Do this |
|---|---|
| Python (pipelines, MCP, agents, scripts) | `from skyyrose.core.sot_images import resolve_image` |
| TS/JS (dashboard) | read `data/sot-images.json` (or `@/lib/catalog` `getProduct(sku)`) |
| PHP (WP theme) | already compliant — `front_model_image` first via `skyyrose_product_image_uri()` |
| Any agent / skill / prompt | reference `data/sot-images.json`, never `assets/images/products/...` literally |

## Enforcement

- **Guard:** `tests/test_sot_no_adhoc_imagery.py` — fails CI on a NEW fabricated
  `/images/scenes/*-product-*` image or a hardcoded product-image literal in the dashboard
  display layer (`frontend/lib|components|app`). Its `ALLOWLIST` is a ratchet that may only shrink.
- **Regen:** `make sot-manifest` after any catalog image change (kept out of `review.approve()`
  on purpose — that write-side has no test-isolation seam; see memory #18918).

## Consumer backlog (audited 2026-06-23 — route each to `resolve_image`)

Write-side feeders that *populate* the SOT columns (`skyyrose/core/review.py`,
`scripts/tripo_publish.py`, `skyyrose/elite_studio/catalog.py`, `scripts/approve_ghost.py`)
are **compliant** — they feed the SOT, they don't bypass it. The READ-side consumers below
display/use product imagery from non-SOT sources and must be migrated:

**Dashboard (display):** `frontend/lib/collections.ts` — hardcoded `/images/scenes/*-product-*`
+ a drifted product list (`lh-006`, `sg-003/005/011/012/013/014` with fabricated names). Real fix
= derive products from `@/lib/catalog` (already SOT-correct) + SOT image URLs; needs the renders
served (currently 404 on skyyrose.co, absent from `frontend/public`) → one-way sync into
`frontend/public/assets/images/products/` (mirror the design-system `sync-theme-assets.mjs` pattern).

**MCP tools:** `mcp_tools/tools/virtual_tryon.py` · `threed.py` · `lora_generation.py` ·
`oai_render.py` · `core/runtime/tool_registry.py` (try-on example) — accept free-form image URLs;
resolve from SKU via `resolve_image` when a `sku`/`product_id` is supplied.

**Pipelines:** `skyyrose/elite_studio/agents/tryon_agent.py:172` (`_find_garment_image` → scratch
`renders/output/`), `scripts/batch_flux_collections.py`, `scripts/tripo_dispatch.py`,
`scripts/tripo_spike_asset_extraction.py` — read CSV `image`/`back_image` directly for generation
input; route through `resolve_image`.

**Agents / prompts:** `agents/claude_sdk/domain_agents/{imagery,immersive,creative}.py`,
`agents/elite_web_builder/agents/imagery.py` — system prompts point at `assets/images/products/`;
redirect to `data/sot-images.json`.

**WP/WC integration:** `integrations/wordpress_client.py`, `integrations/wordpress_product_sync.py`,
`agents/wordpress_bridge/mcp_server.py`, `api/ar_sessions.py` (`SAMPLE_AR_PRODUCTS` hardcodes
non-catalog SKUs + `wp-content/uploads` URLs) — populate `image_urls` from `resolve_image` at
construction.

Each migration removes its surface from the bypass set; the dashboard entry also leaves the guard
ALLOWLIST when fixed.

## Related canon

- `~/.claude/projects/-Users-theceo-DevSkyy/memory/feedback_canonical_sources_only.md`
- `~/.claude/projects/-Users-theceo-DevSkyy/memory/feedback_single_asset_tree.md`
- `skyyrose/core/paths.py` (path authority)
