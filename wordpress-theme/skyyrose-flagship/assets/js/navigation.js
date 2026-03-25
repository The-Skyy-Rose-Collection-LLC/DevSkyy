/**
 * Navigation — Hamburger toggle, keyboard nav, scroll state.
 *
 * @package SkyyRose_Flagship
 * @since   3.0.0
 */

(function () {
	'use strict';

	/* --------------------------------------------------
	   Image Fallback (CSP-safe replacement for inline onerror)
	   Catches broken images site-wide and swaps to data-fallback URL.
	   -------------------------------------------------- */

	document.addEventListener('error', function (e) {
		if (e.target.tagName === 'IMG' && e.target.dataset.fallback) {
			e.target.src = e.target.dataset.fallback;
			delete e.target.dataset.fallback;
		}
	}, true);

	/* --------------------------------------------------
	   Hamburger Toggle (Mobile)
	   -------------------------------------------------- */

	var toggle  = document.querySelector('#mobile-menu-toggle, .menu-toggle');
	var nav     = document.querySelector('.navbar__nav-wrapper, .main-navigation');
	var mobilePanel = document.querySelector('#mobile-menu, .mobile-menu');
	var mobileClose = document.querySelector('#mobile-menu-close, .mobile-menu__close');

	var mobileOverlay = document.querySelector('#mobile-menu-overlay, .mobile-menu__overlay');

	// WCAG 2.4.3: Focus trap for mobile menu (Tab/Shift+Tab cycle within panel).
	function handleMobileMenuKeydown(e) {
		if (e.key === 'Escape') { closeMobileMenu(); return; }
		if (e.key !== 'Tab' || !mobilePanel) return;
		var focusable = mobilePanel.querySelectorAll(
			'button, [href], input, select, [tabindex]:not([tabindex="-1"])'
		);
		if (!focusable.length) return;
		var first = focusable[0];
		var last  = focusable[focusable.length - 1];
		if (e.shiftKey) {
			if (document.activeElement === first) { e.preventDefault(); last.focus(); }
		} else {
			if (document.activeElement === last)  { e.preventDefault(); first.focus(); }
		}
	}

	function closeMobileMenu() {
		if (mobilePanel) {
			mobilePanel.classList.remove('open');
			mobilePanel.setAttribute('aria-hidden', 'true');
			mobilePanel.setAttribute('inert', '');
			mobilePanel.removeEventListener('keydown', handleMobileMenuKeydown);
		}
		document.body.classList.remove('mobile-nav-open');
		if (toggle) {
			toggle.setAttribute('aria-expanded', 'false');
			// Only return focus if toggle is visible (not hidden on desktop resize).
			if (toggle.offsetParent !== null) {
				toggle.focus();
			}
		}
		if (nav) {
			nav.classList.remove('toggled');
		}
		if (mobileOverlay) {
			mobileOverlay.classList.remove('open');
		}
	}

	if (toggle && nav) {
		toggle.addEventListener('click', function () {
			var expanded = toggle.getAttribute('aria-expanded') === 'true';
			toggle.setAttribute('aria-expanded', String(!expanded));
			nav.classList.toggle('toggled');

			if (mobilePanel) {
				mobilePanel.classList.toggle('open');
				mobilePanel.setAttribute('aria-hidden', String(expanded));
				if (expanded) {
					mobilePanel.setAttribute('inert', '');
				} else {
					mobilePanel.removeAttribute('inert');
				}
				document.body.classList.toggle('mobile-nav-open');

				// WCAG 2.4.3: Move focus into mobile menu when it opens + enable focus trap.
				if (!expanded && mobileClose) {
					mobileClose.focus();
					// Guard: remove first to prevent duplicate listeners on rapid toggle.
					mobilePanel.removeEventListener('keydown', handleMobileMenuKeydown);
					mobilePanel.addEventListener('keydown', handleMobileMenuKeydown);
				}
			}
			if (mobileOverlay) {
				mobileOverlay.classList.toggle('open');
			}
		});
	}

	if (mobileClose && mobilePanel) {
		mobileClose.addEventListener('click', closeMobileMenu);
	}

	if (mobileOverlay) {
		mobileOverlay.addEventListener('click', closeMobileMenu);
	}

	/* --------------------------------------------------
	   Dropdown Navigation (Keyboard + Mobile Touch)
	   Parent items with children: tap/Enter toggles submenu.
	   Child items (leaves): tap/click navigates immediately.
	   Desktop hover behaviour is CSS-only and unaffected.
	   -------------------------------------------------- */

	var dropdownToggles = document.querySelectorAll('.navbar__menu .menu-item-has-children > a, .main-navigation .menu-item-has-children > a');
	var isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;

	dropdownToggles.forEach(function (link) {
		// Keyboard: Enter/Space toggles submenu
		link.addEventListener('keydown', function (e) {
			if (e.key === 'Enter' || e.key === ' ') {
				var parent = link.parentElement;
				if (parent) {
					e.preventDefault();
					var isOpen = parent.classList.toggle('focus');
					link.setAttribute('aria-expanded', String(isOpen));
				}
			}
		});

		// Touch: first tap opens submenu, does NOT navigate
		if (isTouchDevice) {
			link.addEventListener('click', function (e) {
				var parent = link.parentElement;
				if (!parent) return;
				// If submenu is already open, allow navigation
				if (parent.classList.contains('focus')) return;
				// First tap — open submenu, block navigation
				e.preventDefault();
				// Close any other open dropdowns
				dropdownToggles.forEach(function (other) {
					if (other !== link && other.parentElement) {
						other.parentElement.classList.remove('focus');
						other.setAttribute('aria-expanded', 'false');
					}
				});
				parent.classList.add('focus');
				link.setAttribute('aria-expanded', 'true');
			});
		}

		// Set initial aria-expanded
		link.setAttribute('aria-expanded', 'false');
	});

	// Close dropdowns on outside click.
	document.addEventListener('click', function (e) {
		var openItems = document.querySelectorAll('.navbar__menu .focus, .main-navigation .focus');
		openItems.forEach(function (item) {
			if (!item.contains(e.target)) {
				item.classList.remove('focus');
			}
		});
	});

	/* --------------------------------------------------
	   Header Scroll State
	   -------------------------------------------------- */

	var header = document.querySelector('.site-header');
	var scrollThreshold = 60;
	var ticking = false;

	function updateHeaderState() {
		if (!header) return;
		if (window.scrollY > scrollThreshold) {
			header.classList.add('scrolled');
		} else {
			header.classList.remove('scrolled');
		}
		ticking = false;
	}

	window.addEventListener('scroll', function () {
		if (!ticking) {
			requestAnimationFrame(updateHeaderState);
			ticking = true;
		}
	}, { passive: true });

	/* --------------------------------------------------
	   Search Overlay
	   -------------------------------------------------- */

	var searchToggle = document.querySelector('#search-toggle, .navbar__search-btn, .header-search-toggle');
	var searchOverlay = document.querySelector('.search-overlay');
	var searchClose = document.querySelector('#search-close, .search-overlay__close, .search-overlay-close');
	var searchInput = searchOverlay ? searchOverlay.querySelector('input[type="search"]') : null;

	var pageWrap = document.getElementById('page');

	if (searchToggle && searchOverlay) {
		searchToggle.addEventListener('click', function () {
			searchOverlay.classList.add('open');
			searchOverlay.setAttribute('aria-hidden', 'false');
			searchOverlay.removeAttribute('inert');
			// Make background inert so focus is trapped inside the overlay.
			if (pageWrap) pageWrap.setAttribute('inert', '');
			if (searchInput) {
				setTimeout(function () { searchInput.focus(); }, 100);
			}
		});
	}

	function closeSearchOverlay() {
		if (searchOverlay) {
			searchOverlay.classList.remove('open');
			searchOverlay.setAttribute('aria-hidden', 'true');
			searchOverlay.setAttribute('inert', '');
		}
		if (pageWrap) pageWrap.removeAttribute('inert');
	}

	if (searchClose && searchOverlay) {
		searchClose.addEventListener('click', function () {
			closeSearchOverlay();
			if (searchToggle) searchToggle.focus();
		});
	}

	// Close search on Escape.
	document.addEventListener('keydown', function (e) {
		if (e.key === 'Escape' && searchOverlay && searchOverlay.classList.contains('open')) {
			closeSearchOverlay();
			if (searchToggle) searchToggle.focus();
		}
	});

	/* --------------------------------------------------
	   Smooth Scroll for Anchor Links
	   -------------------------------------------------- */

	document.querySelectorAll('a.js-smooth-scroll[href^="#"], .site-header a[href^="#"], .site-footer a[href^="#"]').forEach(function (link) {
		link.addEventListener('click', function (e) {
			var href = link.getAttribute('href');
			if (href === '#' || href.length < 2) return;
			var target = document.querySelector(href);
			if (target) {
				e.preventDefault();
				target.scrollIntoView({ behavior: 'smooth', block: 'start' });
			}
		});
	});

	/* --------------------------------------------------
	   Footer Newsletter AJAX (site-wide)
	   Handles the footer newsletter form on all pages.
	   The front-page.js handles .js-newsletter-form separately.
	   -------------------------------------------------- */

	var footerForm = document.querySelector('.footer-newsletter__form');
	if (footerForm) {
		footerForm.addEventListener('submit', function (e) {
			e.preventDefault();
			var emailInput = footerForm.querySelector('input[type="email"]');
			var btn = footerForm.querySelector('button[type="submit"]');
			if (!emailInput || !emailInput.value) return;

			if (btn) {
				btn.disabled = true;
				btn.textContent = 'Subscribing...';
			}

			var xhr = new XMLHttpRequest();
			var footerAjaxUrl = footerForm.action ||
				(typeof skyyRoseData !== 'undefined' && skyyRoseData.ajaxUrl ? skyyRoseData.ajaxUrl : '');
			if (!footerAjaxUrl) return;
			xhr.open('POST', footerAjaxUrl, true);
			xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
			xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');

			xhr.onload = function () {
				if (xhr.status >= 200 && xhr.status < 300) {
					try {
						var resp = JSON.parse(xhr.responseText);
						if (resp.success) {
							if (btn) { btn.textContent = 'Welcome!'; }
							if (emailInput) emailInput.value = '';
							setTimeout(function () {
								if (btn) { btn.textContent = 'Subscribe'; btn.disabled = false; }
							}, 3000);
							return;
						}
					} catch (_) { /* fall through */ }
				}
				if (btn) { btn.textContent = 'Try Again'; btn.disabled = false; }
			};

			xhr.onerror = function () {
				if (btn) { btn.textContent = 'Try Again'; btn.disabled = false; }
			};

			var formData = new FormData(footerForm);
			var params = [];
			formData.forEach(function (value, key) {
				params.push(encodeURIComponent(key) + '=' + encodeURIComponent(value));
			});
			xhr.send(params.join('&'));
		});
	}
})();
