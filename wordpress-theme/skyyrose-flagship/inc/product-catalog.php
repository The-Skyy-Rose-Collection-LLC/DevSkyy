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

	// Prefer the WP object cache (Redis/Memcached) when available so the CSV
	// parse happens at most once per site, not once per request.
	if ( function_exists( 'wp_cache_get' ) ) {
		$cached = wp_cache_get( 'skyyrose_product_catalog', 'skyyrose' );
		if ( is_array( $cached ) && ! empty( $cached ) ) {
			$catalog = $cached;
			return $catalog;
		}
	}

	$catalog  = array();
	$csv_path = skyyrose_catalog_csv_path();

	if ( ! is_readable( $csv_path ) ) {
		return $catalog;
	}

	// phpcs:ignore WordPress.WP.AlternativeFunctions.file_system_operations_fopen -- WP_Filesystem does not support fgetcsv; local theme data file, no remote FS.
	$handle = fopen( $csv_path, 'r' );
	if ( false === $handle ) {
		return $catalog;
	}

	// phpcs:ignore WordPress.WP.AlternativeFunctions.file_system_operations_fgetcsv -- standard CSV parse idiom, no WP_Filesystem equivalent.
	$headers = fgetcsv( $handle, 0, ',', '"', '\\' );
	if ( false === $headers ) {
		// phpcs:ignore WordPress.WP.AlternativeFunctions.file_system_operations_fclose
		fclose( $handle );
		return $catalog;
	}

	// phpcs:ignore WordPress.WP.AlternativeFunctions.file_system_operations_fgetcsv -- idiomatic CSV row iteration; no WP_Filesystem fgetcsv equivalent.
	while ( ( $row = fgetcsv( $handle, 0, ',', '"', '\\' ) ) !== false ) { // phpcs:ignore Generic.CodeAnalysis.AssignmentInCondition.FoundInWhileCondition
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
			'garment_type_lock' => $data['garment_type_lock'] ?? '',
			'dossier_slug'      => $data['dossier_slug'] ?? '',
		);
	}

	// phpcs:ignore WordPress.WP.AlternativeFunctions.file_system_operations_fclose
	fclose( $handle );

	if ( function_exists( 'wp_cache_set' ) && ! empty( $catalog ) ) {
		wp_cache_set( 'skyyrose_product_catalog', $catalog, 'skyyrose', HOUR_IN_SECONDS );
	}

	return $catalog;
}

/**
 * Pick the best available display image for a product card.
 *
 * Callers that only need "show me the product image" should use this
 * helper instead of reaching into product['image'] / front_model_image
 * directly. Keeps the image-slot precedence in one place.
 *
 * @since 7.1.0
 * @param  array $product Product data array from skyyrose_get_product().
 * @return string Theme-relative path to the best available image.
 */
function skyyrose_get_product_display_image( $product ) {
	if ( ! is_array( $product ) ) {
		return '';
	}
	// IMAGERY PRECEDENCE (canon, 2026-06-16): front-model-first, matching
	// product-card-holo.php and the WC ghost-loop filter. Keep all three in sync.
	foreach ( array( 'front_model_image', 'image', 'back_model_image', 'back_image' ) as $slot ) {
		$value = $product[ $slot ] ?? '';
		if ( is_string( $value ) && '' !== $value ) {
			return $value;
		}
	}
	return '';
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
 * Handles: sg-001-tee → sg-001, br-003a → br-003.
 *
 * @since 6.3.0
 * @param  string $sku SKU with optional variant suffix.
 * @return string Base SKU.
 */
function skyyrose_normalize_sku( $sku ) {
	$sku = preg_replace( '/-(tee|shorts)$/', '', $sku );
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
 * Get parsed dossier data for a product by SKU.
 *
 * Reads data/dossiers/{dossier_slug}.md, parses YAML front-matter and
 * markdown body sections into a structured array for PDP editorial layout.
 *
 * @since 7.2.0
 * @param  string $sku Product SKU.
 * @return array|null  Structured dossier data or null if unavailable.
 */
function skyyrose_get_product_dossier( $sku ) {
	static $cache = array();

	$sku = sanitize_key( $sku );
	if ( isset( $cache[ $sku ] ) ) {
		return $cache[ $sku ];
	}

	$product = skyyrose_get_product( $sku );
	if ( ! $product || empty( $product['dossier_slug'] ) ) {
		$cache[ $sku ] = null;
		return null;
	}

	$slug = sanitize_file_name( $product['dossier_slug'] );
	$path = get_theme_file_path( 'data/dossiers/' . $slug . '.md' );

	if ( ! is_readable( $path ) ) {
		$cache[ $sku ] = null;
		return null;
	}

	// phpcs:ignore WordPress.WP.AlternativeFunctions.file_get_contents_file_get_contents -- local theme file read.
	$raw = file_get_contents( $path );
	if ( false === $raw || '' === $raw ) {
		$cache[ $sku ] = null;
		return null;
	}

	$dossier = array(
		'has_editorial_content' => false,
		'garment_type_lock'     => '',
		'branding'              => array(
			'front' => '',
			'back'  => '',
			'other' => '',
		),
	);

	// --- Parse front-matter (between --- fences) ---
	if ( preg_match( '/^---\s*\n(.*?)\n---\s*\n/s', $raw, $fm_match ) ) {
		$body = substr( $raw, strlen( $fm_match[0] ) );
	} else {
		$body = $raw;
	}

	// --- Extract garment type lock (first bold paragraph after # Title) ---
	if ( preg_match( '/\*\*Garment type lock:\*\*\s*(.+?)(?:\n\n|\n##)/s', $body, $gtl_match ) ) {
		$dossier['garment_type_lock'] = sanitize_text_field( trim( $gtl_match[1] ) );
	}

	// --- Parse ## Branding section and its ### sub-sections ---
	if ( preg_match( '/## Branding[^\n]*\n(.*?)(?=\n## [^#]|\z)/s', $body, $brand_match ) ) {
		$brand_body = $brand_match[1];

		if ( preg_match( '/### Front\s*\n(.*?)(?=\n### |\n## |\z)/s', $brand_body, $front_match ) ) {
			$dossier['branding']['front'] = sanitize_text_field( trim( $front_match[1] ) );
		}
		if ( preg_match( '/### Back\s*\n(.*?)(?=\n### |\n## |\z)/s', $brand_body, $back_match ) ) {
			$dossier['branding']['back'] = sanitize_text_field( trim( $back_match[1] ) );
		}
		// Catch Sleeves, Collar, Hem, Other sub-sections.
		if ( preg_match( '/### (?:Sleeves|Collar|Hem|Other)[^\n]*\n(.*?)(?=\n### |\n## |\z)/s', $brand_body, $other_match ) ) {
			$dossier['branding']['other'] = sanitize_text_field( trim( $other_match[1] ) );
		}
	}

	// Mark as having editorial content if we got meaningful data.
	if ( '' !== $dossier['garment_type_lock'] || '' !== $dossier['branding']['front'] ) {
		$dossier['has_editorial_content'] = true;
	}

	$cache[ $sku ] = $dossier;
	return $dossier;
}

/**
 * Get similarity-ranked SKUs for a product from data/product-similarities.json.
 *
 * Originally a fallback for the now-retired complete-the-look cross-sell.
 * Retained because the CLIP-embedding similarity data is still useful for
 * future ranking surfaces (search, recommendations, internal QA). Safe to
 * remove if no consumer materializes.
 *
 * @since 1.5.4
 *
 * @param  string $sku   Source SKU.
 * @param  int    $limit Max number of related SKUs to return.
 * @return array<int, string> Related SKUs, highest similarity first.
 */
function skyyrose_get_similarity_skus( $sku, $limit = 2 ) {
	static $data  = null;
	static $cache = array();

	$sku = sanitize_key( $sku );
	if ( '' === $sku ) {
		return array();
	}

	$cache_key = $sku . ':' . absint( $limit );
	if ( isset( $cache[ $cache_key ] ) ) {
		return $cache[ $cache_key ];
	}

	// Load + memoize the JSON once per request.
	if ( null === $data ) {
		$path = get_theme_file_path( 'data/product-similarities.json' );
		if ( ! is_readable( $path ) ) {
			$data = array();
		} else {
			// phpcs:ignore WordPress.WP.AlternativeFunctions.file_get_contents_file_get_contents -- local theme file read.
			$raw = file_get_contents( $path );
			if ( false === $raw || '' === $raw ) {
				$data = array();
			} else {
				$decoded = json_decode( $raw, true );
				$data    = ( is_array( $decoded ) && isset( $decoded['products'] ) && is_array( $decoded['products'] ) )
					? $decoded['products']
					: array();
			}
		}
	}

	if ( ! isset( $data[ $sku ]['global'] ) || ! is_array( $data[ $sku ]['global'] ) ) {
		$cache[ $cache_key ] = array();
		return array();
	}

	$result = array();
	foreach ( $data[ $sku ]['global'] as $entry ) {
		if ( isset( $entry['sku'] ) && is_string( $entry['sku'] ) ) {
			$result[] = sanitize_key( $entry['sku'] );
			if ( count( $result ) >= absint( $limit ) ) {
				break;
			}
		}
	}

	$cache[ $cache_key ] = $result;
	return $result;
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
		return home_url( '/collections/' . sanitize_title( $product['collection'] ) . '/#' . sanitize_title( $sku ) );
	}

	return home_url( '/pre-order/#' . sanitize_title( $sku ) );
}
