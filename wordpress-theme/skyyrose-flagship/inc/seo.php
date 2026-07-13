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
 * @package SkyyRose
 * @since   1.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Custom-logo URL for og:image / twitter:image — image MIME types only.
 *
 * The live custom_logo attachment has at times been a VideoPress .mp4, which
 * silently produced og:image="…logo_400x100.mp4" and broke link previews
 * everywhere (structural remediation WS4, F13). Social cards require a
 * static image, so any non-image attachment yields '' and callers fall back
 * to the static brand asset.
 *
 * @since 1.8.0
 * @return string Attachment URL, or '' when unset or not an image.
 */
function skyyrose_og_logo_url() {
	$logo_id = get_theme_mod( 'custom_logo' );
	if ( ! $logo_id ) {
		return '';
	}
	// Raster formats only — social crawlers (Facebook, X, LinkedIn) do not
	// render SVG in og:image/twitter:image, so allowing it through recreates
	// the same broken-preview class this function exists to prevent.
	$raster_mimes = array( 'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/avif' );
	$mime         = (string) get_post_mime_type( $logo_id );
	if ( ! in_array( $mime, $raster_mimes, true ) ) {
		return '';
	}
	return (string) wp_get_attachment_url( $logo_id );
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
	if ( ! is_singular( 'product' ) || ! function_exists( 'get_woocommerce_currency' ) ) {
		return;
	}

	// Defer to Yoast WooCommerce SEO if active.
	if ( defined( 'WPSEO_WOO_VERSION' ) ) {
		return;
	}

	$product = skyyrose_current_wc_product();

	if ( ! $product ) {
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
	$reviews = get_comments(
		array(
			'post_id' => $product->get_id(),
			'status'  => 'approve',
			'type'    => 'review',
			'number'  => 5,
		)
	);

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

	echo '<script type="application/ld+json">' . wp_json_encode( $schema, JSON_HEX_TAG | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES ) . '</script>' . "\n"; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- JSON-encoded with JSON_HEX_TAG preventing script injection.
}
add_action( 'wp_head', 'skyyrose_product_schema', 1 );

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

	$logo_url = skyyrose_og_logo_url();

	$schema = array(
		'@context'    => 'https://schema.org',
		'@type'       => 'Organization',
		'name'        => 'SkyyRose',
		'legalName'   => 'SkyyRose LLC',
		'url'         => home_url( '/' ),
		'founder'     => array(
			'@type' => 'Person',
			'name'  => 'Corey Foster',
		),
		'description' => __( 'Luxury Grows from Concrete. Premium streetwear and luxury fashion brand.', 'skyyrose' ),
		'logo'        => $logo_url ? array(
			'@type' => 'ImageObject',
			'url'   => $logo_url,
		) : null,
		'brand'       => array(
			'@type'  => 'Brand',
			'name'   => 'SkyyRose',
			'slogan' => 'Luxury Grows from Concrete.',
		),
		'sameAs'      => array(),
	);

	// Canonical brand social profiles — always present in sameAs.
	$default_profiles = array(
		'https://instagram.com/skyyrose.co',
		'https://tiktok.com/@skyyroseco',
	);

	foreach ( $default_profiles as $profile_url ) {
		$schema['sameAs'][] = $profile_url;
	}

	// Add additional social media profiles from Customizer settings (deduplicated).
	$social_profiles = array(
		'facebook'  => get_theme_mod( 'facebook_url' ),
		'twitter'   => get_theme_mod( 'twitter_url' ),
		'instagram' => get_theme_mod( 'instagram_url' ),
		'linkedin'  => get_theme_mod( 'linkedin_url' ),
		'youtube'   => get_theme_mod( 'youtube_url' ),
	);

	foreach ( $social_profiles as $profile ) {
		if ( ! empty( $profile ) && ! in_array( esc_url_raw( $profile ), $schema['sameAs'], true ) ) {
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
	$schema = array_filter(
		$schema,
		function ( $v ) {
			return null !== $v;
		}
	);

	echo '<script type="application/ld+json">' . wp_json_encode( $schema, JSON_HEX_TAG | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES ) . '</script>' . "\n"; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- JSON-encoded with JSON_HEX_TAG preventing script injection.
}
add_action( 'wp_head', 'skyyrose_organization_schema', 1 );

/**
 * Add WebSite schema with SearchAction (sitelinks search box).
 *
 * Enables the search box that appears in Google sitelinks for branded queries.
 * Only outputs on the front page. Defers to Yoast SEO when active.
 *
 * @since 6.4.0
 */
function skyyrose_website_schema() {
	if ( ! is_front_page() ) {
		return;
	}

	// Defer to Yoast SEO if active.
	if ( defined( 'WPSEO_VERSION' ) ) {
		return;
	}

	$schema = array(
		'@context'        => 'https://schema.org',
		'@type'           => 'WebSite',
		'name'            => get_bloginfo( 'name' ),
		'url'             => home_url( '/' ),
		'potentialAction' => array(
			'@type'       => 'SearchAction',
			'target'      => array(
				'@type'       => 'EntryPoint',
				'urlTemplate' => home_url( '/?s={search_term_string}' ),
			),
			'query-input' => 'required name=search_term_string',
		),
	);

	echo '<script type="application/ld+json">' . wp_json_encode( $schema, JSON_HEX_TAG | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES ) . '</script>' . "\n"; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
}
add_action( 'wp_head', 'skyyrose_website_schema', 1 );

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
		++$position;
	}

	echo '<script type="application/ld+json">' . wp_json_encode( $schema, JSON_HEX_TAG | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES ) . '</script>' . "\n"; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- JSON-encoded with JSON_HEX_TAG preventing script injection.
}
add_action( 'wp_head', 'skyyrose_breadcrumb_schema', 1 );

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
			'title' => __( 'Home', 'skyyrose' ),
			'url'   => home_url( '/' ),
		),
	);

	// Custom collection page templates: Home → Collections → [Collection Name].
	$breadcrumb_collection_templates = array(
		'template-collection-black-rose.php'   => __( 'Black Rose', 'skyyrose' ),
		'template-collection-love-hurts.php'   => __( 'Love Hurts', 'skyyrose' ),
		'template-collection-signature.php'    => __( 'Signature', 'skyyrose' ),
		'template-collection-kids-capsule.php' => __( 'Kids Capsule', 'skyyrose' ),
	);

	$matched_breadcrumb_collection = false;
	foreach ( $breadcrumb_collection_templates as $tpl_file => $col_name ) {
		if ( is_page_template( $tpl_file ) ) {
			$matched_breadcrumb_collection = $col_name;
			break;
		}
	}

	if ( $matched_breadcrumb_collection ) {
		$collections_page = get_page_by_path( 'collections' );
		if ( $collections_page ) {
			$breadcrumbs[] = array(
				'title' => __( 'Collections', 'skyyrose' ),
				'url'   => get_permalink( $collections_page->ID ),
			);
		} else {
			$breadcrumbs[] = array(
				'title' => __( 'Collections', 'skyyrose' ),
				'url'   => home_url( '/collections/' ),
			);
		}

		$breadcrumbs[] = array(
			'title' => $matched_breadcrumb_collection,
			'url'   => get_permalink(),
		);
	} elseif ( is_singular( 'product' ) && function_exists( 'wc_get_page_id' ) ) {
		$breadcrumbs[] = array(
			'title' => __( 'Shop', 'skyyrose' ),
			'url'   => get_permalink( wc_get_page_id( 'shop' ) ),
		);

		$terms = get_the_terms( get_the_ID(), 'product_cat' );
		if ( $terms && ! is_wp_error( $terms ) ) {
			$term          = array_shift( $terms );
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
			'title' => __( 'Shop', 'skyyrose' ),
			'url'   => get_permalink( wc_get_page_id( 'shop' ) ),
		);
	} elseif ( function_exists( 'wc_get_page_id' ) && is_tax( 'product_cat' ) ) {
		$breadcrumbs[] = array(
			'title' => __( 'Shop', 'skyyrose' ),
			'url'   => get_permalink( wc_get_page_id( 'shop' ) ),
		);

		$term = get_queried_object();
		if ( $term instanceof WP_Term ) {
			$breadcrumbs[] = array(
				'title' => wp_strip_all_tags( html_entity_decode( $term->name, ENT_QUOTES, 'UTF-8' ) ),
				'url'   => get_term_link( $term ),
			);
		}
	} elseif ( is_singular( 'post' ) ) {
		$categories = get_the_category();
		if ( $categories ) {
			$category      = array_shift( $categories );
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
			'title' => sprintf( __( 'Search Results for: %s', 'skyyrose' ), esc_html( get_search_query() ) ),
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

	echo '<nav class="breadcrumb-navigation" aria-label="' . esc_attr__( 'Breadcrumb', 'skyyrose' ) . '">';
	echo '<ol class="breadcrumbs" itemscope itemtype="https://schema.org/BreadcrumbList">';

	$position   = 1;
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

		++$position;
	}

	echo '</ol>';
	echo '</nav>';
}
add_action( 'skyyrose_after_header', 'skyyrose_breadcrumb', 10 );

/**
 * Resolve collection SEO context for immersive and landing page templates.
 *
 * The four collection page templates have their own explicit branches. This
 * maps the immersive (3D experience) and landing (conversion) templates to
 * their collection so OG / title / description / Twitter / schema output stays
 * consistent instead of falling through to the generic article handling.
 *
 * @since 1.6.4
 *
 * @return array|null array{slug:string,label:string,type:string} or null when
 *                    the current request is not an immersive/landing template.
 */
function skyyrose_collection_template_context() {
	$templates = array(
		'template-immersive-black-rose.php'   => array( 'black-rose', 'Black Rose', 'immersive' ),
		'template-immersive-love-hurts.php'   => array( 'love-hurts', 'Love Hurts', 'immersive' ),
		'template-immersive-signature.php'    => array( 'signature', 'Signature', 'immersive' ),
		'template-immersive-kids-capsule.php' => array( 'kids-capsule', 'Kids Capsule', 'immersive' ),
		'template-landing-black-rose.php'     => array( 'black-rose', 'Black Rose', 'landing' ),
		'template-landing-love-hurts.php'     => array( 'love-hurts', 'Love Hurts', 'landing' ),
		'template-landing-signature.php'      => array( 'signature', 'Signature', 'landing' ),
		'template-landing-kids-capsule.php'   => array( 'kids-capsule', 'Kids Capsule', 'landing' ),
	);

	foreach ( $templates as $tpl_file => $data ) {
		if ( is_page_template( $tpl_file ) ) {
			return array(
				'slug'  => $data[0],
				'label' => $data[1],
				'type'  => $data[2],
			);
		}
	}

	return null;
}

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

	$site_name = get_bloginfo( 'name' );

	// Locale — always output.
	echo '<meta property="og:locale" content="' . esc_attr( get_locale() ) . '" />' . "\n";
	echo '<meta property="og:site_name" content="' . esc_attr( $site_name ) . '" />' . "\n";

	// Fallback OG image (brand monogram).
	$fallback_og_image = get_template_directory_uri() . '/assets/branding/sr-primary-hero.webp';

	// Custom collection page templates — must precede the generic is_singular() branch.
	$collection_templates = array(
		'template-collection-black-rose.php'   => array( 'Black Rose Collection', 'black-rose' ),
		'template-collection-love-hurts.php'   => array( 'Love Hurts Collection', 'love-hurts' ),
		'template-collection-signature.php'    => array( 'Signature Collection', 'signature' ),
		'template-collection-kids-capsule.php' => array( 'Kids Capsule Collection', 'kids-capsule' ),
	);

	$active_collection_template = false;
	foreach ( $collection_templates as $tpl_file => $tpl_data ) {
		if ( is_page_template( $tpl_file ) ) {
			$active_collection_template = $tpl_data;
			break;
		}
	}

	$collection_ctx = skyyrose_collection_template_context();

	if ( $active_collection_template ) {
		$col_label = $active_collection_template[0];
		echo '<meta property="og:type" content="website" />' . "\n";
		echo '<meta property="og:title" content="' . esc_attr( 'Shop ' . $col_label . ' | ' . $site_name ) . '" />' . "\n";
		echo '<meta property="og:description" content="' . esc_attr( 'Browse the ' . $col_label . ' from SkyyRose. Luxury Grows from Concrete.' ) . '" />' . "\n";
		echo '<meta property="og:url" content="' . esc_url( get_permalink() ) . '" />' . "\n";
		if ( has_post_thumbnail() ) {
			echo '<meta property="og:image" content="' . esc_url( get_the_post_thumbnail_url( get_the_ID(), 'full' ) ) . '" />' . "\n";
			echo '<meta property="og:image:width" content="1200" />' . "\n";
			echo '<meta property="og:image:height" content="630" />' . "\n";
		} else {
			echo '<meta property="og:image" content="' . esc_url( $fallback_og_image ) . '" />' . "\n";
		}
	} elseif ( null !== $collection_ctx ) {
		if ( 'landing' === $collection_ctx['type'] ) {
			$ctx_title = 'Shop ' . $collection_ctx['label'] . ' | ' . $site_name;
			$ctx_desc  = 'Shop the ' . $collection_ctx['label'] . ' collection from SkyyRose. Luxury Grows from Concrete.';
		} else {
			$ctx_title = $collection_ctx['label'] . ' — Immersive Experience | ' . $site_name;
			$ctx_desc  = 'Step inside the ' . $collection_ctx['label'] . ' world — an immersive SkyyRose experience. Luxury Grows from Concrete.';
		}
		echo '<meta property="og:type" content="website" />' . "\n";
		echo '<meta property="og:title" content="' . esc_attr( $ctx_title ) . '" />' . "\n";
		echo '<meta property="og:description" content="' . esc_attr( $ctx_desc ) . '" />' . "\n";
		echo '<meta property="og:url" content="' . esc_url( get_permalink() ) . '" />' . "\n";
		if ( has_post_thumbnail() ) {
			echo '<meta property="og:image" content="' . esc_url( get_the_post_thumbnail_url( get_the_ID(), 'full' ) ) . '" />' . "\n";
			echo '<meta property="og:image:width" content="1200" />' . "\n";
			echo '<meta property="og:image:height" content="630" />' . "\n";
		} else {
			echo '<meta property="og:image" content="' . esc_url( $fallback_og_image ) . '" />' . "\n";
		}
	} elseif ( is_singular() && ! is_front_page() ) {
		global $post;

		echo '<meta property="og:type" content="' . esc_attr( is_singular( 'product' ) ? 'product' : 'article' ) . '" />' . "\n";
		echo '<meta property="og:title" content="' . esc_attr( get_the_title() . ' | ' . $site_name ) . '" />' . "\n";
		echo '<meta property="og:description" content="' . esc_attr( wp_strip_all_tags( get_the_excerpt() ) ) . '" />' . "\n";
		echo '<meta property="og:url" content="' . esc_url( get_permalink() ) . '" />' . "\n";

		if ( has_post_thumbnail() ) {
			$image_url = get_the_post_thumbnail_url( $post->ID, 'full' );
			echo '<meta property="og:image" content="' . esc_url( $image_url ) . '" />' . "\n";
			echo '<meta property="og:image:width" content="1200" />' . "\n";
			echo '<meta property="og:image:height" content="630" />' . "\n";
		} else {
			echo '<meta property="og:image" content="' . esc_url( $fallback_og_image ) . '" />' . "\n";
		}

		// Product-specific OG tags.
		if ( is_singular( 'product' ) ) {
			$product = skyyrose_current_wc_product( $post->ID );
			if ( $product && function_exists( 'get_woocommerce_currency' ) ) {
				echo '<meta property="product:price:amount" content="' . esc_attr( $product->get_price() ) . '" />' . "\n";
				echo '<meta property="product:price:currency" content="' . esc_attr( get_woocommerce_currency() ) . '" />' . "\n";
				echo '<meta property="product:availability" content="' . esc_attr( $product->is_in_stock() ? 'in stock' : 'out of stock' ) . '" />' . "\n";
			}
		}
	} elseif ( is_front_page() ) {
		echo '<meta property="og:type" content="website" />' . "\n";
		echo '<meta property="og:title" content="' . esc_attr( $site_name . ' — Luxury Grows from Concrete.' ) . '" />' . "\n";
		echo '<meta property="og:description" content="' . esc_attr( get_bloginfo( 'description' ) ) . '" />' . "\n";
		echo '<meta property="og:url" content="' . esc_url( home_url( '/' ) ) . '" />' . "\n";

		$logo_url = skyyrose_og_logo_url();
		echo '<meta property="og:image" content="' . esc_url( $logo_url ? $logo_url : $fallback_og_image ) . '" />' . "\n";
	} elseif ( is_tax( 'product_cat' ) ) {
		$term = get_queried_object();
		echo '<meta property="og:type" content="website" />' . "\n";
		echo '<meta property="og:title" content="' . esc_attr( $term->name . ' Collection | ' . $site_name ) . '" />' . "\n";
		$desc = term_description( $term->term_id );
		echo '<meta property="og:description" content="' . esc_attr( wp_strip_all_tags( $desc ?: 'Shop the ' . $term->name . ' collection from SkyyRose.' ) ) . '" />' . "\n";
		$term_link = get_term_link( $term );
		if ( ! is_wp_error( $term_link ) ) {
			echo '<meta property="og:url" content="' . esc_url( $term_link ) . '" />' . "\n";
		}
		echo '<meta property="og:image" content="' . esc_url( $fallback_og_image ) . '" />' . "\n";
	} elseif ( function_exists( 'is_shop' ) && is_shop() ) {
		echo '<meta property="og:type" content="website" />' . "\n";
		echo '<meta property="og:title" content="' . esc_attr( 'Shop | ' . $site_name ) . '" />' . "\n";
		echo '<meta property="og:description" content="' . esc_attr( 'Premium streetwear and luxury fashion. Luxury Grows from Concrete.' ) . '" />' . "\n";
		echo '<meta property="og:url" content="' . esc_url( get_permalink( wc_get_page_id( 'shop' ) ) ) . '" />' . "\n";
		echo '<meta property="og:image" content="' . esc_url( $fallback_og_image ) . '" />' . "\n";
	} elseif ( is_category() || is_tag() ) {
		$term = get_queried_object();
		echo '<meta property="og:type" content="website" />' . "\n";
		echo '<meta property="og:title" content="' . esc_attr( $term->name . ' | ' . $site_name ) . '" />' . "\n";
		$desc = term_description( $term->term_id );
		echo '<meta property="og:description" content="' . esc_attr( wp_strip_all_tags( $desc ?: $site_name ) ) . '" />' . "\n";
		$term_link = get_term_link( $term );
		if ( ! is_wp_error( $term_link ) ) {
			echo '<meta property="og:url" content="' . esc_url( $term_link ) . '" />' . "\n";
		}
		echo '<meta property="og:image" content="' . esc_url( $fallback_og_image ) . '" />' . "\n";
	}
}
add_action( 'wp_head', 'skyyrose_open_graph_tags', 1 );

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

	// Use theme_mod handle when configured; fall back to the canonical brand account.
	$twitter_handle = get_theme_mod( 'twitter_handle', 'skyyroseco' );
	echo '<meta name="twitter:site" content="@' . esc_attr( ltrim( $twitter_handle, '@' ) ) . '" />' . "\n";

	$fallback_image = get_template_directory_uri() . '/assets/branding/sr-primary-hero.webp';

	// Custom collection page templates — must precede the generic is_singular() branch.
	$twitter_collection_templates = array(
		'template-collection-black-rose.php'   => array( 'Black Rose Collection', 'black-rose' ),
		'template-collection-love-hurts.php'   => array( 'Love Hurts Collection', 'love-hurts' ),
		'template-collection-signature.php'    => array( 'Signature Collection', 'signature' ),
		'template-collection-kids-capsule.php' => array( 'Kids Capsule Collection', 'kids-capsule' ),
	);

	$active_twitter_collection = false;
	foreach ( $twitter_collection_templates as $tpl_file => $tpl_data ) {
		if ( is_page_template( $tpl_file ) ) {
			$active_twitter_collection = $tpl_data;
			break;
		}
	}

	$twitter_ctx = skyyrose_collection_template_context();

	if ( $active_twitter_collection ) {
		$tc_label = $active_twitter_collection[0];
		echo '<meta name="twitter:title" content="' . esc_attr( 'Shop ' . $tc_label . ' | SkyyRose' ) . '" />' . "\n";
		echo '<meta name="twitter:description" content="' . esc_attr( 'Browse the ' . $tc_label . ' from SkyyRose. Luxury Grows from Concrete.' ) . '" />' . "\n";
		if ( has_post_thumbnail() ) {
			echo '<meta name="twitter:image" content="' . esc_url( get_the_post_thumbnail_url( get_the_ID(), 'full' ) ) . '" />' . "\n";
		} else {
			echo '<meta name="twitter:image" content="' . esc_url( $fallback_image ) . '" />' . "\n";
		}
	} elseif ( null !== $twitter_ctx ) {
		if ( 'landing' === $twitter_ctx['type'] ) {
			$tw_title = 'Shop ' . $twitter_ctx['label'] . ' | SkyyRose';
			$tw_desc  = 'Shop the ' . $twitter_ctx['label'] . ' collection from SkyyRose. Luxury Grows from Concrete.';
		} else {
			$tw_title = $twitter_ctx['label'] . ' — Immersive Experience | SkyyRose';
			$tw_desc  = 'Step inside the ' . $twitter_ctx['label'] . ' world — an immersive SkyyRose experience.';
		}
		echo '<meta name="twitter:title" content="' . esc_attr( $tw_title ) . '" />' . "\n";
		echo '<meta name="twitter:description" content="' . esc_attr( $tw_desc ) . '" />' . "\n";
		if ( has_post_thumbnail() ) {
			echo '<meta name="twitter:image" content="' . esc_url( get_the_post_thumbnail_url( get_the_ID(), 'full' ) ) . '" />' . "\n";
		} else {
			echo '<meta name="twitter:image" content="' . esc_url( $fallback_image ) . '" />' . "\n";
		}
	} elseif ( is_singular() && ! is_front_page() ) {
		echo '<meta name="twitter:title" content="' . esc_attr( get_the_title() ) . '" />' . "\n";
		echo '<meta name="twitter:description" content="' . esc_attr( wp_strip_all_tags( get_the_excerpt() ) ) . '" />' . "\n";

		if ( has_post_thumbnail() ) {
			echo '<meta name="twitter:image" content="' . esc_url( get_the_post_thumbnail_url( get_the_ID(), 'full' ) ) . '" />' . "\n";
		} else {
			echo '<meta name="twitter:image" content="' . esc_url( $fallback_image ) . '" />' . "\n";
		}
	} elseif ( is_front_page() ) {
		echo '<meta name="twitter:title" content="' . esc_attr( get_bloginfo( 'name' ) . ' — Luxury Grows from Concrete.' ) . '" />' . "\n";
		echo '<meta name="twitter:description" content="' . esc_attr( get_bloginfo( 'description' ) ) . '" />' . "\n";

		$logo_url = skyyrose_og_logo_url();
		echo '<meta name="twitter:image" content="' . esc_url( $logo_url ? $logo_url : $fallback_image ) . '" />' . "\n";
	} elseif ( is_tax( 'product_cat' ) ) {
		$term = get_queried_object();
		echo '<meta name="twitter:title" content="' . esc_attr( $term->name . ' Collection | SkyyRose' ) . '" />' . "\n";
		echo '<meta name="twitter:description" content="' . esc_attr( wp_strip_all_tags( term_description( $term->term_id ) ?: 'Shop the ' . $term->name . ' collection.' ) ) . '" />' . "\n";
		echo '<meta name="twitter:image" content="' . esc_url( $fallback_image ) . '" />' . "\n";
	} elseif ( function_exists( 'is_shop' ) && is_shop() ) {
		echo '<meta name="twitter:title" content="Shop | SkyyRose" />' . "\n";
		echo '<meta name="twitter:description" content="Premium streetwear and luxury fashion. Luxury Grows from Concrete." />' . "\n";
		echo '<meta name="twitter:image" content="' . esc_url( $fallback_image ) . '" />' . "\n";
	}
}
add_action( 'wp_head', 'skyyrose_twitter_card_tags', 1 );

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
	} elseif ( function_exists( 'is_shop' ) && ( is_post_type_archive( 'product' ) || is_shop() ) ) {
		if ( function_exists( 'wc_get_page_id' ) ) {
			echo '<link rel="canonical" href="' . esc_url( get_permalink( wc_get_page_id( 'shop' ) ) ) . '" />' . "\n";
		}
	} elseif ( is_tax() || is_category() || is_tag() ) {
		$queried = get_queried_object();
		if ( $queried instanceof WP_Term ) {
			$term_link = get_term_link( $queried );
			if ( ! is_wp_error( $term_link ) ) {
				echo '<link rel="canonical" href="' . esc_url( $term_link ) . '" />' . "\n";
			}
		}
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

	if ( is_singular() && ! is_front_page() ) {
		// Custom template meta descriptions (155 chars max, CTA-driven).
		if ( is_page() ) {
			$template     = get_page_template_slug();
			$descriptions = array(
				'template-collection-black-rose.php' => 'Browse the full Black Rose Collection. Limited edition gothic streetwear — hockey jerseys, basketball jerseys, and more.',
				'template-collection-love-hurts.php' => 'Browse the full Love Hurts Collection. Crimson luxury fashion — fanny packs, apparel, and accessories from SkyyRose.',
				'template-collection-signature.php'  => 'Browse the full Signature Collection. Everyday luxury — windbreakers, shorts, beanies, and essentials from SkyyRose.',
				'template-about.php'                 => 'The SkyyRose story — Luxury Grows from Concrete. Founded in Oakland, building premium streetwear for the culture.',
				'template-preorder-gateway.php'      => 'Secure your SkyyRose pieces before they drop. Pre-order limited edition streetwear and luxury fashion.',
				'template-contact.php'               => 'Reach SkyyRose directly. Oakland-made, founder-led. Questions about orders, sizing, collaborations, or press — we read every message.',
				'template-faq.php'                   => 'Frequently asked questions about SkyyRose orders, shipping, returns, sizing, and pre-orders. Everything you need to know.',
				'template-shipping-returns.php'      => 'SkyyRose shipping rates, delivery times, 30-day return policy, free exchanges, and pre-order cancellation details.',
			);
			if ( $template && isset( $descriptions[ $template ] ) ) {
				$description = $descriptions[ $template ];
			}

			if ( empty( $description ) ) {
				$collection_ctx = skyyrose_collection_template_context();
				if ( null !== $collection_ctx ) {
					$description = ( 'landing' === $collection_ctx['type'] )
						? 'Shop the ' . $collection_ctx['label'] . ' collection from SkyyRose. Premium streetwear and luxury fashion — Luxury Grows from Concrete.'
						: 'Step inside the ' . $collection_ctx['label'] . ' world. An immersive SkyyRose experience — Luxury Grows from Concrete.';
				}
			}
		}

		if ( empty( $description ) ) {
			$description = get_the_excerpt();
		}
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
	} elseif ( function_exists( 'is_shop' ) && is_shop() ) {
		$description = 'Shop premium streetwear and luxury fashion from SkyyRose. Luxury Grows from Concrete. Oakland, CA.';
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
 * Override document title for specific pages.
 *
 * Uses `pre_get_document_title` at high priority to override before
 * Jetpack/WordPress.com SEO modules can interfere. Returning a
 * non-empty string from this filter makes WordPress use it as-is.
 *
 * @since 1.0.0
 * @since 3.2.3 Switched from wp_title to pre_get_document_title.
 *
 * @param string $title Pre-filtered document title (empty by default).
 * @return string Full document title or empty to use default.
 */
function skyyrose_pre_document_title( $title ) {
	$brand = get_bloginfo( 'name' );

	// Collections "Shop All" page.
	if ( is_page( array( 'collections', 9327 ) ) ) {
		return 'Collections — Shop All | ' . $brand;
	}

	// Custom template page titles (optimized for SEO).
	if ( is_page() ) {
		$template = get_page_template_slug();
		$titles   = array(
			'template-collection-black-rose.php' => 'Shop Black Rose — Limited Edition Streetwear | ' . $brand,
			'template-collection-love-hurts.php' => 'Shop Love Hurts — Crimson Luxury Fashion | ' . $brand,
			'template-collection-signature.php'  => 'Shop Signature — Everyday Luxury Essentials | ' . $brand,
			'template-about.php'                 => 'Our Story — Luxury Grows from Concrete | ' . $brand,
			'template-preorder-gateway.php'      => 'Pre-Order — Secure Your Pieces | ' . $brand,
			'template-contact.php'               => 'Reach Out | ' . $brand,
			'page-wishlist.php'                  => 'Your Wishlist | ' . $brand,
			'template-faq.php'                   => 'FAQ — Orders, Shipping, Returns & Sizing | ' . $brand,
			'template-shipping-returns.php'      => 'Shipping & Returns Policy | ' . $brand,
		);

		if ( $template && isset( $titles[ $template ] ) ) {
			return $titles[ $template ];
		}

		$collection_ctx = skyyrose_collection_template_context();
		if ( null !== $collection_ctx ) {
			if ( 'landing' === $collection_ctx['type'] ) {
				return 'Shop ' . $collection_ctx['label'] . ' — Luxury Streetwear | ' . $brand;
			}
			return $collection_ctx['label'] . ' — Immersive Experience | ' . $brand;
		}

		// Policy pages use the default page template — no template slug to key
		// on above, and the WP.com SEO layer strips the brand suffix, leaving a
		// bare <title> (go-live sweep P1, regressed in the seo.php rewrite).
		if ( is_page( array( 'privacy-policy', 'terms-of-service', 'cookie-policy', 'refund-policy' ) ) ) {
			return get_the_title() . ' | ' . $brand;
		}
	}

	return $title;
}
add_filter( 'pre_get_document_title', 'skyyrose_pre_document_title', 99 );

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
