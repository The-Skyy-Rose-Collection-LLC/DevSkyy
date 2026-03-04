<?php
/**
 * SkyyRose Single Product Page — Elite Web Builder v4.0.0
 *
 * WooCommerce template override. Detects collection category and
 * loads the appropriate collection-skinned product template.
 * Falls back to BLACK ROSE aesthetic for uncategorized products.
 *
 * Three visual worlds:
 *   Black Rose  — silver / monochrome (#C0C0C0)
 *   Love Hurts  — crimson / gothic (#DC143C)
 *   Signature   — gold / opulence (#D4AF37)
 *
 * @package SkyyRose_Flagship
 * @since   4.0.0
 * @version 4.0.0
 *
 * @see https://woocommerce.com/document/template-structure/
 */

defined( 'ABSPATH' ) || exit;

get_header( 'shop' );

/**
 * Hook: woocommerce_before_main_content.
 *
 * @hooked woocommerce_output_content_wrapper - 10
 * @hooked woocommerce_breadcrumb - 20 (removed by theme)
 */
do_action( 'woocommerce_before_main_content' );

while ( have_posts() ) :
	the_post();

	global $product;

	if ( ! is_a( $product, 'WC_Product' ) ) {
		continue;
	}

	// Collection detection and config.
	$collection = skyyrose_get_product_collection();
	$config     = skyyrose_collection_config( $collection );
	$meta       = skyyrose_get_product_meta();
	$related    = skyyrose_get_related_products_by_category( get_the_ID(), 4 );

	// Product data.
	$gallery_ids  = $product->get_gallery_image_ids();
	$main_image   = wp_get_attachment_url( $product->get_image_id() );
	$is_variable  = $product->is_type( 'variable' );
	$price_html   = $product->get_price_html();
	$stock_status = $product->get_stock_status();
	$sku          = $product->get_sku();

	// Breadcrumb data.
	$shop_url   = get_permalink( wc_get_page_id( 'shop' ) );
	$categories = get_the_terms( get_the_ID(), 'product_cat' );
	$cat_link   = '';
	$cat_name   = $config['label'];
	if ( $categories && ! is_wp_error( $categories ) ) {
		$cat_link = get_term_link( $categories[0] );
		$cat_name = $categories[0]->name;
	}
	?>

	<style>
	:root {
		--sr-accent: <?php echo esc_attr( $config['accent'] ); ?>;
		--sr-accent-rgb: <?php echo esc_attr( $config['accent_rgb'] ); ?>;
		--sr-bg: <?php echo esc_attr( $config['bg'] ); ?>;
		--sr-bg-alt: <?php echo esc_attr( $config['bg_alt'] ); ?>;
		--sr-text: <?php echo esc_attr( $config['text'] ); ?>;
		--sr-dim: <?php echo esc_attr( $config['dim'] ); ?>;
		--sr-gradient: <?php echo esc_attr( $config['gradient'] ); ?>;
		--sr-cta-color: <?php echo esc_attr( $config['cta_color'] ); ?>;
	}
	</style>

	<main id="product-<?php the_ID(); ?>" <?php wc_product_class( 'sr-product', $product ); ?>
	      data-collection="<?php echo esc_attr( $collection ); ?>">

		<?php
		/**
		 * Hook: woocommerce_before_single_product.
		 *
		 * @hooked woocommerce_output_all_notices - 10
		 */
		do_action( 'woocommerce_before_single_product' );
		?>

		<!-- BREADCRUMB -->
		<nav class="sr-breadcrumb" aria-label="<?php esc_attr_e( 'Breadcrumb', 'skyyrose-flagship' ); ?>">
			<div class="sr-container">
				<a href="<?php echo esc_url( home_url( '/' ) ); ?>">SkyyRose</a>
				<span class="sr-bc-sep">/</span>
				<a href="<?php echo esc_url( $shop_url ); ?>"><?php esc_html_e( 'Shop', 'skyyrose-flagship' ); ?></a>
				<span class="sr-bc-sep">/</span>
				<?php if ( $cat_link && ! is_wp_error( $cat_link ) ) : ?>
					<a href="<?php echo esc_url( $cat_link ); ?>"><?php echo esc_html( $cat_name ); ?></a>
					<span class="sr-bc-sep">/</span>
				<?php endif; ?>
				<span class="sr-bc-current"><?php the_title(); ?></span>
			</div>
		</nav>

		<!-- PRODUCT HERO — Split Layout -->
		<section class="sr-hero">
			<div class="sr-container sr-hero-grid">

				<!-- Gallery Column -->
				<div class="sr-gallery" data-gallery>
					<!-- Main Image -->
					<div class="sr-gallery-main">
						<?php if ( $meta['limited'] ) : ?>
							<span class="sr-badge-limited"><?php
								esc_html_e( 'Limited Edition', 'skyyrose-flagship' );
								if ( $meta['edition_of'] ) {
									echo ' &mdash; ' . intval( $meta['edition_of'] ) . ' pieces';
								}
							?></span>
						<?php endif; ?>

						<span class="sr-badge-collection"><?php echo esc_html( $config['label'] ); ?></span>

						<?php if ( $main_image ) : ?>
							<img src="<?php echo esc_url( $main_image ); ?>"
							     alt="<?php echo esc_attr( $product->get_name() ); ?>"
							     class="sr-gallery-img sr-gallery-active"
							     id="srMainImg"
							     loading="eager" fetchpriority="high" decoding="async">
						<?php else : ?>
							<div class="sr-gallery-placeholder">
								<span class="sr-gallery-letter"><?php echo esc_html( mb_substr( $product->get_name(), 0, 1 ) ); ?></span>
							</div>
						<?php endif; ?>

						<!-- Zoom overlay -->
						<div class="sr-gallery-zoom" id="srZoom" aria-hidden="true"></div>
					</div>

					<!-- Thumbnails -->
					<?php if ( ! empty( $gallery_ids ) ) : ?>
						<div class="sr-gallery-thumbs">
							<?php if ( $main_image ) : ?>
								<button class="sr-thumb sr-thumb-active" data-img="<?php echo esc_url( $main_image ); ?>"
								        aria-label="<?php esc_attr_e( 'Main product image', 'skyyrose-flagship' ); ?>">
									<img src="<?php echo esc_url( $main_image ); ?>" alt="<?php echo esc_attr( $product->get_name() . ' — main view' ); ?>" loading="lazy">
								</button>
							<?php endif; ?>
							<?php
							$sr_thumb_idx = 2;
							foreach ( $gallery_ids as $gid ) :
								$gurl = wp_get_attachment_url( $gid );
								if ( ! $gurl ) {
									continue;
								}
								$sr_galt = wp_get_attachment_caption( $gid ) ?: ( $product->get_name() . ' — view ' . $sr_thumb_idx );
							?>
								<button class="sr-thumb" data-img="<?php echo esc_url( $gurl ); ?>"
								        aria-label="<?php printf( esc_attr__( 'View image %d', 'skyyrose-flagship' ), $sr_thumb_idx ); ?>">
									<img src="<?php echo esc_url( $gurl ); ?>" alt="<?php echo esc_attr( $sr_galt ); ?>" loading="lazy">
								</button>
							<?php
							$sr_thumb_idx++;
							endforeach; ?>
						</div>
					<?php endif; ?>
				</div>

				<!-- Info Column -->
				<div class="sr-info">
					<div class="sr-info-inner">
						<!-- Collection badge -->
						<p class="sr-info-collection"><?php echo esc_html( $config['label'] ); ?> COLLECTION</p>

						<!-- Product name -->
						<h1 class="sr-info-name"><?php the_title(); ?></h1>

						<!-- Price -->
						<div class="sr-info-price"><?php echo $price_html; // phpcs:ignore WordPress.Security.EscapeOutput ?></div>

						<!-- Short description -->
						<?php if ( $product->get_short_description() ) : ?>
							<div class="sr-info-desc">
								<?php echo wp_kses_post( $product->get_short_description() ); ?>
							</div>
						<?php endif; ?>

						<!-- Spec table -->
						<?php if ( $meta['material'] || $meta['fit'] || $meta['detail'] ) : ?>
							<div class="sr-info-specs">
								<?php if ( $meta['material'] ) : ?>
									<div class="sr-spec">
										<span class="sr-spec-label"><?php esc_html_e( 'Material', 'skyyrose-flagship' ); ?></span>
										<span class="sr-spec-value"><?php echo esc_html( $meta['material'] ); ?></span>
									</div>
								<?php endif; ?>
								<?php if ( $meta['fit'] ) : ?>
									<div class="sr-spec">
										<span class="sr-spec-label"><?php esc_html_e( 'Fit', 'skyyrose-flagship' ); ?></span>
										<span class="sr-spec-value"><?php echo esc_html( $meta['fit'] ); ?></span>
									</div>
								<?php endif; ?>
								<?php if ( $meta['detail'] ) : ?>
									<div class="sr-spec">
										<span class="sr-spec-label"><?php esc_html_e( 'Detail', 'skyyrose-flagship' ); ?></span>
										<span class="sr-spec-value"><?php echo esc_html( $meta['detail'] ); ?></span>
									</div>
								<?php endif; ?>
								<?php if ( $sku ) : ?>
									<div class="sr-spec">
										<span class="sr-spec-label"><?php esc_html_e( 'SKU', 'skyyrose-flagship' ); ?></span>
										<span class="sr-spec-value"><?php echo esc_html( $sku ); ?></span>
									</div>
								<?php endif; ?>
							</div>
						<?php endif; ?>

						<!-- Add to Cart Form -->
						<div class="sr-atc-wrap" id="sr-atc-anchor">
							<?php
							// Remove default WC hooks — we control the layout.
							remove_action( 'woocommerce_single_product_summary', 'woocommerce_template_single_add_to_cart', 30 );

							// Output the appropriate add-to-cart template.
							if ( $is_variable ) {
								woocommerce_variable_add_to_cart();
							} else {
								woocommerce_simple_add_to_cart();
							}
							?>
						</div>

						<!-- Stock status -->
						<div class="sr-stock sr-stock-<?php echo esc_attr( $stock_status ); ?>">
							<?php if ( 'instock' === $stock_status ) : ?>
								<span class="sr-stock-dot"></span> <?php esc_html_e( 'In Stock — Ready to Ship', 'skyyrose-flagship' ); ?>
							<?php elseif ( 'onbackorder' === $stock_status ) : ?>
								<span class="sr-stock-dot"></span> <?php esc_html_e( 'Pre-Order — Ships Spring 2026', 'skyyrose-flagship' ); ?>
							<?php else : ?>
								<span class="sr-stock-dot"></span> <?php esc_html_e( 'Sold Out', 'skyyrose-flagship' ); ?>
							<?php endif; ?>
						</div>

						<!-- Trust signals -->
						<div class="sr-trust">
							<div class="sr-trust-item">
								<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
								<span><?php esc_html_e( 'Secure Checkout', 'skyyrose-flagship' ); ?></span>
							</div>
							<div class="sr-trust-item">
								<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
								<span><?php esc_html_e( 'Free Shipping $150+', 'skyyrose-flagship' ); ?></span>
							</div>
							<div class="sr-trust-item">
								<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M3 12a9 9 0 1018 0 9 9 0 00-18 0z"/><path d="M12 8v4l3 3"/></svg>
								<span><?php esc_html_e( '30-Day Returns', 'skyyrose-flagship' ); ?></span>
							</div>
						</div>

						<!-- Social Share -->
						<div class="sr-share" aria-label="<?php esc_attr_e( 'Share this product', 'skyyrose-flagship' ); ?>">
							<span class="sr-share-label"><?php esc_html_e( 'Share', 'skyyrose-flagship' ); ?></span>
							<div class="sr-share-btns">
								<button class="sr-share-btn sr-share-native" type="button" aria-label="<?php esc_attr_e( 'Share', 'skyyrose-flagship' ); ?>" style="display:none"
									data-title="<?php echo esc_attr( get_the_title() ); ?>"
									data-text="<?php echo esc_attr( $config['label'] . ' — ' . wp_strip_all_tags( $price_html ) ); ?>"
									data-url="<?php echo esc_attr( get_permalink() ); ?>">
									<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M4 12v8a2 2 0 002 2h12a2 2 0 002-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" y1="2" x2="12" y2="15"/></svg>
								</button>
								<a class="sr-share-btn sr-share-pin" href="https://pinterest.com/pin/create/button/?url=<?php echo rawurlencode( get_permalink() ); ?>&media=<?php echo rawurlencode( $main_image ?: '' ); ?>&description=<?php echo rawurlencode( get_the_title() . ' — ' . $config['label'] . ' by SkyyRose' ); ?>" target="_blank" rel="noopener noreferrer" aria-label="<?php esc_attr_e( 'Share on Pinterest', 'skyyrose-flagship' ); ?>">
									<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.08 3.15 9.42 7.6 11.18-.1-.95-.2-2.42.04-3.46.22-.94 1.42-6.03 1.42-6.03s-.36-.73-.36-1.8c0-1.69.98-2.95 2.2-2.95 1.04 0 1.54.78 1.54 1.71 0 1.04-.66 2.6-1.01 4.04-.29 1.21.6 2.2 1.79 2.2 2.14 0 3.79-2.26 3.79-5.52 0-2.89-2.08-4.9-5.04-4.9-3.43 0-5.45 2.58-5.45 5.24 0 1.04.4 2.15.9 2.75.1.12.11.22.08.34-.09.38-.3 1.21-.34 1.38-.06.22-.18.27-.42.16-1.56-.73-2.54-3.01-2.54-4.85 0-3.95 2.87-7.58 8.28-7.58 4.35 0 7.73 3.1 7.73 7.23 0 4.32-2.72 7.8-6.5 7.8-1.27 0-2.46-.66-2.87-1.44l-.78 2.98c-.28 1.08-1.04 2.44-1.55 3.27C9.58 23.81 10.77 24 12 24c6.63 0 12-5.37 12-12S18.63 0 12 0z"/></svg>
								</a>
								<a class="sr-share-btn sr-share-x" href="https://twitter.com/intent/tweet?url=<?php echo rawurlencode( get_permalink() ); ?>&text=<?php echo rawurlencode( get_the_title() . ' — ' . $config['label'] . ' by @SkyyRose. Luxury Grows from Concrete.' ); ?>" target="_blank" rel="noopener noreferrer" aria-label="<?php esc_attr_e( 'Share on X', 'skyyrose-flagship' ); ?>">
									<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
								</a>
								<a class="sr-share-btn sr-share-fb" href="https://www.facebook.com/sharer/sharer.php?u=<?php echo rawurlencode( get_permalink() ); ?>" target="_blank" rel="noopener noreferrer" aria-label="<?php esc_attr_e( 'Share on Facebook', 'skyyrose-flagship' ); ?>">
									<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
								</a>
								<button class="sr-share-btn sr-share-copy" type="button" aria-label="<?php esc_attr_e( 'Copy link', 'skyyrose-flagship' ); ?>" data-url="<?php echo esc_attr( get_permalink() ); ?>">
									<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/></svg>
								</button>
							</div>
						</div>
					</div>
				</div>
			</div>
		</section>

		<!-- PRODUCT DETAILS ACCORDION -->
		<section class="sr-details">
			<div class="sr-container">
				<div class="sr-details-grid">

					<!-- Full Description -->
					<?php if ( $product->get_description() ) : ?>
						<div class="sr-accordion" data-accordion>
							<button class="sr-accordion-trigger" aria-expanded="true">
								<span><?php esc_html_e( 'Description', 'skyyrose-flagship' ); ?></span>
								<span class="sr-accordion-icon">&minus;</span>
							</button>
							<div class="sr-accordion-content sr-accordion-open">
								<?php echo wp_kses_post( $product->get_description() ); ?>
							</div>
						</div>
					<?php endif; ?>

					<!-- Materials & Care -->
					<?php if ( $meta['material'] || $meta['care'] || $meta['made_in'] ) : ?>
						<div class="sr-accordion" data-accordion>
							<button class="sr-accordion-trigger" aria-expanded="false">
								<span><?php esc_html_e( 'Materials & Care', 'skyyrose-flagship' ); ?></span>
								<span class="sr-accordion-icon">+</span>
							</button>
							<div class="sr-accordion-content">
								<?php if ( $meta['material'] ) : ?>
									<p><strong><?php esc_html_e( 'Material:', 'skyyrose-flagship' ); ?></strong> <?php echo esc_html( $meta['material'] ); ?></p>
								<?php endif; ?>
								<?php if ( $meta['made_in'] ) : ?>
									<p><strong><?php esc_html_e( 'Made in:', 'skyyrose-flagship' ); ?></strong> <?php echo esc_html( $meta['made_in'] ); ?></p>
								<?php endif; ?>
								<?php if ( $meta['care'] ) : ?>
									<p><strong><?php esc_html_e( 'Care:', 'skyyrose-flagship' ); ?></strong> <?php echo esc_html( $meta['care'] ); ?></p>
								<?php endif; ?>
							</div>
						</div>
					<?php endif; ?>

					<!-- Size Guide -->
					<div class="sr-accordion" data-accordion>
						<button class="sr-accordion-trigger" aria-expanded="false">
							<span><?php esc_html_e( 'Size Guide', 'skyyrose-flagship' ); ?></span>
							<span class="sr-accordion-icon">+</span>
						</button>
						<div class="sr-accordion-content">
							<p><?php esc_html_e( 'All SkyyRose pieces are designed gender-neutral. We recommend ordering your usual size for a standard fit, or sizing up for an oversized look.', 'skyyrose-flagship' ); ?></p>
							<p><?php
								printf(
									/* translators: %s: contact email */
									esc_html__( 'Need help? Email %s with your height and weight for a personal recommendation.', 'skyyrose-flagship' ),
									'<a href="mailto:corey@skyyrose.co">corey@skyyrose.co</a>'
								);
							?></p>
						</div>
					</div>

					<!-- Shipping & Returns -->
					<div class="sr-accordion" data-accordion>
						<button class="sr-accordion-trigger" aria-expanded="false">
							<span><?php esc_html_e( 'Shipping & Returns', 'skyyrose-flagship' ); ?></span>
							<span class="sr-accordion-icon">+</span>
						</button>
						<div class="sr-accordion-content">
							<p><?php esc_html_e( 'Free shipping on orders over $150. Standard delivery 5-7 business days. Expedited options available at checkout.', 'skyyrose-flagship' ); ?></p>
							<p><?php esc_html_e( '30-day return policy on unworn items with original tags. Pre-order items ship on the announced date.', 'skyyrose-flagship' ); ?></p>
						</div>
					</div>
				</div>
			</div>
		</section>

		<!-- COLLECTION PRODUCTS (Related) -->
		<?php if ( ! empty( $related ) ) : ?>
			<section class="sr-related" aria-label="<?php esc_attr_e( 'Related Products', 'skyyrose-flagship' ); ?>">
				<div class="sr-container">
					<div class="sr-related-head">
						<h2 class="sr-related-title"><?php
							printf(
								/* translators: %s: collection name */
								esc_html__( 'More from %s', 'skyyrose-flagship' ),
								esc_html( $config['label'] )
							);
						?></h2>
						<?php if ( $cat_link && ! is_wp_error( $cat_link ) ) : ?>
							<a href="<?php echo esc_url( $cat_link ); ?>" class="sr-related-link">
								<?php esc_html_e( 'View Full Collection', 'skyyrose-flagship' ); ?> &rarr;
							</a>
						<?php endif; ?>
					</div>
					<div class="sr-related-grid">
						<?php foreach ( $related as $rel_product ) :
							$rel_img  = wp_get_attachment_url( $rel_product->get_image_id() );
							$rel_link = get_permalink( $rel_product->get_id() );
						?>
							<a href="<?php echo esc_url( $rel_link ); ?>" class="sr-related-card">
								<div class="sr-related-img">
									<?php if ( $rel_img ) : ?>
										<img src="<?php echo esc_url( $rel_img ); ?>"
										     alt="<?php echo esc_attr( $rel_product->get_name() ); ?>"
										     loading="lazy">
									<?php else : ?>
										<span class="sr-related-letter"><?php echo esc_html( mb_substr( $rel_product->get_name(), 0, 1 ) ); ?></span>
									<?php endif; ?>
									<span class="sr-related-badge"><?php echo esc_html( $config['label'] ); ?></span>
									<div class="sr-related-hov"><span><?php esc_html_e( 'View Piece', 'skyyrose-flagship' ); ?></span></div>
								</div>
								<div class="sr-related-body">
									<h3 class="sr-related-name"><?php echo esc_html( $rel_product->get_name() ); ?></h3>
									<span class="sr-related-price"><?php echo $rel_product->get_price_html(); // phpcs:ignore WordPress.Security.EscapeOutput ?></span>
								</div>
							</a>
						<?php endforeach; ?>
					</div>
				</div>
			</section>
		<?php endif; ?>

		<!-- COLLECTION CTA BANNER -->
		<section class="sr-cta-banner">
			<div class="sr-container sr-cta-inner">
				<div class="sr-cta-text">
					<p class="sr-cta-eye"><?php echo esc_html( $config['badge_text'] ); ?></p>
					<h2 class="sr-cta-title"><?php echo esc_html( $config['label'] ); ?></h2>
					<p class="sr-cta-tagline"><?php echo esc_html( $config['tagline'] ); ?></p>
				</div>
				<?php if ( $cat_link && ! is_wp_error( $cat_link ) ) : ?>
					<a href="<?php echo esc_url( $cat_link ); ?>" class="sr-cta-btn">
						<?php esc_html_e( 'Shop Full Collection', 'skyyrose-flagship' ); ?>
					</a>
				<?php endif; ?>
			</div>
		</section>

		<!-- RECENTLY VIEWED PRODUCTS (localStorage-driven, no server cost) -->
		<section class="sr-recently-viewed" aria-label="<?php esc_attr_e( 'Recently Viewed', 'skyyrose-flagship' ); ?>" style="display:none">
			<div class="sr-container">
				<div class="sr-rv-head">
					<h2 class="sr-rv-title"><?php esc_html_e( 'Recently Viewed', 'skyyrose-flagship' ); ?></h2>
				</div>
				<div class="sr-rv-grid"></div>
			</div>
		</section>

		<?php
		// Localize current product data for the recently-viewed JS tracker.
		$rv_data = array(
			'id'         => get_the_ID(),
			'name'       => get_the_title(),
			'url'        => get_permalink(),
			'image'      => $main_image ?: '',
			'price'      => wp_strip_all_tags( $price_html ),
			'collection' => $collection,
			'badge'      => $config['label'],
		);
		?>
		<script type="application/json" id="sr-rv-product"><?php echo wp_json_encode( $rv_data ); ?></script>

		<!-- STICKY ADD TO CART (mobile + scroll) -->
		<div class="sr-sticky-atc" id="srStickyATC" aria-hidden="true">
			<div class="sr-container sr-sticky-inner">
				<div class="sr-sticky-info">
					<span class="sr-sticky-name"><?php the_title(); ?></span>
					<span class="sr-sticky-price"><?php echo $price_html; // phpcs:ignore WordPress.Security.EscapeOutput ?></span>
				</div>
				<a href="#sr-atc-anchor" class="sr-sticky-btn"><?php esc_html_e( 'Add to Bag', 'skyyrose-flagship' ); ?></a>
			</div>
		</div>

		<?php
		/**
		 * Hook: woocommerce_after_single_product.
		 */
		do_action( 'woocommerce_after_single_product' );
		?>

	</main>

	<?php
endwhile;

/**
 * Hook: woocommerce_after_main_content.
 *
 * @hooked woocommerce_output_content_wrapper_end - 10
 */
do_action( 'woocommerce_after_main_content' );

get_footer( 'shop' );
