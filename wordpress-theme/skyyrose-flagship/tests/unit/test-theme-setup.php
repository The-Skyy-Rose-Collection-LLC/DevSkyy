<?php
/**
 * Class Test_Theme_Setup
 *
 * Tests for theme setup and initialization.
 *
 * @package SkyyRose_Flagship
 */

class Test_Theme_Setup extends WP_UnitTestCase {

    /**
     * Test theme constants are defined.
     */
    public function test_theme_constants_defined() {
        $this->assertTrue( defined( 'SKYYROSE_VERSION' ) );
        $this->assertTrue( defined( 'SKYYROSE_THEME_DIR' ) );
        $this->assertTrue( defined( 'SKYYROSE_THEME_URI' ) );
        $this->assertTrue( defined( 'SKYYROSE_ASSETS_URI' ) );
    }

    /**
     * Test theme version constant.
     */
    public function test_theme_version() {
        $this->assertEquals( '1.0.0', SKYYROSE_VERSION );
    }

    /**
     * Test theme supports.
     */
    public function test_theme_supports() {
        $this->assertTrue( current_theme_supports( 'title-tag' ) );
        $this->assertTrue( current_theme_supports( 'post-thumbnails' ) );
        $this->assertTrue( current_theme_supports( 'html5' ) );
        $this->assertTrue( current_theme_supports( 'custom-logo' ) );
        $this->assertTrue( current_theme_supports( 'align-wide' ) );
        $this->assertTrue( current_theme_supports( 'responsive-embeds' ) );
        $this->assertTrue( current_theme_supports( 'woocommerce' ) );
    }

    /**
     * Test WooCommerce features.
     */
    public function test_woocommerce_features() {
        if ( class_exists( 'WooCommerce' ) ) {
            $this->assertTrue( current_theme_supports( 'wc-product-gallery-zoom' ) );
            $this->assertTrue( current_theme_supports( 'wc-product-gallery-lightbox' ) );
            $this->assertTrue( current_theme_supports( 'wc-product-gallery-slider' ) );
        }
    }

    /**
     * Test navigation menus registered.
     */
    public function test_nav_menus_registered() {
        $menus = get_registered_nav_menus();

        $this->assertArrayHasKey( 'primary', $menus );
        $this->assertArrayHasKey( 'footer', $menus );
        $this->assertArrayHasKey( 'mobile', $menus );
        $this->assertArrayHasKey( 'top-bar', $menus );
    }

    /**
     * Test widget areas registered.
     */
    public function test_widget_areas_registered() {
        global $wp_registered_sidebars;

        $this->assertArrayHasKey( 'sidebar-1', $wp_registered_sidebars );
        $this->assertArrayHasKey( 'footer-1', $wp_registered_sidebars );
        $this->assertArrayHasKey( 'footer-2', $wp_registered_sidebars );
        $this->assertArrayHasKey( 'footer-3', $wp_registered_sidebars );
        $this->assertArrayHasKey( 'footer-4', $wp_registered_sidebars );

        if ( class_exists( 'WooCommerce' ) ) {
            $this->assertArrayHasKey( 'shop-sidebar', $wp_registered_sidebars );
        }
    }

    /**
     * Test custom image sizes.
     */
    public function test_custom_image_sizes() {
        $sizes = get_intermediate_image_sizes();

        $this->assertContains( 'skyyrose-featured', $sizes );
        $this->assertContains( 'skyyrose-thumbnail', $sizes );
        $this->assertContains( 'skyyrose-medium', $sizes );
    }

    /**
     * Test content width is set.
     */
    public function test_content_width() {
        global $content_width;

        $this->assertEquals( 1200, $content_width );
    }

    /**
     * Test scripts enqueued on frontend.
     */
    public function test_frontend_scripts_enqueued() {
        do_action( 'wp_enqueue_scripts' );

        $this->assertTrue( wp_script_is( 'threejs', 'enqueued' ) );
        $this->assertTrue( wp_script_is( 'skyyrose-main', 'enqueued' ) );
        $this->assertTrue( wp_script_is( 'skyyrose-three-init', 'enqueued' ) );
        $this->assertTrue( wp_script_is( 'skyyrose-navigation', 'enqueued' ) );
    }

    /**
     * Test styles enqueued on frontend.
     */
    public function test_frontend_styles_enqueued() {
        do_action( 'wp_enqueue_scripts' );

        $this->assertTrue( wp_style_is( 'skyyrose-style', 'enqueued' ) );
        $this->assertTrue( wp_style_is( 'skyyrose-custom', 'enqueued' ) );
    }

    /**
     * Test localized script data.
     */
    public function test_localized_script_data() {
        do_action( 'wp_enqueue_scripts' );

        $script_data = wp_scripts()->get_data( 'skyyrose-main', 'data' );

        $this->assertStringContainsString( 'skyyRoseData', $script_data );
        $this->assertStringContainsString( 'ajaxUrl', $script_data );
        $this->assertStringContainsString( 'nonce', $script_data );
    }

    /**
     * Test body classes.
     */
    public function test_body_classes() {
        $classes = get_body_class();

        // Test for singular class on single posts.
        $post_id = $this->factory->post->create();
        $this->go_to( get_permalink( $post_id ) );
        $classes = get_body_class();
        $this->assertContains( 'singular', $classes );
    }

    /**
     * Test security enhancements.
     */
    public function test_security_headers_removed() {
        // Check that wp_generator is removed.
        $this->assertFalse( has_action( 'wp_head', 'wp_generator' ) );
        $this->assertFalse( has_action( 'wp_head', 'rsd_link' ) );
        $this->assertFalse( has_action( 'wp_head', 'wlwmanifest_link' ) );
        $this->assertFalse( has_action( 'wp_head', 'wp_shortlink_wp_head' ) );
    }

    /**
     * Test XML-RPC disabled.
     */
    public function test_xmlrpc_disabled() {
        $this->assertFalse( apply_filters( 'xmlrpc_enabled', true ) );
    }
}
