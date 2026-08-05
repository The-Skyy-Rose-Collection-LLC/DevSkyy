<?php
/**
 * Builder-neutral page ownership and Elementor/Divi integration.
 *
 * The theme owns its commerce and collection fallbacks. Builders may own page
 * content explicitly, while Elementor Pro may replace registered theme
 * locations when an assigned template exists.
 *
 * @package SkyyRoseFlagship2
 */

defined( 'ABSPATH' ) || exit;

/** Register builder theme support without requiring either plugin. */
function skyyrose2_builder_support() {
	add_theme_support( 'elementor' );
	add_theme_support( 'elementor-pro' );
	add_theme_support( 'et-builder' );
}
add_action( 'after_setup_theme', 'skyyrose2_builder_support', 20 );

/**
 * Register every Elementor Pro core location rendered by V2 templates.
 *
 * @param object $locations_manager Elementor theme locations manager.
 * @return void
 */
function skyyrose2_register_elementor_locations( $locations_manager ) {
	if ( is_object( $locations_manager ) && method_exists( $locations_manager, 'register_all_core_location' ) ) {
		$locations_manager->register_all_core_location();
	}
}
add_action( 'elementor/theme/register_locations', 'skyyrose2_register_elementor_locations' );

/**
 * Render an assigned Elementor Pro location once, with a theme fallback.
 *
 * @param string $location Elementor core location.
 * @return bool Whether Elementor rendered the location.
 */
function skyyrose2_render_builder_location( $location ) {
	$location = sanitize_key( $location );
	if ( ! isset( $GLOBALS['skyyrose2_builder_locations'] ) || ! is_array( $GLOBALS['skyyrose2_builder_locations'] ) ) {
		$GLOBALS['skyyrose2_builder_locations'] = array();
	}
	if ( array_key_exists( $location, $GLOBALS['skyyrose2_builder_locations'] ) ) {
		return (bool) $GLOBALS['skyyrose2_builder_locations'][ $location ];
	}

	$rendered = function_exists( 'elementor_theme_do_location' ) && elementor_theme_do_location( $location );
	$GLOBALS['skyyrose2_builder_locations'][ $location ] = (bool) $rendered;
	return (bool) $rendered;
}

/**
 * Check whether an Elementor location already replaced the theme fallback.
 *
 * @param string $location Elementor core location.
 * @return bool
 */
function skyyrose2_builder_location_rendered( $location ) {
	return ! empty( $GLOBALS['skyyrose2_builder_locations'][ sanitize_key( $location ) ] );
}

/**
 * Identify the active builder that explicitly owns a page.
 *
 * @param int $post_id Page or post ID.
 * @return string Empty string or builder slug.
 */
function skyyrose2_page_builder( $post_id ) {
	$post_id = absint( $post_id );
	if ( ! $post_id ) {
		return '';
	}

	if (
		( defined( 'ELEMENTOR_VERSION' ) || class_exists( '\\Elementor\\Plugin' ) )
		&& 'builder' === get_post_meta( $post_id, '_elementor_edit_mode', true )
	) {
		return 'elementor';
	}
	if (
		( defined( 'ET_BUILDER_VERSION' ) || class_exists( 'ET_Builder_Module' ) )
		&& 'on' === get_post_meta( $post_id, '_et_pb_use_builder', true )
	) {
		return 'divi';
	}
	if (
		( defined( 'FL_BUILDER_VERSION' ) || class_exists( 'FLBuilderLoader' ) )
		&& ( '1' === (string) get_post_meta( $post_id, '_fl_builder_enabled', true )
			|| ( class_exists( 'FLBuilderModel' )
				&& method_exists( 'FLBuilderModel', 'is_builder_enabled' )
				&& FLBuilderModel::is_builder_enabled( $post_id ) ) )
	) {
		return 'beaver-builder';
	}
	return '';
}

/**
 * Check whether a builder should receive an unwrapped content area.
 *
 * @param int|null $post_id Page or post ID. Defaults to the queried object.
 * @return bool
 */
function skyyrose2_builder_owns_page( $post_id = null ) {
	$post_id = null === $post_id ? get_queried_object_id() : $post_id;
	return '' !== skyyrose2_page_builder( $post_id );
}

/**
 * Return content classes that account for the fixed fallback header.
 *
 * @return string
 */
function skyyrose2_builder_content_class() {
	$classes = array( 'sr2-builder-content' );
	if ( ! skyyrose2_builder_location_rendered( 'header' ) ) {
		$classes[] = 'sr2-builder-content--theme-header';
	}
	return implode( ' ', $classes );
}

/**
 * Mark builder-owned pages for scoped CSS and troubleshooting.
 *
 * @param array<int,string> $classes Existing body classes.
 * @return array<int,string>
 */
function skyyrose2_builder_body_classes( $classes ) {
	$builder = skyyrose2_page_builder( get_queried_object_id() );
	if ( $builder ) {
		$classes[] = 'sr2-builder-active';
		$classes[] = 'sr2-builder-' . sanitize_html_class( $builder );
	}
	return $classes;
}
add_filter( 'body_class', 'skyyrose2_builder_body_classes' );

/** Keep builder typography on the self-hosted SkyyRose font system. */
add_filter( 'elementor/frontend/print_google_fonts', '__return_false' );

/**
 * Permit the progressive product viewer custom element in Divi code modules.
 *
 * @param array<int,string> $tags Allowed tags.
 * @return array<int,string>
 */
function skyyrose2_divi_allowed_tags( $tags ) {
	if ( is_array( $tags ) && ! in_array( 'model-viewer', $tags, true ) ) {
		$tags[] = 'model-viewer';
	}
	return $tags;
}
add_filter( 'et_pb_allowed_tags', 'skyyrose2_divi_allowed_tags' );
