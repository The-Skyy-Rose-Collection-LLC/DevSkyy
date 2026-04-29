# WordPress Template Parts — Agent Guide

## Isolated Workspace

**Your scope — read/write freely:**
```
wordpress-theme/skyyrose-flagship/template-parts/
```

**Adjacent reads allowed (do not write):**
```
wordpress-theme/skyyrose-flagship/inc/product-catalog.php   # catalog helpers
wordpress-theme/skyyrose-flagship/assets/css/               # read CSS only
wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv # verify SKUs
```

**Out of bounds — do not touch:**
```
wordpress-theme/skyyrose-flagship/inc/        # except reading product-catalog.php
wordpress-theme/skyyrose-flagship/assets/js/  # separate agent scope
wordpress-theme/skyyrose-flagship/data/       # read-only
frontend/                                     # separate system
```

If a fix requires changes outside your workspace, stop and report — do not reach across boundaries.

---

## Infrastructure

**Host**: WordPress.com Business plan — NOT self-hosted
- **Deploy**: `bash scripts/deploy-theme.sh` (script) OR `sftp sftp.wp.com` (SSH) — both require explicit user confirmation before execution
- No wp-cli shell access on the host
- PHP 8.2 | WordPress Coding Standard (`.phpcs.xml`)

Template parts live in `template-parts/`. Always loaded via `get_template_part()` — never `require` or `include` directly.

---

## Partial Map

| Partial | Purpose |
|---------|---------|
| `product-card-holo.php` | Holographic glass product card with magnetic tilt |
| `landing/hero.php` | Landing page hero — accepts `$args['collection']` |
| `landing/product-grid.php` | Landing product grid — accepts `$args['skus']` array |
| `landing/faq.php` | Landing FAQ accordion |
| `mobile-nav.php` | Off-canvas mobile navigation |
| `cookie-consent.php` | GDPR cookie banner |
| `size-guide.php` | Size guide modal |
| `toast-container.php` | Toast notification mount point |
| `icon/` | SVG icon partials |

---

## Permissions

You MAY:
- Modify markup/content of any template part within your workspace
- Add new `$args` parameters (always use `wp_parse_args()` for defaults)
- Create new template parts in `template-parts/` or subdirectories
- Use catalog helpers: `skyyrose_get_product()`, `skyyrose_get_collection_products()`
- Add `aria-*` attributes, `data-*` attributes, and CSS classes

You MUST NOT:
- Call `wc_get_products()` — banned in all template parts
- Hardcode product names, prices, or SKU arrays — use catalog helpers
- Load template parts via `require` / `include` — use `get_template_part()`
- Reference retired SKUs: `lh-001`, `sg-004`, `sg-008`, `br-d01`–`br-d04`
- Write `<style>` blocks inline — all styles live in `assets/css/`
- Use `innerHTML` in any associated JavaScript

---

## Safeguards — Hard Rules

**All `$args` must use `wp_parse_args()`:**
```php
$args = wp_parse_args( $args ?? [], [
    'collection' => 'signature',
    'skus'       => [],
    'show_price' => true,
] );
```

**Escape all output:**
```php
echo esc_html( $args['title'] );
echo esc_attr( $args['collection'] );
echo esc_url( $args['link'] );
```

**Content-visibility on heavy image sections:**
```php
<section style="content-visibility:auto;contain-intrinsic-size:0 500px;">
```

**Catalog-only product data — never invent fallbacks:**
```php
$product = skyyrose_get_product( $sku );
if ( empty( $product ) ) {
    continue; // Silent skip — NEVER substitute fake product data
}
```

**Immediate fix mandate**: If you spot a safeguard violation in surrounding code, fix it in the same edit before moving on.

---

## Template Part Call Pattern

```php
// Caller (e.g., a page template)
get_template_part( 'template-parts/landing/hero', null, [
    'collection' => 'black-rose',
    'heading'    => __( 'Black Rose', 'skyyrose' ),
] );

// Inside template-parts/landing/hero.php
$args       = wp_parse_args( $args ?? [], [
    'collection' => 'signature',
    'heading'    => '',
] );
$collection = sanitize_key( $args['collection'] );
$heading    = sanitize_text_field( $args['heading'] );
?>
<section class="lp-hero" data-collection="<?php echo esc_attr( $collection ); ?>">
    <h1><?php echo esc_html( $heading ); ?></h1>
</section>
```

---

## Mandatory Quality Workflow

After every change to any template part, run ALL three steps in order.

### 1. PHP Lint
```bash
cd wordpress-theme/skyyrose-flagship
~/.local/bin/composer exec phpcs -- --standard=.phpcs.xml -s template-parts/
# Zero errors required.
# Auto-fix:
~/.local/bin/composer exec phpcbf -- --standard=.phpcs.xml template-parts/
```

### 2. /simplify
Invoke the `code-simplifier` agent on the modified partial. Verify no logic change — clarity only.

### 3. /verification-loop
```bash
# Verify theme loads — no fatal errors
curl -s -o /dev/null -w "%{http_code}" https://skyyrose.co/
# If the modified partial is used on a specific page, verify that page too:
curl -s -o /dev/null -w "%{http_code}" https://skyyrose.co/collections/black-rose/
# Both must return 200.
```

---

## Do NOT

- Use `wc_get_products()` — banned; use catalog helpers
- Hardcode SKU data — always query via `skyyrose_get_collection_products()`
- Write `<style>` blocks inline in template parts
- Access `$_GET` / `$_POST` directly without `sanitize_*()`
- Skip `wp_parse_args()` for `$args` defaults
- Invent product fallbacks when a SKU is not in the catalog
- Touch files outside your workspace without flagging to the user
