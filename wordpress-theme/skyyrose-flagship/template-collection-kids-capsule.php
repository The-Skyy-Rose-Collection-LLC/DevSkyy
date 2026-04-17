<?php
/**
 * Template Name: Collection - Kids Capsule
 *
 * KIDS CAPSULE — luxury runs in the family. Rose-gold on dark.
 * Delegates to unified collection layout with slug-specific content.
 *
 * @package SkyyRose
 * @since   6.1.0
 */

defined( 'ABSPATH' ) || exit;

get_header();

if ( function_exists( 'skyyrose_kc_is_launch_mode' ) && skyyrose_kc_is_launch_mode() ) {
	get_template_part( 'template-parts/kids-capsule/teaser' );
} else {
	get_template_part( 'template-parts/collection/page', null, array( 'slug' => 'kids-capsule' ) );
}

get_footer();
