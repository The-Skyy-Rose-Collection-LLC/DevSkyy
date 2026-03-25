<?php
/**
 * Plugin Name: SkyyRose 3D Experience
 * Plugin URI: https://skyyrose.com/3d-experience
 * Description: Immersive 3D product experiences for SkyyRose collections with Elementor integration
 * Version: 2.0.0
 * Author: SkyyRose LLC
 * Author URI: https://skyyrose.com
 * License: GPL v2 or later
 * License URI: https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain: skyyrose-3d
 * Domain Path: /languages
 * Requires at least: 6.0
 * Requires PHP: 8.0
 *
 * Elementor tested up to: 3.18
 * Elementor Pro tested up to: 3.18
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

// Plugin constants
define('SKYYROSE_3D_VERSION', '2.0.0');
define('SKYYROSE_3D_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('SKYYROSE_3D_PLUGIN_URL', plugin_dir_url(__FILE__));
define('SKYYROSE_3D_API_BASE', get_option('skyyrose_api_url', 'https://api.skyyrose.com/api/v1'));

/**
 * Main plugin class
 */
final class SkyyRose_3D_Experience {

    /**
     * Singleton instance
     */
    private static ?SkyyRose_3D_Experience $instance = null;

    /**
     * Available collections
     */
    public const COLLECTIONS = [
        'black_rose' => 'BLACK ROSE Collection',
        'signature' => 'Signature Collection',
        'love_hurts' => 'Love Hurts Collection',
        'showroom' => 'Virtual Showroom',
        'runway' => 'Fashion Runway',
    ];

    /**
     * Get singleton instance
     */
    public static function instance(): SkyyRose_3D_Experience {
        if (is_null(self::$instance)) {
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
     * Initialize hooks
     */
    private function init_hooks(): void {
        // Activation/Deactivation
        register_activation_hook(__FILE__, [$this, 'activate']);
        register_deactivation_hook(__FILE__, [$this, 'deactivate']);

        // Init
        add_action('init', [$this, 'init']);
        add_action('wp_enqueue_scripts', [$this, 'enqueue_scripts']);
        add_action('admin_menu', [$this, 'admin_menu']);
        add_action('admin_init', [$this, 'register_settings']);

        // Shortcodes
        add_shortcode('skyyrose_3d', [$this, 'render_shortcode']);
        add_shortcode('skyyrose_spinning_logo', [$this, 'render_spinning_logo_shortcode']);

        // Inline styles for spinning logo (no external CSS dependency)
        add_action('wp_head', [$this, 'output_spinning_logo_styles'], 5);

        // REST API
        add_action('rest_api_init', [$this, 'register_rest_routes']);

        // Elementor integration
        add_action('elementor/widgets/register', [$this, 'register_elementor_widgets']);
        add_action('elementor/elements/categories_registered', [$this, 'register_elementor_category']);
    }

    /**
     * Plugin activation
     */
    public function activate(): void {
        // Create required tables if needed
        $this->create_analytics_table();

        // Set default options
        add_option('skyyrose_3d_version', SKYYROSE_3D_VERSION);
        add_option('skyyrose_api_url', 'https://api.skyyrose.com/api/v1');
        add_option('skyyrose_enable_analytics', true);

        // Flush rewrite rules
        flush_rewrite_rules();
    }

    /**
     * Plugin deactivation
     */
    public function deactivate(): void {
        flush_rewrite_rules();
    }

    /**
     * Initialize plugin
     */
    public function init(): void {
        load_plugin_textdomain('skyyrose-3d', false, dirname(plugin_basename(__FILE__)) . '/languages');
    }

    /**
     * Enqueue frontend scripts
     */
    public function enqueue_scripts(): void {
        // Only enqueue when needed
        if (!$this->should_enqueue_scripts()) {
            return;
        }

        // Three.js
        wp_enqueue_script(
            'three-js',
            'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.min.js',
            [],
            '0.160.0',
            true
        );

        // Three.js addons (OrbitControls, GLTFLoader, DRACOLoader)
        wp_enqueue_script(
            'three-js-addons',
            'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/Addons.js',
            ['three-js'],
            '0.160.0',
            true
        );

        // SkyyRose 3D Experience bundle
        $js_file = defined('WP_DEBUG') && WP_DEBUG
            ? 'assets/js/skyyrose-3d-experiences.js'
            : 'assets/js/skyyrose-3d-experiences.js';

        wp_enqueue_script(
            'skyyrose-3d',
            SKYYROSE_3D_PLUGIN_URL . $js_file,
            ['three-js', 'three-js-addons'],
            SKYYROSE_3D_VERSION,
            true
        );

        // Localize script
        wp_localize_script('skyyrose-3d', 'SkyyRose3DConfig', [
            'apiBase' => SKYYROSE_3D_API_BASE,
            'nonce' => wp_create_nonce('skyyrose_3d_nonce'),
            'collections' => self::COLLECTIONS,
            'enableAnalytics' => get_option('skyyrose_enable_analytics', true),
        ]);

        // Styles
        wp_enqueue_style(
            'skyyrose-3d',
            SKYYROSE_3D_PLUGIN_URL . 'assets/css/skyyrose-3d.css',
            [],
            SKYYROSE_3D_VERSION
        );
    }

    /**
     * Check if scripts should be enqueued
     */
    private function should_enqueue_scripts(): bool {
        global $post;

        if (!$post) {
            return false;
        }

        // Check for shortcode
        if (has_shortcode($post->post_content, 'skyyrose_3d')) {
            return true;
        }

        // Check for Elementor widget
        if (class_exists('\Elementor\Plugin')) {
            $document = \Elementor\Plugin::$instance->documents->get($post->ID);
            if ($document && $document->is_built_with_elementor()) {
                return true;
            }
        }

        return false;
    }

    /**
     * Render shortcode
     */
    public function render_shortcode(array $atts): string {
        $atts = shortcode_atts([
            'collection' => 'black_rose',
            'width' => '100%',
            'height' => '600px',
            'fullscreen' => 'true',
            'products' => '',
            'class' => '',
        ], $atts, 'skyyrose_3d');

        // Validate collection
        if (!array_key_exists($atts['collection'], self::COLLECTIONS)) {
            return '<p class="skyyrose-3d-error">' .
                   esc_html__('Invalid collection specified.', 'skyyrose-3d') .
                   '</p>';
        }

        $container_id = 'skyyrose-3d-' . wp_generate_uuid4();

        $products = !empty($atts['products']) ? explode(',', $atts['products']) : [];

        $config = wp_json_encode([
            'collection' => sanitize_key($atts['collection']),
            'products' => array_map('trim', $products),
            'enableFullscreen' => filter_var($atts['fullscreen'], FILTER_VALIDATE_BOOLEAN),
        ]);

        $classes = 'skyyrose-3d-container';
        if (!empty($atts['class'])) {
            $classes .= ' ' . esc_attr($atts['class']);
        }

        ob_start();
        ?>
        <div
            id="<?php echo esc_attr($container_id); ?>"
            class="<?php echo esc_attr($classes); ?>"
            style="width: <?php echo esc_attr($atts['width']); ?>; height: <?php echo esc_attr($atts['height']); ?>;"
            data-skyyrose-3d="<?php echo esc_attr($config); ?>"
        >
            <div class="skyyrose-3d-loader">
                <div class="skyyrose-3d-spinner"></div>
                <p><?php esc_html_e('Loading 3D Experience...', 'skyyrose-3d'); ?></p>
            </div>
        </div>
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                if (typeof SkyyRose3D !== 'undefined') {
                    SkyyRose3D.init('#<?php echo esc_js($container_id); ?>');
                }
            });
        </script>
        <?php
        return ob_get_clean();
    }

    /**
     * Admin menu
     */
    public function admin_menu(): void {
        add_options_page(
            __('SkyyRose 3D Settings', 'skyyrose-3d'),
            __('SkyyRose 3D', 'skyyrose-3d'),
            'manage_options',
            'skyyrose-3d-settings',
            [$this, 'render_settings_page']
        );
    }

    /**
     * Register settings
     */
    public function register_settings(): void {
        register_setting('skyyrose_3d_settings', 'skyyrose_api_url', [
            'type' => 'string',
            'sanitize_callback' => 'esc_url_raw',
            'default' => 'https://api.skyyrose.com/api/v1',
        ]);

        register_setting('skyyrose_3d_settings', 'skyyrose_enable_analytics', [
            'type' => 'boolean',
            'sanitize_callback' => 'rest_sanitize_boolean',
            'default' => true,
        ]);

        register_setting('skyyrose_3d_settings', 'skyyrose_default_collection', [
            'type' => 'string',
            'sanitize_callback' => 'sanitize_key',
            'default' => 'black_rose',
        ]);
    }

    /**
     * Render settings page
     */
    public function render_settings_page(): void {
        if (!current_user_can('manage_options')) {
            return;
        }
        ?>
        <div class="wrap">
            <h1><?php echo esc_html(get_admin_page_title()); ?></h1>

            <form action="options.php" method="post">
                <?php
                settings_fields('skyyrose_3d_settings');
                ?>

                <table class="form-table">
                    <tr>
                        <th scope="row">
                            <label for="skyyrose_api_url">
                                <?php esc_html_e('API URL', 'skyyrose-3d'); ?>
                            </label>
                        </th>
                        <td>
                            <input
                                type="url"
                                id="skyyrose_api_url"
                                name="skyyrose_api_url"
                                value="<?php echo esc_attr(get_option('skyyrose_api_url')); ?>"
                                class="regular-text"
                            />
                            <p class="description">
                                <?php esc_html_e('DevSkyy API endpoint for 3D experiences.', 'skyyrose-3d'); ?>
                            </p>
                        </td>
                    </tr>

                    <tr>
                        <th scope="row">
                            <?php esc_html_e('Enable Analytics', 'skyyrose-3d'); ?>
                        </th>
                        <td>
                            <label>
                                <input
                                    type="checkbox"
                                    name="skyyrose_enable_analytics"
                                    value="1"
                                    <?php checked(get_option('skyyrose_enable_analytics', true)); ?>
                                />
                                <?php esc_html_e('Track 3D experience interactions', 'skyyrose-3d'); ?>
                            </label>
                        </td>
                    </tr>

                    <tr>
                        <th scope="row">
                            <label for="skyyrose_default_collection">
                                <?php esc_html_e('Default Collection', 'skyyrose-3d'); ?>
                            </label>
                        </th>
                        <td>
                            <select
                                id="skyyrose_default_collection"
                                name="skyyrose_default_collection"
                            >
                                <?php foreach (self::COLLECTIONS as $key => $name): ?>
                                    <option
                                        value="<?php echo esc_attr($key); ?>"
                                        <?php selected(get_option('skyyrose_default_collection'), $key); ?>
                                    >
                                        <?php echo esc_html($name); ?>
                                    </option>
                                <?php endforeach; ?>
                            </select>
                        </td>
                    </tr>
                </table>

                <?php submit_button(); ?>
            </form>

            <hr>

            <h2><?php esc_html_e('Shortcode Usage', 'skyyrose-3d'); ?></h2>
            <p><?php esc_html_e('Use the following shortcode to embed 3D experiences:', 'skyyrose-3d'); ?></p>
            <code>[skyyrose_3d collection="black_rose" height="600px" fullscreen="true"]</code>

            <h3><?php esc_html_e('Available Collections', 'skyyrose-3d'); ?></h3>
            <ul>
                <?php foreach (self::COLLECTIONS as $key => $name): ?>
                    <li><code><?php echo esc_html($key); ?></code> - <?php echo esc_html($name); ?></li>
                <?php endforeach; ?>
            </ul>
        </div>
        <?php
    }

    /**
     * Register REST API routes
     */
    public function register_rest_routes(): void {
        register_rest_route('skyyrose-3d/v1', '/experiences', [
            'methods' => 'GET',
            'callback' => [$this, 'api_get_experiences'],
            'permission_callback' => '__return_true',
        ]);

        register_rest_route('skyyrose-3d/v1', '/analytics', [
            'methods' => 'POST',
            'callback' => [$this, 'api_track_analytics'],
            'permission_callback' => [$this, 'verify_nonce'],
        ]);
    }

    /**
     * API: Get experiences
     */
    public function api_get_experiences(\WP_REST_Request $request): \WP_REST_Response {
        $response = wp_remote_get(SKYYROSE_3D_API_BASE . '/elementor-3d/experiences');

        if (is_wp_error($response)) {
            return new \WP_REST_Response(['error' => 'Failed to fetch experiences'], 500);
        }

        $body = wp_remote_retrieve_body($response);
        return new \WP_REST_Response(json_decode($body, true), 200);
    }

    /**
     * API: Track analytics
     */
    public function api_track_analytics(\WP_REST_Request $request): \WP_REST_Response {
        $data = $request->get_json_params();

        // Forward to DevSkyy API
        $response = wp_remote_post(SKYYROSE_3D_API_BASE . '/elementor-3d/analytics', [
            'headers' => ['Content-Type' => 'application/json'],
            'body' => wp_json_encode($data),
        ]);

        if (is_wp_error($response)) {
            return new \WP_REST_Response(['error' => 'Failed to track analytics'], 500);
        }

        return new \WP_REST_Response(['success' => true], 200);
    }

    /**
     * Verify nonce for REST requests
     */
    public function verify_nonce(\WP_REST_Request $request): bool {
        $nonce = $request->get_header('X-WP-Nonce');
        return wp_verify_nonce($nonce, 'wp_rest');
    }

    /**
     * Register Elementor category
     */
    public function register_elementor_category($elements_manager): void {
        $elements_manager->add_category('skyyrose', [
            'title' => __('SkyyRose', 'skyyrose-3d'),
            'icon' => 'fa fa-cube',
        ]);
    }

    /**
     * Register Elementor widgets
     */
    public function register_elementor_widgets($widgets_manager): void {
        require_once SKYYROSE_3D_PLUGIN_DIR . 'includes/elementor/class-skyyrose-3d-widget.php';
        $widgets_manager->register(new \SkyyRose_3D_Elementor_Widget());
    }

    /**
     * Create analytics table
     */
    private function create_analytics_table(): void {
        global $wpdb;

        $table_name = $wpdb->prefix . 'skyyrose_3d_analytics';
        $charset_collate = $wpdb->get_charset_collate();

        $sql = "CREATE TABLE IF NOT EXISTS $table_name (
            id bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT,
            event_type varchar(50) NOT NULL,
            collection varchar(50) NOT NULL,
            session_id varchar(64) NOT NULL,
            product_id varchar(64) DEFAULT NULL,
            metadata longtext DEFAULT NULL,
            created_at datetime DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY event_type (event_type),
            KEY collection (collection),
            KEY session_id (session_id)
        ) $charset_collate;";

        require_once ABSPATH . 'wp-admin/includes/upgrade.php';
        dbDelta($sql);
    }

    /**
     * Output spinning logo styles inline (no external CSS file dependency)
     */
    public function output_spinning_logo_styles(): void {
        ?>
        <style id="skyyrose-spinning-logo-css">
        /* SkyyRose Spinning Logo - Inline CSS v2.0 */
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@400;500;600&display=swap');

        :root {
            --sr-rose-gold: #B76E79;
            --sr-gold: #D4AF37;
            --sr-silver: #C0C0C0;
            --sr-deep-rose: #D4A5A5;
            --sr-obsidian: #0D0D0D;
            --sr-ivory: #FAFAFA;
        }

        /* Logo Container */
        .skyyrose-logo {
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            text-decoration: none !important;
        }

        .skyyrose-logo__spinner {
            width: 60px;
            height: 60px;
            animation: sr-spin 8s linear infinite, sr-glow-pulse 3s ease-in-out infinite;
            transition: filter 0.5s cubic-bezier(0.16, 1, 0.3, 1), transform 0.5s cubic-bezier(0.16, 1, 0.3, 1);
            filter: drop-shadow(0 0 15px rgba(212, 175, 55, 0.3)) drop-shadow(0 0 30px rgba(212, 175, 55, 0.2));
        }

        .skyyrose-logo:hover .skyyrose-logo__spinner {
            animation-play-state: paused, paused;
            transform: scale(1.1);
            filter: drop-shadow(0 0 20px rgba(212, 175, 55, 0.5)) drop-shadow(0 0 40px rgba(212, 175, 55, 0.3)) drop-shadow(0 0 60px rgba(212, 175, 55, 0.2));
        }

        @keyframes sr-spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        @keyframes sr-glow-pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.85; }
        }

        /* Color Variants */
        .skyyrose-logo--gold .skyyrose-logo__spinner { filter: drop-shadow(0 0 15px rgba(212, 175, 55, 0.3)) drop-shadow(0 0 30px rgba(212, 175, 55, 0.2)); }
        .skyyrose-logo--gold .skyyrose-logo__spinner path, .skyyrose-logo--gold .skyyrose-logo__spinner circle { fill: #D4AF37; }

        .skyyrose-logo--silver .skyyrose-logo__spinner { filter: drop-shadow(0 0 15px rgba(192, 192, 192, 0.3)) drop-shadow(0 0 30px rgba(192, 192, 192, 0.2)); }
        .skyyrose-logo--silver .skyyrose-logo__spinner path, .skyyrose-logo--silver .skyyrose-logo__spinner circle { fill: #C0C0C0; }
        .skyyrose-logo--silver:hover .skyyrose-logo__spinner { filter: drop-shadow(0 0 20px rgba(192, 192, 192, 0.5)) drop-shadow(0 0 40px rgba(192, 192, 192, 0.3)); }

        .skyyrose-logo--rose-gold .skyyrose-logo__spinner { filter: drop-shadow(0 0 15px rgba(183, 110, 121, 0.3)) drop-shadow(0 0 30px rgba(183, 110, 121, 0.2)); }
        .skyyrose-logo--rose-gold .skyyrose-logo__spinner path, .skyyrose-logo--rose-gold .skyyrose-logo__spinner circle { fill: #B76E79; }
        .skyyrose-logo--rose-gold:hover .skyyrose-logo__spinner { filter: drop-shadow(0 0 20px rgba(183, 110, 121, 0.5)) drop-shadow(0 0 40px rgba(183, 110, 121, 0.3)); }

        .skyyrose-logo--deep-rose .skyyrose-logo__spinner { filter: drop-shadow(0 0 15px rgba(212, 165, 165, 0.3)) drop-shadow(0 0 30px rgba(212, 165, 165, 0.2)); }
        .skyyrose-logo--deep-rose .skyyrose-logo__spinner path, .skyyrose-logo--deep-rose .skyyrose-logo__spinner circle { fill: #D4A5A5; }
        .skyyrose-logo--deep-rose:hover .skyyrose-logo__spinner { filter: drop-shadow(0 0 20px rgba(212, 165, 165, 0.5)) drop-shadow(0 0 40px rgba(212, 165, 165, 0.3)); }

        .skyyrose-logo--black .skyyrose-logo__spinner { filter: drop-shadow(0 0 10px rgba(0, 0, 0, 0.2)) drop-shadow(0 0 20px rgba(0, 0, 0, 0.1)); }
        .skyyrose-logo--black .skyyrose-logo__spinner path, .skyyrose-logo--black .skyyrose-logo__spinner circle { fill: #0D0D0D; }

        /* Mobile */
        @media (max-width: 768px) {
            .skyyrose-logo__spinner { width: 48px; height: 48px; }
        }

        /* Luxury Typography */
        h1, h2, h3, h4, h5, h6, .elementor-heading-title {
            font-family: 'Playfair Display', Georgia, serif !important;
            font-weight: 600;
            line-height: 1.2;
        }

        body, p, .elementor-widget-text-editor {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Luxury Buttons */
        .woocommerce .button,
        .elementor-button,
        .wp-block-button__link {
            background: linear-gradient(135deg, #D4AF37 0%, #F5D76E 50%, #D4AF37 100%) !important;
            color: #0D0D0D !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            letter-spacing: 0.05em !important;
            border: none !important;
            border-radius: 0 !important;
            padding: 14px 32px !important;
            text-transform: uppercase !important;
            transition: all 0.3s ease !important;
        }

        .woocommerce .button:hover,
        .elementor-button:hover,
        .wp-block-button__link:hover {
            background: linear-gradient(135deg, #C9A962 0%, #E8CA5D 50%, #C9A962 100%) !important;
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(212, 175, 55, 0.3) !important;
        }

        /* Luxury Product Cards */
        .woocommerce ul.products li.product,
        .elementor-product {
            background: #0D0D0D;
            border: 1px solid rgba(212, 175, 55, 0.1);
            padding: 20px;
            transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .woocommerce ul.products li.product:hover {
            border-color: rgba(212, 175, 55, 0.3);
            transform: translateY(-8px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }

        .woocommerce ul.products li.product .woocommerce-loop-product__title {
            color: #FAFAFA !important;
            font-family: 'Playfair Display', serif !important;
            font-size: 1.1rem !important;
        }

        .woocommerce ul.products li.product .price {
            color: #D4AF37 !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 500 !important;
        }

        /* Collection-specific accents */
        body.collection-signature { --collection-accent: #B76E79; }
        body.collection-blackrose { --collection-accent: #C0C0C0; }
        body.collection-lovehurts { --collection-accent: #D4A5A5; }
        </style>
        <?php
    }

    /**
     * Render spinning logo shortcode
     */
    public function render_spinning_logo_shortcode(array $atts): string {
        $atts = shortcode_atts([
            'variant' => '',
            'size' => '60',
            'link' => 'true',
        ], $atts, 'skyyrose_spinning_logo');

        // Auto-detect variant based on page
        $variant = !empty($atts['variant']) ? sanitize_key($atts['variant']) : $this->detect_logo_variant();

        $allowed_variants = ['gold', 'silver', 'rose-gold', 'deep-rose', 'black'];
        if (!in_array($variant, $allowed_variants)) {
            $variant = 'gold';
        }

        $size = intval($atts['size']);
        $show_link = filter_var($atts['link'], FILTER_VALIDATE_BOOLEAN);

        // Inline SVG for the rose logo (no external file dependency)
        $svg = $this->get_rose_svg();

        $wrapper_start = $show_link
            ? '<a href="' . esc_url(home_url('/')) . '" class="skyyrose-logo skyyrose-logo--' . esc_attr($variant) . '" aria-label="SkyyRose Home">'
            : '<div class="skyyrose-logo skyyrose-logo--' . esc_attr($variant) . '">';

        $wrapper_end = $show_link ? '</a>' : '</div>';

        $style = $size !== 60 ? ' style="width:' . $size . 'px;height:' . $size . 'px;"' : '';

        return $wrapper_start . '<div class="skyyrose-logo__spinner"' . $style . '>' . $svg . '</div>' . $wrapper_end;
    }

    /**
     * Auto-detect logo variant based on current page
     */
    private function detect_logo_variant(): string {
        if (is_front_page()) {
            return 'gold';
        }

        if (is_page()) {
            $page_slug = get_post_field('post_name', get_the_ID());

            if (strpos($page_slug, 'black-rose') !== false || strpos($page_slug, 'blackrose') !== false) {
                return 'silver';
            }
            if (strpos($page_slug, 'love-hurts') !== false || strpos($page_slug, 'lovehurts') !== false) {
                return 'deep-rose';
            }
            if (strpos($page_slug, 'signature') !== false) {
                return 'rose-gold';
            }
        }

        // Check product category
        if (function_exists('is_product') && is_product()) {
            global $product;
            if ($product instanceof \WC_Product) {
                $categories = wp_get_post_terms($product->get_id(), 'product_cat', ['fields' => 'slugs']);
                if (in_array('black-rose', $categories)) return 'silver';
                if (in_array('love-hurts', $categories)) return 'deep-rose';
                if (in_array('signature', $categories)) return 'rose-gold';
            }
        }

        return 'gold';
    }

    /**
     * Get inline SVG for rose logo
     */
    private function get_rose_svg(): string {
        return '<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="roseGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:currentColor;stop-opacity:0.8"/>
                    <stop offset="100%" style="stop-color:currentColor;stop-opacity:1"/>
                </linearGradient>
            </defs>
            <!-- Rose Petals -->
            <g fill="currentColor" opacity="0.95">
                <!-- Center -->
                <circle cx="50" cy="50" r="8"/>
                <!-- Inner petals -->
                <ellipse cx="50" cy="35" rx="12" ry="18" transform="rotate(0 50 50)"/>
                <ellipse cx="50" cy="35" rx="12" ry="18" transform="rotate(72 50 50)"/>
                <ellipse cx="50" cy="35" rx="12" ry="18" transform="rotate(144 50 50)"/>
                <ellipse cx="50" cy="35" rx="12" ry="18" transform="rotate(216 50 50)"/>
                <ellipse cx="50" cy="35" rx="12" ry="18" transform="rotate(288 50 50)"/>
                <!-- Outer petals -->
                <ellipse cx="50" cy="25" rx="10" ry="22" transform="rotate(36 50 50)" opacity="0.7"/>
                <ellipse cx="50" cy="25" rx="10" ry="22" transform="rotate(108 50 50)" opacity="0.7"/>
                <ellipse cx="50" cy="25" rx="10" ry="22" transform="rotate(180 50 50)" opacity="0.7"/>
                <ellipse cx="50" cy="25" rx="10" ry="22" transform="rotate(252 50 50)" opacity="0.7"/>
                <ellipse cx="50" cy="25" rx="10" ry="22" transform="rotate(324 50 50)" opacity="0.7"/>
            </g>
            <!-- Stem hint -->
            <path d="M50 75 Q48 85 50 95" stroke="currentColor" stroke-width="2" fill="none" opacity="0.5"/>
        </svg>';
    }
}

/**
 * Initialize plugin
 */
function skyyrose_3d_experience(): SkyyRose_3D_Experience {
    return SkyyRose_3D_Experience::instance();
}

// Initialize
skyyrose_3d_experience();
