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
 *   - slug  (string) Collection slug for content lookup. Required for landing templates.
 *   - beats (array)  Optional pre-resolved beats. Each item: array(
 *                        'label'  => mono micro-label,
 *                        'lead'   => headline lead (rendered plain),
 *                        'accent' => headline accent (rendered in accent colour),
 *                        'sub'    => mono caption
 *                    ). When omitted, resolved from
 *                    skyyrose_get_collection_content( slug )['pin_beats'].
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

$pin_total = count( $pin_beats );
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
