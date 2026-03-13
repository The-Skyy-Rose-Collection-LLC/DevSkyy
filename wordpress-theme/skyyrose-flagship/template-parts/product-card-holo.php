<?php
/**
 * Template Part: Holo Product Card
 *
 * Physics-based magnetic tilt, holographic cursor refraction, front/back
 * crossfade, ambient collection glow, and inline quick-add drawer.
 * Progressively enhanced by product-card-holo.js.
 *
 * Accepts WC_Product objects OR static arrays. Collection-aware via
 * CSS custom properties (--holo-accent, --holo-accent-rgb, --holo-radius).
 *
 * Usage:
 *   get_template_part( 'template-parts/product-card-holo', null, $args );
 *
 * @param array $args {
 *     @type WC_Product|null $product      WC product object.
 *     @type string          $title        Fallback title if no product.
 *     @type string          $price        Fallback price HTML.
 *     @type string          $image_url    Fallback front image URL.
 *     @type string          $image_back   Back image URL (crossfade).
 *     @type string          $permalink    Fallback permalink.
 *     @type string          $collection   Collection slug override.
 *     @type string          $badge_text   Override badge text.
 *     @type string          $desc         Short description.
 *     @type string          $sku          SKU string.
 *     @type int             $index        Card index for stagger delay.
 * }
 *
 * @package SkyyRose_Flagship
 * @since   5.0.0
 */

defined( 'ABSPATH' ) || exit;

$defaults = array(
	'product'    => null,
	'title'      => '',
	'price'      => '',
	'image_url'  => '',
	'image_back' => '',
	'permalink'  => '#',
	'collection' => '',
	'badge_text' => '',
	'desc'       => '',
	'sku'        => '',
	'index'      => 0,
);
$args = wp_parse_args( $args ?? array(), $defaults );

// ---------------------------------------------------------------------------
// Resolve product data from WC_Product or static args.
// ---------------------------------------------------------------------------
$wc         = $args['product'];
$is_wc      = ( $wc instanceof WC_Product );
$product_id = $is_wc ? $wc->get_id() : 0;

$title     = $is_wc ? $wc->get_name()          : $args['title'];
$price     = $is_wc ? $wc->get_price_html()     : $args['price'];
$permalink = $is_wc ? $wc->get_permalink()       : $args['permalink'];
$sku       = $is_wc ? $wc->get_sku()             : $args['sku'];
$desc      = $is_wc ? wp_strip_all_tags( $wc->get_short_description() ) : $args['desc'];

// Front image.
if ( $is_wc ) {
	$img_id    = $wc->get_image_id();
	$image_url = $img_id ? wp_get_attachment_image_url( $img_id, 'large' ) : '';
} else {
	$image_url = $args['image_url'];
}
if ( empty( $image_url ) && defined( 'SKYYROSE_ASSETS_URI' ) ) {
	$image_url = SKYYROSE_ASSETS_URI . '/images/placeholder-product.jpg';
}

// Back image (from gallery second image or explicit arg).
$image_back = $args['image_back'];
if ( empty( $image_back ) && $is_wc ) {
	$gallery = $wc->get_gallery_image_ids();
	if ( ! empty( $gallery[0] ) ) {
		$image_back = wp_get_attachment_image_url( $gallery[0], 'large' );
	}
}

// Stock and pre-order status.
$in_stock   = $is_wc ? $wc->is_in_stock() : true;
$on_sale    = $is_wc ? $wc->is_on_sale() : false;
$is_preorder = false;
if ( function_exists( 'skyyrose_is_preorder' ) && $product_id ) {
	$is_preorder = skyyrose_is_preorder( $product_id );
}
$stock_status = $is_wc ? $wc->get_stock_status() : 'instock';

// Badge.
$badge = $args['badge_text'];
if ( empty( $badge ) ) {
	if ( $is_preorder ) {
		$badge = __( 'Pre-Order', 'skyyrose-flagship' );
	} elseif ( $on_sale ) {
		$badge = __( 'Sale', 'skyyrose-flagship' );
	} elseif ( ! $in_stock ) {
		$badge = __( 'Sold Out', 'skyyrose-flagship' );
	}
}

// Sizes (from variable product or static).
$sizes = array();
if ( $is_wc && $wc->is_type( 'variable' ) ) {
	$attrs = $wc->get_variation_attributes();
	foreach ( $attrs as $attr_name => $values ) {
		if ( false !== stripos( $attr_name, 'size' ) ) {
			$sizes = array_values( array_filter( $values ) );
			break;
		}
	}
}

// Edition info.
$edition_size = $product_id ? get_post_meta( $product_id, '_skyyrose_edition_of', true ) : '';
$is_limited   = $product_id ? get_post_meta( $product_id, '_skyyrose_limited', true ) : '';

// ---------------------------------------------------------------------------
// Collection detection.
// ---------------------------------------------------------------------------
$collection = $args['collection'];
if ( empty( $collection ) && function_exists( 'skyyrose_get_product_collection' ) && $product_id ) {
	$collection = skyyrose_get_product_collection( $product_id );
}

// Collection palette defaults per slug.
$palettes = array(
	'black-rose'   => array( '#C0C0C0', '192,192,192', '2px' ),
	'love-hurts'   => array( '#DC143C', '220,20,60', '2px' ),
	'signature'    => array( '#D4AF37', '212,175,55', '2px' ),
	'kids-capsule' => array( '#FFB6C1', '255,182,193', '16px' ),
	'default'      => array( '#B76E79', '183,110,121', '8px' ),
);
$pal = isset( $palettes[ $collection ] ) ? $palettes[ $collection ] : $palettes['default'];

// Stagger delay.
$delay = min( (int) $args['index'], 11 ) * 80;

// Card classes.
$classes = array( 'holo' );
if ( ! empty( $collection ) ) {
	$classes[] = 'holo--' . sanitize_html_class( $collection );
}
if ( $is_preorder ) {
	$classes[] = 'holo--preorder';
}
if ( ! $in_stock && ! $is_preorder ) {
	$classes[] = 'holo--sold-out';
}
if ( $is_limited ) {
	$classes[] = 'holo--limited';
}
?>

<article
	class="<?php echo esc_attr( implode( ' ', $classes ) ); ?>"
	data-product-id="<?php echo esc_attr( $product_id ); ?>"
	data-sku="<?php echo esc_attr( $sku ); ?>"
	data-has-back="<?php echo esc_attr( ! empty( $image_back ) ? '1' : '0' ); ?>"
	style="--holo-accent:<?php echo esc_attr( $pal[0] ); ?>;--holo-accent-rgb:<?php echo esc_attr( $pal[1] ); ?>;--holo-radius:<?php echo esc_attr( $pal[2] ); ?>;--holo-delay:<?php echo esc_attr( $delay ); ?>ms;"
	tabindex="0"
	role="group"
	aria-label="<?php echo esc_attr( $title ); ?>">

	<!-- Ambient glow (beneath card, collection-colored) -->
	<div class="holo__glow" aria-hidden="true"></div>

	<!-- Tiltable card body -->
	<div class="holo__body">

		<!-- Holographic shimmer overlay -->
		<div class="holo__shimmer" aria-hidden="true"></div>

		<!-- Gallery -->
		<div class="holo__gallery">
			<a href="<?php echo esc_url( $permalink ); ?>" class="holo__img-link"
			   aria-label="<?php echo esc_attr( sprintf( __( 'View %s', 'skyyrose-flagship' ), $title ) ); ?>">
				<img src="<?php echo esc_url( $image_url ); ?>"
				     alt="<?php echo esc_attr( $title ); ?>"
				     class="holo__img holo__img--front"
				     width="400" height="533" loading="lazy" decoding="async">
				<?php if ( ! empty( $image_back ) ) : ?>
					<img src="<?php echo esc_url( $image_back ); ?>"
					     alt="<?php echo esc_attr( $title . ' — back' ); ?>"
					     class="holo__img holo__img--back"
					     width="400" height="533" loading="lazy" decoding="async">
				<?php endif; ?>
			</a>

			<!-- Badge -->
			<?php if ( ! empty( $badge ) ) : ?>
				<span class="holo__badge holo__badge--<?php echo esc_attr( $is_preorder ? 'preorder' : ( $on_sale ? 'sale' : ( $in_stock ? 'default' : 'soldout' ) ) ); ?>">
					<?php echo esc_html( $badge ); ?>
				</span>
			<?php endif; ?>

			<?php if ( $is_limited && $edition_size ) : ?>
				<span class="holo__edition"><?php
					printf(
						/* translators: %d: edition size */
						esc_html__( '%d Pieces', 'skyyrose-flagship' ),
						intval( $edition_size )
					);
				?></span>
			<?php endif; ?>

			<!-- Wishlist -->
			<button class="holo__wishlist" type="button"
			        data-wishlist-id="<?php echo esc_attr( $sku ?: $product_id ); ?>"
			        aria-label="<?php echo esc_attr( sprintf( __( 'Add %s to wishlist', 'skyyrose-flagship' ), $title ) ); ?>"
			        aria-pressed="false">
				<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
					<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
				</svg>
			</button>

			<!-- View indicator (shows on hover with back image) -->
			<?php if ( ! empty( $image_back ) ) : ?>
				<div class="holo__view-indicator" aria-hidden="true">
					<span class="holo__view-dot holo__view-dot--active"></span>
					<span class="holo__view-dot"></span>
				</div>
			<?php endif; ?>
		</div>

		<!-- Info -->
		<div class="holo__info">
			<?php if ( ! empty( $collection ) && 'default' !== $collection ) : ?>
				<span class="holo__collection"><?php echo esc_html( strtoupper( str_replace( '-', ' ', $collection ) ) ); ?></span>
			<?php endif; ?>

			<h3 class="holo__name">
				<a href="<?php echo esc_url( $permalink ); ?>"><?php echo esc_html( $title ); ?></a>
			</h3>

			<div class="holo__price-row">
				<span class="holo__price"><?php echo wp_kses_post( $price ); ?></span>
				<?php if ( $stock_status === 'onbackorder' ) : ?>
					<span class="holo__ship-note"><?php esc_html_e( 'Ships Spring 2026', 'skyyrose-flagship' ); ?></span>
				<?php endif; ?>
			</div>
		</div>

		<!-- Quick-Add Drawer (slides up on hover) -->
		<?php if ( $in_stock || $is_preorder ) : ?>
		<div class="holo__drawer" aria-label="<?php esc_attr_e( 'Quick add to cart', 'skyyrose-flagship' ); ?>">

			<?php if ( ! empty( $sizes ) ) : ?>
			<div class="holo__sizes" role="radiogroup" aria-label="<?php esc_attr_e( 'Select size', 'skyyrose-flagship' ); ?>">
				<?php foreach ( $sizes as $size ) : ?>
					<button class="holo__size-pill" type="button"
					        data-size="<?php echo esc_attr( $size ); ?>"
					        role="radio" aria-checked="false">
						<?php echo esc_html( $size ); ?>
					</button>
				<?php endforeach; ?>
			</div>
			<?php endif; ?>

			<?php if ( $is_wc ) : ?>
				<button class="holo__buy" type="button"
				        data-product-id="<?php echo esc_attr( $product_id ); ?>"
				        data-add-to-cart-url="<?php echo esc_url( $wc->add_to_cart_url() ); ?>"
				        <?php echo ! empty( $sizes ) ? 'disabled' : ''; ?>>
					<?php echo esc_html( $is_preorder ? __( 'Pre-Order Now', 'skyyrose-flagship' ) : __( 'Add to Bag', 'skyyrose-flagship' ) ); ?>
				</button>
			<?php else : ?>
				<a class="holo__buy holo__buy--link" href="<?php echo esc_url( $permalink ); ?>">
					<?php echo esc_html( $is_preorder ? __( 'Pre-Order Now', 'skyyrose-flagship' ) : __( 'Shop Now', 'skyyrose-flagship' ) ); ?>
				</a>
			<?php endif; ?>

		</div>
		<?php endif; ?>

	</div>
</article>
