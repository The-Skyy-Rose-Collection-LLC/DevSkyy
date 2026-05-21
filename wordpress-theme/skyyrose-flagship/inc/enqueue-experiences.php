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
 * @since 5.2.0
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

	// Three.js r147 via CDN with add-on scripts.
	// r147 is the last release that ships /examples/js/ UMD add-ons which attach
	// classes to window.THREE.*  r148+ removed that directory — pinned here to
	// avoid 404s on OrbitControls, GLTFLoader, postprocessing, etc.
	$threejs_ver = '0.147.0';
	$threejs_cdn = 'https://cdn.jsdelivr.net/npm/three@' . $threejs_ver;

	if ( ! wp_script_is( 'threejs', 'enqueued' ) ) {
		wp_enqueue_script( 'threejs', $threejs_cdn . '/build/three.min.js', array(), $threejs_ver, true );
	}

	$addons = array(
		'threejs-orbit-controls'  => '/examples/js/controls/OrbitControls.js',
		'threejs-gltf-loader'     => '/examples/js/loaders/GLTFLoader.js',
		'threejs-draco-loader'    => '/examples/js/loaders/DRACOLoader.js',
		'threejs-rgbe-loader'     => '/examples/js/loaders/RGBELoader.js',
		'threejs-effect-composer' => '/examples/js/postprocessing/EffectComposer.js',
		'threejs-render-pass'     => '/examples/js/postprocessing/RenderPass.js',
		'threejs-unreal-bloom'    => '/examples/js/postprocessing/UnrealBloomPass.js',
		'threejs-shader-pass'     => '/examples/js/postprocessing/ShaderPass.js',
		'threejs-copy-shader'     => '/examples/js/shaders/CopyShader.js',
	);

	foreach ( $addons as $handle => $path ) {
		if ( ! wp_script_is( $handle, 'enqueued' ) ) {
			wp_enqueue_script( $handle, $threejs_cdn . $path, array( 'threejs' ), $threejs_ver, true );
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
