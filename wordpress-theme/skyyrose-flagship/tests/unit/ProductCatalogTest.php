<?php
/**
 * Tests for inc/product-catalog.php
 *
 * Reads the real data/skyyrose-catalog.csv via get_theme_file_path() stub.
 * The static cache inside skyyrose_get_product_catalog() persists across
 * test methods within a single process — intentional and safe here.
 *
 * @package SkyyRose
 */

use PHPUnit\Framework\TestCase;

class ProductCatalogTest extends TestCase {

	// --- skyyrose_normalize_sku() ------------------------------------------

	public function test_normalize_sku_strips_tee_suffix(): void {
		$this->assertSame( 'sg-001', skyyrose_normalize_sku( 'sg-001-tee' ) );
	}

	public function test_normalize_sku_strips_giants_suffix(): void {
		$this->assertSame( 'br-003', skyyrose_normalize_sku( 'br-003-giants' ) );
	}

	public function test_normalize_sku_strips_white_suffix(): void {
		$this->assertSame( 'br-003', skyyrose_normalize_sku( 'br-003-white' ) );
	}

	public function test_normalize_sku_strips_oakland_suffix(): void {
		$this->assertSame( 'br-003', skyyrose_normalize_sku( 'br-003-oakland' ) );
	}

	public function test_normalize_sku_strips_trailing_letter(): void {
		$this->assertSame( 'br-003', skyyrose_normalize_sku( 'br-003a' ) );
	}

	public function test_normalize_sku_passthrough_clean_sku(): void {
		$this->assertSame( 'br-001', skyyrose_normalize_sku( 'br-001' ) );
	}

	public function test_normalize_sku_passthrough_kc_sku(): void {
		$this->assertSame( 'kc-001', skyyrose_normalize_sku( 'kc-001' ) );
	}

	// --- skyyrose_get_product_catalog() ------------------------------------

	public function test_catalog_is_non_empty_array(): void {
		$catalog = skyyrose_get_product_catalog();
		$this->assertIsArray( $catalog );
		$this->assertNotEmpty( $catalog );
	}

	public function test_catalog_keyed_by_sku(): void {
		$catalog = skyyrose_get_product_catalog();
		$this->assertArrayHasKey( 'br-001', $catalog );
		$this->assertArrayHasKey( 'br-002', $catalog );
		$this->assertArrayHasKey( 'br-003', $catalog );
	}

	public function test_catalog_product_has_required_fields(): void {
		$product  = skyyrose_get_product_catalog()['br-001'];
		$required = array( 'sku', 'name', 'price', 'collection', 'description', 'published', 'is_preorder', 'garment_type_lock' );
		foreach ( $required as $field ) {
			$this->assertArrayHasKey( $field, $product, "Product missing field '$field'" );
		}
	}

	// --- skyyrose_get_product() -------------------------------------------

	public function test_get_product_br001_name(): void {
		$product = skyyrose_get_product( 'br-001' );
		$this->assertSame( 'BLACK Rose Crewneck', $product['name'] );
	}

	public function test_get_product_br001_price(): void {
		$product = skyyrose_get_product( 'br-001' );
		$this->assertSame( 35.0, $product['price'] );
	}

	public function test_get_product_br001_collection(): void {
		$product = skyyrose_get_product( 'br-001' );
		$this->assertSame( 'black-rose', $product['collection'] );
	}

	public function test_get_product_br001_published(): void {
		$product = skyyrose_get_product( 'br-001' );
		$this->assertTrue( $product['published'] );
	}

	public function test_get_product_br001_not_preorder(): void {
		$product = skyyrose_get_product( 'br-001' );
		$this->assertFalse( $product['is_preorder'] );
	}

	public function test_get_product_br003_is_preorder(): void {
		$product = skyyrose_get_product( 'br-003' );
		$this->assertTrue( $product['is_preorder'] );
	}

	public function test_get_product_br001_garment_type(): void {
		$product = skyyrose_get_product( 'br-001' );
		$this->assertSame( 'crewneck', $product['garment_type_lock'] );
	}

	public function test_get_product_returns_null_for_unknown_sku(): void {
		$this->assertNull( skyyrose_get_product( 'xx-999' ) );
	}

	public function test_get_product_sku_field_matches(): void {
		$product = skyyrose_get_product( 'br-002' );
		$this->assertSame( 'br-002', $product['sku'] );
	}

	// --- skyyrose_get_collection_products() --------------------------------

	public function test_black_rose_products_non_empty(): void {
		$products = skyyrose_get_collection_products( 'black-rose' );
		$this->assertNotEmpty( $products );
	}

	public function test_black_rose_includes_br001(): void {
		$products = skyyrose_get_collection_products( 'black-rose' );
		$skus     = array_column( $products, 'sku' );
		$this->assertContains( 'br-001', $skus );
	}

	public function test_black_rose_products_all_have_correct_collection(): void {
		foreach ( skyyrose_get_collection_products( 'black-rose' ) as $product ) {
			$this->assertSame( 'black-rose', $product['collection'] );
		}
	}

	public function test_empty_collection_returns_empty_array(): void {
		$this->assertSame( array(), skyyrose_get_collection_products( 'nonexistent-collection' ) );
	}

	// --- skyyrose_get_product_display_image() ------------------------------

	public function test_display_image_returns_primary_image_slot(): void {
		$product = array(
			'image'            => 'assets/images/br-001.webp',
			'front_model_image' => 'assets/images/br-001-model.webp',
			'back_image'       => '',
			'back_model_image' => '',
		);
		$this->assertSame( 'assets/images/br-001.webp', skyyrose_get_product_display_image( $product ) );
	}

	public function test_display_image_falls_back_to_front_model(): void {
		$product = array(
			'image'            => '',
			'front_model_image' => 'assets/images/model.webp',
			'back_image'       => 'assets/images/back.webp',
			'back_model_image' => '',
		);
		$this->assertSame( 'assets/images/model.webp', skyyrose_get_product_display_image( $product ) );
	}

	public function test_display_image_falls_back_to_back_image(): void {
		$product = array(
			'image'            => '',
			'front_model_image' => '',
			'back_image'       => 'assets/images/back.webp',
			'back_model_image' => '',
		);
		$this->assertSame( 'assets/images/back.webp', skyyrose_get_product_display_image( $product ) );
	}

	public function test_display_image_returns_empty_when_all_slots_empty(): void {
		$product = array(
			'image'            => '',
			'front_model_image' => '',
			'back_image'       => '',
			'back_model_image' => '',
		);
		$this->assertSame( '', skyyrose_get_product_display_image( $product ) );
	}

	public function test_display_image_returns_empty_for_non_array(): void {
		$this->assertSame( '', skyyrose_get_product_display_image( null ) );
		$this->assertSame( '', skyyrose_get_product_display_image( 'string' ) );
	}

	// --- skyyrose_format_price() ------------------------------------------

	private function make_product( bool $published, bool $is_preorder, float $price ): array {
		return compact( 'published', 'is_preorder', 'price' ) + array(
			'sku'        => 'test-001',
			'name'       => 'Test',
			'collection' => 'black-rose',
		);
	}

	public function test_format_price_published_product(): void {
		$p = $this->make_product( true, false, 35.0 );
		$this->assertSame( '$35', skyyrose_format_price( $p ) );
	}

	public function test_format_price_coming_soon_when_unpublished_and_not_preorder(): void {
		$p = $this->make_product( false, false, 0.0 );
		$this->assertSame( 'Coming Soon', skyyrose_format_price( $p ) );
	}

	public function test_format_price_preorder_label_when_preorder_with_no_price(): void {
		$p = $this->make_product( true, true, 0.0 );
		$this->assertSame( 'Pre-Order', skyyrose_format_price( $p ) );
	}

	public function test_format_price_shows_price_for_preorder_with_price(): void {
		$p = $this->make_product( true, true, 100.0 );
		$this->assertSame( '$100', skyyrose_format_price( $p ) );
	}

	public function test_format_price_rounds_to_whole_dollar(): void {
		$p = $this->make_product( true, false, 49.99 );
		$this->assertSame( '$50', skyyrose_format_price( $p ) );
	}

	// --- skyyrose_product_image_uri() -----------------------------------------

	public function test_product_image_uri_empty_path_returns_placeholder(): void {
		$uri = skyyrose_product_image_uri( '' );
		$this->assertStringContainsString( 'placeholder-product.jpg', $uri );
	}

	public function test_product_image_uri_non_empty_path_returns_themed_uri(): void {
		$uri = skyyrose_product_image_uri( 'assets/images/br-001.webp' );
		$this->assertSame( 'https://theme.test/assets/images/br-001.webp', $uri );
	}

	// --- skyyrose_product_url() -----------------------------------------------
	// wc_get_product_id_by_sku() is not defined in stubs, so the WC branch
	// is always skipped — only the catalog-fallback paths are exercised here.

	public function test_product_url_preorder_product_returns_preorder_anchor(): void {
		$url = skyyrose_product_url( 'br-003' );
		$this->assertStringContainsString( '/pre-order/', $url );
		$this->assertStringContainsString( 'br-003', $url );
	}

	public function test_product_url_non_preorder_product_returns_collection_anchor(): void {
		$url = skyyrose_product_url( 'br-001' );
		$this->assertStringContainsString( 'collection-black-rose', $url );
		$this->assertStringContainsString( 'br-001', $url );
	}

	public function test_product_url_unknown_sku_returns_preorder_fallback(): void {
		$url = skyyrose_product_url( 'xx-999' );
		$this->assertStringContainsString( '/pre-order/', $url );
		$this->assertStringContainsString( 'xx-999', $url );
	}

	// --- skyyrose_get_product_dossier() ---------------------------------------
	// Note: all catalog products have existing dossier .md files, so the
	// "file not readable" null path is unreachable with real test data.
	// Tests cover: unknown-SKU null, and the full parse happy path.

	public function test_get_product_dossier_null_for_unknown_sku(): void {
		$this->assertNull( skyyrose_get_product_dossier( 'xx-999' ) );
	}

	public function test_get_product_dossier_returns_array_for_existing_dossier(): void {
		$dossier = skyyrose_get_product_dossier( 'br-002' );
		$this->assertIsArray( $dossier );
		$this->assertArrayHasKey( 'has_editorial_content', $dossier );
		$this->assertArrayHasKey( 'garment_type_lock', $dossier );
		$this->assertArrayHasKey( 'branding', $dossier );
	}

	public function test_get_product_dossier_branding_has_expected_keys(): void {
		$dossier = skyyrose_get_product_dossier( 'br-002' );
		$this->assertIsArray( $dossier['branding'] );
		$this->assertArrayHasKey( 'front', $dossier['branding'] );
		$this->assertArrayHasKey( 'back', $dossier['branding'] );
		$this->assertArrayHasKey( 'other', $dossier['branding'] );
	}

	public function test_get_product_dossier_has_editorial_content_is_bool(): void {
		$dossier = skyyrose_get_product_dossier( 'br-002' );
		$this->assertIsBool( $dossier['has_editorial_content'] );
	}
}
