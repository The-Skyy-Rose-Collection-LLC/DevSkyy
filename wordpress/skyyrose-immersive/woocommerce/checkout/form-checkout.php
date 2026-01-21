<?php
/**
 * SkyyRose Immersive Checkout Form
 *
 * Streamlined luxury checkout experience
 *
 * @package SkyyRose_Immersive
 */

defined('ABSPATH') || exit;

do_action('woocommerce_before_checkout_form', $checkout);

// If checkout registration is disabled and not logged in, the user cannot checkout.
if (!$checkout->is_registration_enabled() && $checkout->is_registration_required() && !is_user_logged_in()) {
    echo esc_html(apply_filters('woocommerce_checkout_must_be_logged_in_message', __('You must be logged in to checkout.', 'woocommerce')));
    return;
}
?>

<style>
    :root {
        --co-rose-gold: #B76E79;
        --co-obsidian: #1A1A1A;
        --co-champagne: #F7E7CE;
        --co-white: #FFFFFF;
        --co-gray: #666666;
        --co-light: #f8f8f8;
        --co-success: #28a745;
        --co-error: #dc3545;
    }

    .skyyrose-checkout {
        background: var(--co-white);
        min-height: 100vh;
    }

    .checkout-header {
        background: var(--co-obsidian);
        padding: 20px 5%;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .checkout-header .logo {
        font-size: 1.5rem;
        color: var(--co-rose-gold);
        font-weight: 300;
        letter-spacing: 3px;
        text-decoration: none;
    }
    .checkout-header .secure-badge {
        display: flex;
        align-items: center;
        gap: 8px;
        color: white;
        font-size: 0.85rem;
    }
    .checkout-header .secure-badge svg {
        width: 18px;
        height: 18px;
        fill: var(--co-success);
    }

    /* Progress Steps */
    .checkout-progress {
        display: flex;
        justify-content: center;
        padding: 40px 5%;
        background: var(--co-light);
        border-bottom: 1px solid #eee;
    }
    .progress-steps {
        display: flex;
        align-items: center;
        gap: 20px;
    }
    .progress-step {
        display: flex;
        align-items: center;
        gap: 10px;
        color: var(--co-gray);
    }
    .progress-step.active {
        color: var(--co-rose-gold);
    }
    .progress-step.completed {
        color: var(--co-success);
    }
    .step-number {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        border: 2px solid currentColor;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.9rem;
        font-weight: 600;
    }
    .progress-step.active .step-number {
        background: var(--co-rose-gold);
        border-color: var(--co-rose-gold);
        color: white;
    }
    .progress-step.completed .step-number {
        background: var(--co-success);
        border-color: var(--co-success);
        color: white;
    }
    .progress-connector {
        width: 60px;
        height: 2px;
        background: #ddd;
    }
    .progress-connector.completed {
        background: var(--co-success);
    }

    /* Checkout Container */
    .checkout-container {
        display: grid;
        grid-template-columns: 1fr 450px;
        gap: 60px;
        max-width: 1400px;
        margin: 0 auto;
        padding: 50px 5%;
    }

    /* Form Sections */
    .checkout-form-section {
        margin-bottom: 40px;
    }
    .checkout-form-section h3 {
        font-size: 1.3rem;
        font-weight: 500;
        color: var(--co-obsidian);
        margin: 0 0 25px;
        padding-bottom: 15px;
        border-bottom: 2px solid var(--co-obsidian);
    }

    /* Form Fields */
    .woocommerce-billing-fields__field-wrapper,
    .woocommerce-shipping-fields__field-wrapper {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
    }

    .form-row {
        margin-bottom: 0;
    }
    .form-row-wide {
        grid-column: span 2;
    }
    .form-row-first,
    .form-row-last {
        grid-column: span 1;
    }

    .form-row label {
        display: block;
        font-size: 0.9rem;
        font-weight: 500;
        color: var(--co-obsidian);
        margin-bottom: 8px;
    }
    .form-row label .required {
        color: var(--co-rose-gold);
    }
    .form-row label .optional {
        color: var(--co-gray);
        font-weight: 400;
        font-size: 0.85rem;
    }

    .form-row input[type="text"],
    .form-row input[type="email"],
    .form-row input[type="tel"],
    .form-row input[type="password"],
    .form-row select,
    .form-row textarea {
        width: 100%;
        padding: 14px 18px;
        border: 1px solid #ddd;
        font-size: 1rem;
        transition: border-color 0.3s, box-shadow 0.3s;
        background: white;
    }
    .form-row input:focus,
    .form-row select:focus,
    .form-row textarea:focus {
        outline: none;
        border-color: var(--co-rose-gold);
        box-shadow: 0 0 0 3px rgba(183, 110, 121, 0.1);
    }
    .form-row.woocommerce-invalid input,
    .form-row.woocommerce-invalid select {
        border-color: var(--co-error);
    }
    .form-row.woocommerce-validated input,
    .form-row.woocommerce-validated select {
        border-color: var(--co-success);
    }

    /* Select2 Styling */
    .select2-container--default .select2-selection--single {
        height: 50px;
        border: 1px solid #ddd;
        padding: 10px 18px;
    }
    .select2-container--default .select2-selection--single .select2-selection__rendered {
        line-height: 28px;
    }
    .select2-container--default .select2-selection--single .select2-selection__arrow {
        height: 48px;
    }

    /* Checkbox Styling */
    .form-row input[type="checkbox"] {
        width: auto;
        margin-right: 10px;
    }
    .woocommerce-form__label-for-checkbox {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        cursor: pointer;
    }

    /* Ship to Different Address */
    .woocommerce-shipping-fields {
        margin-top: 30px;
    }
    #ship-to-different-address {
        margin-bottom: 20px;
    }
    #ship-to-different-address label {
        font-size: 1rem;
        font-weight: 500;
    }
    .shipping_address {
        margin-top: 20px;
    }

    /* Order Notes */
    .woocommerce-additional-fields {
        margin-top: 30px;
    }
    .woocommerce-additional-fields textarea {
        min-height: 100px;
        resize: vertical;
    }

    /* Payment Methods */
    .woocommerce-checkout-payment {
        background: var(--co-light);
        padding: 30px;
        border-radius: 8px;
    }
    .wc_payment_methods {
        list-style: none;
        padding: 0;
        margin: 0;
    }
    .wc_payment_method {
        padding: 20px;
        background: white;
        margin-bottom: 10px;
        border-radius: 8px;
        border: 2px solid transparent;
        transition: all 0.3s;
    }
    .wc_payment_method.active,
    .wc_payment_method:has(input:checked) {
        border-color: var(--co-rose-gold);
    }
    .wc_payment_method label {
        display: flex;
        align-items: center;
        gap: 12px;
        cursor: pointer;
        font-weight: 500;
    }
    .wc_payment_method label img {
        max-height: 30px;
        width: auto;
    }
    .payment_box {
        padding: 15px 0 0 32px;
        font-size: 0.9rem;
        color: var(--co-gray);
    }

    /* Terms */
    .woocommerce-terms-and-conditions-wrapper {
        margin: 25px 0;
    }
    .woocommerce-privacy-policy-text {
        font-size: 0.85rem;
        color: var(--co-gray);
        margin-bottom: 15px;
    }
    .woocommerce-privacy-policy-text a {
        color: var(--co-rose-gold);
    }

    /* Place Order Button */
    #place_order {
        width: 100%;
        padding: 18px;
        background: var(--co-rose-gold);
        color: white;
        border: none;
        font-size: 1.1rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 2px;
        cursor: pointer;
        transition: background 0.3s;
    }
    #place_order:hover {
        background: #a05d68;
    }
    #place_order:disabled {
        background: #ccc;
        cursor: not-allowed;
    }

    /* Order Review */
    .checkout-order-review {
        position: sticky;
        top: 30px;
    }

    .order-review-card {
        background: var(--co-light);
        padding: 35px;
        border-radius: 8px;
    }
    .order-review-card h2 {
        font-size: 1.3rem;
        font-weight: 500;
        margin: 0 0 25px;
        padding-bottom: 15px;
        border-bottom: 2px solid var(--co-obsidian);
    }

    /* Order Items */
    .order-review-items {
        margin-bottom: 25px;
    }
    .order-review-item {
        display: flex;
        gap: 15px;
        padding: 15px 0;
        border-bottom: 1px solid #eee;
    }
    .order-review-item:last-child {
        border-bottom: none;
    }
    .order-item-image {
        width: 70px;
        height: 70px;
        border-radius: 8px;
        overflow: hidden;
        flex-shrink: 0;
    }
    .order-item-image img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .order-item-details {
        flex: 1;
    }
    .order-item-details h4 {
        font-size: 0.95rem;
        margin: 0 0 5px;
        font-weight: 500;
    }
    .order-item-details .quantity {
        font-size: 0.85rem;
        color: var(--co-gray);
    }
    .order-item-price {
        font-weight: 600;
        color: var(--co-rose-gold);
    }

    /* Order Totals */
    .order-review-totals {
        border-top: 1px solid #ddd;
        padding-top: 20px;
    }
    .order-total-row {
        display: flex;
        justify-content: space-between;
        padding: 12px 0;
    }
    .order-total-row span:first-child {
        color: var(--co-gray);
    }
    .order-total-row span:last-child {
        font-weight: 500;
    }
    .order-total-row.grand-total {
        border-top: 2px solid var(--co-obsidian);
        margin-top: 15px;
        padding-top: 20px;
    }
    .order-total-row.grand-total span:first-child {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--co-obsidian);
    }
    .order-total-row.grand-total span:last-child {
        font-size: 1.4rem;
        font-weight: 700;
        color: var(--co-rose-gold);
    }

    /* Trust Badges */
    .checkout-trust {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 15px;
        margin-top: 25px;
        padding-top: 25px;
        border-top: 1px solid #ddd;
    }
    .checkout-trust-item {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.8rem;
        color: var(--co-gray);
    }
    .checkout-trust-item svg {
        width: 18px;
        height: 18px;
        fill: var(--co-rose-gold);
    }

    /* Coupon Code Section */
    .checkout-coupon {
        margin-top: 25px;
        padding-top: 25px;
        border-top: 1px solid #ddd;
    }
    .checkout-coupon summary {
        cursor: pointer;
        font-weight: 500;
        color: var(--co-obsidian);
        list-style: none;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .checkout-coupon summary::-webkit-details-marker {
        display: none;
    }
    .checkout-coupon summary svg {
        width: 16px;
        height: 16px;
        transition: transform 0.3s;
    }
    .checkout-coupon[open] summary svg {
        transform: rotate(180deg);
    }
    .coupon-form {
        display: flex;
        gap: 10px;
        margin-top: 15px;
    }
    .coupon-form input {
        flex: 1;
        padding: 12px 16px;
        border: 1px solid #ddd;
    }
    .coupon-form button {
        padding: 12px 20px;
        background: var(--co-obsidian);
        color: white;
        border: none;
        cursor: pointer;
        font-weight: 500;
        transition: background 0.3s;
    }
    .coupon-form button:hover {
        background: #333;
    }

    /* Express Checkout */
    .express-checkout {
        background: white;
        padding: 25px;
        border-radius: 8px;
        margin-bottom: 25px;
        text-align: center;
    }
    .express-checkout h4 {
        font-size: 0.9rem;
        color: var(--co-gray);
        margin: 0 0 15px;
        font-weight: 400;
    }
    .express-checkout-buttons {
        display: flex;
        gap: 10px;
    }
    .express-checkout-buttons button {
        flex: 1;
        padding: 14px;
        border: 1px solid #ddd;
        background: white;
        border-radius: 4px;
        cursor: pointer;
        transition: all 0.3s;
    }
    .express-checkout-buttons button:hover {
        border-color: var(--co-obsidian);
    }
    .express-checkout-buttons img {
        height: 24px;
    }

    .express-divider {
        display: flex;
        align-items: center;
        gap: 15px;
        margin: 25px 0;
        color: var(--co-gray);
        font-size: 0.85rem;
    }
    .express-divider::before,
    .express-divider::after {
        content: '';
        flex: 1;
        height: 1px;
        background: #ddd;
    }

    /* Mobile Responsive */
    @media (max-width: 1024px) {
        .checkout-container {
            grid-template-columns: 1fr;
        }
        .checkout-order-review {
            position: relative;
            top: 0;
        }
    }

    @media (max-width: 768px) {
        .woocommerce-billing-fields__field-wrapper,
        .woocommerce-shipping-fields__field-wrapper {
            grid-template-columns: 1fr;
        }
        .form-row-first,
        .form-row-last,
        .form-row-wide {
            grid-column: span 1;
        }
        .checkout-header {
            flex-direction: column;
            gap: 15px;
        }
        .progress-steps {
            flex-wrap: wrap;
            justify-content: center;
        }
        .progress-connector {
            display: none;
        }
        .checkout-trust {
            grid-template-columns: 1fr;
        }
    }
</style>

<div class="skyyrose-checkout">
    <!-- Checkout Header -->
    <div class="checkout-header">
        <a href="<?php echo home_url(); ?>" class="logo">SKYYROSE</a>
        <div class="secure-badge">
            <svg viewBox="0 0 24 24">
                <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z"/>
            </svg>
            Secure Checkout
        </div>
    </div>

    <!-- Progress Steps -->
    <div class="checkout-progress">
        <div class="progress-steps">
            <div class="progress-step completed">
                <span class="step-number">1</span>
                <span>Cart</span>
            </div>
            <div class="progress-connector completed"></div>
            <div class="progress-step active">
                <span class="step-number">2</span>
                <span>Checkout</span>
            </div>
            <div class="progress-connector"></div>
            <div class="progress-step">
                <span class="step-number">3</span>
                <span>Confirmation</span>
            </div>
        </div>
    </div>

    <form name="checkout" method="post" class="checkout woocommerce-checkout" action="<?php echo esc_url(wc_get_checkout_url()); ?>" enctype="multipart/form-data">

        <div class="checkout-container">
            <div class="checkout-form-main">
                <?php if ($checkout->get_checkout_fields()) : ?>

                    <?php do_action('woocommerce_checkout_before_customer_details'); ?>

                    <div class="checkout-form-section" id="customer_details">
                        <div class="col-1">
                            <h3><?php esc_html_e('Contact Information', 'woocommerce'); ?></h3>
                            <?php do_action('woocommerce_checkout_billing'); ?>
                        </div>

                        <div class="col-2">
                            <?php do_action('woocommerce_checkout_shipping'); ?>
                        </div>
                    </div>

                    <?php do_action('woocommerce_checkout_after_customer_details'); ?>

                <?php endif; ?>

                <!-- Payment Section -->
                <div class="checkout-form-section">
                    <h3><?php esc_html_e('Payment Method', 'woocommerce'); ?></h3>

                    <?php if (WC()->cart->needs_payment()) : ?>
                        <div id="payment" class="woocommerce-checkout-payment">
                            <?php if (WC()->cart->needs_payment()) : ?>
                                <ul class="wc_payment_methods payment_methods methods">
                                    <?php
                                    if (!empty($available_gateways = WC()->payment_gateways->get_available_payment_gateways())) {
                                        foreach ($available_gateways as $gateway) {
                                            wc_get_template('checkout/payment-method.php', array('gateway' => $gateway));
                                        }
                                    } else {
                                        echo '<li>' . apply_filters('woocommerce_no_available_payment_methods_message', WC()->customer->get_billing_country() ? esc_html__('Sorry, it seems that there are no available payment methods for your state. Please contact us if you require assistance or wish to make alternate arrangements.', 'woocommerce') : esc_html__('Please fill in your details above to see available payment methods.', 'woocommerce')) . '</li>';
                                    }
                                    ?>
                                </ul>
                            <?php endif; ?>

                            <div class="form-row place-order">
                                <nonce><?php wp_nonce_field('woocommerce-process_checkout', 'woocommerce-process-checkout-nonce'); ?></nonce>

                                <?php wc_get_template('checkout/terms.php'); ?>

                                <?php do_action('woocommerce_review_order_before_submit'); ?>

                                <?php echo apply_filters('woocommerce_order_button_html', '<button type="submit" class="button alt' . esc_attr(wc_wp_theme_get_element_class_name('button') ? ' ' . wc_wp_theme_get_element_class_name('button') : '') . '" name="woocommerce_checkout_place_order" id="place_order" value="' . esc_attr($order_button_text) . '" data-value="' . esc_attr($order_button_text) . '">' . esc_html($order_button_text) . '</button>'); ?>

                                <?php do_action('woocommerce_review_order_after_submit'); ?>
                            </div>
                        </div>
                    <?php else : ?>
                        <div class="woocommerce-checkout-payment">
                            <div class="form-row place-order">
                                <nonce><?php wp_nonce_field('woocommerce-process_checkout', 'woocommerce-process-checkout-nonce'); ?></nonce>

                                <?php wc_get_template('checkout/terms.php'); ?>

                                <?php do_action('woocommerce_review_order_before_submit'); ?>

                                <?php echo apply_filters('woocommerce_order_button_html', '<button type="submit" class="button alt' . esc_attr(wc_wp_theme_get_element_class_name('button') ? ' ' . wc_wp_theme_get_element_class_name('button') : '') . '" name="woocommerce_checkout_place_order" id="place_order" value="' . esc_attr($order_button_text) . '" data-value="' . esc_attr($order_button_text) . '">' . esc_html($order_button_text) . '</button>'); ?>

                                <?php do_action('woocommerce_review_order_after_submit'); ?>
                            </div>
                        </div>
                    <?php endif; ?>
                </div>
            </div>

            <!-- Order Review Sidebar -->
            <div class="checkout-order-review">
                <div class="order-review-card">
                    <h2><?php esc_html_e('Order Summary', 'woocommerce'); ?></h2>

                    <!-- Order Items -->
                    <div class="order-review-items">
                        <?php
                        foreach (WC()->cart->get_cart() as $cart_item_key => $cart_item) :
                            $_product = apply_filters('woocommerce_cart_item_product', $cart_item['data'], $cart_item, $cart_item_key);
                            $product_id = apply_filters('woocommerce_cart_item_product_id', $cart_item['product_id'], $cart_item, $cart_item_key);

                            if ($_product && $_product->exists() && $cart_item['quantity'] > 0 && apply_filters('woocommerce_checkout_cart_item_visible', true, $cart_item, $cart_item_key)) :
                        ?>
                            <div class="order-review-item">
                                <div class="order-item-image">
                                    <?php echo $_product->get_image('thumbnail'); ?>
                                </div>
                                <div class="order-item-details">
                                    <h4><?php echo wp_kses_post(apply_filters('woocommerce_cart_item_name', $_product->get_name(), $cart_item, $cart_item_key)); ?></h4>
                                    <span class="quantity">Qty: <?php echo esc_html($cart_item['quantity']); ?></span>
                                    <?php echo wc_get_formatted_cart_item_data($cart_item); ?>
                                </div>
                                <div class="order-item-price">
                                    <?php echo apply_filters('woocommerce_cart_item_subtotal', WC()->cart->get_product_subtotal($_product, $cart_item['quantity']), $cart_item, $cart_item_key); ?>
                                </div>
                            </div>
                        <?php
                            endif;
                        endforeach;
                        ?>
                    </div>

                    <!-- Order Totals -->
                    <div class="order-review-totals">
                        <div class="order-total-row">
                            <span><?php esc_html_e('Subtotal', 'woocommerce'); ?></span>
                            <span><?php wc_cart_totals_subtotal_html(); ?></span>
                        </div>

                        <?php foreach (WC()->cart->get_coupons() as $code => $coupon) : ?>
                            <div class="order-total-row coupon-<?php echo esc_attr(sanitize_title($code)); ?>">
                                <span><?php wc_cart_totals_coupon_label($coupon); ?></span>
                                <span><?php wc_cart_totals_coupon_html($coupon); ?></span>
                            </div>
                        <?php endforeach; ?>

                        <?php if (WC()->cart->needs_shipping() && WC()->cart->show_shipping()) : ?>
                            <div class="order-total-row">
                                <span><?php esc_html_e('Shipping', 'woocommerce'); ?></span>
                                <span>
                                    <?php
                                    $packages = WC()->shipping()->get_packages();
                                    foreach ($packages as $i => $package) {
                                        $chosen_method = isset(WC()->session->chosen_shipping_methods[$i]) ? WC()->session->chosen_shipping_methods[$i] : '';
                                        $available_methods = $package['rates'];

                                        if ($available_methods) {
                                            foreach ($available_methods as $method) {
                                                if ($method->id === $chosen_method) {
                                                    echo wp_kses_post($method->get_label() . ': ' . wc_price($method->get_cost()));
                                                    break;
                                                }
                                            }
                                        }
                                    }
                                    ?>
                                </span>
                            </div>
                        <?php endif; ?>

                        <?php foreach (WC()->cart->get_fees() as $fee) : ?>
                            <div class="order-total-row fee">
                                <span><?php echo esc_html($fee->name); ?></span>
                                <span><?php wc_cart_totals_fee_html($fee); ?></span>
                            </div>
                        <?php endforeach; ?>

                        <?php if (wc_tax_enabled() && !WC()->cart->display_prices_including_tax()) : ?>
                            <?php if ('itemized' === get_option('woocommerce_tax_total_display')) : ?>
                                <?php foreach (WC()->cart->get_tax_totals() as $code => $tax) : ?>
                                    <div class="order-total-row tax-rate tax-rate-<?php echo esc_attr(sanitize_title($code)); ?>">
                                        <span><?php echo esc_html($tax->label); ?></span>
                                        <span><?php echo wp_kses_post($tax->formatted_amount); ?></span>
                                    </div>
                                <?php endforeach; ?>
                            <?php else : ?>
                                <div class="order-total-row tax-total">
                                    <span><?php echo esc_html(WC()->countries->tax_or_vat()); ?></span>
                                    <span><?php wc_cart_totals_taxes_total_html(); ?></span>
                                </div>
                            <?php endif; ?>
                        <?php endif; ?>

                        <div class="order-total-row grand-total">
                            <span><?php esc_html_e('Total', 'woocommerce'); ?></span>
                            <span><?php wc_cart_totals_order_total_html(); ?></span>
                        </div>
                    </div>

                    <!-- Coupon Code -->
                    <details class="checkout-coupon">
                        <summary>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="6 9 12 15 18 9"/>
                            </svg>
                            Have a coupon code?
                        </summary>
                        <div class="coupon-form">
                            <input type="text" name="coupon_code" id="checkout_coupon_code" placeholder="Enter code">
                            <button type="button" id="apply_coupon_btn">Apply</button>
                        </div>
                    </details>

                    <!-- Trust Badges -->
                    <div class="checkout-trust">
                        <div class="checkout-trust-item">
                            <svg viewBox="0 0 24 24"><path d="M12 2L2 7v10l10 5 10-5V7L12 2zm0 18l-8-4V8l8 4 8-4v8l-8 4z"/></svg>
                            Free Shipping Over $100
                        </div>
                        <div class="checkout-trust-item">
                            <svg viewBox="0 0 24 24"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z"/></svg>
                            256-bit SSL Encryption
                        </div>
                        <div class="checkout-trust-item">
                            <svg viewBox="0 0 24 24"><path d="M17 3H7c-1.1 0-2 .9-2 2v16l7-3 7 3V5c0-1.1-.9-2-2-2z"/></svg>
                            30-Day Returns
                        </div>
                        <div class="checkout-trust-item">
                            <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                            100% Authentic
                        </div>
                    </div>
                </div>
            </div>
        </div>

    </form>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    // Apply Coupon
    const applyCouponBtn = document.getElementById('apply_coupon_btn');
    const couponInput = document.getElementById('checkout_coupon_code');

    if (applyCouponBtn && couponInput) {
        applyCouponBtn.addEventListener('click', function() {
            const couponCode = couponInput.value.trim();
            if (couponCode) {
                // Create hidden form and submit
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = '<?php echo esc_url(wc_get_cart_url()); ?>';

                const codeInput = document.createElement('input');
                codeInput.type = 'hidden';
                codeInput.name = 'coupon_code';
                codeInput.value = couponCode;

                const nonceInput = document.createElement('input');
                nonceInput.type = 'hidden';
                nonceInput.name = 'woocommerce-cart-nonce';
                nonceInput.value = '<?php echo wp_create_nonce('woocommerce-cart'); ?>';

                const applyInput = document.createElement('input');
                applyInput.type = 'hidden';
                applyInput.name = 'apply_coupon';
                applyInput.value = 'Apply coupon';

                form.appendChild(codeInput);
                form.appendChild(nonceInput);
                form.appendChild(applyInput);

                document.body.appendChild(form);
                form.submit();
            }
        });
    }

    // Payment method selection
    document.querySelectorAll('.wc_payment_method').forEach(method => {
        method.addEventListener('click', function() {
            document.querySelectorAll('.wc_payment_method').forEach(m => m.classList.remove('active'));
            this.classList.add('active');
            const radio = this.querySelector('input[type="radio"]');
            if (radio) radio.checked = true;
        });
    });
});
</script>

<?php do_action('woocommerce_after_checkout_form', $checkout); ?>
