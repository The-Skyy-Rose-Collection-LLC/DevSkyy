<?php
/**
 * Template Name: Immersive - Black Rose
 *
 * "The Garden" — Gothic cathedral garden rooms with wrought-iron racks,
 * black roses, marble rotundas, and moonlit grottos.
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
 * Products are positioned on contextual props within each scene.
 */
$black_rose_rooms = array(
	// Room 1 — Moonlit Courtyard
	array(
		'name'     => esc_html__( 'Moonlit Courtyard', 'skyyrose-flagship' ),
		'image'    => get_template_directory_uri() . '/assets/scenes/black-rose/black-rose-moonlit-courtyard.png',
		'alt'      => esc_attr__( 'Moonlit garden courtyard with marble statues, black rose topiaries, and ornate fountains', 'skyyrose-flagship' ),
		'products' => array(
			array(
				'id'         => 'br-006',
				'name'       => esc_html__( 'BLACK Rose Sherpa Jacket', 'skyyrose-flagship' ),
				'price'      => '$295',
				'collection' => esc_html__( 'Black Rose Collection', 'skyyrose-flagship' ),
				'sizes'      => 'S,M,L,XL,2XL,3XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/br-006-sherpa.jpg',
				'url'        => '/?product_id=br-006',
				'left'       => '25',
				'top'        => '52',
				'prop'       => 'marble-statue',
				'prop_label' => esc_html__( 'Draped over marble garden statue', 'skyyrose-flagship' ),
			),
			array(
				'id'         => 'br-001',
				'name'       => esc_html__( 'BLACK Rose Crewneck', 'skyyrose-flagship' ),
				'price'      => '$125',
				'collection' => esc_html__( 'Black Rose Collection', 'skyyrose-flagship' ),
				'sizes'      => 'S,M,L,XL,2XL,3XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/br-001-crewneck.jpg',
				'url'        => '/?product_id=br-001',
				'left'       => '68',
				'top'        => '40',
				'prop'       => 'fountain-edge',
				'prop_label' => esc_html__( 'Folded on fountain edge', 'skyyrose-flagship' ),
			),
		),
	),
	// Room 2 — Iron Gazebo Garden
	array(
		'name'     => esc_html__( 'Iron Gazebo Garden', 'skyyrose-flagship' ),
		'image'    => get_template_directory_uri() . '/assets/scenes/black-rose/black-rose-iron-gazebo-garden.png',
		'alt'      => esc_attr__( 'Aerial view of ornate iron gazebo surrounded by rose hedge maze and cobblestone paths under moonlight', 'skyyrose-flagship' ),
		'products' => array(
			array(
				'id'         => 'br-008',
				'name'       => esc_html__( "Women's BLACK Rose Hooded Dress", 'skyyrose-flagship' ),
				'price'      => '$175',
				'collection' => esc_html__( 'Black Rose Collection', 'skyyrose-flagship' ),
				'sizes'      => 'XS,S,M,L,XL,2XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/br-008-hooded-dress.jpg',
				'url'        => '/?product_id=br-008',
				'left'       => '48',
				'top'        => '35',
				'prop'       => 'iron-gazebo',
				'prop_label' => esc_html__( 'Displayed inside iron gazebo', 'skyyrose-flagship' ),
			),
			array(
				'id'         => 'br-004',
				'name'       => esc_html__( 'BLACK Rose Hoodie', 'skyyrose-flagship' ),
				'price'      => '$145',
				'collection' => esc_html__( 'Black Rose Collection', 'skyyrose-flagship' ),
				'sizes'      => 'S,M,L,XL,2XL,3XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/br-004-hoodie.jpg',
				'url'        => '/?product_id=br-004',
				'left'       => '72',
				'top'        => '55',
				'prop'       => 'hedge-arch',
				'prop_label' => esc_html__( 'Hanging from rose hedge archway', 'skyyrose-flagship' ),
			),
		),
	),
	// Room 3 — Marble Rotunda
	array(
		'name'     => esc_html__( 'Marble Rotunda', 'skyyrose-flagship' ),
		'image'    => get_template_directory_uri() . '/assets/scenes/black-rose/black-rose-marble-rotunda.png',
		'alt'      => esc_attr__( 'Dark marble rotunda with twisted glowing tree, mannequin statue, and dramatic skylight', 'skyyrose-flagship' ),
		'products' => array(
			array(
				'id'         => 'br-005',
				'name'       => esc_html__( 'BLACK Rose Hoodie — Signature Edition', 'skyyrose-flagship' ),
				'price'      => '$185',
				'collection' => esc_html__( 'Black Rose Collection', 'skyyrose-flagship' ),
				'sizes'      => 'S,M,L,XL,2XL,3XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/br-005-hoodie-sig.jpg',
				'url'        => '/?product_id=br-005',
				'left'       => '38',
				'top'        => '45',
				'prop'       => 'mannequin-statue',
				'prop_label' => esc_html__( 'On mannequin beneath skylight', 'skyyrose-flagship' ),
			),
			array(
				'id'         => 'br-002',
				'name'       => esc_html__( 'BLACK Rose Joggers', 'skyyrose-flagship' ),
				'price'      => '$95',
				'collection' => esc_html__( 'Black Rose Collection', 'skyyrose-flagship' ),
				'sizes'      => 'S,M,L,XL,2XL,3XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/br-002-joggers.jpg',
				'url'        => '/?product_id=br-002',
				'left'       => '65',
				'top'        => '60',
				'prop'       => 'twisted-tree-base',
				'prop_label' => esc_html__( 'Folded at base of glowing tree', 'skyyrose-flagship' ),
			),
		),
	),
	// Room 4 — White Rose Grotto
	array(
		'name'     => esc_html__( 'White Rose Grotto', 'skyyrose-flagship' ),
		'image'    => get_template_directory_uri() . '/assets/scenes/black-rose/black-rose-white-rose-grotto.png',
		'alt'      => esc_attr__( 'Underground grotto with white roses on marble pedestal, ethereal light beams through stone arches', 'skyyrose-flagship' ),
		'products' => array(
			array(
				'id'         => 'br-003',
				'name'       => esc_html__( 'BLACK is Beautiful Jersey', 'skyyrose-flagship' ),
				'price'      => '$110',
				'collection' => esc_html__( 'Black Rose Collection', 'skyyrose-flagship' ),
				'sizes'      => 'S,M,L,XL,2XL,3XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/br-003-jersey.jpg',
				'url'        => '/?product_id=br-003',
				'left'       => '50',
				'top'        => '38',
				'prop'       => 'marble-pedestal',
				'prop_label' => esc_html__( 'Displayed on marble rose pedestal', 'skyyrose-flagship' ),
			),
			array(
				'id'         => 'br-007',
				'name'       => esc_html__( 'BLACK Rose × Love Hurts Basketball Shorts', 'skyyrose-flagship' ),
				'price'      => '$85',
				'collection' => esc_html__( 'Black Rose Collection', 'skyyrose-flagship' ),
				'sizes'      => 'S,M,L,XL,2XL,3XL',
				'image'      => get_template_directory_uri() . '/assets/images/products/br-007-shorts.jpg',
				'url'        => '/?product_id=br-007',
				'left'       => '30',
				'top'        => '58',
				'prop'       => 'stone-arch',
				'prop_label' => esc_html__( 'Draped over grotto stone arch', 'skyyrose-flagship' ),
			),
		),
	),
);

get_header();
?>

<main id="primary" class="site-main immersive-page">

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
			<?php foreach ( $black_rose_rooms as $index => $room ) : ?>
				<button
					class="room-dot<?php echo 0 === $index ? ' active' : ''; ?>"
					type="button"
					aria-label="<?php echo esc_attr( $room['name'] ); ?>"
				></button>
			<?php endforeach; ?>
		</div>
		<div class="room-name"><?php echo esc_html( $black_rose_rooms[0]['name'] ); ?></div>

		<!-- Hotspot Containers — One per room, products on contextual props -->
		<?php foreach ( $black_rose_rooms as $room_index => $room ) : ?>
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
			<h1><?php echo esc_html__( 'The Garden', 'skyyrose-flagship' ); ?></h1>
			<p class="scene-subtitle"><?php echo esc_html__( 'Black Rose Collection', 'skyyrose-flagship' ); ?></p>
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
		<a href="<?php echo esc_url( home_url( '/experience-black-rose/' ) ); ?>" class="immersive-tab active" aria-current="page" style="--tab-accent: #C0C0C0;">
			<?php echo esc_html__( 'Black Rose', 'skyyrose-flagship' ); ?>
		</a>
		<a href="<?php echo esc_url( home_url( '/experience-love-hurts/' ) ); ?>" class="immersive-tab" style="--tab-accent: #DC143C;">
			<?php echo esc_html__( 'Love Hurts', 'skyyrose-flagship' ); ?>
		</a>
		<a href="<?php echo esc_url( home_url( '/experience-signature/' ) ); ?>" class="immersive-tab" style="--tab-accent: #B76E79;">
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
