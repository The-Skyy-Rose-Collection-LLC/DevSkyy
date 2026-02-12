<?php
/**
 * Single Product Template
 * Custom single product page with enhanced design
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) exit;

function skyyrose_single_product_enqueue() {
    wp_enqueue_style( 'single-product-css', get_template_directory_uri() . '/assets/css/single-product.css', array(), '1.0.0' );
    wp_enqueue_script( 'single-product-js', get_template_directory_uri() . '/assets/js/single-product.js', array( 'jquery' ), '1.0.0', true );
}
add_action( 'wp_enqueue_scripts', 'skyyrose_single_product_enqueue' );

get_header( 'shop' );
?>

<div id="primary" class="content-area single-product-page">
    <main id="main" class="site-main">
        <?php
        while ( have_posts() ) :
            the_post();
            wc_get_template_part( 'content', 'single-product' );
        endwhile;
        ?>
    </main>
</div>

<?php
get_footer( 'shop' );
