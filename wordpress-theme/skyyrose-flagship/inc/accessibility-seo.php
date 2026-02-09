<?php
/**
 * Accessibility and SEO Features
 *
 * Implements WCAG 2.1 AA compliance and comprehensive SEO optimization
 * for the SkyyRose Flagship Theme.
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * ============================================================================
 * WCAG 2.1 AA COMPLIANCE FEATURES
 * ============================================================================
 */

/**
 * Enqueue accessibility CSS file.
 *
 * @since 1.0.0
 */
function skyyrose_accessibility_styles() {
	wp_enqueue_style(
		'skyyrose-accessibility',
		SKYYROSE_ASSETS_URI . '/css/accessibility.css',
		array( 'skyyrose-style' ),
		SKYYROSE_VERSION
	);
}
add_action( 'wp_enqueue_scripts', 'skyyrose_accessibility_styles' );

/**
 * Add ARIA labels to navigation menus.
 *
 * @since 1.0.0
 *
 * @param array $args Navigation menu arguments.
 * @return array Modified arguments.
 */
function skyyrose_nav_menu_aria_labels( $args ) {
	if ( 'primary' === $args['theme_location'] ) {
		$args['container_aria_label'] = __( 'Primary Navigation', 'skyyrose-flagship' );
	} elseif ( 'footer' === $args['theme_location'] ) {
		$args['container_aria_label'] = __( 'Footer Navigation', 'skyyrose-flagship' );
	} elseif ( 'mobile' === $args['theme_location'] ) {
		$args['container_aria_label'] = __( 'Mobile Navigation', 'skyyrose-flagship' );
	}

	return $args;
}
add_filter( 'wp_nav_menu_args', 'skyyrose_nav_menu_aria_labels' );

/**
 * Enqueue accessibility JavaScript file.
 *
 * @since 1.0.0
 */
function skyyrose_accessibility_scripts() {
	wp_enqueue_script(
		'skyyrose-accessibility',
		SKYYROSE_ASSETS_URI . '/js/accessibility.js',
		array( 'jquery' ),
		SKYYROSE_VERSION,
		true
	);
}
add_action( 'wp_enqueue_scripts', 'skyyrose_accessibility_scripts' );

/**
 * Add ARIA live regions to the page.
 *
 * @since 1.0.0
 */
function skyyrose_aria_live_regions() {
	echo '<div id="skyyrose-announcer-polite" class="aria-live-region" aria-live="polite" aria-atomic="true"></div>';
	echo '<div id="skyyrose-announcer-assertive" class="aria-live-region" aria-live="assertive" aria-atomic="true"></div>';
}
add_action( 'wp_footer', 'skyyrose_aria_live_regions' );

/**
 * Ensure all images have alt text.
 *
 * @since 1.0.0
 *
 * @param string $html Image HTML.
 * @param int    $post_id Post ID.
 * @param int    $attachment_id Attachment ID.
 * @return string Modified image HTML.
 */
function skyyrose_ensure_image_alt( $html, $post_id, $attachment_id ) {
	if ( strpos( $html, 'alt=' ) === false ) {
		$alt = get_post_meta( $attachment_id, '_wp_attachment_image_alt', true );
		if ( empty( $alt ) ) {
			$alt = get_the_title( $attachment_id );
		}
		$html = str_replace( '<img', '<img alt="' . esc_attr( $alt ) . '"', $html );
	}
	return $html;
}
add_filter( 'post_thumbnail_html', 'skyyrose_ensure_image_alt', 10, 3 );

/**
 * Add proper heading hierarchy.
 *
 * @since 1.0.0
 */
function skyyrose_heading_hierarchy() {
	if ( is_singular() && ! is_front_page() ) {
		// On single posts/pages, use h1 for title
		add_filter( 'the_title', function( $title, $id ) {
			if ( is_main_query() && get_the_ID() === $id && is_singular() ) {
				return '<h1 class="entry-title">' . $title . '</h1>';
			}
			return $title;
		}, 10, 2 );
	}
}
add_action( 'wp', 'skyyrose_heading_hierarchy' );

/**
 * ============================================================================
 * SEO OPTIMIZATION FEATURES
 * ============================================================================
 */

/**
 * Add Schema.org markup for products.
 *
 * @since 1.0.0
 */
function skyyrose_product_schema() {
	if ( ! is_singular( 'product' ) ) {
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
			'price'         => $product->get_price(),
			'availability'  => $product->is_in_stock() ? 'https://schema.org/InStock' : 'https://schema.org/OutOfStock',
		),
	);

	// Add brand if available
	$brand = get_post_meta( $product->get_id(), '_product_brand', true );
	if ( $brand ) {
		$schema['brand'] = array(
			'@type' => 'Brand',
			'name'  => $brand,
		);
	}

	// Add aggregate rating if available
	if ( $product->get_average_rating() ) {
		$schema['aggregateRating'] = array(
			'@type'       => 'AggregateRating',
			'ratingValue' => $product->get_average_rating(),
			'reviewCount' => $product->get_review_count(),
		);
	}

	// Add reviews
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
						'name'  => $review->comment_author,
					),
					'reviewRating'  => array(
						'@type'       => 'Rating',
						'ratingValue' => $rating,
					),
					'reviewBody'    => $review->comment_content,
					'datePublished' => $review->comment_date,
				);
			}
		}
	}

	echo '<script type="application/ld+json">' . wp_json_encode( $schema, JSON_UNESCAPED_SLASHES ) . '</script>' . "\n";
}
add_action( 'wp_head', 'skyyrose_product_schema' );

/**
 * Add Organization schema markup.
 *
 * @since 1.0.0
 */
function skyyrose_organization_schema() {
	if ( ! is_front_page() ) {
		return;
	}

	$schema = array(
		'@context' => 'https://schema.org',
		'@type'    => 'Organization',
		'name'     => get_bloginfo( 'name' ),
		'url'      => home_url( '/' ),
		'logo'     => array(
			'@type' => 'ImageObject',
			'url'   => get_theme_mod( 'custom_logo' ) ? wp_get_attachment_url( get_theme_mod( 'custom_logo' ) ) : '',
		),
		'sameAs'   => array(),
	);

	// Add social media profiles
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

	// Add contact information
	$phone = get_theme_mod( 'contact_phone' );
	$email = get_theme_mod( 'contact_email' );

	if ( $phone || $email ) {
		$schema['contactPoint'] = array(
			'@type'       => 'ContactPoint',
			'contactType' => 'customer service',
		);

		if ( $phone ) {
			$schema['contactPoint']['telephone'] = $phone;
		}
		if ( $email ) {
			$schema['contactPoint']['email'] = $email;
		}
	}

	echo '<script type="application/ld+json">' . wp_json_encode( $schema, JSON_UNESCAPED_SLASHES ) . '</script>' . "\n";
}
add_action( 'wp_head', 'skyyrose_organization_schema' );

/**
 * Add BreadcrumbList schema markup.
 *
 * @since 1.0.0
 */
function skyyrose_breadcrumb_schema() {
	if ( is_front_page() ) {
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

	echo '<script type="application/ld+json">' . wp_json_encode( $schema, JSON_UNESCAPED_SLASHES ) . '</script>' . "\n";
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

	if ( is_singular( 'product' ) ) {
		$breadcrumbs[] = array(
			'title' => __( 'Shop', 'skyyrose-flagship' ),
			'url'   => get_permalink( wc_get_page_id( 'shop' ) ),
		);

		$terms = get_the_terms( get_the_ID(), 'product_cat' );
		if ( $terms && ! is_wp_error( $terms ) ) {
			$term = array_shift( $terms );
			$breadcrumbs[] = array(
				'title' => $term->name,
				'url'   => get_term_link( $term ),
			);
		}

		$breadcrumbs[] = array(
			'title' => get_the_title(),
			'url'   => get_permalink(),
		);
	} elseif ( is_post_type_archive( 'product' ) || is_shop() ) {
		$breadcrumbs[] = array(
			'title' => __( 'Shop', 'skyyrose-flagship' ),
			'url'   => get_permalink( wc_get_page_id( 'shop' ) ),
		);
	} elseif ( is_tax( 'product_cat' ) ) {
		$breadcrumbs[] = array(
			'title' => __( 'Shop', 'skyyrose-flagship' ),
			'url'   => get_permalink( wc_get_page_id( 'shop' ) ),
		);

		$term = get_queried_object();
		$breadcrumbs[] = array(
			'title' => $term->name,
			'url'   => get_term_link( $term ),
		);
	} elseif ( is_singular( 'post' ) ) {
		$categories = get_the_category();
		if ( $categories ) {
			$category = array_shift( $categories );
			$breadcrumbs[] = array(
				'title' => $category->name,
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
 * @since 1.0.0
 */
function skyyrose_open_graph_tags() {
	if ( is_singular() ) {
		global $post;

		echo '<meta property="og:type" content="' . ( is_singular( 'product' ) ? 'product' : 'article' ) . '" />' . "\n";
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

		// Product-specific OG tags
		if ( is_singular( 'product' ) ) {
			$product = wc_get_product( $post->ID );
			if ( $product ) {
				echo '<meta property="product:price:amount" content="' . esc_attr( $product->get_price() ) . '" />' . "\n";
				echo '<meta property="product:price:currency" content="' . esc_attr( get_woocommerce_currency() ) . '" />' . "\n";
				echo '<meta property="product:availability" content="' . ( $product->is_in_stock() ? 'in stock' : 'out of stock' ) . '" />' . "\n";
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
 * @since 1.0.0
 */
function skyyrose_twitter_card_tags() {
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
 * @since 1.0.0
 */
function skyyrose_canonical_url() {
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
 * @since 1.0.0
 */
function skyyrose_meta_description() {
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

	// Add site name to all pages except front page
	if ( ! is_front_page() ) {
		$title .= " $separator " . get_bloginfo( 'name' );
	}

	// Add page number if paginated
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
 * Filter sitemap entries for products.
 *
 * @since 1.0.0
 *
 * @param array  $entries Array of sitemap entries.
 * @param string $post_type Post type name.
 * @return array Modified entries.
 */
function skyyrose_filter_product_sitemap( $entries, $post_type ) {
	if ( 'product' !== $post_type ) {
		return $entries;
	}

	// Add product images to sitemap
	foreach ( $entries as &$entry ) {
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
	}

	return $entries;
}
add_filter( 'wp_sitemaps_posts_entry', 'skyyrose_filter_product_sitemap', 10, 2 );

/**
 * ============================================================================
 * ADDITIONAL ACCESSIBILITY & SEO FEATURES
 * ============================================================================
 */

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
 * Add language attributes to HTML tag.
 *
 * @since 1.0.0
 *
 * @param string $output Language attributes.
 * @return string Modified attributes.
 */
function skyyrose_language_attributes( $output ) {
	return $output . ' lang="' . esc_attr( get_bloginfo( 'language' ) ) . '"';
}
add_filter( 'language_attributes', 'skyyrose_language_attributes' );

/**
 * Enhance WooCommerce accessibility.
 *
 * @since 1.0.0
 */
function skyyrose_woocommerce_accessibility() {
	// Add ARIA labels to WooCommerce elements
	add_filter( 'woocommerce_product_add_to_cart_text', function( $text, $product ) {
		return '<span aria-label="' . esc_attr( sprintf( __( 'Add %s to your cart', 'skyyrose-flagship' ), $product->get_name() ) ) . '">' . $text . '</span>';
	}, 10, 2 );

	// Add proper labels to quantity inputs
	add_action( 'woocommerce_before_quantity_input_field', function() {
		echo '<label for="quantity" class="screen-reader-text">' . __( 'Product quantity', 'skyyrose-flagship' ) . '</label>';
	} );

	// Add ARIA labels to cart items
	add_filter( 'woocommerce_cart_item_remove_link', function( $link, $cart_item_key ) {
		$product_name = get_the_title( $link );
		return str_replace(
			'class="remove"',
			'class="remove" aria-label="' . esc_attr( sprintf( __( 'Remove %s from cart', 'skyyrose-flagship' ), $product_name ) ) . '"',
			$link
		);
	}, 10, 2 );
}
add_action( 'init', 'skyyrose_woocommerce_accessibility' );

/**
 * Add landmark roles to main content areas.
 *
 * @since 1.0.0
 */
function skyyrose_add_landmark_roles() {
	echo '<script>
		document.addEventListener("DOMContentLoaded", function() {
			// Add main role if not present
			var content = document.getElementById("content");
			if (content && !content.hasAttribute("role")) {
				content.setAttribute("role", "main");
			}

			// Add navigation role to nav elements
			var navs = document.querySelectorAll("nav:not([role])");
			navs.forEach(function(nav) {
				nav.setAttribute("role", "navigation");
			});

			// Add complementary role to sidebars
			var sidebars = document.querySelectorAll(".sidebar, .widget-area");
			sidebars.forEach(function(sidebar) {
				if (!sidebar.hasAttribute("role")) {
					sidebar.setAttribute("role", "complementary");
				}
			});

			// Add contentinfo role to footer
			var footer = document.querySelector(".site-footer, footer");
			if (footer && !footer.hasAttribute("role")) {
				footer.setAttribute("role", "contentinfo");
			}

			// Add banner role to header
			var header = document.querySelector(".site-header, header");
			if (header && !header.hasAttribute("role")) {
				header.setAttribute("role", "banner");
			}
		});
	</script>';
}
add_action( 'wp_footer', 'skyyrose_add_landmark_roles' );

/**
 * Add preconnect for external resources.
 *
 * @since 1.0.0
 */
function skyyrose_preconnect_resources() {
	echo '<link rel="preconnect" href="https://fonts.googleapis.com">' . "\n";
	echo '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>' . "\n";

	if ( class_exists( 'WooCommerce' ) ) {
		// Preconnect to WooCommerce CDN if using external resources
		echo '<link rel="dns-prefetch" href="//www.google-analytics.com">' . "\n";
	}
}
add_action( 'wp_head', 'skyyrose_preconnect_resources', 1 );

/**
 * Add Collection schema for product categories.
 *
 * @since 1.0.0
 */
function skyyrose_collection_schema() {
	if ( ! is_tax( 'product_cat' ) && ! is_post_type_archive( 'product' ) ) {
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

	echo '<script type="application/ld+json">' . wp_json_encode( $schema, JSON_UNESCAPED_SLASHES ) . '</script>' . "\n";
}
add_action( 'wp_head', 'skyyrose_collection_schema' );

/**
 * ============================================================================
 * ACCESSIBILITY & SEO TESTING TOOLS
 * ============================================================================
 */

/**
 * Register accessibility testing admin page.
 *
 * @since 1.0.0
 */
function skyyrose_accessibility_testing_page() {
	add_theme_page(
		__( 'Accessibility & SEO Tools', 'skyyrose-flagship' ),
		__( 'A11y & SEO', 'skyyrose-flagship' ),
		'manage_options',
		'skyyrose-accessibility-seo',
		'skyyrose_accessibility_testing_page_content'
	);
}
add_action( 'admin_menu', 'skyyrose_accessibility_testing_page' );

/**
 * Accessibility testing page content.
 *
 * @since 1.0.0
 */
function skyyrose_accessibility_testing_page_content() {
	?>
	<div class="wrap">
		<h1><?php esc_html_e( 'Accessibility & SEO Tools', 'skyyrose-flagship' ); ?></h1>

		<div class="card">
			<h2><?php esc_html_e( 'WCAG 2.1 AA Compliance Checklist', 'skyyrose-flagship' ); ?></h2>
			<ul style="list-style: disc; margin-left: 20px;">
				<li><strong>✓</strong> Semantic HTML5 structure implemented</li>
				<li><strong>✓</strong> ARIA labels and roles for interactive elements</li>
				<li><strong>✓</strong> Keyboard navigation support (Tab, Enter, Space, Esc)</li>
				<li><strong>✓</strong> Focus indicators with 2px outline</li>
				<li><strong>✓</strong> Skip to content link</li>
				<li><strong>✓</strong> Alt text enforcement for images</li>
				<li><strong>✓</strong> Color contrast ratio support (4.5:1 text, 3:1 UI)</li>
				<li><strong>✓</strong> Screen reader announcements for dynamic content</li>
				<li><strong>✓</strong> Form labels and error messages</li>
				<li><strong>✓</strong> Accessible modals with keyboard trap</li>
				<li><strong>✓</strong> ARIA live regions</li>
				<li><strong>✓</strong> Reduced motion support</li>
				<li><strong>✓</strong> High contrast mode support</li>
			</ul>
		</div>

		<div class="card">
			<h2><?php esc_html_e( 'SEO Features Checklist', 'skyyrose-flagship' ); ?></h2>
			<ul style="list-style: disc; margin-left: 20px;">
				<li><strong>✓</strong> Product Schema.org markup</li>
				<li><strong>✓</strong> Organization schema</li>
				<li><strong>✓</strong> BreadcrumbList schema</li>
				<li><strong>✓</strong> Review schema</li>
				<li><strong>✓</strong> Collection/CollectionPage schema</li>
				<li><strong>✓</strong> Open Graph tags (Facebook)</li>
				<li><strong>✓</strong> Twitter Cards</li>
				<li><strong>✓</strong> Canonical URLs</li>
				<li><strong>✓</strong> Meta descriptions</li>
				<li><strong>✓</strong> Title tag optimization</li>
				<li><strong>✓</strong> XML sitemap support</li>
				<li><strong>✓</strong> Robots meta tags</li>
				<li><strong>✓</strong> Breadcrumb navigation</li>
			</ul>
		</div>

		<div class="card">
			<h2><?php esc_html_e( 'Recommended Testing Tools', 'skyyrose-flagship' ); ?></h2>
			<h3><?php esc_html_e( 'Accessibility Testing', 'skyyrose-flagship' ); ?></h3>
			<ul style="list-style: disc; margin-left: 20px;">
				<li><a href="https://wave.webaim.org/" target="_blank">WAVE Web Accessibility Evaluation Tool</a></li>
				<li><a href="https://www.deque.com/axe/" target="_blank">Axe DevTools</a></li>
				<li><a href="https://www.nvaccess.org/" target="_blank">NVDA Screen Reader</a></li>
				<li><a href="https://chrome.google.com/webstore/detail/lighthouse/" target="_blank">Google Lighthouse</a></li>
				<li><a href="https://www.tpgi.com/color-contrast-checker/" target="_blank">Color Contrast Analyzer</a></li>
				<li>Built-in browser keyboard navigation testing (Tab, Shift+Tab)</li>
			</ul>

			<h3><?php esc_html_e( 'SEO Testing', 'skyyrose-flagship' ); ?></h3>
			<ul style="list-style: disc; margin-left: 20px;">
				<li><a href="https://search.google.com/test/rich-results" target="_blank">Google Rich Results Test</a></li>
				<li><a href="https://search.google.com/search-console" target="_blank">Google Search Console</a></li>
				<li><a href="https://validator.schema.org/" target="_blank">Schema.org Validator</a></li>
				<li><a href="https://developers.facebook.com/tools/debug/" target="_blank">Facebook Sharing Debugger</a></li>
				<li><a href="https://cards-dev.twitter.com/validator" target="_blank">Twitter Card Validator</a></li>
				<li><a href="https://www.xml-sitemaps.com/" target="_blank">XML Sitemap Validator</a></li>
				<li><a href="https://pagespeed.web.dev/" target="_blank">PageSpeed Insights</a></li>
			</ul>
		</div>

		<div class="card">
			<h2><?php esc_html_e( 'Manual Testing Checklist', 'skyyrose-flagship' ); ?></h2>
			<h3><?php esc_html_e( 'Keyboard Navigation', 'skyyrose-flagship' ); ?></h3>
			<ol style="margin-left: 20px;">
				<li>Navigate entire site using only Tab key</li>
				<li>Test all interactive elements with Enter/Space</li>
				<li>Verify focus indicators are visible</li>
				<li>Test modal dialogs (Esc to close, Tab trap)</li>
				<li>Test dropdown menus with arrow keys</li>
				<li>Verify skip link functionality</li>
			</ol>

			<h3><?php esc_html_e( 'Screen Reader Testing', 'skyyrose-flagship' ); ?></h3>
			<ol style="margin-left: 20px;">
				<li>Test with NVDA (Windows) or VoiceOver (Mac)</li>
				<li>Verify heading hierarchy (H1, H2, H3)</li>
				<li>Check form labels are announced</li>
				<li>Test ARIA live region announcements</li>
				<li>Verify image alt text is read</li>
				<li>Test link descriptions are meaningful</li>
			</ol>

			<h3><?php esc_html_e( 'SEO Validation', 'skyyrose-flagship' ); ?></h3>
			<ol style="margin-left: 20px;">
				<li>Validate structured data with Google Rich Results Test</li>
				<li>Check meta descriptions are under 160 characters</li>
				<li>Verify canonical URLs are correct</li>
				<li>Test Open Graph tags with Facebook Debugger</li>
				<li>Validate XML sitemap</li>
				<li>Check robots.txt accessibility</li>
				<li>Verify breadcrumb navigation accuracy</li>
			</ol>
		</div>

		<div class="card">
			<h2><?php esc_html_e( 'Quick Tests', 'skyyrose-flagship' ); ?></h2>
			<p><strong><?php esc_html_e( 'Test Page URL:', 'skyyrose-flagship' ); ?></strong></p>
			<input type="url" id="test-url" value="<?php echo esc_url( home_url( '/' ) ); ?>" style="width: 100%; max-width: 600px; padding: 8px; margin-bottom: 10px;">

			<p>
				<button type="button" class="button button-primary" onclick="window.open('https://wave.webaim.org/report#/' + document.getElementById('test-url').value, '_blank')">
					<?php esc_html_e( 'Test with WAVE', 'skyyrose-flagship' ); ?>
				</button>
				<button type="button" class="button button-primary" onclick="window.open('https://search.google.com/test/rich-results?url=' + encodeURIComponent(document.getElementById('test-url').value), '_blank')">
					<?php esc_html_e( 'Test Rich Results', 'skyyrose-flagship' ); ?>
				</button>
				<button type="button" class="button button-primary" onclick="window.open('https://pagespeed.web.dev/report?url=' + encodeURIComponent(document.getElementById('test-url').value), '_blank')">
					<?php esc_html_e( 'Test PageSpeed', 'skyyrose-flagship' ); ?>
				</button>
			</p>
		</div>

		<div class="card">
			<h2><?php esc_html_e( 'Customizer Settings', 'skyyrose-flagship' ); ?></h2>
			<p><?php esc_html_e( 'Configure social media profiles and contact information for enhanced SEO:', 'skyyrose-flagship' ); ?></p>
			<ul style="list-style: disc; margin-left: 20px;">
				<li>Facebook URL</li>
				<li>Twitter Handle & URL</li>
				<li>Instagram URL</li>
				<li>LinkedIn URL</li>
				<li>YouTube URL</li>
				<li>Contact Phone</li>
				<li>Contact Email</li>
			</ul>
			<p>
				<a href="<?php echo esc_url( admin_url( 'customize.php' ) ); ?>" class="button button-primary">
					<?php esc_html_e( 'Open Customizer', 'skyyrose-flagship' ); ?>
				</a>
			</p>
		</div>
	</div>
	<?php
}
