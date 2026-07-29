<?php
/**
 * Homepage Act II — the ticker.
 *
 * Counter-scrolling shear band: two tiers moving against each other, split by
 * a hairline. The top tier is dominant in SIZE but not in INK (outline-only
 * Cinzel over a 7%-alpha fill), so it has scale without weight. The lower tier
 * carries the mantra in Pinyon Script plus the house attribute strings.
 *
 * Decorative by construction — every string here is repeated in accessible
 * form elsewhere on the page, so the whole band is aria-hidden and the loop
 * clones that homepage-v3.js appends never reach the accessibility tree.
 *
 * @package SkyyRose
 * @since   1.13.0
 */

defined( 'ABSPATH' ) || exit;

$hp_ticker = skyyrose_home_ticker();
?>
<div class="hp-ticker" aria-hidden="true">
	<div class="hp-ticker__row">
		<div class="hp-ticker__track hp-ticker__track--left">
			<?php foreach ( $hp_ticker['names'] as $hp_name ) : ?>
				<span class="hp-ticker__name"><?php echo esc_html( $hp_name ); ?></span>
			<?php endforeach; ?>
		</div>
	</div>

	<div class="hp-ticker__rule"></div>

	<div class="hp-ticker__row">
		<div class="hp-ticker__track hp-ticker__track--right">
			<?php foreach ( $hp_ticker['lower'] as $hp_item ) : ?>
				<span class="hp-ticker__<?php echo esc_attr( $hp_item['kind'] ); ?>"><?php echo esc_html( $hp_item['text'] ); ?></span>
			<?php endforeach; ?>
		</div>
	</div>
</div>
