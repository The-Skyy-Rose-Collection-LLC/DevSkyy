<?php
/**
 * Tests for inc/brand-colors.php
 *
 * @package SkyyRose
 */

use PHPUnit\Framework\TestCase;

class BrandColorsTest extends TestCase {

	// --- skyyrose_brand_colors() -------------------------------------------

	public function test_brand_colors_returns_array(): void {
		$colors = skyyrose_brand_colors();
		$this->assertIsArray( $colors );
	}

	public function test_brand_colors_has_twelve_keys(): void {
		$this->assertCount( 12, skyyrose_brand_colors() );
	}

	public function test_brand_colors_contains_expected_keys(): void {
		$keys   = array_keys( skyyrose_brand_colors() );
		$expect = array(
			'rose_gold', 'gold', 'crimson', 'silver', 'dark',
			'deep_black', 'deep_red', 'purple', 'navy', 'deep_blue',
			'soft_pink', 'lavender',
		);
		$this->assertSame( $expect, $keys );
	}

	public function test_brand_colors_rose_gold_hex(): void {
		$this->assertSame( '#B76E79', skyyrose_brand_colors()['rose_gold'] );
	}

	public function test_brand_colors_gold_hex(): void {
		$this->assertSame( '#D4AF37', skyyrose_brand_colors()['gold'] );
	}

	public function test_brand_colors_crimson_hex(): void {
		$this->assertSame( '#DC143C', skyyrose_brand_colors()['crimson'] );
	}

	public function test_brand_colors_silver_hex(): void {
		$this->assertSame( '#C0C0C0', skyyrose_brand_colors()['silver'] );
	}

	public function test_brand_colors_dark_hex(): void {
		$this->assertSame( '#0A0A0A', skyyrose_brand_colors()['dark'] );
	}

	// --- skyyrose_hex_to_rgba() -------------------------------------------

	public function test_hex_to_rgba_full_alpha(): void {
		// #B76E79 = R:183 G:110 B:121
		$this->assertSame( 'rgba(183, 110, 121, 1)', skyyrose_hex_to_rgba( '#B76E79', 1.0 ) );
	}

	public function test_hex_to_rgba_partial_alpha(): void {
		$this->assertSame( 'rgba(183, 110, 121, 0.3)', skyyrose_hex_to_rgba( '#B76E79', 0.3 ) );
	}

	public function test_hex_to_rgba_without_hash(): void {
		$this->assertSame( 'rgba(183, 110, 121, 1)', skyyrose_hex_to_rgba( 'B76E79', 1.0 ) );
	}

	public function test_hex_to_rgba_shorthand(): void {
		// #fff expands to #ffffff = 255,255,255
		$this->assertSame( 'rgba(255, 255, 255, 1)', skyyrose_hex_to_rgba( '#fff', 1.0 ) );
	}

	public function test_hex_to_rgba_zero_alpha(): void {
		$this->assertSame( 'rgba(183, 110, 121, 0)', skyyrose_hex_to_rgba( '#B76E79', 0.0 ) );
	}

	public function test_hex_to_rgba_gold(): void {
		// #D4AF37 = R:212 G:175 B:55
		$this->assertSame( 'rgba(212, 175, 55, 1)', skyyrose_hex_to_rgba( '#D4AF37', 1.0 ) );
	}

	// --- Constants ---------------------------------------------------------

	public function test_constants_are_defined(): void {
		$this->assertTrue( defined( 'SKYYROSE_COLOR_ROSE_GOLD' ) );
		$this->assertTrue( defined( 'SKYYROSE_COLOR_GOLD' ) );
		$this->assertTrue( defined( 'SKYYROSE_COLOR_CRIMSON' ) );
		$this->assertTrue( defined( 'SKYYROSE_COLOR_SILVER' ) );
		$this->assertTrue( defined( 'SKYYROSE_COLOR_DARK' ) );
	}

	public function test_constant_rose_gold_value(): void {
		$this->assertSame( '#B76E79', SKYYROSE_COLOR_ROSE_GOLD );
	}
}
