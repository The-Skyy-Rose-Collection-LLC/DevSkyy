---
name: skyyrose-seo-commerce
description: "WooCommerce SEO system for SkyyRose. Keyword strategy, product page optimization, collection SEO, schema markup with PHP code, technical SEO checklist, and site architecture. Use when optimizing skyyrose.co for search engines or auditing SEO performance."
allowed-tools: Read Write Edit Glob Grep Bash
---

# SkyyRose E-Commerce SEO System

## When to Use This Skill

- Optimizing WooCommerce product pages for search
- Writing SEO meta titles and descriptions
- Adding schema markup (JSON-LD) to the WordPress theme
- Auditing site SEO health
- Planning keyword strategy for luxury streetwear
- Building internal linking architecture
- Optimizing collection/category pages

---

## Keyword Strategy

### Brand Keywords (Protect)
| Keyword | Search Intent | Priority |
|---------|--------------|----------|
| skyyrose | Brand search | Must own #1 |
| skyy rose collection | Brand search | Must own #1 |
| skyyrose clothing | Brand + category | Must own #1 |

### Category Keywords (Target)
| Keyword | Volume Est. | Difficulty | Target Page |
|---------|-----------|-----------|-------------|
| luxury streetwear | High | High | Homepage / About |
| Black-owned clothing brand | Medium | Medium | About page |
| Oakland streetwear | Low-Medium | Low | Homepage / Collections |
| Bay Area clothing brand | Medium | Medium | About page |
| limited edition streetwear | Medium | Medium | Shop / Collections |
| Black-owned streetwear | Medium | Low | About / Collections |
| luxury hoodies men | Medium | High | Black Rose Collection |
| streetwear jerseys | Medium | Medium | Black Rose Collection |
| designer joggers | Medium | High | Signature Collection |

### Long-Tail Keywords (Content + Product Pages)
- "Black-owned luxury hoodie brand"
- "limited edition streetwear Oakland"
- "Bay Area designer clothing"
- "premium streetwear pre-order"
- "luxury streetwear for kids"
- "Oakland fashion brand founded by single dad"
- "heavyweight french terry hoodie"
- "limited edition basketball jersey Black-owned"

### Local SEO Keywords
- "clothing brand Oakland CA"
- "streetwear brand San Francisco Bay Area"
- "Black-owned business Oakland"
- "fashion brand San Leandro CA"

---

## WooCommerce Product SEO

### Product Title Formula
```
[Primary Keyword] — [Brand] [Differentiator]
```
Examples:
- "Black Rose Heavyweight Hoodie — SkyyRose Limited Edition"
- "Bay Bridge Premium Shorts — SkyyRose Bridge Series"
- "Love Hurts Varsity Jacket — SkyyRose Full-Grain Leather"

### Short Description (WooCommerce excerpt)
- 150-200 characters
- Primary keyword in first sentence
- Benefit-first, then feature
- End with differentiator (limited, Oakland-made, etc.)

### Long Description Structure
```
[SEO-rich opening paragraph — primary keyword + brand story hook]

[Product story — cultural reference, design intent]

[Construction details with secondary keywords]
- Material and weight
- Stitching and hardware
- Design elements

[Fit guide with keywords]

[Pre-order / availability — urgency keywords]

[CTA]
```

### Image Alt Text Formula
```
[Product name] [view] — [one detail] | SkyyRose [Collection]
```
Examples:
- "Black Rose Hoodie front view — embroidered script heavyweight French terry | SkyyRose Black Rose Collection"
- "Bay Bridge Shorts lifestyle — gold hardware on Oakland waterfront | SkyyRose Signature"

### URL Slug Best Practices
- `/product/black-rose-hoodie/` NOT `/product/br-004/`
- Include primary keyword
- No filler words (a, the, and)
- Hyphens between words
- Lowercase only

### Yoast / RankMath Configuration
```
SEO Title: [Product Name] — [Key Feature] | SkyyRose
Meta Description: [Benefit] + [key feature] + [differentiator]. [CTA]. [155 chars max]
Focus Keyword: [primary keyword for this product]
```

---

## Collection Page SEO

### Per-Collection Optimization

**Black Rose Collection:**
```
H1: Black Rose Collection — Limited Edition Oakland Streetwear
Meta Title: Black Rose Collection — Dark Luxury Streetwear | SkyyRose (56 chars)
Meta Desc: Limited edition streetwear from Oakland. Heavyweight hoodies, collector jerseys, statement pieces. Pre-order from SkyyRose Black Rose. (134 chars)
Focus: "limited edition streetwear", "Oakland streetwear"
```

**Love Hurts Collection:**
```
H1: Love Hurts Collection — Streetwear That Speaks
Meta Title: Love Hurts Collection — Luxury Streetwear | SkyyRose (52 chars)
Meta Desc: Raw emotion turned wearable. Varsity jackets, joggers, and shorts from SkyyRose Love Hurts. Limited pre-order runs. (115 chars)
Focus: "luxury streetwear collection", "varsity jacket streetwear"
```

**Signature Collection:**
```
H1: Signature Collection — Bay Area Everyday Luxury
Meta Title: Signature Collection — Bay Area Luxury Streetwear | SkyyRose (58 chars)
Meta Desc: Golden hour in cotton. Bay Area-inspired hoodies, shorts, and tees from SkyyRose Signature. Premium essentials, limited runs. (124 chars)
Focus: "Bay Area clothing", "luxury streetwear essentials"
```

**Kids Capsule:**
```
H1: Kids Capsule — Little Royalty by SkyyRose
Meta Title: Kids Streetwear — SkyyRose Kids Capsule Collection (50 chars)
Meta Desc: Luxury streetwear for kids. Matching sets in purple and red. Black-owned, designed in Oakland. Shop SkyyRose Kids. (114 chars)
Focus: "kids streetwear", "Black-owned kids clothing"
```

---

## Schema Markup (JSON-LD for WordPress)

### Product Schema (add to `inc/seo.php` or `functions.php`)

```php
/**
 * Enhanced Product Schema for SkyyRose WooCommerce
 * Adds PreOrder availability, brand, and review data
 */
add_action('wp_head', 'skyyrose_product_schema');
function skyyrose_product_schema() {
    if (!is_product()) return;

    global $product;
    if (!$product) return;

    $schema = array(
        '@context'    => 'https://schema.org',
        '@type'       => 'Product',
        'name'        => $product->get_name(),
        'description' => wp_strip_all_tags($product->get_short_description()),
        'image'       => wp_get_attachment_url($product->get_image_id()),
        'sku'         => $product->get_sku(),
        'brand'       => array(
            '@type' => 'Brand',
            'name'  => 'SkyyRose',
            'url'   => 'https://skyyrose.co',
        ),
        'offers'      => array(
            '@type'         => 'Offer',
            'price'         => $product->get_price(),
            'priceCurrency' => 'USD',
            'url'           => get_permalink(),
            'availability'  => $product->is_in_stock()
                ? 'https://schema.org/PreOrder'
                : 'https://schema.org/SoldOut',
            'seller'        => array(
                '@type' => 'Organization',
                'name'  => 'The Skyy Rose Collection LLC',
            ),
        ),
    );

    // Add review data if available
    if ($product->get_review_count() > 0) {
        $schema['aggregateRating'] = array(
            '@type'       => 'AggregateRating',
            'ratingValue' => $product->get_average_rating(),
            'reviewCount' => $product->get_review_count(),
        );
    }

    echo '<script type="application/ld+json">'
        . wp_json_encode($schema, JSON_UNESCAPED_SLASHES | JSON_HEX_TAG)
        . '</script>' . "\n";
}
```

### Organization Schema (site-wide)

```php
add_action('wp_head', 'skyyrose_org_schema');
function skyyrose_org_schema() {
    if (!is_front_page()) return;

    $schema = array(
        '@context'    => 'https://schema.org',
        '@type'       => 'Organization',
        'name'        => 'The Skyy Rose Collection',
        'url'         => 'https://skyyrose.co',
        'logo'        => get_template_directory_uri() . '/assets/images/branding/skyyrose-logo.png',
        'description' => 'Luxury streetwear brand from Oakland, California. Founded by Corey Foster.',
        'founder'     => array(
            '@type' => 'Person',
            'name'  => 'Corey Foster',
        ),
        'address'     => array(
            '@type'           => 'PostalAddress',
            'addressLocality' => 'Oakland',
            'addressRegion'   => 'CA',
            'addressCountry'  => 'US',
        ),
        'sameAs'      => array(
            'https://instagram.com/theskyyrosecollection',
            'https://tiktok.com/@skyyrose',
            'https://x.com/skyyrose',
        ),
    );

    echo '<script type="application/ld+json">'
        . wp_json_encode($schema, JSON_UNESCAPED_SLASHES | JSON_HEX_TAG)
        . '</script>' . "\n";
}
```

### BreadcrumbList Schema

```php
add_action('wp_head', 'skyyrose_breadcrumb_schema');
function skyyrose_breadcrumb_schema() {
    if (is_front_page()) return;

    $items = array();
    $items[] = array(
        '@type'    => 'ListItem',
        'position' => 1,
        'name'     => 'Home',
        'item'     => home_url(),
    );

    if (is_product_category()) {
        $term = get_queried_object();
        $items[] = array(
            '@type'    => 'ListItem',
            'position' => 2,
            'name'     => 'Shop',
            'item'     => get_permalink(wc_get_page_id('shop')),
        );
        $items[] = array(
            '@type'    => 'ListItem',
            'position' => 3,
            'name'     => $term->name,
        );
    } elseif (is_product()) {
        global $product;
        $terms = get_the_terms($product->get_id(), 'product_cat');
        if ($terms && !is_wp_error($terms)) {
            $items[] = array(
                '@type'    => 'ListItem',
                'position' => 2,
                'name'     => $terms[0]->name,
                'item'     => get_term_link($terms[0]),
            );
        }
        $items[] = array(
            '@type'    => 'ListItem',
            'position' => count($items) + 1,
            'name'     => $product->get_name(),
        );
    }

    $schema = array(
        '@context'        => 'https://schema.org',
        '@type'           => 'BreadcrumbList',
        'itemListElement' => $items,
    );

    echo '<script type="application/ld+json">'
        . wp_json_encode($schema, JSON_UNESCAPED_SLASHES | JSON_HEX_TAG)
        . '</script>' . "\n";
}
```

---

## Technical SEO Checklist

### Core Web Vitals Targets
| Metric | Target | How to Check |
|--------|--------|-------------|
| LCP (Largest Contentful Paint) | < 2.5s | PageSpeed Insights |
| INP (Interaction to Next Paint) | < 200ms | PageSpeed Insights |
| CLS (Cumulative Layout Shift) | < 0.1 | PageSpeed Insights |

### Image Optimization
- [ ] All product images served as WebP (use `<picture>` with JPEG fallback)
- [ ] Lazy loading on below-fold images (`loading="lazy"`)
- [ ] Explicit width/height attributes to prevent CLS
- [ ] Max file size: 200KB for product images, 500KB for hero banners
- [ ] Alt text on every image (use formula above)

### Sitemap & Indexing
- [ ] XML sitemap at `/sitemap.xml` (Yoast generates this)
- [ ] Products, collections, and pages all in sitemap
- [ ] `robots.txt` blocks: `/cart/`, `/checkout/`, `/my-account/`, `/wp-admin/`
- [ ] No `noindex` on product or collection pages
- [ ] Submit sitemap to Google Search Console

### Canonical URLs
- [ ] Each product has a single canonical URL
- [ ] Variant pages (size, color) point canonical to main product
- [ ] Pre-order products use same URL when they transition to in-stock
- [ ] No duplicate content between collection pages and shop page

### Mobile-First
- [ ] All pages pass Google Mobile-Friendly Test
- [ ] Touch targets >= 48px
- [ ] No horizontal scrolling on any page
- [ ] Font size >= 16px on mobile
- [ ] Product images swipeable on mobile gallery

### Page Speed
- [ ] Critical CSS inlined in `<head>`
- [ ] JavaScript deferred (`defer` attribute)
- [ ] Third-party scripts (analytics, chat) loaded async
- [ ] Font preloading for Cinzel, Playfair Display, Cormorant Garamond
- [ ] CDN cache headers set correctly (bump SKYYROSE_VERSION for busting)

---

## Site Architecture

### URL Hierarchy
```
skyyrose.co/
├── /shop/                          (all products)
├── /collections/black-rose/        (collection page)
├── /collections/love-hurts/
├── /collections/signature/
├── /collections/kids-capsule/
├── /product/black-rose-hoodie/     (individual product)
├── /product/bay-bridge-shorts/
├── /about/                         (brand story)
├── /preorder/                      (pre-order gateway)
└── /blog/                          (content marketing)
```

### Internal Linking Rules
1. Every product page links to its collection page
2. Every collection page links to all its products
3. Collection pages cross-link to related collections
4. Blog posts link to relevant products and collections
5. About page links to all collections
6. Pre-order gateway links to active pre-order products

### Related Products Strategy
- Show 4 related products on each product page
- Priority: same collection > same product type > same price range
- Never show out-of-stock products in related without "Sold Out" badge

---

## SEO Audit Workflow

### Monthly Audit Checklist
1. **Search Console check:** crawl errors, index coverage, manual actions
2. **Keyword rankings:** track top 20 keywords, note movement
3. **Page speed:** run PageSpeed Insights on homepage + top 5 product pages
4. **Broken links:** scan with Screaming Frog or similar
5. **Content freshness:** update any product descriptions changed by new drops
6. **Schema validation:** test with Google Rich Results Test
7. **Mobile check:** spot-check 3 pages on actual phone
8. **Competitor check:** search top 5 keywords, note who's ranking

### Priority Fix Matrix
| Issue | Impact | Urgency | Fix First? |
|-------|--------|---------|-----------|
| Missing meta titles/descriptions | High | High | Yes |
| Missing product alt text | Medium | Medium | Yes |
| Slow page speed (>3s LCP) | High | High | Yes |
| Missing schema markup | Medium | Medium | After basics |
| Broken internal links | Medium | High | Yes |
| Thin product descriptions (<100 words) | Medium | Medium | Batch fix |
| Missing canonical tags | High | Medium | Yes |
| No XML sitemap submission | High | High | Yes |

---

## Anti-Patterns

- **DO NOT** keyword-stuff product titles — "Luxury Hoodie Black Rose Hoodie Oakland Streetwear Hoodie" is spam
- **DO NOT** use the same meta description on multiple pages — each page needs unique meta
- **DO NOT** block CSS/JS in robots.txt — Googlebot needs to render pages
- **DO NOT** use JavaScript-only content for product descriptions — crawlers may miss it
- **DO NOT** ignore Search Console warnings — they indicate real indexing problems
- **DO NOT** change URLs without 301 redirects — broken links kill SEO equity
- **DO NOT** rely solely on Yoast green lights — Yoast checks basics, not strategy
