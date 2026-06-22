/**
 * Footer CRO — FAQ accordion behavior.
 *
 * Single-open accordion: clicking a question closes any other open question,
 * then toggles the clicked one. Uses aria-expanded as state of truth and
 * style.maxHeight for the height transition (scrollHeight measured at click
 * time so dynamic content reflows correctly).
 *
 * Loaded site-wide by skyyrose_enqueue_global_scripts() when the footer-cro
 * template part renders. Extracted from template-parts/footer-cro.php in
 * v1.5.3 to remove inline <script> tag and keep behavior versioned + minifiable.
 *
 * @package SkyyRose
 * @since   1.5.3
 */
( function () {
	'use strict';

	function init() {
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
