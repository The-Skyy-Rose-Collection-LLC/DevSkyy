/**
 * Magnetic Obsidian — Cursor-Tracking 3D Cards + Exit-Intent Capture
 *
 * Magnetic tilt on product cards, gravitational hotspot pull,
 * exit-intent email overlay, and lightweight conversion tracking.
 *
 * Vanilla JS, no dependencies. XSS-safe DOM manipulation.
 *
 * @package SkyyRose_Flagship
 * @since   3.3.0
 */

(function () {
	'use strict';

	/* ==========================================================================
	   Shared Utilities
	   ========================================================================== */

	var REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
	var IS_TOUCH = window.matchMedia('(hover: none)').matches;

	function clamp(val, min, max) {
		return Math.max(min, Math.min(max, val));
	}

	function lerp(start, end, factor) {
		return start + (end - start) * factor;
	}

	function createElement(tag, className, attrs) {
		var el = document.createElement(tag);
		if (className) el.className = className;
		if (attrs) {
			for (var key in attrs) {
				if (Object.prototype.hasOwnProperty.call(attrs, key)) {
					el.setAttribute(key, attrs[key]);
				}
			}
		}
		return el;
	}

	/* ==========================================================================
	   1. MagneticEngine — 3D tilt effect on product cards
	   ========================================================================== */

	function MagneticEngine() {
		this._cards = [];
		this._frameId = null;
		this._active = null; // card currently being hovered
		this._mouseX = 0;
		this._mouseY = 0;
		this._targetRotateX = 0;
		this._targetRotateY = 0;
		this._currentRotateX = 0;
		this._currentRotateY = 0;
		this._tiltMultiplier = 1;

		this._onMouseMove = this._handleMouseMove.bind(this);
		this._onMouseLeave = this._handleMouseLeave.bind(this);
		this._boundAnimate = this._animate.bind(this);
	}

	MagneticEngine.prototype.init = function () {
		var selectors = '.product-card, .preorder-product, .collection-product-card';
		var elements = document.querySelectorAll(selectors);

		if (!elements.length) return;

		// Detect variant B for enhanced tilt
		if (document.body.classList.contains('variant-b')) {
			this._tiltMultiplier = 2;
		}

		for (var i = 0; i < elements.length; i++) {
			var card = elements[i];
			card.classList.add('magnetic-card');

			// Wrap in perspective container if not already wrapped
			if (!card.parentElement || !card.parentElement.classList.contains('magnetic-card-wrap')) {
				var wrap = createElement('div', 'magnetic-card-wrap');
				card.parentNode.insertBefore(wrap, card);
				wrap.appendChild(card);
			}

			card.addEventListener('mousemove', this._onMouseMove, { passive: true });
			card.addEventListener('mouseleave', this._onMouseLeave);

			this._cards.push(card);
		}

		this._frameId = requestAnimationFrame(this._boundAnimate);
	};

	MagneticEngine.prototype._handleMouseMove = function (e) {
		var card = e.currentTarget;
		var rect = card.getBoundingClientRect();

		// Mouse position as 0-100 within the card
		var x = clamp(((e.clientX - rect.left) / rect.width) * 100, 0, 100);
		var y = clamp(((e.clientY - rect.top) / rect.height) * 100, 0, 100);

		this._active = card;
		this._mouseX = x;
		this._mouseY = y;

		// Target rotation: ±15deg range, multiplied by variant factor
		var maxTilt = 15 * this._tiltMultiplier;
		this._targetRotateX = ((y - 50) / 50) * -maxTilt;
		this._targetRotateY = ((x - 50) / 50) * maxTilt;

		// Set CSS custom properties for the light reflection
		card.style.setProperty('--mouse-x', x.toFixed(1));
		card.style.setProperty('--mouse-y', y.toFixed(1));
	};

	MagneticEngine.prototype._handleMouseLeave = function (e) {
		var card = e.currentTarget;

		this._active = null;
		this._targetRotateX = 0;
		this._targetRotateY = 0;

		// Let the CSS transition handle the smooth spring back
		card.style.setProperty('--rotate-x', '0deg');
		card.style.setProperty('--rotate-y', '0deg');
		card.style.setProperty('--mouse-x', '50');
		card.style.setProperty('--mouse-y', '50');
		card.style.transform = '';
	};

	MagneticEngine.prototype._animate = function () {
		if (this._active) {
			// Smooth interpolation toward target
			this._currentRotateX = lerp(this._currentRotateX, this._targetRotateX, 0.08);
			this._currentRotateY = lerp(this._currentRotateY, this._targetRotateY, 0.08);

			// Apply transform directly for best perf (bypasses CSS transition)
			var rx = this._currentRotateX.toFixed(2);
			var ry = this._currentRotateY.toFixed(2);

			this._active.style.transform =
				'rotateX(' + rx + 'deg) rotateY(' + ry + 'deg) scale(1.02)';
			this._active.style.setProperty('--rotate-x', rx + 'deg');
			this._active.style.setProperty('--rotate-y', ry + 'deg');
		} else {
			// Decay current values toward zero when not hovering
			if (Math.abs(this._currentRotateX) > 0.01 || Math.abs(this._currentRotateY) > 0.01) {
				this._currentRotateX = lerp(this._currentRotateX, 0, 0.06);
				this._currentRotateY = lerp(this._currentRotateY, 0, 0.06);
			} else {
				this._currentRotateX = 0;
				this._currentRotateY = 0;
			}
		}

		this._frameId = requestAnimationFrame(this._boundAnimate);
	};

	MagneticEngine.prototype.destroy = function () {
		if (this._frameId) cancelAnimationFrame(this._frameId);

		for (var i = 0; i < this._cards.length; i++) {
			var card = this._cards[i];
			card.removeEventListener('mousemove', this._onMouseMove);
			card.removeEventListener('mouseleave', this._onMouseLeave);
			card.style.transform = '';
		}

		this._cards = [];
		this._active = null;
	};

	/* ==========================================================================
	   2. HotspotMagnetism — Gravitational pull on immersive hotspots
	   ========================================================================== */

	function HotspotMagnetism() {
		this._hotspots = [];
		this._scene = null;
		this._lastMoveTime = 0;
		this._throttleMs = 16; // ~60fps
		this._pullRadius = 120; // px

		this._onMouseMove = this._handleMouseMove.bind(this);
	}

	HotspotMagnetism.prototype.init = function () {
		this._scene = document.querySelector('.immersive-scene');
		if (!this._scene) return;

		var spots = this._scene.querySelectorAll('.hotspot');
		if (!spots.length) return;

		for (var i = 0; i < spots.length; i++) {
			this._hotspots.push(spots[i]);
		}

		this._scene.addEventListener('mousemove', this._onMouseMove, { passive: true });
	};

	HotspotMagnetism.prototype._handleMouseMove = function (e) {
		var now = Date.now();
		if (now - this._lastMoveTime < this._throttleMs) return;
		this._lastMoveTime = now;

		var cursorX = e.clientX;
		var cursorY = e.clientY;

		for (var i = 0; i < this._hotspots.length; i++) {
			var hotspot = this._hotspots[i];
			var rect = hotspot.getBoundingClientRect();
			var centerX = rect.left + rect.width / 2;
			var centerY = rect.top + rect.height / 2;

			var dx = cursorX - centerX;
			var dy = cursorY - centerY;
			var distance = Math.sqrt(dx * dx + dy * dy);

			if (distance < this._pullRadius) {
				// Strength: 1 at center, 0 at edge of radius (inverse)
				var strength = 1 - (distance / this._pullRadius);
				strength = strength * strength; // quadratic falloff for physics feel

				// Normalized direction toward cursor
				var pullX = distance > 0 ? (dx / distance) * strength : 0;
				var pullY = distance > 0 ? (dy / distance) * strength : 0;

				hotspot.classList.add('magnetic-active');
				hotspot.style.setProperty('--pull-x', pullX.toFixed(3));
				hotspot.style.setProperty('--pull-y', pullY.toFixed(3));
			} else {
				if (hotspot.classList.contains('magnetic-active')) {
					hotspot.classList.remove('magnetic-active');
					hotspot.style.setProperty('--pull-x', '0');
					hotspot.style.setProperty('--pull-y', '0');
				}
			}
		}
	};

	HotspotMagnetism.prototype.destroy = function () {
		if (this._scene) {
			this._scene.removeEventListener('mousemove', this._onMouseMove);
		}

		for (var i = 0; i < this._hotspots.length; i++) {
			this._hotspots[i].classList.remove('magnetic-active');
		}

		this._hotspots = [];
	};

	/* ==========================================================================
	   3. ExitIntentCapture — Premium email capture overlay
	   ========================================================================== */

	function ExitIntentCapture() {
		this._overlay = null;
		this._enteredAt = Date.now();
		this._shown = false;
		this._minTimeOnPage = 15000; // 15 seconds
		this._lastScrollY = 0;
		this._rapidScrollCount = 0;

		this._onMouseLeave = this._handleMouseLeave.bind(this);
		this._onScroll = this._handleScroll.bind(this);
	}

	ExitIntentCapture.prototype.init = function () {
		// Don't show if already submitted
		if (localStorage.getItem('sr_exit_email_submitted')) return;

		// Don't show if already shown this session
		if (sessionStorage.getItem('sr_exit_shown')) return;

		// Desktop: mouseleave detection
		document.documentElement.addEventListener('mouseleave', this._onMouseLeave);

		// Mobile: rapid scroll-up detection
		if (IS_TOUCH) {
			window.addEventListener('scroll', this._onScroll, { passive: true });
		}
	};

	ExitIntentCapture.prototype._handleMouseLeave = function (e) {
		if (e.clientY > 10) return; // only trigger when mouse leaves top of viewport
		this._tryShow();
	};

	ExitIntentCapture.prototype._handleScroll = function () {
		var currentY = window.scrollY;
		var delta = this._lastScrollY - currentY;
		this._lastScrollY = currentY;

		// Detect rapid upward scroll (> 200px in one frame-ish)
		if (delta > 200) {
			this._rapidScrollCount++;
			if (this._rapidScrollCount >= 2) {
				this._tryShow();
			}
		} else if (delta <= 0) {
			this._rapidScrollCount = 0;
		}
	};

	ExitIntentCapture.prototype._tryShow = function () {
		if (this._shown) return;

		// Must have been on page for minimum time
		if (Date.now() - this._enteredAt < this._minTimeOnPage) return;

		this._shown = true;
		sessionStorage.setItem('sr_exit_shown', '1');
		this._buildAndShow();
	};

	ExitIntentCapture.prototype._buildAndShow = function () {
		var self = this;

		// Build overlay
		var overlay = createElement('div', 'exit-intent-overlay');
		overlay.setAttribute('role', 'dialog');
		overlay.setAttribute('aria-modal', 'true');
		overlay.setAttribute('aria-label', 'VIP offer');

		// Card
		var card = createElement('div', 'exit-intent-card');

		// Close button
		var closeBtn = createElement('button', 'exit-intent-close', {
			'type': 'button',
			'aria-label': 'Close dialog'
		});
		closeBtn.textContent = '\u00D7';

		// Headline
		var headline = createElement('h2', 'exit-intent-headline');
		headline.textContent = 'Before You Go\u2026';

		// Subtitle
		var subtitle = createElement('p', 'exit-intent-subtitle');
		subtitle.textContent = 'Join the Inner Circle for VIP early access & 15% off your first order.';

		// Form row
		var form = createElement('div', 'exit-intent-form');

		var input = createElement('input', 'exit-intent-input', {
			'type': 'email',
			'placeholder': 'Enter your email',
			'aria-label': 'Email address',
			'autocomplete': 'email'
		});

		var ctaBtn = createElement('button', 'exit-intent-cta', { 'type': 'button' });
		ctaBtn.textContent = 'Unlock VIP Access';

		form.appendChild(input);
		form.appendChild(ctaBtn);

		// Dismiss link
		var dismissBtn = createElement('button', 'exit-intent-dismiss', { 'type': 'button' });
		dismissBtn.textContent = 'No thanks';

		// Thank-you message (hidden initially)
		var thankYou = createElement('p', 'exit-intent-thank-you');
		thankYou.textContent = 'Welcome to the Inner Circle. Check your inbox for something special.';

		// Assemble
		card.appendChild(closeBtn);
		card.appendChild(headline);
		card.appendChild(subtitle);
		card.appendChild(form);
		card.appendChild(dismissBtn);
		card.appendChild(thankYou);
		overlay.appendChild(card);
		document.body.appendChild(overlay);
		this._overlay = overlay;

		// Trigger active state in next frame for CSS transition
		requestAnimationFrame(function () {
			overlay.classList.add('active');
		});

		// Event handlers
		closeBtn.addEventListener('click', function () {
			self._close();
		});

		dismissBtn.addEventListener('click', function () {
			self._close();
		});

		// Click outside card to close
		overlay.addEventListener('click', function (e) {
			if (e.target === overlay) self._close();
		});

		// Escape key
		var escHandler = function (e) {
			if (e.key === 'Escape') {
				self._close();
				document.removeEventListener('keydown', escHandler);
			}
		};
		document.addEventListener('keydown', escHandler);

		// Submit handler
		ctaBtn.addEventListener('click', function () {
			var email = input.value.trim();
			if (!email || !self._isValidEmail(email)) {
				input.style.borderColor = 'rgba(220, 20, 60, 0.6)';
				input.focus();
				return;
			}

			// Store email submission flag (not the actual email — just the flag)
			localStorage.setItem('sr_exit_email_submitted', '1');

			// Show thank-you state
			card.classList.add('thank-you');
			headline.textContent = 'You\u2019re In.';

			// Auto-close after 2 seconds
			setTimeout(function () {
				self._close();
			}, 2000);
		});

		// Reset input border on typing
		input.addEventListener('input', function () {
			input.style.borderColor = '';
		});
	};

	ExitIntentCapture.prototype._isValidEmail = function (email) {
		// Basic structural check — not exhaustive, server validates fully
		return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
	};

	ExitIntentCapture.prototype._close = function () {
		var self = this;
		if (!this._overlay) return;

		this._overlay.classList.remove('active');

		// Remove from DOM after transition
		setTimeout(function () {
			if (self._overlay && self._overlay.parentNode) {
				self._overlay.parentNode.removeChild(self._overlay);
			}
			self._overlay = null;
		}, 500);
	};

	ExitIntentCapture.prototype.destroy = function () {
		document.documentElement.removeEventListener('mouseleave', this._onMouseLeave);
		window.removeEventListener('scroll', this._onScroll);
		this._close();
	};

	/* ==========================================================================
	   4. ConversionTracker — Lightweight session analytics
	   ========================================================================== */

	function ConversionTracker() {
		this._storageKey = 'sr_conversion_state';
		this._startTime = Date.now();
		this._scrollMax = 0;
		this._interactions = 0;
		this._state = null;
	}

	ConversionTracker.prototype.init = function () {
		var self = this;

		// Load or create state
		this._state = this._loadState();

		// Track current page
		var slug = window.location.pathname.replace(/^\/|\/$/g, '') || 'home';
		if (this._state.pages_visited.indexOf(slug) === -1) {
			this._state.pages_visited.push(slug);
		}

		// Determine funnel stage from URL context
		this._state.funnel_stage = this._determineFunnelStage(slug);

		// Track scroll depth
		window.addEventListener('scroll', function () {
			var docHeight = document.documentElement.scrollHeight - window.innerHeight;
			if (docHeight > 0) {
				var pct = Math.round((window.scrollY / docHeight) * 100);
				self._scrollMax = Math.max(self._scrollMax, pct);
			}
		}, { passive: true });

		// Track product interactions (click/tap on product cards)
		document.addEventListener('click', function (e) {
			var card = e.target.closest('.product-card, .preorder-product, .collection-product-card, .hotspot');
			if (!card) return;
			self._interactions++;

			var sku = card.getAttribute('data-sku') || card.getAttribute('data-product-id');
			if (sku && self._state.products_viewed.indexOf(sku) === -1) {
				self._state.products_viewed.push(sku);
			}
		});

		// Persist on visibility change (tab switch, close)
		document.addEventListener('visibilitychange', function () {
			if (document.visibilityState === 'hidden') {
				self._updateTimeAndSave();
			}
		});

		// Persist on unload as backup
		window.addEventListener('pagehide', function () {
			self._updateTimeAndSave();
		});

		// Save periodically every 10 seconds
		this._saveInterval = setInterval(function () {
			self._updateTimeAndSave();
		}, 10000);

		// Expose public API
		window.__skyyConversion = {
			getState: function () {
				self._updateEngagementDepth();
				return JSON.parse(JSON.stringify(self._state));
			},
			getVariant: function () {
				return self._state.variant;
			}
		};
	};

	ConversionTracker.prototype._loadState = function () {
		var stored = null;
		try {
			var raw = sessionStorage.getItem(this._storageKey);
			if (raw) stored = JSON.parse(raw);
		} catch (e) {
			// Ignore parse errors
		}

		if (stored && stored.pages_visited) {
			return stored;
		}

		// Initialize fresh state
		var variant = localStorage.getItem('sr_ab_variant');
		if (!variant) {
			variant = Math.random() < 0.5 ? 'a' : 'b';
			localStorage.setItem('sr_ab_variant', variant);
		}

		return {
			pages_visited: [],
			time_on_page: {},
			products_viewed: [],
			engagement_depth: 0,
			funnel_stage: 'browsing',
			variant: variant
		};
	};

	ConversionTracker.prototype._determineFunnelStage = function (slug) {
		// Checkout takes highest priority
		if (/checkout/.test(slug)) return 'checkout';

		// Cart or pre-order with prior product interactions
		if (/cart|pre-?order/.test(slug)) {
			return this._state.products_viewed.length > 0 ? 'cart' : 'browsing';
		}

		// Product detail, immersive experience, or individual collection page
		if (/immersive|product\/|collections\/[a-z]/.test(slug)) return 'engaged';

		// Homepage, landing, top-level collections
		return 'browsing';
	};

	ConversionTracker.prototype._updateEngagementDepth = function () {
		// Score from 0-100 based on three signals
		var timeScore = Math.min(30, Math.round(((Date.now() - this._startTime) / 1000 / 120) * 30));
		var scrollScore = Math.min(30, Math.round((this._scrollMax / 100) * 30));
		var interactionScore = Math.min(40, this._interactions * 8);

		this._state.engagement_depth = clamp(timeScore + scrollScore + interactionScore, 0, 100);
	};

	ConversionTracker.prototype._updateTimeAndSave = function () {
		var slug = window.location.pathname.replace(/^\/|\/$/g, '') || 'home';
		var elapsed = Math.round((Date.now() - this._startTime) / 1000);
		this._state.time_on_page[slug] = elapsed;

		this._updateEngagementDepth();

		try {
			sessionStorage.setItem(this._storageKey, JSON.stringify(this._state));
		} catch (e) {
			// Storage full — silently ignore
		}
	};

	ConversionTracker.prototype.destroy = function () {
		if (this._saveInterval) clearInterval(this._saveInterval);
		this._updateTimeAndSave();
		delete window.__skyyConversion;
	};

	/* ==========================================================================
	   5. Initialization
	   ========================================================================== */

	function initMagneticObsidian() {
		// 1. Determine and apply A/B variant
		var variant = localStorage.getItem('sr_ab_variant');
		if (!variant) {
			variant = Math.random() < 0.5 ? 'a' : 'b';
			localStorage.setItem('sr_ab_variant', variant);
		}
		document.body.classList.add('variant-' + variant);

		// 2. Conversion tracker runs regardless of motion preference
		var tracker = new ConversionTracker();
		tracker.init();

		// 3. Exit-intent runs regardless of motion preference (animations degrade gracefully)
		var exitIntent = new ExitIntentCapture();
		exitIntent.init();

		// 4. Skip motion-intensive features for accessibility
		if (REDUCED_MOTION || IS_TOUCH) return;

		// 5. Magnetic card engine
		var engine = new MagneticEngine();
		engine.init();

		// 6. Hotspot magnetism — only on immersive pages
		if (document.querySelector('.immersive-scene')) {
			var hotspots = new HotspotMagnetism();
			hotspots.init();
		}

		// Cleanup on page leave
		window.addEventListener('pagehide', function () {
			engine.destroy();
			if (typeof hotspots !== 'undefined' && hotspots) hotspots.destroy();
			exitIntent.destroy();
			tracker.destroy();
		});
	}

	/* --------------------------------------------------
	   Boot
	   -------------------------------------------------- */

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', initMagneticObsidian);
	} else {
		initMagneticObsidian();
	}
})();
