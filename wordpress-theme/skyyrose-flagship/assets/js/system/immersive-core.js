/**
 * Immersive Core — Capabilities A, B, C
 *
 * A — Lenis smooth-scroll (preorder gateway only, shares GSAP clock via ticker)
 * B — Scene intro (immersive rooms + preorder gateway, GSAP timeline)
 * C — Media hover-warp (SVG feTurbulence+feDisplacementMap, opt-in [data-warp])
 *
 * Each capability is an independent guarded function. One failing/not-applying
 * never blocks the others. A and C are called BEFORE the intro early-return
 * ladder so they run even on repeat visits / reduced-motion / GSAP-absent paths.
 *
 * Lenis source: unpkg.com/lenis@1.3.23/dist/lenis.min.js
 * Lenis sets globalThis.Lenis (IIFE build); window.Lenis is the access point.
 *
 * @package SkyyRose
 * @since   7.0.0
 */

(function () {
	'use strict';

	/* ── Public API ─────────────────────────────────────────────────── */

	/**
	 * Entry point. Called on DOMContentLoaded.
	 * Capabilities A and C are self-guarding and run first (before any early
	 * returns) so they fire even on repeat visits, reduced-motion, and GSAP-
	 * absent paths. Capability B (scene intro) follows the existing ladder.
	 */
	function initImmersiveCore() {
		// ── Cap A: Lenis smooth-scroll (preorder only, fully self-guarding) ──
		initLenis();

		// ── Cap C: media hover-warp (both surfaces, fully self-guarding) ─────
		initWarp();

		// ── Cap B: Scene intro (GSAP-dependent) ──────────────────────────────
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
			scheduleTitleHide( ctx.titleOverlay, 4000 );
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
			lockup:       document.querySelector( '.scene-lockup' ),
			taglineEl:    document.querySelector( '.scene-tagline' ),
			h1:           document.querySelector( '#scene-title' ),
			hairline:     document.querySelector( '.scene-hairline' ),
			titleOverlay: document.querySelector( '.scene-title-overlay' ),
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

		// The lockup is now the room title — let it linger, then fade. Anchored
		// to intro completion (here) so it is reliably seen regardless of how
		// long the intro took on a heavy page.
		scheduleTitleHide( document.querySelector( '.scene-title-overlay' ), TITLE_HOLD_MS );

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
		// Opaque from the instant it mounts so the heavy room init beneath is
		// masked even before the GSAP timeline starts (the timeline can be
		// delayed by main-thread contention on these script-heavy pages).
		overlay.style.opacity = '1';

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

	/** How long the lockup title lingers (after it is shown) before fading. */
	var TITLE_HOLD_MS = 3000;

	/**
	 * Fade the room title (.scene-title-overlay) after a hold, once the lockup
	 * has actually been shown. Replaces immersive.js's old fixed 4s-from-DOM-ready
	 * timer, which raced the variable-timing intro (on heavy pages the intro
	 * finished ~6s but the title was hidden at 4s — so it was never seen). No-op
	 * when there is no title overlay (e.g. the preorder gateway).
	 *
	 * @param {Element|null} titleOverlay
	 * @param {number}       holdMs
	 */
	function scheduleTitleHide( titleOverlay, holdMs ) {
		if ( ! titleOverlay ) return;
		window.setTimeout( function () {
			titleOverlay.classList.add( 'hidden' );
		}, holdMs );
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

		// Overlay is already opaque (masking the room) from buildOverlay; only
		// apply the per-collection background here. No opacity fade — the mask
		// must stay solid from mount through the reveal.
		tl.set( overlay, { backgroundColor: bgColor } );

		// Reveal the concrete-dust canvas with the fill (CSS starts it at
		// opacity:0 — GSAP owns it). It leaves with the overlay wipe. Without
		// this tween the canvas drew particles that never showed (dead rAF).
		tl.fromTo( canvas, { opacity: 0 }, { opacity: 1, duration: 0.4, ease: 'power1.out' }, 0 );

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
	 * Step 2 (0.35 – 0.95s): lockup opacity + blur reveal + parallax attach.
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
			{ opacity: 1, filter: 'blur(0px)', duration: 0.6, ease: 'power2.out' },
			0.35
		).add( function () { attachParallax( lockup ); }, 0.35 );
	}

	/**
	 * Step 3 (0.95 – 1.45s): hairline scale-in + tagline fade-up.
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
				{ scaleX: 1, duration: 0.35, ease: 'power2.inOut' },
				0.95
			);
		}

		if ( taglineEl ) {
			tl.fromTo(
				taglineEl,
				{ opacity: 0, y: 14 },
				{ opacity: 1, y: 0, duration: 0.4, ease: 'power2.out' },
				1.05
			);
		}
	}

	/**
	 * Step 4 (1.5 – 2.0s): overlay clip-path wipe upward + room scale push.
	 *
	 * @param {gsap.core.Timeline} tl
	 * @param {HTMLElement}        overlay
	 * @param {Element}            sceneEl
	 */
	function addStepWipe( tl, overlay, sceneEl ) {
		tl.fromTo(
			overlay,
			{ clipPath: 'inset(0% 0% 0% 0%)' },
			{ clipPath: 'inset(100% 0% 0% 0%)', duration: 0.5, ease: 'power3.inOut' },
			1.5
		);

		if ( sceneEl ) {
			tl.fromTo(
				sceneEl,
				{ scale: 1.0 },
				{ scale: 1.03, duration: 0.5, ease: 'power2.out' },
				1.5
			).to(
				sceneEl,
				{ scale: 1.0, duration: 0.4, ease: 'power2.inOut' },
				2.0
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
	 * Full ~2.0s intro for immersive collection rooms (curtain wipe completes at
	 * 2.0s; the room's scale settle resolves at ~2.4s).
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

		// Apply the per-collection background immediately so the mask matches the
		// room palette from mount (overlay is already opacity:1 from buildOverlay).
		var bgEl   = ( sceneEl && sceneEl !== document.body ) ? sceneEl : document.documentElement;
		var maskBg = getComputedStyle( bgEl ).getPropertyValue( '--skyyrose-bg' ).trim();
		if ( maskBg ) overlay.style.backgroundColor = maskBg;

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

		// Timeline starts PAUSED. Steps that don't depend on the lockup image are
		// added now; the lockup blur-reveal is added only once the cloned <img>
		// is decode-ready, then play(). Without this, GSAP animates an undecoded
		// clone on a contended main thread and it paints solid black. The overlay
		// stays opaque (masking the room) during the short decode wait.
		var tl = window.gsap.timeline( { onComplete: cleanup, paused: true } );
		activeTl = tl;

		addStepConcrete( tl, overlay, canvas, sceneEl );
		addStepHairlineTagline( tl, clones.hairline, clones.taglineEl );
		revealRoomTitle( tl, ctx, 1.5 );
		addStepWipe( tl, overlay, sceneEl );

		// Decode the cloned lockup before revealing it. Race a 600ms timeout so a
		// hung/slow decode can never leave the overlay stuck (it plays regardless).
		var cloneImg    = introLockup ? introLockup.querySelector( 'img' ) : null;
		var decodeReady = ( cloneImg && typeof cloneImg.decode === 'function' )
			? Promise.race( [
				cloneImg.decode().catch( function () {} ),
				new Promise( function ( resolve ) { window.setTimeout( resolve, 600 ); } )
			] )
			: Promise.resolve();

		decodeReady.then( function () {
			if ( cleanupFired ) return;        // user skipped during decode
			addStepLockup( tl, introLockup );  // inserts the reveal at position 0.4
			tl.play();
		} );
	}

	/* ── Capability A: Lenis smooth-scroll (preorder gateway only) ─────── */

	/** @type {import('lenis').default|null} */
	var lenisInstance = null;

	/**
	 * Named ticker callback kept in module scope so we can remove it on destroy.
	 * @type {Function|null}
	 */
	var lenisTicker = null;

	/**
	 * Init Lenis smooth-scroll.
	 *
	 * Guards (all must pass):
	 *   1. Page is NOT an immersive room (.immersive-page with overflow:hidden).
	 *      Detection: main.preorder-gateway present in DOM.
	 *   2. window.Lenis constructor available (lenis lib loaded).
	 *   3. window.gsap available (ticker is the clock).
	 *   4. prefers-reduced-motion: reduce → native scroll, do NOT init.
	 *
	 * Single clock: lenis.raf driven by gsap.ticker; lenis.on('scroll',
	 * ScrollTrigger.update) if ScrollTrigger is present. No second rAF.
	 * Destroyed on pagehide.
	 */
	function initLenis() {
		// Guard 1: only on the preorder gateway (long-scroll page)
		if ( ! document.querySelector( 'main.preorder-gateway' ) ) {
			return;
		}

		// Guard 2: Lenis lib must be available
		if ( typeof window.Lenis !== 'function' ) {
			return;
		}

		// Guard 3: GSAP ticker is the clock — no GSAP, no Lenis
		if ( typeof window.gsap === 'undefined' ) {
			return;
		}

		// Guard 4: honour reduced-motion — native scroll
		if ( prefersReducedMotion() ) {
			return;
		}

		// autoRaf: false — GSAP ticker drives raf, not Lenis's internal loop.
		// This is the single-clock requirement from spec §4A.
		lenisInstance = new window.Lenis( { autoRaf: false } );

		// Wire scroll events so existing ScrollTrigger-based parallax rides
		// the Lenis scroll position (one event chain, no double-fire).
		lenisInstance.on( 'scroll', function () {
			if ( window.ScrollTrigger ) {
				window.ScrollTrigger.update();
			}
		} );

		// Drive Lenis from GSAP ticker (convert seconds → ms).
		lenisTicker = function ( time ) {
			lenisInstance.raf( time * 1000 );
		};
		window.gsap.ticker.add( lenisTicker );

		// lagSmoothing(0) prevents GSAP inserting artificial lag-catch frames
		// that would produce jitter between Lenis scroll and GSAP animations.
		window.gsap.ticker.lagSmoothing( 0 );

		// Destroy on tab hide / back-forward cache to avoid orphaned tickers.
		window.addEventListener( 'pagehide', destroyLenis );
	}

	/** Tear down Lenis instance and remove ticker callback. */
	function destroyLenis() {
		if ( lenisTicker && window.gsap ) {
			window.gsap.ticker.remove( lenisTicker );
			lenisTicker = null;
		}
		if ( lenisInstance ) {
			lenisInstance.destroy();
			lenisInstance = null;
		}
	}

	/* ── Capability C: media hover-warp ────────────────────────────────── */

	/** ID used for the injected SVG filter element. */
	var WARP_FILTER_ID = 'ic-warp-filter';

	/**
	 * Init the SVG displacement-map warp filter and wire [data-warp] targets.
	 *
	 * Approach: inject an <svg><filter> block once into <body> using
	 * createElementNS (HTML createElement does NOT produce usable SVG
	 * primitives). CSS in immersive-core.css applies `filter:url(#ic-warp-filter)`
	 * on [data-warp]:hover via @media (hover:hover). JS guards gate on reduced-
	 * motion and touch so the SVG element itself is never injected on those paths.
	 *
	 * Warp targets (spec §4C + §9):
	 *   scene.php  .scene-layer img         (each scene image)
	 *   scene.php  .product-panel-thumb img  (product panel thumbnail)
	 *   preorder   .showcase__card           (collection showcase cards)
	 *
	 * data-warp attributes are added by PHP (scene.php + template-preorder-gateway.php).
	 * This function only injects the filter and wires nothing extra — CSS handles hover.
	 *
	 * Guards:
	 *   prefers-reduced-motion: reduce → do NOT inject (no filter to trigger)
	 *   hover: none (touch devices)      → do NOT inject
	 *   Filter already injected           → do NOT inject a second time
	 */
	function initWarp() {
		// Guard: reduced-motion
		if ( prefersReducedMotion() ) {
			return;
		}

		// Guard: touch / no-hover device
		if ( window.matchMedia( '(hover: none)' ).matches ) {
			return;
		}

		// Guard: already injected (idempotent)
		if ( document.getElementById( WARP_FILTER_ID ) ) {
			return;
		}

		injectWarpFilter();
	}

	/**
	 * Build and inject the SVG warp filter into <body>, then wire mouseenter/
	 * mouseleave on every [data-warp] element.
	 *
	 * Uses createElementNS throughout — createElement produces HTML elements
	 * that do NOT participate in SVG filter resolution.
	 *
	 * Filter: feTurbulence (baseFrequency 0.018 0.022, octaves 2) →
	 * feDisplacementMap (scale tweened 0→5→0px per hover). Amplitude 5px is
	 * within the spec-specified 4-8px luxury range.
	 *
	 * Easing mechanism: CSS cannot interpolate url() filter references (they are
	 * discrete), so the smoothing is done by tweening the feDisplacementMap
	 * `scale` SVG attribute via a GSAP gsap.to(). The CSS [data-warp-active]
	 * selector gates presence of the filter url (added/removed by JS); GSAP
	 * owns intensity ramp so the warp fades in/out rather than snapping.
	 * If GSAP is absent the tween block is skipped; the attribute-toggle still
	 * applies the filter (a snap rather than a ramp — acceptable degradation).
	 *
	 * Chromatic offset: a genuine per-channel feOffset split is deferred to a
	 * later pass. The current filter produces a single-displacement warp only.
	 */
	function injectWarpFilter() {
		var NS = 'http://www.w3.org/2000/svg';

		var svg = document.createElementNS( NS, 'svg' );
		svg.setAttribute( 'xmlns',       NS );
		svg.setAttribute( 'width',       '0' );
		svg.setAttribute( 'height',      '0' );
		svg.setAttribute( 'aria-hidden', 'true' );
		svg.setAttribute( 'focusable',   'false' );
		// Position out of flow — zero-size SVG still needs to be in the DOM.
		svg.style.position = 'absolute';
		svg.style.width    = '0';
		svg.style.height   = '0';
		svg.style.overflow = 'hidden';

		var defs = document.createElementNS( NS, 'defs' );

		var filter = document.createElementNS( NS, 'filter' );
		filter.setAttribute( 'id',      WARP_FILTER_ID );
		// Expand filter region so displaced pixels near edges aren't clipped.
		filter.setAttribute( 'x',      '-5%' );
		filter.setAttribute( 'y',      '-5%' );
		filter.setAttribute( 'width',  '110%' );
		filter.setAttribute( 'height', '110%' );

		var turbulence = document.createElementNS( NS, 'feTurbulence' );
		turbulence.setAttribute( 'type',          'turbulence' );
		// Low baseFrequency = slow, large-scale organic displacement (not grain).
		turbulence.setAttribute( 'baseFrequency', '0.018 0.022' );
		turbulence.setAttribute( 'numOctaves',    '2' );
		turbulence.setAttribute( 'seed',          '3' );
		turbulence.setAttribute( 'result',        'warpNoise' );

		var displacement = document.createElementNS( NS, 'feDisplacementMap' );
		displacement.setAttribute( 'in',              'SourceGraphic' );
		displacement.setAttribute( 'in2',             'warpNoise' );
		// Start at scale 0; GSAP tweens it up to 5 on hover, back to 0 on leave.
		displacement.setAttribute( 'scale',           '0' );
		displacement.setAttribute( 'xChannelSelector', 'R' );
		displacement.setAttribute( 'yChannelSelector', 'G' );

		filter.appendChild( turbulence );
		filter.appendChild( displacement );
		defs.appendChild( filter );
		svg.appendChild( defs );
		document.body.appendChild( svg );

		// Store reference to the displacement node for GSAP tweening.
		warpDisplacementEl = displacement;

		// Wire hover listeners on all [data-warp] targets now present in the DOM.
		wireWarpTargets();
	}

	/** @type {SVGFEDisplacementMapElement|null} */
	var warpDisplacementEl = null;

	/** @type {Function|null} Running tween object (GSAP) for the scale attr. */
	var warpTween = null;

	/**
	 * Attach mouseenter/mouseleave to every [data-warp] element currently in DOM.
	 * Toggles [data-warp-active] (gates CSS filter url) and tweens the
	 * feDisplacementMap scale attribute 0→5→0 so the warp eases in and out.
	 */
	function wireWarpTargets() {
		var targets = document.querySelectorAll( '[data-warp]' );
		if ( ! targets.length ) return;

		var hasGsap = ( typeof window.gsap !== 'undefined' );

		// Proxy object that GSAP can tween — SVG attributes aren't
		// directly animatable via gsap.to(el,...) without GSAP's attr plugin.
		// We use a plain object with an onUpdate callback that writes the attribute.
		var scaleProxy = { value: 0 };

		function setScale( v ) {
			if ( warpDisplacementEl ) {
				warpDisplacementEl.setAttribute( 'scale', String( Math.round( v * 10 ) / 10 ) );
			}
		}

		function onEnter( el ) {
			el.setAttribute( 'data-warp-active', '' );

			if ( hasGsap && warpDisplacementEl ) {
				if ( warpTween ) warpTween.kill();
				warpTween = window.gsap.to( scaleProxy, {
					value:    5,
					duration: 0.45,
					ease:     'power2.out',
					onUpdate: function () { setScale( scaleProxy.value ); }
				} );
			} else {
				// GSAP absent — snap to target scale (still correct, not smooth).
				setScale( 5 );
			}
		}

		function onLeave( el ) {
			if ( hasGsap && warpDisplacementEl ) {
				if ( warpTween ) warpTween.kill();
				warpTween = window.gsap.to( scaleProxy, {
					value:    0,
					duration: 0.4,
					ease:     'power2.in',
					onUpdate: function () { setScale( scaleProxy.value ); },
					onComplete: function () { el.removeAttribute( 'data-warp-active' ); }
				} );
			} else {
				setScale( 0 );
				el.removeAttribute( 'data-warp-active' );
			}
		}

		for ( var i = 0; i < targets.length; i++ ) {
			(function ( el ) {
				el.addEventListener( 'mouseenter', function () { onEnter( el ); } );
				el.addEventListener( 'mouseleave', function () { onLeave( el ); } );
			})( targets[ i ] );
		}
	}

	/* ── Bootstrap ──────────────────────────────────────────────────── */

	if ( document.readyState === 'loading' ) {
		document.addEventListener( 'DOMContentLoaded', initImmersiveCore );
	} else {
		initImmersiveCore();
	}

})();
