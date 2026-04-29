# WordPress Inc — Agent Guide

## Infrastructure

**Host**: WordPress.com Business plan — NOT self-hosted
- NO wp-cli shell access — commands like `wp post create` will fail silently
- **Deploy**: `bash scripts/deploy-theme.sh` (atomic hot-swap script) OR `sftp sftp.wp.com` (SSH) — both require explicit user confirmation before execution
- NO direct database access — use WooCommerce REST API for data writes (also requires confirmation)
- PHP 8.2 | WordPress latest | WooCommerce latest

**PHP standard**: WordPress Coding Standard enforced via `.phpcs.xml` in theme root
- Check: `cd wordpress-theme/skyyrose-flagship && ~/.local/bin/composer exec phpcs -- --standard=.phpcs.xml -s inc/`
- Auto-fix: `~/.local/bin/composer exec phpcbf -- --standard=.phpcs.xml inc/`
- Composer installed at: `~/.local/bin/composer`

---

## Module Map

| File | Purpose |
|------|---------|
| `enqueue.php` | All CSS/JS loading; template slug detection map |
| `security.php` | CSP headers, rate limiting, ABSPATH guards |
| `seo.php` | JSON-LD schemas (Organization, Product, ItemList), OG/Twitter tags, breadcrumbs |
| `woocommerce.php` | WC hooks, shop overrides, cart behavior |
| `woocommerce-preorder.php` | Pre-order meta, display, add-to-cart logic |
| `product-catalog.php` | Canonical catalog loader — `skyyrose_get_product()`, `skyyrose_get_collection_products()` |
| `patterns.php` | Block pattern registration (files live in `patterns/` directory) |
| `performance.php` | AVIF support, custom image sizes, Google Fonts removal |
| `ajax.php` | AJAX handler registration — nonce + capability checks required |
| `builders/detection.php` | `skyyrose_active_builder()`, `skyyrose_builder_owns_template()` |
| `builders/elementor.php` | Elementor widget/skin registration |
| `builders/divi.php` | Divi module registration |
| `builders/beaver.php` | Beaver Builder module registration |
| `builders/bricks.php` | Bricks element registration |

---

## Permissions

You MAY:
- Add or modify PHP functions in any `inc/` file
- Add new action/filter hooks via `add_action()` / `add_filter()`
- Add new helper functions to `product-catalog.php` using the catalog array pattern
- Add new JSON-LD schema functions to `seo.php`
- Add new AJAX handlers to `ajax.php` (nonce + capability checks mandatory)
- Register new block patterns in `patterns.php`
- Read catalog data via `skyyrose_get_product_catalog()` — never hardcode SKU data

You MUST NOT (without explicit user confirmation):
- Execute `bash scripts/deploy-theme.sh` or any SFTP file transfer
- Call WooCommerce REST API write endpoints (create/update/delete product, order, media)
- Delete or rename any existing `inc/` file
- Modify `enqueue.php` without verifying the template slug map remains correct after your change

---

## Safeguards — Hard Rules

**Escape all output — no exceptions:**
```php
echo esc_html( $var );          // text content
echo esc_attr( $var );          // HTML attributes
echo esc_url( $var );           // URLs
echo wp_kses_post( $content );  // trusted HTML content
```

**Sanitize all input:**
```php
$val = sanitize_text_field( $_POST['field'] );
$id  = absint( $_GET['id'] );
$key = sanitize_key( $_REQUEST['collection'] );
```

**Always use `$wpdb->prepare()`** — never string-concatenate SQL:
```php
$results = $wpdb->get_results( $wpdb->prepare( 'SELECT * FROM %i WHERE id = %d', $table, $id ) );
```

**Nonce + capability on every AJAX write:**
```php
check_ajax_referer( 'skyyrose_action', 'nonce' );
if ( ! current_user_can( 'edit_posts' ) ) {
    wp_send_json_error( [ 'message' => 'Unauthorized' ] );
    return;
}
```

**Prefix everything with `skyyrose_`** (no leading underscore — WPCS violation):
- Functions: `skyyrose_my_function()` ✓ | `_skyyrose_my_function()` ✗
- Hooks: `skyyrose_my_action` ✓
- Options: `skyyrose_my_option` ✓

**Never call `wc_get_products()`** in templates — use `skyyrose_get_collection_products()` from `product-catalog.php`.

**Never reference retired SKUs**: `lh-001`, `br-d01`–`br-d04`, `sg-d01`–`sg-d04`, `sg-004`, `sg-008`, `sg-010`.

**Immediate fix mandate**: If you discover a safeguard violation in existing code while working nearby, fix it in the same edit — do not leave it in place.

---

## PHP Hook Registration Pattern

```php
add_action( 'wp_head', 'skyyrose_my_schema', 1 ); // Priority 1 for SEO output

function skyyrose_my_schema(): void {
    if ( ! is_singular( 'product' ) ) {
        return;
    }
    ?>
    <script type="application/ld+json">
    <?php echo wp_json_encode( skyyrose_build_schema_array(), JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE ); ?>
    </script>
    <?php
}
```

## JSON-LD Output Pattern

```php
function skyyrose_collection_schema( string $collection_slug ): void {
    $products = skyyrose_get_collection_products( $collection_slug );
    if ( empty( $products ) ) {
        return;
    }
    $items = [];
    $i     = 1;
    foreach ( $products as $p ) {
        $items[] = [
            '@type'    => 'ListItem',
            'position' => $i++,
            'name'     => $p['name'],
            'url'      => skyyrose_product_url( $p['sku'] ),
        ];
    }
    $schema = [
        '@context'        => 'https://schema.org',
        '@type'           => 'ItemList',
        'itemListElement' => $items,
    ];
    echo '<script type="application/ld+json">'
        . wp_json_encode( $schema, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE )
        . "</script>\n";
}
```

---

## Mandatory Quality Workflow

After every change to any `inc/` file, run ALL three steps in order. Do not skip any.

### 1. PHP Lint
```bash
cd wordpress-theme/skyyrose-flagship
~/.local/bin/composer exec phpcs -- --standard=.phpcs.xml -s inc/
# Zero errors required before proceeding.
# Auto-fix available (safe for formatting issues):
~/.local/bin/composer exec phpcbf -- --standard=.phpcs.xml inc/
```

### 2. /simplify
Invoke the `code-simplifier` agent on the modified file. Verify no logic was changed — only clarity improved.

### 3. /verification-loop
```bash
# Verify theme loads — no PHP fatal errors or warnings
curl -s -o /dev/null -w "%{http_code}" https://skyyrose.co/
# Must return 200. If not: diagnose root cause, fix, re-run lint, re-verify before any deploy.

# If SEO functions were modified:
curl -s https://skyyrose.co/ | grep -c 'application/ld+json'
# Must be >= 1
```

---

## Do NOT

- Use wp-cli commands — WordPress.com hosting has no shell access
- Call `wc_get_products()` — always use catalog helpers from `product-catalog.php`
- Hardcode any product name, price, or SKU array
- Use `echo` without an escape function
- Register SEO output hooks at priority 10 — use priority 1 so they fire early
- Create functions with `_skyyrose_` prefix (leading underscore violates WPCS)
- Deploy without passing lint:php
- Omit `return;` early-exit guards in conditional functions
