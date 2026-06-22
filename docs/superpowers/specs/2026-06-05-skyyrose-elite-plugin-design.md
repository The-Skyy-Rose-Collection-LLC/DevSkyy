# SkyyRose Elite Plugin — Design Spec

**Date:** 2026-06-05
**Status:** Approved (founder), building
**Owner:** DevSkyy engineering agent

## Goal

Bundle the SkyyRose marketing & commerce skills into **one installable Claude Code plugin** (`skyyrose-elite`), keep **every** skill, **enhance** each with verified vendor docs, author **seven specialist agent personas** that embed the skills, and **wire** the whole thing to the Elite Team runtime + Elite Studio pipelines + dev-team workflow.

## Decisions (founder-approved)

- **Packaging:** installable CC plugin (`.claude-plugin/plugin.json` + `marketplace.json`), mirroring the repo's `wordpress-copilot` pattern.
- **Elite-team embedding:** CC subagent personas (markdown), each loading its skill(s), wired to the Python runtime via documented seams (see `WIRING.md`).
- **Stubs:** scaffold `skyyrose-influencer-growth` + `skyyrose-photography-brief` distilled from the existing `skyyrose-social-*` twins; delete the empty stubs after.
- **Launch Commander:** **propose-roster-and-wait** — never auto-runs paid-media/email/WC actions.
- **Keep every skill; enhance all with verified docs.**

## Components

### Skills (9, in `skills/`)
`skyyrose-brand-dna`, `skyyrose-content-engine`, `skyyrose-product-copy`, `skyyrose-seo-commerce`, `skyyrose-email-flows`, `skyyrose-paid-media`, `skyyrose-influencer-growth` (new), `skyyrose-photography-brief` (new), `skyyrose-launch-commander`.

### Agents (7, in `agents/`)
`skyyrose-content-engine`, `skyyrose-email-strategist`, `skyyrose-paid-media-buyer`, `skyyrose-seo-commerce`, `skyyrose-influencer-lead`, `skyyrose-photography-director`, `skyyrose-launch-commander`.

### Command
`/skyyrose-elite <intent>` — dispatcher + full-campaign mode.

## Verified-doc enhancements (per skill)

| Skill | Inject (Context7-verified) | Canon bug to fix |
|---|---|---|
| `email-flows` | Klaviyo trigger types (`Started Checkout` vs `Added to Cart` metric), conditional-split, predictive analytics, suppression, A/B | Post-purchase Email 3 cross-sell link → remove (violates no-cross-sell) |
| `paid-media` | Meta campaign hierarchy + bid strategies (`LOWEST_COST_WITH_MIN_ROAS` + `roas_average_floor`), Advantage+ toggle; Google PMax (`advertising_channel_type=PERFORMANCE_MAX`, `merchant_id`) + Standard Shopping (`SHOPPING_PRODUCT_ADS`); add Pixel/CAPI + Merchant Center feed (`availability: preorder`) | Frame budget splits as starting points, not fact |
| `seo-commerce` | schema.org availability URIs (`InStock`/`PreOrder`/`OutOfStock`); add `ItemList` for collections; WC REST `meta_data` for Yoast/RankMath | Hardcoded `PreOrder` for all products → gate on WC pre-order meta; remove related-products-on-PDP |
| `product-copy` | WC REST field mapping (`name`/`description`/`short_description`/`meta_data`); schema.org `material`/`color`/`size`; image `alt` | "use memory for names" → "use catalog CSV/dossier" |
| `content-engine` | Add date stamp + catalog warning + escape hatch to brand-dna | — |
| `launch-commander` | WooCommerce pre-order plugin context; Meta ad-review SLA (24-48h); add STOP-AND-SHOW gate | Broken refs to influencer/photography skills now resolve |
| `brand-dna` | Cross-reference brand-guardrails.md | — |
| `influencer-growth` (new) | FTC disclosure (cited to ftc.gov, not Context7), platform creator programs, CA model-release/AB-2496 | Built from social twins |
| `photography-brief` (new) | WooCommerce image specs, sRGB delivery, platform crop safe-zones, model release | Built from social twins |

## Wiring (summary — full in `WIRING.md`)

- Persona → runtime seam table (content→`SkyyRoseContentAgent`, email/influencer→`MarketingAgent`, paid-media→`agents/core/marketing/` slot, photography→`SkyyRoseImageryAgent`, launch→`orchestrator.route`).
- Dev-team lane: extend `batch` enum + `agentFor()` in `.claude/workflows/skyyrose-dev-team.js` (applied to main at install — gitignored, not shipped).
- Data spine: catalog CSV + dossiers → content agent → WC REST `meta_data`.

## Migration / install steps (post-build, on main)

1. Register local marketplace + install plugin; verify the 9 skills load under the plugin namespace.
2. Delete the old `.claude/skills/skyyrose-*` copies (now canonical in the plugin) + the 2 empty global stubs — no double-load.
3. Fix 3 path-based doc refs (`docs/brand/visual-references.md:67`, `docs/superpowers/specs/2026-05-25-v2-mockup-design.md:259`, `docs/archive/.../ENHANCED_WORDPRESS_PROMPT.md:12`).
4. Apply dev-team marketing lane edit.

## Quality bar

No `TODO`/placeholder/stub content. Every external claim traces to a verified doc. Every agent references a real skill. `plugin.json`/`marketplace.json` valid. Canon violations removed. Names unique.
