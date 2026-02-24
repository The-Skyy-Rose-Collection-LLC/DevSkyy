/**
 * Navigation — Hamburger toggle, keyboard nav, scroll state.
 *
 * @package SkyyRose_Flagship
 * @since   3.0.0
 */

(function () {
	'use strict';

	/* --------------------------------------------------
	   Hamburger Toggle (Mobile)
	   -------------------------------------------------- */

	var toggle  = document.querySelector('.menu-toggle');
	var nav     = document.querySelector('.main-navigation');
	var mobilePanel = document.querySelector('.mobile-nav-panel');
	var mobileClose = document.querySelector('.mobile-nav-close');

	if (toggle && nav) {
		toggle.addEventListener('click', function () {
			var expanded = toggle.getAttribute('aria-expanded') === 'true';
			toggle.setAttribute('aria-expanded', String(!expanded));
			nav.classList.toggle('toggled');

			if (mobilePanel) {
				mobilePanel.classList.toggle('open');
				document.body.classList.toggle('mobile-nav-open');
			}
		});
	}

	if (mobileClose && mobilePanel) {
		mobileClose.addEventListener('click', function () {
			mobilePanel.classList.remove('open');
			document.body.classList.remove('mobile-nav-open');
			if (toggle) {
				toggle.setAttribute('aria-expanded', 'false');
			}
			if (nav) {
				nav.classList.remove('toggled');
			}
		});
	}

	/* --------------------------------------------------
	   Dropdown Keyboard Navigation
	   -------------------------------------------------- */

	var dropdownToggles = document.querySelectorAll('.main-navigation .menu-item-has-children > a');

	dropdownToggles.forEach(function (link) {
		link.addEventListener('keydown', function (e) {
			if (e.key === 'Enter' || e.key === ' ') {
				var parent = link.parentElement;
				if (parent) {
					e.preventDefault();
					parent.classList.toggle('focus');
				}
			}
		});
	});

	// Close dropdowns on outside click.
	document.addEventListener('click', function (e) {
		var openItems = document.querySelectorAll('.main-navigation .focus');
		openItems.forEach(function (item) {
			if (!item.contains(e.target)) {
				item.classList.remove('focus');
			}
		});
	});

	/* --------------------------------------------------
	   Header Scroll State
	   -------------------------------------------------- */

	var header = document.querySelector('.site-header');
	var scrollThreshold = 60;
	var ticking = false;

	function updateHeaderState() {
		if (!header) return;
		if (window.scrollY > scrollThreshold) {
			header.classList.add('scrolled');
		} else {
			header.classList.remove('scrolled');
		}
		ticking = false;
	}

	window.addEventListener('scroll', function () {
		if (!ticking) {
			requestAnimationFrame(updateHeaderState);
			ticking = true;
		}
	}, { passive: true });

	/* --------------------------------------------------
	   Search Overlay
	   -------------------------------------------------- */

	var searchToggle = document.querySelector('.header-search-toggle');
	var searchOverlay = document.querySelector('.search-overlay');
	var searchClose = document.querySelector('.search-overlay-close');
	var searchInput = searchOverlay ? searchOverlay.querySelector('input[type="search"]') : null;

	if (searchToggle && searchOverlay) {
		searchToggle.addEventListener('click', function () {
			searchOverlay.classList.add('open');
			searchOverlay.setAttribute('aria-hidden', 'false');
			if (searchInput) {
				setTimeout(function () { searchInput.focus(); }, 100);
			}
		});
	}

	if (searchClose && searchOverlay) {
		searchClose.addEventListener('click', function () {
			searchOverlay.classList.remove('open');
			searchOverlay.setAttribute('aria-hidden', 'true');
		});
	}

	// Close search on Escape.
	document.addEventListener('keydown', function (e) {
		if (e.key === 'Escape' && searchOverlay && searchOverlay.classList.contains('open')) {
			searchOverlay.classList.remove('open');
			searchOverlay.setAttribute('aria-hidden', 'true');
			if (searchToggle) searchToggle.focus();
		}
	});

	/* --------------------------------------------------
	   Smooth Scroll for Anchor Links
	   -------------------------------------------------- */

	document.querySelectorAll('a[href^="#"]').forEach(function (link) {
		link.addEventListener('click', function (e) {
			var target = document.querySelector(link.getAttribute('href'));
			if (target) {
				e.preventDefault();
				target.scrollIntoView({ behavior: 'smooth', block: 'start' });
			}
		});
	});
})();
