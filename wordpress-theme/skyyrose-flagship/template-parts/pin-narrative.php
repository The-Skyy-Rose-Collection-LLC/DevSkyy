<?php
/**
 * Scroll-Pinned Brand Narrative
 *
 * A sticky, scroll-driven sequence of brand "beats" that holds the viewport
 * while the visitor scrolls, advancing one verbatim line of founder canon at a
 * time. Shared by all 4 collection pages and all 4 landing pages.
 *
 * Data flow: pass the collection slug via $args['slug']; beats are read from
 * skyyrose_get_collection_content( $slug )['pin_beats']. Beats may also be
 * passed directly via $args['beats'] to override the catalog copy.
 *
 * Progressive enhancement: with JS off (or reduced-motion) the beats render in
 * normal document flow — every line stays readable. premium-interactions.js
 * adds the .is-pinned class to switch on the sticky stage + overlap.
 *
 * @package SkyyRose
 * @since   1.1.3
 */

defined( 'ABSPATH' ) || exit;

$slug  = isset( $args['slug'] ) ? sanitize_key( $args['slug'] ) : '';
$beats = isset( $args['beats'] ) && is_array( $args['beats'] ) ? $args['beats'] : array();

if ( empty( $beats ) && function_exists( 'skyyrose_get_collection_content' ) ) {
	$content = skyyrose_get_collection_content( $slug );
	if ( is_array( $content ) && ! empty( $content['pin_beats'] ) ) {
		$beats = $content['pin_beats'];
	}
}

// No canon, no section — never render an empty pinned stage.
if ( empty( $beats ) ) {
	return;
}

$count = count( $beats );
?>

<section class="pin-narrative" data-collection="<?php echo esc_attr( $slug ); ?>" style="--pin-count:<?php echo esc_attr( $count ); ?>" aria-label="<?php esc_attr_e( 'Brand narrative', 'skyyrose' ); ?>">
	<div class="pin-narrative__stage">
		<ol class="pin-narrative__beats">
			<?php foreach ( $beats as $i => $beat ) : ?>
				<li class="pin-beat<?php echo 0 === $i ? ' is-active' : ''; ?>" data-beat="<?php echo esc_attr( $i ); ?>">
					<span class="pin-beat__num" aria-hidden="true"><?php echo esc_html( $beat['num'] ); ?></span>
					<span class="pin-beat__label"><?php echo esc_html( $beat['label'] ); ?></span>
					<p class="pin-beat__text"><?php echo esc_html( $beat['text'] ); ?></p>
				</li>
			<?php endforeach; ?>
		</ol>
		<div class="pin-narrative__progress" aria-hidden="true">
			<?php for ( $d = 0; $d < $count; $d++ ) : ?>
				<span class="pin-narrative__dot<?php echo 0 === $d ? ' is-active' : ''; ?>"></span>
			<?php endfor; ?>
		</div>
	</div>
</section>
