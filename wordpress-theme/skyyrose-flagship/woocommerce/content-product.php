<?php
/**
 * WooCommerce Product Loop Card — Holo Card
 *
 * Overrides WooCommerce templates/content-product.php.
 * Delegates rendering to the Holo product card template part,
 * passing the WC_Product object for automatic data resolution.
 *
 * @see     https://woocommerce.com/document/template-structure/
 * @package SkyyRose_Flagship
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
	get_template_part( 'template-parts/product-card-holo', null, array(
		'product' => $product,
	) );
	?>
</li>
