/**
 * Smart Showcase — 3D Tilt Cards, Quick View, Hover Zoom
 *
 * Interactive product cards with:
 *   1. 3D perspective tilt on mouse move
 *   2. Quick-view dialog on click/tap
 *   3. Hover zoom on product images
 *   4. Collection-aware accent colors (via data-see-collection)
 *
 * Follows the magnetic-obsidian.js and interactive-cards.js patterns
 * from the existing theme.
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
		tiltMaxAngle:   8,       // Max rotation degrees
		tiltPerspective: 1000,   // CSS perspective value
		tiltScale:       1.02,   // Scale on hover
		tiltDuration:    300,    // Reset transition ms
		zoomScale:       1.5,    // Image zoom factor
		selector:        '.see-product-wrapper, .see-product-card, .product',
	};

	var tiltedCards = [];
	var dialog = null;

	/* ==========================================================================
	   3D Tilt Effect
	   ========================================================================== */

	function initTilt() {
		if (SEE.prefersReducedMotion) {
			return;
		}

		var cards = document.querySelectorAll(CONFIG.selector);
		cards.forEach(function (card) {
			if (card.classList.contains('see-tilt-init')) {
				return;
			}
			card.classList.add('see-tilt-init');
			card.style.transformStyle = 'preserve-3d';
			card.style.transition = 'transform ' + CONFIG.tiltDuration + 'ms ease';

			card.addEventListener('mousemove', function (e) {
				handleTilt(card, e);
			});

			card.addEventListener('mouseleave', function () {
				resetTilt(card);
			});

			tiltedCards.push(card);
		});
	}

	function handleTilt(card, e) {
		var rect = card.getBoundingClientRect();
		var x = e.clientX - rect.left;
		var y = e.clientY - rect.top;
		var centerX = rect.width / 2;
		var centerY = rect.height / 2;

		var rotateX = ((y - centerY) / centerY) * -CONFIG.tiltMaxAngle;
		var rotateY = ((x - centerX) / centerX) * CONFIG.tiltMaxAngle;

		card.style.transform =
			'perspective(' + CONFIG.tiltPerspective + 'px) ' +
			'rotateX(' + rotateX.toFixed(2) + 'deg) ' +
			'rotateY(' + rotateY.toFixed(2) + 'deg) ' +
			'scale3d(' + CONFIG.tiltScale + ', ' + CONFIG.tiltScale + ', 1)';
	}

	function resetTilt(card) {
		card.style.transform = 'perspective(' + CONFIG.tiltPerspective + 'px) rotateX(0) rotateY(0) scale3d(1, 1, 1)';
	}

	/* ==========================================================================
	   Hover Zoom on Product Images
	   ========================================================================== */

	function initHoverZoom() {
		if (SEE.prefersReducedMotion) {
			return;
		}

		var images = document.querySelectorAll('.see-product-wrapper img, .see-product-card img');
		images.forEach(function (img) {
			if (img.classList.contains('see-zoom-init')) {
				return;
			}
			img.classList.add('see-zoom-init');

			var wrapper = img.parentElement;
			wrapper.style.overflow = 'hidden';

			img.addEventListener('mousemove', function (e) {
				var rect = img.getBoundingClientRect();
				var x = ((e.clientX - rect.left) / rect.width) * 100;
				var y = ((e.clientY - rect.top) / rect.height) * 100;
				img.style.transformOrigin = x + '% ' + y + '%';
				img.style.transform = 'scale(' + CONFIG.zoomScale + ')';
			});

			img.addEventListener('mouseleave', function () {
				img.style.transform = 'scale(1)';
				img.style.transformOrigin = 'center center';
			});
		});
	}

	/* ==========================================================================
	   Quick View Dialog
	   ========================================================================== */

	function initQuickView() {
		dialog = document.getElementById('see-quick-view');
		if (!dialog) {
			return;
		}

		// Close button.
		var closeBtn = dialog.querySelector('.see-qv-close');
		if (closeBtn) {
			closeBtn.addEventListener('click', function () {
				dialog.close();
			});
		}

		// Close on backdrop click.
		dialog.addEventListener('click', function (e) {
			if (e.target === dialog) {
				dialog.close();
			}
		});

		// Close on Escape.
		dialog.addEventListener('keydown', function (e) {
			if (e.key === 'Escape') {
				dialog.close();
			}
		});

		// Add quick-view buttons to product cards.
		var cards = document.querySelectorAll(CONFIG.selector);
		cards.forEach(function (card) {
			if (card.querySelector('.see-qv-trigger')) {
				return;
			}

			var trigger = document.createElement('button');
			trigger.className = 'see-qv-trigger';
			trigger.textContent = 'Quick View';
			trigger.setAttribute('aria-label', 'Quick view product');

			trigger.addEventListener('click', function (e) {
				e.preventDefault();
				e.stopPropagation();
				openQuickView(card);
			});

			card.style.position = 'relative';
			card.appendChild(trigger);
		});
	}

	function openQuickView(card) {
		if (!dialog || !SEE.supportsDialog) {
			// Fallback: navigate to product page.
			var link = card.querySelector('a[href]');
			if (link) {
				window.location.href = link.href;
			}
			return;
		}

		// Extract product data from card's data attributes.
		var wrapper = card.closest('.see-product-wrapper') || card;
		var sku = wrapper.getAttribute('data-see-sku') || '';
		var collection = wrapper.getAttribute('data-see-collection') || '';
		var price = wrapper.getAttribute('data-see-price') || '';

		// Extract from card content.
		var img = card.querySelector('img');
		var title = card.querySelector('.woocommerce-loop-product__title, h2, h3');
		var link = card.querySelector('a[href]');
		var desc = card.querySelector('.woocommerce-product-details__short-description, .description');

		// Populate dialog.
		var qvImage = dialog.querySelector('.see-qv-image');
		var qvTitle = dialog.querySelector('.see-qv-title');
		var qvPrice = dialog.querySelector('.see-qv-price');
		var qvDesc = dialog.querySelector('.see-qv-description');
		var qvLink = dialog.querySelector('.see-qv-link');

		if (qvImage && img) {
			qvImage.innerHTML = '<img src="' + img.src + '" alt="' + (img.alt || '') + '" />';
		}
		if (qvTitle) {
			qvTitle.textContent = title ? title.textContent : sku;
		}
		if (qvPrice) {
			qvPrice.textContent = price ? '$' + price : '';
		}
		if (qvDesc && desc) {
			qvDesc.textContent = desc.textContent;
		}
		if (qvLink && link) {
			qvLink.href = link.href;
		}

		// Set collection accent.
		if (collection) {
			dialog.setAttribute('data-see-collection', collection);
		}

		dialog.showModal();
		SEE.emit('showcase:quick-view', { sku: sku, collection: collection });
	}

	/* ==========================================================================
	   Module Registration
	   ========================================================================== */

	SEE.registerModule('smart-showcase', {
		init: function (moduleConfig) {
			Object.assign(CONFIG, moduleConfig);
		},

		ready: function () {
			initTilt();
			initHoverZoom();
			initQuickView();
		},

		destroy: function () {
			tiltedCards.forEach(function (card) {
				card.style.transform = '';
				card.style.transformStyle = '';
			});
			tiltedCards = [];

			if (dialog && dialog.open) {
				dialog.close();
			}
		},
	});

})();
