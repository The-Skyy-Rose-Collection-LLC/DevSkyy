<?php
/**
 * Verify fail-closed commerce and storefront truth contracts without WordPress.
 *
 * @package SkyyRoseFlagship2
 */

$theme_dir = dirname( __DIR__ );

/**
 * Read a required theme file.
 *
 * @param string $relative_path Theme-relative path.
 * @return string
 */
function skyyrose2_test_read( $relative_path ) {
	global $theme_dir;
	$contents = file_get_contents( $theme_dir . '/' . $relative_path );
	if ( false === $contents ) {
		throw new RuntimeException( 'Unable to read ' . $relative_path );
	}
	return $contents;
}

$functions   = skyyrose2_test_read( 'functions.php' );
$page        = skyyrose2_test_read( 'page.php' );
$card        = skyyrose2_test_read( 'template-parts/product-card.php' );
$loop        = skyyrose2_test_read( 'woocommerce/content-product.php' );
$mascot      = skyyrose2_test_read( 'assets/js/mascot.js' );
$mascot_view = skyyrose2_test_read( 'template-parts/skyy-mascot.php' );

if ( false !== strpos( $functions, "'pre-order' === \$collection ) {\n\t\t\$products =" ) ) {
	throw new RuntimeException( 'Pre-order products still fall back to ordinary inventory.' );
}
foreach ( array( 'wc_get_product_id_by_sku', "true !== has_term( 'pre-order'", "\$scene_product->get_name()", "\$scene_product->get_permalink()" ) as $required ) {
	if ( false === strpos( $page, $required ) ) {
		throw new RuntimeException( 'Missing salon truth contract: ' . $required );
	}
}
foreach ( array( 'Black Is Beautiful', 'Number 30', 'Number 32', 'The Oakland Jacket', 'The Bay Tee' ) as $stale_label ) {
	if ( false !== strpos( $page, $stale_label ) ) {
		throw new RuntimeException( 'Stale hardcoded salon label remains: ' . $stale_label );
	}
}
foreach ( array( 'get_availability()', "true === has_term( 'pre-order'", "__( 'Out of stock'", "__( 'Pre-order'" ) as $required ) {
	if ( false === strpos( $card, $required ) ) {
		throw new RuntimeException( 'Missing product-card truth contract: ' . $required );
	}
}
foreach ( array( "__( 'Reserved'", 'data-sr2-wishlist-id' ) as $prohibited ) {
	if ( false !== strpos( $card, $prohibited ) ) {
		throw new RuntimeException( 'Prohibited product-card state remains: ' . $prohibited );
	}
}
foreach ( array( 'woocommerce_before_shop_loop_item', 'woocommerce_before_shop_loop_item_title', 'woocommerce_shop_loop_item_title', 'woocommerce_after_shop_loop_item_title', 'woocommerce_after_shop_loop_item' ) as $hook ) {
	if ( false === strpos( $loop, "do_action( '" . $hook . "'" ) ) {
		throw new RuntimeException( 'Missing WooCommerce loop hook: ' . $hook );
	}
}
foreach ( array( '/collections-world/', 'ajaxUrl', 'emitSkyy', 'skyy-ask-' ) as $dead_seam ) {
	if ( false !== strpos( $mascot . $mascot_view, $dead_seam ) ) {
		throw new RuntimeException( 'Dead Skyy guide seam remains: ' . $dead_seam );
	}
}

echo "Commerce truth: PASS\n";
