<?php
/**
 * Template Name: Immersive - Signature
 *
 * "The Runway" — Multi-room experience with 2 scenes:
 * Room 1: Waterfront Runway — Bay Bridge at night, black marble platform,
 *         gold-lit LED display frames, glass orb case, marble pedestals.
 * Room 2: Golden Gate Showroom — Sunset panoramic windows, black marble
 *         interior, clothing racks, marble pedestals, center display table.
 *
 * Arrow/swipe navigation between rooms with 0.6s crossfade.
 * drakerelated.com-style immersive experience with hotspot beacons.
 *
 * @package SkyyRose_Flagship
 * @since 2.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Multi-room scene data with hotspot products per room.
 * Products placed on props visible in the actual scene images:
 * glass orbs, marble pedestals, gold-lit display frames, clothing racks,
 * display tables — not floating in air.
 *
 * Scene images:
 * - signature-waterfront-runway.png (Bay Bridge waterfront at night)
 * - signature-golden-gate-showroom.png (Golden Gate sunset showroom)
 */
$signature_rooms = array(
	// Room 1 — Waterfront Runway
	array(
		'name'     => esc_html__( 'Waterfront Runway', 'skyyrose-flagship' ),
		'image'    => get_template_directory_uri() . '/assets/scenes/signature/signature-waterfront-runway.png',
		'alt'      => esc_attr__( 'Bay Bridge waterfront at night with black marble platform floating over water, gold-lit LED display frames with hanging garments, glass orb display case, and stepped marble pedestals', 'skyyrose-flagship' ),
		'products' => array(
			// Glass orb display case (left) — beanies
			array(
				'id'         => 'sg-009',
				'name'       => esc_html__( 'Red Rose Beanie', 'skyyrose-flagship' ),
				'price'      => '$45',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'One Size',
				'image'      => get_template_directory_uri() . '/assets/images/products/sg-009-red-rose-beanie.jpg',
				'url'        => '/?product_id=sg-009',
				'left'       => '15',
				'top'        => '42',
				'prop'       => 'glass-orb',
				'prop_label' => esc_html__( 'Inside glass orb display case', 'skyyrose-flagship' ),
			),
			array(
				'id'         => 'sg-010',
				'name'       => esc_html__( 'Lavender Rose Beanie', 'skyyrose-flagship' ),
				'price'      => '$45',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'One Size',
				'image'      => get_template_directory_uri() . '/assets/images/products/sg-010-lavender-beanie.jpg',
				'url'        => '/?product_id=sg-010',
				'left'       => '20',
				'top'        => '48',
				'prop'       => 'glass-orb',
				'prop_label' => esc_html__( 'Inside glass orb display case', 'skyyrose-flagship' ),
			),
			// Stepped marble pedestals (left row)
			array(
				'id'         => 'sg-006',
				'name'       => esc_html__( 'Cotton Candy Tee', 'skyyrose-flagship' ),
				'price'      => '$65',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'XS,S,M,L,XL,2XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/sg-006-cotton-candy-tee.jpg',
				'url'        => '/?product_id=sg-006',
				'left'       => '28',
				'top'        => '55',
				'prop'       => 'marble-pedestal',
				'prop_label' => esc_html__( 'Folded on stepped marble pedestal', 'skyyrose-flagship' ),
			),
			array(
				'id'         => 'sg-007',
				'name'       => esc_html__( 'Cotton Candy Shorts', 'skyyrose-flagship' ),
				'price'      => '$55',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'S,M,L,XL,2XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/sg-007-cotton-candy-shorts.jpg',
				'url'        => '/?product_id=sg-007',
				'left'       => '32',
				'top'        => '62',
				'prop'       => 'marble-pedestal',
				'prop_label' => esc_html__( 'Stacked on stepped marble pedestal', 'skyyrose-flagship' ),
			),
			// Gold-lit display frames (center)
			array(
				'id'         => 'sg-002',
				'name'       => esc_html__( 'Stay Golden Tee', 'skyyrose-flagship' ),
				'price'      => '$65',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'XS,S,M,L,XL,2XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/sg-002-stay-golden-tee.jpg',
				'url'        => '/?product_id=sg-002',
				'left'       => '42',
				'top'        => '35',
				'prop'       => 'gold-display-frame',
				'prop_label' => esc_html__( 'Hanging in gold-lit LED display frame', 'skyyrose-flagship' ),
			),
			array(
				'id'         => 'sg-004',
				'name'       => esc_html__( 'Signature Hoodie', 'skyyrose-flagship' ),
				'price'      => '$145',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'S,M,L,XL,2XL,3XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/sg-004-signature-hoodie.jpg',
				'url'        => '/?product_id=sg-004',
				'left'       => '50',
				'top'        => '38',
				'prop'       => 'gold-display-frame',
				'prop_label' => esc_html__( 'Hanging in gold-lit LED display frame', 'skyyrose-flagship' ),
			),
			// Gold-lit display frame (right)
			array(
				'id'         => 'sg-008',
				'name'       => esc_html__( 'Crop Hoodie', 'skyyrose-flagship' ),
				'price'      => '$125',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'XS,S,M,L,XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/sg-008-crop-hoodie.jpg',
				'url'        => '/?product_id=sg-008',
				'left'       => '62',
				'top'        => '36',
				'prop'       => 'gold-display-frame',
				'prop_label' => esc_html__( 'Hanging in gold-lit LED display frame', 'skyyrose-flagship' ),
			),
			// Stepped marble pedestals (right row)
			array(
				'id'         => 'sg-005',
				'name'       => esc_html__( 'Signature Shorts', 'skyyrose-flagship' ),
				'price'      => '$55',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'S,M,L,XL,2XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/sg-005-signature-shorts.jpg',
				'url'        => '/?product_id=sg-005',
				'left'       => '70',
				'top'        => '55',
				'prop'       => 'marble-pedestal',
				'prop_label' => esc_html__( 'Displayed on stepped marble pedestal', 'skyyrose-flagship' ),
			),
			array(
				'id'         => 'sg-001',
				'name'       => esc_html__( 'The Bay Set', 'skyyrose-flagship' ),
				'price'      => '$225',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'S,M,L,XL,2XL,3XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/sg-001-bay-set.jpg',
				'url'        => '/?product_id=sg-001',
				'left'       => '75',
				'top'        => '60',
				'prop'       => 'marble-pedestal',
				'prop_label' => esc_html__( 'Featured on stepped marble pedestal', 'skyyrose-flagship' ),
			),
			// Marble platform edge displays
			array(
				'id'         => 'sg-011',
				'name'       => esc_html__( 'Original Label Tee (White)', 'skyyrose-flagship' ),
				'price'      => '$55',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'XS,S,M,L,XL,2XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/sg-011-label-tee-white.jpg',
				'url'        => '/?product_id=sg-011',
				'left'       => '38',
				'top'        => '72',
				'prop'       => 'marble-platform-edge',
				'prop_label' => esc_html__( 'On marble platform edge display', 'skyyrose-flagship' ),
			),
			array(
				'id'         => 'sg-012',
				'name'       => esc_html__( 'Original Label Tee (Orchid)', 'skyyrose-flagship' ),
				'price'      => '$55',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'XS,S,M,L,XL,2XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/sg-012-label-tee-orchid.jpg',
				'url'        => '/?product_id=sg-012',
				'left'       => '58',
				'top'        => '72',
				'prop'       => 'marble-platform-edge',
				'prop_label' => esc_html__( 'On marble platform edge display', 'skyyrose-flagship' ),
			),
		),
	),
	// Room 2 — Golden Gate Showroom
	array(
		'name'     => esc_html__( 'Golden Gate Showroom', 'skyyrose-flagship' ),
		'image'    => get_template_directory_uri() . '/assets/scenes/signature/signature-golden-gate-showroom.png',
		'alt'      => esc_attr__( 'Golden Gate Bridge sunset showroom with floor-to-ceiling panoramic windows, black marble interior with gold LED trim, clothing racks, marble pedestals, and dramatic sunset sky', 'skyyrose-flagship' ),
		'products' => array(
			// Left wall clothing rack
			array(
				'id'         => 'sg-004',
				'name'       => esc_html__( 'Signature Hoodie', 'skyyrose-flagship' ),
				'price'      => '$145',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'S,M,L,XL,2XL,3XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/sg-004-signature-hoodie.jpg',
				'url'        => '/?product_id=sg-004',
				'left'       => '15',
				'top'        => '35',
				'prop'       => 'clothing-rack',
				'prop_label' => esc_html__( 'Hanging on left wall clothing rack', 'skyyrose-flagship' ),
			),
			array(
				'id'         => 'sg-003',
				'name'       => esc_html__( 'Pink Smoke Crewneck', 'skyyrose-flagship' ),
				'price'      => '$95',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'S,M,L,XL,2XL,3XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/sg-003-pink-smoke-crewneck.jpg',
				'url'        => '/?product_id=sg-003',
				'left'       => '22',
				'top'        => '40',
				'prop'       => 'clothing-rack',
				'prop_label' => esc_html__( 'Hanging on left wall clothing rack', 'skyyrose-flagship' ),
			),
			// Right wall clothing rack
			array(
				'id'         => 'sg-008',
				'name'       => esc_html__( 'Crop Hoodie', 'skyyrose-flagship' ),
				'price'      => '$125',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'XS,S,M,L,XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/sg-008-crop-hoodie.jpg',
				'url'        => '/?product_id=sg-008',
				'left'       => '78',
				'top'        => '35',
				'prop'       => 'clothing-rack',
				'prop_label' => esc_html__( 'Hanging on right wall clothing rack', 'skyyrose-flagship' ),
			),
			array(
				'id'         => 'sg-002',
				'name'       => esc_html__( 'Stay Golden Tee', 'skyyrose-flagship' ),
				'price'      => '$65',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'XS,S,M,L,XL,2XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/sg-002-stay-golden-tee.jpg',
				'url'        => '/?product_id=sg-002',
				'left'       => '85',
				'top'        => '40',
				'prop'       => 'clothing-rack',
				'prop_label' => esc_html__( 'Hanging on right wall clothing rack', 'skyyrose-flagship' ),
			),
			// Center marble display table — featured
			array(
				'id'         => 'sg-001',
				'name'       => esc_html__( 'The Bay Set', 'skyyrose-flagship' ),
				'price'      => '$225',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'S,M,L,XL,2XL,3XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/sg-001-bay-set.jpg',
				'url'        => '/?product_id=sg-001',
				'left'       => '50',
				'top'        => '52',
				'prop'       => 'marble-display-table',
				'prop_label' => esc_html__( 'Featured on center marble display table', 'skyyrose-flagship' ),
			),
			// Left marble pedestal — beanie
			array(
				'id'         => 'sg-009',
				'name'       => esc_html__( 'Red Rose Beanie', 'skyyrose-flagship' ),
				'price'      => '$45',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'One Size',
				'image'      => get_template_directory_uri() . '/assets/images/products/sg-009-red-rose-beanie.jpg',
				'url'        => '/?product_id=sg-009',
				'left'       => '32',
				'top'        => '48',
				'prop'       => 'marble-pedestal',
				'prop_label' => esc_html__( 'On left marble pedestal', 'skyyrose-flagship' ),
			),
			// Right marble pedestal — beanie
			array(
				'id'         => 'sg-010',
				'name'       => esc_html__( 'Lavender Rose Beanie', 'skyyrose-flagship' ),
				'price'      => '$45',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'One Size',
				'image'      => get_template_directory_uri() . '/assets/images/products/sg-010-lavender-beanie.jpg',
				'url'        => '/?product_id=sg-010',
				'left'       => '68',
				'top'        => '48',
				'prop'       => 'marble-pedestal',
				'prop_label' => esc_html__( 'On right marble pedestal', 'skyyrose-flagship' ),
			),
			// Left wall shelf (lower)
			array(
				'id'         => 'sg-005',
				'name'       => esc_html__( 'Signature Shorts', 'skyyrose-flagship' ),
				'price'      => '$55',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'S,M,L,XL,2XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/sg-005-signature-shorts.jpg',
				'url'        => '/?product_id=sg-005',
				'left'       => '18',
				'top'        => '58',
				'prop'       => 'wall-shelf',
				'prop_label' => esc_html__( 'Folded on left wall shelf', 'skyyrose-flagship' ),
			),
			array(
				'id'         => 'sg-006',
				'name'       => esc_html__( 'Cotton Candy Tee', 'skyyrose-flagship' ),
				'price'      => '$65',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'XS,S,M,L,XL,2XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/sg-006-cotton-candy-tee.jpg',
				'url'        => '/?product_id=sg-006',
				'left'       => '25',
				'top'        => '62',
				'prop'       => 'wall-shelf',
				'prop_label' => esc_html__( 'Folded on left wall shelf', 'skyyrose-flagship' ),
			),
			// Right wall display
			array(
				'id'         => 'sg-007',
				'name'       => esc_html__( 'Cotton Candy Shorts', 'skyyrose-flagship' ),
				'price'      => '$55',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'S,M,L,XL,2XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/sg-007-cotton-candy-shorts.jpg',
				'url'        => '/?product_id=sg-007',
				'left'       => '75',
				'top'        => '58',
				'prop'       => 'wall-display',
				'prop_label' => esc_html__( 'On right wall display', 'skyyrose-flagship' ),
			),
			array(
				'id'         => 'sg-011',
				'name'       => esc_html__( 'Original Label Tee (White)', 'skyyrose-flagship' ),
				'price'      => '$55',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'XS,S,M,L,XL,2XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/sg-011-label-tee-white.jpg',
				'url'        => '/?product_id=sg-011',
				'left'       => '82',
				'top'        => '58',
				'prop'       => 'wall-display',
				'prop_label' => esc_html__( 'On right wall display', 'skyyrose-flagship' ),
			),
			array(
				'id'         => 'sg-012',
				'name'       => esc_html__( 'Original Label Tee (Orchid)', 'skyyrose-flagship' ),
				'price'      => '$55',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'XS,S,M,L,XL,2XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/sg-012-label-tee-orchid.jpg',
				'url'        => '/?product_id=sg-012',
				'left'       => '88',
				'top'        => '62',
				'prop'       => 'wall-display',
				'prop_label' => esc_html__( 'On right wall display', 'skyyrose-flagship' ),
			),
		),
	),
);

get_header();
?>

<main id="primary" class="site-main immersive-page">

	<div class="immersive-scene immersive-signature" role="region" aria-label="<?php esc_attr_e( 'Signature Collection — The Runway', 'skyyrose-flagship' ); ?>">

		<!-- Loading Screen -->
		<div class="scene-loading" aria-hidden="true">
			<div class="scene-loading-monogram"><?php echo esc_html__( 'SR', 'skyyrose-flagship' ); ?></div>
			<div class="scene-loading-text"><?php echo esc_html__( 'Entering The Runway', 'skyyrose-flagship' ); ?></div>
		</div>

		<!-- Scene Viewport -->
		<div class="scene-viewport">
			<?php foreach ( $signature_rooms as $index => $room ) : ?>
				<div
					class="scene-layer<?php echo 0 === $index ? ' active' : ''; ?>"
					data-room-name="<?php echo esc_attr( $room['name'] ); ?>"
				>
					<img
						src="<?php echo esc_url( $room['image'] ); ?>"
						alt="<?php echo esc_attr( $room['alt'] ); ?>"
						loading="<?php echo 0 === $index ? 'eager' : 'lazy'; ?>"
						<?php if ( 0 === $index ) : ?>fetchpriority="high"<?php endif; ?>
					>
				</div>
			<?php endforeach; ?>
		</div>

		<!-- Vignette -->
		<div class="scene-vignette"></div>

		<!-- Film Grain -->
		<div class="scene-film-grain" aria-hidden="true"></div>

		<!-- Room Navigation Arrows -->
		<div class="room-nav room-nav-prev">
			<button class="room-nav-btn" type="button" aria-label="<?php esc_attr_e( 'Previous room', 'skyyrose-flagship' ); ?>">
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
			</button>
		</div>
		<div class="room-nav room-nav-next">
			<button class="room-nav-btn" type="button" aria-label="<?php esc_attr_e( 'Next room', 'skyyrose-flagship' ); ?>">
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
			</button>
		</div>

		<!-- Room Indicators -->
		<div class="room-indicators" role="group" aria-label="<?php esc_attr_e( 'Room selector', 'skyyrose-flagship' ); ?>">
			<?php foreach ( $signature_rooms as $index => $room ) : ?>
				<button
					class="room-dot<?php echo 0 === $index ? ' active' : ''; ?>"
					type="button"
					aria-label="<?php echo esc_attr( $room['name'] ); ?>"
				></button>
			<?php endforeach; ?>
		</div>
		<div class="room-name"><?php echo esc_html( $signature_rooms[0]['name'] ); ?></div>

		<!-- Hotspot Containers — Products placed on contextual props -->
		<?php foreach ( $signature_rooms as $room_index => $room ) : ?>
			<div class="hotspot-container" <?php echo 0 !== $room_index ? 'style="display:none;"' : ''; ?>>
				<?php foreach ( $room['products'] as $product ) : ?>
					<a
						href="<?php echo esc_url( $product['url'] ); ?>"
						class="hotspot hotspot--prop-<?php echo esc_attr( $product['prop'] ); ?>"
						style="left: <?php echo esc_attr( $product['left'] ); ?>%; top: <?php echo esc_attr( $product['top'] ); ?>%;"
						data-product-id="<?php echo esc_attr( $product['id'] ); ?>"
						data-product-name="<?php echo esc_attr( $product['name'] ); ?>"
						data-product-price="<?php echo esc_attr( $product['price'] ); ?>"
						data-product-image="<?php echo esc_url( $product['image'] ); ?>"
						data-product-collection="<?php echo esc_attr( $product['collection'] ); ?>"
						data-product-sizes="<?php echo esc_attr( $product['sizes'] ); ?>"
						data-product-url="<?php echo esc_url( $product['url'] ); ?>"
						data-prop="<?php echo esc_attr( $product['prop'] ); ?>"
						data-prop-label="<?php echo esc_attr( $product['prop_label'] ); ?>"
						aria-label="<?php echo esc_attr( $product['name'] . ' — ' . $product['price'] . ' — ' . $product['prop_label'] ); ?>"
					>
						<span class="hotspot-beacon"></span>
						<span class="hotspot-label">
							<span class="hotspot-label-name"><?php echo esc_html( $product['name'] ); ?></span>
							<span class="hotspot-label-prop"><?php echo esc_html( $product['prop_label'] ); ?></span>
						</span>
					</a>
				<?php endforeach; ?>
			</div>
		<?php endforeach; ?>

		<!-- Scene Title -->
		<div class="scene-title-overlay">
			<h1><?php echo esc_html__( 'The Runway', 'skyyrose-flagship' ); ?></h1>
			<p class="scene-subtitle"><?php echo esc_html__( 'Signature Collection', 'skyyrose-flagship' ); ?></p>
		</div>

	</div><!-- .immersive-scene -->

	<!-- Product Detail Panel (Glassmorphism Slide-Up) -->
	<div class="product-panel-overlay" aria-hidden="true"></div>
	<aside class="product-panel" role="dialog" aria-modal="true" aria-label="<?php esc_attr_e( 'Product Details', 'skyyrose-flagship' ); ?>">
		<button class="product-panel-close" type="button" aria-label="<?php esc_attr_e( 'Close product details', 'skyyrose-flagship' ); ?>">&times;</button>
		<div class="product-panel-inner">
			<div class="product-panel-thumb">
				<img src="<?php echo esc_url( get_template_directory_uri() . '/assets/images/placeholder.jpg' ); ?>" alt="">
			</div>
			<div class="product-panel-info">
				<p class="product-panel-collection"></p>
				<h3 class="product-panel-name"></h3>
				<p class="product-panel-prop"></p>
				<p class="product-panel-price"></p>
				<div class="product-panel-sizes" role="group" aria-label="<?php esc_attr_e( 'Available sizes', 'skyyrose-flagship' ); ?>"></div>
				<div class="product-panel-actions">
					<button class="btn-add-to-cart" type="button"><?php echo esc_html__( 'Pre-Order Now', 'skyyrose-flagship' ); ?></button>
					<a class="btn-view-details" href="#"><?php echo esc_html__( 'View Details', 'skyyrose-flagship' ); ?></a>
				</div>
			</div>
		</div>
	</aside>

	<!-- Collection Tab Bar -->
	<nav class="immersive-tab-bar" aria-label="<?php esc_attr_e( 'Collection navigation', 'skyyrose-flagship' ); ?>">
		<a href="<?php echo esc_url( home_url( '/experience-black-rose/' ) ); ?>" class="immersive-tab" style="--tab-accent: #C0C0C0;">
			<?php echo esc_html__( 'Black Rose', 'skyyrose-flagship' ); ?>
		</a>
		<a href="<?php echo esc_url( home_url( '/experience-love-hurts/' ) ); ?>" class="immersive-tab" style="--tab-accent: #DC143C;">
			<?php echo esc_html__( 'Love Hurts', 'skyyrose-flagship' ); ?>
		</a>
		<a href="<?php echo esc_url( home_url( '/experience-signature/' ) ); ?>" class="immersive-tab active" aria-current="page" style="--tab-accent: #B76E79;">
			<?php echo esc_html__( 'Signature', 'skyyrose-flagship' ); ?>
		</a>
		<a href="<?php echo esc_url( home_url( '/preorder/' ) ); ?>" class="immersive-tab" style="--tab-accent: #D4AF37;">
			<?php echo esc_html__( 'Pre-Order', 'skyyrose-flagship' ); ?>
		</a>
	</nav>

	<?php get_template_part( 'template-parts/cinematic-toggle' ); ?>

	<!-- Conversion Intelligence: Urgency Countdown -->
	<div style="position:absolute; bottom:56px; right:16px; z-index:12;">
		<div data-cie-countdown="auto" data-cie-countdown-label="Pre-Order Closes"></div>
	</div>

</main><!-- #primary -->

<?php
get_footer();
