---
name: wp-sync
description: Sync and validate WordPress/WooCommerce headless CMS connection
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - WebFetch
argument-hint: "[check|sync|revalidate]"
---

# WordPress Sync Command

Sync and validate the WordPress/WooCommerce headless CMS connection and data.

## Actions

### Check Connection
```
/wp-sync check
```
Test WordPress and WooCommerce API connectivity.

### Full Sync
```
/wp-sync sync
```
Validate all endpoints and sync content availability.

### Revalidate Cache
```
/wp-sync revalidate
```
Trigger ISR revalidation for WordPress content.

## Execution Steps

### For `check`:
1. Test WordPress REST API:
   ```bash
   curl -s "${WORDPRESS_API_URL}/wp-json"
   ```
2. Test WooCommerce API:
   ```bash
   curl -s "${WOOCOMMERCE_API_URL}/wp-json/wc/v3/products?per_page=1&consumer_key=${WC_CONSUMER_KEY}&consumer_secret=${WC_CONSUMER_SECRET}"
   ```
3. Report connection status

### For `sync`:
1. Test all WordPress endpoints (posts, pages, media, categories)
2. Test all WooCommerce endpoints (products, categories, orders)
3. Verify data counts
4. Report sync status

### For `revalidate`:
1. Call revalidation API endpoint
2. Clear CDN cache if configured
3. Verify fresh data loads

## Endpoints Tested

**WordPress:**
- `/wp-json/wp/v2/posts`
- `/wp-json/wp/v2/pages`
- `/wp-json/wp/v2/media`
- `/wp-json/wp/v2/categories`
- `/wp-json/wp/v2/tags`

**WooCommerce:**
- `/wp-json/wc/v3/products`
- `/wp-json/wc/v3/products/categories`
- `/wp-json/wc/v3/system_status`

## Example Usage

```
/wp-sync check       # Quick connectivity check
/wp-sync sync        # Full sync validation
/wp-sync revalidate  # Clear cache and revalidate
```

## Error Handling

If connection fails:
1. Check environment variables are set
2. Verify WordPress site is accessible
3. Check API credentials are correct
4. Verify permalinks are configured
5. Check CORS settings

Use Context7 to find solutions for specific API errors.
