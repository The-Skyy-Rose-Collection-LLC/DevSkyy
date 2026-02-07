<?php
/**
 * WooCommerce template wrapper
 *
 * @package SkyyRose_2025
 * @version 3.0.0
 */

if (!defined('ABSPATH')) exit;

get_header();
?>

<main class="site-main woocommerce-main">
    <div class="container">
        <?php woocommerce_content(); ?>
    </div>
</main>

<?php get_footer(); ?>
