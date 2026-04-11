<?php
/**
 * Template Part: Unified Product Grid
 *
 * Canonical product-grid wrapper used across every surface that renders
 * a set of product cards (homepage featured, collection pages, landing
 * pages, shop archive). Handles the shared concerns so each caller does
 * not duplicate this loop:
 *
 *   - Section wrapper with semantic heading + aria-labelledby
 *   - Scroll reveal class (collection-/page-appropriate)
 *   - Palette data-attribute (drives holo --accent variables)
 *   - Staggered entrance (stagger-grid + index-based delay)
 *   - Mixed input: pre-resolved products, collection slug, or SKU list
 *   - Kids-capsule permalink override routes to /pre-order/
 *   - Graceful empty state (emits nothing if no products)
 *
 * Usage:
 *   // From a collection page (data already resolved)
 *   get_template_part( 'template-parts/product-grid', null, array(
 *       'products'      => $products,
 *       'collection'    => $slug,
 *       'heading'       => __( 'The Collection', 'skyyrose-flagship' ),
 *       'subheading'    => $subheading_text,
 *       'section_class' => 'col-products',
 *       'section_id'    => 'shop',
 *   ) );
 *
 *   // From the homepage (featured cross-collection set)
 *   get_template_part( 'template-parts/product-grid', null, array(
 *       'featured'      => true,
 *       'limit'         => 8,
 *       'heading'       => __( 'Featured', 'skyyrose-flagship' ),
 *       'subheading'    => __( 'Shop the staples', 'skyyrose-flagship' ),
 *       'section_class' => 'fp-featured',
 *       'section_id'    => 'featured',
 *   ) );
 *
 *   // From a landing page (hand-picked SKU list)
 *   get_template_part( 'template-parts/product-grid', null, array(
 *       'skus'          => array( 'br-004', 'br-005', 'br-006' ),
 *       'collection'    => 'black-rose',
 *       'heading'       => $heading,
 *       'subheading'    => $subheading,
 *       'section_class' => 'lp-products',
 *       'reveal_class'  => 'lp-rv',
 *   ) );
 *
 *   // From any surface with a pre-resolved product list (custom query)
 *   get_template_part( 'template-parts/product-grid', null, array(
 *       'products' => $my_curated_list, // empty array renders nothing (no fallback)
 *       'heading'  => __( 'Staff Picks', 'skyyrose-flagship' ),
 *   ) );
 *
 * @param array $args {
 *     Data source — the wrapper checks these in order and uses the first
 *     non-empty source. `products` is the null-sentinel path: passing it
 *     explicitly (including as an empty array) always short-circuits the
 *     cascade so a caller-provided empty list renders an empty grid
 *     instead of silently falling through to featured/collection/skus.
 *
 *     @type array    $products       1. Pre-resolved list (WC_Product | static card).
 *                                    Explicitly passing an empty array is honored
 *                                    (renders nothing — no cascade to other sources).
 *     @type bool     $featured       2. If true, use skyyrose_get_featured_display_products().
 *     @type string   $collection     3. Collection slug → skyyrose_get_collection_display_products().
 *     @type string[] $skus           4. SKU list resolved through the shared catalog resolver.
 *     @type int      $limit          Cap on items rendered. 0 (default) = no cap.
 *                                    The featured path pre-caps inside its own helper;
 *                                    collection/skus/products paths rely on the late-stage
 *                                    slice below. The late-stage slice is a no-op for
 *                                    already-capped results.
 *
 *     Display:
 *     @type string   $heading        Section heading text. Omit to hide header.
 *     @type string   $subheading     Section subheading text.
 *     @type string   $section_id     HTML id for the <section> (default: 'shop').
 *     @type string   $section_class  Extra class(es) added to the <section>. May be
 *                                    space-separated; the first token is used for
 *                                    legacy `{token}__header` alias generation.
 *     @type string   $reveal_class   Scroll reveal class (default: 'rv-clip-up').
 *     @type string   $permalink      Override card permalinks (e.g. /pre-order/ for
 *                                    kids-capsule). Passed through to the holo card,
 *                                    which honors real URLs over its own resolution.
 *     @type string   $empty_message  Text shown if no products resolve. Empty = render nothing.
 * }
 *
 * @package SkyyRose_Flagship
 * @since   6.5.0
 */

defined( 'ABSPATH' ) || exit;

// ---------------------------------------------------------------------------
// Parse args with sane defaults.
// ---------------------------------------------------------------------------
$defaults = array(
	'products'      => null,
	'featured'      => false,
	'collection'    => '',
	'skus'          => array(),
	'limit'         => 0,
	'heading'       => '',
	'subheading'    => '',
	'section_id'    => 'shop',
	'section_class' => '',
	'reveal_class'  => 'rv-clip-up',
	'permalink'     => '',
	'empty_message' => '',
);
$args = wp_parse_args( $args ?? array(), $defaults );

// ---------------------------------------------------------------------------
// Resolve the product list from whichever data source was provided.
//
// `products` uses a `null` sentinel so callers can explicitly pass an
// empty array without silently cascading to a different data source —
// a collection with zero visible products should render nothing, not
// fall through to featured/collection/skus.
// ---------------------------------------------------------------------------
$products = array();
$debug    = defined( 'WP_DEBUG' ) && WP_DEBUG;

if ( null !== $args['products'] ) {
	// 1. Pre-resolved products — caller provided explicit data (possibly empty).
	$products = is_array( $args['products'] ) ? $args['products'] : array();
} elseif ( ! empty( $args['featured'] ) ) {
	// 2. Featured cross-collection set.
	if ( function_exists( 'skyyrose_get_featured_display_products' ) ) {
		$products = skyyrose_get_featured_display_products( (int) $args['limit'] );
	} elseif ( $debug ) {
		trigger_error(
			'product-grid: skyyrose_get_featured_display_products() missing — inc/product-catalog.php not loaded.',
			E_USER_WARNING
		);
	}
} elseif ( ! empty( $args['collection'] ) ) {
	// 3. Full collection by slug.
	if ( function_exists( 'skyyrose_get_collection_display_products' ) ) {
		$products = skyyrose_get_collection_display_products( $args['collection'] );
	} elseif ( $debug ) {
		trigger_error(
			'product-grid: skyyrose_get_collection_display_products() missing — inc/product-catalog.php not loaded.',
			E_USER_WARNING
		);
	}
} elseif ( ! empty( $args['skus'] ) ) {
	// 4. Hand-picked SKU list — resolve through the shared catalog resolver
	//    so visibility rules and WC-first logic stay centralised.
	if ( function_exists( 'skyyrose_get_product' ) && function_exists( '_skyyrose_resolve_display_products' ) ) {
		$entries        = array();
		$requested      = count( (array) $args['skus'] );
		foreach ( (array) $args['skus'] as $sku ) {
			$cat = skyyrose_get_product( $sku );
			if ( $cat ) {
				$entries[] = $cat;
			} elseif ( $debug ) {
				trigger_error(
					sprintf(
						'product-grid: SKU %s not in catalog — dropped from grid.',
						esc_html( (string) $sku )
					),
					E_USER_NOTICE
				);
			}
		}
		$products = _skyyrose_resolve_display_products( $entries );
	} elseif ( $debug ) {
		trigger_error(
			'product-grid: catalog helpers missing — inc/product-catalog.php not loaded.',
			E_USER_WARNING
		);
	}
}

// Apply limit (late-stage cap — covers the paths that do not pre-cap).
// 0 (or less) = no cap. Lets callers pass through "render everything".
$limit_cap = (int) $args['limit'];
if ( $limit_cap > 0 && count( $products ) > $limit_cap ) {
	$products = array_slice( $products, 0, $limit_cap );
}

// Empty state — bail silently unless caller provided empty_message.
if ( empty( $products ) ) {
	if ( ! empty( $args['empty_message'] ) ) {
		printf( '<p class="product-grid__empty">%s</p>', esc_html( $args['empty_message'] ) );
	}
	return;
}

// ---------------------------------------------------------------------------
// Build wrapper classes + accessibility ids.
//
// `heading_id` is only populated when an actual <h2> will render, so we
// never emit aria-labelledby pointing at a nonexistent element — WCAG.
// section_class may contain space-separated tokens; we split, sanitize
// each, and rejoin so multi-class values survive sanitize_html_class().
// ---------------------------------------------------------------------------
$has_heading  = ! empty( $args['heading'] );
$has_subhead  = ! empty( $args['subheading'] );
$has_header   = $has_heading || $has_subhead;
// sanitize_title() yields a valid HTML5 id slug (lowercase, hyphen-separated);
// sanitize_html_class() was semantically for class tokens and would leak
// uppercase/underscored values into the id attribute.
$section_id   = $args['section_id'] ? sanitize_title( (string) $args['section_id'] ) : 'shop';
$heading_id   = $has_heading ? $section_id . '-heading' : '';

// Multi-token class handling — each whitespace-separated token is sanitized
// independently so spaces are preserved. sanitize_html_class() strips any
// character that isn't [a-zA-Z0-9_-], so splitting is required for any
// caller passing more than one class.
$section_cls = array( 'product-grid-section' );
$first_slug  = '';
if ( ! empty( $args['section_class'] ) ) {
	$tokens = preg_split( '/\s+/', trim( (string) $args['section_class'] ) );
	foreach ( (array) $tokens as $tok ) {
		$clean = sanitize_html_class( $tok );
		if ( '' !== $clean ) {
			$section_cls[] = $clean;
			if ( '' === $first_slug ) {
				$first_slug = $clean; // Remember the first token for header alias.
			}
		}
	}
}
if ( ! empty( $args['reveal_class'] ) ) {
	$reveal_tokens = preg_split( '/\s+/', trim( (string) $args['reveal_class'] ) );
	foreach ( (array) $reveal_tokens as $tok ) {
		$clean = sanitize_html_class( $tok );
		if ( '' !== $clean ) {
			$section_cls[] = $clean;
		}
	}
}

// Legacy header class alias for pre-6.5 CSS (e.g. .col-products__header,
// .lp-products__header). Keeps existing typography styles applying cleanly
// to sections that predate the unified grid-section base class.
$header_cls = array( 'product-grid-section__header' );
if ( $first_slug ) {
	$header_cls[] = $first_slug . '__header';
}
?>

<section
	id="<?php echo esc_attr( $section_id ); ?>"
	class="<?php echo esc_attr( implode( ' ', $section_cls ) ); ?>"
	<?php if ( $heading_id ) : ?>
	aria-labelledby="<?php echo esc_attr( $heading_id ); ?>"
	<?php else : ?>
	aria-label="<?php esc_attr_e( 'Product grid', 'skyyrose-flagship' ); ?>"
	<?php endif; ?>
>
	<?php if ( $has_header ) : ?>
		<div class="<?php echo esc_attr( implode( ' ', $header_cls ) ); ?>">
			<?php if ( $has_heading ) : ?>
				<h2 id="<?php echo esc_attr( $heading_id ); ?>" class="product-grid-section__heading">
					<?php echo esc_html( $args['heading'] ); ?>
				</h2>
			<?php endif; ?>
			<?php if ( $has_subhead ) : ?>
				<p class="product-grid-section__subheading">
					<?php echo esc_html( $args['subheading'] ); ?>
				</p>
			<?php endif; ?>
		</div>
	<?php endif; ?>

	<div class="product-grid stagger-grid"
		<?php if ( ! empty( $args['collection'] ) ) : ?>
		data-collection="<?php echo esc_attr( $args['collection'] ); ?>"
		<?php endif; ?>
	>
		<div class="product-grid__items" role="list">
			<?php
			$index            = 0;
			$permalink_override = ! empty( $args['permalink'] ) ? (string) $args['permalink'] : '';
			foreach ( $products as $item ) :
				// Build card args — this template part delegates rendering to the holo card.
				if ( $item instanceof WC_Product ) {
					$card_args = array(
						'product'    => $item,
						'collection' => $args['collection'] ?: '',
						'index'      => $index,
					);
					if ( '' !== $permalink_override ) {
						$card_args['permalink'] = $permalink_override;
					}
				} else {
					$card_args = array(
						'product'    => null,
						'title'      => $item['title'] ?? '',
						'price'      => $item['price'] ?? '',
						'image_url'  => $item['image_url'] ?? '',
						'image_back' => $item['image_back'] ?? '',
						'badge_text' => $item['badge_text'] ?? '',
						'collection' => $args['collection'] ?: ( $item['collection'] ?? '' ),
						'permalink'  => '' !== $permalink_override ? $permalink_override : ( $item['permalink'] ?? '#' ),
						'sku'        => $item['sku'] ?? '',
						'index'      => $index,
					);
				}
				get_template_part( 'template-parts/product-card-holo', null, $card_args );
				$index++;
			endforeach;
			?>
		</div>
	</div>
</section>
