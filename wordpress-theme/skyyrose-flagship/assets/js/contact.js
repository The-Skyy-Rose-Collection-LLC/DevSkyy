/**
 * Contact Page JavaScript — SkyyRose Flagship
 *
 * FAQ accordion toggle with ARIA support, client-side form validation,
 * AJAX submission with loading state, toast notifications, conditional
 * order number field, and radio group interactions.
 *
 * Zero jQuery dependencies.
 *
 * @package SkyyRose_Flagship
 * @since   3.1.0
 */

(function () {
	'use strict';

	/* ==========================================================================
	   Constants
	   ========================================================================== */

	var SELECTORS = Object.freeze({
		form: '#skyyrose-contact-form',
		submitBtn: '#contact-submit-btn',
		faqTriggers: '.faq-item__trigger',
		honeypot: 'input[name="website"]',
		toastContainer: '#toast-container',
		subjectSelect: '#contact-subject',
		orderNumberGroup: '#order-number-group',
	});

	/** Subjects that should show the order number field. */
	var ORDER_SUBJECTS = Object.freeze([
		'order-status',
		'returns-exchanges',
	]);

	var VALIDATION_RULES = Object.freeze({
		'first_name': { required: true, minLength: 1, label: 'First name' },
		'last_name': { required: true, minLength: 1, label: 'Last name' },
		'email': { required: true, pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, label: 'Email address' },
		'subject': { required: true, minLength: 1, label: 'Subject' },
		'message': { required: true, minLength: 10, label: 'Message' },
	});

	var TOAST_DURATION_MS = 5000;

	/* ==========================================================================
	   Utility Functions
	   ========================================================================== */

	/**
	 * Safely query a single element.
	 *
	 * @param {string}           selector CSS selector.
	 * @param {Element|Document} context  Parent node (default: document).
	 * @returns {Element|null}
	 */
	function qs(selector, context) {
		return (context || document).querySelector(selector);
	}

	/**
	 * Safely query all matching elements.
	 *
	 * @param {string}           selector CSS selector.
	 * @param {Element|Document} context  Parent node (default: document).
	 * @returns {Element[]}
	 */
	function qsa(selector, context) {
		return Array.prototype.slice.call(
			(context || document).querySelectorAll(selector)
		);
	}

	/* ==========================================================================
	   FAQ Accordion
	   ========================================================================== */

	/**
	 * Initialize the FAQ accordion with ARIA-compliant toggle behavior.
	 */
	function initFaqAccordion() {
		var triggers = qsa(SELECTORS.faqTriggers);

		if (triggers.length === 0) {
			return;
		}

		triggers.forEach(function (trigger) {
			trigger.addEventListener('click', function () {
				var isExpanded = trigger.getAttribute('aria-expanded') === 'true';
				var panelId = trigger.getAttribute('aria-controls');
				var panel = document.getElementById(panelId);

				if (!panel) {
					return;
				}

				// Optionally close other panels (single-open mode).
				triggers.forEach(function (otherTrigger) {
					if (otherTrigger !== trigger) {
						var otherId = otherTrigger.getAttribute('aria-controls');
						var otherPanel = document.getElementById(otherId);
						if (otherPanel && otherTrigger.getAttribute('aria-expanded') === 'true') {
							otherTrigger.setAttribute('aria-expanded', 'false');
							otherPanel.setAttribute('hidden', '');
						}
					}
				});

				// Toggle the clicked panel.
				if (isExpanded) {
					trigger.setAttribute('aria-expanded', 'false');
					panel.setAttribute('hidden', '');
				} else {
					trigger.setAttribute('aria-expanded', 'true');
					panel.removeAttribute('hidden');

					// Smooth scroll the opened item into view if partially off-screen.
					scrollIntoViewIfNeeded(trigger);
				}
			});

			// Keyboard support: Enter and Space already handled by <button>.
		});
	}

	/**
	 * Scroll an element into view if it is not fully visible.
	 *
	 * @param {Element} el The element to scroll into view.
	 */
	function scrollIntoViewIfNeeded(el) {
		if (!el || typeof el.getBoundingClientRect !== 'function') {
			return;
		}

		var rect = el.getBoundingClientRect();
		var viewportHeight = window.innerHeight || document.documentElement.clientHeight;

		// Only scroll if the bottom of the element is below the viewport.
		if (rect.bottom > viewportHeight) {
			el.scrollIntoView({ behavior: 'smooth', block: 'center' });
		}
	}

	/* ==========================================================================
	   Conditional Order Number Field
	   ========================================================================== */

	/**
	 * Show or hide the order number field based on the selected subject.
	 */
	function initConditionalOrderNumber() {
		var subjectSelect = qs(SELECTORS.subjectSelect);
		var orderGroup = qs(SELECTORS.orderNumberGroup);

		if (!subjectSelect || !orderGroup) {
			return;
		}

		function updateOrderNumberVisibility() {
			var selectedValue = subjectSelect.value;
			var shouldShow = ORDER_SUBJECTS.indexOf(selectedValue) !== -1;

			if (shouldShow) {
				orderGroup.classList.remove('is-hidden');
			} else {
				orderGroup.classList.add('is-hidden');
			}
		}

		// Set initial state.
		updateOrderNumberVisibility();

		// Listen for changes.
		subjectSelect.addEventListener('change', updateOrderNumberVisibility);
	}

	/* ==========================================================================
	   Form Validation
	   ========================================================================== */

	/**
	 * Validate a single form field and return an error message or empty string.
	 *
	 * @param {string} fieldName Name attribute of the field.
	 * @param {string} value     Current field value.
	 * @returns {string} Error message or empty string if valid.
	 */
	function validateField(fieldName, value) {
		var rule = VALIDATION_RULES[fieldName];

		if (!rule) {
			return '';
		}

		var trimmed = value.trim();

		if (rule.required && trimmed.length === 0) {
			return rule.label + ' is required.';
		}

		if (rule.minLength && trimmed.length < rule.minLength) {
			return rule.label + ' must be at least ' + rule.minLength + ' characters.';
		}

		if (rule.pattern && !rule.pattern.test(trimmed)) {
			return 'Please enter a valid ' + rule.label.toLowerCase() + '.';
		}

		return '';
	}

	/**
	 * Show or clear the error message for a form field.
	 *
	 * @param {Element} field   The input/select/textarea element.
	 * @param {string}  message Error message (empty to clear).
	 */
	function setFieldError(field, message) {
		var group = field.closest('.contact-form__group');
		if (!group) {
			return;
		}

		var errorEl = qs('.contact-form__error', group);

		if (message) {
			field.classList.add('is-invalid');
			field.setAttribute('aria-invalid', 'true');
			if (errorEl) {
				errorEl.textContent = message;
			}
		} else {
			field.classList.remove('is-invalid');
			field.removeAttribute('aria-invalid');
			if (errorEl) {
				errorEl.textContent = '';
			}
		}
	}

	/**
	 * Validate all form fields and return whether the form is valid.
	 *
	 * @param {HTMLFormElement} form The form element.
	 * @returns {boolean} True if all fields are valid.
	 */
	function validateForm(form) {
		var isValid = true;
		var firstInvalidField = null;

		Object.keys(VALIDATION_RULES).forEach(function (fieldName) {
			var field = form.elements[fieldName];
			if (!field) {
				return;
			}

			var error = validateField(fieldName, field.value);
			setFieldError(field, error);

			if (error && isValid) {
				isValid = false;
				firstInvalidField = field;
			}
		});

		// Focus the first invalid field for accessibility.
		if (firstInvalidField) {
			firstInvalidField.focus();
		}

		return isValid;
	}

	/**
	 * Attach real-time validation listeners to form fields.
	 *
	 * @param {HTMLFormElement} form The form element.
	 */
	function attachFieldValidation(form) {
		Object.keys(VALIDATION_RULES).forEach(function (fieldName) {
			var field = form.elements[fieldName];
			if (!field) {
				return;
			}

			field.addEventListener('blur', function () {
				var error = validateField(fieldName, field.value);
				setFieldError(field, error);
			});

			field.addEventListener('input', function () {
				// Clear error on input if field was previously invalid.
				if (field.classList.contains('is-invalid')) {
					var error = validateField(fieldName, field.value);
					setFieldError(field, error);
				}
			});
		});
	}

	/* ==========================================================================
	   Toast Notifications
	   ========================================================================== */

	/**
	 * Show a toast notification that auto-dismisses.
	 *
	 * @param {string} message  The message to display.
	 * @param {'success'|'error'} type Toast type.
	 */
	function showToast(message, type) {
		// Remove any existing toast.
		var existing = qs('.contact-toast');
		if (existing) {
			existing.remove();
		}

		var iconSvg = type === 'success'
			? '<svg class="contact-toast__icon contact-toast__icon--success" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>'
			: '<svg class="contact-toast__icon contact-toast__icon--error" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>';

		var toast = document.createElement('div');
		toast.className = 'contact-toast contact-toast--' + type;
		toast.setAttribute('role', 'alert');
		toast.setAttribute('aria-live', 'assertive');
		toast.innerHTML =
			iconSvg +
			'<span class="contact-toast__message">' + escapeHtml(message) + '</span>' +
			'<button type="button" class="contact-toast__dismiss" aria-label="Dismiss notification">' +
			'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>' +
			'</button>';

		document.body.appendChild(toast);

		// Dismiss on click.
		var dismissBtn = qs('.contact-toast__dismiss', toast);
		if (dismissBtn) {
			dismissBtn.addEventListener('click', function () {
				dismissToast(toast);
			});
		}

		// Animate in.
		requestAnimationFrame(function () {
			requestAnimationFrame(function () {
				toast.classList.add('is-visible');
			});
		});

		// Auto-dismiss.
		var timerId = setTimeout(function () {
			dismissToast(toast);
		}, TOAST_DURATION_MS);

		// Store timer for cleanup.
		toast._dismissTimer = timerId;
	}

	/**
	 * Animate out and remove a toast element.
	 *
	 * @param {Element} toast The toast element to dismiss.
	 */
	function dismissToast(toast) {
		if (!toast || !toast.parentNode) {
			return;
		}

		if (toast._dismissTimer) {
			clearTimeout(toast._dismissTimer);
		}

		toast.classList.remove('is-visible');

		var onTransitionEnd = function () {
			toast.removeEventListener('transitionend', onTransitionEnd);
			if (toast.parentNode) {
				toast.parentNode.removeChild(toast);
			}
		};

		toast.addEventListener('transitionend', onTransitionEnd);

		// Fallback removal if transitionend doesn't fire (reduced motion).
		setTimeout(function () {
			if (toast.parentNode) {
				toast.parentNode.removeChild(toast);
			}
		}, 600);
	}

	/**
	 * Escape HTML entities to prevent XSS in toast messages.
	 *
	 * @param {string} str Raw string.
	 * @returns {string} Escaped string.
	 */
	function escapeHtml(str) {
		var div = document.createElement('div');
		div.appendChild(document.createTextNode(str));
		return div.innerHTML;
	}

	/* ==========================================================================
	   AJAX Form Submission
	   ========================================================================== */

	/**
	 * Set the submit button to loading or default state.
	 *
	 * @param {Element} btn        The submit button element.
	 * @param {boolean} isLoading  Whether to show loading state.
	 */
	function setButtonLoading(btn, isLoading) {
		if (!btn) {
			return;
		}

		if (isLoading) {
			btn.classList.add('is-loading');
			btn.disabled = true;
			btn.setAttribute('aria-busy', 'true');
		} else {
			btn.classList.remove('is-loading');
			btn.disabled = false;
			btn.removeAttribute('aria-busy');
		}
	}

	/**
	 * Initialize the contact form with AJAX submission.
	 */
	function initContactForm() {
		var form = qs(SELECTORS.form);
		if (!form) {
			return;
		}

		var submitBtn = qs(SELECTORS.submitBtn);

		// Attach real-time validation.
		attachFieldValidation(form);

		form.addEventListener('submit', function (event) {
			event.preventDefault();

			// Client-side validation.
			if (!validateForm(form)) {
				return;
			}

			// Honeypot check.
			var honeypot = qs(SELECTORS.honeypot, form);
			if (honeypot && honeypot.value.length > 0) {
				// Bot detected — show fake success.
				showToast(
					'Thank you for your message! We will get back to you within 24 hours.',
					'success'
				);
				form.reset();
				return;
			}

			// Collect form data.
			var formData = new FormData(form);

			// Set loading state.
			setButtonLoading(submitBtn, true);

			// Determine AJAX URL from the form action or localized data.
			var ajaxUrl = form.getAttribute('action');
			if (!ajaxUrl && typeof skyyRoseData !== 'undefined') {
				ajaxUrl = skyyRoseData.ajaxUrl;
			}

			// Submit via fetch.
			fetch(ajaxUrl, {
				method: 'POST',
				body: formData,
				credentials: 'same-origin',
			})
				.then(function (response) {
					if (!response.ok) {
						throw new Error('Network response was not ok');
					}
					return response.json();
				})
				.then(function (data) {
					setButtonLoading(submitBtn, false);

					if (data && data.success) {
						showToast(
							data.data && data.data.message
								? data.data.message
								: 'Thank you for your message! We will get back to you within 24 hours.',
							'success'
						);
						form.reset();

						// Clear any remaining validation states.
						qsa('.is-invalid', form).forEach(function (el) {
							el.classList.remove('is-invalid');
							el.removeAttribute('aria-invalid');
						});
						qsa('.contact-form__error', form).forEach(function (el) {
							el.textContent = '';
						});

						// Reset conditional field visibility after form reset.
						initConditionalOrderNumber();
					} else {
						showToast(
							data.data && data.data.message
								? data.data.message
								: 'Something went wrong. Please try again or email us directly at hello@skyyrose.co.',
							'error'
						);
					}
				})
				.catch(function () {
					setButtonLoading(submitBtn, false);
					showToast(
						'Unable to send your message. Please check your connection and try again.',
						'error'
					);
				});
		});
	}

	/* ==========================================================================
	   Initialization
	   ========================================================================== */

	/**
	 * Boot all contact page modules when the DOM is ready.
	 */
	function init() {
		initFaqAccordion();
		initContactForm();
		initConditionalOrderNumber();
	}

	// Wait for DOM readiness.
	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}
})();
