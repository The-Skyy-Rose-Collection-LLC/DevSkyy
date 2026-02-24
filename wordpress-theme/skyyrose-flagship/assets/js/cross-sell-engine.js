/**
 * Cross-Sell Engine — "Complete the Look"
 *
 * Watches the immersive product panel for visibility changes. When a hotspot
 * panel opens, it harvests all sibling products from the same collection's
 * hotspot beacons, injects a "Complete the Look" section beneath the size
 * selector, and fires a rose-gold particle celebration when a Quick Add
 * button is clicked.
 *
 * No external dependencies. Pure vanilla JS, IIFE-wrapped, strict mode.
 *
 * Engagement events are accumulated in window.SkyyRoseCrossSell.analytics so
 * they can be read by any future analytics pipeline without coupling this file
 * to a specific backend.
 *
 * Data source: hotspot [data-*] attributes on the immersive scene page.
 *   data-product-id
 *   data-product-name
 *   data-product-price
 *   data-product-image
 *   data-product-collection
 *   data-product-sizes
 *   data-product-url
 *
 * @package SkyyRose_Flagship
 * @since   3.7.0
 */

(function () {
	'use strict';

	/* --------------------------------------------------
	   Public API namespace — exposes analytics to the
	   outer page without polluting the global scope.
	   -------------------------------------------------- */

	window.SkyyRoseCrossSell = window.SkyyRoseCrossSell || {
		analytics: {
			panelViews:   0,   // times the cross-sell section was rendered
			cardViews:    {},  // { sku: count } — incremented per unique render
			quickAddClicks: {}, // { sku: count } — incremented per click
		},
		/** Programmatically refresh cross-sell for a given panel open event. */
		refresh: function () {
			injectCrossSell();
		},
	};

	var analytics = window.SkyyRoseCrossSell.analytics;

	/* --------------------------------------------------
	   Configuration
	   -------------------------------------------------- */

	var CFG = {
		maxRecs:          3,     // max cross-sell recommendations to show
		particleCount:    18,    // per Quick Add burst
		particleDuration: 800,   // ms before particle DOM nodes are removed
		sectionId:        'sr-cross-sell-section',
		panelSelector:    '.product-panel',
		panelOpenClass:   'open',
		sizesSelector:    '.product-panel-sizes',
		panelInfoSelector:'.product-panel-info',
		// MutationObserver watches the panel element for class changes.
		observeTarget:    '.product-panel',
	};

	/* --------------------------------------------------
	   Rose gold / collection colour palette for particles
	   -------------------------------------------------- */

	var PARTICLE_COLOURS = [
		'#B76E79', // rose gold
		'#D4AF37', // gold
		'#E8C4C4', // blush
		'#C49A6C', // champagne
		'#F5E6E8', // soft pink
		'#9B5563', // deep rose
	];

	/* --------------------------------------------------
	   State
	   -------------------------------------------------- */

	var currentSku        = null; // SKU of the product currently open in the panel
	var currentCollection = null; // collection name of the open product
	var allProducts       = [];   // harvested once from all visible hotspots

	/* --------------------------------------------------
	   Harvest product catalogue from hotspot beacons
	   -------------------------------------------------- */

	/**
	 * Walk every .hotspot element on the page and build a deduplicated
	 * product catalogue from their data attributes.
	 *
	 * Called once after DOMContentLoaded; the list is stable for the
	 * lifetime of the page (multi-room pages don't reload the DOM).
	 */
	function harvestProducts() {
		var hotspots = Array.from(document.querySelectorAll('.hotspot[data-product-id]'));

		var seen = {};

		hotspots.forEach(function (hotspot) {
			var sku = hotspot.dataset.productId;
			if (!sku || seen[sku]) return;
			seen[sku] = true;

			allProducts.push({
				sku:        sku,
				name:       hotspot.dataset.productName  || '',
				price:      hotspot.dataset.productPrice || '',
				image:      hotspot.dataset.productImage || '',
				collection: hotspot.dataset.productCollection || '',
				sizes:      hotspot.dataset.productSizes || '',
				url:        hotspot.dataset.productUrl   || '#',
			});
		});
	}

	/* --------------------------------------------------
	   Recommendation logic
	   -------------------------------------------------- */

	/**
	 * Return up to CFG.maxRecs products from the same collection,
	 * excluding the product currently shown in the main panel.
	 *
	 * A Fisher-Yates shuffle ensures the picks feel fresh between opens.
	 *
	 * @param  {string} collection  Collection name to match.
	 * @param  {string} excludeSku  SKU to omit.
	 * @return {Array}              Recommended product objects.
	 */
	function getRecommendations(collection, excludeSku) {
		var pool = allProducts.filter(function (p) {
			return p.collection === collection && p.sku !== excludeSku;
		});

		// Fisher-Yates shuffle (immutable: copy first).
		var shuffled = pool.slice();
		for (var i = shuffled.length - 1; i > 0; i--) {
			var j = Math.floor(Math.random() * (i + 1));
			var tmp = shuffled[i];
			shuffled[i] = shuffled[j];
			shuffled[j] = tmp;
		}

		return shuffled.slice(0, CFG.maxRecs);
	}

	/* --------------------------------------------------
	   Panel observation — detect open / close
	   -------------------------------------------------- */

	/**
	 * Set up a MutationObserver that watches for the `open` class being
	 * added to or removed from the product panel.
	 */
	function initObserver() {
		var panel = document.querySelector(CFG.observeTarget);
		if (!panel) return;

		var observer = new MutationObserver(function (mutations) {
			mutations.forEach(function (mutation) {
				if (mutation.type !== 'attributes' || mutation.attributeName !== 'class') return;

				var isOpen = panel.classList.contains(CFG.panelOpenClass);
				if (isOpen) {
					// Defer one microtask so immersive.js finishes populating
					// the panel's text nodes before we read them.
					requestAnimationFrame(function () {
						syncCurrentProduct(panel);
						injectCrossSell();
					});
				} else {
					removeCrossSell();
				}
			});
		});

		observer.observe(panel, { attributes: true });
	}

	/**
	 * Read the panel's current state to update currentSku / currentCollection.
	 * We derive these from the panel's rendered text nodes rather than keeping
	 * a parallel state, so this file stays decoupled from immersive.js internals.
	 *
	 * @param {Element} panel
	 */
	function syncCurrentProduct(panel) {
		// The collection label is the quickest canonical identifier.
		var collectionEl = panel.querySelector('.product-panel-collection');
		var nameEl       = panel.querySelector('.product-panel-name');

		currentCollection = collectionEl ? collectionEl.textContent.trim() : null;

		// Match the open product's SKU by name against the harvested catalogue.
		var openName = nameEl ? nameEl.textContent.trim() : '';
		var match = allProducts.find(function (p) {
			return p.name === openName;
		});
		currentSku = match ? match.sku : null;
	}

	/* --------------------------------------------------
	   DOM injection — build the "Complete the Look" section
	   -------------------------------------------------- */

	/**
	 * Build and insert the cross-sell section beneath the size selector.
	 * If a section already exists from a previous open, remove it first.
	 */
	function injectCrossSell() {
		if (!currentCollection) return;

		var recs = getRecommendations(currentCollection, currentSku);
		if (recs.length === 0) return;

		// Remove any stale section.
		removeCrossSell();

		var section = buildSection(recs);

		// Anchor: insert after .product-panel-sizes, or fall back to end of .product-panel-info.
		var anchor = document.querySelector(CFG.sizesSelector);
		var info   = document.querySelector(CFG.panelInfoSelector);

		if (anchor && anchor.parentNode) {
			anchor.parentNode.insertBefore(section, anchor.nextSibling);
		} else if (info) {
			info.appendChild(section);
		} else {
			// Last-resort: append to panel body.
			var panel = document.querySelector(CFG.panelSelector);
			if (panel) panel.appendChild(section);
		}

		// Track engagement.
		analytics.panelViews += 1;
		recs.forEach(function (p) {
			analytics.cardViews[p.sku] = (analytics.cardViews[p.sku] || 0) + 1;
		});

		// Trigger slide-in animation on next frame.
		requestAnimationFrame(function () {
			section.classList.add('cs-visible');
		});
	}

	/**
	 * Remove the cross-sell section from the DOM.
	 */
	function removeCrossSell() {
		var existing = document.getElementById(CFG.sectionId);
		if (existing) {
			existing.parentNode.removeChild(existing);
		}
	}

	/**
	 * Build the full "Complete the Look" section element.
	 *
	 * @param  {Array}   recs  Product recommendation objects.
	 * @return {Element}       Fully constructed section node.
	 */
	function buildSection(recs) {
		var section = document.createElement('div');
		section.id        = CFG.sectionId;
		section.className = 'cs-section';
		section.setAttribute('aria-label', 'Complete the Look');

		// Heading
		var heading = document.createElement('p');
		heading.className   = 'cs-heading';
		heading.textContent = 'Complete the Look';
		section.appendChild(heading);

		// Scroll track
		var track = document.createElement('div');
		track.className = 'cs-track';
		track.setAttribute('role', 'list');

		recs.forEach(function (product) {
			track.appendChild(buildCard(product));
		});

		section.appendChild(track);
		return section;
	}

	/**
	 * Build a single product recommendation card.
	 *
	 * @param  {Object}  product  Product data object from the catalogue.
	 * @return {Element}          Card element.
	 */
	function buildCard(product) {
		var card = document.createElement('div');
		card.className = 'cs-card';
		card.setAttribute('role', 'listitem');
		card.setAttribute('data-sku', product.sku);

		// Thumbnail wrapper
		var thumbWrap = document.createElement('div');
		thumbWrap.className = 'cs-thumb';

		if (product.image) {
			var img = document.createElement('img');
			img.src   = product.image;
			img.alt   = product.name;
			img.loading = 'lazy';
			img.className = 'cs-thumb-img';
			// Graceful degradation: show placeholder on error.
			img.addEventListener('error', function () {
				img.style.display = 'none';
				var fallback = buildThumbPlaceholder(product.name);
				thumbWrap.appendChild(fallback);
			});
			thumbWrap.appendChild(img);
		} else {
			thumbWrap.appendChild(buildThumbPlaceholder(product.name));
		}

		// Product link wrapping thumb
		var thumbLink = document.createElement('a');
		thumbLink.href      = product.url;
		thumbLink.className = 'cs-thumb-link';
		thumbLink.setAttribute('aria-label', 'View ' + product.name);
		thumbLink.appendChild(thumbWrap);
		card.appendChild(thumbLink);

		// Product name
		var nameEl = document.createElement('p');
		nameEl.className   = 'cs-name';
		nameEl.textContent = product.name;
		card.appendChild(nameEl);

		// Price
		var priceEl = document.createElement('p');
		priceEl.className   = 'cs-price';
		priceEl.textContent = product.price;
		card.appendChild(priceEl);

		// Quick Add button
		var btn = document.createElement('button');
		btn.type      = 'button';
		btn.className = 'cs-quick-add';
		btn.textContent = 'Quick Add';
		btn.setAttribute('aria-label', 'Quick add ' + product.name + ' to cart');
		btn.addEventListener('click', function (e) {
			handleQuickAdd(e, product, btn);
		});
		card.appendChild(btn);

		return card;
	}

	/**
	 * Build a lettered placeholder thumbnail for products without images.
	 *
	 * @param  {string}  name  Product name (used for initials).
	 * @return {Element}
	 */
	function buildThumbPlaceholder(name) {
		var placeholder = document.createElement('div');
		placeholder.className = 'cs-thumb-placeholder';

		// Extract up to 2 initials.
		var words    = (name || '').split(/\s+/).filter(Boolean);
		var initials = words.slice(0, 2).map(function (w) { return w[0].toUpperCase(); }).join('');
		placeholder.textContent = initials || 'SR';

		return placeholder;
	}

	/* --------------------------------------------------
	   Quick Add handler
	   -------------------------------------------------- */

	/**
	 * Handle Quick Add button click:
	 *   1. Attempt WooCommerce AJAX add-to-cart.
	 *   2. Fire particle celebration from button origin.
	 *   3. Track analytics event.
	 *
	 * @param {Event}   e        Click event.
	 * @param {Object}  product  Product data.
	 * @param {Element} btn      The clicked button element.
	 */
	function handleQuickAdd(e, product, btn) {
		e.stopPropagation();

		// Analytics.
		analytics.quickAddClicks[product.sku] = (analytics.quickAddClicks[product.sku] || 0) + 1;

		// Particle celebration — fires immediately for instant delight.
		fireParticles(btn);

		// Attempt WooCommerce AJAX add to cart.
		var wcUrl = getWcAjaxUrl();
		if (wcUrl && product.sku) {
			btn.disabled = true;
			var originalText = btn.textContent;
			btn.textContent = 'Adding…';

			var xhr = new XMLHttpRequest();
			xhr.open('POST', wcUrl, true);
			xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
			xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');

			xhr.onload = function () {
				btn.disabled = false;
				if (xhr.status >= 200 && xhr.status < 300) {
					try {
						var resp = JSON.parse(xhr.responseText);
						if (!resp.error) {
							btn.textContent = 'Added!';
							btn.classList.add('cs-quick-add--added');
							// Trigger WooCommerce cart fragment refresh.
							if (typeof jQuery !== 'undefined') {
								jQuery(document.body).trigger('wc_fragment_refresh');
							}
							setTimeout(function () {
								btn.textContent = originalText;
								btn.classList.remove('cs-quick-add--added');
							}, 2200);
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

			// Use product SKU as the product identifier since that is what
			// the immersive templates store in data-product-id.
			var body = 'wc-ajax=add_to_cart' +
				'&product_id=' + encodeURIComponent(product.sku) +
				'&quantity=1';

			xhr.send(body);
		} else {
			// WooCommerce not available — visual feedback only.
			btn.textContent = 'Added!';
			btn.classList.add('cs-quick-add--added');
			setTimeout(function () {
				btn.textContent = 'Quick Add';
				btn.classList.remove('cs-quick-add--added');
			}, 2200);
		}
	}

	/* --------------------------------------------------
	   WooCommerce AJAX URL helper
	   (mirrors the helper in immersive.js so this file
	    works standalone without importing immersive.js)
	   -------------------------------------------------- */

	function getWcAjaxUrl() {
		if (typeof wc_add_to_cart_params !== 'undefined' && wc_add_to_cart_params.wc_ajax_url) {
			return wc_add_to_cart_params.wc_ajax_url.toString().replace('%%endpoint%%', 'add_to_cart');
		}
		if (document.body.classList.contains('woocommerce') ||
			document.body.classList.contains('woocommerce-page')) {
			return window.location.origin + '/';
		}
		return null;
	}

	/* --------------------------------------------------
	   Particle celebration engine
	   -------------------------------------------------- */

	/**
	 * Burst CFG.particleCount particles from the centre of `originEl`.
	 * Particles are absolutely positioned on document.body and cleaned up
	 * after CFG.particleDuration ms to keep DOM lean.
	 *
	 * @param {Element} originEl  The element to originate the burst from.
	 */
	function fireParticles(originEl) {
		var rect    = originEl.getBoundingClientRect();
		var originX = rect.left + rect.width  / 2 + window.scrollX;
		var originY = rect.top  + rect.height / 2 + window.scrollY;

		// Reuse or create the particle container so we don't thrash body children.
		var container = document.getElementById('sr-particle-layer');
		if (!container) {
			container = document.createElement('div');
			container.id             = 'sr-particle-layer';
			container.style.cssText  =
				'position:absolute;top:0;left:0;width:0;height:0;' +
				'pointer-events:none;z-index:9999;overflow:visible;';
			document.body.appendChild(container);
		}

		for (var i = 0; i < CFG.particleCount; i++) {
			container.appendChild(createParticle(originX, originY, i));
		}

		// Prune old particles after animation completes.
		setTimeout(function () {
			var old = container.querySelectorAll('.sr-particle');
			Array.from(old).forEach(function (p) {
				if (p.parentNode) p.parentNode.removeChild(p);
			});
		}, CFG.particleDuration + 100);
	}

	/**
	 * Create a single particle element with randomised trajectory and colour.
	 *
	 * @param  {number}  ox     Origin X (page coords).
	 * @param  {number}  oy     Origin Y (page coords).
	 * @param  {number}  index  Particle index (used to distribute angles).
	 * @return {Element}
	 */
	function createParticle(ox, oy, index) {
		var p = document.createElement('span');
		p.className = 'sr-particle';

		// Random size: 4–9 px.
		var size = 4 + Math.random() * 5;

		// Distribute angle evenly then add jitter so burst looks organic.
		var baseAngle  = (index / CFG.particleCount) * 360;
		var jitter     = (Math.random() - 0.5) * 40;
		var angle      = (baseAngle + jitter) * (Math.PI / 180);

		// Variable travel distance: 40–90 px.
		var distance   = 40 + Math.random() * 50;
		var dx         = Math.cos(angle) * distance;
		var dy         = Math.sin(angle) * distance;

		// Random colour from palette.
		var colour     = PARTICLE_COLOURS[Math.floor(Math.random() * PARTICLE_COLOURS.length)];

		// Alternate between circles and slim rectangles for variety.
		var isCircle   = Math.random() > 0.45;
		var borderRadius = isCircle ? '50%' : '2px';

		p.style.cssText = [
			'position:absolute',
			'left:' + ox + 'px',
			'top:'  + oy + 'px',
			'width:'  + size + 'px',
			'height:' + size + 'px',
			'border-radius:' + borderRadius,
			'background:' + colour,
			'opacity:1',
			'pointer-events:none',
			// CSS custom properties drive the keyframe animation.
			'--cs-dx:' + dx.toFixed(1) + 'px',
			'--cs-dy:' + dy.toFixed(1) + 'px',
			'animation:srParticleBurst ' + CFG.particleDuration + 'ms cubic-bezier(.22,1,.36,1) forwards',
		].join(';');

		return p;
	}

	/* --------------------------------------------------
	   Inject particle keyframe into <head> once
	   -------------------------------------------------- */

	function injectParticleKeyframe() {
		if (document.getElementById('sr-particle-keyframe')) return;

		var style = document.createElement('style');
		style.id  = 'sr-particle-keyframe';
		// Uses CSS custom properties set inline per-particle.
		style.textContent = [
			'@keyframes srParticleBurst {',
			'  0%   { transform: translate(0, 0) scale(1);   opacity: 1; }',
			'  60%  { opacity: 0.9; }',
			'  100% { transform: translate(var(--cs-dx), var(--cs-dy)) scale(0);',
			'         opacity: 0; }',
			'}',
		].join('\n');
		document.head.appendChild(style);
	}

	/* --------------------------------------------------
	   Initialisation
	   -------------------------------------------------- */

	function init() {
		// Only run on immersive scene pages.
		if (!document.querySelector('.immersive-scene')) return;

		injectParticleKeyframe();
		harvestProducts();
		initObserver();
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}

})();
