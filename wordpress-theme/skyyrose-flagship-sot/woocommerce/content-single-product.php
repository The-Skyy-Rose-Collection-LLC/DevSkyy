<?php
/**
 * SOT-only WooCommerce product surface.
 *
 * @package SkyyRoseFlagshipSOT
 */

defined( 'ABSPATH' ) || exit;

global $product;

$product_data = skyyrosesot_product_by_sku( $product->get_sku() );
$image        = skyyrosesot_product_image( $product_data );
?>
<div id="product-<?php the_ID(); ?>" <?php wc_product_class( 'srs-single-product', $product ); ?>><?php do_action( 'woocommerce_before_single_product' ); ?>
<?php
if ( post_password_required() ) {
		echo wp_kses_post( get_the_password_form() );
	return; }
?>
<div class="srs-single-product__media">
<?php
if ( $image ) :
	?>
	<img src="<?php echo esc_url( skyyrosesot_asset_uri( $image ) ); ?>" alt="<?php echo esc_attr( $product->get_name() ); ?>" fetchpriority="high" width="1200" height="1600"><?php endif; ?></div><div class="summary entry-summary"><?php do_action( 'woocommerce_single_product_summary' ); ?></div><?php do_action( 'woocommerce_after_single_product_summary' ); ?></div>
