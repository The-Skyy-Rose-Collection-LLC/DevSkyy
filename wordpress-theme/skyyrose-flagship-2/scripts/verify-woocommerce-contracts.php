<?php
/**
 * Verify WooCommerce override versions and public extension contracts.
 *
 * This is a source preflight, not a substitute for installed runtime testing.
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
function skyyrose2_contract_read( $relative_path ) {
	global $theme_dir;
	$contents = file_get_contents( $theme_dir . '/' . $relative_path );
	if ( false === $contents ) {
		throw new RuntimeException( 'Unable to read ' . $relative_path );
	}
	return $contents;
}

/**
 * Require every contract marker in a source file.
 *
 * @param string        $relative_path Theme-relative path.
 * @param array<string> $markers Required source markers.
 * @return void
 */
function skyyrose2_contract_require_markers( $relative_path, $markers ) {
	$contents = skyyrose2_contract_read( $relative_path );
	foreach ( $markers as $marker ) {
		if ( false === strpos( $contents, $marker ) ) {
			throw new RuntimeException( $relative_path . ' is missing contract marker: ' . $marker );
		}
	}
}

$override_versions = array(
	'woocommerce/archive-product.php' => '8.6.0',
	'woocommerce/single-product.php'  => '1.6.4',
	'woocommerce/content-product.php' => '9.4.0',
	'woocommerce/cart/cart.php'       => '10.8.0',
);

if ( file_exists( $theme_dir . '/woocommerce.php' ) ) {
	throw new RuntimeException( 'woocommerce.php would shadow the archive-product.php flagship contract.' );
}

foreach ( $override_versions as $relative_path => $expected_version ) {
	$contents = skyyrose2_contract_read( $relative_path );
	if ( ! preg_match( '/@version\s+' . preg_quote( $expected_version, '/' ) . '\b/', $contents ) ) {
		throw new RuntimeException( $relative_path . ' is not synchronized to template version ' . $expected_version );
	}
}

skyyrose2_contract_require_markers(
	'inc/woocommerce-integration.php',
	array(
		"remove_action( 'woocommerce_before_main_content', 'woocommerce_output_content_wrapper', 10 )",
		"add_action( 'woocommerce_before_main_content', 'skyyrose2_woocommerce_wrapper_start', 10 )",
		"add_action( 'woocommerce_after_main_content', 'skyyrose2_woocommerce_wrapper_end', 10 )",
		"remove_action( 'woocommerce_shop_loop_header', 'woocommerce_product_taxonomy_archive_header', 10 )",
		"remove_action( 'woocommerce_sidebar', 'woocommerce_get_sidebar', 10 )",
	)
);

skyyrose2_contract_require_markers(
	'woocommerce/archive-product.php',
	array(
		"do_action( 'woocommerce_before_main_content' )",
		"do_action( 'woocommerce_archive_description' )",
		"do_action( 'woocommerce_shop_loop_header' )",
		"do_action( 'woocommerce_before_shop_loop' )",
		"do_action( 'woocommerce_shop_loop' )",
		"do_action( 'woocommerce_after_shop_loop' )",
		"do_action( 'woocommerce_no_products_found' )",
		"do_action( 'woocommerce_after_main_content' )",
		"do_action( 'woocommerce_sidebar' )",
	)
);

skyyrose2_contract_require_markers(
	'woocommerce/single-product.php',
	array(
		"do_action( 'woocommerce_before_main_content' )",
		"wc_get_template_part( 'content', 'single-product' )",
		"do_action( 'woocommerce_after_main_content' )",
		"do_action( 'woocommerce_sidebar' )",
	)
);

skyyrose2_contract_require_markers(
	'woocommerce/content-product.php',
	array(
		"do_action( 'woocommerce_before_shop_loop_item' )",
		"do_action( 'woocommerce_before_shop_loop_item_title' )",
		"do_action( 'woocommerce_shop_loop_item_title' )",
		"do_action( 'woocommerce_after_shop_loop_item_title' )",
		"do_action( 'woocommerce_after_shop_loop_item' )",
	)
);

skyyrose2_contract_require_markers(
	'woocommerce/cart/cart.php',
	array(
		"do_action( 'woocommerce_before_cart' )",
		"do_action( 'woocommerce_before_cart_table' )",
		"do_action( 'woocommerce_before_cart_contents' )",
		"do_action( 'woocommerce_after_cart_item_name'",
		"do_action( 'woocommerce_cart_contents' )",
		"do_action( 'woocommerce_cart_coupon' )",
		"do_action( 'woocommerce_cart_actions' )",
		"do_action( 'woocommerce_after_cart_contents' )",
		"do_action( 'woocommerce_after_cart_table' )",
		"do_action( 'woocommerce_before_cart_collaterals' )",
		"do_action( 'woocommerce_cart_collaterals' )",
		"do_action( 'woocommerce_after_cart' )",
		"'woocommerce_cart_item_remove_link'",
		"'woocommerce_cart_item_price'",
		"'woocommerce_cart_item_quantity'",
		"'woocommerce_cart_item_subtotal'",
		"'woocommerce_cart_item_backorder_notification'",
	)
);

echo "WooCommerce contracts: PASS (baseline 10.9.1)\n";
