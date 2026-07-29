/**
 * Build-time asset bundles — static concatenation of individually-minified
 * outputs, grouped ONLY by handles that share (a) the same enqueue condition
 * and (b) the same async/render-blocking semantics in enqueue-performance.php.
 *
 * This is NOT WordPress runtime concatenation: CONCATENATE_SCRIPTS stays
 * false (WP.com MIME constraint). Bundles are physical .min files emitted by
 * build-css.js / build-js.js and enqueued statically in inc/enqueue.php.
 *
 * ORDER IS LOAD-BEARING. Each list preserves the exact enqueue (cascade)
 * order of its members. Reordering across bundle boundaries was proven
 * duplicate-selector-safe on 2026-07-29 (zero exact-selector overlap between
 * every pair whose relative print position changes). Re-run that check before
 * moving any file between bundles.
 *
 * Paths are theme-root-relative SOURCE files; the build derives each part's
 * minified output and concatenates those, so a bundle is byte-identical to
 * its parts' .min files joined in order.
 */

'use strict';

module.exports = {
	css: {
		// Always render-blocking, unconditionally enqueued globals, in
		// enqueue order. Handle: skyyrose-main (keeps the fetchpriority=high
		// critical-handle entry matching).
		'assets/css/bundles/core.min.css': [
			'assets/css/main.css',
			'assets/css/design-tokens.css',
			'assets/css/components.css',
			'assets/css/system/animations.css',
			'assets/css/header.css',
			'assets/css/mobile-bottom-nav.css',
			'assets/css/agency-tier-visuals.css',
		],
		// Unconditional pair, async-swapped together on tall-content slugs.
		// Handle: skyyrose-footer (keeps the async-handle entry matching).
		'assets/css/bundles/footer.min.css': [
			'assets/css/footer.css',
			'assets/css/footer-cro.css',
		],
		// Same mascot kill-switch gate, skyy-walk depends on mascot.
		// Handle: skyyrose-mascot.
		'assets/css/bundles/mascot.min.css': [
			'assets/css/mascot.css',
			'assets/css/skyy-walk.css',
		],
		// Same skip-slug condition, both always async (print-media swap).
		// Handle: skyyrose-size-guide.
		'assets/css/bundles/optional-ui.min.css': [
			'assets/css/size-guide.css',
			'assets/css/luxury-cursor.css',
		],
		// WooCommerce base + page-specific, one bundle per slug (base first —
		// same cascade order the dependency chain produces today).
		// Handle: skyyrose-template-woocommerce on each slug.
		'assets/css/bundles/wc-cart.min.css': [
			'assets/css/woocommerce.css',
			'assets/css/woocommerce-cart.css',
		],
		'assets/css/bundles/wc-checkout.min.css': [
			'assets/css/woocommerce.css',
			'assets/css/woocommerce-checkout.css',
		],
		'assets/css/bundles/wc-account.min.css': [
			'assets/css/woocommerce.css',
			'assets/css/woocommerce-account.css',
		],
	},
	js: {
		// Unconditional globals, all defer + in_footer, independent IIFEs, in
		// enqueue order. Handle: skyyrose-navigation (keeps the
		// skyyrose_localize_scripts target + wp_script_is check matching).
		'assets/js/bundles/core.min.js': [
			'assets/js/navigation.js',
			'assets/js/toast.js',
			'assets/js/footer-cro.js',
			'assets/js/page-transitions.js',
		],
	},
};
