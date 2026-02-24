/**
 * Social Proof + Urgency Engine
 *
 * Rotating purchase notifications, live viewer count,
 * scarcity indicators, and sticky pre-order CTA bar.
 * All data is simulated client-side for pre-launch.
 *
 * @package SkyyRose_Flagship
 * @since   3.2.0
 */

(function () {
	'use strict';

	/* --------------------------------------------------
	   Configuration
	   -------------------------------------------------- */

	var CONFIG = {
		toastInterval:    18000,  // 18s between toasts
		toastDuration:     6000,  // 6s visible
		stickyDelay:       4000,  // 4s before sticky bar appears
		viewerRefresh:    30000,  // 30s between viewer count updates
		minViewers:          12,
		maxViewers:          47,
	};

	/* --------------------------------------------------
	   Product Catalog (pre-launch simulated data)
	   -------------------------------------------------- */

	var PRODUCTS = [
		{ name: 'BLACK Rose Sherpa Jacket',       price: '$295', collection: 'Black Rose',  image: 'br-006-sherpa.jpg' },
		{ name: 'BLACK Rose Quarter Zip Fleece',   price: '$175', collection: 'Black Rose',  image: 'br-005-fleece.jpg' },
		{ name: 'BLACK Rose Beanie',               price: '$45',  collection: 'Black Rose',  image: 'br-007-beanie.jpg' },
		{ name: 'Love Hurts Varsity Jacket',       price: '$265', collection: 'Love Hurts',  image: 'lh-004-varsity.jpg' },
		{ name: 'Love Hurts Joggers',              price: '$95',  collection: 'Love Hurts',  image: 'lh-002-joggers.jpg' },
		{ name: 'Love Hurts Basketball Shorts',    price: '$75',  collection: 'Love Hurts',  image: 'lh-003-shorts.jpg' },
		{ name: 'Signature Rose Gold Hoodie',      price: '$185', collection: 'Signature',   image: 'sig-001-hoodie.jpg' },
		{ name: 'Signature Rose Gold Joggers',     price: '$125', collection: 'Signature',   image: 'sig-003-joggers.jpg' },
		{ name: 'Signature Premium Tee',           price: '$85',  collection: 'Signature',   image: 'sig-002-tee.jpg' },
	];

	var FIRST_NAMES = [
		'Sarah', 'Marcus', 'Aaliyah', 'Devon', 'Kenji',
		'Jasmine', 'Tyler', 'Nia', 'Carlos', 'Imani',
		'Jordan', 'Ayanna', 'Darius', 'Zara', 'Andre',
		'Raven', 'Xavier', 'Amara', 'Trey', 'Maya',
	];

	var CITIES = [
		'Oakland, CA', 'Los Angeles, CA', 'Atlanta, GA', 'Houston, TX',
		'New York, NY', 'Chicago, IL', 'Miami, FL', 'Detroit, MI',
		'Dallas, TX', 'San Francisco, CA', 'Brooklyn, NY', 'Seattle, WA',
		'Portland, OR', 'Denver, CO', 'Nashville, TN', 'Phoenix, AZ',
	];

	var ACTIONS = [
		'just pre-ordered',
		'just added to cart',
		'just secured',
	];

	var TIME_LABELS = [
		'2 minutes ago', '5 minutes ago', '8 minutes ago',
		'12 minutes ago', '15 minutes ago', '20 minutes ago',
	];

	/* --------------------------------------------------
	   Helpers
	   -------------------------------------------------- */

	function rand(arr) {
		return arr[Math.floor(Math.random() * arr.length)];
	}

	function randInt(min, max) {
		return Math.floor(Math.random() * (max - min + 1)) + min;
	}

	/* --------------------------------------------------
	   Toast Notification System
	   -------------------------------------------------- */

	var toastEl     = null;
	var toastTimer  = null;
	var hideTimer   = null;
	var dismissed   = false;

	function createToast() {
		var el = document.createElement('div');
		el.className = 'social-proof-toast';
		el.setAttribute('role', 'status');
		el.setAttribute('aria-live', 'polite');
		el.innerHTML =
			'<div class="social-proof-toast__thumb"><img src="" alt="" loading="lazy"></div>' +
			'<div class="social-proof-toast__body">' +
				'<div class="social-proof-toast__action"></div>' +
				'<div class="social-proof-toast__product"></div>' +
				'<div class="social-proof-toast__meta"></div>' +
			'</div>' +
			'<button class="social-proof-toast__close" type="button" aria-label="Dismiss">&times;</button>';

		el.querySelector('.social-proof-toast__close').addEventListener('click', function () {
			hideToast();
			dismissed = true;
			if (toastTimer) clearInterval(toastTimer);
		});

		document.body.appendChild(el);
		return el;
	}

	function showToast() {
		if (dismissed || !toastEl) return;

		var product = rand(PRODUCTS);
		var name    = rand(FIRST_NAMES);
		var city    = rand(CITIES);
		var action  = rand(ACTIONS);
		var time    = rand(TIME_LABELS);

		var imgBase = '';
		if (typeof skyyRoseData !== 'undefined' && skyyRoseData.assetsUri) {
			imgBase = skyyRoseData.assetsUri + '/images/products/';
		}

		var thumb = toastEl.querySelector('.social-proof-toast__thumb img');
		if (thumb && imgBase) {
			thumb.src = imgBase + product.image;
			thumb.alt = product.name;
		}

		toastEl.querySelector('.social-proof-toast__action').textContent =
			name + ' from ' + city + ' ' + action;
		toastEl.querySelector('.social-proof-toast__product').textContent =
			product.name + ' — ' + product.price;
		toastEl.querySelector('.social-proof-toast__meta').textContent = time;

		toastEl.classList.add('visible');

		if (hideTimer) clearTimeout(hideTimer);
		hideTimer = setTimeout(hideToast, CONFIG.toastDuration);
	}

	function hideToast() {
		if (toastEl) toastEl.classList.remove('visible');
	}

	function initToasts() {
		toastEl = createToast();

		// First toast after 8 seconds
		setTimeout(function () {
			showToast();
			toastTimer = setInterval(showToast, CONFIG.toastInterval);
		}, 8000);
	}

	/* --------------------------------------------------
	   Sticky Pre-Order CTA Bar
	   -------------------------------------------------- */

	var stickyBar    = null;
	var viewerCount  = null;

	function createStickyBar() {
		var el = document.createElement('div');
		el.className = 'sticky-cta-bar';
		el.innerHTML =
			'<div class="sticky-cta-bar__urgency">' +
				'<span class="sticky-cta-bar__dot"></span>' +
				'<span><span class="sticky-cta-bar__count" data-viewer-count></span> people viewing now</span>' +
			'</div>' +
			'<span class="sticky-cta-bar__sep"></span>' +
			'<a href="/pre-order/" class="sticky-cta-bar__cta">' +
				'Secure Your Pre-Order' +
				'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>' +
			'</a>' +
			'<button class="sticky-cta-bar__dismiss" type="button" aria-label="Dismiss bar">&times;</button>';

		el.querySelector('.sticky-cta-bar__dismiss').addEventListener('click', function () {
			el.classList.remove('visible');
			sessionStorage.setItem('sr_sticky_dismissed', '1');
		});

		document.body.appendChild(el);
		return el;
	}

	function updateViewerCount() {
		if (!viewerCount) return;
		var count = randInt(CONFIG.minViewers, CONFIG.maxViewers);
		viewerCount.textContent = count;
	}

	function initStickyBar() {
		if (sessionStorage.getItem('sr_sticky_dismissed')) return;

		stickyBar = createStickyBar();
		viewerCount = stickyBar.querySelector('[data-viewer-count]');

		updateViewerCount();

		// Show after scroll or delay
		var shown = false;
		function reveal() {
			if (shown) return;
			shown = true;
			stickyBar.classList.add('visible');
		}

		setTimeout(reveal, CONFIG.stickyDelay);

		window.addEventListener('scroll', function () {
			if (window.scrollY > 400) reveal();
		}, { passive: true });

		// Refresh viewer count periodically
		setInterval(updateViewerCount, CONFIG.viewerRefresh);
	}

	/* --------------------------------------------------
	   Init
	   -------------------------------------------------- */

	function init() {
		// Don't show on admin pages
		if (document.body.classList.contains('wp-admin')) return;

		initToasts();
		initStickyBar();
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}
})();
