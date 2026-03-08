<?php
/**
 * SkyyRose WooCommerce Product Functions
 * 
 * Collection detection, structured data helpers, custom meta fields.
 * Included from functions.php
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

defined('ABSPATH') || exit;

/**
 * Detect which collection a product belongs to.
 * Checks product categories for collection slugs.
 *
 * @param int|null $product_id Optional. Defaults to current post.
 * @return string Collection key: 'black-rose', 'love-hurts', 'signature', or 'default'
 */
function skyyrose_get_product_collection($product_id = null) {
    $product_id = $product_id ?: get_the_ID();
    $terms = get_the_terms($product_id, 'product_cat');
    
    if (!$terms || is_wp_error($terms)) {
        return 'default';
    }

    $collection_map = [
        'black-rose'  => ['black-rose', 'black_rose', 'blackrose'],
        'love-hurts'  => ['love-hurts', 'love_hurts', 'lovehurts'],
        'signature'   => ['signature', 'sig', 'foundation'],
    ];

    foreach ($terms as $term) {
        foreach ($collection_map as $collection => $slugs) {
            if (in_array($term->slug, $slugs, true) || 
                stripos($term->name, str_replace('-', ' ', $collection)) !== false) {
                return $collection;
            }
        }
        // Check parent categories too
        if ($term->parent) {
            $parent = get_term($term->parent, 'product_cat');
            if ($parent && !is_wp_error($parent)) {
                foreach ($collection_map as $collection => $slugs) {
                    if (in_array($parent->slug, $slugs, true)) {
                        return $collection;
                    }
                }
            }
        }
    }

    return 'default';
}

/**
 * Get collection display config (colors, labels, fonts).
 *
 * @param string $collection Collection key.
 * @return array Config array with accent, bg, label, tagline, etc.
 */
function skyyrose_collection_config($collection) {
    $configs = [
        'black-rose' => [
            'accent'     => '#C0C0C0',
            'accent_rgb' => '192,192,192',
            'bg'         => '#000000',
            'bg_alt'     => '#050505',
            'text'       => '#FFFFFF',
            'dim'        => '#8A8A8A',
            'label'      => 'BLACK ROSE',
            'tagline'    => 'For those who found power in the dark.',
            'badge_text' => 'Collection 01',
            'nav_font'   => "'Cinzel', serif",
            'body_class' => 'collection-black-rose',
            'gradient'   => 'linear-gradient(135deg, #444, #888, #C0C0C0)',
            'cta_color'  => '#000000',
        ],
        'love-hurts' => [
            'accent'     => '#DC143C',
            'accent_rgb' => '220,20,60',
            'bg'         => '#0C0206',
            'bg_alt'     => '#0A0105',
            'text'       => '#FFFFFF',
            'dim'        => 'rgba(255,180,180,.35)',
            'label'      => 'LOVE HURTS',
            'tagline'    => 'Wear your heart. Own your scars.',
            'badge_text' => 'Collection 02',
            'nav_font'   => "'Playfair Display', serif",
            'body_class' => 'collection-love-hurts',
            'gradient'   => 'linear-gradient(135deg, #8B0000, #DC143C, #E91E63)',
            'cta_color'  => '#FFFFFF',
        ],
        'signature' => [
            'accent'     => '#D4AF37',
            'accent_rgb' => '212,175,55',
            'bg'         => '#0A0804',
            'bg_alt'     => '#080602',
            'text'       => '#F5E6D3',
            'dim'        => 'rgba(245,230,211,.3)',
            'label'      => 'SIGNATURE',
            'tagline'    => 'The foundation of any wardrobe worth building.',
            'badge_text' => 'Collection 03',
            'nav_font'   => "'Cinzel', serif",
            'body_class' => 'collection-signature',
            'gradient'   => 'linear-gradient(135deg, #8B7020, #D4AF37, #F5E6D3)',
            'cta_color'  => '#0A0804',
        ],
    ];

    return $configs[$collection] ?? $configs['black-rose'];
}

/**
 * Get custom product meta fields for SkyyRose products.
 *
 * @param int|null $product_id
 * @return array Associative array of custom fields.
 */
function skyyrose_get_product_meta($product_id = null) {
    $product_id = $product_id ?: get_the_ID();
    
    return [
        'material'   => get_post_meta($product_id, '_skyyrose_material', true) ?: '',
        'fit'        => get_post_meta($product_id, '_skyyrose_fit', true) ?: '',
        'detail'     => get_post_meta($product_id, '_skyyrose_detail', true) ?: '',
        'care'       => get_post_meta($product_id, '_skyyrose_care', true) ?: '',
        'made_in'    => get_post_meta($product_id, '_skyyrose_made_in', true) ?: 'USA',
        'limited'    => get_post_meta($product_id, '_skyyrose_limited', true) ?: '',
        'edition_of' => get_post_meta($product_id, '_skyyrose_edition_of', true) ?: '',
    ];
}

/**
 * Register custom product meta fields in WooCommerce product editor.
 */
function skyyrose_add_product_meta_fields() {
    global $post;

    echo '<div class="options_group">';
    echo '<h4 style="padding-left:12px;color:#B76E79;">SkyyRose Product Details</h4>';

    woocommerce_wp_text_input([
        'id'          => '_skyyrose_material',
        'label'       => 'Material',
        'placeholder' => 'e.g. 380gsm Cotton Fleece',
        'desc_tip'    => true,
        'description' => 'Primary material composition',
    ]);
    woocommerce_wp_text_input([
        'id'          => '_skyyrose_fit',
        'label'       => 'Fit',
        'placeholder' => 'e.g. Oversized, Tailored, Relaxed',
    ]);
    woocommerce_wp_text_input([
        'id'          => '_skyyrose_detail',
        'label'       => 'Signature Detail',
        'placeholder' => 'e.g. Silver thorn zipper pulls',
    ]);
    woocommerce_wp_textarea_input([
        'id'          => '_skyyrose_care',
        'label'       => 'Care Instructions',
        'placeholder' => 'Cold wash, hang dry...',
    ]);
    woocommerce_wp_text_input([
        'id'          => '_skyyrose_made_in',
        'label'       => 'Made In',
        'placeholder' => 'USA',
    ]);
    woocommerce_wp_text_input([
        'id'          => '_skyyrose_limited',
        'label'       => 'Limited Edition?',
        'placeholder' => 'yes or leave blank',
    ]);
    woocommerce_wp_text_input([
        'id'          => '_skyyrose_edition_of',
        'label'       => 'Edition Size',
        'placeholder' => 'e.g. 100',
        'type'        => 'number',
    ]);

    echo '</div>';
}
add_action('woocommerce_product_options_general_product_data', 'skyyrose_add_product_meta_fields');

/**
 * Save custom product meta fields.
 */
function skyyrose_save_product_meta_fields($post_id) {
    $fields = [
        '_skyyrose_material', '_skyyrose_fit', '_skyyrose_detail',
        '_skyyrose_care', '_skyyrose_made_in', '_skyyrose_limited',
        '_skyyrose_edition_of',
    ];

    foreach ($fields as $field) {
        if (isset($_POST[$field])) {
            update_post_meta($post_id, $field, sanitize_text_field($_POST[$field]));
        }
    }
}
add_action('woocommerce_process_product_meta', 'skyyrose_save_product_meta_fields');

/**
 * Get related products from the same collection.
 *
 * @param int   $product_id  Current product ID.
 * @param int   $limit       Number of related products.
 * @return array Array of WC_Product objects.
 */
function skyyrose_get_collection_products($product_id = null, $limit = 4) {
    $product_id = $product_id ?: get_the_ID();
    $terms = get_the_terms($product_id, 'product_cat');
    
    if (!$terms || is_wp_error($terms)) {
        return [];
    }

    $cat_ids = wp_list_pluck($terms, 'term_id');

    $args = [
        'post_type'      => 'product',
        'posts_per_page' => $limit,
        'post__not_in'   => [$product_id],
        'post_status'    => 'publish',
        'tax_query'      => [
            [
                'taxonomy' => 'product_cat',
                'field'    => 'term_id',
                'terms'    => $cat_ids,
            ],
        ],
        'orderby' => 'menu_order date',
        'order'   => 'ASC',
    ];

    $query = new WP_Query($args);
    $products = [];

    foreach ($query->posts as $post) {
        $products[] = wc_get_product($post->ID);
    }

    wp_reset_postdata();
    return $products;
}

/**
 * Output JSON-LD structured data for product.
 */
function skyyrose_product_schema() {
    if (!is_product()) return;

    global $product;
    $meta = skyyrose_get_product_meta($product->get_id());
    $image = wp_get_attachment_url($product->get_image_id());

    $schema = [
        '@context'    => 'https://schema.org',
        '@type'       => 'Product',
        'name'        => $product->get_name(),
        'description' => wp_strip_all_tags($product->get_short_description()),
        'image'       => $image ?: '',
        'sku'         => $product->get_sku(),
        'brand'       => [
            '@type' => 'Brand',
            'name'  => 'SkyyRose',
        ],
        'offers'      => [
            '@type'           => 'Offer',
            'url'             => get_permalink(),
            'priceCurrency'   => get_woocommerce_currency(),
            'price'           => $product->get_price(),
            'availability'    => $product->is_in_stock()
                ? 'https://schema.org/InStock'
                : 'https://schema.org/PreOrder',
            'itemCondition'   => 'https://schema.org/NewCondition',
            'seller'          => [
                '@type' => 'Organization',
                'name'  => 'SkyyRose LLC',
            ],
        ],
    ];

    if ($meta['material']) {
        $schema['material'] = $meta['material'];
    }

    echo '<script type="application/ld+json">' . wp_json_encode($schema, JSON_UNESCAPED_SLASHES) . '</script>' . "\n";
}
add_action('wp_head', 'skyyrose_product_schema');

/**
 * Enqueue single product page assets.
 */
function skyyrose_enqueue_product_assets() {
    if (!is_product()) return;

    wp_enqueue_style(
        'skyyrose-single-product',
        get_template_directory_uri() . '/assets/css/single-product.css',
        [],
        filemtime(get_template_directory() . '/assets/css/single-product.css')
    );

    wp_enqueue_script(
        'skyyrose-single-product',
        get_template_directory_uri() . '/assets/js/single-product.js',
        ['jquery', 'wc-add-to-cart-variation'],
        filemtime(get_template_directory() . '/assets/js/single-product.js'),
        true
    );

    // Pass collection config to JS
    $collection = skyyrose_get_product_collection();
    $config = skyyrose_collection_config($collection);

    wp_localize_script('skyyrose-single-product', 'skyyrose', [
        'ajax_url'   => admin_url('admin-ajax.php'),
        'nonce'      => wp_create_nonce('skyyrose-nonce'),
        'collection' => $collection,
        'config'     => $config,
        'cart_url'   => wc_get_cart_url(),
    ]);
}
add_action('wp_enqueue_scripts', 'skyyrose_enqueue_product_assets');

/**
 * Add collection body class.
 */
function skyyrose_product_body_class($classes) {
    if (is_product()) {
        $collection = skyyrose_get_product_collection();
        $config = skyyrose_collection_config($collection);
        $classes[] = $config['body_class'];
        $classes[] = 'skyyrose-product';
    }
    return $classes;
}
add_filter('body_class', 'skyyrose_product_body_class');
