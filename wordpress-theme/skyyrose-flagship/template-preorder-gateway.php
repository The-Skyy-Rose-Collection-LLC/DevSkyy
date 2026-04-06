<?php
/**
 * Template Name: Pre-Order Gateway
 *
 * Showcase-style pre-order page with hero, interactive collection selector grid,
 * tabbed product grids using holo cards, sticky cart summary bar, and GSAP
 * entrance/collection-switching animations. Dark luxury aesthetic.
 *
 * @package SkyyRose_Flagship
 * @since   2.0.0
 * @updated 6.0.0 — complete rewrite from static pre-order.html
 */

defined( 'ABSPATH' ) || exit;

/*
 * ─── Collection Configuration ───────────────────────────────────────────────
 */
$collections = array(
	'black-rose' => array(
		'label'    => esc_html__( 'Black Rose', 'skyyrose-flagship' ),
		'tagline'  => esc_html__( 'The Beauty of Black', 'skyyrose-flagship' ),
		'number'   => esc_html__( 'Collection 01', 'skyyrose-flagship' ),
		'subtitle' => esc_html__( 'Dark Elegance', 'skyyrose-flagship' ),
	),
	'love-hurts' => array(
		'label'    => esc_html__( 'Love Hurts', 'skyyrose-flagship' ),
		'tagline'  => esc_html__( 'The Hurts Bloodline', 'skyyrose-flagship' ),
		'number'   => esc_html__( 'Collection 02', 'skyyrose-flagship' ),
		'subtitle' => esc_html__( 'The Hurts Bloodline', 'skyyrose-flagship' ),
	),
	'signature'  => array(
		'label'    => esc_html__( 'Signature', 'skyyrose-flagship' ),
		'tagline'  => esc_html__( 'The Origin. The Crown.', 'skyyrose-flagship' ),
		'number'   => esc_html__( 'Collection 03', 'skyyrose-flagship' ),
		'subtitle' => esc_html__( 'The Origin. The Crown.', 'skyyrose-flagship' ),
	),
);

/*
 * ─── Static fallback products (used when WooCommerce is unavailable) ────────
 */
$fallback_products = array(
	'black-rose' => array(
		array( 'name' => 'Black Rose Classic Hoodie', 'price' => 65, 'sku' => 'br-hoodie' ),
		array( 'name' => 'Obsidian Tee',              'price' => 40, 'sku' => 'br-tee' ),
		array( 'name' => 'Dark Bloom Jacket',          'price' => 95, 'sku' => 'br-jacket' ),
		array( 'name' => 'Midnight Crewneck',           'price' => 55, 'sku' => 'br-crew' ),
	),
	'love-hurts' => array(
		array( 'name' => 'Enchanted Rose Hoodie', 'price' => 65, 'sku' => 'lh-hoodie' ),
		array( 'name' => 'Beast Mode Tee',         'price' => 40, 'sku' => 'lh-tee' ),
		array( 'name' => 'Thorned Heart Jacket',   'price' => 95, 'sku' => 'lh-jacket' ),
		array( 'name' => 'Bloodline Crewneck',      'price' => 55, 'sku' => 'lh-crew' ),
	),
	'signature'  => array(
		array( 'name' => 'Signature Rose Hoodie', 'price' => 65, 'sku' => 'sg-hoodie' ),
		array( 'name' => 'Script Logo Tee',        'price' => 40, 'sku' => 'sg-tee' ),
		array( 'name' => 'Gold Standard Jacket',   'price' => 95, 'sku' => 'sg-jacket' ),
		array( 'name' => 'Heritage Crewneck',       'price' => 55, 'sku' => 'sg-crew' ),
	),
);

/*
 * ─── Query WooCommerce Products (with static fallback) ──────────────────────
 */
$products_by_collection = array();

if ( function_exists( 'wc_get_products' ) ) {
	foreach ( array_keys( $collections ) as $slug ) {
		$wc_products = wc_get_products( array(
			'status'   => 'publish',
			'limit'    => 12,
			'category' => array( $slug ),
			'orderby'  => 'menu_order',
			'order'    => 'ASC',
		) );
		$products_by_collection[ $slug ] = ! empty( $wc_products ) ? $wc_products : array();
	}
}

// If WooCommerce returned nothing or is unavailable, use static fallback.
foreach ( array_keys( $collections ) as $slug ) {
	if ( empty( $products_by_collection[ $slug ] ) && isset( $fallback_products[ $slug ] ) ) {
		$products_by_collection[ $slug ] = $fallback_products[ $slug ];
	}
}

$currency_symbol = function_exists( 'get_woocommerce_currency_symbol' )
	? html_entity_decode( get_woocommerce_currency_symbol(), ENT_QUOTES, 'UTF-8' )
	: '$';

$checkout_url = function_exists( 'wc_get_checkout_url' ) ? wc_get_checkout_url() : '#';

get_header();
?>

<main id="primary" class="site-main preorder-gateway" role="main" tabindex="-1">

	<!-- ==================== HERO ==================== -->
	<section class="hero" id="hero" data-scroll-fade>
		<span class="hero__badge rv-blur-down"><?php esc_html_e( 'Exclusive Access', 'skyyrose-flagship' ); ?></span>
		<h1 class="hero__title rv-split-char"><?php esc_html_e( 'Pre-Order', 'skyyrose-flagship' ); ?></h1>
		<p class="hero__tagline rv-split-word"><?php esc_html_e( 'Secure Your Pieces Before They Drop', 'skyyrose-flagship' ); ?></p>
		<p class="hero__subtitle rv-blur"><?php esc_html_e( 'Luxury Grows from Concrete', 'skyyrose-flagship' ); ?></p>
	</section>

	<!-- ==================== SHOWCASE GRID ==================== -->
	<section class="showcase" id="showcase"
	         aria-label="<?php esc_attr_e( 'Browse collections', 'skyyrose-flagship' ); ?>">
		<div class="showcase__grid stagger-grid">
			<?php foreach ( $collections as $slug => $col ) : ?>
				<div class="showcase__card showcase__card--<?php echo esc_attr( $slug ); ?> magnetic"
				     data-collection="<?php echo esc_attr( $slug ); ?>"
				     role="button"
				     tabindex="0"
				     aria-label="<?php echo esc_attr( sprintf(
						/* translators: %s: collection name */
						__( 'Explore %s collection', 'skyyrose-flagship' ),
						$col['label']
					) ); ?>">
					<span class="showcase__card-number"><?php echo esc_html( $col['number'] ); ?></span>
					<h2 class="showcase__card-title"><?php echo esc_html( $col['label'] ); ?></h2>
					<p class="showcase__card-tagline"><?php echo esc_html( $col['tagline'] ); ?></p>
					<span class="showcase__card-cta"><?php
						echo wp_kses(
							__( 'Explore Collection &rarr;', 'skyyrose-flagship' ),
							array()
						);
					?></span>
				</div>
			<?php endforeach; ?>
		</div>
	</section>

	<!-- ==================== COLLECTION TAB BAR ==================== -->
	<div class="tab-bar" id="tab-bar" role="tablist"
	     aria-label="<?php esc_attr_e( 'Filter by collection', 'skyyrose-flagship' ); ?>">
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
	         aria-label="<?php esc_attr_e( 'Pre-order products', 'skyyrose-flagship' ); ?>">
		<?php foreach ( $collections as $slug => $col ) :
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
						<?php esc_html_e( 'Limited Edition', 'skyyrose-flagship' ); ?>
					</p>
				</div>

				<?php if ( ! empty( $items ) ) :
					$index = 0;
					foreach ( $items as $item ) :
						if ( $item instanceof WC_Product ) {
							$card_args = array(
								'product'    => $item,
								'collection' => $slug,
								'badge_text' => __( 'Pre-Order', 'skyyrose-flagship' ),
								'index'      => $index,
							);
						} else {
							$card_args = array(
								'title'      => isset( $item['name'] ) ? $item['name'] : '',
								'price'      => $currency_symbol . number_format( isset( $item['price'] ) ? (float) $item['price'] : 0, 0 ),
								'image_url'  => '',
								'permalink'  => '#',
								'collection' => $slug,
								'badge_text' => __( 'Pre-Order', 'skyyrose-flagship' ),
								'desc'       => isset( $item['description'] ) ? $item['description'] : '',
								'sku'        => isset( $item['sku'] ) ? $item['sku'] : '',
								'index'      => $index,
							);
						}
						get_template_part( 'template-parts/product-card-holo', null, $card_args );
						$index++;
					endforeach;
				else : ?>
					<p class="product-grid__empty">
						<?php esc_html_e( 'Products coming soon.', 'skyyrose-flagship' ); ?>
					</p>
				<?php endif; ?>
			</div>
		<?php endforeach; ?>
	</section>

	<!-- ==================== CART SUMMARY BAR ==================== -->
	<div class="cart-summary" id="cart-summary"
	     aria-label="<?php esc_attr_e( 'Cart summary', 'skyyrose-flagship' ); ?>">
		<div class="cart-summary__info">
			<span class="cart-summary__count" id="cart-summary-count">
				<?php esc_html_e( '0 items', 'skyyrose-flagship' ); ?>
			</span>
			<span class="cart-summary__total" id="cart-summary-total">
				<?php echo esc_html( $currency_symbol . '0' ); ?>
			</span>
		</div>
		<a class="cart-summary__checkout"
		   href="<?php echo esc_url( $checkout_url ); ?>">
			<?php esc_html_e( 'Proceed to Checkout', 'skyyrose-flagship' ); ?>
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
