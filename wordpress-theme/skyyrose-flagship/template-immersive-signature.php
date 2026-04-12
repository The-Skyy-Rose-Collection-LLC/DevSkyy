<?php
/**
 * Template Name: Immersive - Signature
 *
 * "The Golden Gate Runway" — San Francisco waterfront, golden hour,
 * Golden Gate Bridge showroom. Bay Area luxury.
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

/*
─────────────────────────────────────────────────────────
	Room Data — 2 atmospheric rooms with product hotspots.
	Products use skyyrose_immersive_product() from product-catalog.php.
	───────────────────────────────────────────────────────── */

$rooms = array(

	// Room 1 — The Golden Gate.
	array(
		'name'     => esc_html__( 'The Golden Gate', 'skyyrose' ),
		'image'    => 'scene-signature-golden-gate.webp',
		'products' => array(
			skyyrose_immersive_product(
				'sg-009',
				array(
					'left'       => '15',
					'top'        => '42',
					'prop'       => 'glass-orb',
					'prop_label' => __( 'Inside glass orb display case', 'skyyrose' ),
				)
			),
			skyyrose_immersive_product(
				'sg-002',
				array(
					'left'       => '42',
					'top'        => '35',
					'prop'       => 'gold-display-frame',
					'prop_label' => __( 'Hanging in gold-lit LED display frame', 'skyyrose' ),
				)
			),
			skyyrose_immersive_product(
				'sg-010',
				array(
					'left'       => '50',
					'top'        => '38',
					'prop'       => 'gold-display-frame',
					'prop_label' => __( 'Hanging in gold-lit LED display frame', 'skyyrose' ),
				)
			),
			skyyrose_immersive_product(
				'sg-006',
				array(
					'left'       => '62',
					'top'        => '36',
					'prop'       => 'gold-display-frame',
					'prop_label' => __( 'Hanging in gold-lit LED display frame', 'skyyrose' ),
				)
			),
			skyyrose_immersive_product(
				'sg-001',
				array(
					'left'       => '78',
					'top'        => '50',
					'prop'       => 'marble-pedestal',
					'prop_label' => __( 'Featured on stepped marble pedestal', 'skyyrose' ),
				)
			),
		),
	),

	// Room 2 — The Bay Bridge.
	array(
		'name'     => esc_html__( 'The Bay Bridge', 'skyyrose' ),
		'image'    => 'scene-signature-bay-bridge.webp',
		'products' => array(
			skyyrose_immersive_product(
				'sg-003',
				array(
					'left'       => '18',
					'top'        => '38',
					'prop'       => 'clothing-rack',
					'prop_label' => __( 'Hanging on left wall clothing rack', 'skyyrose' ),
				)
			),
			skyyrose_immersive_product(
				'sg-005',
				array(
					'left'       => '50',
					'top'        => '52',
					'prop'       => 'marble-display-table',
					'prop_label' => __( 'Featured on center marble display table', 'skyyrose' ),
				)
			),
			skyyrose_immersive_product(
				'sg-007',
				array(
					'left'       => '32',
					'top'        => '48',
					'prop'       => 'marble-pedestal',
					'prop_label' => __( 'On left marble pedestal', 'skyyrose' ),
				)
			),
			skyyrose_immersive_product(
				'sg-004',
				array(
					'left'       => '72',
					'top'        => '38',
					'prop'       => 'clothing-rack',
					'prop_label' => __( 'Hanging on right wall clothing rack', 'skyyrose' ),
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
		'template-parts/immersive-scene',
		null,
		array(
			'collection_slug' => 'signature',
			'collection_name' => __( 'Signature Collection', 'skyyrose' ),
			'world_name'      => __( 'The Golden Gate Runway', 'skyyrose' ),
			'tagline'         => __( 'The Origin. The Crown.', 'skyyrose' ),
			'accent_color'    => '#D4AF37',
			'collection_url'  => home_url( '/collection-signature/' ),
			'rooms'           => $rooms,
		)
	);
	?>
</main>

<?php
get_footer();
