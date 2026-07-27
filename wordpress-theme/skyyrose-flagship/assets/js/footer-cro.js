/**
 * Footer CRO — FAQ accordion + animated newsletter capture.
 *
 * Accordion: single-open, aria-expanded as state of truth, style.maxHeight
 * for the height transition (scrollHeight measured at click time so dynamic
 * content reflows correctly).
 *
 * Newsletter: intercepts the footer email-capture form (which otherwise
 * full-page-navigates to admin-ajax.php's raw JSON response), submits via
 * fetch, and animates the success / error states in place. Server-side
 * messages arrive already localized from skyyrose_ajax_newsletter_subscribe();
 * the only client-only string (network failure) is localized via
 * skyyRoseFooterCro (wp_localize_script in inc/enqueue.php).
 *
 * Loaded site-wide by skyyrose_enqueue_global_scripts(). Extracted from
 * template-parts/footer-cro.php in v1.5.3 to remove inline <script> tag.
 *
 * @package SkyyRose
 * @since   1.5.3
 */
( function () {
	'use strict';

	function initNewsletter() {
		var form = document.querySelector( '.footer-newsletter__form' );
		if ( ! form ) {
			return;
		}

		var input  = form.querySelector( '.footer-newsletter__input' );
		var submit = form.querySelector( '.footer-newsletter__submit' );
		var status = form.querySelector( '.footer-newsletter__status' );
		if ( ! input || ! submit || ! status ) {
			return;
		}

		var reduced = window.matchMedia( '(prefers-reduced-motion: reduce)' ).matches;

		function setStatus( message, isError ) {
			status.textContent = message;
			status.classList.toggle( 'footer-newsletter__status--error', !! isError );
			status.classList.toggle( 'footer-newsletter__status--success', ! isError );
		}

		function flashError() {
			if ( reduced ) {
				return;
			}
			form.classList.add( 'is-error' );
			setTimeout( function () {
				form.classList.remove( 'is-error' );
			}, 500 );
		}

		form.addEventListener( 'submit', function ( e ) {
			e.preventDefault();
			if ( form.classList.contains( 'is-submitting' ) || form.classList.contains( 'is-success' ) ) {
				return;
			}

			form.classList.add( 'is-submitting' );
			submit.disabled = true;

			// getAttribute, NOT form.action: this form carries a hidden input named "action"
			// (admin-ajax requires it), and a named form control shadows the form's `action`
			// IDL property. form.action returns that HTMLInputElement, which stringifies to
			// "[object HTMLInputElement]" and resolves to a bogus same-origin path — every
			// submission would 404 and fall into the catch below. Verified in-browser.
			fetch( form.getAttribute( 'action' ), {
				method: 'POST',
				body: new FormData( form ),
				credentials: 'same-origin'
			} )
				.then( function ( res ) {
					return res.json();
				} )
				.then( function ( data ) {
					form.classList.remove( 'is-submitting' );
					var message = ( data && data.data && data.data.message ) || '';

					if ( data && data.success ) {
						form.classList.add( 'is-success' );
						setStatus( message, false );
					} else {
						submit.disabled = false;
						setStatus( message, true );
						flashError();
					}
				} )
				.catch( function () {
					form.classList.remove( 'is-submitting' );
					submit.disabled = false;
					var fallback = ( window.skyyRoseFooterCro && window.skyyRoseFooterCro.networkError ) || '';
					setStatus( fallback, true );
					flashError();
				} );
		} );
	}

	function init() {
		initNewsletter();

		var btns = document.querySelectorAll( '.ft-cro-faq__question' );
		if ( ! btns.length ) {
			return;
		}

		btns.forEach( function ( btn ) {
			btn.addEventListener( 'click', function () {
				var expanded   = btn.getAttribute( 'aria-expanded' ) === 'true';
				var answerId   = btn.getAttribute( 'aria-controls' );
				var answerEl   = answerId ? document.getElementById( answerId ) : null;

				// Close every other open question.
				btns.forEach( function ( other ) {
					if ( other === btn ) {
						return;
					}
					other.setAttribute( 'aria-expanded', 'false' );
					var otherId = other.getAttribute( 'aria-controls' );
					var otherEl = otherId ? document.getElementById( otherId ) : null;
					if ( otherEl ) {
						otherEl.style.maxHeight = '0';
					}
				} );

				// Toggle this one.
				btn.setAttribute( 'aria-expanded', expanded ? 'false' : 'true' );
				if ( answerEl ) {
					answerEl.style.maxHeight = expanded ? '0' : answerEl.scrollHeight + 'px';
				}
			} );
		} );
	}

	if ( document.readyState === 'loading' ) {
		document.addEventListener( 'DOMContentLoaded', init );
	} else {
		init();
	}
} )();
