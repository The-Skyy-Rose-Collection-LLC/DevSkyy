/**
 * Navigation — Hamburger toggle, keyboard nav, scroll state.
 *
 * @package SkyyRose_Flagship
 * @since   3.0.0
 */

(function () {
	'use strict';

	/* --------------------------------------------------
	   Image Fallback (CSP-safe replacement for inline onerror)
	   Catches broken images site-wide and swaps to data-fallback URL.
	   -------------------------------------------------- */

	document.addEventListener('error', function (e) {
		if (e.target.tagName === 'IMG' && e.target.dataset.fallback) {
			e.target.src = e.target.dataset.fallback;
			delete e.target.dataset.fallback;
		}
	}, true);

	/* --------------------------------------------------
	   Hamburger Toggle (Mobile)
	   -------------------------------------------------- */

	var toggle  = document.querySelector('#mobile-menu-toggle, .menu-toggle');
	var nav     = document.querySelector('.navbar__nav-wrapper, .main-navigation');
	var mobilePanel = document.querySelector('#mobile-menu, .mobile-menu');
	var mobileClose = document.querySelector('#mobile-menu-close, .mobile-menu__close');

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

	var dropdownToggles = document.querySelectorAll('.navbar__menu .menu-item-has-children > a, .main-navigation .menu-item-has-children > a');

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
		var openItems = document.querySelectorAll('.navbar__menu .focus, .main-navigation .focus');
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

	var searchToggle = document.querySelector('#search-toggle, .navbar__search-btn, .header-search-toggle');
	var searchOverlay = document.querySelector('.search-overlay');
	var searchClose = document.querySelector('#search-close, .search-overlay__close, .search-overlay-close');
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

	document.querySelectorAll('a.js-smooth-scroll[href^="#"], .site-header a[href^="#"], .site-footer a[href^="#"]').forEach(function (link) {
		link.addEventListener('click', function (e) {
			var href = link.getAttribute('href');
			if (href === '#' || href.length < 2) return;
			var target = document.querySelector(href);
			if (target) {
				e.preventDefault();
				target.scrollIntoView({ behavior: 'smooth', block: 'start' });
			}
		});
	});
})();
