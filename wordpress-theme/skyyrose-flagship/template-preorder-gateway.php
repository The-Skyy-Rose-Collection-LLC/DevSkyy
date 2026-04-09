<?php
/**
 * Template Name: Pre-Order Gateway
 *
 * High-converting pre-order hub. Scrolling layout with all collections
 * displayed vertically, CRO sections (trust, reviews, value props, FAQ),
 * and holo product cards powered by the centralized product catalog.
 *
 * @package SkyyRose_Flagship
 * @since   2.0.0
 * @updated 7.0.0 — CRO transformation: scrolling grids, trust bar, reviews, FAQ
 */

defined( 'ABSPATH' ) || exit;

/*
 * ─── Collection Configuration ───────────────────────────────────────────────
 */
$collections = array(
	'black-rose' => array(
		'label'    => 'Black Rose',
		'tagline'  => 'Dark Elegance. Gothic Luxury.',
		'accent'   => '#C0C0C0',
	),
	'love-hurts' => array(
		'label'    => 'Love Hurts',
		'tagline'  => 'Beauty Meets the Beast.',
		'accent'   => '#DC143C',
	),
	'signature'  => array(
		'label'    => 'Signature',
		'tagline'  => 'The Origin. The Crown.',
		'accent'   => '#D4AF37',
	),
);

/*
 * ─── Build Pre-Order Product Lists ─────────────────────────────────────────
 *
 * Source of truth: product-catalog.php → is_preorder flag.
 * WooCommerce overlay: if a matching WC product exists by SKU, use it
 * for live pricing and add-to-cart. Otherwise, static catalog card.
 */
$preorder_by_collection = array();
$total_preorder_count   = 0;
$has_wc                 = function_exists( 'wc_get_product_id_by_sku' );

if ( function_exists( 'skyyrose_get_product_catalog' ) ) {
	$catalog = skyyrose_get_product_catalog();

	foreach ( $catalog as $cat ) {
		if ( empty( $cat['is_preorder'] ) ) {
			continue;
		}

		$col = $cat['collection'];
		if ( ! isset( $collections[ $col ] ) ) {
			continue;
		}

		// Try to match to a WC product for live pricing + add-to-cart.
		$wc_product = null;
		if ( $has_wc ) {
			$pid = wc_get_product_id_by_sku( $cat['sku'] );
			if ( ! $pid && function_exists( 'skyyrose_normalize_sku' ) ) {
				$pid = wc_get_product_id_by_sku( skyyrose_normalize_sku( $cat['sku'] ) );
			}
			if ( $pid ) {
				$wc_product = wc_get_product( $pid );
			}
		}

		if ( $wc_product ) {
			$preorder_by_collection[ $col ][] = array(
				'type'    => 'wc',
				'product' => $wc_product,
				'catalog' => $cat,
			);
		} else {
			$preorder_by_collection[ $col ][] = array(
				'type'    => 'static',
				'catalog' => $cat,
			);
		}

		$total_preorder_count++;
	}
}

$currency_symbol = function_exists( 'get_woocommerce_currency_symbol' )
	? html_entity_decode( get_woocommerce_currency_symbol(), ENT_QUOTES, 'UTF-8' )
	: '$';

get_header();
?>

<main id="primary" class="site-main preorder-gateway" role="main" tabindex="-1">

	<!-- ==================== 1. HERO ==================== -->
	<section class="po-hero" id="hero">
		<span class="po-hero__badge"><?php esc_html_e( 'Pre-Order Open — Limited Numbered Pieces', 'skyyrose-flagship' ); ?></span>
		<h1 class="po-hero__title"><?php esc_html_e( 'Pre-Order', 'skyyrose-flagship' ); ?></h1>
		<p class="po-hero__tagline"><?php esc_html_e( 'Luxury Grows from Concrete.', 'skyyrose-flagship' ); ?></p>

		<div class="po-hero__countdown" data-countdown="72h" aria-label="<?php esc_attr_e( 'Pre-order countdown', 'skyyrose-flagship' ); ?>">
			<div class="po-countdown__unit">
				<span class="po-countdown__num" data-cd="d">00</span>
				<span class="po-countdown__label"><?php esc_html_e( 'Days', 'skyyrose-flagship' ); ?></span>
			</div>
			<span class="po-countdown__sep" aria-hidden="true">:</span>
			<div class="po-countdown__unit">
				<span class="po-countdown__num" data-cd="h">00</span>
				<span class="po-countdown__label"><?php esc_html_e( 'Hours', 'skyyrose-flagship' ); ?></span>
			</div>
			<span class="po-countdown__sep" aria-hidden="true">:</span>
			<div class="po-countdown__unit">
				<span class="po-countdown__num" data-cd="m">00</span>
				<span class="po-countdown__label"><?php esc_html_e( 'Min', 'skyyrose-flagship' ); ?></span>
			</div>
			<span class="po-countdown__sep" aria-hidden="true">:</span>
			<div class="po-countdown__unit">
				<span class="po-countdown__num" data-cd="s">00</span>
				<span class="po-countdown__label"><?php esc_html_e( 'Sec', 'skyyrose-flagship' ); ?></span>
			</div>
		</div>

		<div class="po-hero__ctas">
			<a href="#collections" class="po-btn po-btn--primary"><?php esc_html_e( 'Shop Collections', 'skyyrose-flagship' ); ?></a>
			<a href="#craft" class="po-btn po-btn--secondary"><?php esc_html_e( 'How It Works', 'skyyrose-flagship' ); ?></a>
		</div>

		<div class="po-hero__scroll" aria-hidden="true">
			<span><?php esc_html_e( 'Scroll', 'skyyrose-flagship' ); ?></span>
			<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
		</div>
	</section>

	<!-- ==================== 2. TRUST BAR ==================== -->
	<div class="po-trust po-rv" aria-label="<?php esc_attr_e( 'Pre-order benefits', 'skyyrose-flagship' ); ?>">
		<div class="po-trust__item">
			<svg class="po-trust__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
			<span><?php esc_html_e( 'Numbered Edition', 'skyyrose-flagship' ); ?></span>
		</div>
		<div class="po-trust__item">
			<svg class="po-trust__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18.36 6.64a9 9 0 1 1-12.73 0"/><line x1="12" y1="2" x2="12" y2="12"/></svg>
			<span><?php esc_html_e( 'Never Restocked', 'skyyrose-flagship' ); ?></span>
		</div>
		<div class="po-trust__item">
			<svg class="po-trust__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
			<span><?php esc_html_e( 'Secure Checkout', 'skyyrose-flagship' ); ?></span>
		</div>
		<div class="po-trust__item">
			<svg class="po-trust__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>
			<span><?php esc_html_e( 'Ships Spring 2026', 'skyyrose-flagship' ); ?></span>
		</div>
	</div>

	<!-- ==================== 3. COLLECTION GRIDS ==================== -->
	<div id="collections">
	<?php
	$collection_index = 0;
	foreach ( $collections as $slug => $col ) :
		$items = isset( $preorder_by_collection[ $slug ] ) ? $preorder_by_collection[ $slug ] : array();
		if ( empty( $items ) ) {
			continue;
		}

		// Price range for this collection.
		$prices = array_map( function ( $item ) {
			return (float) $item['catalog']['price'];
		}, $items );
		$min_price = min( $prices );
		$max_price = max( $prices );
		$price_range = ( $min_price === $max_price )
			? $currency_symbol . number_format( $min_price, 0 )
			: $currency_symbol . number_format( $min_price, 0 ) . '–' . $currency_symbol . number_format( $max_price, 0 );
	?>
		<section class="po-collection" id="collection-<?php echo esc_attr( $slug ); ?>"
		         data-collection="<?php echo esc_attr( $slug ); ?>">

			<div class="po-collection__header po-rv">
				<span class="po-collection__number"><?php
					printf(
						/* translators: %d: collection number */
						esc_html__( 'Collection %02d', 'skyyrose-flagship' ),
						$collection_index + 1
					);
				?></span>
				<h2 class="po-collection__title"><?php echo esc_html( $col['label'] ); ?></h2>
				<p class="po-collection__tagline"><?php echo esc_html( $col['tagline'] ); ?></p>
				<div class="po-collection__meta">
					<span class="po-collection__count"><?php
						printf(
							esc_html( _n( '%d piece', '%d pieces', count( $items ), 'skyyrose-flagship' ) ),
							count( $items )
						);
					?></span>
					<span class="po-collection__divider" aria-hidden="true">&bull;</span>
					<span class="po-collection__range"><?php echo esc_html( $price_range ); ?></span>
					<span class="po-collection__divider" aria-hidden="true">&bull;</span>
					<span class="po-collection__edition"><?php esc_html_e( 'Limited Edition', 'skyyrose-flagship' ); ?></span>
				</div>
			</div>

			<div class="po-collection__grid">
				<?php
				$card_index = 0;
				foreach ( $items as $item ) :
					if ( 'wc' === $item['type'] ) {
						$card_args = array(
							'product'    => $item['product'],
							'collection' => $slug,
							'badge_text' => __( 'Pre-Order', 'skyyrose-flagship' ),
							'index'      => $card_index,
						);
					} else {
						$cat = $item['catalog'];
						$card_args = array(
							'title'      => $cat['name'],
							'price'      => skyyrose_format_price( $cat ),
							'image_url'  => skyyrose_product_image_uri( $cat['front_model_image'] ?: $cat['image'] ),
							'image_back' => ! empty( $cat['back_image'] ) ? skyyrose_product_image_uri( $cat['back_image'] ) : '',
							'permalink'  => '#',
							'collection' => $slug,
							'badge_text' => $cat['badge'],
							'desc'       => $cat['description'],
							'sku'        => $cat['sku'],
							'index'      => $card_index,
						);
					}

					get_template_part( 'template-parts/product-card-holo', null, $card_args );
					$card_index++;
				endforeach;
				?>
			</div>

		</section>
	<?php
		$collection_index++;
	endforeach;
	?>
	</div>

	<!-- ==================== CART SUMMARY BAR ==================== -->
	<div class="po-cart-summary" id="cart-summary"
	     aria-label="<?php esc_attr_e( 'Cart summary', 'skyyrose-flagship' ); ?>">
		<div class="po-cart-summary__info">
			<span class="po-cart-summary__count" id="cart-summary-count">
				<?php esc_html_e( '0 items', 'skyyrose-flagship' ); ?>
			</span>
			<span class="po-cart-summary__total" id="cart-summary-total">
				<?php echo esc_html( $currency_symbol . '0' ); ?>
			</span>
		</div>
		<a class="po-cart-summary__checkout"
		   href="<?php echo esc_url( function_exists( 'wc_get_checkout_url' ) ? wc_get_checkout_url() : '#' ); ?>">
			<?php esc_html_e( 'Proceed to Checkout', 'skyyrose-flagship' ); ?>
		</a>
	</div>

</main><!-- #primary -->

<?php get_footer(); ?>
