<?php
/**
 * Block Patterns — Registration and Content Loader
 *
 * Registers block pattern categories for all SkyyRose collections
 * and provides a helper function to load pattern content from
 * the patterns/ directory.
 *
 * Individual patterns are auto-registered by WordPress core from
 * the patterns/ directory (WP 6.0+) using PHP file header comments.
 * This file handles category registration and the content loader utility.
 *
 * @package SkyyRose
 * @since   6.6.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Register block pattern categories for the theme.
 *
 * @since 6.6.0
 * @return void
 */
function skyyrose_register_pattern_categories() {
	$categories = array(
		'skyyrose'             => array(
			'label'       => esc_html__( 'SkyyRose', 'skyyrose' ),
			'description' => esc_html__( 'Luxury fashion brand patterns', 'skyyrose' ),
		),
		'skyyrose-collections' => array(
			'label'       => esc_html__( 'SkyyRose Collections', 'skyyrose' ),
			'description' => esc_html__( 'Collection-specific hero sections and grids', 'skyyrose' ),
		),
		'skyyrose-commerce'    => array(
			'label'       => esc_html__( 'SkyyRose Commerce', 'skyyrose' ),
			'description' => esc_html__( 'Product display and shopping patterns', 'skyyrose' ),
		),
	);

	foreach ( $categories as $slug => $args ) {
		register_block_pattern_category( $slug, $args );
	}
}
add_action( 'init', 'skyyrose_register_pattern_categories' );

/**
 * Load a pattern's content from the patterns/ directory.
 *
 * Reads a PHP file from patterns/, captures its output, and returns
 * the block markup string. This allows patterns to use PHP for
 * dynamic content (e.g., collection config data) while outputting
 * valid block markup.
 *
 * @since 6.6.0
 *
 * @param  string $pattern_slug Pattern slug (filename without .php).
 * @return string Block markup content, or empty string if not found.
 */
function skyyrose_get_pattern( $pattern_slug ) {
	$sanitized = sanitize_file_name( $pattern_slug );
	$file_path = SKYYROSE_DIR . '/patterns/' . $sanitized . '.php';

	if ( ! file_exists( $file_path ) ) {
		return '';
	}

	ob_start();
	include $file_path;
	return ob_get_clean();
}
