<?php
/**
 * Template Name: Immersive - Love Hurts
 *
 * "The Beast's Cathedral" — Beauty and the Beast from the Beast's perspective.
 * Enchanted rose under glass dome, gothic cathedral, thorns, candlelight, crimson.
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
   ───────────────────────────────────────────────────────── */

$love_hurts_rooms = array(
	// Room 1 — Cathedral Rose Chamber
	array(
		'name'     => esc_html__( 'Cathedral Rose Chamber', 'skyyrose-flagship' ),
		'image'    => get_template_directory_uri() . '/assets/scenes/love-hurts/love-hurts-cathedral-rose-chamber.png',
		'alt'      => esc_attr__( 'Gothic cathedral with enchanted rose under glass dome, stained glass windows, candelabras, and crimson petals', 'skyyrose-flagship' ),
		'products' => array(
			skyyrose_immersive_product( 'lh-004', array(
				'left'       => '35',
				'top'        => '42',
				'prop'       => 'glass-dome',
				'prop_label' => __( 'Draped beside enchanted rose dome', 'skyyrose-flagship' ),
			) ),
			skyyrose_immersive_product( 'lh-006', array(
				'left'       => '68',
				'top'        => '38',
				'prop'       => 'candelabra',
				'prop_label' => __( 'Hung from gothic candelabra stand', 'skyyrose-flagship' ),
			) ),
			skyyrose_immersive_product( 'lh-003', array(
				'left'       => '52',
				'top'        => '60',
				'prop'       => 'stained-glass-alcove',
				'prop_label' => __( 'Displayed in stained glass alcove', 'skyyrose-flagship' ),
			) ),
		),
	),
	// Room 2 — Gothic Ballroom
	array(
		'name'     => esc_html__( 'Gothic Ballroom', 'skyyrose-flagship' ),
		'image'    => get_template_directory_uri() . '/assets/scenes/love-hurts/love-hurts-gothic-ballroom.png',
		'alt'      => esc_attr__( 'Gothic chamber with rose under glass dome, purple draped fabrics, pink petals, and candlelit atmosphere', 'skyyrose-flagship' ),
		'products' => array(
			skyyrose_immersive_product( 'lh-002', array(
				'name'       => __( 'Love Hurts Joggers (BLACK)', 'skyyrose-flagship' ),
				'left'       => '40',
				'top'        => '45',
				'prop'       => 'velvet-drape',
				'prop_label' => __( 'Folded on purple velvet drape', 'skyyrose-flagship' ),
			) ),
			skyyrose_immersive_product( 'lh-002b', array(
				'name'       => __( 'Love Hurts Joggers (WHITE)', 'skyyrose-flagship' ),
				'image'      => get_theme_file_uri( 'assets/images/products/love-hurts-joggers-front-model.webp' ),
				'left'       => '65',
				'top'        => '48',
				'prop'       => 'glass-dome',
				'prop_label' => __( 'Displayed beside glass dome', 'skyyrose-flagship' ),
			) ),
		),
	),
);

// Remove empty entries (unpublished products filtered by skyyrose_immersive_product()).
foreach ( $love_hurts_rooms as &$room ) {
	$room['products'] = array_values( array_filter( $room['products'] ) );
}
unset( $room );

/* ─────────────────────────────────────────────────────────
   3D World Config — "The Beast's Cathedral"

   Scroll-driven Three.js experience:
   - 7 scenes as parallax depth layers (cathedral → dome climax)
   - Camera path with smooth waypoints through gothic spaces
   - Crimson petals, candle flicker, dust beams particles
   - 5 product hotspots in 3D space
   - Beast's inner monologue narrative panels
   ───────────────────────────────────────────────────────── */

$assets_uri  = get_template_directory_uri() . '/assets';
$scenes_uri  = $assets_uri . '/scenes/love-hurts';
$products_uri = $assets_uri . '/images/products';

// Build product data for 3D world (ALL 5 LH products — ignores publish status).
$lh_world_products = array();
$lh_world_skus     = array( 'lh-002', 'lh-003', 'lh-004', 'lh-005', 'lh-006' );

foreach ( $lh_world_skus as $sku ) {
	$p = function_exists( 'skyyrose_get_product' ) ? skyyrose_get_product( $sku ) : null;
	if ( ! $p ) {
		continue;
	}
	$img = ! empty( $p['front_model_image'] ) ? $p['front_model_image'] : $p['image'];
	$lh_world_products[] = array(
		'sku'   => $sku,
		'name'  => $p['name'],
		'price' => number_format( (float) $p['price'], 0 ),
		'image' => get_theme_file_uri( $img ),
		'sizes' => array_map( 'trim', explode( '|', $p['sizes'] ) ),
	);
}

$world_config = array(
	'collection'  => 'love-hurts',
	'bgColor'     => '0x1a0508',
	'accentColor' => '#DC143C',

	/*
	 * Scene Layers — 3 depth layers for parallax effect.
	 *
	 * Layer 0 (front): Hero cathedral scene — the main visual.
	 * Layer 1 (mid):   Gothic ballroom — adds depth behind hero.
	 * Layer 2 (back):  Reflective ballroom — deep background, low opacity.
	 *
	 * depth: 0 = front (z:0), 1 = back (z:-20).
	 * parallax: movement multiplier on scroll (higher = more movement).
	 */
	'layers' => array(
		array(
			'image'    => $scenes_uri . '/love-hurts-cathedral-rose-chamber-v2.webp',
			'depth'    => 0.0,
			'parallax' => 0.2,
			'opacity'  => 1,
		),
		array(
			'image'    => $scenes_uri . '/love-hurts-gothic-ballroom.webp',
			'depth'    => 0.35,
			'parallax' => 0.5,
			'opacity'  => 0.7,
		),
		array(
			'image'    => $scenes_uri . '/love-hurts-reflective-ballroom.webp',
			'depth'    => 0.7,
			'parallax' => 0.8,
			'opacity'  => 0.4,
		),
	),

	/*
	 * Particle Systems — atmospheric effects.
	 *
	 * Crimson petals falling slowly (enchanted rose losing petals).
	 * Candle flicker points (warm gold glow).
	 * Dust beams (light through stained glass).
	 */
	'particles' => array(
		array(
			'type'    => 'petals',
			'count'   => 80,
			'color'   => '#DC143C',
			'size'    => 0.06,
			'opacity' => 0.7,
			'speed'   => 0.3,
			'bounds'  => array( 14, 12, 10 ),
		),
		array(
			'type'    => 'flicker',
			'count'   => 35,
			'color'   => '#FFB700',
			'size'    => 0.03,
			'opacity' => 0.5,
			'speed'   => 0.08,
			'bounds'  => array( 10, 8, 8 ),
		),
		array(
			'type'    => 'dust',
			'count'   => 50,
			'color'   => '#FFE4C4',
			'size'    => 0.02,
			'opacity' => 0.25,
			'speed'   => 0.12,
			'bounds'  => array( 12, 14, 12 ),
		),
	),

	/* Product data (for panel display). */
	'products' => $lh_world_products,

	/*
	 * Product placements in 3D space.
	 * Spread across the depth of the scene so products reveal as you scroll.
	 * position: [x, y, z] in world units.
	 */
	'productPlacements' => array(
		array( 'sku' => 'lh-006', 'position' => array( 3.0, 2.0, -1.0 ) ),
		array( 'sku' => 'lh-003', 'position' => array( -2.5, 1.5, -3.0 ) ),
		array( 'sku' => 'lh-005', 'position' => array( 1.0, 2.5, -6.0 ) ),
		array( 'sku' => 'lh-002', 'position' => array( -3.0, 1.8, -9.0 ) ),
		array( 'sku' => 'lh-004', 'position' => array( 2.0, 2.2, -13.0 ) ),
	),

	/*
	 * Camera Path — scroll-driven waypoints.
	 *
	 * As scroll progresses 0→1, camera moves deeper into the cathedral.
	 * Each waypoint: position (where camera IS), target (where camera LOOKS).
	 * Smooth interpolation with smoothstep between waypoints.
	 */
	'cameraPath' => array(
		// 0.0 — Opening: wide establishing shot of cathedral
		array(
			'position' => array( 0, 2.5, 8 ),
			'target'   => array( 0, 1.5, -5 ),
			'fov'      => 65,
		),
		// ~0.15 — Move into the space, enchanted rose visible
		array(
			'position' => array( 0.5, 2.8, 5 ),
			'target'   => array( 0, 2.0, -8 ),
			'fov'      => 58,
		),
		// ~0.30 — Deeper, panning slightly left
		array(
			'position' => array( -0.8, 3.0, 2 ),
			'target'   => array( 0, 2.0, -12 ),
			'fov'      => 52,
		),
		// ~0.45 — Close to rose shrine area
		array(
			'position' => array( 0.3, 2.2, -1 ),
			'target'   => array( 0, 1.8, -15 ),
			'fov'      => 48,
		),
		// ~0.60 — Deep into the staircase region
		array(
			'position' => array( -0.5, 2.8, -4 ),
			'target'   => array( 0, 2.0, -18 ),
			'fov'      => 50,
		),
		// ~0.75 — Near the reflective ballroom
		array(
			'position' => array( 0.2, 2.0, -7 ),
			'target'   => array( 0, 1.5, -20 ),
			'fov'      => 52,
		),
		// ~0.90 — Climax: close, intimate, rose dome finale
		array(
			'position' => array( 0, 1.5, -10 ),
			'target'   => array( 0, 1.0, -22 ),
			'fov'      => 58,
		),
	),

	/*
	 * Avatar Easter Egg — hidden mascot in the scene.
	 * Position matches the composited sprite in the -avatar.webp scene image.
	 */
	'avatar' => array(
		'x'          => 83.9,
		'y'          => 71.9,
		'w'          => 5.5,
		'h'          => 9.9,
		'sprite'     => $assets_uri . '/images/mascot/skyyrose-mascot-love-hurts.png',
		'introImage' => $assets_uri . '/images/mascot/skyyrose-mascot-reference.png',
	),

	/*
	 * Narrative Panels — Beast's inner monologue.
	 *
	 * Each panel triggered at a scroll position (0→1).
	 * position: left|right|center — which side of the screen.
	 * style: prose|quote|whisper — visual treatment.
	 */
	'narrativePanels' => array(
		array(
			'trigger'  => 0.05,
			'text'     => 'She never saw the thorns I grew to protect myself...',
			'position' => 'left',
			'style'    => 'whisper',
		),
		array(
			'trigger'  => 0.18,
			'text'     => 'Every petal that falls is a day closer to forever alone...',
			'subtext'  => 'The enchanted rose counts down what I cannot say.',
			'position' => 'right',
			'style'    => 'prose',
		),
		array(
			'trigger'  => 0.35,
			'text'     => 'The ballroom remembers her laughter. I remember the silence after.',
			'position' => 'center',
			'style'    => 'quote',
		),
		array(
			'trigger'  => 0.50,
			'text'     => 'Love doesn\'t hurt. Loving without being seen hurts.',
			'position' => 'left',
			'style'    => 'prose',
		),
		array(
			'trigger'  => 0.68,
			'text'     => 'The rose was never the curse. Hope was.',
			'position' => 'right',
			'style'    => 'whisper',
		),
		array(
			'trigger'  => 0.82,
			'text'     => 'In the silence between petals falling, I hear my own heart still beating.',
			'position' => 'center',
			'style'    => 'quote',
		),
		array(
			'trigger'  => 0.95,
			'text'     => 'Luxury Grows from Concrete.',
			'subtext'  => 'Love Hurts Collection',
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

	<div id="world-canvas" aria-label="<?php esc_attr_e( 'Immersive 3D experience — The Beast\'s Cathedral', 'skyyrose-flagship' ); ?>"></div>
	<div id="world-narrative" aria-live="polite"></div>

	<!-- Scroll spacer: gives scroll distance for the camera path to traverse -->
	<div class="world-scroll-spacer" aria-hidden="true"></div>

	<script type="application/json" id="world-config">
	<?php echo wp_json_encode( $world_config, JSON_UNESCAPED_SLASHES ); ?>
	</script>

	<!-- ═══ 2D Fallback (hidden when 3D active) ═══ -->
	<div class="immersive-scene immersive-love-hurts" role="region" aria-labelledby="scene-title">

		<!-- Loading Screen -->
		<?php get_template_part( 'template-parts/immersive-loader', null, array( 'world_name' => __( "The Beast's Cathedral", 'skyyrose-flagship' ) ) ); ?>

		<!-- Scene Viewport — Multi-Room Layers -->
		<div class="scene-viewport">
			<?php foreach ( $love_hurts_rooms as $index => $room ) : ?>
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
			<?php foreach ( $love_hurts_rooms as $index => $room ) : ?>
				<button
					class="room-dot<?php echo 0 === $index ? ' active' : ''; ?>"
					type="button"
					aria-pressed="<?php echo 0 === $index ? 'true' : 'false'; ?>"
					aria-label="<?php echo esc_attr( sprintf( __( 'Room %1$d of %2$d: %3$s', 'skyyrose-flagship' ), $index + 1, count( $love_hurts_rooms ), $room['name'] ) ); ?>"
				></button>
			<?php endforeach; ?>
		</div>
		<div class="room-name" aria-live="polite" aria-atomic="true"><?php echo esc_html( $love_hurts_rooms[0]['name'] ); ?></div>

		<!-- Hotspot Containers — One per room -->
		<?php foreach ( $love_hurts_rooms as $room_index => $room ) : ?>
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
			<h1 id="scene-title"><?php echo esc_html__( 'The Beast\'s Cathedral', 'skyyrose-flagship' ); ?></h1>
			<p class="scene-subtitle"><?php echo esc_html__( 'Love Hurts Collection', 'skyyrose-flagship' ); ?></p>
			<p class="scene-tagline"><?php echo esc_html__( 'Luxury Grows from Concrete.', 'skyyrose-flagship' ); ?></p>
		</div>

		<!-- Explore Full Collection CTA -->
		<div class="immersive-cta">
			<a href="<?php echo esc_url( home_url( '/collection-love-hurts/' ) ); ?>" class="immersive-cta__link">
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
				<a class="btn-view-collection" href="<?php echo esc_url( home_url( '/collection-love-hurts/' ) ); ?>">
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
				<span class="world-nav__door-label"><?php echo esc_html__( 'Enter The Garden', 'skyyrose-flagship' ); ?></span>
			</a>
			<a href="<?php echo esc_url( home_url( '/experience-signature/' ) ); ?>" class="world-nav__door">
				<img
					class="world-nav__door-image"
					src="<?php echo esc_url( get_template_directory_uri() . '/assets/scenes/signature/signature-golden-gate-showroom-lookbook.webp' ); ?>"
					alt="" loading="lazy" width="320" height="180"
				>
				<span class="world-nav__door-label"><?php echo esc_html__( 'Enter The Runway', 'skyyrose-flagship' ); ?></span>
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
