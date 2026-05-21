<?php
/**
 * Enqueue — Three.js collection experiences
 *
 * Loads Three.js + add-ons and the SkyyRose immersive scene scripts on the
 * four template-immersive-*.php pages. Extracted from inc/enqueue.php in
 * v1.5.0 to keep that file under the 800-line cap.
 *
 * Hook priority 65 runs after template scripts (20) and phase2/3/4 enqueues
 * (30/40/42) so the experience scripts can depend on already-registered
 * handles if needed.
 *
 * @package SkyyRose
 * @since   1.5.0
 */

defined( 'ABSPATH' ) || exit;

/**
 * Enqueue collection-specific Three.js experience scenes.
 *
 * @since 1.5.0
 * @return void
 */
function skyyrose_enqueue_collection_experiences() {
	if ( is_admin() ) {
		return;
	}

	$experience_map = array(
		'template-immersive-black-rose.php'   => 'experiences/blackrose-experience',
		'template-immersive-love-hurts.php'   => 'experiences/lovehurts-experience',
		'template-immersive-signature.php'    => 'experiences/signature-experience',
		'template-immersive-kids-capsule.php' => 'experiences/kidscapsule-experience',
	);

	$current_template = get_page_template_slug();

	if ( ! $current_template || ! isset( $experience_map[ $current_template ] ) ) {
		return;
	}

	$use_min = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;
	$js_dir  = SKYYROSE_DIR . '/assets/js';
	$js_uri  = SKYYROSE_ASSETS_URI . '/js';

	// Three.js r147 — self-hosted from assets/js/lib/ to eliminate jsDelivr
	// supply-chain risk. r147 is the last release that ships /examples/js/
	// UMD add-ons which attach classes to window.THREE.*  r148+ removed that
	// directory — pinned here to avoid 404s on OrbitControls, GLTFLoader, etc.
	$threejs_ver  = '0.147.0';
	$threejs_base = SKYYROSE_ASSETS_URI . '/js/lib';

	if ( ! wp_script_is( 'threejs', 'enqueued' ) ) {
		wp_enqueue_script( 'threejs', $threejs_base . '/three.min.js', array(), $threejs_ver, true );
	}

	$addons = array(
		'threejs-orbit-controls'  => '/three-examples/controls/OrbitControls.js',
		'threejs-gltf-loader'     => '/three-examples/loaders/GLTFLoader.js',
		'threejs-draco-loader'    => '/three-examples/loaders/DRACOLoader.js',
		'threejs-rgbe-loader'     => '/three-examples/loaders/RGBELoader.js',
		'threejs-effect-composer' => '/three-examples/postprocessing/EffectComposer.js',
		'threejs-render-pass'     => '/three-examples/postprocessing/RenderPass.js',
		'threejs-unreal-bloom'    => '/three-examples/postprocessing/UnrealBloomPass.js',
		'threejs-shader-pass'     => '/three-examples/postprocessing/ShaderPass.js',
		'threejs-copy-shader'     => '/three-examples/shaders/CopyShader.js',
	);

	foreach ( $addons as $handle => $path ) {
		if ( ! wp_script_is( $handle, 'enqueued' ) ) {
			wp_enqueue_script( $handle, $threejs_base . $path, array( 'threejs' ), $threejs_ver, true );
		}
	}

	// Experience base class.
	$base_file = $use_min && file_exists( $js_dir . '/experiences/experience-base.min.js' )
		? 'experiences/experience-base.min.js' : 'experiences/experience-base.js';
	if ( file_exists( $js_dir . '/' . $base_file ) ) {
		wp_enqueue_script( 'skyyrose-experience-base', $js_uri . '/' . $base_file, array( 'threejs' ), SKYYROSE_VERSION, true );
	}

	// Luxury animations.
	$anim_file = $use_min && file_exists( $js_dir . '/experiences/luxury-animations.min.js' )
		? 'experiences/luxury-animations.min.js' : 'experiences/luxury-animations.js';
	if ( file_exists( $js_dir . '/' . $anim_file ) ) {
		wp_enqueue_script( 'skyyrose-luxury-animations', $js_uri . '/' . $anim_file, array( 'skyyrose-experience-base' ), SKYYROSE_VERSION, true );
	}

	// Collection-specific scene.
	$scene_slug = $experience_map[ $current_template ];
	$scene_file = $use_min && file_exists( $js_dir . '/' . $scene_slug . '.min.js' )
		? $scene_slug . '.min.js' : $scene_slug . '.js';
	if ( file_exists( $js_dir . '/' . $scene_file ) ) {
		wp_enqueue_script( 'skyyrose-collection-experience', $js_uri . '/' . $scene_file, array( 'skyyrose-experience-base', 'skyyrose-luxury-animations' ), SKYYROSE_VERSION, true );
	}

	// Init-3D orchestrator.
	$init_file = $use_min && file_exists( $js_dir . '/experiences/init-3d.min.js' )
		? 'experiences/init-3d.min.js' : 'experiences/init-3d.js';
	if ( file_exists( $js_dir . '/' . $init_file ) ) {
		wp_enqueue_script( 'skyyrose-3d-init', $js_uri . '/' . $init_file, array( 'skyyrose-collection-experience' ), SKYYROSE_VERSION, true );

		// Provide runtime config that init-3d.js reads from window.skyyrose3D.
		wp_localize_script(
			'skyyrose-3d-init',
			'skyyrose3D',
			array(
				'debug'    => defined( 'WP_DEBUG' ) && WP_DEBUG,
				'lazyLoad' => true,
				'isMobile' => wp_is_mobile(),
				'siteUrl'  => esc_url( home_url() ),
				'ajaxUrl'  => admin_url( 'admin-ajax.php' ),
				'nonce'    => wp_create_nonce( 'skyyrose_3d_nonce' ),
			)
		);
	}
}

add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_collection_experiences', 65 );
