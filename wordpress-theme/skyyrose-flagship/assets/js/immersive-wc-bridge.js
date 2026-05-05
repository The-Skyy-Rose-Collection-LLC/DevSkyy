/**
 * SkyyRose Immersive — WooCommerce Bridge
 *
 * Wires the immersive scene's product panel "Pre-Order Now" button to the
 * skyyrose_immersive_add_to_cart AJAX endpoint (inc/immersive-ajax.php:213).
 *
 * Reads:
 *   - panel.dataset.currentProductSku (set by immersive.js:openPanel)
 *   - panel.dataset.currentProductId  (optional; numeric WC product ID)
 *   - .size-btn.selected.textContent  (optional; size pill the user picked)
 *
 * Uses:
 *   - window.skyyRoseImmersive.ajaxUrl
 *   - window.skyyRoseImmersive.nonce  (action: 'skyyrose-immersive-nonce')
 *   - window.skyyToast(msg, type)     (graceful fallback if missing)
 *
 * @package SkyyRose
 * @since   1.1.0
 */
(function () {
	'use strict';

	var cfg = window.skyyRoseImmersive || null;
	if (!cfg || !cfg.ajaxUrl || !cfg.nonce) {
		return; // Missing localization — bail silently.
	}

	function notify(msg, type) {
		if (typeof window.skyyToast === 'function') {
			window.skyyToast(msg, type || 'info', 3500);
			return;
		}
		// Fallback: reuse the immersive scene's notification element if present.
		var existing = document.querySelector('.immersive-cart-notification');
		var el = existing || document.createElement('div');
		if (!existing) {
			el.className = 'immersive-cart-notification';
			el.setAttribute('role', 'status');
			el.setAttribute('aria-live', 'polite');
			document.body.appendChild(el);
		}
		el.textContent = msg;
		el.classList.add('visible');
		setTimeout(function () { el.classList.remove('visible'); }, 3500);
	}

	function applyCartFragments(fragments) {
		if (!fragments) return;
		Object.keys(fragments).forEach(function (selector) {
			var html = fragments[selector];
			document.querySelectorAll(selector).forEach(function (node) {
				// Use a sandboxed parse: build a temp container, take the first
				// element, and replace the live node. Avoids innerHTML on the
				// live DOM.
				var tmp = document.createElement('div');
				tmp.innerHTML = html;
				var fresh = tmp.firstElementChild;
				if (fresh && node.parentNode) {
					node.parentNode.replaceChild(fresh, node);
				}
			});
		});
	}

	function getSelectedSize(panel) {
		if (!panel) return '';
		var selected = panel.querySelector('.size-btn.selected');
		return selected ? (selected.textContent || '').trim() : '';
	}

	function buildPayload(panel) {
		var body = new URLSearchParams();
		body.append('action', 'skyyrose_immersive_add_to_cart');
		body.append('nonce', cfg.nonce);
		body.append('quantity', '1');

		if (panel.dataset.currentProductId) {
			body.append('product_id', panel.dataset.currentProductId);
		}
		if (panel.dataset.currentProductSku) {
			body.append('sku', panel.dataset.currentProductSku);
		}
		var size = getSelectedSize(panel);
		if (size) {
			body.append('attribute_pa_size', size);
		}
		return body;
	}

	function setBusy(btn, busy) {
		if (!btn) return;
		btn.disabled = !!busy;
		btn.setAttribute('aria-busy', busy ? 'true' : 'false');
		if (busy) {
			btn.dataset.skyyOriginalLabel = btn.textContent;
			btn.textContent = 'Adding…';
		} else if (btn.dataset.skyyOriginalLabel) {
			btn.textContent = btn.dataset.skyyOriginalLabel;
			delete btn.dataset.skyyOriginalLabel;
		}
	}

	function handleSubmit(btn) {
		var panel = btn.closest('.product-panel');
		if (!panel) return;
		if (!panel.dataset.currentProductId && !panel.dataset.currentProductSku) {
			notify('Product unavailable. Please try again.', 'error');
			return;
		}

		setBusy(btn, true);

		fetch(cfg.ajaxUrl, {
			method: 'POST',
			credentials: 'same-origin',
			headers: { 'Accept': 'application/json' },
			body: buildPayload(panel)
		})
			.then(function (res) { return res.json(); })
			.then(function (json) {
				if (json && json.success) {
					var data = json.data || {};
					applyCartFragments(data.fragments);
					notify(data.message || 'Added to cart', 'success');
					// Notify any listeners (header badge, mini-cart, etc.).
					document.dispatchEvent(new CustomEvent('skyyrose:cart:updated', {
						detail: { count: data.cart_count, source: 'immersive' }
					}));
				} else {
					var msg = (json && json.data && json.data.message) || 'Could not add to cart.';
					notify(msg, 'error');
				}
			})
			.catch(function () {
				notify('Network error. Please try again.', 'error');
			})
			.then(function () {
				setBusy(btn, false);
			});
	}

	function init() {
		// Delegate so panels rendered later (or re-rendered) still bind.
		document.addEventListener('click', function (e) {
			var btn = e.target.closest('.product-panel .btn-add-to-cart');
			if (!btn) return;
			e.preventDefault();
			handleSubmit(btn);
		});
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}
})();
