# Trusted Reference Set — Canonical Sources for V2 Development

**Source:** `docs/SKYYROSE_WORDPRESS_PLAN.md §1.5.4`
**Phase 0 seeding date:** 2026-05-03
**How to use:** Before writing code that touches any of the 16 domains below, load the canonical source
first. "Loaded" means: use Context7 (`mcp__claude_ai_Context7__resolve-library-id` →
`mcp__claude_ai_Context7__query-docs`) for libraries, or fetch the primary vendor doc page for platform
references. Do not rely on training memory for API signatures — versions drift.

---

## 1. WordPress Core

**Domain:** CMS core (hooks, filters, template functions, REST API, Options API)
**Canonical source:** https://developer.wordpress.org/
**Key sections:** Plugin Handbook (hooks/actions/filters), Theme Handbook (template hierarchy, template
tags), REST API Handbook (route registration, `WP_REST_Request`, authentication), Code Reference (function
signatures with version notes).
**V2 note:** WordPress.com Business runs WordPress 6.x — verify version compatibility for any new API
function, especially block editor APIs and Full Site Editing. Use `index.php?rest_route=` not `/wp-json/`
(WordPress.com routing constraint).

---

## 2. WooCommerce

**Domain:** E-commerce hooks, product data, cart/checkout, REST API
**Canonical source:** https://developer.woocommerce.com/
**Key sections:** Action and Filter Reference (hook signatures with version), REST API Reference (v3 endpoint
schemas), WC_Product class methods, WC_Cart and WC_Checkout hooks.
**V2 note:** Always use `skyyrose_get_product_catalog()` / `skyyrose_get_collection_products()` from
`inc/product-catalog.php` for catalog data in templates — never `wc_get_products()`. WC REST write
operations require STOP-AND-SHOW confirmation (production write).

---

## 3. PHP Standards (PSR / PHP.net)

**Domain:** PHP language reference, PSR coding standards
**Canonical source:** https://www.php.net/manual/ and https://www.php-fig.org/psr/
**Key sections:** Language Reference (type system, exceptions, generators), Security chapter (password
hashing, input filtering, prepared statements). PSR-1 (basic coding standard), PSR-2 (coding style),
PSR-4 (autoloading).
**V2 note:** Theme requires PHP 8.2+. Use named arguments and union types freely. PHPCS WordPress standard
enforced via `.phpcs.xml` — run `vendor/bin/phpcs` before commits.

---

## 4. Three.js

**Domain:** 3D rendering (WebGL, scene graph, loaders, post-processing)
**Canonical source:** https://threejs.org/docs/
**Key sections:** Core (Object3D, Scene, Renderer), Loaders (GLTFLoader), Materials (MeshStandardMaterial,
MeshPhysicalMaterial), Post-processing (EffectComposer, passes).
**V2 note:** CDN version is locked at `three@0.160.0` — do NOT upgrade without explicit approval. The
immersive experience files (`assets/js/experiences/`) were written against this version. Breaking changes
in r161+ could silently corrupt shadow maps and HDR environment loading.

---

## 5. React Three Fiber (R3F)

**Domain:** React bindings for Three.js (Vercel dashboard / Next.js side only)
**Canonical source:** https://docs.pmnd.rs/react-three-fiber/
**Key sections:** Getting Started, API Reference (useFrame, useThree, useLoader), Drei helpers.
**V2 note:** R3F is for the Vercel dashboard (`devskyy.app`) only — NOT for the WordPress theme. The
WordPress theme uses vanilla Three.js via CDN. Never import R3F into theme JavaScript files.

---

## 6. GSAP

**Domain:** Animation library (ScrollTrigger, timelines, ease curves)
**Canonical source:** https://gsap.com/docs/v3/
**Key sections:** Core (gsap.to, gsap.timeline, easing), ScrollTrigger plugin, GSDevTools.
**V2 note:** GSAP is used in the WordPress theme for `preorder`, `about`, and `immersive` templates ONLY.
Collection pages use IntersectionObserver scroll-reveal (`.col-reveal` class) — NOT GSAP. Landing pages
use `.lp-rv` IntersectionObserver. Using GSAP on a collection or landing page is an anti-pattern.

---

## 7. CSS / Web Platform

**Domain:** Modern CSS (custom properties, cascade layers, container queries, scroll-driven animations)
**Canonical source:** https://developer.mozilla.org/en-US/docs/Web/CSS
**Key sections:** CSS Custom Properties, @layer, @container, scroll-driven animations, CSS Grid, Flexbox.
**V2 note:** The theme uses scroll-driven animations for homepage interactions (cmem #347). CSS custom
properties (`--collection-*`, `--lp-*`) drive collection palette switching via `data-collection` attributes.
Container queries are preferred over media queries for component-level responsive design.

---

## 8. Tailwind CSS

**Domain:** Utility-first CSS (Vercel dashboard / Next.js side only)
**Canonical source:** https://tailwindcss.com/docs
**Key sections:** Core Concepts (utility classes, responsive prefixes), Configuration (tailwind.config.js,
theme extension), Arbitrary values, CSS-in-JS integration.
**V2 note:** Tailwind is for the Vercel dashboard (`frontend/`) ONLY — NOT for the WordPress theme. The
WordPress theme uses hand-authored CSS with design tokens defined in `assets/css/design-tokens.css`.
Never add Tailwind dependencies to `wordpress-theme/`.

---

## 9. Accessibility (WCAG)

**Domain:** Web accessibility standards and techniques
**Canonical source:** https://www.w3.org/WAI/WCAG22/quickref/
**Key sections:** Perceivable (1.3.1 Info and Relationships, 1.4.3 Contrast), Operable (2.1.1 Keyboard,
2.4.3 Focus Order), Understandable (3.1.1 Language), Robust (4.1.2 Name/Role/Value).
**V2 note:** Target is WCAG 2.2 AA. The production audit (serena: production_audit_findings) scored
Frontend at 7.5/10 — accessibility was one of the gaps. All new V2 pages must pass WCAG AA before launch.
Key items: holo cards must be keyboard-navigable; collection pages must have visible focus rings; modals
must trap focus.

---

## 10. Performance (Core Web Vitals / Lighthouse)

**Domain:** Web performance metrics, measurement, and optimization
**Canonical source:** https://web.dev/performance/ and https://developers.google.com/search/docs/appearance/core-web-vitals
**Key sections:** LCP (Largest Contentful Paint), CLS (Cumulative Layout Shift), INP (Interaction to Next
Paint), Image optimization, JavaScript loading strategies.
**V2 note:** All fonts are self-hosted woff2 (zero Google Fonts CDN). `inc/performance.php` removes
Jetpack Google Fonts. AVIF support is enabled. Target: LCP < 2.5s on 3G. Three.js experience assets
(GLB models) must be lazy-loaded and gated behind user intent (scroll past fold / click "Enter Experience").

---

## 11. Schema.org / SEO (Structured Data)

**Domain:** JSON-LD structured data, OpenGraph, Twitter Cards, meta tags
**Canonical source:** https://schema.org/ and https://developers.google.com/search/docs/appearance/structured-data
**Key sections:** Product schema, BreadcrumbList, Organization, Article, FAQPage.
**V2 note:** The new FAQ pages (`page-faq.php`) must include `FAQPage` JSON-LD. Product pages should have
`Product` + `Offer` schema. The WordPress theme's `inc/seo.php` handles meta tags — extend it for V2
page types rather than adding ad-hoc meta output to templates.

---

## 12. Stripe

**Domain:** Payment processing (Checkout, Payment Intents, webhooks)
**Canonical source:** https://stripe.com/docs
**Key sections:** Checkout Session API, Payment Intents, Webhooks (event types, signature verification),
WooCommerce Stripe plugin integration.
**V2 note:** Stripe is integrated via the WooCommerce Stripe plugin — do not build a direct Stripe
integration from scratch. Any Stripe-related V2 work (custom checkout flow, pre-order payment capture,
drop waitlist billing) must layer on top of the existing WC plugin, not replace it.

---

## 13. Klaviyo

**Domain:** Email marketing (flows, campaigns, list management, custom properties)
**Canonical source:** https://developers.klaviyo.com/
**Key sections:** Track API (server-side events), Identify API (profile properties), Flows (trigger types,
conditional splits), List API (subscription management).
**V2 note:** Klaviyo is integrated for drop waitlist, post-purchase flows, and collection launch announcements.
The `mcp__claude_ai_Klaviyo__*` MCP tools are available for Klaviyo operations. All Klaviyo write
operations (profile create/update, campaign send, list subscribe) are confirmed per the cost-cap policy
(they are free-tier but production writes — confirm before executing).

---

## 14. Pinecone

**Domain:** Vector database (upsert, query, metadata filtering)
**Canonical source:** https://docs.pinecone.io/
**Key sections:** Python client (`pinecone-client`), Upsert API, Query API (top-k, metadata filter), Index
management.
**V2 note:** Index name: `skyyrose-catalog`, region: `us-west-2`, dimensions: 1024, metric: cosine.
Standard plan. Score scale is cosine similarity (0–1, higher is better) — different from ChromaDB's
distance scale. Re-index on catalog changes only (ADR 0001). Voyage embeddings use `voyageai>=0.2.4`
(version constraint: 0.3.x is prerelease on Python 3.14).

---

## 15. FASHN

**Domain:** AI virtual try-on (product-to-model, outfit composition)
**Canonical source:** https://fashn.ai/docs
**Key sections:** Tryon endpoint, product-to-model endpoint, image requirements (background, resolution),
pricing model.
**V2 note:** FASHN calls are ALWAYS STOP-AND-SHOW regardless of individual call cost (see ADR 0002 and
`eval/cost-cap-policy.md`). Per-session limit: 30 calls. Before any FASHN call, confirm: (a) source
garment file is the correct SKU, (b) model image is approved, (c) estimated cost is within budget.

---

## 16. Anthropic (Claude API)

**Domain:** LLM inference (claude-sonnet, claude-opus, claude-haiku), Claude SDK
**Canonical source:** https://docs.anthropic.com/
**Key sections:** Messages API (system prompts, tool use, vision), Python SDK (`anthropic` package),
Rate limits and pricing, Claude Code SDK integration.
**V2 note:** Model assignments (from MEMORY.md): Vision = `gemini-3-flash-preview`, QC = `claude-sonnet-4`,
Compositor brain = `claude-opus-4-6`, Nano Banana primary = `gemini-2.5-flash-image`. Per-session Anthropic
budget: $25 (autonomous). Synthesis calls >$1 are edge cases given typical token volumes — if encountered,
STOP-AND-SHOW applies.

---

## How to Add to This Set

A new source may be added to the trusted set when:
1. It becomes a primary dependency for a new V2 feature domain.
2. It has stable, versioned documentation that can be fetched via Context7 or direct URL.
3. It is used more than once in a single V2 phase.

Proposed additions go in `tasks/todo.md` as a proposal. The standard for inclusion is "canonical primary
vendor documentation" — not blog posts, tutorials, or Stack Overflow answers (those may be cited in
individual pattern/lesson entries but are not part of the trusted set).
