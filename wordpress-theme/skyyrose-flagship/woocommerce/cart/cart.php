<?php
/**
 * Cart Page - Dark Luxury Design
 *
 * Overrides WooCommerce templates/cart/cart.php.
 * Features: dark #0A0A0A background, 150px product images, quantity controls,
 * sticky order summary sidebar, empty cart state.
 *
 * @package SkyyRose_Flagship
 * @since   2.0.0
 * @version 9.5.0
 */

defined( 'ABSPATH' ) || exit;

/**
 * Hook: woocommerce_before_cart.
 */
do_action( 'woocommerce_before_cart' );
?>

<div class="skyy-cart" data-skyy-cart>

	<?php if ( WC()->cart->is_empty() ) : ?>

		<!-- EMPTY CART STATE -->
		<div class="skyy-cart__empty">
			<div class="skyy-cart__empty-inner">
				<svg class="skyy-cart__empty-icon" width="80" height="80" viewBox="0 0 80 80" fill="none">
					<path d="M20 20h5l5 30h25l5-20H30" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
					<circle cx="37" cy="58" r="3" stroke="currentColor" stroke-width="2"/>
					<circle cx="53" cy="58" r="3" stroke="currentColor" stroke-width="2"/>
				</svg>
				<h1 class="skyy-cart__empty-title">
					<?php esc_html_e( 'Your Cart is Empty', 'skyyrose-flagship' ); ?>
				</h1>
				<p class="skyy-cart__empty-text">
					<?php esc_html_e( 'Explore our collections and find pieces that speak to you.', 'skyyrose-flagship' ); ?>
				</p>
				<a href="<?php echo esc_url( apply_filters( 'woocommerce_return_to_shop_redirect', wc_get_page_permalink( 'shop' ) ) ); ?>"
				   class="skyy-cart__empty-cta">
					<?php esc_html_e( 'Explore Collections', 'skyyrose-flagship' ); ?>
				</a>
			</div>
		</div>

	<?php else : ?>

		<div class="skyy-cart__header">
			<h1 class="skyy-cart__title">
				<?php esc_html_e( 'Shopping Cart', 'skyyrose-flagship' ); ?>
			</h1>
			<span class="skyy-cart__count">
				<?php
				printf(
					/* translators: %d: number of items */
					esc_html( _n( '%d item', '%d items', WC()->cart->get_cart_contents_count(), 'skyyrose-flagship' ) ),
					WC()->cart->get_cart_contents_count()
				);
				?>
			</span>
		</div>

		<div class="skyy-cart__layout">

			<!-- CART ITEMS -->
			<div class="skyy-cart__items-section">
				<form class="woocommerce-cart-form" action="<?php echo esc_url( wc_get_cart_url() ); ?>" method="post">
					<?php
					/**
					 * Hook: woocommerce_before_cart_table.
					 */
					do_action( 'woocommerce_before_cart_table' );
					?>

					<div class="skyy-cart__items-list" data-skyy-cart-items>
						<?php
						foreach ( WC()->cart->get_cart() as $cart_item_key => $cart_item ) :
							$_product   = apply_filters( 'woocommerce_cart_item_product', $cart_item['data'], $cart_item, $cart_item_key );
							$product_id = apply_filters( 'woocommerce_cart_item_product_id', $cart_item['product_id'], $cart_item, $cart_item_key );

							if ( ! $_product || ! $_product->exists() || $cart_item['quantity'] <= 0 ) {
								continue;
							}

							if ( ! apply_filters( 'woocommerce_cart_item_visible', true, $cart_item, $cart_item_key ) ) {
								continue;
							}

							$product_name      = apply_filters( 'woocommerce_cart_item_name', $_product->get_name(), $cart_item, $cart_item_key );
							$product_permalink = apply_filters( 'woocommerce_cart_item_permalink', $_product->is_visible() ? $_product->get_permalink( $cart_item ) : '', $cart_item, $cart_item_key );
							$product_price     = apply_filters( 'woocommerce_cart_item_price', WC()->cart->get_product_price( $_product ), $cart_item, $cart_item_key );
							$product_subtotal  = apply_filters( 'woocommerce_cart_item_subtotal', WC()->cart->get_product_subtotal( $_product, $cart_item['quantity'] ), $cart_item, $cart_item_key );
							$product_thumbnail = apply_filters( 'woocommerce_cart_item_thumbnail', $_product->get_image( array( 150, 150 ) ), $cart_item, $cart_item_key );

							// Extract variation attributes for display.
							$variation_data = array();
							if ( ! empty( $cart_item['variation'] ) ) {
								foreach ( $cart_item['variation'] as $attr_name => $attr_value ) {
									$attr_label = wc_attribute_label( str_replace( 'attribute_', '', $attr_name ) );
									$variation_data[ $attr_label ] = $attr_value;
								}
							}
							?>

							<div class="skyy-cart__item <?php echo esc_attr( apply_filters( 'woocommerce_cart_item_class', 'cart_item', $cart_item, $cart_item_key ) ); ?>"
								 data-cart-item-key="<?php echo esc_attr( $cart_item_key ); ?>">

								<!-- Product Image (150px) -->
								<div class="skyy-cart__item-image">
									<?php if ( $product_permalink ) : ?>
										<a href="<?php echo esc_url( $product_permalink ); ?>">
											<?php echo wp_kses_post( $product_thumbnail ); ?>
										</a>
									<?php else : ?>
										<?php echo wp_kses_post( $product_thumbnail ); ?>
									<?php endif; ?>
								</div>

								<!-- Product Details -->
								<div class="skyy-cart__item-details">
									<div class="skyy-cart__item-info">
										<h3 class="skyy-cart__item-name">
											<?php if ( $product_permalink ) : ?>
												<a href="<?php echo esc_url( $product_permalink ); ?>">
													<?php echo wp_kses_post( $product_name ); ?>
												</a>
											<?php else : ?>
												<?php echo wp_kses_post( $product_name ); ?>
											<?php endif; ?>
										</h3>

										<?php if ( ! empty( $variation_data ) ) : ?>
											<div class="skyy-cart__item-variations">
												<?php foreach ( $variation_data as $label => $value ) : ?>
													<span class="skyy-cart__item-variation">
														<?php echo esc_html( $label ); ?>: <?php echo esc_html( ucfirst( $value ) ); ?>
													</span>
												<?php endforeach; ?>
											</div>
										<?php endif; ?>

										<div class="skyy-cart__item-price-single">
											<?php echo wp_kses_post( $product_price ); ?>
										</div>
									</div>

									<!-- Quantity Controls -->
									<div class="skyy-cart__item-quantity">
										<div class="skyy-cart__qty-controls">
											<button type="button"
													class="skyy-cart__qty-btn skyy-cart__qty-btn--minus"
													data-action="decrease"
													data-key="<?php echo esc_attr( $cart_item_key ); ?>"
													aria-label="<?php esc_attr_e( 'Decrease quantity', 'skyyrose-flagship' ); ?>">
												<svg width="14" height="14" viewBox="0 0 14 14" fill="none">
													<path d="M3 7h8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
												</svg>
											</button>
											<input type="number"
												   class="skyy-cart__qty-input"
												   name="cart[<?php echo esc_attr( $cart_item_key ); ?>][qty]"
												   value="<?php echo esc_attr( $cart_item['quantity'] ); ?>"
												   min="0"
												   max="<?php echo esc_attr( $_product->get_max_purchase_quantity() > 0 ? $_product->get_max_purchase_quantity() : 99 ); ?>"
												   step="1"
												   inputmode="numeric"
												   aria-label="<?php esc_attr_e( 'Item quantity', 'skyyrose-flagship' ); ?>" />
											<button type="button"
													class="skyy-cart__qty-btn skyy-cart__qty-btn--plus"
													data-action="increase"
													data-key="<?php echo esc_attr( $cart_item_key ); ?>"
													aria-label="<?php esc_attr_e( 'Increase quantity', 'skyyrose-flagship' ); ?>">
												<svg width="14" height="14" viewBox="0 0 14 14" fill="none">
													<path d="M7 3v8M3 7h8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
												</svg>
											</button>
										</div>
									</div>

									<!-- Price -->
									<div class="skyy-cart__item-subtotal">
										<?php echo wp_kses_post( $product_subtotal ); ?>
									</div>

									<!-- Remove Button -->
									<div class="skyy-cart__item-remove">
										<?php
										echo wp_kses_post( apply_filters(
											'woocommerce_cart_item_remove_link',
											sprintf(
												'<a href="%s" class="skyy-cart__remove-btn" aria-label="%s" data-product_id="%s" data-product_sku="%s">&times;</a>',
												esc_url( wc_get_cart_remove_url( $cart_item_key ) ),
												/* translators: %s: product name */
												esc_attr( sprintf( __( 'Remove %s from cart', 'skyyrose-flagship' ), wp_strip_all_tags( $product_name ) ) ),
												esc_attr( $product_id ),
												esc_attr( $_product->get_sku() )
											),
											$cart_item_key
										) );
										?>
									</div>
								</div>
							</div>

						<?php endforeach; ?>
					</div>

					<?php
					/**
					 * Hook: woocommerce_cart_contents.
					 */
					do_action( 'woocommerce_cart_contents' );
					?>

					<div class="skyy-cart__actions">
						<?php if ( wc_coupons_enabled() ) : ?>
							<div class="skyy-cart__coupon">
								<label for="skyy-coupon-code" class="screen-reader-text">
									<?php esc_html_e( 'Coupon code', 'skyyrose-flagship' ); ?>
								</label>
								<input type="text"
									   name="coupon_code"
									   class="skyy-cart__coupon-input"
									   id="skyy-coupon-code"
									   value=""
									   placeholder="<?php esc_attr_e( 'Coupon code', 'skyyrose-flagship' ); ?>" />
								<button type="submit"
										class="skyy-cart__coupon-btn"
										name="apply_coupon"
										value="<?php esc_attr_e( 'Apply', 'skyyrose-flagship' ); ?>">
									<?php esc_html_e( 'Apply', 'skyyrose-flagship' ); ?>
								</button>
							</div>
						<?php endif; ?>

						<button type="submit"
								class="skyy-cart__update-btn"
								name="update_cart"
								value="<?php esc_attr_e( 'Update cart', 'skyyrose-flagship' ); ?>">
							<?php esc_html_e( 'Update Cart', 'skyyrose-flagship' ); ?>
						</button>

						<?php wp_nonce_field( 'woocommerce-cart', 'woocommerce-cart-nonce' ); ?>
					</div>

					<?php
					/**
					 * Hook: woocommerce_after_cart_table.
					 */
					do_action( 'woocommerce_after_cart_table' );
					?>

				</form>

				<div class="skyy-cart__continue">
					<a href="<?php echo esc_url( apply_filters( 'woocommerce_return_to_shop_redirect', wc_get_page_permalink( 'shop' ) ) ); ?>"
					   class="skyy-cart__continue-btn">
						<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
							<path d="M10 12l-4-4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
						</svg>
						<?php esc_html_e( 'Continue Shopping', 'skyyrose-flagship' ); ?>
					</a>
				</div>
			</div>

			<!-- ORDER SUMMARY SIDEBAR (Sticky, 400px) -->
			<aside class="skyy-cart__summary" data-skyy-cart-summary>
				<div class="skyy-cart__summary-inner">
					<h2 class="skyy-cart__summary-title">
						<?php esc_html_e( 'Order Summary', 'skyyrose-flagship' ); ?>
					</h2>

					<?php
					/**
					 * Hook: woocommerce_before_cart_totals.
					 */
					do_action( 'woocommerce_before_cart_totals' );
					?>

					<div class="skyy-cart__summary-rows">

						<!-- Subtotal -->
						<div class="skyy-cart__summary-row">
							<span class="skyy-cart__summary-label">
								<?php esc_html_e( 'Subtotal', 'skyyrose-flagship' ); ?>
							</span>
							<span class="skyy-cart__summary-value">
								<?php wc_cart_totals_subtotal_html(); ?>
							</span>
						</div>

						<!-- Coupons -->
						<?php foreach ( WC()->cart->get_coupons() as $code => $coupon ) : ?>
							<div class="skyy-cart__summary-row skyy-cart__summary-row--coupon">
								<span class="skyy-cart__summary-label">
									<?php
									/* translators: %s: coupon code */
									printf( esc_html__( 'Coupon: %s', 'skyyrose-flagship' ), esc_html( $code ) );
									?>
								</span>
								<span class="skyy-cart__summary-value">
									<?php wc_cart_totals_coupon_html( $coupon ); ?>
								</span>
							</div>
						<?php endforeach; ?>

						<!-- Shipping Estimate -->
						<?php if ( WC()->cart->needs_shipping() && WC()->cart->show_shipping() ) : ?>
							<div class="skyy-cart__summary-row">
								<span class="skyy-cart__summary-label">
									<?php esc_html_e( 'Shipping', 'skyyrose-flagship' ); ?>
								</span>
								<span class="skyy-cart__summary-value">
									<?php wc_cart_totals_shipping_html(); ?>
								</span>
							</div>
						<?php elseif ( WC()->cart->needs_shipping() ) : ?>
							<div class="skyy-cart__summary-row">
								<span class="skyy-cart__summary-label">
									<?php esc_html_e( 'Shipping', 'skyyrose-flagship' ); ?>
								</span>
								<span class="skyy-cart__summary-value skyy-cart__summary-value--estimate">
									<?php esc_html_e( 'Calculated at checkout', 'skyyrose-flagship' ); ?>
								</span>
							</div>
						<?php endif; ?>

						<!-- Fees -->
						<?php foreach ( WC()->cart->get_fees() as $fee ) : ?>
							<div class="skyy-cart__summary-row">
								<span class="skyy-cart__summary-label">
									<?php echo esc_html( $fee->name ); ?>
								</span>
								<span class="skyy-cart__summary-value">
									<?php wc_cart_totals_fee_html( $fee ); ?>
								</span>
							</div>
						<?php endforeach; ?>

						<!-- Tax -->
						<?php if ( wc_tax_enabled() && ! WC()->cart->display_prices_including_tax() ) : ?>
							<?php foreach ( WC()->cart->get_tax_totals() as $tax_code => $tax ) : ?>
								<div class="skyy-cart__summary-row">
									<span class="skyy-cart__summary-label">
										<?php echo esc_html( $tax->label ); ?>
									</span>
									<span class="skyy-cart__summary-value">
										<?php echo wp_kses_post( $tax->formatted_amount ); ?>
									</span>
								</div>
							<?php endforeach; ?>
						<?php endif; ?>

					</div>

					<!-- Total -->
					<div class="skyy-cart__summary-total">
						<span class="skyy-cart__summary-total-label">
							<?php esc_html_e( 'Total', 'skyyrose-flagship' ); ?>
						</span>
						<span class="skyy-cart__summary-total-value">
							<?php wc_cart_totals_order_total_html(); ?>
						</span>
					</div>

					<?php
					/**
					 * Hook: woocommerce_after_cart_totals.
					 */
					do_action( 'woocommerce_after_cart_totals' );
					?>

					<!-- Proceed to Checkout -->
					<div class="skyy-cart__summary-checkout">
						<a href="<?php echo esc_url( wc_get_checkout_url() ); ?>"
						   class="skyy-cart__checkout-btn wc-proceed-to-checkout">
							<?php esc_html_e( 'Proceed to Checkout', 'skyyrose-flagship' ); ?>
						</a>
					</div>

					<!-- Trust Badges -->
					<div class="skyy-cart__trust-badges">
						<div class="skyy-cart__trust-badge">
							<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
								<path d="M8 1l2 3h3l-2.5 2.5L11.5 10 8 8l-3.5 2 1-3.5L3 4h3l2-3z" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"/>
							</svg>
							<span><?php esc_html_e( 'Secure Checkout', 'skyyrose-flagship' ); ?></span>
						</div>
						<div class="skyy-cart__trust-badge">
							<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
								<path d="M2 8l4 4 8-8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
							</svg>
							<span><?php esc_html_e( 'Free Shipping 150+', 'skyyrose-flagship' ); ?></span>
						</div>
						<div class="skyy-cart__trust-badge">
							<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
								<path d="M1 4l7-3 7 3v5c0 3.5-3 5.5-7 7-4-1.5-7-3.5-7-7V4z" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"/>
							</svg>
							<span><?php esc_html_e( '30-Day Returns', 'skyyrose-flagship' ); ?></span>
						</div>
					</div>

				</div>
			</aside>

		</div><!-- .skyy-cart__layout -->

	<?php endif; ?>

</div><!-- .skyy-cart -->

<?php
/**
 * Hook: woocommerce_after_cart.
 */
do_action( 'woocommerce_after_cart' );
