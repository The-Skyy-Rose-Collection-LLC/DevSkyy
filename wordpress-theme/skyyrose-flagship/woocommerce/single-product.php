<?php
/**
 * Single Product Page - Dark Luxury Design
 *
 * Overrides WooCommerce templates/single-product.php.
 * Features: sticky gallery, color/size selectors, quantity controls,
 * accordions, related products, collection-specific gradient overlay.
 *
 * @package SkyyRose_Flagship
 * @since   2.0.0
 * @version 9.5.0
 */

defined( 'ABSPATH' ) || exit;

get_header( 'shop' );

/**
 * Hook: woocommerce_before_main_content.
 *
 * @hooked woocommerce_output_content_wrapper - 10 (outputs opening divs for the content)
 * @hooked woocommerce_breadcrumb - 20 (removed by theme)
 */
do_action( 'woocommerce_before_main_content' );

while ( have_posts() ) :
	the_post();

	global $product;

	if ( ! is_a( $product, 'WC_Product' ) ) {
		continue;
	}

	$product_id   = $product->get_id();
	$gallery_ids  = $product->get_gallery_image_ids();
	$main_image   = $product->get_image_id();
	$all_images   = $main_image ? array_merge( array( $main_image ), $gallery_ids ) : $gallery_ids;
	$product_cats = get_the_terms( $product_id, 'product_cat' );

	// Determine collection for gradient overlay and accent color.
	$collection       = 'signature';
	$collection_class = 'collection-signature';
	if ( $product_cats && ! is_wp_error( $product_cats ) ) {
		foreach ( $product_cats as $cat ) {
			if ( false !== strpos( $cat->slug, 'black-rose' ) ) {
				$collection       = 'black-rose';
				$collection_class = 'collection-black-rose';
				break;
			}
			if ( false !== strpos( $cat->slug, 'love-hurts' ) ) {
				$collection       = 'love-hurts';
				$collection_class = 'collection-love-hurts';
				break;
			}
			if ( false !== strpos( $cat->slug, 'signature' ) ) {
				$collection       = 'signature';
				$collection_class = 'collection-signature';
				break;
			}
		}
	}

	// Get product attributes for color/size selectors.
	$color_attribute = $product->get_attribute( 'pa_color' );
	$size_attribute  = $product->get_attribute( 'pa_size' );
	$colors          = $color_attribute ? array_map( 'trim', explode( ',', $color_attribute ) ) : array();
	$sizes           = $size_attribute ? array_map( 'trim', explode( ',', $size_attribute ) ) : array();

	// Fallback sizes if none set.
	if ( empty( $sizes ) && $product->is_type( 'variable' ) ) {
		$available_variations = $product->get_available_variations();
		foreach ( $available_variations as $variation ) {
			if ( isset( $variation['attributes']['attribute_pa_size'] ) ) {
				$size_val = $variation['attributes']['attribute_pa_size'];
				if ( ! in_array( $size_val, $sizes, true ) ) {
					$sizes[] = $size_val;
				}
			}
		}
	}

	// Product meta for accordions.
	$product_details  = $product->get_description();
	$short_desc       = $product->get_short_description();
	$sizing_guide     = get_post_meta( $product_id, '_sizing_guide', true );
	$shipping_returns = get_post_meta( $product_id, '_shipping_returns', true );
	?>

	<div class="skyy-single-product <?php echo esc_attr( $collection_class ); ?>"
		 data-collection="<?php echo esc_attr( $collection ); ?>"
		 data-product-id="<?php echo esc_attr( $product_id ); ?>">

		<!-- Collection gradient overlay -->
		<div class="skyy-single-product__gradient-overlay" aria-hidden="true"></div>

		<?php
		/**
		 * Hook: woocommerce_before_single_product.
		 *
		 * @hooked woocommerce_output_all_notices - 10
		 */
		do_action( 'woocommerce_before_single_product' );
		?>

		<div class="skyy-single-product__container">

			<!-- GALLERY (Sticky) -->
			<div class="skyy-single-product__gallery" data-skyy-gallery>

				<div class="skyy-single-product__gallery-main">
					<?php if ( ! empty( $all_images ) ) : ?>
						<?php
						$main_src  = wp_get_attachment_image_url( $all_images[0], 'woocommerce_single' );
						$main_full = wp_get_attachment_image_url( $all_images[0], 'full' );
						?>
						<img id="skyy-gallery-main-img"
							 src="<?php echo esc_url( $main_src ); ?>"
							 data-full="<?php echo esc_url( $main_full ); ?>"
							 alt="<?php echo esc_attr( $product->get_name() ); ?>"
							 class="skyy-single-product__gallery-main-img" />
					<?php else : ?>
						<?php echo wp_kses_post( wc_placeholder_img( 'woocommerce_single' ) ); ?>
					<?php endif; ?>
				</div>

				<?php if ( count( $all_images ) > 1 ) : ?>
					<div class="skyy-single-product__gallery-thumbs">
						<?php foreach ( array_slice( $all_images, 0, 4 ) as $index => $image_id ) : ?>
							<?php
							$thumb_src = wp_get_attachment_image_url( $image_id, 'woocommerce_gallery_thumbnail' );
							$full_src  = wp_get_attachment_image_url( $image_id, 'woocommerce_single' );
							$full_url  = wp_get_attachment_image_url( $image_id, 'full' );
							$alt       = get_post_meta( $image_id, '_wp_attachment_image_alt', true );
							?>
							<button type="button"
									class="skyy-single-product__gallery-thumb<?php echo 0 === $index ? ' is-active' : ''; ?>"
									data-src="<?php echo esc_url( $full_src ); ?>"
									data-full="<?php echo esc_url( $full_url ); ?>"
									aria-label="<?php printf( esc_attr__( 'View image %d', 'skyyrose-flagship' ), $index + 1 ); ?>">
								<img src="<?php echo esc_url( $thumb_src ); ?>"
									 alt="<?php echo esc_attr( $alt ? $alt : $product->get_name() ); ?>"
									 loading="lazy" />
							</button>
						<?php endforeach; ?>
					</div>
				<?php endif; ?>

				<?php
				/**
				 * Hook: woocommerce_product_thumbnails.
				 */
				do_action( 'woocommerce_product_thumbnails' );
				?>
			</div>

			<!-- PRODUCT INFO PANEL -->
			<div class="skyy-single-product__info">

				<?php
				/**
				 * Hook: woocommerce_single_product_summary.
				 *
				 * @hooked woocommerce_template_single_title - 5
				 * @hooked woocommerce_template_single_rating - 10
				 * @hooked woocommerce_template_single_price - 10
				 * @hooked woocommerce_template_single_excerpt - 20
				 * @hooked woocommerce_template_single_add_to_cart - 30
				 * @hooked woocommerce_template_single_meta - 40
				 * @hooked woocommerce_template_single_sharing - 50
				 */
				?>

				<!-- Breadcrumb / Collection tag -->
				<div class="skyy-single-product__collection-tag">
					<?php if ( $product_cats && ! is_wp_error( $product_cats ) ) : ?>
						<a href="<?php echo esc_url( get_term_link( $product_cats[0] ) ); ?>"
						   class="skyy-single-product__collection-link">
							<?php echo esc_html( $product_cats[0]->name ); ?>
						</a>
					<?php endif; ?>
				</div>

				<!-- Title -->
				<h1 class="skyy-single-product__title">
					<?php echo esc_html( $product->get_name() ); ?>
				</h1>

				<!-- Price -->
				<div class="skyy-single-product__price">
					<?php echo wp_kses_post( $product->get_price_html() ); ?>
				</div>

				<!-- Short Description -->
				<?php if ( $short_desc ) : ?>
					<div class="skyy-single-product__description">
						<?php echo wp_kses_post( $short_desc ); ?>
					</div>
				<?php endif; ?>

				<!-- Rating -->
				<?php if ( wc_review_ratings_enabled() && $product->get_average_rating() ) : ?>
					<div class="skyy-single-product__rating">
						<?php woocommerce_template_single_rating(); ?>
					</div>
				<?php endif; ?>

				<form class="skyy-single-product__form cart"
					  action="<?php echo esc_url( apply_filters( 'woocommerce_add_to_cart_form_action', $product->get_permalink() ) ); ?>"
					  method="post"
					  enctype="multipart/form-data"
					  data-product_id="<?php echo esc_attr( $product_id ); ?>">

					<?php
					/**
					 * Hook: woocommerce_before_add_to_cart_form.
					 */
					do_action( 'woocommerce_before_add_to_cart_form' );
					?>

					<!-- COLOR SELECTOR -->
					<?php if ( ! empty( $colors ) ) : ?>
						<div class="skyy-single-product__option-group">
							<label class="skyy-single-product__option-label">
								<?php esc_html_e( 'Color', 'skyyrose-flagship' ); ?>
								<span class="skyy-single-product__option-selected" data-skyy-color-name>
									<?php echo esc_html( $colors[0] ); ?>
								</span>
							</label>
							<div class="skyy-single-product__color-swatches" role="radiogroup"
								 aria-label="<?php esc_attr_e( 'Color options', 'skyyrose-flagship' ); ?>">
								<?php foreach ( $colors as $idx => $color_name ) : ?>
									<?php
									$color_slug = sanitize_title( $color_name );
									$color_hex  = get_term_meta(
										get_term_by( 'slug', $color_slug, 'pa_color' ) ? get_term_by( 'slug', $color_slug, 'pa_color' )->term_id : 0,
										'color_hex',
										true
									);
									if ( ! $color_hex ) {
										// Fallback color map for common names.
										$color_map = array(
											'black'     => '#000000',
											'white'     => '#FFFFFF',
											'red'       => '#DC143C',
											'rose-gold' => '#B76E79',
											'gold'      => '#D4AF37',
											'silver'    => '#C0C0C0',
											'navy'      => '#1B1B3A',
											'mauve'     => '#D8A7B1',
											'crimson'   => '#DC143C',
										);
										$color_hex = isset( $color_map[ $color_slug ] ) ? $color_map[ $color_slug ] : '#666666';
									}
									?>
									<button type="button"
											class="skyy-single-product__color-swatch<?php echo 0 === $idx ? ' is-active' : ''; ?>"
											data-color="<?php echo esc_attr( $color_slug ); ?>"
											data-color-name="<?php echo esc_attr( $color_name ); ?>"
											style="background-color: <?php echo esc_attr( $color_hex ); ?>;"
											role="radio"
											aria-checked="<?php echo 0 === $idx ? 'true' : 'false'; ?>"
											aria-label="<?php echo esc_attr( $color_name ); ?>">
										<span class="screen-reader-text"><?php echo esc_html( $color_name ); ?></span>
									</button>
								<?php endforeach; ?>
							</div>
							<input type="hidden" name="attribute_pa_color"
								   value="<?php echo esc_attr( sanitize_title( $colors[0] ) ); ?>"
								   data-skyy-color-input />
						</div>
					<?php endif; ?>

					<!-- SIZE SELECTOR -->
					<?php if ( ! empty( $sizes ) ) : ?>
						<div class="skyy-single-product__option-group">
							<label class="skyy-single-product__option-label">
								<?php esc_html_e( 'Size', 'skyyrose-flagship' ); ?>
							</label>
							<div class="skyy-single-product__size-buttons" role="radiogroup"
								 aria-label="<?php esc_attr_e( 'Size options', 'skyyrose-flagship' ); ?>">
								<?php foreach ( $sizes as $idx => $size_name ) : ?>
									<button type="button"
											class="skyy-single-product__size-btn<?php echo 0 === $idx ? ' is-active' : ''; ?>"
											data-size="<?php echo esc_attr( sanitize_title( $size_name ) ); ?>"
											role="radio"
											aria-checked="<?php echo 0 === $idx ? 'true' : 'false'; ?>"
											aria-label="<?php echo esc_attr( strtoupper( $size_name ) ); ?>">
										<?php echo esc_html( strtoupper( $size_name ) ); ?>
									</button>
								<?php endforeach; ?>
							</div>
							<input type="hidden" name="attribute_pa_size"
								   value="<?php echo esc_attr( sanitize_title( $sizes[0] ) ); ?>"
								   data-skyy-size-input />
						</div>
					<?php endif; ?>

					<!-- QUANTITY CONTROLS -->
					<div class="skyy-single-product__option-group">
						<label class="skyy-single-product__option-label" for="skyy-quantity">
							<?php esc_html_e( 'Quantity', 'skyyrose-flagship' ); ?>
						</label>
						<div class="skyy-single-product__quantity-wrap">
							<button type="button" class="skyy-single-product__qty-btn skyy-single-product__qty-btn--minus"
									aria-label="<?php esc_attr_e( 'Decrease quantity', 'skyyrose-flagship' ); ?>">
								<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
									<path d="M3 8h10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
								</svg>
							</button>
							<input type="number"
								   id="skyy-quantity"
								   class="skyy-single-product__qty-input"
								   name="quantity"
								   value="1"
								   min="1"
								   max="<?php echo esc_attr( $product->get_max_purchase_quantity() > 0 ? $product->get_max_purchase_quantity() : 99 ); ?>"
								   step="1"
								   inputmode="numeric"
								   aria-label="<?php esc_attr_e( 'Product quantity', 'skyyrose-flagship' ); ?>" />
							<button type="button" class="skyy-single-product__qty-btn skyy-single-product__qty-btn--plus"
									aria-label="<?php esc_attr_e( 'Increase quantity', 'skyyrose-flagship' ); ?>">
								<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
									<path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
								</svg>
							</button>
						</div>
					</div>

					<?php
					/**
					 * Hook: woocommerce_before_add_to_cart_button.
					 */
					do_action( 'woocommerce_before_add_to_cart_button' );
					?>

					<!-- ADD TO CART BUTTON -->
					<?php if ( $product->is_purchasable() && $in_stock = $product->is_in_stock() ) : ?>
						<button type="submit"
								name="add-to-cart"
								value="<?php echo esc_attr( $product_id ); ?>"
								class="skyy-single-product__add-to-cart single_add_to_cart_button button alt">
							<span class="skyy-single-product__add-to-cart-text">
								<?php echo esc_html( $product->single_add_to_cart_text() ); ?>
							</span>
							<span class="skyy-single-product__add-to-cart-price">
								<?php echo wp_kses_post( $product->get_price_html() ); ?>
							</span>
						</button>
					<?php else : ?>
						<button type="button" class="skyy-single-product__add-to-cart is-disabled" disabled>
							<?php esc_html_e( 'Out of Stock', 'skyyrose-flagship' ); ?>
						</button>
					<?php endif; ?>

					<?php
					/**
					 * Hook: woocommerce_after_add_to_cart_button.
					 */
					do_action( 'woocommerce_after_add_to_cart_button' );

					/**
					 * Hook: woocommerce_after_add_to_cart_form.
					 */
					do_action( 'woocommerce_after_add_to_cart_form' );
					?>

					<?php if ( $product->is_type( 'variable' ) ) : ?>
						<input type="hidden" name="variation_id" value="0" data-skyy-variation-id />
						<input type="hidden" name="product_id" value="<?php echo esc_attr( $product_id ); ?>" />
					<?php endif; ?>

				</form>

				<!-- ACCORDIONS -->
				<div class="skyy-single-product__accordions" data-skyy-accordions>

					<!-- Details -->
					<div class="skyy-single-product__accordion">
						<button type="button"
								class="skyy-single-product__accordion-trigger"
								aria-expanded="false"
								aria-controls="skyy-accordion-details">
							<span><?php esc_html_e( 'Details', 'skyyrose-flagship' ); ?></span>
							<svg class="skyy-single-product__accordion-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
								<path d="M5 8l5 5 5-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
							</svg>
						</button>
						<div id="skyy-accordion-details"
							 class="skyy-single-product__accordion-panel"
							 role="region"
							 hidden>
							<div class="skyy-single-product__accordion-content">
								<?php if ( $product_details ) : ?>
									<?php echo wp_kses_post( $product_details ); ?>
								<?php else : ?>
									<p><?php esc_html_e( 'Product details coming soon.', 'skyyrose-flagship' ); ?></p>
								<?php endif; ?>
							</div>
						</div>
					</div>

					<!-- Sizing Guide -->
					<div class="skyy-single-product__accordion">
						<button type="button"
								class="skyy-single-product__accordion-trigger"
								aria-expanded="false"
								aria-controls="skyy-accordion-sizing">
							<span><?php esc_html_e( 'Sizing Guide', 'skyyrose-flagship' ); ?></span>
							<svg class="skyy-single-product__accordion-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
								<path d="M5 8l5 5 5-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
							</svg>
						</button>
						<div id="skyy-accordion-sizing"
							 class="skyy-single-product__accordion-panel"
							 role="region"
							 hidden>
							<div class="skyy-single-product__accordion-content">
								<?php if ( $sizing_guide ) : ?>
									<?php echo wp_kses_post( $sizing_guide ); ?>
								<?php else : ?>
									<table class="skyy-sizing-table">
										<thead>
											<tr>
												<th><?php esc_html_e( 'Size', 'skyyrose-flagship' ); ?></th>
												<th><?php esc_html_e( 'Chest', 'skyyrose-flagship' ); ?></th>
												<th><?php esc_html_e( 'Waist', 'skyyrose-flagship' ); ?></th>
												<th><?php esc_html_e( 'Length', 'skyyrose-flagship' ); ?></th>
											</tr>
										</thead>
										<tbody>
											<tr><td>S</td><td>36"</td><td>28"</td><td>27"</td></tr>
											<tr><td>M</td><td>38"</td><td>30"</td><td>28"</td></tr>
											<tr><td>L</td><td>40"</td><td>32"</td><td>29"</td></tr>
											<tr><td>XL</td><td>42"</td><td>34"</td><td>30"</td></tr>
											<tr><td>XXL</td><td>44"</td><td>36"</td><td>31"</td></tr>
										</tbody>
									</table>
								<?php endif; ?>
							</div>
						</div>
					</div>

					<!-- Shipping & Returns -->
					<div class="skyy-single-product__accordion">
						<button type="button"
								class="skyy-single-product__accordion-trigger"
								aria-expanded="false"
								aria-controls="skyy-accordion-shipping">
							<span><?php esc_html_e( 'Shipping & Returns', 'skyyrose-flagship' ); ?></span>
							<svg class="skyy-single-product__accordion-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
								<path d="M5 8l5 5 5-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
							</svg>
						</button>
						<div id="skyy-accordion-shipping"
							 class="skyy-single-product__accordion-panel"
							 role="region"
							 hidden>
							<div class="skyy-single-product__accordion-content">
								<?php if ( $shipping_returns ) : ?>
									<?php echo wp_kses_post( $shipping_returns ); ?>
								<?php else : ?>
									<ul>
										<li><?php esc_html_e( 'Free shipping on orders over $150', 'skyyrose-flagship' ); ?></li>
										<li><?php esc_html_e( 'Standard shipping: 5-7 business days', 'skyyrose-flagship' ); ?></li>
										<li><?php esc_html_e( 'Express shipping: 2-3 business days', 'skyyrose-flagship' ); ?></li>
										<li><?php esc_html_e( 'Returns accepted within 30 days', 'skyyrose-flagship' ); ?></li>
										<li><?php esc_html_e( 'Items must be unworn with original tags', 'skyyrose-flagship' ); ?></li>
									</ul>
								<?php endif; ?>
							</div>
						</div>
					</div>

				</div>

				<?php
				/**
				 * Hook: woocommerce_single_product_summary.
				 */
				do_action( 'woocommerce_single_product_summary' );
				?>

			</div><!-- .skyy-single-product__info -->

		</div><!-- .skyy-single-product__container -->

		<!-- RELATED PRODUCTS: 4-card grid -->
		<?php
		$related_ids = wc_get_related_products( $product_id, 4 );
		if ( ! empty( $related_ids ) ) :
			?>
			<section class="skyy-single-product__related" aria-label="<?php esc_attr_e( 'Related Products', 'skyyrose-flagship' ); ?>">
				<div class="skyy-single-product__related-container">
					<h2 class="skyy-single-product__related-title">
						<?php esc_html_e( 'You May Also Like', 'skyyrose-flagship' ); ?>
					</h2>
					<div class="skyy-single-product__related-grid">
						<?php
						$related_products = array_map( 'wc_get_product', $related_ids );
						foreach ( $related_products as $related_product ) :
							if ( ! $related_product || ! $related_product->is_visible() ) {
								continue;
							}
							$GLOBALS['product'] = $related_product; // phpcs:ignore WordPress.WP.GlobalVariablesOverride.Prohibited
							setup_postdata( $related_product->get_id() );
							wc_get_template_part( 'content', 'product' );
						endforeach;
						wp_reset_postdata();
						$GLOBALS['product'] = $product; // phpcs:ignore WordPress.WP.GlobalVariablesOverride.Prohibited
						?>
					</div>
				</div>
			</section>
		<?php endif; ?>

		<?php
		/**
		 * Hook: woocommerce_after_single_product.
		 */
		do_action( 'woocommerce_after_single_product' );
		?>

		<?php get_template_part( 'template-parts/cinematic-toggle' ); ?>

	</div><!-- .skyy-single-product -->

	<?php
endwhile;

/**
 * Hook: woocommerce_after_main_content.
 *
 * @hooked woocommerce_output_content_wrapper_end - 10 (outputs closing divs for the content)
 */
do_action( 'woocommerce_after_main_content' );

get_footer( 'shop' );
