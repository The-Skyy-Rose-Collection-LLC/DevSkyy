/**
 * SkyyRose Flagship — Three.js Initialization
 *
 * Base scene setup for immersive 3D collection experiences.
 * Individual templates (Black Rose Garden, Love Hurts Castle,
 * Signature Runway) define their own scene-specific logic.
 *
 * @package SkyyRose_Flagship
 * @since 2.0.0
 */

( function() {
	'use strict';

	// Only initialize if a 3D scene container exists on the page
	var sceneContainer = document.querySelector( '.three-scene-wrapper' );
	if ( ! sceneContainer ) return;

	// Expose shared utilities for immersive templates
	window.SkyyRose3D = {

		/**
		 * Create standard renderer with SkyyRose defaults.
		 */
		createRenderer: function( container ) {
			if ( typeof THREE === 'undefined' ) return null;

			var renderer = new THREE.WebGLRenderer( {
				antialias: true,
				alpha: false,
				powerPreference: 'high-performance'
			} );
			renderer.setSize( window.innerWidth, window.innerHeight );
			renderer.setPixelRatio( Math.min( window.devicePixelRatio, 2 ) );
			renderer.shadowMap.enabled = true;
			renderer.shadowMap.type = THREE.PCFSoftShadowMap;
			renderer.toneMapping = THREE.ACESFilmicToneMapping;
			renderer.toneMappingExposure = 1.2;
			container.appendChild( renderer.domElement );
			return renderer;
		},

		/**
		 * Brand colors as Three.js Color instances.
		 */
		colors: {
			roseGold:  0xB76E79,
			gold:      0xD4AF37,
			silver:    0xC0C0C0,
			crimson:   0xDC143C,
			mauve:     0xD8A7B1,
			black:     0x0a0a0a,
			white:     0xffffff
		},

		/**
		 * Handle window resize for any scene.
		 */
		onResize: function( camera, renderer ) {
			window.addEventListener( 'resize', function() {
				camera.aspect = window.innerWidth / window.innerHeight;
				camera.updateProjectionMatrix();
				renderer.setSize( window.innerWidth, window.innerHeight );
			} );
		}
	};

} )();
