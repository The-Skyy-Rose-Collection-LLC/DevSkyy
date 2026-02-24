<?php
/**
 * Template Name: Immersive - Love Hurts
 *
 * "The Ballroom" — Baroque ballrooms, gothic cathedrals, enchanted rose
 * shrines, and crimson throne rooms. drakerelated.com-style immersive
 * experience: full-viewport rooms, pulsing beacon hotspots, smooth
 * room-to-room transitions.
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
 * 4 rooms from the Love Hurts collection, each a full-viewport scene.
 * Products positioned on contextual props within each ballroom/chamber.
 */
$love_hurts_rooms = array(
	// Room 1 — Cathedral Rose Chamber
	array(
		'name'     => esc_html__( 'Cathedral Rose Chamber', 'skyyrose-flagship' ),
		'image'    => get_template_directory_uri() . '/assets/scenes/love-hurts/love-hurts-cathedral-rose-chamber.png',
		'alt'      => esc_attr__( 'Gothic cathedral with enchanted rose under glass dome, stained glass windows, candelabras, and crimson petals', 'skyyrose-flagship' ),
		'products' => array(
			array(
				'id'         => 'lh-004',
				'name'       => esc_html__( 'Love Hurts Varsity Jacket', 'skyyrose-flagship' ),
				'price'      => '$265',
				'collection' => esc_html__( 'Love Hurts Collection', 'skyyrose-flagship' ),
				'sizes'      => 'S,M,L,XL,2XL,3XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/lh-004-varsity.jpg',
				'url'        => '/?product_id=lh-004',
				'left'       => '35',
				'top'        => '42',
				'prop'       => 'glass-dome',
				'prop_label' => esc_html__( 'Draped beside enchanted rose dome', 'skyyrose-flagship' ),
			),
			array(
				'id'         => 'lh-005',
				'name'       => esc_html__( 'Love Hurts Bomber Jacket', 'skyyrose-flagship' ),
				'price'      => '$245',
				'collection' => esc_html__( 'Love Hurts Collection', 'skyyrose-flagship' ),
				'sizes'      => 'S,M,L,XL,2XL,3XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/lh-005-bomber.jpg',
				'url'        => '/?product_id=lh-005',
				'left'       => '68',
				'top'        => '38',
				'prop'       => 'candelabra',
				'prop_label' => esc_html__( 'Hung from gothic candelabra stand', 'skyyrose-flagship' ),
			),
		),
	),
	// Room 2 — Gothic Ballroom
	array(
		'name'     => esc_html__( 'Gothic Ballroom', 'skyyrose-flagship' ),
		'image'    => get_template_directory_uri() . '/assets/scenes/love-hurts/love-hurts-gothic-ballroom.png',
		'alt'      => esc_attr__( 'Gothic chamber with rose under glass dome, purple draped fabrics, pink petals, and candlelit atmosphere', 'skyyrose-flagship' ),
		'products' => array(
			array(
				'id'         => 'lh-002',
				'name'       => esc_html__( 'Love Hurts Joggers', 'skyyrose-flagship' ),
				'price'      => '$95',
				'collection' => esc_html__( 'Love Hurts Collection', 'skyyrose-flagship' ),
				'sizes'      => 'S,M,L,XL,2XL,3XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/lh-002-joggers.jpg',
				'url'        => '/?product_id=lh-002',
				'left'       => '55',
				'top'        => '48',
				'prop'       => 'velvet-drape',
				'prop_label' => esc_html__( 'Folded on purple velvet drape', 'skyyrose-flagship' ),
			),
			array(
				'id'         => 'lh-004',
				'name'       => esc_html__( 'Love Hurts Varsity Jacket', 'skyyrose-flagship' ),
				'price'      => '$265',
				'collection' => esc_html__( 'Love Hurts Collection', 'skyyrose-flagship' ),
				'sizes'      => 'S,M,L,XL,2XL,3XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/lh-004-varsity.jpg',
				'url'        => '/?product_id=lh-004',
				'left'       => '28',
				'top'        => '35',
				'prop'       => 'chandelier',
				'prop_label' => esc_html__( 'Draped from crystal chandelier arm', 'skyyrose-flagship' ),
			),
		),
	),
	// Room 3 — Crimson Throne Room
	array(
		'name'     => esc_html__( 'Crimson Throne Room', 'skyyrose-flagship' ),
		'image'    => get_template_directory_uri() . '/assets/scenes/love-hurts/love-hurts-crimson-throne-room.png',
		'alt'      => esc_attr__( 'Cloaked figure in golden ballroom with crimson cape, ornate throne, scattered rose petals, and dramatic fog', 'skyyrose-flagship' ),
		'products' => array(
			array(
				'id'         => 'lh-001',
				'name'       => esc_html__( 'The Fannie Pack', 'skyyrose-flagship' ),
				'price'      => '$65',
				'collection' => esc_html__( 'Love Hurts Collection', 'skyyrose-flagship' ),
				'sizes'      => 'One Size',
				'image'      => get_template_directory_uri() . '/assets/images/products/lh-001-fannie.jpg',
				'url'        => '/?product_id=lh-001',
				'left'       => '62',
				'top'        => '55',
				'prop'       => 'ornate-throne',
				'prop_label' => esc_html__( 'Resting on ornate golden throne', 'skyyrose-flagship' ),
			),
			array(
				'id'         => 'lh-003',
				'name'       => esc_html__( 'Love Hurts Basketball Shorts', 'skyyrose-flagship' ),
				'price'      => '$75',
				'collection' => esc_html__( 'Love Hurts Collection', 'skyyrose-flagship' ),
				'sizes'      => 'S,M,L,XL,2XL,3XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/lh-003-shorts.jpg',
				'url'        => '/?product_id=lh-003',
				'left'       => '35',
				'top'        => '62',
				'prop'       => 'carpet-pedestal',
				'prop_label' => esc_html__( 'Folded on crimson carpet pedestal', 'skyyrose-flagship' ),
			),
		),
	),
	// Room 4 — Enchanted Rose Shrine
	array(
		'name'     => esc_html__( 'Enchanted Rose Shrine', 'skyyrose-flagship' ),
		'image'    => get_template_directory_uri() . '/assets/scenes/love-hurts/love-hurts-enchanted-rose-shrine.png',
		'alt'      => esc_attr__( 'Red-caped figure facing golden shrine with enchanted rose, ornate columns, and warm ethereal light', 'skyyrose-flagship' ),
		'products' => array(
			array(
				'id'         => 'lh-005',
				'name'       => esc_html__( 'Love Hurts Bomber Jacket', 'skyyrose-flagship' ),
				'price'      => '$245',
				'collection' => esc_html__( 'Love Hurts Collection', 'skyyrose-flagship' ),
				'sizes'      => 'S,M,L,XL,2XL,3XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/lh-005-bomber.jpg',
				'url'        => '/?product_id=lh-005',
				'left'       => '45',
				'top'        => '42',
				'prop'       => 'golden-shrine',
				'prop_label' => esc_html__( 'Displayed at golden shrine altar', 'skyyrose-flagship' ),
			),
			array(
				'id'         => 'lh-002',
				'name'       => esc_html__( 'Love Hurts Joggers', 'skyyrose-flagship' ),
				'price'      => '$95',
				'collection' => esc_html__( 'Love Hurts Collection', 'skyyrose-flagship' ),
				'sizes'      => 'S,M,L,XL,2XL,3XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/lh-002-joggers.jpg',
				'url'        => '/?product_id=lh-002',
				'left'       => '70',
				'top'        => '58',
				'prop'       => 'ornate-column',
				'prop_label' => esc_html__( 'Draped over ornate column base', 'skyyrose-flagship' ),
			),
		),
	),
);

get_header();
?>

<main id="primary" class="site-main immersive-page">

	<div class="immersive-scene immersive-love-hurts" role="region" aria-label="<?php esc_attr_e( 'Love Hurts Collection — The Ballroom', 'skyyrose-flagship' ); ?>">

		<!-- Loading Screen -->
		<div class="scene-loading" aria-hidden="true">
			<div class="scene-loading-monogram"><?php echo esc_html__( 'SR', 'skyyrose-flagship' ); ?></div>
			<div class="scene-loading-text"><?php echo esc_html__( 'Entering The Ballroom', 'skyyrose-flagship' ); ?></div>
		</div>

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
			<?php foreach ( $love_hurts_rooms as $index => $room ) : ?>
				<button
					class="room-dot<?php echo 0 === $index ? ' active' : ''; ?>"
					type="button"
					aria-label="<?php echo esc_attr( $room['name'] ); ?>"
				></button>
			<?php endforeach; ?>
		</div>
		<div class="room-name"><?php echo esc_html( $love_hurts_rooms[0]['name'] ); ?></div>

		<!-- Hotspot Containers — One per room -->
		<?php foreach ( $love_hurts_rooms as $room_index => $room ) : ?>
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
			<h1><?php echo esc_html__( 'The Ballroom', 'skyyrose-flagship' ); ?></h1>
			<p class="scene-subtitle"><?php echo esc_html__( 'Love Hurts Collection', 'skyyrose-flagship' ); ?></p>
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
		<a href="<?php echo esc_url( home_url( '/immersive/love-hurts/' ) ); ?>" class="immersive-tab active" aria-current="page" style="--tab-accent: #DC143C;">
			<?php echo esc_html__( 'Love Hurts', 'skyyrose-flagship' ); ?>
		</a>
		<a href="<?php echo esc_url( home_url( '/immersive/signature/' ) ); ?>" class="immersive-tab" style="--tab-accent: #B76E79;">
			<?php echo esc_html__( 'Signature', 'skyyrose-flagship' ); ?>
		</a>
		<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>" class="immersive-tab" style="--tab-accent: #D4AF37;">
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
