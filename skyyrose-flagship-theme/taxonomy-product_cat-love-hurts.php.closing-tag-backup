<?php
/**
 * WooCommerce Product Category Archive: Love Hurts Collection
 * Static product grid with link to 3D castle experience
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) exit;

function skyyrose_love_hurts_archive_enqueue() {
    wp_enqueue_style( 'collection-love-hurts-css', get_template_directory_uri() . '/assets/css/collection-love-hurts.css', array(), '1.0.0-r182' );
    wp_enqueue_script( 'collection-love-hurts-js', get_template_directory_uri() . '/assets/js/collection-love-hurts.js', array(), '1.0.0-r182', true );
}
add_action( 'wp_enqueue_scripts', 'skyyrose_love_hurts_archive_enqueue' );

get_header();
?>

<div class="collection-archive love-hurts-collection">
    <div class="collection-hero">
        <div class="hero-content">
            <h1 class="collection-title">LOVE HURTS Collection</h1>
            <p class="collection-subtitle">Enchanted Castle Romance</p>
            <div class="hero-actions">
                <a href="<?php echo esc_url( home_url( '/love-hurts-3d/' ) ); ?>" class="btn-3d-experience">
                    <span class="icon">🏰</span>
                    Enter the Castle
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
