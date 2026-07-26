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
	/** Self-hosted Draco decoder directory — no new CSP origin (decoder files
	 *  land here once a Draco-compressed GLB ships; non-Draco GLBs never
	 *  touch this path). */
	var DRACO_DECODER_PATH = SKYYROSE_ASSETS_URI_3D() + '/js/lib/draco/';
	var CANVAS_ID     = 'skyy-3d-canvas';
	var CHARACTER_W   = 220;       // px — canvas width
	var CHARACTER_H   = 340;       // px — canvas height

	/** Best-effort theme assets base for the Draco decoder path — falls back
	 *  to a relative guess if skyyRoseData hasn't localized yet. */
	function SKYYROSE_ASSETS_URI_3D() {
		return ( window.skyyRoseData && window.skyyRoseData.assetsUri )
			? window.skyyRoseData.assetsUri
			: '/wp-content/themes/skyyrose-flagship/assets';
	}

	// Animation clip names expected in the .glb (Mixamo standard names).
	// The model should contain at minimum: 'idle' and 'walk'. wave/point/
	// talk/joy are optional — missing clips fall back to idle gracefully
	// (see playNamedAction below).
	var CLIP_IDLE  = 'idle';
	var CLIP_WALK  = 'walk';
	var CLIP_WAVE  = 'wave';
	var CLIP_POINT = 'point';
	var CLIP_TALK  = 'talk';
	var CLIP_JOY   = 'joy';

	// -------------------------------------------------------------------------
	// DOM / Three.js setup
	// -------------------------------------------------------------------------

	/** Three.js globals (declared after THREE is available) */
	var scene, camera, renderer, mixer, clock;
	var currentAction = null;
	var actions = {};
	var canvas = document.getElementById( CANVAS_ID );

	if ( ! canvas ) return;

	// Respect prefers-reduced-motion — render a single static frame, never a
	// running animation loop (SC 2.2.2: no auto-playing motion).
	var reduced = window.matchMedia( '(prefers-reduced-motion: reduce)' ).matches;

	// Session-dismissal + visibility state. mascot.js owns the sessionStorage
	// key; the 3D layer honours the same contract (nothing pops in unsolicited
	// after a dismissal) and stops rendering while the character is hidden.
	var SESSION_KEY_DISMISSED = 'skyy_dismissed';
	// Starts false: mascot.js's "no pop-in on page load" rule (state only
	// becomes visible on a real skyy:walking-in event) must hold for the 3D
	// layer too. Without this, a GLB that finishes loading before the
	// visitor's idle-entrance timer fires would reveal the canvas in idle
	// pose ahead of any walk-on decision. skyy:walking-in flips this true.
	var visible     = false;
	var loopRunning = false;
	var modelReady  = false;
	var bootStarted = false;
	var pendingClip = null; // clip requested before the GLB finished loading

	function dismissedThisSession() {
		try {
			return sessionStorage.getItem( SESSION_KEY_DISMISSED ) === '1';
		} catch ( e ) {
			return false;
		}
	}

	function startLoop() {
		if ( ! renderer ) return;
		if ( reduced ) {
			renderer.render( scene, camera );
			return;
		}
		if ( ! loopRunning ) {
			clock.getDelta(); // flush time accrued while stopped
			renderer.setAnimationLoop( render );
			loopRunning = true;
		}
	}

	function stopLoop() {
		if ( renderer && loopRunning ) {
			renderer.setAnimationLoop( null );
			loopRunning = false;
		}
	}

	function revealCanvas() {
		canvas.style.display = 'block';
		var staticImg = document.querySelector( '.skyyrose-mascot__image' );
		if ( staticImg ) staticImg.style.display = 'none';
	}

	// -------------------------------------------------------------------------
	// Bootstrap — load Three.js dynamically then initialise
	// -------------------------------------------------------------------------

	function loadThree( callback ) {
		if ( window.THREE && window.THREE_GLTFLoader && window.THREE_DRACOLoader ) {
			callback( window.THREE );
			return;
		}

		var base = 'https://cdn.jsdelivr.net/npm/three@0.170.0';

		// Inject a module script that imports THREE and attaches it to window.
		// jsdelivr is already an allowed script-src origin (inc/security.php) —
		// this adds no new CSP surface. The Draco decoder binaries themselves
		// are self-hosted (DRACO_DECODER_PATH below) since their runtime
		// fetch falls under connect-src, which does not allow jsdelivr.
		var injectScript = document.createElement( 'script' );
		injectScript.type = 'module';
		// /+esm endpoints rewrite the loaders' bare `from 'three'` specifiers to
		// jsdelivr's own ESM URL for the same version — one shared three
		// instance, no importmap needed (a late importmap is rejected once the
		// page has already executed any module script, which the homepage does).
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
	// Three.js scene initialisation
	// -------------------------------------------------------------------------

	function initScene( THREE ) {
		// No-WebGL guard (audit D10): headless/bot renders, GPU-blocklisted
		// and legacy clients have no usable context — three's constructor
		// console.errors then THROWS, which surfaced as an uncaught pageerror
		// on every page. Probe a throwaway canvas first (silent in most
		// engines), keep try/catch as the backstop, and degrade to the 2D
		// sprite mascot (mascot.js) by hiding the 3D canvas only.
		var probeCanvas = document.createElement( 'canvas' );
		var probeGl = probeCanvas.getContext( 'webgl2' ) || probeCanvas.getContext( 'webgl' );
		if ( ! probeGl ) {
			canvas.style.display = 'none';
			return;
		}

		// Renderer — transparent background, alpha
		try {
			renderer = new THREE.WebGLRenderer( {
				canvas: canvas,
				alpha: true,
				antialias: true,
				powerPreference: 'low-power',
			} );
		} catch ( e ) {
			canvas.style.display = 'none';
			renderer = null;
			return;
		}
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
			if ( window.SKYYROSE_DEBUG ) {
				// eslint-disable-next-line no-console
				console.warn( 'Skyy 3D: GLTFLoader not available' );
			}
			return;
		}

		var loader = new GLTFLoader();

		// DRACOLoader is only invoked by GLTFLoader when a loaded glTF actually
		// declares the KHR_draco_mesh_compression extension — wiring it in is
		// a no-op for non-Draco GLBs (today, since no GLB exists yet).
		var DRACOLoaderClass = window.THREE_DRACOLoader || ( window.THREE && window.THREE.DRACOLoader );
		if ( DRACOLoaderClass ) {
			var dracoLoader = new DRACOLoaderClass();
			dracoLoader.setDecoderPath( DRACO_DECODER_PATH );
			loader.setDRACOLoader( dracoLoader );
		}

		loader.load(
			MODEL_URL,
			function ( gltf ) {
				var model = gltf.scene;

				// Scale FIRST, then centre from a recomputed box — the offsets
				// must be in post-scale units. Computing them pre-scale displaces
				// the model by the scale factor (she floated in the top half of
				// the canvas whenever the source GLB wasn't already 1.8u tall).
				var size = new THREE.Box3().setFromObject( model ).getSize( new THREE.Vector3() );
				model.scale.setScalar( 1.8 / size.y );
				var box = new THREE.Box3().setFromObject( model );
				var centre = box.getCenter( new THREE.Vector3() );
				model.position.x -= centre.x;
				model.position.z -= centre.z;
				model.position.y -= box.min.y; // feet on the origin plane

				// Enable shadows + PBR materials
				model.traverse( function ( child ) {
					if ( child.isMesh ) {
						// Skinned mesh + baked clips: the static bounding sphere
						// leaves the frustum mid-walk and the whole mesh vanishes
						// unless culling is disabled.
						if ( child.isSkinnedMesh ) child.frustumCulled = false;
						child.castShadow    = false;
						child.receiveShadow = false;
						if ( child.material ) {
							child.material.envMapIntensity = 0.8;
						}
					}
				} );

				scene.add( model );

				// Animation mixer
				if ( gltf.animations && gltf.animations.length ) {
					mixer = new THREE.AnimationMixer( model );

					gltf.animations.forEach( function ( clip ) {
						actions[ clip.name.toLowerCase() ] = mixer.clipAction( clip );
					} );

					// Warn if expected clip names weren't found (helps debug GLB exports).
					if ( ( ! actions[ CLIP_IDLE ] || ! actions[ CLIP_WALK ] ) && window.SKYYROSE_DEBUG ) {
						// eslint-disable-next-line no-console
						console.warn( 'Skyy 3D: expected clips "idle"/"walk" not found. Available:', Object.keys( actions ) );
					}

					modelReady = true;

					if ( reduced ) {
						// Pose one static idle frame — no loop ever runs.
						var idle = actions[ CLIP_IDLE ];
						if ( idle ) idle.play();
						mixer.update( 0.05 );
					} else {
						// Apply whichever state fired while the GLB was still
						// downloading, falling back to idle.
						playAction( pendingClip || CLIP_IDLE );
						pendingClip = null;
					}
				} else {
					modelReady = true;
				}

				// Reveal + animate only while the character is on screen — a
				// load resolving after a dismissal/walk-off must stay hidden.
				if ( visible ) {
					revealCanvas();
					startLoop();
				}
			},
			undefined,
			function ( error ) {
				if ( window.SKYYROSE_DEBUG ) {
					// eslint-disable-next-line no-console
					console.warn( 'Skyy 3D: model load failed —', error );
				}
				// Hide canvas so it doesn't show a black box
				canvas.style.display = 'none';
			}
		);
	}

	// -------------------------------------------------------------------------
	// Animation helpers
	// -------------------------------------------------------------------------

	function playAction( clipName, options ) {
		if ( ! mixer ) {
			// GLB still loading — remember the request, apply on load.
			pendingClip = clipName;
			return;
		}
		if ( reduced ) return; // static idle pose only under reduced motion

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

	/**
	 * Play the first clip found among candidateNames, falling back to the
	 * idle clip when none of them exist in this GLB's animation set —
	 * missing clips (wave/point/talk/joy are all optional) degrade
	 * gracefully instead of throwing or freezing on the last pose.
	 */
	function playFirstAvailable( candidateNames, options ) {
		for ( var i = 0; i < candidateNames.length; i++ ) {
			if ( actions[ candidateNames[ i ] ] ) {
				playAction( candidateNames[ i ], options );
				return;
			}
		}
		playAction( CLIP_IDLE, options );
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

		// The mascot.min.js dispatches CustomEvents that we listen for here.
		// Motion is opt-in (same rule as the CSS sprite path): when the
		// visitor prefers reduced motion, walk/transient-reaction clips are
		// skipped entirely and the character sits on idle instead.
		document.addEventListener( 'skyy:walking-in', function () {
			clearExcitedTimer();
			visible = true;
			if ( ! bootStarted ) {
				// First user-invited appearance in a dismissed session — the
				// 3D layer was deliberately never booted. Boot lazily now.
				boot();
			} else if ( modelReady ) {
				revealCanvas();
				startLoop();
			}
			playAction( reduced ? CLIP_IDLE : CLIP_WALK, { fadeIn: 0.2, fadeOut: 0.2 } );
		} );

		// mascot.js emits skyy:hidden when the character is fully off screen
		// (minimize / ESC / walk-off complete). The canvas is a DOM sibling of
		// the mascot container, out of reach of its CSS state classes — it has
		// to be stopped and hidden here or it animates forever.
		document.addEventListener( 'skyy:hidden', function () {
			clearExcitedTimer();
			visible = false;
			stopLoop();
			canvas.style.display = 'none';
		} );

		document.addEventListener( 'skyy:idle', function () {
			clearExcitedTimer();
			playAction( CLIP_IDLE, { fadeIn: 0.4, fadeOut: 0.4 } );
		} );

		document.addEventListener( 'skyy:speaking', function () {
			clearExcitedTimer();
			playFirstAvailable( [ CLIP_TALK ], { fadeIn: 0.3, fadeOut: 0.3 } );
		} );

		document.addEventListener( 'skyy:exiting', function () {
			clearExcitedTimer();
			playAction( reduced ? CLIP_IDLE : CLIP_WALK, { fadeIn: 0.2, fadeOut: 0.2 } );
		} );

		// Transient reaction clips — crossfade in, hold briefly, crossfade
		// back to idle. Shared by excited/wave/point so the timer-cleanup
		// logic isn't repeated four times.
		function playTransient( candidateNames, holdMs ) {
			clearExcitedTimer();
			if ( reduced ) {
				playAction( CLIP_IDLE, { fadeIn: 0.3, fadeOut: 0.3 } );
				return;
			}
			playFirstAvailable( candidateNames, { fadeIn: 0.15, fadeOut: 0.15 } );
			excitedTimer = setTimeout( function () {
				excitedTimer = null;
				playAction( CLIP_IDLE, { fadeIn: 0.3, fadeOut: 0.3 } );
			}, holdMs );
		}

		document.addEventListener( 'skyy:excited', function () {
			playTransient( [ CLIP_JOY, CLIP_WAVE ], 1000 );
		} );

		document.addEventListener( 'skyy:wave', function () {
			playTransient( [ CLIP_WAVE ], 1200 );
		} );

		document.addEventListener( 'skyy:point', function () {
			playTransient( [ CLIP_POINT ], 1200 );
		} );

		document.addEventListener( 'skyy:joy', function () {
			playTransient( [ CLIP_JOY ], 1000 );
		} );
	}

	// -------------------------------------------------------------------------
	// Bootstrap
	// -------------------------------------------------------------------------
	//
	// No additional page-load delay here: this script is only ever injected
	// by mascot-loader.js after requestIdleCallback/first-interaction, so
	// the "don't cost LCP/CLS budget" job is already done by the time this
	// line runs.

	function boot() {
		bootStarted = true;
		loadThree( initScene );
	}

	// Bind immediately — mascot.js can fire its first skyy:* events before
	// Three.js or the GLB have loaded; pendingClip catches those.
	bindMascotEvents();

	if ( dismissedThisSession() ) {
		// Same contract as mascot.js: after a dismissal nothing pops in
		// unsolicited. Defer boot until a user-initiated skyy:walking-in.
		visible = false;
	} else {
		boot();
	}

} )();
