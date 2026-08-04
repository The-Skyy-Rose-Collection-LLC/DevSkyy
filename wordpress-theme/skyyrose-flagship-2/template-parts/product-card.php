<?php
/**
 * Reusable WooCommerce-backed product card.
 *
 * The product's attached media remains the only image source in this
 * self-contained theme. A missing attachment deliberately renders an honest
 * unavailable state instead of substituting an unrelated garment or stock art.
 *
 * @package SkyyRoseFlagship2
 */

defined( 'ABSPATH' ) || exit;

$args = wp_parse_args(
	$args ?? array(),
	array(
		'product'        => null,
		'image_loading'  => 'lazy',
		'image_priority' => false,
	)
);

$card_product = $args['product'];

if ( ! $card_product instanceof WC_Product || ! $card_product->is_visible() ) {
	return;
}

$product_id     = $card_product->get_id();
$product_url    = get_permalink( $product_id );
$product_name   = $card_product->get_name();
$image_id       = $card_product->get_image_id();
$image_loading  = 'eager' === $args['image_loading'] ? 'eager' : 'lazy';
$image_priority = ! empty( $args['image_priority'] );
$categories     = wc_get_product_category_list( $product_id, ' · ' );
$availability   = $card_product->is_in_stock()
	? __( 'Available', 'skyyrose-flagship-2' )
	: __( 'Reserved', 'skyyrose-flagship-2' );

$image_attributes = array(
	'class'    => 'sr2-product-card__image-asset',
	'alt'      => $product_name,
	'loading'  => $image_loading,
	'decoding' => $image_priority ? 'sync' : 'async',
);

if ( $image_priority ) {
	$image_attributes['fetchpriority'] = 'high';
}

/**
 * Lets an SOT-aware integration supply verified product imagery without
 * coupling this standalone theme to the production theme's catalog files.
 *
 * @param string     $image_html Image markup.
 * @param WC_Product $product Product being rendered.
 * @param array      $image_attributes Attachment image attributes.
 */
$image_html = apply_filters( 'skyyrose2_product_card_image_html', '', $card_product, $image_attributes );

if ( '' === $image_html && $image_id ) {
	$image_html = wp_get_attachment_image( $image_id, 'woocommerce_thumbnail', false, $image_attributes );
}
?>
<article class="sr2-product sr2-product-card" data-depth-card>
	<div class="sr2-product-card__gallery">
		<a class="sr2-product-card__image" href="<?php echo esc_url( $product_url ); ?>" aria-label="<?php echo esc_attr( sprintf( __( 'View %s', 'skyyrose-flagship-2' ), $product_name ) ); ?>">
			<?php if ( $image_html ) : ?>
				<?php echo wp_kses_post( $image_html ); ?>
			<?php else : ?>
				<span class="sr2-product-card__image-unavailable"><?php esc_html_e( 'Product imagery unavailable', 'skyyrose-flagship-2' ); ?></span>
			<?php endif; ?>
			<span class="sr2-product-card__view"><?php esc_html_e( 'View piece', 'skyyrose-flagship-2' ); ?></span>
		</a>
		<button class="sr2-product-card__wishlist" type="button" data-sr2-wishlist-id="<?php echo esc_attr( (string) $product_id ); ?>" data-wishlist-add-label="<?php echo esc_attr( sprintf( __( 'Add %s to wishlist', 'skyyrose-flagship-2' ), $product_name ) ); ?>" data-wishlist-remove-label="<?php echo esc_attr( sprintf( __( 'Remove %s from wishlist', 'skyyrose-flagship-2' ), $product_name ) ); ?>" aria-pressed="false" aria-label="<?php echo esc_attr( sprintf( __( 'Add %s to wishlist', 'skyyrose-flagship-2' ), $product_name ) ); ?>">
			<span aria-hidden="true">♡</span>
		</button>
	</div>
	<div class="sr2-product-card__info">
		<p class="sr2-product-card__meta"><?php echo $categories ? wp_kses_post( $categories ) : esc_html__( 'SkyyRose', 'skyyrose-flagship-2' ); ?></p>
		<h3 class="sr2-product-card__title"><a href="<?php echo esc_url( $product_url ); ?>"><?php echo esc_html( $product_name ); ?></a></h3>
		<div class="sr2-product-card__price-row">
			<span class="sr2-product-card__price"><?php echo wp_kses_post( $card_product->get_price_html() ); ?></span>
			<span class="sr2-product-card__availability"><?php echo esc_html( $availability ); ?></span>
		</div>
	</div>
	<div class="sr2-product-card__commerce">
		<?php
		global $product;
		$previous_product = $product;
		$product          = $card_product;
		woocommerce_template_loop_add_to_cart();
		$product = $previous_product;
		?>
	</div>
</article>
