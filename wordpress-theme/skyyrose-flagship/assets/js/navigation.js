/**
 * Navigation — Impeccable Luxury Refinement
 * Staggered reveals, smooth transitions, keyboard access.
 *
 * @package SkyyRose
 * @since   3.3.0
 */
(function () {
	'use strict';

	/* --------------------------------------------------
	   Staggered Entrance Animation (Slow UI)
	   -------------------------------------------------- */
	document.addEventListener('DOMContentLoaded', function() {
		const navMenu = document.querySelector('.navbar__menu');
		if (navMenu) {
			const items = navMenu.querySelectorAll(':scope > li');
			items.forEach((item, index) => {
				item.style.transitionDelay = `${0.1 + (index * 0.08)}s`;
			});
			// Slight delay to allow initial DOM paint before triggering transition
			setTimeout(() => {
				navMenu.classList.add('is-revealed');
			}, 50);
		}
	});

	/* --------------------------------------------------
	   Image Fallback (CSP-safe replacement)
	   -------------------------------------------------- */
	document.addEventListener('error', function (e) {
		if (e.target.tagName === 'IMG' && e.target.dataset.fallback) {
			e.target.src = e.target.dataset.fallback;
			delete e.target.dataset.fallback;
		}
	}, true);

	/* --------------------------------------------------
	   Single-Menu Relocation (Desktop ⇄ Mobile Drawer)
	   The primary menu is server-rendered once inside
	   .navbar__nav-wrapper; at ≤1024px the same node moves
	   into the drawer. One DOM node, two homes.
	   -------------------------------------------------- */
	var toggle  = document.querySelector('#mobile-menu-toggle');
	var nav     = document.querySelector('.navbar__nav-wrapper');
	var mobilePanel = document.querySelector('#mobile-menu');
	var mobileClose = document.querySelector('#mobile-menu-close');
	var mobileOverlay = document.querySelector('#mobile-menu-overlay');

	var primaryMenu = document.querySelector('.navbar__nav-wrapper .navbar__menu');
	var drawerNav   = document.querySelector('.mobile-menu__nav');
	var drawerMq    = window.matchMedia('(max-width: 1024px)');

	function placePrimaryMenu() {
		if (!primaryMenu || !nav || !drawerNav) return;
		var home = drawerMq.matches ? drawerNav : nav;
		if (primaryMenu.parentElement !== home) {
			home.appendChild(primaryMenu);
		}
	}
	placePrimaryMenu();
	if (typeof drawerMq.addEventListener === 'function') {
		drawerMq.addEventListener('change', placePrimaryMenu);
	} else if (typeof drawerMq.addListener === 'function') {
		drawerMq.addListener(placePrimaryMenu);
	}

	function closeMobileMenu() {
		if (mobilePanel) {
			mobilePanel.setAttribute('aria-hidden', 'true');
			mobilePanel.setAttribute('inert', '');
		}
		document.body.classList.remove('mobile-nav-open');
		if (toggle) {
			toggle.setAttribute('aria-expanded', 'false');
		}
	}

	if (toggle && mobilePanel) {
		toggle.addEventListener('click', function () {
			var expanded = toggle.getAttribute('aria-expanded') === 'true';
			toggle.setAttribute('aria-expanded', String(!expanded));
			
			mobilePanel.setAttribute('aria-hidden', String(expanded));
			if (expanded) {
				mobilePanel.setAttribute('inert', '');
			} else {
				mobilePanel.removeAttribute('inert');
			}
			document.body.classList.toggle('mobile-nav-open');
		});
	}

	if (mobileClose) mobileClose.addEventListener('click', closeMobileMenu);
	if (mobileOverlay) mobileOverlay.addEventListener('click', closeMobileMenu);

	/* --------------------------------------------------
	   Dropdown Navigation
	   -------------------------------------------------- */
	var dropdownToggles = document.querySelectorAll('.navbar__menu .menu-item-has-children > a');
	var isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;

	dropdownToggles.forEach(function (link) {
		if (isTouchDevice) {
			link.addEventListener('click', function (e) {
				var parent = link.parentElement;
				if (!parent) return;
				if (parent.classList.contains('focus')) return;
				
				e.preventDefault();
				dropdownToggles.forEach(function (other) {
					if (other !== link && other.parentElement) {
						other.parentElement.classList.remove('focus');
					}
				});
				parent.classList.add('focus');
			});
		}
	});

	document.addEventListener('click', function (e) {
		var openItems = document.querySelectorAll('.navbar__menu .focus');
		openItems.forEach(function (item) {
			if (!item.contains(e.target)) item.classList.remove('focus');
		});
	});

	/* --------------------------------------------------
	   Header Scroll State
	   -------------------------------------------------- */
	var header = document.querySelector('.site-header');
	var scrollThreshold = 70;
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
	var searchToggle = document.querySelector('#search-toggle');
	var searchOverlay = document.querySelector('.search-overlay');
	var searchClose = document.querySelector('#search-close');
	var searchInput = searchOverlay ? searchOverlay.querySelector('input[type="search"]') : null;
	var pageWrap = document.getElementById('page');

	function closeSearchOverlay() {
		if (searchOverlay) {
			searchOverlay.classList.remove('open');
			searchOverlay.setAttribute('aria-hidden', 'true');
			searchOverlay.setAttribute('inert', '');
		}
		if (searchToggle) searchToggle.setAttribute('aria-expanded', 'false');
		if (pageWrap) pageWrap.removeAttribute('inert');
	}

	if (searchToggle && searchOverlay) {
		searchToggle.addEventListener('click', function () {
			searchOverlay.classList.add('open');
			searchOverlay.setAttribute('aria-hidden', 'false');
			searchOverlay.removeAttribute('inert');
			searchToggle.setAttribute('aria-expanded', 'true');
			if (pageWrap) pageWrap.setAttribute('inert', '');
			if (searchInput) setTimeout(function () { searchInput.focus(); }, 100);
		});
	}

	if (searchClose) searchClose.addEventListener('click', closeSearchOverlay);
	document.addEventListener('keydown', function (e) {
		if (e.key === 'Escape') {
			closeSearchOverlay();
			closeMobileMenu();
		}
	});

	/* --------------------------------------------------
	   Announcement Bar Dismiss
	   -------------------------------------------------- */
	var announcementBar = document.getElementById('announcement-bar');
	var announcementDismissKey = 'skyyrose_announcement_dismissed';

	if (announcementBar) {
		// Hide immediately if dismissed this session.
		if (sessionStorage.getItem(announcementDismissKey)) {
			announcementBar.style.display = 'none';
		}
		var dismissBtn = announcementBar.querySelector('.announcement-bar__dismiss');
		if (dismissBtn) {
			dismissBtn.addEventListener('click', function () {
				sessionStorage.setItem(announcementDismissKey, '1');
				announcementBar.style.display = 'none';
			});
		}
	}

	/* --------------------------------------------------
	   Smooth Scroll
	   -------------------------------------------------- */
	document.querySelectorAll('a.js-smooth-scroll[href^="#"]').forEach(function (link) {
		link.addEventListener('click', function (e) {
			var target = document.querySelector(link.getAttribute('href'));
			if (target) {
				e.preventDefault();
				target.scrollIntoView({ behavior: 'smooth', block: 'start' });
			}
		});
	});
})();
