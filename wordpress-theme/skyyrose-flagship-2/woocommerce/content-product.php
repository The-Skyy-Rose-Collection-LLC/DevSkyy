<?php
/**
 * Product loop card override.
 *
 * Keeps WooCommerce's loop contract while delegating visual hierarchy to the
 * shared card used on editorial collection and home product sections.
 *
 * @package SkyyRoseFlagship2
 * @version 9.4.0
 */

defined( 'ABSPATH' ) || exit;

global $product;

if ( ! $product instanceof WC_Product || ! $product->is_visible() ) {
	return;
}

$loop_index = (int) wc_get_loop_prop( 'loop' );
$eager_card = ( is_shop() || is_product_taxonomy() )
	&& in_the_loop()
	&& $loop_index >= 1
	&& $loop_index <= 4;
?>
<li <?php wc_product_class( 'sr2-product-card-item', $product ); ?>>
	<?php
	$loop_defaults = array(
		array( 'woocommerce_before_shop_loop_item', 'woocommerce_template_loop_product_link_open', 10 ),
		array( 'woocommerce_before_shop_loop_item_title', 'woocommerce_show_product_loop_sale_flash', 10 ),
		array( 'woocommerce_before_shop_loop_item_title', 'woocommerce_template_loop_product_thumbnail', 10 ),
		array( 'woocommerce_shop_loop_item_title', 'woocommerce_template_loop_product_title', 10 ),
		array( 'woocommerce_after_shop_loop_item_title', 'woocommerce_template_loop_rating', 5 ),
		array( 'woocommerce_after_shop_loop_item_title', 'woocommerce_template_loop_price', 10 ),
		array( 'woocommerce_after_shop_loop_item', 'woocommerce_template_loop_product_link_close', 5 ),
		array( 'woocommerce_after_shop_loop_item', 'woocommerce_template_loop_add_to_cart', 10 ),
	);
	$removed_loop_defaults = array();
	foreach ( $loop_defaults as $loop_default ) {
		if ( false !== has_action( $loop_default[0], $loop_default[1] ) && remove_action( $loop_default[0], $loop_default[1], $loop_default[2] ) ) {
			$removed_loop_defaults[] = $loop_default;
		}
	}

	// Fire the public WooCommerce loop contract while the shared card supplies
	// core image, title, price, link, and add-to-cart markup exactly once.
	do_action( 'woocommerce_before_shop_loop_item' );
	do_action( 'woocommerce_before_shop_loop_item_title' );

	get_template_part(
		'template-parts/product-card',
		null,
		array(
			'product'        => $product,
			'image_loading'  => $eager_card ? 'eager' : 'lazy',
			'image_priority' => $eager_card && 1 === $loop_index,
		)
	);

	do_action( 'woocommerce_shop_loop_item_title' );
	do_action( 'woocommerce_after_shop_loop_item_title' );
	do_action( 'woocommerce_after_shop_loop_item' );

	foreach ( $removed_loop_defaults as $loop_default ) {
		add_action( $loop_default[0], $loop_default[1], $loop_default[2] );
	}
	?>
</li>
