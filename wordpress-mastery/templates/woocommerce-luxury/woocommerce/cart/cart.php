<?php
/**
 * Shopping cart page
 *
 * This template can be overridden by copying it to yourtheme/woocommerce/cart/cart.php.
 * Enhanced with Skyy Rose Collection brand integration and AI-powered features.
 *
 * @package WP_Mastery_WooCommerce_Luxury
 * @version 7.0.1
 */

// Prevent direct access
if (!defined('ABSPATH')) {
	exit;
}

do_action('woocommerce_before_cart'); ?>

<div class="skyy-rose-cart-wrapper" id="luxury-cart-experience">
	<!-- Skyy Rose Collection Brand Header -->
	<div class="skyy-rose-cart-header">
		<div class="container">
			<div class="cart-brand-section">
				<div class="brand-logo-area">
					<div class="skyy-rose-logo">
						<img src="<?php echo esc_url(get_template_directory_uri() . '/assets/images/skyy-rose-logo-luxury.svg'); ?>" 
							 alt="<?php esc_attr_e('Skyy Rose Collection', 'wp-mastery-woocommerce-luxury'); ?>" 
							 class="brand-logo">
					</div>
					<div class="brand-tagline">
						<h1 class="cart-title"><?php esc_html_e('Your Luxury Selection', 'wp-mastery-woocommerce-luxury'); ?></h1>
						<p class="brand-subtitle luxury-accent"><?php esc_html_e('Curated Fashion, Elevated Style', 'wp-mastery-woocommerce-luxury'); ?></p>
					</div>
				</div>
				
				<!-- AI-Powered Cart Intelligence -->
				<div class="cart-ai-insights" id="cart-intelligence-panel">
					<div class="ai-insight-card">
						<div class="insight-icon">🎯</div>
						<div class="insight-content">
							<h4 class="insight-title"><?php esc_html_e('Style Analysis', 'wp-mastery-woocommerce-luxury'); ?></h4>
							<p class="insight-text" id="cart-style-analysis"><?php esc_html_e('Analyzing your selections...', 'wp-mastery-woocommerce-luxury'); ?></p>
						</div>
					</div>
					<div class="ai-insight-card">
						<div class="insight-icon">💎</div>
						<div class="insight-content">
							<h4 class="insight-title"><?php esc_html_e('Collection Value', 'wp-mastery-woocommerce-luxury'); ?></h4>
							<p class="insight-text" id="cart-value-analysis"><?php esc_html_e('Calculating luxury index...', 'wp-mastery-woocommerce-luxury'); ?></p>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>

	<div class="container">
		<form class="woocommerce-cart-form" action="<?php echo esc_url(wc_get_cart_url()); ?>" method="post">
			<?php do_action('woocommerce_before_cart_table'); ?>

			<div class="luxury-cart-layout">
				<!-- Cart Items Section -->
				<div class="cart-items-section">
					<div class="cart-section-header">
						<h2 class="section-title"><?php esc_html_e('Your Curated Collection', 'wp-mastery-woocommerce-luxury'); ?></h2>
						<div class="cart-item-count">
							<span class="item-count"><?php echo WC()->cart->get_cart_contents_count(); ?></span>
							<span class="item-label"><?php esc_html_e('Items', 'wp-mastery-woocommerce-luxury'); ?></span>
						</div>
					</div>

					<div class="luxury-cart-table-wrapper">
						<table class="shop_table shop_table_responsive cart woocommerce-cart-form__contents luxury-cart-table" cellspacing="0">
							<thead class="cart-table-header">
								<tr>
									<th class="product-thumbnail"><?php esc_html_e('Product', 'wp-mastery-woocommerce-luxury'); ?></th>
									<th class="product-name"><?php esc_html_e('Details', 'wp-mastery-woocommerce-luxury'); ?></th>
									<th class="product-price"><?php esc_html_e('Price', 'wp-mastery-woocommerce-luxury'); ?></th>
									<th class="product-quantity"><?php esc_html_e('Quantity', 'wp-mastery-woocommerce-luxury'); ?></th>
									<th class="product-subtotal"><?php esc_html_e('Subtotal', 'wp-mastery-woocommerce-luxury'); ?></th>
									<th class="product-remove">&nbsp;</th>
								</tr>
							</thead>
							<tbody>
								<?php do_action('woocommerce_before_cart_contents'); ?>

								<?php
								foreach (WC()->cart->get_cart() as $cart_item_key => $cart_item) {
									$_product   = apply_filters('woocommerce_cart_item_product', $cart_item['data'], $cart_item, $cart_item_key);
									$product_id = apply_filters('woocommerce_cart_item_product_id', $cart_item['product_id'], $cart_item, $cart_item_key);

									if ($_product && $_product->exists() && $cart_item['quantity'] > 0 && apply_filters('woocommerce_cart_item_visible', true, $cart_item, $cart_item_key)) {
										$product_permalink = apply_filters('woocommerce_cart_item_permalink', $_product->is_visible() ? $_product->get_permalink($cart_item) : '', $cart_item, $cart_item_key);
										?>
										<tr class="woocommerce-cart-form__cart-item <?php echo esc_attr(apply_filters('woocommerce_cart_item_class', 'cart_item', $cart_item, $cart_item_key)); ?> luxury-cart-item" data-product-id="<?php echo esc_attr($product_id); ?>">

											<!-- Product Image -->
											<td class="product-thumbnail">
												<div class="luxury-product-image">
													<?php
													$thumbnail = apply_filters('woocommerce_cart_item_thumbnail', $_product->get_image('luxury-product-thumb'), $cart_item, $cart_item_key);

													if (!$product_permalink) {
														echo $thumbnail; // PHPCS: XSS ok.
													} else {
														printf('<a href="%s" class="product-image-link">%s</a>', esc_url($product_permalink), $thumbnail); // PHPCS: XSS ok.
													}
													?>
													<!-- AI Style Badge -->
													<div class="ai-style-badge" id="style-badge-<?php echo esc_attr($product_id); ?>">
														<span class="badge-text"><?php esc_html_e('Analyzing...', 'wp-mastery-woocommerce-luxury'); ?></span>
													</div>
												</div>
											</td>

											<!-- Product Details -->
											<td class="product-name" data-title="<?php esc_attr_e('Product', 'wp-mastery-woocommerce-luxury'); ?>">
												<div class="luxury-product-details">
													<?php
													if (!$product_permalink) {
														echo wp_kses_post(apply_filters('woocommerce_cart_item_name', $_product->get_name(), $cart_item, $cart_item_key) . '&nbsp;');
													} else {
														echo wp_kses_post(apply_filters('woocommerce_cart_item_name', sprintf('<a href="%s" class="product-name-link">%s</a>', esc_url($product_permalink), $_product->get_name()), $cart_item, $cart_item_key));
													}

													do_action('woocommerce_after_cart_item_name', $cart_item, $cart_item_key);

													// Meta data.
													echo wc_get_formatted_cart_item_data($cart_item); // PHPCS: XSS ok.

													// Backorder notification.
													if ($_product->backorders_require_notification() && $_product->is_on_backorder($cart_item['quantity'])) {
														echo wp_kses_post(apply_filters('woocommerce_cart_item_backorder_notification', '<p class="backorder_notification">' . esc_html__('Available on backorder', 'wp-mastery-woocommerce-luxury') . '</p>', $product_id));
													}
													?>
													
													<!-- AI Product Insights -->
													<div class="ai-product-insights" id="insights-<?php echo esc_attr($product_id); ?>">
														<div class="insight-tags">
															<!-- Populated by AI analysis -->
														</div>
													</div>
												</div>
											</td>

											<!-- Product Price -->
											<td class="product-price" data-title="<?php esc_attr_e('Price', 'wp-mastery-woocommerce-luxury'); ?>">
												<div class="luxury-price-display">
													<?php
													echo apply_filters('woocommerce_cart_item_price', WC()->cart->get_product_price($_product), $cart_item, $cart_item_key); // PHPCS: XSS ok.
													?>
													<!-- Dynamic Pricing Indicator -->
													<div class="dynamic-pricing-indicator" id="pricing-<?php echo esc_attr($product_id); ?>">
														<!-- Populated by AI pricing analysis -->
													</div>
												</div>
											</td>

											<!-- Product Quantity -->
											<td class="product-quantity" data-title="<?php esc_attr_e('Quantity', 'wp-mastery-woocommerce-luxury'); ?>">
												<div class="luxury-quantity-selector">
													<?php
													if ($_product->is_sold_individually()) {
														$product_quantity = sprintf('1 <input type="hidden" name="cart[%s][qty]" value="1" />', $cart_item_key);
													} else {
														$product_quantity = woocommerce_quantity_input(
															array(
																'input_name'   => "cart[{$cart_item_key}][qty]",
																'input_value'  => $cart_item['quantity'],
																'max_value'    => $_product->get_max_purchase_quantity(),
																'min_value'    => '0',
																'product_name' => $_product->get_name(),
															),
															$_product,
															false
														);
													}

													echo apply_filters('woocommerce_cart_item_quantity', $product_quantity, $cart_item_key, $cart_item); // PHPCS: XSS ok.
													?>
												</div>
											</td>

											<!-- Product Subtotal -->
											<td class="product-subtotal" data-title="<?php esc_attr_e('Subtotal', 'wp-mastery-woocommerce-luxury'); ?>">
												<div class="luxury-subtotal-display">
													<?php
													echo apply_filters('woocommerce_cart_item_subtotal', WC()->cart->get_product_subtotal($_product, $cart_item['quantity']), $cart_item, $cart_item_key); // PHPCS: XSS ok.
													?>
												</div>
											</td>

											<!-- Remove Product -->
											<td class="product-remove">
												<div class="luxury-remove-button">
													<?php
													echo apply_filters( // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
														'woocommerce_cart_item_remove_link',
														sprintf(
															'<a href="%s" class="remove luxury-remove-link" aria-label="%s" data-product_id="%s" data-product_sku="%s">&times;</a>',
															esc_url(wc_get_cart_remove_url($cart_item_key)),
															esc_html__('Remove this item', 'wp-mastery-woocommerce-luxury'),
															esc_attr($product_id),
															esc_attr($_product->get_sku())
														),
														$cart_item_key
													);
													?>
												</div>
											</td>
										</tr>
										<?php
									}
								}
								?>

								<?php do_action('woocommerce_cart_contents'); ?>

								<tr class="cart-actions-row">
									<td colspan="6" class="actions">
										<div class="luxury-cart-actions">
											<?php if (wc_coupons_enabled()) { ?>
												<div class="coupon-section">
													<label for="coupon_code" class="coupon-label"><?php esc_html_e('Coupon:', 'wp-mastery-woocommerce-luxury'); ?></label>
													<input type="text" name="coupon_code" class="input-text luxury-coupon-input" id="coupon_code" value="" placeholder="<?php esc_attr_e('Coupon code', 'wp-mastery-woocommerce-luxury'); ?>" />
													<button type="submit" class="button btn-luxury-outline" name="apply_coupon" value="<?php esc_attr_e('Apply coupon', 'wp-mastery-woocommerce-luxury'); ?>"><?php esc_html_e('Apply coupon', 'wp-mastery-woocommerce-luxury'); ?></button>
													<?php do_action('woocommerce_cart_coupon'); ?>
												</div>
											<?php } ?>

											<button type="submit" class="button btn-luxury" name="update_cart" value="<?php esc_attr_e('Update cart', 'wp-mastery-woocommerce-luxury'); ?>"><?php esc_html_e('Update cart', 'wp-mastery-woocommerce-luxury'); ?></button>

											<?php do_action('woocommerce_cart_actions'); ?>

											<?php wp_nonce_field('woocommerce-cart', 'woocommerce-cart-nonce'); ?>
										</div>
									</td>
								</tr>

								<?php do_action('woocommerce_after_cart_contents'); ?>
							</tbody>
						</table>
					</div>
				</div>

				<!-- Cart Totals & AI Recommendations -->
				<div class="cart-sidebar-section">
					<?php do_action('woocommerce_before_cart_collaterals'); ?>

					<div class="cart-collaterals">
						<?php
						/**
						 * Cart collaterals hook.
						 *
						 * @hooked woocommerce_cross_sell_display
						 * @hooked woocommerce_cart_totals - 10
						 */
						do_action('woocommerce_cart_collaterals');
						?>

						<!-- AI-Powered Cart Recommendations -->
						<div class="ai-cart-recommendations" id="cart-ai-suggestions">
							<h3 class="recommendations-title"><?php esc_html_e('Complete Your Look', 'wp-mastery-woocommerce-luxury'); ?></h3>
							<div class="cart-recommendations-grid" id="ai-cart-suggestions-grid">
								<!-- Populated by AI recommendation engine -->
							</div>
						</div>

						<!-- Luxury Shopping Benefits -->
						<div class="luxury-benefits-section">
							<h3 class="benefits-title"><?php esc_html_e('Skyy Rose Collection Benefits', 'wp-mastery-woocommerce-luxury'); ?></h3>
							<div class="benefits-list">
								<div class="benefit-item">
									<span class="benefit-icon">🚚</span>
									<span class="benefit-text"><?php esc_html_e('Free Luxury Shipping', 'wp-mastery-woocommerce-luxury'); ?></span>
								</div>
								<div class="benefit-item">
									<span class="benefit-icon">💎</span>
									<span class="benefit-text"><?php esc_html_e('Authenticity Guarantee', 'wp-mastery-woocommerce-luxury'); ?></span>
								</div>
								<div class="benefit-item">
									<span class="benefit-icon">🔄</span>
									<span class="benefit-text"><?php esc_html_e('30-Day Returns', 'wp-mastery-woocommerce-luxury'); ?></span>
								</div>
								<div class="benefit-item">
									<span class="benefit-icon">👗</span>
									<span class="benefit-text"><?php esc_html_e('Personal Styling', 'wp-mastery-woocommerce-luxury'); ?></span>
								</div>
							</div>
						</div>
					</div>

					<?php do_action('woocommerce_after_cart_collaterals'); ?>
				</div>
			</div>
		</form>

		<?php do_action('woocommerce_after_cart_table'); ?>
	</div>

	<!-- AI Cart Analytics (Hidden) -->
	<div class="cart-analytics-tracker" id="cart-behavior-tracking" style="display: none;">
		<input type="hidden" id="cart-session-id" value="<?php echo esc_attr(WC()->session->get_customer_id()); ?>">
		<input type="hidden" id="cart-total-value" value="<?php echo esc_attr(WC()->cart->get_total('edit')); ?>">
		<input type="hidden" id="cart-item-count" value="<?php echo esc_attr(WC()->cart->get_cart_contents_count()); ?>">
		<input type="hidden" id="cart-categories" value="">
		<input type="hidden" id="cart-brands" value="">
	</div>
</div>

<?php do_action('woocommerce_after_cart'); ?>
