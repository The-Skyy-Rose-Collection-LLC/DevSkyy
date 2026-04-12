<?php
/**
 * Active Builder Detection
 *
 * Provides utility functions to detect which page builder plugin is active
 * and whether a builder controls the current page output. Used throughout
 * the theme to avoid builder conflicts and conditional asset loading.
 *
 * @package SkyyRose
 * @since   1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Detect which page builder plugin is active.
 *
 * Returns the slug of the first detected builder. Detection order is
 * intentional — check the most common builders first for performance.
 *
 * @since 1.0.0
 * @return string Builder slug: 'elementor', 'divi', 'beaver-builder', 'bricks', or 'gutenberg'.
 */
function skyyrose_active_builder(): string {
	static $builder = null;

	if ( null !== $builder ) {
		return $builder;
	}

	if ( defined( 'ELEMENTOR_VERSION' ) || class_exists( '\Elementor\Plugin' ) ) {
		$builder = 'elementor';
		return $builder;
	}

	if ( defined( 'ET_BUILDER_VERSION' ) || class_exists( 'ET_Builder_Module' ) ) {
		$builder = 'divi';
		return $builder;
	}

	if ( class_exists( 'FLBuilderLoader' ) || defined( 'FL_BUILDER_VERSION' ) ) {
		$builder = 'beaver-builder';
		return $builder;
	}

	if ( defined( 'BRICKS_VERSION' ) ) {
		$builder = 'bricks';
		return $builder;
	}

	$builder = 'gutenberg';
	return $builder;
}

/**
 * Check if a page builder controls the current page output.
 *
 * When true, the theme should defer to the builder for content rendering
 * and avoid outputting its own template markup in the content area.
 *
 * @since 1.0.0
 * @param int|null $post_id Post ID to check. Defaults to current post.
 * @return bool True if a builder owns the current page template.
 */
function skyyrose_builder_owns_template( $post_id = null ): bool {
	if ( null === $post_id ) {
		$post_id = get_the_ID();
	}

	if ( ! $post_id ) {
		return false;
	}

	$builder = skyyrose_active_builder();

	switch ( $builder ) {
		case 'elementor':
			if ( class_exists( '\Elementor\Plugin' ) && \Elementor\Plugin::$instance->documents ) {
				$document = \Elementor\Plugin::$instance->documents->get( $post_id );
				if ( $document && $document->is_built_with_elementor() ) {
					return true;
				}
			}
			break;

		case 'divi':
			if ( 'on' === get_post_meta( $post_id, '_et_pb_use_builder', true ) ) {
				return true;
			}
			break;

		case 'beaver-builder':
			if ( class_exists( 'FLBuilderModel' ) && FLBuilderModel::is_builder_enabled( $post_id ) ) {
				return true;
			}
			break;

		case 'bricks':
			if ( 'bricks' === get_post_meta( $post_id, '_bricks_editor_mode', true ) ) {
				return true;
			}
			break;
	}

	return false;
}
