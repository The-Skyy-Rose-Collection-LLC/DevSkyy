<?php
/**
 * Template Name: Collection - Kids Capsule
 *
 * KIDS CAPSULE — luxury runs in the family. Rose-gold on dark.
 * Delegates to unified collection layout with slug-specific content.
 *
 * @package SkyyRose_Flagship
 * @since   6.1.0
 */

defined( 'ABSPATH' ) || exit;

get_header();
get_template_part( 'template-parts/collection/page', null, array( 'slug' => 'kids-capsule' ) );
get_footer();
