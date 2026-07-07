<?php
/**
 * Immersive Scene — Shared Room Structure
 *
 * Renders the full-viewport immersive experience:
 * loading screen, room viewport with composited AI scene images,
 * hotspot beacons, glassmorphism product panel, room
 * navigation, title overlay, cinematic toggle, and tab bar.
 *
 * Called via get_template_part() from each collection's
 * immersive page template with $args containing room data.
 *
 * @package SkyyRose
 * @since   6.0.0
 *
 * @param array $args {
 *     @type string $collection_slug  CSS class suffix (e.g., 'signature').
 *     @type string $collection_name  Display name (e.g., 'Signature Collection').
 *     @type string $world_name       H1 title (e.g., 'The Golden Gate Runway').
 *     @type string $tagline          Subtitle text.
 *     @type string $collection_url   CTA link to collection page.
 *     @type array  $rooms            Room data — see structure below.
 * }
 *
 * Room structure:
 *   array(
 *       'name'     => 'The Golden Gate',
 *       'image'    => 'scene-signature-golden-gate.webp',
 *       'products' => array( ... hotspot product arrays ... ),
 *   )
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

// Extract args with defaults.
$collection_slug = isset( $args['collection_slug'] ) ? sanitize_key( $args['collection_slug'] ) : '';
$collection_name = isset( $args['collection_name'] ) ? $args['collection_name'] : '';
$world_name      = isset( $args['world_name'] ) ? $args['world_name'] : '';
$tagline         = isset( $args['tagline'] ) ? $args['tagline'] : '';
$collection_url  = isset( $args['collection_url'] ) ? $args['collection_url'] : '';
$rooms           = isset( $args['rooms'] ) && is_array( $args['rooms'] ) ? $args['rooms'] : array();
$room_count      = count( $rooms );
$first_room_name = $room_count > 0 && isset( $rooms[0]['name'] ) ? $rooms[0]['name'] : '';

/*
 * Embedded mode (structural remediation WS3): the scene renders as the
 * opening experience layer INSIDE a /collections/{slug}/ page rather than
 * as a standalone full-page world. Embedded mode:
 *   - skips the loading screen, tab bar, cinematic toggle, and the
 *     "Explore the Full Collection" CTA (the collection is this page);
 *   - lazy-loads every scene image (the collection hero is the LCP element);
 *   - demotes the scene heading from <h1> to <h2> (the page owns the h1).
 */
$embedded    = ! empty( $args['embedded'] );
$scene_h_tag = $embedded ? 'h2' : 'h1';
?>

<!-- ═══ Immersive Scene: <?php echo esc_html( $world_name ); ?> ═══ -->
<div class="immersive-scene immersive-<?php echo esc_attr( $collection_slug ); ?>"
	data-collection="<?php echo esc_attr( $collection_slug ); ?>"
	role="region"
	aria-labelledby="scene-title">

	<!-- Loading Screen (standalone only — embedded scenes reveal in-flow) -->
	<?php
	if ( ! $embedded ) {
		get_template_part( 'template-parts/immersive/loader', null, array( 'world_name' => $world_name ) );
	}
	?>

	<!-- Scene Viewport — Composited AI Scene Images -->
	<div class="scene-viewport">
		<?php
		foreach ( $rooms as $index => $room ) :
			$room_name  = isset( $room['name'] ) ? $room['name'] : '';
			$room_image = isset( $room['image'] ) ? $room['image'] : '';
			?>
			<?php
				$scene_image_path   = get_theme_file_path( 'assets/images/immersive/' . $room_image );
				$scene_image_exists = ! empty( $room_image ) && file_exists( $scene_image_path );
			?>
			<div class="scene-layer<?php echo 0 === $index ? ' active' : ''; ?><?php echo ! $scene_image_exists ? ' scene-layer--missing' : ''; ?>"
				data-room-name="<?php echo esc_attr( $room_name ); ?>"
				<?php if ( ! $scene_image_exists ) : ?>
					data-missing-scene="<?php echo esc_attr( $room_image ); ?>"
				<?php endif; ?>>
				<?php if ( $scene_image_exists ) : ?>
					<img src="<?php echo esc_url( get_template_directory_uri() . '/assets/images/immersive/' . $room_image ); ?>"
						alt="<?php echo esc_attr( $room_name ); ?>"
						width="1344"
						height="896"
						<?php echo ( 0 === $index && ! $embedded ) ? 'fetchpriority="high"' : 'loading="lazy"'; ?>
						data-warp>
				<?php else : ?>
					<?php
					/*
					 * Branded empty state — immersive-core.css §7 (.scene-layer--missing)
					 * already paints an accent-tinted gradient here so the room never
					 * renders blank; this caption makes the state read as an intentional
					 * "next chapter" rather than a broken image.
					 * aria-hidden: the room name is already announced via the
					 * room-indicator buttons and the live .room-name region — this is
					 * a sighted-only decorative label, not new information.
					 */
					?>
					<div class="scene-layer-fallback" aria-hidden="true">
						<span class="scene-layer-fallback__name"><?php echo esc_html( $room_name ); ?></span>
						<span class="scene-layer-fallback__note"><?php esc_html_e( 'Coming soon.', 'skyyrose' ); ?></span>
					</div>
				<?php endif; ?>
			</div>
		<?php endforeach; ?>
	</div>

	<!-- Atmospheric Overlays -->
	<div class="scene-vignette" aria-hidden="true"></div>
	<div class="scene-film-grain" aria-hidden="true"></div>

	<!-- Room Navigation Arrows -->
	<div class="room-nav room-nav-prev">
		<button class="room-nav-btn" type="button" aria-label="<?php esc_attr_e( 'Previous room', 'skyyrose' ); ?>">
			<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><polyline points="15 18 9 12 15 6"></polyline></svg>
		</button>
	</div>
	<div class="room-nav room-nav-next">
		<button class="room-nav-btn" type="button" aria-label="<?php esc_attr_e( 'Next room', 'skyyrose' ); ?>">
			<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><polyline points="9 18 15 12 9 6"></polyline></svg>
		</button>
	</div>

	<!-- Room Indicators -->
	<div class="room-indicators stagger-grid" role="group" aria-label="<?php esc_attr_e( 'Room selector', 'skyyrose' ); ?>">
		<?php foreach ( $rooms as $index => $room ) : ?>
			<button
				class="room-dot<?php echo 0 === $index ? ' active' : ''; ?>"
				type="button"
				aria-pressed="<?php echo 0 === $index ? 'true' : 'false'; ?>"
				aria-label="
				<?php
				echo esc_attr(
					sprintf(
					/* translators: 1: room number, 2: total rooms, 3: room name */
						__( 'Room %1$d of %2$d: %3$s', 'skyyrose' ),
						$index + 1,
						$room_count,
						$room['name']
					)
				);
				?>
				"
			></button>
		<?php endforeach; ?>
	</div>
	<div class="room-name rv-blur-down" aria-live="polite" aria-atomic="true"><?php echo esc_html( $first_room_name ); ?></div>

	<!-- Hotspot Containers — One per room -->
	<?php foreach ( $rooms as $room_index => $room ) : ?>
		<div class="hotspot-container"<?php echo 0 !== $room_index ? ' aria-hidden="true" inert style="display:none;"' : ''; ?>>
			<?php
			foreach ( $room['products'] as $product ) :
				if ( empty( $product ) ) {
					continue;
				}
				?>
				<?php
					$p_id  = isset( $product['id'] ) ? $product['id'] : '';
					$p_sku = isset( $product['sku'] ) ? $product['sku'] : $p_id;
					$p_wc  = isset( $product['wc_id'] ) ? (int) $product['wc_id'] : 0;
				?>
				<a
					href="<?php echo esc_url( isset( $product['url'] ) ? $product['url'] : '' ); ?>"
					class="hotspot<?php echo ! empty( $product['prop'] ) ? ' hotspot--prop-' . esc_attr( $product['prop'] ) : ''; ?>"
					style="left: <?php echo esc_attr( isset( $product['left'] ) ? $product['left'] : '50' ); ?>%; top: <?php echo esc_attr( isset( $product['top'] ) ? $product['top'] : '50' ); ?>%;"
					data-product-id="<?php echo esc_attr( $p_id ); ?>"
					data-product-sku="<?php echo esc_attr( $p_sku ); ?>"
					<?php
					if ( $p_wc > 0 ) :
						?>
						data-product-wc-id="<?php echo esc_attr( $p_wc ); ?>"<?php endif; ?>
					data-product-name="<?php echo esc_attr( $product['name'] ); ?>"
					data-product-price="<?php echo esc_attr( $product['price'] ); ?>"
					data-product-image="<?php echo esc_url( $product['image'] ); ?>"
					data-product-collection="<?php echo esc_attr( $product['collection'] ); ?>"
					data-product-sizes="<?php echo esc_attr( $product['sizes'] ); ?>"
					data-product-url="<?php echo esc_url( $product['url'] ); ?>"
					<?php if ( ! empty( $product['prop'] ) ) : ?>
						data-prop="<?php echo esc_attr( $product['prop'] ); ?>"
						data-prop-label="<?php echo esc_attr( $product['prop_label'] ); ?>"
					<?php endif; ?>
					aria-label="<?php echo esc_attr( $product['name'] . ' — ' . $product['price'] ); ?>"
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

	<?php
	// Per-collection lockup (hero title is an image, never type-rendered).
	$lockup_map = array(
		'black-rose'   => array(
			'dir'     => 'hero-overlays',
			'base'    => 'br-brand-script-logotype',
			'has_png' => true,
			'alt'     => __( 'Black Rose', 'skyyrose' ),
		),
		'love-hurts'   => array(
			'dir'     => 'hero-overlays',
			'base'    => 'lh-logo-combined',
			'has_png' => true,
			'alt'     => __( 'Love Hurts', 'skyyrose' ),
		),
		'signature'    => array(
			'dir'     => 'hero-overlays',
			'base'    => 'sig-brand-skyy-rose-gold',
			'has_png' => true,
			'alt'     => __( 'Signature', 'skyyrose' ),
		),
		'kids-capsule' => array(
			'dir'     => 'logos',
			'base'    => 'sr-monogram-rose-gold',
			'has_png' => false,
			'alt'     => __( 'Kids Capsule', 'skyyrose' ),
		),
	);

	$lockup_info  = isset( $lockup_map[ $collection_slug ] ) ? $lockup_map[ $collection_slug ] : null;
	$img_base_uri = get_template_directory_uri() . '/assets/images/';
	?>

	<!-- Scene Title -->
	<div class="scene-title-overlay">
		<?php if ( $lockup_info ) : ?>
			<picture class="scene-lockup">
				<source srcset="<?php echo esc_url( $img_base_uri . $lockup_info['dir'] . '/' . $lockup_info['base'] . '.avif' ); ?>" type="image/avif">
				<source srcset="<?php echo esc_url( $img_base_uri . $lockup_info['dir'] . '/' . $lockup_info['base'] . '.webp' ); ?>" type="image/webp">
				<?php
				$lockup_loading = $embedded ? 'loading="lazy"' : 'fetchpriority="high" loading="eager"';
				?>
				<?php if ( $lockup_info['has_png'] ) : ?>
					<img src="<?php echo esc_url( $img_base_uri . $lockup_info['dir'] . '/' . $lockup_info['base'] . '.png' ); ?>"
						alt="<?php echo esc_attr( $lockup_info['alt'] ); ?>" width="480"
						<?php echo $lockup_loading; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- literal attribute pair. ?> class="scene-lockup__img">
				<?php else : ?>
					<img src="<?php echo esc_url( $img_base_uri . $lockup_info['dir'] . '/' . $lockup_info['base'] . '.webp' ); ?>"
						alt="<?php echo esc_attr( $lockup_info['alt'] ); ?>" width="480"
						<?php echo $lockup_loading; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- literal attribute pair. ?> class="scene-lockup__img">
				<?php endif; ?>
			</picture>
			<?php
			/*
			 * No-JS fallback: .scene-lockup starts at opacity:0 in
			 * immersive-core.css, awaiting the GSAP intro reveal
			 * (immersive-core.js). If JS never runs (blocked, failed,
			 * disabled) the lockup would stay invisible forever — force it
			 * visible, matching the reduced-motion override already in
			 * immersive-core.css §6. Same idiom as header.php / front-page.php.
			 */
			?>
			<noscript><style>.scene-lockup{opacity:1!important}</style></noscript>
		<?php endif; ?>
		<!-- Hairline accent rule: JS queries .scene-hairline; CSS sizes it (width:120px) in immersive-core.css. The intro clones it into the overlay and GSAP animates scaleX 0→1 in step 3. -->
		<div class="scene-hairline" aria-hidden="true"></div>
		<<?php echo esc_html( $scene_h_tag ); ?> id="scene-title" class="screen-reader-text"><?php echo esc_html( $collection_name ); ?></<?php echo esc_html( $scene_h_tag ); ?>>
		<p class="scene-subtitle rv-clip-left"><?php echo esc_html( $collection_name ); ?></p>
		<?php if ( $tagline ) : ?>
			<p class="scene-tagline rv-blur"><?php echo esc_html( $tagline ); ?></p>
		<?php endif; ?>
	</div>

	<!-- Explore Full Collection CTA (standalone only) -->
	<?php if ( $collection_url && ! $embedded ) : ?>
		<div class="immersive-cta">
			<a href="<?php echo esc_url( $collection_url ); ?>" class="immersive-cta__link btn-sweep rv-clip-up">
				<span class="immersive-cta__text"><?php esc_html_e( 'Explore the Full Collection', 'skyyrose' ); ?></span>
				<svg class="immersive-cta__arrow" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
					<path d="M5 12h14"/>
					<path d="m12 5 7 7-7 7"/>
				</svg>
			</a>
		</div>
	<?php endif; ?>

</div><!-- .immersive-scene -->

<!-- Product Detail Panel (Glassmorphism Slide-Up) -->
<div class="product-panel-overlay" aria-hidden="true"></div>
<div class="product-panel" role="dialog" aria-modal="true" aria-hidden="true" inert aria-labelledby="product-panel-name" tabindex="-1">
	<button class="product-panel-close" type="button" aria-label="<?php esc_attr_e( 'Close product details', 'skyyrose' ); ?>">&times;</button>
	<div class="product-panel-inner">
		<div class="product-panel-thumb">
			<img src="<?php echo esc_url( get_template_directory_uri() . '/assets/images/placeholder-product.jpg' ); ?>"
				alt="<?php esc_attr_e( 'Product preview', 'skyyrose' ); ?>"
				width="400"
				height="533"
				data-fallback="<?php echo esc_url( get_template_directory_uri() . '/assets/images/placeholder-product.jpg' ); ?>"
				data-warp>
		</div>
		<div class="product-panel-info">
			<p class="product-panel-collection"></p>
			<h3 class="product-panel-name" id="product-panel-name"><?php esc_html_e( 'Product Details', 'skyyrose' ); ?></h3>
			<p class="product-panel-prop"></p>
			<p class="product-panel-price"></p>
			<div class="product-panel-sizes" role="group" aria-label="<?php esc_attr_e( 'Available sizes', 'skyyrose' ); ?>"></div>
			<div class="product-panel-actions">
				<button class="btn-add-to-cart" type="button"><?php esc_html_e( 'Pre-Order Now', 'skyyrose' ); ?></button>
				<a class="btn-view-details" href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>"><?php esc_html_e( 'View Details', 'skyyrose' ); ?></a>
			</div>
			<?php if ( $collection_url ) : ?>
				<a class="btn-view-collection" href="<?php echo esc_url( $collection_url ); ?>">
					<?php esc_html_e( 'View Full Collection', 'skyyrose' ); ?>
					<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
						<path d="M5 12h14"/>
						<path d="m12 5 7 7-7 7"/>
					</svg>
				</a>
			<?php endif; ?>
		</div>
	</div>
</div>

<?php if ( ! $embedded ) : ?>
	<!-- Cross-Collection Tab Bar -->
	<?php get_template_part( 'template-parts/immersive/tab-bar', null, array( 'active_slug' => $collection_slug ) ); ?>

	<!-- Cinematic Mode Toggle -->
	<?php get_template_part( 'template-parts/immersive/cinematic-toggle' ); ?>
<?php endif; ?>
