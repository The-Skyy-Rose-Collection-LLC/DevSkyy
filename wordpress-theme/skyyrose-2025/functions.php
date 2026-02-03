<?php
/**
 * SkyyRose 2025 Theme Functions
 *
 * @package SkyyRose_2025
 * @version 2.0.0
 */

if (!defined('ABSPATH')) {
    exit;
}

define('SKYYROSE_VERSION', '2.0.0');
define('SKYYROSE_THEME_DIR', get_template_directory());
define('SKYYROSE_THEME_URL', get_template_directory_uri());

/**
 * Load Core Functionality
 */
// Security must be loaded FIRST
require_once SKYYROSE_THEME_DIR . '/inc/security-hardening.php';

require_once SKYYROSE_THEME_DIR . '/inc/theme-customizer.php';
require_once SKYYROSE_THEME_DIR . '/inc/woocommerce-config.php';
require_once SKYYROSE_THEME_DIR . '/inc/performance.php';
require_once SKYYROSE_THEME_DIR . '/inc/performance-optimizations.php';
require_once SKYYROSE_THEME_DIR . '/inc/ai-image-enhancement.php';
require_once SKYYROSE_THEME_DIR . '/inc/pre-order-functions.php';

// Load Elementor widgets if Elementor is active
if (did_action('elementor/loaded')) {
    require_once SKYYROSE_THEME_DIR . '/inc/elementor-widgets.php';
}

/**
 * Theme Setup
 */
function skyyrose_setup() {
    // Add theme support
    add_theme_support('title-tag');
    add_theme_support('post-thumbnails');
    add_theme_support('html5', ['search-form', 'comment-form', 'comment-list', 'gallery', 'caption']);
    add_theme_support('custom-logo');
    add_theme_support('responsive-embeds');
    add_theme_support('align-wide');
    add_theme_support('editor-styles');

    // WooCommerce support
    add_theme_support('woocommerce');
    add_theme_support('wc-product-gallery-zoom');
    add_theme_support('wc-product-gallery-lightbox');
    add_theme_support('wc-product-gallery-slider');

    // Register nav menus
    register_nav_menus([
        'primary' => __('Primary Menu', 'skyyrose-2025'),
        'footer' => __('Footer Menu', 'skyyrose-2025'),
    ]);

    // Image sizes
    add_image_size('skyyrose-hero', 1920, 1080, true);
    add_image_size('skyyrose-product', 800, 800, true);
    add_image_size('skyyrose-thumbnail', 400, 400, true);
}
add_action('after_setup_theme', 'skyyrose_setup');

/**
 * Get asset suffix (.min for production, empty for development)
 */
function skyyrose_asset_suffix() {
    return (defined('WP_DEBUG') && WP_DEBUG) ? '' : '.min';
}

/**
 * Enqueue Scripts & Styles
 */
function skyyrose_enqueue_assets() {
    $suffix = skyyrose_asset_suffix();

    // Styles
    wp_enqueue_style('skyyrose-style', get_stylesheet_uri(), [], SKYYROSE_VERSION);
    wp_enqueue_style('skyyrose-fonts', 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@400;700&display=swap', [], null);
    wp_enqueue_style('skyyrose-animations', SKYYROSE_THEME_URL . "/assets/css/animations{$suffix}.css", [], SKYYROSE_VERSION);
    wp_enqueue_style('skyyrose-templates', SKYYROSE_THEME_URL . "/assets/css/templates-luxury{$suffix}.css", [], SKYYROSE_VERSION);

    // Scripts
    wp_enqueue_script('gsap', 'https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js', [], '3.12.5', true);
    wp_enqueue_script('gsap-scrolltrigger', 'https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/ScrollTrigger.min.js', ['gsap'], '3.12.5', true);
    wp_enqueue_script('three', 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js', [], '0.160.0', true);
    wp_enqueue_script('three-gltf', 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/loaders/GLTFLoader.js', ['three'], '0.160.0', true);
    wp_enqueue_script('three-orbit', 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/controls/OrbitControls.js', ['three'], '0.160.0', true);

    // Theme scripts
    wp_enqueue_script('skyyrose-animations', SKYYROSE_THEME_URL . "/assets/js/animations{$suffix}.js", ['gsap', 'gsap-scrolltrigger'], SKYYROSE_VERSION, true);

    // Collection-specific immersive scenes (only on collection pages)
    if (is_page_template('template-collection.php')) {
        // Add Three.js post-processing dependencies
        wp_enqueue_script('three-effectcomposer', 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/postprocessing/EffectComposer.js', ['three'], '0.160.0', true);
        wp_enqueue_script('three-renderpass', 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/postprocessing/RenderPass.js', ['three-effectcomposer'], '0.160.0', true);
        wp_enqueue_script('three-bloom', 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/postprocessing/UnrealBloomPass.js', ['three-effectcomposer'], '0.160.0', true);

        // Collection scene scripts
        wp_enqueue_script('black-rose-scene', SKYYROSE_THEME_URL . "/assets/js/black-rose-scene{$suffix}.js", ['three', 'three-orbit', 'three-effectcomposer', 'three-renderpass', 'three-bloom'], SKYYROSE_VERSION, true);
        wp_enqueue_script('love-hurts-scene', SKYYROSE_THEME_URL . "/assets/js/love-hurts-scene{$suffix}.js", ['three', 'three-orbit'], SKYYROSE_VERSION, true);
        wp_enqueue_script('signature-scene', SKYYROSE_THEME_URL . "/assets/js/signature-scene{$suffix}.js", ['three', 'three-orbit'], SKYYROSE_VERSION, true);

        // TWEEN.js for camera animations
        wp_enqueue_script('tween', 'https://cdn.jsdelivr.net/npm/@tweenjs/tween.js@18.6.4/dist/tween.umd.js', [], '18.6.4', true);
    }

    // LuxuryProductViewer (single product pages, Vault, Elementor widgets)
    if (is_singular('product') || is_page_template('template-vault.php') || (function_exists('elementor_is_edit_mode') && elementor_is_edit_mode())) {
        // Add Three.js post-processing dependencies
        wp_enqueue_script('three-effectcomposer', 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/postprocessing/EffectComposer.js', ['three'], '0.160.0', true);
        wp_enqueue_script('three-renderpass', 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/postprocessing/RenderPass.js', ['three-effectcomposer'], '0.160.0', true);
        wp_enqueue_script('three-bloom', 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/postprocessing/UnrealBloomPass.js', ['three-effectcomposer'], '0.160.0', true);

        // DRACO loader for compressed models
        wp_enqueue_script('three-draco', 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/loaders/DRACOLoader.js', ['three'], '0.160.0', true);

        // Luxury Product Viewer
        wp_enqueue_script('luxury-product-viewer', SKYYROSE_THEME_URL . "/assets/js/luxury-product-viewer{$suffix}.js", ['three', 'three-orbit', 'three-gltf', 'three-draco', 'three-effectcomposer', 'three-renderpass', 'three-bloom'], SKYYROSE_VERSION, true);
    }

    // Vault Enhanced (only on Vault page)
    if (is_page_template('template-vault.php')) {
        // Enqueue Vault CSS (inline in template, but could be separate)
        // wp_enqueue_style('vault-enhanced', SKYYROSE_THEME_URL . '/assets/css/vault-enhanced.css', [], SKYYROSE_VERSION);

        // Vault JavaScript (NOT enqueued - loaded inline in template with vaultData)
        // This is intentional to allow vaultData to be defined before the script runs
    }

    // Localize script
    wp_localize_script('skyyrose-main', 'skyyrose', [
        'ajaxUrl' => admin_url('admin-ajax.php'),
        'nonce' => wp_create_nonce('skyyrose_nonce'),
        'apiUrl' => get_rest_url(),
        'themeUrl' => SKYYROSE_THEME_URL,
    ]);
}
add_action('wp_enqueue_scripts', 'skyyrose_enqueue_assets');

/**
 * Register 3D Viewer Shortcode
 */
function skyyrose_3d_viewer_shortcode($atts) {
    $atts = shortcode_atts([
        'id' => '',
        'model' => '',
        'thumbnail' => '',
        'autoplay' => 'true',
        'bg-color' => '#1A1A1A',
    ], $atts, 'skyyrose_3d');

    $viewer_id = !empty($atts['id']) ? esc_attr($atts['id']) : 'viewer-' . uniqid();

    ob_start();
    ?>
    <div id="<?php echo $viewer_id; ?>"
         class="skyyrose-3d-viewer"
         data-model="<?php echo esc_url($atts['model']); ?>"
         data-thumbnail="<?php echo esc_url($atts['thumbnail']); ?>"
         data-autoplay="<?php echo esc_attr($atts['autoplay']); ?>"
         data-bg-color="<?php echo esc_attr($atts['bg-color']); ?>">
        <div class="loading-skeleton"></div>
    </div>
    <?php
    return ob_get_clean();
}
add_shortcode('skyyrose_3d', 'skyyrose_3d_viewer_shortcode');

/**
 * Elementor Widget Registration
 */
function skyyrose_register_elementor_widgets() {
    if (did_action('elementor/loaded')) {
        require_once SKYYROSE_THEME_DIR . '/inc/elementor/3d-viewer-widget.php';
        \Elementor\Plugin::instance()->widgets_manager->register(new \SkyyRose\Elementor\ThreeDViewer());
    }
}
add_action('elementor/widgets/register', 'skyyrose_register_elementor_widgets');

/**
 * WooCommerce Product 3D Model Meta
 */
function skyyrose_add_product_3d_meta() {
    global $post;
    $model_url = get_post_meta($post->ID, '_skyyrose_3d_model_url', true);

    if ($model_url) {
        echo do_shortcode('[skyyrose_3d model="' . esc_url($model_url) . '"]');
    }
}
add_action('woocommerce_before_single_product_summary', 'skyyrose_add_product_3d_meta', 15);

/**
 * View Transitions API Support
 */
function skyyrose_add_view_transitions() {
    ?>
    <script>
    if ('startViewTransition' in document) {
        document.addEventListener('DOMContentLoaded', () => {
            const links = document.querySelectorAll('a:not([target="_blank"])');
            links.forEach(link => {
                link.addEventListener('click', (e) => {
                    if (e.ctrlKey || e.metaKey) return;
                    e.preventDefault();
                    document.startViewTransition(() => {
                        window.location = link.href;
                    });
                });
            });
        });
    }
    </script>
    <?php
}
add_action('wp_footer', 'skyyrose_add_view_transitions');

/**
 * Custom REST API Endpoints
 */
function skyyrose_register_api_routes() {
    register_rest_route('skyyrose/v1', '/3d-models', [
        'methods' => 'GET',
        'callback' => 'skyyrose_get_3d_models',
        'permission_callback' => '__return_true',
    ]);
}
add_action('rest_api_init', 'skyyrose_register_api_routes');

function skyyrose_get_3d_models($request) {
    $args = [
        'post_type' => 'product',
        'posts_per_page' => -1,
        'meta_query' => [
            [
                'key' => '_skyyrose_3d_model_url',
                'compare' => 'EXISTS',
            ],
        ],
    ];

    $products = get_posts($args);
    $models = [];

    foreach ($products as $product) {
        $models[] = [
            'id' => $product->ID,
            'title' => $product->post_title,
            'model_url' => get_post_meta($product->ID, '_skyyrose_3d_model_url', true),
            'thumbnail' => get_the_post_thumbnail_url($product->ID, 'medium'),
        ];
    }

    return rest_ensure_response($models);
}

/**
 * Admin: Add 3D Model Meta Box
 */
function skyyrose_add_3d_model_meta_box() {
    add_meta_box(
        'skyyrose_3d_model',
        __('3D Model', 'skyyrose-2025'),
        'skyyrose_3d_model_meta_box_callback',
        'product',
        'side',
        'default'
    );
}
add_action('add_meta_boxes', 'skyyrose_add_3d_model_meta_box');

function skyyrose_3d_model_meta_box_callback($post) {
    $model_url = get_post_meta($post->ID, '_skyyrose_3d_model_url', true);
    wp_nonce_field('skyyrose_3d_model_nonce', 'skyyrose_3d_model_nonce');
    ?>
    <p>
        <label for="skyyrose_3d_model_url"><?php _e('3D Model URL (.glb/.gltf):', 'skyyrose-2025'); ?></label>
        <input type="url"
               id="skyyrose_3d_model_url"
               name="skyyrose_3d_model_url"
               value="<?php echo esc_attr($model_url); ?>"
               style="width: 100%;" />
    </p>
    <?php
}

function skyyrose_save_3d_model_meta($post_id) {
    if (!isset($_POST['skyyrose_3d_model_nonce']) ||
        !wp_verify_nonce($_POST['skyyrose_3d_model_nonce'], 'skyyrose_3d_model_nonce')) {
        return;
    }

    if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) {
        return;
    }

    if (isset($_POST['skyyrose_3d_model_url'])) {
        update_post_meta($post_id, '_skyyrose_3d_model_url', esc_url_raw($_POST['skyyrose_3d_model_url']));
    }
}
add_action('save_post', 'skyyrose_save_3d_model_meta');

/**
 * Contact Form Handler
 */
add_action('wp_ajax_skyyrose_contact_form', 'skyyrose_handle_contact_form');
add_action('wp_ajax_nopriv_skyyrose_contact_form', 'skyyrose_handle_contact_form');

function skyyrose_handle_contact_form() {
    // Verify nonce
    if (!isset($_POST['contact_nonce']) || !wp_verify_nonce($_POST['contact_nonce'], 'skyyrose_contact')) {
        wp_send_json_error('Security check failed');
    }

    // Sanitize inputs
    $name = sanitize_text_field($_POST['name'] ?? '');
    $email = sanitize_email($_POST['email'] ?? '');
    $subject = sanitize_text_field($_POST['subject'] ?? '');
    $message = sanitize_textarea_field($_POST['message'] ?? '');

    // Validate
    if (empty($name) || empty($email) || empty($subject) || empty($message)) {
        wp_send_json_error('All fields are required');
    }

    if (!is_email($email)) {
        wp_send_json_error('Invalid email address');
    }

    // Send email
    $to = get_option('skyyrose_contact_email', get_option('admin_email'));
    $email_subject = "SkyyRose Contact Form: $subject";
    $email_message = "Name: $name\n";
    $email_message .= "Email: $email\n";
    $email_message .= "Subject: $subject\n\n";
    $email_message .= "Message:\n$message";

    $headers = array('Reply-To: ' . $email);

    $sent = wp_mail($to, $email_subject, $email_message, $headers);

    if ($sent) {
        wp_send_json_success('Message sent successfully');
    } else {
        wp_send_json_error('Failed to send message. Please try again.');
    }
}

/**
 * AJAX Add to Cart Handler
 */
add_action('wp_ajax_woocommerce_ajax_add_to_cart', 'skyyrose_ajax_add_to_cart');
add_action('wp_ajax_nopriv_woocommerce_ajax_add_to_cart', 'skyyrose_ajax_add_to_cart');

function skyyrose_ajax_add_to_cart() {
    // CSRF protection
    check_ajax_referer('skyyrose_cart_nonce', 'nonce');

    // Rate limiting
    if (!skyyrose_check_rate_limit('add_to_cart', 10, 60)) {
        wp_send_json_error('Too many requests. Please slow down.');
        return;
    }

    $product_id = absint($_POST['product_id'] ?? 0);
    $quantity = absint($_POST['quantity'] ?? 1);

    if ($product_id <=0 || $quantity <= 0) {
        wp_send_json_error('Invalid product or quantity');
        return;
    }

    // Verify product exists
    $product = wc_get_product($product_id);
    if (!$product) {
        wp_send_json_error('Product not found');
        return;
    }

    $added = WC()->cart->add_to_cart($product_id, $quantity);

    if ($added) {
        wp_send_json_success(array(
            'message' => 'Product added to cart',
            'cart_count' => WC()->cart->get_cart_contents_count(),
        ));
    } else {
        wp_send_json_error('Failed to add product to cart');
    }
}

/**
 * AJAX Get Collection Products for 3D Scene
 */
add_action('wp_ajax_get_collection_products', 'skyyrose_get_collection_products');
add_action('wp_ajax_nopriv_get_collection_products', 'skyyrose_get_collection_products');

function skyyrose_get_collection_products() {
    // CSRF protection
    check_ajax_referer('skyyrose_collection_nonce', 'nonce');

    // Rate limiting
    if (!skyyrose_check_rate_limit('collection_products', 20, 60)) {
        wp_send_json_error('Too many requests. Please slow down.');
        return;
    }

    $collection = sanitize_text_field($_GET['collection'] ?? '');
    $allowed_collections = ['black-rose', 'love-hurts', 'signature'];

    if (empty($collection) || !in_array($collection, $allowed_collections)) {
        wp_send_json_error('Invalid collection specified');
        return;
    }

    // Query products for this collection
    $args = [
        'post_type' => 'product',
        'posts_per_page' => -1,
        'meta_query' => [
            [
                'key' => '_skyyrose_collection',
                'value' => $collection,
                'compare' => '='
            ]
        ],
        'orderby' => 'menu_order',
        'order' => 'ASC'
    ];

    $products = new WP_Query($args);
    $product_data = [];

    if ($products->have_posts()) {
        $index = 0;
        while ($products->have_posts()) {
            $products->the_post();
            global $product;

            // Calculate position in a circular garden layout
            $radius = 8;
            $angle = ($index / $products->post_count) * 2 * M_PI;
            $x = $radius * cos($angle);
            $z = $radius * sin($angle);

            $product_data[] = [
                'id' => get_the_ID(),
                'name' => get_the_title(),
                'price' => $product->get_price(),
                'url' => get_permalink(),
                'thumbnailUrl' => get_the_post_thumbnail_url(get_the_ID(), 'thumbnail') ?: '',
                'position' => [$x, 0, $z],
                'isEasterEgg' => false
            ];

            $index++;
        }
        wp_reset_postdata();
    }

    wp_send_json_success($product_data);
}

/**
 * Custom Product Meta Fields
 */
function skyyrose_add_custom_product_meta_boxes() {
    add_meta_box(
        'skyyrose_product_meta',
        __('SkyyRose Product Details', 'skyyrose-2025'),
        'skyyrose_product_meta_box_callback',
        'product',
        'normal',
        'default'
    );
}
add_action('add_meta_boxes', 'skyyrose_add_custom_product_meta_boxes');

function skyyrose_product_meta_box_callback($post) {
    $collection = get_post_meta($post->ID, '_skyyrose_collection', true);
    $badge = get_post_meta($post->ID, '_product_badge', true);
    $fabric = get_post_meta($post->ID, '_fabric_composition', true);
    $care = get_post_meta($post->ID, '_care_instructions', true);
    $vault_preorder = get_post_meta($post->ID, '_vault_preorder', true);

    wp_nonce_field('skyyrose_product_meta', 'skyyrose_product_meta_nonce');
    ?>
    <style>
        .skyyrose-meta-field { margin-bottom: 15px; }
        .skyyrose-meta-field label { display: block; font-weight: 600; margin-bottom: 5px; }
        .skyyrose-meta-field input[type="text"],
        .skyyrose-meta-field textarea,
        .skyyrose-meta-field select { width: 100%; }
    </style>

    <div class="skyyrose-meta-field">
        <label for="skyyrose_collection"><?php _e('Collection', 'skyyrose-2025'); ?></label>
        <select name="skyyrose_collection" id="skyyrose_collection">
            <option value="">Select Collection</option>
            <option value="black-rose" <?php selected($collection, 'black-rose'); ?>>Black Rose</option>
            <option value="love-hurts" <?php selected($collection, 'love-hurts'); ?>>Love Hurts</option>
            <option value="signature" <?php selected($collection, 'signature'); ?>>Signature</option>
        </select>
    </div>

    <div class="skyyrose-meta-field">
        <label for="product_badge"><?php _e('Product Badge (Optional)', 'skyyrose-2025'); ?></label>
        <select name="product_badge" id="product_badge">
            <option value="">No Badge</option>
            <option value="NEW" <?php selected($badge, 'NEW'); ?>>NEW</option>
            <option value="LIMITED" <?php selected($badge, 'LIMITED'); ?>>LIMITED</option>
            <option value="EXCLUSIVE" <?php selected($badge, 'EXCLUSIVE'); ?>>EXCLUSIVE</option>
        </select>
    </div>

    <div class="skyyrose-meta-field">
        <label for="fabric_composition"><?php _e('Fabric Composition', 'skyyrose-2025'); ?></label>
        <input type="text" name="fabric_composition" id="fabric_composition" value="<?php echo esc_attr($fabric); ?>" placeholder="e.g., 80% Cotton, 20% Polyester">
    </div>

    <div class="skyyrose-meta-field">
        <label for="care_instructions"><?php _e('Care Instructions', 'skyyrose-2025'); ?></label>
        <textarea name="care_instructions" id="care_instructions" rows="3" placeholder="e.g., Machine wash cold, tumble dry low"><?php echo esc_textarea($care); ?></textarea>
    </div>

    <div class="skyyrose-meta-field">
        <label>
            <input type="checkbox" name="vault_preorder" value="1" <?php checked($vault_preorder, '1'); ?>>
            <?php _e('Show in The Vault (Pre-Order)', 'skyyrose-2025'); ?>
        </label>
    </div>
    <?php
}

function skyyrose_save_product_meta($post_id) {
    if (!isset($_POST['skyyrose_product_meta_nonce']) ||
        !wp_verify_nonce($_POST['skyyrose_product_meta_nonce'], 'skyyrose_product_meta')) {
        return;
    }

    if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) {
        return;
    }

    if (isset($_POST['skyyrose_collection'])) {
        update_post_meta($post_id, '_skyyrose_collection', sanitize_text_field($_POST['skyyrose_collection']));
    }

    if (isset($_POST['product_badge'])) {
        update_post_meta($post_id, '_product_badge', sanitize_text_field($_POST['product_badge']));
    }

    if (isset($_POST['fabric_composition'])) {
        update_post_meta($post_id, '_fabric_composition', sanitize_text_field($_POST['fabric_composition']));
    }

    if (isset($_POST['care_instructions'])) {
        update_post_meta($post_id, '_care_instructions', sanitize_textarea_field($_POST['care_instructions']));
    }

    if (isset($_POST['vault_preorder'])) {
        update_post_meta($post_id, '_vault_preorder', '1');
    } else {
        delete_post_meta($post_id, '_vault_preorder');
    }
}
add_action('save_post_product', 'skyyrose_save_product_meta');

/**
 * Security Hardening
 */

// Disable XML-RPC (prevents brute force and DDoS attacks)
add_filter('xmlrpc_enabled', '__return_false');

// Remove XML-RPC from HTTP headers
add_filter('wp_headers', function($headers) {
    unset($headers['X-Pingback']);
    return $headers;
});

// Block XML-RPC requests
add_filter('xmlrpc_methods', function($methods) {
    unset($methods['pingback.ping']);
    unset($methods['pingback.extensions.getPingbacks']);
    return $methods;
});

// Disable XML-RPC authentication
add_filter('authenticate', function($user, $username, $password) {
    if (isset($_SERVER['REQUEST_URI']) && strpos($_SERVER['REQUEST_URI'], 'xmlrpc.php') !== false) {
        return new WP_Error('xmlrpc_disabled', __('XML-RPC services are disabled on this site.'));
    }
    return $user;
}, 20, 3);

// Remove RSD link (used by XML-RPC)
remove_action('wp_head', 'rsd_link');

// Security headers
add_action('send_headers', function() {
    header('X-Content-Type-Options: nosniff');
    header('X-Frame-Options: SAMEORIGIN');
    header('X-XSS-Protection: 1; mode=block');
    header('Referrer-Policy: strict-origin-when-cross-origin');
    header('Permissions-Policy: geolocation=(), microphone=(), camera=()');
});

// Disable file editing in WordPress admin
if (!defined('DISALLOW_FILE_EDIT')) {
    define('DISALLOW_FILE_EDIT', true);
}

// Remove WordPress version from head
remove_action('wp_head', 'wp_generator');

// Disable REST API for unauthorized users (except WooCommerce and OAuth)
add_filter('rest_authentication_errors', function($result) {
    if (!empty($result)) {
        return $result;
    }

    // Allow WooCommerce REST API
    if (strpos($_SERVER['REQUEST_URI'], '/wc/') !== false) {
        return $result;
    }

    // Allow OAuth authentication
    if (isset($_SERVER['HTTP_AUTHORIZATION']) || isset($_GET['oauth_token'])) {
        return $result;
    }

    // Allow Basic Authentication (for API access)
    if (isset($_SERVER['PHP_AUTH_USER'])) {
        return $result;
    }

    // Allow logged-in users
    if (is_user_logged_in()) {
        return $result;
    }

    // Allow public endpoints (posts, pages - read-only)
    $public_routes = ['/wp/v2/posts', '/wp/v2/pages', '/wp/v2/media', '/wp/v2/categories', '/wp/v2/tags'];
    foreach ($public_routes as $route) {
        if (strpos($_SERVER['REQUEST_URI'], $route) !== false && $_SERVER['REQUEST_METHOD'] === 'GET') {
            return $result;
        }
    }

    // Block unauthenticated REST API access
    return new WP_Error('rest_disabled', __('REST API is disabled for unauthorized users.'), array('status' => 403));
});

// Limit login attempts (basic implementation)
add_action('wp_login_failed', function($username) {
    $ip = $_SERVER['REMOTE_ADDR'];
    $attempts_key = 'login_attempts_' . md5($ip);
    $attempts = get_transient($attempts_key) ?: 0;
    $attempts++;
    set_transient($attempts_key, $attempts, 15 * MINUTE_IN_SECONDS);

    if ($attempts >= 5) {
        wp_die(__('Too many failed login attempts. Please try again in 15 minutes.'), 403);
    }
});

// Reset login attempts on successful login
add_action('wp_login', function($username, $user) {
    $ip = $_SERVER['REMOTE_ADDR'];
    delete_transient('login_attempts_' . md5($ip));
}, 10, 2);

/**
 * WordPress.com API Rate Limit Handling
 */

// Cache API responses to reduce calls
function skyyrose_cache_api_response($endpoint, $callback, $expiration = HOUR_IN_SECONDS) {
    $cache_key = 'api_cache_' . md5($endpoint);
    $cached = get_transient($cache_key);

    if ($cached !== false) {
        return $cached;
    }

    $response = call_user_func($callback);
    set_transient($cache_key, $response, $expiration);

    return $response;
}

// Add rate limit retry logic for API calls
function skyyrose_api_request_with_retry($url, $args = [], $max_retries = 3) {
    $retry_count = 0;
    $retry_delay = 2; // seconds

    while ($retry_count < $max_retries) {
        $response = wp_remote_request($url, $args);

        // Check for rate limit error
        if (is_wp_error($response)) {
            $retry_count++;
            if ($retry_count < $max_retries) {
                sleep($retry_delay);
                $retry_delay *= 2; // Exponential backoff
                continue;
            }
            return $response;
        }

        $response_code = wp_remote_retrieve_response_code($response);

        // Rate limit hit (429) - retry with backoff
        if ($response_code === 429) {
            $retry_count++;
            if ($retry_count < $max_retries) {
                // Check for Retry-After header
                $retry_after = wp_remote_retrieve_header($response, 'retry-after');
                $wait_time = $retry_after ? intval($retry_after) : $retry_delay;
                sleep($wait_time);
                $retry_delay *= 2;
                continue;
            }
            return new WP_Error('rate_limit_exceeded', __('API rate limit exceeded. Please try again later.'));
        }

        // Success or other error - return response
        return $response;
    }

    return new WP_Error('max_retries_exceeded', __('Maximum API retry attempts exceeded.'));
}

// Optimize WooCommerce queries to reduce API calls
add_filter('woocommerce_product_query', function($q) {
    // Cache product queries
    $q->set('cache_results', true);
    $q->set('update_post_meta_cache', true);
    $q->set('update_post_term_cache', true);
    return $q;
});

// Add API request logging (for debugging rate limits)
add_action('http_api_debug', function($response, $context, $class, $args, $url) {
    if (defined('WP_DEBUG') && WP_DEBUG && defined('WP_DEBUG_LOG') && WP_DEBUG_LOG) {
        $log_entry = sprintf(
            "[%s] API Request: %s | Response Code: %s\n",
            current_time('mysql'),
            $url,
            is_wp_error($response) ? 'ERROR' : wp_remote_retrieve_response_code($response)
        );
        error_log($log_entry);
    }
}, 10, 5);
