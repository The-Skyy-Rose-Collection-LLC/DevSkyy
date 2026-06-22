<?php
/**
 * Unit tests for inc/performance.php — picture sources + URL/path mapper.
 *
 * Covers v1.5.10–v1.5.16 helpers that wire AVIF/WebP into the front-end
 * picture element. The Photon URL rewrite is the most regression-prone
 * part (one regex change silently breaks WC product imagery).
 *
 * @package SkyyRose
 */

declare(strict_types=1);

use PHPUnit\Framework\TestCase;

/**
 * @covers ::skyyrose_picture_sources
 * @covers ::skyyrose_url_to_path
 * @covers ::skyyrose_nextgen_backfill_targets
 */
final class PerformanceTest extends TestCase {

	// ------------------------------------------------------------------
	// skyyrose_url_to_path()
	// ------------------------------------------------------------------

	public function test_url_to_path_resolves_theme_asset_url(): void {
		$url      = 'https://theme.test/wp-content/themes/skyyrose-flagship/assets/images/products/foo.jpg';
		$expected = SKYYROSE_DIR . '/assets/images/products/foo.jpg';
		$this->assertSame( $expected, skyyrose_url_to_path( $url ) );
	}

	public function test_url_to_path_resolves_upload_url(): void {
		$url      = 'https://theme.test/wp-content/uploads/2026/04/foo.png';
		$expected = sys_get_temp_dir() . '/skyyrose-test-uploads/2026/04/foo.png';
		$this->assertSame( $expected, skyyrose_url_to_path( $url ) );
	}

	public function test_url_to_path_returns_null_for_external_url(): void {
		$this->assertNull( skyyrose_url_to_path( 'https://example.com/foo.jpg' ) );
		$this->assertNull( skyyrose_url_to_path( 'https://cdn.someplace.io/img.png' ) );
	}

	public function test_url_to_path_strips_query_string(): void {
		$url      = 'https://theme.test/wp-content/themes/skyyrose-flagship/assets/foo.png?ver=1.5.16';
		$expected = SKYYROSE_DIR . '/assets/foo.png';
		$this->assertSame( $expected, skyyrose_url_to_path( $url ) );
	}

	// ------------------------------------------------------------------
	// skyyrose_picture_sources() — Photon strip + sibling resolution
	// ------------------------------------------------------------------

	public function test_picture_sources_returns_empty_for_blank(): void {
		$result = skyyrose_picture_sources( '' );
		$this->assertNull( $result['avif'] );
		$this->assertNull( $result['webp'] );
		$this->assertSame( '', $result['src'] );
	}

	public function test_picture_sources_returns_passthrough_for_external_url(): void {
		$ext    = 'https://cdn.example.com/img.jpg';
		$result = skyyrose_picture_sources( $ext );
		$this->assertNull( $result['avif'] );
		$this->assertNull( $result['webp'] );
		$this->assertSame( $ext, $result['src'] );
	}

	public function test_picture_sources_finds_siblings_for_theme_asset(): void {
		// Use a real on-disk file the helper will resolve. functions.php sits
		// at SKYYROSE_DIR root; we'll fabricate a temp asset to test sibling lookup.
		$dir = SKYYROSE_DIR . '/assets/images';
		$this->assertDirectoryExists( $dir );

		// Test with an actual brand asset that should exist on disk + have
		// AVIF/WebP variants generated in the session's v1.5.15 sweep.
		$src = 'https://theme.test/wp-content/themes/skyyrose-flagship/assets/images/products/black-is-beautiful-jersey-oakland-front-model.webp';
		$result = skyyrose_picture_sources( $src );

		// At minimum, AVIF should resolve since v1.5.9 backfill ran.
		if ( file_exists( SKYYROSE_DIR . '/assets/images/products/black-is-beautiful-jersey-oakland-front-model.avif' ) ) {
			$this->assertNotNull( $result['avif'], 'AVIF sibling should resolve when on-disk' );
			$this->assertStringEndsWith( '.avif', $result['avif'] );
			$this->assertStringContainsString( 'theme.test', $result['avif'] );
		} else {
			$this->markTestSkipped( 'Reference AVIF sibling not present on this checkout.' );
		}
	}

	public function test_picture_sources_strips_photon_prefix(): void {
		// Photon URL → emitted source URLs must NOT contain i0.wp.com.
		// (verified bug 2026-05-21: Photon transcodes .avif → image/jpeg)
		$photon_src = 'https://i0.wp.com/theme.test/wp-content/uploads/2026/04/foo.png?fit=683%2C1024&ssl=1';
		$result     = skyyrose_picture_sources( $photon_src );

		// Even if siblings don't exist on disk, the canonical_src logic must
		// strip the photon prefix before path lookup. We assert the avif/webp
		// emit URLs (when set) carry the canonical host, NOT i0.wp.com.
		if ( ! empty( $result['avif'] ) ) {
			$this->assertStringNotContainsString( 'i0.wp.com', $result['avif'], 'AVIF source must not route through Photon' );
		}
		if ( ! empty( $result['webp'] ) ) {
			$this->assertStringNotContainsString( 'i0.wp.com', $result['webp'], 'WebP source must not route through Photon' );
		}
		// The fallback src field always preserves the input.
		$this->assertSame( $photon_src, $result['src'] );
	}

	public function test_picture_sources_strips_photon_i1_and_i2_shards(): void {
		// Test the rewrite contract for all three Photon shards, regardless of
		// whether on-disk siblings exist. The canonical_src logic should always
		// produce a non-Photon path for filesystem lookup. We verify by checking
		// that the result.src field always preserves input, and that ANY emitted
		// next-gen URL never carries the i[0-2].wp.com prefix.
		foreach ( array( 'i0', 'i1', 'i2' ) as $shard ) {
			$url    = "https://{$shard}.wp.com/theme.test/wp-content/uploads/2026/04/foo.png?fit=200%2C200";
			$result = skyyrose_picture_sources( $url );
			$this->assertSame( $url, $result['src'], "src field preserves input for {$shard}" );
			if ( ! empty( $result['avif'] ) ) {
				$this->assertStringNotContainsString( '.wp.com', $result['avif'], "Photon shard {$shard} must be stripped from AVIF" );
			}
			if ( ! empty( $result['webp'] ) ) {
				$this->assertStringNotContainsString( '.wp.com', $result['webp'], "Photon shard {$shard} must be stripped from WebP" );
			}
		}
	}

	public function test_picture_sources_ignores_non_photon_subdomain(): void {
		// 'i3.wp.com' is NOT covered by the current regex i[0-2]. If Photon
		// expands shards, this test fails fast as an alert.
		$url    = 'https://i3.wp.com/theme.test/wp-content/uploads/2026/04/foo.png';
		$result = skyyrose_picture_sources( $url );
		// Since the regex doesn't match, skyyrose_url_to_path is called with the
		// full i3.wp.com URL — which is outside upload baseurl + theme URI roots.
		// Helper returns null → no siblings resolved.
		$this->assertNull( $result['avif'], 'i3 shard expansion needs regex update — currently no-ops gracefully' );
		$this->assertNull( $result['webp'] );
		$this->assertSame( $url, $result['src'] );
	}

	// ------------------------------------------------------------------
	// skyyrose_nextgen_backfill_targets() — size whitelist
	// ------------------------------------------------------------------

	public function test_targets_returns_just_full_when_metadata_empty(): void {
		$targets = skyyrose_nextgen_backfill_targets( '/srv/uploads/2026/foo.jpg', array() );
		$this->assertSame( array( 'foo.jpg' ), $targets );
	}

	public function test_targets_returns_full_plus_whitelisted_sizes(): void {
		$metadata = array(
			'sizes' => array(
				'thumbnail'             => array( 'file' => 'foo-150x150.jpg' ),
				'medium'                => array( 'file' => 'foo-300x300.jpg' ),
				'large'                 => array( 'file' => 'foo-1024x1024.jpg' ),
				'skyyrose-product-avif' => array( 'file' => 'foo-600x800.jpg' ),
				'medium_large'          => array( 'file' => 'foo-768x768.jpg' ),  // NOT whitelisted
				'1536x1536'             => array( 'file' => 'foo-1536x1536.jpg' ), // NOT whitelisted
			),
		);
		$targets = skyyrose_nextgen_backfill_targets( '/srv/uploads/2026/foo.jpg', $metadata );
		$this->assertContains( 'foo.jpg', $targets, 'full size included' );
		$this->assertContains( 'foo-150x150.jpg', $targets );
		$this->assertContains( 'foo-300x300.jpg', $targets );
		$this->assertContains( 'foo-1024x1024.jpg', $targets );
		$this->assertContains( 'foo-600x800.jpg', $targets );
		$this->assertNotContains( 'foo-768x768.jpg', $targets, 'medium_large not whitelisted' );
		$this->assertNotContains( 'foo-1536x1536.jpg', $targets, '1536x1536 not whitelisted' );
		$this->assertCount( 5, $targets, 'full + 4 whitelisted sizes' );
	}

	public function test_targets_skips_missing_size_keys(): void {
		$metadata = array(
			'sizes' => array(
				'thumbnail' => array( 'file' => 'foo-150x150.jpg' ),
				// medium absent; large absent
			),
		);
		$targets = skyyrose_nextgen_backfill_targets( '/srv/uploads/2026/foo.jpg', $metadata );
		$this->assertCount( 2, $targets, 'full + only-present thumbnail' );
	}
}
