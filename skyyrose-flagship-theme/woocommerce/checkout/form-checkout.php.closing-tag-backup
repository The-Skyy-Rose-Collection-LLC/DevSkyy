<?php
/**
 * Checkout Form Template
 * Custom checkout page with enhanced design
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) exit;

function skyyrose_checkout_enqueue() {
    wp_enqueue_style( 'checkout-css', get_template_directory_uri() . '/assets/css/checkout.css', array(), '1.0.0' );
    wp_enqueue_script( 'checkout-js', get_template_directory_uri() . '/assets/js/checkout.js', array( 'jquery', 'wc-checkout' ), '1.0.0', true );
}
add_action( 'wp_enqueue_scripts', 'skyyrose_checkout_enqueue' );

do_action( 'woocommerce_before_checkout_form', $checkout );

if ( ! $checkout->is_registration_enabled() && $checkout->is_registration_required() && ! is_user_logged_in() ) {
    echo esc_html( apply_filters( 'woocommerce_checkout_must_be_logged_in_message', __( 'You must be logged in to checkout.', 'skyyrose-flagship' ) ) );
    return;
}

?>

<form name="checkout" method="post" class="checkout woocommerce-checkout" action="<?php echo esc_url( wc_get_checkout_url() ); ?>" enctype="multipart/form-data">

    <?php if ( $checkout->get_checkout_fields() ) : ?>

        <?php do_action( 'woocommerce_checkout_before_customer_details' ); ?>

        <div class="col2-set" id="customer_details">
            <div class="col-1">
                <?php do_action( 'woocommerce_checkout_billing' ); ?>
            </div>

            <div class="col-2">
                <?php do_action( 'woocommerce_checkout_shipping' ); ?>
            </div>
        </div>

        <?php do_action( 'woocommerce_checkout_after_customer_details' ); ?>

    <?php endif; ?>
    
    <?php do_action( 'woocommerce_checkout_before_order_review_heading' ); ?>
    
    <h3 id="order_review_heading"><?php esc_html_e( 'Your order', 'skyyrose-flagship' ); ?></h3>
    
    <?php do_action( 'woocommerce_checkout_before_order_review' ); ?>

    <div id="order_review" class="woocommerce-checkout-review-order">
        <?php do_action( 'woocommerce_checkout_order_review' ); ?>
    </div>

    <?php do_action( 'woocommerce_checkout_after_order_review' ); ?>

</form>

<?php do_action( 'woocommerce_after_checkout_form', $checkout ); ?>
