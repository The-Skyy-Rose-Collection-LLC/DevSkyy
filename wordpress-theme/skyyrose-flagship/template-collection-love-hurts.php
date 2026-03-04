<?php
/**
 * Template Name: Collection - Love Hurts
 *
 * LOVE HURTS collection page — v4.0.0 Elite Web Builder design.
 * Full-bleed hero, manifesto, featured product, catalog grid,
 * quick-view modal, newsletter, cross-collection nav.
 *
 * Crimson (#DC143C) accents on deep black.
 *
 * @package SkyyRose_Flagship
 * @since   4.0.0
 */

defined( 'ABSPATH' ) || exit;

$collection_config = array(
	'slug'              => 'love-hurts',
	'name'              => __( 'Love Hurts', 'skyyrose-flagship' ),
	'number'            => '02',
	'accent'            => '#DC143C',
	'accent_rgb'        => '220, 20, 60',
	'tagline'           => __( 'Wear your heart. Own your scars.', 'skyyrose-flagship' ),
	'meta_pieces'       => '',
	'meta_price_range'  => '',
	'meta_edition'      => __( 'Family Legacy', 'skyyrose-flagship' ),
	'hero_image'        => SKYYROSE_ASSETS_URI . '/scenes/love-hurts/love-hurts-crimson-throne-room.webp',

	'manifesto_eye'     => __( 'The Story', 'skyyrose-flagship' ),
	'manifesto_heading' => __( 'Named For Family.<br>Made For Feeling.', 'skyyrose-flagship' ),
	'manifesto_body'    => '<p>' . esc_html__( '"Hurts" is the founder\'s family name. This collection carries that weight — raw emotion transformed into wearable art.', 'skyyrose-flagship' ) . '</p>'
		. '<p>' . esc_html__( 'Gothic castle halls, crimson fire, rose petals on stone floors. Every thread channels the beauty in pain, the strength in vulnerability. Some things you don\'t hide. You wear them.', 'skyyrose-flagship' ) . '</p>',
	'manifesto_scene'   => SKYYROSE_ASSETS_URI . '/scenes/love-hurts/love-hurts-gothic-ballroom.webp',

	'featured_sku'      => 'lh-001',

	'nl_title'          => __( 'Wear Your Heart', 'skyyrose-flagship' ),
	'nl_desc'           => __( 'Early access to drops. Behind-the-scenes from Oakland. Stories that matter.', 'skyyrose-flagship' ),

	'immersive_url'     => home_url( '/experience-love-hurts/' ),

	'cross_nav'         => array(
		array(
			'slug'  => 'collection-black-rose',
			'label' => __( 'Black Rose', 'skyyrose-flagship' ),
			'class' => 'col-crossnav__link--br',
		),
		array(
			'slug'  => 'collection-signature',
			'label' => __( 'Signature', 'skyyrose-flagship' ),
			'class' => 'col-crossnav__link--sg',
		),
		array(
			'slug'  => 'collection-kids-capsule',
			'label' => __( 'Kids Capsule', 'skyyrose-flagship' ),
			'class' => 'col-crossnav__link--kc',
		),
	),
);

include get_template_directory() . '/template-parts/collection-page-v4.php';
