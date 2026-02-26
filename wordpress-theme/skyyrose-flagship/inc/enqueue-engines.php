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
 * Enqueue the Social Proof + Urgency Engine on customer-facing pages.
 *
 * Loads purchase notification toasts, live viewer count, scarcity badges,
 * and a sticky pre-order CTA bar across all non-admin pages.
 *
 * @since 3.2.0
 * @return void
 */
function skyyrose_enqueue_social_proof() {

	// Skip admin context.
	if ( is_admin() ) {
		return;
	}

	$css_path = SKYYROSE_DIR . '/assets/css/social-proof.css';
	if ( file_exists( $css_path ) ) {
		wp_enqueue_style(
			'skyyrose-social-proof',
			SKYYROSE_ASSETS_URI . '/css/social-proof.css',
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	$js_path = SKYYROSE_DIR . '/assets/js/social-proof.js';
	if ( file_exists( $js_path ) ) {
		wp_enqueue_script(
			'skyyrose-social-proof',
			SKYYROSE_ASSETS_URI . '/js/social-proof.js',
			array(),
			SKYYROSE_VERSION,
			true
		);
	}
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

	// Skip admin context.
	if ( is_admin() ) {
		return;
	}

	$css_path = SKYYROSE_DIR . '/assets/css/the-pulse.css';
	if ( file_exists( $css_path ) ) {
		wp_enqueue_style(
			'skyyrose-the-pulse',
			SKYYROSE_ASSETS_URI . '/css/the-pulse.css',
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	$js_path = SKYYROSE_DIR . '/assets/js/the-pulse.js';
	if ( file_exists( $js_path ) ) {
		wp_enqueue_script(
			'skyyrose-the-pulse',
			SKYYROSE_ASSETS_URI . '/js/the-pulse.js',
			array(),
			SKYYROSE_VERSION,
			true
		);
	}
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

	// Skip admin context.
	if ( is_admin() ) {
		return;
	}

	$css_path = SKYYROSE_DIR . '/assets/css/aurora-engine.css';
	if ( file_exists( $css_path ) ) {
		wp_enqueue_style(
			'skyyrose-aurora-engine',
			SKYYROSE_ASSETS_URI . '/css/aurora-engine.css',
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	$js_path = SKYYROSE_DIR . '/assets/js/aurora-engine.js';
	if ( file_exists( $js_path ) ) {
		wp_enqueue_script(
			'skyyrose-aurora-engine',
			SKYYROSE_ASSETS_URI . '/js/aurora-engine.js',
			array(),
			SKYYROSE_VERSION,
			true
		);
	}
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

	// Skip admin context.
	if ( is_admin() ) {
		return;
	}

	$css_path = SKYYROSE_DIR . '/assets/css/magnetic-obsidian.css';
	if ( file_exists( $css_path ) ) {
		wp_enqueue_style(
			'skyyrose-magnetic-obsidian',
			SKYYROSE_ASSETS_URI . '/css/magnetic-obsidian.css',
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	$js_path = SKYYROSE_DIR . '/assets/js/magnetic-obsidian.js';
	if ( file_exists( $js_path ) ) {
		wp_enqueue_script(
			'skyyrose-magnetic-obsidian',
			SKYYROSE_ASSETS_URI . '/js/magnetic-obsidian.js',
			array(),
			SKYYROSE_VERSION,
			true
		);
	}
}

/**
 * Enqueue Conversion Intelligence Engine.
 *
 * Real-time social proof toasts, urgency countdown timers, stock scarcity
 * indicators, floating pre-order CTA, exit-intent capture, and conversion
 * tracking. Proven to increase conversion 15-34% (Spiegel Research Center).
 *
 * @since 3.6.0
 * @return void
 */
function skyyrose_enqueue_conversion_engine() {

	// Skip admin context.
	if ( is_admin() ) {
		return;
	}

	$css_path = SKYYROSE_DIR . '/assets/css/conversion-engine.css';
	if ( file_exists( $css_path ) ) {
		wp_enqueue_style(
			'skyyrose-conversion-engine',
			SKYYROSE_ASSETS_URI . '/css/conversion-engine.css',
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	$js_path = SKYYROSE_DIR . '/assets/js/conversion-engine.js';
	if ( file_exists( $js_path ) ) {
		wp_enqueue_script(
			'skyyrose-conversion-engine',
			SKYYROSE_ASSETS_URI . '/js/conversion-engine.js',
			array(),
			SKYYROSE_VERSION,
			true
		);
	}
}

/**
 * Enqueue Adaptive Personalization Engine.
 *
 * Behavioral scoring, personalized "Your Picks" recommendations drawer,
 * ambient mood transitions on immersive pages, smart bundle suggestions,
 * and recently-viewed product strip. Research shows personalized
 * recommendations increase AOV by 10-30% (McKinsey, 2023).
 *
 * @since 3.8.0
 * @return void
 */
function skyyrose_enqueue_adaptive_personalization() {

	// Skip admin context.
	if ( is_admin() ) {
		return;
	}

	$css_path = SKYYROSE_DIR . '/assets/css/adaptive-personalization.css';
	if ( file_exists( $css_path ) ) {
		wp_enqueue_style(
			'skyyrose-adaptive-personalization',
			SKYYROSE_ASSETS_URI . '/css/adaptive-personalization.css',
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	$js_path = SKYYROSE_DIR . '/assets/js/adaptive-personalization.js';
	if ( file_exists( $js_path ) ) {
		wp_enqueue_script(
			'skyyrose-adaptive-personalization',
			SKYYROSE_ASSETS_URI . '/js/adaptive-personalization.js',
			array(),
			SKYYROSE_VERSION,
			true
		);
	}
}

/**
 * Enqueue Journey Gamification Engine.
 *
 * Room exploration tracking with progress pill, reward reveal upon full
 * collection discovery, achievement badges on static pages, and cross-sell
 * recommendation strip. Gamification increases engagement 48% and conversion
 * 15-30% (Badgeville / Gigya research).
 *
 * @since 3.9.0
 * @return void
 */
function skyyrose_enqueue_journey_gamification() {

	// Skip admin context.
	if ( is_admin() ) {
		return;
	}

	$css_path = SKYYROSE_DIR . '/assets/css/journey-gamification.css';
	if ( file_exists( $css_path ) ) {
		wp_enqueue_style(
			'skyyrose-journey-gamification',
			SKYYROSE_ASSETS_URI . '/css/journey-gamification.css',
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	$js_path = SKYYROSE_DIR . '/assets/js/journey-gamification.js';
	if ( file_exists( $js_path ) ) {
		wp_enqueue_script(
			'skyyrose-journey-gamification',
			SKYYROSE_ASSETS_URI . '/js/journey-gamification.js',
			array(),
			SKYYROSE_VERSION,
			true
		);
	}
}

/**
 * Enqueue Momentum Commerce Engine — "The Closer".
 *
 * Three research-backed conversion techniques:
 *   1. Smart Price Anchoring (Kahneman & Tversky anchoring bias — 20-50% lift)
 *   2. Live Activity Ticker (Spiegel Research — 15-34% social proof lift)
 *   3. Spotlight Moments + Best Seller Glow (Thaler & Sunstein nudge theory)
 *   4. Momentum Score — engagement rewards that drive repeat interaction
 *
 * @since 3.8.0
 * @return void
 */
function skyyrose_enqueue_momentum_commerce() {

	// Skip admin context.
	if ( is_admin() ) {
		return;
	}

	$css_path = SKYYROSE_DIR . '/assets/css/momentum-commerce.css';
	if ( file_exists( $css_path ) ) {
		wp_enqueue_style(
			'skyyrose-momentum-commerce',
			SKYYROSE_ASSETS_URI . '/css/momentum-commerce.css',
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	$js_path = SKYYROSE_DIR . '/assets/js/momentum-commerce.js';
	if ( file_exists( $js_path ) ) {
		wp_enqueue_script(
			'skyyrose-momentum-commerce',
			SKYYROSE_ASSETS_URI . '/js/momentum-commerce.js',
			array( 'skyyrose-conversion-engine' ),
			SKYYROSE_VERSION,
			true
		);
	}
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

	// Skip admin context.
	if ( is_admin() ) {
		return;
	}

	$css_path = SKYYROSE_DIR . '/assets/css/velocity-scroll.css';
	if ( file_exists( $css_path ) ) {
		wp_enqueue_style(
			'skyyrose-velocity-scroll',
			SKYYROSE_ASSETS_URI . '/css/velocity-scroll.css',
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	$js_path = SKYYROSE_DIR . '/assets/js/velocity-scroll.js';
	if ( file_exists( $js_path ) ) {
		wp_enqueue_script(
			'skyyrose-velocity-scroll',
			SKYYROSE_ASSETS_URI . '/js/velocity-scroll.js',
			array(),
			SKYYROSE_VERSION,
			true
		);
	}
}

/**
 * Enqueue Pulse Engine — Unified Conversion Infrastructure.
 *
 * @since 3.9.0
 * @return void
 */
function skyyrose_enqueue_pulse_engine() {

	// Skip admin context.
	if ( is_admin() ) {
		return;
	}

	$css_path = SKYYROSE_DIR . '/assets/css/pulse-engine.css';
	if ( file_exists( $css_path ) ) {
		wp_enqueue_style(
			'skyyrose-pulse-engine',
			SKYYROSE_ASSETS_URI . '/css/pulse-engine.css',
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	$js_path = SKYYROSE_DIR . '/assets/js/pulse-engine.js';
	if ( file_exists( $js_path ) ) {
		wp_enqueue_script(
			'skyyrose-pulse-engine',
			SKYYROSE_ASSETS_URI . '/js/pulse-engine.js',
			array(),
			SKYYROSE_VERSION,
			true
		);
	}
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
