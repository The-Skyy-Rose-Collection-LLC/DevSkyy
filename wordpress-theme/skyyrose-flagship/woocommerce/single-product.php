<?php
/**
 * SkyyRose Single Product Page — Impeccable Refinement
 * 
 * Technical Garment Lock + Techflat-First Visuals.
 */

defined( 'ABSPATH' ) || exit;

get_header( 'shop' );

do_action( 'woocommerce_before_main_content' );

while ( have_posts() ) :
	the_post();

	global $product;
	if ( ! is_a( $product, 'WC_Product' ) ) continue;

	$collection = skyyrose_get_product_collection();
	$config     = skyyrose_collection_config( $collection );
	$meta       = skyyrose_get_product_meta();
	$sku        = $product->get_sku();

	// Technical Garment Lock logic.
	$catalog_entry = function_exists('skyyrose_get_product') ? skyyrose_get_product($sku) : null;
	$techflat_url  = $catalog_entry ? skyyrose_product_image_uri($catalog_entry['image'] ?? '') : '';
	$main_image    = wp_get_attachment_url( $product->get_image_id() );
	$gallery_ids   = $product->get_gallery_image_ids();
    $price_html    = $product->get_price_html();
    $stock_status  = $product->get_stock_status();
	?>

	<main id="product-<?php the_ID(); ?>" <?php wc_product_class( 'sr-product', $product ); ?> data-collection="<?php echo esc_attr( $collection ); ?>">

		<section class="sr-hero">
			<div class="sr-container sr-hero-grid">

				<!-- Gallery Column -->
				<div class="sr-gallery">
					<div class="sr-gallery-main">
						<?php 
						$hero_img = $techflat_url ?: $main_image;
						if ( $hero_img ) : ?>
							<img src="<?php echo esc_url( $hero_img ); ?>" class="sr-gallery-img" id="srMainImg" fetchpriority="high">
						<?php endif; ?>
					</div>

					<div class="sr-gallery-thumbs">
						<?php if ( $techflat_url ) : ?>
							<button type="button" class="sr-thumb sr-thumb-active" data-img="<?php echo esc_url( $techflat_url ); ?>">
								<img src="<?php echo esc_url( $techflat_url ); ?>" alt="Technical Blueprint">
							</button>
						<?php endif; ?>
						<?php if ( $main_image ) : ?>
							<button type="button" class="sr-thumb <?php echo $techflat_url ? '' : 'sr-thumb-active'; ?>" data-img="<?php echo esc_url( $main_image ); ?>">
								<img src="<?php echo esc_url( $main_image ); ?>" alt="Model View">
							</button>
						<?php endif; ?>
					</div>
				</div>

				<!-- Info Column -->
				<div class="sr-info">
					<div class="sr-info-inner">
						<p class="sr-info-collection"><?php echo esc_html( $config['label'] ); ?> COLLECTION</p>
						<h1 class="sr-info-name"><?php the_title(); ?></h1>
						<div class="sr-info-price"><?php echo wp_kses_post( $price_html ); ?></div>

						<div class="sr-info-specs">
							<div class="sr-spec">
								<span class="sr-spec-label">GARMENT TYPE</span>
								<span class="sr-spec-value"><?php echo esc_html( strtoupper($catalog_entry['garment_type_lock'] ?? 'GARMENT') ); ?></span>
							</div>
							<div class="sr-spec">
								<span class="sr-spec-label">SKU</span>
								<span class="sr-spec-value"><?php echo esc_html( $sku ); ?></span>
							</div>
                            <?php if ($meta['material']): ?>
                            <div class="sr-spec">
								<span class="sr-spec-label">MATERIAL</span>
								<span class="sr-spec-value"><?php echo esc_html( $meta['material'] ); ?></span>
							</div>
                            <?php endif; ?>
						</div>

						<div class="sr-atc-wrap">
							<?php woocommerce_template_single_add_to_cart(); ?>
						</div>

                        <div class="sr-stock">
                            <span class="sr-stock-dot"></span> <?php echo 'instock' === $stock_status ? 'IN STOCK — READY TO SHIP' : 'PRE-ORDER'; ?>
                        </div>
					</div>
				</div>
			</div>
		</section>
	</main>
	<?php
endwhile;

get_footer( 'shop' );
