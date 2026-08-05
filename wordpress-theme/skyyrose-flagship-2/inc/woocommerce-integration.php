<?php
/**
 * Hook-first WooCommerce integration for the flagship commerce shell.
 *
 * @package SkyyRoseFlagship2
 */

defined( 'ABSPATH' ) || exit;

/**
 * Resolve the canonical collection represented by a product.
 *
 * WooCommerce taxonomy remains the authority. This helper only maps an
 * attached product category to the theme's registered collection world.
 *
 * @param int $product_id Product ID.
 * @return string
 */
function skyyrose2_product_collection_slug( $product_id ) {
	if ( ! function_exists( 'skyyrose2_collections' ) ) {
		return '';
	}

	foreach ( array_keys( skyyrose2_collections() ) as $collection_slug ) {
		$term_slugs = array(
			$collection_slug,
			str_replace( '-', '_', $collection_slug ),
			str_replace( '-', '', $collection_slug ),
		);

		if ( has_term( $term_slugs, 'product_cat', $product_id ) ) {
			return $collection_slug;
		}
	}

	return '';
}

/**
 * Replace WooCommerce presentation defaults while preserving public hooks.
 *
 * The flagship templates own their breadcrumb, archive heading, and sidebar
 * presentation. Their public actions still fire so extensions can integrate.
 *
 * @return void
 */
function skyyrose2_configure_woocommerce_hooks() {
	remove_action( 'woocommerce_before_main_content', 'woocommerce_output_content_wrapper', 10 );
	remove_action( 'woocommerce_before_main_content', 'woocommerce_breadcrumb', 20 );
	remove_action( 'woocommerce_after_main_content', 'woocommerce_output_content_wrapper_end', 10 );
	remove_action( 'woocommerce_shop_loop_header', 'woocommerce_product_taxonomy_archive_header', 10 );
	remove_action( 'woocommerce_sidebar', 'woocommerce_get_sidebar', 10 );

	add_action( 'woocommerce_before_main_content', 'skyyrose2_woocommerce_wrapper_start', 10 );
	add_action( 'woocommerce_after_main_content', 'skyyrose2_woocommerce_wrapper_end', 10 );
}
add_action( 'wp', 'skyyrose2_configure_woocommerce_hooks' );

/**
 * Open the semantic flagship commerce shell.
 *
 * @return void
 */
function skyyrose2_woocommerce_wrapper_start() {
	$classes    = array( 'sr2-commerce' );
	$attributes = '';

	if ( function_exists( 'is_product' ) && is_product() ) {
		$classes[]       = 'sr2-product-page';
		$collection_slug = skyyrose2_product_collection_slug( get_queried_object_id() );
		if ( $collection_slug ) {
			$attributes = ' data-collection="' . esc_attr( $collection_slug ) . '"';
		}
	} elseif ( ( function_exists( 'is_shop' ) && is_shop() ) || ( function_exists( 'is_product_taxonomy' ) && is_product_taxonomy() ) ) {
		$classes[] = 'sr2-shop';
	}

	printf(
		'<main id="primary" class="%1$s"%2$s>',
		esc_attr( implode( ' ', $classes ) ),
		$attributes // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- Constructed from escaped theme-owned values.
	);
}

/**
 * Close the semantic flagship commerce shell.
 *
 * @return void
 */
function skyyrose2_woocommerce_wrapper_end() {
	echo '</main>';
}
