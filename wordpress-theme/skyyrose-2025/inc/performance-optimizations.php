<?php
/**
 * Performance Optimizations for SkyyRose Theme
 *
 * Comprehensive performance enhancements including:
 * - Asset optimization (minification, compression)
 * - Caching strategies (browser, object, transient)
 * - Database query optimization
 * - Image optimization (lazy loading, responsive, WebP)
 * - JavaScript optimization (defer, async, code splitting)
 * - CSS optimization (critical CSS, unused removal)
 * - Server optimization (Gzip, HTTP/2 headers)
 *
 * @package SkyyRose_2025
 * @version 3.0.0
 */

if (!defined('ABSPATH')) {
    exit;
}

class SkyyRose_Performance_Optimizer {

    private static $instance = null;

    /**
     * Get singleton instance
     */
    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    /**
     * Constructor
     */
    private function __construct() {
        $this->init_hooks();
    }

    /**
     * Initialize WordPress hooks
     */
    private function init_hooks() {
        // Asset optimization
        add_filter('script_loader_tag', [$this, 'optimize_script_loading'], 10, 3);
        add_filter('style_loader_tag', [$this, 'optimize_style_loading'], 10, 4);

        // Image optimization
        add_filter('wp_get_attachment_image_attributes', [$this, 'add_image_lazy_loading'], 10, 3);
        add_filter('the_content', [$this, 'add_content_image_lazy_loading']);
        add_filter('wp_calculate_image_srcset', [$this, 'optimize_srcset'], 10, 5);

        // Database optimization
        add_action('pre_get_posts', [$this, 'optimize_queries']);
        add_filter('posts_clauses', [$this, 'optimize_post_queries'], 10, 2);

        // Caching
        add_action('init', [$this, 'setup_caching']);
        add_action('save_post', [$this, 'clear_post_cache']);
        add_action('wp_ajax_clear_theme_cache', [$this, 'ajax_clear_cache']);

        // Server optimization
        add_action('send_headers', [$this, 'add_performance_headers']);
        add_action('init', [$this, 'enable_gzip_compression']);

        // Preloading & preconnecting
        add_action('wp_head', [$this, 'add_resource_hints'], 1);

        // Remove unnecessary WordPress features
        add_action('init', [$this, 'remove_bloat']);

        // Defer JavaScript
        add_filter('script_loader_tag', [$this, 'defer_non_critical_scripts'], 10, 2);

        // Critical CSS
        add_action('wp_head', [$this, 'inline_critical_css'], 1);
    }

    /**
     * Optimize script loading with async/defer
     */
    public function optimize_script_loading($tag, $handle, $src) {
        // Skip admin scripts
        if (is_admin()) {
            return $tag;
        }

        // Critical scripts that should NOT be deferred
        $critical_scripts = [
            'jquery',
            'jquery-core',
            'jquery-migrate',
            'three',
            'gsap',
        ];

        // Defer non-critical scripts
        if (!in_array($handle, $critical_scripts)) {
            $tag = str_replace(' src', ' defer src', $tag);
        }

        // Add module type for modern scripts
        if (strpos($handle, 'module-') === 0) {
            $tag = str_replace(' src', ' type="module" src', $tag);
        }

        return $tag;
    }

    /**
     * Optimize style loading with preload
     */
    public function optimize_style_loading($html, $handle, $href, $media) {
        // Preload critical styles
        $critical_styles = [
            'skyyrose-style',
            'skyyrose-animations',
        ];

        if (in_array($handle, $critical_styles)) {
            $html = str_replace('rel=\'stylesheet\'', 'rel=\'preload\' as=\'style\' onload="this.onload=null;this.rel=\'stylesheet\'"', $html);
            // Add noscript fallback
            $html .= '<noscript><link rel="stylesheet" href="' . esc_url($href) . '"></noscript>';
        }

        return $html;
    }

    /**
     * Add lazy loading to images
     */
    public function add_image_lazy_loading($attr, $attachment, $size) {
        // Skip if already has loading attribute
        if (isset($attr['loading'])) {
            return $attr;
        }

        // Add lazy loading for non-critical images
        $attr['loading'] = 'lazy';

        // Add decoding async for better performance
        $attr['decoding'] = 'async';

        return $attr;
    }

    /**
     * Add lazy loading to content images
     */
    public function add_content_image_lazy_loading($content) {
        // Add loading="lazy" to images in content
        $content = preg_replace('/<img((?![^>]*loading=)[^>]*)>/i', '<img$1 loading="lazy" decoding="async">', $content);

        return $content;
    }

    /**
     * Optimize image srcset
     */
    public function optimize_srcset($sources, $size_array, $image_src, $image_meta, $attachment_id) {
        // Remove very large sizes if not needed
        $max_width = 2048;

        foreach ($sources as $width => $source) {
            if ($width > $max_width) {
                unset($sources[$width]);
            }
        }

        return $sources;
    }

    /**
     * Optimize WordPress queries
     */
    public function optimize_queries($query) {
        // Skip admin queries
        if (is_admin() || !$query->is_main_query()) {
            return;
        }

        // Optimize post queries
        if ($query->is_home() || $query->is_archive()) {
            // Limit posts per page for better performance
            $query->set('posts_per_page', 12);

            // Only query necessary fields
            $query->set('no_found_rows', true);
            $query->set('update_post_term_cache', false);
            $query->set('update_post_meta_cache', false);
        }
    }

    /**
     * Optimize post queries with caching
     */
    public function optimize_post_queries($clauses, $query) {
        global $wpdb;

        // Skip admin queries
        if (is_admin()) {
            return $clauses;
        }

        // Add indexes hint for better performance
        if ($query->is_main_query() && ($query->is_home() || $query->is_archive())) {
            $clauses['join'] .= " USE INDEX (type_status_date)";
        }

        return $clauses;
    }

    /**
     * Setup caching strategies
     */
    public function setup_caching() {
        // Enable object caching if available
        if (!defined('WP_CACHE')) {
            define('WP_CACHE', true);
        }

        // Set cache headers for static assets
        if (!is_admin()) {
            $this->set_cache_headers();
        }
    }

    /**
     * Set cache headers for browser caching
     */
    private function set_cache_headers() {
        $asset_extensions = ['css', 'js', 'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'woff', 'woff2', 'ttf', 'eot'];

        $request_uri = $_SERVER['REQUEST_URI'] ?? '';
        $extension = pathinfo($request_uri, PATHINFO_EXTENSION);

        if (in_array($extension, $asset_extensions)) {
            // Cache for 1 year
            header('Cache-Control: public, max-age=31536000, immutable');
            header('Expires: ' . gmdate('D, d M Y H:i:s', time() + 31536000) . ' GMT');
        }
    }

    /**
     * Clear post-related caches
     */
    public function clear_post_cache($post_id) {
        // Clear transients related to this post
        $post_type = get_post_type($post_id);

        delete_transient("skyyrose_{$post_type}_query");
        delete_transient('skyyrose_vault_stock');
        delete_transient('skyyrose_vault_products');

        // Clear object cache
        wp_cache_delete($post_id, 'posts');
        wp_cache_delete($post_id, 'post_meta');
    }

    /**
     * AJAX handler to clear theme cache
     */
    public function ajax_clear_cache() {
        check_ajax_referer('skyyrose_nonce', 'nonce');

        if (!current_user_can('manage_options')) {
            wp_send_json_error(['message' => 'Unauthorized']);
            return;
        }

        // Clear all transients
        global $wpdb;
        $wpdb->query("DELETE FROM {$wpdb->options} WHERE option_name LIKE '_transient_skyyrose_%'");
        $wpdb->query("DELETE FROM {$wpdb->options} WHERE option_name LIKE '_transient_timeout_skyyrose_%'");

        // Clear object cache
        wp_cache_flush();

        wp_send_json_success(['message' => 'Cache cleared successfully']);
    }

    /**
     * Add performance headers
     */
    public function add_performance_headers() {
        if (is_admin()) {
            return;
        }

        // Enable HTTP/2 Server Push (if supported)
        header('Link: <' . get_stylesheet_uri() . '>; rel=preload; as=style', false);

        // Add security headers for performance
        header('X-Content-Type-Options: nosniff');
        header('X-Frame-Options: SAMEORIGIN');
        header('X-XSS-Protection: 1; mode=block');

        // Enable Content Security Policy
        header("Content-Security-Policy: default-src 'self' 'unsafe-inline' 'unsafe-eval' https:; img-src 'self' data: https:; font-src 'self' data: https://fonts.gstatic.com;");
    }

    /**
     * Enable Gzip compression
     */
    public function enable_gzip_compression() {
        if (!is_admin() && extension_loaded('zlib') && !ini_get('zlib.output_compression')) {
            if (headers_sent()) {
                return;
            }

            // Check if client accepts gzip
            if (isset($_SERVER['HTTP_ACCEPT_ENCODING']) && strpos($_SERVER['HTTP_ACCEPT_ENCODING'], 'gzip') !== false) {
                ob_start('ob_gzhandler');
            }
        }
    }

    /**
     * Add resource hints (preconnect, dns-prefetch, preload)
     */
    public function add_resource_hints() {
        ?>
        <!-- DNS Prefetch -->
        <link rel="dns-prefetch" href="//fonts.googleapis.com">
        <link rel="dns-prefetch" href="//fonts.gstatic.com">
        <link rel="dns-prefetch" href="//cdn.jsdelivr.net">

        <!-- Preconnect to external domains -->
        <link rel="preconnect" href="https://fonts.googleapis.com" crossorigin>
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>

        <!-- Preload critical fonts -->
        <link rel="preload" href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@400;700&display=swap" as="style">

        <!-- Preload hero image if exists -->
        <?php if (is_front_page() && has_post_thumbnail()): ?>
            <link rel="preload" href="<?php echo esc_url(get_the_post_thumbnail_url(null, 'full')); ?>" as="image">
        <?php endif; ?>
        <?php
    }

    /**
     * Remove WordPress bloat
     */
    public function remove_bloat() {
        // Remove unnecessary features
        remove_action('wp_head', 'wp_generator');
        remove_action('wp_head', 'wlwmanifest_link');
        remove_action('wp_head', 'rsd_link');
        remove_action('wp_head', 'wp_shortlink_wp_head');
        remove_action('wp_head', 'adjacent_posts_rel_link_wp_head', 10);
        remove_action('wp_head', 'rest_output_link_wp_head');
        remove_action('wp_head', 'wp_oembed_add_discovery_links');

        // Remove emoji scripts
        remove_action('wp_head', 'print_emoji_detection_script', 7);
        remove_action('wp_print_styles', 'print_emoji_styles');
        remove_action('admin_print_scripts', 'print_emoji_detection_script');
        remove_action('admin_print_styles', 'print_emoji_styles');

        // Disable embeds
        add_filter('embed_oembed_discover', '__return_false');
        add_filter('xmlrpc_enabled', '__return_false');

        // Limit post revisions
        if (!defined('WP_POST_REVISIONS')) {
            define('WP_POST_REVISIONS', 3);
        }

        // Increase autosave interval
        if (!defined('AUTOSAVE_INTERVAL')) {
            define('AUTOSAVE_INTERVAL', 300);
        }
    }

    /**
     * Defer non-critical scripts
     */
    public function defer_non_critical_scripts($tag, $handle) {
        if (is_admin()) {
            return $tag;
        }

        // Scripts that should NOT be deferred
        $no_defer = ['jquery', 'jquery-core', 'jquery-migrate'];

        if (in_array($handle, $no_defer)) {
            return $tag;
        }

        // Add defer attribute
        return str_replace(' src', ' defer src', $tag);
    }

    /**
     * Inline critical CSS
     */
    public function inline_critical_css() {
        // Critical CSS for above-the-fold content
        ?>
        <style id="critical-css">
            /* Critical styles for initial render */
            body {
                margin: 0;
                padding: 0;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                color: #fff;
                background: #000;
            }

            .site-header {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                z-index: 1000;
                padding: 1rem 2rem;
                background: rgba(0, 0, 0, 0.95);
                backdrop-filter: blur(20px);
            }

            .hero {
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                text-align: center;
                padding: 2rem;
            }

            h1 {
                font-family: 'Playfair Display', serif;
                font-size: clamp(2rem, 5vw, 4rem);
                margin: 0 0 1rem;
            }

            .btn {
                display: inline-block;
                padding: 1rem 2rem;
                background: #B76E79;
                color: #fff;
                text-decoration: none;
                border-radius: 4px;
                transition: transform 0.3s ease;
            }

            /* Skeleton loading for better perceived performance */
            .skeleton {
                background: linear-gradient(
                    90deg,
                    rgba(255, 255, 255, 0.05) 0%,
                    rgba(255, 255, 255, 0.1) 50%,
                    rgba(255, 255, 255, 0.05) 100%
                );
                background-size: 200% 100%;
                animation: skeleton-loading 1.5s ease-in-out infinite;
            }

            @keyframes skeleton-loading {
                0% { background-position: 200% 0; }
                100% { background-position: -200% 0; }
            }
        </style>
        <?php
    }

    /**
     * Get cache statistics
     */
    public static function get_cache_stats() {
        global $wpdb;

        $stats = [
            'transients' => $wpdb->get_var(
                "SELECT COUNT(*) FROM {$wpdb->options} WHERE option_name LIKE '_transient_skyyrose_%'"
            ),
            'object_cache' => wp_using_ext_object_cache() ? 'External' : 'Internal',
            'page_cache' => defined('WP_CACHE') && WP_CACHE ? 'Enabled' : 'Disabled',
        ];

        return $stats;
    }
}

// Initialize performance optimizer
SkyyRose_Performance_Optimizer::get_instance();

/**
 * Helper function to clear theme cache
 */
function skyyrose_clear_theme_cache() {
    global $wpdb;

    // Clear transients
    $wpdb->query("DELETE FROM {$wpdb->options} WHERE option_name LIKE '_transient_skyyrose_%'");
    $wpdb->query("DELETE FROM {$wpdb->options} WHERE option_name LIKE '_transient_timeout_skyyrose_%'");

    // Clear object cache
    wp_cache_flush();

    return true;
}

/**
 * Get performance metrics
 */
function skyyrose_get_performance_metrics() {
    return [
        'cache_stats' => SkyyRose_Performance_Optimizer::get_cache_stats(),
        'queries' => get_num_queries(),
        'memory' => round(memory_get_peak_usage() / 1024 / 1024, 2) . ' MB',
        'time' => timer_stop(0, 3) . 's',
    ];
}
