<?php
/**
 * Plugin Name: SkyyRose AR Quick Look
 * Plugin URI: https://skyyrose.com/plugins/ar-viewer
 * Description: iOS AR Quick Look integration for SkyyRose 3D product viewing with USDZ support
 * Version: 1.0.0
 * Author: SkyyRose
 * Author URI: https://skyyrose.com
 * License: GPL-2.0+
 * License URI: http://www.gnu.org/licenses/gpl-2.0.txt
 * Text Domain: skyyrose-ar
 * Domain Path: /languages
 * Requires at least: 5.8
 * Requires PHP: 7.4
 *
 * @package SkyyRose_AR
 */

// Exit if accessed directly
if (!defined('ABSPATH')) {
    exit;
}

// Define plugin constants
define('SKYYROSE_AR_VERSION', '1.0.0');
define('SKYYROSE_AR_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('SKYYROSE_AR_PLUGIN_URL', plugin_dir_url(__FILE__));
define('SKYYROSE_AR_PLUGIN_BASENAME', plugin_basename(__FILE__));

/**
 * Main SkyyRose AR Quick Look class
 */
class SkyyRose_AR_Quick_Look {

    /**
     * Instance of this class
     *
     * @var SkyyRose_AR_Quick_Look
     */
    private static $instance = null;

    /**
     * Get instance
     *
     * @return SkyyRose_AR_Quick_Look
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
        // Shortcode registration
        add_shortcode('skyyrose_ar_button', array($this, 'ar_button_shortcode'));

        // Asset enqueuing
        add_action('wp_enqueue_scripts', array($this, 'enqueue_assets'));

        // Admin menu and settings
        add_action('admin_menu', array($this, 'add_admin_menu'));
        add_action('admin_init', array($this, 'register_settings'));

        // AJAX handlers
        add_action('wp_ajax_skyyrose_ar_track', array($this, 'track_ar_view'));
        add_action('wp_ajax_nopriv_skyyrose_ar_track', array($this, 'track_ar_view'));

        // Plugin activation/deactivation
        register_activation_hook(__FILE__, array($this, 'activate'));
        register_deactivation_hook(__FILE__, array($this, 'deactivate'));

        // Internationalization
        add_action('plugins_loaded', array($this, 'load_textdomain'));
    }

    /**
     * Load plugin text domain for translations
     */
    public function load_textdomain() {
        load_plugin_textdomain(
            'skyyrose-ar',
            false,
            dirname(SKYYROSE_AR_PLUGIN_BASENAME) . '/languages'
        );
    }

    /**
     * AR button shortcode handler
     *
     * @param array $atts Shortcode attributes
     * @return string HTML output
     */
    public function ar_button_shortcode($atts) {
        // Parse shortcode attributes
        $atts = shortcode_atts(
            array(
                'product_id' => '',
                'text' => get_option('skyyrose_ar_button_text', __('View in AR', 'skyyrose-ar')),
                'class' => '',
                'style' => get_option('skyyrose_ar_button_style', 'primary'),
                'size' => 'medium',
                'icon' => 'true',
            ),
            $atts,
            'skyyrose_ar_button'
        );

        // Validate product ID
        if (empty($atts['product_id'])) {
            return $this->render_error(__('Product ID is required', 'skyyrose-ar'));
        }

        $product_id = intval($atts['product_id']);

        // Get USDZ URL for the product
        $usdz_url = $this->get_product_usdz($product_id);

        if (!$usdz_url) {
            return $this->render_error(__('USDZ file not found for this product', 'skyyrose-ar'));
        }

        // Get product data for AR metadata
        $product_name = get_the_title($product_id);
        $product_image = get_the_post_thumbnail_url($product_id, 'large');

        // Build AR Quick Look URL with parameters
        $ar_url = $this->build_ar_url($usdz_url, array(
            'allowsContentScaling' => '0',
            'canonicalWebPageURL' => get_permalink($product_id),
        ));

        // Generate unique button ID
        $button_id = 'skyyrose-ar-btn-' . $product_id . '-' . wp_rand();

        // Build CSS classes
        $button_classes = array(
            'skyyrose-ar-button',
            'skyyrose-ar-button--' . esc_attr($atts['style']),
            'skyyrose-ar-button--' . esc_attr($atts['size']),
        );

        if (!empty($atts['class'])) {
            $button_classes[] = esc_attr($atts['class']);
        }

        // Check if browser supports AR
        $supports_ar = $this->detect_ar_support();

        // Build data attributes
        $data_attrs = array(
            'product-id' => $product_id,
            'product-name' => esc_attr($product_name),
            'usdz-url' => esc_url($usdz_url),
            'track-analytics' => get_option('skyyrose_ar_analytics_enabled', '1'),
        );

        // Render button HTML
        ob_start();
        ?>
        <div class="skyyrose-ar-button-wrapper" id="<?php echo esc_attr($button_id); ?>-wrapper">
            <?php if ($supports_ar) : ?>
                <a
                    href="<?php echo esc_url($ar_url); ?>"
                    id="<?php echo esc_attr($button_id); ?>"
                    class="<?php echo esc_attr(implode(' ', $button_classes)); ?>"
                    rel="ar"
                    <?php foreach ($data_attrs as $key => $value) : ?>
                        data-<?php echo esc_attr($key); ?>="<?php echo esc_attr($value); ?>"
                    <?php endforeach; ?>
                >
                    <?php if ($atts['icon'] === 'true') : ?>
                        <span class="skyyrose-ar-button__icon" aria-hidden="true">
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20">
                                <path d="M12 2L2 7v10l10 5 10-5V7L12 2zm0 2.18L19.82 8 12 11.82 4.18 8 12 4.18zM4 9.18l7 3.5v7.14l-7-3.5V9.18zm16 0v7.14l-7 3.5v-7.14l7-3.5z" fill="currentColor"/>
                            </svg>
                        </span>
                    <?php endif; ?>
                    <span class="skyyrose-ar-button__text">
                        <?php echo esc_html($atts['text']); ?>
                    </span>
                </a>
            <?php else : ?>
                <button
                    type="button"
                    id="<?php echo esc_attr($button_id); ?>"
                    class="<?php echo esc_attr(implode(' ', $button_classes)); ?> skyyrose-ar-button--fallback"
                    <?php foreach ($data_attrs as $key => $value) : ?>
                        data-<?php echo esc_attr($key); ?>="<?php echo esc_attr($value); ?>"
                    <?php endforeach; ?>
                >
                    <?php if ($atts['icon'] === 'true') : ?>
                        <span class="skyyrose-ar-button__icon" aria-hidden="true">
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20">
                                <path d="M12 2L2 7v10l10 5 10-5V7L12 2zm0 2.18L19.82 8 12 11.82 4.18 8 12 4.18zM4 9.18l7 3.5v7.14l-7-3.5V9.18zm16 0v7.14l-7 3.5v-7.14l7-3.5z" fill="currentColor"/>
                            </svg>
                        </span>
                    <?php endif; ?>
                    <span class="skyyrose-ar-button__text">
                        <?php echo esc_html(__('View 3D Model', 'skyyrose-ar')); ?>
                    </span>
                </button>

                <!-- Fallback 3D Viewer Modal -->
                <div class="skyyrose-ar-modal" id="<?php echo esc_attr($button_id); ?>-modal" style="display: none;">
                    <div class="skyyrose-ar-modal__overlay"></div>
                    <div class="skyyrose-ar-modal__content">
                        <button type="button" class="skyyrose-ar-modal__close" aria-label="<?php esc_attr_e('Close', 'skyyrose-ar'); ?>">
                            <span aria-hidden="true">&times;</span>
                        </button>
                        <div class="skyyrose-ar-modal__viewer">
                            <model-viewer
                                src="<?php echo esc_url(str_replace('.usdz', '.glb', $usdz_url)); ?>"
                                alt="<?php echo esc_attr($product_name); ?>"
                                auto-rotate
                                camera-controls
                                shadow-intensity="1"
                                ar-modes="webxr scene-viewer quick-look"
                                poster="<?php echo esc_url($product_image); ?>"
                            >
                            </model-viewer>
                        </div>
                    </div>
                </div>
            <?php endif; ?>
        </div>
        <?php

        return ob_get_clean();
    }

    /**
     * Get USDZ URL for a product
     *
     * @param int $product_id Product ID
     * @return string|false USDZ URL or false if not found
     */
    private function get_product_usdz($product_id) {
        // Check product meta for USDZ URL
        $usdz_url = get_post_meta($product_id, '_skyyrose_usdz_url', true);

        if ($usdz_url) {
            return $usdz_url;
        }

        // Check for attachment
        $usdz_attachment_id = get_post_meta($product_id, '_skyyrose_usdz_attachment_id', true);

        if ($usdz_attachment_id) {
            return wp_get_attachment_url($usdz_attachment_id);
        }

        // Check WooCommerce product meta if available
        if (class_exists('WooCommerce')) {
            $product = wc_get_product($product_id);
            if ($product) {
                $usdz_url = $product->get_meta('_usdz_file_url');
                if ($usdz_url) {
                    return $usdz_url;
                }
            }
        }

        return false;
    }

    /**
     * Build AR Quick Look URL with parameters
     *
     * @param string $usdz_url Base USDZ URL
     * @param array $params URL parameters
     * @return string Complete AR URL
     */
    private function build_ar_url($usdz_url, $params = array()) {
        $url = $usdz_url;

        if (!empty($params)) {
            $hash_params = array();
            foreach ($params as $key => $value) {
                $hash_params[] = urlencode($key) . '=' . urlencode($value);
            }
            $url .= '#' . implode('&', $hash_params);
        }

        return $url;
    }

    /**
     * Detect if browser supports AR Quick Look
     *
     * @return bool
     */
    private function detect_ar_support() {
        // Server-side detection is limited, rely on client-side JS
        // This is a placeholder that always returns true for AR-capable browsers
        // Actual detection happens in JavaScript
        return true;
    }

    /**
     * Render error message
     *
     * @param string $message Error message
     * @return string HTML error output
     */
    private function render_error($message) {
        if (!current_user_can('edit_posts')) {
            return '';
        }

        return sprintf(
            '<div class="skyyrose-ar-error" style="padding: 10px; background: #ffebee; border-left: 4px solid #c62828; color: #c62828;">%s</div>',
            esc_html($message)
        );
    }

    /**
     * Enqueue plugin assets
     */
    public function enqueue_assets() {
        // Only enqueue if shortcode is present on the page
        global $post;
        if (!is_a($post, 'WP_Post') || !has_shortcode($post->post_content, 'skyyrose_ar_button')) {
            return;
        }

        // Enqueue CSS
        wp_enqueue_style(
            'skyyrose-ar-styles',
            SKYYROSE_AR_PLUGIN_URL . 'assets/css/ar-viewer.css',
            array(),
            SKYYROSE_AR_VERSION
        );

        // Inline critical CSS for button styling
        $custom_css = $this->get_custom_css();
        wp_add_inline_style('skyyrose-ar-styles', $custom_css);

        // Enqueue JavaScript
        wp_enqueue_script(
            'skyyrose-ar-scripts',
            SKYYROSE_AR_PLUGIN_URL . 'assets/js/ar-viewer.js',
            array('jquery'),
            SKYYROSE_AR_VERSION,
            true
        );

        // Localize script
        wp_localize_script('skyyrose-ar-scripts', 'skyyRoseAR', array(
            'ajaxUrl' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('skyyrose_ar_nonce'),
            'analytics' => get_option('skyyrose_ar_analytics_enabled', '1'),
            'i18n' => array(
                'loading' => __('Loading 3D Model...', 'skyyrose-ar'),
                'error' => __('Failed to load 3D model', 'skyyrose-ar'),
                'notSupported' => __('AR not supported on this device', 'skyyrose-ar'),
            ),
        ));

        // Enqueue model-viewer for fallback
        wp_enqueue_script(
            'model-viewer',
            'https://ajax.googleapis.com/ajax/libs/model-viewer/3.3.0/model-viewer.min.js',
            array(),
            '3.3.0',
            true
        );
    }

    /**
     * Get custom CSS based on admin settings
     *
     * @return string CSS
     */
    private function get_custom_css() {
        $primary_color = get_option('skyyrose_ar_button_color', '#B76E79');
        $secondary_color = get_option('skyyrose_ar_button_hover_color', '#A05E69');

        return "
            .skyyrose-ar-button {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                padding: 12px 24px;
                background: {$primary_color};
                color: #ffffff;
                border: none;
                border-radius: 4px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                font-size: 16px;
                font-weight: 600;
                text-decoration: none;
                cursor: pointer;
                transition: all 0.3s ease;
            }

            .skyyrose-ar-button:hover,
            .skyyrose-ar-button:focus {
                background: {$secondary_color};
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(183, 110, 121, 0.4);
            }

            .skyyrose-ar-button--secondary {
                background: #1A1A1A;
            }

            .skyyrose-ar-button--secondary:hover {
                background: #333333;
            }

            .skyyrose-ar-button--small {
                padding: 8px 16px;
                font-size: 14px;
            }

            .skyyrose-ar-button--large {
                padding: 16px 32px;
                font-size: 18px;
            }

            .skyyrose-ar-button__icon svg {
                display: block;
            }

            .skyyrose-ar-modal {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                z-index: 999999;
            }

            .skyyrose-ar-modal__overlay {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.8);
            }

            .skyyrose-ar-modal__content {
                position: relative;
                width: 90%;
                max-width: 800px;
                height: 80%;
                margin: 5% auto;
                background: #ffffff;
                border-radius: 8px;
                overflow: hidden;
            }

            .skyyrose-ar-modal__close {
                position: absolute;
                top: 16px;
                right: 16px;
                z-index: 10;
                background: rgba(0, 0, 0, 0.5);
                color: #ffffff;
                border: none;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                font-size: 24px;
                cursor: pointer;
                transition: background 0.3s ease;
            }

            .skyyrose-ar-modal__close:hover {
                background: rgba(0, 0, 0, 0.8);
            }

            .skyyrose-ar-modal__viewer {
                width: 100%;
                height: 100%;
            }

            .skyyrose-ar-modal__viewer model-viewer {
                width: 100%;
                height: 100%;
            }
        ";
    }

    /**
     * Track AR view via AJAX
     */
    public function track_ar_view() {
        // Verify nonce
        check_ajax_referer('skyyrose_ar_nonce', 'nonce');

        // Check if analytics is enabled
        if (get_option('skyyrose_ar_analytics_enabled', '1') !== '1') {
            wp_send_json_success(array('tracked' => false));
        }

        // Sanitize input
        $product_id = isset($_POST['product_id']) ? intval($_POST['product_id']) : 0;
        $event_type = isset($_POST['event_type']) ? sanitize_text_field($_POST['event_type']) : 'view';

        if (!$product_id) {
            wp_send_json_error(array('message' => __('Invalid product ID', 'skyyrose-ar')));
        }

        // Increment view counter
        $meta_key = '_skyyrose_ar_' . $event_type . '_count';
        $current_count = (int) get_post_meta($product_id, $meta_key, true);
        update_post_meta($product_id, $meta_key, $current_count + 1);

        // Log to custom table if exists
        global $wpdb;
        $table_name = $wpdb->prefix . 'skyyrose_ar_analytics';

        if ($wpdb->get_var("SHOW TABLES LIKE '{$table_name}'") === $table_name) {
            $wpdb->insert(
                $table_name,
                array(
                    'product_id' => $product_id,
                    'event_type' => $event_type,
                    'user_agent' => sanitize_text_field($_SERVER['HTTP_USER_AGENT']),
                    'ip_address' => sanitize_text_field($_SERVER['REMOTE_ADDR']),
                    'created_at' => current_time('mysql'),
                ),
                array('%d', '%s', '%s', '%s', '%s')
            );
        }

        wp_send_json_success(array(
            'tracked' => true,
            'count' => $current_count + 1,
        ));
    }

    /**
     * Add admin menu
     */
    public function add_admin_menu() {
        add_options_page(
            __('SkyyRose AR Settings', 'skyyrose-ar'),
            __('AR Quick Look', 'skyyrose-ar'),
            'manage_options',
            'skyyrose-ar-settings',
            array($this, 'render_admin_page')
        );
    }

    /**
     * Register plugin settings
     */
    public function register_settings() {
        // General settings
        register_setting('skyyrose_ar_general', 'skyyrose_ar_button_text', array(
            'type' => 'string',
            'sanitize_callback' => 'sanitize_text_field',
            'default' => __('View in AR', 'skyyrose-ar'),
        ));

        register_setting('skyyrose_ar_general', 'skyyrose_ar_button_style', array(
            'type' => 'string',
            'sanitize_callback' => 'sanitize_text_field',
            'default' => 'primary',
        ));

        register_setting('skyyrose_ar_general', 'skyyrose_ar_button_color', array(
            'type' => 'string',
            'sanitize_callback' => 'sanitize_hex_color',
            'default' => '#B76E79',
        ));

        register_setting('skyyrose_ar_general', 'skyyrose_ar_button_hover_color', array(
            'type' => 'string',
            'sanitize_callback' => 'sanitize_hex_color',
            'default' => '#A05E69',
        ));

        register_setting('skyyrose_ar_general', 'skyyrose_ar_analytics_enabled', array(
            'type' => 'string',
            'sanitize_callback' => array($this, 'sanitize_checkbox'),
            'default' => '1',
        ));

        // Add settings sections
        add_settings_section(
            'skyyrose_ar_general_section',
            __('General Settings', 'skyyrose-ar'),
            array($this, 'render_general_section'),
            'skyyrose_ar_general'
        );

        add_settings_section(
            'skyyrose_ar_styling_section',
            __('Button Styling', 'skyyrose-ar'),
            array($this, 'render_styling_section'),
            'skyyrose_ar_general'
        );

        add_settings_section(
            'skyyrose_ar_analytics_section',
            __('Analytics', 'skyyrose-ar'),
            array($this, 'render_analytics_section'),
            'skyyrose_ar_general'
        );

        // Add settings fields
        add_settings_field(
            'skyyrose_ar_button_text',
            __('Default Button Text', 'skyyrose-ar'),
            array($this, 'render_text_field'),
            'skyyrose_ar_general',
            'skyyrose_ar_general_section',
            array('label_for' => 'skyyrose_ar_button_text')
        );

        add_settings_field(
            'skyyrose_ar_button_color',
            __('Primary Button Color', 'skyyrose-ar'),
            array($this, 'render_color_field'),
            'skyyrose_ar_general',
            'skyyrose_ar_styling_section',
            array('label_for' => 'skyyrose_ar_button_color')
        );

        add_settings_field(
            'skyyrose_ar_button_hover_color',
            __('Button Hover Color', 'skyyrose-ar'),
            array($this, 'render_color_field'),
            'skyyrose_ar_general',
            'skyyrose_ar_styling_section',
            array('label_for' => 'skyyrose_ar_button_hover_color')
        );

        add_settings_field(
            'skyyrose_ar_analytics_enabled',
            __('Enable Analytics Tracking', 'skyyrose-ar'),
            array($this, 'render_checkbox_field'),
            'skyyrose_ar_general',
            'skyyrose_ar_analytics_section',
            array('label_for' => 'skyyrose_ar_analytics_enabled')
        );
    }

    /**
     * Render admin settings page
     */
    public function render_admin_page() {
        if (!current_user_can('manage_options')) {
            return;
        }

        // Handle form submission
        if (isset($_GET['settings-updated'])) {
            add_settings_error(
                'skyyrose_ar_messages',
                'skyyrose_ar_message',
                __('Settings saved successfully.', 'skyyrose-ar'),
                'success'
            );
        }

        settings_errors('skyyrose_ar_messages');
        ?>
        <div class="wrap">
            <h1><?php echo esc_html(get_admin_page_title()); ?></h1>

            <div style="background: #fff; padding: 20px; margin-top: 20px; border-left: 4px solid #B76E79;">
                <h2><?php esc_html_e('Shortcode Usage', 'skyyrose-ar'); ?></h2>
                <p><?php esc_html_e('Use this shortcode to display AR Quick Look buttons:', 'skyyrose-ar'); ?></p>
                <code>[skyyrose_ar_button product_id="123"]</code>
                <br><br>
                <p><strong><?php esc_html_e('Available Parameters:', 'skyyrose-ar'); ?></strong></p>
                <ul style="list-style: disc; margin-left: 20px;">
                    <li><code>product_id</code> - <?php esc_html_e('(Required) Product ID', 'skyyrose-ar'); ?></li>
                    <li><code>text</code> - <?php esc_html_e('Button text (default: "View in AR")', 'skyyrose-ar'); ?></li>
                    <li><code>style</code> - <?php esc_html_e('Button style: primary, secondary (default: primary)', 'skyyrose-ar'); ?></li>
                    <li><code>size</code> - <?php esc_html_e('Button size: small, medium, large (default: medium)', 'skyyrose-ar'); ?></li>
                    <li><code>icon</code> - <?php esc_html_e('Show icon: true, false (default: true)', 'skyyrose-ar'); ?></li>
                    <li><code>class</code> - <?php esc_html_e('Additional CSS classes', 'skyyrose-ar'); ?></li>
                </ul>
            </div>

            <form action="options.php" method="post">
                <?php
                settings_fields('skyyrose_ar_general');
                do_settings_sections('skyyrose_ar_general');
                submit_button(__('Save Settings', 'skyyrose-ar'));
                ?>
            </form>
        </div>
        <?php
    }

    /**
     * Render section descriptions
     */
    public function render_general_section() {
        echo '<p>' . esc_html__('Configure default settings for AR Quick Look buttons.', 'skyyrose-ar') . '</p>';
    }

    public function render_styling_section() {
        echo '<p>' . esc_html__('Customize the appearance of AR buttons to match your brand.', 'skyyrose-ar') . '</p>';
    }

    public function render_analytics_section() {
        echo '<p>' . esc_html__('Track AR interactions and user engagement.', 'skyyrose-ar') . '</p>';
    }

    /**
     * Render text input field
     */
    public function render_text_field($args) {
        $option = get_option($args['label_for']);
        ?>
        <input
            type="text"
            id="<?php echo esc_attr($args['label_for']); ?>"
            name="<?php echo esc_attr($args['label_for']); ?>"
            value="<?php echo esc_attr($option); ?>"
            class="regular-text"
        />
        <?php
    }

    /**
     * Render color picker field
     */
    public function render_color_field($args) {
        $option = get_option($args['label_for']);
        ?>
        <input
            type="text"
            id="<?php echo esc_attr($args['label_for']); ?>"
            name="<?php echo esc_attr($args['label_for']); ?>"
            value="<?php echo esc_attr($option); ?>"
            class="color-picker"
            data-default-color="<?php echo esc_attr($option); ?>"
        />
        <script>
            jQuery(document).ready(function($) {
                $('.color-picker').wpColorPicker();
            });
        </script>
        <?php
    }

    /**
     * Render checkbox field
     */
    public function render_checkbox_field($args) {
        $option = get_option($args['label_for']);
        ?>
        <label>
            <input
                type="checkbox"
                id="<?php echo esc_attr($args['label_for']); ?>"
                name="<?php echo esc_attr($args['label_for']); ?>"
                value="1"
                <?php checked('1', $option); ?>
            />
            <?php esc_html_e('Track AR button clicks and views', 'skyyrose-ar'); ?>
        </label>
        <?php
    }

    /**
     * Sanitize checkbox input
     */
    public function sanitize_checkbox($input) {
        return ($input === '1' || $input === 1) ? '1' : '0';
    }

    /**
     * Plugin activation
     */
    public function activate() {
        // Create analytics table
        global $wpdb;
        $table_name = $wpdb->prefix . 'skyyrose_ar_analytics';
        $charset_collate = $wpdb->get_charset_collate();

        $sql = "CREATE TABLE IF NOT EXISTS {$table_name} (
            id bigint(20) NOT NULL AUTO_INCREMENT,
            product_id bigint(20) NOT NULL,
            event_type varchar(50) NOT NULL,
            user_agent text,
            ip_address varchar(45),
            created_at datetime NOT NULL,
            PRIMARY KEY (id),
            KEY product_id (product_id),
            KEY event_type (event_type),
            KEY created_at (created_at)
        ) {$charset_collate};";

        require_once(ABSPATH . 'wp-admin/includes/upgrade.php');
        dbDelta($sql);

        // Set default options
        add_option('skyyrose_ar_button_text', __('View in AR', 'skyyrose-ar'));
        add_option('skyyrose_ar_button_style', 'primary');
        add_option('skyyrose_ar_button_color', '#B76E79');
        add_option('skyyrose_ar_button_hover_color', '#A05E69');
        add_option('skyyrose_ar_analytics_enabled', '1');

        flush_rewrite_rules();
    }

    /**
     * Plugin deactivation
     */
    public function deactivate() {
        flush_rewrite_rules();
    }
}

// Initialize plugin
function skyyrose_ar_init() {
    return SkyyRose_AR_Quick_Look::get_instance();
}

// Start the plugin
add_action('plugins_loaded', 'skyyrose_ar_init');

/**
 * Helper function to get USDZ URL programmatically
 *
 * @param int $product_id Product ID
 * @return string|false USDZ URL or false
 */
function skyyrose_get_product_usdz($product_id) {
    $instance = SkyyRose_AR_Quick_Look::get_instance();
    return $instance->get_product_usdz($product_id);
}

/**
 * Helper function to render AR button programmatically
 *
 * @param int $product_id Product ID
 * @param array $args Button arguments
 * @return string HTML output
 */
function skyyrose_render_ar_button($product_id, $args = array()) {
    $args['product_id'] = $product_id;
    return do_shortcode('[skyyrose_ar_button ' . http_build_query($args, '', ' ') . ']');
}
