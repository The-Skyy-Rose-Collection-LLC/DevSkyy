<?php
/**
 * Template Part: Holo Product Card — Impeccable Refinement
 *
 * Enforces technical blueprint hover (techflat) and garment lock.
 *
 * @package SkyyRose
 */

defined( 'ABSPATH' ) || exit;

$wc_product = null;
$product_id = 0;

if ( isset( $args['product'] ) && $args['product'] instanceof WC_Product ) {
	$wc_product = $args['product'];
	$product_id = $wc_product->get_id();
}

$collection   = ! empty( $args['collection'] ) ? sanitize_title( (string) $args['collection'] ) : '';
$title        = $wc_product ? $wc_product->get_name() : ( $args['title'] ?? '' );
$price_html   = $wc_product ? $wc_product->get_price_html() : esc_html( $args['price'] ?? '' );
$sku          = $wc_product ? $wc_product->get_sku() : ( $args['sku'] ?? '' );
$garment_lock = $args['garment_lock'] ?? '';

// Images — Front (Model/Finished) vs Back (Techflat/Technical)
//
// IMAGERY PRECEDENCE (canon, 2026-06-16): the catalog/SOT render is the
// AUTHORITY for which garment a card shows — NOT the WooCommerce featured
// image. WC featured images were uploaded during the store sync and can
// diverge from the per-collection SOT (data/collections/<slug>/sot.json,
// generated from the catalog) — that divergence is how never-made / wrong-
// garment renders leaked onto cards. So resolve the SOT/catalog
// front_model_image FIRST; use a WC featured image only when the catalog has
// no render; placeholder last. WooCommerce still owns price, stock, and
// add-to-cart (below) — imagery is the SOT's job, commerce is WC's.
$front_url = '';
if ( '' !== $sku && function_exists( 'skyyrose_get_product' ) ) {
	$lookup_sku      = function_exists( 'skyyrose_normalize_sku' ) ? skyyrose_normalize_sku( $sku ) : $sku;
	$catalog_product = skyyrose_get_product( $lookup_sku );
	if ( $catalog_product ) {
		$catalog_image = ( $catalog_product['front_model_image'] ?? '' ) ?: ( $catalog_product['image'] ?? '' );
		if ( '' !== $catalog_image ) {
			$front_url = skyyrose_product_image_uri( $catalog_image );
		}
	}
}
// Static-card path (no WC product) already carries the resolved SOT image.
if ( empty( $front_url ) ) {
	$front_url = $args['image_url'] ?? '';
}
// Only if the catalog/SOT has no render: fall back to a WC featured image.
if ( empty( $front_url ) && $wc_product ) {
	$front_url = wp_get_attachment_image_url( $wc_product->get_image_id(), 'large' ) ?: '';
}
$back_url  = $args['image_back'] ?? ''; // Passed from catalog as the 'image' (techflat) column
$permalink = $args['permalink'] ?? '';

if ( empty( $front_url ) ) {
	$front_url = get_theme_file_uri( 'assets/images/placeholder-product.jpg' );
}
if ( empty( $back_url ) ) {
	$back_url = $front_url; // Fallback if no techflat yet
}
if ( empty( $permalink ) && $product_id > 0 ) {
	$permalink = get_permalink( $product_id );
}
if ( empty( $permalink ) ) {
	$permalink = '#';
}

$index = (int) ( $args['index'] ?? 0 );
?>
<div class="holo holo--<?php echo esc_attr( $collection ); ?>" 
	data-sku="<?php echo esc_attr( $sku ); ?>"
	data-garment-lock="<?php echo esc_attr( $garment_lock ); ?>"
	style="--holo-delay: <?php echo esc_attr( $index * 80 ); ?>ms">

	<div class="holo__body">
		<div class="holo__gallery">
			<a href="<?php echo esc_url( $permalink ); ?>" class="holo__img-link" aria-label="<?php echo esc_attr( sprintf( /* translators: %s: product name */ __( 'View %s', 'skyyrose' ), $title ) ); ?>">
				<?php
				echo skyyrose_render_picture( // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- helper escapes internally.
					$front_url,
					$title,
					array(
						'class'    => 'holo__img holo__img--front',
						'loading'  => 'lazy',
						'decoding' => 'async',
						'width'    => '600',
						'height'   => '750',
					)
				);
				echo skyyrose_render_picture( // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- helper escapes internally.
					$back_url,
					$title . ' — technical blueprint view',
					array(
						'class'    => 'holo__img holo__img--back',
						'loading'  => 'lazy',
						'decoding' => 'async',
						'width'    => '600',
						'height'   => '750',
					)
				);
				?>
			</a>
		</div>

		<div class="holo__info">
			<span class="holo__collection"><?php echo esc_html( strtoupper( str_replace( '-', ' ', $collection ) ) ); ?></span>
			<h3 class="holo__name">
				<a href="<?php echo esc_url( $permalink ); ?>"><?php echo esc_html( $title ); ?></a>
			</h3>
			<div class="holo__price-row">
				<span class="holo__price"><?php echo wp_kses_post( $price_html ); ?></span>
			</div>
		</div>

		<div class="holo__drawer">
			<div class="holo__sizes" role="radiogroup" aria-label="<?php esc_attr_e( 'Select size', 'skyyrose' ); ?>">
				<button type="button" class="holo__size-pill" data-size="S" role="radio" aria-checked="false">S</button>
				<button type="button" class="holo__size-pill" data-size="M" role="radio" aria-checked="false">M</button>
				<button type="button" class="holo__size-pill" data-size="L" role="radio" aria-checked="false">L</button>
				<button type="button" class="holo__size-pill" data-size="XL" role="radio" aria-checked="false">XL</button>
			</div>
			<?php
			/*
			 * Add-to-Cart button — wires the holo card into product-card-holo.js's
			 * AJAX handler. The handler binds via `.holo__buy[data-product-id]`,
			 * so the data attribute is the activation contract.
			 *
			 * Element is a real <button> (not <a>) because the JS toggles the
			 * native `disabled` attribute as a double-click guard during the
			 * AJAX cycle — disabled has no semantics on <a>.
			 *
			 * Product-page navigation lives on the title and gallery links
			 * above (lines 44 + 52-54); the holo card's drawer CTA is now
			 * the conversion path.
			 *
			 * aria-label is set so the button has an accessible name even
			 * during the loading state when textContent is cleared.
			 */
			?>
			<button type="button" class="holo__buy"
				data-product-id="<?php echo esc_attr( (int) $product_id ); ?>"
				aria-label="<?php echo esc_attr( sprintf( /* translators: %s: product name */ __( 'Add %s to cart', 'skyyrose' ), $title ) ); ?>"
				<?php disabled( $product_id <= 0 ); ?>>
				<?php esc_html_e( 'Add to Cart', 'skyyrose' ); ?>
			</button>
			<button type="button" class="holo__wishlist"
				data-product-id="<?php echo esc_attr( (int) $product_id ); ?>"
				data-wishlist-id="<?php echo esc_attr( (int) $product_id ); ?>"
				aria-pressed="false"
				aria-label="<?php echo esc_attr( sprintf( /* translators: %s: product name */ __( 'Add %s to wishlist', 'skyyrose' ), $title ) ); ?>">
				&#9825;
			</button>
		</div>
	</div>
</div>
