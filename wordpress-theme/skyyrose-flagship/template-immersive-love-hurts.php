<?php
/**
 * Template Name: Immersive - Love Hurts
 *
 * "The Cathedral" — candlelit chamber, enchanted rose dome, stained glass.
 * Beauty and the Beast narrative reimagined. "Every petal tells a story."
 *
 * AI-composited scene image with beacon-style product discovery.
 * Built on the shared immersive engine (immersive.css + immersive.js).
 *
 * @package SkyyRose
 * @since   3.0.0
 * @updated 6.5.2 — Collapsed to single cathedral room using skyyrose_immersive_product() adapter.
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/*
─────────────────────────────────────────────────────────
	Room Data — The Cathedral (single AI-composited scene).
	Four LH SKUs placed on cathedral props (mannequin, pew,
	float, candelabra). Beauty-and-the-Beast rose dome
	centers the frame.
	───────────────────────────────────────────────────────── */

// SOT-wired scene image. skyyrose_sot_scene() returns imagery.scene_portrait.resolved
// from data/collections/love-hurts/sot.json. basename() strips the directory prefix so
// scene.php can safely prepend assets/images/immersive/.
// Falls back to the original hand-maintained filename when the accessor returns ''.
$_sot_scene_lh       = skyyrose_sot_scene( 'love-hurts' );
$_lh_room1_image     = ( '' !== $_sot_scene_lh ) ? basename( $_sot_scene_lh ) : 'scene-love-hurts-cathedral.webp';

$rooms = array(

	array(
		'name'     => esc_html__( 'The Cathedral', 'skyyrose' ),
		'image'    => $_lh_room1_image,
		'products' => array(
			skyyrose_immersive_product(
				'lh-004',
				array(
					'left'       => '32',
					'top'        => '50',
					'prop'       => 'mannequin',
					'prop_label' => __( 'On the mannequin stand', 'skyyrose' ),
				)
			),
			skyyrose_immersive_product(
				'lh-003',
				array(
					'left'       => '67',
					'top'        => '35',
					'prop'       => 'float',
					'prop_label' => __( 'Suspended above the pews', 'skyyrose' ),
				)
			),
			skyyrose_immersive_product(
				'lh-002',
				array(
					'left'       => '72',
					'top'        => '62',
					'prop'       => 'pew',
					'prop_label' => __( 'Draped across the pew', 'skyyrose' ),
				)
			),
			skyyrose_immersive_product(
				'lh-006',
				array(
					'left'       => '83',
					'top'        => '50',
					'prop'       => 'candelabra',
					'prop_label' => __( 'Hanging from the candelabra', 'skyyrose' ),
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
			'collection_slug' => 'love-hurts',
			'collection_name' => __( 'Love Hurts Collection', 'skyyrose' ),
			'world_name'      => __( 'The Cathedral', 'skyyrose' ),
			'tagline'         => __( 'Every petal tells a story.', 'skyyrose' ),
			'accent_color'    => '#DC143C',
			'collection_url'  => home_url( '/collection-love-hurts/' ),
			'rooms'           => $rooms,
		)
	);
	?>
</main>

<?php
get_footer();
