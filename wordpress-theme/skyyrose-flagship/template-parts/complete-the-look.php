<?php
/**
 * Complete the Look — WooCommerce Product Page Cross-Sell Partial
 *
 * Shows 1-2 complementary products from the same collection beneath the
 * add-to-cart button on single product pages. Cross-sell pairs are defined
 * via a curated map. Falls back to WooCommerce related products if no
 * explicit pair is found.
 *
 * Hooked into: woocommerce_single_product_summary (priority 50)
 * Called by:   inc/woocommerce.php → skyyrose_complete_the_look()
 *
 * @package SkyyRose_Flagship
 * @since   5.0.0
 */

if ( ! defined( 'ABSPATH' ) ) { exit; }

global $product;
if ( ! $product ) { return; }

$current_id  = $product->get_id();
$current_sku = $product->get_sku();

// Curated cross-sell pairs: sku → array of related skus.
$cross_sell_map = array(
	// Black Rose
	'br-004' => array( 'br-002', 'br-006' ),  // Hoodie → Joggers, Sherpa
	'br-002' => array( 'br-004', 'br-006' ),  // Joggers → Hoodie, Sherpa
	'br-006' => array( 'br-004', 'br-002' ),  // Sherpa → Hoodie, Joggers
	'br-005' => array( 'br-004', 'br-002' ),  // Hoodie Sig Ed → Hoodie, Joggers
	'br-007' => array( 'br-004', 'br-002' ),  // Basketball Shorts → Hoodie, Joggers
	// Jersey Series — pair with each other
	'br-008' => array( 'br-009', 'br-010' ),
	'br-009' => array( 'br-008', 'br-011' ),
	'br-010' => array( 'br-008', 'br-009' ),
	'br-011' => array( 'br-009', 'br-010' ),
	// Love Hurts
	'lh-004' => array( 'lh-003', 'lh-002' ),  // Varsity → Shorts, Joggers
	'lh-002' => array( 'lh-003', 'lh-006' ),  // Joggers → Shorts, Fannie
	'lh-003' => array( 'lh-002', 'lh-004' ),  // Shorts → Joggers, Varsity
	'lh-006' => array( 'lh-002', 'lh-003' ),  // Fannie → Joggers, Shorts
	// Signature
	'sg-006' => array( 'sg-014', 'sg-013' ),  // Mint & Lavender Hoodie → Sweatpants, Crewneck
	'sg-014' => array( 'sg-006', 'sg-013' ),  // Sweatpants → Hoodie, Crewneck
	'sg-001' => array( 'sg-002', 'sg-003' ),  // Bay Bridge Shorts → Stay Golden Shirt + Shorts
	'sg-002' => array( 'sg-003', 'sg-001' ),  // Stay Golden Shirt → Shorts, Bay Bridge
	'sg-003' => array( 'sg-002', 'sg-006' ),  // Stay Golden Shorts → Shirt, Hoodie
	'sg-004' => array( 'sg-006', 'sg-014' ),  // Signature Hoodie → Mint Hoodie, Sweatpants
	'sg-009' => array( 'sg-006', 'sg-004' ),  // Sherpa → Hoodies
	'sg-010' => array( 'sg-001', 'sg-002' ),  // Bridge Series Shorts → Bay Bridge, Stay Golden
	'sg-011' => array( 'sg-002', 'sg-010' ),  // Original Label Tee White → Stay Golden, Bridge Shorts
	'sg-012' => array( 'sg-011', 'sg-006' ),  // Original Label Tee Orchid → White Tee, Hoodie
	'sg-013' => array( 'sg-006', 'sg-014' ),  // Mint Crewneck → Hoodie, Sweatpants
);

$related_skus = isset( $cross_sell_map[ $current_sku ] ) ? $cross_sell_map[ $current_sku ] : array();

// Limit to 2 recommendations max.
$related_skus = array_slice( $related_skus, 0, 2 );

if ( empty( $related_skus ) ) { return; }

// Resolve SKUs to WooCommerce products.
$related_products = array();
foreach ( $related_skus as $rel_sku ) {
	$rel_id = function_exists( 'wc_get_product_id_by_sku' ) ? wc_get_product_id_by_sku( $rel_sku ) : 0;
	if ( ! $rel_id ) { continue; }
	$rel_product = wc_get_product( $rel_id );
	if ( $rel_product && 'publish' === get_post_status( $rel_id ) ) {
		$related_products[] = $rel_product;
	}
}

if ( empty( $related_products ) ) { return; }

$collection     = function_exists( 'skyyrose_get_product_collection' ) ? skyyrose_get_product_collection( $current_id ) : 'default';
$config         = function_exists( 'skyyrose_collection_config' ) ? skyyrose_collection_config( $collection ) : array( 'accent' => '#B76E79' );
$accent         = esc_attr( $config['accent'] ?? '#B76E79' );
?>
<section class="sr-complete-look" aria-label="<?php esc_attr_e( 'Complete the Look', 'skyyrose-flagship' ); ?>"
	style="--sr-cl-accent: <?php echo $accent; ?>;">
	<h3 class="sr-complete-look__heading">
		<?php esc_html_e( 'Complete the Look', 'skyyrose-flagship' ); ?>
		<span class="sr-complete-look__badge"><?php esc_html_e( 'Save 10% when added', 'skyyrose-flagship' ); ?></span>
	</h3>

	<div class="sr-complete-look__track">
		<?php foreach ( $related_products as $rel ) : ?>
		<?php
		$rel_id        = $rel->get_id();
		$rel_name      = $rel->get_name();
		$rel_price     = $rel->get_price_html();
		$rel_url       = get_permalink( $rel_id );
		$rel_img_id    = $rel->get_image_id();
		$rel_img       = $rel_img_id
			? wp_get_attachment_image( $rel_img_id, 'woocommerce_thumbnail', false, array( 'class' => 'sr-cl-card__img', 'loading' => 'lazy' ) )
			: wc_placeholder_img( 'woocommerce_thumbnail', array( 'class' => 'sr-cl-card__img' ) );
		$is_preorder   = function_exists( 'skyyrose_is_preorder' ) && skyyrose_is_preorder( $rel_id );
		$btn_text      = $is_preorder ? __( 'Pre-Order', 'skyyrose-flagship' ) : __( 'Quick Add', 'skyyrose-flagship' );
		?>
		<div class="sr-cl-card" data-product-id="<?php echo esc_attr( $rel_id ); ?>">
			<a href="<?php echo esc_url( $rel_url ); ?>" class="sr-cl-card__image-link" tabindex="-1" aria-hidden="true">
				<?php echo $rel_img; ?>
			</a>
			<a href="<?php echo esc_url( $rel_url ); ?>" class="sr-cl-card__name">
				<?php echo esc_html( $rel_name ); ?>
			</a>
			<div class="sr-cl-card__price"><?php echo $rel_price; ?></div>
			<button
				type="button"
				class="sr-cl-card__add"
				data-product-id="<?php echo esc_attr( $rel_id ); ?>"
				data-product-name="<?php echo esc_attr( $rel_name ); ?>"
				data-nonce="<?php echo esc_attr( wp_create_nonce( 'skyyrose-woo-nonce' ) ); ?>"
				aria-label="<?php echo esc_attr( sprintf( __( 'Add %s to cart', 'skyyrose-flagship' ), $rel_name ) ); ?>"
			><?php echo esc_html( $btn_text ); ?></button>
		</div>
		<?php endforeach; ?>
	</div>
</section>

<script>
(function () {
	'use strict';
	var section = document.querySelector('.sr-complete-look');
	if (!section) return;

	var ajaxUrl = (typeof skyyRoseWoo !== 'undefined' && skyyRoseWoo.ajaxUrl)
		? skyyRoseWoo.ajaxUrl
		: (typeof skyyRoseData !== 'undefined' && skyyRoseData.ajaxUrl)
		? skyyRoseData.ajaxUrl
		: '/wp-admin/admin-ajax.php';

	section.querySelectorAll('.sr-cl-card__add').forEach(function (btn) {
		btn.addEventListener('click', function () {
			var pid   = btn.dataset.productId;
			var nonce = btn.dataset.nonce;
			var orig  = btn.textContent;
			if (!pid) return;

			btn.disabled = true;
			btn.textContent = '\u2026';

			var body = new URLSearchParams();
			body.set('action', 'skyyrose_get_cart_count'); // reuse WC nonce validation flow
			body.set('add-to-cart', pid);
			body.set('quantity', '1');
			body.set('nonce', nonce);

			// Use WooCommerce standard add-to-cart AJAX.
			var wcUrl = (typeof wc_add_to_cart_params !== 'undefined')
				? wc_add_to_cart_params.ajax_url
				: ajaxUrl;

			fetch(wcUrl + '?wc-ajax=add_to_cart', {
				method: 'POST',
				headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
				body: 'product_id=' + encodeURIComponent(pid) + '&quantity=1',
			})
			.then(function (r) { return r.json(); })
			.then(function (resp) {
				btn.textContent = resp.error ? orig : 'Added \u2713';
				btn.disabled = false;
				if (!resp.error && typeof jQuery !== 'undefined') {
					jQuery(document.body).trigger('wc_fragment_refresh');
				}
				setTimeout(function () { btn.textContent = orig; }, 2500);
			})
			.catch(function () { btn.textContent = orig; btn.disabled = false; });
		});
	});
}());
</script>
