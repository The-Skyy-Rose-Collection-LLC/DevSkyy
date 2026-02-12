<?php
/**
 * Template part for displaying wishlist button
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

global $product;

if ( ! $product ) {
	return;
}

$product_id   = $product->get_id();
$in_wishlist  = skyyrose_is_in_wishlist( $product_id );
$button_class = $in_wishlist ? 'wishlist-button in-wishlist' : 'wishlist-button';
$button_title = $in_wishlist ? esc_attr__( 'Remove from wishlist', 'skyyrose-flagship' ) : esc_attr__( 'Add to wishlist', 'skyyrose-flagship' );
?>

<button
	type="button"
	class="<?php echo esc_attr( $button_class ); ?>"
	data-product-id="<?php echo esc_attr( $product_id ); ?>"
	title="<?php echo $button_title; ?>"
	aria-label="<?php echo $button_title; ?>"
>
	<svg class="icon" width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
		<path d="M17.367 3.842a4.583 4.583 0 0 0-6.484 0L10 4.725l-.883-.883a4.584 4.584 0 1 0-6.484 6.483l.883.884L10 17.692l6.484-6.483.883-.884a4.583 4.583 0 0 0 0-6.483z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
	</svg>
</button>
