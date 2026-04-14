<?php
/**
 * Template Part: Holo Product Card
 *
 * Physics-based magnetic tilt card with holographic shimmer, front/back
 * crossfade, collection-specific palette, and quick-add drawer.
 *
 * Called from two surfaces:
 *
 *   1. `woocommerce/content-product.php`  — passes `$args['product']` as WC_Product.
 *   2. `template-parts/product-grid.php`  — passes either a WC_Product or a
 *      static-card array (title, price, image_url, etc.) resolved by the
 *      catalog display layer.
 *
 * The template handles both shapes transparently: WC_Product data is read
 * via WC accessors, static-card data is read from the `$args` array.
 *
 * @see assets/css/product-card-holo.css   Card styling (750+ lines).
 * @see assets/js/product-card-holo.js     Magnetic tilt, shimmer, quick-add.
 * @see inc/product-catalog-display.php    skyyrose_catalog_to_static_card().
 * @see inc/collections-config.php         Accent colors per collection.
 *
 * @package SkyyRose
 * @since   5.0.0
 * @version 6.5.2
 */

defined( 'ABSPATH' ) || exit;

// ---------------------------------------------------------------------------
// 1. RESOLVE DATA — WC_Product takes priority, catalog static card fallback.
// ---------------------------------------------------------------------------

$wc_product = null;
$product_id = 0;

if ( isset( $args['product'] ) && $args['product'] instanceof WC_Product ) {
	$wc_product = $args['product'];
	$product_id = $wc_product->get_id();
}

// Collection slug — passed explicitly or derived from WC taxonomy.
$collection = '';
if ( ! empty( $args['collection'] ) ) {
	$collection = sanitize_title( (string) $args['collection'] );
} elseif ( $wc_product ) {
	$terms = wp_get_post_terms( $product_id, 'product_cat', array( 'fields' => 'slugs' ) );
	if ( ! is_wp_error( $terms ) && ! empty( $terms ) ) {
		$collection = $terms[0];
	}
}

// ---------------------------------------------------------------------------
// Title.
// ---------------------------------------------------------------------------
if ( $wc_product ) {
	$title = $wc_product->get_name();
} else {
	$title = $args['title'] ?? '';
}

// ---------------------------------------------------------------------------
// Price.
// ---------------------------------------------------------------------------
if ( $wc_product ) {
	$price_html = $wc_product->get_price_html();
} else {
	$price_html = esc_html( $args['price'] ?? '' );
}

// ---------------------------------------------------------------------------
// Images — WC gallery first, then static-card paths from the catalog.
// ---------------------------------------------------------------------------
$front_url = '';
$back_url  = '';

if ( $wc_product ) {
	$image_id = $wc_product->get_image_id();
	if ( $image_id ) {
		$front_url = wp_get_attachment_image_url( $image_id, 'skyyrose-card' );
		if ( ! $front_url ) {
			$front_url = wp_get_attachment_image_url( $image_id, 'woocommerce_thumbnail' );
		}
	}
	$gallery_ids = $wc_product->get_gallery_image_ids();
	if ( ! empty( $gallery_ids ) ) {
		$back_url = wp_get_attachment_image_url( $gallery_ids[0], 'skyyrose-card' );
		if ( ! $back_url ) {
			$back_url = wp_get_attachment_image_url( $gallery_ids[0], 'woocommerce_thumbnail' );
		}
	}
}

// Catalog fallback — only if WC didn't supply images.
if ( empty( $front_url ) && ! empty( $args['image_url'] ) ) {
	$front_url = $args['image_url'];
}
if ( empty( $back_url ) && ! empty( $args['image_back'] ) ) {
	$back_url = $args['image_back'];
}

// Final fallback — theme placeholder.
if ( empty( $front_url ) ) {
	$front_url = get_theme_file_uri( 'assets/images/placeholder-product.jpg' );
}

$has_back = ! empty( $back_url );

// ---------------------------------------------------------------------------
// Permalink — WC permalink, then explicit override, then catalog URL.
// ---------------------------------------------------------------------------
if ( ! empty( $args['permalink'] ) && '#' !== $args['permalink'] ) {
	$permalink = $args['permalink'];
} elseif ( $wc_product ) {
	$permalink = get_permalink( $product_id );
} else {
	$permalink = function_exists( 'skyyrose_product_url' ) && $sku
		? skyyrose_product_url( $sku )
		: '#';
}

// ---------------------------------------------------------------------------
// SKU.
// ---------------------------------------------------------------------------
if ( $wc_product ) {
	$sku = $wc_product->get_sku();
} else {
	$sku = $args['sku'] ?? '';
}

// ---------------------------------------------------------------------------
// Badge (Pre-Order / Sold Out / Sale / Draft).
// ---------------------------------------------------------------------------
$badge_text  = '';
$badge_class = 'holo__badge--default';

if ( $wc_product ) {
	if ( ! $wc_product->is_in_stock() ) {
		$badge_text  = __( 'Sold Out', 'skyyrose' );
		$badge_class = 'holo__badge--soldout';
	} elseif ( $wc_product->is_on_sale() ) {
		$badge_text  = __( 'Sale', 'skyyrose' );
		$badge_class = 'holo__badge--sale';
	} elseif ( 'preorder' === $wc_product->get_meta( '_skyyrose_status' ) ) {
		$badge_text  = __( 'Pre-Order', 'skyyrose' );
		$badge_class = 'holo__badge--preorder';
	}
} elseif ( ! empty( $args['badge_text'] ) ) {
	$raw_badge = strtolower( trim( $args['badge_text'] ) );
	if ( 'sold out' === $raw_badge ) {
		$badge_text  = __( 'Sold Out', 'skyyrose' );
		$badge_class = 'holo__badge--soldout';
	} elseif ( 'pre-order' === $raw_badge || 'preorder' === $raw_badge ) {
		$badge_text  = __( 'Pre-Order', 'skyyrose' );
		$badge_class = 'holo__badge--preorder';
	} elseif ( 'sale' === $raw_badge ) {
		$badge_text  = __( 'Sale', 'skyyrose' );
		$badge_class = 'holo__badge--sale';
	} else {
		$badge_text  = $args['badge_text'];
		$badge_class = 'holo__badge--default';
	}
}

// ---------------------------------------------------------------------------
// Derived state from badge resolution — single source of truth.
// ---------------------------------------------------------------------------
$is_sold_out = ( 'holo__badge--soldout' === $badge_class );
$is_preorder = ( 'holo__badge--preorder' === $badge_class );

// ---------------------------------------------------------------------------
// Edition size (limited run indicator).
// ---------------------------------------------------------------------------
$edition_size = 0;
if ( $wc_product ) {
	$edition_size = (int) $wc_product->get_meta( '_skyyrose_edition_size' );
} elseif ( ! empty( $args['edition_size'] ) ) {
	$edition_size = (int) $args['edition_size'];
}

// ---------------------------------------------------------------------------
// Sizes — for the quick-add drawer.
// ---------------------------------------------------------------------------
$sizes = array();
if ( $wc_product && $wc_product->is_type( 'variable' ) ) {
	$attributes = $wc_product->get_variation_attributes();
	foreach ( $attributes as $attr_name => $values ) {
		if ( false !== stripos( $attr_name, 'size' ) || 'pa_size' === $attr_name ) {
			$sizes = array_values( $values );
			break;
		}
	}
}
// Static card fallback — sizes as pipe-delimited string.
if ( empty( $sizes ) && ! empty( $args['sizes'] ) ) {
	if ( is_string( $args['sizes'] ) ) {
		$sizes = array_filter( array_map( 'trim', explode( '|', $args['sizes'] ) ) );
	} elseif ( is_array( $args['sizes'] ) ) {
		$sizes = $args['sizes'];
	}
}

// ---------------------------------------------------------------------------
// Collection label (for card info section).
// ---------------------------------------------------------------------------
$collection_label = '';
if ( $collection && function_exists( 'skyyrose_get_collections_config' ) ) {
	$config = skyyrose_get_collections_config();
	if ( isset( $config[ $collection ]['label'] ) ) {
		$collection_label = $config[ $collection ]['label'];
	}
}
if ( empty( $collection_label ) && ! empty( $collection ) ) {
	$collection_label = strtoupper( str_replace( '-', ' ', $collection ) );
}

// ---------------------------------------------------------------------------
// Card index — used for stagger delay in the entrance animation.
// ---------------------------------------------------------------------------
$index = (int) ( $args['index'] ?? 0 );

// ---------------------------------------------------------------------------
// Build wrapper classes.
// ---------------------------------------------------------------------------
$card_classes = array( 'holo' );
if ( $collection ) {
	$card_classes[] = 'holo--' . $collection;
}
if ( $is_sold_out ) {
	$card_classes[] = 'holo--sold-out';
}
if ( $edition_size > 0 ) {
	$card_classes[] = 'holo--limited';
}

// ---------------------------------------------------------------------------
// 2. RENDER
// ---------------------------------------------------------------------------
?>
<div class="<?php echo esc_attr( implode( ' ', $card_classes ) ); ?>"
	data-has-back="<?php echo $has_back ? '1' : '0'; ?>"
	data-collection="<?php echo esc_attr( $collection ); ?>"
	<?php if ( $sku ) : ?>
	data-sku="<?php echo esc_attr( $sku ); ?>"
	<?php endif; ?>
	style="--holo-delay: <?php echo esc_attr( $index * 80 ); ?>ms"
	role="listitem">

	<!-- Ambient glow -->
	<div class="holo__glow" aria-hidden="true"></div>

	<!-- Card body (3D tilt container) -->
	<div class="holo__body">

		<!-- Gallery -->
		<div class="holo__gallery">
			<a href="<?php echo esc_url( $permalink ); ?>"
				class="holo__img-link"
				aria-label="<?php echo esc_attr( $title ); ?>"
				tabindex="-1">

				<img class="holo__img holo__img--front"
					src="<?php echo esc_url( $front_url ); ?>"
					alt="<?php echo esc_attr( $title ); ?>"
					loading="lazy"
					decoding="async"
					width="600"
					height="800" />

				<?php if ( $has_back ) : ?>
					<img class="holo__img holo__img--back"
						src="<?php echo esc_url( $back_url ); ?>"
						alt="
						<?php
								printf(
									/* translators: %s: product name */
									esc_attr__( '%s — alternate view', 'skyyrose' ),
									esc_attr( $title )
								);
						?>
							"
						loading="lazy"
						decoding="async"
						width="600"
						height="800" />
				<?php endif; ?>
			</a>

			<?php if ( $badge_text ) : ?>
				<span class="holo__badge <?php echo esc_attr( $badge_class ); ?>">
					<?php echo esc_html( $badge_text ); ?>
				</span>
			<?php endif; ?>

			<?php if ( $edition_size > 0 ) : ?>
				<span class="holo__edition">
					<?php
					printf(
						/* translators: %d: edition size */
						esc_html__( 'Limited to %d', 'skyyrose' ),
						(int) $edition_size
					);
					?>
				</span>
			<?php endif; ?>

			<?php
			static $has_wishlist = null;
			if ( null === $has_wishlist ) {
				$has_wishlist = function_exists( 'skyyrose_wishlist_button' );
			}
			if ( $has_wishlist ) :
				skyyrose_wishlist_button( $product_id ?: $sku );
			endif;
			?>

			<?php if ( $has_back ) : ?>
				<div class="holo__view-indicator" aria-hidden="true">
					<span class="holo__view-dot holo__view-dot--active"></span>
					<span class="holo__view-dot"></span>
				</div>
			<?php endif; ?>
		</div>

		<!-- Holographic shimmer overlay -->
		<div class="holo__shimmer" aria-hidden="true"></div>

		<!-- Product info -->
		<div class="holo__info">
			<?php if ( $collection_label ) : ?>
				<span class="holo__collection"><?php echo esc_html( $collection_label ); ?></span>
			<?php endif; ?>

			<h3 class="holo__name">
				<a href="<?php echo esc_url( $permalink ); ?>">
					<?php echo esc_html( $title ); ?>
				</a>
			</h3>

			<div class="holo__price-row">
				<span class="holo__price">
					<?php echo wp_kses_post( $price_html ); ?>
				</span>
				<?php if ( $is_preorder ) : ?>
					<span class="holo__ship-note"><?php esc_html_e( 'Ships on release', 'skyyrose' ); ?></span>
				<?php endif; ?>
			</div>
		</div>

		<?php if ( ! $is_sold_out ) : ?>
			<!-- Quick-add drawer -->
			<div class="holo__drawer">
				<?php if ( ! empty( $sizes ) ) : ?>
					<div class="holo__sizes" role="radiogroup"
						aria-label="<?php esc_attr_e( 'Select size', 'skyyrose' ); ?>">
						<?php foreach ( $sizes as $i => $size ) : ?>
							<button type="button"
								class="holo__size-pill<?php echo 0 === $i ? ' holo__size-pill--active' : ''; ?>"
								data-size="<?php echo esc_attr( $size ); ?>"
								role="radio"
								aria-checked="<?php echo 0 === $i ? 'true' : 'false'; ?>">
								<?php echo esc_html( $size ); ?>
							</button>
						<?php endforeach; ?>
					</div>
				<?php endif; ?>

				<?php if ( $wc_product && $wc_product->is_purchasable() ) : ?>
					<button type="button"
						class="holo__buy"
						data-product-id="<?php echo esc_attr( $product_id ); ?>"
						aria-label="
						<?php
								printf(
									/* translators: %s: product name */
									esc_attr__( 'Add %s to bag', 'skyyrose' ),
									esc_attr( $title )
								);
						?>
							">
						<?php esc_html_e( 'Add to Bag', 'skyyrose' ); ?>
					</button>
				<?php else : ?>
					<a href="<?php echo esc_url( $permalink ); ?>"
						class="holo__buy"
						aria-label="
						<?php
								printf(
									/* translators: %s: product name */
									esc_attr__( 'View %s', 'skyyrose' ),
									esc_attr( $title )
								);
						?>
							">
						<?php esc_html_e( 'View Piece', 'skyyrose' ); ?>
					</a>
				<?php endif; ?>
			</div>
		<?php endif; ?>

	</div><!-- .holo__body -->
</div><!-- .holo -->
