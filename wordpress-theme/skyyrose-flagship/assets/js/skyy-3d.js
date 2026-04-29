/**
 * Skyy — Three.js Walking Character
 *
 * Loads the Skyy 3D model (.glb) and plays a walk animation on a
 * transparent canvas overlay. The character walks in from the right,
 * stops near the bottom-right corner, plays the idle animation, and
 * responds to the mascot JS state machine via custom events.
 *
 * Dependencies: Three.js r170+ loaded via importmap or CDN.
 *
 * @package SkyyRose_Flagship
 * @since   5.0.0
 */

( function () {
	'use strict';

	// -------------------------------------------------------------------------
	// Config
	// -------------------------------------------------------------------------

	/** Path to the Skyy .glb model — injected by wp_localize_script as SKYY_3D_CONFIG.modelUrl */
	var MODEL_URL = ( window.SKYY_3D_CONFIG && window.SKYY_3D_CONFIG.modelUrl )
		? window.SKYY_3D_CONFIG.modelUrl
		: '/wp-content/themes/skyyrose-flagship/assets/models/skyy.glb';
	var WALK_ON_DELAY = 3000;      // ms after page load before walk-on starts
	var CANVAS_ID     = 'skyy-3d-canvas';
	var CHARACTER_W   = 220;       // px — canvas width
	var CHARACTER_H   = 340;       // px — canvas height

	// Animation clip names expected in the .glb (Mixamo standard names).
	// The model should contain at minimum: 'idle', 'walk'.
	var CLIP_IDLE = 'idle';
	var CLIP_WALK = 'walk';

	// -------------------------------------------------------------------------
	// DOM / Three.js setup
	// -------------------------------------------------------------------------

	/** Three.js globals (declared after THREE is available) */
	var scene, camera, renderer, mixer, clock;
	var currentAction = null;
	var actions = {};
	var canvas = document.getElementById( CANVAS_ID );

	if ( ! canvas ) return;

	// Respect prefers-reduced-motion — still render but skip walk-in delay
	var reduced = window.matchMedia( '(prefers-reduced-motion: reduce)' ).matches;

	// -------------------------------------------------------------------------
	// Bootstrap — load Three.js dynamically then initialise
	// -------------------------------------------------------------------------

	function loadThree( callback ) {
		if ( window.THREE && window.THREE_GLTFLoader ) {
			callback( window.THREE );
			return;
		}

		var base = 'https://cdn.jsdelivr.net/npm/three@0.170.0';

		// Inject a module script that imports THREE and attaches it to window.
		var injectScript = document.createElement( 'script' );
		injectScript.type = 'module';
		injectScript.textContent = [
			"import * as THREE from '" + base + "/build/three.module.js';",
			"import { GLTFLoader } from '" + base + "/examples/jsm/loaders/GLTFLoader.js';",
			"window.THREE = THREE;",
			"window.THREE_GLTFLoader = GLTFLoader;",
			"document.dispatchEvent(new Event('three-ready'));",
		].join( '\n' );

		document.head.appendChild( injectScript );

		document.addEventListener( 'three-ready', function onReady() {
			document.removeEventListener( 'three-ready', onReady );
			callback( window.THREE );
		} );
	}

	// -------------------------------------------------------------------------
	// Three.js scene initialisation
	// -------------------------------------------------------------------------

	function initScene( THREE ) {
		// Renderer — transparent background, alpha
		renderer = new THREE.WebGLRenderer( {
			canvas: canvas,
			alpha: true,
			antialias: true,
			powerPreference: 'low-power',
		} );
		renderer.setPixelRatio( Math.min( window.devicePixelRatio, 2 ) );
		renderer.setSize( CHARACTER_W, CHARACTER_H );
		renderer.shadowMap.enabled = false;
		renderer.outputColorSpace = THREE.SRGBColorSpace;

		// Scene
		scene = new THREE.Scene();

		// Camera — orthographic-feel perspective, zoomed to character
		camera = new THREE.PerspectiveCamera( 30, CHARACTER_W / CHARACTER_H, 0.1, 50 );
		camera.position.set( 0, 1.2, 5 );
		camera.lookAt( 0, 0.9, 0 );

		// Lights
		var ambient = new THREE.AmbientLight( 0xffffff, 1.4 );
		scene.add( ambient );

		var key = new THREE.DirectionalLight( 0xfff5e6, 1.8 );
		key.position.set( 2, 4, 3 );
		scene.add( key );

		var fill = new THREE.DirectionalLight( 0xe6f0ff, 0.6 );
		fill.position.set( -2, 2, -1 );
		scene.add( fill );

		// Clock
		clock = new THREE.Clock();

		loadModel( THREE );
	}

	// -------------------------------------------------------------------------
	// Model loading
	// -------------------------------------------------------------------------

	function loadModel( THREE ) {
		// r147 add-on scripts attach to THREE.GLTFLoader (window.THREE.GLTFLoader).
		// window.THREE_GLTFLoader is kept as a legacy override path.
		var GLTFLoader = window.THREE_GLTFLoader ||
			( window.THREE && window.THREE.GLTFLoader );
		if ( ! GLTFLoader ) {
			console.warn( 'Skyy 3D: GLTFLoader not available' );
			return;
		}

		var loader = new GLTFLoader();
		loader.load(
			MODEL_URL,
			function ( gltf ) {
				var model = gltf.scene;

				// Centre model at origin
				var box = new THREE.Box3().setFromObject( model );
				var centre = box.getCenter( new THREE.Vector3() );
				model.position.sub( centre );
				model.position.y = -( box.min.y - centre.y );

				// Auto-scale to fit within ~1.8 units height
				var size = box.getSize( new THREE.Vector3() );
				var scale = 1.8 / size.y;
				model.scale.setScalar( scale );

				// Enable shadows + PBR materials
				model.traverse( function ( child ) {
					if ( child.isMesh ) {
						child.castShadow    = false;
						child.receiveShadow = false;
						if ( child.material ) {
							child.material.envMapIntensity = 0.8;
						}
					}
				} );

				scene.add( model );

				// Show 3D canvas, hide static fallback image
				canvas.style.display = 'block';
				var staticImg = document.querySelector( '.skyyrose-mascot__image' );
				if ( staticImg ) staticImg.style.display = 'none';

				// Animation mixer
				if ( gltf.animations && gltf.animations.length ) {
					mixer = new THREE.AnimationMixer( model );

					gltf.animations.forEach( function ( clip ) {
						actions[ clip.name.toLowerCase() ] = mixer.clipAction( clip );
					} );

					// Warn if expected clip names weren't found (helps debug GLB exports).
					if ( ! actions[ CLIP_IDLE ] || ! actions[ CLIP_WALK ] ) {
						console.warn( 'Skyy 3D: expected clips "idle"/"walk" not found. Available:', Object.keys( actions ) );
					}

					// Start with idle, transition to walk when event fires
					playAction( CLIP_IDLE );
				}

				// Start render loop
				renderer.setAnimationLoop( render );

				// Listen for mascot state events
				bindMascotEvents();
			},
			undefined,
			function ( error ) {
				console.warn( 'Skyy 3D: model load failed —', error );
				// Hide canvas so it doesn't show a black box
				canvas.style.display = 'none';
			}
		);
	}

	// -------------------------------------------------------------------------
	// Animation helpers
	// -------------------------------------------------------------------------

	function playAction( clipName, options ) {
		var action = actions[ clipName ] || actions[ Object.keys( actions )[ 0 ] ];
		if ( ! action ) return;

		if ( currentAction && currentAction !== action ) {
			currentAction.fadeOut( options && options.fadeOut || 0.3 );
			action.reset().fadeIn( options && options.fadeIn || 0.3 ).play();
		} else if ( ! currentAction ) {
			action.play();
		}

		currentAction = action;
	}

	// -------------------------------------------------------------------------
	// Render loop
	// -------------------------------------------------------------------------

	function render() {
		var delta = clock.getDelta();
		if ( mixer ) mixer.update( delta );
		renderer.render( scene, camera );
	}

	// -------------------------------------------------------------------------
	// Mascot state machine integration
	// -------------------------------------------------------------------------

	function bindMascotEvents() {
		// Track excited-animation timer so it can be cancelled on state change.
		var excitedTimer = null;

		function clearExcitedTimer() {
			if ( excitedTimer !== null ) {
				clearTimeout( excitedTimer );
				excitedTimer = null;
			}
		}

		// The mascot.min.js dispatches CustomEvents that we listen for here
		document.addEventListener( 'skyy:walking-in', function () {
			clearExcitedTimer();
			playAction( CLIP_WALK, { fadeIn: 0.2, fadeOut: 0.2 } );
		} );

		document.addEventListener( 'skyy:idle', function () {
			clearExcitedTimer();
			playAction( CLIP_IDLE, { fadeIn: 0.4, fadeOut: 0.4 } );
		} );

		document.addEventListener( 'skyy:speaking', function () {
			clearExcitedTimer();
			// Play talk clip if available, else stay on idle
			playAction( actions.talk ? 'talk' : CLIP_IDLE );
		} );

		document.addEventListener( 'skyy:exiting', function () {
			clearExcitedTimer();
			playAction( CLIP_WALK, { fadeIn: 0.2, fadeOut: 0.2 } );
		} );

		document.addEventListener( 'skyy:excited', function () {
			var exciteClip = actions.jump || actions.wave || actions[ CLIP_IDLE ];
			if ( ! exciteClip ) return;
			clearExcitedTimer();
			currentAction && currentAction.fadeOut( 0.15 );
			exciteClip.reset().fadeIn( 0.15 ).play();
			currentAction = exciteClip;
			excitedTimer = setTimeout( function () {
				excitedTimer = null;
				playAction( CLIP_IDLE, { fadeIn: 0.3, fadeOut: 0.3 } );
			}, 1000 );
		} );
	}

	// -------------------------------------------------------------------------
	// Bootstrap
	// -------------------------------------------------------------------------

	setTimeout( function () {
		loadThree( initScene );
	}, reduced ? 100 : WALK_ON_DELAY );

} )();
