<?php
/**
 * Front Page: Featured Products
 *
 * WooCommerce product grid with static fallback. Uses a single shared
 * fallback product array (consolidating previously duplicated data).
 *
 * @package SkyyRose_Flagship
 * @since   3.2.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Static fallback product data — sourced from the centralized catalog
 * (inc/product-catalog.php) to guarantee price/name consistency.
 * Used when WooCommerce has no featured products or is not active.
 */
$featured_skus = array( 'br-006', 'lh-001', 'sg-001', 'sg-008' );
$badge_map     = array(
	'br-006' => array( __( 'Pre-Order', 'skyyrose-flagship' ), 'product-card__badge--limited' ),
	'lh-001' => array( __( 'Pre-Order', 'skyyrose-flagship' ), 'product-card__badge--limited' ),
	'sg-001' => array( __( 'Pre-Order', 'skyyrose-flagship' ), 'product-card__badge--limited' ),
	'sg-008' => array( __( 'Pre-Order', 'skyyrose-flagship' ), 'product-card__badge--limited' ),
);
$collection_labels = array(
	'black-rose' => __( 'Black Rose', 'skyyrose-flagship' ),
	'love-hurts' => __( 'Love Hurts', 'skyyrose-flagship' ),
	'signature'  => __( 'Signature', 'skyyrose-flagship' ),
);

$fallback_products = array();
foreach ( $featured_skus as $fsku ) {
	$p = skyyrose_get_product( $fsku );
	if ( ! $p ) {
		continue;
	}
	$badge_info          = isset( $badge_map[ $fsku ] ) ? $badge_map[ $fsku ] : array( '', '' );
	$fallback_products[] = array(
		'badge'      => $badge_info[0],
		'badge_cls'  => $badge_info[1],
		'collection' => isset( $collection_labels[ $p['collection'] ] ) ? $collection_labels[ $p['collection'] ] : $p['collection'],
		'name'       => $p['name'],
		'desc'       => $p['description'],
		'price'      => skyyrose_format_price( $p ),
		'rating'     => 5,
		'reviews'    => 0,
		'sku'        => $fsku,
	);
}
?>

<section class="featured" aria-labelledby="featured-heading">
	<div class="featured__header section-header">
		<span class="section-header__label">
			<?php esc_html_e( 'Featured', 'skyyrose-flagship' ); ?>
		</span>
		<h2 class="section-header__title" id="featured-heading">
			<?php esc_html_e( 'New Arrivals', 'skyyrose-flagship' ); ?>
		</h2>
		<p class="section-header__subtitle">
			<?php esc_html_e( 'The latest additions to our collections, each piece crafted with intention.', 'skyyrose-flagship' ); ?>
		</p>
	</div>

	<div class="featured__grid">
		<?php
		$has_woo_products = false;

		if ( class_exists( 'WooCommerce' ) ) :

			$featured_args = array(
				'post_type'      => 'product',
				'posts_per_page' => 4,
				'post_status'    => 'publish',
				'meta_key'       => 'total_sales',
				'orderby'        => 'meta_value_num',
				'order'          => 'DESC',
				'tax_query'      => array(
					array(
						'taxonomy' => 'product_visibility',
						'field'    => 'name',
						'terms'    => 'featured',
					),
				),
			);

			$featured_query = new WP_Query( $featured_args );

			// Fallback: if no featured products, get latest products.
			if ( ! $featured_query->have_posts() ) {
				$featured_args = array(
					'post_type'      => 'product',
					'posts_per_page' => 4,
					'post_status'    => 'publish',
					'orderby'        => 'date',
					'order'          => 'DESC',
				);
				$featured_query = new WP_Query( $featured_args );
			}

			if ( $featured_query->have_posts() ) :
				$has_woo_products = true;

				while ( $featured_query->have_posts() ) :
					$featured_query->the_post();
					global $product;

					if ( ! $product ) {
						continue;
					}

					// Determine badge type.
					$badge_text  = '';
					$badge_class = '';
					if ( $product->is_on_sale() ) {
						$badge_text  = __( 'Sale', 'skyyrose-flagship' );
						$badge_class = 'product-card__badge--sale';
					} elseif ( $product->get_date_created() ) {
						$created   = $product->get_date_created()->getTimestamp();
						$two_weeks = strtotime( '-14 days' );
						if ( $created > $two_weeks ) {
							$badge_text  = __( 'New', 'skyyrose-flagship' );
							$badge_class = 'product-card__badge--new';
						}
					}
					if ( ! $product->is_in_stock() ) {
						$badge_text  = __( 'Sold Out', 'skyyrose-flagship' );
						$badge_class = 'product-card__badge--sold-out';
					}
					if ( $product->managing_stock() && $product->get_stock_quantity() <= 5 && $product->get_stock_quantity() > 0 ) {
						$badge_text  = __( 'Limited', 'skyyrose-flagship' );
						$badge_class = 'product-card__badge--limited';
					}

					// Get collection / category.
					$categories      = get_the_terms( get_the_ID(), 'product_cat' );
					$collection_name = '';
					if ( $categories && ! is_wp_error( $categories ) ) {
						$collection_name = $categories[0]->name;
					}

					// Get average rating.
					$average_rating = $product->get_average_rating();
					$review_count   = $product->get_review_count();

					// Get short description.
					$short_desc = $product->get_short_description();
					?>
					<article class="product-card js-scroll-reveal" aria-label="<?php echo esc_attr( get_the_title() ); ?>">
						<?php if ( $badge_text ) : ?>
							<span class="product-card__badge <?php echo esc_attr( $badge_class ); ?>">
								<?php echo esc_html( $badge_text ); ?>
							</span>
						<?php endif; ?>

						<a href="<?php the_permalink(); ?>" class="product-card__image-link">
							<div class="product-card__image">
								<?php
								if ( has_post_thumbnail() ) {
									the_post_thumbnail(
										'woocommerce_thumbnail',
										array(
											'class'   => 'product-card__img',
											'loading' => 'lazy',
											'alt'     => esc_attr( get_the_title() ),
										)
									);
								} else {
									?>
									<div class="product-card__placeholder" aria-hidden="true"></div>
									<?php
								}
								?>
							</div>
						</a>

						<div class="product-card__actions" aria-label="<?php esc_attr_e( 'Quick actions', 'skyyrose-flagship' ); ?>">
							<a href="<?php the_permalink(); ?>" class="product-card__action-btn" aria-label="<?php esc_attr_e( 'Quick View', 'skyyrose-flagship' ); ?>" title="<?php esc_attr_e( 'Quick View', 'skyyrose-flagship' ); ?>">
								<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
									<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
									<circle cx="12" cy="12" r="3"/>
								</svg>
							</a>
							<button class="product-card__action-btn js-wishlist-btn" data-product-id="<?php echo esc_attr( get_the_ID() ); ?>" aria-label="<?php esc_attr_e( 'Add to Wishlist', 'skyyrose-flagship' ); ?>" title="<?php esc_attr_e( 'Add to Wishlist', 'skyyrose-flagship' ); ?>" type="button">
								<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
									<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
								</svg>
							</button>
							<?php if ( $product->is_in_stock() ) : ?>
								<button class="product-card__action-btn js-add-to-cart" data-product-id="<?php echo esc_attr( get_the_ID() ); ?>" aria-label="<?php esc_attr_e( 'Add to Cart', 'skyyrose-flagship' ); ?>" title="<?php esc_attr_e( 'Add to Cart', 'skyyrose-flagship' ); ?>" type="button">
									<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
										<path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/>
										<path d="M3 6h18"/>
										<path d="M16 10a4 4 0 0 1-8 0"/>
									</svg>
								</button>
							<?php endif; ?>
						</div>

						<div class="product-card__info">
							<?php if ( $collection_name ) : ?>
								<p class="product-card__collection">
									<?php echo esc_html( $collection_name ); ?>
								</p>
							<?php endif; ?>
							<h3 class="product-card__name">
								<a href="<?php the_permalink(); ?>">
									<?php the_title(); ?>
								</a>
							</h3>

							<?php if ( $short_desc ) : ?>
								<p class="product-card__desc">
									<?php echo esc_html( wp_trim_words( wp_strip_all_tags( $short_desc ), 15, '...' ) ); ?>
								</p>
							<?php endif; ?>

							<?php if ( $average_rating > 0 ) : ?>
								<div class="product-card__rating" aria-label="<?php echo esc_attr( sprintf( __( 'Rated %s out of 5', 'skyyrose-flagship' ), $average_rating ) ); ?>">
									<?php
									for ( $i = 1; $i <= 5; $i++ ) :
										$star_class = $i <= round( $average_rating ) ? 'product-card__star--filled' : 'product-card__star--empty';
										?>
										<svg class="product-card__star <?php echo esc_attr( $star_class ); ?>" width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false">
											<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
										</svg>
									<?php endfor; ?>
									<span class="product-card__review-count">
										<?php
										/* translators: %d: number of reviews */
										echo esc_html( sprintf( _n( '(%d)', '(%d)', $review_count, 'skyyrose-flagship' ), $review_count ) );
										?>
									</span>
								</div>
							<?php endif; ?>

							<div class="product-card__price-row">
								<p class="product-card__price">
									<?php echo wp_kses_post( $product->get_price_html() ); ?>
								</p>
							</div>

							<div class="product-card__buttons">
								<a href="<?php the_permalink(); ?>" class="btn btn--sm btn--primary">
									<?php esc_html_e( 'Shop Now', 'skyyrose-flagship' ); ?>
								</a>
								<a href="<?php the_permalink(); ?>" class="btn btn--sm btn--ghost">
									<?php esc_html_e( 'Quick View', 'skyyrose-flagship' ); ?>
								</a>
							</div>
						</div>
					</article>
				<?php endwhile; ?>
				<?php wp_reset_postdata(); ?>

			<?php endif; ?>
		<?php endif; ?>

		<?php
		// Static fallback: render when WooCommerce is missing or has no products.
		if ( ! $has_woo_products ) :
			foreach ( $fallback_products as $fp ) :
				$product_url = home_url( '/product/' . sanitize_title( $fp['name'] ) . '/' );
				?>
				<article class="product-card js-scroll-reveal" aria-label="<?php echo esc_attr( $fp['name'] ); ?>">
					<?php if ( $fp['badge'] ) : ?>
						<span class="product-card__badge <?php echo esc_attr( $fp['badge_cls'] ); ?>">
							<?php echo esc_html( $fp['badge'] ); ?>
						</span>
					<?php endif; ?>

					<a href="<?php echo esc_url( $product_url ); ?>" class="product-card__image-link">
						<div class="product-card__image">
							<div class="product-card__placeholder product-card__placeholder--<?php echo esc_attr( $fp['sku'] ); ?>" aria-hidden="true"></div>
						</div>
					</a>

					<div class="product-card__actions" aria-label="<?php esc_attr_e( 'Quick actions', 'skyyrose-flagship' ); ?>">
						<button class="product-card__action-btn" aria-label="<?php esc_attr_e( 'Quick View', 'skyyrose-flagship' ); ?>" type="button">
							<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
								<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
								<circle cx="12" cy="12" r="3"/>
							</svg>
						</button>
						<button class="product-card__action-btn" aria-label="<?php esc_attr_e( 'Add to Wishlist', 'skyyrose-flagship' ); ?>" type="button">
							<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
								<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
							</svg>
						</button>
						<button class="product-card__action-btn" aria-label="<?php esc_attr_e( 'Add to Cart', 'skyyrose-flagship' ); ?>" type="button">
							<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
								<path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/>
								<path d="M3 6h18"/>
								<path d="M16 10a4 4 0 0 1-8 0"/>
							</svg>
						</button>
					</div>

					<div class="product-card__info">
						<p class="product-card__collection">
							<?php echo esc_html( $fp['collection'] ); ?>
						</p>
						<h3 class="product-card__name">
							<a href="<?php echo esc_url( $product_url ); ?>">
								<?php echo esc_html( $fp['name'] ); ?>
							</a>
						</h3>
						<p class="product-card__desc">
							<?php echo esc_html( $fp['desc'] ); ?>
						</p>
						<?php if ( ! empty( $fp['rating'] ) ) : ?>
							<div class="product-card__rating" aria-label="<?php echo esc_attr( sprintf( __( 'Rated %d out of 5', 'skyyrose-flagship' ), $fp['rating'] ) ); ?>">
								<?php
								for ( $i = 1; $i <= 5; $i++ ) :
									$star_class = $i <= $fp['rating'] ? 'product-card__star--filled' : 'product-card__star--empty';
									?>
									<svg class="product-card__star <?php echo esc_attr( $star_class ); ?>" width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false">
										<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
									</svg>
								<?php endfor; ?>
								<span class="product-card__review-count">
									<?php echo esc_html( '(' . $fp['reviews'] . ')' ); ?>
								</span>
							</div>
						<?php endif; ?>
						<p class="product-card__price">
							<?php echo esc_html( $fp['price'] ); ?>
						</p>
						<div class="product-card__buttons">
							<a href="<?php echo esc_url( $product_url ); ?>" class="btn btn--sm btn--primary">
								<?php esc_html_e( 'Shop Now', 'skyyrose-flagship' ); ?>
							</a>
							<a href="<?php echo esc_url( $product_url ); ?>" class="btn btn--sm btn--ghost">
								<?php esc_html_e( 'Quick View', 'skyyrose-flagship' ); ?>
							</a>
						</div>
					</div>
				</article>
			<?php endforeach; ?>
		<?php endif; ?>
	</div>
</section>
