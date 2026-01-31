# WordPress.com API & OAuth - Rate Limits Guide

**Issue**: "Too many API calls" error when using OAuth

---

## WordPress.com API Rate Limits

WordPress.com enforces strict rate limits:

| Tier | Requests per Hour | Requests per Day |
|------|-------------------|------------------|
| **Free** | 60 | 1,000 |
| **Personal** | 120 | 2,000 |
| **Premium** | 600 | 10,000 |
| **Business** | 3,600 | 60,000 |

**Note**: Limits are per OAuth application, not per user.

---

## Theme Features Added

### 1. API Response Caching ✅

```php
// Cache API responses for 1 hour (default)
function skyyrose_cache_api_response($endpoint, $callback, $expiration = HOUR_IN_SECONDS) {
    $cache_key = 'api_cache_' . md5($endpoint);
    $cached = get_transient($cache_key);

    if ($cached !== false) {
        return $cached; // Return cached response
    }

    $response = call_user_func($callback);
    set_transient($cache_key, $response, $expiration);

    return $response;
}
```

**Usage**:
```php
// Instead of direct API call:
$products = wp_remote_get('https://yoursite.com/wp-json/wc/v3/products');

// Use cached version:
$products = skyyrose_cache_api_response(
    '/wc/v3/products',
    function() {
        return wp_remote_get('https://yoursite.com/wp-json/wc/v3/products');
    },
    HOUR_IN_SECONDS
);
```

### 2. Automatic Retry with Exponential Backoff ✅

```php
// Handles 429 (rate limit) responses automatically
$response = skyyrose_api_request_with_retry(
    'https://yoursite.com/wp-json/wc/v3/products',
    ['headers' => ['Authorization' => 'Bearer ' . $token]],
    3 // max retries
);
```

**Features**:
- Retries on 429 (rate limit exceeded)
- Exponential backoff (2s, 4s, 8s)
- Respects `Retry-After` header
- Returns error after max retries

### 3. OAuth Authentication Allowed ✅

REST API now allows:
- OAuth tokens (`HTTP_AUTHORIZATION` header)
- Basic authentication (`PHP_AUTH_USER`)
- WooCommerce API keys
- Logged-in users

---

## Solutions for "Too Many API Calls"

### Solution 1: Increase Cache Duration

Edit `functions.php` to cache responses longer:

```php
// Cache for 6 hours instead of 1 hour
$products = skyyrose_cache_api_response(
    '/wc/v3/products',
    function() {
        return wp_remote_get('https://yoursite.com/wp-json/wc/v3/products');
    },
    6 * HOUR_IN_SECONDS // 6 hours
);
```

### Solution 2: Batch API Requests

Instead of multiple single-product requests:

```php
// BAD: 30 API calls for 30 products
foreach ($product_ids as $id) {
    $product = wp_remote_get("/wc/v3/products/$id");
}

// GOOD: 1 API call for all products
$products = wp_remote_get("/wc/v3/products?include=" . implode(',', $product_ids));
```

### Solution 3: Use WordPress.com Index Pattern

For WordPress.com sites, use `index.php?rest_route=` instead of `/wp-json/`:

```php
// WordPress.com sites MUST use this format
$base_url = 'https://yoursite.wordpress.com/index.php?rest_route=';

// NOT this format (will fail on WordPress.com)
$base_url = 'https://yoursite.wordpress.com/wp-json/';
```

**Example**:
```php
// Correct for WordPress.com
$products = wp_remote_get('https://yoursite.wordpress.com/index.php?rest_route=/wc/v3/products');

// Correct for self-hosted WordPress
$products = wp_remote_get('https://yoursite.com/wp-json/wc/v3/products');
```

### Solution 4: Reduce Sync Frequency

If syncing products from external source:

```php
// Instead of syncing every page load
if (get_transient('last_product_sync')) {
    return; // Skip sync
}

// Sync products
sync_products();

// Set transient to prevent re-sync for 12 hours
set_transient('last_product_sync', true, 12 * HOUR_IN_SECONDS);
```

### Solution 5: Use Webhooks Instead of Polling

Set up WooCommerce webhooks to push updates instead of polling API:

1. **WooCommerce → Settings → Advanced → Webhooks**
2. **Add Webhook**:
   - Name: "Product Updated"
   - Status: Active
   - Topic: `product.updated`
   - Delivery URL: `https://yoursite.com/wp-json/skyyrose/v1/webhook`

Then handle webhook in theme:

```php
register_rest_route('skyyrose/v1', '/webhook', [
    'methods' => 'POST',
    'callback' => function($request) {
        $data = $request->get_json_params();
        // Update local cache with webhook data
        update_product_cache($data);
        return ['success' => true];
    },
    'permission_callback' => function($request) {
        // Verify webhook signature
        return verify_webhook_signature($request);
    }
]);
```

---

## OAuth Best Practices

### 1. Store Tokens Securely

```php
// NEVER hardcode tokens
$token = 'abc123'; // ❌ BAD

// Store in wp_options with encryption
update_option('oauth_access_token', encrypt_token($token)); // ✅ GOOD

// Or use WordPress Transients API
set_transient('oauth_access_token', $token, DAY_IN_SECONDS);
```

### 2. Refresh Tokens Before Expiry

```php
function refresh_oauth_token() {
    $refresh_token = get_option('oauth_refresh_token');

    $response = wp_remote_post('https://public-api.wordpress.com/oauth2/token', [
        'body' => [
            'client_id' => OAUTH_CLIENT_ID,
            'client_secret' => OAUTH_CLIENT_SECRET,
            'grant_type' => 'refresh_token',
            'refresh_token' => $refresh_token,
        ]
    ]);

    if (!is_wp_error($response)) {
        $body = json_decode(wp_remote_retrieve_body($response), true);
        update_option('oauth_access_token', $body['access_token']);
        update_option('oauth_refresh_token', $body['refresh_token']);
    }
}

// Refresh token before it expires (every 6 hours)
if (!wp_next_scheduled('refresh_oauth_token_cron')) {
    wp_schedule_event(time(), 'sixhourly', 'refresh_oauth_token_cron');
}
add_action('refresh_oauth_token_cron', 'refresh_oauth_token');
```

### 3. Handle Rate Limit Errors Gracefully

```php
$response = wp_remote_get($url, ['headers' => ['Authorization' => "Bearer $token"]]);

if (wp_remote_retrieve_response_code($response) === 429) {
    // Rate limit hit
    $retry_after = wp_remote_retrieve_header($response, 'retry-after');

    // Queue request for later
    wp_schedule_single_event(time() + $retry_after, 'retry_api_request', [$url]);

    // Show user-friendly message
    return new WP_Error('rate_limit', 'Too many requests. Please try again in ' . $retry_after . ' seconds.');
}
```

---

## Debugging API Calls

### Enable Debug Logging

Add to `wp-config.php`:

```php
define('WP_DEBUG', true);
define('WP_DEBUG_LOG', true);
define('WP_DEBUG_DISPLAY', false);
```

All API requests will be logged to `/wp-content/debug.log`:

```
[2026-01-30 22:30:15] API Request: https://yoursite.com/wp-json/wc/v3/products | Response Code: 200
[2026-01-30 22:30:16] API Request: https://yoursite.com/wp-json/wc/v3/products/123 | Response Code: 429
```

### Monitor API Usage

```php
// Track API calls in database
function log_api_call($endpoint) {
    global $wpdb;
    $wpdb->insert($wpdb->prefix . 'api_logs', [
        'endpoint' => $endpoint,
        'timestamp' => current_time('mysql'),
        'ip_address' => $_SERVER['REMOTE_ADDR'],
    ]);
}

// Get API call count for last hour
function get_api_call_count() {
    global $wpdb;
    $one_hour_ago = date('Y-m-d H:i:s', strtotime('-1 hour'));

    return $wpdb->get_var($wpdb->prepare(
        "SELECT COUNT(*) FROM {$wpdb->prefix}api_logs WHERE timestamp > %s",
        $one_hour_ago
    ));
}

// Show warning if approaching limit
if (get_api_call_count() > 50) {
    // 50 out of 60 per hour (free tier)
    error_log('WARNING: Approaching API rate limit');
}
```

---

## WordPress.com vs Self-Hosted

| Feature | WordPress.com | Self-Hosted |
|---------|---------------|-------------|
| **REST API Endpoint** | `index.php?rest_route=` | `/wp-json/` |
| **Rate Limits** | 60/hour (free tier) | No limits |
| **OAuth Required** | Yes | Optional |
| **FTP Access** | No (Business+ only) | Yes |
| **Plugin Install** | Limited (Business+) | Unlimited |
| **Custom Code** | Limited | Unlimited |

---

## Quick Fixes

### Error: "Too many API calls"

```bash
# 1. Clear WordPress transient cache
wp transient delete --all

# 2. Increase cache duration
# Edit functions.php, change HOUR_IN_SECONDS to 6 * HOUR_IN_SECONDS

# 3. Check current API usage
wp eval 'echo get_transient("api_cache_" . md5("/wc/v3/products"));'
```

### Error: "REST API disabled"

The theme's security hardening may be blocking. To allow all authenticated requests:

```php
// Temporarily disable REST API restriction (in functions.php)
remove_filter('rest_authentication_errors', 'skyyrose_rest_api_protection');
```

### Error: "Invalid OAuth token"

```php
// Delete stored tokens and re-authenticate
delete_option('oauth_access_token');
delete_option('oauth_refresh_token');

// Clear all API cache
global $wpdb;
$wpdb->query("DELETE FROM {$wpdb->prefix}options WHERE option_name LIKE '_transient_api_cache_%'");
```

---

## Production Checklist

Before deploying to production:

- [ ] OAuth tokens stored securely (not in code)
- [ ] API caching enabled (1+ hour duration)
- [ ] Rate limit retry logic active
- [ ] Webhook delivery confirmed (if using webhooks)
- [ ] Debug logging disabled (`WP_DEBUG` = false)
- [ ] API call monitoring set up
- [ ] Fallback UI for rate limit errors
- [ ] Token refresh cron job scheduled

---

## Contact

**WordPress.com API Support**: https://developer.wordpress.com/docs/api/
**WooCommerce API Docs**: https://woocommerce.github.io/woocommerce-rest-api-docs/

**SkyyRose Support**: hello@skyyrose.co

---

**Last Updated**: 2026-01-30
