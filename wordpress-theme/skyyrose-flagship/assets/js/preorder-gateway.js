/**
 * Pre-Order Gateway Interactions
 *
 * Loading screen, collection tab filtering, product modal,
 * cart sidebar, sign-in panel, and wishlist toggling.
 *
 * @package SkyyRose_Flagship
 * @since   2.0.0
 */

(function () {
	'use strict';

	/* --------------------------------------------------
	   DOM References
	   -------------------------------------------------- */

	var loadingScreen = document.querySelector('.preorder-loading');
	var progressBar   = document.querySelector('.loading-progress-bar');

	// Collection tabs
	var tabs     = Array.from(document.querySelectorAll('.collection-tab'));
	var cards    = Array.from(document.querySelectorAll('.product-grid-card'));

	// Product modal
	var modalOverlay = document.querySelector('.product-modal-overlay');
	var modalClose   = document.querySelector('.product-modal-close');
	var modalImage   = modalOverlay ? modalOverlay.querySelector('.modal-360-area img') : null;
	var modalName    = modalOverlay ? modalOverlay.querySelector('.modal-product-name') : null;
	var modalCol     = modalOverlay ? modalOverlay.querySelector('.modal-product-collection') : null;
	var modalPrice   = modalOverlay ? modalOverlay.querySelector('.modal-product-price') : null;
	var modalDesc    = modalOverlay ? modalOverlay.querySelector('.modal-product-desc') : null;
	var modalSizes   = modalOverlay ? modalOverlay.querySelector('.modal-sizes') : null;
	var modalAddBtn  = modalOverlay ? modalOverlay.querySelector('.modal-add-to-cart') : null;

	// Cart sidebar
	var cartOverlay  = document.querySelector('.cart-sidebar-overlay');
	var cartSidebar  = document.querySelector('.cart-sidebar');
	var cartClose    = document.querySelector('.cart-sidebar-close');
	var cartBadge    = document.querySelector('.cart-count-badge');
	var cartTotal    = document.querySelector('.cart-total-amount');
	var cartList     = document.querySelector('.cart-items-list');
	var cartEmptyMsg = document.querySelector('.cart-empty-msg');
	var checkoutBtn  = document.querySelector('.cart-checkout-btn');

	// Sign-in panel
	var signinOverlay = document.querySelector('.signin-overlay');
	var signinPanel   = document.querySelector('.signin-panel');
	var signinClose   = document.querySelector('.signin-close');

	// Action buttons
	var actionBtns = Array.from(document.querySelectorAll('[data-action]'));

	// Cart state
	var cartItems = [];
	var cartCount = 0;
	var currentProductId = null;

	/* --------------------------------------------------
	   Loading Screen
	   -------------------------------------------------- */

	function initLoading() {
		if (!loadingScreen || !progressBar) return;

		var progress = 0;
		var interval = setInterval(function () {
			progress += Math.random() * 20 + 5;
			if (progress >= 100) {
				progress = 100;
				clearInterval(interval);
				setTimeout(function () {
					loadingScreen.classList.add('hidden');
				}, 400);
			}
			progressBar.style.width = progress + '%';
		}, 120);
	}

	/* --------------------------------------------------
	   Collection Tab Filtering
	   -------------------------------------------------- */

	function initTabs() {
		tabs.forEach(function (tab) {
			tab.addEventListener('click', function () {
				var collection = tab.dataset.collection;

				// Update active tab and ARIA state
				tabs.forEach(function (t) {
					t.classList.remove('active');
					t.setAttribute('aria-selected', 'false');
				});
				tab.classList.add('active');
				tab.setAttribute('aria-selected', 'true');

				// Filter cards
				cards.forEach(function (card) {
					if (collection === 'all' || card.dataset.collection === collection) {
						card.classList.remove('hidden');
					} else {
						card.classList.add('hidden');
					}
				});
			});
		});
	}

	/* --------------------------------------------------
	   Product Modal
	   -------------------------------------------------- */

	var previousFocusEl = null;
	var focusTrapHandler = null;
	var focusTrapContainer = null;

	function trapFocus(container) {
		var focusable = container.querySelectorAll(
			'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
		);
		if (focusable.length === 0) return;
		var first = focusable[0];
		var last  = focusable[focusable.length - 1];

		// Remove any previously attached handler to prevent accumulation.
		if (focusTrapHandler && focusTrapContainer) {
			focusTrapContainer.removeEventListener('keydown', focusTrapHandler);
		}

		focusTrapHandler = function (e) {
			if (e.key !== 'Tab') return;
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
		};

		focusTrapContainer = container;
		container.addEventListener('keydown', focusTrapHandler);
		first.focus();
	}

	function openModal(data) {
		if (!modalOverlay) return;

		if (modalImage) { modalImage.src = data.image || ''; modalImage.alt = data.name || ''; }
		if (modalName)  modalName.textContent = data.name || '';
		if (modalCol)   modalCol.textContent = data.collectionLabel || '';
		if (modalPrice) modalPrice.textContent = data.price || '';
		if (modalDesc)  modalDesc.textContent = data.desc || '';

		// Populate sizes
		if (modalSizes) {
			while (modalSizes.firstChild) {
				modalSizes.removeChild(modalSizes.firstChild);
			}
			var sizes = (data.sizes || '').split(',').filter(Boolean);
			sizes.forEach(function (size) {
				var btn = document.createElement('button');
				btn.type = 'button';
				btn.className = 'size-btn';
				btn.textContent = size.trim();
				btn.addEventListener('click', function () {
					modalSizes.querySelectorAll('.size-btn').forEach(function (b) {
						b.classList.remove('selected');
					});
					btn.classList.add('selected');
				});
				modalSizes.appendChild(btn);
			});
		}

		previousFocusEl = document.activeElement;
		modalOverlay.classList.add('open');
		modalOverlay.setAttribute('aria-hidden', 'false');
		var dialog = modalOverlay.querySelector('[role="dialog"]') || modalOverlay;
		dialog.setAttribute('aria-hidden', 'false');
		trapFocus(dialog);
	}

	function closeModal() {
		if (modalOverlay) {
			modalOverlay.classList.remove('open');
			modalOverlay.setAttribute('aria-hidden', 'true');
			var dialog = modalOverlay.querySelector('[role="dialog"]');
			if (dialog) dialog.setAttribute('aria-hidden', 'true');
			// Clean up focus trap handler to prevent accumulation.
			if (focusTrapHandler && focusTrapContainer) {
				focusTrapContainer.removeEventListener('keydown', focusTrapHandler);
				focusTrapHandler = null;
				focusTrapContainer = null;
			}
		}
		if (previousFocusEl) {
			previousFocusEl.focus();
			previousFocusEl = null;
		}
	}

	function initModal() {
		// Open modal from "View Details" button or card image click
		cards.forEach(function (card) {
			function openFromCard() {
				currentProductId = card.dataset.productId || null;
				openModal({
					name:            card.dataset.productName,
					price:           card.dataset.productPrice,
					image:           card.dataset.productImage,
					collectionLabel: card.dataset.productCollectionLabel,
					desc:            card.dataset.productDesc,
					sizes:           card.dataset.productSizes
				});
			}

			card.addEventListener('click', function (e) {
				// Only open on View Details button or image area, not wishlist
				if (e.target.closest('.product-grid-wishlist')) return;
				if (e.target.closest('.product-grid-view-btn') || e.target.closest('.product-grid-image')) {
					openFromCard();
				}
			});
		});

		if (modalClose) modalClose.addEventListener('click', closeModal);
		if (modalOverlay) {
			modalOverlay.addEventListener('click', function (e) {
				if (e.target === modalOverlay) closeModal();
			});
		}

		// Add to cart from modal
		if (modalAddBtn) {
			modalAddBtn.addEventListener('click', function () {
				var selectedSizeBtn = modalSizes ? modalSizes.querySelector('.size-btn.selected') : null;
				if (!selectedSizeBtn && modalSizes && modalSizes.children.length > 0) {
					// Auto-select first size if none selected
					selectedSizeBtn = modalSizes.querySelector('.size-btn');
					if (selectedSizeBtn) selectedSizeBtn.classList.add('selected');
				}
				addToCart({
					name:      modalName ? modalName.textContent : '',
					price:     modalPrice ? modalPrice.textContent : '',
					size:      selectedSizeBtn ? selectedSizeBtn.textContent : 'OS',
					productId: currentProductId
				});
				closeModal();
			});
		}
	}

	/* --------------------------------------------------
	   Cart Notification
	   -------------------------------------------------- */

	function showCartNotification(message) {
		var msgEl = document.querySelector('.cart-empty-msg');
		if (msgEl) {
			var p = msgEl.querySelector('p');
			if (p) {
				p.textContent = message;
				msgEl.style.display = '';
				setTimeout(function () {
					p.textContent = '';
				}, 5000);
			}
		}
	}

	/* --------------------------------------------------
	   Cart
	   -------------------------------------------------- */

	function addToCart(item) {
		cartItems.push(item);
		cartCount = cartItems.length;
		updateCartUI();
		openCart();

		// Send to WooCommerce server-side cart if available.
		if (typeof skyyRoseGateway !== 'undefined' && skyyRoseGateway.wcActive && item.productId) {
			var xhr = new XMLHttpRequest();
			xhr.open('POST', skyyRoseGateway.ajaxUrl, true);
			xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
			xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');

			xhr.onload = function () {
				if (xhr.status >= 200 && xhr.status < 300) {
					try {
						var resp = JSON.parse(xhr.responseText);
						if (!resp.success) {
							// Server rejected — remove item from local cart and notify user.
							var idx = cartItems.indexOf(item);
							if (idx > -1) cartItems.splice(idx, 1);
							cartCount = cartItems.length;
							updateCartUI();
							showCartNotification('Could not add item. Please try again.');
						}
					} catch (e) { /* non-JSON response — keep local state */ }
				}
			};

			xhr.onerror = function () {
				// Network failure — remove optimistically added item and notify user.
				var idx = cartItems.indexOf(item);
				if (idx > -1) cartItems.splice(idx, 1);
				cartCount = cartItems.length;
				updateCartUI();
				showCartNotification('Network error. Please check your connection.');
			};

			var postData = 'action=skyyrose_immersive_add_to_cart' +
				'&nonce=' + encodeURIComponent(skyyRoseGateway.nonce) +
				'&product_id=' + encodeURIComponent(item.productId) +
				'&quantity=1';
			if (item.size && item.size !== 'OS') {
				postData += '&attribute_pa_size=' + encodeURIComponent(item.size);
			}
			xhr.send(postData);
		}
	}

	function updateCartUI() {
		// Update badge
		if (cartBadge) {
			cartBadge.textContent = cartCount;
			cartBadge.classList.toggle('visible', cartCount > 0);
		}

		// Update total (parse prices like "$1,899")
		var total = 0;
		cartItems.forEach(function (item) {
			var price = parseFloat((item.price || '').replace(/[^0-9.]/g, ''));
			if (!isNaN(price)) total += price;
		});

		if (cartTotal) {
			cartTotal.textContent = '$' + total.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
		}

		// Show/hide empty message
		if (cartEmptyMsg) {
			cartEmptyMsg.style.display = cartCount === 0 ? '' : 'none';
		}

		// Enable/disable checkout button
		if (checkoutBtn) {
			checkoutBtn.disabled = cartCount === 0;
		}
	}

	function openCart() {
		if (cartOverlay) cartOverlay.classList.add('open');
		if (cartSidebar) cartSidebar.classList.add('open');
	}

	function closeCartPanel() {
		if (cartOverlay) cartOverlay.classList.remove('open');
		if (cartSidebar) cartSidebar.classList.remove('open');
	}

	function initCart() {
		if (cartClose) cartClose.addEventListener('click', closeCartPanel);
		if (cartOverlay) cartOverlay.addEventListener('click', closeCartPanel);

		// Wire checkout button to redirect to WooCommerce checkout.
		if (checkoutBtn) {
			checkoutBtn.addEventListener('click', function () {
				if (cartItems.length === 0) return;
				var checkoutUrl = (typeof skyyRoseGateway !== 'undefined' && skyyRoseGateway.checkoutUrl)
					? skyyRoseGateway.checkoutUrl
					: '/checkout/';
				window.location.href = checkoutUrl;
			});
		}
	}

	/* --------------------------------------------------
	   Sign-In Panel
	   -------------------------------------------------- */

	function openSignin() {
		if (signinOverlay) signinOverlay.classList.add('open');
		if (signinPanel) signinPanel.classList.add('open');
	}

	function closeSigninPanel() {
		if (signinOverlay) signinOverlay.classList.remove('open');
		if (signinPanel) signinPanel.classList.remove('open');
	}

	function initSignin() {
		if (signinClose) signinClose.addEventListener('click', closeSigninPanel);
		if (signinOverlay) signinOverlay.addEventListener('click', closeSigninPanel);
	}

	/* --------------------------------------------------
	   Action Buttons (data-action routing)
	   -------------------------------------------------- */

	function initActionBtns() {
		actionBtns.forEach(function (btn) {
			btn.addEventListener('click', function (e) {
				e.preventDefault();
				var action = btn.dataset.action;
				if (action === 'open-cart') openCart();
				if (action === 'open-signin') openSignin();
			});
		});
	}

	/* --------------------------------------------------
	   Wishlist Buttons
	   -------------------------------------------------- */

	function initWishlist() {
		var wishlistBtns = Array.from(document.querySelectorAll('.product-grid-wishlist'));
		wishlistBtns.forEach(function (btn) {
			btn.addEventListener('click', function (e) {
				e.stopPropagation();
				btn.classList.toggle('active');
			});
		});
	}

	/* --------------------------------------------------
	   Keyboard Navigation
	   -------------------------------------------------- */

	function initKeyboard() {
		document.addEventListener('keydown', function (e) {
			if (e.key === 'Escape') {
				closeModal();
				closeCartPanel();
				closeSigninPanel();
			}
		});
	}

	/* --------------------------------------------------
	   Countdown Timer
	   -------------------------------------------------- */

	function initCountdown() {
		var timerEl = document.querySelector('.countdown-timer');
		if (!timerEl) return;

		var launchDate = new Date(timerEl.dataset.launchDate || '2026-04-01T00:00:00').getTime();
		var daysEl    = timerEl.querySelector('[data-unit="days"]');
		var hoursEl   = timerEl.querySelector('[data-unit="hours"]');
		var minutesEl = timerEl.querySelector('[data-unit="minutes"]');
		var secondsEl = timerEl.querySelector('[data-unit="seconds"]');

		function pad(n) {
			return n < 10 ? '0' + n : '' + n;
		}

		var tickInterval;

		function tick() {
			var now  = Date.now();
			var diff = Math.max(0, launchDate - now);

			var days    = Math.floor(diff / (1000 * 60 * 60 * 24));
			var hours   = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
			var minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
			var seconds = Math.floor((diff % (1000 * 60)) / 1000);

			if (daysEl)    daysEl.textContent    = pad(days);
			if (hoursEl)   hoursEl.textContent   = pad(hours);
			if (minutesEl) minutesEl.textContent  = pad(minutes);
			if (secondsEl) secondsEl.textContent  = pad(seconds);

			if (diff === 0 && tickInterval) {
				clearInterval(tickInterval);
			}
		}

		tick();
		tickInterval = setInterval(tick, 1000);
	}

	/* --------------------------------------------------
	   Incentive Popup
	   -------------------------------------------------- */

	function initIncentivePopup() {
		var overlay = document.querySelector('.incentive-popup-overlay');
		var closeBtn = overlay ? overlay.querySelector('.incentive-popup-close') : null;
		if (!overlay) return;

		var shown = sessionStorage.getItem('sr_incentive_shown');
		if (shown) return;

		function showPopup() {
			if (shown) return;
			shown = '1';
			document.removeEventListener('mouseout', onExitIntent);
			overlay.classList.add('open');
			overlay.setAttribute('aria-hidden', 'false');
			sessionStorage.setItem('sr_incentive_shown', '1');
		}

		function hidePopup() {
			overlay.classList.remove('open');
			overlay.setAttribute('aria-hidden', 'true');
		}

		// Exit intent on desktop — removed after trigger to avoid needless event checks.
		function onExitIntent(e) {
			if (e.clientY < 5 && !shown) {
				showPopup();
			}
		}
		document.addEventListener('mouseout', onExitIntent);

		// Show after 15 seconds if not already shown.
		setTimeout(showPopup, 15000);

		if (closeBtn) {
			closeBtn.addEventListener('click', hidePopup);
		}

		overlay.addEventListener('click', function (e) {
			if (e.target === overlay) hidePopup();
		});

		// Handle form submission — send to AJAX handler
		var form = overlay.querySelector('.incentive-popup-form');
		if (form) {
			form.addEventListener('submit', function (e) {
				e.preventDefault();
				var submitBtn = form.querySelector('.incentive-popup-submit');
				if (submitBtn) {
					submitBtn.textContent = 'Joining...';
					submitBtn.disabled = true;
				}
				var formData = new FormData(form);
				var xhr = new XMLHttpRequest();
				var ajaxUrl = (window.skyyRoseData && window.skyyRoseData.ajaxUrl)
					? window.skyyRoseData.ajaxUrl
					: form.getAttribute('action');
				xhr.open('POST', ajaxUrl, true);
				xhr.onload = function () {
					if (submitBtn) {
						submitBtn.textContent = 'Welcome to the Inner Circle!';
					}
					setTimeout(hidePopup, 2000);
				};
				xhr.onerror = function () {
					if (submitBtn) {
						submitBtn.textContent = 'Something went wrong. Try again.';
						submitBtn.disabled = false;
					}
				};
				xhr.send(formData);
			});
		}
	}

	/* --------------------------------------------------
	   Trending Badges — Pulse on Popular Products
	   -------------------------------------------------- */

	function initTrendingBadges() {
		if (cards.length === 0) return;

		// Mark ~30% of products as "trending" (randomized per page load)
		var trendingIndices = [];
		var copy = cards.slice();
		for (var i = copy.length - 1; i > 0; i--) {
			var j = Math.floor(Math.random() * (i + 1));
			var tmp = copy[i];
			copy[i] = copy[j];
			copy[j] = tmp;
		}
		var trendingCount = Math.max(2, Math.ceil(cards.length * 0.3));
		for (var t = 0; t < trendingCount && t < copy.length; t++) {
			trendingIndices.push(copy[t]);
		}

		trendingIndices.forEach(function (card) {
			var imageContainer = card.querySelector('.product-grid-image');
			if (!imageContainer) return;
			if (imageContainer.querySelector('.pulse-trending-badge')) return;

			var badge = document.createElement('span');
			badge.className = 'pulse-trending-badge';
			badge.innerHTML =
				'<span class="pulse-trending-badge__fire">\ud83d\udd25</span>' +
				'Trending';

			var style = window.getComputedStyle(imageContainer);
			if (style.position === 'static') {
				imageContainer.style.position = 'relative';
			}

			imageContainer.appendChild(badge);
		});
	}

	/* --------------------------------------------------
	   Countdown Urgency — Inline Near Pre-Order Buttons
	   -------------------------------------------------- */

	function initUrgencyCountdowns() {
		var priceEls = document.querySelectorAll('.product-grid-price');
		if (priceEls.length === 0) return;

		var timerEl = document.querySelector('.countdown-timer');
		var deadlineStr = (timerEl && timerEl.dataset.launchDate) || '2026-04-01T00:00:00';
		var launchDate = new Date(deadlineStr).getTime();
		var countdownEls = [];

		priceEls.forEach(function (priceEl) {
			var parent = priceEl.parentNode;
			if (!parent) return;
			if (parent.querySelector('.pulse-urgency-countdown')) return;

			var el = document.createElement('div');
			el.className = 'pulse-urgency-countdown';
			el.innerHTML =
				'<span class="pulse-urgency-countdown__icon">\u23f0</span>' +
				'Pre-order closes in ' +
				'<span class="pulse-urgency-countdown__time">--d --h --m</span>';

			parent.appendChild(el);
			countdownEls.push(el.querySelector('.pulse-urgency-countdown__time'));
		});

		if (countdownEls.length === 0) return;

		function padNum(n) {
			return n < 10 ? '0' + n : '' + n;
		}

		var urgencyInterval = null;

		function tickUrgency() {
			var now = Date.now();
			var diff = Math.max(0, launchDate - now);

			var days  = Math.floor(diff / 86400000);
			var hours = Math.floor((diff % 86400000) / 3600000);
			var mins  = Math.floor((diff % 3600000) / 60000);

			var text = days + 'd ' + padNum(hours) + 'h ' + padNum(mins) + 'm';

			for (var i = 0; i < countdownEls.length; i++) {
				if (countdownEls[i]) {
					countdownEls[i].textContent = text;
				}
			}

			if (diff === 0 && urgencyInterval) {
				clearInterval(urgencyInterval);
			}
		}

		tickUrgency();
		urgencyInterval = setInterval(tickUrgency, 60000);
	}

	/* --------------------------------------------------
	   Scarcity Price Indicator — "Only X left at this price"
	   -------------------------------------------------- */

	function initScarcityPrice() {
		var priceEls = document.querySelectorAll('.product-grid-price');
		if (priceEls.length === 0) return;

		priceEls.forEach(function (priceEl) {
			var parent = priceEl.parentNode;
			if (!parent) return;
			if (parent.querySelector('.pulse-scarcity-price')) return;

			// Only show on ~40% of products for realism
			if (Math.random() > 0.4) return;

			var remaining = Math.floor(Math.random() * 12) + 3;
			var el = document.createElement('div');
			el.className = 'pulse-scarcity-price' + (remaining <= 5 ? ' pulse-scarcity-price--critical' : ' pulse-scarcity-price--low');

			var dot = document.createElement('span');
			dot.className = 'pulse-scarcity-dot';

			el.appendChild(dot);
			el.appendChild(document.createTextNode(
				'Only ' + remaining + ' left at this price'
			));

			parent.appendChild(el);
		});
	}

	/* --------------------------------------------------
	   Init
	   -------------------------------------------------- */

	function init() {
		initLoading();
		initTabs();
		initModal();
		initCart();
		initSignin();
		initActionBtns();
		initWishlist();
		initKeyboard();
		initCountdown();
		initIncentivePopup();
		initTrendingBadges();
		initUrgencyCountdowns();
		initScarcityPrice();
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}
})();
