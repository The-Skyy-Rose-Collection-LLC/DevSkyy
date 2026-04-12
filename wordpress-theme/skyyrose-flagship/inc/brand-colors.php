<?php
/**
 * Brand Colors — Single Source of Truth
 *
 * All hex color codes for the SkyyRose brand live here. PHP templates and
 * functions should reference these constants instead of hardcoding hex values.
 *
 * The canonical CSS source is assets/css/design-tokens.css (CSS custom
 * properties). This file mirrors those values for PHP consumers.
 *
 * @package SkyyRose_Flagship
 * @since   6.4.0
 */

defined( 'ABSPATH' ) || exit;

// -- Core brand palette -------------------------------------------------------

define( 'SKYYROSE_COLOR_ROSE_GOLD', '#B76E79' );  // Global accent, Kids Capsule fallback
define( 'SKYYROSE_COLOR_GOLD', '#D4AF37' );  // Signature collection accent
define( 'SKYYROSE_COLOR_CRIMSON', '#DC143C' );  // Love Hurts accent
define( 'SKYYROSE_COLOR_SILVER', '#C0C0C0' );  // Black Rose accent
define( 'SKYYROSE_COLOR_DARK', '#0A0A0A' );  // Background, primary dark

// -- Extended palette ---------------------------------------------------------

define( 'SKYYROSE_COLOR_DEEP_BLACK', '#1A1A2E' );  // Black Rose primary
define( 'SKYYROSE_COLOR_DEEP_RED', '#8B0000' );  // Love Hurts primary
define( 'SKYYROSE_COLOR_PURPLE', '#4B0082' );  // Love Hurts secondary
define( 'SKYYROSE_COLOR_NAVY', '#16213E' );  // Black Rose secondary
define( 'SKYYROSE_COLOR_DEEP_BLUE', '#0F3460' );  // Black Rose accent
define( 'SKYYROSE_COLOR_SOFT_PINK', '#FFB6C1' );  // Kids Capsule primary
define( 'SKYYROSE_COLOR_LAVENDER', '#FFF0F5' );  // Kids Capsule secondary

/**
 * Get all brand colors as an associative array.
 *
 * @since  6.4.0
 * @return array<string, string>
 */
function skyyrose_brand_colors(): array {
	return array(
		'rose_gold'  => SKYYROSE_COLOR_ROSE_GOLD,
		'gold'       => SKYYROSE_COLOR_GOLD,
		'crimson'    => SKYYROSE_COLOR_CRIMSON,
		'silver'     => SKYYROSE_COLOR_SILVER,
		'dark'       => SKYYROSE_COLOR_DARK,
		'deep_black' => SKYYROSE_COLOR_DEEP_BLACK,
		'deep_red'   => SKYYROSE_COLOR_DEEP_RED,
		'purple'     => SKYYROSE_COLOR_PURPLE,
		'navy'       => SKYYROSE_COLOR_NAVY,
		'deep_blue'  => SKYYROSE_COLOR_DEEP_BLUE,
		'soft_pink'  => SKYYROSE_COLOR_SOFT_PINK,
		'lavender'   => SKYYROSE_COLOR_LAVENDER,
	);
}

/**
 * Convert a hex color to an rgba() string with given alpha.
 *
 * @since  6.4.0
 * @param  string $hex   Hex color (with or without #).
 * @param  float  $alpha Alpha value 0.0-1.0.
 * @return string rgba() CSS value.
 */
function skyyrose_hex_to_rgba( string $hex, float $alpha = 1.0 ): string {
	$hex = ltrim( $hex, '#' );
	if ( strlen( $hex ) === 3 ) {
		$hex = $hex[0] . $hex[0] . $hex[1] . $hex[1] . $hex[2] . $hex[2];
	}
	$r = hexdec( substr( $hex, 0, 2 ) );
	$g = hexdec( substr( $hex, 2, 2 ) );
	$b = hexdec( substr( $hex, 4, 2 ) );
	return sprintf( 'rgba(%d, %d, %d, %s)', $r, $g, $b, $alpha );
}
