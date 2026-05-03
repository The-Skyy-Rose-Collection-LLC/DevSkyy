<?php
/**
 * Visual Similarity Shortcode — [skyyrose_visual_similar]
 *
 * Renders a "Customers also viewed" widget driven by CLIP image embeddings.
 *
 * Server-side: pre-renders the cards for every candidate SKU (hidden by
 * default). Client-side: visual-similarity.js loads the embeddings JSON,
 * computes cosine similarity to the source SKU, and reveals the top N in
 * ranked order.
 *
 * If JS fails or embeddings JSON is missing, the server-rendered fallback
 * (first `count` cards from the same collection) stays visible. No layout
 * collapse, no broken page.
 *
 * Usage:
 *   [skyyrose_visual_similar]                                 — uses current product
 *   [skyyrose_visual_similar sku="br-001"]                    — explicit SKU
 *   [skyyrose_visual_similar sku="br-001" count="4"]
 *   [skyyrose_visual_similar sku="br-001" same_collection="1"]
 *
 * @package SkyyRose
 * @since   1.1.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Register similarity scripts and styles. Conditionally enqueued by the
 * shortcode renderer below.
 *
 * @since 1.1.0
 * @return void
 */
function skyyrose_register_visual_similarity_assets() {
	wp_register_style(
		'skyyrose-visual-similarity',
		SKYYROSE_ASSETS_URI . '/css/components/visual-similarity.css',
		array(),
		SKYYROSE_VERSION
	);

	wp_register_script(
		'skyyrose-visual-similarity',
		SKYYROSE_ASSETS_URI . '/js/components/visual-similarity.js',
		array(),
		SKYYROSE_VERSION,
		array(
			'in_footer' => true,
			'strategy'  => 'defer',
		)
	);

	add_filter( 'script_loader_tag', 'skyyrose_visual_similarity_module_tag', 10, 3 );
}
add_action( 'init', 'skyyrose_register_visual_similarity_assets' );

/**
 * Add type="module" to the visual-similarity script.
 *
 * @param string $tag    Generated <script> HTML.
 * @param string $handle Script handle.
 * @param string $src    Script URL.
 * @return string Filtered tag.
 */
function skyyrose_visual_similarity_module_tag( $tag, $handle, $src ) {
	if ( 'skyyrose-visual-similarity' !== $handle ) {
		return $tag;
	}
	// Script is enqueued via wp_enqueue_script() — this filter only adds type="module".
	return sprintf(
		'<script type="module" src="%s" defer></script>' . "\n", // phpcs:ignore WordPress.WP.EnqueuedResources.NonEnqueuedScript
		esc_url( $src )
	);
}

/**
 * Determine the source SKU. Explicit attribute wins; otherwise infer from
 * current single-product context if WooCommerce.
 *
 * @param array $atts Shortcode attributes (already merged with defaults).
 * @return string|null
 */
function skyyrose_visual_similarity_resolve_sku( $atts ) {
	if ( ! empty( $atts['sku'] ) ) {
		return sanitize_key( $atts['sku'] );
	}
	if ( function_exists( 'is_product' ) && is_product() ) {
		global $product;
		if ( $product instanceof WC_Product ) {
			$sku = $product->get_sku();
			if ( $sku ) {
				return sanitize_key( $sku );
			}
		}
	}
	return null;
}

/**
 * Render a single candidate card (hidden by default). The browser unhides
 * the top N matches.
 *
 * @param array $product Catalog product array (from skyyrose_get_product()).
 * @return string
 */
function skyyrose_visual_similarity_render_card( $product ) {
	$sku         = $product['sku'] ?? '';
	$name        = $product['name'] ?? '';
	$collection  = $product['collection'] ?? '';
	$image_uri   = function_exists( 'skyyrose_product_image_uri' ) && ! empty( $product['image'] )
		? skyyrose_product_image_uri( $product['image'] )
		: '';
	$product_url = function_exists( 'skyyrose_product_url' ) ? skyyrose_product_url( $sku ) : '';
	$price       = function_exists( 'skyyrose_format_price' ) ? skyyrose_format_price( $product ) : '';

	ob_start();
	?>
	<a
		class="sr-similar__card"
		href="<?php echo esc_url( $product_url ); ?>"
		data-similar-sku="<?php echo esc_attr( $sku ); ?>"
		data-similar-collection="<?php echo esc_attr( $collection ); ?>"
		hidden
	>
		<figure class="sr-similar__cardImg">
			<?php if ( $image_uri ) : ?>
				<img
					src="<?php echo esc_url( $image_uri ); ?>"
					alt="<?php echo esc_attr( $name ); ?>"
					loading="lazy"
					decoding="async"
				/>
			<?php endif; ?>
		</figure>
		<div class="sr-similar__cardBody">
			<span class="sr-similar__cardCollection"><?php echo esc_html( $collection ); ?></span>
			<span class="sr-similar__cardName"><?php echo esc_html( $name ); ?></span>
			<span class="sr-similar__cardPrice"><?php echo esc_html( $price ); ?></span>
		</div>
	</a>
	<?php
	return (string) ob_get_clean();
}

/**
 * Render the visual similarity widget.
 *
 * @since 1.1.0
 * @param array $atts Shortcode attributes.
 * @return string
 */
function skyyrose_visual_similarity_shortcode( $atts ) {
	$atts = shortcode_atts(
		array(
			'sku'             => '',
			'count'           => '3',
			'heading'         => __( 'You may also love', 'skyyrose' ),
			'same_collection' => '0',
		),
		$atts,
		'skyyrose_visual_similar'
	);

	$source_sku = skyyrose_visual_similarity_resolve_sku( $atts );
	if ( ! $source_sku ) {
		return '';
	}

	if ( ! function_exists( 'skyyrose_get_product_catalog' ) ) {
		return '';
	}

	$catalog = skyyrose_get_product_catalog();
	if ( empty( $catalog ) || ! isset( $catalog[ $source_sku ] ) ) {
		return '';
	}

	wp_enqueue_style( 'skyyrose-visual-similarity' );
	wp_enqueue_script( 'skyyrose-visual-similarity' );

	$count = max( 1, absint( $atts['count'] ) );

	// Cache-bust by theme version so deploys invalidate the browser cache cleanly.
	$embeddings_url = add_query_arg(
		array( 'v' => SKYYROSE_VERSION ),
		SKYYROSE_URI . '/data/product-embeddings.json'
	);

	// Build candidate set: every published SKU except the source.
	// Server-side fallback: prioritize same-collection candidates so JS-disabled
	// users still see relevant items even before ranking applies.
	$source     = $catalog[ $source_sku ];
	$candidates = array();
	$same_col   = array();
	$other_col  = array();
	foreach ( $catalog as $sku => $product ) {
		if ( $sku === $source_sku ) {
			continue;
		}
		if ( ( $product['published'] ?? '0' ) !== '1' ) {
			continue;
		}
		if ( ( $product['collection'] ?? '' ) === ( $source['collection'] ?? '' ) ) {
			$same_col[] = $product;
		} else {
			$other_col[] = $product;
		}
	}
	// Reveal first `count` same-collection cards as fallback. JS will hide and
	// re-pick by ranking.
	$candidates = array_merge( $same_col, $other_col );

	ob_start();
	?>
	<section
		class="sr-similar"
		data-skyyrose-similar
		data-similar-source="<?php echo esc_attr( $source_sku ); ?>"
		data-similar-src="<?php echo esc_url( $embeddings_url ); ?>"
		data-similar-count="<?php echo esc_attr( (string) $count ); ?>"
		data-similar-same-collection="<?php echo esc_attr( '1' === $atts['same_collection'] ? '1' : '0' ); ?>"
	>
		<h3 class="sr-similar__heading"><?php echo esc_html( $atts['heading'] ); ?></h3>
		<div class="sr-similar__grid">
			<?php
			$revealed = 0;
			foreach ( $candidates as $product ) {
				$card_html = skyyrose_visual_similarity_render_card( $product );
				if ( $revealed < $count ) {
					// Reveal initial fallback cards (server-rendered, no JS needed).
					$card_html = str_replace( ' hidden', '', $card_html );
					++$revealed;
				}
				// Output is built from helpers that already escape; safe to echo.
				echo $card_html; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
			}
			?>
		</div>
	</section>
	<?php
	return (string) ob_get_clean();
}
add_shortcode( 'skyyrose_visual_similar', 'skyyrose_visual_similarity_shortcode' );
