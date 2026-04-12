<?php
/**
 * Landing Page — Product Grid (Thin Adapter)
 *
 * Thin adapter that translates the landing-page API to the unified
 * product-grid template part. The new grid uses holo cards end-to-end,
 * replacing the former lp-product-card layout with the same visual
 * language used on the homepage, collection pages, and shop archive.
 *
 * Expected $args:
 *   'heading'     => string   Section heading ("The Collection")
 *   'subheading'  => string   Subtext below heading
 *   'skus'        => string[] List of SKU strings to display
 *   'collection'  => string   Collection slug for palette (optional, inferred from first SKU)
 *   'wear_count'  => int      Legacy param for cost-per-wear (no longer rendered on the card itself)
 *   'remaining'   => array    Legacy scarcity map (no longer rendered; holo reads WC stock)
 *
 * @package SkyyRose_Flagship
 * @since   6.5.0
 */

defined( 'ABSPATH' ) || exit;

$skus = isset( $args['skus'] ) ? (array) $args['skus'] : array();
if ( empty( $skus ) ) {
	return;
}

// Infer collection slug from the first SKU if not provided — drives holo palette.
$collection = $args['collection'] ?? '';
if ( empty( $collection ) && function_exists( 'skyyrose_get_product' ) ) {
	$first = skyyrose_get_product( $skus[0] );
	if ( $first && ! empty( $first['collection'] ) ) {
		$collection = $first['collection'];
	}
}

// Permalink override:
// Kids Capsule is pre-order-only, so all its cards route to /pre-order/.
// Every other collection lets the holo card use its own URL resolution
// (WC permalink for live products, catalog fallback for drafts). Sending
// Signature / Black Rose / Love Hurts shoppers to a pre-order funnel from
// a landing page is a conversion regression — let the card link to the
// real PDP instead.
$permalink_override = ( 'kids-capsule' === $collection ) ? home_url( '/pre-order/' ) : '';

get_template_part(
	'template-parts/product-grid',
	null,
	array(
		'skus'          => $skus,
		'collection'    => $collection,
		'heading'       => $args['heading'] ?? __( 'The Collection', 'skyyrose' ),
		'subheading'    => $args['subheading'] ?? '',
		'section_id'    => 'products',
		'section_class' => 'lp-products',
		'reveal_class'  => 'lp-rv',
		'permalink'     => $permalink_override,
	)
);
