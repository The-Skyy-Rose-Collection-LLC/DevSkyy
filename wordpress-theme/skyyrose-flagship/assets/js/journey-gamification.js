/**
 * Journey Gamification Engine
 *
 * Tracks room exploration on immersive pages, rewards users who
 * complete the full journey, renders achievement badges on static
 * collection pages, and populates cross-sell recommendation strips
 * on product-centric pages.
 *
 * No external dependencies. Pure vanilla JS, IIFE-wrapped, strict mode.
 *
 * Sections:
 *   1. Room Exploration Tracker (immersive pages)
 *   2. Journey Progress Pill UI (immersive pages)
 *   3. Reward Reveal Modal (immersive pages, on completion)
 *   4. Achievement Badge Renderer (collection / static pages)
 *   5. Cross-Sell Recommendation Strip (product-centric pages)
 *
 * Persistence: sessionStorage (per-tab, privacy-friendly)
 * Analytics:   window.SkyyRoseCIE.trackEvent() if available
 *
 * @package SkyyRose_Flagship
 * @since   3.8.0
 */

(function () {
	'use strict';

	/* --------------------------------------------------
	   Configuration
	   -------------------------------------------------- */

	var CFG = {
		storagePrefix:    'skyyrose_journey_',
		rewardDelay:      1500,   // ms after full exploration before showing reward
		confettiCount:    40,     // particles in reward modal
		confettiDuration: 2800,   // ms for confetti animation
		promoCode:        'EXPLORE15',
		promoDiscount:    '15% off',
		preorderUrl:      '/pre-order',
	};

	/* --------------------------------------------------
	   Collection metadata — maps CSS class to collection
	   slug, display name, room names, and immersive URL.
	   -------------------------------------------------- */

	var COLLECTIONS = {
		'immersive-black-rose': {
			slug:          'black-rose',
			name:          'Black Rose',
			collectionUrl: '/collections/black-rose/',
			immersiveUrl:  '/immersive-black-rose/',
		},
		'immersive-love-hurts': {
			slug:          'love-hurts',
			name:          'Love Hurts',
			collectionUrl: '/collections/love-hurts/',
			immersiveUrl:  '/immersive-love-hurts/',
		},
		'immersive-signature': {
			slug:          'signature',
			name:          'Signature',
			collectionUrl: '/collections/signature/',
			immersiveUrl:  '/immersive-signature/',
		},
	};

	/* --------------------------------------------------
	   Cross-sell product catalog — hardcoded to match
	   the existing data-* attributes on hotspot beacons.
	   Each collection has its own product array.
	   -------------------------------------------------- */

	var PRODUCT_CATALOG = {
		'black-rose': [
			{ sku: 'br-001', name: 'BLACK Rose Crewneck',                         price: 'DRAFT', image: '', url: '/pre-order/#br-001' },
			{ sku: 'br-002', name: 'BLACK Rose Joggers',                          price: '$50',   image: '', url: '/pre-order/#br-002' },
			{ sku: 'br-003', name: 'BLACK is Beautiful Jersey',                   price: 'DRAFT', image: '', url: '/pre-order/#br-003' },
			{ sku: 'br-004', name: 'BLACK Rose Hoodie',                           price: '$40',   image: '', url: '/pre-order/#br-004' },
			{ sku: 'br-005', name: 'BLACK Rose Hoodie \u2014 Signature Edition',  price: '$65',   image: '', url: '/pre-order/#br-005' },
			{ sku: 'br-006', name: 'BLACK Rose Sherpa Jacket',                    price: '$95',   image: '', url: '/pre-order/#br-006' },
			{ sku: 'br-007', name: 'BLACK Rose \u00d7 Love Hurts Basketball Shorts', price: '$65', image: '', url: '/pre-order/#br-007' },
			{ sku: 'br-008', name: "Women's BLACK Rose Hooded Dress",             price: 'TBD',   image: '', url: '/pre-order/#br-008' },
		],
		'love-hurts': [
			{ sku: 'lh-001', name: 'The Fannie Pack',                  price: '$65',  image: '', url: '/pre-order/#lh-001' },
			{ sku: 'lh-002', name: 'Love Hurts Joggers (BLACK)',       price: '$95',  image: '', url: '/pre-order/#lh-002' },
			{ sku: 'lh-002b', name: 'Love Hurts Joggers (WHITE)',      price: '$95',  image: '', url: '/pre-order/#lh-002b' },
			{ sku: 'lh-003', name: 'Love Hurts Basketball Shorts',     price: '$75',  image: '', url: '/pre-order/#lh-003' },
			{ sku: 'lh-004', name: 'Love Hurts Varsity Jacket',        price: 'DRAFT', image: '', url: '/pre-order/#lh-004' },
		],
		'signature': [
			{ sku: 'sg-001-tee',    name: 'The Bay Set \u2014 Tee',       price: '$40',   image: '', url: '/pre-order/#sg-001-tee' },
			{ sku: 'sg-001-shorts',  name: 'The Bay Set \u2014 Shorts',    price: '$50',   image: '', url: '/pre-order/#sg-001-shorts' },
			{ sku: 'sg-002-tee',    name: 'Stay Golden Set \u2014 Tee',   price: '$40',   image: '', url: '/pre-order/#sg-002-tee' },
			{ sku: 'sg-002-shorts',  name: 'Stay Golden Set \u2014 Shorts', price: '$50',   image: '', url: '/pre-order/#sg-002-shorts' },
			{ sku: 'sg-003', name: 'The Signature Tee (Orchid)',           price: '$15',   image: '', url: '/pre-order/#sg-003' },
			{ sku: 'sg-005', name: 'Stay Golden Tee',                     price: '$40',   image: '', url: '/pre-order/#sg-005' },
			{ sku: 'sg-006', name: 'Mint & Lavender Hoodie',              price: '$45',   image: '', url: '/pre-order/#sg-006' },
			{ sku: 'sg-007', name: 'The Signature Beanie',                price: '$25',   image: '', url: '/pre-order/#sg-007' },
			{ sku: 'sg-009', name: 'The Sherpa Jacket',                   price: '$80',   image: '', url: '/pre-order/#sg-009' },
			{ sku: 'sg-010', name: 'The Bridge Series Shorts',            price: '$25',   image: '', url: '/pre-order/#sg-010' },
			{ sku: 'sg-011', name: 'Original Label Tee (White)',          price: 'DRAFT', image: '', url: '/pre-order/#sg-011' },
			{ sku: 'sg-012', name: 'Original Label Tee (Orchid)',         price: 'DRAFT', image: '', url: '/pre-order/#sg-012' },
		],
	};

	/* Particle colours for confetti (rose-gold palette) */
	var CONFETTI_COLOURS = [
		'#B76E79', '#D4AF37', '#E8C4C4', '#C49A6C',
		'#F5E6E8', '#9B5563', '#F0D5CE', '#DAA520',
	];

	/* --------------------------------------------------
	   Utility — sessionStorage safe wrapper
	   -------------------------------------------------- */

	function storageGet(key) {
		try {
			var raw = sessionStorage.getItem(key);
			return raw ? JSON.parse(raw) : null;
		} catch (_) {
			return null;
		}
	}

	function storageSet(key, value) {
		try {
			sessionStorage.setItem(key, JSON.stringify(value));
		} catch (_) {
			/* quota exceeded — degrade gracefully */
		}
	}

	/* --------------------------------------------------
	   Utility — analytics bridge
	   -------------------------------------------------- */

	function trackEvent(eventName, data) {
		if (window.SkyyRoseCIE && typeof window.SkyyRoseCIE.trackEvent === 'function') {
			window.SkyyRoseCIE.trackEvent(eventName, data || {});
		}
	}

	/* --------------------------------------------------
	   Utility — detect active collection from the scene
	   -------------------------------------------------- */

	function detectCollection() {
		var scene = document.querySelector('.immersive-scene');
		if (!scene) return null;

		var keys = Object.keys(COLLECTIONS);
		for (var i = 0; i < keys.length; i++) {
			if (scene.classList.contains(keys[i])) {
				return Object.assign({}, COLLECTIONS[keys[i]], { cssClass: keys[i] });
			}
		}
		return null;
	}

	/* --------------------------------------------------
	   Utility — detect collection slug on static pages
	   -------------------------------------------------- */

	function detectCollectionSlugFromPage() {
		var path = window.location.pathname.toLowerCase();

		// Match /collections/black-rose/ or template slug patterns
		if (path.indexOf('black-rose') !== -1) return 'black-rose';
		if (path.indexOf('love-hurts') !== -1) return 'love-hurts';
		if (path.indexOf('signature') !== -1)  return 'signature';

		// Fallback: check body class
		var body = document.body;
		if (body.classList.contains('page-template-template-collection-black-rose')) return 'black-rose';
		if (body.classList.contains('page-template-template-collection-love-hurts')) return 'love-hurts';
		if (body.classList.contains('page-template-template-collection-signature'))  return 'signature';

		return null;
	}

	/* ==================================================
	   1. ROOM EXPLORATION TRACKER
	   Watches .scene-layer.active changes via
	   MutationObserver and records visited rooms
	   in sessionStorage.
	   ================================================== */

	var explorationState = {
		collection: null,   // collection metadata object
		storageKey: null,   // sessionStorage key
		journeyData: null,  // { visited: { roomName: true }, totalRooms: N }
		pillEl: null,       // the progress pill DOM element
		rewardShown: false, // prevent double-fire
	};

	function initExplorationTracker() {
		var collection = detectCollection();
		if (!collection) return;

		var scene    = document.querySelector('.immersive-scene');
		var viewport = document.querySelector('.scene-viewport');
		if (!scene || !viewport) return;

		var layers = Array.from(viewport.querySelectorAll('.scene-layer'));
		var totalRooms = layers.length;
		if (totalRooms === 0) return;

		explorationState.collection = collection;
		explorationState.storageKey = CFG.storagePrefix + collection.slug;

		// Load or initialise journey data.
		var existing = storageGet(explorationState.storageKey);
		explorationState.journeyData = existing || { visited: {}, totalRooms: totalRooms };
		// Always update totalRooms in case the template added new rooms.
		explorationState.journeyData.totalRooms = totalRooms;

		// Record the initial active room.
		recordCurrentRoom(viewport);

		// Build the progress pill UI.
		buildProgressPill(scene);
		updateProgressPill();

		// Disconnect any previous observer to prevent multiple listeners on re-init.
		if (explorationState.observer) {
			explorationState.observer.disconnect();
		}

		// Watch for room transitions via MutationObserver.
		var observer = new MutationObserver(function (mutations) {
			for (var i = 0; i < mutations.length; i++) {
				var m = mutations[i];
				if (m.type === 'attributes' && m.attributeName === 'class') {
					var target = m.target;
					if (target.classList.contains('scene-layer') && target.classList.contains('active')) {
						onRoomChanged(target);
					}
				}
			}
		});

		// Observe all scene-layer elements for class changes.
		explorationState.observer = observer;
		layers.forEach(function (layer) {
			observer.observe(layer, { attributes: true, attributeFilter: ['class'] });
		});

		trackEvent('journey_tracker_init', {
			collection: collection.slug,
			totalRooms: totalRooms,
			visitedCount: Object.keys(explorationState.journeyData.visited).length,
		});
	}

	function recordCurrentRoom(viewport) {
		var active = viewport.querySelector('.scene-layer.active');
		if (active) {
			var roomName = active.dataset.roomName || 'Room';
			explorationState.journeyData.visited[roomName] = true;
			storageSet(explorationState.storageKey, explorationState.journeyData);
		}
	}

	function onRoomChanged(layerEl) {
		var roomName = layerEl.dataset.roomName || 'Room';
		var data = explorationState.journeyData;
		var wasNew = !data.visited[roomName];

		data.visited[roomName] = true;
		storageSet(explorationState.storageKey, data);

		updateProgressPill();

		if (wasNew) {
			trackEvent('journey_room_discovered', {
				collection: explorationState.collection.slug,
				room: roomName,
				visitedCount: Object.keys(data.visited).length,
				totalRooms: data.totalRooms,
			});
		}

		// Check for completion.
		var visitedCount = Object.keys(data.visited).length;
		if (visitedCount >= data.totalRooms && !explorationState.rewardShown) {
			explorationState.rewardShown = true;
			setTimeout(function () {
				showRewardReveal();
			}, CFG.rewardDelay);
		}
	}

	/* ==================================================
	   2. JOURNEY PROGRESS PILL UI
	   ================================================== */

	function buildProgressPill(scene) {
		var pill = document.createElement('div');
		pill.className = 'jge-progress-pill';
		pill.setAttribute('aria-live', 'polite');
		pill.setAttribute('role', 'status');

		// Progress bar
		var bar = document.createElement('div');
		bar.className = 'jge-progress-pill__bar';
		var fill = document.createElement('div');
		fill.className = 'jge-progress-pill__fill';
		bar.appendChild(fill);

		// Label
		var label = document.createElement('span');
		label.className = 'jge-progress-pill__label';

		// Checkmark (hidden by default, shown on completion)
		var check = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
		check.setAttribute('class', 'jge-progress-pill__check');
		check.setAttribute('viewBox', '0 0 24 24');
		check.setAttribute('fill', 'none');
		check.setAttribute('stroke', '#D4AF37');
		check.setAttribute('stroke-width', '2.5');
		check.setAttribute('stroke-linecap', 'round');
		check.setAttribute('stroke-linejoin', 'round');
		check.setAttribute('aria-hidden', 'true');
		var path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
		path.setAttribute('d', 'M20 6L9 17l-5-5');
		check.appendChild(path);

		pill.appendChild(bar);
		pill.appendChild(label);
		pill.appendChild(check);

		scene.appendChild(pill);
		explorationState.pillEl = pill;

		// Animate in after a short delay.
		requestAnimationFrame(function () {
			requestAnimationFrame(function () {
				pill.classList.add('jge-visible');
			});
		});
	}

	function updateProgressPill() {
		var pill = explorationState.pillEl;
		if (!pill) return;

		var data = explorationState.journeyData;
		var visited = Object.keys(data.visited).length;
		var total = data.totalRooms;
		var pct = total > 0 ? Math.round((visited / total) * 100) : 0;

		var label = pill.querySelector('.jge-progress-pill__label');
		var fill  = pill.querySelector('.jge-progress-pill__fill');

		if (label) {
			label.textContent = 'Room ' + visited + ' of ' + total;
		}
		if (fill) {
			fill.style.width = pct + '%';
		}

		if (visited >= total) {
			pill.classList.add('jge-progress-pill--complete');
			if (label) {
				label.textContent = 'Journey Complete';
			}
		} else {
			pill.classList.remove('jge-progress-pill--complete');
		}
	}

	/* ==================================================
	   3. REWARD REVEAL MODAL
	   ================================================== */

	function showRewardReveal() {
		// Prevent showing if it was already shown this session for this collection.
		var rewardKey = explorationState.storageKey + '_rewarded';
		if (storageGet(rewardKey)) return;
		storageSet(rewardKey, true);

		var collectionName = explorationState.collection.name;

		// Build the overlay.
		var overlay = document.createElement('div');
		overlay.className = 'jge-reward-overlay';
		overlay.setAttribute('role', 'dialog');
		overlay.setAttribute('aria-modal', 'true');
		overlay.setAttribute('aria-label', 'Exploration Reward');

		var modal = document.createElement('div');
		modal.className = 'jge-reward-modal';

		// Close button
		var closeBtn = document.createElement('button');
		closeBtn.type = 'button';
		closeBtn.className = 'jge-reward-modal__close';
		closeBtn.setAttribute('aria-label', 'Close reward modal');
		closeBtn.textContent = '\u2715';
		modal.appendChild(closeBtn);

		// Particle container
		var particles = document.createElement('div');
		particles.className = 'jge-reward-modal__particles';
		modal.appendChild(particles);

		// Content wrapper
		var content = document.createElement('div');
		content.className = 'jge-reward-modal__content';

		// Trophy icon
		var icon = document.createElement('div');
		icon.className = 'jge-reward-modal__icon';
		icon.setAttribute('aria-hidden', 'true');
		icon.textContent = '\u2728'; // sparkles
		content.appendChild(icon);

		// Headline
		var headline = document.createElement('h2');
		headline.className = 'jge-reward-modal__headline';
		headline.textContent = 'You\u2019ve explored the entire ' + collectionName + '!';
		content.appendChild(headline);

		// Subtext
		var subtext = document.createElement('p');
		subtext.className = 'jge-reward-modal__subtext';
		subtext.textContent = 'As a reward for completing your journey, enjoy ' + CFG.promoDiscount + ' on your first pre-order.';
		content.appendChild(subtext);

		// Promo code box
		var codeBox = document.createElement('div');
		codeBox.className = 'jge-reward-code';

		var codeValue = document.createElement('span');
		codeValue.className = 'jge-reward-code__value';
		codeValue.textContent = CFG.promoCode;
		codeBox.appendChild(codeValue);

		var copyBtn = document.createElement('button');
		copyBtn.type = 'button';
		copyBtn.className = 'jge-reward-code__copy';
		copyBtn.textContent = 'Copy';
		copyBtn.addEventListener('click', function () {
			copyToClipboard(CFG.promoCode, copyBtn);
		});
		codeBox.appendChild(copyBtn);

		content.appendChild(codeBox);

		// CTA button
		var cta = document.createElement('a');
		cta.href = CFG.preorderUrl;
		cta.className = 'jge-reward-modal__cta';
		cta.textContent = 'Pre-Order Now';
		content.appendChild(cta);

		modal.appendChild(content);
		overlay.appendChild(modal);
		document.body.appendChild(overlay);

		// Close handlers.
		function keyHandler(e) {
			if (e.key === 'Escape') {
				dismiss();
				return;
			}

			// Focus trap — keep Tab cycling within the modal.
			if (e.key === 'Tab') {
				var focusable = modal.querySelectorAll('button, a[href], input, [tabindex]:not([tabindex="-1"])');
				if (focusable.length === 0) return;
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
		}

		function dismiss() {
			window.removeEventListener('beforeunload', dismiss);
			document.removeEventListener('keydown', keyHandler);
			overlay.classList.remove('jge-visible');
			setTimeout(function () {
				if (overlay.parentNode) {
					overlay.parentNode.removeChild(overlay);
				}
			}, 500);
		}

		closeBtn.addEventListener('click', dismiss);
		overlay.addEventListener('click', function (e) {
			if (e.target === overlay) dismiss();
		});
		document.addEventListener('keydown', keyHandler);
		// Clean up document-level listener if user navigates away while modal is open.
		window.addEventListener('beforeunload', dismiss);

		// Show with animation.
		requestAnimationFrame(function () {
			requestAnimationFrame(function () {
				overlay.classList.add('jge-visible');
				spawnConfetti(particles);
			});
		});

		// Focus the close button for accessibility.
		setTimeout(function () {
			closeBtn.focus();
		}, 100);

		trackEvent('journey_reward_shown', {
			collection: explorationState.collection.slug,
			promoCode: CFG.promoCode,
		});
	}

	function copyToClipboard(text, btn) {
		if (navigator.clipboard && navigator.clipboard.writeText) {
			navigator.clipboard.writeText(text).then(function () {
				showCopied(btn);
			}, function () {
				fallbackCopy(text, btn);
			});
		} else {
			fallbackCopy(text, btn);
		}
	}

	function fallbackCopy(text, btn) {
		var ta = document.createElement('textarea');
		ta.value = text;
		ta.style.cssText = 'position:fixed;top:-9999px;left:-9999px;opacity:0;';
		document.body.appendChild(ta);
		ta.select();
		try {
			document.execCommand('copy');
			showCopied(btn);
		} catch (_) {
			/* silently fail */
		}
		document.body.removeChild(ta);
	}

	function showCopied(btn) {
		btn.textContent = 'Copied!';
		btn.classList.add('jge-reward-code__copy--copied');
		setTimeout(function () {
			btn.textContent = 'Copy';
			btn.classList.remove('jge-reward-code__copy--copied');
		}, 2000);
	}

	/* --------------------------------------------------
	   Confetti particle spawner for reward modal
	   -------------------------------------------------- */

	function spawnConfetti(container) {
		var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
		if (reducedMotion) return;

		for (var i = 0; i < CFG.confettiCount; i++) {
			var p = document.createElement('span');
			p.className = 'jge-reward-particle';

			var size = 4 + Math.random() * 6;
			var isRect = Math.random() > 0.5;
			var colour = CONFETTI_COLOURS[Math.floor(Math.random() * CONFETTI_COLOURS.length)];
			var left = Math.random() * 100;
			var fallDist = 200 + Math.random() * 200;
			var fallDur = 2 + Math.random() * 1.5;
			var delay = Math.random() * 0.6;
			var rotate = 180 + Math.random() * 540;

			p.style.cssText = [
				'left:' + left + '%',
				'top:-10px',
				'width:' + size + 'px',
				'height:' + (isRect ? size * 2 : size) + 'px',
				'border-radius:' + (isRect ? '2px' : '50%'),
				'background:' + colour,
				'--jge-fall-distance:' + fallDist + 'px',
				'--jge-fall-duration:' + fallDur + 's',
				'--jge-fall-delay:' + delay + 's',
				'--jge-fall-rotate:' + rotate + 'deg',
			].join(';');

			container.appendChild(p);
		}

		// Cleanup after animation.
		setTimeout(function () {
			while (container.firstChild) {
				container.removeChild(container.firstChild);
			}
		}, CFG.confettiDuration + 200);
	}

	/* ==================================================
	   4. ACHIEVEMENT BADGE RENDERER
	   On collection / static pages, reads sessionStorage
	   to show discovery progress.
	   ================================================== */

	function initAchievementBadges() {
		// Only run on collection / product pages (not immersive).
		if (document.querySelector('.immersive-scene')) return;

		var isCollectionPage = document.querySelector('.collection-product-card') ||
		                       document.querySelector('.product-grid');
		if (!isCollectionPage) return;

		var slug = detectCollectionSlugFromPage();
		if (!slug) return;

		var storageKey = CFG.storagePrefix + slug;
		var data = storageGet(storageKey);
		if (!data || !data.visited) return;

		var visitedCount = Object.keys(data.visited).length;
		if (visitedCount === 0) return;

		var totalRooms = data.totalRooms || 0;
		var isComplete = visitedCount >= totalRooms && totalRooms > 0;

		// Find the immersive URL for this collection.
		var immersiveUrl = null;
		var collectionKeys = Object.keys(COLLECTIONS);
		for (var i = 0; i < collectionKeys.length; i++) {
			if (COLLECTIONS[collectionKeys[i]].slug === slug) {
				immersiveUrl = COLLECTIONS[collectionKeys[i]].immersiveUrl;
				break;
			}
		}

		// Build the badge.
		var bar = document.createElement('div');
		bar.className = 'jge-achievement-bar' + (isComplete ? ' jge-achievement-bar--complete' : '');
		bar.setAttribute('role', 'status');

		// Icon
		var icon = document.createElement('div');
		icon.className = 'jge-achievement-bar__icon';
		icon.setAttribute('aria-hidden', 'true');
		icon.textContent = isComplete ? '\u2728' : '\uD83D\uDD0D'; // sparkles or magnifying glass
		bar.appendChild(icon);

		// Text
		var text = document.createElement('div');
		text.className = 'jge-achievement-bar__text';
		if (isComplete) {
			var strong1 = document.createElement('strong');
			strong1.textContent = 'Journey Complete!';
			text.appendChild(strong1);
			text.appendChild(document.createTextNode(' You explored all ' + parseInt(totalRooms, 10) + ' rooms'));
		} else {
			text.appendChild(document.createTextNode('Explored '));
			var strong2 = document.createElement('strong');
			strong2.textContent = parseInt(visitedCount, 10) + '/' + parseInt(totalRooms, 10);
			text.appendChild(strong2);
			text.appendChild(document.createTextNode(' rooms'));
		}
		bar.appendChild(text);

		// Mini progress bar
		var progress = document.createElement('div');
		progress.className = 'jge-achievement-bar__progress';
		var fill = document.createElement('div');
		fill.className = 'jge-achievement-bar__fill';
		progress.appendChild(fill);
		bar.appendChild(progress);

		// Link back to immersive
		if (immersiveUrl) {
			var link = document.createElement('a');
			link.href = immersiveUrl;
			link.className = 'jge-achievement-bar__link';
			link.textContent = isComplete ? 'Revisit' : 'Continue';
			bar.appendChild(link);
		}

		// Insert into DOM — find the best anchor point.
		var anchor = document.querySelector('.collection-hero') ||
		             document.querySelector('.collection-header') ||
		             document.querySelector('.product-grid') ||
		             document.querySelector('.collection-product-card');
		if (!anchor) return;

		var parent = anchor.parentNode;
		parent.insertBefore(bar, anchor);

		// Set fill width after insertion.
		requestAnimationFrame(function () {
			var pct = totalRooms > 0 ? Math.round((visitedCount / totalRooms) * 100) : 0;
			fill.style.width = pct + '%';
			bar.classList.add('jge-visible');
		});

		trackEvent('journey_achievement_shown', {
			collection: slug,
			visitedCount: visitedCount,
			totalRooms: totalRooms,
			isComplete: isComplete,
		});
	}

	/* ==================================================
	   5. CROSS-SELL RECOMMENDATION STRIP
	   Populates [data-journey-crosssell] containers with
	   horizontally scrollable product cards.
	   ================================================== */

	function initCrossSellStrips() {
		var containers = Array.from(document.querySelectorAll('[data-journey-crosssell]'));
		if (containers.length === 0) return;

		containers.forEach(function (container) {
			var slug = container.dataset.journeyCrosssell || detectCollectionSlugFromPage();
			if (!slug) return;

			var products = PRODUCT_CATALOG[slug];
			if (!products || products.length === 0) return;

			// Determine which SKUs are already visible on the page to exclude them.
			var visibleSkus = getVisibleProductSkus();

			// Filter and shuffle.
			var candidates = products.filter(function (p) {
				return visibleSkus.indexOf(p.sku) === -1;
			});

			// Fisher-Yates shuffle.
			var shuffled = candidates.slice();
			for (var i = shuffled.length - 1; i > 0; i--) {
				var j = Math.floor(Math.random() * (i + 1));
				var tmp = shuffled[i];
				shuffled[i] = shuffled[j];
				shuffled[j] = tmp;
			}

			// Take up to 8 recommendations.
			var recs = shuffled.slice(0, 8);
			if (recs.length === 0) return;

			buildCrossSellStrip(container, recs);
		});
	}

	function getVisibleProductSkus() {
		var skus = [];

		// From collection product cards.
		var cards = Array.from(document.querySelectorAll('.collection-product-card[data-sku]'));
		cards.forEach(function (card) {
			if (card.dataset.sku) skus.push(card.dataset.sku);
		});

		// From hotspot beacons.
		var hotspots = Array.from(document.querySelectorAll('.hotspot[data-product-id]'));
		hotspots.forEach(function (h) {
			if (h.dataset.productId) skus.push(h.dataset.productId);
		});

		return skus;
	}

	function buildCrossSellStrip(container, products) {
		// Clear any existing content.
		container.innerHTML = '';

		var wrapper = document.createElement('div');
		wrapper.className = 'jge-crosssell';

		// Heading
		var heading = document.createElement('p');
		heading.className = 'jge-crosssell__heading';
		heading.textContent = 'Complete the Look';
		wrapper.appendChild(heading);

		// Scroll track
		var track = document.createElement('div');
		track.className = 'jge-crosssell__track';
		track.setAttribute('role', 'list');

		products.forEach(function (product) {
			track.appendChild(buildCrossSellCard(product));
		});

		wrapper.appendChild(track);
		container.appendChild(wrapper);

		// Touch scroll enhancement — prevent vertical scrolling
		// when the user is horizontally scrolling the track.
		initTouchScroll(track);
	}

	function buildCrossSellCard(product) {
		var card = document.createElement('div');
		card.className = 'jge-crosssell__card';
		card.setAttribute('role', 'listitem');
		card.setAttribute('data-sku', product.sku);

		// Thumbnail
		var thumb = document.createElement('div');
		thumb.className = 'jge-crosssell__thumb';

		if (product.image) {
			var img = document.createElement('img');
			img.src = product.image;
			img.alt = product.name;
			img.loading = 'lazy';
			img.addEventListener('error', function () {
				img.style.display = 'none';
				thumb.appendChild(buildThumbPlaceholder(product.name));
			});
			thumb.appendChild(img);
		} else {
			thumb.appendChild(buildThumbPlaceholder(product.name));
		}

		card.appendChild(thumb);

		// Product name
		var nameEl = document.createElement('p');
		nameEl.className = 'jge-crosssell__name';
		nameEl.textContent = product.name;
		card.appendChild(nameEl);

		// Price
		var priceEl = document.createElement('p');
		priceEl.className = 'jge-crosssell__price';
		priceEl.textContent = product.price;
		card.appendChild(priceEl);

		// Add button
		var addBtn = document.createElement('button');
		addBtn.type = 'button';
		addBtn.className = 'jge-crosssell__add';
		addBtn.textContent = 'Add';
		addBtn.setAttribute('aria-label', 'Add ' + product.name + ' to cart');

		addBtn.addEventListener('click', function (e) {
			e.stopPropagation();
			handleCrossSellAdd(product, addBtn);
		});

		card.appendChild(addBtn);

		// Card click navigates to product.
		card.addEventListener('click', function () {
			if (product.url) {
				window.location.href = product.url;
			}
		});

		return card;
	}

	function buildThumbPlaceholder(name) {
		var el = document.createElement('div');
		el.className = 'jge-crosssell__thumb-placeholder';
		var words = (name || '').split(/\s+/).filter(Boolean);
		var initials = words.slice(0, 2).map(function (w) { return w.charAt(0).toUpperCase(); }).join('');
		el.textContent = initials || 'SR';
		return el;
	}

	function handleCrossSellAdd(product, btn) {
		trackEvent('journey_crosssell_add', { sku: product.sku, name: product.name });

		// Use the theme's AJAX handler which accepts SKU (not numeric product_id).
		var ajaxUrl = (typeof skyyRoseData !== 'undefined' && skyyRoseData.ajaxUrl)
			? skyyRoseData.ajaxUrl
			: null;

		var nonce = (typeof skyyRoseData !== 'undefined') ? skyyRoseData.nonce : '';
		if (ajaxUrl && nonce && product.sku) {
			btn.disabled = true;
			var originalText = btn.textContent;
			btn.textContent = '...';

			var xhr = new XMLHttpRequest();
			xhr.open('POST', ajaxUrl, true);
			xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
			xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');

			xhr.onload = function () {
				btn.disabled = false;
				if (xhr.status >= 200 && xhr.status < 300) {
					try {
						var resp = JSON.parse(xhr.responseText);
						if (resp.success) {
							showAddedState(btn, originalText);
							if (typeof jQuery !== 'undefined') {
								jQuery(document.body).trigger('wc_fragment_refresh');
							}
							return;
						}
					} catch (_) { /* fall through */ }
				}
				btn.textContent = originalText;
			};

			xhr.onerror = function () {
				btn.disabled = false;
				btn.textContent = originalText;
			};

			xhr.send(
				'action=skyyrose_immersive_add_to_cart' +
				'&sku=' + encodeURIComponent(product.sku) +
				'&quantity=1' +
				'&nonce=' + encodeURIComponent(nonce)
			);
		} else {
			// No WooCommerce — visual feedback only.
			showAddedState(btn, btn.textContent);
		}
	}

	function showAddedState(btn, originalText) {
		btn.textContent = 'Added!';
		btn.classList.add('jge-crosssell__add--added');
		setTimeout(function () {
			btn.textContent = originalText;
			btn.classList.remove('jge-crosssell__add--added');
		}, 2200);
	}

	/* WooCommerce add-to-cart now routed through skyyRoseData.ajaxUrl
	   via skyyrose_immersive_add_to_cart action (accepts SKU). */

	/* --------------------------------------------------
	   Touch scroll enhancement for cross-sell track
	   -------------------------------------------------- */

	function initTouchScroll(track) {
		var startX = 0;
		var startY = 0;
		var isHorizontal = null;

		track.addEventListener('touchstart', function (e) {
			startX = e.touches[0].clientX;
			startY = e.touches[0].clientY;
			isHorizontal = null;
		}, { passive: true });

		track.addEventListener('touchmove', function (e) {
			if (isHorizontal === null) {
				var dx = Math.abs(e.touches[0].clientX - startX);
				var dy = Math.abs(e.touches[0].clientY - startY);
				isHorizontal = dx > dy;
			}
			// If horizontal scrolling, prevent vertical page scroll.
			if (isHorizontal) {
				e.preventDefault();
			}
		}, { passive: false });
	}

	/* ==================================================
	   INITIALISATION
	   ================================================== */

	function init() {
		// 1. Immersive pages: room tracker + progress pill + reward.
		initExplorationTracker();

		// 2. Collection/static pages: achievement badges.
		initAchievementBadges();

		// 3. All pages with cross-sell containers.
		initCrossSellStrips();
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}

})();
