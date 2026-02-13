<?php
/**
 * The template for displaying product content within loops
 *
 * This template can be overridden by copying it to yourtheme/woocommerce/content-product.php.
 *
 * @package SkyyRose_Flagship
 * @since 2.0.0
 */

defined( 'ABSPATH' ) || exit;

global $product;

// Ensure visibility.
if ( empty( $product ) || ! $product->is_visible() ) {
	return;
}
?>
<li <?php wc_product_class( 'skyyrose-product-card', $product ); ?>>
	<div class="product-card-inner">
		<?php
		/**
		 * Hook: woocommerce_before_shop_loop_item.
		 */
		do_action( 'woocommerce_before_shop_loop_item' );
		?>

		<div class="product-card-image">
			<a href="<?php the_permalink(); ?>">
				<?php
				/**
				 * Hook: woocommerce_before_shop_loop_item_title.
				 *
				 * @hooked woocommerce_show_product_loop_sale_flash - 10
				 * @hooked woocommerce_template_loop_product_thumbnail - 10
				 */
				do_action( 'woocommerce_before_shop_loop_item_title' );
				?>
			</a>

			<?php
			// Add to cart button overlay
			if ( $product->is_purchasable() && $product->is_in_stock() ) {
				echo '<div class="product-card-actions">';
				woocommerce_template_loop_add_to_cart();
				echo '</div>';
			}
			?>
		</div>

		<div class="product-card-content">
			<?php
			/**
			 * Hook: woocommerce_shop_loop_item_title.
			 *
			 * @hooked woocommerce_template_loop_product_title - 10
			 */
			do_action( 'woocommerce_shop_loop_item_title' );

			/**
			 * Hook: woocommerce_after_shop_loop_item_title.
			 *
			 * @hooked woocommerce_template_loop_rating - 5
			 * @hooked woocommerce_template_loop_price - 10
			 */
			do_action( 'woocommerce_after_shop_loop_item_title' );
			?>
		</div>

		<?php
		/**
		 * Hook: woocommerce_after_shop_loop_item.
		 */
		do_action( 'woocommerce_after_shop_loop_item' );
		?>
	</div>
</li>

<style>
/* SkyyRose Product Card Styling */
.skyyrose-product-card {
	background: var(--white);
	border-radius: var(--radius-lg);
	overflow: hidden;
	transition: all var(--transition-luxury);
	box-shadow: var(--shadow-md);
	list-style: none;
}

.skyyrose-product-card:hover {
	transform: translateY(-12px);
	box-shadow: var(--shadow-xl), var(--shadow-rose-glow);
}

.product-card-inner {
	position: relative;
}

.product-card-image {
	position: relative;
	width: 100%;
	height: 350px;
	overflow: hidden;
	background: var(--off-white);
}

.product-card-image img {
	width: 100%;
	height: 100%;
	object-fit: cover;
	transition: transform var(--transition-luxury);
}

.skyyrose-product-card:hover .product-card-image img {
	transform: scale(1.1);
}

.product-card-actions {
	position: absolute;
	bottom: var(--space-md);
	left: var(--space-md);
	right: var(--space-md);
	opacity: 0;
	transform: translateY(10px);
	transition: all var(--transition-luxury);
}

.skyyrose-product-card:hover .product-card-actions {
	opacity: 1;
	transform: translateY(0);
}

.product-card-actions .button {
	width: 100%;
	background: var(--gradient-rose-gold);
	color: var(--white);
	border: none;
	padding: var(--space-md) var(--space-lg);
	font-weight: var(--weight-semibold);
	border-radius: var(--radius-md);
	cursor: pointer;
	transition: all var(--transition-base);
}

.product-card-actions .button:hover {
	transform: translateY(-2px);
	box-shadow: var(--shadow-lg);
}

.product-card-content {
	padding: var(--space-xl);
}

.product-card-content .woocommerce-loop-product__title {
	font-size: var(--text-lg);
	color: var(--dark-gray);
	margin-bottom: var(--space-sm);
	transition: color var(--transition-base);
}

.skyyrose-product-card:hover .woocommerce-loop-product__title {
	color: var(--rose-gold);
}

.product-card-content .price {
	font-size: var(--text-2xl);
	color: var(--rose-gold);
	font-weight: var(--weight-bold);
	margin-top: var(--space-md);
}

.product-card-content .price del {
	font-size: var(--text-lg);
	color: var(--medium-gray);
	opacity: 0.7;
	margin-right: var(--space-sm);
}

.onsale {
	position: absolute;
	top: var(--space-md);
	right: var(--space-md);
	background: var(--gradient-rose-gold);
	color: var(--white);
	padding: var(--space-xs) var(--space-md);
	font-size: var(--text-xs);
	font-weight: var(--weight-bold);
	text-transform: uppercase;
	border-radius: var(--radius-full);
	z-index: 1;
}
</style>
