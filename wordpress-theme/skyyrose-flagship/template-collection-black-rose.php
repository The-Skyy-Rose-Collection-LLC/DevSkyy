<?php
/**
 * Template Name: Collection - Black Rose
 *
 * BLACK ROSE collection page — v4.0.0 Elite Web Builder design.
 * Full-bleed hero, manifesto, featured product, catalog grid,
 * quick-view modal, newsletter, cross-collection nav.
 *
 * Metallic silver (#C0C0C0) accents on deep black.
 *
 * @package SkyyRose_Flagship
 * @since   4.0.0
 */

defined( 'ABSPATH' ) || exit;

$collection_config = array(
	'slug'              => 'black-rose',
	'name'              => __( 'Black Rose', 'skyyrose-flagship' ),
	'number'            => '01',
	'accent'            => '#C0C0C0',
	'accent_rgb'        => '192, 192, 192',
	'tagline'           => __( 'Where darkness blooms, beauty follows.', 'skyyrose-flagship' ),
	'meta_pieces'       => '',
	'meta_price_range'  => '',
	'meta_edition'      => __( 'Limited Edition', 'skyyrose-flagship' ),
	'hero_image'        => SKYYROSE_ASSETS_URI . '/scenes/black-rose/black-rose-marble-rotunda.webp',
	'hero_logo'         => get_template_directory_uri() . '/assets/branding/black-rose-logo-hero-transparent.png',

	'manifesto_eye'     => __( 'The Philosophy', 'skyyrose-flagship' ),
	'manifesto_heading' => __( 'Limited Drops.<br>Unlimited Vision.', 'skyyrose-flagship' ),
	'manifesto_body'    => '<p>' . esc_html__( 'Born from moonlit gardens and shadowed cathedrals, the Black Rose collection is an ode to those who find beauty in the dark. Each piece is woven with gothic elegance — deep blacks punctuated by silver moonlight accents, roses that bloom only after midnight.', 'skyyrose-flagship' ) . '</p>'
		. '<p>' . esc_html__( 'This is not fashion for the faint of heart. It is armor for the bold, the defiant, the eternally romantic. Limited drops. Once they are gone, they are gone.', 'skyyrose-flagship' ) . '</p>',
	'manifesto_scene'   => SKYYROSE_ASSETS_URI . '/scenes/black-rose/black-rose-moonlit-courtyard.webp',

	'featured_sku'      => 'br-d02',

	'nl_title'          => __( 'Available Until It\'s Not', 'skyyrose-flagship' ),
	'nl_desc'           => __( 'First access to drops. Limited pieces. No second chances.', 'skyyrose-flagship' ),

	'immersive_url'     => home_url( '/experience-black-rose/' ),

	'cross_nav'         => array(
		array(
			'slug'  => 'collection-love-hurts',
			'label' => __( 'Love Hurts', 'skyyrose-flagship' ),
			'class' => 'col-crossnav__link--lh',
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
