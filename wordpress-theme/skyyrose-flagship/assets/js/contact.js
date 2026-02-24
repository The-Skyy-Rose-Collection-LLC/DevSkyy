/**
 * Contact Page Scripts — SkyyRose Flagship
 *
 * AJAX form submission, client-side validation, FAQ accordion,
 * and conditional field visibility.
 *
 * @package SkyyRose_Flagship
 * @since   3.1.0
 */

(function () {
	'use strict';

	/* --------------------------------------------------
	 * FAQ Accordion
	 * -------------------------------------------------- */
	const faqTriggers = document.querySelectorAll('.faq-item__trigger');

	faqTriggers.forEach(function (trigger) {
		trigger.addEventListener('click', function () {
			const expanded = this.getAttribute('aria-expanded') === 'true';
			const panelId = this.getAttribute('aria-controls');
			const panel = document.getElementById(panelId);

			if (!panel) return;

			// Close all other panels first.
			faqTriggers.forEach(function (otherTrigger) {
				if (otherTrigger !== trigger) {
					otherTrigger.setAttribute('aria-expanded', 'false');
					const otherPanel = document.getElementById(
						otherTrigger.getAttribute('aria-controls')
					);
					if (otherPanel) otherPanel.hidden = true;
				}
			});

			// Toggle current panel.
			this.setAttribute('aria-expanded', String(!expanded));
			panel.hidden = expanded;
		});
	});

	/* --------------------------------------------------
	 * Conditional Order Number Field
	 * -------------------------------------------------- */
	const subjectSelect = document.getElementById('contact-subject');
	const orderGroup = document.getElementById('order-number-group');

	if (subjectSelect && orderGroup) {
		function toggleOrderField() {
			const showOrder =
				subjectSelect.value === 'order-status' ||
				subjectSelect.value === 'returns-exchanges';
			orderGroup.style.display = showOrder ? '' : 'none';
		}

		toggleOrderField();
		subjectSelect.addEventListener('change', toggleOrderField);
	}

	/* --------------------------------------------------
	 * Form Validation + AJAX Submit
	 * -------------------------------------------------- */
	const form = document.getElementById('skyyrose-contact-form');
	const submitBtn = document.getElementById('contact-submit-btn');

	if (!form || !submitBtn) return;

	/**
	 * Show an inline error message beneath a field.
	 *
	 * @param {HTMLElement} field  - The input/select/textarea element.
	 * @param {string}      message - Error message to display.
	 */
	function showError(field, message) {
		const errorEl = field
			.closest('.contact-form__group')
			?.querySelector('.contact-form__error');
		if (errorEl) {
			errorEl.textContent = message;
		}
		field.classList.add('contact-form__input--error');
	}

	/**
	 * Clear the error state from a field.
	 *
	 * @param {HTMLElement} field - The input/select/textarea element.
	 */
	function clearError(field) {
		const errorEl = field
			.closest('.contact-form__group')
			?.querySelector('.contact-form__error');
		if (errorEl) {
			errorEl.textContent = '';
		}
		field.classList.remove('contact-form__input--error');
	}

	/**
	 * Validate the entire form.
	 *
	 * @return {boolean} Whether all validations pass.
	 */
	function validateForm() {
		let valid = true;

		// First name.
		const firstName = form.querySelector('[name="first_name"]');
		if (firstName && !firstName.value.trim()) {
			showError(firstName, 'First name is required.');
			valid = false;
		} else if (firstName) {
			clearError(firstName);
		}

		// Last name.
		const lastName = form.querySelector('[name="last_name"]');
		if (lastName && !lastName.value.trim()) {
			showError(lastName, 'Last name is required.');
			valid = false;
		} else if (lastName) {
			clearError(lastName);
		}

		// Email.
		const email = form.querySelector('[name="email"]');
		const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
		if (email && !emailPattern.test(email.value.trim())) {
			showError(email, 'Please enter a valid email address.');
			valid = false;
		} else if (email) {
			clearError(email);
		}

		// Subject.
		const subject = form.querySelector('[name="subject"]');
		if (subject && !subject.value) {
			showError(subject, 'Please select a topic.');
			valid = false;
		} else if (subject) {
			clearError(subject);
		}

		// Message.
		const message = form.querySelector('[name="message"]');
		if (message && !message.value.trim()) {
			showError(message, 'Please enter your message.');
			valid = false;
		} else if (message) {
			clearError(message);
		}

		return valid;
	}

	// Clear errors on input.
	form.querySelectorAll('input, select, textarea').forEach(function (field) {
		field.addEventListener('input', function () {
			clearError(this);
		});
	});

	form.addEventListener('submit', function (e) {
		e.preventDefault();

		if (!validateForm()) return;

		// Honeypot check.
		const honeypot = form.querySelector('[name="website"]');
		if (honeypot && honeypot.value) return;

		// Set loading state.
		submitBtn.classList.add('contact-form__submit--loading');
		submitBtn.disabled = true;

		const formData = new FormData(form);

		fetch(form.action, {
			method: 'POST',
			body: formData,
			credentials: 'same-origin',
		})
			.then(function (response) {
				return response.json();
			})
			.then(function (data) {
				submitBtn.classList.remove('contact-form__submit--loading');
				submitBtn.disabled = false;

				if (data.success) {
					form.reset();
					submitBtn.textContent = 'Message Sent!';
					submitBtn.style.background =
						'linear-gradient(135deg, #2ecc71, #27ae60)';
					setTimeout(function () {
						submitBtn.innerHTML =
							'<span class="contact-form__submit-text">Send Message</span>' +
							'<span class="contact-form__submit-loading" aria-hidden="true">Sending...</span>';
						submitBtn.style.background = '';
					}, 3000);
				} else {
					submitBtn.textContent = 'Error — Try Again';
					submitBtn.style.background =
						'linear-gradient(135deg, #DC143C, #a01030)';
					setTimeout(function () {
						submitBtn.innerHTML =
							'<span class="contact-form__submit-text">Send Message</span>' +
							'<span class="contact-form__submit-loading" aria-hidden="true">Sending...</span>';
						submitBtn.style.background = '';
					}, 3000);
				}
			})
			.catch(function () {
				submitBtn.classList.remove('contact-form__submit--loading');
				submitBtn.disabled = false;
				submitBtn.textContent = 'Connection Error';
				setTimeout(function () {
					submitBtn.innerHTML =
						'<span class="contact-form__submit-text">Send Message</span>' +
						'<span class="contact-form__submit-loading" aria-hidden="true">Sending...</span>';
				}, 3000);
			});
	});
})();
