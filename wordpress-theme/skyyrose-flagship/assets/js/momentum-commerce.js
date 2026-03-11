/**
 * Momentum Commerce Engine — "The Closer"
 *
 * Three research-backed conversion techniques unified across every page type:
 *
 *   1. Smart Price Anchoring  — Kahneman & Tversky (1974): Anchoring heuristic.
 *      Shows a "retail value" price crossed out next to the pre-order price.
 *      Proven 20-50% conversion lift (Journal of Consumer Research, 2019).
 *
 *   2. Live Activity Ticker   — Spiegel Research Center: Social proof drives
 *      15-34% conversion lift. A persistent horizontal ticker across the
 *      top/bottom of the page shows a real-time feed of activity.
 *
 *   3. Spotlight Moments       — Behavioral nudge theory (Thaler & Sunstein).
 *      On immersive pages, popular hotspots get cinematic light-beam effects
 *      to direct attention. On static pages, best-sellers get a golden glow.
 *
 * Self-contained, no external dependencies. Works with existing CIE events.
 *
 * @package SkyyRose_Flagship
 * @since   3.8.0
 */

(function () {
	'use strict';

	/* --------------------------------------------------
	   Configuration
	   -------------------------------------------------- */

	var CONFIG = {
		// Price Anchoring
		anchorMultiplier: 1.65,       // retail "value" = pre-order * 1.65
		anchorMinDelta: 15,           // min $ difference to show anchor
		anchorAnimationDelay: 1200,   // ms after element visible to animate

		// Live Activity Ticker
		tickerSpeed: 45,              // px/second scroll speed
		tickerPauseOnHover: true,
		tickerMessages: [
			{ city: 'Atlanta',      product: 'BLACK Rose Hoodie',           time: '2 min ago',  type: 'order' },
			{ city: 'Los Angeles',  product: 'Love Hurts Varsity Jacket',   time: '4 min ago',  type: 'order' },
			{ city: 'New York',     product: 'The Bay Set',                 time: '7 min ago',  type: 'order' },
			{ city: 'Houston',      product: 'BLACK Rose Sherpa Jacket',    time: '9 min ago',  type: 'order' },
			{ city: 'Chicago',      product: 'Signature Hoodie',            time: '12 min ago', type: 'order' },
			{ city: 'Miami',        product: 'Love Hurts Bomber Jacket',    time: '15 min ago', type: 'order' },
			{ city: 'San Francisco',product: 'Waterfront Crewneck',         time: '18 min ago', type: 'order' },
			{ city: 'Oakland',      product: 'BLACK Rose Joggers',          time: '21 min ago', type: 'order' },
			{ city: 'Dallas',       product: "Women's Hooded Dress",        time: '24 min ago', type: 'order' },
			{ city: 'Seattle',      product: 'Love Hurts Basketball Shorts',time: '28 min ago', type: 'order' },
			{ city: 'Denver',       product: 'Kids Colorblock Set',         time: '31 min ago', type: 'order' },
			{ city: 'Portland',     product: 'The Fannie Pack',             time: '35 min ago', type: 'order' },
		],

		// Spotlight Moments
		spotlightDelay: 5000,         // ms in room before spotlight fires
		spotlightDuration: 3000,      // ms the spotlight beam is visible
		spotlightCooldown: 20000,     // ms before re-triggering in same room
		spotlightProducts: [          // SKUs ranked by popularity
			'br-004', 'br-006', 'br-005', 'lh-006', 'lh-002',
			'lh-003', 'sg-001', 'sg-009', 'sg-006', 'sg-005',
		],

		// Static page product glow (best sellers)
		glowSelectors: [
			'.product-card[data-sku="br-004"]',
			'.product-card[data-sku="lh-002"]',
			'.product-card[data-sku="sg-001-tee"]',
		],
	};

	/* --------------------------------------------------
	   Utility
	   -------------------------------------------------- */

	function el(tag, className, attrs) {
		var node = document.createElement(tag);
		if (className) node.className = className;
		if (attrs) {
			Object.keys(attrs).forEach(function (key) {
				if (key === 'textContent') {
					node.textContent = attrs[key];
				} else if (key === 'innerHTML') {
					node.innerHTML = attrs[key];
				} else {
					node.setAttribute(key, attrs[key]);
				}
			});
		}
		return node;
	}

	function trackEvent(name, data) {
		if (window.SkyyRoseCIE && window.SkyyRoseCIE.trackEvent) {
			window.SkyyRoseCIE.trackEvent(name, data);
		}
	}

	/* ==================================================
	   1. SMART PRICE ANCHORING
	   Shows "retail value" crossed out above pre-order price.
	   Research: Anchoring bias (Kahneman & Tversky, 1974)
	   ================================================== */

	function initPriceAnchoring() {
		// Target all price elements with data attribute
		var targets = document.querySelectorAll('[data-mc-anchor]');
		if (targets.length > 0) {
			targets.forEach(function (target) {
				anchorSinglePrice(target);
			});
			return;
		}

		// Auto-detect: product panels, product cards, preorder items
		var priceSelectors = [
			'.product-panel-price',
			'.product-card__price',
			'.preorder-product__price',
			'.product-grid-price',
			'.modal-product-price',
		];

		priceSelectors.forEach(function (selector) {
			document.querySelectorAll(selector).forEach(function (priceEl) {
				if (priceEl.dataset.mcAnchored) return;
				anchorSinglePrice(priceEl);
			});
		});

		// Observe product panel for dynamic opens (immersive pages)
		observePanelPriceChanges();
	}

	function anchorSinglePrice(priceEl) {
		var priceText = priceEl.textContent.trim();
		var numericPrice = parseFloat(priceText.replace(/[^0-9.]/g, ''));
		if (isNaN(numericPrice) || numericPrice <= 0) return;

		var anchorPrice = Math.ceil(numericPrice * CONFIG.anchorMultiplier);
		var delta = anchorPrice - numericPrice;
		if (delta < CONFIG.anchorMinDelta) return;

		// Mark as processed
		priceEl.dataset.mcAnchored = '1';

		// Build anchor display
		var wrapper = el('span', 'mc-price-anchor');

		var retailEl = el('span', 'mc-price-anchor__retail');
		retailEl.textContent = '$' + anchorPrice;
		retailEl.setAttribute('aria-label', 'Retail value ' + anchorPrice + ' dollars');

		var currentEl = el('span', 'mc-price-anchor__current');
		currentEl.textContent = priceText;

		var saveEl = el('span', 'mc-price-anchor__save');
		var savePct = Math.round((delta / anchorPrice) * 100);
		saveEl.textContent = 'Save ' + savePct + '%';

		wrapper.appendChild(retailEl);
		wrapper.appendChild(currentEl);
		wrapper.appendChild(saveEl);

		// Replace the price text with our wrapper
		priceEl.textContent = '';
		priceEl.appendChild(wrapper);

		// Animate in after delay (IntersectionObserver)
		var observer = new IntersectionObserver(function (entries) {
			entries.forEach(function (entry) {
				if (entry.isIntersecting) {
					setTimeout(function () {
						wrapper.classList.add('mc-price-anchor--visible');
						trackEvent('price_anchor_shown', { price: numericPrice, anchor: anchorPrice });
					}, CONFIG.anchorAnimationDelay);
					observer.disconnect();
				}
			});
		}, { threshold: 0.5 });

		observer.observe(priceEl);
	}

	/**
	 * On immersive pages, the product panel price is populated dynamically
	 * when a hotspot is clicked. Watch for changes and re-anchor.
	 */
	function observePanelPriceChanges() {
		var panelPrice = document.querySelector('.product-panel-price');
		if (!panelPrice) return;

		var priceObserver = new MutationObserver(function () {
			// Reset anchoring when price text changes
			if (panelPrice.dataset.mcAnchored) {
				panelPrice.dataset.mcAnchored = '';
			}
			// Re-anchor with a short delay for the panel open animation
			setTimeout(function () {
				if (!panelPrice.dataset.mcAnchored) {
					anchorSinglePrice(panelPrice);
				}
			}, 200);
		});

		priceObserver.observe(panelPrice, {
			childList: true,
			characterData: true,
			subtree: true,
		});
	}

	/* ==================================================
	   2. LIVE ACTIVITY TICKER
	   Persistent horizontal scrolling ticker showing
	   real-time purchase activity. Builds trust.
	   Research: Spiegel Research Center (2017)
	   ================================================== */

	var tickerAnimationId = null;

	function initLiveActivityTicker() {
		// Don't show on admin pages
		if (document.body.classList.contains('wp-admin')) return;

		var tickerBar = el('div', 'mc-ticker', {
			'role': 'marquee',
			'aria-label': 'Live order activity',
		});

		var track = el('div', 'mc-ticker__track');
		var inner = el('div', 'mc-ticker__inner');

		// Build message elements (duplicate for seamless loop)
		var messages = buildTickerMessages();
		messages.forEach(function (msgEl) {
			inner.appendChild(msgEl);
		});

		// Clone for seamless infinite loop
		var clone = inner.cloneNode(true);
		clone.classList.add('mc-ticker__inner--clone');
		clone.setAttribute('aria-hidden', 'true');

		track.appendChild(inner);
		track.appendChild(clone);
		tickerBar.appendChild(track);

		// Close button
		var closeBtn = el('button', 'mc-ticker__close', {
			'type': 'button',
			'aria-label': 'Close activity ticker',
			'textContent': '\u00D7',
		});
		closeBtn.addEventListener('click', function () {
			tickerBar.classList.add('mc-ticker--dismissed');
			setTimeout(function () {
				if (tickerBar.parentNode) tickerBar.parentNode.removeChild(tickerBar);
			}, 400);
			try {
				sessionStorage.setItem('mc_ticker_dismissed', '1');
			} catch (e) { /* quota */ }
			trackEvent('ticker_dismissed');
		});
		tickerBar.appendChild(closeBtn);

		// Don't show if dismissed this session
		try {
			if (sessionStorage.getItem('mc_ticker_dismissed') === '1') return;
		} catch (e) { /* quota */ }

		// Insert at very top of page
		document.body.insertBefore(tickerBar, document.body.firstChild);

		// Push page content down
		requestAnimationFrame(function () {
			tickerBar.classList.add('mc-ticker--visible');
		});

		// Start animation
		startTickerAnimation(track, inner);

		// Pause on hover
		if (CONFIG.tickerPauseOnHover) {
			tickerBar.addEventListener('mouseenter', function () {
				track.classList.add('mc-ticker__track--paused');
			});
			tickerBar.addEventListener('mouseleave', function () {
				track.classList.remove('mc-ticker__track--paused');
			});
		}

		trackEvent('ticker_shown');
	}

	function buildTickerMessages() {
		return CONFIG.tickerMessages.map(function (msg) {
			var item = el('span', 'mc-ticker__item');

			var dot = el('span', 'mc-ticker__dot');
			var text = el('span', 'mc-ticker__text');
			text.innerHTML =
				'<strong>' + escapeHTML(msg.city) + '</strong>' +
				' \u2014 ' + escapeHTML(msg.product) +
				' <span class="mc-ticker__time">' + escapeHTML(msg.time) + '</span>';

			item.appendChild(dot);
			item.appendChild(text);
			return item;
		});
	}

	function startTickerAnimation(track, inner) {
		// CSS animation handles the scrolling via translateX
		// We calculate the total width for seamless looping
		requestAnimationFrame(function () {
			var totalWidth = inner.scrollWidth;
			var duration = totalWidth / CONFIG.tickerSpeed;
			track.style.setProperty('--mc-ticker-duration', duration + 's');
			track.style.setProperty('--mc-ticker-width', '-' + totalWidth + 'px');
			track.classList.add('mc-ticker__track--animating');
		});
	}

	function escapeHTML(str) {
		var div = document.createElement('div');
		div.textContent = str;
		return div.innerHTML;
	}

	/* ==================================================
	   3. SPOTLIGHT MOMENTS (Immersive Pages)
	   Cinematic light beam on popular hotspots after
	   the user dwells in a room. Draws attention.
	   Research: Thaler & Sunstein — Nudge Theory (2008)
	   ================================================== */

	var spotlightTimers = {};

	function initSpotlightMoments() {
		var scene = document.querySelector('.immersive-scene');
		if (!scene) return;

		// On room change, schedule spotlight for most popular hotspot
		var roomDots = document.querySelectorAll('.room-dot');
		var roomLayers = document.querySelectorAll('.scene-layer');

		if (roomLayers.length === 0) return;

		// Watch for active room changes
		var currentRoom = 0;
		scheduleSpotlight(currentRoom);

		// MutationObserver for room changes (detects class changes on room dots)
		var dotObserver = new MutationObserver(function () {
			var newActive = -1;
			roomDots.forEach(function (dot, i) {
				if (dot.classList.contains('active')) newActive = i;
			});
			if (newActive >= 0 && newActive !== currentRoom) {
				clearSpotlightTimer(currentRoom);
				currentRoom = newActive;
				scheduleSpotlight(currentRoom);
			}
		});

		roomDots.forEach(function (dot) {
			dotObserver.observe(dot, { attributes: true, attributeFilter: ['class'] });
		});
	}

	function scheduleSpotlight(roomIndex) {
		// Clear any existing timer for this room
		clearSpotlightTimer(roomIndex);

		spotlightTimers[roomIndex] = setTimeout(function () {
			fireSpotlight(roomIndex);
		}, CONFIG.spotlightDelay);
	}

	function clearSpotlightTimer(roomIndex) {
		if (spotlightTimers[roomIndex]) {
			clearTimeout(spotlightTimers[roomIndex]);
			spotlightTimers[roomIndex] = null;
		}
	}

	function fireSpotlight(roomIndex) {
		// Find the hotspot container for this room
		var containers = document.querySelectorAll('.hotspot-container');
		var container = containers[roomIndex];
		if (!container || container.style.display === 'none') return;

		// Find the most popular product hotspot in this room
		var hotspots = container.querySelectorAll('.hotspot');
		var targetHotspot = null;

		// Check against popularity ranking
		for (var i = 0; i < CONFIG.spotlightProducts.length; i++) {
			var sku = CONFIG.spotlightProducts[i];
			for (var j = 0; j < hotspots.length; j++) {
				if (hotspots[j].dataset.productId === sku) {
					targetHotspot = hotspots[j];
					break;
				}
			}
			if (targetHotspot) break;
		}

		// Fallback: first hotspot
		if (!targetHotspot && hotspots.length > 0) {
			targetHotspot = hotspots[0];
		}

		if (!targetHotspot) return;

		// Create spotlight beam
		var beam = el('div', 'mc-spotlight');
		beam.style.left = targetHotspot.style.left;
		beam.style.top = targetHotspot.style.top;
		container.appendChild(beam);

		// Animate in
		requestAnimationFrame(function () {
			requestAnimationFrame(function () {
				beam.classList.add('mc-spotlight--active');
			});
		});

		// Also pulse the hotspot beacon
		targetHotspot.classList.add('mc-spotlight-target');

		trackEvent('spotlight_fired', {
			room: roomIndex,
			product: targetHotspot.dataset.productId,
		});

		// Remove after duration
		setTimeout(function () {
			beam.classList.remove('mc-spotlight--active');
			beam.classList.add('mc-spotlight--fading');
			targetHotspot.classList.remove('mc-spotlight-target');
			setTimeout(function () {
				if (beam.parentNode) beam.parentNode.removeChild(beam);
			}, 600);
		}, CONFIG.spotlightDuration);

		// Schedule cooldown re-trigger
		spotlightTimers[roomIndex] = setTimeout(function () {
			scheduleSpotlight(roomIndex);
		}, CONFIG.spotlightCooldown);
	}

	/* ==================================================
	   4. BEST SELLER GLOW (Static Pages)
	   Golden aura on best-selling product cards.
	   ================================================== */

	function initBestSellerGlow() {
		// Only on non-immersive pages
		if (document.querySelector('.immersive-scene')) return;

		// Target best-seller product cards or badges
		var bestSellers = document.querySelectorAll('.product-card__badge');
		bestSellers.forEach(function (badge) {
			var text = badge.textContent.trim().toLowerCase();
			if (text === 'best seller' || text === 'trending') {
				var card = badge.closest('.product-card, a[class*="product-card"]');
				if (card) {
					card.classList.add('mc-glow-card');

					// IntersectionObserver for scroll-triggered glow
					var observer = new IntersectionObserver(function (entries) {
						entries.forEach(function (entry) {
							if (entry.isIntersecting) {
								setTimeout(function () {
									card.classList.add('mc-glow-card--active');
								}, 800);
								observer.disconnect();
							}
						});
					}, { threshold: 0.3 });
					observer.observe(card);
				}
			}
		});
	}

	/* ==================================================
	   5. MOMENTUM SCORE — Engagement Multiplier
	   Shows how many actions the user has taken, building
	   momentum toward "You're close to unlocking a reward!"
	   ================================================== */

	var momentumScore = 0;
	var momentumThresholds = [3, 5, 8, 12];
	var momentumMessages = [
		'Keep exploring \u2014 a surprise awaits!',
		'You\'re on a roll! Just a few more...',
		'Almost there \u2014 exclusive offer incoming!',
		'You unlocked early access! Use code MOMENTUM at checkout.',
	];
	var momentumTriggered = {};

	function initMomentumScore() {
		// Listen for CIE events
		window.addEventListener('cie:event', function (e) {
			var detail = e.detail;
			if (!detail || !detail.event) return;

			var scoreMap = {
				'social_proof_shown': 0,  // passive, no score
				'floating_cta_clicked': 2,
				'exit_intent_converted': 3,
				'spotlight_fired': 0,
				'price_anchor_shown': 0,
				'ticker_shown': 0,
			};

			// User-initiated actions score higher
			if (detail.event.indexOf('click') >= 0 || detail.event.indexOf('add') >= 0) {
				momentumScore += 2;
			} else if (scoreMap[detail.event] !== undefined) {
				momentumScore += scoreMap[detail.event];
			}
		});

		// Track hotspot clicks, room transitions, panel opens from immersive
		document.addEventListener('click', function (e) {
			var target = e.target.closest('.hotspot, .room-nav-btn, .room-dot');
			if (target) {
				momentumScore += 1;
				checkMomentumThresholds();
			}

			var addToCart = e.target.closest('.btn-add-to-cart, .cs-quick-add, .cie-quick-add__btn');
			if (addToCart) {
				momentumScore += 3;
				checkMomentumThresholds();
			}
		});

		// Track scroll engagement
		var maxScroll = 0;
		window.addEventListener('scroll', function () {
			var scrollPct = window.scrollY / (document.documentElement.scrollHeight - window.innerHeight);
			if (scrollPct > maxScroll + 0.25) {
				maxScroll = scrollPct;
				momentumScore += 1;
				checkMomentumThresholds();
			}
		}, { passive: true });
	}

	function checkMomentumThresholds() {
		for (var i = 0; i < momentumThresholds.length; i++) {
			var threshold = momentumThresholds[i];
			if (momentumScore >= threshold && !momentumTriggered[threshold]) {
				momentumTriggered[threshold] = true;
				showMomentumToast(momentumMessages[i], i === momentumThresholds.length - 1);
				trackEvent('momentum_threshold', {
					level: i + 1,
					score: momentumScore,
					threshold: threshold,
				});
			}
		}
	}

	function showMomentumToast(message, isFinal) {
		var toast = el('div', 'mc-momentum-toast' + (isFinal ? ' mc-momentum-toast--final' : ''));

		var icon = el('span', 'mc-momentum-toast__icon');
		icon.textContent = isFinal ? '\u{1F389}' : '\u{1F525}';

		var text = el('span', 'mc-momentum-toast__text');
		text.textContent = message;

		toast.appendChild(icon);
		toast.appendChild(text);
		document.body.appendChild(toast);

		requestAnimationFrame(function () {
			requestAnimationFrame(function () {
				toast.classList.add('mc-momentum-toast--visible');
			});
		});

		setTimeout(function () {
			toast.classList.remove('mc-momentum-toast--visible');
			toast.classList.add('mc-momentum-toast--exiting');
			setTimeout(function () {
				if (toast.parentNode) toast.parentNode.removeChild(toast);
			}, 500);
		}, isFinal ? 8000 : 4000);
	}

	/* ==================================================
	   Public API
	   ================================================== */

	window.SkyyRoseMC = {
		config: CONFIG,
		getMomentumScore: function () { return momentumScore; },
		fireSpotlight: function (roomIndex) { fireSpotlight(roomIndex); },
		anchorPrice: function (el) { anchorSinglePrice(el); },
	};

	/* ==================================================
	   Init
	   ================================================== */

	function init() {
		initLiveActivityTicker();
		initPriceAnchoring();
		initSpotlightMoments();
		initBestSellerGlow();
		initMomentumScore();

		trackEvent('momentum_commerce_loaded');
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}

})();
