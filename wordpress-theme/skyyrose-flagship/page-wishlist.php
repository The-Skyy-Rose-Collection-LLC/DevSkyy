<?php
/**
 * Template Name: Wishlist
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

get_header();
?>

<main id="primary" class="site-main wishlist-page">
	<div class="container">

		<header class="page-header">
			<h1 class="page-title"><?php esc_html_e( 'My Wishlist', 'skyyrose-flagship' ); ?></h1>
		</header>

		<?php
		$wishlist = skyyrose_get_wishlist_items();
		?>

		<?php if ( ! empty( $wishlist ) ) : ?>

			<div class="wishlist-actions">
				<button type="button" class="button alt wishlist-move-all" data-action="move-all">
					<?php esc_html_e( 'Move All to Cart', 'skyyrose-flagship' ); ?>
				</button>
				<button type="button" class="button wishlist-clear-all" data-action="clear-all">
					<?php esc_html_e( 'Clear Wishlist', 'skyyrose-flagship' ); ?>
				</button>
				<button type="button" class="button wishlist-share" data-action="share">
					<svg class="icon" width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
						<path d="M13 10.5C12.4 10.5 11.85 10.7 11.4 11.05L5.55 7.55C5.6 7.37 5.625 7.187 5.625 7C5.625 6.813 5.6 6.63 5.55 6.45L11.35 2.975C11.825 3.35 12.388 3.563 13 3.563C14.381 3.563 15.5 2.444 15.5 1.063C15.5 -0.319 14.381 -1.438 13 -1.438C11.619 -1.438 10.5 -0.319 10.5 1.063C10.5 1.25 10.525 1.432 10.575 1.613L4.775 5.088C4.3 4.712 3.738 4.5 3.125 4.5C1.744 4.5 0.625 5.619 0.625 7C0.625 8.381 1.744 9.5 3.125 9.5C3.738 9.5 4.3 9.287 4.775 8.912L10.6 12.425C10.55 12.593 10.525 12.768 10.525 12.95C10.525 14.281 11.606 15.362 12.938 15.362C14.269 15.362 15.35 14.281 15.35 12.95C15.35 11.619 14.269 10.538 12.938 10.538L13 10.5Z" fill="currentColor"/>
					</svg>
					<?php esc_html_e( 'Share Wishlist', 'skyyrose-flagship' ); ?>
				</button>
			</div>

			<div class="wishlist-grid products">
				<?php foreach ( $wishlist as $product_id ) : ?>
					<?php
					$product = wc_get_product( $product_id );
					if ( ! $product ) {
						continue;
					}
					?>
					<div class="product-card wishlist-item" data-product-id="<?php echo esc_attr( $product_id ); ?>">
						<div class="product-card-inner">

							<div class="product-image">
								<a href="<?php echo esc_url( $product->get_permalink() ); ?>">
									<?php echo $product->get_image( 'woocommerce_thumbnail' ); ?>
								</a>
								<button type="button" class="wishlist-remove" data-product-id="<?php echo esc_attr( $product_id ); ?>" title="<?php esc_attr_e( 'Remove from wishlist', 'skyyrose-flagship' ); ?>">
									<svg class="icon" width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
										<path d="M12.5 3.5L3.5 12.5M3.5 3.5L12.5 12.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
									</svg>
								</button>
							</div>

							<div class="product-info">
								<h3 class="product-title">
									<a href="<?php echo esc_url( $product->get_permalink() ); ?>">
										<?php echo esc_html( $product->get_name() ); ?>
									</a>
								</h3>

								<?php if ( $product->get_short_description() ) : ?>
									<div class="product-excerpt">
										<?php echo wp_kses_post( wp_trim_words( $product->get_short_description(), 15 ) ); ?>
									</div>
								<?php endif; ?>

								<div class="product-price">
									<?php echo $product->get_price_html(); ?>
								</div>

								<div class="product-meta">
									<?php if ( $product->is_in_stock() ) : ?>
										<span class="stock in-stock"><?php esc_html_e( 'In Stock', 'skyyrose-flagship' ); ?></span>
									<?php else : ?>
										<span class="stock out-of-stock"><?php esc_html_e( 'Out of Stock', 'skyyrose-flagship' ); ?></span>
									<?php endif; ?>
								</div>

								<div class="product-actions">
									<?php if ( $product->is_purchasable() && $product->is_in_stock() ) : ?>
										<button type="button" class="button alt wishlist-move-to-cart" data-product-id="<?php echo esc_attr( $product_id ); ?>">
											<?php esc_html_e( 'Move to Cart', 'skyyrose-flagship' ); ?>
										</button>
									<?php else : ?>
										<a href="<?php echo esc_url( $product->get_permalink() ); ?>" class="button">
											<?php esc_html_e( 'View Product', 'skyyrose-flagship' ); ?>
										</a>
									<?php endif; ?>
								</div>
							</div>

						</div>
					</div>
				<?php endforeach; ?>
			</div>

		<?php else : ?>

			<div class="wishlist-empty">
				<div class="wishlist-empty-icon">
					<svg width="80" height="80" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
						<path d="M40 70C55.464 70 68 57.464 68 42C68 26.536 55.464 14 40 14C24.536 14 12 26.536 12 42C12 57.464 24.536 70 40 70Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
						<path d="M40 26.667V42L48.889 46.444" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
						<path d="M58.333 20L68 10M22 20L12 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
					</svg>
				</div>
				<h2 class="wishlist-empty-title"><?php esc_html_e( 'Your Wishlist is Empty', 'skyyrose-flagship' ); ?></h2>
				<p class="wishlist-empty-text">
					<?php esc_html_e( 'Save your favorite items here to purchase later or keep track of items you love.', 'skyyrose-flagship' ); ?>
				</p>
				<div class="wishlist-empty-actions">
					<a href="<?php echo esc_url( get_permalink( wc_get_page_id( 'shop' ) ) ); ?>" class="button alt">
						<?php esc_html_e( 'Start Shopping', 'skyyrose-flagship' ); ?>
					</a>
				</div>
			</div>

		<?php endif; ?>

	</div>

	<!-- Toast Notification -->
	<div class="wishlist-toast" id="wishlist-toast" role="alert" aria-live="polite">
		<div class="wishlist-toast-content">
			<span class="wishlist-toast-icon"></span>
			<span class="wishlist-toast-message"></span>
		</div>
	</div>

</main>

<?php
get_sidebar();
get_footer();
