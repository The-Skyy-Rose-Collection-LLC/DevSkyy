<?php
/**
 * WooCommerce Product Loop Card — Holo Card
 *
 * Overrides WooCommerce templates/content-product.php.
 * Delegates rendering to the Holo product card template part,
 * passing the WC_Product object for automatic data resolution.
 *
 * @see     https://woocommerce.com/document/template-structure/
 * @package SkyyRose
 * @since   5.0.0
 * @version 9.4.0
 */

defined( 'ABSPATH' ) || exit;

global $product;

if ( ! is_a( $product, WC_Product::class ) || ! $product->is_visible() ) {
	return;
}
?>

<li <?php wc_product_class( '', $product ); ?>>
	<?php
	$skyyrose_card_type = apply_filters( 'skyyrose_product_card_type', 'holo' );
	if ( ! in_array( $skyyrose_card_type, array( 'holo', 'v7-lookbook' ), true ) ) {
		$skyyrose_card_type = 'holo';
	}

	/*
	 * Wave 7: on the main shop/taxonomy archive the FIRST-ROW card images must
	 * be eager — round-6 Lighthouse flagged the first holo card's lazy front
	 * image as the shop mobile LCP (lcp-lazy-loaded score 0), and on the run
	 * where it never painted in-trace the late cookie banner became LCP at
	 * 9.6s. wc_product_class() above already incremented the loop counter, so
	 * wc_get_loop_prop( 'loop' ) is 1-based here; 0 (non-loop context) stays
	 * lazy. in_the_loop() keeps secondary loops (related products,
	 * cross-sells — below the fold) lazy.
	 */
	$skyyrose_loop_index = (int) wc_get_loop_prop( 'loop' );
	$skyyrose_eager_card = ( is_shop() || is_product_taxonomy() )
		&& in_the_loop()
		&& $skyyrose_loop_index >= 1
		&& $skyyrose_loop_index <= 4;
	get_template_part(
		'template-parts/product-card-' . $skyyrose_card_type,
		null,
		array(
			'product'        => $product,
			'image_loading'  => $skyyrose_eager_card ? 'eager' : 'lazy',
			'image_priority' => $skyyrose_eager_card && 1 === $skyyrose_loop_index,
		)
	);
	?>
</li>
