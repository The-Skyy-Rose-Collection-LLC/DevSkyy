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

**Dashboard (display):** `frontend/lib/collections.ts` — RESOLVED. Now derives products from
`@/lib/catalog` via `getEnrichedCollection`/`getAllEnrichedCollections` in `catalog-server.ts`;
the raw `COLLECTIONS` config carries no hand-populated `products` array. Removed from
`ALLOWLIST` in `tests/test_sot_no_adhoc_imagery.py`.

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

---

# Product Render Playbook (OAI gpt-image-2)

Read before ANY product render. Exists so sessions STOP re-deriving the same fidelity checks.
Engine: `scripts/oai-render-run.py` (`dry-run` free · `generate --yes` PAID, STOP-AND-SHOW).
Cost: gpt-image-2 ≈ **$0.40/image** floor · **$50** hard run cap (SpendTracker). Preflight with `dry-run`.

## Reference priority — real photo wins

Fidelity comes from the *reference image*, not prose. Authority order for a SKU's garment look:
1. **Real product photo** (founder-shared or `assets/products/references/{sku}-*real*front*`) — GROUND TRUTH.
2. **Techflat** (`assets/products/references/{sku}-techflat.jpeg` / dossier `reference_image`).
3. **Dossier prose** — disambiguates, never the sole source.

Founder shares a real garment photo → copy to `assets/products/references/{sku}-<name>-real-front.jpeg`;
`references.py` auto-resolves it via the `{sku}-*real*front*` glob (no dossier frontmatter edit). Then regen the
manifest and re-render. **Canon can outrank the SOT image** — a SKU's SOT/on-model photo can be STALE vs the true
design (lh-004 bomber hood, br-006 name). Founder ruling + dossier + real photo are authority; if they disagree,
flag it, don't render the stale one.

## Render Fidelity Checklist — verify EVERY render, pre and post (eyes-on vs dossier)

- **Patches present.** Jerseys carry the league AUTHENTIC patch (NFL/MLB/NBA/hockey), lower-left hip. Pipeline
  REFUSES patchless jerseys — a missing patch = a missing `assets/products/techflats/hero-overlays/br-patch-*.png`,
  not a prompt tweak.
- **Numbers — fill + split.** Digit fill (rose-cluster / solid / plain) matches spec PER DIGIT and PER PLACEMENT.
  A two-digit number on a sleeve shows the FULL number on EACH sleeve (never "2" on one, "3" on the other). Never a
  hollow digit where the spec says rose-fill.
- **Lettering treatment.** White-with-black-border vs solid-black vs tackle-twill differ by colorway and by
  front/back. Check letter FILL + border, not just the text.
- **Set completeness.** A "set" SKU renders ALL pieces (hoodie + joggers). Paired on-model shows both.
- **Fabric read.** Nylon windbreaker (sheen/structure) ≠ cotton-fleece sweatsuit; satin bomber ≠ fleece; sherpa
  lining visible where specified. Wrong fabric = re-spec the dossier fabric lock + re-render.
- **Colorway.** Body / hood / trim / cuff+waistband bands per DOSSIER (its COLORWAY note), not the CSV `color`
  field (can be stale).
- **Wrong-garment (#1 defect).** The rendered garment must be THIS SKU. Looks like a different product → stop.

Renders land in `renders/oai/<slug>/`; a QC-judge failure sends them to `renders/oai/_rejected/<slug>/`.
`_rejected` on a JUDGE ERROR ≠ quality rejection — QC by eye and promote the good ones.

## Dossier precision — write specs the model can't misread

Every defect traces to a dossier line readable two ways. When a render is wrong, fix the DOSSIER (reusable spec),
then re-render — don't just re-roll. State exact placement/count/fill ("the FULL '32' on EACH sleeve"). Add a
NEGATIVE for every wrong reading seen ("NO split single digit per sleeve", "NO hollow digit — carries the same rose
fill", "NO solid-black letters — white with black border"). Keep front/back/sleeves independent when they differ.

## Environment (renders run from a full checkout with keys)

- **Keys:** `gemini/.env` needs `OPENAI_API_KEY` (image gen) AND `ANTHROPIC_API_KEY` (QC judge). Loader =
  `config/load_env.py`. Missing ANTHROPIC = QC-gate crash BEFORE spend; judge account also needs positive credit
  balance or every QC call errors → all outputs to `_rejected` as needs-review (then QC by eye).
- **Sparse worktree** excludes `assets/` (since 2026-07-12). Before rendering or regenerating the manifest:
  `git sparse-checkout add assets/products` so references AND the manifest resolve against the FULL tree.
  Regenerating manifest.json against a sparse tree DROPS entries and corrupts it (bug-273, class of bug-252).
- **After ANY catalog CSV / dossier / reference-asset edit, regen ALL derived artifacts** (bug-273):
  `build_asset_manifest.py` · `build-collection-sot.py` · `python -m skyyrose.core.sot_images`. The asset manifest
  hashes dossiers + names + reference photos and has a Stop-gate test.

## Gate

`dry-run` first (free) → show manifest + image count + cost → wait for explicit **y** → `generate --yes`
(prepend `STOPSHOW_ACK=1`). Eyes-on QC every output vs dossier. Promotion to the live catalog (wire into
`sot-images.json` + deploy) is a SEPARATE founder-gated production step.
