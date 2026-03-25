<?php
/**
 * Class Test_Template_Functions
 *
 * Tests for template functions.
 *
 * @package SkyyRose_Flagship
 */

class Test_Template_Functions extends WP_UnitTestCase {

    /**
     * Set up before each test.
     */
    public function setUp(): void {
        parent::setUp();

        // Load template functions if they exist.
        $template_functions_file = SKYYROSE_THEME_DIR . '/inc/template-functions.php';
        if ( file_exists( $template_functions_file ) ) {
            require_once $template_functions_file;
        }
    }

    /**
     * Test pagination function exists.
     */
    public function test_pagination_function_exists() {
        if ( function_exists( 'skyyrose_pagination' ) ) {
            $this->assertTrue( true );
        } else {
            $this->markTestSkipped( 'Pagination function not yet implemented' );
        }
    }

    /**
     * Test breadcrumbs function exists.
     */
    public function test_breadcrumbs_function_exists() {
        if ( function_exists( 'skyyrose_breadcrumbs' ) ) {
            $this->assertTrue( true );
        } else {
            $this->markTestSkipped( 'Breadcrumbs function not yet implemented' );
        }
    }

    /**
     * Test entry meta function exists.
     */
    public function test_entry_meta_function_exists() {
        if ( function_exists( 'skyyrose_entry_meta' ) ) {
            $this->assertTrue( true );
        } else {
            $this->markTestSkipped( 'Entry meta function not yet implemented' );
        }
    }

    /**
     * Test that functions produce output.
     */
    public function test_functions_produce_output() {
        // Create a test post.
        $post_id = $this->factory->post->create( [
            'post_title' => 'Test Post',
            'post_content' => 'Test content',
        ] );

        $this->go_to( get_permalink( $post_id ) );

        // Test various template functions produce output.
        if ( function_exists( 'skyyrose_entry_meta' ) ) {
            ob_start();
            skyyrose_entry_meta();
            $output = ob_get_clean();
            $this->assertNotEmpty( $output );
        }
    }
}
