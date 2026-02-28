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

	// Product modal — overlay and dialog are siblings in the DOM.
	var modalOverlay = document.querySelector('.product-modal-overlay');
	var modalDialog  = document.querySelector('.product-modal');
	var modalClose   = document.querySelector('.product-modal-close');
	var modalImage   = modalDialog ? modalDialog.querySelector('.modal-360-area img') : null;
	var modalName    = modalDialog ? modalDialog.querySelector('.modal-product-name') : null;
	var modalCol     = modalDialog ? modalDialog.querySelector('.modal-product-collection') : null;
	var modalPrice   = modalDialog ? modalDialog.querySelector('.modal-product-price') : null;
	var modalDesc    = modalDialog ? modalDialog.querySelector('.modal-product-desc') : null;
	var modalSizes   = modalDialog ? modalDialog.querySelector('.modal-sizes') : null;
	var modalAddBtn  = modalDialog ? modalDialog.querySelector('.modal-add-to-cart') : null;

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
	var MAX_CART_ITEMS = 50;
	var cartItems = [];
	var cartCount = 0;
	var currentProductId = null;
	var loadingInterval = null;

	/* --------------------------------------------------
	   Loading Screen
	   -------------------------------------------------- */

	function initLoading() {
		if (!loadingScreen || !progressBar) return;

		var progress = 0;
		loadingInterval = setInterval(function () {
			progress += Math.random() * 20 + 5;
			if (progress >= 100) {
				progress = 100;
				clearInterval(loadingInterval);
				loadingInterval = null;
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
		tabs.forEach(function (tab, index) {
			// Set initial tabindex: only active tab is focusable.
			tab.setAttribute('tabindex', tab.classList.contains('active') ? '0' : '-1');

			tab.addEventListener('click', function () {
				activateTab(tab);
			});

			tab.addEventListener('keydown', function (e) {
				var newIndex = -1;
				if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
					e.preventDefault();
					newIndex = (index + 1) % tabs.length;
				} else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
					e.preventDefault();
					newIndex = (index - 1 + tabs.length) % tabs.length;
				} else if (e.key === 'Home') {
					e.preventDefault();
					newIndex = 0;
				} else if (e.key === 'End') {
					e.preventDefault();
					newIndex = tabs.length - 1;
				}
				if (newIndex >= 0) {
					activateTab(tabs[newIndex]);
					tabs[newIndex].focus();
				}
			});
		});
	}

	function activateTab(tab) {
		var collection = tab.dataset.collection;

		// Update active tab and ARIA selected state (role="tablist" pattern).
		tabs.forEach(function (t) {
			t.classList.remove('active');
			t.setAttribute('aria-selected', 'false');
			t.setAttribute('tabindex', '-1');
		});
		tab.classList.add('active');
		tab.setAttribute('aria-selected', 'true');
		tab.setAttribute('tabindex', '0');

		// Update tabpanel aria-labelledby to track active tab.
		var gridPanel = document.getElementById('product-grid-panel');
		if (gridPanel && tab.id) {
			gridPanel.setAttribute('aria-labelledby', tab.id);
		}

		// Filter cards.
		var visibleCount = 0;
		cards.forEach(function (card) {
			if (collection === 'all' || card.dataset.collection === collection) {
				card.classList.remove('hidden');
				visibleCount++;
			} else {
				card.classList.add('hidden');
			}
		});

		// Announce filter result to screen readers via status region.
		var statusEl = document.querySelector('.product-grid-status');
		if (statusEl) {
			var label = tab.textContent.trim();
			statusEl.textContent = 'Showing ' + visibleCount + ' products for ' + label;
		}
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

	// Direct references to sibling dialog elements (not children of overlays).
	var productModal   = modalDialog;
	var incentivePopup = document.querySelector('.incentive-popup');

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
		// Remove inert from the dialog so keyboard/AT users can interact.
		if (productModal) {
			productModal.removeAttribute('inert');
			productModal.setAttribute('aria-hidden', 'false');
			trapFocus(productModal);
		}
	}

	function closeModal() {
		if (modalOverlay) {
			modalOverlay.classList.remove('open');
			modalOverlay.setAttribute('aria-hidden', 'true');
		}
		// Restore inert on the dialog.
		if (productModal) {
			productModal.setAttribute('inert', '');
			productModal.setAttribute('aria-hidden', 'true');
		}
		// Clean up focus trap handler to prevent accumulation.
		if (focusTrapHandler && focusTrapContainer) {
			focusTrapContainer.removeEventListener('keydown', focusTrapHandler);
			focusTrapHandler = null;
			focusTrapContainer = null;
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
		var container = cartSidebar || document.querySelector('.cart-sidebar');
		if (!container) return;
		// Create a dedicated notification element instead of reusing cart-empty-msg.
		var el = document.createElement('div');
		el.className = 'cart-notification';
		el.setAttribute('role', 'alert');
		el.textContent = message;
		container.prepend(el);
		setTimeout(function () {
			if (el.parentNode) el.parentNode.removeChild(el);
		}, 5000);
	}

	/* --------------------------------------------------
	   Cart
	   -------------------------------------------------- */

	function addToCart(item) {
		if (cartItems.length >= MAX_CART_ITEMS) {
			showCartNotification('Cart limit reached. Please proceed to checkout.');
			return;
		}
		cartItems.push(item);
		cartCount = cartItems.length;
		updateCartUI();
		openCart();

		// Send to WooCommerce server-side cart if available.
		if (typeof skyyRoseGateway !== 'undefined' && skyyRoseGateway.wcActive && item.productId) {
			// Disable checkout until server confirms to prevent race condition.
			if (checkoutBtn) checkoutBtn.disabled = true;

			var xhr = new XMLHttpRequest();
			xhr.open('POST', skyyRoseGateway.ajaxUrl, true);
			xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
			xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');

			xhr.onload = function () {
				if (xhr.status >= 200 && xhr.status < 300) {
					try {
						var resp = JSON.parse(xhr.responseText);
						if (resp.success) {
							// Server confirmed — enable checkout.
							if (checkoutBtn) checkoutBtn.disabled = false;
						} else {
							// Server rejected — remove item from local cart and notify user.
							var idx = cartItems.indexOf(item);
							if (idx > -1) cartItems.splice(idx, 1);
							cartCount = cartItems.length;
							updateCartUI();
							showCartNotification('Could not add item. Please try again.');
						}
					} catch (e) {
						// Non-JSON response — enable checkout (keep local state).
						if (checkoutBtn) checkoutBtn.disabled = false;
					}
				} else {
					if (checkoutBtn) checkoutBtn.disabled = false;
				}
			};

			xhr.onerror = function () {
				// Network failure — remove optimistically added item and notify user.
				var idx = cartItems.indexOf(item);
				if (idx > -1) cartItems.splice(idx, 1);
				cartCount = cartItems.length;
				updateCartUI();
				if (checkoutBtn) checkoutBtn.disabled = (cartItems.length === 0);
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

		// Render item rows into the cart list.
		renderCartItems();

		// Show/hide empty message
		if (cartEmptyMsg) {
			cartEmptyMsg.style.display = cartCount === 0 ? '' : 'none';
		}

		// Enable/disable checkout button
		if (checkoutBtn) {
			checkoutBtn.disabled = cartCount === 0;
			checkoutBtn.setAttribute('aria-disabled', cartCount === 0 ? 'true' : 'false');
		}
	}

	function renderCartItems() {
		if (!cartList) return;
		// Remove existing item rows (but preserve the empty message element).
		var rows = cartList.querySelectorAll('.cart-item-row');
		rows.forEach(function (r) { r.parentNode.removeChild(r); });
		cartItems.forEach(function (item) {
			var row = document.createElement('div');
			row.className = 'cart-item-row';
			var nameSpan = document.createElement('span');
			nameSpan.className = 'cart-item-row__name';
			nameSpan.textContent = (item.name || '') + (item.size && item.size !== 'OS' ? ' — ' + item.size : '');
			var priceSpan = document.createElement('span');
			priceSpan.className = 'cart-item-row__price';
			priceSpan.textContent = item.price || '';
			row.appendChild(nameSpan);
			row.appendChild(priceSpan);
			cartList.appendChild(row);
		});
	}

	function openCart() {
		if (cartOverlay) cartOverlay.classList.add('open');
		if (cartSidebar) {
			cartSidebar.classList.add('open');
			cartSidebar.removeAttribute('inert');
			cartSidebar.setAttribute('aria-hidden', 'false');
			// Move focus into the cart sidebar for keyboard/AT users.
			var firstFocusable = cartSidebar.querySelector(
				'button:not([disabled]), [href], input, [tabindex]:not([tabindex="-1"])'
			);
			if (firstFocusable) {
				setTimeout(function () { firstFocusable.focus(); }, 50);
			}
		}
	}

	function closeCartPanel() {
		if (cartOverlay) cartOverlay.classList.remove('open');
		if (cartSidebar) {
			cartSidebar.classList.remove('open');
			cartSidebar.setAttribute('inert', '');
			cartSidebar.setAttribute('aria-hidden', 'true');
		}
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
		if (signinPanel) {
			signinPanel.classList.add('open');
			signinPanel.removeAttribute('inert');
			signinPanel.setAttribute('aria-hidden', 'false');
		}
	}

	function closeSigninPanel() {
		if (signinOverlay) signinOverlay.classList.remove('open');
		if (signinPanel) {
			signinPanel.classList.remove('open');
			signinPanel.setAttribute('inert', '');
			signinPanel.setAttribute('aria-hidden', 'true');
		}
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
		var STORAGE_KEY = 'skyyrose_wishlist';
		var wishlist = [];
		try { wishlist = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); } catch (_) {}

		var wishlistBtns = Array.from(document.querySelectorAll('.product-grid-wishlist'));
		wishlistBtns.forEach(function (btn) {
			var productId = btn.dataset.productId || '';
			// Restore active state from localStorage.
			if (productId && wishlist.indexOf(productId) !== -1) {
				btn.classList.add('active');
			}
			btn.addEventListener('click', function (e) {
				e.stopPropagation();
				btn.classList.toggle('active');
				if (productId) {
					var idx = wishlist.indexOf(productId);
					if (idx === -1) { wishlist.push(productId); }
					else { wishlist.splice(idx, 1); }
					try { localStorage.setItem(STORAGE_KEY, JSON.stringify(wishlist)); } catch (_) {}
				}
			});
		});
	}

	/* --------------------------------------------------
	   Keyboard Navigation
	   -------------------------------------------------- */

	function initKeyboard() {
		document.addEventListener('keydown', function (e) {
			if (e.key === 'Escape') {
				// Close incentive popup first if open (its own trap only fires when focus is inside).
				var incOverlay = document.querySelector('.incentive-popup-overlay.open');
				if (incOverlay) {
					var incClose = document.querySelector('.incentive-popup-close');
					if (incClose) incClose.click();
					return;
				}
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
		var closeBtn = incentivePopup ? incentivePopup.querySelector('.incentive-popup-close') : null;
		if (!overlay) return;

		var shown = sessionStorage.getItem('sr_incentive_shown');
		if (shown) return;

		var _incentivePreviousFocus = null;

		function showPopup() {
			if (shown) return;
			shown = '1';
			clearTimeout(popupTimerId);
			document.removeEventListener('mouseout', onExitIntent);
			// WCAG 2.4.3: Store previous focus to restore on close.
			_incentivePreviousFocus = document.activeElement;
			overlay.classList.add('open');
			overlay.setAttribute('aria-hidden', 'false');
			if (incentivePopup) {
				incentivePopup.removeAttribute('inert');
				incentivePopup.setAttribute('aria-hidden', 'false');
				// Ensure dialog semantics.
				if (!incentivePopup.getAttribute('role')) {
					incentivePopup.setAttribute('role', 'dialog');
					incentivePopup.setAttribute('aria-modal', 'true');
					incentivePopup.setAttribute('aria-label', 'Exclusive offer');
				}
			}
			sessionStorage.setItem('sr_incentive_shown', '1');
			// Move focus into the popup for keyboard/AT users.
			if (closeBtn) closeBtn.focus();
			// WCAG 2.4.3: Focus trap within the popup.
			if (incentivePopup) incentivePopup.addEventListener('keydown', _incentiveTrapFocus);
		}

		function hidePopup() {
			document.removeEventListener('mouseout', onExitIntent);
			if (incentivePopup) incentivePopup.removeEventListener('keydown', _incentiveTrapFocus);
			overlay.classList.remove('open');
			overlay.setAttribute('aria-hidden', 'true');
			if (incentivePopup) {
				incentivePopup.setAttribute('inert', '');
				incentivePopup.setAttribute('aria-hidden', 'true');
			}
			// WCAG 2.4.3: Restore focus to the element that was active before.
			if (_incentivePreviousFocus && _incentivePreviousFocus.focus) {
				_incentivePreviousFocus.focus();
				_incentivePreviousFocus = null;
			}
		}

		function _incentiveTrapFocus(e) {
			if (e.key !== 'Tab' && e.keyCode !== 9) {
				if (e.key === 'Escape' || e.keyCode === 27) hidePopup();
				return;
			}
			var focusable = incentivePopup.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
			if (focusable.length === 0) return;
			var first = focusable[0];
			var last = focusable[focusable.length - 1];
			if (e.shiftKey && document.activeElement === first) {
				e.preventDefault();
				last.focus();
			} else if (!e.shiftKey && document.activeElement === last) {
				e.preventDefault();
				first.focus();
			}
		}

		// Exit intent on desktop — removed after trigger to avoid needless event checks.
		function onExitIntent(e) {
			if (e.clientY < 5 && !shown) {
				clearTimeout(popupTimerId);
				showPopup();
			}
		}
		document.addEventListener('mouseout', onExitIntent);

		// Show after 15 seconds if not already shown.
		var popupTimerId = setTimeout(showPopup, 15000);

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
				var ajaxUrl = window.skyyRoseData && window.skyyRoseData.ajaxUrl;
				if (!ajaxUrl) {
					if (submitBtn) { submitBtn.textContent = 'Try Again'; submitBtn.disabled = false; }
					return;
				}
				xhr.open('POST', ajaxUrl, true);
				xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
				xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
				xhr.onload = function () {
					try {
						var resp = JSON.parse(xhr.responseText);
						if (resp && resp.success) {
							if (submitBtn) submitBtn.textContent = 'Welcome to the Inner Circle!';
							setTimeout(hidePopup, 2000);
						} else {
							if (submitBtn) { submitBtn.textContent = 'Try Again'; submitBtn.disabled = false; }
						}
					} catch (parseErr) {
						if (submitBtn) { submitBtn.textContent = 'Try Again'; submitBtn.disabled = false; }
					}
				};
				xhr.onerror = function () {
					if (submitBtn) {
						submitBtn.textContent = 'Something went wrong. Try again.';
						submitBtn.disabled = false;
					}
				};
				var params = [];
				formData.forEach(function (value, key) {
					params.push(encodeURIComponent(key) + '=' + encodeURIComponent(value));
				});
				// Ensure nonce is included for server-side verification.
				var nonce = window.skyyRoseData && window.skyyRoseData.nonce;
				if (nonce && params.join('').indexOf('nonce') === -1) {
					params.push('nonce=' + encodeURIComponent(nonce));
				}
				xhr.send(params.join('&'));
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
			var fireIcon = document.createElement('span');
			fireIcon.className = 'pulse-trending-badge__fire';
			fireIcon.textContent = '\ud83d\udd25';
			badge.appendChild(fireIcon);
			badge.appendChild(document.createTextNode('Trending'));

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
			var clockIcon = document.createElement('span');
			clockIcon.className = 'pulse-urgency-countdown__icon';
			clockIcon.textContent = '\u23f0';
			el.appendChild(clockIcon);
			el.appendChild(document.createTextNode('Pre-order closes in '));
			var timeSpan = document.createElement('span');
			timeSpan.className = 'pulse-urgency-countdown__time';
			timeSpan.textContent = '--d --h --m';
			el.appendChild(timeSpan);

			parent.appendChild(el);
			countdownEls.push(timeSpan);
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

		// Pause/resume urgency countdown when tab visibility changes.
		document.addEventListener('visibilitychange', function () {
			if (document.hidden) {
				if (urgencyInterval) { clearInterval(urgencyInterval); urgencyInterval = null; }
			} else {
				tickUrgency();
				if (!urgencyInterval) { urgencyInterval = setInterval(tickUrgency, 60000); }
			}
		});
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
			if (parent.querySelector('.pulse-scarcity-price, .cie-scarcity')) return;

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
