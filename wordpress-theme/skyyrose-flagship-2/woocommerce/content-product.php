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
	/**
	 * Fires before the Flagship 2 product-card markup.
	 *
	 * @param WC_Product $product Product being rendered.
	 */
	do_action( 'skyyrose2_before_product_card', $product );

	get_template_part(
		'template-parts/product-card',
		null,
		array(
			'product'        => $product,
			'image_loading'  => $eager_card ? 'eager' : 'lazy',
			'image_priority' => $eager_card && 1 === $loop_index,
		)
	);

	/**
	 * Fires after the Flagship 2 product-card markup.
	 *
	 * @param WC_Product $product Product being rendered.
	 */
	do_action( 'skyyrose2_after_product_card', $product );
	?>
</li>
