<?php
/**
 * V7 lookbook product-card data loader.
 *
 * Single source: data/v7-cards.json — generated from the asset hub manifest,
 * verdict:verified ONLY (see feedback_real_products_only). Never resolves
 * product imagery from the legacy catalog image columns.
 *
 * @package SkyyRose
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Load and cache the verified V7 card map (keyed by SKU).
 *
 * @return array<string,array>
 */
function skyyrose_v7_cards() {
	static $cards = null;
	if ( null !== $cards ) {
		return $cards;
	}
	$cards = array();
	$file  = get_theme_file_path( 'data/v7-cards.json' );
	if ( ! is_readable( $file ) ) {
		return $cards;
	}
	$json = json_decode( (string) file_get_contents( $file ), true ); // phpcs:ignore WordPress.WP.AlternativeFunctions.file_get_contents_file_get_contents -- local theme asset.
	if ( ! is_array( $json ) || empty( $json['cards'] ) || ! is_array( $json['cards'] ) ) {
		return $cards;
	}
	foreach ( $json['cards'] as $card ) {
		if ( ! empty( $card['sku'] ) ) {
			$cards[ $card['sku'] ] = $card;
		}
	}
	return $cards;
}

/**
 * Look up one verified V7 card by SKU (variant suffix stripped).
 *
 * @param string $sku Product SKU.
 * @return array|null
 */
function skyyrose_v7_card( $sku ) {
	if ( empty( $sku ) ) {
		return null;
	}
	$sku   = function_exists( 'skyyrose_normalize_sku' ) ? skyyrose_normalize_sku( $sku ) : $sku;
	$cards = skyyrose_v7_cards();
	return isset( $cards[ $sku ] ) ? $cards[ $sku ] : null;
}

/**
 * Human label for a collection slug. Single source of truth =
 * skyyrose_get_collections_config() (i18n labels).
 *
 * @param string $collection Collection slug.
 * @return string
 */
function skyyrose_v7_coll_label( $collection ) {
	if ( function_exists( 'skyyrose_get_collections_config' ) ) {
		$cfg = skyyrose_get_collections_config();
		if ( isset( $cfg[ $collection ]['label'] ) ) {
			return $cfg[ $collection ]['label'];
		}
	}
	return ucwords( str_replace( '-', ' ', (string) $collection ) );
}

/**
 * Collection-logo backdrop URI (falls back to the rose-gold monogram).
 *
 * @param string $collection Collection slug.
 * @return string Theme URI or empty string.
 */
function skyyrose_v7_lockup_uri( $collection ) {
	$collection = sanitize_title( (string) $collection );
	$rel        = 'assets/images/products/v7/_lockups/' . $collection . '.webp';
	if ( $collection && is_readable( get_theme_file_path( $rel ) ) ) {
		return get_theme_file_uri( $rel );
	}
	$mono = 'assets/images/logos/sr-monogram-rose-gold.webp';
	return is_readable( get_theme_file_path( $mono ) ) ? get_theme_file_uri( $mono ) : '';
}

/**
 * Is the current request a surface where V7 cards are styled + scripted?
 * The card-type filter and the asset enqueue MUST share this guard, or v7
 * markup renders unstyled on WooCommerce-native surfaces (related products,
 * up-sells, [products] shortcode, cart) that fall outside the allowlist.
 *
 * @return bool
 */
function skyyrose_v7_is_active_surface() {
	if ( ! function_exists( 'skyyrose_get_current_template_slug' ) ) {
		return false;
	}
	static $active = null;
	if ( null === $active ) {
		$active = in_array(
			skyyrose_get_current_template_slug(),
			array( 'collection-standalone', 'front-page', 'shop-archive', 'preorder-gateway', 'search', 'landing' ),
			true
		);
	}
	return $active;
}

/**
 * Enqueue V7 card assets on active surfaces. Serves .min in production.
 *
 * @return void
 */
function skyyrose_v7_enqueue() {
	if ( ! skyyrose_v7_is_active_surface() ) {
		return;
	}
	$use_min = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;
	$css_dir = get_theme_file_path( 'assets/css' );
	$css_uri = get_theme_file_uri( 'assets/css' );
	$js_dir  = get_theme_file_path( 'assets/js' );
	$js_uri  = get_theme_file_uri( 'assets/js' );

	$css = ( $use_min && file_exists( $css_dir . '/product-card-v7.min.css' ) ) ? 'product-card-v7.min.css' : 'product-card-v7.css';
	if ( file_exists( $css_dir . '/' . $css ) ) {
		wp_enqueue_style( 'skyyrose-product-card-v7', $css_uri . '/' . $css, array(), SKYYROSE_VERSION );
	}
	$js = ( $use_min && file_exists( $js_dir . '/product-card-v7.min.js' ) ) ? 'product-card-v7.min.js' : 'product-card-v7.js';
	if ( file_exists( $js_dir . '/' . $js ) ) {
		wp_enqueue_script( 'skyyrose-product-card-v7', $js_uri . '/' . $js, array(), SKYYROSE_VERSION, true );
	}
}
add_action( 'wp_enqueue_scripts', 'skyyrose_v7_enqueue', 20 );

/**
 * Activate the V7 lookbook card for product grids on active surfaces only
 * (falls back to holo per-SKU inside the template when no verified data exists).
 *
 * @param string $type Default card type.
 * @return string
 */
function skyyrose_v7_card_type( $type ) {
	return skyyrose_v7_is_active_surface() ? 'v7-lookbook' : $type;
}
add_filter( 'skyyrose_product_card_type', 'skyyrose_v7_card_type' );
