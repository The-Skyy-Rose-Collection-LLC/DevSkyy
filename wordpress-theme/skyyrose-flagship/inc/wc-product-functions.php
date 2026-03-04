<?php
/**
 * WooCommerce Product Functions — Elite Web Builder
 *
 * Collection detection via WooCommerce categories, display config (colors,
 * labels, fonts), custom meta fields for the WP admin product editor,
 * and single-product page asset loading with collection-aware theming.
 *
 * @package SkyyRose_Flagship
 * @since   4.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Detect which collection a WooCommerce product belongs to.
 *
 * Checks product categories (and parent categories) against known
 * collection slug variants. Used by the single-product template to
 * apply collection-specific visual theming.
 *
 * @since 4.0.0
 *
 * @param int|null $product_id Optional. Defaults to current post ID.
 * @return string Collection key: 'black-rose', 'love-hurts', 'signature', or 'default'.
 */
function skyyrose_get_product_collection( $product_id = null ) {
	$product_id = $product_id ? (int) $product_id : get_the_ID();
	$terms      = get_the_terms( $product_id, 'product_cat' );

	if ( ! $terms || is_wp_error( $terms ) ) {
		return 'default';
	}

	$collection_map = array(
		'black-rose' => array( 'black-rose', 'black_rose', 'blackrose' ),
		'love-hurts' => array( 'love-hurts', 'love_hurts', 'lovehurts' ),
		'signature'  => array( 'signature', 'sig', 'foundation' ),
	);

	foreach ( $terms as $term ) {
		foreach ( $collection_map as $collection => $slugs ) {
			if (
				in_array( $term->slug, $slugs, true ) ||
				false !== stripos( $term->name, str_replace( '-', ' ', $collection ) )
			) {
				return $collection;
			}
		}
		// Check parent categories too.
		if ( $term->parent ) {
			$parent = get_term( $term->parent, 'product_cat' );
			if ( $parent && ! is_wp_error( $parent ) ) {
				foreach ( $collection_map as $collection => $slugs ) {
					if ( in_array( $parent->slug, $slugs, true ) ) {
						return $collection;
					}
				}
			}
		}
	}

	return 'default';
}

/**
 * Get collection display configuration (colors, labels, fonts).
 *
 * Returns the full visual config for a collection key, used by
 * single-product pages and collection-aware templates.
 *
 * @since 4.0.0
 *
 * @param string $collection Collection key.
 * @return array Config array with accent, bg, label, tagline, body_class, etc.
 */
function skyyrose_collection_config( $collection ) {
	$configs = array(
		'black-rose' => array(
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
		),
		'love-hurts' => array(
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
		),
		'signature'  => array(
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
		),
	);

	return isset( $configs[ $collection ] ) ? $configs[ $collection ] : $configs['black-rose'];
}

/**
 * Get custom product meta fields for SkyyRose products.
 *
 * @since 4.0.0
 *
 * @param int|null $product_id Optional. Defaults to current post ID.
 * @return array Associative array of custom fields.
 */
function skyyrose_get_product_meta( $product_id = null ) {
	$product_id = $product_id ? (int) $product_id : get_the_ID();

	return array(
		'material'   => get_post_meta( $product_id, '_skyyrose_material', true ) ?: '',
		'fit'        => get_post_meta( $product_id, '_skyyrose_fit', true ) ?: '',
		'detail'     => get_post_meta( $product_id, '_skyyrose_detail', true ) ?: '',
		'care'       => get_post_meta( $product_id, '_skyyrose_care', true ) ?: '',
		'made_in'    => get_post_meta( $product_id, '_skyyrose_made_in', true ) ?: 'USA',
		'limited'    => get_post_meta( $product_id, '_skyyrose_limited', true ) ?: '',
		'edition_of' => get_post_meta( $product_id, '_skyyrose_edition_of', true ) ?: '',
	);
}

/**
 * Register custom product meta fields in WooCommerce product editor.
 *
 * @since 4.0.0
 * @return void
 */
function skyyrose_add_product_meta_fields() {
	echo '<div class="options_group">';
	echo '<h4 style="padding-left:12px;color:#B76E79;">' . esc_html__( 'SkyyRose Product Details', 'skyyrose-flagship' ) . '</h4>';

	woocommerce_wp_text_input( array(
		'id'          => '_skyyrose_material',
		'label'       => esc_html__( 'Material', 'skyyrose-flagship' ),
		'placeholder' => 'e.g. 380gsm Cotton Fleece',
		'desc_tip'    => true,
		'description' => esc_html__( 'Primary material composition', 'skyyrose-flagship' ),
	) );
	woocommerce_wp_text_input( array(
		'id'          => '_skyyrose_fit',
		'label'       => esc_html__( 'Fit', 'skyyrose-flagship' ),
		'placeholder' => 'e.g. Oversized, Tailored, Relaxed',
	) );
	woocommerce_wp_text_input( array(
		'id'          => '_skyyrose_detail',
		'label'       => esc_html__( 'Signature Detail', 'skyyrose-flagship' ),
		'placeholder' => 'e.g. Silver thorn zipper pulls',
	) );
	woocommerce_wp_textarea_input( array(
		'id'          => '_skyyrose_care',
		'label'       => esc_html__( 'Care Instructions', 'skyyrose-flagship' ),
		'placeholder' => 'Cold wash, hang dry...',
	) );
	woocommerce_wp_text_input( array(
		'id'          => '_skyyrose_made_in',
		'label'       => esc_html__( 'Made In', 'skyyrose-flagship' ),
		'placeholder' => 'USA',
	) );
	woocommerce_wp_text_input( array(
		'id'          => '_skyyrose_limited',
		'label'       => esc_html__( 'Limited Edition?', 'skyyrose-flagship' ),
		'placeholder' => 'yes or leave blank',
	) );
	woocommerce_wp_text_input( array(
		'id'          => '_skyyrose_edition_of',
		'label'       => esc_html__( 'Edition Size', 'skyyrose-flagship' ),
		'placeholder' => 'e.g. 100',
		'type'        => 'number',
	) );

	wp_nonce_field( 'skyyrose_product_meta', 'skyyrose_product_meta_nonce' );
	echo '</div>';
}
add_action( 'woocommerce_product_options_general_product_data', 'skyyrose_add_product_meta_fields' );

/**
 * Save custom product meta fields.
 *
 * Verifies our own nonce as defense-in-depth (WooCommerce also checks its
 * nonce before firing `woocommerce_process_product_meta`).
 *
 * @since 4.0.0
 *
 * @param int $post_id Product post ID.
 * @return void
 */
function skyyrose_save_product_meta_fields( $post_id ) {
	if ( ! isset( $_POST['skyyrose_product_meta_nonce'] ) ||
	     ! wp_verify_nonce( sanitize_text_field( wp_unslash( $_POST['skyyrose_product_meta_nonce'] ) ), 'skyyrose_product_meta' ) ) {
		return;
	}

	$fields = array(
		'_skyyrose_material',
		'_skyyrose_fit',
		'_skyyrose_detail',
		'_skyyrose_care',
		'_skyyrose_made_in',
		'_skyyrose_limited',
		'_skyyrose_edition_of',
	);

	foreach ( $fields as $field ) {
		if ( isset( $_POST[ $field ] ) ) {
			update_post_meta( $post_id, $field, sanitize_text_field( wp_unslash( $_POST[ $field ] ) ) );
		}
	}
}
add_action( 'woocommerce_process_product_meta', 'skyyrose_save_product_meta_fields' );

/**
 * Get related products from the same WooCommerce category.
 *
 * Unlike `skyyrose_get_collection_products()` in product-catalog.php which
 * takes a collection slug and queries the static catalog, this function
 * queries WooCommerce directly by the product's assigned categories.
 *
 * @since 4.0.0
 *
 * @param int|null $product_id Current product ID. Defaults to current post.
 * @param int      $limit      Number of related products to return.
 * @return array Array of WC_Product objects.
 */
function skyyrose_get_related_products_by_category( $product_id = null, $limit = 4 ) {
	$product_id = $product_id ? (int) $product_id : get_the_ID();
	$terms      = get_the_terms( $product_id, 'product_cat' );

	if ( ! $terms || is_wp_error( $terms ) ) {
		return array();
	}

	$cat_ids = wp_list_pluck( $terms, 'term_id' );

	$args = array(
		'post_type'      => 'product',
		'posts_per_page' => $limit,
		'post__not_in'   => array( $product_id ),
		'post_status'    => 'publish',
		'tax_query'      => array( // phpcs:ignore WordPress.DB.SlowDBQuery
			array(
				'taxonomy' => 'product_cat',
				'field'    => 'term_id',
				'terms'    => $cat_ids,
			),
		),
		'orderby'        => 'menu_order date',
		'order'          => 'ASC',
	);

	$query    = new WP_Query( $args );
	$products = array();

	foreach ( $query->posts as $post ) {
		$products[] = wc_get_product( $post->ID );
	}

	wp_reset_postdata();
	return $products;
}

/**
 * Localize single product page script with collection config.
 *
 * CSS/JS enqueue is handled by the template-based system in enqueue.php.
 * This function adds the collection-aware data (colors, AJAX URL, nonce)
 * that JavaScript needs for collection theming and cart interactions.
 *
 * @since 4.0.0
 * @return void
 */
function skyyrose_localize_product_data() {
	if ( ! function_exists( 'is_product' ) || ! is_product() ) {
		return;
	}

	// Handle matches the template system: 'skyyrose-template-' + filename stem.
	$handle = 'skyyrose-template-single-product';

	$collection = skyyrose_get_product_collection();
	$config     = skyyrose_collection_config( $collection );

	wp_localize_script( $handle, 'skyyrose', array(
		'ajax_url'   => admin_url( 'admin-ajax.php' ),
		'nonce'      => wp_create_nonce( 'skyyrose-nonce' ),
		'collection' => $collection,
		'config'     => $config,
		'cart_url'   => function_exists( 'wc_get_cart_url' ) ? wc_get_cart_url() : home_url( '/cart/' ),
	) );
}
add_action( 'wp_enqueue_scripts', 'skyyrose_localize_product_data', 25 );

/**
 * Add collection-specific body class on single product pages.
 *
 * @since 4.0.0
 *
 * @param array $classes Existing body classes.
 * @return array Modified classes.
 */
function skyyrose_product_body_class( $classes ) {
	if ( function_exists( 'is_product' ) && is_product() ) {
		$collection = skyyrose_get_product_collection();
		$config     = skyyrose_collection_config( $collection );
		$classes[]  = $config['body_class'];
		$classes[]  = 'skyyrose-product';
	}
	return $classes;
}
add_filter( 'body_class', 'skyyrose_product_body_class' );
