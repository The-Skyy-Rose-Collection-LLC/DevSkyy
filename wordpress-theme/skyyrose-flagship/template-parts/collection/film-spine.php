<?php
/**
 * Collection Film Spine — scroll-scrubbed shoppable stage (Variant C).
 *
 * Founder-picked base layout 2026-07-29 ("Shop the Film / scroll-world
 * spine", docs/brand/design-mockups/prototype-collection-base-layout.NOTES.md).
 * Evolves the passive ambient film loop into: a tall scroll track with a
 * sticky 100vh stage, an accent progress bar, narrative beat captions that
 * swap by scroll progress, and shoppable hotspots linking to real products.
 *
 * Scrub mechanic is transform-only — the video's currentTime is NEVER
 * seeked (decode jank). The silent autoplay-near-view loop, poster-first
 * markup, and WCAG 2.2.2 pause toggle are unchanged from the previous
 * col-film section; collection-pages.js drives them by the same classes.
 * collection-motion.js scrubs the stage; collection-motion.css lays it out
 * and provides the reduced-motion static fallback (non-sticky ambient
 * section, beats stacked, hotspots as a static row).
 *
 * Beat copy = the collection's pin_beats canon (inc/collection-content.php)
 * — consumed here INSTEAD of the pin-narrative part, which page.php no
 * longer includes (double-render guard). Hotspot products are the first
 * 1-3 entries of the already-resolved $products list — deterministic, no
 * hardcoded SKUs; kids-capsule routes every hotspot to its pre-order URL.
 *
 * @package SkyyRose
 * @since   1.13.0
 *
 * @param array $args {
 *     @type string $slug      Collection slug.
 *     @type array  $content   Collection content config (pin_beats source).
 *     @type array  $products  Resolved display products (hotspot source).
 *     @type string $permalink Optional permalink override (kids pre-order).
 * }
 */

defined( 'ABSPATH' ) || exit;

$slug     = isset( $args['slug'] ) ? sanitize_key( $args['slug'] ) : '';
$c        = isset( $args['content'] ) && is_array( $args['content'] ) ? $args['content'] : array();
$products = isset( $args['products'] ) && is_array( $args['products'] ) ? $args['products'] : array();
$link_fix = isset( $args['permalink'] ) ? (string) $args['permalink'] : '';

// Flight films resolve by Media Library attachment ID, not a hardcoded
// path: a re-upload/replace, a dated-folder move, or a relocated uploads
// dir can't silently serve a stale file, and wp_get_attachment_url() passes
// through CDN/offload filters. Fail-closed — a missing or deleted attachment
// skips the whole spine (never a broken embed). Silent by design (founder
// audio rule). Map is filterable so a future replace can repoint without a
// template edit. (Moved verbatim from collection/page.php, WS-C.)
$film_ids   = apply_filters(
	'skyyrose_collection_film_ids',
	array(
		'signature'    => array(
			'video'  => 10329,
			'poster' => 10328,
		),
		'black-rose'   => array(
			'video'  => 10323,
			'poster' => 10322,
		),
		'love-hurts'   => array(
			'video'  => 10327,
			'poster' => 10326,
		),
		'kids-capsule' => array(
			'video'  => 10325,
			'poster' => 10324,
		),
	),
	$slug
);
$film       = $film_ids[ $slug ] ?? null;
$film_url   = $film ? wp_get_attachment_url( $film['video'] ) : '';
$poster_url = $film ? wp_get_attachment_url( $film['poster'] ) : '';
$film_path  = $film ? get_attached_file( $film['video'] ) : '';

if ( ! ( $film_url && $poster_url && $film_path && file_exists( $film_path ) ) ) {
	return;
}

// Narrative beats — the collection's own pin_beats canon. Cap at 3 for the
// stage (BR/LH/SIG ship 3, KC ships 2 — count drives the scrub segments).
$beats = isset( $c['pin_beats'] ) && is_array( $c['pin_beats'] ) ? array_slice( $c['pin_beats'], 0, 3 ) : array();

// Shoppable hotspots — first 1-3 display products, same SOT-first field
// resolution the pin-narrative feature beat used. Deterministic order from
// the front of the resolved list; no SKU literals.
$hotspots = array();
if ( function_exists( 'skyyrose_get_display_product_fields' ) ) {
	foreach ( array_slice( $products, 0, 3 ) as $spot_item ) {
		$fields = skyyrose_get_display_product_fields( $spot_item );
		if ( '' === $fields['title'] ) {
			continue;
		}
		if ( '' !== $link_fix ) {
			$fields['permalink'] = $link_fix; // Kids Capsule: all product links route to pre-order.
		}
		$hotspots[] = $fields;
	}
}
?>

<section class="col-film col-film--spine" aria-label="<?php esc_attr_e( 'Collection film', 'skyyrose' ); ?>">
	<div class="col-film__scrolltrack" data-film-scrub>
		<div class="col-film__stage">
			<div class="col-film__progress" aria-hidden="true"></div>

			<div class="col-film__media">
				<?php
				// No autoplay + preload="none": reduced-motion users never trigger
				// a video fetch. collection-pages.js calls .play() (which starts the
				// load) only when motion is allowed AND the film scrolls near view,
				// and reveals the pause/play toggle then — WCAG 2.2.2 needs a stop
				// mechanism for auto motion over 5s. aria-hidden on the video: it's a
				// decorative silent loop with no accessible name; the toggle is a
				// sibling (not a descendant), so it stays reachable.
				?>
				<video class="col-film__video" muted loop playsinline preload="none" aria-hidden="true"
					poster="<?php echo esc_url( $poster_url ); ?>"
					width="720" height="1280">
					<source src="<?php echo esc_url( $film_url ); ?>" type="video/mp4">
				</video>
				<img class="col-film__poster" src="<?php echo esc_url( $poster_url ); ?>"
					alt="" aria-hidden="true" loading="lazy" decoding="async" width="720" height="1280">
			</div>

			<?php if ( ! empty( $beats ) ) : ?>
				<?php
				// Beats cross-fade via .is-on (collection-motion.js scrub); first
				// beat ships active server-side so no-JS/pre-JS paint isn't empty.
				// Not aria-hidden: opacity-hidden copy stays readable in sequence
				// for screen readers — the full narrative, same as pin-narrative.
				?>
				<div class="col-film__beats">
					<?php foreach ( $beats as $beat_i => $beat ) : ?>
						<div class="col-film__beat<?php echo 0 === $beat_i ? ' is-on' : ''; ?>" data-film-beat="<?php echo esc_attr( (string) $beat_i ); ?>">
							<?php if ( ! empty( $beat['label'] ) ) : ?>
								<span class="col-film__beat-label"><?php echo esc_html( $beat['label'] ); ?></span>
							<?php endif; ?>
							<h2 class="col-film__beat-title">
								<?php echo esc_html( isset( $beat['lead'] ) ? $beat['lead'] : '' ); ?>
								<?php if ( ! empty( $beat['accent'] ) ) : ?>
									<span class="col-film__beat-accent"><?php echo esc_html( $beat['accent'] ); ?></span>
								<?php endif; ?>
							</h2>
							<?php if ( ! empty( $beat['sub'] ) ) : ?>
								<span class="col-film__beat-sub"><?php echo esc_html( $beat['sub'] ); ?></span>
							<?php endif; ?>
						</div>
					<?php endforeach; ?>
				</div>
			<?php endif; ?>

			<?php if ( ! empty( $hotspots ) ) : ?>
				<?php
				// Real focusable links (never aria-hidden): name + price + dot.
				// Absolute positions (--1/--2/--3, collection-motion.css) avoid the
				// pause toggle's bottom-right corner; <768px and reduced-motion
				// reflow them into a static row under the media.
				?>
				<div class="col-film__hotspots">
					<?php foreach ( $hotspots as $spot_i => $spot ) : ?>
						<a class="col-film__hotspot col-film__hotspot--<?php echo esc_attr( (string) ( $spot_i + 1 ) ); ?>"
							href="<?php echo esc_url( $spot['permalink'] ); ?>">
							<span class="col-film__hotspot-dot" aria-hidden="true"></span>
							<span class="col-film__hotspot-name"><?php echo esc_html( $spot['title'] ); ?></span>
							<span class="col-film__hotspot-price"><?php echo wp_kses_post( $spot['price_html'] ); ?></span>
						</a>
					<?php endforeach; ?>
				</div>
			<?php endif; ?>

			<button type="button" class="col-film__toggle" aria-label="<?php esc_attr_e( 'Pause background video', 'skyyrose' ); ?>" hidden></button>
		</div>
	</div>
</section>
