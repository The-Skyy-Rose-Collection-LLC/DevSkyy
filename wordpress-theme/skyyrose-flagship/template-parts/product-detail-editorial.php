<?php
/**
 * Product Detail — Editorial 7-Chapter Scroll Layout
 *
 * Renders a full-page narrative experience when dossier data exists for a product.
 * Falls back to standard PDP when no dossier is available (handled by caller).
 *
 * @package SkyyRose
 * @since   7.2.0
 *
 * @param array $args {
 *     @type WC_Product $product       WooCommerce product object.
 *     @type array      $catalog_entry Catalog data from skyyrose_get_product().
 *     @type array      $dossier       Parsed dossier from skyyrose_get_product_dossier().
 *     @type string     $collection    Collection slug.
 *     @type array      $config        Collection config from skyyrose_collection_config().
 *     @type array      $meta          Product meta from skyyrose_get_product_meta().
 * }
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$product       = $args['product'] ?? null;
$catalog_entry = $args['catalog_entry'] ?? array();
$dossier       = $args['dossier'] ?? array();
$collection    = $args['collection'] ?? '';
$config        = $args['config'] ?? array();
$meta          = $args['meta'] ?? array();

if ( ! $product || ! is_a( $product, 'WC_Product' ) ) {
	return;
}

$sku        = $product->get_sku();
$price_html = $product->get_price_html();
$stock      = $product->get_stock_status();

// Collection content for story chapter.
$story = function_exists( 'skyyrose_get_collection_content' )
	? skyyrose_get_collection_content( $collection )
	: null;

// Image URIs.
$hero_image  = ! empty( $catalog_entry['image'] )
	? skyyrose_product_image_uri( $catalog_entry['image'] )
	: '';
$front_model = ! empty( $catalog_entry['front_model_image'] )
	? skyyrose_product_image_uri( $catalog_entry['front_model_image'] )
	: '';
$back_model  = ! empty( $catalog_entry['back_model_image'] )
	? skyyrose_product_image_uri( $catalog_entry['back_model_image'] )
	: '';

$garment_lock = $dossier['garment_type_lock'] ?? '';
$branding     = $dossier['branding'] ?? array();
$edition_size = (int) ( $catalog_entry['edition_size'] ?? 0 );
$sizes_raw    = $catalog_entry['sizes'] ?? '';
?>

<article class="sr-editorial" data-collection="<?php echo esc_attr( $collection ); ?>">

	<?php // ── Chapter 1: Encounter ─────────────────────────────────────── ?>
	<section class="sr-ed__encounter rv-clip-up" role="region" aria-labelledby="sr-ed-encounter-h">
		<h2 id="sr-ed-encounter-h" class="screen-reader-text">
			<?php echo esc_html( $product->get_name() ); ?>
		</h2>
		<?php if ( $hero_image ) : ?>
			<img
				src="<?php echo esc_url( $hero_image ); ?>"
				alt="<?php echo esc_attr( $product->get_name() ); ?>"
				class="sr-ed__encounter-img"
				fetchpriority="high"
			/>
		<?php endif; ?>
	</section>

	<?php // ── Chapter 2: The Piece ─────────────────────────────────────── ?>
	<section class="sr-ed__piece rv-clip-up" role="region" aria-labelledby="sr-ed-piece-h">
		<span class="sr-ed__chapter-num"><?php esc_html_e( '02', 'skyyrose' ); ?></span>
		<h2 id="sr-ed-piece-h" class="sr-ed__section-title">
			<?php esc_html_e( 'The Piece', 'skyyrose' ); ?>
		</h2>
		<?php
		// Numbered-authentication badge (F4, v1.5.4). Black Rose only,
		// gated on edition_size > 0. Surfaces the brand-DNA pillar
		// "Every piece is hand-numbered" above the descriptive copy
		// instead of burying it in product details.
		if ( 'black-rose' === $collection && $edition_size > 0 ) :
			?>
			<aside class="sr-ed__edition-badge" role="note" aria-label="<?php esc_attr_e( 'Numbered authentication', 'skyyrose' ); ?>">
				<span class="sr-ed__edition-badge-label"><?php esc_html_e( 'Numbered Authentication', 'skyyrose' ); ?></span>
				<span class="sr-ed__edition-badge-value">
					<?php
					// translators: %d is the total edition run size, e.g. "One of 80".
					echo esc_html( sprintf( __( 'One of %d', 'skyyrose' ), $edition_size ) );
					?>
				</span>
				<span class="sr-ed__edition-badge-note">
					<?php esc_html_e( 'Hand-numbered at fulfillment. Never restocked.', 'skyyrose' ); ?>
				</span>
			</aside>
		<?php endif; ?>
		<?php if ( $garment_lock ) : ?>
			<p class="sr-ed__garment-lock"><?php echo esc_html( $garment_lock ); ?></p>
		<?php endif; ?>
		<?php if ( ! empty( $branding['front'] ) ) : ?>
			<div class="sr-ed__branding-detail">
				<h3 class="sr-ed__branding-label"><?php esc_html_e( 'Front', 'skyyrose' ); ?></h3>
				<p><?php echo esc_html( $branding['front'] ); ?></p>
			</div>
		<?php endif; ?>
		<?php if ( ! empty( $branding['back'] ) ) : ?>
			<div class="sr-ed__branding-detail">
				<h3 class="sr-ed__branding-label"><?php esc_html_e( 'Back', 'skyyrose' ); ?></h3>
				<p><?php echo esc_html( $branding['back'] ); ?></p>
			</div>
		<?php endif; ?>
		<?php if ( ! empty( $catalog_entry['description'] ) ) : ?>
			<p class="sr-ed__description"><?php echo esc_html( $catalog_entry['description'] ); ?></p>
		<?php endif; ?>
	</section>

	<?php // ── Chapter 3: The Story ─────────────────────────────────────── ?>
	<?php if ( $story && ! empty( $story['story_text_1'] ) ) : ?>
	<section class="sr-ed__story rv-blur" role="region" aria-labelledby="sr-ed-story-h">
		<span class="sr-ed__chapter-num"><?php esc_html_e( '03', 'skyyrose' ); ?></span>
		<h2 id="sr-ed-story-h" class="sr-ed__section-title">
			<?php esc_html_e( 'The Story', 'skyyrose' ); ?>
		</h2>
		<p class="sr-ed__story-text"><?php echo esc_html( $story['story_text_1'] ); ?></p>
		<?php if ( ! empty( $story['story_quote'] ) ) : ?>
			<blockquote class="sr-ed__blockquote">
				<p><?php echo esc_html( $story['story_quote'] ); ?></p>
			</blockquote>
		<?php endif; ?>
		<?php if ( ! empty( $story['story_text_2'] ) ) : ?>
			<p class="sr-ed__story-text"><?php echo esc_html( $story['story_text_2'] ); ?></p>
		<?php endif; ?>
	</section>
	<?php endif; ?>

	<?php // ── Chapter 4: The Fit ───────────────────────────────────────── ?>
	<?php if ( $front_model || $back_model ) : ?>
	<section class="sr-ed__fit rv-clip-up" role="region" aria-labelledby="sr-ed-fit-h">
		<span class="sr-ed__chapter-num"><?php esc_html_e( '04', 'skyyrose' ); ?></span>
		<h2 id="sr-ed-fit-h" class="sr-ed__section-title">
			<?php esc_html_e( 'The Fit', 'skyyrose' ); ?>
		</h2>
		<div class="sr-ed__fit-images">
			<?php if ( $front_model ) : ?>
				<img src="<?php echo esc_url( $front_model ); ?>"
					alt="<?php echo esc_attr( $product->get_name() . ' — front' ); ?>"
					class="sr-ed__fit-img" loading="lazy" />
			<?php endif; ?>
			<?php if ( $back_model ) : ?>
				<img src="<?php echo esc_url( $back_model ); ?>"
					alt="<?php echo esc_attr( $product->get_name() . ' — back' ); ?>"
					class="sr-ed__fit-img" loading="lazy" />
			<?php endif; ?>
		</div>
	</section>
	<?php endif; ?>

	<?php // ── Chapter 5: Add to Cart ───────────────────────────────────── ?>
	<section class="sr-ed__cart" role="region" aria-labelledby="sr-ed-cart-h">
		<span class="sr-ed__chapter-num"><?php esc_html_e( '05', 'skyyrose' ); ?></span>
		<h2 id="sr-ed-cart-h" class="sr-ed__section-title">
			<?php esc_html_e( 'Make It Yours', 'skyyrose' ); ?>
		</h2>

		<p class="sr-ed__price"><?php echo wp_kses_post( $price_html ); ?></p>

		<?php if ( $sizes_raw ) : ?>
			<p class="sr-ed__sizes-label" id="sr-ed-sizes-label"><?php esc_html_e( 'Select Size', 'skyyrose' ); ?></p>
			<div class="sr-ed__sizes" role="group" aria-labelledby="sr-ed-sizes-label">
				<?php foreach ( explode( '|', $sizes_raw ) as $size ) : ?>
					<?php $size_clean = trim( $size ); ?>
						<button type="button" class="sr-ed__size" aria-pressed="false" data-size="<?php echo esc_attr( $size_clean ); ?>"><?php echo esc_html( $size_clean ); ?></button>
				<?php endforeach; ?>
			</div>
		<?php endif; ?>

		<div class="sr-ed__atc-wrap">
			<?php woocommerce_template_single_add_to_cart(); ?>
		</div>

		<div class="sr-ed__stock">
			<span class="sr-ed__stock-dot"></span>
			<?php
			echo 'instock' === $stock
				? esc_html__( 'In Stock — Ready to Ship', 'skyyrose' )
				: esc_html__( 'Pre-Order', 'skyyrose' );
			?>
		</div>

		<?php if ( $edition_size > 0 ) : ?>
			<p class="sr-ed__edition">
				<?php
				printf(
					/* translators: %d: edition size */
					esc_html__( 'Limited Edition — %d Pieces', 'skyyrose' ),
					(int) $edition_size
				);
				?>
			</p>
		<?php endif; ?>
	</section>

	<?php // Chapter 6 "Wears With" retired 2026-05-27 — founder canon: no related products on PDP. ?>

	<?php // ── Chapter 7: Care + Craft ──────────────────────────────────── ?>
	<section class="sr-ed__care rv-blur" role="region" aria-labelledby="sr-ed-care-h">
		<span class="sr-ed__chapter-num"><?php esc_html_e( '07', 'skyyrose' ); ?></span>
		<h2 id="sr-ed-care-h" class="sr-ed__section-title">
			<?php esc_html_e( 'Care + Craft', 'skyyrose' ); ?>
		</h2>
		<div class="sr-ed__care-items">
			<div class="sr-ed__care-item">
				<h3 class="sr-ed__care-item-title"><?php esc_html_e( 'Care Instructions', 'skyyrose' ); ?></h3>
				<p><?php esc_html_e( 'Machine wash cold, inside out. Tumble dry low. Do not bleach. Iron on low heat if needed — avoid direct contact with prints and embroidery.', 'skyyrose' ); ?></p>
			</div>
			<div class="sr-ed__care-item">
				<h3 class="sr-ed__care-item-title"><?php esc_html_e( 'Construction', 'skyyrose' ); ?></h3>
				<p><?php esc_html_e( 'Every piece is constructed with reinforced stitching at stress points, pre-shrunk heavyweight fabric, and solid-brass hardware. Built to last through real life.', 'skyyrose' ); ?></p>
			</div>
			<div class="sr-ed__care-item">
				<h3 class="sr-ed__care-item-title"><?php esc_html_e( 'Sustainability', 'skyyrose' ); ?></h3>
				<p><?php esc_html_e( 'We produce in limited runs to minimize waste. Every unsold unit is donated — nothing goes to landfill. Packaging is recycled and recyclable.', 'skyyrose' ); ?></p>
			</div>
		</div>
	</section>

</article>
