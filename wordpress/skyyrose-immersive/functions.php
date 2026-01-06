<?php
/**
 * SkyyRose Immersive Child Theme Functions
 *
 * Provides immersive 3D experiences for collection pages using Three.js WebGL
 *
 * @package SkyyRose_Immersive
 * @version 1.0.0
 */

defined('ABSPATH') || exit;

// Theme constants
define('SKYYROSE_IMMERSIVE_VERSION', '1.0.0');
define('SKYYROSE_IMMERSIVE_DIR', get_stylesheet_directory());
define('SKYYROSE_IMMERSIVE_URI', get_stylesheet_directory_uri());

/**
 * Enqueue parent and child theme styles
 */
add_action('wp_enqueue_scripts', 'skyyrose_immersive_enqueue_styles', 10);
function skyyrose_immersive_enqueue_styles() {
    // Parent theme style
    wp_enqueue_style(
        'shoptimizer-parent-style',
        get_template_directory_uri() . '/style.css',
        array(),
        wp_get_theme()->parent()->get('Version')
    );

    // Child theme style
    wp_enqueue_style(
        'skyyrose-immersive-style',
        get_stylesheet_uri(),
        array('shoptimizer-parent-style'),
        SKYYROSE_IMMERSIVE_VERSION
    );

    // Immersive experience styles
    wp_enqueue_style(
        'skyyrose-immersive-experiences',
        SKYYROSE_IMMERSIVE_URI . '/assets/css/immersive.css',
        array('skyyrose-immersive-style'),
        SKYYROSE_IMMERSIVE_VERSION
    );

    // Google Fonts for luxury typography
    wp_enqueue_style(
        'skyyrose-fonts',
        'https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,400&family=Montserrat:wght@300;400;500;600&family=Playfair+Display:ital,wght@0,400;0,600;1,400&display=swap',
        array(),
        null
    );
}

/**
 * Register Three.js and experience scripts (ES Module approach)
 */
add_action('wp_enqueue_scripts', 'skyyrose_immersive_register_scripts', 5);
function skyyrose_immersive_register_scripts() {
    // Three.js core library
    wp_register_script(
        'threejs',
        'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js',
        array(),
        '0.160.0',
        true
    );

    // Three.js addons (OrbitControls, GLTFLoader, etc.)
    wp_register_script(
        'threejs-orbit-controls',
        SKYYROSE_IMMERSIVE_URI . '/assets/js/lib/OrbitControls.js',
        array('threejs'),
        '0.160.0',
        true
    );

    wp_register_script(
        'threejs-gltf-loader',
        SKYYROSE_IMMERSIVE_URI . '/assets/js/lib/GLTFLoader.js',
        array('threejs'),
        '0.160.0',
        true
    );

    wp_register_script(
        'threejs-draco-loader',
        SKYYROSE_IMMERSIVE_URI . '/assets/js/lib/DRACOLoader.js',
        array('threejs'),
        '0.160.0',
        true
    );

    wp_register_script(
        'threejs-hdr-loader',
        SKYYROSE_IMMERSIVE_URI . '/assets/js/lib/RGBELoader.js',
        array('threejs'),
        '0.160.0',
        true
    );

    wp_register_script(
        'threejs-postprocessing',
        SKYYROSE_IMMERSIVE_URI . '/assets/js/lib/postprocessing.js',
        array('threejs'),
        '0.160.0',
        true
    );

    // Base experience class
    wp_register_script(
        'skyyrose-experience-base',
        SKYYROSE_IMMERSIVE_URI . '/assets/js/experience-base.js',
        array('threejs', 'threejs-orbit-controls', 'threejs-gltf-loader'),
        SKYYROSE_IMMERSIVE_VERSION,
        true
    );

    // Collection-specific experiences
    wp_register_script(
        'skyyrose-signature-experience',
        SKYYROSE_IMMERSIVE_URI . '/assets/js/signature-experience.js',
        array('skyyrose-experience-base'),
        SKYYROSE_IMMERSIVE_VERSION,
        true
    );

    wp_register_script(
        'skyyrose-lovehurts-experience',
        SKYYROSE_IMMERSIVE_URI . '/assets/js/lovehurts-experience.js',
        array('skyyrose-experience-base'),
        SKYYROSE_IMMERSIVE_VERSION,
        true
    );

    wp_register_script(
        'skyyrose-blackrose-experience',
        SKYYROSE_IMMERSIVE_URI . '/assets/js/blackrose-experience.js',
        array('skyyrose-experience-base'),
        SKYYROSE_IMMERSIVE_VERSION,
        true
    );

    // Mannequin bust for product display
    wp_register_script(
        'skyyrose-mannequin-bust',
        SKYYROSE_IMMERSIVE_URI . '/assets/js/mannequin-bust.js',
        array('threejs'),
        SKYYROSE_IMMERSIVE_VERSION,
        true
    );

    // Main initialization script
    wp_register_script(
        'skyyrose-3d-init',
        SKYYROSE_IMMERSIVE_URI . '/assets/js/init-3d.js',
        array('skyyrose-experience-base', 'skyyrose-mannequin-bust'),
        SKYYROSE_IMMERSIVE_VERSION,
        true
    );

    // Localize script with theme data
    wp_localize_script('skyyrose-3d-init', 'skyyrose3D', array(
        'ajaxUrl' => admin_url('admin-ajax.php'),
        'themeUri' => SKYYROSE_IMMERSIVE_URI,
        'assetsUri' => SKYYROSE_IMMERSIVE_URI . '/assets',
        'modelsUri' => SKYYROSE_IMMERSIVE_URI . '/assets/models',
        'texturesUri' => SKYYROSE_IMMERSIVE_URI . '/assets/textures',
        'nonce' => wp_create_nonce('skyyrose_3d_nonce'),
        'isMobile' => wp_is_mobile(),
    ));
}

/**
 * Check if Elementor is active
 */
function skyyrose_is_elementor_active() {
    return did_action('elementor/loaded');
}

/**
 * Register Elementor widgets
 */
add_action('elementor/widgets/register', 'skyyrose_register_elementor_widgets');
function skyyrose_register_elementor_widgets($widgets_manager) {
    require_once SKYYROSE_IMMERSIVE_DIR . '/widgets/class-threejs-viewer-widget.php';
    require_once SKYYROSE_IMMERSIVE_DIR . '/widgets/class-collection-hero-widget.php';

    $widgets_manager->register(new \SkyyRose_ThreeJS_Viewer_Widget());
    $widgets_manager->register(new \SkyyRose_Collection_Hero_Widget());
}

/**
 * Register Elementor widget category
 */
add_action('elementor/elements/categories_registered', 'skyyrose_add_elementor_category');
function skyyrose_add_elementor_category($elements_manager) {
    $elements_manager->add_category(
        'skyyrose',
        array(
            'title' => __('SkyyRose', 'skyyrose-immersive'),
            'icon' => 'eicon-site-logo',
        )
    );
}

/**
 * Enqueue scripts for Elementor frontend
 */
add_action('elementor/frontend/after_register_scripts', 'skyyrose_elementor_scripts');
function skyyrose_elementor_scripts() {
    // Scripts are already registered, just need to be enqueued when widget is used
}

/**
 * Add body classes for collection pages
 */
add_filter('body_class', 'skyyrose_collection_body_class');
function skyyrose_collection_body_class($classes) {
    if (is_page()) {
        $page_id = get_the_ID();
        $page_slug = get_post_field('post_name', $page_id);

        // Add collection-specific classes
        $collections = array('signature', 'love-hurts', 'lovehurts', 'black-rose', 'blackrose');
        foreach ($collections as $collection) {
            if (strpos($page_slug, $collection) !== false) {
                $classes[] = 'collection-page';
                $classes[] = 'collection-' . str_replace('-', '', $collection);
                $classes[] = 'has-3d-experience';
                break;
            }
        }
    }

    return $classes;
}

/**
 * Register custom page templates
 */
add_filter('theme_page_templates', 'skyyrose_register_page_templates');
function skyyrose_register_page_templates($templates) {
    $templates['templates/template-signature.php'] = __('Signature Collection (Immersive)', 'skyyrose-immersive');
    $templates['templates/template-lovehurts.php'] = __('Love Hurts Collection (Immersive)', 'skyyrose-immersive');
    $templates['templates/template-blackrose.php'] = __('Black Rose Collection (Immersive)', 'skyyrose-immersive');

    return $templates;
}

/**
 * Load custom page templates
 */
add_filter('template_include', 'skyyrose_load_page_template');
function skyyrose_load_page_template($template) {
    if (is_page()) {
        $page_template = get_page_template_slug();

        if ($page_template && file_exists(SKYYROSE_IMMERSIVE_DIR . '/' . $page_template)) {
            return SKYYROSE_IMMERSIVE_DIR . '/' . $page_template;
        }
    }

    return $template;
}

/**
 * Add theme support
 */
add_action('after_setup_theme', 'skyyrose_immersive_setup');
function skyyrose_immersive_setup() {
    // Add custom logo support
    add_theme_support('custom-logo', array(
        'height' => 100,
        'width' => 400,
        'flex-height' => true,
        'flex-width' => true,
    ));

    // Add custom image sizes for 3D thumbnails
    add_image_size('skyyrose-3d-thumb', 600, 600, true);
    add_image_size('skyyrose-hero', 1920, 1080, true);
}

/**
 * AJAX handler for loading 3D model data
 */
add_action('wp_ajax_skyyrose_get_model_data', 'skyyrose_get_model_data');
add_action('wp_ajax_nopriv_skyyrose_get_model_data', 'skyyrose_get_model_data');
function skyyrose_get_model_data() {
    // Capture any stray output (PHP warnings, errors, etc.)
    ob_start();

    // Verify nonce with graceful JSON error instead of wp_die()
    if (!wp_verify_nonce($_POST['nonce'] ?? '', 'skyyrose_3d_nonce')) {
        ob_end_clean();
        wp_send_json_error(['message' => 'Invalid security token'], 403);
        return;
    }

    // Check for any unexpected output before sending JSON
    $stray_output = ob_get_clean();
    if (!empty($stray_output)) {
        error_log('SkyyRose AJAX: Unexpected output captured: ' . substr($stray_output, 0, 500));
    }

    $product_id = intval($_POST['product_id'] ?? 0);

    if (!$product_id) {
        wp_send_json_error(['message' => 'Invalid product ID'], 400);
        return;
    }

    $model_url = get_post_meta($product_id, '_3d_model_url', true);
    $model_scale = get_post_meta($product_id, '_3d_model_scale', true) ?: 1;
    $model_rotation = get_post_meta($product_id, '_3d_model_rotation', true) ?: array(0, 0, 0);

    wp_send_json_success(array(
        'modelUrl' => $model_url,
        'scale' => floatval($model_scale),
        'rotation' => $model_rotation,
    ));
}

/**
 * Add Three.js import map for ESM modules
 */
add_action('wp_head', 'skyyrose_add_importmap', 1);
function skyyrose_add_importmap() {
    ?>
    <script type="importmap">
    {
        "imports": {
            "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
            "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"
        }
    }
    </script>
    <?php
}

/**
 * Preload critical 3D assets
 */
add_action('wp_head', 'skyyrose_preload_3d_assets');
function skyyrose_preload_3d_assets() {
    if (!is_page()) return;

    $page_slug = get_post_field('post_name', get_the_ID());

    // Preload Three.js for collection pages
    if (strpos($page_slug, 'signature') !== false ||
        strpos($page_slug, 'love-hurts') !== false ||
        strpos($page_slug, 'black-rose') !== false) {
        ?>
        <link rel="modulepreload" href="https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js">
        <?php
    }
}

/**
 * Add structured data for 3D products
 */
add_action('wp_head', 'skyyrose_3d_structured_data');
function skyyrose_3d_structured_data() {
    if (!is_product()) return;

    global $product;

    // Ensure $product is a valid WC_Product object (sometimes it's a string slug)
    if (!$product instanceof WC_Product) {
        $product = wc_get_product(get_the_ID());
    }

    // Bail if we still don't have a valid product
    if (!$product || !($product instanceof WC_Product)) {
        return;
    }

    $model_url = get_post_meta($product->get_id(), '_3d_model_url', true);

    if (!$model_url) return;

    $structured_data = array(
        '@context' => 'https://schema.org',
        '@type' => 'Product',
        'name' => $product->get_name(),
        'image' => wp_get_attachment_url($product->get_image_id()),
        'model' => $model_url,
        'offers' => array(
            '@type' => 'Offer',
            'price' => $product->get_price(),
            'priceCurrency' => get_woocommerce_currency(),
        ),
    );

    echo '<script type="application/ld+json">' . wp_json_encode($structured_data) . '</script>';
}

/**
 * Defer non-critical Three.js scripts for better page load performance
 */
add_filter('script_loader_tag', 'skyyrose_modify_script_tags', 10, 2);
function skyyrose_modify_script_tags($tag, $handle) {
    // Defer non-critical scripts
    $defer_scripts = array(
        'threejs',
        'threejs-orbit-controls',
        'threejs-gltf-loader',
        'skyyrose-experience-base',
        'skyyrose-signature-experience',
        'skyyrose-lovehurts-experience',
        'skyyrose-blackrose-experience',
    );

    if (in_array($handle, $defer_scripts)) {
        return str_replace(' src', ' defer src', $tag);
    }

    return $tag;
}

// Include additional functionality
require_once SKYYROSE_IMMERSIVE_DIR . '/inc/elementor-widgets.php';
require_once SKYYROSE_IMMERSIVE_DIR . '/inc/spinning-logo-functions.php';

/**
 * Universal AJAX JSON Response Sanitizer
 *
 * Plugins like CommerceKit, reCAPTCHA, and others can wrap JSON responses in HTML
 * tags (<p>, <div>, etc.) which causes JSON.parse() errors on the client side.
 *
 * This filter intercepts ALL AJAX responses and strips HTML wrappers if present.
 *
 * Root cause analysis sources:
 * - Mike Jolley (WooCommerce Lead): https://mikejolley.com/2015/11/12/debugging-unexpected-token-in-woocommerce-2-4/
 * - Zack Katz (GravityView): https://katz.co/7671/
 * - WordPress.org Support: https://wordpress.org/support/topic/added-to-json-response/
 */
add_action('init', 'skyyrose_universal_ajax_json_sanitizer', 1);
function skyyrose_universal_ajax_json_sanitizer() {
    // Only process AJAX requests (catches ALL WordPress AJAX, not just specific plugins)
    if (!defined('DOING_AJAX') || !DOING_AJAX) {
        return;
    }

    // Start output buffering to capture any plugin interference
    ob_start(function($output) {
        $trimmed = trim($output);

        // Check for common HTML wrapper patterns that break JSON
        // Handles: <p>...</p>, <div>...</div>, <span>...</span>, etc.
        if (preg_match('/^<[a-z]+[^>]*>(.*)<\/[a-z]+>$/is', $trimmed, $matches)) {
            $potential_json = trim($matches[1]);

            // Verify the inner content is valid JSON before returning
            if ($potential_json && json_decode($potential_json) !== null) {
                return $potential_json;
            }
        }

        // Also handle leading junk before JSON (PHP warnings, notices, etc.)
        // Per Zack Katz: strip characters preceding the opening { or [
        if (preg_match('/^[^{\[]*([{\[].*[}\]])$/s', $trimmed, $matches)) {
            $potential_json = $matches[1];

            // Verify it's valid JSON
            if (json_decode($potential_json) !== null) {
                // Log that we had to clean the response (for debugging)
                error_log('SkyyRose AJAX Sanitizer: Cleaned junk from JSON response');
                return $potential_json;
            }
        }

        // If not valid JSON or no HTML wrapper detected, return original
        return $output;
    });

    // Ensure buffer is flushed on shutdown
    add_action('shutdown', function() {
        if (ob_get_level() > 0) {
            ob_end_flush();
        }
    }, 0);
}

/**
 * =============================================================================
 * SHORTCODE REGISTRATIONS
 * =============================================================================
 */

/**
 * Shortcode: [skyyrose_3d_viewer]
 * Parameters: model_url, product_id, height (500px), auto_rotate (true), background (#1A1A1A)
 */
add_shortcode('skyyrose_3d_viewer', 'skyyrose_3d_viewer_shortcode');
function skyyrose_3d_viewer_shortcode($atts) {
    $atts = shortcode_atts(array(
        'model_url' => '',
        'product_id' => 0,
        'height' => '500px',
        'auto_rotate' => 'true',
        'background' => '#1A1A1A',
    ), $atts, 'skyyrose_3d_viewer');

    $model_url = $atts['model_url'];
    if (empty($model_url) && $atts['product_id']) {
        $model_url = get_post_meta(intval($atts['product_id']), '_skyyrose_glb_url', true);
    }
    if (empty($model_url)) return '<div class="skyyrose-3d-error">No 3D model URL</div>';

    wp_enqueue_script('threejs');
    wp_enqueue_script('threejs-orbit-controls');
    wp_enqueue_script('threejs-gltf-loader');
    wp_enqueue_script('skyyrose-3d-init');

    $id = 'viewer-' . uniqid();
    $rotate = filter_var($atts['auto_rotate'], FILTER_VALIDATE_BOOLEAN);

    return '<div id="' . esc_attr($id) . '" class="skyyrose-3d-container" style="height:' . esc_attr($atts['height']) . ';background:' . esc_attr($atts['background']) . ';" data-model-url="' . esc_url($model_url) . '" data-auto-rotate="' . ($rotate ? 'true' : 'false') . '"><div class="skyyrose-3d-loading"><div class="skyyrose-spinner"></div></div><canvas class="skyyrose-3d-canvas"></canvas><div class="skyyrose-3d-controls">Drag to rotate | Scroll to zoom</div></div>';
}

/**
 * Shortcode: [skyyrose_virtual_tryon]
 * Parameters: product_id (required), category (tops)
 */
add_shortcode('skyyrose_virtual_tryon', 'skyyrose_virtual_tryon_shortcode');
function skyyrose_virtual_tryon_shortcode($atts) {
    $atts = shortcode_atts(array('product_id' => 0, 'category' => 'tops'), $atts, 'skyyrose_virtual_tryon');
    $product_id = intval($atts['product_id']);
    if (!$product_id) return '<div class="skyyrose-tryon-error">Product ID required</div>';

    $product = wc_get_product($product_id);
    if (!$product) return '<div class="skyyrose-tryon-error">Product not found</div>';

    $id = 'tryon-' . uniqid();
    return '<div id="' . esc_attr($id) . '" class="skyyrose-virtual-tryon" data-product-id="' . esc_attr($product_id) . '" data-category="' . esc_attr($atts['category']) . '"><div class="tryon-header"><h3>Virtual Try-On: ' . esc_html($product->get_name()) . '</h3><p>' . $product->get_price_html() . '</p></div><div class="tryon-upload-area"><input type="file" id="' . esc_attr($id) . '-input" accept="image/*" class="tryon-file-input"><label for="' . esc_attr($id) . '-input" class="tryon-upload-label"><span class="tryon-icon">📷</span><span>Upload your photo</span></label></div><div class="tryon-result" style="display:none;"></div><button class="tryon-generate-btn" style="display:none;">Generate Try-On</button></div>';
}

/**
 * Shortcode: [skyyrose_collection_experience]
 * Parameters: collection (signature|black_rose|love_hurts), height (800px), enable_bloom, enable_ar, enable_audio, products_api
 */
add_shortcode('skyyrose_collection_experience', 'skyyrose_collection_experience_shortcode');
function skyyrose_collection_experience_shortcode($atts) {
    $atts = shortcode_atts(array(
        'collection' => 'signature',
        'height' => '800px',
        'enable_bloom' => 'true',
        'enable_ar' => 'true',
        'enable_audio' => 'false',
        'products_api' => '',
    ), $atts, 'skyyrose_collection_experience');

    $collection = sanitize_key($atts['collection']);
    if (!in_array($collection, array('signature', 'black_rose', 'love_hurts'))) $collection = 'signature';

    wp_enqueue_script('threejs');
    wp_enqueue_script('threejs-orbit-controls');
    wp_enqueue_script('threejs-gltf-loader');
    wp_enqueue_script('threejs-postprocessing');
    wp_enqueue_script('skyyrose-experience-base');
    wp_enqueue_script('skyyrose-' . str_replace('_', '', $collection) . '-experience');

    $id = 'experience-' . $collection . '-' . uniqid();
    $bloom = filter_var($atts['enable_bloom'], FILTER_VALIDATE_BOOLEAN);
    $ar = filter_var($atts['enable_ar'], FILTER_VALIDATE_BOOLEAN);
    $audio = filter_var($atts['enable_audio'], FILTER_VALIDATE_BOOLEAN);
    $api = !empty($atts['products_api']) ? $atts['products_api'] : rest_url('wc/v3/products?category=' . $collection);

    return '<div id="' . esc_attr($id) . '" class="skyyrose-collection-experience collection-' . esc_attr($collection) . '" style="height:' . esc_attr($atts['height']) . ';" data-collection="' . esc_attr($collection) . '" data-enable-bloom="' . ($bloom ? 'true' : 'false') . '" data-enable-ar="' . ($ar ? 'true' : 'false') . '" data-enable-audio="' . ($audio ? 'true' : 'false') . '" data-products-api="' . esc_url($api) . '"><div class="experience-loading"><div class="loading-spinner"></div><span>Entering ' . esc_html(ucwords(str_replace('_', ' ', $collection))) . ' Experience...</span></div><canvas class="experience-canvas"></canvas><div class="experience-ui"><div class="product-hotspots"></div>' . ($ar ? '<button class="ar-button">📱 View in AR</button>' : '') . '</div><div class="experience-instructions">Drag to explore | Click products | Scroll to zoom</div></div>';
}

/**
 * Shortcode styles
 */
add_action('wp_head', 'skyyrose_shortcode_styles');
function skyyrose_shortcode_styles() {
    echo '<style>
    .skyyrose-3d-container,.skyyrose-collection-experience{position:relative;width:100%;border-radius:12px;overflow:hidden}
    .skyyrose-3d-canvas,.experience-canvas{width:100%;height:100%;display:block}
    .skyyrose-3d-loading,.experience-loading{position:absolute;top:0;left:0;right:0;bottom:0;display:flex;flex-direction:column;align-items:center;justify-content:center;background:inherit;color:#B76E79;z-index:10}
    .skyyrose-spinner,.loading-spinner{width:50px;height:50px;border:3px solid rgba(183,110,121,0.3);border-top-color:#B76E79;border-radius:50%;animation:spin 1s linear infinite;margin-bottom:10px}
    @keyframes spin{to{transform:rotate(360deg)}}
    .skyyrose-3d-controls,.experience-instructions{position:absolute;bottom:15px;left:50%;transform:translateX(-50%);background:rgba(0,0,0,0.7);color:#fff;padding:8px 16px;border-radius:20px;font-size:12px}
    .skyyrose-virtual-tryon{background:#1a1a1a;border-radius:12px;padding:20px;color:#fff}
    .tryon-header h3{color:#B76E79;margin:0 0 5px}
    .tryon-upload-area{border:2px dashed rgba(183,110,121,0.5);border-radius:8px;padding:40px;text-align:center;margin:20px 0;cursor:pointer}
    .tryon-file-input{display:none}.tryon-icon{font-size:48px;display:block;margin-bottom:10px}
    .tryon-generate-btn,.ar-button{background:#B76E79;color:#fff;border:none;padding:12px 24px;border-radius:6px;cursor:pointer;font-weight:600}
    .ar-button{position:absolute;bottom:80px;right:20px;border-radius:25px;display:flex;align-items:center;gap:8px}
    .collection-signature{--accent:#D4AF37}.collection-black_rose{--accent:#722F37}.collection-love_hurts{--accent:#DC143C}
    </style>';
}
