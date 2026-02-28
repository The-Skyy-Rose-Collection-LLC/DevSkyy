/**
 * Size & Fit Guide — Interactive Modal
 *
 * Tab switching, unit conversion (in↔cm), focus trap, keyboard nav.
 *
 * @package SkyyRose_Flagship
 * @since   3.10.0
 */

(function () {
	'use strict';

	var modal     = document.getElementById('size-guide-modal');
	var backdrop  = modal ? modal.querySelector('.size-guide-modal__backdrop') : null;
	var content   = modal ? modal.querySelector('.size-guide-modal__content') : null;
	var closeBtn  = modal ? modal.querySelector('.size-guide-modal__close') : null;
	var triggers  = document.querySelectorAll('.size-guide-trigger, [data-open-size-guide]');

	if (!modal || !content) return;

	var tabs      = modal.querySelectorAll('.size-guide-tab');
	var panels    = modal.querySelectorAll('.size-guide-panel');
	var unitBtns  = modal.querySelectorAll('.size-guide-unit');
	var lastFocus = null;
	var currentUnit = 'in';

	/* --------------------------------------------------
	   Open / Close
	   -------------------------------------------------- */

	function openModal(triggerEl) {
		lastFocus = triggerEl || document.activeElement;
		modal.setAttribute('aria-hidden', 'false');
		modal.removeAttribute('inert');
		document.body.style.overflow = 'hidden';

		// Focus close button after transition.
		setTimeout(function () {
			if (closeBtn) closeBtn.focus();
		}, 100);

		modal.addEventListener('keydown', handleKeydown);
	}

	function closeModal() {
		modal.setAttribute('aria-hidden', 'true');
		modal.setAttribute('inert', '');
		document.body.style.overflow = '';
		modal.removeEventListener('keydown', handleKeydown);

		if (lastFocus && lastFocus.offsetParent !== null) {
			lastFocus.focus();
		}
	}

	// Trigger buttons.
	triggers.forEach(function (btn) {
		btn.addEventListener('click', function (e) {
			e.preventDefault();
			openModal(btn);
		});
	});

	// Close button.
	if (closeBtn) {
		closeBtn.addEventListener('click', closeModal);
	}

	// Backdrop click.
	if (backdrop) {
		backdrop.addEventListener('click', closeModal);
	}

	/* --------------------------------------------------
	   Keyboard Navigation
	   -------------------------------------------------- */

	function handleKeydown(e) {
		if (e.key === 'Escape') {
			closeModal();
			return;
		}

		// Focus trap.
		if (e.key === 'Tab') {
			var focusable = content.querySelectorAll(
				'button, [href], input, select, [tabindex]:not([tabindex="-1"])'
			);
			if (!focusable.length) return;
			var first = focusable[0];
			var last  = focusable[focusable.length - 1];

			if (e.shiftKey) {
				if (document.activeElement === first) {
					e.preventDefault();
					last.focus();
				}
			} else {
				if (document.activeElement === last) {
					e.preventDefault();
					first.focus();
				}
			}
		}

		// Arrow key tab navigation (ARIA tabs pattern).
		if (document.activeElement && document.activeElement.getAttribute('role') === 'tab') {
			var tabArr = Array.from(tabs);
			var idx    = tabArr.indexOf(document.activeElement);

			if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
				e.preventDefault();
				var next = (idx + 1) % tabArr.length;
				activateTab(tabArr[next]);
			}
			if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
				e.preventDefault();
				var prev = (idx - 1 + tabArr.length) % tabArr.length;
				activateTab(tabArr[prev]);
			}
		}
	}

	/* --------------------------------------------------
	   Tabs
	   -------------------------------------------------- */

	function activateTab(tab) {
		tabs.forEach(function (t) {
			t.classList.remove('active');
			t.setAttribute('aria-selected', 'false');
			t.setAttribute('tabindex', '-1');
		});
		panels.forEach(function (p) {
			p.classList.remove('active');
			p.setAttribute('hidden', '');
		});

		tab.classList.add('active');
		tab.setAttribute('aria-selected', 'true');
		tab.removeAttribute('tabindex');
		tab.focus();

		var panelId = tab.getAttribute('aria-controls');
		var panel   = document.getElementById(panelId);
		if (panel) {
			panel.classList.add('active');
			panel.removeAttribute('hidden');
		}
	}

	tabs.forEach(function (tab) {
		tab.addEventListener('click', function () {
			activateTab(tab);
		});
	});

	/* --------------------------------------------------
	   Unit Conversion (in ↔ cm)
	   -------------------------------------------------- */

	function switchUnit(unit) {
		if (unit === currentUnit) return;
		currentUnit = unit;

		unitBtns.forEach(function (btn) {
			var isActive = btn.dataset.unit === unit;
			btn.classList.toggle('active', isActive);
			btn.setAttribute('aria-checked', String(isActive));
		});

		// Update all measurement cells.
		var cells = modal.querySelectorAll('td[data-in]');
		cells.forEach(function (td) {
			var value = td.getAttribute('data-' + unit);
			if (value) {
				td.textContent = value + (unit === 'in' ? '\u2033' : ' cm');
			}
		});
	}

	unitBtns.forEach(function (btn) {
		btn.addEventListener('click', function () {
			switchUnit(btn.dataset.unit);
		});
	});

})();
