<?php
/**
 * WooCommerce Product Loop Card - Dark Luxury Design
 *
 * Overrides WooCommerce templates/content-product.php.
 * Used in shop archives and related products grids.
 *
 * @see     https://woocommerce.com/document/template-structure/
 * @package SkyyRose_Flagship
 * @since   2.0.0
 * @version 9.4.0
 */

defined( 'ABSPATH' ) || exit;

global $product;

// Check if the product is a valid WooCommerce product and ensure its visibility before proceeding.
if ( ! is_a( $product, WC_Product::class ) || ! $product->is_visible() ) {
	return;
}

$product_id    = $product->get_id();
$product_link  = get_permalink( $product_id );
$product_title = $product->get_name();
$product_price = $product->get_price_html();
$on_sale       = $product->is_on_sale();
$in_stock      = $product->is_in_stock();
$is_preorder   = function_exists( 'skyyrose_is_preorder' ) && skyyrose_is_preorder( $product_id );

// Determine collection from product categories for accent colors.
$collection_class = 'collection-signature';
$terms            = get_the_terms( $product_id, 'product_cat' );
if ( $terms && ! is_wp_error( $terms ) ) {
	foreach ( $terms as $term ) {
		$slug = $term->slug;
		if ( false !== strpos( $slug, 'black-rose' ) ) {
			$collection_class = 'collection-black-rose';
			break;
		}
		if ( false !== strpos( $slug, 'love-hurts' ) ) {
			$collection_class = 'collection-love-hurts';
			break;
		}
		if ( false !== strpos( $slug, 'signature' ) ) {
			$collection_class = 'collection-signature';
			break;
		}
	}
}
?>

<li <?php wc_product_class( 'skyy-product-card ' . esc_attr( $collection_class ), $product ); ?>>
	<div class="skyy-product-card__inner">

		<?php
		/**
		 * Hook: woocommerce_before_shop_loop_item.
		 *
		 * @hooked woocommerce_template_loop_product_link_open - 10
		 */
		do_action( 'woocommerce_before_shop_loop_item' );
		?>

		<div class="skyy-product-card__image-wrap">
			<a href="<?php echo esc_url( $product_link ); ?>"
			   class="skyy-product-card__image-link"
			   aria-label="<?php echo esc_attr( $product_title ); ?>">

				<?php if ( $is_preorder ) : ?>
					<span class="skyy-product-card__badge skyy-product-card__badge--preorder" style="background:#B76E79;">
						<?php esc_html_e( 'Pre-Order', 'skyyrose-flagship' ); ?>
					</span>
				<?php elseif ( $on_sale ) : ?>
					<span class="skyy-product-card__badge skyy-product-card__badge--sale">
						<?php esc_html_e( 'Sale', 'skyyrose-flagship' ); ?>
					</span>
				<?php endif; ?>

				<?php if ( ! $in_stock && ! $is_preorder ) : ?>
					<span class="skyy-product-card__badge skyy-product-card__badge--soldout">
						<?php esc_html_e( 'Sold Out', 'skyyrose-flagship' ); ?>
					</span>
				<?php endif; ?>

				<?php
				/**
				 * Hook: woocommerce_before_shop_loop_item_title.
				 *
				 * @hooked woocommerce_show_product_loop_sale_flash - 10
				 * @hooked woocommerce_template_loop_product_thumbnail - 10
				 */
				do_action( 'woocommerce_before_shop_loop_item_title' );
				?>

				<div class="skyy-product-card__overlay">
					<span class="skyy-product-card__quick-view">
						<?php esc_html_e( 'Quick View', 'skyyrose-flagship' ); ?>
					</span>
				</div>
			</a>

			<?php if ( $product->is_purchasable() && $in_stock ) : ?>
				<div class="skyy-product-card__actions">
					<?php woocommerce_template_loop_add_to_cart(); ?>
				</div>
			<?php endif; ?>
		</div>

		<div class="skyy-product-card__content">
			<a href="<?php echo esc_url( $product_link ); ?>" class="skyy-product-card__content-link">
				<?php
				/**
				 * Hook: woocommerce_shop_loop_item_title.
				 *
				 * @hooked woocommerce_template_loop_product_title - 10
				 */
				do_action( 'woocommerce_shop_loop_item_title' );
				?>

				<?php
				/**
				 * Hook: woocommerce_after_shop_loop_item_title.
				 *
				 * @hooked woocommerce_template_loop_rating - 5
				 * @hooked woocommerce_template_loop_price - 10
				 */
				do_action( 'woocommerce_after_shop_loop_item_title' );
				?>

				<?php if ( $product_price ) : ?>
					<div class="skyy-product-card__price">
						<?php echo $product_price; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- WC handles escaping. ?>
					</div>
				<?php endif; ?>

				<?php if ( $is_preorder ) :
					$edition_size = get_post_meta( $product_id, '_preorder_edition_size', true );
					$available    = get_post_meta( $product_id, '_preorder_available', true );
				?>
					<div class="skyy-product-card__preorder-info" style="font-size:11px;color:#B76E79;margin-top:4px;letter-spacing:0.5px;text-transform:uppercase;">
						<?php if ( $edition_size ) : ?>
							<?php echo esc_html( $edition_size ); ?> Edition
						<?php endif; ?>
						<?php if ( $available ) : ?>
							&middot; <?php echo esc_html( $available ); ?> left
						<?php endif; ?>
					</div>
				<?php endif; ?>
			</a>
		</div>

		<?php
		/**
		 * Hook: woocommerce_after_shop_loop_item.
		 *
		 * @hooked woocommerce_template_loop_product_link_close - 5
		 * @hooked woocommerce_template_loop_add_to_cart - 10
		 */
		do_action( 'woocommerce_after_shop_loop_item' );
		?>

	</div>
</li>
