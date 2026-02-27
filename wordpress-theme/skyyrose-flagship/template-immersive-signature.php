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
 * @since 3.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Multi-room scene data with hotspot products per room.
 * Product data (name, price, image, sizes) pulled from centralized catalog.
 * Scene-specific data (position, prop, prop_label) and split-SKU overrides defined here.
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
			// Glass orb display case (left)
			skyyrose_immersive_product( 'sg-009', array(
				'left'       => '15',
				'top'        => '42',
				'prop'       => 'glass-orb',
				'prop_label' => __( 'Inside glass orb display case', 'skyyrose-flagship' ),
			) ),
			// Gold-lit display frames (center) — sg-002 (Stay Golden Tee, $65 catalog)
			skyyrose_immersive_product( 'sg-002', array(
				'left'       => '42',
				'top'        => '35',
				'prop'       => 'gold-display-frame',
				'prop_label' => __( 'Hanging in gold-lit LED display frame', 'skyyrose-flagship' ),
			) ),
			// sg-010 (Bridge Shorts) displayed alongside
			skyyrose_immersive_product( 'sg-010', array(
				'left'       => '50',
				'top'        => '38',
				'prop'       => 'gold-display-frame',
				'prop_label' => __( 'Hanging in gold-lit LED display frame', 'skyyrose-flagship' ),
			) ),
			// Gold-lit display frame (right)
			skyyrose_immersive_product( 'sg-006', array(
				'left'       => '62',
				'top'        => '36',
				'prop'       => 'gold-display-frame',
				'prop_label' => __( 'Hanging in gold-lit LED display frame', 'skyyrose-flagship' ),
			) ),
			// Featured marble pedestal (right) — sg-001 The Bay Set ($195 catalog)
			skyyrose_immersive_product( 'sg-001', array(
				'left'       => '75',
				'top'        => '50',
				'prop'       => 'marble-pedestal',
				'prop_label' => __( 'Featured on stepped marble pedestal', 'skyyrose-flagship' ),
			) ),
			// sg-008 Signature Crop Hoodie — displayed on lower pedestal step
			skyyrose_immersive_product( 'sg-008', array(
				'left'       => '82',
				'top'        => '58',
				'prop'       => 'marble-pedestal',
				'prop_label' => __( 'On lower marble pedestal step', 'skyyrose-flagship' ),
			) ),
		),
	),
	// Room 2 — Golden Gate Showroom
	array(
		'name'     => esc_html__( 'Golden Gate Showroom', 'skyyrose-flagship' ),
		'image'    => get_template_directory_uri() . '/assets/scenes/signature/signature-golden-gate-showroom.png',
		'alt'      => esc_attr__( 'Golden Gate Bridge sunset showroom with floor-to-ceiling panoramic windows, black marble interior with gold LED trim, clothing racks, marble pedestals, and dramatic sunset sky', 'skyyrose-flagship' ),
		'products' => array(
			// Left wall clothing rack — sg-003 uses sg-012 image (no sg-003 source image available)
			skyyrose_immersive_product( 'sg-003', array(
				'image'      => get_theme_file_uri( 'assets/images/products/sg-012-label-tee-orchid.webp' ),
				'left'       => '18',
				'top'        => '38',
				'prop'       => 'clothing-rack',
				'prop_label' => __( 'Hanging on left wall clothing rack', 'skyyrose-flagship' ),
			) ),
			// Center marble display table
			skyyrose_immersive_product( 'sg-005', array(
				'left'       => '50',
				'top'        => '52',
				'prop'       => 'marble-display-table',
				'prop_label' => __( 'Featured on center marble display table', 'skyyrose-flagship' ),
			) ),
			// Left marble pedestal
			skyyrose_immersive_product( 'sg-007', array(
				'left'       => '32',
				'top'        => '48',
				'prop'       => 'marble-pedestal',
				'prop_label' => __( 'On left marble pedestal', 'skyyrose-flagship' ),
			) ),
			// Right wall clothing rack
			skyyrose_immersive_product( 'sg-010', array(
				'left'       => '78',
				'top'        => '38',
				'prop'       => 'clothing-rack',
				'prop_label' => __( 'Hanging on right wall clothing rack', 'skyyrose-flagship' ),
			) ),
		),
	),
);

// Remove empty entries (unpublished products filtered by skyyrose_immersive_product()).
foreach ( $signature_rooms as &$room ) {
	$room['products'] = array_values( array_filter( $room['products'] ) );
}
unset( $room );

get_header();
?>

<main id="primary" class="site-main immersive-page" role="main" tabindex="-1">

	<div class="immersive-scene immersive-signature" role="region" aria-labelledby="scene-title">

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
						data-fallback="<?php echo esc_url( get_template_directory_uri() . '/assets/images/placeholder.jpg' ); ?>"
					>
				</div>
			<?php endforeach; ?>
		</div>

		<!-- Vignette -->
		<div class="scene-vignette" aria-hidden="true"></div>

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
					aria-pressed="<?php echo 0 === $index ? 'true' : 'false'; ?>"
					aria-label="<?php echo esc_attr( sprintf( __( 'Room %1$d of %2$d: %3$s', 'skyyrose-flagship' ), $index + 1, count( $signature_rooms ), $room['name'] ) ); ?>"
				></button>
			<?php endforeach; ?>
		</div>
		<div class="room-name" aria-live="polite" aria-atomic="true"><?php echo esc_html( $signature_rooms[0]['name'] ); ?></div>

		<!-- Hotspot Containers — Products placed on contextual props -->
		<?php foreach ( $signature_rooms as $room_index => $room ) : ?>
			<div class="hotspot-container" <?php echo 0 !== $room_index ? 'aria-hidden="true" inert style="display:none;"' : ''; ?>>
				<?php foreach ( $room['products'] as $product ) : ?>
					<a
						href="<?php echo esc_url( $product['url'] ); ?>"
						class="hotspot hotspot--prop-<?php echo esc_attr( $product['prop'] ); ?>"
						style="left: <?php echo esc_attr( $product['left'] ); ?>%; top: <?php echo esc_attr( $product['top'] ); ?>%;"
						data-product-id="<?php echo esc_attr( $product['id'] ); ?>"
						data-product-sku="<?php echo esc_attr( $product['id'] ); ?>"
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
							<span class="hotspot-label-price"><?php echo esc_html( $product['price'] ); ?></span>
						</span>
					</a>
				<?php endforeach; ?>
			</div>
		<?php endforeach; ?>

		<!-- Scene Title -->
		<div class="scene-title-overlay">
			<h1 id="scene-title"><?php echo esc_html__( 'The Runway', 'skyyrose-flagship' ); ?></h1>
			<p class="scene-subtitle"><?php echo esc_html__( 'Signature Collection', 'skyyrose-flagship' ); ?></p>
			<p class="scene-tagline"><?php echo esc_html__( 'Luxury Grows from Concrete.', 'skyyrose-flagship' ); ?></p>
		</div>

		<!-- Explore Full Collection CTA -->
		<div class="immersive-cta">
			<a href="<?php echo esc_url( home_url( '/collection-signature/' ) ); ?>" class="immersive-cta__link">
				<span class="immersive-cta__text"><?php esc_html_e( 'Explore the Full Collection', 'skyyrose-flagship' ); ?></span>
				<svg class="immersive-cta__arrow" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
					<path d="M5 12h14"/>
					<path d="m12 5 7 7-7 7"/>
				</svg>
			</a>
		</div>

	</div><!-- .immersive-scene -->

	<!-- Product Detail Panel (Glassmorphism Slide-Up) -->
	<div class="product-panel-overlay" aria-hidden="true"></div>
	<div class="product-panel" role="dialog" aria-modal="true" aria-hidden="true" inert aria-labelledby="product-panel-name">
		<button class="product-panel-close" type="button" aria-label="<?php esc_attr_e( 'Close product details', 'skyyrose-flagship' ); ?>">&times;</button>
		<div class="product-panel-inner">
			<div class="product-panel-thumb">
				<img src="<?php echo esc_url( get_template_directory_uri() . '/assets/images/placeholder-product.jpg' ); ?>" alt="<?php esc_attr_e( 'Product preview', 'skyyrose-flagship' ); ?>" data-fallback="<?php echo esc_url( get_template_directory_uri() . '/assets/images/placeholder-product.jpg' ); ?>">
			</div>
			<div class="product-panel-info">
				<p class="product-panel-collection"></p>
				<h3 class="product-panel-name" id="product-panel-name"><?php esc_html_e( 'Product Details', 'skyyrose-flagship' ); ?></h3>
				<p class="product-panel-prop"></p>
				<p class="product-panel-price"></p>
				<div class="product-panel-sizes" role="group" aria-label="<?php esc_attr_e( 'Available sizes', 'skyyrose-flagship' ); ?>"></div>
				<div class="product-panel-actions">
					<button class="btn-add-to-cart" type="button"><?php echo esc_html__( 'Pre-Order Now', 'skyyrose-flagship' ); ?></button>
					<a class="btn-view-details" href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>"><?php echo esc_html__( 'View Details', 'skyyrose-flagship' ); ?></a>
				</div>
				<a class="btn-view-collection" href="<?php echo esc_url( home_url( '/collection-signature/' ) ); ?>">
					<?php esc_html_e( 'View Full Collection', 'skyyrose-flagship' ); ?>
					<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
						<path d="M5 12h14"/>
						<path d="m12 5 7 7-7 7"/>
					</svg>
				</a>
			</div>
		</div>
	</div>

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
		<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>" class="immersive-tab" style="--tab-accent: #D4AF37;">
			<?php echo esc_html__( 'Pre-Order', 'skyyrose-flagship' ); ?>
		</a>
	</nav>

	<?php get_template_part( 'template-parts/cinematic-toggle' ); ?>

	<!-- Conversion Intelligence: Urgency Countdown -->
	<div style="position:absolute; bottom:56px; right:16px; z-index:12;">
		<div data-cie-countdown="auto" data-cie-countdown-label="<?php esc_attr_e( 'Pre-Order Closes', 'skyyrose-flagship' ); ?>"></div>
	</div>

</main><!-- #primary -->

<?php
get_footer();
