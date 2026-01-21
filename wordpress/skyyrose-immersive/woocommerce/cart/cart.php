<?php
/**
 * SkyyRose Immersive Cart Template
 *
 * Premium cart experience with luxury styling
 *
 * @package SkyyRose_Immersive
 */

defined('ABSPATH') || exit;

do_action('woocommerce_before_cart');
?>

<style>
    :root {
        --cart-rose-gold: #B76E79;
        --cart-obsidian: #1A1A1A;
        --cart-champagne: #F7E7CE;
        --cart-white: #FFFFFF;
        --cart-gray: #666666;
        --cart-light: #f8f8f8;
    }

    .skyyrose-cart-page {
        background: var(--cart-white);
        min-height: 100vh;
        padding: 60px 5%;
    }

    .cart-page-title {
        text-align: center;
        margin-bottom: 50px;
    }
    .cart-page-title h1 {
        font-size: 2.5rem;
        font-weight: 300;
        color: var(--cart-obsidian);
        margin: 0 0 10px;
    }
    .cart-page-title p {
        color: var(--cart-gray);
        font-size: 1rem;
    }

    .cart-container {
        display: grid;
        grid-template-columns: 1fr 400px;
        gap: 60px;
        max-width: 1400px;
        margin: 0 auto;
    }

    /* Cart Items */
    .cart-items-section {
        background: var(--cart-white);
    }

    .cart-header {
        display: grid;
        grid-template-columns: 2fr 1fr 1fr 1fr 50px;
        gap: 20px;
        padding: 15px 20px;
        background: var(--cart-light);
        font-weight: 600;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: var(--cart-gray);
    }

    .cart-item {
        display: grid;
        grid-template-columns: 2fr 1fr 1fr 1fr 50px;
        gap: 20px;
        padding: 30px 20px;
        border-bottom: 1px solid #eee;
        align-items: center;
        transition: background 0.3s;
    }
    .cart-item:hover {
        background: #fafafa;
    }

    .cart-item-product {
        display: flex;
        gap: 20px;
        align-items: center;
    }
    .cart-item-image {
        width: 100px;
        height: 100px;
        border-radius: 8px;
        overflow: hidden;
        flex-shrink: 0;
    }
    .cart-item-image img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .cart-item-info h3 {
        font-size: 1.1rem;
        font-weight: 500;
        margin: 0 0 8px;
        color: var(--cart-obsidian);
    }
    .cart-item-info h3 a {
        color: inherit;
        text-decoration: none;
    }
    .cart-item-info h3 a:hover {
        color: var(--cart-rose-gold);
    }
    .cart-item-meta {
        font-size: 0.85rem;
        color: var(--cart-gray);
    }
    .cart-item-meta span {
        display: block;
        margin-bottom: 4px;
    }

    .cart-item-price {
        font-weight: 500;
        color: var(--cart-obsidian);
    }

    .cart-item-quantity {
        display: flex;
        align-items: center;
        border: 1px solid #ddd;
        width: fit-content;
    }
    .qty-btn {
        width: 36px;
        height: 36px;
        border: none;
        background: #f8f8f8;
        cursor: pointer;
        font-size: 1.1rem;
        transition: background 0.3s;
    }
    .qty-btn:hover {
        background: #eee;
    }
    .qty-input {
        width: 50px;
        height: 36px;
        border: none;
        border-left: 1px solid #ddd;
        border-right: 1px solid #ddd;
        text-align: center;
        font-size: 1rem;
    }

    .cart-item-subtotal {
        font-weight: 600;
        color: var(--cart-rose-gold);
        font-size: 1.1rem;
    }

    .cart-item-remove {
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .cart-item-remove a {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: #f8f8f8;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--cart-gray);
        text-decoration: none;
        transition: all 0.3s;
    }
    .cart-item-remove a:hover {
        background: #DC143C;
        color: white;
    }

    /* Coupon Section */
    .cart-coupon {
        display: flex;
        gap: 10px;
        padding: 30px 20px;
        border-bottom: 1px solid #eee;
    }
    .cart-coupon input {
        flex: 1;
        padding: 14px 20px;
        border: 1px solid #ddd;
        font-size: 0.95rem;
    }
    .cart-coupon input:focus {
        outline: none;
        border-color: var(--cart-rose-gold);
    }
    .cart-coupon button {
        padding: 14px 30px;
        background: var(--cart-obsidian);
        color: white;
        border: none;
        cursor: pointer;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: background 0.3s;
    }
    .cart-coupon button:hover {
        background: #333;
    }

    /* Cart Actions */
    .cart-actions {
        display: flex;
        justify-content: space-between;
        padding: 20px;
    }
    .cart-actions button {
        padding: 14px 30px;
        background: transparent;
        border: 2px solid #ddd;
        cursor: pointer;
        font-weight: 500;
        transition: all 0.3s;
    }
    .cart-actions button:hover {
        border-color: var(--cart-obsidian);
    }

    /* Cart Summary */
    .cart-summary {
        background: var(--cart-light);
        padding: 40px;
        border-radius: 8px;
        height: fit-content;
        position: sticky;
        top: 100px;
    }
    .cart-summary h2 {
        font-size: 1.5rem;
        font-weight: 500;
        margin: 0 0 30px;
        color: var(--cart-obsidian);
        padding-bottom: 20px;
        border-bottom: 1px solid #ddd;
    }

    .cart-summary-row {
        display: flex;
        justify-content: space-between;
        padding: 15px 0;
        border-bottom: 1px solid #eee;
    }
    .cart-summary-row:last-of-type {
        border-bottom: none;
    }
    .cart-summary-row span:first-child {
        color: var(--cart-gray);
    }
    .cart-summary-row span:last-child {
        font-weight: 500;
        color: var(--cart-obsidian);
    }
    .cart-summary-row.total {
        padding: 20px 0;
        margin-top: 10px;
        border-top: 2px solid var(--cart-obsidian);
        border-bottom: none;
    }
    .cart-summary-row.total span:first-child {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--cart-obsidian);
    }
    .cart-summary-row.total span:last-child {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--cart-rose-gold);
    }

    .cart-summary-shipping {
        background: white;
        padding: 20px;
        border-radius: 8px;
        margin: 20px 0;
    }
    .cart-summary-shipping p {
        margin: 0 0 10px;
        font-size: 0.9rem;
        color: var(--cart-gray);
    }
    .cart-summary-shipping strong {
        color: var(--cart-obsidian);
    }

    .cart-checkout-btn {
        width: 100%;
        padding: 18px;
        background: var(--cart-rose-gold);
        color: white;
        border: none;
        font-size: 1rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        cursor: pointer;
        transition: background 0.3s;
        margin-bottom: 15px;
    }
    .cart-checkout-btn:hover {
        background: #a05d68;
    }

    .cart-continue-btn {
        display: block;
        text-align: center;
        padding: 14px;
        border: 2px solid var(--cart-obsidian);
        color: var(--cart-obsidian);
        text-decoration: none;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s;
    }
    .cart-continue-btn:hover {
        background: var(--cart-obsidian);
        color: white;
    }

    /* Trust Section */
    .cart-trust {
        display: flex;
        flex-wrap: wrap;
        gap: 15px;
        margin-top: 25px;
        padding-top: 25px;
        border-top: 1px solid #ddd;
    }
    .cart-trust-item {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.8rem;
        color: var(--cart-gray);
    }
    .cart-trust-item svg {
        width: 18px;
        height: 18px;
        fill: var(--cart-rose-gold);
    }

    /* Empty Cart */
    .cart-empty {
        text-align: center;
        padding: 80px 20px;
    }
    .cart-empty svg {
        width: 80px;
        height: 80px;
        fill: #ddd;
        margin-bottom: 30px;
    }
    .cart-empty h2 {
        font-size: 1.8rem;
        font-weight: 300;
        margin: 0 0 15px;
        color: var(--cart-obsidian);
    }
    .cart-empty p {
        color: var(--cart-gray);
        margin-bottom: 30px;
    }
    .cart-empty a {
        display: inline-block;
        padding: 16px 40px;
        background: var(--cart-rose-gold);
        color: white;
        text-decoration: none;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: background 0.3s;
    }
    .cart-empty a:hover {
        background: #a05d68;
    }

    /* Mobile Responsive */
    @media (max-width: 1024px) {
        .cart-container {
            grid-template-columns: 1fr;
        }
        .cart-summary {
            position: relative;
            top: 0;
        }
    }

    @media (max-width: 768px) {
        .cart-header {
            display: none;
        }
        .cart-item {
            grid-template-columns: 1fr;
            gap: 15px;
        }
        .cart-item-product {
            flex-direction: column;
            text-align: center;
        }
        .cart-item-price,
        .cart-item-quantity,
        .cart-item-subtotal,
        .cart-item-remove {
            justify-content: center;
            text-align: center;
        }
        .cart-item-quantity {
            margin: 0 auto;
        }
        .cart-coupon {
            flex-direction: column;
        }
        .cart-actions {
            flex-direction: column;
            gap: 10px;
        }
    }
</style>

<div class="skyyrose-cart-page">
    <div class="cart-page-title">
        <h1>Shopping Cart</h1>
        <p><?php echo WC()->cart->get_cart_contents_count(); ?> items in your cart</p>
    </div>

    <?php if (WC()->cart->is_empty()) : ?>
        <div class="cart-empty">
            <svg viewBox="0 0 24 24">
                <path d="M17 18c-1.1 0-1.99.9-1.99 2s.89 2 1.99 2 2-.9 2-2-.9-2-2-2zM7 18c-1.1 0-1.99.9-1.99 2S5.9 22 7 22s2-.9 2-2-.9-2-2-2zm0-3l1.1-2h7.45c.75 0 1.41-.41 1.75-1.03L21 5H6.21l-.94-2H1v2h2l3.6 7.59-1.35 2.44C4.52 15.37 5 16.12 5 17h12v-2H7z"/>
            </svg>
            <h2>Your Cart is Empty</h2>
            <p>Discover our luxury collections and find your perfect piece.</p>
            <a href="<?php echo get_permalink(wc_get_page_id('shop')); ?>">Start Shopping</a>
        </div>
    <?php else : ?>
        <form class="woocommerce-cart-form" action="<?php echo esc_url(wc_get_cart_url()); ?>" method="post">
            <?php do_action('woocommerce_before_cart_table'); ?>

            <div class="cart-container">
                <div class="cart-items-section">
                    <div class="cart-header">
                        <span>Product</span>
                        <span>Price</span>
                        <span>Quantity</span>
                        <span>Subtotal</span>
                        <span></span>
                    </div>

                    <?php
                    foreach (WC()->cart->get_cart() as $cart_item_key => $cart_item) :
                        $_product = apply_filters('woocommerce_cart_item_product', $cart_item['data'], $cart_item, $cart_item_key);
                        $product_id = apply_filters('woocommerce_cart_item_product_id', $cart_item['product_id'], $cart_item, $cart_item_key);

                        if ($_product && $_product->exists() && $cart_item['quantity'] > 0 && apply_filters('woocommerce_cart_item_visible', true, $cart_item, $cart_item_key)) :
                            $product_permalink = apply_filters('woocommerce_cart_item_permalink', $_product->is_visible() ? $_product->get_permalink($cart_item) : '', $cart_item, $cart_item_key);
                    ?>
                        <div class="cart-item woocommerce-cart-form__cart-item <?php echo esc_attr(apply_filters('woocommerce_cart_item_class', 'cart_item', $cart_item, $cart_item_key)); ?>">
                            <div class="cart-item-product">
                                <div class="cart-item-image">
                                    <?php
                                    $thumbnail = apply_filters('woocommerce_cart_item_thumbnail', $_product->get_image(), $cart_item, $cart_item_key);
                                    if (!$product_permalink) {
                                        echo $thumbnail;
                                    } else {
                                        printf('<a href="%s">%s</a>', esc_url($product_permalink), $thumbnail);
                                    }
                                    ?>
                                </div>
                                <div class="cart-item-info">
                                    <h3>
                                        <?php
                                        if (!$product_permalink) {
                                            echo wp_kses_post(apply_filters('woocommerce_cart_item_name', $_product->get_name(), $cart_item, $cart_item_key) . '&nbsp;');
                                        } else {
                                            echo wp_kses_post(apply_filters('woocommerce_cart_item_name', sprintf('<a href="%s">%s</a>', esc_url($product_permalink), $_product->get_name()), $cart_item, $cart_item_key));
                                        }
                                        ?>
                                    </h3>
                                    <div class="cart-item-meta">
                                        <?php
                                        // Get variation data
                                        echo wc_get_formatted_cart_item_data($cart_item);
                                        ?>
                                    </div>
                                </div>
                            </div>

                            <div class="cart-item-price" data-title="<?php esc_attr_e('Price', 'woocommerce'); ?>">
                                <?php echo apply_filters('woocommerce_cart_item_price', WC()->cart->get_product_price($_product), $cart_item, $cart_item_key); ?>
                            </div>

                            <div class="cart-item-quantity" data-title="<?php esc_attr_e('Quantity', 'woocommerce'); ?>">
                                <?php
                                if ($_product->is_sold_individually()) {
                                    $min_quantity = 1;
                                    $max_quantity = 1;
                                } else {
                                    $min_quantity = 0;
                                    $max_quantity = $_product->get_max_purchase_quantity();
                                }

                                $product_quantity = woocommerce_quantity_input(
                                    array(
                                        'input_name'   => "cart[{$cart_item_key}][qty]",
                                        'input_value'  => $cart_item['quantity'],
                                        'max_value'    => $max_quantity,
                                        'min_value'    => $min_quantity,
                                        'product_name' => $_product->get_name(),
                                    ),
                                    $_product,
                                    false
                                );

                                echo apply_filters('woocommerce_cart_item_quantity', $product_quantity, $cart_item_key, $cart_item);
                                ?>
                            </div>

                            <div class="cart-item-subtotal" data-title="<?php esc_attr_e('Subtotal', 'woocommerce'); ?>">
                                <?php echo apply_filters('woocommerce_cart_item_subtotal', WC()->cart->get_product_subtotal($_product, $cart_item['quantity']), $cart_item, $cart_item_key); ?>
                            </div>

                            <div class="cart-item-remove">
                                <?php
                                echo apply_filters(
                                    'woocommerce_cart_item_remove_link',
                                    sprintf(
                                        '<a href="%s" class="remove" aria-label="%s" data-product_id="%s" data-product_sku="%s">
                                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                                <line x1="18" y1="6" x2="6" y2="18"></line>
                                                <line x1="6" y1="6" x2="18" y2="18"></line>
                                            </svg>
                                        </a>',
                                        esc_url(wc_get_cart_remove_url($cart_item_key)),
                                        esc_html__('Remove this item', 'woocommerce'),
                                        esc_attr($product_id),
                                        esc_attr($_product->get_sku())
                                    ),
                                    $cart_item_key
                                );
                                ?>
                            </div>
                        </div>
                    <?php
                        endif;
                    endforeach;
                    ?>

                    <!-- Coupon -->
                    <?php if (wc_coupons_enabled()) : ?>
                        <div class="cart-coupon coupon">
                            <input type="text" name="coupon_code" class="input-text" id="coupon_code" value="" placeholder="Enter coupon code" />
                            <button type="submit" class="button<?php echo esc_attr(wc_wp_theme_get_element_class_name('button') ? ' ' . wc_wp_theme_get_element_class_name('button') : ''); ?>" name="apply_coupon" value="<?php esc_attr_e('Apply coupon', 'woocommerce'); ?>">Apply</button>
                            <?php do_action('woocommerce_cart_coupon'); ?>
                        </div>
                    <?php endif; ?>

                    <div class="cart-actions">
                        <button type="submit" class="button<?php echo esc_attr(wc_wp_theme_get_element_class_name('button') ? ' ' . wc_wp_theme_get_element_class_name('button') : ''); ?>" name="update_cart" value="<?php esc_attr_e('Update cart', 'woocommerce'); ?>"><?php esc_html_e('Update cart', 'woocommerce'); ?></button>
                        <?php do_action('woocommerce_cart_actions'); ?>
                        <?php wp_nonce_field('woocommerce-cart', 'woocommerce-cart-nonce'); ?>
                    </div>
                </div>

                <div class="cart-summary">
                    <h2>Order Summary</h2>

                    <div class="cart-summary-row">
                        <span>Subtotal</span>
                        <span><?php wc_cart_totals_subtotal_html(); ?></span>
                    </div>

                    <?php foreach (WC()->cart->get_coupons() as $code => $coupon) : ?>
                        <div class="cart-summary-row coupon-<?php echo esc_attr(sanitize_title($code)); ?>">
                            <span><?php wc_cart_totals_coupon_label($coupon); ?></span>
                            <span><?php wc_cart_totals_coupon_html($coupon); ?></span>
                        </div>
                    <?php endforeach; ?>

                    <?php if (WC()->cart->needs_shipping() && WC()->cart->show_shipping()) : ?>
                        <div class="cart-summary-shipping">
                            <?php do_action('woocommerce_cart_totals_before_shipping'); ?>
                            <?php wc_cart_totals_shipping_html(); ?>
                            <?php do_action('woocommerce_cart_totals_after_shipping'); ?>
                        </div>
                    <?php elseif (WC()->cart->needs_shipping() && 'yes' === get_option('woocommerce_enable_shipping_calc')) : ?>
                        <div class="cart-summary-shipping">
                            <p><strong>Free Shipping</strong> on orders over $100</p>
                            <p>Shipping calculated at checkout</p>
                        </div>
                    <?php endif; ?>

                    <?php foreach (WC()->cart->get_fees() as $fee) : ?>
                        <div class="cart-summary-row fee">
                            <span><?php echo esc_html($fee->name); ?></span>
                            <span><?php wc_cart_totals_fee_html($fee); ?></span>
                        </div>
                    <?php endforeach; ?>

                    <?php if (wc_tax_enabled() && !WC()->cart->display_prices_including_tax()) : ?>
                        <?php if ('itemized' === get_option('woocommerce_tax_total_display')) : ?>
                            <?php foreach (WC()->cart->get_tax_totals() as $code => $tax) : ?>
                                <div class="cart-summary-row tax-rate tax-rate-<?php echo esc_attr(sanitize_title($code)); ?>">
                                    <span><?php echo esc_html($tax->label); ?></span>
                                    <span><?php echo wp_kses_post($tax->formatted_amount); ?></span>
                                </div>
                            <?php endforeach; ?>
                        <?php else : ?>
                            <div class="cart-summary-row tax-total">
                                <span><?php echo esc_html(WC()->countries->tax_or_vat()); ?></span>
                                <span><?php wc_cart_totals_taxes_total_html(); ?></span>
                            </div>
                        <?php endif; ?>
                    <?php endif; ?>

                    <?php do_action('woocommerce_cart_totals_before_order_total'); ?>

                    <div class="cart-summary-row total">
                        <span><?php esc_html_e('Total', 'woocommerce'); ?></span>
                        <span><?php wc_cart_totals_order_total_html(); ?></span>
                    </div>

                    <?php do_action('woocommerce_cart_totals_after_order_total'); ?>

                    <div class="wc-proceed-to-checkout">
                        <?php do_action('woocommerce_proceed_to_checkout'); ?>
                    </div>

                    <a href="<?php echo get_permalink(wc_get_page_id('shop')); ?>" class="cart-continue-btn">
                        Continue Shopping
                    </a>

                    <div class="cart-trust">
                        <div class="cart-trust-item">
                            <svg viewBox="0 0 24 24"><path d="M12 2L2 7v10l10 5 10-5V7L12 2zm0 18l-8-4V8l8 4 8-4v8l-8 4z"/></svg>
                            Free Shipping Over $100
                        </div>
                        <div class="cart-trust-item">
                            <svg viewBox="0 0 24 24"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z"/></svg>
                            Secure Checkout
                        </div>
                        <div class="cart-trust-item">
                            <svg viewBox="0 0 24 24"><path d="M17 3H7c-1.1 0-2 .9-2 2v16l7-3 7 3V5c0-1.1-.9-2-2-2z"/></svg>
                            30-Day Returns
                        </div>
                    </div>
                </div>
            </div>

            <?php do_action('woocommerce_after_cart_table'); ?>
        </form>

        <?php do_action('woocommerce_before_cart_collaterals'); ?>

        <div class="cart-collaterals">
            <?php
            /**
             * Cart collaterals hook.
             *
             * @hooked woocommerce_cross_sell_display
             */
            do_action('woocommerce_cart_collaterals');
            ?>
        </div>
    <?php endif; ?>
</div>

<?php do_action('woocommerce_after_cart'); ?>
