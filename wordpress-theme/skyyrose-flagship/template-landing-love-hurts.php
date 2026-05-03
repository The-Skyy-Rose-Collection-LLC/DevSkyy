<?php
/**
 * Template Name: Landing — Love Hurts
 * Template Post Type: page
 *
 * Conversion-focused landing page for the Love Hurts collection.
 * "Hurts" is the founder's family name — this collection is deeply personal.
 * Voice: raw, emotional, vulnerability as strength.
 *
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
		'collection' => 'love-hurts',
		'data'       => skyyrose_get_landing_data( 'love-hurts' ),
	)
);
get_footer();
