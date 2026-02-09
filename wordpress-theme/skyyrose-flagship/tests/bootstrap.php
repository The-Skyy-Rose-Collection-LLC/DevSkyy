<?php
/**
 * PHPUnit Bootstrap File
 *
 * @package SkyyRose_Flagship
 */

// Composer autoloader.
require_once dirname( __DIR__ ) . '/vendor/autoload.php';

// WordPress tests library.
$_tests_dir = getenv( 'WP_TESTS_DIR' );
if ( ! $_tests_dir ) {
    $_tests_dir = '/tmp/wordpress-tests-lib';
}

// Give access to tests_add_filter() function.
require_once $_tests_dir . '/includes/functions.php';

/**
 * Manually load the theme being tested.
 */
function _manually_load_theme() {
    $theme_dir = dirname( __DIR__ );
    switch_theme( basename( $theme_dir ) );
}
tests_add_filter( 'muplugins_loaded', '_manually_load_theme' );

/**
 * Load WooCommerce for testing.
 */
function _manually_load_woocommerce() {
    // Load WooCommerce if it exists in the plugins directory.
    $wc_plugin_path = dirname( dirname( dirname( __DIR__ ) ) ) . '/plugins/woocommerce/woocommerce.php';
    if ( file_exists( $wc_plugin_path ) ) {
        require_once $wc_plugin_path;
    }
}
tests_add_filter( 'muplugins_loaded', '_manually_load_woocommerce' );

// Start up the WP testing environment.
require $_tests_dir . '/includes/bootstrap.php';

// Load WooCommerce testing framework.
if ( class_exists( 'WooCommerce' ) ) {
    require_once dirname( dirname( dirname( __DIR__ ) ) ) . '/plugins/woocommerce/tests/legacy/bootstrap.php';
}
