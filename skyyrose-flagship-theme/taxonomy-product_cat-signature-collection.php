<?php
/**
 * WooCommerce Product Category Archive: Signature Collection
 * Static product grid with link to 3D experience
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) exit;

function skyyrose_signature_archive_enqueue() {
    wp_enqueue_style( 'collection-signature-css', get_template_directory_uri() . '/assets/css/collection-signature.css', array(), '1.0.0-r182' );
    wp_enqueue_script( 'collection-signature-js', get_template_directory_uri() . '/assets/js/collection-signature.js', array(), '1.0.0-r182', true );
}
add_action( 'wp_enqueue_scripts', 'skyyrose_signature_archive_enqueue' );

get_header();
?>

<div class="collection-archive signature-collection">
    <!-- Hero Section with 3D Link -->
    <div class="collection-hero">
        <div class="hero-content">
            <h1 class="collection-title">SIGNATURE Collection</h1>
            <p class="collection-subtitle">Foundation of Luxury</p>
            <div class="hero-actions">
                <a href="<?php echo esc_url( home_url( '/signature-collection-3d/' ) ); ?>" class="btn-3d-experience">
                    <span class="icon">✨</span>
                    Explore in 3D
                </a>
            </div>
        </div>
    </div>

    <!-- Product Grid -->
    <div class="products-container">
        <?php
        if ( have_posts() ) :
            woocommerce_product_loop_start();
            
            while ( have_posts() ) :
                the_post();
                wc_get_template_part( 'content', 'product' );
            endwhile;
            
            woocommerce_product_loop_end();
            
            woocommerce_pagination();
        else :
            echo '<p class="woocommerce-info">' . esc_html__( 'No products found in this collection.', 'skyyrose-flagship' ) . '</p>';
        endif;
        ?>
    </div>
</div>

<?php get_footer(); ?>
