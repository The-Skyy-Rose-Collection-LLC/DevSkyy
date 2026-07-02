<?php
/**
 * Fashion Chrome — Luxury streetwear UX refinements.
 *
 * Handles Cart→Bag gettext rewrite, cart-count badge AJAX fragment,
 * and shop archive column count.
 *
 * @package SkyyRose
 * @since   1.7.0
 */
defined( 'ABSPATH' ) || exit;

/**
 * Rewrite WooCommerce "Cart" → "Bag" throughout the storefront.
 *
 * Scoped to the woocommerce text domain so only WC strings are affected.
 *
 * @param string $translated Translated string.
 * @param string $text       Original source string.
 * @param string $domain     Text domain.
 * @return string
 */
function skyyrose_cart_to_bag_gettext( $translated, $text, $domain ) {
	if ( 'woocommerce' !== $domain ) {
		return $translated;
	}
	$map = array(
		'Cart'        => 'Bag',
		'Add to cart' => 'Add to Bag',
		'View cart'   => 'View Bag',
	);
	return isset( $map[ $text ] ) ? $map[ $text ] : $translated;
}
add_filter( 'gettext', 'skyyrose_cart_to_bag_gettext', 20, 3 );

// WooCommerce-dependent functionality — badge fragment + column count.
if ( class_exists( 'WooCommerce' ) ) :

	/**
	 * Push updated cart badge HTML into WooCommerce AJAX fragments.
	 *
	 * Targets .navbar__cart-badge so the badge refreshes without a page
	 * reload after add-to-cart.
	 *
	 * @param array $fragments Existing AJAX fragments.
	 * @return array
	 */
	function skyyrose_cart_badge_fragment( $fragments ) {
		if ( ! function_exists( 'WC' ) || ! WC()->cart ) {
			return $fragments;
		}
		$count       = WC()->cart->get_cart_contents_count();
		$badge_class = 'navbar__cart-badge' . ( $count > 0 ? ' navbar__cart-badge--visible' : '' );
		$fragments['.navbar__cart-badge'] = '<span class="' . esc_attr( $badge_class ) . '">' . esc_html( $count ) . '</span>';
		return $fragments;
	}
	add_filter( 'woocommerce_add_to_cart_fragments', 'skyyrose_cart_badge_fragment' );

	/**
	 * Shop archive — 3 columns for editorial density.
	 *
	 * Mirrors the product-grid.css three-column layout. WooCommerce uses
	 * this value to set the columns-N class on ul.products.
	 *
	 * @since  1.7.0
	 * @return int
	 */
	function skyyrose_loop_shop_columns() {
		return 3;
	}
	add_filter( 'loop_shop_columns', 'skyyrose_loop_shop_columns' );

endif;
