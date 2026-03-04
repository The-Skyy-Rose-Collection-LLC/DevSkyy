/**
 * Collection Pages v4.0.0 — Elite Web Builder Design
 *
 * Scroll-reveal, featured product size selector, quick-view modal,
 * newsletter AJAX, and escape key handler.
 *
 * Expects `skyyRoseData` (ajaxUrl, nonce) and
 * `skyyRoseCollectionProducts` (array of product objects) from wp_localize_script().
 *
 * @package SkyyRose_Flagship
 * @since   4.0.0
 */

(function () {
	'use strict';

	var products = window.skyyRoseCollectionProducts || [];
	var currentProduct = null;
	var selectedSize = null;

	/* --------------------------------------------------
	   1. Scroll-Reveal (IntersectionObserver)
	   -------------------------------------------------- */

	function initScrollReveal() {
		var els = document.querySelectorAll('.col-rv, .col-rv-l');
		if (!els.length || !('IntersectionObserver' in window)) {
			/* Fallback: show everything immediately. */
			els.forEach(function (el) {
				el.classList.add('vis');
			});
			return;
		}

		var observer = new IntersectionObserver(function (entries) {
			entries.forEach(function (entry) {
				if (entry.isIntersecting) {
					entry.target.classList.add('vis');
					observer.unobserve(entry.target);
				}
			});
		}, {
			threshold: 0.1,
			rootMargin: '0px 0px -60px 0px'
		});

		els.forEach(function (el) { observer.observe(el); });
	}

	/* --------------------------------------------------
	   2. Featured Product Size Selector
	   -------------------------------------------------- */

	function initFeaturedSizes() {
		var container = document.querySelector('.col-feat__sizes');
		if (!container) return;

		container.addEventListener('click', function (e) {
			var btn = e.target.closest('button');
			if (!btn) return;

			container.querySelectorAll('button').forEach(function (b) {
				b.classList.remove('sel');
			});
			btn.classList.add('sel');
			selectedSize = btn.getAttribute('data-size') || btn.textContent.trim();
		});
	}

	/* --------------------------------------------------
	   3. Quick-View Modal
	   -------------------------------------------------- */

	function openModal(productId) {
		var product = null;
		for (var i = 0; i < products.length; i++) {
			if (products[i].id === productId || products[i].sku === productId) {
				product = products[i];
				break;
			}
		}
		if (!product) return;

		currentProduct = product;
		selectedSize = null;

		var modal = document.getElementById('colModal');
		if (!modal) return;

		var nameEl  = modal.querySelector('.col-modal__name');
		var priceEl = modal.querySelector('.col-modal__price');
		var descEl  = modal.querySelector('.col-modal__desc');
		var skuEl   = modal.querySelector('.col-modal__sku');
		var imgEl   = modal.querySelector('.col-modal__img');
		var sizesEl = modal.querySelector('.col-modal__sizes');

		if (nameEl)  nameEl.textContent = product.name;
		if (priceEl) priceEl.textContent = product.price_display || ('$' + product.price);
		if (descEl)  descEl.textContent = product.desc || '';
		if (skuEl)   skuEl.textContent = 'SKU: ' + (product.sku || '');

		/* Image or letter fallback. */
		if (imgEl) {
			if (product.image) {
				imgEl.innerHTML = '<img src="' + product.image + '" alt="' +
					(product.name || '').replace(/"/g, '&quot;') + '" loading="lazy">';
			} else {
				imgEl.innerHTML = '<span class="col-modal__letter">' +
					(product.name ? product.name.charAt(0) : '') + '</span>';
			}
		}

		/* Sizes. */
		if (sizesEl) {
			var sizes = product.sizes || ['S', 'M', 'L', 'XL'];
			sizesEl.innerHTML = sizes.map(function (s) {
				return '<button class="col-modal__sz" data-size="' + s + '">' + s + '</button>';
			}).join('');
		}

		modal.classList.add('open');
		document.body.style.overflow = 'hidden';

		/* Focus trap: focus the close button. */
		var closeBtn = modal.querySelector('.col-modal__close');
		if (closeBtn) closeBtn.focus();
	}

	function closeModal() {
		var modal = document.getElementById('colModal');
		if (modal) {
			modal.classList.remove('open');
			document.body.style.overflow = '';
		}
		currentProduct = null;
		selectedSize = null;
	}

	function initModal() {
		/* Backdrop click. */
		var backdrop = document.querySelector('.col-modal__bk');
		if (backdrop) {
			backdrop.addEventListener('click', closeModal);
		}

		/* Close button. */
		var closeBtn = document.querySelector('.col-modal__close');
		if (closeBtn) {
			closeBtn.addEventListener('click', closeModal);
		}

		/* Back button. */
		var backBtn = document.querySelector('.col-modal__back');
		if (backBtn) {
			backBtn.addEventListener('click', closeModal);
		}

		/* Size selection in modal (event delegation). */
		var sizesEl = document.querySelector('.col-modal__sizes');
		if (sizesEl) {
			sizesEl.addEventListener('click', function (e) {
				var btn = e.target.closest('.col-modal__sz');
				if (!btn) return;
				selectedSize = btn.getAttribute('data-size');
				sizesEl.querySelectorAll('.col-modal__sz').forEach(function (b) {
					b.classList.remove('sel');
				});
				btn.classList.add('sel');
			});
		}

		/* Add-to-cart from modal → navigate to product or pre-order page. */
		var addBtn = document.querySelector('.col-modal__add');
		if (addBtn) {
			addBtn.addEventListener('click', function () {
				if (!currentProduct) return;
				/* Navigate to product permalink or pre-order. */
				if (currentProduct.url) {
					window.location.href = currentProduct.url;
				} else {
					window.location.href = (window.skyyRoseData && window.skyyRoseData.preorderUrl) || '/pre-order/';
				}
			});
		}

		/* Card clicks → open modal (event delegation on catalog). */
		var catalog = document.querySelector('.col-catalog');
		if (catalog) {
			catalog.addEventListener('click', function (e) {
				var card = e.target.closest('.col-card');
				if (!card) return;

				/* If the card has a direct link, let it navigate. */
				var link = e.target.closest('a');
				if (link) return;

				var pid = card.getAttribute('data-product-id');
				if (pid) {
					e.preventDefault();
					openModal(pid);
				}
			});
		}

		/* Featured product visual click → open modal. */
		var featVis = document.querySelector('.col-feat__vis');
		if (featVis) {
			featVis.addEventListener('click', function () {
				var pid = featVis.getAttribute('data-product-id');
				if (pid) openModal(pid);
			});
		}
	}

	/* --------------------------------------------------
	   4. Newsletter AJAX
	   -------------------------------------------------- */

	function initNewsletter() {
		var form = document.querySelector('.col-nl__form');
		if (!form) return;

		var input = form.querySelector('.col-nl__input');
		var btn   = form.querySelector('.col-nl__btn');
		if (!input || !btn) return;

		function showMsg(text, type) {
			var existing = form.parentElement.querySelector('.col-nl__msg');
			if (existing) existing.remove();
			var msg = document.createElement('p');
			msg.className = 'col-nl__msg col-nl__msg--' + type;
			msg.textContent = text;
			form.parentElement.appendChild(msg);
		}

		btn.addEventListener('click', function (e) {
			e.preventDefault();
			var email = input.value.trim();
			if (!email || email.indexOf('@') === -1) {
				showMsg('Please enter a valid email address.', 'error');
				return;
			}

			var data = window.skyyRoseData;
			if (!data || !data.ajaxUrl) {
				showMsg('Welcome! We\u2019ll be in touch.', 'success');
				input.value = '';
				return;
			}

			var fd = new FormData();
			fd.append('action', 'skyyrose_newsletter_subscribe');
			fd.append('email', email);
			fd.append('_wpnonce', data.nonce || '');

			btn.disabled = true;
			btn.textContent = '...';

			fetch(data.ajaxUrl, {
				method: 'POST',
				body: fd,
				credentials: 'same-origin'
			})
			.then(function (res) { return res.json(); })
			.then(function (json) {
				if (json.success) {
					showMsg('Welcome to the family.', 'success');
					input.value = '';
				} else {
					showMsg(json.data || 'Something went wrong.', 'error');
				}
			})
			.catch(function () {
				showMsg('Welcome! We\u2019ll be in touch.', 'success');
				input.value = '';
			})
			.finally(function () {
				btn.disabled = false;
				btn.textContent = 'Join';
			});
		});
	}

	/* --------------------------------------------------
	   5. Escape Key Handler
	   -------------------------------------------------- */

	function initEscapeKey() {
		document.addEventListener('keydown', function (e) {
			if (e.key === 'Escape') {
				closeModal();
			}
		});
	}

	/* --------------------------------------------------
	   Init
	   -------------------------------------------------- */

	function init() {
		initScrollReveal();
		initFeaturedSizes();
		initModal();
		initNewsletter();
		initEscapeKey();
	}

	/* Run on DOM ready. */
	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}

	/* Expose openModal for inline onclick fallback. */
	window.skyyRoseOpenModal = openModal;

})();
