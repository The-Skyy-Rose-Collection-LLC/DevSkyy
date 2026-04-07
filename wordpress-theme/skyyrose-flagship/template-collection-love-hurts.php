<?php
/**
 * Template Name: Collection - Love Hurts
 *
 * LOVE HURTS collection — Beauty and the Beast, the Hurts bloodline.
 * Delegates to unified collection layout with slug-specific content.
 *
 * @package SkyyRose_Flagship
 * @since   6.1.0
 */

defined( 'ABSPATH' ) || exit;

get_header();
get_template_part( 'template-parts/collection/page', null, array( 'slug' => 'love-hurts' ) );
get_footer();
