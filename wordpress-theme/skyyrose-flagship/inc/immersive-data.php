<?php
/**
 * Immersive Page Data — per-collection room + hotspot data.
 *
 * Single source of truth for the immersive world templates. Consumed by the
 * 4 thin template-immersive-{slug}.php stubs which delegate rendering to
 * template-parts/immersive-scene.php.
 *
 * Adding a new immersive world:
 *   1. Add an entry to skyyrose_immersive_data() keyed by collection slug
 *   2. Create template-immersive-{slug}.php as a 17-line stub
 *   3. Set the page's "Page Attributes > Template" in WP admin
 *
 * Hotspot product structure (per room):
 *   'sku'        — catalog SKU (looked up via skyyrose_immersive_product)
 *   'left', 'top' — hotspot percentages on the scene image
 *   'prop'       — prop key for analytics / class hooks
 *   'prop_label' — accessible label, run through __() at render time
 *
 * @package SkyyRose
 * @since   7.1.0
 */

defined( 'ABSPATH' ) || exit;

/**
 * Per-collection immersive world content.
 *
 * @since 7.1.0
 * @return array<string, array<string, mixed>>
 */
function skyyrose_immersive_data() {
	return array(
		'black-rose'   => array(
			'collection_name'     => __( 'Black Rose Collection', 'skyyrose' ),
			'world_name'          => __( 'The Bay Bridge', 'skyyrose' ),
			'tagline'             => __( 'Luxury Grows from Concrete.', 'skyyrose' ),
			'accent_color'        => '#C0C0C0',
			'collection_url_path' => 'collection-black-rose',
			'rooms'               => array(
				array(
					'name'     => __( 'Moonlit Courtyard', 'skyyrose' ),
					'image'    => 'scene-black-rose-courtyard.webp',
					'products' => array(
						array( 'sku' => 'br-006', 'left' => '15', 'top' => '42', 'prop' => 'marble-statue',     'prop_label' => 'Draped over marble garden statue' ),
						array( 'sku' => 'br-005', 'left' => '38', 'top' => '50', 'prop' => 'fountain-edge',     'prop_label' => 'Folded on fountain edge' ),
						array( 'sku' => 'br-002', 'left' => '62', 'top' => '55', 'prop' => 'topiary-base',      'prop_label' => 'Folded at base of rose topiary' ),
						array( 'sku' => 'br-007', 'left' => '82', 'top' => '48', 'prop' => 'statue-pedestal',   'prop_label' => 'Draped over statue pedestal' ),
					),
				),
				array(
					'name'     => __( 'Iron Gazebo', 'skyyrose' ),
					'image'    => 'scene-black-rose-gazebo.webp',
					'products' => array(
						array( 'sku' => 'br-004', 'left' => '30', 'top' => '40', 'prop' => 'iron-gazebo',       'prop_label' => 'Displayed inside iron gazebo' ),
						array( 'sku' => 'br-001', 'left' => '55', 'top' => '35', 'prop' => 'hedge-arch',        'prop_label' => 'Hanging from rose hedge archway' ),
						array( 'sku' => 'br-003', 'left' => '72', 'top' => '50', 'prop' => 'cobblestone-bench', 'prop_label' => 'Draped over cobblestone garden bench' ),
					),
				),
			),
		),
		'love-hurts'   => array(
			'collection_name'     => __( 'Love Hurts Collection', 'skyyrose' ),
			'world_name'          => __( 'The Cathedral', 'skyyrose' ),
			'tagline'             => __( 'Every petal tells a story.', 'skyyrose' ),
			'accent_color'        => '#DC143C',
			'collection_url_path' => 'collection-love-hurts',
			'rooms'               => array(
				array(
					'name'     => __( 'The Cathedral', 'skyyrose' ),
					'image'    => 'scene-love-hurts-cathedral.webp',
					'products' => array(
						array( 'sku' => 'lh-004', 'left' => '32', 'top' => '50', 'prop' => 'mannequin',  'prop_label' => 'On the mannequin stand' ),
						array( 'sku' => 'lh-003', 'left' => '67', 'top' => '35', 'prop' => 'float',      'prop_label' => 'Suspended above the pews' ),
						array( 'sku' => 'lh-002', 'left' => '72', 'top' => '62', 'prop' => 'pew',        'prop_label' => 'Draped across the pew' ),
						array( 'sku' => 'lh-006', 'left' => '83', 'top' => '50', 'prop' => 'candelabra', 'prop_label' => 'Hanging from the candelabra' ),
					),
				),
			),
		),
		'signature'    => array(
			'collection_name'     => __( 'Signature Collection', 'skyyrose' ),
			'world_name'          => __( 'The Golden Gate Runway', 'skyyrose' ),
			'tagline'             => __( 'The Origin. The Crown.', 'skyyrose' ),
			'accent_color'        => '#D4AF37',
			'collection_url_path' => 'collection-signature',
			'rooms'               => array(
				array(
					'name'     => __( 'The Golden Gate', 'skyyrose' ),
					'image'    => 'scene-signature-golden-gate.webp',
					'products' => array(
						array( 'sku' => 'sg-009', 'left' => '15', 'top' => '42', 'prop' => 'glass-orb',          'prop_label' => 'Inside glass orb display case' ),
						array( 'sku' => 'sg-002', 'left' => '42', 'top' => '35', 'prop' => 'gold-display-frame', 'prop_label' => 'Hanging in gold-lit LED display frame' ),
						array( 'sku' => 'sg-003', 'left' => '50', 'top' => '38', 'prop' => 'gold-display-frame', 'prop_label' => 'Hanging in gold-lit LED display frame' ),
						array( 'sku' => 'sg-006', 'left' => '62', 'top' => '36', 'prop' => 'gold-display-frame', 'prop_label' => 'Hanging in gold-lit LED display frame' ),
						array( 'sku' => 'sg-001', 'left' => '78', 'top' => '50', 'prop' => 'marble-pedestal',    'prop_label' => 'Featured on stepped marble pedestal' ),
					),
				),
				array(
					'name'     => __( 'The Bay Bridge', 'skyyrose' ),
					'image'    => 'scene-signature-bay-bridge.webp',
					'products' => array(
						array( 'sku' => 'sg-011', 'left' => '18', 'top' => '38', 'prop' => 'clothing-rack',        'prop_label' => 'Hanging on left wall clothing rack' ),
						array( 'sku' => 'sg-005', 'left' => '50', 'top' => '52', 'prop' => 'marble-display-table', 'prop_label' => 'Featured on center marble display table' ),
						array( 'sku' => 'sg-007', 'left' => '32', 'top' => '48', 'prop' => 'marble-pedestal',      'prop_label' => 'On left marble pedestal' ),
						array( 'sku' => 'sg-015', 'left' => '72', 'top' => '38', 'prop' => 'clothing-rack',        'prop_label' => 'Hanging on right wall clothing rack' ),
					),
				),
			),
		),
		'kids-capsule' => array(
			'collection_name'     => __( 'Kids Capsule Collection', 'skyyrose' ),
			'world_name'          => __( 'The Playroom', 'skyyrose' ),
			'tagline'             => __( 'Luxury runs in the family.', 'skyyrose' ),
			'accent_color'        => '#B76E79',
			'collection_url_path' => 'collection-kids-capsule',
			'rooms'               => array(
				array(
					'name'     => __( 'The Playroom', 'skyyrose' ),
					'image'    => 'scene-kids-capsule-playroom.webp',
					'products' => array(
						array( 'sku' => 'kids-001', 'left' => '50', 'top' => '38', 'prop' => 'playroom-display', 'prop_label' => 'Featured on center playroom display' ),
					),
				),
				array(
					'name'     => __( 'The Runway', 'skyyrose' ),
					'image'    => 'scene-kids-capsule-runway.webp',
					'products' => array(
						array( 'sku' => 'kids-002', 'left' => '50', 'top' => '38', 'prop' => 'playroom-display', 'prop_label' => 'Featured on center runway display' ),
					),
				),
			),
		),
	);
}

/**
 * Build the full $args array for template-parts/immersive-scene given a slug.
 *
 * Performs the catalog lookup for each hotspot product and returns the args
 * shape that immersive-scene.php expects.
 *
 * @since 7.1.0
 * @param string $slug Collection slug (e.g., 'black-rose').
 * @return array<string, mixed>|null Args ready for get_template_part(), or null on unknown slug.
 */
function skyyrose_get_immersive_args( $slug ) {
	$all = skyyrose_immersive_data();
	if ( empty( $all[ $slug ] ) ) {
		return null;
	}

	$config = $all[ $slug ];
	$rooms  = array();

	foreach ( ( $config['rooms'] ?? array() ) as $room ) {
		$products = array();
		foreach ( ( $room['products'] ?? array() ) as $hotspot ) {
			if ( empty( $hotspot['sku'] ) ) {
				continue;
			}
			$resolved = skyyrose_immersive_product(
				$hotspot['sku'],
				array(
					'left'       => $hotspot['left'] ?? '50',
					'top'        => $hotspot['top'] ?? '50',
					'prop'       => $hotspot['prop'] ?? 'display',
					'prop_label' => __( $hotspot['prop_label'] ?? '', 'skyyrose' ), // phpcs:ignore WordPress.WP.I18n.NonSingularStringLiteralText
				)
			);
			if ( $resolved ) {
				$products[] = $resolved;
			}
		}
		// Only emit rooms that ended up with at least one published product.
		if ( ! empty( $products ) ) {
			$rooms[] = array(
				'name'     => $room['name'] ?? '',
				'image'    => $room['image'] ?? '',
				'products' => $products,
			);
		}
	}

	return array(
		'collection_slug' => $slug,
		'collection_name' => $config['collection_name'] ?? '',
		'world_name'      => $config['world_name'] ?? '',
		'tagline'         => $config['tagline'] ?? '',
		'accent_color'    => $config['accent_color'] ?? '#B76E79',
		'collection_url'  => home_url( '/' . ltrim( $config['collection_url_path'] ?? '', '/' ) . '/' ),
		'rooms'           => $rooms,
	);
}
