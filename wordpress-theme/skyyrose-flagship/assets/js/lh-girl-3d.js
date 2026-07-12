/**
 * Love Hurts Girl — Walk-On Cameo
 *
 * Loads the Love Hurts Girl 3D model (draco GLB, single baked walk clip)
 * and walks her once across the embedded immersive scene on the
 * /collections/love-hurts/ page, then tears everything down. She is a
 * scene resident, not a site host: no state machine, no chat, no chips —
 * that job belongs to the global Skyy mascot (skyy-3d.js), which owns the
 * bottom-right corner on this page. The girl enters from the LEFT so the
 * two never collide.
 *
 * Decorative enhancement contract: under prefers-reduced-motion, missing
 * WebGL, a missing scene container, or any load failure the script exits
 * without touching the page — the scene renders exactly as it does today.
 *
 * Dependencies: Three.js r170+ (shared window globals with skyy-3d.js).
 *
 * @package SkyyRose_Flagship
 * @since   1.11.0
 */

( function () {
	'use strict';

	// -------------------------------------------------------------------------
	// Config
	// -------------------------------------------------------------------------

	/** Model URL — injected by wp_localize_script as LH_GIRL_CONFIG.modelUrl
	 *  (carries an explicit ?ver= for WP.com edge-cache busting). */
	var MODEL_URL = ( window.LH_GIRL_CONFIG && window.LH_GIRL_CONFIG.modelUrl )
		? window.LH_GIRL_CONFIG.modelUrl
		: null;

	var CONTAINER_SELECTOR = '.immersive-scene.immersive-love-hurts';
	var CANVAS_ID          = 'lh-girl-3d-canvas';
	var CHARACTER_W        = 260;  // px — canvas width
	var CHARACTER_H        = 400;  // px — canvas height
	var BOTTOM_OFFSET      = '7%'; // above the scene's floor line
	var CLIP_WALK          = 'girlwalk_baked'; // lowercased clip name in the GLB
	/** Facing correction so she looks toward +X (her travel direction).
	 *  The rig exports glTF-forward (-Z); -90° about Y turns -Z into +X. */
	var FACING_Y = -Math.PI / 2;
	/** Horizontal speed, expressed as canvas-widths per walk cycle (1s clip).
	 *  0.85 keeps foot-slide imperceptible at cameo scale. */
	var SPEED_CANVAS_WIDTHS_PER_CYCLE = 0.85;

	/** Best-effort theme assets base for the Draco decoder path — same
	 *  fallback contract as skyy-3d.js. */
	function assetsUri() {
		return ( window.skyyRoseData && window.skyyRoseData.assetsUri )
			? window.skyyRoseData.assetsUri
			: '/wp-content/themes/skyyrose-flagship/assets';
	}
	var DRACO_DECODER_PATH = assetsUri() + '/js/lib/draco/';

	// -------------------------------------------------------------------------
	// Hard exits — the cameo is additive, never load-bearing
	// -------------------------------------------------------------------------

	if ( ! MODEL_URL ) return;

	if ( window.matchMedia( '(prefers-reduced-motion: reduce)' ).matches ) {
		// A character that ONLY walks has no meaningful static pose to offer
		// (unlike Skyy, who poses on her idle clip) — skip entirely.
		return;
	}

	var container = document.querySelector( CONTAINER_SELECTOR );
	if ( ! container ) return;

	// -------------------------------------------------------------------------
	// State
	// -------------------------------------------------------------------------

	var scene, camera, renderer, mixer, clock, canvas;
	var travelX     = 0;     // current canvas translateX in px
	var loopRunning = false;
	var done        = false; // cameo finished (or failed) — everything torn down

	// -------------------------------------------------------------------------
	// Three.js bootstrap — shares the window globals with skyy-3d.js, so on a
	// page where both run, three.js is fetched exactly once.
	// -------------------------------------------------------------------------

	function loadThree( callback ) {
		if ( window.THREE && window.THREE_GLTFLoader && window.THREE_DRACOLoader ) {
			callback( window.THREE );
			return;
		}

		var base = 'https://cdn.jsdelivr.net/npm/three@0.170.0';

		// /+esm endpoints rewrite the loaders' bare `from 'three'` specifiers to
		// jsdelivr's own ESM URL for the same version — one shared three
		// instance, no importmap needed. jsdelivr is an allowed script-src
		// origin (inc/security.php); the Draco decoder binaries stay
		// self-hosted because their runtime fetch falls under connect-src.
		var injectScript = document.createElement( 'script' );
		injectScript.type = 'module';
		injectScript.textContent = [
			"import * as THREE from '" + base + "/+esm';",
			"import { GLTFLoader } from '" + base + "/examples/jsm/loaders/GLTFLoader.js/+esm';",
			"import { DRACOLoader } from '" + base + "/examples/jsm/loaders/DRACOLoader.js/+esm';",
			"window.THREE = THREE;",
			"window.THREE_GLTFLoader = GLTFLoader;",
			"window.THREE_DRACOLoader = DRACOLoader;",
			"document.dispatchEvent(new Event('three-ready'));",
		].join( '\n' );

		document.head.appendChild( injectScript );

		document.addEventListener( 'three-ready', function onReady() {
			document.removeEventListener( 'three-ready', onReady );
			callback( window.THREE );
		} );
	}

	// -------------------------------------------------------------------------
	// Scene setup
	// -------------------------------------------------------------------------

	function initScene( THREE ) {
		canvas = document.createElement( 'canvas' );
		canvas.id = CANVAS_ID;
		canvas.setAttribute( 'aria-hidden', 'true' );
		// Inline-styled on purpose: one decorative, JS-owned element — keeping
		// its box model here avoids a CSS build round-trip for a single node.
		canvas.style.cssText = [
			'position:absolute',
			'bottom:' + BOTTOM_OFFSET,
			'left:0',
			'width:' + CHARACTER_W + 'px',
			'height:' + CHARACTER_H + 'px',
			'z-index:2', // above scene layers/vignette, below hotspots + panel
			'pointer-events:none',
			'transform:translateX(-' + ( CHARACTER_W + 20 ) + 'px)',
			'will-change:transform',
		].join( ';' );
		container.appendChild( canvas );

		try {
			renderer = new THREE.WebGLRenderer( {
				canvas: canvas,
				alpha: true,
				antialias: true,
				powerPreference: 'low-power',
			} );
		} catch ( e ) {
			// No WebGL — remove the canvas, scene stays untouched.
			teardown();
			return;
		}
		renderer.setPixelRatio( Math.min( window.devicePixelRatio, 2 ) );
		renderer.setSize( CHARACTER_W, CHARACTER_H );
		renderer.shadowMap.enabled = false;
		renderer.outputColorSpace = THREE.SRGBColorSpace;

		scene = new THREE.Scene();

		camera = new THREE.PerspectiveCamera( 30, CHARACTER_W / CHARACTER_H, 0.1, 50 );
		camera.position.set( 0, 1.2, 5 );
		camera.lookAt( 0, 0.9, 0 );

		// Crimson-warmed key against the cathedral's low light — Love Hurts
		// accent (#DC143C) folded into the rim, not painted on the model.
		scene.add( new THREE.AmbientLight( 0xffffff, 1.3 ) );
		var key = new THREE.DirectionalLight( 0xfff0ea, 1.7 );
		key.position.set( 2, 4, 3 );
		scene.add( key );
		var rim = new THREE.DirectionalLight( 0xdc143c, 0.35 );
		rim.position.set( -3, 2, -2 );
		scene.add( rim );

		clock = new THREE.Clock();

		loadModel( THREE );
	}

	// -------------------------------------------------------------------------
	// Model
	// -------------------------------------------------------------------------

	function loadModel( THREE ) {
		var GLTFLoader = window.THREE_GLTFLoader ||
			( window.THREE && window.THREE.GLTFLoader );
		if ( ! GLTFLoader ) {
			teardown();
			return;
		}

		var loader = new GLTFLoader();

		// lh-girl.glb declares KHR_draco_mesh_compression as REQUIRED — without
		// the decoder the load fails outright (same wiring rule as skyy.glb).
		var DRACOLoaderClass = window.THREE_DRACOLoader || ( window.THREE && window.THREE.DRACOLoader );
		if ( DRACOLoaderClass ) {
			var dracoLoader = new DRACOLoaderClass();
			dracoLoader.setDecoderPath( DRACO_DECODER_PATH );
			loader.setDRACOLoader( dracoLoader );
		}

		loader.load(
			MODEL_URL,
			function ( gltf ) {
				if ( done ) return; // torn down while downloading (e.g. tab churn)

				var model = gltf.scene;

				// Scale FIRST, then centre from a recomputed box — offsets must
				// be in post-scale units (same lesson skyy-3d.js documents).
				var size = new THREE.Box3().setFromObject( model ).getSize( new THREE.Vector3() );
				model.scale.setScalar( 1.8 / size.y );
				var box = new THREE.Box3().setFromObject( model );
				var centre = box.getCenter( new THREE.Vector3() );
				model.position.x -= centre.x;
				model.position.z -= centre.z;
				model.position.y -= box.min.y; // feet on the origin plane
				model.rotation.y = FACING_Y;   // face the travel direction

				model.traverse( function ( child ) {
					if ( child.isMesh ) {
						// Skinned mesh + baked clip: the static bounding sphere
						// leaves the frustum mid-stride and the mesh vanishes
						// unless culling is disabled.
						if ( child.isSkinnedMesh ) child.frustumCulled = false;
						child.castShadow    = false;
						child.receiveShadow = false;
					}
				} );

				scene.add( model );

				if ( ! gltf.animations || ! gltf.animations.length ) {
					// A cameo with no walk clip is a statue sliding across the
					// scene — worse than nothing. Bail out.
					teardown();
					return;
				}

				mixer = new THREE.AnimationMixer( model );
				var clip = null;
				for ( var i = 0; i < gltf.animations.length; i++ ) {
					if ( gltf.animations[ i ].name.toLowerCase() === CLIP_WALK ) {
						clip = gltf.animations[ i ];
						break;
					}
				}
				mixer.clipAction( clip || gltf.animations[ 0 ] ).play();

				startLoop();
			},
			undefined,
			function () {
				teardown();
			}
		);
	}

	// -------------------------------------------------------------------------
	// Walk loop — canvas translates left→right; the clip supplies the legs
	// -------------------------------------------------------------------------

	var speedPxPerSec = CHARACTER_W * SPEED_CANVAS_WIDTHS_PER_CYCLE; // clip cycle = 1s

	function render() {
		var delta = clock.getDelta();
		mixer.update( delta );

		travelX += speedPxPerSec * delta;
		var exitX = container.clientWidth + CHARACTER_W;
		canvas.style.transform =
			'translateX(' + ( travelX - ( CHARACTER_W + 20 ) ) + 'px)';

		renderer.render( scene, camera );

		if ( travelX >= exitX ) {
			// Off the far edge — cameo over, free everything.
			teardown();
		}
	}

	function startLoop() {
		if ( done || loopRunning || ! renderer ) return;
		clock.getDelta(); // flush time accrued while stopped
		renderer.setAnimationLoop( render );
		loopRunning = true;
	}

	function stopLoop() {
		if ( renderer && loopRunning ) {
			renderer.setAnimationLoop( null );
			loopRunning = false;
		}
	}

	// Hidden tab: stop rendering (and the clock with it) so she resumes
	// mid-scene instead of teleporting off-screen on return.
	function onVisibility() {
		if ( done ) return;
		if ( document.hidden ) {
			stopLoop();
		} else if ( mixer ) {
			startLoop();
		}
	}
	document.addEventListener( 'visibilitychange', onVisibility );

	// -------------------------------------------------------------------------
	// Teardown — the cameo runs once; leave no GPU residue behind
	// -------------------------------------------------------------------------

	function teardown() {
		if ( done ) return;
		done = true;
		stopLoop();
		document.removeEventListener( 'visibilitychange', onVisibility );
		if ( scene ) {
			scene.traverse( function ( child ) {
				if ( child.isMesh ) {
					if ( child.geometry ) child.geometry.dispose();
					var mats = Array.isArray( child.material ) ? child.material : [ child.material ];
					mats.forEach( function ( m ) {
						if ( ! m ) return;
						if ( m.map ) m.map.dispose();
						if ( m.emissiveMap ) m.emissiveMap.dispose();
						if ( m.metalnessMap ) m.metalnessMap.dispose();
						if ( m.roughnessMap ) m.roughnessMap.dispose();
						m.dispose();
					} );
				}
			} );
		}
		if ( renderer ) renderer.dispose();
		if ( canvas && canvas.parentNode ) canvas.parentNode.removeChild( canvas );
		scene = camera = renderer = mixer = clock = canvas = null;
	}

	// -------------------------------------------------------------------------
	// Trigger — boot once when the scene is actually being looked at
	// -------------------------------------------------------------------------

	if ( 'IntersectionObserver' in window ) {
		var io = new IntersectionObserver( function ( entries ) {
			for ( var i = 0; i < entries.length; i++ ) {
				if ( entries[ i ].isIntersecting ) {
					io.disconnect();
					loadThree( initScene );
					return;
				}
			}
		}, { threshold: 0.25 } );
		io.observe( container );
	} else {
		loadThree( initScene );
	}

} )();
