<?php
/**
 * Template Name: Collection - Signature
 *
 * SIGNATURE collection page — v4.0.0 Elite Web Builder design.
 * Full-bleed hero, manifesto, featured product, catalog grid,
 * quick-view modal, newsletter, cross-collection nav.
 *
 * Gold (#D4AF37) accents on deep black.
 *
 * @package SkyyRose_Flagship
 * @since   4.0.0
 */

defined( 'ABSPATH' ) || exit;

$collection_config = array(
	'slug'              => 'signature',
	'name'              => __( 'Signature', 'skyyrose-flagship' ),
	'number'            => '03',
	'accent'            => '#D4AF37',
	'accent_rgb'        => '212, 175, 55',
	'tagline'           => __( 'The foundation of any wardrobe worth building.', 'skyyrose-flagship' ),
	'meta_pieces'       => '',
	'meta_price_range'  => '',
	'meta_edition'      => __( 'Foundation Wardrobe', 'skyyrose-flagship' ),
	'hero_image'        => SKYYROSE_ASSETS_URI . '/scenes/signature/signature-golden-gate-showroom.webp',

	'manifesto_eye'     => __( 'The Standard', 'skyyrose-flagship' ),
	'manifesto_heading' => __( 'Start Here.<br>Build Everything.', 'skyyrose-flagship' ),
	'manifesto_body'    => '<p>' . esc_html__( 'Clean lines. Quality materials. Pieces that work as hard as you do. No logos screaming for attention. Just clothes that fit right and last.', 'skyyrose-flagship' ) . '</p>'
		. '<p>' . esc_html__( 'Signature is the foundation — Italian wool-blends, premium cotton, rose-gold hardware. Grand ballroom energy in everyday wear. Timeless pieces built for the long game.', 'skyyrose-flagship' ) . '</p>',
	'manifesto_scene'   => SKYYROSE_ASSETS_URI . '/scenes/signature/signature-waterfront-runway.webp',

	'featured_sku'      => 'sg-d01',

	'nl_title'          => __( 'Start Here. Build Everything.', 'skyyrose-flagship' ),
	'nl_desc'           => __( 'First access to new pieces. Curated Oakland style. No noise.', 'skyyrose-flagship' ),

	'immersive_url'     => home_url( '/experience-signature/' ),

	'cross_nav'         => array(
		array(
			'slug'  => 'collection-black-rose',
			'label' => __( 'Black Rose', 'skyyrose-flagship' ),
			'class' => 'col-crossnav__link--br',
		),
		array(
			'slug'  => 'collection-love-hurts',
			'label' => __( 'Love Hurts', 'skyyrose-flagship' ),
			'class' => 'col-crossnav__link--lh',
		),
		array(
			'slug'  => 'collection-kids-capsule',
			'label' => __( 'Kids Capsule', 'skyyrose-flagship' ),
			'class' => 'col-crossnav__link--kc',
		),
	),
);

include get_template_directory() . '/template-parts/collection-page-v4.php';
