<?php
/**
 * Template Name: Landing — Signature
 * Template Post Type: page
 *
 * Signature collection landing page — everyday luxury, foundation wardrobe.
 * Gold accent palette (#D4AF37). Uses shared landing-pages.css/js via enqueue.php.
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
		'collection' => 'signature',
		'data'       => skyyrose_get_landing_data( 'signature' ),
	)
);
get_footer();
