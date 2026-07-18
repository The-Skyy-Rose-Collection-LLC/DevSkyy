<?php
/**
 * Collections World — scroll-scrubbed camera fly-through config.
 *
 * Single source for the scroll-world experience data (scenes + copy + assets),
 * consumed in two places:
 *   - inc/enqueue.php localizes it as `SKYY_SCROLL_WORLD_CONFIG` for the
 *     vanilla engine (assets/js/scroll-world.js) on the 'collections-world' slug.
 *   - template-collections-world.php renders the mount container the engine
 *     builds into.
 *
 * Mirrors the skyyrose_get_experience_config() pattern (inc/experience-rooms.php).
 * Scene stills live in assets/scenes/collections-world/; the .mp4 camera legs are
 * generated later (Higgsfield) and dropped in beside the stills — until they
 * exist the engine falls back to each scene's still poster automatically.
 *
 * @package SkyyRose
 * @since   1.12.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Build the scroll-world engine config (brand kit + 5 scenes + finale CTA).
 *
 * Accents follow collection canon: Signature gold, Black Rose silver,
 * Love Hurts crimson, Kids Capsule + finale rose gold.
 *
 * @since 1.12.0
 * @return array Config array passed verbatim to mountScrollWorld() (JSON-encoded
 *               by wp_localize_script; the engine escapes all copy before render).
 */
function skyyrose_get_collections_world_config() {
	// Memoized: called from both the styles and scripts enqueue passes each
	// request — rebuild the section array once, return the cached copy after.
	static $config = null;
	if ( null !== $config ) {
		return $config;
	}

	$scenes_uri = SKYYROSE_ASSETS_URI . '/scenes/collections-world';
	$shop_url   = esc_url( home_url( '/collections/' ) );

	/**
	 * Helper: build one scene's still + (pending) clip asset URLs.
	 *
	 * @param string $base Scene basename (e.g. 'scene-1-signature').
	 * @return array{still:string,clip:string,clipMobile:string}
	 */
	$assets = static function ( $base ) use ( $scenes_uri ) {
		return array(
			'still'      => esc_url( $scenes_uri . '/' . $base . '.webp' ),
			'clip'       => esc_url( $scenes_uri . '/' . $base . '.mp4' ),
			'clipMobile' => esc_url( $scenes_uri . '/' . $base . '-m.mp4' ),
		);
	};

	$config = array(
		'brand'      => array(
			'name' => 'SkyyRose',
			'href' => esc_url( home_url( '/' ) ),
		),
		'cta'        => array(
			'label' => __( 'Shop', 'skyyrose' ),
			'href'  => $shop_url,
		),
		'hint'       => __( 'scroll to enter', 'skyyrose' ),
		'nav'        => true,
		'atmosphere' => false, // Gothic-noir restraint: dark ground + film grain, no particles.
		'diveScroll' => 1.4,
		'crossfade'  => 0.12,
		'sections'   => array(
			array_merge(
				$assets( 'scene-1-signature' ),
				array(
					'id'      => 'signature',
					'label'   => __( 'Signature', 'skyyrose' ),
					'accent'  => SKYYROSE_COLOR_GOLD,
					'scroll'  => 1.6,
					'linger'  => 0.4,
					'eyebrow' => __( 'The Signature', 'skyyrose' ),
					'title'   => __( 'Luxury Grows from Concrete.', 'skyyrose' ),
					'body'    => __( 'Oakland-born luxury, cut in gold and earned on the block.', 'skyyrose' ),
					'tags'    => array( __( 'Signature', 'skyyrose' ), __( 'Gold', 'skyyrose' ) ),
				)
			),
			array_merge(
				$assets( 'scene-2-black-rose' ),
				array(
					'id'      => 'black-rose',
					'label'   => __( 'Black Rose', 'skyyrose' ),
					'accent'  => SKYYROSE_COLOR_SILVER,
					'linger'  => 0.4,
					'eyebrow' => __( 'Black Rose', 'skyyrose' ),
					'title'   => __( 'Worn As Armor', 'skyyrose' ),
					'body'    => __( 'You wear it because you already stood up.', 'skyyrose' ),
					'tags'    => array( __( 'Black Rose', 'skyyrose' ), __( 'Armor', 'skyyrose' ) ),
				)
			),
			array_merge(
				$assets( 'scene-3-love-hurts' ),
				array(
					'id'      => 'love-hurts',
					'label'   => __( 'Love Hurts', 'skyyrose' ),
					'accent'  => SKYYROSE_COLOR_CRIMSON,
					'linger'  => 0.4,
					'eyebrow' => __( 'Love Hurts', 'skyyrose' ),
					'title'   => __( 'The Bloodline That Raised Me', 'skyyrose' ),
					'body'    => __( 'Crimson and thorn — the love that scarred you is the love that made you.', 'skyyrose' ),
					'tags'    => array( __( 'Love Hurts', 'skyyrose' ), __( 'Crimson', 'skyyrose' ) ),
				)
			),
			array_merge(
				$assets( 'scene-4-kids-capsule' ),
				array(
					'id'      => 'kids-capsule',
					'label'   => __( 'Kids Capsule', 'skyyrose' ),
					'accent'  => SKYYROSE_COLOR_ROSE_GOLD,
					'linger'  => 0.4,
					'eyebrow' => __( 'Kids Capsule', 'skyyrose' ),
					'title'   => __( 'The Next Generation, Suited', 'skyyrose' ),
					'body'    => __( 'The same concrete-luxe, cut for the ones coming up.', 'skyyrose' ),
					'tags'    => array( __( 'Kids Capsule', 'skyyrose' ), __( 'Rose Gold', 'skyyrose' ) ),
				)
			),
			array_merge(
				$assets( 'scene-5-finale' ),
				array(
					'id'      => 'finale',
					'label'   => __( 'The Collection', 'skyyrose' ),
					'accent'  => SKYYROSE_COLOR_ROSE_GOLD,
					'linger'  => 0.3,
					'eyebrow' => __( 'The Skyy Rose Collection', 'skyyrose' ),
					'title'   => __( 'Enter The Collections', 'skyyrose' ),
					'body'    => __( 'Four cinematic worlds, one house built from Oakland concrete.', 'skyyrose' ),
					'cta'     => array(
						'primary' => array(
							'label' => __( 'Shop the Collections', 'skyyrose' ),
							'href'  => $shop_url,
						),
					),
				)
			),
		),
	);

	return $config;
}
