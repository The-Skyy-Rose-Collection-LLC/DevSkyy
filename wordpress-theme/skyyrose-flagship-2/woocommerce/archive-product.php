<?php
/**
 * Marketplace archive.
 *
 * @package SkyyRoseFlagship2
 */

defined( 'ABSPATH' ) || exit;

$archive_title = woocommerce_page_title( false );

get_header();
?>
<main id="primary" class="sr2-shop">
	<header class="sr2-shop-head">
		<div><p class="sr2-eyebrow"><?php esc_html_e( 'SkyyRose Marketplace', 'skyyrose-flagship-2' ); ?></p><h1><?php echo esc_html( $archive_title ); ?></h1></div>
		<p><?php esc_html_e( 'Limited pieces across four story worlds. Choose what carries yours.', 'skyyrose-flagship-2' ); ?></p>
	</header>
	<nav class="sr2-shop-worlds" aria-label="<?php esc_attr_e( 'Shop by collection', 'skyyrose-flagship-2' ); ?>">
		<a href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>"><?php esc_html_e( 'All', 'skyyrose-flagship-2' ); ?></a>
		<?php foreach ( skyyrose2_collections() as $slug => $collection ) : ?>
			<a data-collection="<?php echo esc_attr( $slug ); ?>" href="<?php echo esc_url( skyyrose2_collection_url( $slug ) ); ?>"><?php echo esc_html( $collection['name'] ); ?></a>
		<?php endforeach; ?>
	</nav>
	<section class="sr2-shop-loop" aria-label="<?php esc_attr_e( 'Products', 'skyyrose-flagship-2' ); ?>">
		<?php
		do_action( 'woocommerce_before_main_content' );
		if ( woocommerce_product_loop() ) {
			do_action( 'woocommerce_before_shop_loop' );
			woocommerce_product_loop_start();
			while ( have_posts() ) {
				the_post();
				do_action( 'woocommerce_shop_loop' );
				wc_get_template_part( 'content', 'product' );
			}
			woocommerce_product_loop_end();
			do_action( 'woocommerce_after_shop_loop' );
		} else {
			do_action( 'woocommerce_no_products_found' );
		}
		do_action( 'woocommerce_after_main_content' );
		?>
	</section>
</main>
<?php
get_footer();
