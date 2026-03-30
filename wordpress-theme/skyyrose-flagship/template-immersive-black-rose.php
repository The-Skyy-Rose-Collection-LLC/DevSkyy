<?php
/**
 * Template Name: Immersive - Black Rose
 *
 * "The Bay Bridge" — East Oakland rooftop, night skyline, Bay Bridge glow.
 * Street luxury. "Luxury Grows from Concrete."
 *
 * AI-composited scene images with beacon-style product discovery.
 * Built on the shared immersive engine (immersive.css + immersive.js).
 *
 * @package SkyyRose_Flagship
 * @since   3.0.0
 * @updated 6.0.0 — Rebuild on shared 2D engine, AI scene images
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/* ─────────────────────────────────────────────────────────
   Room Data — 2 atmospheric rooms with product hotspots.
   ───────────────────────────────────────────────────────── */

$rooms = array(

	// Room 1 — Moonlit Courtyard.
	array(
		'name'  => esc_html__( 'Moonlit Courtyard', 'skyyrose-flagship' ),
		'image' => 'scene-black-rose-courtyard.webp',
		'products'  => array(
			skyyrose_immersive_product( 'br-006', array(
				'left'       => '15',
				'top'        => '42',
				'prop'       => 'marble-statue',
				'prop_label' => __( 'Draped over marble garden statue', 'skyyrose-flagship' ),
			) ),
			skyyrose_immersive_product( 'br-005', array(
				'left'       => '38',
				'top'        => '50',
				'prop'       => 'fountain-edge',
				'prop_label' => __( 'Folded on fountain edge', 'skyyrose-flagship' ),
			) ),
			skyyrose_immersive_product( 'br-002', array(
				'left'       => '62',
				'top'        => '55',
				'prop'       => 'topiary-base',
				'prop_label' => __( 'Folded at base of rose topiary', 'skyyrose-flagship' ),
			) ),
			skyyrose_immersive_product( 'br-007', array(
				'left'       => '82',
				'top'        => '48',
				'prop'       => 'statue-pedestal',
				'prop_label' => __( 'Draped over statue pedestal', 'skyyrose-flagship' ),
			) ),
		),
	),

	// Room 2 — Iron Gazebo.
	array(
		'name'  => esc_html__( 'Iron Gazebo', 'skyyrose-flagship' ),
		'image' => 'scene-black-rose-gazebo.webp',
		'products'  => array(
			skyyrose_immersive_product( 'br-004', array(
				'left'       => '30',
				'top'        => '40',
				'prop'       => 'iron-gazebo',
				'prop_label' => __( 'Displayed inside iron gazebo', 'skyyrose-flagship' ),
			) ),
			skyyrose_immersive_product( 'br-001', array(
				'left'       => '55',
				'top'        => '35',
				'prop'       => 'hedge-arch',
				'prop_label' => __( 'Hanging from rose hedge archway', 'skyyrose-flagship' ),
			) ),
			skyyrose_immersive_product( 'br-003', array(
				'left'       => '72',
				'top'        => '50',
				'prop'       => 'cobblestone-bench',
				'prop_label' => __( 'Draped over cobblestone garden bench', 'skyyrose-flagship' ),
			) ),
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
	get_template_part( 'template-parts/immersive-scene', null, array(
		'collection_slug' => 'black-rose',
		'collection_name' => __( 'Black Rose Collection', 'skyyrose-flagship' ),
		'world_name'      => __( 'The Bay Bridge', 'skyyrose-flagship' ),
		'tagline'         => __( 'Luxury Grows from Concrete.', 'skyyrose-flagship' ),
		'accent_color'    => '#C0C0C0',
		'collection_url'  => home_url( '/collection-black-rose/' ),
		'rooms'           => $rooms,
	) );
	?>
</main>

<?php
get_footer();
