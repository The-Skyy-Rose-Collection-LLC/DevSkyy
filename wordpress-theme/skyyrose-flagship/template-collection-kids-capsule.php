<?php
/**
 * Template Name: Collection - Kids Capsule
 *
 * Standalone catalog page for the KIDS CAPSULE collection.
 * Rose-gold (#B76E79) on warm charcoal (#1A1A1A) — dark luxury, not playful.
 *
 * @package SkyyRose_Flagship
 * @since   5.0.0
 */

defined( 'ABSPATH' ) || exit;

/* ------------------------------------------------------------------
   Product catalog — WooCommerce first, static fallback
   ------------------------------------------------------------------ */
$skyyrose_kc_products = array();

if ( function_exists( 'wc_get_products' ) ) {
	$skyyrose_kc_wc = wc_get_products( array(
		'limit'    => 10,
		'category' => array( 'kids-capsule' ),
		'status'   => 'publish',
		'orderby'  => 'menu_order',
		'order'    => 'ASC',
	) );

	foreach ( $skyyrose_kc_wc as $skyyrose_wc_item ) {
		$skyyrose_kc_products[] = array(
			'product'   => $skyyrose_wc_item,
			'sku'       => $skyyrose_wc_item->get_sku(),
			'name'      => $skyyrose_wc_item->get_name(),
			'price'     => $skyyrose_wc_item->get_price_html(),
			'desc'      => wp_strip_all_tags( $skyyrose_wc_item->get_short_description() ),
			'badge'     => $skyyrose_wc_item->get_meta( '_collection_badge' ),
			'url'       => get_permalink( $skyyrose_wc_item->get_id() ),
			'image_url' => wp_get_attachment_image_url( $skyyrose_wc_item->get_image_id(), 'large' ),
		);
	}
}

/* Static fallback when WooCommerce is absent or category is empty */
if ( empty( $skyyrose_kc_products ) ) {
	$skyyrose_kc_preorder = home_url( '/pre-order/' );
	$skyyrose_kc_products = array(
		array(
			'product'   => null,
			'sku'       => 'kids-001',
			'name'      => __( 'Kids Colorblock Hoodie Set — Purple/Pink', 'skyyrose-flagship' ),
			'price'     => '$55',
			'desc'      => __( 'Luxury colorblock hoodie and jogger set in deep purple and rose-gold', 'skyyrose-flagship' ),
			'badge'     => __( 'New', 'skyyrose-flagship' ),
			'url'       => $skyyrose_kc_preorder,
			'image_url' => '',
		),
		array(
			'product'   => null,
			'sku'       => 'kids-002',
			'name'      => __( 'Kids Colorblock Hoodie Set — Black/Red/White', 'skyyrose-flagship' ),
			'price'     => '$55',
			'desc'      => __( 'Bold colorblock hoodie and jogger set in classic black, red, and white', 'skyyrose-flagship' ),
			'badge'     => __( 'New', 'skyyrose-flagship' ),
			'url'       => $skyyrose_kc_preorder,
			'image_url' => '',
		),
		array(
			'product'   => null,
			'sku'       => 'kids-003',
			'name'      => __( 'Mini Rose Classic Tee', 'skyyrose-flagship' ),
			'price'     => '$35',
			'desc'      => __( 'Premium classic tee with Mini Rose branding', 'skyyrose-flagship' ),
			'badge'     => '',
			'url'       => $skyyrose_kc_preorder,
			'image_url' => '',
		),
		array(
			'product'   => null,
			'sku'       => 'kids-004',
			'name'      => __( 'Little Legend Joggers', 'skyyrose-flagship' ),
			'price'     => '$45',
			'desc'      => __( 'Dark-luxury joggers built for the next generation', 'skyyrose-flagship' ),
			'badge'     => '',
			'url'       => $skyyrose_kc_preorder,
			'image_url' => '',
		),
	);
}

$skyyrose_kc_count = count( $skyyrose_kc_products );
$skyyrose_kc_cart  = function_exists( 'wc_get_cart_url' ) ? wc_get_cart_url() : home_url( '/cart/' );

/* Cross-collection navigation */
$skyyrose_kc_collections = array(
	array(
		'slug'  => 'collection-signature',
		'name'  => __( 'Signature', 'skyyrose-flagship' ),
		'desc'  => __( 'The Foundation', 'skyyrose-flagship' ),
		'class' => 'kc-cross__link--signature',
	),
	array(
		'slug'  => 'collection-black-rose',
		'name'  => __( 'Black Rose', 'skyyrose-flagship' ),
		'desc'  => __( 'Dark Elegance', 'skyyrose-flagship' ),
		'class' => 'kc-cross__link--black-rose',
	),
	array(
		'slug'  => 'collection-love-hurts',
		'name'  => __( 'Love Hurts', 'skyyrose-flagship' ),
		'desc'  => __( 'Crimson Rebellion', 'skyyrose-flagship' ),
		'class' => 'kc-cross__link--love-hurts',
	),
);

get_header();
?>

<style>
/* Inline override — CDN caches external CSS aggressively */
.kc-fade-up { animation: kcUp 1s ease-out .3s forwards !important; }
.kc-fade-left { animation: kcLeft 1s ease-out .5s forwards !important; }
.kc-fade-right { animation: kcRight 1s ease-out .7s forwards !important; }
@keyframes kcUp { to { opacity:1; transform:translateY(0); } }
@keyframes kcLeft { to { opacity:1; transform:translateX(0); } }
@keyframes kcRight { to { opacity:1; transform:translateX(0); } }
</style>

<main id="primary" class="site-main kc-page" role="main" tabindex="-1">

	<!-- ============================================================
	     HERO — Rose-gold radial gradient
	     ============================================================ -->
	<section class="kc-hero" aria-label="<?php esc_attr_e( 'Kids Capsule Hero', 'skyyrose-flagship' ); ?>">
		<div class="kc-hero__bg" aria-hidden="true"></div>
		<div class="kc-hero__content kc-fade-up" id="kc-hero-content">
			<span class="kc-hero__badge">
				<?php esc_html_e( 'New Collection', 'skyyrose-flagship' ); ?>
			</span>
			<h1 class="kc-hero__title">
				<span><?php esc_html_e( 'KIDS CAPSULE', 'skyyrose-flagship' ); ?></span>
			</h1>
			<p class="kc-hero__subtitle">
				<?php esc_html_e( 'Luxury runs in the family. Premium streetwear for the next generation — powerful, elevated, and born into legacy.', 'skyyrose-flagship' ); ?>
			</p>
			<a href="#kc-products" class="kc-hero__cta">
				<?php esc_html_e( 'Shop the Collection', 'skyyrose-flagship' ); ?>
			</a>
		</div>
	</section>

	<!-- ============================================================
	     BRAND STORY — "Born Into Luxury" + KC monogram
	     ============================================================ -->
	<section class="kc-story" aria-labelledby="kc-story-heading">
		<div class="kc-story__inner">
			<div class="kc-story__text kc-fade-left" id="kc-story-text">
				<h2 id="kc-story-heading">
					<?php esc_html_e( 'The Next Generation of', 'skyyrose-flagship' ); ?>
					<span><?php esc_html_e( 'SkyyRose', 'skyyrose-flagship' ); ?></span>
				</h2>
				<p>
					<?php esc_html_e( 'Born into luxury, built for the bold. Kids Capsule carries the same uncompromising vision that defines every SkyyRose collection — distilled for the youngest members of the family.', 'skyyrose-flagship' ); ?>
				</p>
				<p>
					<?php esc_html_e( 'No pastels. No cartoons. This is real streetwear scaled down, not dumbed down. Every piece is crafted with the same premium materials and dark elegance that the brand was built on.', 'skyyrose-flagship' ); ?>
				</p>
				<p>
					<?php esc_html_e( 'Because legacy is not inherited. It is worn.', 'skyyrose-flagship' ); ?>
				</p>
			</div>
			<div class="kc-story__visual kc-fade-right" id="kc-story-visual" aria-hidden="true"></div>
		</div>
	</section>

	<!-- ============================================================
	     PRODUCT GRID — Holo cards with data-collection
	     ============================================================ -->
	<section class="kc-products" id="kc-products" aria-labelledby="kc-products-heading">
		<div class="kc-products__header">
			<h2 id="kc-products-heading">
				<?php esc_html_e( 'The Collection', 'skyyrose-flagship' ); ?>
			</h2>
			<p>
				<?php
				printf(
					/* translators: %d: number of products */
					esc_html( _n( '%d Piece', '%d Pieces', $skyyrose_kc_count, 'skyyrose-flagship' ) ),
					$skyyrose_kc_count
				);
				echo ' &middot; ';
				esc_html_e( 'Limited Run', 'skyyrose-flagship' );
				?>
			</p>
		</div>

		<div class="product-grid" data-collection="kids-capsule">
			<?php
			$skyyrose_kc_idx = 0;
			foreach ( $skyyrose_kc_products as $skyyrose_kc_item ) :
				get_template_part( 'template-parts/product-card-holo', null, array(
					'product'    => $skyyrose_kc_item['product'] ?? null,
					'title'      => $skyyrose_kc_item['name'],
					'price'      => $skyyrose_kc_item['price'],
					'image_url'  => $skyyrose_kc_item['image_url'],
					'permalink'  => $skyyrose_kc_item['url'],
					'collection' => 'kids-capsule',
					'badge_text' => $skyyrose_kc_item['badge'],
					'desc'       => $skyyrose_kc_item['desc'],
					'sku'        => $skyyrose_kc_item['sku'],
					'index'      => $skyyrose_kc_idx,
				) );
				$skyyrose_kc_idx++;
			endforeach;
			?>
		</div>
	</section>

	<!-- ============================================================
	     CROSS-COLLECTION NAVIGATION
	     ============================================================ -->
	<section class="kc-cross" aria-labelledby="kc-cross-heading">
		<h2 id="kc-cross-heading" class="kc-cross__heading">
			<?php esc_html_e( 'Explore More Collections', 'skyyrose-flagship' ); ?>
		</h2>
		<div class="kc-cross__grid">
			<?php foreach ( $skyyrose_kc_collections as $skyyrose_kc_col ) : ?>
				<a href="<?php echo esc_url( home_url( '/' . $skyyrose_kc_col['slug'] . '/' ) ); ?>"
				   class="kc-cross__link <?php echo esc_attr( $skyyrose_kc_col['class'] ); ?>"
				   aria-label="<?php echo esc_attr( sprintf(
					   /* translators: %s: collection name */
					   __( 'Explore the %s collection', 'skyyrose-flagship' ),
					   $skyyrose_kc_col['name']
				   ) ); ?>">
					<h3><?php echo esc_html( $skyyrose_kc_col['name'] ); ?></h3>
					<p><?php echo esc_html( $skyyrose_kc_col['desc'] ); ?></p>
				</a>
			<?php endforeach; ?>
		</div>
	</section>

</main><!-- #primary -->

<!-- Toast notification for add-to-cart feedback -->
<div class="kc-toast" id="kc-toast" aria-live="polite"></div>

<script>
(function () {
	/* GSAP scroll animations (progressive — no-op if GSAP missing) */
	if ( typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined' ) { return; }
	gsap.registerPlugin( ScrollTrigger );

	/* Hero fade-up */
	gsap.to( '#kc-hero-content', {
		opacity: 1, y: 0, duration: 1.2, ease: 'power3.out', delay: 0.3
	} );

	/* Story section */
	gsap.to( '#kc-story-text', {
		scrollTrigger: { trigger: '.kc-story', start: 'top 75%', toggleActions: 'play none none none' },
		opacity: 1, x: 0, duration: 1, ease: 'power3.out'
	} );
	gsap.to( '#kc-story-visual', {
		scrollTrigger: { trigger: '.kc-story', start: 'top 75%', toggleActions: 'play none none none' },
		opacity: 1, x: 0, duration: 1, ease: 'power3.out', delay: 0.2
	} );

	/* Cross-collection links stagger */
	gsap.utils.toArray( '.kc-cross__link' ).forEach( function ( link, i ) {
		gsap.from( link, {
			scrollTrigger: { trigger: link, start: 'top 85%', toggleActions: 'play none none none' },
			opacity: 0, y: 30, duration: 0.8, delay: i * 0.15, ease: 'power3.out'
		} );
	} );
})();
</script>

<?php get_footer(); ?>
