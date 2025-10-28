<?php
/**
 * Checkout Form
 *
 * This template can be overridden by copying it to yourtheme/woocommerce/checkout/form-checkout.php.
 * Enhanced with Skyy Rose Collection luxury styling and AI-powered multi-step checkout.
 *
 * @package WP_Mastery_WooCommerce_Luxury
 * @version 3.5.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
	exit;
}

do_action('woocommerce_before_checkout_form', $checkout);

// If checkout registration is disabled and not logged in, the user cannot checkout.
if (!$checkout->is_registration_enabled() && $checkout->is_registration_required() && !is_user_logged_in()) {
	echo esc_html(apply_filters('woocommerce_checkout_must_be_logged_in_message', __('You must be logged in to checkout.', 'wp-mastery-woocommerce-luxury')));
	return;
}

?>

<div class="skyy-rose-checkout-wrapper" id="luxury-checkout-experience">
	<!-- Skyy Rose Collection Checkout Header -->
	<div class="skyy-rose-checkout-header">
		<div class="container">
			<div class="checkout-brand-section">
				<div class="brand-logo-area">
					<div class="skyy-rose-logo">
						<img src="<?php echo esc_url(get_template_directory_uri() . '/assets/images/skyy-rose-logo-luxury.svg'); ?>" 
							 alt="<?php esc_attr_e('Skyy Rose Collection', 'wp-mastery-woocommerce-luxury'); ?>" 
							 class="brand-logo">
					</div>
					<div class="brand-tagline">
						<h1 class="checkout-title"><?php esc_html_e('Secure Checkout', 'wp-mastery-woocommerce-luxury'); ?></h1>
						<p class="brand-subtitle luxury-accent"><?php esc_html_e('Complete Your Luxury Experience', 'wp-mastery-woocommerce-luxury'); ?></p>
					</div>
				</div>
				
				<!-- AI-Powered Checkout Intelligence -->
				<div class="checkout-ai-insights" id="checkout-intelligence-panel">
					<div class="ai-insight-card">
						<div class="insight-icon">🔒</div>
						<div class="insight-content">
							<h4 class="insight-title"><?php esc_html_e('Security Level', 'wp-mastery-woocommerce-luxury'); ?></h4>
							<p class="insight-text"><?php esc_html_e('Bank-grade encryption active', 'wp-mastery-woocommerce-luxury'); ?></p>
						</div>
					</div>
					<div class="ai-insight-card">
						<div class="insight-icon">⚡</div>
						<div class="insight-content">
							<h4 class="insight-title"><?php esc_html_e('Express Checkout', 'wp-mastery-woocommerce-luxury'); ?></h4>
							<p class="insight-text" id="checkout-time-estimate"><?php esc_html_e('Estimated: 2 minutes', 'wp-mastery-woocommerce-luxury'); ?></p>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>

	<!-- Multi-Step Checkout Progress -->
	<div class="checkout-progress-wrapper">
		<div class="container">
			<div class="checkout-progress-bar" id="luxury-checkout-progress">
				<div class="progress-step active" data-step="1">
					<div class="step-number">1</div>
					<div class="step-label"><?php esc_html_e('Information', 'wp-mastery-woocommerce-luxury'); ?></div>
				</div>
				<div class="progress-step" data-step="2">
					<div class="step-number">2</div>
					<div class="step-label"><?php esc_html_e('Shipping', 'wp-mastery-woocommerce-luxury'); ?></div>
				</div>
				<div class="progress-step" data-step="3">
					<div class="step-number">3</div>
					<div class="step-label"><?php esc_html_e('Payment', 'wp-mastery-woocommerce-luxury'); ?></div>
				</div>
				<div class="progress-step" data-step="4">
					<div class="step-number">4</div>
					<div class="step-label"><?php esc_html_e('Review', 'wp-mastery-woocommerce-luxury'); ?></div>
				</div>
			</div>
		</div>
	</div>

	<div class="container">
		<form name="checkout" method="post" class="checkout woocommerce-checkout luxury-checkout-form" action="<?php echo esc_url(wc_get_checkout_url()); ?>" enctype="multipart/form-data">

			<div class="luxury-checkout-layout">
				<!-- Main Checkout Content -->
				<div class="checkout-main-content">
					
					<!-- Step 1: Customer Information -->
					<div class="checkout-step" id="checkout-step-1" data-step="1">
						<div class="step-header">
							<h2 class="step-title"><?php esc_html_e('Customer Information', 'wp-mastery-woocommerce-luxury'); ?></h2>
							<p class="step-description"><?php esc_html_e('Please provide your contact and billing details', 'wp-mastery-woocommerce-luxury'); ?></p>
						</div>

						<?php if ($checkout->get_checkout_fields()) : ?>
							<?php do_action('woocommerce_checkout_before_customer_details'); ?>

							<div class="col2-set" id="customer_details">
								<div class="col-1">
									<?php do_action('woocommerce_checkout_billing'); ?>
								</div>

								<div class="col-2">
									<?php do_action('woocommerce_checkout_shipping'); ?>
								</div>
							</div>

							<?php do_action('woocommerce_checkout_after_customer_details'); ?>
						<?php endif; ?>

						<!-- AI-Powered Address Validation -->
						<div class="ai-address-validation" id="address-validation-panel">
							<div class="validation-status" id="address-validation-status">
								<!-- Populated by AI address validation -->
							</div>
						</div>

						<div class="step-navigation">
							<button type="button" class="btn-luxury step-next" data-next-step="2">
								<?php esc_html_e('Continue to Shipping', 'wp-mastery-woocommerce-luxury'); ?>
								<span class="nav-arrow">→</span>
							</button>
						</div>
					</div>

					<!-- Step 2: Shipping Options -->
					<div class="checkout-step" id="checkout-step-2" data-step="2" style="display: none;">
						<div class="step-header">
							<h2 class="step-title"><?php esc_html_e('Shipping Options', 'wp-mastery-woocommerce-luxury'); ?></h2>
							<p class="step-description"><?php esc_html_e('Choose your preferred delivery method', 'wp-mastery-woocommerce-luxury'); ?></p>
						</div>

						<div class="shipping-options-section">
							<?php if (WC()->cart->needs_shipping() && WC()->cart->show_shipping()) : ?>
								<?php do_action('woocommerce_review_order_before_shipping'); ?>
								<?php wc_cart_totals_shipping_html(); ?>
								<?php do_action('woocommerce_review_order_after_shipping'); ?>
							<?php endif; ?>

							<!-- AI-Powered Shipping Recommendations -->
							<div class="ai-shipping-recommendations" id="shipping-ai-suggestions">
								<h3 class="recommendations-title"><?php esc_html_e('Recommended for You', 'wp-mastery-woocommerce-luxury'); ?></h3>
								<div class="shipping-recommendations-grid" id="ai-shipping-options">
									<!-- Populated by AI shipping optimization -->
								</div>
							</div>

							<!-- Luxury Shipping Benefits -->
							<div class="luxury-shipping-benefits">
								<div class="benefit-item">
									<span class="benefit-icon">📦</span>
									<span class="benefit-text"><?php esc_html_e('Signature packaging with every order', 'wp-mastery-woocommerce-luxury'); ?></span>
								</div>
								<div class="benefit-item">
									<span class="benefit-icon">🎁</span>
									<span class="benefit-text"><?php esc_html_e('Complimentary gift wrapping available', 'wp-mastery-woocommerce-luxury'); ?></span>
								</div>
								<div class="benefit-item">
									<span class="benefit-icon">📱</span>
									<span class="benefit-text"><?php esc_html_e('Real-time tracking and notifications', 'wp-mastery-woocommerce-luxury'); ?></span>
								</div>
							</div>
						</div>

						<div class="step-navigation">
							<button type="button" class="btn-luxury-outline step-back" data-prev-step="1">
								<span class="nav-arrow">←</span>
								<?php esc_html_e('Back', 'wp-mastery-woocommerce-luxury'); ?>
							</button>
							<button type="button" class="btn-luxury step-next" data-next-step="3">
								<?php esc_html_e('Continue to Payment', 'wp-mastery-woocommerce-luxury'); ?>
								<span class="nav-arrow">→</span>
							</button>
						</div>
					</div>

					<!-- Step 3: Payment Information -->
					<div class="checkout-step" id="checkout-step-3" data-step="3" style="display: none;">
						<div class="step-header">
							<h2 class="step-title"><?php esc_html_e('Payment Information', 'wp-mastery-woocommerce-luxury'); ?></h2>
							<p class="step-description"><?php esc_html_e('Secure payment processing with bank-grade encryption', 'wp-mastery-woocommerce-luxury'); ?></p>
						</div>

						<div class="payment-section">
							<?php if (WC()->cart->needs_payment()) : ?>
								<div id="payment" class="woocommerce-checkout-payment luxury-payment-section">
									<?php if (WC()->cart->needs_payment()) : ?>
										<ul class="wc_payment_methods payment_methods methods luxury-payment-methods">
											<?php
											if (!empty($available_gateways)) {
												foreach ($available_gateways as $gateway) {
													wc_get_template('checkout/payment-method.php', array('gateway' => $gateway), '', WC()->plugin_path() . '/templates/');
												}
											} else {
												echo '<li class="woocommerce-notice woocommerce-notice--info woocommerce-info">' . apply_filters('woocommerce_no_available_payment_methods_message', WC()->customer->get_billing_country() ? esc_html__('Sorry, it seems that there are no available payment methods for your state. Please contact us if you require assistance or wish to make alternate arrangements.', 'wp-mastery-woocommerce-luxury') : esc_html__('Please fill in your details above to see available payment methods.', 'wp-mastery-woocommerce-luxury')) . '</li>'; // @codingStandardsIgnoreLine
											}
											?>
										</ul>
									<?php endif; ?>

									<!-- AI-Powered Payment Security -->
									<div class="payment-security-indicators" id="payment-security-panel">
										<div class="security-badge">
											<span class="security-icon">🔒</span>
											<span class="security-text"><?php esc_html_e('256-bit SSL Encryption', 'wp-mastery-woocommerce-luxury'); ?></span>
										</div>
										<div class="security-badge">
											<span class="security-icon">🛡️</span>
											<span class="security-text"><?php esc_html_e('PCI DSS Compliant', 'wp-mastery-woocommerce-luxury'); ?></span>
										</div>
										<div class="security-badge">
											<span class="security-icon">✅</span>
											<span class="security-text"><?php esc_html_e('Fraud Protection', 'wp-mastery-woocommerce-luxury'); ?></span>
										</div>
									</div>

									<div class="form-row place-order">
										<noscript>
											<?php
											/* translators: $1 and $2 opening and closing emphasis tags respectively */
											printf(esc_html__('Since your browser does not support JavaScript, or it is disabled, please ensure you click the %1$sUpdate Totals%2$s button before placing your order. You may be charged more than the amount stated above if you fail to do so.', 'wp-mastery-woocommerce-luxury'), '<em>', '</em>');
											?>
											<br/><button type="submit" class="button alt" name="woocommerce_checkout_update_totals" value="<?php esc_attr_e('Update totals', 'wp-mastery-woocommerce-luxury'); ?>"><?php esc_html_e('Update totals', 'wp-mastery-woocommerce-luxury'); ?></button>
										</noscript>

										<?php wc_get_template('checkout/terms.php'); ?>

										<?php do_action('woocommerce_review_order_before_submit'); ?>

										<?php echo apply_filters('woocommerce_order_button_html', '<button type="submit" class="button alt btn-luxury-large" name="woocommerce_checkout_place_order" id="place_order" value="' . esc_attr($order_button_text) . '" data-value="' . esc_attr($order_button_text) . '">' . esc_html($order_button_text) . '</button>'); // @codingStandardsIgnoreLine ?>

										<?php do_action('woocommerce_review_order_after_submit'); ?>

										<?php wp_nonce_field('woocommerce-process_checkout', 'woocommerce-process-checkout-nonce'); ?>
									</div>
								</div>
							<?php endif; ?>
						</div>

						<div class="step-navigation">
							<button type="button" class="btn-luxury-outline step-back" data-prev-step="2">
								<span class="nav-arrow">←</span>
								<?php esc_html_e('Back', 'wp-mastery-woocommerce-luxury'); ?>
							</button>
							<button type="button" class="btn-luxury step-next" data-next-step="4">
								<?php esc_html_e('Review Order', 'wp-mastery-woocommerce-luxury'); ?>
								<span class="nav-arrow">→</span>
							</button>
						</div>
					</div>

					<!-- Step 4: Order Review -->
					<div class="checkout-step" id="checkout-step-4" data-step="4" style="display: none;">
						<div class="step-header">
							<h2 class="step-title"><?php esc_html_e('Review Your Order', 'wp-mastery-woocommerce-luxury'); ?></h2>
							<p class="step-description"><?php esc_html_e('Please review your order details before completing your purchase', 'wp-mastery-woocommerce-luxury'); ?></p>
						</div>

						<div class="order-review-section">
							<?php do_action('woocommerce_checkout_before_order_review_heading'); ?>
							
							<div id="order_review" class="woocommerce-checkout-review-order luxury-order-review">
								<?php do_action('woocommerce_checkout_before_order_review'); ?>

								<?php wc_get_template('checkout/review-order.php'); ?>

								<?php do_action('woocommerce_checkout_after_order_review'); ?>
							</div>

							<?php do_action('woocommerce_checkout_after_order_review_heading'); ?>
						</div>

						<div class="step-navigation">
							<button type="button" class="btn-luxury-outline step-back" data-prev-step="3">
								<span class="nav-arrow">←</span>
								<?php esc_html_e('Back', 'wp-mastery-woocommerce-luxury'); ?>
							</button>
						</div>
					</div>
				</div>

				<!-- Checkout Sidebar -->
				<div class="checkout-sidebar">
					<!-- Order Summary -->
					<div class="checkout-order-summary" id="checkout-summary-panel">
						<h3 class="summary-title"><?php esc_html_e('Order Summary', 'wp-mastery-woocommerce-luxury'); ?></h3>
						<div class="summary-content" id="dynamic-order-summary">
							<!-- Populated dynamically -->
						</div>
					</div>

					<!-- AI-Powered Last-Minute Recommendations -->
					<div class="checkout-recommendations" id="checkout-ai-recommendations">
						<h3 class="recommendations-title"><?php esc_html_e('Before You Go...', 'wp-mastery-woocommerce-luxury'); ?></h3>
						<div class="recommendations-grid" id="last-minute-suggestions">
							<!-- Populated by AI recommendation engine -->
						</div>
					</div>

					<!-- Trust Signals -->
					<div class="checkout-trust-signals">
						<div class="trust-signal">
							<span class="trust-icon">🏆</span>
							<span class="trust-text"><?php esc_html_e('Award-winning customer service', 'wp-mastery-woocommerce-luxury'); ?></span>
						</div>
						<div class="trust-signal">
							<span class="trust-icon">⭐</span>
							<span class="trust-text"><?php esc_html_e('4.9/5 customer satisfaction', 'wp-mastery-woocommerce-luxury'); ?></span>
						</div>
						<div class="trust-signal">
							<span class="trust-icon">🌍</span>
							<span class="trust-text"><?php esc_html_e('Worldwide luxury shipping', 'wp-mastery-woocommerce-luxury'); ?></span>
						</div>
					</div>
				</div>
			</div>
		</form>

		<?php do_action('woocommerce_after_checkout_form', $checkout); ?>
	</div>

	<!-- AI Checkout Analytics (Hidden) -->
	<div class="checkout-analytics-tracker" id="checkout-behavior-tracking" style="display: none;">
		<input type="hidden" id="checkout-session-id" value="<?php echo esc_attr(WC()->session->get_customer_id()); ?>">
		<input type="hidden" id="checkout-start-time" value="<?php echo esc_attr(time()); ?>">
		<input type="hidden" id="current-step" value="1">
		<input type="hidden" id="abandonment-risk" value="">
		<input type="hidden" id="conversion-signals" value="">
	</div>
</div>
