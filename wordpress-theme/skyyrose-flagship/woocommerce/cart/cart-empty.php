<?php
/**
 * Empty Cart Page - Dark Luxury Design
 *
 * Overrides WooCommerce templates/cart/cart-empty.php.
 *
 * WooCommerce routes EMPTY carts here (WC_Shortcode_Cart::output()), never
 * into cart/cart.php — so without this override the empty state rendered
 * core's unstyled markup while cart.php's own empty branch sat unreachable.
 * Markup mirrors that branch (same .skyy-cart__empty classes; styles ship in
 * woocommerce-cart(.min).css already).
 *
 * Deliberate deviations from core, mirroring cart.php's documented approach:
 * - woocommerce_cart_is_empty is NOT fired: core hooks the default
 *   "Your cart is currently empty." notice into it, which would duplicate
 *   the styled empty state below. Plugins targeting that hook will not
 *   output here.
 * - The title is an <h2>: the cart route always renders inside page.php
 *   (template_include shell, inc/redirects.php), whose page header already
 *   provides the <h1>.
 *
 * @see     https://woocommerce.com/document/template-structure/
 * @package SkyyRose
 * @since   1.11.2
 * @version 10.8.0
 */

defined( 'ABSPATH' ) || exit;
?>

<div class="skyy-cart" data-skyy-cart>

	<?php
	// WC core prints ALL queued notices ("'X' removed. Undo?", out-of-stock
	// removals, checkout-error redirects) through this action at priority 5
	// (woocommerce_output_all_notices) — swallowing it strands the notice in
	// the session and it pops out of context on the next WC surface. Only the
	// duplicate default empty-cart message (priority 10) is unwanted here:
	// this template renders its own styled empty state below.
	remove_action( 'woocommerce_cart_is_empty', 'wc_empty_cart_message', 10 );
	do_action( 'woocommerce_cart_is_empty' );
	?>

	<div class="skyy-cart__empty">
		<div class="skyy-cart__empty-inner">
			<svg class="skyy-cart__empty-icon" width="80" height="80" viewBox="0 0 80 80" fill="none" aria-hidden="true" focusable="false">
				<path d="M20 20h5l5 30h25l5-20H30" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
				<circle cx="37" cy="58" r="3" stroke="currentColor" stroke-width="2"/>
				<circle cx="53" cy="58" r="3" stroke="currentColor" stroke-width="2"/>
			</svg>
			<?php
			// No rv-* reveal classes here: this block IS the above-fold content
			// (and likely LCP) of the empty-cart view — reveal classes hide it
			// until deferred JS runs (the PDP 24.9s-LCP bug class, fix-log Wave 1).
			?>
			<h2 class="skyy-cart__empty-title">
				<?php esc_html_e( 'Your Cart is Empty', 'skyyrose' ); ?>
			</h2>
			<p class="skyy-cart__empty-text">
				<?php esc_html_e( 'Explore our collections and find pieces that speak to you.', 'skyyrose' ); ?>
			</p>
			<?php if ( wc_get_page_id( 'shop' ) > 0 ) : ?>
				<a href="<?php echo esc_url( apply_filters( 'woocommerce_return_to_shop_redirect', wc_get_page_permalink( 'shop' ) ) ); ?>"
					class="skyy-cart__empty-cta magnetic btn-sweep">
					<?php esc_html_e( 'Explore Collections', 'skyyrose' ); ?>
				</a>
			<?php endif; ?>
		</div>
	</div>

</div>
