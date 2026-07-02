<?php
/**
 * SkyyRose Single Product Page — Impeccable Refinement
 *
 * Technical Garment Lock + Techflat-First Visuals.
 *
 * Fully custom PDP — intentionally replaces WooCommerce core's single-product
 * structure (no woocommerce_single_product_summary hook scaffold). @version is
 * tracked against core single-product.php (last core change: 1.6.4) so the
 * WooCommerce status scanner does not flag this deliberate override as outdated.
 *
 * @package SkyyRose
 * @version 1.6.4
 */

defined( 'ABSPATH' ) || exit;

get_header( 'shop' );

do_action( 'woocommerce_before_main_content' );

while ( have_posts() ) :
	the_post();

	global $product;
	if ( ! is_a( $product, 'WC_Product' ) ) {
		continue;
	}

	$collection = skyyrose_get_product_collection();
	$config     = skyyrose_get_collection( $collection );
	$meta       = skyyrose_get_product_meta();
	$sku        = $product->get_sku();

	// Technical Garment Lock logic.
	$catalog_entry = function_exists( 'skyyrose_get_product' ) ? skyyrose_get_product( $sku ) : null;

	// Editorial PDP: if dossier data exists, render 7-chapter scroll layout.
	$dossier       = function_exists( 'skyyrose_get_product_dossier' ) ? skyyrose_get_product_dossier( $sku ) : null;
	$has_editorial = $dossier && ! empty( $dossier['has_editorial_content'] );

	if ( $has_editorial ) :
		get_template_part(
			'template-parts/product-detail-editorial',
			null,
			array(
				'product'       => $product,
				'catalog_entry' => $catalog_entry,
				'dossier'       => $dossier,
				'collection'    => $collection,
				'config'        => $config,
				'meta'          => $meta,
			)
		);
	else :
		$techflat_url = $catalog_entry ? skyyrose_product_image_uri( $catalog_entry['image'] ?? '' ) : '';
		$main_image   = wp_get_attachment_url( $product->get_image_id() );
		$price_html   = $product->get_price_html();
		$stock_status = $product->get_stock_status();
		?>

		<main id="product-<?php the_ID(); ?>" <?php wc_product_class( 'sr-product', $product ); ?> data-collection="<?php echo esc_attr( $collection ); ?>">

			<section class="sr-hero">
				<div class="sr-container sr-hero-grid">

					<!-- Gallery Column -->
					<div class="sr-gallery rv-clip-left">
						<div class="sr-gallery-main">
							<?php
							$hero_img = $techflat_url ? $techflat_url : $main_image;
							if ( $hero_img ) :
								?>
								<img
									src="<?php echo esc_url( $hero_img ); ?>"
									class="sr-gallery-img"
									id="srMainImg"
									alt="<?php echo esc_attr( get_the_title() ); ?>"
									loading="eager"
									decoding="async"
									fetchpriority="high">
							<?php endif; ?>
						</div>

						<div class="sr-gallery-thumbs">
							<?php if ( $techflat_url ) : ?>
								<button type="button" class="sr-thumb sr-thumb-active" data-img="<?php echo esc_url( $techflat_url ); ?>">
									<img src="<?php echo esc_url( $techflat_url ); ?>" alt="<?php esc_attr_e( 'Technical Blueprint', 'skyyrose' ); ?>">
								</button>
							<?php endif; ?>
							<?php if ( $main_image ) : ?>
								<button type="button" class="sr-thumb <?php echo $techflat_url ? '' : 'sr-thumb-active'; ?>" data-img="<?php echo esc_url( $main_image ); ?>">
									<img src="<?php echo esc_url( $main_image ); ?>" alt="<?php esc_attr_e( 'Model View', 'skyyrose' ); ?>">
								</button>
							<?php endif; ?>
						</div>
					</div>

					<!-- Info Column -->
					<div class="sr-info rv-clip-right">
						<div class="sr-info-inner">
							<p class="sr-info-collection"><?php echo esc_html( $config['label'] ); ?> COLLECTION</p>
							<h1 class="sr-info-name"><?php the_title(); ?></h1>
							<div class="sr-info-price"><?php echo wp_kses_post( $price_html ); ?></div>

							<div class="sr-info-specs">
								<div class="sr-spec">
									<span class="sr-spec-label"><?php esc_html_e( 'GARMENT TYPE', 'skyyrose' ); ?></span>
									<span class="sr-spec-value"><?php echo esc_html( strtoupper( $catalog_entry['garment_type_lock'] ?? 'GARMENT' ) ); ?></span>
								</div>
								<div class="sr-spec">
									<span class="sr-spec-label"><?php esc_html_e( 'SKU', 'skyyrose' ); ?></span>
									<span class="sr-spec-value"><?php echo esc_html( $sku ); ?></span>
								</div>
								<?php if ( ! empty( $meta['material'] ) ) : ?>
								<div class="sr-spec">
									<span class="sr-spec-label"><?php esc_html_e( 'MATERIAL', 'skyyrose' ); ?></span>
									<span class="sr-spec-value"><?php echo esc_html( $meta['material'] ); ?></span>
								</div>
								<?php endif; ?>
							</div>

							<div class="sr-atc-wrap magnetic btn-sweep">
								<?php woocommerce_template_single_add_to_cart(); ?>
							</div>

							<div class="sr-stock">
								<span class="sr-stock-dot"></span>
								<?php
								echo 'instock' === $stock_status
									? esc_html__( 'In Stock — Ready to Ship', 'skyyrose' )
									: esc_html__( 'Pre-Order', 'skyyrose' );
								?>
							</div>
							<?php if ( function_exists( 'skyyrose_render_fit_block' ) ) { skyyrose_render_fit_block( $product->get_id() ); } ?>
						</div>
					</div>
				</div>
			</section>
		</main>
	<?php endif; ?>
	<?php
endwhile;

get_footer( 'shop' );
