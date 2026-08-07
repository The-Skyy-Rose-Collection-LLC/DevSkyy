<?php
/**
 * SOT-only cart image surface.
 *
 * @package SkyyRoseFlagshipSOT
 */

defined( 'ABSPATH' ) || exit;
do_action( 'woocommerce_before_cart' );
?>
<main id="primary" class="srs-page"><header><p><?php esc_html_e( 'Your bag', 'skyyrose-flagship-sot' ); ?></p><h1><?php esc_html_e( 'Keep your pieces close.', 'skyyrose-flagship-sot' ); ?></h1></header>
<?php
if ( WC()->cart && ! WC()->cart->is_empty() ) :
	?>
	<form class="woocommerce-cart-form srs-cart" action="<?php echo esc_url( wc_get_cart_url() ); ?>" method="post">
	<?php
	do_action( 'woocommerce_before_cart_table' );
	do_action( 'woocommerce_before_cart_contents' );
	?>
	<?php
	foreach ( WC()->cart->get_cart() as $cart_item_key => $cart_item ) :
		$product = apply_filters( 'woocommerce_cart_item_product', $cart_item['data'], $cart_item, $cart_item_key );
		if ( ! $product || ! $product->exists() || $cart_item['quantity'] <= 0 ) {
			continue;
		} $product_data = skyyrosesot_product_by_sku( $product->get_sku() );
		$image          = skyyrosesot_product_image( $product_data );
		?>
		<?php
		if ( $image ) :
			?>
	<article class="srs-product"><a href="<?php echo esc_url( $product->get_permalink( $cart_item ) ); ?>"><img src="<?php echo esc_url( skyyrosesot_asset_uri( $image ) ); ?>" alt="<?php echo esc_attr( $product->get_name() ); ?>" width="720" height="960"></a><p><?php echo esc_html( $product->get_sku() ); ?></p><h3><a href="<?php echo esc_url( $product->get_permalink( $cart_item ) ); ?>"><?php echo esc_html( $product->get_name() ); ?></a></h3><div><span><?php echo wp_kses_post( WC()->cart->get_product_subtotal( $product, $cart_item['quantity'] ) ); ?></span>
			<?php
			echo wp_kses_post(
				woocommerce_quantity_input(
					array(
						'input_name'   => "cart[{$cart_item_key}][qty]",
						'input_value'  => $cart_item['quantity'],
						'max_value'    => $product->get_max_purchase_quantity(),
						'min_value'    => '0',
						'product_name' => $product->get_name(),
					),
					$product,
					false
				)
			);
			?>
	</div></article><?php endif; ?><?php endforeach; ?>
	<?php
	do_action( 'woocommerce_cart_contents' );
	do_action( 'woocommerce_after_cart_contents' );
	?>
<button class="button" type="submit" name="update_cart" value="<?php esc_attr_e( 'Update bag', 'skyyrose-flagship-sot' ); ?>"><?php esc_html_e( 'Update bag', 'skyyrose-flagship-sot' ); ?></button>
	<?php
	wp_nonce_field( 'woocommerce-cart', 'woocommerce-cart-nonce' );
	do_action( 'woocommerce_cart_actions' );
	do_action( 'woocommerce_after_cart_table' );
	?>
</form><div class="cart-collaterals"><?php do_action( 'woocommerce_cart_collaterals' ); ?></div>
	<?php
else :
	?>
	<p class="srs-empty"><?php esc_html_e( 'Your bag is empty.', 'skyyrose-flagship-sot' ); ?></p><a class="srs-button" href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>"><?php esc_html_e( 'Shop pieces', 'skyyrose-flagship-sot' ); ?></a><?php endif; ?></main><?php do_action( 'woocommerce_after_cart' ); ?>
