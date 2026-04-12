<?php
/**
 * Immersive Scene — Product Adapter
 *
 * Builds hotspot entries for the 3D immersive scene templates by merging
 * catalog product data with scene-specific placement metadata (left/top
 * coordinates, prop id, prop label, and optional per-scene overrides for
 * name, price, image, sizes, and collection).
 *
 * Consumed by:
 *   - template-immersive-signature.php
 *   - template-immersive-black-rose.php
 *   - template-parts/immersive-scene.php
 *
 * Split out of `inc/product-catalog.php` in v6.5.1 to keep that module
 * under the 800-line cap and to localize immersive-scene concerns.
 *
 * @package SkyyRose
 * @since   6.5.1
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Build an immersive hotspot product entry from the centralized catalog.
 *
 * Merges catalog data (name, price, image, sizes, collection) with
 * scene-specific placement data (left, top, prop, prop_label).
 * Supports virtual split SKUs (e.g., 'sg-001-tee') by looking up
 * the parent SKU and allowing name/price/image overrides.
 *
 * @since 3.2.2
 * @param string $sku       Product SKU (e.g., 'br-006') or virtual split (e.g., 'sg-001-tee').
 * @param array  $scene     Scene-specific data: left, top, prop, prop_label, and optional overrides.
 * @return array Merged product entry ready for hotspot rendering.
 */
function skyyrose_immersive_product( $sku, $scene ) {

	// Validate required scene keys.
	$required_keys = array( 'left', 'top', 'prop', 'prop_label' );
	foreach ( $required_keys as $key ) {
		if ( ! isset( $scene[ $key ] ) ) {
			return array();
		}
	}

	// For split/variant SKUs like 'sg-001-tee' or 'lh-002b', look up the parent.
	$parent_sku = preg_replace( '/-(tee|shorts)$/', '', $sku );
	$parent_sku = preg_replace( '/([a-z]{2}-\d{3})[a-z]$/', '$1', $parent_sku );
	$product    = skyyrose_get_product( $parent_sku );

	// Skip unpublished products.
	if ( $product && isset( $product['published'] ) && ! $product['published'] ) {
		return array();
	}

	// Determine the best display image: front-model VTON > flat product.
	$display_image = '';
	if ( $product ) {
		$display_image = ! empty( $product['front_model_image'] )
			? $product['front_model_image']
			: $product['image'];
	}

	// Collection display name.
	$collection_label = '';
	if ( $product ) {
		$slugs            = array(
			'black-rose'   => 'Black Rose Collection',
			'love-hurts'   => 'Love Hurts Collection',
			'signature'    => 'Signature Collection',
			'kids-capsule' => 'Kids Capsule Collection',
		);
		$collection_label = isset( $slugs[ $product['collection'] ] )
			? $slugs[ $product['collection'] ]
			: ucfirst( $product['collection'] ) . ' Collection';
	}

	// Build the entry — scene overrides win for name/price/image/sizes.
	// Return raw strings — templates apply esc_html()/esc_attr() at output time.
	// Do NOT pre-escape here or templates will double-encode via esc_attr().
	return array(
		'id'         => $sku,
		'name'       => isset( $scene['name'] )
			? $scene['name']
			: ( $product ? $product['name'] : $sku ),
		'price'      => isset( $scene['price'] )
			? $scene['price']
			: ( $product ? skyyrose_format_price( $product ) : '' ),
		'collection' => isset( $scene['collection'] )
			? $scene['collection']
			: $collection_label,
		'sizes'      => isset( $scene['sizes'] )
			? $scene['sizes']
			: ( $product ? str_replace( '|', ',', $product['sizes'] ) : '' ),
		'image'      => isset( $scene['image'] )
			? $scene['image']
			: ( $display_image ? get_theme_file_uri( $display_image ) : '' ),
		'url'        => skyyrose_product_url( $sku ),
		'left'       => $scene['left'],
		'top'        => $scene['top'],
		'prop'       => $scene['prop'],
		'prop_label' => $scene['prop_label'],
	);
}
