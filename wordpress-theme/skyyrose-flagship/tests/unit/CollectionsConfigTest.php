<?php
/**
 * Tests for inc/collections-config.php
 *
 * @package SkyyRose
 */

use PHPUnit\Framework\TestCase;

class CollectionsConfigTest extends TestCase {

	private const SLUGS = array( 'black-rose', 'love-hurts', 'signature', 'kids-capsule' );

	// --- skyyrose_get_collections_config() ---------------------------------

	public function test_returns_array(): void {
		$this->assertIsArray( skyyrose_get_collections_config() );
	}

	public function test_has_four_collections(): void {
		$this->assertCount( 4, skyyrose_get_collections_config() );
	}

	public function test_all_expected_slugs_present(): void {
		$config = skyyrose_get_collections_config();
		foreach ( self::SLUGS as $slug ) {
			$this->assertArrayHasKey( $slug, $config, "Missing slug: $slug" );
		}
	}

	public function test_each_collection_has_required_keys(): void {
		$required = array( 'slug', 'label', 'accent', 'glow', 'tagline', 'description', 'page_url', 'palette' );
		foreach ( skyyrose_get_collections_config() as $slug => $config ) {
			foreach ( $required as $key ) {
				$this->assertArrayHasKey( $key, $config, "Collection '$slug' missing key '$key'" );
			}
		}
	}

	public function test_black_rose_accent_is_silver(): void {
		$config = skyyrose_get_collections_config();
		$this->assertSame( SKYYROSE_COLOR_SILVER, $config['black-rose']['accent'] );
	}

	public function test_love_hurts_accent_is_crimson(): void {
		$config = skyyrose_get_collections_config();
		$this->assertSame( SKYYROSE_COLOR_CRIMSON, $config['love-hurts']['accent'] );
	}

	public function test_signature_accent_is_gold(): void {
		$config = skyyrose_get_collections_config();
		$this->assertSame( SKYYROSE_COLOR_GOLD, $config['signature']['accent'] );
	}

	public function test_page_url_contains_home_url(): void {
		$config = skyyrose_get_collections_config();
		$this->assertStringContainsString( 'skyyrose.co', $config['black-rose']['page_url'] );
	}

	public function test_front_page_show_on_front_set(): void {
		// Every collection must have show_on_front declared (true OR false).
		// Kids Capsule is intentionally false while in coming-soon state.
		foreach ( skyyrose_get_collections_config() as $slug => $config ) {
			$this->assertArrayHasKey( 'front_page', $config, "Collection '$slug' missing front_page block" );
			$this->assertArrayHasKey(
				'show_on_front',
				$config['front_page'],
				"Collection '$slug' missing front_page.show_on_front"
			);
			$this->assertIsBool(
				$config['front_page']['show_on_front'],
				"Collection '$slug' show_on_front must be a bool"
			);
		}
	}

	// --- skyyrose_get_collection() -----------------------------------------

	public function test_get_collection_returns_array_for_valid_slug(): void {
		$result = skyyrose_get_collection( 'black-rose' );
		$this->assertIsArray( $result );
	}

	public function test_get_collection_returns_null_for_unknown_slug(): void {
		$this->assertNull( skyyrose_get_collection( 'nonexistent' ) );
	}

	public function test_get_collection_slug_field_matches(): void {
		$config = skyyrose_get_collection( 'signature' );
		$this->assertSame( 'signature', $config['slug'] );
	}

	// --- skyyrose_get_collection_field() -----------------------------------

	public function test_get_collection_field_returns_correct_value(): void {
		$this->assertSame(
			SKYYROSE_COLOR_SILVER,
			skyyrose_get_collection_field( 'black-rose', 'accent' )
		);
	}

	public function test_get_collection_field_default_for_unknown_collection(): void {
		$this->assertSame( 'fallback', skyyrose_get_collection_field( 'unknown', 'accent', 'fallback' ) );
	}

	public function test_get_collection_field_default_for_missing_field(): void {
		$this->assertNull( skyyrose_get_collection_field( 'black-rose', 'nonexistent_field' ) );
	}

	// --- skyyrose_get_cross_nav() ------------------------------------------

	public function test_cross_nav_excludes_given_slug(): void {
		$nav = skyyrose_get_cross_nav( 'black-rose' );
		$slugs = array_column( $nav, 'slug' );
		$this->assertNotContains( 'black-rose', $slugs );
	}

	public function test_cross_nav_returns_three_items_when_excluding_one(): void {
		$this->assertCount( 3, skyyrose_get_cross_nav( 'black-rose' ) );
	}

	public function test_cross_nav_entries_have_required_keys(): void {
		$nav = skyyrose_get_cross_nav( 'signature' );
		foreach ( $nav as $entry ) {
			$this->assertArrayHasKey( 'slug', $entry );
			$this->assertArrayHasKey( 'name', $entry );
			$this->assertArrayHasKey( 'desc', $entry );
			$this->assertArrayHasKey( 'class', $entry );
		}
	}

	public function test_cross_nav_urls_are_canonical_collections_routes(): void {
		$nav = skyyrose_get_cross_nav( 'black-rose' );
		foreach ( $nav as $entry ) {
			$this->assertStringNotContainsString( '/collection-', $entry['url'] );
			$this->assertStringContainsString( '/collections/' . $entry['slug'] . '/', $entry['url'] );
		}
	}

	// --- skyyrose_get_front_page_collections() -----------------------------

	public function test_front_page_collections_returns_visible_items_only(): void {
		// Helper filters by show_on_front. Currently 3 visible (Signature,
		// Black Rose, Love Hurts); Kids Capsule is coming-soon so excluded.
		$visible_count = 0;
		foreach ( skyyrose_get_collections_config() as $config ) {
			if ( ! empty( $config['front_page']['show_on_front'] ) ) {
				++$visible_count;
			}
		}
		$this->assertCount( $visible_count, skyyrose_get_front_page_collections() );
		$this->assertGreaterThanOrEqual( 1, $visible_count, 'At least one collection must be visible on front page' );
	}

	public function test_front_page_collections_have_required_keys(): void {
		$required = array( 'slug', 'class', 'name', 'title', 'tagline', 'label', 'num', 'link', 'image' );
		foreach ( skyyrose_get_front_page_collections() as $entry ) {
			foreach ( $required as $key ) {
				$this->assertArrayHasKey( $key, $entry, "Front-page entry missing key '$key'" );
			}
		}
	}

	public function test_front_page_collections_image_contains_uri(): void {
		foreach ( skyyrose_get_front_page_collections() as $entry ) {
			$this->assertStringContainsString( 'theme.test', $entry['image'] );
		}
	}
}
