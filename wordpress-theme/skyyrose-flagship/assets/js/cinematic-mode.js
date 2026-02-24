/**
 * Cinematic Mode Toggle
 *
 * Adds a film-like presentation layer with letterbox bars,
 * deeper vignette, desaturation, and hidden UI chrome.
 * Persists preference in sessionStorage for the current visit.
 *
 * @package SkyyRose_Flagship
 * @since   3.1.0
 */

(function () {
	'use strict';

	var STORAGE_KEY = 'skyyrose_cinematic_mode';
	var toggle = document.querySelector('.cinematic-toggle');

	if (!toggle) return;

	function enable() {
		document.body.classList.add('cinematic-mode');
		toggle.setAttribute('aria-pressed', 'true');
		try { sessionStorage.setItem(STORAGE_KEY, '1'); } catch (e) { /* quota */ }
	}

	function disable() {
		document.body.classList.remove('cinematic-mode');
		toggle.setAttribute('aria-pressed', 'false');
		try { sessionStorage.removeItem(STORAGE_KEY); } catch (e) { /* quota */ }
	}

	function isEnabled() {
		try { return sessionStorage.getItem(STORAGE_KEY) === '1'; } catch (e) { return false; }
	}

	// Restore previous state.
	if (isEnabled()) {
		enable();
	}

	toggle.addEventListener('click', function () {
		if (document.body.classList.contains('cinematic-mode')) {
			disable();
		} else {
			enable();
		}
	});
})();
