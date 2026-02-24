/**
 * The Pulse — Real-Time Social Proof & Urgency Engine
 *
 * Conversion-driving social proof system: purchase toast notifications,
 * urgency bar with scarcity/viewer counts, scarcity badges on product
 * cards, VIP banner, confidence signals, and immersive hotspot
 * enhancements. All data is simulated client-side for pre-launch.
 *
 * No dependencies — vanilla JS. Production-quality.
 *
 * @package SkyyRose_Flagship
 * @since   3.3.0
 */

(function () {
	'use strict';

	/* ==========================================================================
	   Configuration
	   ========================================================================== */

	var CONFIG = {
		/* Toast timing (ms) */
		toastMinInterval:    15000,
		toastMaxInterval:    30000,
		toastDuration:        5000,
		toastFirstDelay:      6000,

		/* Urgency bar */
		urgencyBarDelay:      3000,
		urgencyBarScrollThreshold: 300,

		/* Viewer count */
		viewerCountMin:        15,
		viewerCountMax:        80,
		viewerFluctuation:      5,
		viewerUpdateInterval: 8000,

		/* VIP banner */
		vipBannerDelay:       2000,

		/* Scarcity */
		scarcityHideThreshold: 10,

		/* Immersive hotspot enhancement */
		hotspotPopularityMin:   1,
		hotspotPopularityMax:   3
	};


	/* ==========================================================================
	   Simulation Data — Products, Names, Cities
	   ========================================================================== */

	var PRODUCTS = [
		/* --- Black Rose Collection --- */
		{ name: 'BLACK Rose Sherpa Jacket',      price: '$295', collection: 'Black Rose',  slug: 'br-sherpa-jacket' },
		{ name: 'BLACK Rose Quarter Zip Fleece',  price: '$175', collection: 'Black Rose',  slug: 'br-quarter-zip' },
		{ name: 'BLACK Rose Beanie',              price: '$45',  collection: 'Black Rose',  slug: 'br-beanie' },
		{ name: 'BLACK Rose Crewneck',            price: '$125', collection: 'Black Rose',  slug: 'br-crewneck' },
		{ name: 'BLACK Rose Cargo Pants',         price: '$145', collection: 'Black Rose',  slug: 'br-cargo-pants' },
		{ name: 'BLACK Rose Tee',                 price: '$65',  collection: 'Black Rose',  slug: 'br-tee' },
		{ name: 'BLACK Rose Hoodie',              price: '$165', collection: 'Black Rose',  slug: 'br-hoodie' },

		/* --- Love Hurts Collection --- */
		{ name: 'Love Hurts Varsity Jacket',      price: '$265', collection: 'Love Hurts',  slug: 'lh-varsity' },
		{ name: 'Love Hurts Joggers',             price: '$95',  collection: 'Love Hurts',  slug: 'lh-joggers' },
		{ name: 'Love Hurts Basketball Shorts',   price: '$75',  collection: 'Love Hurts',  slug: 'lh-shorts' },
		{ name: 'Love Hurts Hoodie',              price: '$155', collection: 'Love Hurts',  slug: 'lh-hoodie' },
		{ name: 'Love Hurts Crewneck',            price: '$115', collection: 'Love Hurts',  slug: 'lh-crewneck' },
		{ name: 'Love Hurts Tee',                 price: '$60',  collection: 'Love Hurts',  slug: 'lh-tee' },

		/* --- Signature Collection --- */
		{ name: 'Signature Rose Gold Hoodie',     price: '$185', collection: 'Signature',   slug: 'sig-hoodie' },
		{ name: 'Signature Rose Gold Joggers',    price: '$125', collection: 'Signature',   slug: 'sig-joggers' },
		{ name: 'Signature Premium Tee',          price: '$85',  collection: 'Signature',   slug: 'sig-tee' },
		{ name: 'Signature Crewneck',             price: '$135', collection: 'Signature',   slug: 'sig-crewneck' },
		{ name: 'Signature Quarter Zip',          price: '$155', collection: 'Signature',   slug: 'sig-quarter-zip' },
		{ name: 'Signature Track Pants',          price: '$110', collection: 'Signature',   slug: 'sig-track-pants' }
	];

	var FIRST_NAMES = [
		'Sarah', 'Marcus', 'Aaliyah', 'Devon', 'Kenji',
		'Jasmine', 'Tyler', 'Nia', 'Carlos', 'Imani',
		'Jordan', 'Ayanna', 'Darius', 'Zara', 'Andre',
		'Raven', 'Xavier', 'Amara', 'Trey', 'Maya',
		'Sienna', 'Malik', 'Luna', 'Isaiah', 'Aria',
		'Cameron', 'Bianca', 'Kai', 'Priya', 'Elijah',
		'Destiny', 'Sebastian', 'Nadia', 'Jaylen'
	];

	var CITIES = [
		'Los Angeles, CA', 'New York, NY', 'Atlanta, GA', 'Houston, TX',
		'Miami, FL', 'Chicago, IL', 'San Francisco, CA', 'Brooklyn, NY',
		'Dallas, TX', 'Seattle, WA', 'Nashville, TN', 'Detroit, MI',
		'Denver, CO', 'Oakland, CA', 'Portland, OR', 'Phoenix, AZ',
		'Scottsdale, AZ', 'Beverly Hills, CA', 'SoHo, NY', 'Buckhead, GA',
		'Calabasas, CA', 'Bel Air, CA'
	];

	var ACTIONS = [
		'just pre-ordered',
		'just secured',
		'just added to cart',
		'just grabbed'
	];

	var TIME_LABELS = [
		'just now', '1 min ago', '2 min ago', '3 min ago',
		'5 min ago', '8 min ago', '12 min ago'
	];


	/* ==========================================================================
	   Utility Functions
	   ========================================================================== */

	function rand(arr) {
		return arr[Math.floor(Math.random() * arr.length)];
	}

	function randInt(min, max) {
		return Math.floor(Math.random() * (max - min + 1)) + min;
	}

	/**
	 * Simple deterministic hash from a string.
	 * Returns an integer suitable for seeding consistent random values.
	 */
	function hashString(str) {
		var hash = 5381;
		for (var i = 0; i < str.length; i++) {
			hash = ((hash << 5) + hash + str.charCodeAt(i)) & 0x7FFFFFFF;
		}
		return hash;
	}

	/**
	 * Seeded pseudo-random: returns a number 0-1 based on seed.
	 */
	function seededRandom(seed) {
		var x = Math.sin(seed) * 10000;
		return x - Math.floor(x);
	}

	/**
	 * Seeded integer in range [min, max].
	 */
	function seededInt(seed, min, max) {
		return Math.floor(seededRandom(seed) * (max - min + 1)) + min;
	}

	/**
	 * Sanitize text content — prevent XSS in any dynamic strings.
	 */
	function escapeHtml(str) {
		var div = document.createElement('div');
		div.appendChild(document.createTextNode(str));
		return div.innerHTML;
	}

	/**
	 * Detect page type from body classes and URL.
	 */
	function detectPageType() {
		var body = document.body;
		var path = window.location.pathname.toLowerCase();

		if (body.classList.contains('immersive-page') || path.indexOf('/immersive') !== -1) {
			return 'immersive';
		}
		if (body.classList.contains('preorder-gateway-page') || path.indexOf('/pre-order') !== -1) {
			return 'preorder';
		}
		if (path.indexOf('/collection') !== -1 || body.className.indexOf('collection') !== -1) {
			return 'collection';
		}
		if (path === '/' || path === '' || body.classList.contains('home')) {
			return 'homepage';
		}
		if (path.indexOf('/product') !== -1) {
			return 'product';
		}
		return 'other';
	}


	/* ==========================================================================
	   SVG Icon Helpers
	   ========================================================================== */

	var ICONS = {
		eye: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>',

		flame: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8.5 14.5A2.5 2.5 0 0011 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 11-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 002.5 2.5z"/></svg>',

		shield: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/></svg>',

		refresh: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"/><polyline points="23 20 23 14 17 14"/><path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15"/></svg>',

		lock: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>',

		gem: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="6 3 18 3 22 9 12 22 2 9 6 3"/><path d="M2 9h20"/><path d="M12 22L6 9"/><path d="M12 22l6-13"/></svg>',

		star: '<svg viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',

		starEmpty: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',

		heart: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"/></svg>',

		cart: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 002 1.61h9.72a2 2 0 002-1.61L23 6H6"/></svg>',

		arrow: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>',

		crown: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 20h20"/><path d="M3.09 13.91L2 7l5 4 5-7 5 7 5-4-1.09 6.91A2 2 0 0118.93 16H5.07a2 2 0 01-1.98-2.09z"/></svg>'
	};


	/* ==========================================================================
	   PulseEngine Class
	   ========================================================================== */

	function PulseEngine() {
		this.pageType = null;
		this.toastEl = null;
		this.toastTimer = null;
		this.toastHideTimer = null;
		this.toastDismissed = false;
		this.urgencyBar = null;
		this.vipBanner = null;
		this.viewerIntervals = [];
		this.cleanupFns = [];
		this.sessionSeed = Date.now();
		this.lastToastProductIndex = -1;
	}


	/* --------------------------------------------------------------------------
	   init()
	   -------------------------------------------------------------------------- */

	PulseEngine.prototype.init = function () {
		/* Skip on admin pages */
		if (document.body.classList.contains('wp-admin')) return;

		this.pageType = detectPageType();

		/* All pages: toasts + VIP banner */
		this.startSocialProofLoop();
		this.initVIPBanner();

		/* Product-relevant pages: urgency, scarcity, confidence */
		if (this.pageType === 'preorder' || this.pageType === 'collection' || this.pageType === 'product') {
			this.initUrgencyBar();
			this.initScarcityBadges();
			this.initConfidenceSignals();
		}

		/* Homepage: urgency bar + confidence signals */
		if (this.pageType === 'homepage') {
			this.initUrgencyBar();
			this.initConfidenceSignals();
		}

		/* Immersive pages: hotspot + panel enhancements */
		if (this.pageType === 'immersive') {
			this.enhanceImmersiveHotspots();
			this.enhanceProductPanels();
		}

		/* Viewer counts on all product-related pages */
		if (this.pageType !== 'other') {
			this.initViewerCount();
		}

		/* Cleanup on page unload */
		var self = this;
		window.addEventListener('beforeunload', function () {
			self.destroy();
		});
	};


	/* --------------------------------------------------------------------------
	   destroy() — Cleanup all intervals and timers
	   -------------------------------------------------------------------------- */

	PulseEngine.prototype.destroy = function () {
		if (this.toastTimer) clearTimeout(this.toastTimer);
		if (this.toastHideTimer) clearTimeout(this.toastHideTimer);
		this.viewerIntervals.forEach(function (id) { clearInterval(id); });
		this.cleanupFns.forEach(function (fn) { fn(); });
	};


	/* --------------------------------------------------------------------------
	   startSocialProofLoop() — Show purchase toasts on a random interval
	   -------------------------------------------------------------------------- */

	PulseEngine.prototype.startSocialProofLoop = function () {
		var self = this;
		this.toastEl = this._createToastElement();
		document.body.appendChild(this.toastEl);

		/* First toast after initial delay */
		this.toastTimer = setTimeout(function () {
			self._showNextToast();
		}, CONFIG.toastFirstDelay);
	};

	PulseEngine.prototype._createToastElement = function () {
		var el = document.createElement('div');
		el.className = 'pulse-toast';
		el.setAttribute('role', 'status');
		el.setAttribute('aria-live', 'polite');

		el.innerHTML =
			'<div class="pulse-toast__avatar"></div>' +
			'<div class="pulse-toast__body">' +
				'<div class="pulse-toast__action"></div>' +
				'<div class="pulse-toast__product"></div>' +
				'<div class="pulse-toast__meta">' +
					'<span class="pulse-toast__meta-dot"></span>' +
					'<span class="pulse-toast__meta-time"></span>' +
				'</div>' +
			'</div>' +
			'<div class="pulse-toast__thumb"><img src="" alt="" loading="lazy"></div>' +
			'<button class="pulse-toast__close" type="button" aria-label="Dismiss">&times;</button>' +
			'<div class="pulse-toast__timer"><div class="pulse-toast__timer-bar"></div></div>';

		var self = this;
		el.querySelector('.pulse-toast__close').addEventListener('click', function () {
			self._hideToast();
			self.toastDismissed = true;
			if (self.toastTimer) clearTimeout(self.toastTimer);
		});

		return el;
	};

	PulseEngine.prototype._showNextToast = function () {
		if (this.toastDismissed) return;

		/* Pick a product that differs from the last shown */
		var productIndex;
		var attempts = 0;
		do {
			productIndex = randInt(0, PRODUCTS.length - 1);
			attempts++;
		} while (productIndex === this.lastToastProductIndex && attempts < 5);
		this.lastToastProductIndex = productIndex;

		var product = PRODUCTS[productIndex];
		var buyerName = rand(FIRST_NAMES);
		var city = rand(CITIES);

		this.showPurchaseToast(buyerName, city, product.name, product.collection);

		/* Schedule next toast with randomized interval */
		var self = this;
		var nextDelay = randInt(CONFIG.toastMinInterval, CONFIG.toastMaxInterval);
		this.toastTimer = setTimeout(function () {
			self._showNextToast();
		}, nextDelay);
	};


	/* --------------------------------------------------------------------------
	   showPurchaseToast() — Render and animate a single toast
	   -------------------------------------------------------------------------- */

	PulseEngine.prototype.showPurchaseToast = function (buyerName, city, productName, collection) {
		if (this.toastDismissed || !this.toastEl) return;

		var action = rand(ACTIONS);
		var timeLabel = rand(TIME_LABELS);

		/* Avatar: first letter of buyer name */
		var avatarEl = this.toastEl.querySelector('.pulse-toast__avatar');
		if (avatarEl) {
			avatarEl.textContent = buyerName.charAt(0).toUpperCase();
		}

		/* Action text */
		var actionEl = this.toastEl.querySelector('.pulse-toast__action');
		if (actionEl) {
			actionEl.textContent = escapeHtml(buyerName) + ' from ' + escapeHtml(city) + ' ' + action;
		}

		/* Product name */
		var productEl = this.toastEl.querySelector('.pulse-toast__product');
		if (productEl) {
			productEl.textContent = escapeHtml(productName);
		}

		/* Time label */
		var timeEl = this.toastEl.querySelector('.pulse-toast__meta-time');
		if (timeEl) {
			timeEl.textContent = timeLabel;
		}

		/* Thumbnail — try to use theme assets if available */
		var thumbImg = this.toastEl.querySelector('.pulse-toast__thumb img');
		if (thumbImg) {
			var imgBase = '';
			if (typeof skyyRoseData !== 'undefined' && skyyRoseData.assetsUri) {
				imgBase = skyyRoseData.assetsUri + '/images/products/';
			}
			/* Use collection-based placeholder logic */
			var collSlug = collection.toLowerCase().replace(/\s+/g, '-');
			thumbImg.src = imgBase ? imgBase + collSlug + '-thumb.jpg' : '';
			thumbImg.alt = productName;
		}

		/* Reset timer bar animation */
		var timerBar = this.toastEl.querySelector('.pulse-toast__timer-bar');
		if (timerBar) {
			timerBar.style.animation = 'none';
			/* Force reflow */
			void timerBar.offsetWidth;
			timerBar.style.animation = '';
		}

		/* Show the toast */
		this.toastEl.classList.remove('pulse-toast--exiting');
		this.toastEl.classList.add('pulse-toast--visible');

		/* Schedule auto-hide */
		var self = this;
		if (this.toastHideTimer) clearTimeout(this.toastHideTimer);
		this.toastHideTimer = setTimeout(function () {
			self._hideToast();
		}, CONFIG.toastDuration);
	};

	PulseEngine.prototype._hideToast = function () {
		if (!this.toastEl) return;
		this.toastEl.classList.add('pulse-toast--exiting');
		var el = this.toastEl;
		setTimeout(function () {
			el.classList.remove('pulse-toast--visible');
			el.classList.remove('pulse-toast--exiting');
		}, 450);
	};


	/* --------------------------------------------------------------------------
	   initUrgencyBar() — Sticky bottom bar with scarcity + viewers + CTA
	   -------------------------------------------------------------------------- */

	PulseEngine.prototype.initUrgencyBar = function () {
		/* Check if already dismissed this session */
		if (sessionStorage.getItem('sr_pulse_urgency_dismissed')) return;

		var self = this;
		this.urgencyBar = this._createUrgencyBarElement();
		document.body.appendChild(this.urgencyBar);

		var viewerCountEl = this.urgencyBar.querySelector('[data-pulse-viewer-count]');
		var scarcityCountEl = this.urgencyBar.querySelector('[data-pulse-scarcity-count]');

		/* Set initial viewer count */
		var baseViewers = randInt(CONFIG.viewerCountMin, CONFIG.viewerCountMax);
		if (viewerCountEl) viewerCountEl.textContent = baseViewers;

		/* Set scarcity based on page context */
		var scarcityNum = randInt(2, 7);
		if (scarcityCountEl) scarcityCountEl.textContent = scarcityNum;

		/* Fluctuate viewer count over time */
		var viewerInterval = setInterval(function () {
			if (!viewerCountEl) return;
			var current = parseInt(viewerCountEl.textContent, 10) || baseViewers;
			var delta = randInt(-CONFIG.viewerFluctuation, CONFIG.viewerFluctuation);
			var next = Math.max(CONFIG.viewerCountMin, Math.min(CONFIG.viewerCountMax, current + delta));
			viewerCountEl.textContent = next;
		}, CONFIG.viewerUpdateInterval);
		this.viewerIntervals.push(viewerInterval);

		/* Reveal after delay or scroll */
		var revealed = false;
		function reveal() {
			if (revealed) return;
			revealed = true;
			self.urgencyBar.classList.add('pulse-urgency-bar--visible');
		}

		setTimeout(reveal, CONFIG.urgencyBarDelay);

		var scrollHandler = function () {
			if (window.scrollY > CONFIG.urgencyBarScrollThreshold) reveal();
		};
		window.addEventListener('scroll', scrollHandler, { passive: true });
		this.cleanupFns.push(function () {
			window.removeEventListener('scroll', scrollHandler);
		});
	};

	PulseEngine.prototype._createUrgencyBarElement = function () {
		var el = document.createElement('div');
		el.className = 'pulse-urgency-bar';

		el.innerHTML =
			'<div class="pulse-urgency-bar__scarcity">' +
				'<span class="pulse-urgency-bar__scarcity-icon">' + ICONS.flame + '</span>' +
				'<span>Only <strong class="pulse-urgency-bar__scarcity-count" data-pulse-scarcity-count></strong> left in your size</span>' +
			'</div>' +
			'<span class="pulse-urgency-bar__sep"></span>' +
			'<div class="pulse-urgency-bar__viewers">' +
				'<span class="pulse-urgency-bar__live-dot"></span>' +
				'<span><span class="pulse-urgency-bar__viewer-count" data-pulse-viewer-count></span> people viewing</span>' +
			'</div>' +
			'<span class="pulse-urgency-bar__sep"></span>' +
			'<a href="/pre-order/" class="pulse-urgency-bar__cta">' +
				'Secure Yours Now ' + ICONS.arrow +
			'</a>' +
			'<button class="pulse-urgency-bar__dismiss" type="button" aria-label="Dismiss">&times;</button>';

		el.querySelector('.pulse-urgency-bar__dismiss').addEventListener('click', function () {
			el.classList.remove('pulse-urgency-bar--visible');
			sessionStorage.setItem('sr_pulse_urgency_dismissed', '1');
		});

		return el;
	};


	/* --------------------------------------------------------------------------
	   initScarcityBadges() — Add "Limited: X left" badges to product cards
	   -------------------------------------------------------------------------- */

	PulseEngine.prototype.initScarcityBadges = function () {
		var productCards = document.querySelectorAll('.product-grid-card');
		if (!productCards.length) return;

		var self = this;

		/* Use Intersection Observer for viewport-based triggering */
		var observer = null;
		if ('IntersectionObserver' in window) {
			observer = new IntersectionObserver(function (entries) {
				entries.forEach(function (entry) {
					if (entry.isIntersecting) {
						self._addScarcityBadge(entry.target);
						observer.unobserve(entry.target);
					}
				});
			}, { rootMargin: '100px' });
		}

		for (var i = 0; i < productCards.length; i++) {
			if (observer) {
				observer.observe(productCards[i]);
			} else {
				/* Fallback: add immediately */
				this._addScarcityBadge(productCards[i]);
			}
		}
	};

	PulseEngine.prototype._addScarcityBadge = function (card) {
		/* Get product name for consistent seeding */
		var productName = card.dataset.productName || card.querySelector('.product-grid-name')?.textContent || '';
		if (!productName) return;

		/* Already has a badge? */
		if (card.querySelector('.pulse-scarcity-badge')) return;

		/* Seed-based stock level: consistent per product name per session */
		var seed = hashString(productName + this.sessionSeed);
		var stock = seededInt(seed, 1, 15);

		/* Determine severity */
		var modifier, label;
		if (stock > CONFIG.scarcityHideThreshold) {
			/* Don't show badge for well-stocked items */
			return;
		} else if (stock <= 2) {
			modifier = 'pulse-scarcity-badge--critical';
			label = 'Only ' + stock + ' left';
		} else if (stock <= 5) {
			modifier = 'pulse-scarcity-badge--low';
			label = 'Limited: ' + stock + ' left';
		} else {
			modifier = 'pulse-scarcity-badge--moderate';
			label = stock + ' remaining';
		}

		/* Create badge */
		var badge = document.createElement('div');
		badge.className = 'pulse-scarcity-badge ' + modifier;
		badge.setAttribute('aria-label', label);
		badge.innerHTML = '<span class="pulse-scarcity-badge__dot"></span>' + escapeHtml(label);

		/* Insert into the product image container */
		var imageContainer = card.querySelector('.product-grid-image');
		if (imageContainer) {
			imageContainer.style.position = 'relative';
			imageContainer.appendChild(badge);
		}
	};


	/* --------------------------------------------------------------------------
	   initViewerCount() — "X viewing now" indicators near products
	   -------------------------------------------------------------------------- */

	PulseEngine.prototype.initViewerCount = function () {
		var self = this;

		/* For product cards, add viewer count to each visible card */
		var productCards = document.querySelectorAll('.product-grid-card');
		if (productCards.length > 0) {
			this._addViewerCountsToCards(productCards);
			return;
		}

		/* For immersive/single product pages, add near the main product image */
		var mainImage = document.querySelector('.product-panel-thumb, .modal-360-area');
		if (mainImage) {
			this._addSingleViewerCount(mainImage);
		}
	};

	PulseEngine.prototype._addViewerCountsToCards = function (cards) {
		var self = this;
		/* Only show viewer count on a subset of cards to avoid clutter */
		var maxViewerBadges = Math.min(cards.length, 6);

		for (var i = 0; i < maxViewerBadges; i++) {
			var card = cards[i];
			var imageContainer = card.querySelector('.product-grid-image');
			if (!imageContainer) continue;

			/* Already has viewer count? */
			if (imageContainer.querySelector('.pulse-viewer-count')) continue;

			var productName = card.dataset.productName || '';
			var seed = hashString(productName + 'viewers');
			var viewerNum = seededInt(seed, CONFIG.viewerCountMin, CONFIG.viewerCountMax);

			var el = document.createElement('div');
			el.className = 'pulse-viewer-count pulse-viewer-count--positioned';
			el.innerHTML =
				'<span class="pulse-viewer-count__eye">' + ICONS.eye + '</span>' +
				'<span><span class="pulse-viewer-count__number">' + viewerNum + '</span> viewing</span>';

			imageContainer.style.position = 'relative';
			imageContainer.appendChild(el);

			/* Fluctuate this count */
			(function (element, baseNum) {
				var interval = setInterval(function () {
					var numEl = element.querySelector('.pulse-viewer-count__number');
					if (!numEl) return;
					var current = parseInt(numEl.textContent, 10) || baseNum;
					var delta = randInt(-3, 3);
					var next = Math.max(CONFIG.viewerCountMin, Math.min(CONFIG.viewerCountMax, current + delta));
					numEl.textContent = next;
				}, CONFIG.viewerUpdateInterval + randInt(-2000, 2000));
				self.viewerIntervals.push(interval);
			})(el, viewerNum);
		}
	};

	PulseEngine.prototype._addSingleViewerCount = function (container) {
		var viewerNum = randInt(CONFIG.viewerCountMin, CONFIG.viewerCountMax);

		var el = document.createElement('div');
		el.className = 'pulse-viewer-count pulse-viewer-count--positioned';
		el.innerHTML =
			'<span class="pulse-viewer-count__eye">' + ICONS.eye + '</span>' +
			'<span><span class="pulse-viewer-count__number">' + viewerNum + '</span> viewing now</span>';

		container.style.position = 'relative';
		container.appendChild(el);

		/* Fluctuate */
		var self = this;
		var interval = setInterval(function () {
			var numEl = el.querySelector('.pulse-viewer-count__number');
			if (!numEl) return;
			var current = parseInt(numEl.textContent, 10) || viewerNum;
			var delta = randInt(-CONFIG.viewerFluctuation, CONFIG.viewerFluctuation);
			numEl.textContent = Math.max(CONFIG.viewerCountMin, Math.min(CONFIG.viewerCountMax, current + delta));
		}, CONFIG.viewerUpdateInterval);
		this.viewerIntervals.push(interval);
	};


	/* --------------------------------------------------------------------------
	   initVIPBanner() — Full-width VIP early access banner (first visit only)
	   -------------------------------------------------------------------------- */

	PulseEngine.prototype.initVIPBanner = function () {
		if (sessionStorage.getItem('sr_pulse_vip_dismissed')) return;

		var self = this;
		this.vipBanner = this._createVIPBannerElement();
		document.body.appendChild(this.vipBanner);

		/* Show after delay */
		setTimeout(function () {
			self.vipBanner.classList.add('pulse-vip-banner--visible');
		}, CONFIG.vipBannerDelay);
	};

	PulseEngine.prototype._createVIPBannerElement = function () {
		var el = document.createElement('div');
		el.className = 'pulse-vip-banner';
		el.setAttribute('role', 'banner');

		el.innerHTML =
			'<span class="pulse-vip-banner__icon">' + ICONS.crown + '</span>' +
			'<span class="pulse-vip-banner__text">' +
				'<strong>VIP Early Access</strong> &mdash; Members save 25% on all pre-orders' +
			'</span>' +
			'<a href="/login/" class="pulse-vip-banner__cta">Join Now</a>' +
			'<button class="pulse-vip-banner__dismiss" type="button" aria-label="Dismiss">&times;</button>';

		var self = this;
		el.querySelector('.pulse-vip-banner__dismiss').addEventListener('click', function () {
			el.classList.remove('pulse-vip-banner--visible');
			sessionStorage.setItem('sr_pulse_vip_dismissed', '1');
			/* Animate out */
			setTimeout(function () {
				if (el.parentNode) el.parentNode.removeChild(el);
			}, 600);
		});

		return el;
	};


	/* --------------------------------------------------------------------------
	   initConfidenceSignals() — Trust badges after product grids
	   -------------------------------------------------------------------------- */

	PulseEngine.prototype.initConfidenceSignals = function () {
		/* Find the insertion point — after the product grid or before footer */
		var productSection = document.querySelector('.gateway-product-section, .product-grid, .woocommerce-products');
		var insertTarget = productSection || document.querySelector('main, .site-main, #main');
		if (!insertTarget) return;

		/* Already inserted? */
		if (document.querySelector('.pulse-confidence-signals')) return;

		var signals = [
			{ icon: ICONS.refresh, label: 'Free Returns' },
			{ icon: ICONS.lock,    label: 'Secure Checkout' },
			{ icon: ICONS.gem,     label: 'Authentic Luxury' },
			{ icon: ICONS.shield,  label: '100% Guarantee' }
		];

		var container = document.createElement('div');
		container.className = 'pulse-confidence-signals';
		container.setAttribute('role', 'list');
		container.setAttribute('aria-label', 'Trust signals');

		signals.forEach(function (signal) {
			var item = document.createElement('div');
			item.className = 'pulse-confidence-signal';
			item.setAttribute('role', 'listitem');
			item.innerHTML =
				'<div class="pulse-confidence-signal__icon">' + signal.icon + '</div>' +
				'<span class="pulse-confidence-signal__label">' + escapeHtml(signal.label) + '</span>';
			container.appendChild(item);
		});

		/* Insert after the product section */
		if (productSection && productSection.nextSibling) {
			productSection.parentNode.insertBefore(container, productSection.nextSibling);
		} else if (insertTarget) {
			insertTarget.appendChild(container);
		}
	};


	/* --------------------------------------------------------------------------
	   enhanceImmersiveHotspots() — Add popularity indicators to hotspot beacons
	   -------------------------------------------------------------------------- */

	PulseEngine.prototype.enhanceImmersiveHotspots = function () {
		var hotspots = document.querySelectorAll('.hotspot');
		if (!hotspots.length) return;

		for (var i = 0; i < hotspots.length; i++) {
			var hotspot = hotspots[i];
			var productName = hotspot.dataset.productName || 'product-' + i;
			var seed = hashString(productName + 'popularity');
			var intensity = seededInt(seed, CONFIG.hotspotPopularityMin, CONFIG.hotspotPopularityMax);

			/* Add the pulse-hotspot-heat wrapper class */
			hotspot.classList.add('pulse-hotspot-heat');
			hotspot.style.setProperty('--pulse-intensity', intensity);

			/* Add popularity label for high-intensity hotspots */
			if (intensity >= 2) {
				var label = document.createElement('span');
				label.className = 'pulse-hotspot-heat__label';
				if (intensity === 3) {
					label.textContent = 'Trending';
				} else {
					label.textContent = 'Popular';
				}
				hotspot.appendChild(label);
			}
		}
	};


	/* --------------------------------------------------------------------------
	   enhanceProductPanels() — Add social proof data to immersive product panels
	   -------------------------------------------------------------------------- */

	PulseEngine.prototype.enhanceProductPanels = function () {
		var panel = document.querySelector('.product-panel');
		if (!panel) return;

		var self = this;

		/* We need to add social proof when the panel opens.
		   Listen for the panel open class change. */
		var observer = new MutationObserver(function (mutations) {
			mutations.forEach(function (mutation) {
				if (mutation.attributeName !== 'class') return;
				var target = mutation.target;
				if (target.classList.contains('open')) {
					self._injectPanelSocialProof(target);
				}
			});
		});

		observer.observe(panel, { attributes: true });
		this.cleanupFns.push(function () { observer.disconnect(); });
	};

	PulseEngine.prototype._injectPanelSocialProof = function (panel) {
		/* Remove existing social proof section to prevent duplicates */
		var existing = panel.querySelector('.pulse-product-panel-social');
		if (existing) existing.parentNode.removeChild(existing);

		var infoSection = panel.querySelector('.product-panel-info');
		if (!infoSection) return;

		/* Get product name from the panel to seed consistent data */
		var nameEl = panel.querySelector('.product-panel-name');
		var productName = nameEl ? nameEl.textContent : 'product';
		var seed = hashString(productName);

		var interested = seededInt(seed, 18, 92);
		var addedToday = seededInt(seed + 1, 3, 24);
		var rating = seededInt(seed + 2, 40, 50) / 10; /* 4.0 - 5.0 */
		var fullStars = Math.floor(rating);

		/* Build star HTML */
		var starsHtml = '';
		for (var s = 0; s < 5; s++) {
			if (s < fullStars) {
				starsHtml += '<span class="pulse-product-panel-social__star">' + ICONS.star + '</span>';
			} else {
				starsHtml += '<span class="pulse-product-panel-social__star pulse-product-panel-social__star--empty">' + ICONS.starEmpty + '</span>';
			}
		}

		var el = document.createElement('div');
		el.className = 'pulse-product-panel-social';
		el.innerHTML =
			'<div class="pulse-product-panel-social__stat">' +
				'<span class="pulse-product-panel-social__stat-icon">' + ICONS.heart + '</span>' +
				'<span><span class="pulse-product-panel-social__stat-value">' + interested + '</span> interested</span>' +
			'</div>' +
			'<span class="pulse-product-panel-social__sep"></span>' +
			'<div class="pulse-product-panel-social__stat">' +
				'<span class="pulse-product-panel-social__stat-icon">' + ICONS.cart + '</span>' +
				'<span><span class="pulse-product-panel-social__stat-value">' + addedToday + '</span> added today</span>' +
			'</div>' +
			'<span class="pulse-product-panel-social__sep"></span>' +
			'<div class="pulse-product-panel-social__stars">' +
				starsHtml +
				'<span class="pulse-product-panel-social__rating">' + rating.toFixed(1) + '</span>' +
			'</div>';

		infoSection.appendChild(el);
	};


	/* ==========================================================================
	   Initialization — DOMContentLoaded
	   ========================================================================== */

	var engine = new PulseEngine();

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', function () {
			engine.init();
		});
	} else {
		engine.init();
	}

})();
