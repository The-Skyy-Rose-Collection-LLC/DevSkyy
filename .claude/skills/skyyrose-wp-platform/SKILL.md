---
name: skyyrose-wp-platform
description: The SkyyRose flagship theme's own engineering doctrine (wordpress-theme/skyyrose-flagship/) -- not a generic WordPress reference, a stack-specific one built around this brand's actual collections, visual canon, and production pipeline. Covers block/template development, WooCommerce integration, the vanilla three.js mascot and immersive worlds, and the quality gates that keep a luxury storefront feeling luxury. Use for any task touching the theme's PHP, the .min build pipeline, WooCommerce REST/webhooks, or the site's Three.js scenes.
---

# SkyyRose WordPress Platform

"Luxury Grows from Concrete." This skill exists because a generic WordPress reference can't
carry that -- it doesn't know the difference between Black Rose's gothic armor and Love Hurts'
"bloodline that raised me," it doesn't know the mascot is the face of the brand, and it doesn't
know a wrong-garment render is the single most repeated defect on this project. Every section
below is written for THIS storefront, not a portable template that happens to mention it.

It replaces what fifteen scattered generic skills (`wp-block-development`, `wp-block-themes`,
`wordpress-plugin-core`, `wordpress-router`, `wp-performance`, `wp-plugin-development`,
`wp-rest-api`, `woocommerce*`, `wc-pdp-correctness`, `immersive-interactive-architect`,
`css-cascade-discipline`, `accessibility`, `seo`, `web-vitals-budgets`) covered in the abstract.
Those stay installed -- disabling them is a separate, confirmed decision -- but nothing in
this skill borrows their generic framing. If a section here could apply unchanged to any other
WooCommerce theme, it's wrong and should be rewritten until it can't.

## Brand doctrine (the part a generic skill has no way to know)

- **Four collections, four identities, never interchangeable**: Signature (gold `#D4AF37`,
  Archivo headings, Pinyon Script name-lockup, city-tour immersive world), Black Rose (silver
  `#C0C0C0`, Archivo headings with Cinzel as engraved-caps accent, SkyyRose Black Rose Script
  name-lockup, gothic cathedral immersive world, armor as its visual language), Love Hurts
  (crimson `#DC143C`, Archivo headings, SkyyRose Love Hurts Graffiti name-lockup, romantic
  castle immersive world, "the bloodline that raised me" -- that line belongs to Love Hurts
  alone, never borrowed for another collection), Kids Capsule (rose gold `#B76E79`, Archivo
  headings, Grand Hotel name-lockup). Collection name-lockups are bespoke-script images, never
  live type; interior copy is unified (Archivo display, Hanken Grotesk body/UI, Anton UI caps).
  Rose Gold `#B76E79` is also the global accent
  across the whole storefront; `#0A0A0A` is the dark background every collection sits on.
- **Visual lineage is Kith, Oaklandish, Culture Kings, Fear of God, Palm Angels — never
  European luxury.** This is a locked canon decision, not a style preference. A build,
  render, or copy pass that reaches for European-luxury visual language is wrong regardless
  of how polished it looks.
- **The mascot is the face of the brand** -- a full-body walk-on presence, not a chatbot, not
  a decorative widget. Its rig integrity (see `threejs-immersive.md`) is treated with the same
  seriousness as the product photography.
- **Real products only.** No hallucinated or never-made renders reach this storefront. Product
  imagery resolves through the catalog CSV + SOT manifest, never a filename guess -- see
  `woocommerce-integration.md`.
- **The founder is the authority on the brand's own story.** Corey's bio and product dossiers
  are founder-authored, not ML-drafted -- this skill documents how the engineering serves that
  voice, it does not generate brand narrative itself.

## Router — which reference file for which task

| Task | Read |
|---|---|
| Templates, patterns, blocks, `.min` build pipeline, enqueue/template routing | `reference/build-and-templates.md` |
| WooCommerce REST v3, webhooks, product sync, PDP correctness | `reference/woocommerce-integration.md` |
| The mascot, the four immersive worlds, anything in `skyy-3d.js` or `assets/scenes/` | `reference/threejs-immersive.md` (and `threejs-animation` + `3d-rigging-pipeline` for the Blender/animation side) |
| Accessibility, SEO/schema, Core Web Vitals, CSS cascade discipline, CSP/nonce security -- the gates that keep the storefront feeling like the brand it claims to be | `reference/quality-gates.md` |

Read only the reference file(s) the task actually needs -- this router file plus one
reference file is the normal footprint, not all four.

## Universal discipline (applies to every reference file below)

Every capability below exists to protect one thing: nothing about SkyyRose ships generic,
half-verified, or unchecked against the real brand. Three non-negotiable layers, inherited by
every reference file -- do not restate them per-section there:

**1. efficient-production discipline.** Before any tool call: do I already have this? No
re-reading a file already read this session. No rebuilding `.min` assets you haven't actually
changed source for. Batch parallel reads/greps instead of issuing them one at a time. Zero
`TODO`/placeholder/dummy data in delivered PHP or JS. Every factual claim about this theme's
code traces to a `Read`/`Grep` call from this session, not memory of an earlier session.

**2. Boris Cherny's verification philosophy (tip #14, verbatim).** "Give Claude a way to
verify its work... invest in domain-specific verification, it 2-3x's quality." Every section
below names a *specific, re-derivable* verification method using a real authoritative source
for this project -- never "looks correct," never a self-graded pass from the same script that
made the change. If you cannot name what tool call proves a claim, the claim isn't done yet.

**3. Production-gate before "done."** Match this project's existing Loop Protocol: write the
change, run the real check for that domain (phpcs, `.min` rebuild + curl, WooCommerce REST
read-back, Playwright, Context7 lookup), read the actual output, fix if it fails, repeat up to
5 times, stop and report if the same error repeats twice. Never claim "deployed" or "fixed"
without the check's actual output from this session.

## Verification sources this skill trusts (and why)

| Claim type | Authoritative check | Never substitute |
|---|---|---|
| PHP syntax/style | `php -l` + `vendor/bin/phpcs --standard=.phpcs.xml -s .` | Reading the code and assuming it's valid |
| Live HTML/JSON-LD/headers | `curl -s "URL?cb=$(date +%s)"` (cache-busted) | `WebFetch` -- it strips `<script>` tags, silently hiding JSON-LD/OG data |
| Visual/rendering result | Playwright or Chrome DevTools MCP screenshot, desktop + mobile | Trusting a curl 200 as "the page looks right" |
| WooCommerce/product state | Live REST v3 read via `.env.wordpress` BasicAuth | The catalog CSV alone -- CSV is the source of truth for what *should* be true, REST is the source of truth for what *is* live |
| Product imagery ↔ SKU match | Reading the actual pixels (vision) against the catalog/dossier | The filename or the manifest -- both can lie, and wrong-garment imagery is this project's most repeated defect |
| Library/API usage (WP, WooCommerce, Elementor, three.js) | Context7 `resolve-library-id` → `query-docs` | Memory of the API shape -- training data predates recent WP/WC/three.js releases |
| `.min` build actually changed | Diff or byte-size check on the `.min` output itself | Confirming the source file changed and stopping there |

## See also

- `threejs-animation` — runtime playback mechanics (this skill's `threejs-immersive.md` covers
  the WP-specific loading/CSP wiring, not general three.js API)
- `3d-rigging-pipeline` — Blender-side authoring for anything this theme's Three.js scenes play back
- `wc-pdp-correctness`, `woocommerce-webhooks` — still installed standalone; this skill's
  `woocommerce-integration.md` is the stack-specific entry point, not a replacement for their detail
