<?php
/**
 * Template Name: Immersive - Kids Capsule
 *
 * "The Playroom" — warm rose-gold atmosphere, playful sophistication.
 * Luxury grows young. Mini-me collection for the next generation.
 *
 * AI-composited scene images with beacon-style product discovery.
 * Built on the shared immersive engine (immersive.css + immersive.js).
 *
 * @package SkyyRose
 * @since   6.0.0
 * @updated 6.5.2 — Refactored to skyyrose_immersive_product() adapter; removed wc_get_products().
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/*
─────────────────────────────────────────────────────────
	Room Data — 2 atmospheric rooms, 1 product per room (catalog has 2 Kids SKUs).
	Cap: 3 products per room maximum (hotspot position formula overflows at 4+).
	Uses skyyrose_immersive_product() adapter — no direct WooCommerce queries.
	───────────────────────────────────────────────────────── */

// SOT-wired scene image for Room 1. skyyrose_sot_scene() returns imagery.scene_portrait.resolved
// from data/collections/kids-capsule/sot.json. Kids Capsule has no scene_portrait in sot.json
// (null) so the accessor returns '' and the fallback fires, preserving the hand-maintained value.
// basename() strips any directory prefix so scene.php can safely prepend assets/images/immersive/.
$_sot_scene_kc       = skyyrose_sot_scene( 'kids-capsule' );
$_kc_room1_image     = ( '' !== $_sot_scene_kc ) ? basename( $_sot_scene_kc ) : 'scene-kids-capsule-playroom.webp';

$rooms = array(

	// Room 1 — The Playroom.
	array(
		'name'     => esc_html__( 'The Playroom', 'skyyrose' ),
		'image'    => $_kc_room1_image,
		'products' => array(
			skyyrose_immersive_product(
				'kids-001',
				array(
					'left'       => '50',
					'top'        => '38',
					'prop'       => 'playroom-display',
					'prop_label' => __( 'Featured on center playroom display', 'skyyrose' ),
				)
			),
		),
	),

	// Room 2 — The Runway.
	array(
		'name'     => esc_html__( 'The Runway', 'skyyrose' ),
		'image'    => 'scene-kids-capsule-runway.webp',
		'products' => array(
			skyyrose_immersive_product(
				'kids-002',
				array(
					'left'       => '50',
					'top'        => '38',
					'prop'       => 'playroom-display',
					'prop_label' => __( 'Featured on center runway display', 'skyyrose' ),
				)
			),
		),
	),
);

// Remove empty entries (unpublished products filtered by skyyrose_immersive_product()).
foreach ( $rooms as &$room ) {
	$room['products'] = array_values( array_filter( $room['products'] ) );
}
unset( $room );

get_header();
?>

<main id="primary" class="site-main immersive-page" role="main" tabindex="-1">
	<?php
	get_template_part(
		'template-parts/immersive/scene',
		null,
		array(
			'collection_slug' => 'kids-capsule',
			'collection_name' => __( 'Kids Capsule Collection', 'skyyrose' ),
			'world_name'      => __( 'The Playroom', 'skyyrose' ),
			'tagline'         => __( 'Luxury runs in the family.', 'skyyrose' ),
			'accent_color'    => '#B76E79',
			'collection_url'  => home_url( '/collection-kids-capsule/' ),
			'rooms'           => $rooms,
		)
	);
	?>
</main>

<?php
get_footer();
