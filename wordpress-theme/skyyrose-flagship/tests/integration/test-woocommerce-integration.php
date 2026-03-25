<?php
/**
 * Class Test_WooCommerce_Integration
 *
 * Tests for WooCommerce integration.
 *
 * @package SkyyRose_Flagship
 */

class Test_WooCommerce_Integration extends WP_UnitTestCase {

    /**
     * Set up before each test.
     */
    public function setUp(): void {
        parent::setUp();

        if ( ! class_exists( 'WooCommerce' ) ) {
            $this->markTestSkipped( 'WooCommerce is not available' );
        }
    }

    /**
     * Test WooCommerce support is declared.
     */
    public function test_woocommerce_support() {
        $this->assertTrue( current_theme_supports( 'woocommerce' ) );
    }

    /**
     * Test WooCommerce gallery features.
     */
    public function test_woocommerce_gallery_features() {
        $this->assertTrue( current_theme_supports( 'wc-product-gallery-zoom' ) );
        $this->assertTrue( current_theme_supports( 'wc-product-gallery-lightbox' ) );
        $this->assertTrue( current_theme_supports( 'wc-product-gallery-slider' ) );
    }

    /**
     * Test shop sidebar is registered.
     */
    public function test_shop_sidebar_registered() {
        global $wp_registered_sidebars;
        $this->assertArrayHasKey( 'shop-sidebar', $wp_registered_sidebars );
    }

    /**
     * Test simple product creation.
     */
    public function test_create_simple_product() {
        $product = WC_Helper_Product::create_simple_product();

        $this->assertInstanceOf( 'WC_Product_Simple', $product );
        $this->assertGreaterThan( 0, $product->get_id() );
    }

    /**
     * Test variable product creation.
     */
    public function test_create_variable_product() {
        $product = WC_Helper_Product::create_variation_product();

        $this->assertInstanceOf( 'WC_Product_Variable', $product );
        $this->assertGreaterThan( 0, count( $product->get_children() ) );
    }

    /**
     * Test product has correct price.
     */
    public function test_product_price() {
        $product = WC_Helper_Product::create_simple_product();
        $product->set_regular_price( 99.99 );
        $product->save();

        $this->assertEquals( '99.99', $product->get_regular_price() );
    }

    /**
     * Test sale price.
     */
    public function test_sale_price() {
        $product = WC_Helper_Product::create_simple_product();
        $product->set_regular_price( 99.99 );
        $product->set_sale_price( 79.99 );
        $product->save();

        $this->assertTrue( $product->is_on_sale() );
        $this->assertEquals( '79.99', $product->get_sale_price() );
        $this->assertEquals( '79.99', $product->get_price() );
    }

    /**
     * Test product stock management.
     */
    public function test_product_stock() {
        $product = WC_Helper_Product::create_simple_product();
        $product->set_manage_stock( true );
        $product->set_stock_quantity( 10 );
        $product->save();

        $this->assertTrue( $product->managing_stock() );
        $this->assertTrue( $product->is_in_stock() );
        $this->assertEquals( 10, $product->get_stock_quantity() );
    }

    /**
     * Test out of stock product.
     */
    public function test_out_of_stock_product() {
        $product = WC_Helper_Product::create_simple_product();
        $product->set_manage_stock( true );
        $product->set_stock_quantity( 0 );
        $product->set_stock_status( 'outofstock' );
        $product->save();

        $this->assertFalse( $product->is_in_stock() );
    }

    /**
     * Test add to cart functionality.
     */
    public function test_add_to_cart() {
        $product = WC_Helper_Product::create_simple_product();
        WC()->cart->add_to_cart( $product->get_id(), 1 );

        $this->assertEquals( 1, WC()->cart->get_cart_contents_count() );
    }

    /**
     * Test cart total calculation.
     */
    public function test_cart_total() {
        WC()->cart->empty_cart();

        $product = WC_Helper_Product::create_simple_product();
        $product->set_regular_price( 10 );
        $product->save();

        WC()->cart->add_to_cart( $product->get_id(), 2 );

        $this->assertEquals( 20, WC()->cart->get_cart_contents_total() );
    }

    /**
     * Test remove from cart.
     */
    public function test_remove_from_cart() {
        WC()->cart->empty_cart();

        $product = WC_Helper_Product::create_simple_product();
        $cart_item_key = WC()->cart->add_to_cart( $product->get_id(), 1 );

        WC()->cart->remove_cart_item( $cart_item_key );

        $this->assertEquals( 0, WC()->cart->get_cart_contents_count() );
    }

    /**
     * Test cart quantity update.
     */
    public function test_update_cart_quantity() {
        WC()->cart->empty_cart();

        $product = WC_Helper_Product::create_simple_product();
        $cart_item_key = WC()->cart->add_to_cart( $product->get_id(), 1 );

        WC()->cart->set_quantity( $cart_item_key, 3 );

        $this->assertEquals( 3, WC()->cart->get_cart_contents_count() );
    }

    /**
     * Test coupon application.
     */
    public function test_apply_coupon() {
        WC()->cart->empty_cart();

        // Create a coupon.
        $coupon = WC_Helper_Coupon::create_coupon( 'testcoupon' );
        $coupon->set_amount( 10 );
        $coupon->set_discount_type( 'fixed_cart' );
        $coupon->save();

        // Add product to cart.
        $product = WC_Helper_Product::create_simple_product();
        $product->set_regular_price( 50 );
        $product->save();
        WC()->cart->add_to_cart( $product->get_id(), 1 );

        // Apply coupon.
        WC()->cart->apply_coupon( 'testcoupon' );

        $this->assertTrue( WC()->cart->has_discount( 'testcoupon' ) );
    }

    /**
     * Test product categories.
     */
    public function test_product_categories() {
        $product = WC_Helper_Product::create_simple_product();
        $category_id = $this->factory->term->create( [
            'taxonomy' => 'product_cat',
            'name' => 'Test Category'
        ] );

        wp_set_object_terms( $product->get_id(), $category_id, 'product_cat' );

        $categories = wp_get_post_terms( $product->get_id(), 'product_cat' );
        $this->assertGreaterThan( 0, count( $categories ) );
    }

    /**
     * Test product tags.
     */
    public function test_product_tags() {
        $product = WC_Helper_Product::create_simple_product();
        $tag_id = $this->factory->term->create( [
            'taxonomy' => 'product_tag',
            'name' => 'Test Tag'
        ] );

        wp_set_object_terms( $product->get_id(), $tag_id, 'product_tag' );

        $tags = wp_get_post_terms( $product->get_id(), 'product_tag' );
        $this->assertGreaterThan( 0, count( $tags ) );
    }

    /**
     * Test product attributes.
     */
    public function test_product_attributes() {
        $product = WC_Helper_Product::create_simple_product();

        $attribute = new WC_Product_Attribute();
        $attribute->set_name( 'color' );
        $attribute->set_options( [ 'Red', 'Blue', 'Green' ] );
        $attribute->set_visible( true );

        $product->set_attributes( [ $attribute ] );
        $product->save();

        $attributes = $product->get_attributes();
        $this->assertCount( 1, $attributes );
    }

    /**
     * Test product gallery images.
     */
    public function test_product_gallery() {
        $product = WC_Helper_Product::create_simple_product();

        $image_id = $this->factory->attachment->create_object( [
            'file' => 'test-image.jpg',
            'post_mime_type' => 'image/jpeg'
        ] );

        $product->set_gallery_image_ids( [ $image_id ] );
        $product->save();

        $gallery_ids = $product->get_gallery_image_ids();
        $this->assertContains( $image_id, $gallery_ids );
    }

    /**
     * Test related products.
     */
    public function test_related_products() {
        $product = WC_Helper_Product::create_simple_product();
        $related = wc_get_related_products( $product->get_id(), 4 );

        $this->assertTrue( is_array( $related ) );
    }

    /**
     * Tear down after each test.
     */
    public function tearDown(): void {
        WC()->cart->empty_cart();
        parent::tearDown();
    }
}
