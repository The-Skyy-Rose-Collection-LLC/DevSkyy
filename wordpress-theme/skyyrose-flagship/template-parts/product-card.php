<?php
/**
 * Template Part: Product Card
 *
 * Reusable product card component with hover effects, quick actions overlay,
 * and collection-aware accent colors. Accepts either a WooCommerce product
 * object or a custom args array.
 *
 * Usage:
 *   get_template_part( 'template-parts/product-card', null, $args );
 *
 * @param array $args {
 *     Product card arguments.
 *
 *     @type WC_Product|null $product       WooCommerce product object.
 *     @type string          $title         Product title (fallback if no product).
 *     @type string          $price         Formatted price string (fallback).
 *     @type string          $image_url     Product image URL (fallback).
 *     @type string          $permalink     Product permalink (fallback).
 *     @type string          $collection    Collection slug for accent color.
 *     @type bool            $show_actions  Whether to show quick action buttons (default true).
 *     @type string          $badge_text    Optional badge text (e.g. "New", "Sale").
 * }
 *
 * @package SkyyRose_Flagship
 * @since 2.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

// Parse arguments with sensible defaults.
$defaults = array(
	'product'      => null,
	'title'        => '',
	'price'        => '',
	'image_url'    => '',
	'permalink'    => '#',
	'collection'   => '',
	'show_actions' => true,
	'badge_text'   => '',
);

$args = wp_parse_args( $args ?? array(), $defaults );

// Extract product data from WooCommerce product object if provided.
$product = $args['product'];

if ( $product instanceof WC_Product ) {
	$product_id   = $product->get_id();
	$title        = $product->get_name();
	$price        = $product->get_price_html();
	$permalink    = $product->get_permalink();
	$image_id     = $product->get_image_id();
	$image_url    = $image_id
		? wp_get_attachment_image_url( $image_id, 'skyyrose-medium' )
		: wc_placeholder_img_src( 'skyyrose-medium' );
	$image_alt    = $image_id
		? get_post_meta( $image_id, '_wp_attachment_image_alt', true )
		: $title;
	$is_on_sale   = $product->is_on_sale();
	$is_in_stock  = $product->is_in_stock();
	$badge_text   = $args['badge_text'];

	if ( empty( $badge_text ) && $is_on_sale ) {
		$badge_text = __( 'Sale', 'skyyrose-flagship' );
	}
} else {
	$product_id  = 0;
	$title       = $args['title'];
	$price       = $args['price'];
	$permalink   = $args['permalink'];
	$image_url   = $args['image_url'] ?: get_template_directory_uri() . '/assets/images/placeholder.jpg';
	$image_alt   = $title;
	$is_on_sale  = false;
	$is_in_stock = true;
	$badge_text  = $args['badge_text'];
}

$collection   = $args['collection'];
$show_actions = $args['show_actions'];

// Build CSS class list.
$card_classes = array( 'product-card' );
if ( ! empty( $collection ) ) {
	$card_classes[] = 'product-card--' . sanitize_html_class( $collection );
}
if ( ! $is_in_stock ) {
	$card_classes[] = 'product-card--out-of-stock';
}
?>

<article class="<?php echo esc_attr( implode( ' ', $card_classes ) ); ?>" data-product-id="<?php echo esc_attr( $product_id ); ?>">

	<!-- Image Container (3:4 aspect ratio) -->
	<div class="product-card__image-container">
		<a href="<?php echo esc_url( $permalink ); ?>" class="product-card__image-link" aria-label="<?php echo esc_attr( sprintf(
			/* translators: %s: product name */
			__( 'View %s', 'skyyrose-flagship' ),
			$title
		) ); ?>">
			<img
				src="<?php echo esc_url( $image_url ); ?>"
				alt="<?php echo esc_attr( $image_alt ); ?>"
				class="product-card__image"
				loading="lazy"
				decoding="async"
			>
		</a>

		<?php if ( ! empty( $badge_text ) ) : ?>
			<span class="product-card__badge">
				<?php echo esc_html( $badge_text ); ?>
			</span>
		<?php endif; ?>

		<?php if ( ! $is_in_stock ) : ?>
			<span class="product-card__badge product-card__badge--sold-out">
				<?php esc_html_e( 'Sold Out', 'skyyrose-flagship' ); ?>
			</span>
		<?php endif; ?>

		<?php if ( $show_actions ) : ?>
			<!-- Quick Actions Overlay -->
			<div class="product-card__actions" aria-label="<?php esc_attr_e( 'Quick actions', 'skyyrose-flagship' ); ?>">

				<!-- Wishlist Heart -->
				<button
					class="product-card__action-btn product-card__wishlist-btn"
					data-product-id="<?php echo esc_attr( $product_id ); ?>"
					aria-label="<?php echo esc_attr( sprintf(
						/* translators: %s: product name */
						__( 'Add %s to wishlist', 'skyyrose-flagship' ),
						$title
					) ); ?>"
					type="button"
				>
					<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
						<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
					</svg>
				</button>

				<!-- Quick View Eye -->
				<button
					class="product-card__action-btn product-card__quickview-btn"
					data-product-id="<?php echo esc_attr( $product_id ); ?>"
					aria-label="<?php echo esc_attr( sprintf(
						/* translators: %s: product name */
						__( 'Quick view %s', 'skyyrose-flagship' ),
						$title
					) ); ?>"
					type="button"
				>
					<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
						<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
						<circle cx="12" cy="12" r="3"/>
					</svg>
				</button>

				<!-- Add to Cart -->
				<?php if ( $is_in_stock && $product instanceof WC_Product ) : ?>
					<a
						href="<?php echo esc_url( $product->add_to_cart_url() ); ?>"
						class="product-card__action-btn product-card__add-to-cart ajax_add_to_cart"
						data-product_id="<?php echo esc_attr( $product_id ); ?>"
						data-quantity="1"
						aria-label="<?php echo esc_attr( sprintf(
							/* translators: %s: product name */
							__( 'Add %s to cart', 'skyyrose-flagship' ),
							$title
						) ); ?>"
					>
						<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
							<path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/>
							<path d="M3 6h18"/>
							<path d="M16 10a4 4 0 0 1-8 0"/>
						</svg>
						<span class="product-card__action-text">
							<?php esc_html_e( 'Add to Cart', 'skyyrose-flagship' ); ?>
						</span>
					</a>
				<?php elseif ( $is_in_stock ) : ?>
					<a
						href="<?php echo esc_url( $permalink ); ?>"
						class="product-card__action-btn product-card__add-to-cart"
						aria-label="<?php echo esc_attr( sprintf(
							/* translators: %s: product name */
							__( 'View %s', 'skyyrose-flagship' ),
							$title
						) ); ?>"
					>
						<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
							<path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/>
							<path d="M3 6h18"/>
							<path d="M16 10a4 4 0 0 1-8 0"/>
						</svg>
						<span class="product-card__action-text">
							<?php esc_html_e( 'Shop Now', 'skyyrose-flagship' ); ?>
						</span>
					</a>
				<?php endif; ?>

			</div>
		<?php endif; ?>
	</div>

	<!-- Product Info -->
	<div class="product-card__info">
		<h3 class="product-card__title">
			<a href="<?php echo esc_url( $permalink ); ?>">
				<?php echo esc_html( $title ); ?>
			</a>
		</h3>
		<?php if ( ! empty( $price ) ) : ?>
			<div class="product-card__price">
				<?php echo wp_kses_post( $price ); ?>
			</div>
		<?php endif; ?>
	</div>

</article>
