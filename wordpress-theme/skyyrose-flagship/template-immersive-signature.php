<?php
/**
 * Template Name: Immersive - Signature
 *
 * "The Golden Gate Runway" — San Francisco waterfront, golden hour,
 * Golden Gate Bridge showroom. Bay Area luxury.
 *
 * Three.js-powered scroll-driven 3D world (progressive enhancement).
 * Falls back to 2D hotspot rooms if WebGL unavailable.
 *
 * @package SkyyRose_Flagship
 * @since   3.0.0
 * @updated 4.3.0 — Three.js immersive world engine
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/* ─────────────────────────────────────────────────────────
   2D Fallback Room Data (preserved for non-WebGL browsers)
   Note: sg-008 is permanently deleted — not included here.
   ───────────────────────────────────────────────────────── */

$signature_rooms = array(
	// Room 1 — Waterfront Runway
	array(
		'name'     => esc_html__( 'Waterfront Runway', 'skyyrose-flagship' ),
		'image'    => get_template_directory_uri() . '/assets/scenes/signature/signature-waterfront-runway.png',
		'alt'      => esc_attr__( 'Bay Bridge waterfront at night with black marble platform floating over water, gold-lit LED display frames with hanging garments, glass orb display case, and stepped marble pedestals', 'skyyrose-flagship' ),
		'products' => array(
			skyyrose_immersive_product( 'sg-009', array(
				'left'       => '15',
				'top'        => '42',
				'prop'       => 'glass-orb',
				'prop_label' => __( 'Inside glass orb display case', 'skyyrose-flagship' ),
			) ),
			skyyrose_immersive_product( 'sg-002', array(
				'left'       => '42',
				'top'        => '35',
				'prop'       => 'gold-display-frame',
				'prop_label' => __( 'Hanging in gold-lit LED display frame', 'skyyrose-flagship' ),
			) ),
			skyyrose_immersive_product( 'sg-010', array(
				'left'       => '50',
				'top'        => '38',
				'prop'       => 'gold-display-frame',
				'prop_label' => __( 'Hanging in gold-lit LED display frame', 'skyyrose-flagship' ),
			) ),
			skyyrose_immersive_product( 'sg-006', array(
				'left'       => '62',
				'top'        => '36',
				'prop'       => 'gold-display-frame',
				'prop_label' => __( 'Hanging in gold-lit LED display frame', 'skyyrose-flagship' ),
			) ),
			skyyrose_immersive_product( 'sg-001', array(
				'left'       => '75',
				'top'        => '50',
				'prop'       => 'marble-pedestal',
				'prop_label' => __( 'Featured on stepped marble pedestal', 'skyyrose-flagship' ),
			) ),
		),
	),
	// Room 2 — Golden Gate Showroom
	array(
		'name'     => esc_html__( 'Golden Gate Showroom', 'skyyrose-flagship' ),
		'image'    => get_template_directory_uri() . '/assets/scenes/signature/signature-golden-gate-showroom.png',
		'alt'      => esc_attr__( 'Golden Gate Bridge sunset showroom with floor-to-ceiling panoramic windows, black marble interior with gold LED trim, clothing racks, marble pedestals, and dramatic sunset sky', 'skyyrose-flagship' ),
		'products' => array(
			skyyrose_immersive_product( 'sg-003', array(
				'left'       => '18',
				'top'        => '38',
				'prop'       => 'clothing-rack',
				'prop_label' => __( 'Hanging on left wall clothing rack', 'skyyrose-flagship' ),
			) ),
			skyyrose_immersive_product( 'sg-005', array(
				'left'       => '50',
				'top'        => '52',
				'prop'       => 'marble-display-table',
				'prop_label' => __( 'Featured on center marble display table', 'skyyrose-flagship' ),
			) ),
			skyyrose_immersive_product( 'sg-007', array(
				'left'       => '32',
				'top'        => '48',
				'prop'       => 'marble-pedestal',
				'prop_label' => __( 'On left marble pedestal', 'skyyrose-flagship' ),
			) ),
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

/* ─────────────────────────────────────────────────────────
   3D World Config — "The Golden Gate Runway"

   Scroll-driven Three.js experience:
   - 2 scene images as parallax depth layers (showroom → avatar reveal)
   - Camera path through Golden Gate Bridge showroom at golden hour
   - Lens flare, bay fog, water sparkle particles
   - 7 product hotspots in 3D space
   - Bay Area luxury narrative panels
   ───────────────────────────────────────────────────────── */

$assets_uri   = get_template_directory_uri() . '/assets';
$scenes_uri   = $assets_uri . '/scenes/signature';
$products_uri = $assets_uri . '/images/products';

// Build product data for 3D world — core Signature lineup (sg-008 is deleted, excluded).
$sg_world_products = array();
$sg_world_skus     = array( 'sg-001', 'sg-002', 'sg-003', 'sg-005', 'sg-006', 'sg-007', 'sg-009', 'sg-010', 'sg-013' );

foreach ( $sg_world_skus as $sku ) {
	$p = function_exists( 'skyyrose_get_product' ) ? skyyrose_get_product( $sku ) : null;
	if ( ! $p ) {
		continue;
	}
	$img = ! empty( $p['front_model_image'] ) ? $p['front_model_image'] : $p['image'];
	$sg_world_products[] = array(
		'sku'   => $sku,
		'name'  => $p['name'],
		'price' => number_format( (float) $p['price'], 0 ),
		'image' => get_theme_file_uri( $img ),
		'sizes' => array_map( 'trim', explode( '|', $p['sizes'] ) ),
	);
}

$world_config = array(
	'collection'  => 'signature',
	'bgColor'     => '0x1a1008',
	'accentColor' => '#D4AF37',

	/*
	 * Scene Layers — 2 depth layers for parallax effect.
	 *
	 * Layer 0 (front): Golden Gate showroom — main visual.
	 * Layer 1 (back):  Avatar version — easter egg hidden in background.
	 *
	 * depth: 0 = front (z:0), 1 = back (z:-20).
	 * parallax: movement multiplier on scroll (higher = more movement).
	 */
	'layers' => array(
		array(
			'image'    => $scenes_uri . '/signature-golden-gate-showroom-lookbook.webp',
			'depth'    => 0.0,
			'parallax' => 0.2,
			'opacity'  => 1,
		),
		array(
			'image'    => $scenes_uri . '/signature-golden-gate-showroom-v2-avatar.webp',
			'depth'    => 0.6,
			'parallax' => 0.7,
			'opacity'  => 0.5,
		),
	),

	/*
	 * Particle Systems — atmospheric effects.
	 *
	 * Golden hour lens flare (warm Bay sunlight refracting).
	 * Bay fog (cables and water vapor drifting through).
	 * Water sparkle (sunlight on the Bay surface below).
	 */
	'particles' => array(
		array(
			'type'    => 'flare',
			'count'   => 25,
			'color'   => '#D4AF37',
			'size'    => 0.06,
			'opacity' => 0.4,
			'speed'   => 0.05,
			'bounds'  => array( 16, 10, 12 ),
		),
		array(
			'type'    => 'fog',
			'count'   => 45,
			'color'   => '#C8D8E8',
			'size'    => 0.07,
			'opacity' => 0.2,
			'speed'   => 0.08,
			'bounds'  => array( 20, 8, 14 ),
		),
		array(
			'type'    => 'sparkle',
			'count'   => 35,
			'color'   => '#FFD700',
			'size'    => 0.025,
			'opacity' => 0.3,
			'speed'   => 0.12,
			'bounds'  => array( 14, 6, 10 ),
		),
	),

	/* Product data (for panel display). */
	'products' => $sg_world_products,

	/*
	 * Product placements in 3D space.
	 * Spread across the depth of the scene so products reveal as you scroll.
	 * position: [x, y, z] in world units.
	 */
	'productPlacements' => array(
		array( 'sku' => 'sg-009', 'position' => array( -3.5, 2.5, -1.0 ) ),
		array( 'sku' => 'sg-006', 'position' => array( 3.0, 2.0, -3.0 ) ),
		array( 'sku' => 'sg-001', 'position' => array( -2.5, 1.8, -6.0 ) ),
		array( 'sku' => 'sg-002', 'position' => array( 2.0, 2.2, -9.0 ) ),
		array( 'sku' => 'sg-010', 'position' => array( -1.5, 1.5, -12.0 ) ),
		array( 'sku' => 'sg-007', 'position' => array( 1.5, 2.0, -15.0 ) ),
		array( 'sku' => 'sg-013', 'position' => array( 0, 2.5, -18.0 ) ),
	),

	/*
	 * Camera Path — scroll-driven waypoints.
	 *
	 * As scroll progresses 0→1, camera glides through the Golden Gate showroom
	 * toward the bridge panorama at golden hour.
	 */
	'cameraPath' => array(
		// 0.0 — Showroom entrance, wide golden hour shot
		array(
			'position' => array( 0, 2.5, 8 ),
			'target'   => array( 0, 2.0, -4 ),
			'fov'      => 68,
		),
		// ~0.15 — Moving into the showroom, clothing racks visible
		array(
			'position' => array( 0.6, 3.0, 5 ),
			'target'   => array( 0, 2.0, -7 ),
			'fov'      => 60,
		),
		// ~0.30 — Sweeping left past the marble pedestals
		array(
			'position' => array( -0.8, 2.5, 2 ),
			'target'   => array( 0, 2.0, -10 ),
			'fov'      => 54,
		),
		// ~0.45 — Mid-runway, golden light at peak
		array(
			'position' => array( 0.4, 2.0, -1 ),
			'target'   => array( 0, 1.8, -13 ),
			'fov'      => 50,
		),
		// ~0.60 — Deep in, fog wisps through window panels
		array(
			'position' => array( -0.3, 2.5, -4 ),
			'target'   => array( 0, 2.0, -16 ),
			'fov'      => 52,
		),
		// ~0.75 — Near back, bridge towers visible through glass
		array(
			'position' => array( 0.2, 2.0, -7 ),
			'target'   => array( 0, 1.5, -19 ),
			'fov'      => 54,
		),
		// ~0.95 — Climax: close to panoramic windows, bridge and bay below
		array(
			'position' => array( 0, 1.8, -10 ),
			'target'   => array( 0, 1.0, -22 ),
			'fov'      => 58,
		),
	),

	/*
	 * Avatar Easter Egg — hidden mascot in the scene.
	 * Position matches the composited sprite in the -avatar.webp scene image.
	 */
	'avatar' => array(
		'x'          => 87.9,
		'y'          => 69.9,
		'w'          => 5.0,
		'h'          => 9.0,
		'walkSide'   => 'right',
		'sprite'     => $assets_uri . '/images/mascot/skyyrose-mascot-signature.png',
		'introImage' => $assets_uri . '/images/mascot/skyyrose-mascot-reference.png',
	),

	/*
	 * Narrative Panels — Bay Area luxury story.
	 *
	 * Each panel triggered at a scroll position (0→1).
	 * position: left|right|center — which side of the screen.
	 * style: prose|quote|whisper — visual treatment.
	 */
	'narrativePanels' => array(
		array(
			'trigger'  => 0.05,
			'text'     => 'Between the fog and the water, a runway was born.',
			'position' => 'left',
			'style'    => 'whisper',
		),
		array(
			'trigger'  => 0.18,
			'text'     => 'Signature isn\'t about what you wear. It\'s how you carry it.',
			'subtext'  => 'Signature Collection — San Francisco.',
			'position' => 'right',
			'style'    => 'prose',
		),
		array(
			'trigger'  => 0.35,
			'text'     => 'The bridge between street and luxury — this is it.',
			'position' => 'center',
			'style'    => 'quote',
		),
		array(
			'trigger'  => 0.50,
			'text'     => 'Golden hour on the Bay. Every color in this collection caught in that light.',
			'position' => 'left',
			'style'    => 'prose',
		),
		array(
			'trigger'  => 0.68,
			'text'     => 'San Francisco built its own rules. So did we.',
			'position' => 'right',
			'style'    => 'whisper',
		),
		array(
			'trigger'  => 0.82,
			'text'     => 'Stay Golden. The Bay never asks permission to shine.',
			'position' => 'center',
			'style'    => 'quote',
		),
		array(
			'trigger'  => 0.95,
			'text'     => 'Luxury Grows from Concrete.',
			'subtext'  => 'Signature Collection',
			'position' => 'center',
			'style'    => 'prose',
		),
	),
);

get_header();
?>

<main id="primary" class="site-main immersive-page immersive-world-page" role="main" tabindex="-1">

	<!-- ═══ 3D World (Progressive Enhancement) ═══
	     Three.js canvas + narrative overlay + JSON config.
	     If WebGL unavailable, immersive-world.js bails out and
	     the 2D .immersive-scene fallback below remains visible.
	     ═══════════════════════════════════════════════════════ -->

	<div id="world-canvas" aria-label="<?php esc_attr_e( 'Immersive 3D experience — The Golden Gate Runway', 'skyyrose-flagship' ); ?>"></div>
	<div id="world-narrative" aria-live="polite"></div>

	<!-- Scroll spacer: gives scroll distance for the camera path to traverse -->
	<div class="world-scroll-spacer" aria-hidden="true"></div>

	<script type="application/json" id="world-config">
	<?php echo wp_json_encode( $world_config, JSON_UNESCAPED_SLASHES ); ?>
	</script>

	<!-- ═══ 2D Fallback (hidden when 3D active) ═══ -->
	<div class="immersive-scene immersive-signature" role="region" aria-labelledby="scene-title">

		<!-- Loading Screen -->
		<?php get_template_part( 'template-parts/immersive-loader', null, array( 'world_name' => __( 'The Golden Gate Runway', 'skyyrose-flagship' ) ) ); ?>

		<!-- Scene Viewport — Multi-Room Layers -->
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
			<h1 id="scene-title"><?php echo esc_html__( 'The Golden Gate Runway', 'skyyrose-flagship' ); ?></h1>
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

	</div><!-- .immersive-scene (2D fallback) -->

	<!-- Product Detail Panel (Glassmorphism Slide-Up — shared by 2D + 3D) -->
	<div class="product-panel-overlay" aria-hidden="true"></div>
	<div class="product-panel" role="dialog" aria-modal="true" aria-hidden="true" inert aria-labelledby="product-panel-name" tabindex="-1">
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

	<!-- Cross-World Navigation Doors -->
	<nav class="world-nav" aria-label="<?php esc_attr_e( 'Enter another world', 'skyyrose-flagship' ); ?>">
		<div class="world-nav__doors">
			<a href="<?php echo esc_url( home_url( '/experience-black-rose/' ) ); ?>" class="world-nav__door">
				<img
					class="world-nav__door-image"
					src="<?php echo esc_url( get_template_directory_uri() . '/assets/scenes/black-rose/black-rose-rooftop-garden-lookbook.webp' ); ?>"
					alt="" loading="lazy" width="320" height="180"
				>
				<span class="world-nav__door-label"><?php echo esc_html__( 'Enter The Bay Bridge', 'skyyrose-flagship' ); ?></span>
			</a>
			<a href="<?php echo esc_url( home_url( '/experience-love-hurts/' ) ); ?>" class="world-nav__door">
				<img
					class="world-nav__door-image"
					src="<?php echo esc_url( get_template_directory_uri() . '/assets/scenes/love-hurts/love-hurts-cathedral-rose-chamber-lookbook.webp' ); ?>"
					alt="" loading="lazy" width="320" height="180"
				>
				<span class="world-nav__door-label"><?php echo esc_html__( 'Enter The Cathedral', 'skyyrose-flagship' ); ?></span>
			</a>
		</div>
		<a href="<?php echo esc_url( home_url( '/spatial/' ) ); ?>" class="world-nav__back">
			<?php echo esc_html__( 'Return to Front Door', 'skyyrose-flagship' ); ?>
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
