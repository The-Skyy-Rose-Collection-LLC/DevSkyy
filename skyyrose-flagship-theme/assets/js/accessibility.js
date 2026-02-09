/**
 * Accessibility JavaScript
 *
 * Handles keyboard navigation, focus management, and ARIA announcements
 * for WCAG 2.1 AA compliance.
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

(function($) {
	'use strict';

	/**
	 * Initialize accessibility features.
	 */
	function initAccessibility() {
		// Add focus-visible polyfill class
		try {
			document.body.classList.add('js-focus-visible');
		} catch(e) {
			console.warn('Focus-visible polyfill not supported');
		}

		// Track input method (keyboard vs mouse)
		trackInputMethod();

		// Initialize modal accessibility
		initModalAccessibility();

		// Initialize menu keyboard navigation
		initMenuKeyboardNav();

		// Initialize dropdown keyboard support
		initDropdownKeyboardNav();

		// Enhance WooCommerce accessibility
		enhanceWooCommerceAccessibility();

		// Initialize form accessibility
		initFormAccessibility();

		// Initialize skip links
		initSkipLinks();
	}

	/**
	 * Track whether user is using keyboard or mouse for better focus management.
	 */
	function trackInputMethod() {
		let isUsingKeyboard = false;

		// Detect keyboard usage
		document.addEventListener('keydown', function(e) {
			if (e.key === 'Tab') {
				isUsingKeyboard = true;
				document.body.classList.add('using-keyboard');
				document.body.classList.remove('using-mouse');
			}
		});

		// Detect mouse usage
		document.addEventListener('mousedown', function() {
			isUsingKeyboard = false;
			document.body.classList.add('using-mouse');
			document.body.classList.remove('using-keyboard');
		});

		// Handle touch events
		document.addEventListener('touchstart', function() {
			document.body.classList.remove('using-keyboard');
			document.body.classList.add('using-mouse');
		});
	}

	/**
	 * Initialize modal accessibility features.
	 */
	function initModalAccessibility() {
		const modals = document.querySelectorAll('.modal-dialog, [role="dialog"]');

		modals.forEach(function(modal) {
			// Get all focusable elements
			const focusableElements = modal.querySelectorAll(
				'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
			);

			if (focusableElements.length === 0) {
				return;
			}

			const firstElement = focusableElements[0];
			const lastElement = focusableElements[focusableElements.length - 1];

			// Keyboard trap within modal
			modal.addEventListener('keydown', function(e) {
				// Tab key navigation
				if (e.key === 'Tab') {
					if (e.shiftKey && document.activeElement === firstElement) {
						e.preventDefault();
						lastElement.focus();
					} else if (!e.shiftKey && document.activeElement === lastElement) {
						e.preventDefault();
						firstElement.focus();
					}
				}

				// Escape key to close
				if (e.key === 'Escape' || e.key === 'Esc') {
					const closeBtn = modal.querySelector('.modal-close, [data-dismiss="modal"]');
					if (closeBtn) {
						closeBtn.click();
					}
				}
			});

			// When modal opens, focus first element
			const observer = new MutationObserver(function(mutations) {
				mutations.forEach(function(mutation) {
					if (mutation.attributeName === 'style' || mutation.attributeName === 'class') {
						const isVisible = window.getComputedStyle(modal).display !== 'none';
						if (isVisible) {
							// Store previously focused element
							modal.dataset.previousFocus = document.activeElement.id || '';
							// Focus first element in modal
							setTimeout(function() {
								firstElement.focus();
							}, 100);
						}
					}
				});
			});

			observer.observe(modal, { attributes: true });
		});
	}

	/**
	 * Initialize menu keyboard navigation.
	 */
	function initMenuKeyboardNav() {
		const menuToggles = document.querySelectorAll('.menu-toggle');

		menuToggles.forEach(function(toggle) {
			// Handle Enter and Space keys
			toggle.addEventListener('keydown', function(e) {
				if (e.key === 'Enter' || e.key === ' ') {
					e.preventDefault();
					toggle.click();
				}
			});

			// Update ARIA attributes on click
			toggle.addEventListener('click', function() {
				const expanded = toggle.getAttribute('aria-expanded') === 'true';
				toggle.setAttribute('aria-expanded', !expanded);
			});
		});

		// Handle menu item navigation with arrow keys
		const menuItems = document.querySelectorAll('.menu-item > a');
		menuItems.forEach(function(item, index) {
			item.addEventListener('keydown', function(e) {
				let targetIndex;

				switch(e.key) {
					case 'ArrowDown':
						e.preventDefault();
						targetIndex = index + 1;
						if (menuItems[targetIndex]) {
							menuItems[targetIndex].focus();
						}
						break;

					case 'ArrowUp':
						e.preventDefault();
						targetIndex = index - 1;
						if (menuItems[targetIndex]) {
							menuItems[targetIndex].focus();
						}
						break;

					case 'Home':
						e.preventDefault();
						menuItems[0].focus();
						break;

					case 'End':
						e.preventDefault();
						menuItems[menuItems.length - 1].focus();
						break;
				}
			});
		});
	}

	/**
	 * Initialize dropdown keyboard navigation.
	 */
	function initDropdownKeyboardNav() {
		const dropdownParents = document.querySelectorAll('.menu-item-has-children');

		dropdownParents.forEach(function(parent) {
			const link = parent.querySelector('> a');
			const submenu = parent.querySelector('.sub-menu, .dropdown-menu');

			if (!link || !submenu) {
				return;
			}

			// Set initial ARIA attributes
			link.setAttribute('aria-haspopup', 'true');
			link.setAttribute('aria-expanded', 'false');
			submenu.setAttribute('aria-hidden', 'true');

			// Handle keyboard interactions
			link.addEventListener('keydown', function(e) {
				const isOpen = parent.classList.contains('open');

				switch(e.key) {
					case 'Enter':
					case ' ':
						e.preventDefault();
						toggleDropdown(parent, link, submenu);
						break;

					case 'Escape':
					case 'Esc':
						if (isOpen) {
							e.preventDefault();
							closeDropdown(parent, link, submenu);
							link.focus();
						}
						break;

					case 'ArrowDown':
						e.preventDefault();
						if (!isOpen) {
							openDropdown(parent, link, submenu);
						}
						// Focus first submenu item
						const firstSubmenuItem = submenu.querySelector('a');
						if (firstSubmenuItem) {
							firstSubmenuItem.focus();
						}
						break;
				}
			});

			// Close on outside click
			document.addEventListener('click', function(e) {
				if (!parent.contains(e.target)) {
					closeDropdown(parent, link, submenu);
				}
			});
		});
	}

	/**
	 * Toggle dropdown open/closed state.
	 */
	function toggleDropdown(parent, link, submenu) {
		const isOpen = parent.classList.contains('open');
		if (isOpen) {
			closeDropdown(parent, link, submenu);
		} else {
			openDropdown(parent, link, submenu);
		}
	}

	/**
	 * Open dropdown.
	 */
	function openDropdown(parent, link, submenu) {
		parent.classList.add('open');
		link.setAttribute('aria-expanded', 'true');
		submenu.setAttribute('aria-hidden', 'false');
	}

	/**
	 * Close dropdown.
	 */
	function closeDropdown(parent, link, submenu) {
		parent.classList.remove('open');
		link.setAttribute('aria-expanded', 'false');
		submenu.setAttribute('aria-hidden', 'true');
	}

	/**
	 * Enhance WooCommerce accessibility.
	 */
	function enhanceWooCommerceAccessibility() {
		// Add labels to quantity inputs
		const quantityInputs = document.querySelectorAll('input.qty');
		quantityInputs.forEach(function(input) {
			if (!input.getAttribute('aria-label')) {
				input.setAttribute('aria-label', 'Product quantity');
			}
			input.setAttribute('inputmode', 'numeric');
			input.setAttribute('pattern', '[0-9]*');
		});

		// Enhance add to cart buttons
		const addToCartButtons = document.querySelectorAll('.add_to_cart_button, .single_add_to_cart_button');
		addToCartButtons.forEach(function(button) {
			if (!button.getAttribute('aria-label')) {
				const productName = button.closest('.product')?.querySelector('.product_title, .woocommerce-loop-product__title')?.textContent;
				if (productName) {
					button.setAttribute('aria-label', 'Add ' + productName.trim() + ' to cart');
				} else {
					button.setAttribute('aria-label', 'Add product to cart');
				}
			}
		});

		// Enhance product images with proper alt text
		const productImages = document.querySelectorAll('.woocommerce-product-gallery__image img');
		productImages.forEach(function(img) {
			if (!img.getAttribute('alt') || img.getAttribute('alt') === '') {
				const productTitle = document.querySelector('.product_title')?.textContent;
				if (productTitle) {
					img.setAttribute('alt', productTitle.trim());
				}
			}
		});

		// Add ARIA labels to wishlist buttons
		const wishlistButtons = document.querySelectorAll('.add-to-wishlist, .remove-from-wishlist');
		wishlistButtons.forEach(function(button) {
			const action = button.classList.contains('add-to-wishlist') ? 'Add to' : 'Remove from';
			const productName = button.closest('.product')?.querySelector('.product_title, .woocommerce-loop-product__title')?.textContent;
			if (productName && !button.getAttribute('aria-label')) {
				button.setAttribute('aria-label', action + ' wishlist: ' + productName.trim());
			}
		});

		// Enhance cart quantity buttons
		$('body').on('DOMNodeInserted', '.quantity', function() {
			$(this).find('.qty').attr('aria-label', 'Product quantity');
		});
	}

	/**
	 * Initialize form accessibility.
	 */
	function initFormAccessibility() {
		// Ensure all form inputs have labels
		const inputs = document.querySelectorAll('input:not([type="hidden"]), select, textarea');
		inputs.forEach(function(input) {
			// Skip if already has label or aria-label
			if (input.getAttribute('aria-label') || input.id && document.querySelector('label[for="' + input.id + '"]')) {
				return;
			}

			// Add aria-label based on placeholder or name
			const placeholder = input.getAttribute('placeholder');
			const name = input.getAttribute('name');

			if (placeholder) {
				input.setAttribute('aria-label', placeholder);
			} else if (name) {
				// Convert name to readable label (e.g., 'first_name' to 'First Name')
				const label = name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
				input.setAttribute('aria-label', label);
			}
		});

		// Add aria-required to required fields
		const requiredFields = document.querySelectorAll('input[required], select[required], textarea[required]');
		requiredFields.forEach(function(field) {
			field.setAttribute('aria-required', 'true');
		});

		// Handle form validation errors
		const forms = document.querySelectorAll('form');
		forms.forEach(function(form) {
			form.addEventListener('submit', function(e) {
				const invalidFields = form.querySelectorAll(':invalid');
				if (invalidFields.length > 0) {
					// Focus first invalid field
					invalidFields[0].focus();

					// Announce error to screen readers
					announceToScreenReader('Form has errors. Please correct the highlighted fields.', 'assertive');
				}
			});
		});
	}

	/**
	 * Initialize skip links.
	 */
	function initSkipLinks() {
		const skipLinks = document.querySelectorAll('.skip-link');

		skipLinks.forEach(function(link) {
			link.addEventListener('click', function(e) {
				const target = document.querySelector(link.getAttribute('href'));
				if (target) {
					e.preventDefault();
					target.setAttribute('tabindex', '-1');
					target.focus();

					// Remove tabindex after focus
					target.addEventListener('blur', function() {
						target.removeAttribute('tabindex');
					}, { once: true });

					// Smooth scroll to target
					target.scrollIntoView({ behavior: 'smooth', block: 'start' });
				}
			});
		});
	}

	/**
	 * Announce message to screen readers.
	 *
	 * @param {string} message Message to announce.
	 * @param {string} priority 'polite' or 'assertive'.
	 */
	function announceToScreenReader(message, priority) {
		priority = priority || 'polite';

		let announcer = document.getElementById('skyyrose-announcer-' + priority);
		if (!announcer) {
			announcer = document.createElement('div');
			announcer.id = 'skyyrose-announcer-' + priority;
			announcer.className = 'aria-live-region';
			announcer.setAttribute('aria-live', priority);
			announcer.setAttribute('aria-atomic', 'true');
			document.body.appendChild(announcer);
		}

		// Clear and announce
		announcer.textContent = '';
		setTimeout(function() {
			announcer.textContent = message;
		}, 100);
	}

	/**
	 * WooCommerce cart update announcements.
	 */
	if (typeof jQuery !== 'undefined') {
		// Product added to cart
		$(document.body).on('added_to_cart', function(event, fragments, cart_hash, button) {
			const productName = button.attr('data-product_name') || button.closest('.product').find('.product_title, .woocommerce-loop-product__title').text() || 'Product';
			announceToScreenReader(productName.trim() + ' has been added to your cart', 'polite');
		});

		// Cart updated
		$(document.body).on('updated_cart_totals', function() {
			announceToScreenReader('Cart has been updated', 'polite');
		});

		// Checkout field validation
		$(document.body).on('checkout_error', function() {
			announceToScreenReader('There are errors in your checkout form. Please correct them and try again.', 'assertive');
		});
	}

	/**
	 * Export announce function globally.
	 */
	window.skyyRoseAnnounce = announceToScreenReader;

	/**
	 * Initialize on DOM ready.
	 */
	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', initAccessibility);
	} else {
		initAccessibility();
	}

})(jQuery);
