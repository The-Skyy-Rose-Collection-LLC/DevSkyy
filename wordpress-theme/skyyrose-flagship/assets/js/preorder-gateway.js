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

	// Sign-in panel
	var signinOverlay = document.querySelector('.signin-overlay');
	var signinPanel   = document.querySelector('.signin-panel');
	var signinClose   = document.querySelector('.signin-close');

	// Action buttons
	var actionBtns = Array.from(document.querySelectorAll('[data-action]'));

	// Cart state
	var cartItems = [];
	var cartCount = 0;

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

				// Update active tab
				tabs.forEach(function (t) { t.classList.remove('active'); });
				tab.classList.add('active');

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

	function openModal(data) {
		if (!modalOverlay) return;

		if (modalImage) { modalImage.src = data.image || ''; modalImage.alt = data.name || ''; }
		if (modalName)  modalName.textContent = data.name || '';
		if (modalCol)   modalCol.textContent = data.collectionLabel || '';
		if (modalPrice) modalPrice.textContent = data.price || '';
		if (modalDesc)  modalDesc.textContent = data.desc || '';

		// Populate sizes
		if (modalSizes) {
			modalSizes.innerHTML = '';
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

		modalOverlay.classList.add('open');
	}

	function closeModal() {
		if (modalOverlay) modalOverlay.classList.remove('open');
	}

	function initModal() {
		// Open modal on card click
		cards.forEach(function (card) {
			card.addEventListener('click', function (e) {
				// Don't open modal if wishlist button was clicked
				if (e.target.closest('.product-grid-wishlist')) return;

				openModal({
					name:            card.dataset.productName,
					price:           card.dataset.productPrice,
					image:           card.dataset.productImage,
					collectionLabel: card.dataset.productCollectionLabel,
					desc:            card.dataset.productDesc,
					sizes:           card.dataset.productSizes
				});
			});

			// Keyboard support
			card.addEventListener('keydown', function (e) {
				if (e.key === 'Enter' || e.key === ' ') {
					e.preventDefault();
					card.click();
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
				var selectedSize = modalSizes ? modalSizes.querySelector('.size-btn.selected') : null;
				if (!selectedSize && modalSizes && modalSizes.children.length > 0) {
					// Auto-select first size if none selected
					modalSizes.querySelector('.size-btn').classList.add('selected');
				}
				addToCart({
					name:  modalName ? modalName.textContent : '',
					price: modalPrice ? modalPrice.textContent : '',
					size:  selectedSize ? selectedSize.textContent : 'OS'
				});
				closeModal();
			});
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
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}
})();
