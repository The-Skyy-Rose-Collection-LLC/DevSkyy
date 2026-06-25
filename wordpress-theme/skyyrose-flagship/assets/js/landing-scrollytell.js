/**
 * Landing Pages — Split Scrollytell (v3)
 *
 * Handles scroll-sync between .lp-narrative__pane elements and
 * the pre-rendered .lp-vp__layer divs inside #lp-viewport-inner.
 *
 * What this file does:
 *   - IntersectionObserver on .lp-narrative__pane → crossfades
 *     .lp-vp__layer[data-pane="N"] by toggling .lp-vp__layer--visible.
 *   - Tracks .lp-split visibility → shows/hides .lp-pane-indicators.
 *   - Indicator dot clicks → scrollIntoView on the target pane.
 *   - MutationObserver syncs aria-hidden on layers.
 *   - Screen-reader announcements via #lp-live-region.
 *   - Email CTA form validation and status feedback.
 *
 * What this file does NOT do:
 *   - Fetch product data (PHP renders all layers server-side).
 *   - Use innerHTML (DOM manipulation only via createElement/textContent).
 *   - Handle .lp-rv scroll-reveal (premium-interactions.js owns that).
 *   - Use GSAP.
 *
 * @package SkyyRose
 * @since   1.2.0
 */

( function () {
	'use strict';

	/* ------------------------------------------------------------------
	   State
	------------------------------------------------------------------ */

	var state = {
		activePane: 0,
	};

	var announcementTimer = null;

	/* ------------------------------------------------------------------
	   DOM references (set in init)
	------------------------------------------------------------------ */

	var panes        = [];
	var layers       = [];
	var indicators   = [];
	var indicatorWrap = null;
	var liveRegion   = null;
	var splitEl      = null;

	/* ------------------------------------------------------------------
	   Layer crossfade
	------------------------------------------------------------------ */

	/**
	 * Show the viewport layer matching paneIndex; hide all others.
	 * Uses a two-step crossfade: add visible to new, remove from old
	 * after a short overlap so there is no flash of empty.
	 *
	 * @param {number} paneIndex
	 */
	function showPaneLayer( paneIndex ) {
		if ( ! layers.length ) { return; }

		var next = null;
		var toHide = [];

		for ( var i = 0; i < layers.length; i++ ) {
			var dataPane = parseInt( layers[ i ].getAttribute( 'data-pane' ), 10 );
			if ( dataPane === paneIndex ) {
				next = layers[ i ];
			} else if ( layers[ i ].classList.contains( 'lp-vp__layer--visible' ) ) {
				toHide.push( layers[ i ] );
			}
		}

		if ( ! next ) { return; }

		// Make new layer visible first (overlap window keeps display non-blank).
		next.classList.add( 'lp-vp__layer--visible' );

		// After one animation frame, remove old layers.
		window.requestAnimationFrame( function () {
			window.requestAnimationFrame( function () {
				for ( var j = 0; j < toHide.length; j++ ) {
					toHide[ j ].classList.remove( 'lp-vp__layer--visible' );
				}
				syncLayerAriaHidden();
			} );
		} );

		scheduleAnnouncement( paneIndex );
	}

	/* ------------------------------------------------------------------
	   aria-hidden sync on layers
	------------------------------------------------------------------ */

	function syncLayerAriaHidden() {
		for ( var i = 0; i < layers.length; i++ ) {
			if ( layers[ i ].classList.contains( 'lp-vp__layer--visible' ) ) {
				layers[ i ].removeAttribute( 'aria-hidden' );
			} else {
				layers[ i ].setAttribute( 'aria-hidden', 'true' );
			}
		}
	}

	/* ------------------------------------------------------------------
	   Screen-reader announcement
	------------------------------------------------------------------ */

	/**
	 * Debounced announcement: read the product name from the active layer.
	 *
	 * @param {number} paneIndex
	 */
	function scheduleAnnouncement( paneIndex ) {
		if ( ! liveRegion ) { return; }
		if ( announcementTimer ) {
			clearTimeout( announcementTimer );
		}
		announcementTimer = setTimeout( function () {
			var activeLayer = null;
			for ( var i = 0; i < layers.length; i++ ) {
				if ( parseInt( layers[ i ].getAttribute( 'data-pane' ), 10 ) === paneIndex ) {
					activeLayer = layers[ i ];
					break;
				}
			}
			if ( ! activeLayer ) { return; }
			var nameEl = activeLayer.querySelector( '.lp-vp__name' );
			if ( nameEl ) {
				liveRegion.textContent = nameEl.textContent;
			}
		}, 350 );
	}

	/* ------------------------------------------------------------------
	   Pane indicators
	------------------------------------------------------------------ */

	function updatePaneIndicators( activeIndex ) {
		for ( var i = 0; i < indicators.length; i++ ) {
			if ( i === activeIndex ) {
				indicators[ i ].classList.add( 'is-active' );
				indicators[ i ].setAttribute( 'aria-current', 'true' );
			} else {
				indicators[ i ].classList.remove( 'is-active' );
				indicators[ i ].removeAttribute( 'aria-current' );
			}
		}
	}

	function attachPaneIndicatorClicks() {
		for ( var i = 0; i < indicators.length; i++ ) {
			( function ( idx ) {
				indicators[ idx ].addEventListener( 'click', function () {
					if ( panes[ idx ] ) {
						panes[ idx ].scrollIntoView( { behavior: 'smooth', block: 'center' } );
					}
				} );
			} )( i );
		}
	}

	/* ------------------------------------------------------------------
	   IntersectionObserver: pane scroll-sync
	------------------------------------------------------------------ */

	function attachPaneObserver() {
		if ( ! window.IntersectionObserver ) { return; }

		var observer = new IntersectionObserver(
			function ( entries ) {
				for ( var e = 0; e < entries.length; e++ ) {
					var entry = entries[ e ];
					if ( ! entry.isIntersecting ) { continue; }
					var idx = parseInt( entry.target.getAttribute( 'data-pane-index' ), 10 );
					if ( isNaN( idx ) ) { continue; }
					if ( state.activePane === idx ) { continue; }
					state.activePane = idx;
					showPaneLayer( idx );
					updatePaneIndicators( idx );
				}
			},
			{
				threshold: 0.4,
				rootMargin: '0px 0px -15% 0px',
			}
		);

		for ( var i = 0; i < panes.length; i++ ) {
			observer.observe( panes[ i ] );
		}
	}

	/* ------------------------------------------------------------------
	   IntersectionObserver: indicator show/hide on .lp-split visibility
	------------------------------------------------------------------ */

	function attachSplitVisibilityObserver() {
		if ( ! indicatorWrap || ! splitEl || ! window.IntersectionObserver ) { return; }

		var splitObserver = new IntersectionObserver(
			function ( entries ) {
				for ( var e = 0; e < entries.length; e++ ) {
					if ( entries[ e ].isIntersecting ) {
						indicatorWrap.classList.add( 'is-active' );
					} else {
						indicatorWrap.classList.remove( 'is-active' );
					}
				}
			},
			{ threshold: 0.05 }
		);

		splitObserver.observe( splitEl );
	}

	/* ------------------------------------------------------------------
	   MutationObserver: watch layer class changes → sync aria-hidden
	------------------------------------------------------------------ */

	function watchLayerClasses() {
		if ( ! window.MutationObserver || ! layers.length ) { return; }

		var mo = new MutationObserver( function () {
			syncLayerAriaHidden();
		} );

		for ( var i = 0; i < layers.length; i++ ) {
			mo.observe( layers[ i ], { attributes: true, attributeFilter: [ 'class' ] } );
		}
	}

	/* ------------------------------------------------------------------
	   Email form
	------------------------------------------------------------------ */

	function initEmailForm() {
		var forms = document.querySelectorAll( '.lp-email__form' );
		for ( var f = 0; f < forms.length; f++ ) {
			( function ( form ) {
				form.addEventListener( 'submit', function ( evt ) {
					evt.preventDefault();
					var emailInput = form.querySelector( '.lp-email__input[type="email"]' );
					var statusEl   = form.parentNode ? form.parentNode.querySelector( '.lp-email__status' ) : null;

					if ( ! emailInput ) { return; }

					var email = emailInput.value.trim();
					if ( ! email || ! /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test( email ) ) {
						setEmailStatus( statusEl, 'error', 'Please enter a valid email address.' );
						emailInput.focus();
						return;
					}

					// Disable form while submitting.
					var submitBtn = form.querySelector( '[type="submit"]' );
					if ( submitBtn ) { submitBtn.disabled = true; }
					emailInput.disabled = true;
					setEmailStatus( statusEl, '', 'Subscribing…' );

					// Native WordPress AJAX via wp-admin/admin-ajax.php.
					var formData = new FormData();
					formData.append( 'action', 'skyyrose_newsletter_subscribe' );
					formData.append( 'email', email );
					var nonceField = form.querySelector( '[name="skyyrose_newsletter_nonce"]' );
					if ( nonceField ) {
						formData.append( 'skyyrose_newsletter_nonce', nonceField.value );
					}

					fetch(
						( typeof skyyRoseData !== 'undefined' && skyyRoseData.ajaxUrl )
							? skyyRoseData.ajaxUrl
							: '/wp-admin/admin-ajax.php',
						{ method: 'POST', body: formData, credentials: 'same-origin' }
					)
						.then( function ( res ) { return res.json(); } )
						.then( function ( data ) {
							if ( data && data.success ) {
								setEmailStatus( statusEl, 'success', data.data || 'You’re in. Welcome to the collection.' );
								emailInput.value = '';
							} else {
								setEmailStatus( statusEl, 'error', ( data && data.data ) ? data.data : 'Something went wrong. Please try again.' );
							}
						} )
						.catch( function () {
							setEmailStatus( statusEl, 'error', 'Something went wrong. Please try again.' );
						} )
						.finally( function () {
							if ( submitBtn ) { submitBtn.disabled = false; }
							emailInput.disabled = false;
						} );
				} );
			} )( forms[ f ] );
		}
	}

	/**
	 * @param {Element|null} statusEl
	 * @param {string}       type   'success' | 'error' | ''
	 * @param {string}       msg
	 */
	function setEmailStatus( statusEl, type, msg ) {
		if ( ! statusEl ) { return; }
		statusEl.textContent = msg;
		statusEl.className   = 'lp-email__status';
		if ( type ) {
			statusEl.classList.add( 'lp-email__status--' + type );
		}
	}

	/* ------------------------------------------------------------------
	   Reduced motion: skip crossfade transitions
	------------------------------------------------------------------ */

	function applyReducedMotion() {
		var mq = window.matchMedia && window.matchMedia( '(prefers-reduced-motion: reduce)' );
		if ( ! mq || ! mq.matches ) { return; }
		// Force all layers to their final state immediately.
		for ( var i = 0; i < layers.length; i++ ) {
			layers[ i ].style.transition = 'none';
		}
		// Show pane 0 without animation.
		showPaneLayer( 0 );
	}

	/* ------------------------------------------------------------------
	   Init
	------------------------------------------------------------------ */

	function init() {
		panes         = Array.prototype.slice.call( document.querySelectorAll( '.lp-narrative__pane' ) );
		layers        = Array.prototype.slice.call( document.querySelectorAll( '#lp-viewport-inner .lp-vp__layer' ) );
		indicators    = Array.prototype.slice.call( document.querySelectorAll( '.lp-pane-indicator' ) );
		indicatorWrap = document.querySelector( '.lp-pane-indicators' );
		liveRegion    = document.getElementById( 'lp-live-region' );
		splitEl       = document.querySelector( '.lp-split' );

		// Bail gracefully if key elements are absent.
		if ( ! panes.length || ! layers.length ) { return; }

		// Show first pane's layer immediately.
		showPaneLayer( 0 );
		updatePaneIndicators( 0 );

		applyReducedMotion();
		attachPaneObserver();
		attachSplitVisibilityObserver();
		attachPaneIndicatorClicks();
		watchLayerClasses();
		initEmailForm();
	}

	if ( document.readyState === 'loading' ) {
		document.addEventListener( 'DOMContentLoaded', init );
	} else {
		init();
	}

} )();
