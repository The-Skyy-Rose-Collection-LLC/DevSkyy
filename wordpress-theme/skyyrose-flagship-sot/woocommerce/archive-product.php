<?php
defined( 'ABSPATH' ) || exit;
get_header();
?><main id="primary" class="srs-page"><header><p><?php esc_html_e( 'Marketplace', 'skyyrose-flagship-sot' ); ?></p><h1><?php woocommerce_page_title(); ?></h1></header>
<?php
if ( woocommerce_product_loop() ) :
	do_action( 'woocommerce_before_shop_loop' );
	woocommerce_product_loop_start();
	while ( have_posts() ) :
		the_post();
		wc_get_template_part( 'content', 'product' );
endwhile;
	woocommerce_product_loop_end();
	do_action( 'woocommerce_after_shop_loop' );
else :
	do_action( 'woocommerce_no_products_found' );
endif;
?>
</main>
<?php
get_footer();
