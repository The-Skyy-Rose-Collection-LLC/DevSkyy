<?php
/**
 * Front Page — storefront entry point.
 *
 * Commerce first: collection worlds introduce house, verified products stay
 * one scroll away, pre-order keeps its own focused journey.
 *
 * @package SkyyRose
 * @since 2.2.4
 */

defined( 'ABSPATH' ) || exit;

get_header();
get_template_part( 'template-parts/home/storefront' );
get_footer();
