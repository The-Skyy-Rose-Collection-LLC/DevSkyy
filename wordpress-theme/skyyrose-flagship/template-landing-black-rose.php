<?php
/**
 * Template Name: Landing — Black Rose
 * Template Post Type: page
 *
 * Conversion-focused landing page for the Black Rose collection.
 * Per-collection content lives in inc/landing-data.php; rendering happens
 * in template-parts/landing/page.php (shared across all 3 landing templates).
 *
 * @package SkyyRose
 * @since   7.1.0
 */

defined( 'ABSPATH' ) || exit;

get_header();
get_template_part(
	'template-parts/landing/page',
	null,
	array(
		'collection' => 'black-rose',
		'data'       => skyyrose_get_landing_data( 'black-rose' ),
	)
);
get_footer();
