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

	// Arrow-key navigation for dropdown menus (WCAG 2.1.1 Keyboard).
	// ArrowDown/ArrowUp: cycle items. Home/End: first/last. Escape: close.
	document.querySelectorAll('.navbar__menu, .main-navigation').forEach(function (menu) {
		menu.addEventListener('keydown', function (e) {
			var active = document.activeElement;
			if (!active || !menu.contains(active)) return;

			var parent = active.closest('.menu-item-has-children');
			if (!parent) return;

			var submenu = parent.querySelector('.sub-menu');
			if (!submenu) return;

			var items = Array.from(submenu.querySelectorAll(':scope > li > a'));
			if (!items.length) return;

			var idx = items.indexOf(active);

			switch (e.key) {
				case 'ArrowDown':
					e.preventDefault();
					// If on parent link, open and focus first child.
					if (active === parent.querySelector(':scope > a')) {
						parent.classList.add('focus');
						active.setAttribute('aria-expanded', 'true');
						items[0].focus();
					} else if (idx >= 0 && idx < items.length - 1) {
						items[idx + 1].focus();
					} else if (idx === items.length - 1) {
						items[0].focus(); // Wrap to first.
					}
					break;

				case 'ArrowUp':
					e.preventDefault();
					if (idx > 0) {
						items[idx - 1].focus();
					} else if (idx === 0) {
						// Back to parent link.
						var parentLink = parent.querySelector(':scope > a');
						if (parentLink) parentLink.focus();
					}
					break;

				case 'Home':
					e.preventDefault();
					items[0].focus();
					break;

				case 'End':
					e.preventDefault();
					items[items.length - 1].focus();
					break;

				case 'Escape':
					e.preventDefault();
					parent.classList.remove('focus');
					var trigger = parent.querySelector(':scope > a');
					if (trigger) {
						trigger.setAttribute('aria-expanded', 'false');
						trigger.focus();
					}
					break;
			}
		});
	});

	// Close dropdowns on outside click.
	document.addEventListener('click', function (e) {
		var openItems = document.querySelectorAll('.navbar__menu .focus, .main-navigation .focus');
		openItems.forEach(function (item) {
			if (!item.contains(e.target)) {
				item.classList.remove('focus');
				var link = item.querySelector(':scope > a');
				if (link) link.setAttribute('aria-expanded', 'false');
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
	   AJAX Search Autocomplete (debounced, WP REST API)
	   Shows product/page suggestions below search input.
	   Uses safe DOM construction (no innerHTML).
	   -------------------------------------------------- */
	if (searchInput && searchOverlay) {
		var suggestionsBox = document.createElement('div');
		suggestionsBox.className = 'search-autocomplete';
		suggestionsBox.setAttribute('role', 'listbox');
		suggestionsBox.setAttribute('aria-label', 'Search suggestions');
		suggestionsBox.id = 'search-suggestions';
		searchInput.parentElement.style.position = 'relative';
		searchInput.parentElement.appendChild(suggestionsBox);
		searchInput.setAttribute('role', 'combobox');
		searchInput.setAttribute('aria-autocomplete', 'list');
		searchInput.setAttribute('aria-controls', 'search-suggestions');

		var searchDebounce = null;
		var activeIndex = -1;

		function clearSuggestions() {
			while (suggestionsBox.firstChild) {
				suggestionsBox.removeChild(suggestionsBox.firstChild);
			}
		}

		function renderSuggestions(items) {
			activeIndex = -1;
			clearSuggestions();
			if (!items.length) {
				suggestionsBox.style.display = 'none';
				searchInput.setAttribute('aria-expanded', 'false');
				return;
			}
			items.forEach(function (item, i) {
				var link = document.createElement('a');
				link.href = item.link;
				link.className = 'search-autocomplete__item';
				link.setAttribute('role', 'option');
				link.id = 'suggestion-' + i;
				link.dataset.index = String(i);

				if (item._thumbnail) {
					var img = document.createElement('img');
					img.src = item._thumbnail;
					img.alt = '';
					img.width = 40;
					img.height = 40;
					img.className = 'search-autocomplete__thumb';
					img.loading = 'lazy';
					link.appendChild(img);
				}

				var textSpan = document.createElement('span');
				textSpan.className = 'search-autocomplete__text';

				var titleSpan = document.createElement('span');
				titleSpan.className = 'search-autocomplete__title';
				titleSpan.textContent = item._title || '';
				textSpan.appendChild(titleSpan);

				if (item._price) {
					var priceSpan = document.createElement('span');
					priceSpan.className = 'search-autocomplete__price';
					priceSpan.textContent = item._price;
					textSpan.appendChild(priceSpan);
				}
				link.appendChild(textSpan);

				var badge = document.createElement('span');
				badge.className = 'search-autocomplete__badge search-autocomplete__badge--' + item._type;
				badge.textContent = item._type === 'product' ? 'Product' : 'Page';
				link.appendChild(badge);

				suggestionsBox.appendChild(link);
			});
			suggestionsBox.style.display = 'block';
			searchInput.setAttribute('aria-expanded', 'true');
		}

		function fetchSuggestions(query) {
			if (query.length < 2) { renderSuggestions([]); return; }

			var restBase = (typeof skyyRoseData !== 'undefined' && skyyRoseData.themeUri)
				? skyyRoseData.themeUri.replace(/\/wp-content\/themes\/.*$/, '')
				: '';

			var productUrl = restBase + '/wp-json/wc/store/v1/products?search=' + encodeURIComponent(query) + '&per_page=4';
			var pageUrl = restBase + '/wp-json/wp/v2/pages?search=' + encodeURIComponent(query) + '&per_page=3&_fields=id,title,link';

			Promise.all([
				fetch(productUrl).then(function (r) { return r.ok ? r.json() : []; }).catch(function () { return []; }),
				fetch(pageUrl).then(function (r) { return r.ok ? r.json() : []; }).catch(function () { return []; })
			]).then(function (results) {
				var products = (results[0] || []).map(function (p) {
					return {
						_title: p.name || '',
						link: p.permalink || '#',
						_type: 'product',
						_thumbnail: (p.images && p.images[0]) ? p.images[0].thumbnail : '',
						_price: p.prices ? p.prices.currency_symbol + p.prices.price : ''
					};
				});
				var pages = (results[1] || []).map(function (p) {
					return {
						_title: (p.title && p.title.rendered) || '',
						link: p.link || '#',
						_type: 'page',
						_thumbnail: '',
						_price: ''
					};
				});
				renderSuggestions(products.concat(pages));
			});
		}

		searchInput.addEventListener('input', function () {
			clearTimeout(searchDebounce);
			searchDebounce = setTimeout(function () {
				fetchSuggestions(searchInput.value.trim());
			}, 300);
		});

		// Keyboard nav within suggestions.
		searchInput.addEventListener('keydown', function (e) {
			var items = suggestionsBox.querySelectorAll('.search-autocomplete__item');
			if (!items.length) return;

			if (e.key === 'ArrowDown') {
				e.preventDefault();
				activeIndex = Math.min(activeIndex + 1, items.length - 1);
				items.forEach(function (el, i) { el.classList.toggle('is-active', i === activeIndex); });
				searchInput.setAttribute('aria-activedescendant', 'suggestion-' + activeIndex);
			} else if (e.key === 'ArrowUp') {
				e.preventDefault();
				activeIndex = Math.max(activeIndex - 1, -1);
				items.forEach(function (el, i) { el.classList.toggle('is-active', i === activeIndex); });
				searchInput.setAttribute('aria-activedescendant', activeIndex >= 0 ? 'suggestion-' + activeIndex : '');
			} else if (e.key === 'Enter' && activeIndex >= 0 && items[activeIndex]) {
				e.preventDefault();
				items[activeIndex].click();
			}
		});

		// Close on blur (with delay for click registration).
		searchInput.addEventListener('blur', function () {
			setTimeout(function () {
				suggestionsBox.style.display = 'none';
				searchInput.setAttribute('aria-expanded', 'false');
			}, 200);
		});
	}

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
