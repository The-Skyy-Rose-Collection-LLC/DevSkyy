<?php
/**
 * SOT-only WooCommerce product card.
 *
 * @package SkyyRoseFlagshipSOT
 */

defined( 'ABSPATH' ) || exit;

global $product;

if ( ! $product || ! $product->is_visible() ) {
	return;
}

$product_data = skyyrosesot_product_by_sku( $product->get_sku() );
$image        = skyyrosesot_product_image( $product_data );

if ( '' === $image ) {
	return;
}
?>
<li <?php wc_product_class( 'srs-product', $product ); ?>><a href="<?php echo esc_url( get_permalink( $product->get_id() ) ); ?>"><img src="<?php echo esc_url( skyyrosesot_asset_uri( $image ) ); ?>" alt="<?php echo esc_attr( $product->get_name() ); ?>" loading="lazy" width="720" height="960"></a><p><?php echo esc_html( $product->get_sku() ); ?></p><h3><a href="<?php echo esc_url( get_permalink( $product->get_id() ) ); ?>"><?php echo esc_html( $product->get_name() ); ?></a></h3><div><span><?php echo wp_kses_post( $product->get_price_html() ); ?></span><a href="<?php echo esc_url( get_permalink( $product->get_id() ) ); ?>"><?php esc_html_e( 'View piece', 'skyyrose-flagship-sot' ); ?></a></div></li>
