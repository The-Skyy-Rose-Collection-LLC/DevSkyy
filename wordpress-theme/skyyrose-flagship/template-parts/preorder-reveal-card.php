<?php
/**
 * Template Part: Pre-Order Reveal Card
 *
 * Dramatic countdown card with blur-to-reveal animation.
 * Card starts locked (blurred) with a countdown timer overlay.
 * When timer completes, blur removes with scale animation and
 * particle burst, revealing the product with a pulsing CTA.
 *
 * Enhanced by interactive-cards.js (initPreOrderReveal).
 *
 * Usage:
 *   get_template_part( 'template-parts/preorder-reveal-card', null, $args );
 *
 * @param array $args {
 *     @type array  $product    Product data array.
 *     @type array  $collection Collection config (slug, name, accent, accent_rgb).
 *     @type string $reveal_at  ISO 8601 UTC timestamp for reveal, or empty for immediate.
 * }
 *
 * @package SkyyRose_Flagship
 * @since   4.1.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

// Parse top-level args.
$args = wp_parse_args( $args ?? array(), array(
	'product'    => array(),
	'collection' => array(),
	'reveal_at'  => '',
) );

// Normalise product.
$product = wp_parse_args( is_array( $args['product'] ) ? $args['product'] : array(), array(
	'sku'           => '',
	'name'          => '',
	'price'         => 0,
	'price_display' => '',
	'desc'          => '',
	'image'         => '',
	'url'           => '',
	'sizes'         => array(),
	'is_preorder'   => true,
) );

// Normalise collection.
$collection = wp_parse_args( is_array( $args['collection'] ) ? $args['collection'] : array(), array(
	'slug'       => '',
	'name'       => '',
	'accent'     => '#B76E79',
	'accent_rgb' => '183, 110, 121',
) );

// Reveal-time logic.
$reveal_at   = (string) $args['reveal_at'];
$is_revealed = empty( $reveal_at ) || strtotime( $reveal_at ) <= time();

// Normalise timestamp for JS.
$reveal_at_iso = '';
if ( ! empty( $reveal_at ) ) {
	$ts = strtotime( $reveal_at );
	if ( false !== $ts ) {
		$reveal_at_iso = gmdate( 'Y-m-d\TH:i:s\Z', $ts );
	}
}

// Resolve image URL.
$image_raw = (string) $product['image'];
if ( empty( $image_raw ) ) {
	$image_url = SKYYROSE_ASSETS_URI . '/images/placeholder-product.jpg';
} elseif ( 0 === strpos( $image_raw, 'http' ) ) {
	$image_url = $image_raw;
} elseif ( function_exists( 'skyyrose_product_image_uri' ) ) {
	$image_url = skyyrose_product_image_uri( $image_raw );
} else {
	$image_url = get_theme_file_uri( $image_raw );
}

// Product URL.
$product_url = ! empty( $product['url'] )
	? $product['url']
	: home_url( '/pre-order/#' . sanitize_title( $product['sku'] ) );

// Price display.
$price_display = '';
if ( ! empty( $product['price_display'] ) ) {
	$price_display = $product['price_display'];
} elseif ( ! empty( $product['price'] ) ) {
	$price_display = '$' . number_format( (float) $product['price'], 0 );
}

// Description.
$desc_trimmed = '';
if ( ! empty( $product['desc'] ) ) {
	$desc_trimmed = wp_trim_words( wp_strip_all_tags( $product['desc'] ), 12, '&hellip;' );
}

// Sizes.
$sizes_raw = $product['sizes'];
if ( is_string( $sizes_raw ) ) {
	$sizes_raw = array_filter( array_map( 'trim', explode( '|', $sizes_raw ) ) );
}
$sizes_array = is_array( $sizes_raw ) ? array_values( array_filter( $sizes_raw ) ) : array();

// Collection name.
$col_name = ! empty( $collection['name'] ) ? $collection['name'] : ucwords( str_replace( '-', ' ', $collection['slug'] ) );

// Card classes.
$card_classes = array( 'prc' );
$card_classes[] = $is_revealed ? 'prc--revealed' : 'prc--locked';
if ( ! empty( $collection['slug'] ) ) {
	$card_classes[] = 'prc--' . sanitize_html_class( $collection['slug'] );
}
?>

<article
	class="<?php echo esc_attr( implode( ' ', $card_classes ) ); ?>"
	data-reveal-at="<?php echo esc_attr( $reveal_at_iso ); ?>"
	data-product-sku="<?php echo esc_attr( $product['sku'] ); ?>"
	data-product-url="<?php echo esc_url( $product_url ); ?>"
	tabindex="0"
	role="group"
	aria-label="<?php echo esc_attr( sprintf(
		/* translators: %s: product name */
		__( 'Pre-order: %s', 'skyyrose-flagship' ),
		$product['name']
	) ); ?>"
	style="--collection-accent: <?php echo esc_attr( $collection['accent'] ); ?>; --collection-accent-rgb: <?php echo esc_attr( $collection['accent_rgb'] ); ?>;">

	<!-- Blurred product preview -->
	<div class="prc__preview">
		<img src="<?php echo esc_url( $image_url ); ?>"
			alt="<?php echo esc_attr( $product['name'] ); ?>"
			width="400" height="533"
			loading="lazy" decoding="async">

		<?php if ( ! empty( $col_name ) ) : ?>
			<span class="prc__badge"><?php echo esc_html( $col_name ); ?></span>
		<?php endif; ?>
	</div>

	<!-- Countdown overlay -->
	<?php if ( ! $is_revealed ) : ?>
	<div class="prc__countdown" aria-live="polite">
		<div class="prc__countdown-inner">
			<span class="prc__timer"
				aria-label="<?php esc_attr_e( 'Time until reveal', 'skyyrose-flagship' ); ?>">00:00:00</span>
			<p class="prc__tease"><?php esc_html_e( "Something's coming\u{2026}", 'skyyrose-flagship' ); ?></p>
		</div>
	</div>
	<?php endif; ?>

	<!-- Particle burst container -->
	<div class="prc__particles" aria-hidden="true"></div>

	<!-- Product info + CTA -->
	<div class="prc__content">

		<div class="prc__info">
			<?php if ( ! empty( $col_name ) ) : ?>
				<span class="prc__collection-tag">
					<?php echo esc_html( strtoupper( $col_name ) . ' COLLECTION' ); ?>
				</span>
			<?php endif; ?>

			<h3 class="prc__title">
				<a href="<?php echo esc_url( $product_url ); ?>">
					<?php echo esc_html( $product['name'] ); ?>
				</a>
			</h3>

			<p class="prc__price"><?php echo wp_kses_post( $price_display ); ?></p>

			<?php if ( ! empty( $desc_trimmed ) ) : ?>
				<p class="prc__desc"><?php echo esc_html( $desc_trimmed ); ?></p>
			<?php endif; ?>
		</div>

		<?php if ( ! empty( $sizes_array ) ) : ?>
		<div class="prc__sizes" role="radiogroup" aria-label="<?php esc_attr_e( 'Select size', 'skyyrose-flagship' ); ?>">
			<?php foreach ( $sizes_array as $size ) : ?>
				<button type="button" class="ipc__size-pill"
					data-size="<?php echo esc_attr( $size ); ?>"
					role="radio" aria-checked="false">
					<?php echo esc_html( $size ); ?>
				</button>
			<?php endforeach; ?>
		</div>
		<?php endif; ?>

		<a href="<?php echo esc_url( $product_url ); ?>" class="prc__cta"
			aria-label="<?php echo esc_attr( sprintf(
				/* translators: 1: product name, 2: price */
				__( 'Pre-order %1$s — %2$s', 'skyyrose-flagship' ),
				$product['name'],
				wp_strip_all_tags( $price_display )
			) ); ?>">
			<?php
			printf(
				/* translators: %s: formatted price */
				esc_html__( 'Pre-Order Now — %s', 'skyyrose-flagship' ),
				wp_kses_post( $price_display )
			);
			?>
		</a>

	</div>

</article>
