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
 * @package SkyyRose_Flagship
 * @since   6.0.0
 *
 * @param array $args {
 *     @type string $collection_slug  CSS class suffix (e.g., 'signature').
 *     @type string $collection_name  Display name (e.g., 'Signature Collection').
 *     @type string $world_name       H1 title (e.g., 'The Golden Gate Runway').
 *     @type string $tagline          Subtitle text.
 *     @type string $accent_color     CSS custom property value (e.g., '#D4AF37').
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
$collection_slug = isset( $args['collection_slug'] ) ? $args['collection_slug'] : '';
$collection_name = isset( $args['collection_name'] ) ? $args['collection_name'] : '';
$world_name      = isset( $args['world_name'] ) ? $args['world_name'] : '';
$tagline         = isset( $args['tagline'] ) ? $args['tagline'] : '';
$accent_color    = isset( $args['accent_color'] ) ? $args['accent_color'] : '#B76E79';
$collection_url  = isset( $args['collection_url'] ) ? $args['collection_url'] : '';
$rooms           = isset( $args['rooms'] ) ? $args['rooms'] : array();
$room_count      = count( $rooms );
$first_room_name = $room_count > 0 ? $rooms[0]['name'] : '';
?>

<!-- ═══ Immersive Scene: <?php echo esc_html( $world_name ); ?> ═══ -->
<div class="immersive-scene immersive-<?php echo esc_attr( $collection_slug ); ?>"
     role="region"
     aria-labelledby="scene-title"
     style="--accent-color: <?php echo esc_attr( $accent_color ); ?>;">

	<!-- Loading Screen -->
	<?php get_template_part( 'template-parts/immersive-loader', null, array( 'world_name' => $world_name ) ); ?>

	<!-- Scene Viewport — Composited AI Scene Images -->
	<div class="scene-viewport">
		<?php foreach ( $rooms as $index => $room ) : ?>
			<div class="scene-layer<?php echo 0 === $index ? ' active' : ''; ?>"
			     data-room-name="<?php echo esc_attr( $room['name'] ); ?>">
				<?php if ( ! empty( $room['image'] ) ) : ?>
					<img src="<?php echo esc_url( get_template_directory_uri() . '/assets/images/immersive/' . $room['image'] ); ?>"
					     alt="<?php echo esc_attr( $room['name'] ); ?>"
					     <?php echo 0 === $index ? 'fetchpriority="high"' : 'loading="lazy"'; ?>>
				<?php endif; ?>
			</div>
		<?php endforeach; ?>
	</div>

	<!-- Atmospheric Overlays -->
	<div class="scene-vignette" aria-hidden="true"></div>
	<div class="scene-film-grain" aria-hidden="true"></div>

	<!-- Room Navigation Arrows -->
	<div class="room-nav room-nav-prev">
		<button class="room-nav-btn" type="button" aria-label="<?php esc_attr_e( 'Previous room', 'skyyrose-flagship' ); ?>">
			<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><polyline points="15 18 9 12 15 6"></polyline></svg>
		</button>
	</div>
	<div class="room-nav room-nav-next">
		<button class="room-nav-btn" type="button" aria-label="<?php esc_attr_e( 'Next room', 'skyyrose-flagship' ); ?>">
			<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><polyline points="9 18 15 12 9 6"></polyline></svg>
		</button>
	</div>

	<!-- Room Indicators -->
	<div class="room-indicators" role="group" aria-label="<?php esc_attr_e( 'Room selector', 'skyyrose-flagship' ); ?>">
		<?php foreach ( $rooms as $index => $room ) : ?>
			<button
				class="room-dot<?php echo 0 === $index ? ' active' : ''; ?>"
				type="button"
				aria-pressed="<?php echo 0 === $index ? 'true' : 'false'; ?>"
				aria-label="<?php echo esc_attr( sprintf(
					/* translators: 1: room number, 2: total rooms, 3: room name */
					__( 'Room %1$d of %2$d: %3$s', 'skyyrose-flagship' ),
					$index + 1,
					$room_count,
					$room['name']
				) ); ?>"
			></button>
		<?php endforeach; ?>
	</div>
	<div class="room-name" aria-live="polite" aria-atomic="true"><?php echo esc_html( $first_room_name ); ?></div>

	<!-- Hotspot Containers — One per room -->
	<?php foreach ( $rooms as $room_index => $room ) : ?>
		<div class="hotspot-container"<?php echo 0 !== $room_index ? ' aria-hidden="true" inert style="display:none;"' : ''; ?>>
			<?php foreach ( $room['products'] as $product ) :
				if ( empty( $product ) ) {
					continue;
				}
			?>
				<a
					href="<?php echo esc_url( $product['url'] ); ?>"
					class="hotspot<?php echo ! empty( $product['prop'] ) ? ' hotspot--prop-' . esc_attr( $product['prop'] ) : ''; ?>"
					style="left: <?php echo esc_attr( $product['left'] ); ?>%; top: <?php echo esc_attr( $product['top'] ); ?>%;"
					data-product-id="<?php echo esc_attr( $product['id'] ); ?>"
					data-product-sku="<?php echo esc_attr( $product['id'] ); ?>"
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

	<!-- Scene Title -->
	<div class="scene-title-overlay">
		<h1 id="scene-title"><?php echo esc_html( $world_name ); ?></h1>
		<p class="scene-subtitle"><?php echo esc_html( $collection_name ); ?></p>
		<?php if ( $tagline ) : ?>
			<p class="scene-tagline"><?php echo esc_html( $tagline ); ?></p>
		<?php endif; ?>
	</div>

	<!-- Explore Full Collection CTA -->
	<?php if ( $collection_url ) : ?>
		<div class="immersive-cta">
			<a href="<?php echo esc_url( $collection_url ); ?>" class="immersive-cta__link">
				<span class="immersive-cta__text"><?php esc_html_e( 'Explore the Full Collection', 'skyyrose-flagship' ); ?></span>
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
	<button class="product-panel-close" type="button" aria-label="<?php esc_attr_e( 'Close product details', 'skyyrose-flagship' ); ?>">&times;</button>
	<div class="product-panel-inner">
		<div class="product-panel-thumb">
			<img src="<?php echo esc_url( get_template_directory_uri() . '/assets/images/placeholder-product.jpg' ); ?>"
			     alt="<?php esc_attr_e( 'Product preview', 'skyyrose-flagship' ); ?>"
			     data-fallback="<?php echo esc_url( get_template_directory_uri() . '/assets/images/placeholder-product.jpg' ); ?>">
		</div>
		<div class="product-panel-info">
			<p class="product-panel-collection"></p>
			<h3 class="product-panel-name" id="product-panel-name"><?php esc_html_e( 'Product Details', 'skyyrose-flagship' ); ?></h3>
			<p class="product-panel-prop"></p>
			<p class="product-panel-price"></p>
			<div class="product-panel-sizes" role="group" aria-label="<?php esc_attr_e( 'Available sizes', 'skyyrose-flagship' ); ?>"></div>
			<div class="product-panel-actions">
				<button class="btn-add-to-cart" type="button"><?php esc_html_e( 'Pre-Order Now', 'skyyrose-flagship' ); ?></button>
				<a class="btn-view-details" href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>"><?php esc_html_e( 'View Details', 'skyyrose-flagship' ); ?></a>
			</div>
			<?php if ( $collection_url ) : ?>
				<a class="btn-view-collection" href="<?php echo esc_url( $collection_url ); ?>">
					<?php esc_html_e( 'View Full Collection', 'skyyrose-flagship' ); ?>
					<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
						<path d="M5 12h14"/>
						<path d="m12 5 7 7-7 7"/>
					</svg>
				</a>
			<?php endif; ?>
		</div>
	</div>
</div>

<!-- Cross-Collection Tab Bar -->
<?php get_template_part( 'template-parts/immersive-tab-bar', null, array( 'active_slug' => $collection_slug ) ); ?>

<!-- Cinematic Mode Toggle -->
<?php get_template_part( 'template-parts/cinematic-toggle' ); ?>
