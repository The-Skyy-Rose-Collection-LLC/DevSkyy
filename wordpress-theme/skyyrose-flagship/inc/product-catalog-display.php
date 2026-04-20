<?php
/**
 * Product Catalog — Display Layer
 *
 * Projections, resolvers, and view helpers that sit on top of the raw
 * product catalog data in `inc/product-catalog.php`. Extracted from that
 * file in v6.5.1 to keep each module under the 800-line cap.
 *
 * Split rationale:
 *   - `inc/product-catalog.php`          → data source: catalog array,
 *                                          SKU lookups, formatters, URLs.
 *   - `inc/product-catalog-display.php`  → projections that resolve catalog
 *                                          entries into WC_Product-or-static-card
 *                                          display arrays for template parts,
 *                                          including featured rotation, preorder
 *                                          grouping, and transient cache.
 *
 * All functions in this file depend on helpers defined in product-catalog.php,
 * so this file MUST be required AFTER product-catalog.php in functions.php.
 *
 * @package SkyyRose
 * @since   6.5.1
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Build the display-shaped static card from a raw catalog entry.
 *
 * Single source of truth for the catalog-fallback card shape consumed by
 * `template-parts/product-card-holo.php`. Called from both the cold-path
 * resolver and the transient cache rehydration loop, so the two code
 * paths cannot drift — blank fields and dead `#` CTAs regress the moment
 * the shapes stop matching.
 *
 * All `$cat` accesses are `?? ''` guarded so a thinner array (e.g. a
 * partial catalog snapshot from a plugin filter) degrades to empty
 * strings rather than emitting `E_WARNING: Undefined array key` under
 * PHP 8.x.
 *
 * @since  6.5.2
 * @access private
 * @see    skyyrose_resolve_display_products() Cold-path caller.
 * @see    skyyrose_get_featured_display_products() Rehydration caller.
 * @param  array $cat Raw catalog entry.
 * @return array      Display-shaped static card.
 */
function skyyrose_catalog_to_static_card( array $cat ) {
	$sku = (string) ( $cat['sku'] ?? '' );
	// Preserve the original `?:` fall-through semantics (empty string
	// falls through to `image`), not `??` which only falls through on null.
	$front_source = ( $cat['front_model_image'] ?? '' ) ?: ( $cat['image'] ?? '' );
	return array(
		'title'      => $cat['name'] ?? '',
		'price'      => skyyrose_format_price( $cat ),
		'badge_text' => $cat['badge'] ?? '',
		'sku'        => $sku,
		'image_url'  => skyyrose_product_image_uri( $front_source ),
		'image_back' => skyyrose_product_image_uri( $cat['back_image'] ?? '' ),
		'collection' => $cat['collection'] ?? '',
		// Resolve a real URL via skyyrose_product_url() — routes through WC
		// permalink → preorder anchor → collection anchor fallback. Prevents
		// the homepage featured grid from rendering dead href="#" CTAs when
		// a curated SKU has no matching WC product. No function_exists guard
		// here: product-catalog.php is a hard require for this file, matching
		// the unguarded skyyrose_format_price() call above.
		'permalink'  => skyyrose_product_url( $sku ),
	);
}

/**
 * Resolve a list of catalog entries into the mixed display array that the
 * holo card template consumes. Shared by the collection, featured, and SKU
 * code paths so the WC-first / catalog-fallback logic lives in exactly one
 * place. Applies the same visibility filter (skip unpublished non-preorder)
 * everywhere.
 *
 * Each returned item is either a WC_Product (when a matching WooCommerce
 * product exists) or a static card array compatible with product-card-holo.
 *
 * @since  6.5.0
 * @access private
 * @param  array $catalog_entries Array of catalog product arrays.
 * @return array                  Mixed display array (WC_Product | static card).
 */
function skyyrose_resolve_display_products( array $catalog_entries ) {
	$has_wc  = function_exists( 'wc_get_product_id_by_sku' );
	$display = array();

	foreach ( $catalog_entries as $cat ) {
		// Skip unpublished, non-preorder products (visibility rule).
		if ( empty( $cat['published'] ) && empty( $cat['is_preorder'] ) ) {
			continue;
		}

		// Try to match to a WC product by SKU (primary, then normalized).
		$wc_product = null;
		if ( $has_wc ) {
			$product_id = wc_get_product_id_by_sku( $cat['sku'] );
			if ( ! $product_id ) {
				$product_id = wc_get_product_id_by_sku( skyyrose_normalize_sku( $cat['sku'] ) );
			}
			if ( $product_id ) {
				$wc_product = wc_get_product( $product_id );
			}
		}

		if ( $wc_product ) {
			// WC product found — use it (holo card pulls catalog images as fallback).
			$display[] = $wc_product;
		} else {
			// No WC match — use static card from catalog. Log under WP_DEBUG so a
			// silent drift from "live WC product" → "stale catalog snapshot" is
			// diagnosable by shop operators on every request.
			if ( $has_wc && defined( 'WP_DEBUG' ) && WP_DEBUG ) {
				trigger_error(
					sprintf(
						'skyyrose catalog: SKU %s has no WC match — rendering static card fallback.',
						esc_html( $cat['sku'] )
					),
					E_USER_NOTICE
				);
			}
			$display[] = skyyrose_catalog_to_static_card( $cat );
		}
	}

	return $display;
}

/**
 * Get collection products for display — catalog is source of truth.
 *
 * Returns an array of items ready to pass to get_template_part('product-card-holo').
 * Each item is either a WC_Product (matched by SKU from catalog) or a static
 * card array from the catalog. The PHP catalog controls WHAT shows and in WHAT
 * ORDER. WooCommerce just provides live pricing, stock, and add-to-cart.
 *
 * @since  6.4.0
 * @param  string $collection Collection slug (e.g., 'black-rose').
 * @return array  Mixed array — WC_Product objects or static card arrays.
 */
function skyyrose_get_collection_display_products( $collection ) {
	return skyyrose_resolve_display_products( skyyrose_get_collection_products( $collection ) );
}

/**
 * Get products filtered for the pre-order gateway.
 *
 * Returns only published products with active pre-orders,
 * grouped by collection in display order.
 *
 * @since  3.2.1
 * @return array Associative array keyed by collection slug.
 */
function skyyrose_get_preorder_products() {
	$catalog     = skyyrose_get_product_catalog();
	$collections = array(
		'black-rose'   => array(),
		'love-hurts'   => array(),
		'signature'    => array(),
		'kids-capsule' => array(),
	);

	foreach ( $catalog as $product ) {
		if ( $product['is_preorder'] && $product['published'] ) {
			if ( ! isset( $collections[ $product['collection'] ] ) ) {
				$collections[ $product['collection'] ] = array();
			}
			$collections[ $product['collection'] ][] = $product;
		}
	}

	return $collections;
}

/**
 * Get the curated featured cross-collection catalog entries for the homepage.
 *
 * Returns an ordered array of catalog entries representing one flagship
 * piece from each collection plus a small rotation of staples. The
 * homepage featured grid consumes this via skyyrose_get_featured_display_products()
 * which applies the same WC-first / catalog-fallback pattern the collection
 * grids use.
 *
 * The SKU list can be overridden via the `skyyrose_featured_product_skus`
 * filter — this lets a child theme or site plugin curate the featured set
 * without modifying core theme files.
 *
 * @since  6.5.0
 * @param  int $limit Max number of entries. Pass 0 (or any value <= 0) for no cap.
 * @return array      Ordered array of catalog entries.
 */
function skyyrose_get_featured_catalog_products( $limit = 8 ) {
	// Curated featured rotation — one or two flagships per collection, in
	// a natural browsing order (signature → black rose → love hurts → kids).
	$default_skus = array(
		'sg-015',  // The Windbreaker Set
		'br-004',  // BLACK Rose Hoodie
		'br-008',  // SF Inspired Football Jersey
		'lh-004',  // Love Hurts Bomber Jacket
		'sg-006',  // Mint & Lavender Hoodie
		'br-010',  // The Bay Basketball Jersey
		'sg-013',  // Mint & Lavender Crewneck
		'kids-001', // Kids Colorblock Set (Red/Black)
	);

	/**
	 * Filters the curated featured product SKUs shown on the homepage.
	 *
	 * Return an ordered list of SKU strings. Unknown SKUs are silently
	 * skipped when the catalog is resolved downstream (logged under
	 * WP_DEBUG so child-theme authors can catch typos quickly).
	 *
	 * @since 6.5.0
	 * @param string[] $default_skus Default featured SKU list.
	 */
	$featured_skus = apply_filters( 'skyyrose_featured_product_skus', $default_skus );

	$catalog  = skyyrose_get_product_catalog();
	$featured = array();
	$cap      = max( 0, (int) $limit ); // 0 = no cap
	$debug    = defined( 'WP_DEBUG' ) && WP_DEBUG;

	foreach ( (array) $featured_skus as $sku ) {
		if ( $cap > 0 && count( $featured ) >= $cap ) {
			break;
		}
		if ( isset( $catalog[ $sku ] ) ) {
			$featured[] = $catalog[ $sku ];
		} elseif ( $debug ) {
			trigger_error(
				sprintf(
					'skyyrose_featured_product_skus: unknown SKU %s — not in catalog, skipped.',
					esc_html( (string) $sku )
				),
				E_USER_WARNING
			);
		}
	}

	return $featured;
}

/**
 * Get featured products shaped for display (WC_Product or static card).
 *
 * Thin wrapper around the shared resolver — the catalog-level featured list
 * is fed through the same WC-first / catalog-fallback path the collection
 * grids use, keeping homepage visibility rules consistent with collection
 * and shop surfaces.
 *
 * ## Caching strategy
 *
 * Two-tier: a per-request static cache (fastest path) in front of a
 * 5-minute transient (survives across requests). The transient does NOT
 * store WC_Product objects directly — those are heavy, serialize poorly,
 * and go stale for price/stock the moment they land in the option table.
 * Instead we cache a lightweight "descriptor" list (wc id or catalog sku)
 * and rehydrate into live WC_Product / catalog entries on cache hit.
 * wc_get_product() and skyyrose_get_product() each have their own internal
 * caches so rehydration is cheap — still a ~10x speedup over re-running
 * the full resolver on every request.
 *
 * Invalidation hooks live at `skyyrose_flush_featured_display_cache()`
 * below — transients are dropped on any product save, WC update, or trash.
 *
 * @since  6.5.0
 * @param  int $limit Max number of entries. Pass 0 (or any value <= 0) for no cap.
 * @return array      Mixed array — WC_Product objects or static card arrays.
 */
function skyyrose_get_featured_display_products( $limit = 8 ) {
	static $runtime_cache = array();

	$key = (int) $limit;

	// Tier 1 — per-request static cache.
	if ( isset( $runtime_cache[ $key ] ) ) {
		return $runtime_cache[ $key ];
	}

	// Tier 2 — cross-request transient cache holding lightweight descriptors.
	$transient_key = 'skyyrose_featured_display_' . $key;
	$descriptors   = get_transient( $transient_key );

	if ( false === $descriptors || ! is_array( $descriptors ) ) {
		$resolved    = skyyrose_resolve_display_products(
			skyyrose_get_featured_catalog_products( $key )
		);
		$descriptors = array();
		foreach ( $resolved as $entry ) {
			if ( class_exists( 'WC_Product' ) && $entry instanceof WC_Product ) {
				$descriptors[] = array(
					'type' => 'wc',
					'id'   => (int) $entry->get_id(),
				);
			} elseif ( is_array( $entry ) && ! empty( $entry['sku'] ) ) {
				$descriptors[] = array(
					'type' => 'catalog',
					'sku'  => (string) $entry['sku'],
				);
			}
		}
		set_transient( $transient_key, $descriptors, 5 * MINUTE_IN_SECONDS );
	}

	// Rehydrate descriptors back into live products. wc_get_product() is
	// internally cached by WC, so this is O(n) memory lookups on a hot path.
	$hydrated = array();
	foreach ( $descriptors as $desc ) {
		if ( 'wc' === $desc['type'] && function_exists( 'wc_get_product' ) ) {
			$product = wc_get_product( (int) $desc['id'] );
			if ( $product ) {
				$hydrated[] = $product;
			}
		} elseif ( 'catalog' === $desc['type'] && function_exists( 'skyyrose_get_product' ) ) {
			$sku = (string) $desc['sku'];
			$cat = skyyrose_get_product( $sku );
			// Re-check visibility — descriptors are a point-in-time snapshot,
			// and catalog entries can flip 'published' between cache write and
			// cache read (plugin filter, code deploy, etc.). WC product edits
			// are covered by the save_post_product / woocommerce_update_product
			// flush hooks wired below; this guard covers pure-catalog drift.
			if ( $cat && ( ! empty( $cat['published'] ) || ! empty( $cat['is_preorder'] ) ) ) {
				$hydrated[] = skyyrose_catalog_to_static_card( $cat );
			} elseif ( defined( 'WP_DEBUG' ) && WP_DEBUG ) {
				// Symmetric with the cold-path WP_DEBUG trigger_error in
				// skyyrose_resolve_display_products() — a shop operator
				// debugging "why did my homepage card disappear" should see
				// matching log lines from both the cold and rehydration paths.
				trigger_error(
					sprintf(
						'skyyrose featured cache: catalog descriptor SKU %s dropped on rehydration (%s).',
						esc_html( $sku ),
						$cat ? 'not published' : 'missing from catalog'
					),
					E_USER_NOTICE
				);
			}
		}
	}

	$runtime_cache[ $key ] = $hydrated;
	return $hydrated;
}

/**
 * Flush cached featured display products when product data changes.
 *
 * The transient cache in skyyrose_get_featured_display_products() is keyed
 * by $limit. We blast the common limits here; anything uncommon ages out
 * via the 5-minute TTL. Wired into WC + core post hooks below.
 *
 * @since 6.5.0
 * @return void
 */
function skyyrose_flush_featured_display_cache() {
	// Common limits observed in the codebase: 4 (landing lead-in),
	// 6/8 (homepage featured), 12/16 (shop-ish grids), 0 (no cap).
	$common_limits = array( 0, 4, 6, 8, 10, 12, 16, 20, 24 );
	foreach ( $common_limits as $l ) {
		delete_transient( 'skyyrose_featured_display_' . $l );
	}
}

add_action( 'save_post_product', 'skyyrose_flush_featured_display_cache' );
add_action( 'woocommerce_update_product', 'skyyrose_flush_featured_display_cache' );
add_action( 'woocommerce_delete_product', 'skyyrose_flush_featured_display_cache' );
add_action( 'woocommerce_trash_product', 'skyyrose_flush_featured_display_cache' );
add_action( 'trashed_post', 'skyyrose_flush_featured_display_cache' );
add_action( 'untrashed_post', 'skyyrose_flush_featured_display_cache' );
