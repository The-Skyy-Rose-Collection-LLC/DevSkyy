/**
 * Adaptive Personalization Engine (APE)
 *
 * Behavioral tracking, heat-scored recommendations, ambient mood
 * transitions, smart bundle suggestions, and recently-viewed strip.
 * Self-contained, no external dependencies. Pure vanilla JS.
 *
 * Modules:
 *   1. BehaviorTracker  — Page views, scroll depth, time, heat scores
 *   2. RecommendationDrawer — "Your Picks" slide-in drawer
 *   3. AmbientMoodEngine — Collection-aware CSS mood transitions
 *   4. BundleSuggestions — "Bundle & Save" toast for same-collection views
 *   5. RecentlyViewedStrip — Horizontal thumbnail strip
 *
 * Public API: window.SkyyRoseAPE
 *
 * @package SkyyRose_Flagship
 * @since   3.8.0
 */

(function () {
	'use strict';

	/* ==================================================
	   Configuration
	   ================================================== */

	var CFG = {
		storageKey:          'sr_behavior',
		recentKey:           'sr_recently_viewed',
		bundleDismissKey:    'sr_bundle_dismissed',
		maxRecentlyViewed:   6,
		maxRecommendations:  4,
		drawerTriggerTime:   30000,   // 30s before "Your Picks" button appears
		drawerTriggerScroll: 0.5,     // 50% scroll depth
		moodTransitionMs:    2000,    // 2s mood crossfade
		bundleThreshold:     2,       // products from same collection before bundle toast
		bundleMinForOffer:   3,       // "bundle 3+ items" messaging
		heatWeights: {
			view:        1,
			hover:       2,
			panel_open:  5,
			add_to_cart: 10,
		},
		intentThresholds: {
			interested:   10,
			ready_to_buy: 30,
		},
		drawerWidthDesktop: '400px',
		drawerWidthMobile:  '80vw',
		mobileBreakpoint:   768,
	};

	/* ==================================================
	   Utility Helpers
	   ================================================== */

	function $(selector, context) {
		return (context || document).querySelector(selector);
	}

	function $$(selector, context) {
		return Array.from((context || document).querySelectorAll(selector));
	}

	function createElement(tag, className, attrs) {
		var el = document.createElement(tag);
		if (className) el.className = className;
		if (attrs) {
			Object.keys(attrs).forEach(function (key) {
				if (key === 'textContent') {
					el.textContent = attrs[key];
				} else if (key === 'innerHTML') {
					el.innerHTML = attrs[key];
				} else {
					el.setAttribute(key, attrs[key]);
				}
			});
		}
		return el;
	}

	function prefersReducedMotion() {
		return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
	}

	function isMobile() {
		return window.innerWidth < CFG.mobileBreakpoint;
	}

	function throttle(fn, delay) {
		var last = 0;
		return function () {
			var now = Date.now();
			if (now - last >= delay) {
				last = now;
				fn.apply(null, arguments);
			}
		};
	}

	/* ==================================================
	   Product Catalogue — harvested from page DOM
	   ================================================== */

	var catalogue = [];  // { sku, name, price, image, collection, url }
	var catalogueBySku = {};

	/**
	 * Scan the page for product data from three sources:
	 *   1. .hotspot[data-product-id]  (immersive pages)
	 *   2. [data-cie-stock]           (conversion engine stock elements)
	 *   3. .collection-product-card   (collection catalog pages)
	 */
	function harvestCatalogue() {
		var seen = {};

		// Source 1: immersive hotspots
		$$('.hotspot[data-product-id]').forEach(function (el) {
			var sku = el.dataset.productId;
			if (!sku || seen[sku]) return;
			seen[sku] = true;
			catalogue.push({
				sku:        sku,
				name:       el.dataset.productName       || '',
				price:      el.dataset.productPrice      || '',
				image:      el.dataset.productImage      || '',
				collection: el.dataset.productCollection || '',
				url:        el.dataset.productUrl        || '#',
			});
		});

		// Source 2: stock scarcity elements
		$$('[data-cie-stock][data-product-id]').forEach(function (el) {
			var sku = el.dataset.productId;
			if (!sku || seen[sku]) return;
			seen[sku] = true;
			catalogue.push({
				sku:        sku,
				name:       el.dataset.productName       || '',
				price:      el.dataset.productPrice      || '',
				image:      el.dataset.productImage      || '',
				collection: el.dataset.productCollection || '',
				url:        el.dataset.productUrl        || '#',
			});
		});

		// Source 3: collection product cards
		$$('.collection-product-card').forEach(function (el) {
			var nameEl  = el.querySelector('.collection-product-card__name');
			var priceEl = el.querySelector('.collection-product-card__price');
			var imgEl   = el.querySelector('.collection-product-card__image');
			var name    = nameEl  ? nameEl.textContent.trim()  : '';
			var price   = priceEl ? priceEl.textContent.trim() : '';
			var image   = imgEl   ? imgEl.src                  : '';
			var url     = el.href || el.dataset.productUrl     || '#';

			// Derive SKU from URL or name (fallback)
			var sku = el.dataset.productId || name.toLowerCase().replace(/\s+/g, '-').substring(0, 20);
			if (!sku || seen[sku]) return;
			seen[sku] = true;

			// Infer collection from page context or badge
			var badgeEl = el.querySelector('.collection-product-card__badge');
			var collection = el.dataset.productCollection
				|| (badgeEl ? badgeEl.textContent.trim() : '')
				|| deriveCollectionFromPage();

			catalogue.push({
				sku:        sku,
				name:       name,
				price:      price,
				image:      image,
				collection: collection,
				url:        url,
			});
		});

		// Source 4: preorder gateway cards
		$$('[data-product-id][data-product-name]').forEach(function (el) {
			var sku = el.dataset.productId;
			if (!sku || seen[sku]) return;
			seen[sku] = true;
			catalogue.push({
				sku:        sku,
				name:       el.dataset.productName            || '',
				price:      el.dataset.productPrice           || '',
				image:      el.dataset.productImage           || '',
				collection: el.dataset.productCollection
				         || el.dataset.productCollectionLabel || '',
				url:        el.dataset.productUrl             || '#',
			});
		});

		// Build lookup map
		catalogue.forEach(function (p) {
			catalogueBySku[p.sku] = p;
		});
	}

	function deriveCollectionFromPage() {
		var path = window.location.pathname.toLowerCase();
		if (path.indexOf('black-rose') !== -1) return 'Black Rose Collection';
		if (path.indexOf('love-hurts') !== -1) return 'Love Hurts Collection';
		if (path.indexOf('signature')  !== -1) return 'Signature Collection';
		return '';
	}

	/* ==================================================
	   1. Behavioral Tracking & Scoring
	   ================================================== */

	var behavior = {
		sessionStart: Date.now(),
		pageViews:    {},    // { path: count }
		heatScores:   {},    // { sku: number }
		events:       [],    // { name, data, ts }
		scrollDepth:  0,     // 0–100
		timeOnPage:   0,     // seconds
	};

	function loadBehavior() {
		try {
			var stored = sessionStorage.getItem(CFG.storageKey);
			if (stored) {
				var parsed = JSON.parse(stored);
				behavior.pageViews  = parsed.pageViews  || {};
				behavior.heatScores = parsed.heatScores || {};
				behavior.events     = parsed.events     || [];
				behavior.scrollDepth = parsed.scrollDepth || 0;
			}
		} catch (e) { /* sessionStorage unavailable or corrupt */ }
	}

	function saveBehavior() {
		try {
			// Cap events array to prevent unbounded growth
			if (behavior.events.length > 200) {
				behavior.events = behavior.events.slice(-200);
			}
			sessionStorage.setItem(CFG.storageKey, JSON.stringify({
				sessionStart: behavior.sessionStart,
				pageViews:    behavior.pageViews,
				heatScores:   behavior.heatScores,
				events:       behavior.events,
				scrollDepth:  behavior.scrollDepth,
				timeOnPage:   behavior.timeOnPage,
			}));
		} catch (e) { /* quota exceeded or unavailable */ }
	}

	function addHeat(sku, type) {
		if (!sku) return;
		var weight = CFG.heatWeights[type] || 0;
		behavior.heatScores[sku] = (behavior.heatScores[sku] || 0) + weight;
		saveBehavior();
	}

	function trackEvent(name, data) {
		var evt = {
			name: name,
			data: data || {},
			ts:   Date.now(),
		};
		behavior.events.push(evt);
		saveBehavior();

		// Forward to CIE if present
		try {
			window.dispatchEvent(new CustomEvent('ape:event', { detail: evt }));
		} catch (e) { /* old browsers */ }
	}

	function getIntentSignal() {
		var totalHeat = 0;
		Object.keys(behavior.heatScores).forEach(function (sku) {
			totalHeat += behavior.heatScores[sku];
		});
		if (totalHeat >= CFG.intentThresholds.ready_to_buy) return 'ready_to_buy';
		if (totalHeat >= CFG.intentThresholds.interested)   return 'interested';
		return 'browsing';
	}

	function getTopSKUs(limit) {
		var entries = Object.keys(behavior.heatScores).map(function (sku) {
			return { sku: sku, score: behavior.heatScores[sku] };
		});
		entries.sort(function (a, b) { return b.score - a.score; });
		return entries.slice(0, limit || CFG.maxRecommendations).map(function (e) {
			return e.sku;
		});
	}

	/* --- Page view tracking --- */

	function trackPageView() {
		var path = window.location.pathname;
		behavior.pageViews[path] = (behavior.pageViews[path] || 0) + 1;

		// If on a product-context page, add view heat for visible products
		catalogue.forEach(function (p) {
			if (path.indexOf(p.sku) !== -1) {
				addHeat(p.sku, 'view');
			}
		});

		saveBehavior();
	}

	/* --- Scroll depth tracking --- */

	function initScrollTracking() {
		var onScroll = throttle(function () {
			var scrollTop    = window.pageYOffset || document.documentElement.scrollTop;
			var docHeight    = document.documentElement.scrollHeight - document.documentElement.clientHeight;
			var depth        = docHeight > 0 ? Math.round((scrollTop / docHeight) * 100) : 0;
			behavior.scrollDepth = Math.max(behavior.scrollDepth, depth);
		}, 250);

		window.addEventListener('scroll', onScroll, { passive: true });
	}

	/* --- Time on page tracking --- */

	function initTimeTracking() {
		setInterval(function () {
			behavior.timeOnPage = Math.round((Date.now() - behavior.sessionStart) / 1000);
			saveBehavior();
		}, 5000);
	}

	/* --- Product interaction tracking --- */

	function initInteractionTracking() {
		// Hover tracking on hotspots and product cards
		$$('.hotspot, .collection-product-card, .product-card').forEach(function (el) {
			var sku = el.dataset.productId || null;
			var hoverTimer = null;

			el.addEventListener('mouseenter', function () {
				hoverTimer = setTimeout(function () {
					if (sku) addHeat(sku, 'hover');
				}, 500); // 500ms dwell = intentional hover
			});

			el.addEventListener('mouseleave', function () {
				if (hoverTimer) clearTimeout(hoverTimer);
			});
		});

		// Panel open tracking — listen for product-panel class changes
		var panelEl = $('.product-panel');
		if (panelEl) {
			var observer = new MutationObserver(function (mutations) {
				mutations.forEach(function (m) {
					if (m.type !== 'attributes' || m.attributeName !== 'class') return;
					if (panelEl.classList.contains('open')) {
						// Find the SKU from the panel's content
						var nameEl = panelEl.querySelector('.product-panel-name');
						if (nameEl) {
							var name = nameEl.textContent.trim();
							var match = catalogue.find(function (p) {
								return p.name === name;
							});
							if (match) {
								addHeat(match.sku, 'panel_open');
								trackEvent('panel_open', { sku: match.sku });
								addToRecentlyViewed(match.sku);
								checkBundleSuggestion(match.collection);
							}
						}
					}
				});
			});
			observer.observe(panelEl, { attributes: true });
		}

		// Add-to-cart tracking
		document.addEventListener('click', function (e) {
			var btn = e.target.closest('.js-add-to-cart, .add-to-cart-btn, [data-action="add-to-cart"]');
			if (!btn) return;
			var card = btn.closest('[data-product-id]');
			if (card && card.dataset.productId) {
				addHeat(card.dataset.productId, 'add_to_cart');
				trackEvent('add_to_cart', { sku: card.dataset.productId });
			}
		});

		// CIE event forwarding
		window.addEventListener('cie:event', function (e) {
			if (e.detail && e.detail.event) {
				trackEvent('cie_' + e.detail.event, e.detail.data);
			}
		});
	}

	/* ==================================================
	   2. Personalized "For You" Recommendations Drawer
	   ================================================== */

	var drawerEl       = null;
	var drawerOverlay  = null;
	var drawerTrigger  = null;
	var drawerOpen     = false;
	var triggerVisible = false;

	function buildDrawer() {
		// Overlay backdrop
		drawerOverlay = createElement('div', 'ape-drawer-overlay', {
			'aria-hidden': 'true',
		});

		// Drawer container
		drawerEl = createElement('div', 'ape-drawer', {
			'role':        'dialog',
			'aria-label':  'Your personalized picks',
			'aria-hidden': 'true',
		});

		drawerEl.innerHTML =
			'<div class="ape-drawer__header">' +
				'<h2 class="ape-drawer__title">Your Picks</h2>' +
				'<button class="ape-drawer__close" type="button" aria-label="Close recommendations">' +
					'<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
						'<line x1="18" y1="6" x2="6" y2="18"></line>' +
						'<line x1="6" y1="6" x2="18" y2="18"></line>' +
					'</svg>' +
				'</button>' +
			'</div>' +
			'<p class="ape-drawer__subtitle">Curated for you based on what caught your eye</p>' +
			'<div class="ape-drawer__cards"></div>' +
			'<div class="ape-drawer__empty">' +
				'<p>Keep exploring — your personalized picks will appear here.</p>' +
			'</div>';

		document.body.appendChild(drawerOverlay);
		document.body.appendChild(drawerEl);

		// Close button
		drawerEl.querySelector('.ape-drawer__close').addEventListener('click', closeDrawer);

		// Click-outside
		drawerOverlay.addEventListener('click', closeDrawer);

		// Escape key
		document.addEventListener('keydown', function (e) {
			if (e.key === 'Escape' && drawerOpen) closeDrawer();
		});
	}

	function buildDrawerTrigger() {
		drawerTrigger = createElement('button', 'ape-trigger', {
			'type':       'button',
			'aria-label': 'Open your personalized picks',
		});
		drawerTrigger.innerHTML =
			'<svg class="ape-trigger__icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
				'<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>' +
			'</svg>' +
			'<span class="ape-trigger__label">Your Picks</span>';

		drawerTrigger.addEventListener('click', function () {
			if (drawerOpen) {
				closeDrawer();
			} else {
				openDrawer();
			}
		});

		document.body.appendChild(drawerTrigger);
	}

	function showTrigger() {
		if (triggerVisible) return;
		triggerVisible = true;
		if (drawerTrigger) drawerTrigger.classList.add('ape-trigger--visible');
	}

	function populateDrawer() {
		var cardsContainer = drawerEl.querySelector('.ape-drawer__cards');
		var emptyState     = drawerEl.querySelector('.ape-drawer__empty');
		cardsContainer.innerHTML = '';

		var topSKUs = getTopSKUs(CFG.maxRecommendations);
		var products = topSKUs
			.map(function (sku) { return catalogueBySku[sku]; })
			.filter(Boolean);

		if (products.length === 0) {
			cardsContainer.style.display = 'none';
			emptyState.style.display = '';
			return;
		}

		cardsContainer.style.display = '';
		emptyState.style.display = 'none';

		products.forEach(function (product, i) {
			var card = createElement('a', 'ape-rec-card', {
				'href':       product.url,
				'aria-label': 'View ' + product.name,
			});

			var initial = product.name ? product.name.charAt(0).toUpperCase() : '?';
			var imageHtml = product.image
				? '<img class="ape-rec-card__image" src="' + escapeAttr(product.image) + '" alt="' + escapeAttr(product.name) + '" loading="lazy" />'
				: '<div class="ape-rec-card__placeholder">' + escapeHtml(initial) + '</div>';

			var collectionBadge = product.collection
				? '<span class="ape-rec-card__badge">' + escapeHtml(product.collection) + '</span>'
				: '';

			card.innerHTML =
				'<div class="ape-rec-card__visual">' +
					imageHtml +
				'</div>' +
				'<div class="ape-rec-card__info">' +
					'<h3 class="ape-rec-card__name">' + escapeHtml(product.name) + '</h3>' +
					'<p class="ape-rec-card__price">' + escapeHtml(product.price) + '</p>' +
					collectionBadge +
				'</div>' +
				'<span class="ape-rec-card__action">View</span>';

			if (!prefersReducedMotion()) {
				card.style.animationDelay = (i * 0.08) + 's';
			}

			card.addEventListener('click', function () {
				trackEvent('recommendation_clicked', { sku: product.sku, position: i });
			});

			cardsContainer.appendChild(card);
		});
	}

	function openDrawer() {
		if (drawerOpen) return;
		drawerOpen = true;

		populateDrawer();

		drawerEl.classList.add('ape-drawer--open');
		drawerOverlay.classList.add('ape-drawer-overlay--visible');
		drawerEl.setAttribute('aria-hidden', 'false');
		drawerOverlay.setAttribute('aria-hidden', 'false');

		// Focus the close button
		var closeBtn = drawerEl.querySelector('.ape-drawer__close');
		if (closeBtn) closeBtn.focus();

		trackEvent('drawer_opened', { intent: getIntentSignal() });
	}

	function closeDrawer() {
		if (!drawerOpen) return;
		drawerOpen = false;

		drawerEl.classList.remove('ape-drawer--open');
		drawerOverlay.classList.remove('ape-drawer-overlay--visible');
		drawerEl.setAttribute('aria-hidden', 'true');
		drawerOverlay.setAttribute('aria-hidden', 'true');

		// Return focus to trigger
		if (drawerTrigger) drawerTrigger.focus();
	}

	function initDrawerTriggers() {
		var timeTriggered  = false;
		var scrollTriggered = false;

		// Time-based trigger
		setTimeout(function () {
			timeTriggered = true;
			showTrigger();
		}, CFG.drawerTriggerTime);

		// Scroll-based trigger
		var checkScroll = throttle(function () {
			if (scrollTriggered) return;
			var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
			var docHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
			if (docHeight > 0 && (scrollTop / docHeight) >= CFG.drawerTriggerScroll) {
				scrollTriggered = true;
				showTrigger();
			}
		}, 300);

		window.addEventListener('scroll', checkScroll, { passive: true });
	}

	/* ==================================================
	   3. Ambient Mood Engine (immersive pages only)
	   ================================================== */

	var currentMood = null;

	var MOOD_MAP = {
		'black rose':  'mood-gothic',
		'blackrose':   'mood-gothic',
		'love hurts':  'mood-romantic',
		'lovehurts':   'mood-romantic',
		'signature':   'mood-golden',
	};

	var ALL_MOODS = ['mood-gothic', 'mood-romantic', 'mood-golden'];

	function detectCollectionFromPath() {
		var path = window.location.pathname.toLowerCase();
		if (path.indexOf('black-rose') !== -1) return 'mood-gothic';
		if (path.indexOf('love-hurts') !== -1) return 'mood-romantic';
		if (path.indexOf('signature')  !== -1) return 'mood-golden';
		return null;
	}

	function detectCollectionFromActiveLayer() {
		var activeLayer = document.querySelector('.scene-layer.active');
		if (!activeLayer) return null;

		// Check the hotspot container for the active room
		var roomIndex = Array.from(document.querySelectorAll('.scene-layer')).indexOf(activeLayer);
		var hotspotContainers = $$('.hotspot-container');
		var container = hotspotContainers[roomIndex];
		if (!container) return null;

		// Check first hotspot's collection
		var hotspot = container.querySelector('.hotspot[data-product-collection]');
		if (!hotspot) return null;

		var collection = (hotspot.dataset.productCollection || '').toLowerCase();
		var keys = Object.keys(MOOD_MAP);
		for (var i = 0; i < keys.length; i++) {
			if (collection.indexOf(keys[i]) !== -1) return MOOD_MAP[keys[i]];
		}
		return null;
	}

	function setMood(moodClass) {
		if (!moodClass || moodClass === currentMood) return;

		var reducedMotion = prefersReducedMotion();

		// Remove all mood classes
		ALL_MOODS.forEach(function (mood) {
			document.body.classList.remove(mood);
		});

		if (!reducedMotion) {
			// Use a transitioning class for smooth crossfade
			document.body.classList.add('ape-mood-transitioning');
		}

		document.body.classList.add(moodClass);
		currentMood = moodClass;

		if (!reducedMotion) {
			setTimeout(function () {
				document.body.classList.remove('ape-mood-transitioning');
			}, CFG.moodTransitionMs);
		}

		trackEvent('mood_changed', { mood: moodClass });
	}

	function initMoodEngine() {
		// Only activate on immersive pages
		var isImmersive = !!document.querySelector('.immersive-scene');
		var isCollection = !!document.querySelector('.collection-product-card');

		if (isImmersive) {
			// Set initial mood from page URL
			var initialMood = detectCollectionFromPath();
			if (initialMood) setMood(initialMood);

			// Listen for CIE events (room changes, etc.)
			window.addEventListener('cie:event', function (e) {
				if (e.detail && e.detail.event === 'room_changed') {
					// Re-detect mood from new active layer
					setTimeout(function () {
						var mood = detectCollectionFromActiveLayer() || detectCollectionFromPath();
						if (mood) setMood(mood);
					}, 100);
				}
			});

			// Watch for active scene-layer changes via MutationObserver
			var viewport = document.querySelector('.scene-viewport');
			if (viewport) {
				var layerObserver = new MutationObserver(function () {
					var mood = detectCollectionFromActiveLayer();
					if (mood) setMood(mood);
				});

				$$('.scene-layer', viewport).forEach(function (layer) {
					layerObserver.observe(layer, { attributes: true, attributeFilter: ['class'] });
				});
			}
		}

		if (isCollection) {
			// Set mood from collection page path
			var collectionMood = detectCollectionFromPath();
			if (collectionMood) setMood(collectionMood);

			// Increase saturation on deeper scroll
			initScrollSaturation();
		}
	}

	function initScrollSaturation() {
		var onScroll = throttle(function () {
			var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
			var docHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
			var depth = docHeight > 0 ? scrollTop / docHeight : 0;

			// Map depth 0-1 to saturation intensity 0-30 (percentage boost)
			var intensity = Math.round(Math.min(depth, 1) * 30);
			document.body.style.setProperty('--ape-saturation-boost', intensity + '%');
		}, 200);

		window.addEventListener('scroll', onScroll, { passive: true });
	}

	/* ==================================================
	   4. Smart Bundle Suggestions
	   ================================================== */

	var collectionInteractions = {};  // { collection: Set<sku> }
	var bundleToast = null;

	function checkBundleSuggestion(collection) {
		if (!collection) return;

		// Check if already dismissed for this collection
		var dismissed = loadBundleDismissals();
		var normalizedCollection = collection.toLowerCase().replace(/\s+collection$/i, '').trim();
		if (dismissed[normalizedCollection]) return;

		// Track interaction
		if (!collectionInteractions[normalizedCollection]) {
			collectionInteractions[normalizedCollection] = {};
		}

		// Use the product data from the most recent event
		var latestEvents = behavior.events.slice(-5);
		latestEvents.forEach(function (evt) {
			if (evt.data && evt.data.sku) {
				var product = catalogueBySku[evt.data.sku];
				if (product) {
					var prodCol = product.collection.toLowerCase().replace(/\s+collection$/i, '').trim();
					if (!collectionInteractions[prodCol]) {
						collectionInteractions[prodCol] = {};
					}
					collectionInteractions[prodCol][evt.data.sku] = true;
				}
			}
		});

		// Count unique products interacted with in this collection
		var uniqueCount = Object.keys(collectionInteractions[normalizedCollection] || {}).length;

		if (uniqueCount >= CFG.bundleThreshold) {
			showBundleToast(normalizedCollection);
		}
	}

	function loadBundleDismissals() {
		try {
			var stored = sessionStorage.getItem(CFG.bundleDismissKey);
			return stored ? JSON.parse(stored) : {};
		} catch (e) { return {}; }
	}

	function saveBundleDismissal(collection) {
		try {
			var dismissed = loadBundleDismissals();
			dismissed[collection] = true;
			sessionStorage.setItem(CFG.bundleDismissKey, JSON.stringify(dismissed));
		} catch (e) { /* unavailable */ }
	}

	function showBundleToast(collectionKey) {
		if (bundleToast) return; // already showing

		var displayName = collectionKey.charAt(0).toUpperCase() + collectionKey.slice(1);

		bundleToast = createElement('div', 'ape-bundle-toast', {
			'role':       'status',
			'aria-live':  'polite',
		});

		bundleToast.innerHTML =
			'<div class="ape-bundle-toast__icon">' +
				'<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
					'<path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path>' +
					'<line x1="7" y1="7" x2="7.01" y2="7"></line>' +
				'</svg>' +
			'</div>' +
			'<div class="ape-bundle-toast__content">' +
				'<strong>Complete your ' + escapeHtml(displayName) + ' look</strong>' +
				'<span>Bundle ' + CFG.bundleMinForOffer + '+ items for free shipping</span>' +
			'</div>' +
			'<button class="ape-bundle-toast__close" type="button" aria-label="Dismiss">&times;</button>';

		document.body.appendChild(bundleToast);

		// Animate in
		requestAnimationFrame(function () {
			requestAnimationFrame(function () {
				bundleToast.classList.add('ape-bundle-toast--visible');
			});
		});

		// Close handler
		bundleToast.querySelector('.ape-bundle-toast__close').addEventListener('click', function () {
			dismissBundleToast(collectionKey);
		});

		trackEvent('bundle_suggestion_shown', { collection: collectionKey });

		// Auto-dismiss after 12 seconds
		setTimeout(function () {
			dismissBundleToast(collectionKey);
		}, 12000);
	}

	function dismissBundleToast(collectionKey) {
		if (!bundleToast) return;

		bundleToast.classList.remove('ape-bundle-toast--visible');
		saveBundleDismissal(collectionKey);
		trackEvent('bundle_suggestion_dismissed', { collection: collectionKey });

		setTimeout(function () {
			if (bundleToast && bundleToast.parentNode) {
				bundleToast.parentNode.removeChild(bundleToast);
			}
			bundleToast = null;
		}, 400);
	}

	/* ==================================================
	   5. Recently Viewed Strip
	   ================================================== */

	var recentStrip = null;

	function loadRecentlyViewed() {
		try {
			var stored = sessionStorage.getItem(CFG.recentKey);
			return stored ? JSON.parse(stored) : [];
		} catch (e) { return []; }
	}

	function saveRecentlyViewed(skus) {
		try {
			sessionStorage.setItem(CFG.recentKey, JSON.stringify(skus));
		} catch (e) { /* unavailable */ }
	}

	function addToRecentlyViewed(sku) {
		if (!sku) return;
		var recent = loadRecentlyViewed();

		// Remove if already present (move to front)
		recent = recent.filter(function (s) { return s !== sku; });
		recent.unshift(sku);

		// Cap at max
		if (recent.length > CFG.maxRecentlyViewed) {
			recent = recent.slice(0, CFG.maxRecentlyViewed);
		}

		saveRecentlyViewed(recent);
		renderRecentStrip();
	}

	function buildRecentStrip() {
		recentStrip = createElement('div', 'ape-recent-strip', {
			'role':       'navigation',
			'aria-label': 'Recently viewed products',
		});

		recentStrip.innerHTML =
			'<span class="ape-recent-strip__label">Recently Viewed</span>' +
			'<div class="ape-recent-strip__scroll"></div>';

		document.body.appendChild(recentStrip);
	}

	function renderRecentStrip() {
		if (!recentStrip) return;

		var recent = loadRecentlyViewed();
		var scrollContainer = recentStrip.querySelector('.ape-recent-strip__scroll');
		scrollContainer.innerHTML = '';

		// Hide if fewer than 2
		if (recent.length < 2) {
			recentStrip.classList.remove('ape-recent-strip--visible');
			return;
		}

		recent.forEach(function (sku) {
			var product = catalogueBySku[sku];
			if (!product) return;

			var thumb = createElement('a', 'ape-recent-thumb', {
				'href':       product.url,
				'title':      product.name,
				'aria-label': product.name,
			});

			if (product.image) {
				var img = createElement('img', 'ape-recent-thumb__img', {
					'src':     product.image,
					'alt':     product.name,
					'loading': 'lazy',
				});
				thumb.appendChild(img);
			} else {
				var initial = createElement('span', 'ape-recent-thumb__initial', {
					'textContent': product.name ? product.name.charAt(0).toUpperCase() : '?',
				});
				thumb.appendChild(initial);
			}

			thumb.addEventListener('click', function () {
				trackEvent('recently_viewed_clicked', { sku: sku });
			});

			scrollContainer.appendChild(thumb);
		});

		recentStrip.classList.add('ape-recent-strip--visible');
	}

	/* ==================================================
	   HTML Escape Utilities
	   ================================================== */

	function escapeHtml(str) {
		if (!str) return '';
		return str
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;')
			.replace(/"/g, '&quot;');
	}

	function escapeAttr(str) {
		return escapeHtml(str);
	}

	/* ==================================================
	   Inject Styles
	   ================================================== */

	function injectStyles() {
		var style = document.createElement('style');
		style.setAttribute('data-ape', 'true');
		style.textContent =
			/* ----------------------------------------
			   Reduced Motion
			   ---------------------------------------- */
			'@media (prefers-reduced-motion: reduce) {' +
				'.ape-drawer,' +
				'.ape-drawer-overlay,' +
				'.ape-trigger,' +
				'.ape-rec-card,' +
				'.ape-bundle-toast,' +
				'.ape-recent-strip,' +
				'.ape-mood-transitioning {' +
					'transition: none !important;' +
					'animation: none !important;' +
				'}' +
			'}' +

			/* ----------------------------------------
			   Mood Engine — ambient overlays
			   ---------------------------------------- */
			'body.mood-gothic::after,' +
			'body.mood-romantic::after,' +
			'body.mood-golden::after {' +
				'content: "";' +
				'position: fixed;' +
				'inset: 0;' +
				'pointer-events: none;' +
				'z-index: 1;' +
				'opacity: 0.12;' +
				'transition: opacity ' + CFG.moodTransitionMs + 'ms ease, background ' + CFG.moodTransitionMs + 'ms ease;' +
			'}' +
			'body.ape-mood-transitioning::after {' +
				'opacity: 0;' +
			'}' +
			'body.mood-gothic::after {' +
				'background: radial-gradient(ellipse at 50% 30%, rgba(70,100,180,0.25) 0%, rgba(20,20,50,0.15) 60%, transparent 100%);' +
			'}' +
			'body.mood-romantic::after {' +
				'background: radial-gradient(ellipse at 50% 60%, rgba(220,20,60,0.18) 0%, rgba(180,50,70,0.1) 50%, transparent 100%);' +
			'}' +
			'body.mood-golden::after {' +
				'background: radial-gradient(ellipse at 50% 40%, rgba(212,175,55,0.2) 0%, rgba(183,110,121,0.12) 50%, transparent 100%);' +
			'}' +

			/* Scroll saturation variable */
			'body {' +
				'--ape-saturation-boost: 0%;' +
				'filter: saturate(calc(100% + var(--ape-saturation-boost)));' +
			'}' +

			/* ----------------------------------------
			   "Your Picks" Trigger Button
			   ---------------------------------------- */
			'.ape-trigger {' +
				'position: fixed;' +
				'right: 20px;' +
				'bottom: 100px;' +
				'z-index: 9998;' +
				'display: flex;' +
				'align-items: center;' +
				'gap: 8px;' +
				'padding: 12px 20px;' +
				'border: none;' +
				'border-radius: 50px;' +
				'background: linear-gradient(135deg, #B76E79 0%, #D4AF37 100%);' +
				'color: #fff;' +
				'font-family: inherit;' +
				'font-size: 14px;' +
				'font-weight: 600;' +
				'letter-spacing: 0.03em;' +
				'cursor: pointer;' +
				'box-shadow: 0 4px 20px rgba(183,110,121,0.35), 0 0 0 0 rgba(183,110,121,0);' +
				'opacity: 0;' +
				'transform: translateY(20px);' +
				'transition: opacity 0.5s ease, transform 0.5s ease, box-shadow 0.3s ease;' +
				'pointer-events: none;' +
			'}' +
			'.ape-trigger--visible {' +
				'opacity: 1;' +
				'transform: translateY(0);' +
				'pointer-events: auto;' +
			'}' +
			'.ape-trigger:hover {' +
				'box-shadow: 0 6px 28px rgba(183,110,121,0.5), 0 0 0 3px rgba(212,175,55,0.2);' +
			'}' +
			'.ape-trigger:focus-visible {' +
				'outline: 2px solid #D4AF37;' +
				'outline-offset: 3px;' +
			'}' +
			'.ape-trigger__icon {' +
				'flex-shrink: 0;' +
			'}' +

			/* ----------------------------------------
			   Drawer Overlay
			   ---------------------------------------- */
			'.ape-drawer-overlay {' +
				'position: fixed;' +
				'inset: 0;' +
				'z-index: 10000;' +
				'background: rgba(0,0,0,0);' +
				'backdrop-filter: blur(0px);' +
				'-webkit-backdrop-filter: blur(0px);' +
				'transition: background 0.4s ease, backdrop-filter 0.4s ease, -webkit-backdrop-filter 0.4s ease;' +
				'pointer-events: none;' +
			'}' +
			'.ape-drawer-overlay--visible {' +
				'background: rgba(0,0,0,0.4);' +
				'backdrop-filter: blur(4px);' +
				'-webkit-backdrop-filter: blur(4px);' +
				'pointer-events: auto;' +
			'}' +

			/* ----------------------------------------
			   Drawer Panel
			   ---------------------------------------- */
			'.ape-drawer {' +
				'position: fixed;' +
				'top: 0;' +
				'right: 0;' +
				'bottom: 0;' +
				'z-index: 10001;' +
				'width: ' + CFG.drawerWidthDesktop + ';' +
				'max-width: 90vw;' +
				'background: rgba(18,18,22,0.92);' +
				'backdrop-filter: blur(24px) saturate(180%);' +
				'-webkit-backdrop-filter: blur(24px) saturate(180%);' +
				'border-left: 1px solid rgba(183,110,121,0.2);' +
				'transform: translateX(100%);' +
				'transition: transform 0.45s cubic-bezier(0.22,1,0.36,1);' +
				'overflow-y: auto;' +
				'overscroll-behavior: contain;' +
				'display: flex;' +
				'flex-direction: column;' +
				'padding: 0;' +
			'}' +
			'.ape-drawer--open {' +
				'transform: translateX(0);' +
			'}' +

			/* Mobile width */
			'@media (max-width: ' + (CFG.mobileBreakpoint - 1) + 'px) {' +
				'.ape-drawer {' +
					'width: ' + CFG.drawerWidthMobile + ';' +
				'}' +
			'}' +

			/* ----------------------------------------
			   Drawer Header
			   ---------------------------------------- */
			'.ape-drawer__header {' +
				'display: flex;' +
				'align-items: center;' +
				'justify-content: space-between;' +
				'padding: 24px 24px 0;' +
			'}' +
			'.ape-drawer__title {' +
				'margin: 0;' +
				'font-size: 20px;' +
				'font-weight: 700;' +
				'letter-spacing: 0.04em;' +
				'background: linear-gradient(135deg, #B76E79, #D4AF37);' +
				'-webkit-background-clip: text;' +
				'-webkit-text-fill-color: transparent;' +
				'background-clip: text;' +
			'}' +
			'.ape-drawer__close {' +
				'background: none;' +
				'border: 1px solid rgba(183,110,121,0.3);' +
				'border-radius: 50%;' +
				'width: 36px;' +
				'height: 36px;' +
				'display: flex;' +
				'align-items: center;' +
				'justify-content: center;' +
				'color: rgba(255,255,255,0.7);' +
				'cursor: pointer;' +
				'transition: border-color 0.2s ease, color 0.2s ease;' +
			'}' +
			'.ape-drawer__close:hover {' +
				'border-color: #B76E79;' +
				'color: #fff;' +
			'}' +
			'.ape-drawer__close:focus-visible {' +
				'outline: 2px solid #D4AF37;' +
				'outline-offset: 2px;' +
			'}' +
			'.ape-drawer__subtitle {' +
				'padding: 8px 24px 16px;' +
				'margin: 0;' +
				'font-size: 13px;' +
				'color: rgba(255,255,255,0.5);' +
				'letter-spacing: 0.02em;' +
			'}' +

			/* ----------------------------------------
			   Recommendation Cards
			   ---------------------------------------- */
			'.ape-drawer__cards {' +
				'padding: 0 24px 24px;' +
				'display: flex;' +
				'flex-direction: column;' +
				'gap: 12px;' +
			'}' +
			'.ape-drawer__empty {' +
				'padding: 48px 24px;' +
				'text-align: center;' +
				'color: rgba(255,255,255,0.4);' +
				'font-size: 14px;' +
			'}' +
			'.ape-rec-card {' +
				'display: flex;' +
				'align-items: center;' +
				'gap: 16px;' +
				'padding: 14px;' +
				'border-radius: 12px;' +
				'background: rgba(255,255,255,0.04);' +
				'border: 1px solid rgba(183,110,121,0.12);' +
				'text-decoration: none;' +
				'color: #fff;' +
				'transition: background 0.25s ease, border-color 0.25s ease, transform 0.25s ease;' +
				'animation: apeCardSlideIn 0.4s ease both;' +
			'}' +
			'.ape-rec-card:hover {' +
				'background: rgba(183,110,121,0.1);' +
				'border-color: rgba(183,110,121,0.35);' +
				'transform: translateX(-4px);' +
			'}' +
			'.ape-rec-card:focus-visible {' +
				'outline: 2px solid #D4AF37;' +
				'outline-offset: 2px;' +
			'}' +
			'@keyframes apeCardSlideIn {' +
				'from { opacity: 0; transform: translateX(20px); }' +
				'to { opacity: 1; transform: translateX(0); }' +
			'}' +
			'.ape-rec-card__visual {' +
				'flex-shrink: 0;' +
				'width: 64px;' +
				'height: 64px;' +
				'border-radius: 10px;' +
				'overflow: hidden;' +
				'background: rgba(183,110,121,0.15);' +
			'}' +
			'.ape-rec-card__image {' +
				'width: 100%;' +
				'height: 100%;' +
				'object-fit: cover;' +
			'}' +
			'.ape-rec-card__placeholder {' +
				'width: 100%;' +
				'height: 100%;' +
				'display: flex;' +
				'align-items: center;' +
				'justify-content: center;' +
				'font-size: 24px;' +
				'font-weight: 700;' +
				'color: #B76E79;' +
			'}' +
			'.ape-rec-card__info {' +
				'flex: 1;' +
				'min-width: 0;' +
			'}' +
			'.ape-rec-card__name {' +
				'margin: 0 0 4px;' +
				'font-size: 14px;' +
				'font-weight: 600;' +
				'white-space: nowrap;' +
				'overflow: hidden;' +
				'text-overflow: ellipsis;' +
			'}' +
			'.ape-rec-card__price {' +
				'margin: 0 0 6px;' +
				'font-size: 13px;' +
				'color: #D4AF37;' +
				'font-weight: 500;' +
			'}' +
			'.ape-rec-card__badge {' +
				'display: inline-block;' +
				'padding: 2px 8px;' +
				'font-size: 10px;' +
				'font-weight: 600;' +
				'letter-spacing: 0.06em;' +
				'text-transform: uppercase;' +
				'border-radius: 20px;' +
				'background: rgba(183,110,121,0.15);' +
				'color: #B76E79;' +
			'}' +
			'.ape-rec-card__action {' +
				'flex-shrink: 0;' +
				'font-size: 12px;' +
				'font-weight: 600;' +
				'text-transform: uppercase;' +
				'letter-spacing: 0.08em;' +
				'color: rgba(212,175,55,0.8);' +
				'transition: color 0.2s ease;' +
			'}' +
			'.ape-rec-card:hover .ape-rec-card__action {' +
				'color: #D4AF37;' +
			'}' +

			/* ----------------------------------------
			   Bundle Toast
			   ---------------------------------------- */
			'.ape-bundle-toast {' +
				'position: fixed;' +
				'bottom: 90px;' +
				'left: 50%;' +
				'transform: translateX(-50%) translateY(20px);' +
				'z-index: 9997;' +
				'display: flex;' +
				'align-items: center;' +
				'gap: 12px;' +
				'padding: 14px 20px;' +
				'border-radius: 14px;' +
				'background: rgba(18,18,22,0.92);' +
				'backdrop-filter: blur(16px) saturate(150%);' +
				'-webkit-backdrop-filter: blur(16px) saturate(150%);' +
				'border: 1px solid rgba(183,110,121,0.25);' +
				'box-shadow: 0 8px 32px rgba(0,0,0,0.3);' +
				'color: #fff;' +
				'font-size: 13px;' +
				'max-width: calc(100vw - 40px);' +
				'opacity: 0;' +
				'transition: opacity 0.4s ease, transform 0.4s ease;' +
				'pointer-events: none;' +
			'}' +
			'.ape-bundle-toast--visible {' +
				'opacity: 1;' +
				'transform: translateX(-50%) translateY(0);' +
				'pointer-events: auto;' +
			'}' +
			'.ape-bundle-toast__icon {' +
				'flex-shrink: 0;' +
				'color: #D4AF37;' +
			'}' +
			'.ape-bundle-toast__content {' +
				'display: flex;' +
				'flex-direction: column;' +
				'gap: 2px;' +
			'}' +
			'.ape-bundle-toast__content strong {' +
				'font-size: 14px;' +
				'background: linear-gradient(135deg, #B76E79, #D4AF37);' +
				'-webkit-background-clip: text;' +
				'-webkit-text-fill-color: transparent;' +
				'background-clip: text;' +
			'}' +
			'.ape-bundle-toast__content span {' +
				'color: rgba(255,255,255,0.6);' +
			'}' +
			'.ape-bundle-toast__close {' +
				'flex-shrink: 0;' +
				'background: none;' +
				'border: none;' +
				'color: rgba(255,255,255,0.4);' +
				'font-size: 20px;' +
				'cursor: pointer;' +
				'padding: 0 0 0 8px;' +
				'line-height: 1;' +
				'transition: color 0.2s ease;' +
			'}' +
			'.ape-bundle-toast__close:hover {' +
				'color: #fff;' +
			'}' +
			'.ape-bundle-toast__close:focus-visible {' +
				'outline: 2px solid #D4AF37;' +
				'outline-offset: 2px;' +
			'}' +

			/* ----------------------------------------
			   Recently Viewed Strip
			   ---------------------------------------- */
			'.ape-recent-strip {' +
				'position: fixed;' +
				'bottom: 0;' +
				'left: 0;' +
				'right: 0;' +
				'z-index: 9996;' +
				'display: flex;' +
				'align-items: center;' +
				'gap: 12px;' +
				'padding: 8px 16px;' +
				'background: rgba(12,12,16,0.94);' +
				'backdrop-filter: blur(12px);' +
				'-webkit-backdrop-filter: blur(12px);' +
				'border-top: 1px solid rgba(183,110,121,0.15);' +
				'transform: translateY(100%);' +
				'transition: transform 0.4s cubic-bezier(0.22,1,0.36,1);' +
			'}' +
			'.ape-recent-strip--visible {' +
				'transform: translateY(0);' +
			'}' +
			'.ape-recent-strip__label {' +
				'flex-shrink: 0;' +
				'font-size: 11px;' +
				'font-weight: 600;' +
				'text-transform: uppercase;' +
				'letter-spacing: 0.08em;' +
				'color: rgba(183,110,121,0.6);' +
			'}' +
			'.ape-recent-strip__scroll {' +
				'display: flex;' +
				'gap: 10px;' +
				'overflow-x: auto;' +
				'overflow-y: hidden;' +
				'-webkit-overflow-scrolling: touch;' +
				'scrollbar-width: none;' +
				'padding: 4px 0;' +
			'}' +
			'.ape-recent-strip__scroll::-webkit-scrollbar { display: none; }' +
			'.ape-recent-thumb {' +
				'flex-shrink: 0;' +
				'width: 48px;' +
				'height: 48px;' +
				'border-radius: 50%;' +
				'overflow: hidden;' +
				'background: rgba(183,110,121,0.12);' +
				'border: 2px solid rgba(183,110,121,0.2);' +
				'transition: border-color 0.2s ease, transform 0.2s ease;' +
				'text-decoration: none;' +
				'display: flex;' +
				'align-items: center;' +
				'justify-content: center;' +
			'}' +
			'.ape-recent-thumb:hover {' +
				'border-color: #B76E79;' +
				'transform: scale(1.1);' +
			'}' +
			'.ape-recent-thumb:focus-visible {' +
				'outline: 2px solid #D4AF37;' +
				'outline-offset: 2px;' +
			'}' +
			'.ape-recent-thumb__img {' +
				'width: 100%;' +
				'height: 100%;' +
				'object-fit: cover;' +
			'}' +
			'.ape-recent-thumb__initial {' +
				'font-size: 18px;' +
				'font-weight: 700;' +
				'color: #B76E79;' +
			'}' +

			/* Ensure strip does not overlap floating CTA */
			'.ape-recent-strip--visible ~ .floating-cta,' +
			'.ape-recent-strip--visible ~ .sticky-cta-bar {' +
				'bottom: 66px;' +
			'}' +

			'';

		document.head.appendChild(style);
	}

	/* ==================================================
	   Public API
	   ================================================== */

	window.SkyyRoseAPE = {
		/**
		 * Returns the full behavior data object.
		 * @return {Object}
		 */
		getBehavior: function () {
			return {
				sessionStart: behavior.sessionStart,
				pageViews:    Object.assign({}, behavior.pageViews),
				heatScores:   Object.assign({}, behavior.heatScores),
				scrollDepth:  behavior.scrollDepth,
				timeOnPage:   behavior.timeOnPage,
				eventCount:   behavior.events.length,
			};
		},

		/**
		 * Returns the current intent signal based on cumulative heat score.
		 * @return {string} 'browsing' | 'interested' | 'ready_to_buy'
		 */
		getIntentSignal: function () {
			return getIntentSignal();
		},

		/**
		 * Returns top product SKUs sorted by heat score.
		 * @param  {number} [limit=4]
		 * @return {string[]}
		 */
		getRecommendations: function (limit) {
			return getTopSKUs(limit || CFG.maxRecommendations);
		},

		/**
		 * Manual event tracking hook for external scripts.
		 * @param {string} name
		 * @param {Object} [data]
		 */
		trackEvent: function (name, data) {
			trackEvent(name, data);
		},
	};

	/* ==================================================
	   Init
	   ================================================== */

	function init() {
		// Don't run on admin pages
		if (document.body.classList.contains('wp-admin')) return;

		// Inject styles
		injectStyles();

		// Load previous session behavior
		loadBehavior();

		// Harvest product data from DOM
		harvestCatalogue();

		// Track this page view
		trackPageView();

		// Also add heat for products visible on this page
		catalogue.forEach(function (p) {
			addHeat(p.sku, 'view');
		});

		// Module 1: Start tracking
		initScrollTracking();
		initTimeTracking();
		initInteractionTracking();

		// Module 2: Recommendation drawer
		buildDrawerTrigger();
		buildDrawer();
		initDrawerTriggers();

		// Module 3: Ambient mood engine
		initMoodEngine();

		// Module 4: Bundle suggestion (passive — triggered by interactions)
		// No explicit init needed; checkBundleSuggestion() is called by interaction tracking

		// Module 5: Recently viewed strip
		buildRecentStrip();
		renderRecentStrip();

		// Add currently visible products to recently viewed
		// (only on pages with a single/focused product)
		var singleProductId = document.body.dataset.productId;
		if (singleProductId) {
			addToRecentlyViewed(singleProductId);
		}

		trackEvent('ape_loaded', {
			catalogue_size: catalogue.length,
			intent: getIntentSignal(),
		});
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}
})();
