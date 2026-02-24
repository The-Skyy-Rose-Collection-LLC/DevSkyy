<?php
/**
 * Template Name: Immersive - Black Rose
 *
 * "The Garden" — Gothic garden scene with wrought-iron racks, roses,
 * and cathedral backdrop. drakerelated.com-style immersive experience
 * with hotspot beacons on products visible in the scene.
 *
 * @package SkyyRose_Flagship
 * @since 2.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Product data for hotspot beacons.
 * Each product is positioned on a contextual prop within the scene —
 * stone benches, iron gates, rose arbors, vintage mirrors, glass bell jars.
 * Products attach TO these props, not floating in air.
 *
 * Will be replaced with WooCommerce product queries in production.
 */
$black_rose_products = array(
	array(
		'id'         => 'br-001',
		'name'       => esc_html__( 'Midnight Thorns Necklace', 'skyyrose-flagship' ),
		'price'      => '$1,899',
		'collection' => esc_html__( 'Black Rose Collection', 'skyyrose-flagship' ),
		'sizes'      => '16in,18in,20in',
		'image'      => get_template_directory_uri() . '/assets/images/scenes/black-rose-product-1.jpg',
		'url'        => '#',
		'left'       => '22',
		'top'        => '38',
		'prop'       => 'vintage-mirror',
		'prop_label' => esc_html__( 'On antique vanity mirror', 'skyyrose-flagship' ),
	),
	array(
		'id'         => 'br-002',
		'name'       => esc_html__( 'Cathedral Ring', 'skyyrose-flagship' ),
		'price'      => '$1,299',
		'collection' => esc_html__( 'Black Rose Collection', 'skyyrose-flagship' ),
		'sizes'      => '5,6,7,8,9',
		'image'      => get_template_directory_uri() . '/assets/images/scenes/black-rose-product-2.jpg',
		'url'        => '#',
		'left'       => '48',
		'top'        => '55',
		'prop'       => 'stone-bench',
		'prop_label' => esc_html__( 'On wrought-iron garden bench', 'skyyrose-flagship' ),
	),
	array(
		'id'         => 'br-003',
		'name'       => esc_html__( 'Iron Garden Bracelet', 'skyyrose-flagship' ),
		'price'      => '$999',
		'collection' => esc_html__( 'Black Rose Collection', 'skyyrose-flagship' ),
		'sizes'      => 'S,M,L',
		'image'      => get_template_directory_uri() . '/assets/images/scenes/black-rose-product-3.jpg',
		'url'        => '#',
		'left'       => '72',
		'top'        => '42',
		'prop'       => 'rose-arbor',
		'prop_label' => esc_html__( 'Draped over rose arbor gate', 'skyyrose-flagship' ),
	),
	array(
		'id'         => 'br-004',
		'name'       => esc_html__( 'Dark Bloom Earrings', 'skyyrose-flagship' ),
		'price'      => '$799',
		'collection' => esc_html__( 'Black Rose Collection', 'skyyrose-flagship' ),
		'sizes'      => 'OS',
		'image'      => get_template_directory_uri() . '/assets/images/scenes/black-rose-product-4.jpg',
		'url'        => '#',
		'left'       => '35',
		'top'        => '28',
		'prop'       => 'glass-bell-jar',
		'prop_label' => esc_html__( 'Inside glass bell jar', 'skyyrose-flagship' ),
	),
	array(
		'id'         => 'br-005',
		'name'       => esc_html__( 'Shadow Vine Pendant', 'skyyrose-flagship' ),
		'price'      => '$1,499',
		'collection' => esc_html__( 'Black Rose Collection', 'skyyrose-flagship' ),
		'sizes'      => '16in,18in,20in,22in',
		'image'      => get_template_directory_uri() . '/assets/images/scenes/black-rose-product-5.jpg',
		'url'        => '#',
		'left'       => '60',
		'top'        => '65',
		'prop'       => 'stone-pedestal',
		'prop_label' => esc_html__( 'On cathedral stone pedestal', 'skyyrose-flagship' ),
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

		<!-- Scene Viewport -->
		<div class="scene-viewport">
			<div class="scene-layer active" data-room-name="<?php esc_attr_e( 'The Garden', 'skyyrose-flagship' ); ?>">
				<img
					src="<?php echo esc_url( get_template_directory_uri() . '/assets/images/scenes/black-rose-garden.jpg' ); ?>"
					alt="<?php esc_attr_e( 'Gothic garden with wrought-iron racks draped in black roses, cathedral spires visible through mist', 'skyyrose-flagship' ); ?>"
					loading="eager"
					fetchpriority="high"
				>
			</div>
		</div>

		<!-- Vignette -->
		<div class="scene-vignette"></div>

		<!-- Film Grain -->
		<div class="scene-film-grain" aria-hidden="true"></div>

		<!-- Hotspot Beacons — Products placed on contextual props -->
		<div class="hotspot-container">
			<?php foreach ( $black_rose_products as $product ) : ?>
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
					<button class="btn-add-to-cart" type="button"><?php echo esc_html__( 'Add to Cart', 'skyyrose-flagship' ); ?></button>
					<a class="btn-view-details" href="#"><?php echo esc_html__( 'Details', 'skyyrose-flagship' ); ?></a>
				</div>
			</div>
		</div>
	</aside>

	<!-- Collection Tab Bar -->
	<nav class="immersive-tab-bar" aria-label="<?php esc_attr_e( 'Collection navigation', 'skyyrose-flagship' ); ?>">
		<a href="<?php echo esc_url( home_url( '/immersive/black-rose/' ) ); ?>" class="immersive-tab active" aria-current="page" style="--tab-accent: #C0C0C0;">
			<?php echo esc_html__( 'Black Rose', 'skyyrose-flagship' ); ?>
		</a>
		<a href="<?php echo esc_url( home_url( '/immersive/love-hurts/' ) ); ?>" class="immersive-tab" style="--tab-accent: #DC143C;">
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

</main><!-- #primary -->

<?php
get_footer();
