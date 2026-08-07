<?php
/**
 * Template Name: Collections World SOT
 *
 * @package SkyyRoseFlagshipSOT
 */

defined( 'ABSPATH' ) || exit;
?><!doctype html><html <?php language_attributes(); ?>><head><meta charset="<?php bloginfo( 'charset' ); ?>"><meta name="viewport" content="width=device-width, initial-scale=1"><?php wp_head(); ?></head><body <?php body_class( 'srs-scroll-world' ); ?>><?php wp_body_open(); ?><a class="srs-skip" href="#srs-world"><?php esc_html_e( 'Skip to collections', 'skyyrose-flagship-sot' ); ?></a><div id="srs-world" tabindex="-1"></div><noscript><main class="srs-noscript"><h1><?php esc_html_e( 'Collections', 'skyyrose-flagship-sot' ); ?></h1><a href="<?php echo esc_url( home_url( '/collections/' ) ); ?>"><?php esc_html_e( 'Shop collections', 'skyyrose-flagship-sot' ); ?></a></main></noscript><?php wp_footer(); ?></body></html>
