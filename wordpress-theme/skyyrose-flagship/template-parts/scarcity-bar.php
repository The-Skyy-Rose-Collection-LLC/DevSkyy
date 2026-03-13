<?php
/**
 * Scarcity Bar — Live Edition Counter
 *
 * Shows "X of 80 claimed" for Jersey Series and other limited products.
 * Fetches live stock from the REST endpoint skyyrose/v1/stock/<sku>.
 * Falls back gracefully if WooCommerce is inactive or sku is not found.
 *
 * Usage:
 *   get_template_part( 'template-parts/scarcity-bar', null, array(
 *       'sku'          => 'br-008',
 *       'edition_size' => 80,
 *       'label'        => 'SF Inspired Jersey',
 *   ) );
 *
 * @package SkyyRose_Flagship
 * @since   5.0.0
 */

if ( ! defined( 'ABSPATH' ) ) { exit; }

$args         = $args ?? array();
$sku          = sanitize_text_field( $args['sku'] ?? '' );
$edition_size = absint( $args['edition_size'] ?? 80 );
$label        = esc_html( $args['label'] ?? '' );

if ( empty( $sku ) ) { return; }

// Server-side seed value — avoids 0 on first paint.
$product_id = function_exists( 'wc_get_product_id_by_sku' ) ? wc_get_product_id_by_sku( $sku ) : 0;
$available  = 0;
$claimed    = 0;

if ( $product_id ) {
	$meta_available = get_post_meta( $product_id, '_preorder_available', true );
	$meta_edition   = (int) get_post_meta( $product_id, '_preorder_edition_size', true );
	$edition_size   = $meta_edition > 0 ? $meta_edition : $edition_size;
	$available      = '' !== $meta_available ? (int) $meta_available : $edition_size;
	$claimed        = max( 0, $edition_size - $available );
}

$percent      = $edition_size > 0 ? min( 100, (int) round( ( $claimed / $edition_size ) * 100 ) ) : 0;
$is_critical  = $percent >= 80;
$bar_class    = 'sr-scarcity-bar' . ( $is_critical ? ' sr-scarcity-bar--critical' : '' );
$bar_id       = 'sr-scarcity-' . sanitize_html_class( $sku );
$rest_url     = esc_url( rest_url( 'skyyrose/v1/stock/' . $sku ) );
?>
<div id="<?php echo esc_attr( $bar_id ); ?>" class="<?php echo esc_attr( $bar_class ); ?>" aria-label="<?php esc_attr_e( 'Availability', 'skyyrose-flagship' ); ?>">
	<?php if ( $label ) : ?>
	<span class="sr-scarcity-bar__label"><?php echo $label; ?></span>
	<?php endif; ?>

	<div class="sr-scarcity-bar__counter">
		<span class="sr-scarcity-bar__claimed"
			data-claimed="<?php echo esc_attr( $claimed ); ?>"><?php echo esc_html( $claimed ); ?></span>
		<span class="sr-scarcity-bar__of"><?php esc_html_e( 'of', 'skyyrose-flagship' ); ?></span>
		<span class="sr-scarcity-bar__total"><?php echo esc_html( $edition_size ); ?></span>
		<span class="sr-scarcity-bar__unit"><?php esc_html_e( 'claimed', 'skyyrose-flagship' ); ?></span>
		<?php if ( $is_critical ) : ?>
		<span class="sr-scarcity-bar__alert"><?php esc_html_e( '— Almost Gone', 'skyyrose-flagship' ); ?></span>
		<?php endif; ?>
	</div>

	<div class="sr-scarcity-bar__track" aria-hidden="true">
		<div class="sr-scarcity-bar__fill"
			data-percent="<?php echo esc_attr( $percent ); ?>"
			style="width: <?php echo esc_attr( $percent ); ?>%;"></div>
	</div>
</div>

<script>
(function () {
	'use strict';
	var bar       = document.getElementById('<?php echo esc_js( $bar_id ); ?>');
	var claimedEl = bar ? bar.querySelector('[data-claimed]') : null;
	var fill      = bar ? bar.querySelector('.sr-scarcity-bar__fill') : null;

	if (!bar || !claimedEl || !fill) return;

	function applyData(data) {
		var claimed  = data.claimed || 0;
		var edition  = data.edition_size || <?php echo esc_js( $edition_size ); ?>;
		var pct      = Math.min(100, Math.round((claimed / edition) * 100));
		claimedEl.textContent = claimed;
		fill.style.width = pct + '%';
		if (pct >= 80) bar.classList.add('sr-scarcity-bar--critical');
		if (data.status === 'sold_out') {
			bar.classList.add('sr-scarcity-bar--sold-out');
		}
	}

	// Fetch live stock count from REST endpoint.
	fetch('<?php echo esc_js( $rest_url ); ?>', { cache: 'no-cache' })
		.then(function (r) { return r.ok ? r.json() : null; })
		.then(function (d) { if (d) applyData(d); })
		.catch(function () {}); // Graceful degradation — server-side values remain.

	// Refresh every 90 seconds while page is visible.
	var iv = setInterval(function () {
		if (document.hidden) return;
		fetch('<?php echo esc_js( $rest_url ); ?>', { cache: 'no-cache' })
			.then(function (r) { return r.ok ? r.json() : null; })
			.then(function (d) { if (d) applyData(d); })
			.catch(function () {});
	}, 90000);

	window.addEventListener('pagehide', function () { clearInterval(iv); });
}());
</script>
