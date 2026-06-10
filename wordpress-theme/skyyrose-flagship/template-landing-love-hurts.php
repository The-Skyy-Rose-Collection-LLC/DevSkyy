<?php
/**
 * Template Name: Landing — Love Hurts
 * Template Post Type: page
 *
 * Thin stub — all content and markup live in template-parts/landing/page.php.
 * Data is sourced from inc/landing-content.php via skyyrose_get_landing_content().
 *
 * @package SkyyRose
 * @since   6.6.0
 */

defined( 'ABSPATH' ) || exit;

get_header();

get_template_part( 'template-parts/landing/page', null, array( 'slug' => 'love-hurts' ) );

get_footer();
