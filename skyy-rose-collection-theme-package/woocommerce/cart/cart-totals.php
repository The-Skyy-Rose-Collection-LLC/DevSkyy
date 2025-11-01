<?php
/**
 * Cart totals
 *
 * This template can be overridden by copying it to yourtheme/woocommerce/cart/cart-totals.php.
 * Enhanced with Skyy Rose Collection luxury styling and AI-powered features.
 *
 * @package WP_Mastery_WooCommerce_Luxury
 * @version 2.3.6
 */

// Prevent direct access
if (!defined('ABSPATH')) {
	exit;
}

?>
<div class="cart_totals <?php echo (WC()->customer->has_calculated_shipping()) ? 'calculated_shipping' : ''; ?> skyy-rose-cart-totals">

	<?php do_action('woocommerce_before_cart_totals'); ?>

	<!-- Skyy Rose Collection Cart Summary Header -->
	<div class="cart-totals-header">
		<h2 class="cart-totals-title"><?php esc_html_e('Order Summary', 'wp-mastery-woocommerce-luxury'); ?></h2>
		<div class="luxury-divider"></div>
	</div>

	<table cellspacing="0" class="shop_table shop_table_responsive luxury-totals-table">

		<!-- Cart Subtotal -->
		<tr class="cart-subtotal">
			<th class="totals-label"><?php esc_html_e('Subtotal', 'wp-mastery-woocommerce-luxury'); ?></th>
			<td class="totals-value" data-title="<?php esc_attr_e('Subtotal', 'wp-mastery-woocommerce-luxury'); ?>">
				<span class="luxury-price"><?php wc_cart_totals_subtotal_html(); ?></span>
			</td>
		</tr>

		<!-- AI-Powered Savings Display -->
		<tr class="ai-savings-row" id="ai-savings-display" style="display: none;">
			<th class="totals-label">
				<span class="savings-icon">💎</span>
				<?php esc_html_e('AI Savings', 'wp-mastery-woocommerce-luxury'); ?>
			</th>
			<td class="totals-value savings-value">
				<span class="luxury-price savings-amount" id="ai-calculated-savings">-</span>
				<small class="savings-note"><?php esc_html_e('Personalized discount applied', 'wp-mastery-woocommerce-luxury'); ?></small>
			</td>
		</tr>

		<?php foreach (WC()->cart->get_coupons() as $code => $coupon) : ?>
			<tr class="cart-discount coupon-<?php echo esc_attr(sanitize_title($code)); ?>">
				<th class="totals-label">
					<span class="coupon-icon">🎫</span>
					<?php wc_cart_totals_coupon_label($coupon); ?>
				</th>
				<td class="totals-value coupon-value" data-title="<?php echo esc_attr(wc_cart_totals_coupon_label($coupon, false)); ?>">
					<span class="luxury-price discount-amount"><?php wc_cart_totals_coupon_html($coupon); ?></span>
				</td>
			</tr>
		<?php endforeach; ?>

		<?php if (WC()->cart->needs_shipping() && WC()->cart->show_shipping()) : ?>

			<?php do_action('woocommerce_cart_totals_before_shipping'); ?>

			<?php wc_cart_totals_shipping_html(); ?>

			<?php do_action('woocommerce_cart_totals_after_shipping'); ?>

		<?php elseif (WC()->cart->needs_shipping() && 'yes' === get_option('woocommerce_enable_shipping_calc')) : ?>

			<tr class="shipping">
				<th class="totals-label"><?php esc_html_e('Shipping', 'wp-mastery-woocommerce-luxury'); ?></th>
				<td class="totals-value" data-title="<?php esc_attr_e('Shipping', 'wp-mastery-woocommerce-luxury'); ?>">
					<?php woocommerce_shipping_calculator(); ?>
				</td>
			</tr>

		<?php endif; ?>

		<?php foreach (WC()->cart->get_fees() as $fee) : ?>
			<tr class="fee">
				<th class="totals-label"><?php echo esc_html($fee->name); ?></th>
				<td class="totals-value" data-title="<?php echo esc_attr($fee->name); ?>">
					<span class="luxury-price"><?php wc_cart_totals_fee_html($fee); ?></span>
				</td>
			</tr>
		<?php endforeach; ?>

		<?php
		if (wc_tax_enabled() && !WC()->cart->display_prices_including_tax()) {
			$taxable_address = WC()->customer->get_taxable_address();
			$estimated_text  = '';

			if (WC()->customer->is_customer_outside_base() && !WC()->customer->has_calculated_shipping()) {
				/* translators: %s location. */
				$estimated_text = sprintf(' <small>' . esc_html__('(estimated for %s)', 'wp-mastery-woocommerce-luxury') . '</small>', WC()->countries->estimated_for_prefix($taxable_address[0]) . WC()->countries->countries[$taxable_address[0]]);
			}

			if ('itemized' === get_option('woocommerce_tax_total_display')) {
				foreach (WC()->cart->get_tax_totals() as $code => $tax) { // phpcs:ignore WordPress.WP.GlobalVariablesOverride.Prohibited
					?>
					<tr class="tax-rate tax-rate-<?php echo esc_attr(sanitize_title($code)); ?>">
						<th class="totals-label"><?php echo esc_html($tax->label) . $estimated_text; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?></th>
						<td class="totals-value" data-title="<?php echo esc_attr($tax->label); ?>">
							<span class="luxury-price"><?php echo wp_kses_post($tax->formatted_amount); ?></span>
						</td>
					</tr>
					<?php
				}
			} else {
				?>
				<tr class="tax-total">
					<th class="totals-label"><?php echo esc_html(WC()->countries->tax_or_vat()) . $estimated_text; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?></th>
					<td class="totals-value" data-title="<?php echo esc_attr(WC()->countries->tax_or_vat()); ?>">
						<span class="luxury-price"><?php wc_cart_totals_taxes_total_html(); ?></span>
					</td>
				</tr>
				<?php
			}
		}
		?>

		<?php do_action('woocommerce_cart_totals_before_order_total'); ?>

		<!-- Order Total with Luxury Styling -->
		<tr class="order-total luxury-order-total">
			<th class="totals-label total-label">
				<span class="total-icon">💎</span>
				<?php esc_html_e('Total', 'wp-mastery-woocommerce-luxury'); ?>
			</th>
			<td class="totals-value total-value" data-title="<?php esc_attr_e('Total', 'wp-mastery-woocommerce-luxury'); ?>">
				<span class="luxury-price total-amount"><?php wc_cart_totals_order_total_html(); ?></span>
			</td>
		</tr>

		<?php do_action('woocommerce_cart_totals_after_order_total'); ?>

	</table>

	<!-- AI-Powered Checkout Optimization -->
	<div class="ai-checkout-optimization" id="checkout-ai-features">
		<!-- Dynamic Pricing Insights -->
		<div class="pricing-insights" id="dynamic-pricing-insights">
			<div class="insight-card">
				<div class="insight-icon">📈</div>
				<div class="insight-content">
					<h4 class="insight-title"><?php esc_html_e('Price Trend', 'wp-mastery-woocommerce-luxury'); ?></h4>
					<p class="insight-text" id="price-trend-analysis"><?php esc_html_e('Analyzing market trends...', 'wp-mastery-woocommerce-luxury'); ?></p>
				</div>
			</div>
		</div>

		<!-- Urgency Indicators -->
		<div class="urgency-indicators" id="ai-urgency-signals">
			<!-- Populated by AI analysis -->
		</div>

		<!-- Personalized Offers -->
		<div class="personalized-offers" id="ai-personalized-offers">
			<!-- Populated by customer segmentation AI -->
		</div>
	</div>

	<!-- Skyy Rose Collection Checkout Benefits -->
	<div class="checkout-benefits-section">
		<div class="benefits-header">
			<h3 class="benefits-title"><?php esc_html_e('Exclusive Benefits', 'wp-mastery-woocommerce-luxury'); ?></h3>
		</div>
		<div class="benefits-grid">
			<div class="benefit-card">
				<div class="benefit-icon">🛡️</div>
				<div class="benefit-content">
					<h4 class="benefit-title"><?php esc_html_e('Secure Checkout', 'wp-mastery-woocommerce-luxury'); ?></h4>
					<p class="benefit-description"><?php esc_html_e('256-bit SSL encryption', 'wp-mastery-woocommerce-luxury'); ?></p>
				</div>
			</div>
			<div class="benefit-card">
				<div class="benefit-icon">⚡</div>
				<div class="benefit-content">
					<h4 class="benefit-title"><?php esc_html_e('Express Delivery', 'wp-mastery-woocommerce-luxury'); ?></h4>
					<p class="benefit-description"><?php esc_html_e('Next-day luxury shipping', 'wp-mastery-woocommerce-luxury'); ?></p>
				</div>
			</div>
			<div class="benefit-card">
				<div class="benefit-icon">💝</div>
				<div class="benefit-content">
					<h4 class="benefit-title"><?php esc_html_e('Gift Wrapping', 'wp-mastery-woocommerce-luxury'); ?></h4>
					<p class="benefit-description"><?php esc_html_e('Complimentary luxury packaging', 'wp-mastery-woocommerce-luxury'); ?></p>
				</div>
			</div>
		</div>
	</div>

	<div class="wc-proceed-to-checkout">
		<?php do_action('woocommerce_proceed_to_checkout'); ?>
	</div>

	<?php do_action('woocommerce_after_cart_totals'); ?>

	<!-- AI Analytics Tracking -->
	<div class="cart-totals-analytics" id="totals-behavior-tracking" style="display: none;">
		<input type="hidden" id="checkout-readiness-score" value="">
		<input type="hidden" id="conversion-probability" value="">
		<input type="hidden" id="price-sensitivity" value="">
		<input type="hidden" id="urgency-level" value="">
	</div>

</div>
