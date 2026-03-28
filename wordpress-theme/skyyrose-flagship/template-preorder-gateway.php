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
	<section class="hero" id="hero">
		<span class="hero__badge"><?php esc_html_e( 'Exclusive Access', 'skyyrose-flagship' ); ?></span>
		<h1 class="hero__title"><?php esc_html_e( 'Pre-Order', 'skyyrose-flagship' ); ?></h1>
		<p class="hero__tagline"><?php esc_html_e( 'Secure Your Pieces Before They Drop', 'skyyrose-flagship' ); ?></p>
		<p class="hero__subtitle"><?php esc_html_e( 'Luxury Grows from Concrete', 'skyyrose-flagship' ); ?></p>
	</section>

	<!-- ==================== SHOWCASE GRID ==================== -->
	<section class="showcase" id="showcase"
	         aria-label="<?php esc_attr_e( 'Browse collections', 'skyyrose-flagship' ); ?>">
		<div class="showcase__grid">
			<?php foreach ( $collections as $slug => $col ) : ?>
				<div class="showcase__card showcase__card--<?php echo esc_attr( $slug ); ?>"
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
 * ─── Inline GSAP Animations ─────────────────────────────────────────────────
 * Entrance animations and collection-switching logic.
 * GSAP + ScrollToPlugin loaded by the theme enqueue system.
 */
?>
<script>
(function() {
	'use strict';

	/* ── DOM References ── */
	var body            = document.body;
	var showcaseCards   = document.querySelectorAll('.showcase__card');
	var tabButtons      = document.querySelectorAll('.tab-bar__btn');
	var productSection  = document.getElementById('products-section');
	var cartSummary     = document.getElementById('cart-summary');
	var cartCountEl     = document.getElementById('cart-summary-count');
	var cartTotalEl     = document.getElementById('cart-summary-total');
	var activeCollection = null;

	/* Collection grid map */
	var grids = {};
	['black-rose', 'love-hurts', 'signature'].forEach(function(slug) {
		grids[slug] = document.getElementById('grid-' + slug);
	});

	/* ── Entrance Animations ── */
	function initEntranceAnimations() {
		if (typeof gsap === 'undefined') { return; }

		gsap.from('.hero__badge', {
			opacity: 0, y: 20, duration: 0.8, delay: 0.2, ease: 'power3.out'
		});
		gsap.from('.hero__title', {
			opacity: 0, y: 30, duration: 1, delay: 0.4, ease: 'power3.out'
		});
		gsap.from('.hero__tagline', {
			opacity: 0, y: 20, duration: 0.8, delay: 0.7, ease: 'power3.out'
		});
		gsap.from('.hero__subtitle', {
			opacity: 0, y: 15, duration: 0.8, delay: 0.9, ease: 'power3.out'
		});
		gsap.from('.showcase__card', {
			opacity: 0, y: 50, duration: 0.9, stagger: 0.15, delay: 1.1,
			ease: 'power3.out'
		});
	}

	/* ── Collection Activation ── */
	function activateCollection(slug) {
		if (activeCollection === slug) { return; }
		activeCollection = slug;

		body.setAttribute('data-active-collection', slug);

		/* Update tab bar */
		tabButtons.forEach(function(btn) {
			var isActive = btn.getAttribute('data-tab') === slug;
			btn.classList.toggle('tab-bar__btn--active', isActive);
			btn.setAttribute('aria-selected', isActive ? 'true' : 'false');
			btn.setAttribute('tabindex', isActive ? '0' : '-1');
		});

		/* Show/hide grids */
		Object.keys(grids).forEach(function(key) {
			var grid = grids[key];
			if (!grid) { return; }
			if (key === slug) {
				grid.style.display = '';
				grid.removeAttribute('hidden');
				animateGridIn(grid);
			} else {
				grid.style.display = 'none';
				grid.setAttribute('hidden', '');
			}
		});

		/* Scroll to product section */
		if (productSection && typeof gsap !== 'undefined' && gsap.plugins && gsap.plugins.scrollTo) {
			gsap.to(window, {
				scrollTo: { y: productSection, offsetY: 120 },
				duration: 0.8,
				ease: 'power3.inOut'
			});
		} else if (productSection) {
			productSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
		}
	}

	function animateGridIn(grid) {
		var cards = grid.querySelectorAll('.holo');
		if (typeof gsap === 'undefined') {
			cards.forEach(function(c) { c.classList.add('holo--visible'); });
			return;
		}

		cards.forEach(function(card) {
			card.classList.remove('holo--visible');
			card.style.opacity = '0';
			card.style.transform = 'translateY(32px)';
		});

		gsap.to(cards, {
			opacity: 1,
			y: 0,
			duration: 0.7,
			stagger: 0.1,
			ease: 'power3.out',
			delay: 0.15,
			onComplete: function() {
				cards.forEach(function(card) {
					card.classList.add('holo--visible');
					card.style.transform = '';
					card.style.opacity = '';
				});
			}
		});
	}

	/* ── Event Listeners ── */
	showcaseCards.forEach(function(card) {
		card.addEventListener('click', function() {
			var slug = card.getAttribute('data-collection');
			if (slug) { activateCollection(slug); }
		});
		card.addEventListener('keydown', function(e) {
			if (e.key === 'Enter' || e.key === ' ') {
				e.preventDefault();
				var slug = card.getAttribute('data-collection');
				if (slug) { activateCollection(slug); }
			}
		});
	});

	tabButtons.forEach(function(btn) {
		btn.addEventListener('click', function() {
			var slug = btn.getAttribute('data-tab');
			if (slug) { activateCollection(slug); }
		});
	});

	/* ── Cart Summary UI (mirrors WooCommerce mini-cart state) ── */
	function updateCartSummary() {
		if (!cartSummary) { return; }
		var countEl = document.querySelector('.nav-cart-count, .cart-contents .count');
		var count   = countEl ? parseInt(countEl.textContent, 10) || 0 : 0;

		if (count > 0) {
			cartSummary.classList.add('cart-summary--visible');
			if (cartCountEl) {
				cartCountEl.textContent = count + (count === 1
					? ' <?php echo esc_js( __( 'item', 'skyyrose-flagship' ) ); ?>'
					: ' <?php echo esc_js( __( 'items', 'skyyrose-flagship' ) ); ?>');
			}
		} else {
			cartSummary.classList.remove('cart-summary--visible');
		}
	}

	/* Listen for WooCommerce fragment updates */
	if (typeof jQuery !== 'undefined') {
		jQuery(document.body).on('added_to_cart removed_from_cart wc_fragments_refreshed', updateCartSummary);
	}

	/* ── Init ── */
	initEntranceAnimations();
	updateCartSummary();
})();
</script>

<?php get_footer(); ?>
