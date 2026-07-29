/**
 * Kids Capsule mascot — the rigged child character, walking on the keepsake
 * board in the homepage Letter act.
 *
 * Scope: this ONE mount, homepage only. It is NOT the site-wide host mascot
 * (mascot.js + skyy-3d.js), whose singleton state machine this file never
 * touches. One WebGL context per page is a deliberate cost decision.
 *
 * Three.js comes from the jsdelivr ESM entry skyy-3d.js already uses (an
 * allowed script-src origin, inc/security.php) via the same window globals, so
 * no second copy is ever fetched. These GLBs add EXT_meshopt_compression, so
 * this file also imports MeshoptDecoder — which skyy-3d.js does not, hence its
 * own ready event rather than a shared one.
 *
 * @package SkyyRose
 * @since   1.13.0
 */

( function () {
	'use strict';

	var THREE_BASE = 'https://cdn.jsdelivr.net/npm/three@0.170.0';
	var READY_EVENT = 'skyy-kc-three-ready';
	var MOBILE_MAX = 900;

	var canvas = document.getElementById( 'skyy-kc-canvas' );
	if ( ! canvas ) { return; }

	var reduce = window.matchMedia( '(prefers-reduced-motion: reduce)' ).matches;

	/* Hide the whole cell, not just the canvas: the mount reserves 260px and
	   carries a caption, so hiding the canvas alone leaves an empty block with
	   a floating label under it — a 260px hole in the stacked mobile board.
	   Reveals a static stand-in if the template ever ships one. */
	function degrade() {
		var host = canvas.closest( '.hp-letter__mascot' ) || canvas;
		host.style.display = 'none';
		var still = document.querySelector( '[data-kc-mascot-fallback]' );
		if ( still ) {
			still.hidden = false;
			host.style.display = '';
			canvas.style.display = 'none';
		}
	}

	/** srcset-equivalent for 3D: the light build below the breakpoint. */
	function modelUrl() {
		var attr = window.innerWidth > MOBILE_MAX ? 'data-model-desktop' : 'data-model-mobile';
		return canvas.getAttribute( attr ) || canvas.getAttribute( 'data-model-mobile' ) || '';
	}

	function loadThree( done, fail ) {
		if ( window.THREE && window.THREE_GLTFLoader && window.THREE_MeshoptDecoder ) {
			done(); return;
		}
		var script = document.createElement( 'script' );
		script.type = 'module';
		// /+esm rewrites the loaders' bare `from 'three'` specifiers to jsdelivr's
		// own ESM URL for the same version, so the loader and the core share one
		// module instance without an importmap (a late importmap is rejected once
		// the page has executed any module script, which this page has).
		script.textContent = [
			"import * as THREE from '" + THREE_BASE + "/+esm';",
			"import { GLTFLoader } from '" + THREE_BASE + "/examples/jsm/loaders/GLTFLoader.js/+esm';",
			"import { MeshoptDecoder } from '" + THREE_BASE + "/examples/jsm/libs/meshopt_decoder.module.js/+esm';",
			'window.THREE = window.THREE || THREE;',
			'window.THREE_GLTFLoader = window.THREE_GLTFLoader || GLTFLoader;',
			'window.THREE_MeshoptDecoder = MeshoptDecoder;',
			"document.dispatchEvent(new Event('" + READY_EVENT + "'));",
		].join( '\n' );
		script.addEventListener( 'error', fail );
		document.addEventListener( READY_EVENT, function onReady() {
			document.removeEventListener( READY_EVENT, onReady );
			done();
		} );
		document.head.appendChild( script );
	}

	function build() {
		var THREE = window.THREE;
		var GLTFLoader = window.THREE_GLTFLoader;
		var MeshoptDecoder = window.THREE_MeshoptDecoder;
		if ( ! THREE || ! GLTFLoader || ! MeshoptDecoder ) {
			degrade(); return;
		}

		// No-WebGL guard: three's constructor throws on GPU-blocklisted and
		// headless clients, which surfaces as an uncaught pageerror. Probe a
		// throwaway context first, keep try/catch as the backstop.
		var probe = document.createElement( 'canvas' );
		if ( ! ( probe.getContext( 'webgl2' ) || probe.getContext( 'webgl' ) ) ) {
			degrade(); return;
		}

		var width = canvas.clientWidth || 240;
		var height = canvas.clientHeight || 300;
		var renderer;
		try {
			renderer = new THREE.WebGLRenderer( {
				canvas: canvas,
				alpha: true,
				antialias: true,
				powerPreference: 'low-power',
			} );
		} catch ( err ) {
			degrade(); return;
		}
		renderer.setPixelRatio( Math.min( window.devicePixelRatio, 2 ) );
		renderer.setSize( width, height, false );
		renderer.outputColorSpace = THREE.SRGBColorSpace;
		var scene = new THREE.Scene();
		var camera = new THREE.PerspectiveCamera( 32, width / height, 0.1, 50 );
		camera.position.set( 0, 1.05, 4.2 );
		camera.lookAt( 0, 0.82, 0 );

		scene.add( new THREE.AmbientLight( 0xffffff, 1.5 ) );
		var key = new THREE.DirectionalLight( 0xfff2e2, 1.7 );
		var fill = new THREE.DirectionalLight( 0xe8ecff, 0.55 );
		key.position.set( 2, 4, 3 );
		fill.position.set( -2, 2, -1 );
		scene.add( key, fill );

		var loader = new GLTFLoader();
		loader.setMeshoptDecoder( MeshoptDecoder );

		var clock = new THREE.Clock();
		var mixer = null;

		loader.load(
			modelUrl(),
			function ( gltf ) {
				var model = gltf.scene;
				// Scale FIRST, then centre from a recomputed box — the offsets
				// must be in post-scale units or the model is displaced by the
				// scale factor. Skinned meshes also deform outside their baked
				// bounds, so the static bounding sphere culls them too early.
				var size = new THREE.Box3().setFromObject( model ).getSize( new THREE.Vector3() );
				if ( size.y > 0 ) { model.scale.setScalar( 1.6 / size.y ); }
				var box = new THREE.Box3().setFromObject( model );
				var centre = box.getCenter( new THREE.Vector3() );
				model.position.x -= centre.x;
				model.position.z -= centre.z;
				model.position.y -= box.min.y;
				model.traverse( function ( child ) {
					if ( child.isMesh ) { child.frustumCulled = false; }
				} );
				scene.add( model );

				var clips = gltf.animations || [];
				var walk = clips.filter( function ( c ) { return c.name === 'walk'; } )[ 0 ] || clips[ 0 ];
				if ( walk ) {
					mixer = new THREE.AnimationMixer( model );
					mixer.clipAction( walk ).play();
				}

				// Reduced motion: one static frame, never a running loop.
				if ( reduce || ! walk ) {
					if ( mixer ) { mixer.update( 0.4 ); }
					renderer.render( scene, camera );
					return;
				}

				function tick() {
					mixer.update( clock.getDelta() );
					renderer.render( scene, camera );
				}
				renderer.setAnimationLoop( tick );

				// Stop burning frames once the board scrolls away.
				if ( 'IntersectionObserver' in window ) {
					var visIo = new IntersectionObserver( function ( entries ) {
						entries.forEach( function ( entry ) {
							if ( ! entry.isIntersecting ) { renderer.setAnimationLoop( null ); return; }
							clock.getDelta(); // flush time accrued while stopped
							renderer.setAnimationLoop( tick );
						} );
					}, { threshold: 0 } );
					visIo.observe( canvas );
				}
			},
			null,
			function () {
				renderer.setAnimationLoop( null );
				renderer.dispose();
				degrade();
			}
		);
	}

	/* Lazy boot: nothing is fetched — not three, not the GLB — until the board
	   is near the viewport, so this can never tax the initial page LCP. */
	function boot() {
		loadThree( build, degrade );
	}

	if ( 'IntersectionObserver' in window ) {
		var io = new IntersectionObserver( function ( entries ) {
			entries.forEach( function ( entry ) {
				if ( ! entry.isIntersecting ) { return; }
				io.disconnect();
				boot();
			} );
		}, { rootMargin: '200px 0px' } );
		io.observe( canvas );
	} else {
		boot();
	}
}() );
