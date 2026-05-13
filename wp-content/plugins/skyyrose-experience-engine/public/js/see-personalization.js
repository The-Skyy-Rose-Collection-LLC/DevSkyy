/**
 * Personalization Engine — Affinity Scoring & Curated For You
 *
 * Tracks collection affinity in localStorage, builds a visitor profile,
 * and renders a "Curated For You" product section. Upgrades to ML-powered
 * recommendations when the FastAPI backend is available.
 *
 * Extends the theme's adaptive-personalization.js BehaviorTracker pattern
 * (sr_behavior storage key, heat score weighting).
 *
 * @package SkyyRose_Experience_Engine
 * @since   1.0.0
 */

(function () {
	'use strict';

	var SEE = window.SkyyRoseExperience;
	if (!SEE) {
		return;
	}

	/* ==========================================================================
	   Configuration
	   ========================================================================== */

	var CONFIG = {
		maxRecommendations: 8,
		affinityDecay:      0.95,   // Daily decay factor for scores
		visitThreshold:     2,      // Visits before showing "Welcome back"
		fetchTimeout:       5000,   // ms before giving up on REST call
	};

	/* ==========================================================================
	   Visitor Profile (localStorage-based, anonymous)
	   ========================================================================== */

	var PROFILE_KEY = 'profile';

	function getProfile() {
		var profile = SEE.storage.get(PROFILE_KEY);
		if (!profile) {
			profile = {
				hash: generateHash(),
				visits: 0,
				firstSeen: Date.now(),
				lastSeen: Date.now(),
				affinity: {},       // { 'black-rose': 12, 'signature': 5 }
				recentProducts: [], // Last 10 viewed product SKUs
				returningGreeted: false,
			};
		}
		return profile;
	}

	function saveProfile(profile) {
		profile.lastSeen = Date.now();
		SEE.storage.set(PROFILE_KEY, profile);
	}

	function generateHash() {
		var array = new Uint8Array(16);
		if (window.crypto) {
			window.crypto.getRandomValues(array);
		} else {
			for (var i = 0; i < 16; i++) {
				array[i] = Math.floor(Math.random() * 256);
			}
		}
		return Array.from(array, function (b) { return b.toString(16).padStart(2, '0'); }).join('');
	}

	/* ==========================================================================
	   Affinity Tracking
	   ========================================================================== */

	function trackAffinity(collection, weight) {
		if (!collection) {
			return;
		}

		var profile = getProfile();
		var current = profile.affinity[collection] || 0;
		profile.affinity[collection] = current + (weight || 1);
		saveProfile(profile);

		SEE.emit('personalization:affinity', {
			collection: collection,
			score: profile.affinity[collection],
		});
	}

	function trackProductView(sku) {
		if (!sku) {
			return;
		}

		var profile = getProfile();
		// Remove if already in list, add to front.
		profile.recentProducts = profile.recentProducts.filter(function (s) { return s !== sku; });
		profile.recentProducts.unshift(sku);
		// Keep last 10.
		if (profile.recentProducts.length > 10) {
			profile.recentProducts = profile.recentProducts.slice(0, 10);
		}
		saveProfile(profile);
	}

	function getTopCollection() {
		var profile = getProfile();
		var top = null;
		var maxScore = 0;

		Object.keys(profile.affinity).forEach(function (col) {
			if (profile.affinity[col] > maxScore) {
				maxScore = profile.affinity[col];
				top = col;
			}
		});

		return top;
	}

	/* ==========================================================================
	   Returning Visitor Recognition
	   ========================================================================== */

	function handleReturningVisitor() {
		var profile = getProfile();
		profile.visits++;

		// Apply daily decay to affinity scores.
		var daysSinceLastVisit = (Date.now() - profile.lastSeen) / (1000 * 60 * 60 * 24);
		if (daysSinceLastVisit > 1) {
			var decayFactor = Math.pow(CONFIG.affinityDecay, Math.floor(daysSinceLastVisit));
			Object.keys(profile.affinity).forEach(function (col) {
				profile.affinity[col] = Math.round(profile.affinity[col] * decayFactor);
			});
		}

		saveProfile(profile);

		if (profile.visits >= CONFIG.visitThreshold && !profile.returningGreeted) {
			var topCollection = getTopCollection();
			SEE.emit('personalization:returning', {
				visits: profile.visits,
				topCollection: topCollection,
			});
			profile.returningGreeted = true;
			saveProfile(profile);
		}
	}

	/* ==========================================================================
	   Curated For You Section
	   ========================================================================== */

	function renderCuratedSection() {
		var containers = document.querySelectorAll('.see-curated-section');
		if (containers.length === 0) {
			return;
		}

		var profile = getProfile();
		var topCollection = getTopCollection();
		var config = SEE.getConfig();

		// Build URL for recommendations.
		var url = (config.restUrl || '/wp-json/see/v1/') +
			'personalization/' + profile.hash +
			'?limit=' + CONFIG.maxRecommendations;

		if (topCollection) {
			url += '&collection=' + encodeURIComponent(topCollection);
		}

		fetch(url, {
			headers: { 'X-WP-Nonce': config.restNonce || '' },
			signal: AbortSignal.timeout ? AbortSignal.timeout(CONFIG.fetchTimeout) : undefined,
		})
			.then(function (res) { return res.json(); })
			.then(function (data) {
				var products = data.products || [];
				if (products.length === 0) {
					containers.forEach(function (c) { c.remove(); });
					return;
				}

				containers.forEach(function (container) {
					container.innerHTML = buildCuratedHTML(products, data.source, topCollection);
					container.classList.add('see-curated-loaded');
					SEE.emit('personalization:curated-rendered', { count: products.length });
				});
			})
			.catch(function () {
				// Remove skeleton on failure.
				containers.forEach(function (c) {
					c.querySelector('.see-skeleton')?.remove();
				});
			});
	}

	function buildCuratedHTML(products, source, collection) {
		var heading = collection
			? 'Curated For You — ' + formatCollectionName(collection)
			: 'Curated For You';

		var html = '<div class="see-curated-inner">';
		html += '<h3 class="see-curated-heading">' + escapeHtml(heading) + '</h3>';
		if (source === 'ml') {
			html += '<span class="see-curated-badge">AI Powered</span>';
		}
		html += '<div class="see-curated-grid">';

		products.forEach(function (p) {
			html += '<a href="' + escapeHtml(p.permalink || '#') + '" class="see-curated-item" data-see-collection="' + escapeHtml(p.collection || '') + '">';
			if (p.image) {
				html += '<img src="' + escapeHtml(p.image) + '" alt="' + escapeHtml(p.name || '') + '" loading="lazy" />';
			}
			html += '<span class="see-curated-name">' + escapeHtml(p.name || '') + '</span>';
			if (p.price) {
				html += '<span class="see-curated-price">$' + escapeHtml(String(p.price)) + '</span>';
			}
			html += '</a>';
		});

		html += '</div></div>';
		return html;
	}

	function formatCollectionName(slug) {
		return slug.replace(/-/g, ' ').replace(/\b\w/g, function (c) { return c.toUpperCase(); });
	}

	function escapeHtml(str) {
		var div = document.createElement('div');
		div.appendChild(document.createTextNode(str));
		return div.innerHTML;
	}

	/* ==========================================================================
	   Event Listeners — Track behavior from other modules
	   ========================================================================== */

	function bindEvents() {
		var ctx = SEE.getContext();

		// Track collection affinity from current page.
		if (ctx.collection) {
			trackAffinity(ctx.collection, 2);
		}

		// Track product view.
		if (ctx.productSku) {
			trackProductView(ctx.productSku);
		}

		// Listen for behavior events from Experience Analyzer.
		SEE.on('behavior:hover', function (data) {
			// Boost affinity when hovering products in a collection context.
			if (ctx.collection) {
				trackAffinity(ctx.collection, 0.5);
			}
		});

		SEE.on('showcase:quick-view', function (data) {
			if (data.collection) {
				trackAffinity(data.collection, 3);
			}
		});
	}

	/* ==========================================================================
	   Module Registration
	   ========================================================================== */

	SEE.registerModule('personalization', {
		init: function (moduleConfig) {
			Object.assign(CONFIG, moduleConfig);
		},

		ready: function () {
			handleReturningVisitor();
			bindEvents();

			// Render curated section after a small delay to not block LCP.
			if (SEE.supportsIdleCallback) {
				requestIdleCallback(renderCuratedSection, { timeout: 3000 });
			} else {
				setTimeout(renderCuratedSection, 1000);
			}
		},

		destroy: function () {
			// No cleanup needed — localStorage persists.
		},
	});

	// Expose for theme integration.
	SEE.personalization = {
		getProfile:       getProfile,
		getTopCollection: getTopCollection,
		trackAffinity:    trackAffinity,
	};

})();
