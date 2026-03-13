<?php
/**
 * Enqueue Conversion & Engagement Engines
 *
 * Separated from enqueue.php to keep each file under 800 lines.
 * Contains all optional conversion/engagement engine enqueue functions
 * that layer on top of the core template assets.
 *
 * @package SkyyRose_Flagship
 * @since   3.3.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Helper: Enqueue a CSS + JS engine pair with min/non-min switching.
 *
 * Centralises the $use_min logic so every engine benefits automatically.
 * Files must follow the naming convention: {slug}.css / {slug}.min.css
 * and {slug}.js / {slug}.min.js in the respective asset directories.
 *
 * @since 4.1.0
 *
 * @param string   $handle   Script/style handle (prefixed with 'skyyrose-').
 * @param string   $slug     Base filename without extension (e.g. 'social-proof').
 * @param string[] $css_deps CSS dependency handles. Default: array( 'skyyrose-design-tokens' ).
 * @param string[] $js_deps  JS dependency handles. Default: array().
 * @return void
 */
function skyyrose_enqueue_engine( $handle, $slug, $css_deps = array( 'skyyrose-design-tokens' ), $js_deps = array() ) {

	$css_dir = SKYYROSE_DIR . '/assets/css';
	$css_uri = SKYYROSE_ASSETS_URI . '/css';
	$js_dir  = SKYYROSE_DIR . '/assets/js';
	$js_uri  = SKYYROSE_ASSETS_URI . '/js';
	$use_min = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;

	// CSS.
	$css_min  = $slug . '.min.css';
	$css_full = $slug . '.css';
	$css_file = $use_min && file_exists( $css_dir . '/' . $css_min ) ? $css_min : $css_full;

	if ( file_exists( $css_dir . '/' . $css_file ) ) {
		wp_enqueue_style(
			$handle,
			$css_uri . '/' . $css_file,
			$css_deps,
			SKYYROSE_VERSION
		);
	}

	// JS.
	$js_min  = $slug . '.min.js';
	$js_full = $slug . '.js';
	$js_file = $use_min && file_exists( $js_dir . '/' . $js_min ) ? $js_min : $js_full;

	if ( file_exists( $js_dir . '/' . $js_file ) ) {
		wp_enqueue_script(
			$handle,
			$js_uri . '/' . $js_file,
			$js_deps,
			SKYYROSE_VERSION,
			true
		);
	}
}

/**
 * Enqueue the Social Proof + Urgency Engine on customer-facing pages.
 *
 * Loads purchase notification toasts, live viewer count, scarcity badges,
 * and a sticky pre-order CTA bar across all non-admin pages.
 *
 * @since 3.2.0
 * @return void
 */
function skyyrose_enqueue_social_proof() {
	if ( is_admin() ) {
		return;
	}
	skyyrose_enqueue_engine( 'skyyrose-social-proof', 'social-proof' );
}

/**
 * Enqueue The Pulse — Real-Time Social Proof & Urgency Engine.
 *
 * Loads animated purchase notification toasts, live viewer counts, scarcity
 * badges, VIP countdown banner, and popularity heat on customer-facing pages.
 *
 * @since 3.2.0
 * @return void
 */
function skyyrose_enqueue_the_pulse() {
	if ( is_admin() ) {
		return;
	}
	skyyrose_enqueue_engine( 'skyyrose-the-pulse', 'the-pulse' );
}

/**
 * Enqueue Aurora — Ambient Engagement Engine.
 *
 * Loads the conversion-driving Aurora layer on all customer-facing pages:
 * CTA shimmer, engagement depth tracking, scroll reveals, product card
 * 3D tilt, VIP countdown, and scarcity pulse indicators.
 *
 * @since 3.4.0
 * @return void
 */
function skyyrose_enqueue_aurora_engine() {
	if ( is_admin() ) {
		return;
	}
	skyyrose_enqueue_engine( 'skyyrose-aurora-engine', 'aurora-engine' );
}

/**
 * Enqueue Magnetic Obsidian — Conversion Intelligence Engine.
 *
 * Loads magnetic 3D product card effects, immersive hotspot magnetism,
 * exit-intent capture overlay, A/B variant assignment, and conversion
 * tracking on all customer-facing pages.
 *
 * @since 3.5.0
 * @return void
 */
function skyyrose_enqueue_magnetic_obsidian() {
	if ( is_admin() ) {
		return;
	}
	skyyrose_enqueue_engine( 'skyyrose-magnetic-obsidian', 'magnetic-obsidian' );
}

/**
 * Enqueue Conversion Intelligence Engine.
 *
 * Real-time social proof toasts, urgency countdown timers, stock scarcity
 * indicators, floating pre-order CTA, exit-intent capture, and conversion
 * tracking.
 *
 * @since 3.6.0
 * @return void
 */
function skyyrose_enqueue_conversion_engine() {
	if ( is_admin() ) {
		return;
	}
	skyyrose_enqueue_engine( 'skyyrose-conversion-engine', 'conversion-engine' );
}

/**
 * Enqueue Adaptive Personalization Engine.
 *
 * Behavioral scoring, personalized "Your Picks" recommendations drawer,
 * ambient mood transitions on immersive pages, smart bundle suggestions,
 * and recently-viewed product strip.
 *
 * @since 3.8.0
 * @return void
 */
function skyyrose_enqueue_adaptive_personalization() {
	if ( is_admin() ) {
		return;
	}
	skyyrose_enqueue_engine( 'skyyrose-adaptive-personalization', 'adaptive-personalization' );
}

/**
 * Enqueue Journey Gamification Engine.
 *
 * Room exploration tracking with progress pill, reward reveal upon full
 * collection discovery, achievement badges on static pages, and cross-sell
 * recommendation strip.
 *
 * @since 3.9.0
 * @return void
 */
function skyyrose_enqueue_journey_gamification() {
	if ( is_admin() ) {
		return;
	}
	skyyrose_enqueue_engine( 'skyyrose-journey-gamification', 'journey-gamification' );
}

/**
 * Enqueue Momentum Commerce Engine — "The Closer".
 *
 * Smart Price Anchoring, Live Activity Ticker, Spotlight Moments,
 * Best Seller Glow, and Momentum Score engagement rewards.
 *
 * @since 3.8.0
 * @return void
 */
function skyyrose_enqueue_momentum_commerce() {
	if ( is_admin() ) {
		return;
	}
	skyyrose_enqueue_engine(
		'skyyrose-momentum-commerce',
		'momentum-commerce',
		array( 'skyyrose-design-tokens' ),
		array( 'skyyrose-conversion-engine' )
	);
}

/**
 * Enqueue Velocity — Scroll-Driven Product Storytelling Engine.
 *
 * Apple-style progressive product reveals, scroll spine, momentum
 * section transitions, product spotlight zone, and velocity tracking.
 *
 * @since 4.0.0
 * @return void
 */
function skyyrose_enqueue_velocity_scroll() {
	if ( is_admin() ) {
		return;
	}
	skyyrose_enqueue_engine( 'skyyrose-velocity-scroll', 'velocity-scroll' );
}

/**
 * Enqueue Pulse Engine — Unified Conversion Infrastructure.
 *
 * @since 3.9.0
 * @return void
 */
function skyyrose_enqueue_pulse_engine() {
	if ( is_admin() ) {
		return;
	}
	skyyrose_enqueue_engine( 'skyyrose-pulse-engine', 'pulse-engine' );
}

/*--------------------------------------------------------------
 * Hook Registration — Conversion & Engagement Engines
 *
 * DISABLED for v3.2.0 launch (re-enable post-deploy after Lighthouse audit).
 * Each engine has its own is_admin() guard already.
 *--------------------------------------------------------------*/

/*
 * add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_social_proof', 30 );
 * add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_the_pulse', 32 );
 * add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_aurora_engine', 34 );
 * add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_magnetic_obsidian', 36 );
 * add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_conversion_engine', 38 );
 * add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_adaptive_personalization', 42 );
 * add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_journey_gamification', 44 );
 * add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_momentum_commerce', 45 );
 * add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_velocity_scroll', 46 );
 * add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_pulse_engine', 47 );
 */
