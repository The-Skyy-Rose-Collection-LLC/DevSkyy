/**
 * The Pulse — Real-Time Social Proof & Urgency Engine
 *
 * Drives conversion through social proof toasts, live viewer counts,
 * scarcity indicators, VIP countdown, popularity heat, and interest
 * counters. All data is simulated client-side for pre-launch.
 *
 * @package SkyyRose_Flagship
 * @since   3.3.0
 */

(function () {
	'use strict';

	/* --------------------------------------------------
	   Configuration
	   -------------------------------------------------- */

	var CONFIG = {
		toastMinDelay:       15000,
		toastMaxDelay:       30000,
		toastDuration:        5000,
		toastMaxVisible:         2,
		viewerUpdateMin:      8000,
		viewerUpdateMax:     12000,
		viewerMin:              12,
		viewerMax:              89,
		viewerFluctuation:       3,
		countdownTarget: '2026-04-01T00:00:00',
		countdownShowDelay:   3000,
		interestBase:           24,
		interestMax:            89,
		interestIncrementMs: 12000,
		scarcityMin:             1,
		scarcityMax:             7,
	};

	/* --------------------------------------------------
	   Product Catalog — All 3 Collections
	   -------------------------------------------------- */

	var PRODUCTS = [
		/* Black Rose Collection */
		{ sku: 'BR-001', name: 'BLACK Rose Hoodie',            price: '$185', collection: 'Black Rose' },
		{ sku: 'BR-002', name: 'BLACK Rose Tee',               price: '$85',  collection: 'Black Rose' },
		{ sku: 'BR-003', name: 'BLACK Rose Joggers',           price: '$125', collection: 'Black Rose' },
		{ sku: 'BR-004', name: 'BLACK Rose Shorts',            price: '$75',  collection: 'Black Rose' },
		{ sku: 'BR-005', name: 'BLACK Rose Quarter Zip Fleece', price: '$175', collection: 'Black Rose' },
		{ sku: 'BR-006', name: 'BLACK Rose Sherpa Jacket',     price: '$295', collection: 'Black Rose' },
		{ sku: 'BR-007', name: 'BLACK Rose Beanie',            price: '$45',  collection: 'Black Rose' },
		/* Love Hurts Collection */
		{ sku: 'LH-001', name: 'Love Hurts Hoodie',           price: '$185', collection: 'Love Hurts' },
		{ sku: 'LH-002', name: 'Love Hurts Joggers',          price: '$95',  collection: 'Love Hurts' },
		{ sku: 'LH-003', name: 'Love Hurts Basketball Shorts', price: '$75',  collection: 'Love Hurts' },
		{ sku: 'LH-004', name: 'Love Hurts Varsity Jacket',   price: '$265', collection: 'Love Hurts' },
		{ sku: 'LH-005', name: 'Love Hurts Tee',              price: '$85',  collection: 'Love Hurts' },
		/* Signature Collection */
		{ sku: 'SIG-001', name: 'Signature Rose Gold Hoodie',  price: '$185', collection: 'Signature' },
		{ sku: 'SIG-002', name: 'Signature Premium Tee',       price: '$85',  collection: 'Signature' },
		{ sku: 'SIG-003', name: 'Signature Rose Gold Joggers', price: '$125', collection: 'Signature' },
		{ sku: 'SIG-004', name: 'Signature Crewneck',          price: '$145', collection: 'Signature' },
		{ sku: 'SIG-005', name: 'Signature Cap',               price: '$45',  collection: 'Signature' },
	];

	var FIRST_NAMES = [
		'Sarah', 'Marcus', 'Aaliyah', 'Devon', 'Kenji',
		'Jasmine', 'Tyler', 'Nia', 'Carlos', 'Imani',
		'Jordan', 'Ayanna', 'Darius', 'Zara', 'Andre',
		'Raven', 'Xavier', 'Amara', 'Trey', 'Maya',
		'Brianna', 'Malik', 'Priya', 'Isaiah', 'Luna',
	];

	var CITIES = [
		'New York, NY', 'Los Angeles, CA', 'Atlanta, GA', 'Houston, TX',
		'Chicago, IL', 'Miami, FL', 'Detroit, MI', 'Dallas, TX',
		'San Francisco, CA', 'Brooklyn, NY', 'Seattle, WA', 'Oakland, CA',
		'Portland, OR', 'Denver, CO', 'Nashville, TN', 'Phoenix, AZ',
		'Charlotte, NC', 'Philadelphia, PA', 'Toronto, ON', 'London, UK',
	];

	var ACTIONS = [
		'just pre-ordered',
		'just secured',
		'just added to cart',
		'just ordered',
	];

	/* --------------------------------------------------
	   Utilities
	   -------------------------------------------------- */

	function rand(arr) {
		return arr[Math.floor(Math.random() * arr.length)];
	}

	function randInt(min, max) {
		return Math.floor(Math.random() * (max - min + 1)) + min;
	}

	function reducedMotion() {
		return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
	}

	/* --------------------------------------------------
	   PulseEngine Class
	   -------------------------------------------------- */

	function PulseEngine() {
		this._timers = [];
		this._toasts = [];
		this._toastIndex = 0;
		this._dismissed = false;
		this._toastStack = null;
		this._countdownBanner = null;
		this._countdownInterval = null;
		this._viewerBadges = [];
		this._currentViewers = randInt(CONFIG.viewerMin, CONFIG.viewerMax);
		this._interestEl = null;
		this._interestCount = 0;
		this._panelObserver = null;
	}

	/* --------------------------------------------------
	   Init / Destroy
	   -------------------------------------------------- */

	PulseEngine.prototype.init = function () {
		if (document.body.classList.contains('wp-admin')) return;

		this._shuffleProducts();
		this._initToastStack();
		this._initViewerBadges();
		this._initScarcityBadges();
		this._initCountdownBanner();

		if (document.querySelector('.immersive-page, .skyyrose-immersive')) {
			this._initPopularityHeat();
			this._initInterestCounter();
		}
	};

	PulseEngine.prototype.destroy = function () {
		var i;
		for (i = 0; i < this._timers.length; i++) {
			clearTimeout(this._timers[i]);
			clearInterval(this._timers[i]);
		}
		this._timers = [];

		if (this._countdownInterval) {
			clearInterval(this._countdownInterval);
			this._countdownInterval = null;
		}

		if (this._toastStack && this._toastStack.parentNode) {
			this._toastStack.parentNode.removeChild(this._toastStack);
		}

		if (this._countdownBanner && this._countdownBanner.parentNode) {
			this._countdownBanner.parentNode.removeChild(this._countdownBanner);
		}

		for (i = 0; i < this._viewerBadges.length; i++) {
			var badge = this._viewerBadges[i];
			if (badge && badge.parentNode) {
				badge.parentNode.removeChild(badge);
			}
		}
		this._viewerBadges = [];

		var scarcityBadges = document.querySelectorAll('.pulse-scarcity');
		for (i = 0; i < scarcityBadges.length; i++) {
			scarcityBadges[i].parentNode.removeChild(scarcityBadges[i]);
		}

		var heatClasses = ['pulse-heat-low', 'pulse-heat-medium', 'pulse-heat-high'];
		var hotspots = document.querySelectorAll('.hotspot');
		for (i = 0; i < hotspots.length; i++) {
			for (var h = 0; h < heatClasses.length; h++) {
				hotspots[i].classList.remove(heatClasses[h]);
			}
		}

		if (this._interestEl && this._interestEl.parentNode) {
			this._interestEl.parentNode.removeChild(this._interestEl);
			this._interestEl = null;
		}

		if (this._panelObserver) {
			this._panelObserver.disconnect();
			this._panelObserver = null;
		}
	};

	/* --------------------------------------------------
	   Product Shuffle — Avoid Repetition
	   -------------------------------------------------- */

	PulseEngine.prototype._shuffleProducts = function () {
		var arr = PRODUCTS.slice();
		for (var i = arr.length - 1; i > 0; i--) {
			var j = Math.floor(Math.random() * (i + 1));
			var tmp = arr[i];
			arr[i] = arr[j];
			arr[j] = tmp;
		}
		this._shuffled = arr;
	};

	/* --------------------------------------------------
	   1. Social Proof Toasts
	   -------------------------------------------------- */

	PulseEngine.prototype._initToastStack = function () {
		var stack = document.createElement('div');
		stack.className = 'pulse-toast-stack';
		stack.setAttribute('aria-label', 'Recent activity');
		stack.setAttribute('role', 'log');
		stack.setAttribute('aria-live', 'polite');

		if (document.querySelector('.sticky-cta-bar')) {
			stack.classList.add('has-sticky-bar');
		}

		document.body.appendChild(stack);
		this._toastStack = stack;

		var self = this;
		var delay = randInt(6000, 10000);
		var firstTimer = setTimeout(function () {
			self._showNextToast();
			self._scheduleNextToast();
		}, delay);
		this._timers.push(firstTimer);
	};

	PulseEngine.prototype._scheduleNextToast = function () {
		if (this._dismissed) return;
		var self = this;
		var delay = randInt(CONFIG.toastMinDelay, CONFIG.toastMaxDelay);
		var timer = setTimeout(function () {
			self._showNextToast();
			self._scheduleNextToast();
		}, delay);
		this._timers.push(timer);
	};

	PulseEngine.prototype._showNextToast = function () {
		if (this._dismissed) return;
		var self = this;

		while (this._toasts.length >= CONFIG.toastMaxVisible) {
			this._removeToast(this._toasts[0]);
		}

		var product = this._shuffled[this._toastIndex % this._shuffled.length];
		this._toastIndex++;

		var name = rand(FIRST_NAMES);
		var city = rand(CITIES);
		var action = rand(ACTIONS);
		var minutes = randInt(1, 18);
		var timeLabel = minutes === 1 ? '1 minute ago' : minutes + ' minutes ago';

		var toast = document.createElement('div');
		toast.className = 'pulse-toast';
		toast.setAttribute('role', 'status');

		toast.innerHTML =
			'<div class="pulse-toast__thumb">' +
				'<div style="width:100%;height:100%;background:linear-gradient(135deg,rgba(183,110,121,0.2),rgba(17,17,17,0.9));display:flex;align-items:center;justify-content:center;">' +
					'<span style="font-size:0.55rem;font-weight:600;color:rgba(255,255,255,0.5);letter-spacing:0.05em;text-transform:uppercase;">' +
						self._escapeHtml(product.sku) +
					'</span>' +
				'</div>' +
			'</div>' +
			'<div class="pulse-toast__body">' +
				'<div class="pulse-toast__action">' +
					self._escapeHtml(name) + ' from ' + self._escapeHtml(city) + ' ' + self._escapeHtml(action) +
				'</div>' +
				'<div class="pulse-toast__product">' +
					self._escapeHtml(product.name) + ' \u2014 ' + self._escapeHtml(product.price) +
				'</div>' +
				'<div class="pulse-toast__meta">' +
					'Verified \u00b7 ' + timeLabel +
				'</div>' +
			'</div>' +
			'<button class="pulse-toast__close" type="button" aria-label="Dismiss">\u00d7</button>';

		toast.querySelector('.pulse-toast__close').addEventListener('click', function (e) {
			e.stopPropagation();
			self._removeToast(toast);
		});

		toast.addEventListener('click', function () {
			self._removeToast(toast);
		});

		this._toastStack.appendChild(toast);
		this._toasts.push(toast);

		requestAnimationFrame(function () {
			requestAnimationFrame(function () {
				toast.classList.add('visible');
			});
		});

		var hideTimer = setTimeout(function () {
			self._removeToast(toast);
		}, CONFIG.toastDuration);
		this._timers.push(hideTimer);
	};

	PulseEngine.prototype._removeToast = function (toast) {
		if (!toast || !toast.parentNode) return;

		var idx = this._toasts.indexOf(toast);
		if (idx > -1) {
			this._toasts.splice(idx, 1);
		}

		toast.classList.remove('visible');
		toast.classList.add('exiting');

		var removeTimer = setTimeout(function () {
			if (toast.parentNode) {
				toast.parentNode.removeChild(toast);
			}
		}, 500);
		this._timers.push(removeTimer);
	};

	/* --------------------------------------------------
	   2. Live Viewer Badges
	   -------------------------------------------------- */

	PulseEngine.prototype._initViewerBadges = function () {
		var targets = document.querySelectorAll(
			'.product-card__image-container, .product-grid-image, .hotspot'
		);

		for (var i = 0; i < targets.length; i++) {
			var target = targets[i];
			if (target.querySelector('.pulse-viewers')) continue;

			var count = this._currentViewers + randInt(-5, 5);
			count = Math.max(CONFIG.viewerMin, Math.min(CONFIG.viewerMax, count));

			var badge = document.createElement('span');
			badge.className = 'pulse-viewers';
			badge.innerHTML =
				'<span class="pulse-viewers__dot"></span>' +
				'<span class="pulse-viewers__count">' + count + '</span>' +
				' viewing';

			var container = target;
			var style = window.getComputedStyle(container);
			if (style.position === 'static') {
				container.style.position = 'relative';
			}

			container.appendChild(badge);
			this._viewerBadges.push(badge);
		}

		this._scheduleViewerUpdate();
	};

	PulseEngine.prototype._scheduleViewerUpdate = function () {
		var self = this;
		var delay = randInt(CONFIG.viewerUpdateMin, CONFIG.viewerUpdateMax);
		var timer = setTimeout(function () {
			self._updateViewers();
			self._scheduleViewerUpdate();
		}, delay);
		this._timers.push(timer);
	};

	PulseEngine.prototype._updateViewers = function () {
		var delta = randInt(-CONFIG.viewerFluctuation, CONFIG.viewerFluctuation);
		this._currentViewers = Math.max(
			CONFIG.viewerMin,
			Math.min(CONFIG.viewerMax, this._currentViewers + delta)
		);

		for (var i = 0; i < this._viewerBadges.length; i++) {
			var badge = this._viewerBadges[i];
			var countEl = badge.querySelector('.pulse-viewers__count');
			if (countEl) {
				var localDelta = randInt(-1, 1);
				var localCount = this._currentViewers + localDelta;
				localCount = Math.max(CONFIG.viewerMin, Math.min(CONFIG.viewerMax, localCount));
				countEl.textContent = localCount;
			}
		}
	};

	/* --------------------------------------------------
	   3. Scarcity Badges
	   -------------------------------------------------- */

	PulseEngine.prototype._initScarcityBadges = function () {
		var self = this;
		var priceEls = document.querySelectorAll(
			'.product-card__price, .product-grid-price, .product-panel-price'
		);

		for (var i = 0; i < priceEls.length; i++) {
			var priceEl = priceEls[i];
			if (priceEl.parentNode.querySelector('.pulse-scarcity')) continue;

			var stock = randInt(CONFIG.scarcityMin, CONFIG.scarcityMax);
			var showSellingFast = Math.random() < 0.3;

			var badge = document.createElement('div');
			var level, text;

			if (showSellingFast) {
				level = 'urgent';
				text = 'Selling Fast';
			} else if (stock <= 3) {
				level = 'critical';
				text = 'Only ' + stock + ' left!';
			} else if (stock <= 5) {
				level = 'urgent';
				text = 'Only ' + stock + ' left';
			} else {
				level = 'warm';
				text = 'Limited Stock';
			}

			badge.className = 'pulse-scarcity pulse-scarcity--' + level;
			badge.innerHTML =
				'<span class="pulse-scarcity__dot"></span>' +
				self._escapeHtml(text);

			priceEl.parentNode.insertBefore(badge, priceEl.nextSibling);
		}
	};

	/* --------------------------------------------------
	   4. VIP Countdown Banner
	   -------------------------------------------------- */

	PulseEngine.prototype._initCountdownBanner = function () {
		if (sessionStorage.getItem('sr_pulse_countdown_dismissed')) return;

		var banner = document.createElement('div');
		banner.className = 'pulse-countdown-banner';
		banner.innerHTML =
			'<span class="pulse-countdown-banner__label">VIP Pre-Order Closes In</span>' +
			'<span class="pulse-countdown-banner__time">' +
				'<span class="pulse-cd-days">--</span>d' +
				'<span> </span>' +
				'<span class="pulse-cd-hours">--</span>h' +
				'<span> </span>' +
				'<span class="pulse-cd-mins">--</span>m' +
				'<span> </span>' +
				'<span class="pulse-cd-secs">--</span>s' +
			'</span>' +
			'<a href="/pre-order/" class="pulse-countdown-banner__cta">Secure Yours</a>' +
			'<button class="pulse-countdown-banner__dismiss" type="button" aria-label="Dismiss">\u00d7</button>';

		var self = this;

		banner.querySelector('.pulse-countdown-banner__dismiss').addEventListener('click', function () {
			banner.classList.remove('visible');
			sessionStorage.setItem('sr_pulse_countdown_dismissed', '1');
			if (self._countdownInterval) {
				clearInterval(self._countdownInterval);
				self._countdownInterval = null;
			}
		});

		document.body.appendChild(banner);
		this._countdownBanner = banner;

		var daysEl = banner.querySelector('.pulse-cd-days');
		var hoursEl = banner.querySelector('.pulse-cd-hours');
		var minsEl = banner.querySelector('.pulse-cd-mins');
		var secsEl = banner.querySelector('.pulse-cd-secs');
		var target = new Date(CONFIG.countdownTarget).getTime();

		function pad(n) {
			return n < 10 ? '0' + n : '' + n;
		}

		function tick() {
			var now = Date.now();
			var diff = Math.max(0, target - now);

			var days = Math.floor(diff / 86400000);
			var hours = Math.floor((diff % 86400000) / 3600000);
			var mins = Math.floor((diff % 3600000) / 60000);
			var secs = Math.floor((diff % 60000) / 1000);

			daysEl.textContent = days;
			hoursEl.textContent = pad(hours);
			minsEl.textContent = pad(mins);
			secsEl.textContent = pad(secs);

			if (diff === 0 && self._countdownInterval) {
				clearInterval(self._countdownInterval);
			}
		}

		tick();
		this._countdownInterval = setInterval(tick, 1000);

		var showTimer = setTimeout(function () {
			banner.classList.add('visible');
		}, CONFIG.countdownShowDelay);
		this._timers.push(showTimer);
	};

	/* --------------------------------------------------
	   5. Popularity Heat for Immersive Pages
	   -------------------------------------------------- */

	PulseEngine.prototype._initPopularityHeat = function () {
		var hotspots = document.querySelectorAll('.hotspot');
		if (hotspots.length === 0) return;

		var heatLevels = ['pulse-heat-low', 'pulse-heat-medium', 'pulse-heat-high'];
		var weights = [0.35, 0.40, 0.25];

		for (var i = 0; i < hotspots.length; i++) {
			var r = Math.random();
			var level;
			if (r < weights[0]) {
				level = heatLevels[0];
			} else if (r < weights[0] + weights[1]) {
				level = heatLevels[1];
			} else {
				level = heatLevels[2];
			}
			hotspots[i].classList.add(level);
		}
	};

	/* --------------------------------------------------
	   6. Interest Counter for Product Panels
	   -------------------------------------------------- */

	PulseEngine.prototype._initInterestCounter = function () {
		var panel = document.querySelector('.product-panel');
		if (!panel) return;

		var self = this;
		this._interestCount = 0;

		if (typeof MutationObserver !== 'undefined') {
			this._panelObserver = new MutationObserver(function (mutations) {
				for (var m = 0; m < mutations.length; m++) {
					if (mutations[m].attributeName === 'class') {
						var isOpen = panel.classList.contains('open');
						if (isOpen) {
							self._showInterest(panel);
						} else {
							self._hideInterest();
						}
					}
				}
			});

			this._panelObserver.observe(panel, { attributes: true });
		}
	};

	PulseEngine.prototype._showInterest = function (panel) {
		this._hideInterest();

		this._interestCount = randInt(CONFIG.interestBase, CONFIG.interestMax);

		var el = document.createElement('div');
		el.className = 'pulse-interest';
		el.innerHTML =
			'<span class="pulse-interest__icon">\ud83d\udd25</span>' +
			'<span class="pulse-interest__count">' + this._interestCount + '</span>' +
			' people interested';

		var infoContainer = panel.querySelector('.product-panel-info');
		if (infoContainer) {
			infoContainer.appendChild(el);
		} else {
			panel.querySelector('.product-panel-inner').appendChild(el);
		}

		this._interestEl = el;

		var self = this;
		var incrementTimer = setInterval(function () {
			if (!panel.classList.contains('open')) {
				clearInterval(incrementTimer);
				return;
			}
			if (Math.random() < 0.6) {
				self._interestCount += randInt(1, 2);
				var countEl = self._interestEl ? self._interestEl.querySelector('.pulse-interest__count') : null;
				if (countEl) {
					countEl.textContent = self._interestCount;
				}
			}
		}, CONFIG.interestIncrementMs);
		this._timers.push(incrementTimer);
	};

	PulseEngine.prototype._hideInterest = function () {
		if (this._interestEl && this._interestEl.parentNode) {
			this._interestEl.parentNode.removeChild(this._interestEl);
			this._interestEl = null;
		}
	};

	/* --------------------------------------------------
	   HTML Escape Utility
	   -------------------------------------------------- */

	PulseEngine.prototype._escapeHtml = function (str) {
		var div = document.createElement('div');
		div.appendChild(document.createTextNode(str));
		return div.innerHTML;
	};

	/* --------------------------------------------------
	   7. Section Reveal — IntersectionObserver Fade-In
	   -------------------------------------------------- */

	PulseEngine.prototype._initSectionReveals = function () {
		if (reducedMotion()) return;
		if (typeof IntersectionObserver === 'undefined') return;

		var revealTargets = document.querySelectorAll(
			'.gateway-section-header, .product-grid-card, .product-card, ' +
			'.preorder-countdown, .collection-tabs, .member-banner, ' +
			'[data-pulse-reveal]'
		);

		if (revealTargets.length === 0) return;

		for (var i = 0; i < revealTargets.length; i++) {
			revealTargets[i].classList.add('pulse-reveal');
		}

		var observer = new IntersectionObserver(
			function (entries) {
				for (var e = 0; e < entries.length; e++) {
					if (entries[e].isIntersecting) {
						entries[e].target.classList.add('pulse-reveal--visible');
						observer.unobserve(entries[e].target);
					}
				}
			},
			{ threshold: 0.15, rootMargin: '0px 0px -40px 0px' }
		);

		for (var j = 0; j < revealTargets.length; j++) {
			observer.observe(revealTargets[j]);
		}

		this._revealObserver = observer;
	};

	/* --------------------------------------------------
	   8. Luxury 3D Tilt on Product Cards
	   -------------------------------------------------- */

	PulseEngine.prototype._initCardTilt = function () {
		if (reducedMotion()) return;
		if (!('ontouchstart' in window)) {
			var cardTargets = document.querySelectorAll(
				'.product-grid-card, .product-card'
			);

			for (var i = 0; i < cardTargets.length; i++) {
				(function (card) {
					card.addEventListener('mousemove', function (e) {
						var rect = card.getBoundingClientRect();
						var x = (e.clientX - rect.left) / rect.width;
						var y = (e.clientY - rect.top) / rect.height;

						var tiltX = (y - 0.5) * -8;
						var tiltY = (x - 0.5) * 8;

						card.style.transform =
							'perspective(1000px) rotateX(' + tiltX + 'deg) rotateY(' + tiltY + 'deg) translateY(-2px)';
						card.style.transition = 'transform 0.1s ease-out';
					});

					card.addEventListener('mouseleave', function () {
						card.style.transform = '';
						card.style.transition = 'transform 0.4s cubic-bezier(0.22, 1, 0.36, 1)';
					});
				})(cardTargets[i]);
			}
		}
	};

	/* --------------------------------------------------
	   9. Rose Gold Shimmer on Buttons
	   -------------------------------------------------- */

	PulseEngine.prototype._initButtonShimmer = function () {
		if (reducedMotion()) return;

		var buttons = document.querySelectorAll(
			'.modal-add-to-cart, .cart-checkout-btn, ' +
			'.pulse-countdown-banner__cta, .incentive-popup-submit, ' +
			'[data-pulse-shimmer]'
		);

		for (var i = 0; i < buttons.length; i++) {
			buttons[i].classList.add('pulse-shimmer-btn');
		}
	};

	/* --------------------------------------------------
	   10. Hero Text Float Animation
	   -------------------------------------------------- */

	PulseEngine.prototype._initHeroFloat = function () {
		if (reducedMotion()) return;

		var heroEls = document.querySelectorAll(
			'.loading-monogram, .gateway-logo, ' +
			'.gateway-section-header h2, [data-pulse-float]'
		);

		for (var i = 0; i < heroEls.length; i++) {
			heroEls[i].classList.add('pulse-hero-float');
		}
	};

	/* --------------------------------------------------
	   11. Collection Logo Glow Rotation
	   -------------------------------------------------- */

	PulseEngine.prototype._initLogoGlow = function () {
		if (reducedMotion()) return;

		var logos = document.querySelectorAll(
			'.collection-logo, .collection-logo-img, [data-pulse-logo-glow]'
		);

		for (var i = 0; i < logos.length; i++) {
			logos[i].classList.add('pulse-logo-glow');
		}
	};

	/* --------------------------------------------------
	   12. Sparkle Particles on Brand Monogram Hover
	   -------------------------------------------------- */

	PulseEngine.prototype._initSparkles = function () {
		if (reducedMotion()) return;

		var monograms = document.querySelectorAll(
			'.loading-monogram, .gateway-logo, .incentive-popup-monogram, ' +
			'[data-pulse-sparkle]'
		);

		var self = this;

		for (var i = 0; i < monograms.length; i++) {
			(function (el) {
				var container = el.parentNode;
				var style = window.getComputedStyle(container);
				if (style.position === 'static') {
					container.style.position = 'relative';
				}
				container.style.overflow = 'visible';

				el.addEventListener('mouseenter', function () {
					self._spawnSparkles(container, 6);
				});
			})(monograms[i]);
		}
	};

	PulseEngine.prototype._spawnSparkles = function (container, count) {
		var self = this;
		for (var i = 0; i < count; i++) {
			(function (index) {
				var delay = index * 80;
				var timer = setTimeout(function () {
					var sparkle = document.createElement('span');
					sparkle.className = 'pulse-sparkle';
					sparkle.textContent = '\u2726';
					sparkle.style.left = Math.random() * 100 + '%';
					sparkle.style.top = Math.random() * 100 + '%';
					sparkle.style.animationDelay = (Math.random() * 0.3) + 's';
					sparkle.style.fontSize = (0.5 + Math.random() * 0.6) + 'rem';

					container.appendChild(sparkle);

					var removeTimer = setTimeout(function () {
						if (sparkle.parentNode) {
							sparkle.parentNode.removeChild(sparkle);
						}
					}, 1200);
					self._timers.push(removeTimer);
				}, delay);
				self._timers.push(timer);
			})(i);
		}
	};

	/* --------------------------------------------------
	   13. Rooms Explored Counter (Immersive Pages)
	   -------------------------------------------------- */

	PulseEngine.prototype._initRoomsExplored = function () {
		var immersivePage = document.querySelector('.immersive-page, .skyyrose-immersive');
		if (!immersivePage) return;

		var rooms = document.querySelectorAll(
			'.immersive-room, .immersive-scene, [data-room]'
		);
		if (rooms.length === 0) return;

		var counter = document.createElement('div');
		counter.className = 'pulse-rooms-counter';
		counter.innerHTML =
			'<span class="pulse-rooms-counter__icon">\ud83c\udfe0</span>' +
			'<span class="pulse-rooms-counter__explored">0</span>' +
			' / ' +
			'<span class="pulse-rooms-counter__total">' + rooms.length + '</span>' +
			' rooms explored';

		document.body.appendChild(counter);
		this._roomsCounter = counter;

		var explored = new Set();
		var exploredEl = counter.querySelector('.pulse-rooms-counter__explored');

		var observer = new IntersectionObserver(
			function (entries) {
				for (var e = 0; e < entries.length; e++) {
					if (entries[e].isIntersecting) {
						explored.add(entries[e].target);
						exploredEl.textContent = explored.size;

						if (explored.size === rooms.length) {
							counter.classList.add('pulse-rooms-counter--complete');
						}
					}
				}
			},
			{ threshold: 0.5 }
		);

		for (var i = 0; i < rooms.length; i++) {
			observer.observe(rooms[i]);
		}

		this._roomsObserver = observer;

		var showTimer = setTimeout(function () {
			counter.classList.add('visible');
		}, 2000);
		this._timers.push(showTimer);
	};

	/* --------------------------------------------------
	   14. Global Page Viewer Counter (Top Bar)
	   -------------------------------------------------- */

	PulseEngine.prototype._initPageViewerCounter = function () {
		var productSection = document.querySelector(
			'.gateway-product-section, .product-grid, .product-listing'
		);
		if (!productSection) return;

		var count = this._currentViewers + randInt(10, 40);
		var counter = document.createElement('div');
		counter.className = 'pulse-page-viewers';
		counter.innerHTML =
			'<span class="pulse-page-viewers__dot"></span>' +
			'<span class="pulse-page-viewers__count">' + count + '</span>' +
			' people are shopping right now';

		var header = document.querySelector('.gateway-section-header');
		if (header && header.parentNode) {
			header.parentNode.insertBefore(counter, header.nextSibling);
		} else {
			productSection.insertBefore(counter, productSection.firstChild);
		}

		this._pageViewerCounter = counter;

		var self = this;
		var updateTimer = setInterval(function () {
			var delta = randInt(-2, 3);
			count = Math.max(15, Math.min(130, count + delta));
			var countEl = counter.querySelector('.pulse-page-viewers__count');
			if (countEl) countEl.textContent = count;
		}, randInt(8000, 15000));
		this._timers.push(updateTimer);
	};

	/* --------------------------------------------------
	   Update Init to Include New Features
	   -------------------------------------------------- */

	var _originalInit = PulseEngine.prototype.init;
	PulseEngine.prototype.init = function () {
		_originalInit.call(this);

		this._initSectionReveals();
		this._initCardTilt();
		this._initButtonShimmer();
		this._initHeroFloat();
		this._initLogoGlow();
		this._initSparkles();
		this._initRoomsExplored();
		this._initPageViewerCounter();
	};

	/* --------------------------------------------------
	   Update Destroy to Clean Up New Features
	   -------------------------------------------------- */

	var _originalDestroy = PulseEngine.prototype.destroy;
	PulseEngine.prototype.destroy = function () {
		_originalDestroy.call(this);

		if (this._revealObserver) {
			this._revealObserver.disconnect();
			this._revealObserver = null;
		}

		if (this._roomsObserver) {
			this._roomsObserver.disconnect();
			this._roomsObserver = null;
		}

		if (this._roomsCounter && this._roomsCounter.parentNode) {
			this._roomsCounter.parentNode.removeChild(this._roomsCounter);
			this._roomsCounter = null;
		}

		if (this._pageViewerCounter && this._pageViewerCounter.parentNode) {
			this._pageViewerCounter.parentNode.removeChild(this._pageViewerCounter);
			this._pageViewerCounter = null;
		}

		var sparkles = document.querySelectorAll('.pulse-sparkle');
		for (var i = 0; i < sparkles.length; i++) {
			if (sparkles[i].parentNode) {
				sparkles[i].parentNode.removeChild(sparkles[i]);
			}
		}
	};

	/* --------------------------------------------------
	   Bootstrap
	   -------------------------------------------------- */

	var engine = null;

	function init() {
		engine = new PulseEngine();
		engine.init();

		window.SkyyRosePulse = engine;
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}
})();
