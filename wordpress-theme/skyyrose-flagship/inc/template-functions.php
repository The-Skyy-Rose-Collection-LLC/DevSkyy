<?php
/**
 * Template Functions
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Adds custom classes to the array of body classes.
 *
 * @since 1.0.0
 *
 * @param array $classes Classes for the body element.
 * @return array
 */
function skyyrose_custom_body_classes( $classes ) {
	// Add a class of hfeed to non-singular pages.
	if ( ! is_singular() ) {
		$classes[] = 'hfeed';
	}

	// Add a class if there is a custom header.
	if ( has_header_image() ) {
		$classes[] = 'has-header-image';
	}

	// Add class for full-width pages.
	if ( is_page_template( 'templates/template-fullwidth.php' ) ) {
		$classes[] = 'page-template-fullwidth';
	}

	return $classes;
}
add_filter( 'body_class', 'skyyrose_custom_body_classes' );

/**
 * Add a pingback url auto-discovery header for singularly identifiable articles.
 *
 * @since 1.0.0
 */
function skyyrose_pingback() {
	if ( is_singular() && pings_open() ) {
		echo '<link rel="pingback" href="', esc_url( get_bloginfo( 'pingback_url' ) ), '">';
	}
}
add_action( 'wp_head', 'skyyrose_pingback' );

// Breadcrumb function removed - using enhanced version from inc/accessibility-seo.php
// which includes ARIA attributes and Schema.org markup for better SEO and accessibility


/**
 * Custom excerpt length.
 *
 * @since 1.0.0
 *
 * @param int $length Excerpt length.
 * @return int
 */
function skyyrose_excerpt_length( $length ) {
	if ( is_admin() ) {
		return $length;
	}
	return 30;
}
add_filter( 'excerpt_length', 'skyyrose_excerpt_length', 999 );

/**
 * Custom excerpt more string.
 *
 * @since 1.0.0
 *
 * @param string $more The string shown within the more link.
 * @return string
 */
function skyyrose_excerpt_more( $more ) {
	if ( is_admin() ) {
		return $more;
	}
	return '&hellip;';
}
add_filter( 'excerpt_more', 'skyyrose_excerpt_more' );

/**
 * Get the post thumbnail URL or placeholder.
 *
 * @since 1.0.0
 *
 * @param string $size Thumbnail size.
 * @return string
 */
function skyyrose_get_post_thumbnail( $size = 'skyyrose-featured' ) {
	if ( has_post_thumbnail() ) {
		return get_the_post_thumbnail_url( get_the_ID(), $size );
	}

	// Return placeholder image.
	return SKYYROSE_ASSETS_URI . '/images/placeholder.jpg';
}

/**
 * Display estimated reading time.
 *
 * @since 1.0.0
 *
 * @param int $post_id Post ID.
 * @return string
 */
function skyyrose_reading_time( $post_id = null ) {
	if ( ! $post_id ) {
		$post_id = get_the_ID();
	}

	$content = get_post_field( 'post_content', $post_id );
	$word_count = str_word_count( wp_strip_all_tags( $content ) );
	$reading_time = ceil( $word_count / 200 ); // Average reading speed: 200 words per minute.

	/* translators: %s: Reading time in minutes */
	return sprintf( esc_html__( '%s min read', 'skyyrose-flagship' ), $reading_time );
}

/**
 * Display post meta information.
 *
 * @since 1.0.0
 */
function skyyrose_posted_on() {
	$time_string = '<time class="entry-date published updated" datetime="%1$s">%2$s</time>';
	if ( get_the_time( 'U' ) !== get_the_modified_time( 'U' ) ) {
		$time_string = '<time class="entry-date published" datetime="%1$s">%2$s</time><time class="updated" datetime="%3$s">%4$s</time>';
	}

	$time_string = sprintf(
		$time_string,
		esc_attr( get_the_date( DATE_W3C ) ),
		esc_html( get_the_date() ),
		esc_attr( get_the_modified_date( DATE_W3C ) ),
		esc_html( get_the_modified_date() )
	);

	$posted_on = sprintf(
		/* translators: %s: post date. */
		esc_html_x( 'Posted on %s', 'post date', 'skyyrose-flagship' ),
		'<a href="' . esc_url( get_permalink() ) . '" rel="bookmark">' . $time_string . '</a>'
	);

	echo '<span class="posted-on">' . $posted_on . '</span>'; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
}

/**
 * Display post author information.
 *
 * @since 1.0.0
 */
function skyyrose_posted_by() {
	$byline = sprintf(
		/* translators: %s: post author. */
		esc_html_x( 'by %s', 'post author', 'skyyrose-flagship' ),
		'<span class="author vcard"><a class="url fn n" href="' . esc_url( get_author_posts_url( get_the_author_meta( 'ID' ) ) ) . '">' . esc_html( get_the_author() ) . '</a></span>'
	);

	echo '<span class="byline"> ' . $byline . '</span>'; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
}

/**
 * Display entry footer meta.
 *
 * @since 1.0.0
 */
function skyyrose_entry_footer() {
	// Hide category and tag text for pages.
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
					array(
						'span' => array(
							'class' => array(),
						),
					)
				),
				wp_kses_post( get_the_title() )
			)
		);
		echo '</span>';
	}

	edit_post_link(
		sprintf(
			wp_kses(
				/* translators: %s: Name of current post. Only visible to screen readers */
				__( 'Edit <span class="screen-reader-text">%s</span>', 'skyyrose-flagship' ),
				array(
					'span' => array(
						'class' => array(),
					),
				)
			),
			wp_kses_post( get_the_title() )
		),
		'<span class="edit-link">',
		'</span>'
	);
}
