/**
 * Immersive Core — Capability B: Scene Intro
 *
 * Orchestrates the entry sequence for immersive collection rooms and the
 * preorder gateway. Reads collection context from the DOM, gates on
 * sessionStorage and prefers-reduced-motion, then runs a GSAP timeline:
 *   step 1 — palette overlay + dust canvas
 *   step 2 — lockup reveal + pointer parallax
 *   step 3 — hairline rule + tagline fade
 *   step 4 — overlay wipe + room scale push
 *   step 5 — cleanup, sessionStorage write, CustomEvent
 *
 * Capabilities A (Lenis smooth scroll) and C (warp transition) are
 * intentionally absent. Add them as sibling guarded functions alongside
 * initSceneIntro() — no refactoring of this file required.
 *
 * @package SkyyRose
 * @since   7.0.0
 */

(function () {
	'use strict';

	/* ── Public API ─────────────────────────────────────────────────── */

	/**
	 * Entry point. Called on DOMContentLoaded.
	 * Feature-detects GSAP and resolves page context before delegating.
	 */
	function initImmersiveCore() {
		if ( typeof window.gsap === 'undefined' ) {
			// .scene-lockup starts at opacity:0 (CSS). Resolve context so we can
			// reveal the lockup and h1 even when GSAP is absent.
			var gsapAbsentCtx = resolveContext();
			if ( gsapAbsentCtx ) {
				ensureRoomInteractive( gsapAbsentCtx.lockup, gsapAbsentCtx.h1 );
			}
			return;
		}

		var ctx = resolveContext();

		if ( ! ctx ) {
			return; // Neither scene nor preorder page — nothing to do.
		}

		if ( isIntroDone( ctx.sessionKey ) ) {
			ensureRoomInteractive( ctx.lockup, ctx.h1 );
			return;
		}

		if ( prefersReducedMotion() ) {
			ensureLockupVisible( ctx.lockup );
			ensureRoomInteractive( ctx.lockup, ctx.h1 );
			return;
		}

		initSceneIntro( ctx );
	}

	/* ── Context resolution ─────────────────────────────────────────── */

	/**
	 * Determine whether we are on an immersive room or the preorder gateway,
	 * and assemble a context object consumed by initSceneIntro.
	 *
	 * @returns {object|null} Context, or null if neither page type matches.
	 */
	function resolveContext() {
		var isPreorder = !! document.querySelector( 'main.preorder-gateway' );
		var sceneEl    = document.querySelector( '.immersive-scene[data-collection]' );
		var slug       = sceneEl ? sceneEl.dataset.collection : '';

		if ( isPreorder ) {
			return buildContext( 'preorder', sceneEl || document.body, true );
		}

		if ( ! slug ) {
			return null; // No scene, not preorder — bail silently.
		}

		return buildContext( slug, sceneEl, false );
	}

	/**
	 * @param {string}      slug       Collection slug or 'preorder'.
	 * @param {Element}     sceneEl    Root element for the room.
	 * @param {boolean}     isPreorder True when on the preorder gateway.
	 * @returns {object}
	 */
	function buildContext( slug, sceneEl, isPreorder ) {
		return {
			slug:        slug,
			sessionKey:  'skyyrose_intro_seen_' + slug,
			sceneEl:     sceneEl,
			isPreorder:  isPreorder,
			lockup:      document.querySelector( '.scene-lockup' ),
			taglineEl:   document.querySelector( '.scene-tagline' ),
			h1:          document.querySelector( '#scene-title' ),
			hairline:    document.querySelector( '.scene-hairline' ),
		};
	}

	/* ── Guards ─────────────────────────────────────────────────────── */

	function isIntroDone( key ) {
		try { return !! sessionStorage.getItem( key ); } catch ( e ) { return false; }
	}

	function prefersReducedMotion() {
		return window.matchMedia( '(prefers-reduced-motion: reduce)' ).matches;
	}

	/* ── Immediate-visible helpers (no GSAP) ───────────────────────── */

	/**
	 * Ensure .scene-lockup is immediately visible without a GSAP timeline.
	 * Used by: reduced-motion, GSAP-absent, and seen paths.
	 *
	 * @param {Element|null} lockup
	 */
	function ensureLockupVisible( lockup ) {
		if ( ! lockup ) return;
		lockup.style.opacity = '1';
		lockup.style.filter  = 'none';
	}

	/**
	 * Ensure the room is interactive: no overlay blocking pointer events.
	 * Reveals fallback h1 when lockup is absent.
	 *
	 * @param {Element|null} lockup
	 * @param {Element|null} h1
	 */
	function ensureRoomInteractive( lockup, h1 ) {
		ensureLockupVisible( lockup );
		if ( ! lockup && h1 ) {
			h1.style.position  = 'static';
			h1.style.clipPath  = 'none';
			h1.style.width     = 'auto';
			h1.style.height    = 'auto';
			h1.style.overflow  = 'visible';
		}
	}

	/* ── Dust canvas ────────────────────────────────────────────────── */

	/** @type {number|null} */
	var dustRafId = null;

	/**
	 * Build and start a ≤120-particle dust canvas loop.
	 *
	 * @param {HTMLCanvasElement} canvas
	 * @param {string}            bgColor   CSS color from design token.
	 * @param {string}            dustColor CSS color from design token.
	 */
	function startDust( canvas, bgColor, dustColor ) {
		var ctx    = canvas.getContext( '2d' );
		var W      = canvas.width;
		var H      = canvas.height;
		var COUNT  = 120;
		var particles = initDustParticles( W, H, COUNT );

		function tick() {
			ctx.clearRect( 0, 0, W, H );
			for ( var i = 0; i < particles.length; i++ ) {
				var p = particles[ i ];
				p.y -= p.vy;
				p.x += p.vx;
				p.life -= 0.004;
				if ( p.life <= 0 ) {
					particles[ i ] = makeParticle( W, H );
					continue;
				}
				ctx.globalAlpha = p.life * p.alpha;
				ctx.fillStyle   = dustColor;
				ctx.beginPath();
				ctx.arc( p.x, p.y, p.r, 0, Math.PI * 2 );
				ctx.fill();
			}
			ctx.globalAlpha = 1;
			dustRafId = requestAnimationFrame( tick );
		}

		dustRafId = requestAnimationFrame( tick );
	}

	/**
	 * @param {number} W
	 * @param {number} H
	 * @param {number} count
	 * @returns {object[]}
	 */
	function initDustParticles( W, H, count ) {
		var arr = [];
		for ( var i = 0; i < count; i++ ) {
			arr.push( makeParticle( W, H ) );
		}
		return arr;
	}

	/**
	 * @param {number} W
	 * @param {number} H
	 * @returns {object}
	 */
	function makeParticle( W, H ) {
		return {
			x:     Math.random() * W,
			y:     H * 0.5 + Math.random() * H * 0.5,
			r:     0.5 + Math.random() * 1.5,
			vy:    0.2 + Math.random() * 0.6,
			vx:    ( Math.random() - 0.5 ) * 0.3,
			alpha: 0.15 + Math.random() * 0.45,
			life:  0.4 + Math.random() * 0.6,
		};
	}

	/** Cancel rAF and remove canvas from DOM. */
	function destroyDust( canvas ) {
		if ( dustRafId !== null ) {
			cancelAnimationFrame( dustRafId );
			dustRafId = null;
		}
		if ( canvas && canvas.parentNode ) {
			canvas.parentNode.removeChild( canvas );
		}
	}

	/* ── Pointer parallax for lockup ────────────────────────────────── */

	/** @type {Function|null} */
	var pointerMoveHandler    = null;
	/** @type {Function|null} */
	var deviceOrientHandler   = null;

	/**
	 * Attach ±8px parallax to lockup.
	 * - Non-touch (hover:fine) → pointermove handler.
	 * - Touch/gyro (hover:none) → deviceorientation handler with clamped gamma/beta.
	 *
	 * @param {Element} lockup
	 */
	function attachParallax( lockup ) {
		if ( ! lockup ) return;
		var isTouch = window.matchMedia( '(hover: none)' ).matches;

		if ( ! isTouch ) {
			// Pointer parallax for mouse/trackpad devices.
			pointerMoveHandler = function ( e ) {
				var cx  = window.innerWidth  / 2;
				var cy  = window.innerHeight / 2;
				var dx  = ( ( e.clientX - cx ) / cx ) * 8;
				var dy  = ( ( e.clientY - cy ) / cy ) * 8;
				lockup.style.transform = 'translate(' + dx.toFixed( 1 ) + 'px,' + dy.toFixed( 1 ) + 'px)';
			};
			document.addEventListener( 'pointermove', pointerMoveHandler );
		} else {
			// Gyroscope parallax for touch/mobile devices.
			// gamma: -90°→90° (left/right tilt). beta: -180°→180° (forward/back tilt).
			// Clamp to ±45° working range before scaling to ±8px so extreme tilts
			// (face-up, upside-down) cannot push the lockup beyond the design envelope.
			deviceOrientHandler = function ( e ) {
				if ( e.gamma === null || e.beta === null ) return;
				var gamma = Math.max( -45, Math.min( 45, e.gamma ) );
				var beta  = Math.max(   0, Math.min( 90, e.beta  ) );
				var dx = ( gamma / 45 ) * 8;
				var dy = ( ( beta - 45 ) / 45 ) * 8;
				lockup.style.transform = 'translate(' + dx.toFixed( 1 ) + 'px,' + dy.toFixed( 1 ) + 'px)';
			};
			window.addEventListener( 'deviceorientation', deviceOrientHandler );
		}
	}

	/** Remove parallax listeners and reset transform. */
	function detachParallax( lockup ) {
		if ( pointerMoveHandler ) {
			document.removeEventListener( 'pointermove', pointerMoveHandler );
			pointerMoveHandler = null;
		}
		if ( deviceOrientHandler ) {
			window.removeEventListener( 'deviceorientation', deviceOrientHandler );
			deviceOrientHandler = null;
		}
		if ( lockup ) {
			lockup.style.transform = '';
		}
	}

	/* ── Skip affordance ────────────────────────────────────────────── */

	/** @type {boolean} */
	var skipFired = false;

	/** @type {boolean} */
	var cleanupFired = false;

	/** @type {gsap.core.Timeline|null} */
	var activeTl = null;

	/** @type {HTMLElement|null} */
	var activeOverlay = null;

	/** @type {HTMLCanvasElement|null} */
	var activeCanvas = null;

	/** @type {Element|null} */
	var activeLockup = null;

	/** @type {string|null} */
	var activeSessionKey = null;

	/** @type {Element|null} */
	var activeSceneEl = null;

	/**
	 * Skip the intro by jumping the timeline to completion.
	 * Idempotent — safe to call from Esc, click, and onComplete.
	 */
	function skipIntro() {
		if ( skipFired ) return;
		skipFired = true;

		if ( activeTl ) {
			activeTl.progress( 1 );
		}

		cleanup();
	}

	/** @type {Function|null} */
	var escHandler     = null;

	/** @type {Function|null} */
	var clickHandler   = null;

	/**
	 * Attach Esc + click skip listeners.
	 *
	 * The overlay carries the `inert` attribute, which blocks pointer events
	 * from reaching it or its subtree — so a listener bound to the overlay can
	 * never fire. Both listeners are therefore bound at the document level; the
	 * click listener uses capture so it runs ahead of any room handler beneath
	 * the (clip-animated) overlay.
	 */
	function attachSkipListeners() {
		escHandler = function ( e ) {
			if ( e.key === 'Escape' ) skipIntro();
		};
		clickHandler = function () {
			skipIntro();
		};
		document.addEventListener( 'keydown', escHandler );
		document.addEventListener( 'click', clickHandler, true );
	}

	/** Remove skip listeners. */
	function detachSkipListeners() {
		if ( escHandler ) {
			document.removeEventListener( 'keydown', escHandler );
			escHandler = null;
		}
		if ( clickHandler ) {
			document.removeEventListener( 'click', clickHandler, true );
			clickHandler = null;
		}
	}

	/* ── Cleanup ────────────────────────────────────────────────────── */

	/**
	 * Post-timeline teardown:
	 * - hide overlay
	 * - destroy dust canvas
	 * - remove skip listeners
	 * - detach parallax
	 * - write sessionStorage gate
	 * - fire CustomEvent
	 */
	function cleanup() {
		if ( cleanupFired ) return;
		cleanupFired = true;

		detachSkipListeners();
		destroyDust( activeCanvas );
		detachParallax( activeLockup );

		if ( activeOverlay ) {
			// Remove the overlay (and any intro-composition clones it holds)
			// from the DOM. The room's own .scene-lockup — revealed at the wipe
			// by revealRoomTitle() — is the persistent title; the clones were
			// intro-only artifacts.
			if ( activeOverlay.parentNode ) {
				activeOverlay.parentNode.removeChild( activeOverlay );
			} else {
				activeOverlay.style.display = 'none';
			}
		}

		if ( activeSceneEl ) {
			activeSceneEl.style.transform = '';
		}

		try {
			if ( activeSessionKey ) {
				sessionStorage.setItem( activeSessionKey, '1' );
			}
		} catch ( e ) { /* quota */ }

		try {
			document.dispatchEvent( new CustomEvent( 'immersive:intro-complete', {
				bubbles: false,
				detail:  { slug: activeSessionKey ? activeSessionKey.replace( 'skyyrose_intro_seen_', '' ) : '' }
			} ) );
		} catch ( e ) { /* older env */ }

		// Reset module-level state for safety.
		activeTl         = null;
		activeOverlay    = null;
		activeCanvas     = null;
		activeLockup     = null;
		activeSessionKey = null;
		activeSceneEl    = null;
	}

	/* ── Overlay DOM construction ───────────────────────────────────── */

	/**
	 * Build the .ic-overlay div and ic-dust canvas via createElement.
	 * No innerHTML used.
	 *
	 * @returns {{ overlay: HTMLElement, canvas: HTMLCanvasElement }}
	 */
	function buildOverlay() {
		var overlay = document.createElement( 'div' );
		overlay.className         = 'ic-overlay';
		overlay.setAttribute( 'aria-hidden', 'true' );
		overlay.setAttribute( 'inert', '' );

		var canvas    = document.createElement( 'canvas' );
		canvas.className = 'ic-dust';
		canvas.width  = window.innerWidth;
		canvas.height = window.innerHeight;

		overlay.appendChild( canvas );
		document.body.appendChild( overlay );

		return { overlay: overlay, canvas: canvas };
	}

	/* ── Intro composition (clones into the overlay) ────────────────── */

	/**
	 * Clone the room's lockup / hairline / tagline into the overlay so the
	 * step-2 and step-3 beats animate ABOVE the opaque z-9999 curtain instead
	 * of behind it. The room's real elements are never moved — the DOM (and the
	 * aria-labelledby="scene-title" relationship beside them) stays intact — and
	 * are revealed at the wipe by revealRoomTitle(). The clones are intro-only
	 * and are removed with the overlay in cleanup(). cloneNode reuses the same
	 * image src, so the second fetch is served from cache.
	 *
	 * @param {HTMLElement} overlay
	 * @param {object}      ctx
	 * @returns {{ lockup: Element|null, hairline: Element|null, taglineEl: Element|null }}
	 */
	function buildIntroComposition( overlay, ctx ) {
		var clones = { lockup: null, hairline: null, taglineEl: null };

		if ( ctx.lockup ) {
			clones.lockup = ctx.lockup.cloneNode( true );
			clones.lockup.removeAttribute( 'id' );
			overlay.appendChild( clones.lockup );
		}
		if ( ctx.hairline ) {
			clones.hairline = ctx.hairline.cloneNode( true );
			overlay.appendChild( clones.hairline );
		}
		if ( ctx.taglineEl ) {
			clones.taglineEl = ctx.taglineEl.cloneNode( true );
			// Drop the scroll-reveal hook so the global IntersectionObserver
			// never toggles the clone — GSAP owns the clone's opacity here.
			clones.taglineEl.classList.remove( 'rv-blur' );
			overlay.appendChild( clones.taglineEl );
		}

		return clones;
	}

	/**
	 * Reveal the room's own title block, timed to the wipe, so the lockup is
	 * present the instant the overlay clips away — no empty-title pop on the
	 * brand's hero moment.
	 *
	 * @param {gsap.core.Timeline} tl
	 * @param {object}             ctx
	 * @param {number}             at  Timeline position (seconds).
	 */
	function revealRoomTitle( tl, ctx, at ) {
		if ( ctx.lockup )    tl.set( ctx.lockup,    { opacity: 1, filter: 'none' }, at );
		if ( ctx.taglineEl ) tl.set( ctx.taglineEl, { opacity: 1, y: 0 }, at );
		if ( ctx.hairline )  tl.set( ctx.hairline,  { scaleX: 1 }, at );
	}

	/* ── Lockup error handler ───────────────────────────────────────── */

	/**
	 * Wire a one-shot error listener to the lockup <img>.
	 * On failure: warn once and make the h1 fallback visible.
	 *
	 * @param {Element|null} lockup
	 * @param {Element|null} h1
	 */
	function watchLockupError( lockup, h1 ) {
		if ( ! lockup ) return;

		var img = lockup.querySelector( 'img' );
		if ( ! img ) return;

		img.addEventListener( 'error', function onLockupError() {
			img.removeEventListener( 'error', onLockupError );
			console.warn( '[immersive-core] .scene-lockup img failed to load — showing scene-title fallback.' ); // eslint-disable-line no-console

			// Hide the broken image icon so it is never on screen.
			img.style.display = 'none';

			if ( h1 ) {
				h1.style.position  = 'static';
				h1.style.clipPath  = 'none';
				h1.style.width     = 'auto';
				h1.style.height    = 'auto';
				h1.style.overflow  = 'visible';
			}
		} );
	}

	/* ── Timeline steps ─────────────────────────────────────────────── */

	/**
	 * Step 1 (0 – 0.4s): palette overlay fill + dust warm-up.
	 *
	 * Reads --skyyrose-bg and --skyyrose-accent from the scene element so that
	 * per-collection overrides scoped to [data-collection='...'] in design-tokens.css
	 * are resolved correctly (e.g. silver for Black Rose, gold for Signature).
	 * Falls back to documentElement for the preorder gateway, which has no
	 * [data-collection] scope.
	 *
	 * @param {gsap.core.Timeline} tl
	 * @param {HTMLElement}        overlay
	 * @param {HTMLCanvasElement}  canvas
	 * @param {Element|null}       sceneEl  Scene root element (has data-collection).
	 */
	function addStepConcrete( tl, overlay, canvas, sceneEl ) {
		var tokenEl   = ( sceneEl && sceneEl !== document.body ) ? sceneEl : document.documentElement;
		var bgColor   = getComputedStyle( tokenEl ).getPropertyValue( '--skyyrose-bg' ).trim()    || 'currentColor';
		var dustColor = getComputedStyle( tokenEl ).getPropertyValue( '--skyyrose-accent' ).trim() || 'currentColor';

		tl.set( overlay, { backgroundColor: bgColor, opacity: 0 } )
		  .to( overlay, { opacity: 1, duration: 0.4, ease: 'power2.out' }, 0 );

		// Warm up dust: use requestIdleCallback when available, else setTimeout(0).
		var warmUp = function () {
			startDust( canvas, bgColor, dustColor );
		};

		if ( typeof requestIdleCallback === 'function' ) {
			requestIdleCallback( warmUp );
		} else {
			setTimeout( warmUp, 0 );
		}
	}

	/**
	 * Step 2 (0.4 – 1.4s): lockup opacity + blur reveal + parallax attach.
	 * Skipped gracefully when lockup is absent.
	 *
	 * @param {gsap.core.Timeline} tl
	 * @param {Element|null}       lockup
	 */
	function addStepLockup( tl, lockup ) {
		if ( ! lockup ) return;

		tl.fromTo(
			lockup,
			{ opacity: 0, filter: 'blur(12px)' },
			{ opacity: 1, filter: 'blur(0px)', duration: 1.0, ease: 'power2.out' },
			0.4
		).add( function () { attachParallax( lockup ); }, 0.4 );
	}

	/**
	 * Step 3 (1.4 – 2.0s): hairline scale-in + tagline fade-up.
	 * Both elements are optional — skipped silently if absent.
	 *
	 * @param {gsap.core.Timeline} tl
	 * @param {Element|null}       hairline
	 * @param {Element|null}       taglineEl
	 */
	function addStepHairlineTagline( tl, hairline, taglineEl ) {
		if ( hairline ) {
			tl.fromTo(
				hairline,
				{ scaleX: 0, transformOrigin: 'left center' },
				{ scaleX: 1, duration: 0.4, ease: 'power2.inOut' },
				1.4
			);
		}

		if ( taglineEl ) {
			tl.fromTo(
				taglineEl,
				{ opacity: 0, y: 14 },
				{ opacity: 1, y: 0, duration: 0.45, ease: 'power2.out' },
				1.55
			);
		}
	}

	/**
	 * Step 4 (2.0 – 2.6s): overlay clip-path wipe upward + room scale push.
	 *
	 * @param {gsap.core.Timeline} tl
	 * @param {HTMLElement}        overlay
	 * @param {Element}            sceneEl
	 */
	function addStepWipe( tl, overlay, sceneEl ) {
		tl.fromTo(
			overlay,
			{ clipPath: 'inset(0% 0% 0% 0%)' },
			{ clipPath: 'inset(100% 0% 0% 0%)', duration: 0.6, ease: 'power3.inOut' },
			2.0
		);

		if ( sceneEl ) {
			tl.fromTo(
				sceneEl,
				{ scale: 1.0 },
				{ scale: 1.03, duration: 0.6, ease: 'power2.out' },
				2.0
			).to(
				sceneEl,
				{ scale: 1.0, duration: 0.4, ease: 'power2.inOut' },
				2.6
			);
		}
	}

	/* ── Preorder lighter intro ─────────────────────────────────────── */

	/**
	 * Reduced intro for the preorder gateway: dust overlay + wipe only.
	 * Steps 2–3 (lockup beat) are omitted — preorder has no .scene-lockup.
	 *
	 * @param {object} ctx
	 */
	function initPreorderIntro( ctx ) {
		var domResult  = buildOverlay();
		var overlay    = domResult.overlay;
		var canvas     = domResult.canvas;
		var sceneEl    = ctx.sceneEl;

		// Store module-level refs for skip/cleanup.
		activeOverlay    = overlay;
		activeCanvas     = canvas;
		activeSessionKey = ctx.sessionKey;
		activeSceneEl    = sceneEl;
		activeLockup     = null;

		skipFired    = false;
		cleanupFired = false;
		attachSkipListeners();

		var tl = window.gsap.timeline( { onComplete: cleanup } );
		activeTl = tl;

		addStepConcrete( tl, overlay, canvas, sceneEl );
		addStepWipe( tl, overlay, sceneEl );
	}

	/* ── Full scene intro ───────────────────────────────────────────── */

	/**
	 * Full 2.5s intro for immersive collection rooms.
	 *
	 * @param {object} ctx
	 */
	function initSceneIntro( ctx ) {
		if ( ctx.isPreorder ) {
			initPreorderIntro( ctx );
			return;
		}

		var domResult  = buildOverlay();
		var overlay    = domResult.overlay;
		var canvas     = domResult.canvas;
		var sceneEl    = ctx.sceneEl;

		// Clone the title block into the overlay so its reveal animates above
		// the opaque curtain; the room originals are revealed at the wipe.
		var clones      = buildIntroComposition( overlay, ctx );
		var introLockup = clones.lockup;

		// Store module-level refs.
		activeOverlay    = overlay;
		activeCanvas     = canvas;
		activeSessionKey = ctx.sessionKey;
		activeSceneEl    = sceneEl;
		activeLockup     = introLockup; // parallax + cleanup target the visible clone

		skipFired    = false;
		cleanupFired = false;
		watchLockupError( introLockup, ctx.h1 ); // hide a broken clone img, reveal h1
		watchLockupError( ctx.lockup, ctx.h1 );  // same guard for the room's real lockup
		attachSkipListeners();

		var tl = window.gsap.timeline( { onComplete: cleanup } );
		activeTl = tl;

		addStepConcrete( tl, overlay, canvas, sceneEl );
		addStepLockup( tl, introLockup );
		addStepHairlineTagline( tl, clones.hairline, clones.taglineEl );
		revealRoomTitle( tl, ctx, 2.0 );
		addStepWipe( tl, overlay, sceneEl );
	}

	/* ── Bootstrap ──────────────────────────────────────────────────── */

	if ( document.readyState === 'loading' ) {
		document.addEventListener( 'DOMContentLoaded', initImmersiveCore );
	} else {
		initImmersiveCore();
	}

})();
