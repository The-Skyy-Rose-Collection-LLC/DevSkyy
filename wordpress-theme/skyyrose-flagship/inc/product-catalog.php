<?php
/**
 * Centralized Product Catalog — CSV-backed loader
 *
 * Single source of truth for all product data:
 *   data/skyyrose-catalog.csv
 *
 * Every consumer (templates, WooCommerce overrides, 404 fallback, immersive
 * templates, JSON-LD, admin screens, sync scripts) MUST read through this file.
 * No other catalog source is authoritative — catalog.yaml, manifest.json,
 * the per-skill products.csv files, and any worktree copies are retired.
 *
 * @package SkyyRose
 * @since   7.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Absolute path to the canonical catalog CSV.
 *
 * @since 7.0.0
 * @return string
 */
function skyyrose_catalog_csv_path() {
	return get_theme_file_path( 'data/skyyrose-catalog.csv' );
}

/**
 * Get the full product catalog, keyed by SKU.
 *
 * Parses data/skyyrose-catalog.csv on first call, caches in a static for the
 * duration of the request. Unknown columns in the CSV are passed through
 * unchanged so the schema can grow without code changes.
 *
 * @since 7.0.0
 * @return array<string, array> Associative array of all products keyed by SKU.
 */
function skyyrose_get_product_catalog() {
	static $catalog = null;

	if ( null !== $catalog ) {
		return $catalog;
	}

	$catalog  = array();
	$csv_path = skyyrose_catalog_csv_path();

	if ( ! is_readable( $csv_path ) ) {
		return $catalog;
	}

	$handle = fopen( $csv_path, 'r' );
	if ( false === $handle ) {
		return $catalog;
	}

	$headers = fgetcsv( $handle, 0, ',', '"', '\\' );
	if ( false === $headers ) {
		fclose( $handle );
		return $catalog;
	}

	while ( ( $row = fgetcsv( $handle, 0, ',', '"', '\\' ) ) !== false ) {
		if ( '' === implode( '', $row ) ) {
			continue;
		}

		// Pad short rows to full column count so array_combine doesn't fail.
		if ( count( $row ) < count( $headers ) ) {
			$row = array_pad( $row, count( $headers ), '' );
		}

		$data = array_combine( $headers, $row );
		$sku  = isset( $data['sku'] ) ? trim( $data['sku'] ) : '';
		if ( '' === $sku ) {
			continue;
		}

		$catalog[ $sku ] = array(
			'sku'               => $sku,
			'name'              => $data['name'] ?? '',
			'price'             => isset( $data['price'] ) ? (float) $data['price'] : 0.0,
			'collection'        => $data['collection'] ?? '',
			'description'       => $data['description'] ?? '',
			'badge'             => $data['badge'] ?? '',
			'image'             => $data['image'] ?? '',
			'front_model_image' => $data['front_model_image'] ?? '',
			'back_image'        => $data['back_image'] ?? '',
			'back_model_image'  => $data['back_model_image'] ?? '',
			'sizes'             => $data['sizes'] ?? '',
			'color'             => $data['color'] ?? '',
			'edition_size'      => isset( $data['edition_size'] ) ? (int) $data['edition_size'] : 0,
			'published'         => ! empty( $data['published'] ) && '0' !== $data['published'],
			'is_preorder'       => ! empty( $data['is_preorder'] ) && '0' !== $data['is_preorder'],
		);
	}

	fclose( $handle );

	return $catalog;
}

/**
 * Get a single product by SKU.
 *
 * @since 3.2.1
 * @param  string $sku Product SKU (e.g., 'br-006').
 * @return array|null  Product data array or null if not found.
 */
function skyyrose_get_product( $sku ) {
	$sku     = sanitize_key( $sku );
	$catalog = skyyrose_get_product_catalog();
	return $catalog[ $sku ] ?? null;
}

/**
 * Get all products for a specific collection.
 *
 * @since 3.2.1
 * @param  string $collection Collection slug: 'black-rose', 'love-hurts', 'signature', 'kids-capsule'.
 * @return array  Array of product data arrays for the collection.
 */
function skyyrose_get_collection_products( $collection ) {
	static $cache = array();

	$collection = sanitize_key( $collection );
	if ( isset( $cache[ $collection ] ) ) {
		return $cache[ $collection ];
	}

	$catalog  = skyyrose_get_product_catalog();
	$products = array();

	foreach ( $catalog as $product ) {
		if ( $product['collection'] === $collection ) {
			$products[] = $product;
		}
	}

	$cache[ $collection ] = $products;
	return $products;
}

/**
 * Normalize a SKU to its base product SKU (strip variant suffixes).
 *
 * Handles: br-003-giants → br-003, sg-001-tee → sg-001, br-003a → br-003.
 *
 * @since 6.3.0
 * @param  string $sku SKU with optional variant suffix.
 * @return string Base SKU.
 */
function skyyrose_normalize_sku( $sku ) {
	$sku = preg_replace( '/-(tee|shorts|giants|white|oakland)$/', '', $sku );
	return preg_replace( '/([a-z]{2,4}-\d{3})[a-z]$/', '$1', $sku );
}

/**
 * Format a product price for display.
 *
 * Returns 'Coming Soon' for unpublished products without pre-order,
 * or the formatted dollar amount.
 *
 * @since 3.2.1
 * @param  array $product Product data array.
 * @return string Formatted price string.
 */
function skyyrose_format_price( $product ) {
	if ( ! $product['published'] && ! $product['is_preorder'] ) {
		return esc_html__( 'Coming Soon', 'skyyrose' );
	}

	$price = (float) $product['price'];

	if ( ! empty( $product['is_preorder'] ) && $price <= 0 ) {
		return esc_html__( 'Pre-Order', 'skyyrose' );
	}

	return '$' . number_format( $price, 0 );
}

/**
 * Get the theme-relative URI for a product image.
 *
 * @since 3.2.1
 * @param  string $image_path Relative image path from catalog (e.g., 'assets/images/products/br-001.webp').
 * @return string Full URI to the image.
 */
function skyyrose_product_image_uri( $image_path ) {
	if ( empty( $image_path ) ) {
		return get_theme_file_uri( 'assets/images/placeholder-product.jpg' );
	}
	return get_theme_file_uri( $image_path );
}

/**
 * Get the best available URL for a product.
 *
 * Uses WooCommerce permalink if product exists, falls back to pre-order page.
 *
 * @since 3.2.3
 * @param  string $sku Product SKU.
 * @return string Product URL.
 */
function skyyrose_product_url( $sku ) {
	if ( function_exists( 'wc_get_product_id_by_sku' ) ) {
		$lookup_sku = skyyrose_normalize_sku( $sku );
		$product_id = wc_get_product_id_by_sku( $lookup_sku );
		if ( $product_id ) {
			return get_permalink( $product_id );
		}
	}

	$product = skyyrose_get_product( $sku );
	if ( $product && ! empty( $product['is_preorder'] ) ) {
		return home_url( '/pre-order/#' . sanitize_title( $sku ) );
	}
	if ( $product && ! empty( $product['collection'] ) ) {
		return home_url( '/collection-' . sanitize_title( $product['collection'] ) . '/#' . sanitize_title( $sku ) );
	}

	return home_url( '/pre-order/#' . sanitize_title( $sku ) );
}
