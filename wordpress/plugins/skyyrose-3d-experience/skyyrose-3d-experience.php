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

        // Shortcode
        add_shortcode('skyyrose_3d', [$this, 'render_shortcode']);

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
}

/**
 * Initialize plugin
 */
function skyyrose_3d_experience(): SkyyRose_3D_Experience {
    return SkyyRose_3D_Experience::instance();
}

// Initialize
skyyrose_3d_experience();
