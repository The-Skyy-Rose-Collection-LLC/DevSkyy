<?php
/**
 * Template Name: Immersive - Kids Capsule
 *
 * "The Playroom" — warm rose-gold atmosphere, playful sophistication.
 * Luxury grows young. Mini-me collection for the next generation.
 *
 * AI-composited scene images with beacon-style product discovery.
 * Products loaded dynamically from WooCommerce (kids-capsule category).
 * Built on the shared immersive engine (immersive.css + immersive.js).
 *
 * @package SkyyRose_Flagship
 * @since   6.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/* ─────────────────────────────────────────────────────────
   Product Data — WooCommerce query by category.
   Distributes products across 2 rooms: first half in room 1,
   second half in room 2. Falls back to hardcoded if WC inactive.
   ───────────────────────────────────────────────────────── */

$products_per_room = array( array(), array() );

// Hotspot positions for each slot across rooms (left%, top%).
$hotspot_positions = array(
	// Room 0 — The Playroom.
	array( array( 22, 45 ), array( 50, 38 ), array( 75, 52 ) ),
	// Room 1 — The Runway.
	array( array( 28, 42 ), array( 55, 50 ), array( 78, 40 ) ),
);

if ( class_exists( 'WooCommerce' ) ) {
	$wc_products = wc_get_products( array(
		'category' => array( 'kids-capsule' ),
		'status'   => 'publish',
		'limit'    => 20,
		'orderby'  => 'menu_order',
		'order'    => 'ASC',
	) );

	$half = max( 1, (int) ceil( count( $wc_products ) / 2 ) );

	foreach ( $wc_products as $idx => $wc_product ) {
		$room_idx = $idx < $half ? 0 : 1;
		$slot     = $room_idx === 0 ? $idx : $idx - $half;
		$pos      = isset( $hotspot_positions[ $room_idx ][ $slot ] )
			? $hotspot_positions[ $room_idx ][ $slot ]
			: array( 30 + ( $slot * 18 ), 42 + ( $slot * 5 ) );

		$products_per_room[ $room_idx ][] = array(
			'id'         => $wc_product->get_slug(),
			'name'       => $wc_product->get_name(),
			'price'      => wp_strip_all_tags( wc_price( $wc_product->get_price() ) ),
			'image'      => wp_get_attachment_url( $wc_product->get_image_id() ),
			'url'        => $wc_product->get_permalink(),
			'collection' => __( 'Kids Capsule Collection', 'skyyrose-flagship' ),
			'sizes'      => '',
			'left'       => (string) $pos[0],
			'top'        => (string) $pos[1],
			'prop'       => 'playroom-display',
			'prop_label' => __( 'Playroom display', 'skyyrose-flagship' ),
		);
	}
} else {
	// Fallback hardcoded products.
	$fallback = array(
		array( 'name' => 'Mini Rose Hoodie',      'price' => '$95',  'room' => 0 ),
		array( 'name' => 'Little Crown Tee',       'price' => '$45',  'room' => 0 ),
		array( 'name' => 'Petal Joggers Kids',     'price' => '$65',  'room' => 1 ),
		array( 'name' => 'Baby Rose Onesie',       'price' => '$55',  'room' => 1 ),
	);

	foreach ( $fallback as $idx => $fb ) {
		$room_idx = $fb['room'];
		$slot     = count( $products_per_room[ $room_idx ] );
		$pos      = isset( $hotspot_positions[ $room_idx ][ $slot ] )
			? $hotspot_positions[ $room_idx ][ $slot ]
			: array( 40, 45 );

		$products_per_room[ $room_idx ][] = array(
			'id'         => sanitize_title( $fb['name'] ),
			'name'       => $fb['name'],
			'price'      => $fb['price'],
			'image'      => '',
			'url'        => home_url( '/pre-order/' ),
			'collection' => __( 'Kids Capsule Collection', 'skyyrose-flagship' ),
			'sizes'      => '',
			'left'       => (string) $pos[0],
			'top'        => (string) $pos[1],
			'prop'       => 'playroom-display',
			'prop_label' => __( 'Playroom display', 'skyyrose-flagship' ),
		);
	}
}

/* ─────────────────────────────────────────────────────────
   Room Config — 2 rooms using AI scene images.
   ───────────────────────────────────────────────────────── */

$rooms = array(
	array(
		'name'     => esc_html__( 'The Playroom', 'skyyrose-flagship' ),
		'image'    => 'scene-kids-capsule-playroom.webp',
		'products' => $products_per_room[0],
	),
	array(
		'name'     => esc_html__( 'The Runway', 'skyyrose-flagship' ),
		'image'    => 'scene-kids-capsule-runway.webp',
		'products' => $products_per_room[1],
	),
);

get_header();
?>

<main id="primary" class="site-main immersive-page" role="main" tabindex="-1">
	<?php
	get_template_part( 'template-parts/immersive-scene', null, array(
		'collection_slug' => 'kids-capsule',
		'collection_name' => __( 'Kids Capsule Collection', 'skyyrose-flagship' ),
		'world_name'      => __( 'The Playroom', 'skyyrose-flagship' ),
		'tagline'         => __( 'Luxury grows young.', 'skyyrose-flagship' ),
		'accent_color'    => '#B76E79',
		'collection_url'  => home_url( '/collection-kids-capsule/' ),
		'rooms'           => $rooms,
	) );
	?>
</main>

<?php
get_footer();
