<?php
/**
 * Template Name: Immersive - Love Hurts
 *
 * "The Cathedral" — candlelit chambers, enchanted rose, crimson
 * glass dome. Beauty and the Beast narrative reimagined.
 *
 * AI-composited scene images with beacon-style product discovery.
 * Products loaded dynamically from WooCommerce (love-hurts category).
 * Built on the shared immersive engine (immersive.css + immersive.js).
 *
 * @package SkyyRose_Flagship
 * @since   3.0.0
 * @updated 6.0.0 — Rebuild on shared 2D engine, AI scene images, WC category query, GDPR fix
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/* ─────────────────────────────────────────────────────────
   Product Data — WooCommerce query by category.
   Distributes products across 2 rooms: first half in room 0,
   remainder in room 1. Falls back to hardcoded if WC inactive.
   ───────────────────────────────────────────────────────── */

$products_per_room = array( array(), array() );

// Hotspot positions for each slot across rooms (left%, top%).
$hotspot_positions = array(
	// Room 0 — The Bedroom.
	array( array( 25, 55 ), array( 55, 42 ), array( 78, 50 ) ),
	// Room 1 — The Balcony.
	array( array( 22, 42 ), array( 50, 55 ), array( 75, 45 ) ),
);

if ( class_exists( 'WooCommerce' ) ) {
	$wc_products = wc_get_products( array(
		'category' => array( 'love-hurts' ),
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
			'image'      => $wc_product->get_image_id() ? wp_get_attachment_url( $wc_product->get_image_id() ) : '',
			'url'        => $wc_product->get_permalink(),
			'collection' => __( 'Love Hurts Collection', 'skyyrose-flagship' ),
			'sizes'      => '',
			'left'       => (string) $pos[0],
			'top'        => (string) $pos[1],
			'prop'       => 'cathedral-display',
			'prop_label' => __( 'Cathedral display', 'skyyrose-flagship' ),
		);
	}
} else {
	// Fallback hardcoded products when WooCommerce is inactive.
	$fallback = array(
		array( 'name' => 'Enchanted Rose Hoodie',  'price' => '$195', 'room' => 0 ),
		array( 'name' => 'Beast Mode Tee',         'price' => '$85',  'room' => 0 ),
		array( 'name' => 'Thorned Heart Jacket',   'price' => '$345', 'room' => 0 ),
		array( 'name' => 'Bloodline Crewneck',     'price' => '$145', 'room' => 1 ),
		array( 'name' => 'Glass Dome Varsity',     'price' => '$295', 'room' => 1 ),
		array( 'name' => 'Last Petal Joggers',     'price' => '$135', 'room' => 1 ),
	);

	foreach ( $fallback as $fb ) {
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
			'collection' => __( 'Love Hurts Collection', 'skyyrose-flagship' ),
			'sizes'      => '',
			'left'       => (string) $pos[0],
			'top'        => (string) $pos[1],
			'prop'       => 'cathedral-display',
			'prop_label' => __( 'Cathedral display', 'skyyrose-flagship' ),
		);
	}
}

/* ─────────────────────────────────────────────────────────
   Room Config — 2 rooms using AI scene images.
   ───────────────────────────────────────────────────────── */

$rooms = array(
	array(
		'name'     => esc_html__( 'The Bedroom', 'skyyrose-flagship' ),
		'image'    => 'scene-love-hurts-bedroom.webp',
		'products' => $products_per_room[0],
	),
	array(
		'name'     => esc_html__( 'The Glass Dome', 'skyyrose-flagship' ),
		'image'    => 'scene-love-hurts-dome.webp',
		'products' => $products_per_room[1],
	),
);

get_header();
?>

<main id="primary" class="site-main immersive-page" role="main" tabindex="-1">
	<?php
	get_template_part( 'template-parts/immersive-scene', null, array(
		'collection_slug' => 'love-hurts',
		'collection_name' => __( 'Love Hurts Collection', 'skyyrose-flagship' ),
		'world_name'      => __( 'The Cathedral', 'skyyrose-flagship' ),
		'tagline'         => __( 'Every petal tells a story.', 'skyyrose-flagship' ),
		'accent_color'    => '#DC143C',
		'collection_url'  => home_url( '/collection-love-hurts/' ),
		'rooms'           => $rooms,
	) );
	?>
</main>

<?php
get_footer();
