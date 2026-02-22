<?php
/**
 * Template Name: Immersive - Signature
 *
 * "The Runway" — Multi-room experience with 3 scenes:
 * Room 1: Bay Bridge glass venue with garment racks (5 products)
 * Room 2: Grand showroom hall with display cases (5 products)
 * Room 3: Intimate fitting room with mirrors (4 beanies on stands)
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
 */
$signature_rooms = array(
	// Room 1 — The Runway
	array(
		'name'     => esc_html__( 'The Runway', 'skyyrose-flagship' ),
		'image'    => get_template_directory_uri() . '/assets/images/scenes/signature-runway.jpg',
		'alt'      => esc_attr__( 'Glass venue overlooking the Bay Bridge at dusk, garment racks lining both sides of a luminous runway', 'skyyrose-flagship' ),
		'products' => array(
			array(
				'id'         => 'sg-001',
				'name'       => esc_html__( 'Rose Gold Statement Necklace', 'skyyrose-flagship' ),
				'price'      => '$2,499',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => '16in,18in,20in',
				'image'      => get_template_directory_uri() . '/assets/images/scenes/signature-product-1.jpg',
				'url'        => '#',
				'left'       => '18',
				'top'        => '32',
			),
			array(
				'id'         => 'sg-002',
				'name'       => esc_html__( 'Bridge View Cuff', 'skyyrose-flagship' ),
				'price'      => '$1,899',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'S,M,L',
				'image'      => get_template_directory_uri() . '/assets/images/scenes/signature-product-2.jpg',
				'url'        => '#',
				'left'       => '38',
				'top'        => '48',
			),
			array(
				'id'         => 'sg-003',
				'name'       => esc_html__( 'Golden Hour Earrings', 'skyyrose-flagship' ),
				'price'      => '$1,299',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'OS',
				'image'      => get_template_directory_uri() . '/assets/images/scenes/signature-product-3.jpg',
				'url'        => '#',
				'left'       => '62',
				'top'        => '36',
			),
			array(
				'id'         => 'sg-004',
				'name'       => esc_html__( 'Skyline Ring', 'skyyrose-flagship' ),
				'price'      => '$1,699',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => '5,6,7,8,9',
				'image'      => get_template_directory_uri() . '/assets/images/scenes/signature-product-4.jpg',
				'url'        => '#',
				'left'       => '80',
				'top'        => '55',
			),
			array(
				'id'         => 'sg-005',
				'name'       => esc_html__( 'Dusk Pendant', 'skyyrose-flagship' ),
				'price'      => '$1,999',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => '16in,18in,20in,22in',
				'image'      => get_template_directory_uri() . '/assets/images/scenes/signature-product-5.jpg',
				'url'        => '#',
				'left'       => '50',
				'top'        => '68',
			),
		),
	),
	// Room 2 — The Showroom
	array(
		'name'     => esc_html__( 'The Showroom', 'skyyrose-flagship' ),
		'image'    => get_template_directory_uri() . '/assets/images/scenes/signature-showroom.jpg',
		'alt'      => esc_attr__( 'Grand exhibition hall with illuminated glass display cases, marble columns, and ambient rose-gold lighting', 'skyyrose-flagship' ),
		'products' => array(
			array(
				'id'         => 'sg-006',
				'name'       => esc_html__( 'Heritage Chain', 'skyyrose-flagship' ),
				'price'      => '$2,799',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => '18in,20in,22in',
				'image'      => get_template_directory_uri() . '/assets/images/scenes/signature-product-6.jpg',
				'url'        => '#',
				'left'       => '25',
				'top'        => '40',
			),
			array(
				'id'         => 'sg-007',
				'name'       => esc_html__( 'Gallery Bangle Set', 'skyyrose-flagship' ),
				'price'      => '$1,499',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'S,M,L',
				'image'      => get_template_directory_uri() . '/assets/images/scenes/signature-product-7.jpg',
				'url'        => '#',
				'left'       => '45',
				'top'        => '52',
			),
			array(
				'id'         => 'sg-008',
				'name'       => esc_html__( 'Exhibition Brooch', 'skyyrose-flagship' ),
				'price'      => '$899',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'OS',
				'image'      => get_template_directory_uri() . '/assets/images/scenes/signature-product-8.jpg',
				'url'        => '#',
				'left'       => '68',
				'top'        => '38',
			),
			array(
				'id'         => 'sg-009',
				'name'       => esc_html__( 'Marble Column Studs', 'skyyrose-flagship' ),
				'price'      => '$699',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'OS',
				'image'      => get_template_directory_uri() . '/assets/images/scenes/signature-product-9.jpg',
				'url'        => '#',
				'left'       => '35',
				'top'        => '28',
			),
			array(
				'id'         => 'sg-010',
				'name'       => esc_html__( 'Vault Ring', 'skyyrose-flagship' ),
				'price'      => '$2,199',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => '5,6,7,8,9,10',
				'image'      => get_template_directory_uri() . '/assets/images/scenes/signature-product-10.jpg',
				'url'        => '#',
				'left'       => '78',
				'top'        => '60',
			),
		),
	),
	// Room 3 — The Fitting Room
	array(
		'name'     => esc_html__( 'The Fitting Room', 'skyyrose-flagship' ),
		'image'    => get_template_directory_uri() . '/assets/images/scenes/signature-fitting-room.jpg',
		'alt'      => esc_attr__( 'Intimate dressing area with floor-to-ceiling mirrors, warm lighting, and beanie stands on a velvet display table', 'skyyrose-flagship' ),
		'products' => array(
			array(
				'id'         => 'sg-011',
				'name'       => esc_html__( 'Rose Gold Signature Beanie', 'skyyrose-flagship' ),
				'price'      => '$149',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'S/M,L/XL',
				'image'      => get_template_directory_uri() . '/assets/images/scenes/signature-beanie-1.jpg',
				'url'        => '#',
				'left'       => '30',
				'top'        => '42',
			),
			array(
				'id'         => 'sg-012',
				'name'       => esc_html__( 'Midnight Cashmere Beanie', 'skyyrose-flagship' ),
				'price'      => '$169',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'S/M,L/XL',
				'image'      => get_template_directory_uri() . '/assets/images/scenes/signature-beanie-2.jpg',
				'url'        => '#',
				'left'       => '48',
				'top'        => '38',
			),
			array(
				'id'         => 'sg-013',
				'name'       => esc_html__( 'Crimson Edge Beanie', 'skyyrose-flagship' ),
				'price'      => '$149',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'S/M,L/XL',
				'image'      => get_template_directory_uri() . '/assets/images/scenes/signature-beanie-3.jpg',
				'url'        => '#',
				'left'       => '65',
				'top'        => '45',
			),
			array(
				'id'         => 'sg-014',
				'name'       => esc_html__( 'Sterling Knit Beanie', 'skyyrose-flagship' ),
				'price'      => '$159',
				'collection' => esc_html__( 'Signature Collection', 'skyyrose-flagship' ),
				'sizes'      => 'S/M,L/XL',
				'image'      => get_template_directory_uri() . '/assets/images/scenes/signature-beanie-4.jpg',
				'url'        => '#',
				'left'       => '52',
				'top'        => '58',
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

		<!-- Hotspot Containers (one per room) -->
		<?php foreach ( $signature_rooms as $room_index => $room ) : ?>
			<div class="hotspot-container" <?php echo 0 !== $room_index ? 'style="display:none;"' : ''; ?>>
				<?php foreach ( $room['products'] as $product ) : ?>
					<a
						href="<?php echo esc_url( $product['url'] ); ?>"
						class="hotspot"
						style="left: <?php echo esc_attr( $product['left'] ); ?>%; top: <?php echo esc_attr( $product['top'] ); ?>%;"
						data-product-id="<?php echo esc_attr( $product['id'] ); ?>"
						data-product-name="<?php echo esc_attr( $product['name'] ); ?>"
						data-product-price="<?php echo esc_attr( $product['price'] ); ?>"
						data-product-image="<?php echo esc_url( $product['image'] ); ?>"
						data-product-collection="<?php echo esc_attr( $product['collection'] ); ?>"
						data-product-sizes="<?php echo esc_attr( $product['sizes'] ); ?>"
						data-product-url="<?php echo esc_url( $product['url'] ); ?>"
						aria-label="<?php echo esc_attr( $product['name'] . ' — ' . $product['price'] ); ?>"
					>
						<span class="hotspot-beacon"></span>
						<span class="hotspot-label"><?php echo esc_html( $product['name'] ); ?></span>
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
	<aside class="product-panel" role="dialog" aria-label="<?php esc_attr_e( 'Product Details', 'skyyrose-flagship' ); ?>">
		<button class="product-panel-close" type="button" aria-label="<?php esc_attr_e( 'Close product details', 'skyyrose-flagship' ); ?>">&times;</button>
		<div class="product-panel-inner">
			<div class="product-panel-thumb">
				<img src="<?php echo esc_url( get_template_directory_uri() . '/assets/images/placeholder.jpg' ); ?>" alt="">
			</div>
			<div class="product-panel-info">
				<p class="product-panel-collection"></p>
				<h3 class="product-panel-name"></h3>
				<p class="product-panel-price"></p>
				<div class="product-panel-sizes" role="group" aria-label="<?php esc_attr_e( 'Available sizes', 'skyyrose-flagship' ); ?>"></div>
				<div class="product-panel-actions">
					<button class="btn-add-to-cart" type="button"><?php echo esc_html__( 'Add to Cart', 'skyyrose-flagship' ); ?></button>
					<a class="btn-view-details" href="#"><?php echo esc_html__( 'Details', 'skyyrose-flagship' ); ?></a>
				</div>
			</div>
		</div>
	</aside>

	<!-- Collection Tab Bar -->
	<nav class="immersive-tab-bar" aria-label="<?php esc_attr_e( 'Collection navigation', 'skyyrose-flagship' ); ?>">
		<a href="<?php echo esc_url( home_url( '/immersive/black-rose/' ) ); ?>" class="immersive-tab" style="--tab-accent: #C0C0C0;">
			<?php echo esc_html__( 'Black Rose', 'skyyrose-flagship' ); ?>
		</a>
		<a href="<?php echo esc_url( home_url( '/immersive/love-hurts/' ) ); ?>" class="immersive-tab" style="--tab-accent: #DC143C;">
			<?php echo esc_html__( 'Love Hurts', 'skyyrose-flagship' ); ?>
		</a>
		<a href="<?php echo esc_url( home_url( '/immersive/signature/' ) ); ?>" class="immersive-tab active" style="--tab-accent: #B76E79;">
			<?php echo esc_html__( 'Signature', 'skyyrose-flagship' ); ?>
		</a>
		<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>" class="immersive-tab" style="--tab-accent: #D4AF37;">
			<?php echo esc_html__( 'Pre-Order', 'skyyrose-flagship' ); ?>
		</a>
	</nav>

</main><!-- #primary -->

<?php
// Enqueue immersive assets.
wp_enqueue_style(
	'skyyrose-immersive',
	get_template_directory_uri() . '/assets/css/immersive.css',
	array( 'skyyrose-style' ),
	SKYYROSE_VERSION
);

wp_enqueue_script(
	'skyyrose-immersive',
	get_template_directory_uri() . '/assets/js/immersive.js',
	array(),
	SKYYROSE_VERSION,
	true
);

get_template_part( 'template-parts/cinematic-toggle' );

get_footer();
