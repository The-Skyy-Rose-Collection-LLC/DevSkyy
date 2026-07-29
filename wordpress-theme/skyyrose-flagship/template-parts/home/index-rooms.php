<?php
/**
 * Homepage Act III — the collection rooms.
 *
 * The single collection chooser on the page (it replaces the commercial
 * runway, the collections grid and the style atelier, which all answered the
 * same question three different ways). A corridor, not a list: one room fills
 * the viewport at a time and floods it with its own accent, and you swipe,
 * drag, shift-wheel, arrow or tap a dot to walk between worlds. The mechanism
 * is CSS scroll-snap — JS only mirrors the current room into the chrome.
 *
 * Names are the collection LOCKUP IMAGES, never type-rendered (brand canon).
 * Kids Capsule has no lockup asset in the theme, so it falls back to type in
 * Grand Hotel — the one documented imagery gap on this surface.
 *
 * Room grounds reuse the collections-world scene stills through the same
 * config helper that surface uses; piece counts come from the catalog helper.
 *
 * @package SkyyRose
 * @since   1.13.0
 */

defined( 'ABSPATH' ) || exit;

$hp_rooms = skyyrose_home_rooms();
if ( empty( $hp_rooms ) ) {
	return;
}
?>
<section class="hp-rooms" id="collections" aria-labelledby="hp-rooms-h">
	<div class="hp-rooms__top">
		<div>
			<p class="hp-rooms__eyebrow"><?php esc_html_e( 'The Collections', 'skyyrose' ); ?></p>
			<h2 id="hp-rooms-h"><?php esc_html_e( 'Four Collections. One Vision.', 'skyyrose' ); ?></h2>
		</div>
		<p class="hp-rooms__counter" aria-hidden="true">
			<b data-room-now>01</b> / <?php echo esc_html( sprintf( '%02d', count( $hp_rooms ) ) ); ?>
		</p>
	</div>

	<div class="hp-rooms__rail"
		data-rooms-rail
		tabindex="0"
		role="group"
		aria-label="<?php esc_attr_e( 'Collections — swipe, or use the left and right arrow keys', 'skyyrose' ); ?>">

		<?php foreach ( $hp_rooms as $hp_room ) : ?>
			<article class="hp-room" data-collection="<?php echo esc_attr( $hp_room['slug'] ); ?>" data-room>

				<?php if ( '' !== $hp_room['still'] ) : ?>
					<div class="hp-room__bg" aria-hidden="true">
						<img src="<?php echo esc_url( $hp_room['still'] ); ?>"
							<?php if ( '' !== $hp_room['still_set'] ) : ?>
								srcset="<?php echo esc_attr( $hp_room['still_set'] ); ?>"
								sizes="<?php echo esc_attr( $hp_room['still_sizes'] ); ?>"
							<?php endif; ?>
							alt=""
							width="1920"
							height="1080"
							loading="lazy"
							decoding="async">
					</div>
				<?php endif; ?>

				<?php
				/*
				 * The garment is the protagonist. Resolved through the SOT
				 * helper (never a hardcoded uploads path), pixel-verified
				 * against the catalog row for its SKU, and held to the right
				 * half so it never fights the copy column. Desktop only: at
				 * phone widths the room is already tight and the scene ground
				 * carries the mood on its own.
				 */
				?>
				<?php if ( '' !== $hp_room['figure'] ) : ?>
					<div class="hp-room__figure">
						<img src="<?php echo esc_url( $hp_room['figure'] ); ?>"
							<?php if ( '' !== $hp_room['figure_set'] ) : ?>
								srcset="<?php echo esc_attr( $hp_room['figure_set'] ); ?>"
								sizes="46vw"
							<?php endif; ?>
							alt="<?php echo esc_attr( $hp_room['figure_alt'] ); ?>"
							width="1024"
							height="1536"
							loading="lazy"
							decoding="async">
					</div>
				<?php endif; ?>

				<p class="hp-room__num"><?php echo esc_html( $hp_room['num'] ); ?></p>

				<span class="hp-room__name">
					<?php if ( '' !== $hp_room['lockup'] ) : ?>
						<picture>
							<source srcset="<?php echo esc_url( $hp_room['lockup'] . '.avif' ); ?>" type="image/avif">
							<source srcset="<?php echo esc_url( $hp_room['lockup'] . '.webp' ); ?>" type="image/webp">
							<img class="hp-room__lockup"
								src="<?php echo esc_url( $hp_room['lockup'] . '.png' ); ?>"
								alt=""
								loading="lazy"
								decoding="async">
						</picture>
						<span class="hp-sr"><?php echo esc_html( $hp_room['label'] ); ?></span>
					<?php else : ?>
						<?php // Kids Capsule: no lockup artwork exists yet — flagged gap. ?>
						<span class="hp-room__name-type"><?php echo esc_html( $hp_room['label'] ); ?></span>
					<?php endif; ?>
				</span>

				<p class="hp-room__poetic"><?php echo esc_html( $hp_room['poetic'] ); ?></p>
				<p class="hp-room__desc"><?php echo esc_html( $hp_room['description'] ); ?></p>

				<dl class="hp-room__facts">
					<div>
						<dt><?php esc_html_e( 'Pieces', 'skyyrose' ); ?></dt>
						<?php // data-* pair = machine-readable count contract asserted by scripts/structural_audit.py. ?>
						<dd data-collection="<?php echo esc_attr( $hp_room['slug'] ); ?>" data-piece-count="<?php echo esc_attr( (string) (int) $hp_room['count'] ); ?>">
							<?php echo esc_html( $hp_room['count'] ? (string) $hp_room['count'] : '—' ); ?>
						</dd>
					</div>
					<div>
						<dt><?php esc_html_e( 'Run', 'skyyrose' ); ?></dt>
						<dd><?php echo esc_html( $hp_room['run'] ); ?></dd>
					</div>
				</dl>

				<a class="hp-room__cta" href="<?php echo esc_url( $hp_room['href'] ); ?>">
					<?php
					/* translators: %s: collection name, e.g. Black Rose. */
					echo esc_html( sprintf( __( 'Enter %s', 'skyyrose' ), $hp_room['label'] ) );
					?>
				</a>
			</article>
		<?php endforeach; ?>
	</div>

	<nav class="hp-rooms__dots" aria-label="<?php esc_attr_e( 'Jump to a collection', 'skyyrose' ); ?>">
		<?php foreach ( $hp_rooms as $hp_index => $hp_room ) : ?>
			<button class="hp-rooms__dot"
				type="button"
				data-room-go="<?php echo esc_attr( (string) (int) $hp_index ); ?>"
				data-collection="<?php echo esc_attr( $hp_room['slug'] ); ?>"
				aria-current="<?php echo 0 === $hp_index ? 'true' : 'false'; ?>">
				<span class="hp-sr"><?php echo esc_html( $hp_room['label'] ); ?></span>
			</button>
		<?php endforeach; ?>
	</nav>

	<p class="hp-rooms__hint"><?php esc_html_e( 'Swipe to walk the corridor', 'skyyrose' ); ?></p>
</section>
