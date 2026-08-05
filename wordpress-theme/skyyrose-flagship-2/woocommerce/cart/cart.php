<?php
/**
 * SkyyRose Flagship 2 cart.
 *
 * @package SkyyRoseFlagship2
 * @version 10.8.0
 */

defined( 'ABSPATH' ) || exit;

do_action( 'woocommerce_before_cart' );

if ( ! WC()->cart || WC()->cart->is_empty() ) :
	?>
	<section class="sr2-cart sr2-cart--empty">
		<p><?php esc_html_e( 'Your bag', 'skyyrose-flagship-2' ); ?></p>
		<h1><?php esc_html_e( 'Nothing here yet.', 'skyyrose-flagship-2' ); ?></h1>
		<a class="sr2-page-action" href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>"><?php esc_html_e( 'Shop collections', 'skyyrose-flagship-2' ); ?></a>
	</section>
	<?php
	do_action( 'woocommerce_after_cart' );
	return;
endif;
?>
<section class="sr2-cart">
	<header class="sr2-page-head"><p><?php esc_html_e( 'Your bag', 'skyyrose-flagship-2' ); ?></p><h1><?php esc_html_e( 'Keep your pieces close.', 'skyyrose-flagship-2' ); ?></h1></header>
	<div class="sr2-cart__layout">
		<form class="woocommerce-cart-form sr2-cart__items" action="<?php echo esc_url( wc_get_cart_url() ); ?>" method="post">
			<?php do_action( 'woocommerce_before_cart_table' ); ?>
			<?php do_action( 'woocommerce_before_cart_contents' ); ?>
			<?php foreach ( WC()->cart->get_cart() as $cart_item_key => $cart_item ) : ?>
				<?php
				$product    = apply_filters( 'woocommerce_cart_item_product', $cart_item['data'], $cart_item, $cart_item_key );
				$product_id = apply_filters( 'woocommerce_cart_item_product_id', $cart_item['product_id'], $cart_item, $cart_item_key );
				$visible    = apply_filters( 'woocommerce_cart_item_visible', true, $cart_item, $cart_item_key );

				if ( ! $product instanceof WC_Product || ! $product->exists() || $cart_item['quantity'] <= 0 || ! $visible ) {
					continue;
				}

				$product_name      = apply_filters( 'woocommerce_cart_item_name', $product->get_name(), $cart_item, $cart_item_key );
				$product_permalink = apply_filters( 'woocommerce_cart_item_permalink', $product->is_visible() ? $product->get_permalink( $cart_item ) : '', $cart_item, $cart_item_key );
				$product_thumbnail = apply_filters( 'woocommerce_cart_item_thumbnail', $product->get_image(), $cart_item, $cart_item_key );
				$product_price     = apply_filters( 'woocommerce_cart_item_price', WC()->cart->get_product_price( $product ), $cart_item, $cart_item_key );
				$product_subtotal  = apply_filters( 'woocommerce_cart_item_subtotal', WC()->cart->get_product_subtotal( $product, $cart_item['quantity'] ), $cart_item, $cart_item_key );

				$remove_link = apply_filters(
					'woocommerce_cart_item_remove_link',
					sprintf(
						'<a role="button" href="%1$s" class="remove sr2-cart__remove" aria-label="%2$s" data-product_id="%3$s" data-product_sku="%4$s">%5$s</a>',
						esc_url( wc_get_cart_remove_url( $cart_item_key ) ),
						esc_attr( sprintf( /* translators: %s: product name. */ __( 'Remove %s from your bag', 'skyyrose-flagship-2' ), wp_strip_all_tags( $product_name ) ) ),
						esc_attr( $product_id ),
						esc_attr( $product->get_sku() ),
						esc_html__( 'Remove', 'skyyrose-flagship-2' )
					),
					$cart_item_key
				);

				if ( $product->is_sold_individually() ) {
					$min_quantity = 1;
					$max_quantity = 1;
				} else {
					$min_quantity = 0;
					$max_quantity = $product->get_max_purchase_quantity();
				}

				$product_quantity = woocommerce_quantity_input(
					array(
						'input_name'   => "cart[{$cart_item_key}][qty]",
						'input_value'  => $cart_item['quantity'],
						'max_value'    => $max_quantity,
						'min_value'    => $min_quantity,
						'product_name' => $product_name,
					),
					$product,
					false
				);
				$product_quantity = apply_filters( 'woocommerce_cart_item_quantity', $product_quantity, $cart_item_key, $cart_item );
				?>
				<article class="sr2-cart__item <?php echo esc_attr( apply_filters( 'woocommerce_cart_item_class', 'cart_item', $cart_item, $cart_item_key ) ); ?>" data-product-id="<?php echo esc_attr( $product_id ); ?>">
					<div class="sr2-cart__image">
						<?php if ( $product_permalink ) : ?>
							<a href="<?php echo esc_url( $product_permalink ); ?>"><?php echo wp_kses_post( $product_thumbnail ); ?></a>
						<?php else : ?>
							<?php echo wp_kses_post( $product_thumbnail ); ?>
						<?php endif; ?>
					</div>
					<div class="sr2-cart__item-copy">
						<h2>
							<?php if ( $product_permalink ) : ?>
								<a href="<?php echo esc_url( $product_permalink ); ?>"><?php echo wp_kses_post( $product_name ); ?></a>
							<?php else : ?>
								<?php echo wp_kses_post( $product_name ); ?>
							<?php endif; ?>
						</h2>
						<?php do_action( 'woocommerce_after_cart_item_name', $cart_item, $cart_item_key ); ?>
						<?php echo wp_kses_post( wc_get_formatted_cart_item_data( $cart_item ) ); ?>
						<?php if ( $product->backorders_require_notification() && $product->is_on_backorder( $cart_item['quantity'] ) ) : ?>
							<?php echo wp_kses_post( apply_filters( 'woocommerce_cart_item_backorder_notification', '<p class="backorder_notification">' . esc_html__( 'Available on backorder', 'woocommerce' ) . '</p>', $product_id ) ); ?>
						<?php endif; ?>
						<div class="sr2-cart__pricing"><span><?php echo wp_kses_post( $product_price ); ?></span><span><?php echo wp_kses_post( $product_subtotal ); ?></span></div>
					</div>
					<div class="sr2-cart__controls">
						<?php echo wp_kses_post( $product_quantity ); ?>
						<?php echo wp_kses_post( $remove_link ); ?>
					</div>
				</article>
			<?php endforeach; ?>
			<?php do_action( 'woocommerce_cart_contents' ); ?>
			<div class="sr2-cart__actions">
				<?php if ( wc_coupons_enabled() ) : ?>
					<div class="coupon">
						<label class="screen-reader-text" for="coupon_code"><?php esc_html_e( 'Coupon:', 'woocommerce' ); ?></label>
						<input id="coupon_code" class="input-text" type="text" name="coupon_code" value="" placeholder="<?php esc_attr_e( 'Gift code', 'skyyrose-flagship-2' ); ?>">
						<button class="button<?php echo esc_attr( wc_wp_theme_get_element_class_name( 'button' ) ? ' ' . wc_wp_theme_get_element_class_name( 'button' ) : '' ); ?>" type="submit" name="apply_coupon" value="<?php esc_attr_e( 'Apply', 'skyyrose-flagship-2' ); ?>"><?php esc_html_e( 'Apply', 'skyyrose-flagship-2' ); ?></button>
						<?php do_action( 'woocommerce_cart_coupon' ); ?>
					</div>
				<?php endif; ?>
				<button class="button<?php echo esc_attr( wc_wp_theme_get_element_class_name( 'button' ) ? ' ' . wc_wp_theme_get_element_class_name( 'button' ) : '' ); ?>" type="submit" name="update_cart" value="<?php esc_attr_e( 'Update bag', 'skyyrose-flagship-2' ); ?>"><?php esc_html_e( 'Update bag', 'skyyrose-flagship-2' ); ?></button>
				<?php do_action( 'woocommerce_cart_actions' ); ?>
				<?php wp_nonce_field( 'woocommerce-cart', 'woocommerce-cart-nonce' ); ?>
			</div>
			<?php do_action( 'woocommerce_after_cart_contents' ); ?>
		</form>
		<?php do_action( 'woocommerce_after_cart_table' ); ?>
		<?php do_action( 'woocommerce_before_cart_collaterals' ); ?>
		<aside class="cart-collaterals sr2-cart__summary"><?php do_action( 'woocommerce_cart_collaterals' ); ?></aside>
	</div>
</section>
<?php do_action( 'woocommerce_after_cart' ); ?>
