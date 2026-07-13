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
	get_template_part(
		'template-parts/product-card-' . $skyyrose_card_type,
		null,
		array(
			'product' => $product,
		)
	);
	?>
</li>
