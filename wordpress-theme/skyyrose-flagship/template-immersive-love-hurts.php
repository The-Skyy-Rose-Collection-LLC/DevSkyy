<?php
/**
 * Template Name: Immersive - Love Hurts
 *
 * "The Ballroom" — Baroque ballroom with candlelit manor, chandeliers,
 * and rose petals. Two scene views (ballroom + candlelit manor).
 * drakerelated.com-style immersive experience with hotspot beacons.
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
 * Spread across two scene views — Ballroom and Candlelit Manor.
 */
$love_hurts_scenes = array(
	array(
		'name'     => esc_html__( 'The Ballroom', 'skyyrose-flagship' ),
		'image'    => get_template_directory_uri() . '/assets/images/scenes/love-hurts-ballroom.jpg',
		'alt'      => esc_attr__( 'Baroque ballroom with crystal chandeliers, crimson drapery, and rose petals scattered across marble floor', 'skyyrose-flagship' ),
		'products' => array(
			array(
				'id'         => 'lh-001',
				'name'       => esc_html__( 'Crimson Heart Necklace', 'skyyrose-flagship' ),
				'price'      => '$2,199',
				'collection' => esc_html__( 'Love Hurts Collection', 'skyyrose-flagship' ),
				'sizes'      => '16in,18in,20in',
				'image'      => get_template_directory_uri() . '/assets/images/scenes/love-hurts-product-1.jpg',
				'url'        => '#',
				'left'       => '28',
				'top'        => '35',
			),
			array(
				'id'         => 'lh-002',
				'name'       => esc_html__( 'Bleeding Rose Ring', 'skyyrose-flagship' ),
				'price'      => '$1,599',
				'collection' => esc_html__( 'Love Hurts Collection', 'skyyrose-flagship' ),
				'sizes'      => '5,6,7,8,9',
				'image'      => get_template_directory_uri() . '/assets/images/scenes/love-hurts-product-2.jpg',
				'url'        => '#',
				'left'       => '55',
				'top'        => '52',
			),
			array(
				'id'         => 'lh-003',
				'name'       => esc_html__( 'Thorned Embrace Bracelet', 'skyyrose-flagship' ),
				'price'      => '$1,099',
				'collection' => esc_html__( 'Love Hurts Collection', 'skyyrose-flagship' ),
				'sizes'      => 'S,M,L',
				'image'      => get_template_directory_uri() . '/assets/images/scenes/love-hurts-product-3.jpg',
				'url'        => '#',
				'left'       => '75',
				'top'        => '40',
			),
		),
	),
	array(
		'name'     => esc_html__( 'The Manor', 'skyyrose-flagship' ),
		'image'    => get_template_directory_uri() . '/assets/images/scenes/love-hurts-manor.jpg',
		'alt'      => esc_attr__( 'Candlelit gothic manor with velvet chairs, golden pedestals, and flickering candlelight', 'skyyrose-flagship' ),
		'products' => array(
			array(
				'id'         => 'lh-004',
				'name'       => esc_html__( 'Passion Drop Earrings', 'skyyrose-flagship' ),
				'price'      => '$899',
				'collection' => esc_html__( 'Love Hurts Collection', 'skyyrose-flagship' ),
				'sizes'      => 'OS',
				'image'      => get_template_directory_uri() . '/assets/images/scenes/love-hurts-product-4.jpg',
				'url'        => '#',
				'left'       => '40',
				'top'        => '45',
			),
			array(
				'id'         => 'lh-005',
				'name'       => esc_html__( 'Velvet Flame Pendant', 'skyyrose-flagship' ),
				'price'      => '$1,799',
				'collection' => esc_html__( 'Love Hurts Collection', 'skyyrose-flagship' ),
				'sizes'      => '16in,18in,20in,22in',
				'image'      => get_template_directory_uri() . '/assets/images/scenes/love-hurts-product-5.jpg',
				'url'        => '#',
				'left'       => '65',
				'top'        => '58',
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

		<!-- Scene Viewport -->
		<div class="scene-viewport">
			<?php foreach ( $love_hurts_scenes as $index => $scene ) : ?>
				<div
					class="scene-layer<?php echo 0 === $index ? ' active' : ''; ?>"
					data-room-name="<?php echo esc_attr( $scene['name'] ); ?>"
				>
					<img
						src="<?php echo esc_url( $scene['image'] ); ?>"
						alt="<?php echo esc_attr( $scene['alt'] ); ?>"
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
			<button class="room-nav-btn" type="button" aria-label="<?php esc_attr_e( 'Previous scene', 'skyyrose-flagship' ); ?>">
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
			</button>
		</div>
		<div class="room-nav room-nav-next">
			<button class="room-nav-btn" type="button" aria-label="<?php esc_attr_e( 'Next scene', 'skyyrose-flagship' ); ?>">
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
			</button>
		</div>

		<!-- Room Indicators -->
		<div class="room-indicators" aria-label="<?php esc_attr_e( 'Scene selector', 'skyyrose-flagship' ); ?>">
			<?php foreach ( $love_hurts_scenes as $index => $scene ) : ?>
				<button
					class="room-dot<?php echo 0 === $index ? ' active' : ''; ?>"
					type="button"
					aria-label="<?php echo esc_attr( $scene['name'] ); ?>"
				></button>
			<?php endforeach; ?>
		</div>
		<div class="room-name"><?php echo esc_html( $love_hurts_scenes[0]['name'] ); ?></div>

		<!-- Hotspot Containers (one per scene) -->
		<?php foreach ( $love_hurts_scenes as $scene_index => $scene ) : ?>
			<div class="hotspot-container" <?php echo 0 !== $scene_index ? 'style="display:none;"' : ''; ?>>
				<?php foreach ( $scene['products'] as $product ) : ?>
					<a
						href="<?php echo esc_url( $product['url'] ); ?>"
						class="hotspot"
						style="left: <?php echo esc_attr( $product['left'] ); ?>%; top: <?php echo esc_attr( $product['top'] ); ?>%;"
						data-product-id="<?php echo esc_attr( $product['id'] ); ?>"
						data-product-name="<?php echo esc_attr( $product['name'] ); ?>"
						data-product-price="<?php echo esc_attr( $product['price'] ); ?>"
						data-product-image="<?php echo esc_url( $product['image'] ); ?>"
						data-product-collection="<?php echo esc_attr( $product['collection'] ); ?>"
						data-product-sizes="<?php echo esc_attr( $product['sizes'] ); ?>"
						data-product-url="<?php echo esc_url( $product['url'] ); ?>"
						aria-label="<?php echo esc_attr( $product['name'] . ' — ' . $product['price'] ); ?>"
					>
						<span class="hotspot-beacon"></span>
						<span class="hotspot-label"><?php echo esc_html( $product['name'] ); ?></span>
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
	<aside class="product-panel" role="dialog" aria-label="<?php esc_attr_e( 'Product Details', 'skyyrose-flagship' ); ?>">
		<button class="product-panel-close" type="button" aria-label="<?php esc_attr_e( 'Close product details', 'skyyrose-flagship' ); ?>">&times;</button>
		<div class="product-panel-inner">
			<div class="product-panel-thumb">
				<img src="<?php echo esc_url( get_template_directory_uri() . '/assets/images/placeholder.jpg' ); ?>" alt="">
			</div>
			<div class="product-panel-info">
				<p class="product-panel-collection"></p>
				<h3 class="product-panel-name"></h3>
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
		<a href="<?php echo esc_url( home_url( '/immersive/black-rose/' ) ); ?>" class="immersive-tab" style="--tab-accent: #C0C0C0;">
			<?php echo esc_html__( 'Black Rose', 'skyyrose-flagship' ); ?>
		</a>
		<a href="<?php echo esc_url( home_url( '/immersive/love-hurts/' ) ); ?>" class="immersive-tab active" style="--tab-accent: #DC143C;">
			<?php echo esc_html__( 'Love Hurts', 'skyyrose-flagship' ); ?>
		</a>
		<a href="<?php echo esc_url( home_url( '/immersive/signature/' ) ); ?>" class="immersive-tab" style="--tab-accent: #B76E79;">
			<?php echo esc_html__( 'Signature', 'skyyrose-flagship' ); ?>
		</a>
		<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>" class="immersive-tab" style="--tab-accent: #D4AF37;">
			<?php echo esc_html__( 'Pre-Order', 'skyyrose-flagship' ); ?>
		</a>
	</nav>

</main><!-- #primary -->

<?php
// Enqueue immersive assets.
wp_enqueue_style(
	'skyyrose-immersive',
	get_template_directory_uri() . '/assets/css/immersive.css',
	array( 'skyyrose-style' ),
	SKYYROSE_VERSION
);

wp_enqueue_script(
	'skyyrose-immersive',
	get_template_directory_uri() . '/assets/js/immersive.js',
	array(),
	SKYYROSE_VERSION,
	true
);

get_template_part( 'template-parts/cinematic-toggle' );

get_footer();
