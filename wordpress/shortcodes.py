"""
WordPress Shortcode Generator
=============================

Generate WordPress shortcode PHP snippets for SkyyRose features.

Features:
- 3D Product Viewer shortcode
- Virtual Try-On shortcode
- Product Gallery shortcode

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations


def generate_3d_viewer_shortcode() -> str:
    """Generate PHP code for the SkyyRose 3D Viewer shortcode.

    Add this to your theme's functions.php or a custom plugin.

    Usage in WordPress: [skyyrose_3d_viewer model_url="https://..." height="500"]
    """
    return '''<?php
/**
 * SkyyRose 3D Product Viewer Shortcode
 *
 * Usage: [skyyrose_3d_viewer model_url="https://..." product_id="123" height="500"]
 */
function skyyrose_3d_viewer_shortcode($atts) {
    $atts = shortcode_atts(array(
        'model_url' => '',
        'product_id' => '',
        'height' => '500',
        'auto_rotate' => 'true',
        'background' => '#1A1A1A',
    ), $atts, 'skyyrose_3d_viewer');

    // Get model URL from product meta if not provided
    if (empty($atts['model_url']) && !empty($atts['product_id'])) {
        $atts['model_url'] = get_post_meta($atts['product_id'], '_skyyrose_3d_model_url', true);
    }

    if (empty($atts['model_url'])) {
        return '<p class="skyyrose-error">No 3D model URL provided.</p>';
    }

    $viewer_id = 'skyyrose-viewer-' . uniqid();
    $height = intval($atts['height']);

    ob_start();
    ?>
    <div id="<?php echo esc_attr($viewer_id); ?>"
         class="skyyrose-3d-viewer"
         data-model-url="<?php echo esc_url($atts['model_url']); ?>"
         data-auto-rotate="<?php echo esc_attr($atts['auto_rotate']); ?>"
         style="height: <?php echo $height; ?>px; background: <?php echo esc_attr($atts['background']); ?>;">
        <canvas class="viewer-canvas"></canvas>
        <div class="loading-overlay">
            <div class="loading-spinner"></div>
            <div class="loading-text">Loading 3D Model...</div>
        </div>
    </div>
    <?php
    return ob_get_clean();
}
add_shortcode('skyyrose_3d_viewer', 'skyyrose_3d_viewer_shortcode');

/**
 * Enqueue Three.js scripts for 3D viewer
 */
function skyyrose_enqueue_3d_viewer_scripts() {
    global $post;

    // Only load on pages with the shortcode
    if (is_a($post, 'WP_Post') && has_shortcode($post->post_content, 'skyyrose_3d_viewer')) {
        wp_enqueue_script(
            'three-js',
            'https://unpkg.com/three@0.160.0/build/three.module.js',
            array(),
            '0.160.0',
            true
        );

        wp_enqueue_script(
            'skyyrose-3d-viewer',
            get_template_directory_uri() . '/js/skyyrose-3d-viewer.js',
            array('three-js'),
            '1.0.0',
            true
        );

        wp_enqueue_style(
            'skyyrose-3d-viewer-style',
            get_template_directory_uri() . '/css/skyyrose-3d-viewer.css',
            array(),
            '1.0.0'
        );
    }
}
add_action('wp_enqueue_scripts', 'skyyrose_enqueue_3d_viewer_scripts');

/**
 * Add 3D model URL meta box to WooCommerce products
 */
function skyyrose_add_3d_model_meta_box() {
    add_meta_box(
        'skyyrose_3d_model',
        'SkyyRose 3D Model',
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
        <label for="skyyrose_3d_model_url">GLB/GLTF Model URL:</label>
        <input type="url" id="skyyrose_3d_model_url" name="skyyrose_3d_model_url"
               value="<?php echo esc_url($model_url); ?>" class="widefat">
    </p>
    <p class="description">Upload 3D model to Media Library or paste external URL.</p>
    <?php
}

function skyyrose_save_3d_model_meta($post_id) {
    if (!isset($_POST['skyyrose_3d_model_nonce']) ||
        !wp_verify_nonce($_POST['skyyrose_3d_model_nonce'], 'skyyrose_3d_model_nonce')) {
        return;
    }
    if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) return;
    if (!current_user_can('edit_post', $post_id)) return;

    if (isset($_POST['skyyrose_3d_model_url'])) {
        update_post_meta($post_id, '_skyyrose_3d_model_url',
                        esc_url_raw($_POST['skyyrose_3d_model_url']));
    }
}
add_action('save_post_product', 'skyyrose_save_3d_model_meta');
?>'''


def generate_virtual_tryon_shortcode() -> str:
    """Generate PHP code for the Virtual Try-On shortcode."""
    return '''<?php
/**
 * SkyyRose Virtual Try-On Shortcode
 *
 * Usage: [skyyrose_virtual_tryon product_id="123"]
 */
function skyyrose_virtual_tryon_shortcode($atts) {
    $atts = shortcode_atts(array(
        'product_id' => '',
        'category' => 'tops',
    ), $atts, 'skyyrose_virtual_tryon');

    if (empty($atts['product_id'])) {
        return '<p class="skyyrose-error">Product ID required.</p>';
    }

    $product = wc_get_product($atts['product_id']);
    if (!$product) {
        return '<p class="skyyrose-error">Product not found.</p>';
    }

    $garment_image = wp_get_attachment_url($product->get_image_id());
    $widget_id = 'skyyrose-tryon-' . uniqid();

    ob_start();
    ?>
    <div id="<?php echo esc_attr($widget_id); ?>" class="skyyrose-virtual-tryon"
         data-product-id="<?php echo esc_attr($atts['product_id']); ?>"
         data-garment-image="<?php echo esc_url($garment_image); ?>"
         data-category="<?php echo esc_attr($atts['category']); ?>">
        <div class="tryon-upload-area">
            <p>Upload your photo to try on this item</p>
            <input type="file" accept="image/*" class="tryon-file-input">
            <button class="tryon-generate-btn">Generate Try-On</button>
        </div>
        <div class="tryon-result" style="display: none;">
            <img class="tryon-result-image" src="" alt="Virtual Try-On Result">
        </div>
    </div>
    <?php
    return ob_get_clean();
}
add_shortcode('skyyrose_virtual_tryon', 'skyyrose_virtual_tryon_shortcode');
?>'''


def generate_collection_experience_shortcode() -> str:
    """Generate PHP code for the SkyyRose Collection 3D Experience shortcode.

    Embeds immersive 3D collection landing pages.
    Usage: [skyyrose_collection_experience collection="black_rose" height="800"]
    """
    return '''<?php
/**
 * SkyyRose Collection 3D Experience Shortcode
 *
 * Usage: [skyyrose_collection_experience collection="black_rose" height="800"]
 * Collections: black_rose, signature, love_hurts
 */
function skyyrose_collection_experience_shortcode($atts) {
    $atts = shortcode_atts(array(
        'collection' => 'black_rose',
        'height' => '800',
        'enable_bloom' => 'true',
        'enable_audio' => 'false',
        'enable_ar' => 'true',
        'products_api' => '',
    ), $atts, 'skyyrose_collection_experience');

    $valid_collections = array('black_rose', 'signature', 'love_hurts');
    if (!in_array($atts['collection'], $valid_collections)) {
        return '<p class="skyyrose-error">Invalid collection. Use: black_rose, signature, or love_hurts</p>';
    }

    $container_id = 'skyyrose-collection-' . uniqid();
    $height = intval($atts['height']);

    // Get products from WooCommerce if API not specified
    $products_json = '[]';
    if (empty($atts['products_api'])) {
        $collection_tag = str_replace('_', '-', $atts['collection']);
        $products = wc_get_products(array(
            'tag' => array($collection_tag),
            'limit' => 20,
            'status' => 'publish',
        ));

        $products_data = array();
        foreach ($products as $product) {
            $products_data[] = array(
                'id' => $product->get_id(),
                'name' => $product->get_name(),
                'price' => floatval($product->get_price()),
                'thumbnailUrl' => wp_get_attachment_url($product->get_image_id()),
                'modelUrl' => get_post_meta($product->get_id(), '_skyyrose_3d_model_url', true),
            );
        }
        $products_json = json_encode($products_data);
    }

    ob_start();
    ?>
    <div id="<?php echo esc_attr($container_id); ?>"
         class="skyyrose-collection-experience"
         data-collection="<?php echo esc_attr($atts['collection']); ?>"
         data-enable-bloom="<?php echo esc_attr($atts['enable_bloom']); ?>"
         data-enable-audio="<?php echo esc_attr($atts['enable_audio']); ?>"
         data-enable-ar="<?php echo esc_attr($atts['enable_ar']); ?>"
         style="height: <?php echo $height; ?>px; width: 100%; position: relative;">
        <div class="loading-overlay">
            <div class="loading-spinner"></div>
            <div class="loading-text">Loading <?php echo ucwords(str_replace('_', ' ', $atts['collection'])); ?> Experience...</div>
        </div>
    </div>
    <script type="module">
        import { createCollectionExperience } from '<?php echo get_template_directory_uri(); ?>/js/collections/index.js';

        const container = document.getElementById('<?php echo esc_js($container_id); ?>');
        const products = <?php echo $products_json; ?>;

        const experience = createCollectionExperience(container, {
            collection: '<?php echo esc_js($atts['collection']); ?>',
            config: {
                enableBloom: <?php echo $atts['enable_bloom'] === 'true' ? 'true' : 'false'; ?>,
            },
            products: products,
            interactivity: {
                enableProductCards: true,
                enableCategoryNavigation: true,
                enableSpatialAudio: <?php echo $atts['enable_audio'] === 'true' ? 'true' : 'false'; ?>,
                enableARPreview: <?php echo $atts['enable_ar'] === 'true' ? 'true' : 'false'; ?>,
                cursorSpotlight: true,
            },
            fallback: {
                enable2DParallax: true,
                lowPerformanceThreshold: 30,
            },
        });

        experience.loadProducts(products).then(() => {
            container.querySelector('.loading-overlay').style.display = 'none';
            experience.start();
        });

        // Product click handler
        experience.setOnProductClick?.((product) => {
            window.location.href = '<?php echo home_url('/product/'); ?>' + product.id;
        });
    </script>
    <?php
    return ob_get_clean();
}
add_shortcode('skyyrose_collection_experience', 'skyyrose_collection_experience_shortcode');

/**
 * Enqueue collection experience scripts
 */
function skyyrose_enqueue_collection_scripts() {
    global $post;

    if (is_a($post, 'WP_Post') && has_shortcode($post->post_content, 'skyyrose_collection_experience')) {
        wp_enqueue_script(
            'three-js',
            'https://unpkg.com/three@0.160.0/build/three.module.js',
            array(),
            '0.160.0',
            true
        );

        wp_enqueue_style(
            'skyyrose-collection-style',
            get_template_directory_uri() . '/css/skyyrose-collection.css',
            array(),
            '1.0.0'
        );
    }
}
add_action('wp_enqueue_scripts', 'skyyrose_enqueue_collection_scripts');
?>'''


# Export shortcode generator functions
__all__ = [
    "generate_3d_viewer_shortcode",
    "generate_virtual_tryon_shortcode",
    "generate_collection_experience_shortcode",
]

