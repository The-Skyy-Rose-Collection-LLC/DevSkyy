<?php
/**
 * Template Name: Pre-Order Gateway
 *
 * Showcase-style pre-order page with hero, interactive collection selector grid,
 * tabbed product grids using holo cards, sticky cart summary bar, and GSAP
 * entrance/collection-switching animations. Dark luxury aesthetic.
 *
 * @package SkyyRose
 * @since   2.0.0
 * @updated 6.0.0 — complete rewrite from static pre-order.html
 */

defined( 'ABSPATH' ) || exit;

/*
 * ─── Collection Configuration ───────────────────────────────────────────────
 */
$collections = array(
	'black-rose'   => array(
		'label'    => esc_html__( 'Black Rose', 'skyyrose' ),
		'tagline'  => esc_html__( 'The Beauty of Black', 'skyyrose' ),
		'number'   => esc_html__( 'Collection 01', 'skyyrose' ),
		'subtitle' => esc_html__( 'Dark Elegance', 'skyyrose' ),
	),
	'love-hurts'   => array(
		'label'    => esc_html__( 'Love Hurts', 'skyyrose' ),
		'tagline'  => esc_html__( 'The Hurts Bloodline', 'skyyrose' ),
		'number'   => esc_html__( 'Collection 02', 'skyyrose' ),
		'subtitle' => esc_html__( 'The Hurts Bloodline', 'skyyrose' ),
	),
	'signature'    => array(
		'label'    => esc_html__( 'Signature', 'skyyrose' ),
		'tagline'  => esc_html__( 'The Origin. The Crown.', 'skyyrose' ),
		'number'   => esc_html__( 'Collection 03', 'skyyrose' ),
		'subtitle' => esc_html__( 'The Origin. The Crown.', 'skyyrose' ),
	),
	'kids-capsule' => array(
		'label'    => esc_html__( 'Kids Capsule', 'skyyrose' ),
		'tagline'  => esc_html__( 'Little Luxury', 'skyyrose' ),
		'number'   => esc_html__( 'Collection 04', 'skyyrose' ),
		'subtitle' => esc_html__( 'Little Luxury', 'skyyrose' ),
	),
);

/*
 * ─── Load products from CSV catalog (single source of truth) ────────────────
 */
$products_by_collection = array();
foreach ( array_keys( $collections ) as $slug ) {
	$products_by_collection[ $slug ] = skyyrose_get_collection_products( $slug );
}

$currency_symbol = function_exists( 'get_woocommerce_currency_symbol' )
	? html_entity_decode( get_woocommerce_currency_symbol(), ENT_QUOTES, 'UTF-8' )
	: '$';

$checkout_url = function_exists( 'wc_get_checkout_url' ) ? wc_get_checkout_url() : '#';

get_header();
?>

<main id="primary" class="site-main preorder-gateway" role="main" tabindex="-1"
	data-collection=""><?php // data-collection wired for immersive-core.js Cap A/C detection; empty = no palette override on this multi-collection page ?>

	<!-- ==================== HERO (cinematic video) ==================== -->
	<?php
	get_template_part(
		'template-parts/hero-cinematic',
		null,
		array(
			'collection' => '', // empty → :root rose-gold palette for the multi-collection gateway.
			'image'      => SKYYROSE_ASSETS_URI . '/images/preorder-hero-poster.jpg',
			'image_webp' => SKYYROSE_ASSETS_URI . '/images/preorder-hero-poster.webp',
			'video'      => SKYYROSE_ASSETS_URI . '/video/preorder-hero.mp4',
			'video_webm' => SKYYROSE_ASSETS_URI . '/video/preorder-hero.webm',
			'lockup'     => SKYYROSE_ASSETS_URI . '/images/hero-overlays/sig-brand-skyy-rose-gold.webp',
			'lockup_alt' => esc_html__( 'Skyy Rose', 'skyyrose' ),
			'eyebrow'    => esc_html__( 'Exclusive Access', 'skyyrose' ),
			'body'       => __( 'Secure your pieces before they drop. Luxury Grows from Concrete.', 'skyyrose' ),
			'cta_label'  => __( 'Browse Collections', 'skyyrose' ),
			'cta_url'    => '#showcase',
		)
	);
	?>

	<!-- ==================== SHOWCASE GRID ==================== -->
	<section class="showcase" id="showcase"
			aria-label="<?php esc_attr_e( 'Browse collections', 'skyyrose' ); ?>">
		<div class="showcase__grid stagger-grid">
			<?php foreach ( $collections as $slug => $col ) : ?>
				<button type="button" class="showcase__card showcase__card--<?php echo esc_attr( $slug ); ?> magnetic"
					data-collection="<?php echo esc_attr( $slug ); ?>"
					data-warp
					aria-label="
					<?php
						echo esc_attr(
							sprintf(
							/* translators: %s: collection name */
								__( 'Explore %s collection', 'skyyrose' ),
								$col['label']
							)
						);
					?>
					">
					<span class="showcase__card-number"><?php echo esc_html( $col['number'] ); ?></span>
					<h2 class="showcase__card-title"><?php echo esc_html( $col['label'] ); ?></h2>
					<p class="showcase__card-tagline"><?php echo esc_html( $col['tagline'] ); ?></p>
					<span class="showcase__card-cta">
					<?php
						echo wp_kses(
							__( 'Explore Collection &rarr;', 'skyyrose' ),
							array()
						);
					?>
					</span>
				</button>
			<?php endforeach; ?>
		</div>
	</section>

	<!-- ==================== COLLECTION TAB BAR ==================== -->
	<div class="tab-bar" id="tab-bar" role="tablist"
		aria-label="<?php esc_attr_e( 'Filter by collection', 'skyyrose' ); ?>">
		<?php foreach ( $collections as $slug => $col ) : ?>
			<button class="tab-bar__btn" type="button"
					role="tab"
					aria-selected="false"
					aria-controls="grid-<?php echo esc_attr( $slug ); ?>"
					data-tab="<?php echo esc_attr( $slug ); ?>"
					id="tab-<?php echo esc_attr( $slug ); ?>"
					tabindex="-1">
				<?php echo esc_html( $col['label'] ); ?>
			</button>
		<?php endforeach; ?>
	</div>

	<!-- ==================== PRODUCT GRIDS ==================== -->
	<section class="products-section" id="products-section"
			aria-label="<?php esc_attr_e( 'Pre-order products', 'skyyrose' ); ?>">
		<?php
		foreach ( $collections as $slug => $col ) :
			$items = isset( $products_by_collection[ $slug ] ) ? $products_by_collection[ $slug ] : array();
			?>
			<div class="product-grid"
				data-collection="<?php echo esc_attr( $slug ); ?>"
				id="grid-<?php echo esc_attr( $slug ); ?>"
				role="tabpanel"
				aria-labelledby="tab-<?php echo esc_attr( $slug ); ?>"
				style="display:none;">

				<div class="product-grid__header">
					<h2 class="product-grid__title"><?php echo esc_html( $col['label'] ); ?></h2>
					<p class="product-grid__subtitle">
						<?php echo esc_html( $col['subtitle'] ); ?>
						&bull;
						<?php esc_html_e( 'Limited Edition', 'skyyrose' ); ?>
					</p>
				</div>

				<?php
				if ( ! empty( $items ) ) :
					$index = 0;
					foreach ( $items as $item ) :
						$item_sku  = isset( $item['sku'] ) ? $item['sku'] : '';
						$card_args = array(
							'title'      => isset( $item['name'] ) ? $item['name'] : '',
							'price'      => skyyrose_format_price( $item ),
							'image_url'  => skyyrose_product_image_uri( isset( $item['front_model_image'] ) ? $item['front_model_image'] : ( isset( $item['image'] ) ? $item['image'] : '' ) ),
							'image_back' => skyyrose_product_image_uri( isset( $item['back_model_image'] ) ? $item['back_model_image'] : ( isset( $item['back_image'] ) ? $item['back_image'] : '' ) ),
							'permalink'  => skyyrose_product_url( $item_sku ),
							'collection' => $slug,
							'badge_text' => __( 'Pre-Order', 'skyyrose' ),
							'desc'       => isset( $item['description'] ) ? $item['description'] : '',
							'sku'        => $item_sku,
							'index'      => $index,
						);
						get_template_part( 'template-parts/product-card-holo', null, $card_args );
						++$index;
					endforeach;
				else :
					?>
					<p class="product-grid__empty">
						<?php esc_html_e( 'Products coming soon.', 'skyyrose' ); ?>
					</p>
				<?php endif; ?>
			</div>
		<?php endforeach; ?>
	</section>

	<!-- ==================== CART SUMMARY BAR ==================== -->
	<div class="cart-summary" id="cart-summary"
		aria-label="<?php esc_attr_e( 'Cart summary', 'skyyrose' ); ?>">
		<div class="cart-summary__info">
			<span class="cart-summary__count" id="cart-summary-count">
				<?php esc_html_e( '0 items', 'skyyrose' ); ?>
			</span>
			<span class="cart-summary__total" id="cart-summary-total">
				<?php echo esc_html( $currency_symbol . '0' ); ?>
			</span>
		</div>
		<a class="cart-summary__checkout"
			href="<?php echo esc_url( $checkout_url ); ?>">
			<?php esc_html_e( 'Proceed to Checkout', 'skyyrose' ); ?>
		</a>
	</div>

</main><!-- #primary -->

<?php
/*
 * GSAP entrance animations and collection-switching logic have been
 * extracted to assets/js/preorder-gateway.js (enqueued via inc/enqueue.php).
 */

get_footer();
?>
