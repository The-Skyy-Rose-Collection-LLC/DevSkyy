<?php
/**
 * Template Name: Experiences
 *
 * Hub page for all three SkyyRose immersive collection experiences.
 *
 * @package SkyyRose_Flagship
 * @since   4.1.0
 */
defined( 'ABSPATH' ) || exit;

$experiences_config = array(
	'page_title'  => __( 'Immersive Experiences', 'skyyrose-flagship' ),
	'tagline'     => __( 'Luxury Grows from Concrete.', 'skyyrose-flagship' ),
	'experiences' => array(
		array(
			'slug'        => 'black-rose',
			'name'        => __( 'Black Rose', 'skyyrose-flagship' ),
			'number'      => '01',
			'accent'      => '#8b0000',
			'accent_rgb'  => '139, 0, 0',
			'description' => __( 'Where darkness blooms, beauty follows.', 'skyyrose-flagship' ),
			'hero_image'  => SKYYROSE_ASSETS_URI . 'scenes/black-rose/black-rose-marble-rotunda.webp',
			'scene_2'     => SKYYROSE_ASSETS_URI . 'scenes/black-rose/black-rose-moonlit-courtyard.webp',
			'url'         => home_url( '/experience-black-rose/' ),
		),
		array(
			'slug'        => 'love-hurts',
			'name'        => __( 'Love Hurts', 'skyyrose-flagship' ),
			'number'      => '02',
			'accent'      => '#dc143c',
			'accent_rgb'  => '220, 20, 60',
			'description' => __( 'Passion etched in crimson.', 'skyyrose-flagship' ),
			'hero_image'  => SKYYROSE_ASSETS_URI . 'scenes/love-hurts/love-hurts-crimson-throne-room.webp',
			'scene_2'     => SKYYROSE_ASSETS_URI . 'scenes/love-hurts/love-hurts-gothic-ballroom.webp',
			'url'         => home_url( '/experience-love-hurts/' ),
		),
		array(
			'slug'        => 'signature',
			'name'        => __( 'Signature', 'skyyrose-flagship' ),
			'number'      => '03',
			'accent'      => '#d4af37',
			'accent_rgb'  => '212, 175, 55',
			'description' => __( 'Bay Area luxury, concrete-born.', 'skyyrose-flagship' ),
			'hero_image'  => SKYYROSE_ASSETS_URI . 'scenes/signature/signature-golden-gate-showroom-v2.webp',
			'scene_2'     => SKYYROSE_ASSETS_URI . 'scenes/signature/signature-waterfront-runway.webp',
			'url'         => home_url( '/experience-signature/' ),
		),
	),
);

include get_template_directory() . '/template-parts/experiences-page.php';
