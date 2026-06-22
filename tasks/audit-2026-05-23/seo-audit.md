# SkyyRose SEO + Structured Data Audit — v1.1.2 (2026-05-23)

**Scope:** JSON-LD coverage, OG/Twitter cards, meta basics, sitemap, robots.txt, heading SEO, internal linking, WooCommerce schema, indexability.
**Source authority:** Live HTTP fetches + `inc/seo.php` (full read this session).
**Out of scope:** A11y, CWV, mobile UX, typography, motion, conversion craft (parallel agents).

---

## Executive Summary

Theme ships complete SEO implementation in `inc/seo.php` with all schema types in code. **Critical disconnect:** all `skyyrose_*_schema()` functions check `if (defined('WPSEO_VERSION')) return;` — if Yoast active on live site, every schema function silently no-ops. JSON-LD absence on live pages (homepage, /collection-signature/, /product/br-001/, /product/sg-001/) consistent with Yoast active but misconfigured OR not outputting equivalent schema. **Root cause of P0.**

Secondary issues fixable: cart/checkout/my-account/wishlist indexed, collection H1s narrative-only, preorder gateway indexed w/ no noindex.

---

## 1. JSON-LD / Schema.org Coverage

| Template | Expected | Live | Source | Status |
|---|---|---|---|---|
| Homepage | Organization, WebSite+SearchAction | No JSON-LD | Hooked, Yoast-gated | P0 |
| Collection (4x) | ItemList + BreadcrumbList | No JSON-LD | Both Yoast-gated | P0 |
| PDP | Product (price, availability, sku, brand, rating) | No JSON-LD | Yoast-gated | P0 |
| WC taxonomy | CollectionPage | Not tested | Yoast-gated | P0 risk |
| Landing pages | None | N/A | No schema hook | P2 |
| About/FAQ/Shipping | None | N/A | Not mapped | P3 |

**Root cause:** `inc/seo.php:35` — `if (defined('WPSEO_VERSION')) return;` on product schema. Same guard at L35, 129, 232, 267, 474, 867, 899 (7 functions).

**Fix options:**
- **A** — Confirm Yoast WC SEO add-on (`WPSEO_WOO_VERSION`) active + configured to emit Product, Organization, BreadcrumbList. Validate via Google Rich Results Test. Zero code change if Yoast doing the job.
- **B** — Yoast active but schema misconfigured: enable schema output per content type in Yoast admin, OR deactivate Yoast schema + let theme functions fire.
- **C** — Yoast absent (CDN cache?): theme code correct, fires on next live request. Validate `curl -s https://skyyrose.co/ | grep -c 'application/ld+json'`.

**Critical theme-code gap regardless of Yoast:** `skyyrose_product_schema()` (L45–111) builds valid Product schema BUT missing `mpn`, `gtin13`, `category`. `brand` only populates if `_product_brand` post meta exists — no fallback to "SkyyRose".

---

## 2. Open Graph + Twitter Cards

| Tag | Impl | Gap |
|---|---|---|
| `og:type` | Per-template (website/product/article) | `og:type="product"` is Meta Commerce, not standard OG (low) |
| `og:title` | Hardcoded in `inc/seo.php:505,519,543` | PDP: `get_the_title() \| site_name` — no keyword modifier |
| `og:description` | Excerpt/content trim | Products w/o excerpt: `wp_trim_words(get_the_content(), 30)` may grab UI text |
| `og:image` | Falls back `assets/branding/sr-primary-hero.webp` | **width/height hardcoded 1200x630 only when post thumbnail exists** (L510–511). Fallback img gets NO dimension tags (L513, 529, 550) |
| `og:url` | `get_permalink()` | Correct |
| `og:locale` + `og:site_name` | Always output (L480–481) | OK |
| `product:price:amount` | PDP (L536–538) | Variable products: `get_price()` returns `''` |
| Twitter `card` | `summary_large_image` always (L598) | OK |
| Twitter `site` | Fallback `skyyroseco` (L601) | OK |
| Twitter `image` | Same fallback, no dimensions | Same issue |

**P1** — Fallback OG/Twitter image emitted with no width/height. FB/LinkedIn crawlers must fetch to measure = round-trip cost. If not exactly 1200x630, FB may crop. Fix: add `og:image:width=1200` + `og:image:height=630` after every `og:image` output at `inc/seo.php` L513, 529, 550, 629, 638, 644.

**P2** — All schema/OG functions gated on `WPSEO_VERSION`. Intentional (Yoast handles OG) but Yoast does NOT emit `product:price:amount` / `product:price:currency` by default → FB/IG product catalog enrichment absent. Fix: move `product:price:*` + `product:availability` OG tags OUTSIDE Yoast guard.

---

## 3. Meta Basics

### Title Tags

| Page | Rendered | Chars | Issues |
|---|---|---|---|
| Collection — Signature | "Shop Signature — Everyday Luxury Essentials \| The Skyy Rose Collection" | ~71 | Over 60. Brand "The Skyy Rose Collection" WRONG — should be "SkyyRose" |
| Product — sg-001 | "The Bridge Series 'The Bay Bridge' Shorts" | ~42 | No brand suffix, no keyword modifier — `pre_get_document_title` only handles template pages, WC products fall to WP default |
| Pre-order | "Pre-Order — Secure Your Pieces \| The Skyy Rose Collection" | ~57 | Wrong brand name |
| Homepage | Not confirmed (head stripped by WebFetch) | — | Check live |

**Source of wrong brand name:** `get_bloginfo('name')` = WordPress Site Title setting (wp-admin → Settings → General). `$brand` variable at `inc/seo.php:768` pulls this. **Fix: Set WP Site Title = "SkyyRose".** Zero code change.

**P1 — Collection titles ~71 chars.** With corrected brand → "Shop Signature — Everyday Luxury Essentials | SkyyRose" = 54 chars. Title fix resolves.

**P2 — Product title tags lack keyword modifier.** `skyyrose_pre_document_title` doesn't handle `is_singular('product')`. Add branch at `inc/seo.php:776`:
```php
if ( is_singular( 'product' ) ) {
    global $product;
    if ( $product instanceof WC_Product ) {
        return $product->get_name() . ' — Buy Online | ' . $brand;
    }
}
```

### Meta Descriptions

`skyyrose_meta_description()` (L699–752) implemented w/ hardcoded descriptions for collection pages, about, preorder, contact, FAQ, shipping-returns. PDP + homepage rely on `get_bloginfo('description')` / `get_the_excerpt()` fallbacks.

**P2** — PDP meta desc falls back to `wp_trim_words(get_the_content(), 30)` (L730). WC product content often empty or contains short desc + UI text. Add PDP branch using catalog `description` field.

**P3** — `wp_trim_words($description, 30)` (L749) truncates to 30 words (~150–180 chars). Not char-count-aware; long words can exceed 160.

### Canonical URLs

`skyyrose_canonical_url()` (L666–690) correct for singular, front, shop, taxonomy. No pagination canonical (`rel="prev"/"next"`) — low risk at 36 products. Yoast-gated.

### Robots Meta

`skyyrose_robots_meta()` (L845–852) only adds `noindex` on search + 404. **No noindex on cart, checkout, my-account, wishlist.**

---

## 4. Sitemap + robots.txt

### robots.txt live:
```
Sitemap: https://skyyrose.co/sitemap.xml
Sitemap: https://skyyrose.co/news-sitemap.xml
User-agent: *
Disallow: /wp-content/uploads/wc-logs/
Disallow: /wp-content/uploads/woocommerce_transient_files/
Disallow: /wp-content/uploads/woocommerce_uploads/
Disallow: /*?add-to-cart=
Disallow: /*?*add-to-cart=
Disallow: /wp-admin/
Allow: /wp-admin/admin-ajax.php
```

**P2** — `news-sitemap.xml` declared. Fashion e-commerce ≠ news publisher. URL either 404 (wasted crawl) or lists non-news (confuses News crawler). Verify; remove `Sitemap:` declaration if 404.

**P1** — Cart/checkout/my-account NOT blocked at path level. Add:
```
Disallow: /cart/
Disallow: /checkout/
Disallow: /my-account/
Disallow: /wishlist/
```

### sitemap-1.xml live (61 URLs)

**P1 — Non-indexable transactional pages in sitemap:**

| URL | In sitemap? | Fix |
|---|---|---|
| `/cart/` | No — session state | Remove from sitemap plugin config |
| `/checkout/` | No — requires cart | Remove |
| `/my-account/` | No — login-gated, personalized | Remove |
| `/wishlist/` | No — user-specific | Remove |
| `/hello-world/` | No — default WP draft | Delete post or set to draft |

**Positive:** 36 product URLs, 4 collection, 4 landing, 4 experience. Image sitemap + video sitemap present.

**P2** — `/pre-order/` indexed w/ no noindex. Title "Pre-Order — Secure Your Pieces", H1 just "Pre-Order", no schema. Either:
- Intentional landing → add keyword copy + Product/Event schema
- Transactional gate → add `<meta name="robots" content="noindex,follow">` branch at L845

---

## 5. Heading Semantic SEO

| Page | H1 | Keyword value | Assessment |
|---|---|---|---|
| `/collection-signature/` | "Where It All Began" | None | P2 narrative |
| `/product/br-001/` | "BLACK Rose Crewneck" | Product name OK | Pass |
| `/product/sg-001/` | (need verify) | — | TBD |
| Pre-order | "Pre-Order" | Minimal | P3 |

Collection H1s authored in `template-collection-*.php`, brand-narrative not keyword-targeted.

**P2 — Collection H1s zero keyword SEO value.** "Where It All Began" doesn't match streetwear/fashion query intent.
- **Option 1:** Visually hidden keyword H1 via `class="screen-reader-text"` above narrative headline. Accessible + SEO-effective. Aligns w/ "Visuals Over Dialog" founder preference (session #7392).
- **Option 2:** SEO `<p>` w/ semantic microdata adjacent to H1.

**P2 — H2s on collection pages 100% decorative.** "Chapter One", "The First Rose", etc. — no search intent. Below-fold H2s should progressively introduce keyword variants.

---

## 6. Internal Linking

**Homepage → landing pages:** 4 landing URLs in sitemap. Presence ≠ internal link. Homepage Three.js portal-driven. If portals render JS anchors w/o `href`, Googlebot won't follow.

**P2** — Verify landing pages have ≥1 internal link from crawlable anchor. Nav menu = reliable crawl path.

**Collection → PDP breadcrumb:** `skyyrose_get_breadcrumb_trail()` (L305–416) builds: Home → Shop → {Category} → {Product}. Uses `wc_get_page_id('shop')` + WC `product_cat`. **Custom collection pages (`template-collection-*.php`) NOT in PDP breadcrumb.** Goes to WC `/shop/` + product_cat, not `/collection-signature/`. Custom collection pages orphaned from PDP link equity.

**P3** — Extend `skyyrose_get_breadcrumb_trail()` to check `_product_brand` or `_product_collection` meta, link to appropriate custom collection page.

---

## 7. WooCommerce Schema Completeness

`skyyrose_product_schema()` (L45–111):

| Field | Present | Notes |
|---|---|---|
| `@type: Product` | Yes | |
| `name`, `description`, `sku` | Yes | |
| `image` | Yes single only | No array for gallery |
| `offers.@type/url/priceCurrency` | Yes | |
| `offers.price` | Yes — variable handled correctly at L56 | |
| `offers.availability` | Yes | InStock/OutOfStock |
| `brand.@type: Brand` | Conditional — `_product_brand` meta only | **P2 no fallback** |
| `aggregateRating` + `review` | Conditional, top 5 approved | OK |
| `mpn`, `gtin13`, `color`, `material`, `category`, `offers.priceValidUntil` | Missing | P3 |

**P1 revised** — `inc/seo.php:536` OG `product:price:amount` uses `$product->get_price()` w/o variable guard → empty for variable products. Fix:
```php
$product->is_type('variable') ? $product->get_variation_price('min') : $product->get_price()
```
(Note: schema L56 already does this correctly; OG L536 doesn't.)

**P2** — Brand fallback. L62: `$brand ?: 'SkyyRose'`.

---

## 8. Prioritized Fix List

| Pri | Finding | File:Line | Fix |
|-----|---------|-----------|-----|
| P0 | JSON-LD absent on all live pages — Yoast guard silencing all schema | `inc/seo.php:35,129,232,267,474,867,899` | Verify Yoast schema config OR remove guards if Yoast schema disabled |
| P0 | OG/Twitter absent — same Yoast guard | `inc/seo.php:474` | Same |
| P1 | cart/checkout/my-account/wishlist in sitemap | Sitemap plugin config | Remove from plugin's included pages |
| P1 | cart/checkout/my-account/wishlist not in robots.txt | robots.txt | Add Disallow paths |
| P1 | Fallback OG/Twitter image no width/height | `inc/seo.php:513,529,550,629,638,644` | Emit `og:image:width=1200` + `og:image:height=630` on all fallback outputs |
| P1 | OG product:price:amount empty for variable products | `inc/seo.php:536` | Variable guard |
| P1 | WP Site Title = "The Skyy Rose Collection" wrong | wp-admin → Settings → General | Change to "SkyyRose" |
| P2 | Collection H1s narrative-only, no keywords | `template-collection-*.php` (4) | Hidden keyword H1 via `screen-reader-text` |
| P2 | Brand fallback missing in schema | `inc/seo.php:62` | `$brand ?: 'SkyyRose'` |
| P2 | PDP meta desc falls back to content trim (UI text risk) | `inc/seo.php:730` | PDP branch w/ catalog short_description |
| P2 | Product title tags no keyword modifier | `inc/seo.php:776` | Add `is_singular('product')` branch |
| P2 | product:price:* OG absent when Yoast active | `inc/seo.php:533–539` | Move outside Yoast guard |
| P2 | Preorder gateway indexed w/ minimal copy + no schema | `inc/seo.php:845` | noindex OR schema + keyword copy |
| P2 | news-sitemap.xml — fashion ≠ news | robots.txt | Verify URL, remove if 404 |
| P2 | Custom collection pages disconnected from PDP breadcrumb | `inc/seo.php:347–366` | Add `_product_collection` meta check |
| P3 | PDP schema missing color, material, category | `inc/seo.php:45–111` | Add from `skyyrose_get_product($sku)` |
| P3 | Landing pages no schema | `inc/seo.php` | Add WebPage or Event schema |
| P3 | `hello-world/` default WP post in sitemap | WP admin | Delete or draft |
| P3 | Breadcrumb uses `/collections/` page fallback that may 404 | `inc/seo.php:339` | Verify page exists |

---

## Key Confirmed Facts (sourced this session)

- `inc/seo.php` implements 7 schema types + OG + Twitter + canonical + meta desc + robots + title filter
- Every function has `if (defined('WPSEO_VERSION')) return;` guard
- Live pages return zero JSON-LD on: homepage, /collection-signature/, /product/br-001/, /product/sg-001/
- sitemap-1.xml: 61 URLs incl. /cart/, /checkout/, /my-account/, /wishlist/, /pre-order/
- robots.txt does NOT Disallow /cart/, /checkout/, /my-account/ at path level
- Collection H1 = "Where It All Began" (confirmed live)
- WP Site Title = "The Skyy Rose Collection" (confirmed from rendered title tags) — NOT "SkyyRose"
- `skyyrose_pre_document_title()` L768 uses `get_bloginfo('name')` for `$brand`
