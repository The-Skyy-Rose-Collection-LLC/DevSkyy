<?php
/**
 * SEO Optimization Features
 *
 * Structured data (Schema.org), Open Graph, Twitter Cards, canonical URLs,
 * meta descriptions, title optimization, sitemap support, and robots meta.
 *
 * All schema/meta functions defer to Yoast SEO when active to prevent duplication.
 *
 * Extracted from accessibility-seo.php in iteration 28 to keep files under 800 lines.
 *
 * @package SkyyRose_Flagship
 * @since   1.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Add Schema.org markup for products.
 *
 * Skips output when Yoast SEO (with WooCommerce SEO add-on) is active
 * to prevent duplicate product structured data.
 *
 * @since 1.0.0
 */
function skyyrose_product_schema() {
	if ( ! is_singular( 'product' ) ) {
		return;
	}

	// Defer to Yoast WooCommerce SEO if active.
	if ( defined( 'WPSEO_WOO_VERSION' ) ) {
		return;
	}

	global $product;

	if ( ! is_a( $product, 'WC_Product' ) ) {
		return;
	}

	$schema = array(
		'@context'    => 'https://schema.org/',
		'@type'       => 'Product',
		'name'        => $product->get_name(),
		'description' => wp_strip_all_tags( $product->get_short_description() ?: $product->get_description() ),
		'sku'         => $product->get_sku(),
		'image'       => wp_get_attachment_url( $product->get_image_id() ),
		'offers'      => array(
			'@type'         => 'Offer',
			'url'           => get_permalink( $product->get_id() ),
			'priceCurrency' => get_woocommerce_currency(),
			'price'         => $product->is_type( 'variable' ) ? $product->get_variation_price( 'min' ) : $product->get_price(),
			'availability'  => $product->is_in_stock() ? 'https://schema.org/InStock' : 'https://schema.org/OutOfStock',
		),
	);

	// Add brand if available (sanitize for safe JSON-LD output).
	$brand = sanitize_text_field( get_post_meta( $product->get_id(), '_product_brand', true ) );
	if ( $brand ) {
		$schema['brand'] = array(
			'@type' => 'Brand',
			'name'  => $brand,
		);
	}

	// Add aggregate rating if available.
	if ( $product->get_average_rating() ) {
		$schema['aggregateRating'] = array(
			'@type'       => 'AggregateRating',
			'ratingValue' => $product->get_average_rating(),
			'reviewCount' => $product->get_review_count(),
		);
	}

	// Add reviews.
	$reviews = get_comments( array(
		'post_id' => $product->get_id(),
		'status'  => 'approve',
		'type'    => 'review',
		'number'  => 5,
	) );

	if ( ! empty( $reviews ) ) {
		$schema['review'] = array();
		foreach ( $reviews as $review ) {
			$rating = get_comment_meta( $review->comment_ID, 'rating', true );
			if ( $rating ) {
				$schema['review'][] = array(
					'@type'         => 'Review',
					'author'        => array(
						'@type' => 'Person',
						'name'  => wp_strip_all_tags( $review->comment_author ),
					),
					'reviewRating'  => array(
						'@type'       => 'Rating',
						'ratingValue' => $rating,
					),
					'reviewBody'    => wp_strip_all_tags( $review->comment_content ),
					'datePublished' => mysql2date( 'c', $review->comment_date ),
				);
			}
		}
	}

	echo '<script type="application/ld+json">' . wp_json_encode( $schema ) . '</script>' . "\n";
}
add_action( 'wp_head', 'skyyrose_product_schema' );

/**
 * Add Organization schema markup for SkyyRose LLC.
 *
 * Outputs JSON-LD Organization structured data on the front page.
 * Skips output when Yoast SEO is active and handles Organization schema.
 *
 * @since 1.0.0
 */
function skyyrose_organization_schema() {
	if ( ! is_front_page() ) {
		return;
	}

	// Defer to Yoast SEO for Organization schema if active.
	if ( defined( 'WPSEO_VERSION' ) ) {
		return;
	}

	$logo_url = '';
	$logo_id  = get_theme_mod( 'custom_logo' );
	if ( $logo_id ) {
		$logo_url = wp_get_attachment_url( $logo_id );
	}

	$schema = array(
		'@context'    => 'https://schema.org',
		'@type'       => 'Organization',
		'name'        => 'SkyyRose',
		'legalName'   => 'SkyyRose LLC',
		'url'         => home_url( '/' ),
		'description' => __( 'Luxury Grows from Concrete. Premium streetwear and luxury fashion brand.', 'skyyrose-flagship' ),
		'logo'        => $logo_url ? array(
			'@type' => 'ImageObject',
			'url'   => $logo_url,
		) : null,
		'brand'       => array(
			'@type' => 'Brand',
			'name'  => 'SkyyRose',
			'slogan' => 'Luxury Grows from Concrete.',
		),
		'sameAs'      => array(),
	);

	// Add social media profiles from Customizer settings.
	$social_profiles = array(
		'facebook'  => get_theme_mod( 'facebook_url' ),
		'twitter'   => get_theme_mod( 'twitter_url' ),
		'instagram' => get_theme_mod( 'instagram_url' ),
		'linkedin'  => get_theme_mod( 'linkedin_url' ),
		'youtube'   => get_theme_mod( 'youtube_url' ),
	);

	foreach ( $social_profiles as $profile ) {
		if ( ! empty( $profile ) ) {
			$schema['sameAs'][] = esc_url( $profile );
		}
	}

	// Add contact information.
	$phone = get_theme_mod( 'contact_phone' );
	$email = get_theme_mod( 'contact_email' );

	if ( $phone || $email ) {
		$schema['contactPoint'] = array(
			'@type'       => 'ContactPoint',
			'contactType' => 'customer service',
		);

		if ( $phone ) {
			$schema['contactPoint']['telephone'] = sanitize_text_field( $phone );
		}
		if ( $email ) {
			$schema['contactPoint']['email'] = sanitize_email( $email );
		}
	}

	// Remove null fields (e.g., logo when no custom logo is set).
	$schema = array_filter( $schema, function ( $v ) { return null !== $v; } );

	echo '<script type="application/ld+json">' . wp_json_encode( $schema ) . '</script>' . "\n";
}
add_action( 'wp_head', 'skyyrose_organization_schema' );

/**
 * Add BreadcrumbList schema markup.
 *
 * Skips output when Yoast SEO is active to prevent duplicate breadcrumb schema.
 *
 * @since 1.0.0
 */
function skyyrose_breadcrumb_schema() {
	if ( is_front_page() ) {
		return;
	}

	// Defer to Yoast SEO for breadcrumb schema if active.
	if ( defined( 'WPSEO_VERSION' ) ) {
		return;
	}

	$breadcrumbs = skyyrose_get_breadcrumb_trail();

	if ( empty( $breadcrumbs ) ) {
		return;
	}

	$schema = array(
		'@context'        => 'https://schema.org',
		'@type'           => 'BreadcrumbList',
		'itemListElement' => array(),
	);

	$position = 1;
	foreach ( $breadcrumbs as $breadcrumb ) {
		$schema['itemListElement'][] = array(
			'@type'    => 'ListItem',
			'position' => $position,
			'name'     => $breadcrumb['title'],
			'item'     => $breadcrumb['url'],
		);
		$position++;
	}

	echo '<script type="application/ld+json">' . wp_json_encode( $schema ) . '</script>' . "\n";
}
add_action( 'wp_head', 'skyyrose_breadcrumb_schema' );

/**
 * Get breadcrumb trail.
 *
 * @since 1.0.0
 *
 * @return array Breadcrumb items.
 */
function skyyrose_get_breadcrumb_trail() {
	$breadcrumbs = array(
		array(
			'title' => __( 'Home', 'skyyrose-flagship' ),
			'url'   => home_url( '/' ),
		),
	);

	if ( is_singular( 'product' ) && function_exists( 'wc_get_page_id' ) ) {
		$breadcrumbs[] = array(
			'title' => __( 'Shop', 'skyyrose-flagship' ),
			'url'   => get_permalink( wc_get_page_id( 'shop' ) ),
		);

		$terms = get_the_terms( get_the_ID(), 'product_cat' );
		if ( $terms && ! is_wp_error( $terms ) ) {
			$term = array_shift( $terms );
			$breadcrumbs[] = array(
				'title' => wp_strip_all_tags( html_entity_decode( $term->name, ENT_QUOTES, 'UTF-8' ) ),
				'url'   => get_term_link( $term ),
			);
		}

		$breadcrumbs[] = array(
			'title' => wp_strip_all_tags( html_entity_decode( get_the_title(), ENT_QUOTES, 'UTF-8' ) ),
			'url'   => get_permalink(),
		);
	} elseif ( function_exists( 'wc_get_page_id' ) && ( is_post_type_archive( 'product' ) || is_shop() ) ) {
		$breadcrumbs[] = array(
			'title' => __( 'Shop', 'skyyrose-flagship' ),
			'url'   => get_permalink( wc_get_page_id( 'shop' ) ),
		);
	} elseif ( function_exists( 'wc_get_page_id' ) && is_tax( 'product_cat' ) ) {
		$breadcrumbs[] = array(
			'title' => __( 'Shop', 'skyyrose-flagship' ),
			'url'   => get_permalink( wc_get_page_id( 'shop' ) ),
		);

		$term = get_queried_object();
		$breadcrumbs[] = array(
			'title' => wp_strip_all_tags( html_entity_decode( $term->name, ENT_QUOTES, 'UTF-8' ) ),
			'url'   => get_term_link( $term ),
		);
	} elseif ( is_singular( 'post' ) ) {
		$categories = get_the_category();
		if ( $categories ) {
			$category = array_shift( $categories );
			$breadcrumbs[] = array(
				'title' => wp_strip_all_tags( html_entity_decode( $category->name, ENT_QUOTES, 'UTF-8' ) ),
				'url'   => get_category_link( $category->term_id ),
			);
		}

		$breadcrumbs[] = array(
			'title' => get_the_title(),
			'url'   => get_permalink(),
		);
	} elseif ( is_page() ) {
		$breadcrumbs[] = array(
			'title' => get_the_title(),
			'url'   => get_permalink(),
		);
	} elseif ( is_category() ) {
		$breadcrumbs[] = array(
			'title' => single_cat_title( '', false ),
			'url'   => get_category_link( get_queried_object_id() ),
		);
	} elseif ( is_search() ) {
		$breadcrumbs[] = array(
			'title' => sprintf( __( 'Search Results for: %s', 'skyyrose-flagship' ), esc_html( get_search_query() ) ),
			'url'   => '',
		);
	}

	return $breadcrumbs;
}

/**
 * Display breadcrumb navigation.
 *
 * @since 1.0.0
 */
function skyyrose_breadcrumb() {
	if ( is_front_page() ) {
		return;
	}

	$breadcrumbs = skyyrose_get_breadcrumb_trail();

	if ( empty( $breadcrumbs ) ) {
		return;
	}

	echo '<nav class="breadcrumb-navigation" aria-label="' . esc_attr__( 'Breadcrumb', 'skyyrose-flagship' ) . '">';
	echo '<ol class="breadcrumbs" itemscope itemtype="https://schema.org/BreadcrumbList">';

	$position = 1;
	$last_index = count( $breadcrumbs ) - 1;

	foreach ( $breadcrumbs as $index => $breadcrumb ) {
		$is_last = ( $index === $last_index );

		echo '<li itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">';

		if ( $is_last ) {
			echo '<span itemprop="name" aria-current="page">' . esc_html( $breadcrumb['title'] ) . '</span>';
		} else {
			echo '<a href="' . esc_url( $breadcrumb['url'] ) . '" itemprop="item">';
			echo '<span itemprop="name">' . esc_html( $breadcrumb['title'] ) . '</span>';
			echo '</a>';
		}

		echo '<meta itemprop="position" content="' . esc_attr( $position ) . '" />';
		echo '</li>';

		$position++;
	}

	echo '</ol>';
	echo '</nav>';
}
add_action( 'skyyrose_after_header', 'skyyrose_breadcrumb', 10 );

/**
 * Add Open Graph tags.
 *
 * Skips output when Yoast SEO is active to prevent duplicate meta tags.
 *
 * @since 1.0.0
 */
function skyyrose_open_graph_tags() {
	// Defer to Yoast SEO if active.
	if ( defined( 'WPSEO_VERSION' ) ) {
		return;
	}

	if ( is_singular() ) {
		global $post;

		echo '<meta property="og:type" content="' . esc_attr( is_singular( 'product' ) ? 'product' : 'article' ) . '" />' . "\n";
		echo '<meta property="og:title" content="' . esc_attr( get_the_title() ) . '" />' . "\n";
		echo '<meta property="og:description" content="' . esc_attr( wp_strip_all_tags( get_the_excerpt() ) ) . '" />' . "\n";
		echo '<meta property="og:url" content="' . esc_url( get_permalink() ) . '" />' . "\n";
		echo '<meta property="og:site_name" content="' . esc_attr( get_bloginfo( 'name' ) ) . '" />' . "\n";

		if ( has_post_thumbnail() ) {
			$image_url = get_the_post_thumbnail_url( $post->ID, 'full' );
			echo '<meta property="og:image" content="' . esc_url( $image_url ) . '" />' . "\n";
			echo '<meta property="og:image:width" content="1200" />' . "\n";
			echo '<meta property="og:image:height" content="630" />' . "\n";
		}

		// Product-specific OG tags.
		if ( is_singular( 'product' ) ) {
			$product = wc_get_product( $post->ID );
			if ( $product ) {
				echo '<meta property="product:price:amount" content="' . esc_attr( $product->get_price() ) . '" />' . "\n";
				echo '<meta property="product:price:currency" content="' . esc_attr( get_woocommerce_currency() ) . '" />' . "\n";
				echo '<meta property="product:availability" content="' . esc_attr( $product->is_in_stock() ? 'in stock' : 'out of stock' ) . '" />' . "\n";
			}
		}
	} elseif ( is_front_page() ) {
		echo '<meta property="og:type" content="website" />' . "\n";
		echo '<meta property="og:title" content="' . esc_attr( get_bloginfo( 'name' ) ) . '" />' . "\n";
		echo '<meta property="og:description" content="' . esc_attr( get_bloginfo( 'description' ) ) . '" />' . "\n";
		echo '<meta property="og:url" content="' . esc_url( home_url( '/' ) ) . '" />' . "\n";
		echo '<meta property="og:site_name" content="' . esc_attr( get_bloginfo( 'name' ) ) . '" />' . "\n";

		$logo_id = get_theme_mod( 'custom_logo' );
		if ( $logo_id ) {
			$logo_url = wp_get_attachment_url( $logo_id );
			echo '<meta property="og:image" content="' . esc_url( $logo_url ) . '" />' . "\n";
		}
	}
}
add_action( 'wp_head', 'skyyrose_open_graph_tags' );

/**
 * Add Twitter Card tags.
 *
 * Skips output when Yoast SEO is active to prevent duplicate meta tags.
 *
 * @since 1.0.0
 */
function skyyrose_twitter_card_tags() {
	// Defer to Yoast SEO if active.
	if ( defined( 'WPSEO_VERSION' ) ) {
		return;
	}

	echo '<meta name="twitter:card" content="summary_large_image" />' . "\n";

	$twitter_handle = get_theme_mod( 'twitter_handle' );
	if ( $twitter_handle ) {
		echo '<meta name="twitter:site" content="@' . esc_attr( str_replace( '@', '', $twitter_handle ) ) . '" />' . "\n";
	}

	if ( is_singular() ) {
		echo '<meta name="twitter:title" content="' . esc_attr( get_the_title() ) . '" />' . "\n";
		echo '<meta name="twitter:description" content="' . esc_attr( wp_strip_all_tags( get_the_excerpt() ) ) . '" />' . "\n";

		if ( has_post_thumbnail() ) {
			$image_url = get_the_post_thumbnail_url( get_the_ID(), 'full' );
			echo '<meta name="twitter:image" content="' . esc_url( $image_url ) . '" />' . "\n";
		}
	} elseif ( is_front_page() ) {
		echo '<meta name="twitter:title" content="' . esc_attr( get_bloginfo( 'name' ) ) . '" />' . "\n";
		echo '<meta name="twitter:description" content="' . esc_attr( get_bloginfo( 'description' ) ) . '" />' . "\n";

		$logo_id = get_theme_mod( 'custom_logo' );
		if ( $logo_id ) {
			$logo_url = wp_get_attachment_url( $logo_id );
			echo '<meta name="twitter:image" content="' . esc_url( $logo_url ) . '" />' . "\n";
		}
	}
}
add_action( 'wp_head', 'skyyrose_twitter_card_tags' );

/**
 * Add canonical URL.
 *
 * Skips output when Yoast SEO is active to prevent duplicate canonical tags.
 *
 * @since 1.0.0
 */
function skyyrose_canonical_url() {
	// Defer to Yoast SEO if active.
	if ( defined( 'WPSEO_VERSION' ) ) {
		return;
	}

	if ( is_singular() ) {
		echo '<link rel="canonical" href="' . esc_url( get_permalink() ) . '" />' . "\n";
	} elseif ( is_front_page() ) {
		echo '<link rel="canonical" href="' . esc_url( home_url( '/' ) ) . '" />' . "\n";
	} elseif ( is_post_type_archive( 'product' ) || is_shop() ) {
		echo '<link rel="canonical" href="' . esc_url( get_permalink( wc_get_page_id( 'shop' ) ) ) . '" />' . "\n";
	} elseif ( is_tax() || is_category() || is_tag() ) {
		echo '<link rel="canonical" href="' . esc_url( get_term_link( get_queried_object() ) ) . '" />' . "\n";
	}
}
add_action( 'wp_head', 'skyyrose_canonical_url', 1 );

/**
 * Add meta descriptions.
 *
 * Skips output when Yoast SEO is active to prevent duplicate meta descriptions.
 *
 * @since 1.0.0
 */
function skyyrose_meta_description() {
	// Defer to Yoast SEO if active.
	if ( defined( 'WPSEO_VERSION' ) ) {
		return;
	}

	$description = '';

	if ( is_singular() ) {
		$description = get_the_excerpt();
		if ( empty( $description ) ) {
			$description = wp_trim_words( get_the_content(), 30, '...' );
		}
	} elseif ( is_front_page() ) {
		$description = get_bloginfo( 'description' );
	} elseif ( is_category() ) {
		$description = category_description();
	} elseif ( is_tag() ) {
		$description = tag_description();
	} elseif ( is_tax( 'product_cat' ) ) {
		$description = term_description();
	}

	if ( ! empty( $description ) ) {
		$description = wp_strip_all_tags( $description );
		$description = str_replace( array( "\r", "\n", "\t" ), ' ', $description );
		$description = trim( preg_replace( '/\s+/', ' ', $description ) );

		echo '<meta name="description" content="' . esc_attr( wp_trim_words( $description, 30 ) ) . '" />' . "\n";
	}
}
add_action( 'wp_head', 'skyyrose_meta_description', 1 );

/**
 * Optimize title tags.
 *
 * @since 1.0.0
 *
 * @param string $title Document title.
 * @return string Modified title.
 */
function skyyrose_document_title( $title ) {
	$separator = '|';

	if ( is_feed() ) {
		return $title;
	}

	// Add site name to all pages except front page.
	if ( ! is_front_page() ) {
		$title .= " $separator " . get_bloginfo( 'name' );
	}

	// Add page number if paginated.
	global $paged;
	if ( $paged >= 2 ) {
		$title .= " $separator " . sprintf( __( 'Page %s', 'skyyrose-flagship' ), $paged );
	}

	return $title;
}
add_filter( 'wp_title', 'skyyrose_document_title', 10, 2 );

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
					'src'   => wp_get_attachment_url( $product->get_image_id() ),
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
		'name'        => is_tax( 'product_cat' ) ? $term->name : __( 'Products', 'skyyrose-flagship' ),
		'description' => is_tax( 'product_cat' ) ? term_description() : get_bloginfo( 'description' ),
		'url'         => is_tax( 'product_cat' ) ? get_term_link( $term ) : get_post_type_archive_link( 'product' ),
	);

	echo '<script type="application/ld+json">' . wp_json_encode( $schema ) . '</script>' . "\n";
}
add_action( 'wp_head', 'skyyrose_collection_schema' );
