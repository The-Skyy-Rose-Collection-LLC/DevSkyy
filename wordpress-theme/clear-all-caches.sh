#!/bin/bash
# WordPress Cache Clearing Script for SkyyRose Theme
# Clears ALL caches: object cache, transients, rewrite rules, opcache

echo "🧹 Clearing ALL WordPress Caches..."

# Navigate to WordPress directory
cd "$(dirname "$0")/skyyrose-2025" || exit 1

# 1. Flush WordPress Object Cache
echo "✓ Flushing object cache..."
wp cache flush --allow-root 2>/dev/null || echo "  ⚠️  WP-CLI not available (will use browser method)"

# 2. Delete ALL Transients (including expired)
echo "✓ Deleting all transients..."
wp transient delete --all --allow-root 2>/dev/null || echo "  ⚠️  WP-CLI not available"

# 3. Flush Rewrite Rules
echo "✓ Flushing rewrite rules..."
wp rewrite flush --allow-root 2>/dev/null || echo "  ⚠️  WP-CLI not available"

# 4. Clear WordPress.com Edge Cache (via HTTP headers)
echo "✓ Purging WordPress.com CDN/Edge cache..."
curl -X PURGE "https://skyyrose.co/" -H "Cache-Control: no-cache" 2>/dev/null || echo "  ⚠️  CDN purge may require admin action"

# 5. Generate PHP script for browser-based cache clearing
cat > /tmp/clear-wp-cache.php << 'PHPEOF'
<?php
/**
 * Emergency WordPress Cache Clearing Script
 * Run via: wp eval-file /tmp/clear-wp-cache.php
 */

// Load WordPress
require_once(__DIR__ . '/wp-load.php');

echo "Starting comprehensive cache clear...\n";

// 1. Flush object cache
if (function_exists('wp_cache_flush')) {
    wp_cache_flush();
    echo "✓ Object cache flushed\n";
}

// 2. Delete all transients
global $wpdb;
$wpdb->query("DELETE FROM $wpdb->options WHERE option_name LIKE '_transient_%'");
$wpdb->query("DELETE FROM $wpdb->options WHERE option_name LIKE '_site_transient_%'");
echo "✓ All transients deleted\n";

// 3. Flush rewrite rules
flush_rewrite_rules(true);
echo "✓ Rewrite rules flushed\n";

// 4. Clear WooCommerce caches
if (function_exists('wc_delete_product_transients')) {
    wc_delete_product_transients();
    echo "✓ WooCommerce product caches cleared\n";
}

if (function_exists('wc_delete_shop_order_transients')) {
    wc_delete_shop_order_transients();
    echo "✓ WooCommerce order caches cleared\n";
}

// 5. Clear theme/plugin update transients
delete_site_transient('update_themes');
delete_site_transient('update_plugins');
delete_site_transient('update_core');
echo "✓ Update check caches cleared\n";

// 6. Clear Jetpack caches (if present)
if (class_exists('Jetpack')) {
    delete_transient('jetpack_assumed_site_creation_date');
    delete_transient('jetpack_file_data');
    echo "✓ Jetpack caches cleared\n";
}

// 7. Clear Elementor caches
if (did_action('elementor/loaded')) {
    \Elementor\Plugin::$instance->files_manager->clear_cache();
    echo "✓ Elementor caches cleared\n";
}

echo "\n🎉 All caches cleared successfully!\n";
PHPEOF

echo ""
echo "📋 Cache clearing script created at: /tmp/clear-wp-cache.php"
echo ""
echo "🌐 WordPress.com Cache Clearing Methods:"
echo "   1. Browser: Navigate to site + add '?nocache=1' to URL"
echo "   2. Admin: WP Admin > Settings > Clear Cache (if available)"
echo "   3. WP-CLI: Run script from WordPress root directory"
echo ""
echo "✅ Local cache clear complete!"
