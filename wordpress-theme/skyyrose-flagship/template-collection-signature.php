<?php
/**
 * Template Name: Collection - Signature
 *
 * SIGNATURE collection — the origin. Gold on deep black.
 * Delegates to unified collection layout with slug-specific content.
 *
 * @package SkyyRose_Flagship
 * @since   6.1.0
 */

defined( 'ABSPATH' ) || exit;

get_header();
get_template_part( 'template-parts/collection/page', null, array( 'slug' => 'signature' ) );
get_footer();
