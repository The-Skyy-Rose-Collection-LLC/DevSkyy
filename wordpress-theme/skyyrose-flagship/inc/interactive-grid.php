<?php
/**
 * Interactive Product Grid
 *
 * Helper functions for rendering the interactive product card grid.
 * Discovers available render images per product and delegates to
 * the interactive-product-card and preorder-reveal-card template parts.
 *
 * @package SkyyRose_Flagship
 * @since   4.1.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Get available render images for a product.
 *
 * @since  4.1.0
 * @param  string $sku Product SKU.
 * @return array Associative array of available views => URLs.
 */
function skyyrose_get_product_render_images( $sku ) {
	$views  = array( 'front', 'back', 'branding' );
	$images = array();
	$base   = '/assets/images/products/';

	foreach ( $views as $view ) {
		$filename = $sku . '-render-' . $view . '.webp';
		if ( file_exists( SKYYROSE_DIR . $base . $filename ) ) {
			$images[ $view ] = SKYYROSE_ASSETS_URI . '/images/products/' . $filename;
		}
	}
	return $images;
}

/**
 * Render an interactive product grid.
 *
 * @since 4.1.0
 * @param array $products         Array of product data arrays.
 * @param array $collection_config Collection configuration.
 * @return void
 */
function skyyrose_render_interactive_grid( $products, $collection_config ) {
	if ( empty( $products ) || ! is_array( $products ) ) {
		return;
	}

	$col = wp_parse_args( $collection_config, array(
		'slug'       => '',
		'name'       => '',
		'accent'     => '#C0C0C0',
		'accent_rgb' => '192, 192, 192',
	) );

	echo '<div class="ipc-grid" data-collection="' . esc_attr( $col['slug'] ) . '">';

	foreach ( $products as $product ) {
		$sku    = isset( $product['sku'] ) ? $product['sku'] : '';
		$images = skyyrose_get_product_render_images( $sku );

		// Normalize catalog fields → template fields.
		$normalized = $product;
		if ( ! isset( $normalized['desc'] ) && isset( $normalized['description'] ) ) {
			$normalized['desc'] = $normalized['description'];
		}
		if ( empty( $normalized['url'] ) && function_exists( 'skyyrose_product_url' ) ) {
			$normalized['url'] = skyyrose_product_url( $sku );
		}
		if ( empty( $normalized['price_display'] ) && function_exists( 'skyyrose_format_price' ) ) {
			$normalized['price_display'] = skyyrose_format_price( $product );
		}

		get_template_part( 'template-parts/interactive-product-card', null, array(
			'product'    => $normalized,
			'images'     => $images,
			'collection' => $col,
		) );
	}

	echo '</div>';

	if ( wp_script_is( 'skyyrose-interactive-cards', 'enqueued' ) ) {
		wp_add_inline_script(
			'skyyrose-interactive-cards',
			'window.skyyRoseCollectionProducts = ' . wp_json_encode( $products, JSON_HEX_TAG | JSON_UNESCAPED_SLASHES ) . ';',
			'before'
		);
	}
}

/**
 * Render a pre-order reveal card grid.
 *
 * @since  4.1.0
 * @param  array  $products         Array of product data arrays.
 * @param  array  $collection_config Collection config.
 * @param  string $reveal_at        ISO 8601 UTC timestamp for reveal.
 * @return void
 */
function skyyrose_render_preorder_grid( $products, $collection_config, $reveal_at = '' ) {
	if ( empty( $products ) || ! is_array( $products ) ) {
		return;
	}

	$preorder_products = array_filter( $products, function ( $p ) {
		return ! empty( $p['is_preorder'] );
	} );

	if ( empty( $preorder_products ) ) {
		return;
	}

	$col = wp_parse_args( $collection_config, array(
		'slug'       => '',
		'name'       => '',
		'accent'     => '#B76E79',
		'accent_rgb' => '183, 110, 121',
	) );

	echo '<div class="ipc-grid ipc-grid--preorder" data-collection="' . esc_attr( $col['slug'] ) . '">';

	foreach ( $preorder_products as $product ) {
		// Normalize catalog fields → template fields.
		$normalized = $product;
		if ( ! isset( $normalized['desc'] ) && isset( $normalized['description'] ) ) {
			$normalized['desc'] = $normalized['description'];
		}
		if ( empty( $normalized['url'] ) && function_exists( 'skyyrose_product_url' ) ) {
			$normalized['url'] = skyyrose_product_url( isset( $product['sku'] ) ? $product['sku'] : '' );
		}
		if ( empty( $normalized['price_display'] ) && function_exists( 'skyyrose_format_price' ) ) {
			$normalized['price_display'] = skyyrose_format_price( $product );
		}

		get_template_part( 'template-parts/preorder-reveal-card', null, array(
			'product'    => $normalized,
			'collection' => $col,
			'reveal_at'  => $reveal_at,
		) );
	}

	echo '</div>';
}

/**
 * Enqueue interactive product card assets.
 *
 * @since  4.1.0
 * @return void
 */
function skyyrose_enqueue_interactive_cards() {
	if ( ! function_exists( 'skyyrose_get_current_template_slug' ) ) {
		return;
	}

	$slug         = skyyrose_get_current_template_slug();
	$target_slugs = array( 'collection-v4', 'collection', 'preorder-gateway', 'immersive', 'shop-archive' );

	if ( ! in_array( $slug, $target_slugs, true ) ) {
		return;
	}

	$use_min = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;
	$css_dir = SKYYROSE_DIR . '/assets/css';
	$css_uri = SKYYROSE_ASSETS_URI . '/css';
	$js_dir  = SKYYROSE_DIR . '/assets/js';
	$js_uri  = SKYYROSE_ASSETS_URI . '/js';

	$css_file = $use_min && file_exists( $css_dir . '/interactive-cards.min.css' )
		? 'interactive-cards.min.css' : 'interactive-cards.css';
	if ( file_exists( $css_dir . '/' . $css_file ) ) {
		wp_enqueue_style(
			'skyyrose-interactive-cards',
			$css_uri . '/' . $css_file,
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	$js_file = $use_min && file_exists( $js_dir . '/interactive-cards.min.js' )
		? 'interactive-cards.min.js' : 'interactive-cards.js';
	if ( file_exists( $js_dir . '/' . $js_file ) ) {
		wp_enqueue_script(
			'skyyrose-interactive-cards',
			$js_uri . '/' . $js_file,
			array(),
			SKYYROSE_VERSION,
			true
		);

		wp_localize_script( 'skyyrose-interactive-cards', 'skyyRoseCards', array(
			'nonce'    => wp_create_nonce( 'skyyrose-immersive-nonce' ),
			'wcActive' => class_exists( 'WooCommerce' ),
		) );
	}
}
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_interactive_cards', 35 );
