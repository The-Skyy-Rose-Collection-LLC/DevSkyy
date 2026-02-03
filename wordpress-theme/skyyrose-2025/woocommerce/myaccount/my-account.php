<?php
/**
 * My Account page
 *
 * This template can be overridden by copying it to yourtheme/woocommerce/myaccount/my-account.php.
 *
 * HOWEVER, on occasion WooCommerce will need to update template files and you
 * (the theme developer) will need to copy the new files to your theme to
 * maintain compatibility.
 *
 * @see https://docs.woocommerce.com/document/template-structure/
 * @package WooCommerce\Templates
 * @version 3.5.0
 */

defined('ABSPATH') || exit;

/**
 * My Account navigation.
 *
 * @since 2.6.0
 */
do_action('woocommerce_account_navigation'); ?>

<div class="woocommerce-MyAccount-content skyyrose-account-content">
    <?php
    /**
     * My Account content.
     *
     * @since 2.6.0
     */
    do_action('woocommerce_account_content');
    ?>
</div>
