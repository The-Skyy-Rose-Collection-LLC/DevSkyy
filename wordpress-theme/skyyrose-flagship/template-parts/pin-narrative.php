<?php
/**
 * Pin-Narrative — scroll-pinned brand manifesto.
 *
 * A reusable narrative interlude: a sticky stage holds while short, collection-
 * specific canon lines cross-fade as the visitor scrolls. The palette comes from
 * the ancestor wrapper's data-collection attribute (design-tokens.css), so this
 * part never sets its own. The scroll behaviour is driven by premium-interactions.js.
 *
 * Args:
 *   - slug     (string) Collection slug for content lookup. Required for landing templates.
 *   - beats    (array)  Optional pre-resolved beats. Each item: array(
 *                           'label'  => mono micro-label,
 *                           'lead'   => headline lead (rendered plain),
 *                           'accent' => headline accent (rendered in accent colour),
 *                           'sub'    => mono caption
 *                       ). When omitted, resolved from
 *                       skyyrose_get_collection_content( slug )['pin_beats'].
 *   - products (array)  Optional pre-resolved display products (the same
 *                       list template-parts/product-grid.php renders below
 *                       this part — pass it through, do not re-query). The
 *                       first entry becomes a closing "feature" beat inside
 *                       the pinned stage so the sticky scroll narrative ends
 *                       on a real, shoppable product instead of empty stage
 *                       space.
 *
 * @package SkyyRose
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$pin_slug  = isset( $args['slug'] ) ? sanitize_key( $args['slug'] ) : '';
$pin_beats = ( isset( $args['beats'] ) && is_array( $args['beats'] ) ) ? $args['beats'] : array();

if ( empty( $pin_beats ) && '' !== $pin_slug && function_exists( 'skyyrose_get_collection_content' ) ) {
	$pin_content = skyyrose_get_collection_content( $pin_slug );
	if ( is_array( $pin_content ) && ! empty( $pin_content['pin_beats'] ) && is_array( $pin_content['pin_beats'] ) ) {
		$pin_beats = $pin_content['pin_beats'];
	}
}

// Graceful no-op when a collection has no narrative beats (e.g. teaser modes).
if ( empty( $pin_beats ) ) {
	return;
}

// Feature product — first item of the already-resolved display list.
// skyyrose_get_display_product_fields() mirrors the SOT-first image
// precedence the holo card uses, so this stays in sync with what the
// grid renders below without a second catalog/WC lookup.
$pin_products = ( isset( $args['products'] ) && is_array( $args['products'] ) ) ? $args['products'] : array();
$pin_product  = null;
if ( ! empty( $pin_products ) && function_exists( 'skyyrose_get_display_product_fields' ) ) {
	$pin_product = skyyrose_get_display_product_fields( reset( $pin_products ) );
}

// Closing-beat narrative copy — continues each collection's own pin_beats
// voice (inc/collection-content.php) instead of one generic caption, so the
// shoppable reveal reads as the next line of the story rather than a product
// card interrupting it. Kept local to this template part (not
// collection-content.php) since it only ever pairs with $pin_product.
$pin_feature_copy = array(
	'signature'    => array(
		'label'  => __( '04 — THE PROOF', 'skyyrose' ),
		'lead'   => __( 'The concrete had a shape.', 'skyyrose' ),
		'accent' => __( 'This is it.', 'skyyrose' ),
		'sub'    => __( 'Signature / Worn', 'skyyrose' ),
	),
	'black-rose'   => array(
		'label'  => __( '04 — THE ARMOR', 'skyyrose' ),
		'lead'   => __( "The stand isn't finished.", 'skyyrose' ),
		'accent' => __( 'Put it on.', 'skyyrose' ),
		'sub'    => __( 'Black Rose / Worn', 'skyyrose' ),
	),
	'love-hurts'   => array(
		'label'  => __( '04 — THE VOW', 'skyyrose' ),
		'lead'   => __( "The bloodline doesn't end in a story.", 'skyyrose' ),
		'accent' => __( 'It ends on your back.', 'skyyrose' ),
		'sub'    => __( 'Love Hurts / Worn', 'skyyrose' ),
	),
	'kids-capsule' => array(
		'label'  => __( '03 — HERS TO WEAR', 'skyyrose' ),
		'lead'   => __( "Legacy isn't a story you tell her.", 'skyyrose' ),
		'accent' => __( "It's a piece she puts on.", 'skyyrose' ),
		'sub'    => __( 'Kids Capsule / Worn', 'skyyrose' ),
	),
);
$pin_feature_text = isset( $pin_feature_copy[ $pin_slug ] ) ? $pin_feature_copy[ $pin_slug ] : array(
	'label'  => __( 'THE REVEAL', 'skyyrose' ),
	'lead'   => __( 'The story becomes', 'skyyrose' ),
	'accent' => __( 'something you wear.', 'skyyrose' ),
	'sub'    => __( 'Worn', 'skyyrose' ),
);

$pin_text_total = count( $pin_beats );
$pin_total      = $pin_text_total + ( $pin_product ? 1 : 0 );
?>
<section class="pin-track" aria-label="<?php esc_attr_e( 'Brand story', 'skyyrose' ); ?>">
	<div class="pin-stage">
		<span class="pin-corner pin-corner--tl" aria-hidden="true"></span>
		<span class="pin-corner pin-corner--tr" aria-hidden="true"></span>
		<span class="pin-corner pin-corner--bl" aria-hidden="true"></span>
		<span class="pin-corner pin-corner--br" aria-hidden="true"></span>

		<div class="pin-beats">
			<?php foreach ( $pin_beats as $pin_i => $pin_beat ) : ?>
				<article class="pin-beat<?php echo ( 0 === $pin_i ) ? ' is-active' : ''; ?>" data-beat="<?php echo esc_attr( (string) $pin_i ); ?>">
					<?php if ( ! empty( $pin_beat['label'] ) ) : ?>
						<span class="pin-beat__label"><?php echo esc_html( $pin_beat['label'] ); ?></span>
					<?php endif; ?>
					<span class="pin-beat__chrome" aria-hidden="true"></span>
					<h2 class="pin-beat__headline">
						<?php echo esc_html( isset( $pin_beat['lead'] ) ? $pin_beat['lead'] : '' ); ?>
						<?php if ( ! empty( $pin_beat['accent'] ) ) : ?>
							<span class="pin-beat__accent"><?php echo esc_html( $pin_beat['accent'] ); ?></span>
						<?php endif; ?>
					</h2>
					<?php if ( ! empty( $pin_beat['sub'] ) ) : ?>
						<span class="pin-beat__sub"><?php echo esc_html( $pin_beat['sub'] ); ?></span>
					<?php endif; ?>
				</article>
			<?php endforeach; ?>

			<?php if ( $pin_product ) : ?>
				<article class="pin-beat pin-beat--product" data-beat="<?php echo esc_attr( (string) $pin_text_total ); ?>">
					<?php if ( ! empty( $pin_feature_text['label'] ) ) : ?>
						<span class="pin-beat__label"><?php echo esc_html( $pin_feature_text['label'] ); ?></span>
					<?php endif; ?>
					<span class="pin-beat__chrome" aria-hidden="true"></span>
					<h2 class="pin-beat__headline">
						<?php echo esc_html( $pin_feature_text['lead'] ); ?>
						<?php if ( ! empty( $pin_feature_text['accent'] ) ) : ?>
							<span class="pin-beat__accent"><?php echo esc_html( $pin_feature_text['accent'] ); ?></span>
						<?php endif; ?>
					</h2>
					<?php if ( ! empty( $pin_feature_text['sub'] ) ) : ?>
						<span class="pin-beat__sub"><?php echo esc_html( $pin_feature_text['sub'] ); ?></span>
					<?php endif; ?>
					<a href="<?php echo esc_url( $pin_product['permalink'] ); ?>" class="pin-feature">
						<span class="pin-feature__media">
							<img src="<?php echo esc_url( $pin_product['image_url'] ); ?>"
								alt="<?php echo esc_attr( $pin_product['title'] ); ?>"
								loading="lazy" decoding="async" width="480" height="600" class="pin-feature__img">
						</span>
						<span class="pin-feature__meta">
							<span class="pin-feature__name"><?php echo esc_html( $pin_product['title'] ); ?></span>
							<span class="pin-feature__price"><?php echo wp_kses_post( $pin_product['price_html'] ); ?></span>
						</span>
						<span class="pin-feature__cta" aria-hidden="true"><?php esc_html_e( 'Shop This Piece', 'skyyrose' ); ?></span>
					</a>
				</article>
			<?php endif; ?>
		</div>

		<div class="pin-progress" aria-hidden="true">
			<?php for ( $pin_p = 0; $pin_p < $pin_total; $pin_p++ ) : ?>
				<span class="pin-pip<?php echo ( 0 === $pin_p ) ? ' is-active' : ''; ?>" data-pip="<?php echo esc_attr( (string) $pin_p ); ?>"></span>
			<?php endfor; ?>
		</div>
		<span class="pin-counter" aria-hidden="true">01 / <?php echo esc_html( str_pad( (string) $pin_total, 2, '0', STR_PAD_LEFT ) ); ?></span>
		<div class="pin-sr-live" role="status" aria-live="polite" aria-atomic="true"></div>
	</div>
</section>
<?php
