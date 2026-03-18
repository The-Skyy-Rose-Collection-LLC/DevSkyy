<?php
/**
 * Template Name: Immersive - Black Rose
 *
 * "The Bay Bridge" — East Oakland rooftop, night skyline, Bay Bridge glow.
 * Street luxury. "Luxury Grows from Concrete."
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
				'prop_label' => __( 'Draped over marble garden statue', 'skyyrose-flagship' ),
			) ),
			skyyrose_immersive_product( 'br-005', array(
				'left'       => '38',
				'top'        => '50',
				'prop'       => 'fountain-edge',
				'prop_label' => __( 'Folded on fountain edge', 'skyyrose-flagship' ),
			) ),
			skyyrose_immersive_product( 'br-002', array(
				'left'       => '62',
				'top'        => '55',
				'prop'       => 'topiary-base',
				'prop_label' => __( 'Folded at base of rose topiary', 'skyyrose-flagship' ),
			) ),
			skyyrose_immersive_product( 'br-007', array(
				'left'       => '82',
				'top'        => '48',
				'prop'       => 'statue-pedestal',
				'prop_label' => __( 'Draped over statue pedestal', 'skyyrose-flagship' ),
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
				'prop_label' => __( 'Displayed inside iron gazebo', 'skyyrose-flagship' ),
			) ),
			skyyrose_immersive_product( 'br-001', array(
				'left'       => '55',
				'top'        => '35',
				'prop'       => 'hedge-arch',
				'prop_label' => __( 'Hanging from rose hedge archway', 'skyyrose-flagship' ),
			) ),
			skyyrose_immersive_product( 'br-003', array(
				'left'       => '72',
				'top'        => '50',
				'prop'       => 'cobblestone-bench',
				'prop_label' => __( 'Draped over cobblestone garden bench', 'skyyrose-flagship' ),
			) ),
		),
	),
);

// Remove empty entries (unpublished products filtered by skyyrose_immersive_product()).
foreach ( $black_rose_rooms as &$room ) {
	$room['products'] = array_values( array_filter( $room['products'] ) );
}
unset( $room );

/* ─────────────────────────────────────────────────────────
   3D World Config — "The Bay Bridge"

   Scroll-driven Three.js experience:
   - 2 scene images as parallax depth layers (rooftop garden → avatar reveal)
   - Camera path through East Oakland rooftop at night
   - Black rose petals, silver city bokeh, bay fog particles
   - 7 product hotspots in 3D space
   - "Luxury Grows from Concrete" narrative panels
   ───────────────────────────────────────────────────────── */

$assets_uri   = get_template_directory_uri() . '/assets';
$scenes_uri   = $assets_uri . '/scenes/black-rose';
$products_uri = $assets_uri . '/images/products';

// Build product data for 3D world — primary BR lineup (br-001 through br-007).
$br_world_products = array();
$br_world_skus     = array( 'br-001', 'br-002', 'br-003', 'br-004', 'br-005', 'br-006', 'br-007' );

foreach ( $br_world_skus as $sku ) {
	$p = function_exists( 'skyyrose_get_product' ) ? skyyrose_get_product( $sku ) : null;
	if ( ! $p ) {
		continue;
	}
	$img = ! empty( $p['front_model_image'] ) ? $p['front_model_image'] : $p['image'];
	$br_world_products[] = array(
		'sku'   => $sku,
		'name'  => $p['name'],
		'price' => number_format( (float) $p['price'], 0 ),
		'image' => get_theme_file_uri( $img ),
		'sizes' => array_map( 'trim', explode( '|', $p['sizes'] ) ),
	);
}

$world_config = array(
	'collection'  => 'black-rose',
	'bgColor'     => '0x0a0a0a',
	'accentColor' => '#C0C0C0',

	/*
	 * Scene Layers — 2 depth layers for parallax effect.
	 *
	 * Layer 0 (front): Rooftop garden scene — main visual.
	 * Layer 1 (back):  Avatar version — easter egg hidden in background.
	 *
	 * depth: 0 = front (z:0), 1 = back (z:-20).
	 * parallax: movement multiplier on scroll (higher = more movement).
	 */
	'layers' => array(
		array(
			'image'    => $scenes_uri . '/black-rose-rooftop-garden-lookbook.webp',
			'depth'    => 0.0,
			'parallax' => 0.2,
			'opacity'  => 1,
		),
		array(
			'image'    => $scenes_uri . '/black-rose-rooftop-garden-v2-avatar.webp',
			'depth'    => 0.6,
			'parallax' => 0.7,
			'opacity'  => 0.5,
		),
	),

	/*
	 * Particle Systems — atmospheric effects.
	 *
	 * Black rose petals drifting slowly (East Bay nights).
	 * City bokeh points (rose gold glow from skyline).
	 * Bay fog (water mist rolling in from the bay).
	 */
	'particles' => array(
		array(
			'type'    => 'petals',
			'count'   => 60,
			'color'   => '#1a1a2e',
			'size'    => 0.05,
			'opacity' => 0.6,
			'speed'   => 0.25,
			'bounds'  => array( 14, 12, 10 ),
		),
		array(
			'type'    => 'bokeh',
			'count'   => 40,
			'color'   => '#B76E79',
			'size'    => 0.04,
			'opacity' => 0.35,
			'speed'   => 0.04,
			'bounds'  => array( 16, 10, 12 ),
		),
		array(
			'type'    => 'fog',
			'count'   => 30,
			'color'   => '#C0C0C0',
			'size'    => 0.08,
			'opacity' => 0.15,
			'speed'   => 0.06,
			'bounds'  => array( 18, 6, 14 ),
		),
	),

	/* Product data (for panel display). */
	'products' => $br_world_products,

	/*
	 * Product placements in 3D space.
	 * Spread across the depth of the scene so products reveal as you scroll.
	 * position: [x, y, z] in world units.
	 */
	'productPlacements' => array(
		array( 'sku' => 'br-006', 'position' => array( -3.0, 2.5, -1.0 ) ),
		array( 'sku' => 'br-004', 'position' => array( 2.5, 2.0, -3.0 ) ),
		array( 'sku' => 'br-002', 'position' => array( -2.0, 1.8, -6.0 ) ),
		array( 'sku' => 'br-007', 'position' => array( 3.0, 1.5, -8.0 ) ),
		array( 'sku' => 'br-001', 'position' => array( -1.5, 2.2, -11.0 ) ),
		array( 'sku' => 'br-005', 'position' => array( 1.0, 2.0, -14.0 ) ),
		array( 'sku' => 'br-003', 'position' => array( 0, 2.5, -17.0 ) ),
	),

	/*
	 * Camera Path — scroll-driven waypoints.
	 *
	 * As scroll progresses 0→1, camera moves across the East Bay rooftop
	 * toward the Bay Bridge horizon. Bay lights bloom in the background.
	 */
	'cameraPath' => array(
		// 0.0 — Street level, looking up at rooftop / city sky
		array(
			'position' => array( 0, 1.5, 8 ),
			'target'   => array( 0, 3.0, -3 ),
			'fov'      => 70,
		),
		// ~0.15 — Rising, Bay Bridge faint in background
		array(
			'position' => array( -0.5, 2.5, 5 ),
			'target'   => array( 0, 2.5, -6 ),
			'fov'      => 62,
		),
		// ~0.30 — Moving across the rooftop
		array(
			'position' => array( 0.8, 3.0, 2 ),
			'target'   => array( 0, 2.0, -9 ),
			'fov'      => 55,
		),
		// ~0.45 — Mid-scene, close to products
		array(
			'position' => array( -0.3, 2.5, -1 ),
			'target'   => array( 0, 2.0, -12 ),
			'fov'      => 50,
		),
		// ~0.60 — Deep in, fog rolling in from water
		array(
			'position' => array( 0.5, 2.0, -4 ),
			'target'   => array( 0, 2.0, -15 ),
			'fov'      => 52,
		),
		// ~0.75 — Near back, city below visible
		array(
			'position' => array( -0.2, 2.5, -7 ),
			'target'   => array( 0, 1.8, -18 ),
			'fov'      => 54,
		),
		// ~0.95 — Climax: edge of rooftop, city lights spread below
		array(
			'position' => array( 0, 2.0, -10 ),
			'target'   => array( 0, 1.5, -20 ),
			'fov'      => 60,
		),
	),

	/*
	 * Avatar Easter Egg — hidden mascot in the scene.
	 * Position matches the composited sprite in the -avatar.webp scene image.
	 */
	'avatar' => array(
		'x'          => 12.0,
		'y'          => 68.0,
		'w'          => 5.0,
		'h'          => 9.0,
		'walkSide'   => 'left',
		'sprite'     => $assets_uri . '/images/mascot/skyyrose-mascot-black-rose.png',
		'introImage' => $assets_uri . '/images/mascot/skyyrose-mascot-reference.png',
	),

	/*
	 * Narrative Panels — "Luxury Grows from Concrete" story.
	 *
	 * Each panel triggered at a scroll position (0→1).
	 * position: left|right|center — which side of the screen.
	 * style: prose|quote|whisper — visual treatment.
	 */
	'narrativePanels' => array(
		array(
			'trigger'  => 0.05,
			'text'     => 'Concrete is where we are planted. Not where we\'re limited.',
			'position' => 'left',
			'style'    => 'whisper',
		),
		array(
			'trigger'  => 0.18,
			'text'     => 'Every stitch is a story. Every hoodie, a home.',
			'subtext'  => 'Black Rose Collection — East Bay.',
			'position' => 'right',
			'style'    => 'prose',
		),
		array(
			'trigger'  => 0.35,
			'text'     => 'The Bay raised us. The streets schooled us. This is what happened after.',
			'position' => 'center',
			'style'    => 'quote',
		),
		array(
			'trigger'  => 0.50,
			'text'     => 'They said luxury wasn\'t for us. We said: watch.',
			'position' => 'left',
			'style'    => 'prose',
		),
		array(
			'trigger'  => 0.68,
			'text'     => 'From the rooftop you can see the bridge and the concrete. Both made us.',
			'position' => 'right',
			'style'    => 'whisper',
		),
		array(
			'trigger'  => 0.82,
			'text'     => 'Black Rose doesn\'t bloom in gardens. It blooms through asphalt.',
			'position' => 'center',
			'style'    => 'quote',
		),
		array(
			'trigger'  => 0.95,
			'text'     => 'Luxury Grows from Concrete.',
			'subtext'  => 'Black Rose Collection',
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

	<div id="world-canvas" aria-label="<?php esc_attr_e( 'Immersive 3D experience — The Bay Bridge', 'skyyrose-flagship' ); ?>"></div>
	<div id="world-narrative" aria-live="polite"></div>

	<!-- Scroll spacer: gives scroll distance for the camera path to traverse -->
	<div class="world-scroll-spacer" aria-hidden="true"></div>

	<script type="application/json" id="world-config">
	<?php echo wp_json_encode( $world_config, JSON_UNESCAPED_SLASHES ); ?>
	</script>

	<!-- ═══ 2D Fallback (hidden when 3D active) ═══ -->
	<div class="immersive-scene immersive-black-rose" role="region" aria-labelledby="scene-title">

		<!-- Loading Screen -->
		<?php get_template_part( 'template-parts/immersive-loader', null, array( 'world_name' => __( 'The Bay Bridge', 'skyyrose-flagship' ) ) ); ?>

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

		<!-- Hotspot Containers — One per room -->
		<?php foreach ( $black_rose_rooms as $room_index => $room ) : ?>
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
			<h1 id="scene-title"><?php echo esc_html__( 'The Bay Bridge', 'skyyrose-flagship' ); ?></h1>
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
				<a class="btn-view-collection" href="<?php echo esc_url( home_url( '/collection-black-rose/' ) ); ?>">
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
			<a href="<?php echo esc_url( home_url( '/experience-love-hurts/' ) ); ?>" class="world-nav__door">
				<img
					class="world-nav__door-image"
					src="<?php echo esc_url( get_template_directory_uri() . '/assets/scenes/love-hurts/love-hurts-cathedral-rose-chamber-lookbook.webp' ); ?>"
					alt="" loading="lazy" width="320" height="180"
				>
				<span class="world-nav__door-label"><?php echo esc_html__( 'Enter The Cathedral', 'skyyrose-flagship' ); ?></span>
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
