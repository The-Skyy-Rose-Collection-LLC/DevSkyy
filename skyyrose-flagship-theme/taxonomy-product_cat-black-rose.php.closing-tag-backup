<?php
/**
 * WooCommerce Product Category Archive: Black Rose Collection
 * Static product grid with link to 3D garden experience
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) exit;

function skyyrose_black_rose_archive_enqueue() {
    wp_enqueue_style( 'collection-black-rose-css', get_template_directory_uri() . '/assets/css/collection-black-rose.css', array(), '1.0.0-r182' );
    wp_enqueue_script( 'collection-black-rose-js', get_template_directory_uri() . '/assets/js/collection-black-rose.js', array(), '1.0.0-r182', true );
}
add_action( 'wp_enqueue_scripts', 'skyyrose_black_rose_archive_enqueue' );

get_header();
?>

<div class="collection-archive black-rose-collection">
    <div class="collection-hero">
        <div class="hero-content">
            <h1 class="collection-title">BLACK ROSE Collection</h1>
            <p class="collection-subtitle">Gothic Garden Elegance</p>
            <div class="hero-actions">
                <a href="<?php echo esc_url( home_url( '/black-rose-3d/' ) ); ?>" class="btn-3d-experience">
                    <span class="icon">🌹</span>
                    Enter the Garden
                </a>
            </div>
        </div>
    </div>

    <div class="products-container">
        <?php
        if ( have_posts() ) :
            woocommerce_product_loop_start();
            while ( have_posts() ) : the_post();
                wc_get_template_part( 'content', 'product' );
            endwhile;
            woocommerce_product_loop_end();
            woocommerce_pagination();
        else :
            echo '<p class="woocommerce-info">' . esc_html__( 'No products found.', 'skyyrose-flagship' ) . '</p>';
        endif;
        ?>
    </div>
</div>

<?php get_footer(); ?>
