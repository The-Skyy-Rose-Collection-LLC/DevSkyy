<?php
/**
 * Homepage Act V — the receipts.
 *
 * Third-party proof, scannable in three seconds, placed at the moment the
 * shopper is justifying a price. A short full-bleed band rather than a block:
 * the press outlets ARE the object (a marquee wall of names at display scale),
 * the award is a struck seal at the centre, and the numbers demote to a
 * caption rail. Replaces both the standalone press strip and the craft grid.
 *
 * The piece count is live from the catalog helper — never a literal.
 *
 * @package SkyyRose
 * @since   1.13.0
 */

defined( 'ABSPATH' ) || exit;

$hp_press  = skyyrose_home_press();
$hp_pieces = skyyrose_home_total_pieces();
$hp_award  = 'https://bestofbestreview.com/awards/the-skyy-rose-collection-best-bay-area-clothing-line-award-2024';
?>
<section class="hp-receipts" aria-labelledby="hp-receipts-h">

	<p class="hp-receipts__label" id="hp-receipts-h"><?php esc_html_e( 'As Featured In', 'skyyrose' ); ?></p>

	<div class="hp-receipts__seal">
		<svg viewBox="0 0 200 200" role="img" aria-label="<?php esc_attr_e( 'Best Bay Area Clothing Line Award 2024, Best of Best Review', 'skyyrose' ); ?>">
			<defs>
				<path id="hpSealArc" d="M 100,100 m -76,0 a 76,76 0 1,1 152,0 a 76,76 0 1,1 -152,0"></path>
			</defs>
			<circle class="hp-receipts__ring" cx="100" cy="100" r="88"></circle>
			<circle class="hp-receipts__ring" cx="100" cy="100" r="62"></circle>
			<text><textPath href="#hpSealArc" startOffset="0"><?php esc_html_e( 'BEST BAY AREA CLOTHING LINE · 2024 ·', 'skyyrose' ); ?></textPath></text>
		</svg>
		<img class="hp-mark-print"
			src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/branding/skyyrose-rose-icon.webp' ); ?>"
			alt=""
			width="96"
			height="96"
			loading="lazy"
			decoding="async">
	</div>

	<div class="hp-receipts__award">
		<strong><?php esc_html_e( 'Best Bay Area Clothing Line', 'skyyrose' ); ?></strong>
		<p>
			<a href="<?php echo esc_url( $hp_award ); ?>" target="_blank" rel="noopener noreferrer">
				<?php esc_html_e( 'Best of Best Review, 2024 ↗', 'skyyrose' ); ?>
			</a>
		</p>
	</div>

	<div class="hp-receipts__wall">
		<div class="hp-receipts__track">
			<?php
			/*
			 * Pass 0 carries the real links. Pass 1 is a visual duplicate only,
			 * so translateX(-50%) loops seamlessly — it is hidden from AT and
			 * from the tab order, and removed entirely by the reduced-motion
			 * static reflow.
			 */
			for ( $hp_pass = 0; $hp_pass < 2; $hp_pass++ ) :
				foreach ( $hp_press as $hp_item ) :
					$hp_dup   = ( 1 === $hp_pass );
					$hp_class = 'hp-receipts__name' . ( empty( $hp_item['url'] ) ? ' hp-receipts__name--flat' : '' );
					?>
					<?php if ( ! $hp_dup && ! empty( $hp_item['url'] ) ) : ?>
						<a class="hp-receipts__name"
							href="<?php echo esc_url( $hp_item['url'] ); ?>"
							target="_blank"
							rel="noopener noreferrer"><?php echo esc_html( $hp_item['name'] ); ?></a>
					<?php elseif ( $hp_dup ) : ?>
						<span class="<?php echo esc_attr( $hp_class ); ?>" data-dup aria-hidden="true"><?php echo esc_html( $hp_item['name'] ); ?></span>
					<?php else : ?>
						<span class="<?php echo esc_attr( $hp_class ); ?>"><?php echo esc_html( $hp_item['name'] ); ?></span>
					<?php endif; ?>
					<?php if ( $hp_dup ) : ?>
						<span class="hp-receipts__dot" data-dup aria-hidden="true"></span>
					<?php else : ?>
						<span class="hp-receipts__dot" aria-hidden="true"></span>
					<?php endif; ?>
					<?php
				endforeach;
			endfor;
			?>
		</div>
	</div>

	<div class="hp-receipts__rail">
		<span class="hp-receipts__stat">
			<b><?php echo esc_html( sprintf( '%02d', $hp_pieces ) ); ?></b>
			<span><?php esc_html_e( 'Pieces', 'skyyrose' ); ?></span>
		</span>
		<span class="hp-receipts__railsep" aria-hidden="true"></span>
		<span class="hp-receipts__stat">
			<b><?php echo esc_html( sprintf( '%02d', count( skyyrose_home_collection_order() ) ) ); ?></b>
			<span><?php esc_html_e( 'Collections', 'skyyrose' ); ?></span>
		</span>
		<span class="hp-receipts__railsep" aria-hidden="true"></span>
		<span class="hp-receipts__stat">
			<b>2020</b>
			<span><?php esc_html_e( 'Established', 'skyyrose' ); ?></span>
		</span>
		<span class="hp-receipts__stat hp-receipts__stat--wide">
			<span><?php esc_html_e( 'Oakland · Gender Neutral · Limited Edition', 'skyyrose' ); ?></span>
		</span>
	</div>
</section>
