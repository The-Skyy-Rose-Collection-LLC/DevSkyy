(() => {
	'use strict';

	const SELECTOR = '[data-sr2-product-viewer]';
	const LOAD_EVENT = 'skyyrose2:product-viewer-load';
	const ERROR_EVENT = 'skyyrose2:product-viewer-error';
	const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
	const initialized = new WeakSet();
	let intersectionObserver = null;
	const prefersReducedMotion = () => reducedMotionQuery.matches;
	const savesData = () => Boolean(navigator.connection && navigator.connection.saveData);
	const isInViewport = (element) => {
		const bounds = element.getBoundingClientRect();
		return bounds.bottom > 0
			&& bounds.right > 0
			&& bounds.top < window.innerHeight
			&& bounds.left < window.innerWidth;
	};

	const emit = (container, type, detail) => {
		container.dispatchEvent(new CustomEvent(type, {
			bubbles: true,
			detail,
		}));
	};

	const isAllowedAssetUrl = (value, extensionRequired) => {
		if (!value) return false;

		try {
			const parsed = new URL(value, document.baseURI);
			const secure = parsed.protocol === 'https:';
			const loopbackHosts = ['localhost', '127.0.0.1', '::1'];
			const localHttp = parsed.protocol === 'http:'
				&& window.location.protocol === 'http:'
				&& loopbackHosts.includes(parsed.hostname);
			if (!secure && !localHttp) return false;
			return !extensionRequired || parsed.pathname.toLowerCase().endsWith('.glb');
		} catch {
			return false;
		}
	};

	const waitForModelViewer = () => {
		if (!window.customElements || !window.customElements.whenDefined) {
			return Promise.reject(new Error('custom-elements-unavailable'));
		}

		return window.customElements.whenDefined('model-viewer');
	};

	const setRotation = (viewer, button, enabled) => {
		viewer.toggleAttribute('auto-rotate', enabled);
		button.setAttribute('aria-pressed', String(enabled));
	};

	const resetCamera = (viewer) => {
		viewer.cameraOrbit = 'auto auto auto';
		viewer.cameraTarget = 'auto auto auto';
		viewer.fieldOfView = 'auto';
		if (typeof viewer.jumpCameraToGoal === 'function') viewer.jumpCameraToGoal();
	};

	const activateViewer = async (container, loadButton) => {
		if (initialized.has(container)) return;
		initialized.add(container);

		const modelUrl = (container.dataset.modelUrl || '').trim();
		const poster = (container.dataset.poster || '').trim();
		const alt = (container.dataset.alt || '').trim();
		const sku = (container.dataset.sku || '').trim();
		const viewer = container.querySelector('[data-sr2-model]');
		const fallback = container.querySelector('[data-sr2-viewer-fallback]');
		const controls = container.querySelector('[data-sr2-viewer-controls]');
		const rotateButton = container.querySelector('[data-sr2-viewer-rotate]');
		const resetButton = container.querySelector('[data-sr2-viewer-reset]');
		const status = container.querySelector('[data-sr2-viewer-status]');

		const fail = (reason) => {
			container.classList.remove('is-loading', 'is-loaded');
			container.classList.add('has-viewer-error');
			container.setAttribute('aria-busy', 'false');
			if (viewer) {
				viewer.hidden = true;
				viewer.removeAttribute('src');
			}
			if (fallback) {
				fallback.hidden = false;
				const fallbackMessage = fallback.querySelector('p');
				if (fallbackMessage) {
					fallbackMessage.textContent = '3D view unavailable. Product photography remains available.';
				}
			}
			if (controls) controls.hidden = true;
			if (status) status.textContent = '3D view unavailable. Product photography remains available.';
			if (loadButton) {
				loadButton.remove();
				if (fallback) {
					fallback.tabIndex = -1;
					fallback.focus({ preventScroll: true });
				}
			}
			emit(container, ERROR_EVENT, { reason, modelUrl, sku });
		};

		if (!viewer || !controls || !rotateButton || !resetButton || !status) {
			fail('incomplete-viewer-markup');
			return;
		}

		if (!alt || !isAllowedAssetUrl(modelUrl, true)) {
			fail(!alt ? 'missing-alt' : 'invalid-model-url');
			return;
		}

		container.classList.remove('has-viewer-error');
		container.classList.add('is-loading');
		container.setAttribute('aria-busy', 'true');
		status.textContent = 'Loading interactive 3D view.';
		if (loadButton) {
			loadButton.disabled = true;
			loadButton.setAttribute('aria-busy', 'true');
			loadButton.textContent = 'Loading 3D view';
		}

		try {
			await waitForModelViewer();

			if (!isInViewport(container)) {
				initialized.delete(container);
				container.classList.remove('is-loading');
				container.setAttribute('aria-busy', 'false');
				status.textContent = '';
				if (loadButton) {
					loadButton.disabled = false;
					loadButton.removeAttribute('aria-busy');
					loadButton.textContent = 'Load 3D view';
				}
				observeContainer(container);
				return;
			}

			viewer.alt = alt;
			viewer.setAttribute('alt', alt);
			if (isAllowedAssetUrl(poster, false)) viewer.setAttribute('poster', poster);
			viewer.hidden = false;

			const initialRotation = !prefersReducedMotion() && !savesData();
			setRotation(viewer, rotateButton, initialRotation);

			rotateButton.addEventListener('click', () => {
				setRotation(viewer, rotateButton, rotateButton.getAttribute('aria-pressed') !== 'true');
			});
			resetButton.addEventListener('click', () => resetCamera(viewer));

			let settled = false;
			const onLoad = () => {
				if (settled) return;
				settled = true;
				viewer.removeEventListener('error', onError);
				container.classList.remove('is-loading', 'has-viewer-error');
				container.classList.add('is-loaded');
				container.setAttribute('aria-busy', 'false');
				if (fallback) fallback.hidden = true;
				controls.hidden = false;
				status.textContent = 'Interactive 3D view ready.';
				if (loadButton) {
					loadButton.remove();
					rotateButton.focus({ preventScroll: true });
				}
				emit(container, LOAD_EVENT, { modelUrl, sku, viewer });
			};

			const onError = (event) => {
				if (settled) return;
				settled = true;
				viewer.removeEventListener('load', onLoad);
				const reason = event.detail && event.detail.type ? event.detail.type : 'model-load-failed';
				fail(reason);
			};

			viewer.addEventListener('load', onLoad, { once: true });
			viewer.addEventListener('error', onError, { once: true });
			const stopForReducedMotion = (event) => {
				if (event.matches) setRotation(viewer, rotateButton, false);
			};
			if (typeof reducedMotionQuery.addEventListener === 'function') {
				reducedMotionQuery.addEventListener('change', stopForReducedMotion, { once: true });
			} else if (typeof reducedMotionQuery.addListener === 'function') {
				reducedMotionQuery.addListener(stopForReducedMotion);
			}

			// The approved URL comes only from the server resolver. Assigning it here is
			// the network boundary: no SKU-derived or filename-derived fallback exists.
			viewer.setAttribute('src', modelUrl);
		} catch (error) {
			fail(error instanceof Error ? error.message : 'viewer-activation-failed');
		}
	};

	const offerSaveDataLoad = (container) => {
		if (container.querySelector('[data-sr2-viewer-load]')) return;

		const stage = container.querySelector('.sr2-product-3d__stage');
		const status = container.querySelector('[data-sr2-viewer-status]');
		if (!stage) return;

		const button = document.createElement('button');
		button.type = 'button';
		button.className = 'sr2-product-3d__load sr2-button';
		button.dataset.sr2ViewerLoad = '';
		button.textContent = 'Load 3D view';
		button.addEventListener('click', () => activateViewer(container, button));
		stage.append(button);
		container.classList.add('is-save-data');
		if (status) status.textContent = 'Data saver is on. Activate the button to load the 3D view.';
	};

	const onIntersection = (container) => {
		if (savesData()) {
			offerSaveDataLoad(container);
			return;
		}
		activateViewer(container, null);
	};

	const observeManually = (container) => {
		let frame = 0;
		const cleanup = () => {
			window.removeEventListener('scroll', requestCheck);
			window.removeEventListener('resize', requestCheck);
			window.removeEventListener('pagehide', cleanup);
		};
		const check = () => {
			frame = 0;
			if (!container.isConnected) {
				cleanup();
				return;
			}
			if (!isInViewport(container)) return;
			cleanup();
			onIntersection(container);
		};
		const requestCheck = () => {
			if (!frame) frame = window.requestAnimationFrame(check);
		};
		window.addEventListener('scroll', requestCheck, { passive: true });
		window.addEventListener('resize', requestCheck, { passive: true });
		window.addEventListener('pagehide', cleanup, { once: true });
		requestCheck();
	};

	const observeContainer = (container) => {
		if (intersectionObserver) {
			intersectionObserver.observe(container);
			return;
		}
		observeManually(container);
	};

	const containers = document.querySelectorAll(SELECTOR);
	if (!containers.length) return;

	if ('IntersectionObserver' in window) {
		intersectionObserver = new IntersectionObserver((entries) => {
			entries.forEach((entry) => {
				if (!entry.isIntersecting) return;
				intersectionObserver.unobserve(entry.target);
				onIntersection(entry.target);
			});
		}, { rootMargin: '0px', threshold: 0.01 });
	}

	containers.forEach(observeContainer);
})();
