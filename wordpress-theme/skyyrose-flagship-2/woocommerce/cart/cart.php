<?php
/**
 * SkyyRose Flagship 2 cart.
 *
 * @package SkyyRoseFlagship2
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
				$product = apply_filters( 'woocommerce_cart_item_product', $cart_item['data'], $cart_item, $cart_item_key );
				if ( ! $product || ! $product->exists() || $cart_item['quantity'] <= 0 || ! apply_filters( 'woocommerce_cart_item_visible', true, $cart_item, $cart_item_key ) ) {
					continue;
				}
				$product_id        = apply_filters( 'woocommerce_cart_item_product_id', $cart_item['product_id'], $cart_item, $cart_item_key );
				$product_permalink = apply_filters( 'woocommerce_cart_item_permalink', $product->is_visible() ? $product->get_permalink( $cart_item ) : '', $cart_item, $cart_item_key );
				$product_name      = apply_filters( 'woocommerce_cart_item_name', $product->get_name(), $cart_item, $cart_item_key );
				$product_thumbnail = apply_filters( 'woocommerce_cart_item_thumbnail', $product->get_image(), $cart_item, $cart_item_key );
				?>
				<article class="sr2-cart__item <?php echo esc_attr( apply_filters( 'woocommerce_cart_item_class', 'cart_item', $cart_item, $cart_item_key ) ); ?>" data-product-id="<?php echo esc_attr( $product_id ); ?>">
					<div class="sr2-cart__image">
						<?php
						if ( $product_permalink ) :
							?>
							<a href="<?php echo esc_url( $product_permalink ); ?>"><?php echo wp_kses_post( $product_thumbnail ); ?></a>
							<?php
else :
	?>
							<?php echo wp_kses_post( $product_thumbnail ); ?><?php endif; ?>
					</div>
					<div class="sr2-cart__item-copy">
						<h2>
						<?php
						if ( $product_permalink ) :
							?>
							<a href="<?php echo esc_url( $product_permalink ); ?>"><?php echo wp_kses_post( $product_name ); ?></a>
							<?php
else :
	?>
							<?php echo wp_kses_post( $product_name ); ?><?php endif; ?></h2>
						<span><?php echo wp_kses_post( WC()->cart->get_product_price( $product ) ); ?></span>
						<?php echo wp_kses_post( wc_get_formatted_cart_item_data( $cart_item ) ); ?>
					</div>
					<div class="sr2-cart__controls">
						<?php
						echo wp_kses_post(
							woocommerce_quantity_input(
								array(
									'input_name'   => "cart[{$cart_item_key}][qty]",
									'input_value'  => $cart_item['quantity'],
									'max_value'    => $product->get_max_purchase_quantity(),
									'min_value'    => '0',
									'product_name' => $product_name,
								),
								$product,
								false
							),
						);
						?>
						<?php
						/* translators: %s: product name. */
						$remove_label = sprintf( __( 'Remove %s from your bag', 'skyyrose-flagship-2' ), wp_strip_all_tags( $product_name ) );
						?>
						<a href="<?php echo esc_url( wc_get_cart_remove_url( $cart_item_key ) ); ?>" aria-label="<?php echo esc_attr( $remove_label ); ?>"><?php esc_html_e( 'Remove', 'skyyrose-flagship-2' ); ?></a>
					</div>
				</article>
			<?php endforeach; ?>
			<?php do_action( 'woocommerce_cart_contents' ); ?>
			<?php do_action( 'woocommerce_after_cart_contents' ); ?>
			<div class="sr2-cart__actions">
				<?php
				if ( wc_coupons_enabled() ) :
					?>
					<label for="coupon_code"><?php esc_html_e( 'Code', 'skyyrose-flagship-2' ); ?></label><input id="coupon_code" type="text" name="coupon_code" value="" placeholder="<?php esc_attr_e( 'Gift code', 'skyyrose-flagship-2' ); ?>"><button type="submit" name="apply_coupon" value="<?php esc_attr_e( 'Apply', 'skyyrose-flagship-2' ); ?>"><?php esc_html_e( 'Apply', 'skyyrose-flagship-2' ); ?></button><?php endif; ?>
				<button type="submit" name="update_cart" value="<?php esc_attr_e( 'Update bag', 'skyyrose-flagship-2' ); ?>"><?php esc_html_e( 'Update bag', 'skyyrose-flagship-2' ); ?></button>
				<?php wp_nonce_field( 'woocommerce-cart', 'woocommerce-cart-nonce' ); ?>
			</div>
			<?php do_action( 'woocommerce_cart_actions' ); ?>
			<?php do_action( 'woocommerce_after_cart_table' ); ?>
		</form>
		<aside class="sr2-cart__summary"><?php do_action( 'woocommerce_cart_collaterals' ); ?></aside>
	</div>
</section>
<?php do_action( 'woocommerce_after_cart' ); ?>
