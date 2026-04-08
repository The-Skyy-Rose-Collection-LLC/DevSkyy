<?php
/**
 * Template Name: Collection - Black Rose
 *
 * BLACK ROSE collection — masculine elegance, silver on deep black.
 * Delegates to unified collection layout with slug-specific content.
 *
 * @package SkyyRose_Flagship
 * @since   6.1.0
 */

defined( 'ABSPATH' ) || exit;

get_header();
get_template_part( 'template-parts/collection/page', null, array( 'slug' => 'black-rose' ) );
get_footer();
