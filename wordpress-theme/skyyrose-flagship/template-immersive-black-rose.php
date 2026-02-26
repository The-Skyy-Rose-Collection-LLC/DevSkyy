<?php
/**
 * Template Name: Immersive - Black Rose
 *
 * "The Garden" — Gothic cathedral garden with moonlit courtyard and
 * iron gazebo garden. 2 immersive rooms with prop-specific hotspots.
 * Extra scenes (marble-rotunda, white-rose-grotto) used as CSS backgrounds.
 * drakerelated.com-style immersive experience: full-viewport rooms,
 * pulsing beacon hotspots, smooth room-to-room transitions.
 *
 * @package SkyyRose_Flagship
 * @since   3.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Multi-room scene data.
 * Each room is a full-viewport scene with its own background image and hotspot products.
 * Product data (name, price, image, sizes) pulled from centralized catalog.
 * Scene-specific data (position, prop, prop_label) defined here.
 */
$black_rose_rooms = array(
	// Room 1 — Moonlit Courtyard
	array(
		'name'     => esc_html__( 'Moonlit Courtyard', 'skyyrose-flagship' ),
		'image'    => get_template_directory_uri() . '/assets/scenes/black-rose/black-rose-moonlit-courtyard.jpg',
		'alt'      => esc_attr__( 'Moonlit garden courtyard with marble statues, black rose topiaries, and ornate fountains', 'skyyrose-flagship' ),
		'products' => array(
			skyyrose_immersive_product( 'br-006', array(
				'left'       => '15',
				'top'        => '42',
				'prop'       => 'marble-statue',
				'prop_label' => esc_html__( 'Draped over marble garden statue', 'skyyrose-flagship' ),
			) ),
			skyyrose_immersive_product( 'br-005', array(
				'left'       => '38',
				'top'        => '50',
				'prop'       => 'fountain-edge',
				'prop_label' => esc_html__( 'Folded on fountain edge', 'skyyrose-flagship' ),
			) ),
			skyyrose_immersive_product( 'br-002', array(
				'left'       => '62',
				'top'        => '55',
				'prop'       => 'topiary-base',
				'prop_label' => esc_html__( 'Folded at base of rose topiary', 'skyyrose-flagship' ),
			) ),
			skyyrose_immersive_product( 'br-007', array(
				'left'       => '82',
				'top'        => '48',
				'prop'       => 'statue-pedestal',
				'prop_label' => esc_html__( 'Draped over statue pedestal', 'skyyrose-flagship' ),
			) ),
		),
	),
	// Room 2 — Iron Gazebo Garden
	array(
		'name'     => esc_html__( 'Iron Gazebo Garden', 'skyyrose-flagship' ),
		'image'    => get_template_directory_uri() . '/assets/scenes/black-rose/black-rose-iron-gazebo-garden.png',
		'alt'      => esc_attr__( 'Aerial view of ornate iron gazebo surrounded by rose hedge maze and cobblestone paths under moonlight', 'skyyrose-flagship' ),
		'products' => array(
			skyyrose_immersive_product( 'br-004', array(
				'left'       => '30',
				'top'        => '40',
				'prop'       => 'iron-gazebo',
				'prop_label' => esc_html__( 'Displayed inside iron gazebo', 'skyyrose-flagship' ),
			) ),
			skyyrose_immersive_product( 'br-001', array(
				'left'       => '55',
				'top'        => '35',
				'prop'       => 'hedge-arch',
				'prop_label' => esc_html__( 'Hanging from rose hedge archway', 'skyyrose-flagship' ),
			) ),
			skyyrose_immersive_product( 'br-008', array(
				'left'       => '72',
				'top'        => '50',
				'prop'       => 'cobblestone-bench',
				'prop_label' => esc_html__( 'Draped over cobblestone garden bench', 'skyyrose-flagship' ),
			) ),
			skyyrose_immersive_product( 'br-003', array(
				'left'       => '48',
				'top'        => '60',
				'prop'       => 'hedge-maze-wall',
				'prop_label' => esc_html__( 'Displayed on hedge maze wall', 'skyyrose-flagship' ),
			) ),
		),
	),
);

get_header();
?>

<main id="primary" class="site-main immersive-page" role="main" tabindex="-1">

	<div class="immersive-scene immersive-black-rose" role="region" aria-label="<?php esc_attr_e( 'Black Rose Collection — The Garden', 'skyyrose-flagship' ); ?>">

		<!-- Loading Screen -->
		<div class="scene-loading" aria-hidden="true">
			<div class="scene-loading-monogram"><?php echo esc_html__( 'SR', 'skyyrose-flagship' ); ?></div>
			<div class="scene-loading-text"><?php echo esc_html__( 'Entering The Garden', 'skyyrose-flagship' ); ?></div>
		</div>

		<!-- Scene Viewport — Multi-Room Layers -->
		<div class="scene-viewport">
			<?php foreach ( $black_rose_rooms as $index => $room ) : ?>
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
			<?php foreach ( $black_rose_rooms as $index => $room ) : ?>
				<button
					class="room-dot<?php echo 0 === $index ? ' active' : ''; ?>"
					type="button"
					aria-pressed="<?php echo 0 === $index ? 'true' : 'false'; ?>"
					aria-label="<?php echo esc_attr( sprintf( __( 'Room %1$d of %2$d: %3$s', 'skyyrose-flagship' ), $index + 1, count( $black_rose_rooms ), $room['name'] ) ); ?>"
				></button>
			<?php endforeach; ?>
		</div>
		<div class="room-name" aria-live="polite" aria-atomic="true"><?php echo esc_html( $black_rose_rooms[0]['name'] ); ?></div>

		<!-- Hotspot Containers — One per room, products on contextual props -->
		<?php foreach ( $black_rose_rooms as $room_index => $room ) : ?>
			<div class="hotspot-container" <?php echo 0 !== $room_index ? 'aria-hidden="true" style="display:none;"' : ''; ?>>
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
							<span class="hotspot-label-price"><?php echo esc_html( $product['price'] ); ?></span>
						</span>
					</a>
				<?php endforeach; ?>
			</div>
		<?php endforeach; ?>

		<!-- Scene Title -->
		<div class="scene-title-overlay">
			<h1><?php echo esc_html__( 'The Garden', 'skyyrose-flagship' ); ?></h1>
			<p class="scene-subtitle"><?php echo esc_html__( 'Black Rose Collection', 'skyyrose-flagship' ); ?></p>
			<p class="scene-tagline"><?php echo esc_html__( 'Luxury Grows from Concrete.', 'skyyrose-flagship' ); ?></p>
		</div>

		<!-- Explore Full Collection CTA -->
		<div class="immersive-cta">
			<a href="<?php echo esc_url( home_url( '/collection-black-rose/' ) ); ?>" class="immersive-cta__link">
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
	<aside class="product-panel" role="dialog" aria-modal="true" aria-hidden="true" aria-labelledby="product-panel-name">
		<button class="product-panel-close" type="button" aria-label="<?php esc_attr_e( 'Close product details', 'skyyrose-flagship' ); ?>">&times;</button>
		<div class="product-panel-inner">
			<div class="product-panel-thumb">
				<img src="<?php echo esc_url( get_template_directory_uri() . '/assets/images/placeholder-product.jpg' ); ?>" alt="<?php esc_attr_e( 'Product preview', 'skyyrose-flagship' ); ?>" data-fallback="<?php echo esc_url( get_template_directory_uri() . '/assets/images/placeholder-product.jpg' ); ?>">
			</div>
			<div class="product-panel-info">
				<p class="product-panel-collection"></p>
				<h3 class="product-panel-name" id="product-panel-name"></h3>
				<p class="product-panel-prop"></p>
				<p class="product-panel-price"></p>
				<div class="product-panel-sizes" role="group" aria-label="<?php esc_attr_e( 'Available sizes', 'skyyrose-flagship' ); ?>"></div>
				<div class="product-panel-actions">
					<button class="btn-add-to-cart" type="button"><?php echo esc_html__( 'Pre-Order Now', 'skyyrose-flagship' ); ?></button>
					<a class="btn-view-details" href="#"><?php echo esc_html__( 'View Details', 'skyyrose-flagship' ); ?></a>
				</div>
				<a class="btn-view-collection" href="<?php echo esc_url( home_url( '/collection-black-rose/' ) ); ?>">
					<?php esc_html_e( 'View Full Collection', 'skyyrose-flagship' ); ?>
					<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
						<path d="M5 12h14"/>
						<path d="m12 5 7 7-7 7"/>
					</svg>
				</a>
			</div>
		</div>
	</aside>

	<!-- Collection Tab Bar -->
	<nav class="immersive-tab-bar" aria-label="<?php esc_attr_e( 'Collection navigation', 'skyyrose-flagship' ); ?>">
		<a href="<?php echo esc_url( home_url( '/experience-black-rose/' ) ); ?>" class="immersive-tab active" aria-current="page" style="--tab-accent: #C0C0C0;">
			<?php echo esc_html__( 'Black Rose', 'skyyrose-flagship' ); ?>
		</a>
		<a href="<?php echo esc_url( home_url( '/experience-love-hurts/' ) ); ?>" class="immersive-tab" style="--tab-accent: #DC143C;">
			<?php echo esc_html__( 'Love Hurts', 'skyyrose-flagship' ); ?>
		</a>
		<a href="<?php echo esc_url( home_url( '/experience-signature/' ) ); ?>" class="immersive-tab" style="--tab-accent: #B76E79;">
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
