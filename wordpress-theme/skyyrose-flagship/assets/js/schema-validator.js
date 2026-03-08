/**
 * Schema Validator — Dev-Mode JSON-LD Checker
 *
 * Scans the page for JSON-LD structured data and validates that
 * required fields are present for each schema type. Shows a
 * non-intrusive console report on every page load in dev mode.
 *
 * Only active when skyyRoseData.debug is true, on localhost,
 * or when ?schema_debug=1 is in the URL.
 *
 * WHY: Rich snippets (stars, price, availability) drive 30% more
 * click-through from Google SERPs. But broken structured data
 * silently loses this advantage. This validator catches missing
 * fields before Google's crawler does.
 *
 * @package SkyyRose_Flagship
 * @since   4.0.0
 */
(function () {
	'use strict';

	var isDev = (typeof skyyRoseData !== 'undefined' && skyyRoseData.debug) ||
	            location.hostname === 'localhost' ||
	            location.hostname.indexOf('.local') !== -1 ||
	            location.search.indexOf('schema_debug=1') !== -1;

	if (!isDev) {
		return;
	}

	// Required fields per schema type (Google's minimum for rich results).
	var requiredFields = {
		'Product': ['name', 'offers'],
		'Offer': ['price', 'priceCurrency', 'availability'],
		'Organization': ['name', 'url'],
		'BreadcrumbList': ['itemListElement'],
		'ListItem': ['position', 'name'],
		'CollectionPage': ['name', 'url'],
		'Review': ['author', 'reviewRating'],
		'AggregateRating': ['ratingValue', 'reviewCount']
	};

	// Recommended fields (warnings, not errors).
	var recommendedFields = {
		'Product': ['image', 'description', 'sku', 'brand'],
		'Organization': ['logo', 'description', 'sameAs'],
		'CollectionPage': ['description']
	};

	function validate() {
		var scripts = document.querySelectorAll('script[type="application/ld+json"]');

		if (scripts.length === 0) {
			console.warn('%c[Schema] No JSON-LD found on this page.', 'color:#ffa400;font-weight:bold');
			return;
		}

		var errors = 0;
		var warnings = 0;

		console.group('%c[Schema Validator] ' + scripts.length + ' JSON-LD block(s) found', 'color:#B76E79;font-weight:bold');

		for (var i = 0; i < scripts.length; i++) {
			try {
				var data = JSON.parse(scripts[i].textContent);
				var type = data['@type'];

				if (!type) {
					console.error('  Block ' + (i + 1) + ': Missing @type');
					errors++;
					continue;
				}

				console.groupCollapsed('%c  ' + type, 'color:#0cce6b');

				// Check required fields.
				var req = requiredFields[type] || [];
				for (var r = 0; r < req.length; r++) {
					if (!data[req[r]] && data[req[r]] !== 0) {
						console.error('    MISSING required: ' + req[r]);
						errors++;
					}
				}

				// Check recommended fields.
				var rec = recommendedFields[type] || [];
				for (var w = 0; w < rec.length; w++) {
					if (!data[rec[w]]) {
						console.warn('    MISSING recommended: ' + rec[w]);
						warnings++;
					}
				}

				// Validate nested offers for Product.
				if (type === 'Product' && data.offers) {
					var offers = Array.isArray(data.offers) ? data.offers : [data.offers];
					for (var o = 0; o < offers.length; o++) {
						var offerReq = requiredFields['Offer'] || [];
						for (var or2 = 0; or2 < offerReq.length; or2++) {
							if (!offers[o][offerReq[or2]] && offers[o][offerReq[or2]] !== 0) {
								console.error('    Offer[' + o + '] MISSING required: ' + offerReq[or2]);
								errors++;
							}
						}
					}
				}

				// Validate BreadcrumbList items.
				if (type === 'BreadcrumbList' && data.itemListElement) {
					for (var b = 0; b < data.itemListElement.length; b++) {
						var item = data.itemListElement[b];
						if (!item.position) {
							console.error('    ListItem[' + b + '] MISSING position');
							errors++;
						}
						if (!item.name) {
							console.error('    ListItem[' + b + '] MISSING name');
							errors++;
						}
					}
				}

				console.groupEnd();
			} catch (e) {
				console.error('  Block ' + (i + 1) + ': Invalid JSON — ' + e.message);
				errors++;
			}
		}

		// Summary.
		if (errors === 0 && warnings === 0) {
			console.log('%c  All schema valid.', 'color:#0cce6b;font-weight:bold');
		} else {
			console.log(
				'%c  ' + errors + ' error(s), ' + warnings + ' warning(s)',
				(errors > 0 ? 'color:#ff4e42' : 'color:#ffa400') + ';font-weight:bold'
			);
		}

		console.groupEnd();
	}

	// Run after DOM is ready.
	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', validate);
	} else {
		validate();
	}

})();
