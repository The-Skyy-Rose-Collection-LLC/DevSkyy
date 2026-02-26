<?php
/**
 * WooCommerce Product Import Script
 *
 * Creates the full SkyyRose product catalog in WooCommerce using the
 * WC_Product API. Designed to be run via WP-CLI:
 *
 *   wp eval-file wordpress-theme/skyyrose-flagship/inc/product-import.php
 *
 * Features:
 *   - Idempotent: checks SKU before creating (safe to run multiple times)
 *   - Creates product categories with proper hierarchy
 *   - Registers pa_size and pa_color global attributes
 *   - Sets all pre-order meta fields used by the theme
 *
 * @package SkyyRose_Flagship
 * @since   3.3.0
 */

/*--------------------------------------------------------------
 * WordPress Context Guard
 *--------------------------------------------------------------*/

if ( ! defined( 'ABSPATH' ) ) {
	echo "=======================================================\n";
	echo "  SkyyRose WooCommerce Product Import\n";
	echo "=======================================================\n\n";
	echo "This script must be run inside WordPress via WP-CLI:\n\n";
	echo "  wp eval-file wordpress-theme/skyyrose-flagship/inc/product-import.php\n\n";
	echo "Requirements:\n";
	echo "  - WordPress must be installed and configured\n";
	echo "  - WooCommerce must be active\n";
	echo "  - WP-CLI must be installed (https://wp-cli.org/)\n\n";
	exit( 1 );
}

/*--------------------------------------------------------------
 * WooCommerce Availability Check
 *--------------------------------------------------------------*/

if ( ! class_exists( 'WooCommerce' ) || ! function_exists( 'wc_get_product_id_by_sku' ) ) {
	WP_CLI::error( 'WooCommerce is not active. Please activate WooCommerce before running this import.' );
}

WP_CLI::log( '' );
WP_CLI::log( '========================================' );
WP_CLI::log( '  SkyyRose Product Import' );
WP_CLI::log( '  Luxury Grows from Concrete.' );
WP_CLI::log( '========================================' );
WP_CLI::log( '' );

/*--------------------------------------------------------------
 * Step 1: Create Product Categories
 *--------------------------------------------------------------*/

WP_CLI::log( '--- Step 1: Creating product categories ---' );

$skyyrose_import_categories = array(
	'black-rose'   => array(
		'name'        => 'Black Rose',
		'description' => 'Dark elegance meets luxury streetwear. Cathedral-inspired pieces for the bold.',
	),
	'love-hurts'   => array(
		'name'        => 'Love Hurts',
		'description' => 'Where passion meets pain. Castle-themed pieces that tell a story of love and resilience.',
	),
	'signature'    => array(
		'name'        => 'Signature',
		'description' => 'The quintessential SkyyRose experience. City-inspired luxury for every day.',
	),
	'kids-capsule' => array(
		'name'        => 'Kids Capsule',
		'description' => 'Luxury fashion for the next generation. Where love meets comfort.',
	),
);

$skyyrose_import_cat_ids = array();

foreach ( $skyyrose_import_categories as $slug => $data ) {
	$existing = term_exists( $slug, 'product_cat' );
	if ( $existing ) {
		$skyyrose_import_cat_ids[ $slug ] = is_array( $existing ) ? (int) $existing['term_id'] : (int) $existing;
		WP_CLI::log( "  [SKIP] Category '{$data['name']}' already exists (ID: {$skyyrose_import_cat_ids[ $slug ]})" );
	} else {
		$result = wp_insert_term(
			$data['name'],
			'product_cat',
			array(
				'slug'        => $slug,
				'description' => $data['description'],
			)
		);
		if ( is_wp_error( $result ) ) {
			WP_CLI::warning( "  [FAIL] Could not create category '{$data['name']}': " . $result->get_error_message() );
		} else {
			$skyyrose_import_cat_ids[ $slug ] = (int) $result['term_id'];
			WP_CLI::success( "  Created category '{$data['name']}' (ID: {$skyyrose_import_cat_ids[ $slug ]})" );
		}
	}
}

WP_CLI::log( '' );

/*--------------------------------------------------------------
 * Step 2: Register Product Attributes
 *--------------------------------------------------------------*/

WP_CLI::log( '--- Step 2: Registering product attributes ---' );

$skyyrose_import_attributes = array(
	'pa_size'  => array(
		'name'    => 'Size',
		'slug'    => 'size',
		'type'    => 'select',
		'order'   => 'menu_order',
	),
	'pa_color' => array(
		'name'    => 'Color',
		'slug'    => 'color',
		'type'    => 'select',
		'order'   => 'menu_order',
	),
);

foreach ( $skyyrose_import_attributes as $taxonomy => $attr_data ) {
	if ( taxonomy_exists( $taxonomy ) ) {
		WP_CLI::log( "  [SKIP] Attribute '{$attr_data['name']}' already registered" );
		continue;
	}

	$attribute_id = wc_create_attribute(
		array(
			'name'         => $attr_data['name'],
			'slug'         => $attr_data['slug'],
			'type'         => $attr_data['type'],
			'order_by'     => $attr_data['order'],
			'has_archives' => false,
		)
	);

	if ( is_wp_error( $attribute_id ) ) {
		WP_CLI::warning( "  [FAIL] Could not create attribute '{$attr_data['name']}': " . $attribute_id->get_error_message() );
	} else {
		// Register the taxonomy so it can be used immediately in this script.
		register_taxonomy(
			$taxonomy,
			array( 'product' ),
			array(
				'labels'       => array( 'name' => $attr_data['name'] ),
				'hierarchical' => false,
				'show_ui'      => false,
				'query_var'    => true,
				'rewrite'      => false,
			)
		);
		WP_CLI::success( "  Created attribute '{$attr_data['name']}' (ID: {$attribute_id})" );
	}
}

WP_CLI::log( '' );

/*--------------------------------------------------------------
 * Step 3: Build Product List from Centralized Catalog
 *
 * Sources all product data from inc/product-catalog.php — the single
 * source of truth. No duplicate product arrays.
 *--------------------------------------------------------------*/

$skyyrose_import_catalog  = skyyrose_get_product_catalog();
$skyyrose_import_products = array();

foreach ( $skyyrose_import_catalog as $catalog_product ) {
	$skyyrose_import_products[] = array(
		'sku'               => $catalog_product['sku'],
		'name'              => $catalog_product['name'],
		'price'             => number_format( $catalog_product['price'], 2, '.', '' ),
		'status'            => $catalog_product['published'] ? 'publish' : 'draft',
		'category'          => $catalog_product['collection'],
		'sizes'             => explode( '|', $catalog_product['sizes'] ),
		'color'             => $catalog_product['color'],
		'description'       => $catalog_product['description'],
		'short_description' => $catalog_product['description'],
	);
}

/*--------------------------------------------------------------
 * Step 4: Create Products
 *--------------------------------------------------------------*/

WP_CLI::log( '--- Step 3: Creating products ---' );
WP_CLI::log( '' );

$skyyrose_import_created  = 0;
$skyyrose_import_skipped  = 0;
$skyyrose_import_failed   = 0;

// Seed the random number generator for reproducible "available" counts.
mt_srand( 42 );

foreach ( $skyyrose_import_products as $product_data ) {

	$sku = $product_data['sku'];

	// ----------------------------------------------------------
	// Check if product already exists by SKU.
	// ----------------------------------------------------------
	$existing_id = wc_get_product_id_by_sku( $sku );
	if ( $existing_id ) {
		WP_CLI::log( "  [SKIP] {$sku} — '{$product_data['name']}' already exists (ID: {$existing_id})" );
		$skyyrose_import_skipped++;
		continue;
	}

	// ----------------------------------------------------------
	// Create the WC_Product_Simple object.
	// ----------------------------------------------------------
	$product = new WC_Product_Simple();

	$product->set_name( $product_data['name'] );
	$product->set_sku( $sku );
	$product->set_regular_price( $product_data['price'] );
	$product->set_status( $product_data['status'] );
	$product->set_catalog_visibility( 'visible' );
	$product->set_description( $product_data['description'] );
	$product->set_short_description( $product_data['short_description'] );
	$product->set_manage_stock( false );
	$product->set_stock_status( 'instock' );
	$product->set_sold_individually( false );
	$product->set_virtual( false );
	$product->set_downloadable( false );
	$product->set_reviews_allowed( true );
	$product->set_weight( '' );

	// ----------------------------------------------------------
	// Assign product category.
	// ----------------------------------------------------------
	$cat_slug = $product_data['category'];
	if ( isset( $skyyrose_import_cat_ids[ $cat_slug ] ) ) {
		$product->set_category_ids( array( $skyyrose_import_cat_ids[ $cat_slug ] ) );
	}

	// ----------------------------------------------------------
	// Set product attributes (Size + Color).
	// ----------------------------------------------------------
	$attributes = array();

	// Size attribute.
	$size_attr = new WC_Product_Attribute();
	$size_attr->set_name( 'pa_size' );
	$size_attr->set_options( $product_data['sizes'] );
	$size_attr->set_position( 0 );
	$size_attr->set_visible( true );
	$size_attr->set_variation( false );
	$attributes[] = $size_attr;

	// Color attribute.
	$color_attr = new WC_Product_Attribute();
	$color_attr->set_name( 'pa_color' );
	$color_attr->set_options( array( $product_data['color'] ) );
	$color_attr->set_position( 1 );
	$color_attr->set_visible( true );
	$color_attr->set_variation( false );
	$attributes[] = $color_attr;

	$product->set_attributes( $attributes );

	// ----------------------------------------------------------
	// Save the product to get an ID.
	// ----------------------------------------------------------
	$product_id = $product->save();

	if ( ! $product_id ) {
		WP_CLI::warning( "  [FAIL] {$sku} — '{$product_data['name']}' could not be created" );
		$skyyrose_import_failed++;
		continue;
	}

	// ----------------------------------------------------------
	// Set pre-order meta fields.
	// ----------------------------------------------------------
	$is_published    = ( 'publish' === $product_data['status'] );
	$preorder_avail  = mt_rand( 50, 200 );

	update_post_meta( $product_id, '_is_preorder', $is_published ? '1' : '0' );
	update_post_meta( $product_id, '_preorder_edition_size', '250' );
	update_post_meta( $product_id, '_preorder_available', (string) $preorder_avail );
	update_post_meta( $product_id, '_preorder_ship_date', '2026-06-15' );
	update_post_meta( $product_id, '_collection_badge', $is_published ? 'Pre-Order' : 'Draft' );

	// ----------------------------------------------------------
	// Set additional theme meta.
	// ----------------------------------------------------------
	update_post_meta( $product_id, '_skyyrose_collection', $cat_slug );

	$status_label = $is_published ? 'Pre-Order' : 'Draft';
	$avail_label  = $is_published ? " | {$preorder_avail}/250 available" : '';

	WP_CLI::success( "  {$sku} — '{$product_data['name']}' created (ID: {$product_id}) [{$status_label}{$avail_label}]" );
	$skyyrose_import_created++;
}

/*--------------------------------------------------------------
 * Summary
 *--------------------------------------------------------------*/

WP_CLI::log( '' );
WP_CLI::log( '========================================' );
WP_CLI::log( '  Import Complete' );
WP_CLI::log( '========================================' );
WP_CLI::log( '' );
WP_CLI::log( "  Created:  {$skyyrose_import_created}" );
WP_CLI::log( "  Skipped:  {$skyyrose_import_skipped}" );
WP_CLI::log( "  Failed:   {$skyyrose_import_failed}" );
WP_CLI::log( "  Total:    " . count( $skyyrose_import_products ) );
WP_CLI::log( '' );

if ( $skyyrose_import_created > 0 ) {
	WP_CLI::log( '  Next steps:' );
	WP_CLI::log( '    1. Upload product images via WP Admin > Media' );
	WP_CLI::log( '    2. Assign featured images to each product' );
	WP_CLI::log( '    3. Review draft products and publish when ready' );
	WP_CLI::log( '    4. Verify pre-order settings on the front end' );
	WP_CLI::log( '' );
}

WP_CLI::log( '  CSV alternative: Import data/products.csv via' );
WP_CLI::log( '  WooCommerce > Products > Import' );
WP_CLI::log( '' );
