<?php
/**
 * Template Part: Holo Product Card — Impeccable Refinement
 * 
 * Enforces technical blueprint hover (techflat) and garment lock.
 */

defined( 'ABSPATH' ) || exit;

$wc_product = null;
$product_id = 0;

if ( isset( $args['product'] ) && $args['product'] instanceof WC_Product ) {
	$wc_product = $args['product'];
	$product_id = $wc_product->get_id();
}

$collection = ! empty( $args['collection'] ) ? sanitize_title( (string) $args['collection'] ) : '';
$title = $wc_product ? $wc_product->get_name() : ($args['title'] ?? '');
$price_html = $wc_product ? $wc_product->get_price_html() : esc_html( $args['price'] ?? '' );
$sku = $wc_product ? $wc_product->get_sku() : ($args['sku'] ?? '');
$garment_lock = $args['garment_lock'] ?? '';

// Images — Front (Model/Finished) vs Back (Techflat/Technical)
$front_url = $wc_product ? wp_get_attachment_image_url($wc_product->get_image_id(), 'large') : ($args['image_url'] ?? '');
$back_url  = $args['image_back'] ?? ''; // Passed from catalog as the 'image' (techflat) column

if ( empty( $front_url ) ) {
	$front_url = get_theme_file_uri( 'assets/images/placeholder-product.jpg' );
}
if ( empty( $back_url ) ) {
	$back_url = $front_url; // Fallback if no techflat yet
}

$index = (int) ( $args['index'] ?? 0 );
?>
<div class="holo holo--<?php echo esc_attr($collection); ?>" 
     data-sku="<?php echo esc_attr($sku); ?>"
     data-garment-lock="<?php echo esc_attr($garment_lock); ?>"
     style="--holo-delay: <?php echo esc_attr($index * 80); ?>ms">

	<div class="holo__body">
		<div class="holo__gallery">
			<a href="<?php echo esc_url( get_permalink($product_id) ); ?>" class="holo__img-link">
				<img class="holo__img holo__img--front" src="<?php echo esc_url($front_url); ?>" alt="<?php echo esc_attr($title); ?>" loading="lazy">
				<img class="holo__img holo__img--back" src="<?php echo esc_url($back_url); ?>" alt="Technical Blueprint" loading="lazy">
			</a>
		</div>

		<div class="holo__info">
			<span class="holo__collection"><?php echo esc_html(strtoupper(str_replace('-', ' ', $collection))); ?></span>
			<h3 class="holo__name">
				<a href="<?php echo esc_url(get_permalink($product_id)); ?>"><?php echo esc_html($title); ?></a>
			</h3>
			<div class="holo__price-row">
				<span class="holo__price"><?php echo wp_kses_post($price_html); ?></span>
			</div>
		</div>

		<div class="holo__drawer">
			<div class="holo__sizes">
				<span class="holo__size-pill">S</span>
				<span class="holo__size-pill">M</span>
				<span class="holo__size-pill">L</span>
				<span class="holo__size-pill">XL</span>
			</div>
			<a href="<?php echo esc_url(get_permalink($product_id)); ?>" class="holo__buy">View Technical Details</a>
		</div>
	</div>
</div>
