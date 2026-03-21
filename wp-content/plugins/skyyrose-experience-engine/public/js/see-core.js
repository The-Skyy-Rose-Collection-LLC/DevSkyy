/**
 * SkyyRose Experience Engine — Core Event Bus & Module Registry
 *
 * Central nervous system for all SEE modules. Provides:
 *   1. Event bus (pub/sub via CustomEvents)
 *   2. Module lifecycle management (init → ready → destroy)
 *   3. Shared config from wp_localize_script
 *   4. Theme detection (enhanced vs standalone mode)
 *   5. Design Narrative directive consumption
 *   6. Accessibility: prefers-reduced-motion respect
 *
 * Public API: window.SkyyRoseExperience (SEE)
 *
 * Follows the same vanilla JS IIFE pattern as the existing theme engines
 * (aurora-engine.js, adaptive-personalization.js) for consistency.
 *
 * @package SkyyRose_Experience_Engine
 * @since   1.0.0
 */

(function () {
	'use strict';

	/* ==========================================================================
	   Configuration (injected via wp_localize_script as window.seeConfig)
	   ========================================================================== */

	var config = window.seeConfig || {};

	/* ==========================================================================
	   Feature Detection
	   ========================================================================== */

	var prefersReducedMotion = window.matchMedia
		? window.matchMedia('(prefers-reduced-motion: reduce)').matches
		: false;

	var supportsIntersectionObserver = 'IntersectionObserver' in window;
	var supportsScrollTimeline       = 'ScrollTimeline' in window;
	var supportsDialog               = typeof HTMLDialogElement !== 'undefined';
	var supportsIdleCallback         = 'requestIdleCallback' in window;

	/* ==========================================================================
	   Event Bus — CustomEvent-based pub/sub
	   Uses 'see:' prefix to avoid colliding with theme's 'cie:' convention.
	   ========================================================================== */

	var bus = document.createElement('div');

	function emit(eventName, detail) {
		bus.dispatchEvent(new CustomEvent('see:' + eventName, { detail: detail || {} }));
	}

	function on(eventName, callback) {
		bus.addEventListener('see:' + eventName, function (e) {
			callback(e.detail);
		});
	}

	function off(eventName, callback) {
		bus.removeEventListener('see:' + eventName, callback);
	}

	/* ==========================================================================
	   Module Registry
	   ========================================================================== */

	var modules = {};
	var readyQueue = [];
	var domReady = false;

	/**
	 * Register a module with the engine.
	 *
	 * @param {string} name    Module slug (e.g., 'experience-analyzer').
	 * @param {object} module  Module object with init(), ready(), destroy() methods.
	 */
	function registerModule(name, module) {
		if (modules[name]) {
			return;
		}

		modules[name] = {
			instance: module,
			state: 'registered', // registered → initialized → ready → destroyed
		};

		// Initialize immediately — ready() deferred to DOMContentLoaded.
		if (typeof module.init === 'function') {
			try {
				module.init(getModuleConfig(name));
				modules[name].state = 'initialized';
			} catch (err) {
				/* eslint-disable-next-line no-console */
				console.error('[SEE] Module "' + name + '" init failed:', err);
			}
		}

		if (domReady) {
			fireReady(name);
		} else {
			readyQueue.push(name);
		}

		emit('module:registered', { name: name });
	}

	function fireReady(name) {
		var mod = modules[name];
		if (mod && mod.state === 'initialized' && typeof mod.instance.ready === 'function') {
			try {
				mod.instance.ready();
				mod.state = 'ready';
				emit('module:ready', { name: name });
			} catch (err) {
				/* eslint-disable-next-line no-console */
				console.error('[SEE] Module "' + name + '" ready failed:', err);
			}
		}
	}

	function destroyModule(name) {
		var mod = modules[name];
		if (mod && typeof mod.instance.destroy === 'function') {
			mod.instance.destroy();
			mod.state = 'destroyed';
			emit('module:destroyed', { name: name });
		}
	}

	/**
	 * Get merged config for a module: base config + directive overrides.
	 */
	function getModuleConfig(name) {
		var base = (config.modules && config.modules[name]) || {};
		var directives = getDirectiveConfig(name);
		return Object.assign({}, base, directives);
	}

	/**
	 * Get directive config overrides for a module from active narratives.
	 */
	function getDirectiveConfig(name) {
		var narrativeConfig = {};
		var directives = config.directives || [];

		directives.forEach(function (d) {
			if (d.status !== 'accepted') {
				return;
			}
			var target = d.target || 'all';
			if (target === 'all' || target === name) {
				Object.assign(narrativeConfig, d.config || {});
			}
		});

		return narrativeConfig;
	}

	/* ==========================================================================
	   Context — Page type, collection, product data
	   ========================================================================== */

	function getContext() {
		return {
			pageType:       config.pageType || 'unknown',
			collection:     config.collection || '',
			collectionConfig: config.collectionConfig || {},
			productId:      config.productId || 0,
			productSku:     config.productSku || '',
			isFlagship:     config.isFlagship || false,
			isWooCommerce:  config.isWooCommerce || false,
		};
	}

	/* ==========================================================================
	   Storage Helpers (namespaced 'see_' to avoid theme 'sr_' collisions)
	   ========================================================================== */

	var storage = {
		get: function (key) {
			try {
				var raw = localStorage.getItem('see_' + key);
				return raw ? JSON.parse(raw) : null;
			} catch (e) {
				return null;
			}
		},
		set: function (key, value) {
			try {
				localStorage.setItem('see_' + key, JSON.stringify(value));
			} catch (e) {
				// Storage full or unavailable — fail silently.
			}
		},
		session: {
			get: function (key) {
				try {
					var raw = sessionStorage.getItem('see_' + key);
					return raw ? JSON.parse(raw) : null;
				} catch (e) {
					return null;
				}
			},
			set: function (key, value) {
				try {
					sessionStorage.setItem('see_' + key, JSON.stringify(value));
				} catch (e) {
					// Fail silently.
				}
			},
		},
	};

	/* ==========================================================================
	   DOMContentLoaded — Fire ready() for all queued modules
	   ========================================================================== */

	function onDomReady() {
		domReady = true;
		readyQueue.forEach(function (name) {
			fireReady(name);
		});
		readyQueue = [];
		emit('engine:ready', { modules: Object.keys(modules) });
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', onDomReady);
	} else {
		onDomReady();
	}

	/* ==========================================================================
	   Cleanup on page unload
	   ========================================================================== */

	window.addEventListener('beforeunload', function () {
		Object.keys(modules).forEach(destroyModule);
	});

	/* ==========================================================================
	   Public API — window.SkyyRoseExperience
	   ========================================================================== */

	window.SkyyRoseExperience = {
		// Event bus.
		on:       on,
		off:      off,
		emit:     emit,

		// Module lifecycle.
		registerModule: registerModule,
		getModule: function (name) {
			return modules[name] ? modules[name].instance : null;
		},
		getActiveModules: function () {
			return Object.keys(modules).filter(function (n) {
				return modules[n].state !== 'destroyed';
			});
		},

		// Config & context.
		getConfig:       function () { return config; },
		getModuleConfig: getModuleConfig,
		getContext:       getContext,
		getDirectives:   function () { return config.directives || []; },

		// Utilities.
		storage:               storage,
		prefersReducedMotion:  prefersReducedMotion,
		supportsIntersection:  supportsIntersectionObserver,
		supportsScrollTimeline: supportsScrollTimeline,
		supportsDialog:        supportsDialog,
		supportsIdleCallback:  supportsIdleCallback,

		// Version.
		version: '1.0.0',
	};

})();
