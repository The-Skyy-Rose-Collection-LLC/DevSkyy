<?php
/**
 * SEO Discovery
 *
 * Sitemaps, robots directives, collection schemas, and favicon output.
 *
 * @package SkyyRose
 * @since   7.2.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Add XML sitemap support.
 *
 * @since 1.0.0
 */
function skyyrose_add_sitemap_support() {
	add_theme_support( 'core-sitemaps' );
}
add_action( 'after_setup_theme', 'skyyrose_add_sitemap_support' );

/**
 * Filter a single sitemap entry for products to add images.
 *
 * @since 1.0.0
 *
 * @param array  $entry     Single sitemap entry with 'loc' key.
 * @param string $post_type Post type name.
 * @return array Modified entry.
 */
function skyyrose_filter_product_sitemap( $entry, $post_type ) {
	if ( 'product' !== $post_type || ! function_exists( 'wc_get_product' ) ) {
		return $entry;
	}

	$product_id = url_to_postid( $entry['loc'] );
	if ( $product_id ) {
		$product = wc_get_product( $product_id );
		if ( $product && $product->get_image_id() ) {
			$entry['images'] = array(
				array(
					'src'   => wp_get_attachment_url( absint( $product->get_image_id() ) ),
					'title' => $product->get_name(),
				),
			);
		}
	}

	return $entry;
}
add_filter( 'wp_sitemaps_posts_entry', 'skyyrose_filter_product_sitemap', 10, 2 );

/**
 * Add robots meta tag.
 *
 * @since 1.0.0
 */
function skyyrose_robots_meta() {
	if ( is_search() || is_404() ) {
		echo '<meta name="robots" content="noindex,follow" />' . "\n";
	} elseif ( is_attachment() ) {
		echo '<meta name="robots" content="noindex,nofollow" />' . "\n";
	}
}
add_action( 'wp_head', 'skyyrose_robots_meta', 1 );

/**
 * Add Collection schema for product categories.
 *
 * Skips output when Yoast SEO is active to prevent duplicate structured data.
 *
 * @since 1.0.0
 */
function skyyrose_collection_schema() {
	if ( ! is_tax( 'product_cat' ) && ! is_post_type_archive( 'product' ) ) {
		return;
	}

	// Defer to Yoast SEO if active.
	if ( defined( 'WPSEO_VERSION' ) ) {
		return;
	}

	$term = get_queried_object();

	$schema = array(
		'@context'    => 'https://schema.org',
		'@type'       => 'CollectionPage',
		'name'        => is_tax( 'product_cat' ) ? $term->name : __( 'Products', 'skyyrose' ),
		'description' => is_tax( 'product_cat' ) ? term_description() : get_bloginfo( 'description' ),
		'url'         => is_tax( 'product_cat' ) ? get_term_link( $term ) : get_post_type_archive_link( 'product' ),
	);

	echo '<script type="application/ld+json">' . wp_json_encode( $schema, JSON_HEX_TAG | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES ) . '</script>' . "\n"; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- JSON-encoded with JSON_HEX_TAG preventing script injection.
}
add_action( 'wp_head', 'skyyrose_collection_schema', 1 );

/**
 * Output ItemList JSON-LD schema for custom collection page templates.
 *
 * Fires on the four SkyyRose collection page templates which are WP pages,
 * not WooCommerce taxonomies, so skyyrose_collection_schema() doesn't fire.
 * Uses the CSV-backed catalog via skyyrose_get_collection_products().
 *
 * Skips output when Yoast SEO is active.
 *
 * @since 1.0.0
 */
function skyyrose_collection_itemlist_schema() {
	// Defer to Yoast SEO if active.
	if ( defined( 'WPSEO_VERSION' ) ) {
		return;
	}

	if ( ! function_exists( 'skyyrose_get_collection_products' ) || ! function_exists( 'skyyrose_product_url' ) ) {
		return;
	}

	$collection_map = array(
		'template-collection-black-rose.php'   => array(
			'slug'  => 'black-rose',
			'label' => 'Black Rose Collection',
		),
		'template-collection-love-hurts.php'   => array(
			'slug'  => 'love-hurts',
			'label' => 'Love Hurts Collection',
		),
		'template-collection-signature.php'    => array(
			'slug'  => 'signature',
			'label' => 'Signature Collection',
		),
		'template-collection-kids-capsule.php' => array(
			'slug'  => 'kids-capsule',
			'label' => 'Kids Capsule Collection',
		),
		'template-landing-black-rose.php'      => array(
			'slug'  => 'black-rose',
			'label' => 'Black Rose Collection',
		),
		'template-landing-love-hurts.php'      => array(
			'slug'  => 'love-hurts',
			'label' => 'Love Hurts Collection',
		),
		'template-landing-signature.php'       => array(
			'slug'  => 'signature',
			'label' => 'Signature Collection',
		),
		'template-landing-kids-capsule.php'    => array(
			'slug'  => 'kids-capsule',
			'label' => 'Kids Capsule Collection',
		),
	);

	$matched = null;
	foreach ( $collection_map as $tpl_file => $col_data ) {
		if ( is_page_template( $tpl_file ) ) {
			$matched = $col_data;
			break;
		}
	}

	if ( null === $matched ) {
		return;
	}

	$products = skyyrose_get_collection_products( $matched['slug'] );

	if ( empty( $products ) ) {
		return;
	}

	$items    = array();
	$position = 1;

	foreach ( $products as $product ) {
		// Only include published products in the schema.
		if ( empty( $product['published'] ) ) {
			continue;
		}

		$product_url = skyyrose_product_url( $product['sku'] );

		$item = array(
			'@type'    => 'ListItem',
			'position' => $position,
			'url'      => $product_url,
			'name'     => $product['name'],
		);

		// Add price when available.
		if ( ! empty( $product['price'] ) && $product['price'] > 0 ) {
			$item['offers'] = array(
				'@type'         => 'Offer',
				'price'         => $product['price'],
				'priceCurrency' => 'USD',
				'availability'  => 'https://schema.org/InStock',
			);
		}

		$items[] = $item;
		++$position;
	}

	if ( empty( $items ) ) {
		return;
	}

	$schema = array(
		'@context'        => 'https://schema.org',
		'@type'           => 'ItemList',
		'name'            => $matched['label'],
		'url'             => get_permalink(),
		'numberOfItems'   => count( $items ),
		'itemListElement' => $items,
	);

	echo '<script type="application/ld+json">' . wp_json_encode( $schema, JSON_HEX_TAG | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES ) . '</script>' . "\n"; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- JSON-encoded with JSON_HEX_TAG preventing script injection.
}
add_action( 'wp_head', 'skyyrose_collection_itemlist_schema', 1 );

/**
 * Output favicon and touch icon tags.
 *
 * Uses the SR monogram favicon from the theme's assets. WordPress's
 * Site Icon customizer setting takes priority if configured — this
 * serves as the theme-level fallback.
 *
 * @since 4.0.0
 */
function skyyrose_favicon_tags() {
	// Skip if the user has set a Site Icon via Customizer.
	if ( has_site_icon() ) {
		return;
	}

	$uri = get_template_directory_uri();
	?>
	<link rel="icon" type="image/webp" sizes="32x32" href="<?php echo esc_url( $uri . '/assets/branding/skyyrose-rose-icon-favicon.webp' ); ?>">
	<link rel="apple-touch-icon" sizes="180x180" href="<?php echo esc_url( $uri . '/assets/images/logos/sr-monogram-rose-gold.webp?v=' . SKYYROSE_VERSION ); ?>">
	<?php
}
add_action( 'wp_head', 'skyyrose_favicon_tags', 2 );
