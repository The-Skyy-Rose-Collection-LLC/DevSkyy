<?php
/**
 * Template Functions
 *
 * Helper functions used across theme templates: collection colors,
 * product queries, breadcrumbs, film grain overlay, and post meta.
 *
 * @package SkyyRose_Flagship
 * @since   1.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/*--------------------------------------------------------------
 * Collection Color Mapping
 *--------------------------------------------------------------*/

/**
 * Get the accent color for a given collection.
 *
 * Returns an immutable color value (new string) based on the collection slug.
 * Used by templates to apply per-collection color theming.
 *
 * @since  3.0.0
 *
 * @param  string $collection Collection slug (e.g., 'black-rose', 'love-hurts', 'signature').
 * @return string Hex color code.
 */
function skyyrose_get_collection_color( $collection ) {

	$colors = array(
		'black-rose'   => '#1A1A2E',
		'love-hurts'   => '#8B0000',
		'signature'    => '#D4AF37',
		'kids-capsule' => '#FFB6C1',
		'default'      => '#B76E79',
	);

	$sanitized_collection = sanitize_key( $collection );

	if ( isset( $colors[ $sanitized_collection ] ) ) {
		return $colors[ $sanitized_collection ];
	}

	return $colors['default'];
}

/**
 * Get the full palette for a collection.
 *
 * Returns an immutable array (new copy) of primary, secondary, and accent colors.
 *
 * @since  3.0.0
 *
 * @param  string $collection Collection slug.
 * @return array  Associative array with 'primary', 'secondary', 'accent' keys.
 */
function skyyrose_get_collection_palette( $collection ) {

	$palettes = array(
		'black-rose' => array(
			'primary'   => '#1A1A2E',
			'secondary' => '#16213E',
			'accent'    => '#0F3460',
		),
		'love-hurts' => array(
			'primary'   => '#8B0000',
			'secondary' => '#4B0082',
			'accent'    => '#D4AF37',
		),
		'signature'  => array(
			'primary'   => '#D4AF37',
			'secondary' => '#0A0A0A',
			'accent'    => '#B76E79',
		),
		'kids-capsule' => array(
			'primary'   => '#FFB6C1',
			'secondary' => '#FFF0F5',
			'accent'    => '#D4AF37',
		),
	);

	$sanitized_collection = sanitize_key( $collection );

	if ( isset( $palettes[ $sanitized_collection ] ) ) {
		return $palettes[ $sanitized_collection ];
	}

	return array(
		'primary'   => '#B76E79',
		'secondary' => '#0A0A0A',
		'accent'    => '#D4AF37',
	);
}

/*--------------------------------------------------------------
 * Product Queries
 *--------------------------------------------------------------*/

/**
 * Get WooCommerce products by collection (product category slug).
 *
 * Returns a new WP_Query result set. Does NOT mutate any global state.
 *
 * @since  3.0.0
 *
 * @param  string $collection Product category slug.
 * @param  int    $limit      Number of products to return. Default 8.
 * @return WP_Query Query result with product posts.
 */
function skyyrose_get_products_by_collection( $collection, $limit = 8 ) {

	$sanitized_collection = sanitize_key( $collection );
	$sanitized_limit      = absint( $limit );

	if ( $sanitized_limit < 1 ) {
		$sanitized_limit = 8;
	}

	if ( $sanitized_limit > 100 ) {
		$sanitized_limit = 100;
	}

	$args = array(
		'post_type'      => 'product',
		'post_status'    => 'publish',
		'posts_per_page' => $sanitized_limit,
		'orderby'        => 'menu_order date',
		'order'          => 'ASC',
		'tax_query'      => array( // phpcs:ignore WordPress.DB.SlowDBQuery.slow_db_query_tax_query
			array(
				'taxonomy' => 'product_cat',
				'field'    => 'slug',
				'terms'    => $sanitized_collection,
			),
		),
		'meta_query'     => array( // phpcs:ignore WordPress.DB.SlowDBQuery.slow_db_query_meta_query
			array(
				'key'     => '_visibility',
				'value'   => array( 'visible', 'catalog' ),
				'compare' => 'IN',
			),
		),
	);

	// For WooCommerce 3.0+ use the product visibility taxonomy instead.
	if ( class_exists( 'WooCommerce' ) && version_compare( WC()->version, '3.0.0', '>=' ) ) {
		unset( $args['meta_query'] );
		$args['tax_query'][] = array(
			'taxonomy' => 'product_visibility',
			'field'    => 'name',
			'terms'    => array( 'exclude-from-catalog' ),
			'operator' => 'NOT IN',
		);
	}

	return new WP_Query( $args );
}

/**
 * Get featured products across all collections.
 *
 * @since  3.0.0
 *
 * @param  int $limit Number of products. Default 4.
 * @return WP_Query Query result.
 */
function skyyrose_get_featured_products( $limit = 4 ) {

	$sanitized_limit = max( 1, min( 50, absint( $limit ) ) );

	$args = array(
		'post_type'      => 'product',
		'post_status'    => 'publish',
		'posts_per_page' => $sanitized_limit,
		'orderby'        => 'rand',
		'tax_query'      => array( // phpcs:ignore WordPress.DB.SlowDBQuery.slow_db_query_tax_query
			array(
				'taxonomy' => 'product_visibility',
				'field'    => 'name',
				'terms'    => 'featured',
			),
		),
	);

	return new WP_Query( $args );
}

/*--------------------------------------------------------------
 * Breadcrumbs
 *--------------------------------------------------------------*/

/**
 * Output custom breadcrumb navigation markup.
 *
 * Uses semantic HTML with ARIA attributes and Schema.org microdata.
 * Skips rendering on the front page.
 *
 * @since 3.0.0
 * @return void
 */
function skyyrose_breadcrumbs() {

	if ( is_front_page() ) {
		return;
	}

	$items = array();

	// Home is always the first breadcrumb.
	$items[] = array(
		'title' => esc_html__( 'Home', 'skyyrose-flagship' ),
		'url'   => home_url( '/' ),
	);

	// WooCommerce product pages.
	if ( function_exists( 'is_product' ) && is_product() ) {
		$items[] = array(
			'title' => esc_html__( 'Shop', 'skyyrose-flagship' ),
			'url'   => get_permalink( wc_get_page_id( 'shop' ) ),
		);

		$terms = get_the_terms( get_the_ID(), 'product_cat' );
		if ( $terms && ! is_wp_error( $terms ) ) {
			$term    = $terms[0];
			$items[] = array(
				'title' => $term->name,
				'url'   => get_term_link( $term ),
			);
		}

		$items[] = array(
			'title' => get_the_title(),
			'url'   => '',
		);
	} elseif ( function_exists( 'is_shop' ) && ( is_shop() || is_product_category() || is_product_tag() ) ) {
		// WooCommerce archive pages.
		$items[] = array(
			'title' => esc_html__( 'Shop', 'skyyrose-flagship' ),
			'url'   => get_permalink( wc_get_page_id( 'shop' ) ),
		);

		if ( is_product_category() ) {
			$term    = get_queried_object();
			$items[] = array(
				'title' => $term->name,
				'url'   => '',
			);
		}
	} elseif ( is_page() ) {
		// Regular pages.
		$items[] = array(
			'title' => get_the_title(),
			'url'   => '',
		);
	} elseif ( is_singular( 'post' ) ) {
		// Blog posts.
		$categories = get_the_category();
		if ( ! empty( $categories ) ) {
			$cat     = $categories[0];
			$items[] = array(
				'title' => $cat->name,
				'url'   => get_category_link( $cat->term_id ),
			);
		}
		$items[] = array(
			'title' => get_the_title(),
			'url'   => '',
		);
	} elseif ( is_category() ) {
		$items[] = array(
			'title' => single_cat_title( '', false ),
			'url'   => '',
		);
	} elseif ( is_search() ) {
		$items[] = array(
			/* translators: %s: search query */
			'title' => sprintf( esc_html__( 'Search: %s', 'skyyrose-flagship' ), get_search_query() ),
			'url'   => '',
		);
	} elseif ( is_404() ) {
		$items[] = array(
			'title' => esc_html__( 'Page Not Found', 'skyyrose-flagship' ),
			'url'   => '',
		);
	}

	// Render.
	if ( count( $items ) < 2 ) {
		return;
	}

	$output    = '<nav class="breadcrumb-navigation" aria-label="' . esc_attr__( 'Breadcrumb', 'skyyrose-flagship' ) . '">';
	$output   .= '<ol class="breadcrumbs" itemscope itemtype="https://schema.org/BreadcrumbList">';
	$last_idx  = count( $items ) - 1;

	foreach ( $items as $index => $item ) {
		$is_last  = ( $index === $last_idx );
		$output  .= '<li itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">';

		if ( $is_last || empty( $item['url'] ) ) {
			$output .= '<span itemprop="name" aria-current="page">' . esc_html( $item['title'] ) . '</span>';
		} else {
			$output .= '<a href="' . esc_url( $item['url'] ) . '" itemprop="item">';
			$output .= '<span itemprop="name">' . esc_html( $item['title'] ) . '</span>';
			$output .= '</a>';
		}

		$output .= '<meta itemprop="position" content="' . esc_attr( $index + 1 ) . '" />';
		$output .= '</li>';
	}

	$output .= '</ol></nav>';

	echo $output; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- Escaped above.
}

/*--------------------------------------------------------------
 * Film Grain Overlay
 *--------------------------------------------------------------*/

/**
 * Output the film grain overlay markup.
 *
 * Renders a fixed-position div that provides a subtle film grain texture
 * over immersive sections. CSS handles the noise pattern via background-image.
 * The overlay is non-interactive (pointer-events: none) and respects
 * prefers-reduced-motion.
 *
 * @since 3.0.0
 * @return void
 */
function skyyrose_film_grain() {
	?>
	<div class="skyyrose-film-grain" aria-hidden="true">
		<div class="film-grain__inner"></div>
	</div>
	<style>
		.skyyrose-film-grain {
			position: fixed;
			top: 0;
			left: 0;
			width: 100%;
			height: 100%;
			pointer-events: none;
			z-index: 9999;
			opacity: 0.035;
			mix-blend-mode: overlay;
		}
		.film-grain__inner {
			width: 100%;
			height: 100%;
			background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
			background-repeat: repeat;
			background-size: 256px 256px;
		}
		@media (prefers-reduced-motion: reduce) {
			.skyyrose-film-grain {
				display: none;
			}
		}
	</style>
	<?php
}

/*--------------------------------------------------------------
 * Body Classes
 *--------------------------------------------------------------*/

/**
 * Add custom body classes.
 *
 * @since 1.0.0
 *
 * @param  array $classes Existing body classes.
 * @return array Modified classes (new array via filter).
 */
function skyyrose_custom_body_classes( $classes ) {

	if ( ! is_singular() ) {
		$classes[] = 'hfeed';
	}

	if ( has_header_image() ) {
		$classes[] = 'has-header-image';
	}

	return $classes;
}
add_filter( 'body_class', 'skyyrose_custom_body_classes' );

/*--------------------------------------------------------------
 * Excerpt Customization
 *--------------------------------------------------------------*/

/**
 * Set custom excerpt length.
 *
 * @since  1.0.0
 *
 * @param  int $length Default excerpt length.
 * @return int Modified length.
 */
function skyyrose_excerpt_length( $length ) {
	if ( is_admin() ) {
		return $length;
	}
	return 30;
}
add_filter( 'excerpt_length', 'skyyrose_excerpt_length', 999 );

/**
 * Set custom excerpt more string.
 *
 * @since  1.0.0
 *
 * @param  string $more Default more text.
 * @return string Ellipsis character.
 */
function skyyrose_excerpt_more( $more ) {
	if ( is_admin() ) {
		return $more;
	}
	return '&hellip;';
}
add_filter( 'excerpt_more', 'skyyrose_excerpt_more' );

/*--------------------------------------------------------------
 * Post Thumbnail Helper
 *--------------------------------------------------------------*/

/**
 * Get the post thumbnail URL or a placeholder.
 *
 * @since  1.0.0
 *
 * @param  string $size WordPress image size name.
 * @return string Image URL.
 */
function skyyrose_get_post_thumbnail( $size = 'skyyrose-featured' ) {
	if ( has_post_thumbnail() ) {
		return get_the_post_thumbnail_url( get_the_ID(), $size );
	}

	return SKYYROSE_ASSETS_URI . '/images/placeholder.jpg';
}

/*--------------------------------------------------------------
 * Reading Time
 *--------------------------------------------------------------*/

/**
 * Calculate estimated reading time for a post.
 *
 * @since  1.0.0
 *
 * @param  int|null $post_id Post ID. Defaults to current post.
 * @return string Formatted reading time string.
 */
function skyyrose_reading_time( $post_id = null ) {

	if ( ! $post_id ) {
		$post_id = get_the_ID();
	}

	$content      = get_post_field( 'post_content', $post_id );
	$word_count   = str_word_count( wp_strip_all_tags( $content ) );
	$reading_time = max( 1, (int) ceil( $word_count / 200 ) );

	/* translators: %s: number of minutes */
	return sprintf( esc_html__( '%s min read', 'skyyrose-flagship' ), $reading_time );
}

/*--------------------------------------------------------------
 * Post Meta Display
 *--------------------------------------------------------------*/

/**
 * Display post date meta.
 *
 * @since 1.0.0
 * @return void
 */
function skyyrose_posted_on() {

	$time_string = '<time class="entry-date published updated" datetime="%1$s">%2$s</time>';

	if ( get_the_time( 'U' ) !== get_the_modified_time( 'U' ) ) {
		$time_string = '<time class="entry-date published" datetime="%1$s">%2$s</time>'
			. '<time class="updated" datetime="%3$s">%4$s</time>';
	}

	$time_string = sprintf(
		$time_string,
		esc_attr( get_the_date( DATE_W3C ) ),
		esc_html( get_the_date() ),
		esc_attr( get_the_modified_date( DATE_W3C ) ),
		esc_html( get_the_modified_date() )
	);

	printf(
		'<span class="posted-on">%s %s</span>',
		esc_html_x( 'Posted on', 'post date', 'skyyrose-flagship' ),
		'<a href="' . esc_url( get_permalink() ) . '" rel="bookmark">' . $time_string . '</a>' // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
	);
}

/**
 * Display post author meta.
 *
 * @since 1.0.0
 * @return void
 */
function skyyrose_posted_by() {
	printf(
		'<span class="byline">%s <span class="author vcard"><a class="url fn n" href="%s">%s</a></span></span>',
		esc_html_x( 'by', 'post author', 'skyyrose-flagship' ),
		esc_url( get_author_posts_url( get_the_author_meta( 'ID' ) ) ),
		esc_html( get_the_author() )
	);
}

/**
 * Display entry footer meta (categories, tags, comments, edit link).
 *
 * @since 1.0.0
 * @return void
 */
function skyyrose_entry_footer() {

	if ( 'post' === get_post_type() ) {
		/* translators: used between list items, there is a space after the comma */
		$categories_list = get_the_category_list( esc_html__( ', ', 'skyyrose-flagship' ) );
		if ( $categories_list ) {
			/* translators: 1: list of categories. */
			printf( '<span class="cat-links">' . esc_html__( 'Posted in %1$s', 'skyyrose-flagship' ) . '</span>', $categories_list ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
		}

		/* translators: used between list items, there is a space after the comma */
		$tags_list = get_the_tag_list( '', esc_html_x( ', ', 'list item separator', 'skyyrose-flagship' ) );
		if ( $tags_list ) {
			/* translators: 1: list of tags. */
			printf( '<span class="tags-links">' . esc_html__( 'Tagged %1$s', 'skyyrose-flagship' ) . '</span>', $tags_list ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
		}
	}

	if ( ! is_single() && ! post_password_required() && ( comments_open() || get_comments_number() ) ) {
		echo '<span class="comments-link">';
		comments_popup_link(
			sprintf(
				wp_kses(
					/* translators: %s: post title */
					__( 'Leave a Comment<span class="screen-reader-text"> on %s</span>', 'skyyrose-flagship' ),
					array( 'span' => array( 'class' => array() ) )
				),
				wp_kses_post( get_the_title() )
			)
		);
		echo '</span>';
	}

	edit_post_link(
		sprintf(
			wp_kses(
				/* translators: %s: post title, only visible to screen readers */
				__( 'Edit <span class="screen-reader-text">%s</span>', 'skyyrose-flagship' ),
				array( 'span' => array( 'class' => array() ) )
			),
			wp_kses_post( get_the_title() )
		),
		'<span class="edit-link">',
		'</span>'
	);
}

/*--------------------------------------------------------------
 * SVG Icon Helper
 *--------------------------------------------------------------*/

/**
 * Output an SVG icon by name, sanitized through wp_kses.
 *
 * @since 3.0.0
 *
 * @param string $name Icon name (e.g., 'phone', 'email', 'cart').
 * @return void
 */
function skyyrose_svg_icon( $name ) {
	$allowed_svg = array(
		'svg'      => array( 'xmlns' => true, 'width' => true, 'height' => true, 'viewBox' => true, 'fill' => true, 'stroke' => true, 'stroke-width' => true, 'stroke-linecap' => true, 'stroke-linejoin' => true, 'aria-hidden' => true, 'class' => true, 'role' => true ),
		'path'     => array( 'd' => true, 'fill' => true, 'stroke' => true ),
		'circle'   => array( 'cx' => true, 'cy' => true, 'r' => true, 'fill' => true, 'stroke' => true ),
		'rect'     => array( 'x' => true, 'y' => true, 'width' => true, 'height' => true, 'rx' => true, 'ry' => true, 'fill' => true ),
		'line'     => array( 'x1' => true, 'y1' => true, 'x2' => true, 'y2' => true, 'stroke' => true ),
		'polyline' => array( 'points' => true, 'fill' => true, 'stroke' => true ),
		'polygon'  => array( 'points' => true, 'fill' => true, 'stroke' => true ),
		'g'        => array( 'fill' => true, 'stroke' => true, 'transform' => true ),
	);

	$icons = array(
		'phone'    => '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>',
		'email'    => '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>',
		'location' => '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>',
		'clock'    => '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>',
		'search'   => '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>',
		'heart'    => '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>',
		'cart'     => '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="9" cy="21" r="1"></circle><circle cx="20" cy="21" r="1"></circle><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path></svg>',
		'star'     => '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" aria-hidden="true"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>',
	);

	if ( isset( $icons[ $name ] ) ) {
		echo wp_kses( $icons[ $name ], $allowed_svg );
	}
}

/*--------------------------------------------------------------
 * Navigation Fallback
 *--------------------------------------------------------------*/

/**
 * Fallback navigation menu when no custom menu is assigned.
 *
 * Renders a hardcoded list of essential pages matching the luxury
 * brand navigation structure: Collections, About, Contact.
 *
 * @since 3.0.0
 * @return void
 */
function skyyrose_flagship_nav_fallback() {

	$items = array(
		array(
			'title'    => __( 'Collections', 'skyyrose-flagship' ),
			'url'      => home_url( '/collections/' ),
			'children' => array(
				array(
					'title' => __( 'Black Rose', 'skyyrose-flagship' ),
					'url'   => home_url( '/collection/black-rose/' ),
				),
				array(
					'title' => __( 'Love Hurts', 'skyyrose-flagship' ),
					'url'   => home_url( '/collection/love-hurts/' ),
				),
				array(
					'title' => __( 'Signature', 'skyyrose-flagship' ),
					'url'   => home_url( '/collection/signature/' ),
				),
				array(
					'title' => __( 'Kids Capsule', 'skyyrose-flagship' ),
					'url'   => home_url( '/collection/kids-capsule/' ),
				),
			),
		),
		array(
			'title'    => __( 'About', 'skyyrose-flagship' ),
			'url'      => home_url( '/about/' ),
			'children' => array(),
		),
		array(
			'title'    => __( 'Contact', 'skyyrose-flagship' ),
			'url'      => home_url( '/contact/' ),
			'children' => array(),
		),
	);

	echo '<ul class="navbar__menu">';

	foreach ( $items as $item ) {
		$has_children = ! empty( $item['children'] );
		$li_class     = $has_children ? ' class="menu-item menu-item-has-children"' : ' class="menu-item"';

		echo '<li' . $li_class . '>';
		echo '<a href="' . esc_url( $item['url'] ) . '">' . esc_html( $item['title'] ) . '</a>';

		if ( $has_children ) {
			echo '<ul class="sub-menu">';
			foreach ( $item['children'] as $child ) {
				echo '<li class="menu-item"><a href="' . esc_url( $child['url'] ) . '">' . esc_html( $child['title'] ) . '</a></li>';
			}
			echo '</ul>';
		}

		echo '</li>';
	}

	echo '</ul>';
}
