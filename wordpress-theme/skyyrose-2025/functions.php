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
 * Enqueue Scripts & Styles
 */
function skyyrose_enqueue_assets() {
    // Styles
    wp_enqueue_style('skyyrose-style', get_stylesheet_uri(), [], SKYYROSE_VERSION);
    wp_enqueue_style('skyyrose-fonts', 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@400;700&display=swap', [], null);

    // Scripts
    wp_enqueue_script('gsap', 'https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js', [], '3.12.5', true);
    wp_enqueue_script('gsap-scrolltrigger', 'https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/ScrollTrigger.min.js', ['gsap'], '3.12.5', true);
    wp_enqueue_script('three', 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js', [], '0.160.0', true);
    wp_enqueue_script('three-gltf', 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/loaders/GLTFLoader.js', ['three'], '0.160.0', true);
    wp_enqueue_script('three-orbit', 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/controls/OrbitControls.js', ['three'], '0.160.0', true);

    // Theme scripts
    wp_enqueue_script('skyyrose-animations', SKYYROSE_THEME_URL . '/assets/js/animations.js', ['gsap', 'gsap-scrolltrigger'], SKYYROSE_VERSION, true);
    wp_enqueue_script('skyyrose-3d-viewer', SKYYROSE_THEME_URL . '/assets/js/3d-viewer.js', ['three'], SKYYROSE_VERSION, true);
    wp_enqueue_script('skyyrose-main', SKYYROSE_THEME_URL . '/assets/js/main.js', ['jquery'], SKYYROSE_VERSION, true);

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
