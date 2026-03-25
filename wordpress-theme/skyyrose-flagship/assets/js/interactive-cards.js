/**
 * SkyyRose Interactive Product Cards — v1.0.0
 *
 * 3D rotating cube, tilt, gestures, wishlist, quick-buy AJAX,
 * scarcity counters, pre-order reveal, keyboard navigation.
 *
 * @package SkyyRose_Flagship
 * @since   4.1.0
 */

(function () {
	'use strict';

	/* -----------------------------------------------
	   Global refs
	   ----------------------------------------------- */

	const data     = window.skyyRoseData              || {};
	const cards    = window.skyyRoseCards             || {};
	const products = window.skyyRoseCollectionProducts || [];

	const AJAX_URL   = data.ajaxUrl   || '';
	const NONCE      = cards.nonce    || data.nonce || '';
	const ASSETS_URI = data.assetsUri || '';

	const SNAP_DURATION_MS  = 380;
	const BURST_DURATION_MS = 400;
	const SCARCITY_MS       = 600;
	const BUY_RESET_MS      = 3000;
	const ADD_GLOW_MS       = 2000;
	const WISHLIST_KEY      = 'skyyrose_ipc_wishlist';
	const PLACEHOLDER_IMG   = ASSETS_URI + '/images/placeholder-product.jpg';

	void products; // available for quick-view modal integration

	/* -----------------------------------------------
	   Utilities
	   ----------------------------------------------- */

	function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

	function normalizeAngle(deg) { return ((deg % 360) + 360) % 360; }

	function nearestFace(normalizedDeg) {
		let bestIdx = 0, bestDist = Infinity;
		[0, 120, 240].forEach(function (angle, idx) {
			const dist = Math.min(
				Math.abs(normalizedDeg - angle),
				360 - Math.abs(normalizedDeg - angle)
			);
			if (dist < bestDist) { bestDist = dist; bestIdx = idx; }
		});
		return { faceIndex: bestIdx, faceAngle: [0, 120, 240][bestIdx] };
	}

	function shortestDelta(currentAccum, faceAngle) {
		const normalized = normalizeAngle(currentAccum);
		let delta = faceAngle - normalized;
		if (delta > 180) delta -= 360;
		if (delta < -180) delta += 360;
		return delta;
	}

	function postAjax(url, formData) {
		return fetch(url, { method: 'POST', credentials: 'same-origin', body: formData })
			.then(function (res) {
				if (!res.ok) throw new Error('HTTP ' + res.status);
				return res.json();
			});
	}

	/* -----------------------------------------------
	   1. Skeleton Loading
	   ----------------------------------------------- */

	function initSkeletonLoading() {
		document.querySelectorAll('.ipc__face').forEach(function (face) {
			const img = face.querySelector('img');
			if (!img) return;

			if (img.complete && img.naturalHeight > 0) return;

			face.classList.add('ipc__face--loading');

			img.addEventListener('load', function () {
				setTimeout(function () {
					face.classList.remove('ipc__face--loading');
				}, 50);
			}, { once: true });

			img.addEventListener('error', function () {
				if (PLACEHOLDER_IMG) img.src = PLACEHOLDER_IMG;
				face.classList.remove('ipc__face--loading');
			}, { once: true });
		});
	}

	/* -----------------------------------------------
	   2. Cube Rotation (Drag-to-Rotate)
	   ----------------------------------------------- */

	const cubeStates = new WeakMap();

	function applyCubeRotation(cube, angle) {
		cube.style.setProperty('--cube-rotation', angle + 'deg');
	}

	function updateDots(card, activeFace) {
		card.querySelectorAll('.ipc__dot').forEach(function (dot, idx) {
			dot.classList.toggle('ipc__dot--active', idx === activeFace);
		});
	}

	function snapCube(cube, state, card) {
		const { faceIndex, faceAngle } = nearestFace(normalizeAngle(state.rotation));
		const snapTarget = state.rotation + shortestDelta(state.rotation, faceAngle);

		state.currentFace = faceIndex;
		state.rotation = snapTarget;

		cube.style.transition = 'transform ' + SNAP_DURATION_MS + 'ms cubic-bezier(0.16, 1, 0.3, 1)';
		applyCubeRotation(cube, snapTarget);

		setTimeout(function () { cube.style.transition = ''; }, SNAP_DURATION_MS + 20);
		updateDots(card, faceIndex);
	}

	function initCubeRotation(reducedMotion) {
		document.querySelectorAll('.ipc__cube').forEach(function (cube) {
			const card = cube.closest('.ipc');
			if (!card) return;

			const galleryCount = parseInt(card.getAttribute('data-gallery-count') || '3', 10);
			if (galleryCount <= 1 || card.getAttribute('data-glb-src')) {
				cube.style.cursor = 'default';
				return;
			}

			const state = {
				currentFace: 0,
				rotation: 0,
				isDragging: false,
				startX: 0,
				startRotation: 0
			};
			cubeStates.set(cube, state);

			cube.addEventListener('pointerdown', function (e) {
				if (e.button !== 0) return;
				state.isDragging = true;
				state.startX = e.clientX;
				state.startRotation = state.rotation;
				cube.setPointerCapture(e.pointerId);
				cube.style.transition = '';
				cube.classList.add('ipc__cube--dragging');
			});

			cube.addEventListener('pointermove', function (e) {
				if (!state.isDragging) return;
				state.rotation = state.startRotation + (e.clientX - state.startX) * 0.5;
				applyCubeRotation(cube, state.rotation);
				updateDots(card, nearestFace(normalizeAngle(state.rotation)).faceIndex);
			});

			cube.addEventListener('pointerup', function (e) {
				if (!state.isDragging) return;
				state.isDragging = false;
				cube.releasePointerCapture(e.pointerId);
				cube.classList.remove('ipc__cube--dragging');

				if (!reducedMotion) {
					snapCube(cube, state, card);
				} else {
					const { faceIndex, faceAngle } = nearestFace(normalizeAngle(state.rotation));
					state.currentFace = faceIndex;
					state.rotation = faceAngle;
					applyCubeRotation(cube, faceAngle);
					updateDots(card, faceIndex);
				}
			});

			cube.addEventListener('pointercancel', function () {
				if (state.isDragging) {
					state.isDragging = false;
					cube.classList.remove('ipc__cube--dragging');
					snapCube(cube, state, card);
				}
			});
		});
	}

	function rotateCubeFace(card, direction) {
		const cube = card.querySelector('.ipc__cube');
		if (!cube) return;
		const state = cubeStates.get(cube);
		if (!state) return;

		const nextFace = (state.currentFace + direction + 3) % 3;
		state.rotation += shortestDelta(state.rotation, [0, 120, 240][nextFace]);
		state.currentFace = nextFace;

		cube.style.transition = 'transform ' + SNAP_DURATION_MS + 'ms cubic-bezier(0.16, 1, 0.3, 1)';
		applyCubeRotation(cube, state.rotation);
		setTimeout(function () { cube.style.transition = ''; }, SNAP_DURATION_MS + 20);
		updateDots(card, nextFace);
	}

	/* -----------------------------------------------
	   3. Perspective Tilt (desktop only)
	   ----------------------------------------------- */

	function initTilt() {
		if (!window.matchMedia('(hover: hover)').matches) return;

		const grid = document.querySelector('.ipc-grid');
		if (!grid) return;

		let rafId = 0;
		let activeCard = null;

		function resetCard(card) {
			if (!card) return;
			cancelAnimationFrame(rafId);
			card.style.transition = 'transform 300ms ease-out';
			card.style.transform = 'translateY(0)';
			setTimeout(function () {
				card.style.transition = '';
				card.style.transform = '';
			}, 310);
		}

		grid.addEventListener('mousemove', function (e) {
			const card = e.target.closest('.ipc');
			if (!card || card.getAttribute('data-glb-src')) return;

			if (activeCard && activeCard !== card) {
				resetCard(activeCard);
			}
			activeCard = card;

			const rect = card.getBoundingClientRect();
			const rx = ((e.clientY - rect.top - rect.height / 2) / (rect.height / 2)) * -8;
			const ry = ((e.clientX - rect.left - rect.width / 2) / (rect.width / 2)) * 6;

			cancelAnimationFrame(rafId);
			rafId = requestAnimationFrame(function () {
				card.style.transform = 'perspective(800px) rotateX(' + rx.toFixed(2) + 'deg) rotateY(' + ry.toFixed(2) + 'deg) translateY(-6px)';
			});
		}, { passive: true });

		grid.addEventListener('mouseleave', function () {
			resetCard(activeCard);
			activeCard = null;
		}, { passive: true });
	}

	/* -----------------------------------------------
	   4. Wishlist Heart Toggle + Burst
	   ----------------------------------------------- */

	function getWishlist() {
		try { return JSON.parse(localStorage.getItem(WISHLIST_KEY)) || []; }
		catch (e) { return []; }
	}

	function saveWishlist(list) {
		try { localStorage.setItem(WISHLIST_KEY, JSON.stringify(list)); }
		catch (e) { /* quota exceeded — fail silently */ }
	}

	function updateWishlistBadge(delta) {
		const badge = document.getElementById('col-wl-count');
		if (!badge) return;
		badge.textContent = Math.max(0, (parseInt(badge.textContent, 10) || 0) + delta);
		badge.classList.remove('bounce');
		void badge.offsetWidth;
		badge.classList.add('bounce');
		setTimeout(function () { badge.classList.remove('bounce'); }, 300);
	}

	function initWishlist() {
		const wishlist = getWishlist();

		// Restore saved states.
		document.querySelectorAll('.ipc__wishlist').forEach(function (btn) {
			const card = btn.closest('.ipc');
			const sku = (card && card.getAttribute('data-product-sku')) || '';
			if (sku && wishlist.indexOf(sku) !== -1) {
				btn.setAttribute('aria-pressed', 'true');
				btn.classList.add('ipc__wishlist--active');
			}
		});

		// Event delegation.
		const grid = document.querySelector('.ipc-grid');
		if (!grid) return;

		grid.addEventListener('click', function (e) {
			const btn = e.target.closest('.ipc__wishlist');
			if (!btn) return;
			e.preventDefault();
			e.stopPropagation();

			const card = btn.closest('.ipc');
			const sku = (card && card.getAttribute('data-product-sku')) || '';
			const pressed = btn.getAttribute('aria-pressed') === 'true';

			btn.setAttribute('aria-pressed', pressed ? 'false' : 'true');
			btn.classList.toggle('ipc__wishlist--active', !pressed);

			// Burst animation.
			btn.classList.add('ipc__wishlist--burst');
			setTimeout(function () { btn.classList.remove('ipc__wishlist--burst'); }, BURST_DURATION_MS);

			// Haptic feedback.
			try { navigator.vibrate(10); } catch (err) { /* unsupported */ }

			// Persist.
			if (sku) {
				const wl = getWishlist();
				const idx = wl.indexOf(sku);
				if (pressed) {
					if (idx !== -1) wl.splice(idx, 1);
					updateWishlistBadge(-1);
				} else {
					if (idx === -1) wl.push(sku);
					updateWishlistBadge(1);
				}
				saveWishlist(wl);
			}
		});
	}

	/* -----------------------------------------------
	   5. Size Pill Selection
	   ----------------------------------------------- */

	function initSizePills() {
		const grid = document.querySelector('.ipc-grid');
		if (!grid) return;

		grid.addEventListener('click', function (e) {
			const pill = e.target.closest('.ipc__size-pill');
			if (!pill) return;

			const card = pill.closest('.ipc, .prc');
			if (!card) return;

			// Deselect siblings.
			card.querySelectorAll('.ipc__size-pill').forEach(function (p) {
				p.classList.remove('ipc__size-pill--active');
				p.setAttribute('aria-checked', 'false');
			});

			// Select this one.
			pill.classList.add('ipc__size-pill--active');
			pill.setAttribute('aria-checked', 'true');

			const size = pill.getAttribute('data-size') || pill.textContent.trim();
			card.dataset.selectedSize = size;

			// Enable buy button.
			const buyBtn = card.querySelector('.ipc__buy-btn');
			if (buyBtn) {
				buyBtn.removeAttribute('disabled');
				const base = card.dataset.buyLabel || buyBtn.textContent;
				if (!card.dataset.buyLabel) card.dataset.buyLabel = buyBtn.textContent;
				buyBtn.textContent = base.replace(/\(.*?\)\s*/, '') .replace(/^(Pre-Order|Add to Cart)/, '$1 (' + size + ')');
			}
		});
	}

	/* -----------------------------------------------
	   6. Quick-Buy AJAX
	   ----------------------------------------------- */

	function initQuickBuy() {
		const grid = document.querySelector('.ipc-grid');
		if (!grid) return;

		const inFlight = new Set();

		grid.addEventListener('click', function (e) {
			const btn = e.target.closest('.ipc__buy-btn');
			if (!btn || btn.disabled) return;

			const card = btn.closest('.ipc');
			if (!card) return;

			const sku = card.getAttribute('data-product-sku') || '';
			if (inFlight.has(sku)) return;
			const size = card.dataset.selectedSize || '';
			const originalText = btn.textContent;

			inFlight.add(sku);
			btn.disabled = true;
			btn.classList.add('ipc__buy-btn--loading');
			btn.textContent = 'Adding\u2026';

			const fd = new FormData();
			fd.append('action', 'skyyrose_immersive_add_to_cart');
			fd.append('nonce', NONCE);
			fd.append('sku', sku);
			fd.append('attribute_pa_size', size);

			postAjax(AJAX_URL, fd)
				.then(function (json) {
					btn.classList.remove('ipc__buy-btn--loading');

					if (json && json.success) {
						btn.classList.add('ipc__buy-btn--added');
						btn.textContent = '\u2713 Added!';
						card.classList.add('ipc--added');
						setTimeout(function () { card.classList.remove('ipc--added'); }, ADD_GLOW_MS);

						// Update cart UI elements from response data.
						if (json.data) {
							var countEl = document.querySelector('.cart-count');
							if (countEl && json.data.cart_count !== undefined) {
								countEl.textContent = json.data.cart_count;
								countEl.classList.toggle('has-items', json.data.cart_count > 0);
							}
							var subtotalEl = document.querySelector('.cart-subtotal');
							if (subtotalEl && json.data.fragments && json.data.fragments['.cart-subtotal']) {
								var parser = new DOMParser();
								var doc = parser.parseFromString(json.data.fragments['.cart-subtotal'], 'text/html');
								var safe = doc.body.firstChild;
								if (safe && subtotalEl.parentNode) {
									subtotalEl.parentNode.replaceChild(safe, subtotalEl);
								}
							}
						}
					} else {
						btn.classList.add('ipc__buy-btn--error');
						btn.textContent = 'Try Again';
					}

					setTimeout(function () {
						btn.classList.remove('ipc__buy-btn--added', 'ipc__buy-btn--error');
						btn.textContent = originalText;
						btn.disabled = false;
						inFlight.delete(sku);
					}, BUY_RESET_MS);
				})
				.catch(function () {
					btn.classList.remove('ipc__buy-btn--loading');
					inFlight.delete(sku);

					// Fallback: navigate to product page.
					const link = card.querySelector('.ipc__title a');
					if (link && link.href) {
						window.location.href = link.href;
						return;
					}

					btn.classList.add('ipc__buy-btn--error');
					btn.textContent = 'Try Again';
					setTimeout(function () {
						btn.classList.remove('ipc__buy-btn--error');
						btn.textContent = originalText;
						btn.disabled = false;
					}, BUY_RESET_MS);
				});
		});
	}

	/* -----------------------------------------------
	   6b. Share Button
	   ----------------------------------------------- */

	function initShare() {
		var grid = document.querySelector('.ipc-grid');
		if (!grid) return;

		grid.addEventListener('click', function (e) {
			var btn = e.target.closest('.ipc__share');
			if (!btn) return;
			e.preventDefault();
			e.stopPropagation();

			var card = btn.closest('.ipc');
			var url = card ? card.getAttribute('data-product-url') : '';
			var nameEl = card ? card.querySelector('.ipc__title a') : null;
			var title = nameEl ? nameEl.textContent.trim() : '';

			if (navigator.share) {
				navigator.share({ title: title, url: url }).catch(function () {});
			} else if (url && navigator.clipboard) {
				navigator.clipboard.writeText(url).then(function () {
					btn.setAttribute('aria-label', 'Link copied!');
					setTimeout(function () {
						btn.setAttribute('aria-label', 'Share ' + title);
					}, 2000);
				}).catch(function () {});
			}
		});
	}

	/* -----------------------------------------------
	   7. Touch Gesture System
	   ----------------------------------------------- */

	const gestureStates = new WeakMap();
	const TAP_MAX_MS = 200;
	const DBL_MS     = 300;
	const LP_MS      = 320;
	const DRAG_PX    = 10;

	function triggerSingleTap(card) {
		const link = card.querySelector('.ipc__title a');
		if (link && link.href) window.location.href = link.href;
	}

	function triggerDoubleTap(card) {
		const viewer = card.querySelector('model-viewer');
		if (viewer && typeof viewer.activateAR === 'function') {
			try { viewer.activateAR(); } catch (e) { /* no AR support */ }
			return;
		}
		rotateCubeFace(card, 1);
	}

	function triggerLongPress(card) {
		// Integrate with existing quick-view modal.
		if (typeof window.skyyRoseOpenModal === 'function') {
			const pid = card.getAttribute('data-product-sku') || '';
			if (pid) { window.skyyRoseOpenModal(pid); return; }
		}
		try {
			card.dispatchEvent(new CustomEvent('ipc:longpress', {
				bubbles: true,
				detail: { sku: card.getAttribute('data-product-sku') || '' }
			}));
		} catch (err) { /* CustomEvent unsupported — fail silently */ }
	}

	function initGestures() {
		const grid = document.querySelector('.ipc-grid');
		if (!grid) return;

		grid.addEventListener('pointerdown', function (e) {
			const card = e.target.closest('.ipc');
			if (!card) return;
			if (e.target.closest('.ipc__buy-btn, .ipc__wishlist, .ipc__share, .ipc__size-pill')) return;

			let gs = gestureStates.get(card);
			if (!gs) {
				gs = { downTime: 0, downX: 0, downY: 0, moved: false, lastTapTime: 0, longPressTimer: null, singleTapTimer: null };
				gestureStates.set(card, gs);
			}

			gs.downTime = Date.now();
			gs.downX = e.clientX;
			gs.downY = e.clientY;
			gs.moved = false;

			clearTimeout(gs.longPressTimer);
			gs.longPressTimer = setTimeout(function () {
				if (!gs.moved) triggerLongPress(card);
			}, LP_MS);
		}, { passive: true });

		grid.addEventListener('pointermove', function (e) {
			const card = e.target.closest('.ipc');
			if (!card) return;
			const gs = gestureStates.get(card);
			if (!gs) return;
			if (Math.abs(e.clientX - gs.downX) > DRAG_PX || Math.abs(e.clientY - gs.downY) > DRAG_PX) {
				gs.moved = true;
				clearTimeout(gs.longPressTimer);
			}
		}, { passive: true });

		grid.addEventListener('pointerup', function (e) {
			const card = e.target.closest('.ipc');
			if (!card) return;
			if (e.target.closest('.ipc__buy-btn, .ipc__wishlist, .ipc__share, .ipc__size-pill')) return;

			const gs = gestureStates.get(card);
			if (!gs) return;
			clearTimeout(gs.longPressTimer);
			if (gs.moved) return;

			const now = Date.now();
			const holdMs = now - gs.downTime;

			if (holdMs <= TAP_MAX_MS) {
				if ((now - gs.lastTapTime) <= DBL_MS && gs.lastTapTime > 0) {
					clearTimeout(gs.singleTapTimer);
					gs.lastTapTime = 0;
					triggerDoubleTap(card);
				} else {
					gs.lastTapTime = now;
					clearTimeout(gs.singleTapTimer);
					gs.singleTapTimer = setTimeout(function () {
						gs.lastTapTime = 0;
						triggerSingleTap(card);
					}, DBL_MS + 10);
				}
			}
		}, { passive: true });
	}

	/* -----------------------------------------------
	   8. model-viewer Activation
	   ----------------------------------------------- */

	function initModelViewer() {
		document.querySelectorAll('.ipc[data-glb-src]').forEach(function (card) {
			const glbSrc = (card.getAttribute('data-glb-src') || '').trim();
			if (!glbSrc) return;

			card.classList.add('ipc--3d-active');
			const viewer = card.querySelector('.ipc__3d, model-viewer');
			if (viewer) viewer.setAttribute('src', glbSrc);
			const cube = card.querySelector('.ipc__cube');
			if (cube) cube.setAttribute('aria-hidden', 'true');
		});
	}

	/* -----------------------------------------------
	   9. Scarcity Counter Animation
	   ----------------------------------------------- */

	function animateScarcityCounter(el) {
		const target = parseInt((el.textContent || '').replace(/[^0-9]/g, ''), 10);
		if (isNaN(target)) return;

		const container = el.closest('.ipc__scarcity');
		if (container && target > 20) { container.hidden = true; return; }

		const start = target + 5;
		const startTime = performance.now();

		(function tick(now) {
			const p = clamp((now - startTime) / SCARCITY_MS, 0, 1);
			el.textContent = Math.round(start - (start - target) * p);
			if (p < 1) requestAnimationFrame(tick);
		})(performance.now());
	}

	function initScarcityCounters() {
		const counters = document.querySelectorAll('.ipc__stock-count');
		if (!counters.length) return;

		if (!('IntersectionObserver' in window)) {
			counters.forEach(animateScarcityCounter);
			return;
		}

		const observer = new IntersectionObserver(function (entries) {
			entries.forEach(function (entry) {
				if (!entry.isIntersecting) return;
				animateScarcityCounter(entry.target);
				observer.unobserve(entry.target);
			});
		}, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

		counters.forEach(function (el) { observer.observe(el); });
	}

	/* -----------------------------------------------
	   10. Scroll Entrance Animation
	   ----------------------------------------------- */

	function initScrollEntrance(reducedMotion) {
		const cards = document.querySelectorAll('.ipc');
		if (!cards.length) return;

		if (reducedMotion || !('IntersectionObserver' in window)) {
			cards.forEach(function (c) { c.classList.add('ipc--visible'); });
			return;
		}

		const observer = new IntersectionObserver(function (entries) {
			entries.forEach(function (entry) {
				if (!entry.isIntersecting) return;
				entry.target.classList.add('ipc--visible');
				observer.unobserve(entry.target);
			});
		}, { threshold: 0.1, rootMargin: '0px 0px -60px 0px' });

		cards.forEach(function (c) { observer.observe(c); });
	}

	/* -----------------------------------------------
	   11. Pre-Order Reveal
	   ----------------------------------------------- */

	function formatCountdown(s) {
		const d  = Math.floor(s / 86400);
		const h  = Math.floor((s % 86400) / 3600);
		const m  = Math.floor((s % 3600) / 60);
		const ss = s % 60;
		const pad = function (n) { return String(n).padStart(2, '0'); };
		return d > 0
			? d + ':' + pad(h) + ':' + pad(m) + ':' + pad(ss)
			: pad(h) + ':' + pad(m) + ':' + pad(ss);
	}

	function createParticleBurst(prc) {
		const container = prc.querySelector('.prc__particles') || prc;
		for (let i = 0; i < 6; i++) {
			const p = document.createElement('div');
			p.className = 'prc__particle prc__particle--' + i;
			p.setAttribute('aria-hidden', 'true');
			container.appendChild(p);
			setTimeout(function () { if (p.parentNode) p.parentNode.removeChild(p); }, 700);
		}
	}

	function revealPrc(prc) {
		prc.classList.remove('prc--locked');
		setTimeout(function () {
			prc.classList.add('prc--revealed');
			createParticleBurst(prc);
		}, 100);
	}

	function initPreOrderReveal() {
		document.querySelectorAll('.prc').forEach(function (prc) {
			const revealAtStr = prc.getAttribute('data-reveal-at') || '';
			if (!revealAtStr) return;

			const revealAt = new Date(revealAtStr);
			if (isNaN(revealAt.getTime())) return;

			const timerEl = prc.querySelector('.prc__timer');

			if (Date.now() >= revealAt.getTime()) {
				revealPrc(prc);
				return;
			}

			(function tick() {
				const remaining = Math.max(0, Math.floor((revealAt.getTime() - Date.now()) / 1000));
				if (remaining <= 0) { revealPrc(prc); return; }
				if (timerEl) timerEl.textContent = formatCountdown(remaining);
				setTimeout(tick, 1000);
			})();
		});
	}

	/* -----------------------------------------------
	   12. Keyboard Navigation
	   ----------------------------------------------- */

	function initKeyboard() {
		document.addEventListener('keydown', function (e) {
			const focused = document.activeElement;
			if (!focused) return;

			// Card-level navigation.
			const card = focused.closest ? focused.closest('.ipc') : null;
			if (card) {
				if (e.key === 'ArrowRight') { e.preventDefault(); rotateCubeFace(card, 1); return; }
				if (e.key === 'ArrowLeft')  { e.preventDefault(); rotateCubeFace(card, -1); return; }
				if ((e.key === 'Enter' || e.key === ' ') && focused === card) {
					e.preventDefault();
					triggerSingleTap(card);
					return;
				}
			}

			// Size pill arrow navigation.
			if (focused.classList && focused.classList.contains('ipc__size-pill')) {
				const container = focused.closest('.ipc__sizes, .prc__sizes');
				if (!container) return;

				const pills = Array.from(container.querySelectorAll('.ipc__size-pill'));
				const ci = pills.indexOf(focused);
				let target = -1;

				if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
					target = (ci + 1) % pills.length;
				} else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
					target = (ci - 1 + pills.length) % pills.length;
				} else if (e.key === 'Enter' || e.key === ' ') {
					focused.click();
					e.preventDefault();
					return;
				}

				if (target >= 0) {
					e.preventDefault();
					pills[target].focus();
					pills[target].click();
				}
			}
		});
	}

	/* -----------------------------------------------
	   13. Init
	   ----------------------------------------------- */

	function init() {
		const reducedMotion = window.matchMedia &&
			window.matchMedia('(prefers-reduced-motion: reduce)').matches;

		initSkeletonLoading();
		initScrollEntrance(reducedMotion);
		initCubeRotation(reducedMotion);
		if (!reducedMotion) initTilt();
		initWishlist();
		initSizePills();
		initQuickBuy();
		initShare();
		initGestures();
		initModelViewer();
		initScarcityCounters();
		initPreOrderReveal();
		initKeyboard();
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}

})();
