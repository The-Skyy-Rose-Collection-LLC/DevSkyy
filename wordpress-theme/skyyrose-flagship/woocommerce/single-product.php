<?php
/**
 * The Template for displaying all single products
 *
 * This template can be overridden by copying it to yourtheme/woocommerce/single-product.php.
 *
 * @package SkyyRose_Flagship
 * @since 2.0.0
 */

defined( 'ABSPATH' ) || exit;

get_header( 'shop' ); ?>

	<?php
		/**
		 * Hook: woocommerce_before_main_content.
		 */
		do_action( 'woocommerce_before_main_content' );
	?>

	<?php while ( have_posts() ) : ?>
		<?php the_post(); ?>

		<?php wc_get_template_part( 'content', 'single-product' ); ?>

	<?php endwhile; ?>

	<?php
		/**
		 * Hook: woocommerce_after_main_content.
		 */
		do_action( 'woocommerce_after_main_content' );
	?>

	<?php
		/**
		 * Hook: woocommerce_sidebar.
		 */
		do_action( 'woocommerce_sidebar' );
	?>

<?php
get_footer( 'shop' );
