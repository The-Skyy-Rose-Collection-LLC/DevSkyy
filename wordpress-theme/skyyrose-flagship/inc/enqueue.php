<?php
/**
 * Enqueue Scripts & Styles
 *
 * Handles all CSS and JS enqueue logic with conditional loading per template.
 * Global assets load on every page; template-specific assets load only where needed.
 *
 * @package SkyyRose
 * @since   3.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Enqueue self-hosted fonts (all brand typography).
 *
 * GDPR-compliant: zero external requests to Google Fonts.
 * All 8 font families served locally from assets/fonts/ as woff2.
 * Fonts: Inter, Playfair Display, Cinzel, Cormorant Garamond,
 *        Oswald, Barlow, Bebas Neue, Instrument Serif.
 *
 * @since 3.2.1
 * @updated 4.1.0 — self-hosted all Google Fonts families
 * @return void
 */
function skyyrose_enqueue_local_fonts() {
	wp_enqueue_style(
		'skyyrose-fonts',
		SKYYROSE_ASSETS_URI . '/css/fonts.css',
		array(),
		SKYYROSE_VERSION
	);
}

/**
 * Enqueue global styles that load on every page.
 *
 * @since 3.0.0
 * @return void
 */
function skyyrose_enqueue_global_styles() {

	$base_uri = SKYYROSE_ASSETS_URI . '/css';
	$base_dir = SKYYROSE_DIR . '/assets/css';
	$use_min  = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;

	// Main theme stylesheet (style.css with WordPress header).
	wp_enqueue_style(
		'skyyrose-style',
		get_stylesheet_uri(),
		array(),
		SKYYROSE_VERSION
	);

	// Elite Web Builder global styles: font vars, grain overlay, sr-container.
	$main_file = $use_min && file_exists( $base_dir . '/main.min.css' ) ? 'main.min.css' : 'main.css';
	if ( file_exists( $base_dir . '/' . $main_file ) ) {
		wp_enqueue_style(
			'skyyrose-main',
			$base_uri . '/' . $main_file,
			array( 'skyyrose-style', 'skyyrose-fonts' ),
			SKYYROSE_VERSION
		);
	}

	// Design tokens: CSS custom properties for colors, spacing, typography.
	$tokens_file = $use_min && file_exists( $base_dir . '/design-tokens.min.css' ) ? 'design-tokens.min.css' : 'design-tokens.css';
	wp_enqueue_style(
		'skyyrose-design-tokens',
		$base_uri . '/' . $tokens_file,
		array( 'skyyrose-style' ),
		SKYYROSE_VERSION
	);

	// Components: reusable component styles (buttons, cards, forms, etc.).
	$comp_file = $use_min && file_exists( $base_dir . '/components.min.css' ) ? 'components.min.css' : 'components.css';
	if ( file_exists( $base_dir . '/' . $comp_file ) ) {
		wp_enqueue_style(
			'skyyrose-components',
			$base_uri . '/' . $comp_file,
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	// Animations: unified scroll-reveal system (.rv, .rv-left, .rv-right, .rv-scale).
	$anim_file = $use_min && file_exists( $base_dir . '/system/animations.min.css' ) ? 'system/animations.min.css' : 'system/animations.css';
	if ( file_exists( $base_dir . '/' . $anim_file ) ) {
		wp_enqueue_style(
			'skyyrose-animations',
			$base_uri . '/' . $anim_file,
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	// Premium animations: clip-path reveals, split-text, stagger, magnetic, parallax.
	// Conditionally loaded — skip on lightweight pages where the extra CSS is wasted
	// (cart, checkout, blog, search, 404, generic pages, contact).
	// Loaded on: front-page, about, immersive, preorder-gateway, collection pages,
	// single-product, shop-archive (footer uses stagger-grid + rv-clip-up).
	$prem_anim = $use_min && file_exists( $base_dir . '/system/animations-premium.min.css' )
		? 'system/animations-premium.min.css' : 'system/animations-premium.css';
	if ( file_exists( $base_dir . '/' . $prem_anim ) ) {
		$prem_slug    = skyyrose_get_current_template_slug();
		$prem_skip    = array( 'cart', 'checkout', 'blog', 'single', 'page', 'contact', '404', 'default' );
		$skip_premium = in_array( $prem_slug, $prem_skip, true );
		if ( ! $skip_premium ) {
			wp_enqueue_style(
				'skyyrose-animations-premium',
				$base_uri . '/' . $prem_anim,
				array( 'skyyrose-animations' ),
				SKYYROSE_VERSION
			);
		}
	}

	// Commercial polish is now enqueued at priority 25 via
	// skyyrose_enqueue_commercial_polish() to guarantee it loads AFTER
	// all template-specific stylesheets (priority 20).

	// Header: navbar, search overlay, mobile menu, dropdowns.
	$header_file = $use_min && file_exists( $base_dir . '/header.min.css' ) ? 'header.min.css' : 'header.css';
	if ( file_exists( $base_dir . '/' . $header_file ) ) {
		wp_enqueue_style(
			'skyyrose-header',
			$base_uri . '/' . $header_file,
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	// Footer: newsletter bar, grid columns, copyright bar, brand column.
	$footer_file = $use_min && file_exists( $base_dir . '/footer.min.css' ) ? 'footer.min.css' : 'footer.css';
	if ( file_exists( $base_dir . '/' . $footer_file ) ) {
		wp_enqueue_style(
			'skyyrose-footer',
			$base_uri . '/' . $footer_file,
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	// Mobile bottom navigation bar (hidden via CSS on desktop ≥769px).
	$mobnav_file = $use_min && file_exists( $base_dir . '/mobile-bottom-nav.min.css' ) ? 'mobile-bottom-nav.min.css' : 'mobile-bottom-nav.css';
	if ( file_exists( $base_dir . '/' . $mobnav_file ) ) {
		wp_enqueue_style(
			'skyyrose-mobile-nav',
			$base_uri . '/' . $mobnav_file,
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}

	// Cookie consent banner (GDPR).
	if ( file_exists( $base_dir . '/cookie-consent.css' ) ) {
		wp_enqueue_style(
			'skyyrose-cookie-consent',
			$base_uri . '/cookie-consent.css',
			array(),
			SKYYROSE_VERSION
		);
	}

	// Lightweight slugs skip optional CSS bundles (size guide, luxury cursor,
	// skeleton). Cart / checkout / 404 / search / blog / single never trigger
	// these features, so shipping their CSS is dead bytes. v1.5.12 audit.
	$skip_optional_css = in_array(
		skyyrose_get_current_template_slug(),
		array( 'cart', 'checkout', 'blog', 'single', '404', 'search', 'default' ),
		true
	);

	// Size guide modal (trigger via [data-open-size-guide] or .js-size-guide-trigger).
	if ( ! $skip_optional_css && file_exists( $base_dir . '/size-guide.css' ) ) {
		wp_enqueue_style(
			'skyyrose-size-guide',
			$base_uri . '/size-guide.css',
			array(),
			SKYYROSE_VERSION
		);
	}

	// Luxury cursor — dot follower (desktop only, CSS hidden on touch/mobile).
	if ( ! $skip_optional_css && file_exists( $base_dir . '/luxury-cursor.css' ) ) {
		wp_enqueue_style(
			'skyyrose-luxury-cursor',
			$base_uri . '/luxury-cursor.css',
			array(),
			SKYYROSE_VERSION
		);
	}

	// Skeleton loading states — shimmer placeholders for images and cards.
	if ( ! $skip_optional_css && file_exists( $base_dir . '/skeleton.css' ) ) {
		wp_enqueue_style(
			'skyyrose-skeleton',
			$base_uri . '/skeleton.css',
			array(),
			SKYYROSE_VERSION
		);
	}

	// Skyy mascot CSS disabled — character widget is not rendered until art is finalized.
	// Re-enable mascot.min.css and skyy-walk.css when get_template_part('skyy-mascot')
	// is restored in footer.php and front-page.php.

	// Agency-Tier Visuals: Double-Bezel, Island buttons, macro-whitespace.
	wp_enqueue_style(
		'skyyrose-agency-visuals',
		$base_uri . '/agency-tier-visuals.css',
		array( 'skyyrose-design-tokens', 'skyyrose-components' ),
		SKYYROSE_VERSION
	);

	// Cinematic hero (template-parts/hero-cinematic.php): image/video hero with a
	// collection lockup. Loaded in <head> on content templates so this above-the-fold
	// part never flashes unstyled. Skipped on lightweight slugs that never host it.
	$hero_file = $use_min && file_exists( $base_dir . '/hero-cinematic.min.css' )
		? 'hero-cinematic.min.css' : 'hero-cinematic.css';
	$hero_skip = in_array(
		skyyrose_get_current_template_slug(),
		array( 'cart', 'checkout', 'blog', 'single', 'page', 'contact', '404', 'search', 'default' ),
		true
	);
	if ( ! $hero_skip && file_exists( $base_dir . '/' . $hero_file ) ) {
		wp_enqueue_style(
			'skyyrose-hero-cinematic',
			$base_uri . '/' . $hero_file,
			array( 'skyyrose-design-tokens' ),
			SKYYROSE_VERSION
		);
	}
}

/**
 * Enqueue global scripts that load on every page.
 *
 * @since 3.0.0
 * @return void
 */
function skyyrose_enqueue_global_scripts() {

	$js_uri  = SKYYROSE_ASSETS_URI . '/js';
	$js_dir  = SKYYROSE_DIR . '/assets/js';
	$css_uri = SKYYROSE_ASSETS_URI . '/css';
	$css_dir = SKYYROSE_DIR . '/assets/css';
	$use_min = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;

	// Lightweight slugs (cart/checkout/404/search) don't trigger premium
	// animations. Skip Motion One + premium-interactions to save ~60KB parse.
	// v1.5.12 audit. Same skip list as global_styles.
	$skip_premium_js = in_array(
		skyyrose_get_current_template_slug(),
		array( 'cart', 'checkout', 'blog', 'single', '404', 'search', 'default' ),
		true
	);

	// Navigation script (hamburger toggle, keyboard nav, dropdowns).
	$nav_file = $use_min && file_exists( $js_dir . '/navigation.min.js' ) ? 'navigation.min.js' : 'navigation.js';
	if ( file_exists( $js_dir . '/' . $nav_file ) ) {
		wp_enqueue_script(
			'skyyrose-navigation',
			$js_uri . '/' . $nav_file,
			array(),
			SKYYROSE_VERSION,
			array(
				'strategy'  => 'defer',
				'in_footer' => true,
			)
		);
	}

	// Toast notification utility (global, used by wishlist, add-to-cart, newsletter).
	$toast_file = $use_min && file_exists( $js_dir . '/toast.min.js' ) ? 'toast.min.js' : 'toast.js';
	if ( file_exists( $js_dir . '/' . $toast_file ) ) {
		wp_enqueue_script(
			'skyyrose-toast',
			$js_uri . '/' . $toast_file,
			array(),
			SKYYROSE_VERSION,
			array(
				'strategy'  => 'defer',
				'in_footer' => true,
			)
		);
	}

	// Footer CRO — FAQ accordion (extracted from inline <script> in v1.5.3).
	$fcro_file = $use_min && file_exists( $js_dir . '/footer-cro.min.js' ) ? 'footer-cro.min.js' : 'footer-cro.js';
	if ( file_exists( $js_dir . '/' . $fcro_file ) ) {
		wp_enqueue_script(
			'skyyrose-footer-cro',
			$js_uri . '/' . $fcro_file,
			array(),
			SKYYROSE_VERSION,
			array(
				'strategy'  => 'defer',
				'in_footer' => true,
			)
		);
	}

	// Motion One — vanilla JS animation library (same author as Framer Motion).
	// Self-hosted from assets/js/lib/ to eliminate jsDelivr CDN supply-chain risk.
	// Exposes window.Motion with animate(), scroll(), inView(), timeline().
	// Loaded with `defer` strategy: parsed in parallel with HTML, executed after
	// DOMContentLoaded. premium-interactions.js depends on it and self-defers.
	// v1.5.12: skip on lightweight slugs (cart/checkout/404/search) — saves ~65KB.
	if ( ! $skip_premium_js ) {
		wp_enqueue_script(
			'motion-one',
			SKYYROSE_ASSETS_URI . '/js/lib/motion.min.js',
			array(),
			'11',
			array(
				'strategy'  => 'defer',
				'in_footer' => true,
			)
		);

		// Premium interactions: parallax, split-text, magnetic, stagger, scroll-fade.
		$prem_js = $use_min && file_exists( $js_dir . '/premium-interactions.min.js' )
			? 'premium-interactions.min.js' : 'premium-interactions.js';
		if ( file_exists( $js_dir . '/' . $prem_js ) ) {
			wp_enqueue_script(
				'skyyrose-premium-interactions',
				$js_uri . '/' . $prem_js,
				array( 'motion-one' ),
				SKYYROSE_VERSION,
				array(
					'strategy'  => 'defer',
					'in_footer' => true,
				)
			);
		}
	}

	// Page transitions + skeleton screens + scarcity bars.
	$pt_file = $use_min && file_exists( $js_dir . '/page-transitions.min.js' )
		? 'page-transitions.min.js' : 'page-transitions.js';
	if ( file_exists( $js_dir . '/' . $pt_file ) ) {
		wp_enqueue_script(
			'skyyrose-page-transitions',
			$js_uri . '/' . $pt_file,
			array(),
			SKYYROSE_VERSION,
			array(
				'strategy'  => 'defer',
				'in_footer' => true,
			)
		);
	}

	// Comment reply script (WordPress built-in).
	if ( is_singular() && comments_open() && get_option( 'thread_comments' ) ) {
		wp_enqueue_script( 'comment-reply' );
	}

	// Skyy mascot JS disabled — character widget is not rendered until art is finalized.
	// Re-enable mascot.min.js and skyy-3d.js when get_template_part('skyy-mascot')
	// is restored in footer.php and front-page.php.
}

/**
 * Localize script data for AJAX URLs, nonces, and theme URIs.
 *
 * @since 3.0.0
 * @return void
 */
function skyyrose_localize_scripts() {

	// navigation.js is always enqueued (see skyyrose_scripts); fall back to
	// jquery only as a last resort to ensure skyyRoseData is always available.
	$handle = 'skyyrose-navigation';
	if ( ! wp_script_is( $handle, 'enqueued' ) ) {
		wp_enqueue_script( 'jquery' );
		$handle = 'jquery';
	}

	wp_localize_script(
		$handle,
		'skyyRoseData',
		array(
			'ajaxUrl'   => admin_url( 'admin-ajax.php' ),
			'nonce'     => wp_create_nonce( 'skyyrose-nonce' ),
			'themeUri'  => SKYYROSE_URI,
			'assetsUri' => SKYYROSE_ASSETS_URI,
		)
	);
}

/**
 * Determine the current page template slug.
 *
 * Returns a normalized identifier that can be used for conditional enqueue.
 * Checks page template files, WooCommerce conditionals, and front-page.
 *
 * @since  3.0.0
 * @return string Template identifier slug (e.g., 'front-page', 'collection', 'about').
 */
function skyyrose_get_current_template_slug() {
	static $slug = null;
	if ( null !== $slug ) {
		return $slug;
	}

	$page_template = get_page_template_slug();

	if ( is_front_page() ) {
		$slug = 'front-page';
	} elseif ( is_404() ) {
		$slug = '404';
	} elseif ( function_exists( 'is_product' ) && is_product() ) {
		$slug = 'single-product';
	} elseif ( function_exists( 'is_cart' ) && is_cart() ) {
		$slug = 'cart';
	} elseif ( function_exists( 'is_checkout' ) && is_checkout() ) {
		$slug = 'checkout';
	} elseif ( function_exists( 'is_shop' ) && ( is_shop() || is_product_category() || is_product_tag() ) ) {
		$slug = 'shop-archive';
	} elseif ( ! empty( $page_template ) ) {
		$template_map = array(
			'template-collection-black-rose.php'   => 'collection-standalone',
			'template-collection-love-hurts.php'   => 'collection-standalone',
			'template-collection-signature.php'    => 'collection-standalone',
			'template-collection-kids-capsule.php' => ( function_exists( 'skyyrose_kc_is_launch_mode' ) && skyyrose_kc_is_launch_mode() ) ? 'kc-launch' : 'collection-standalone',
			'template-immersive-black-rose.php'    => 'immersive',
			'template-immersive-love-hurts.php'    => 'immersive',
			'template-immersive-signature.php'     => 'immersive',
			'template-immersive-kids-capsule.php'  => 'immersive',
			'template-about.php'                   => 'about',
			'template-contact.php'                 => 'contact',
			'template-preorder-gateway.php'        => 'preorder-gateway',
			'template-faq.php'                     => 'faq',
			'template-shipping-returns.php'        => 'shipping-returns',
			'template-landing-black-rose.php'      => 'landing',
			'template-landing-love-hurts.php'      => 'landing',
			'template-landing-signature.php'       => 'landing',
			'template-landing-kids-capsule.php'    => 'landing',
			'template-elementor-editorial.php'     => 'elementor-editorial',
			'template-elementor-canvas.php'        => 'elementor-canvas',
			'template-elementor-fullwidth.php'     => 'elementor-fullwidth',
		);
		$slug         = isset( $template_map[ $page_template ] ) ? $template_map[ $page_template ] : null;
	}

	if ( null === $slug ) {
		if ( is_single() ) {
			$slug = 'single';
		} elseif ( is_search() ) {
			$slug = 'search';
		} elseif ( is_home() || is_archive() ) {
			$slug = 'blog';
		} elseif ( is_page() ) {
			$slug = 'page';
		} else {
			$slug = 'default';
		}
	}

	return $slug;
}

/**
 * Conditionally enqueue template-specific CSS.
 *
 * Only loads the stylesheet that matches the current page template.
 *
 * @since 3.0.0
 * @return void
 */
function skyyrose_enqueue_template_styles() {

	$slug         = skyyrose_get_current_template_slug();
	$base_css_uri = SKYYROSE_ASSETS_URI . '/css';
	$base_css_dir = SKYYROSE_DIR . '/assets/css';
	$global_deps  = array( 'skyyrose-design-tokens' );
	$use_min      = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;

	$template_styles = array(
		'front-page'          => 'homepage-v2.css',
		'immersive'           => 'immersive.css',
		'single-product'      => 'single-product.css',
		'cart'                => 'woocommerce.css',
		'checkout'            => 'woocommerce.css',
		'shop-archive'        => 'woocommerce.css',
		'about'               => 'about.css',
		'contact'             => 'contact.css',
		'preorder-gateway'    => 'preorder-gateway.css',
		'404'                 => '404.css',
		'search'              => 'search-results.css',
		'faq'                 => 'info-pages.css',
		'shipping-returns'    => 'info-pages.css',
		'landing'             => 'landing-scrollytell.css',
		'elementor-editorial' => 'landing-pages.css',
		'single'              => 'generic-pages.css',
		'blog'                => 'generic-pages.css',
		'page'                => 'generic-pages.css',
		'kc-launch'           => 'kids-capsule.css',
	);

	if ( isset( $template_styles[ $slug ] ) ) {
		$css_file = $template_styles[ $slug ];
		$handle   = 'skyyrose-template-' . sanitize_title( pathinfo( $css_file, PATHINFO_FILENAME ) );
		$min_file = str_replace( '.css', '.min.css', $css_file );

		// Prefer minified version in production.
		if ( $use_min && file_exists( $base_css_dir . '/' . $min_file ) ) {
			$css_file = $min_file;
		}

		if ( file_exists( $base_css_dir . '/' . $css_file ) ) {
			wp_enqueue_style(
				$handle,
				$base_css_uri . '/' . $css_file,
				$global_deps,
				SKYYROSE_VERSION
			);
		}
	}

	// Scroll-pinned brand-narrative styles — collection + landing templates.
	if ( in_array( $slug, array( 'collection-standalone', 'landing' ), true ) ) {
		$pin_css = $use_min && file_exists( $base_css_dir . '/pin-narrative.min.css' )
			? 'pin-narrative.min.css' : 'pin-narrative.css';
		if ( file_exists( $base_css_dir . '/' . $pin_css ) ) {
			wp_enqueue_style(
				'skyyrose-pin-narrative',
				$base_css_uri . '/' . $pin_css,
				array( 'skyyrose-design-tokens' ),
				SKYYROSE_VERSION
			);
		}
	}

	// Immersive scene images — overlays, tab bar, cinematic toggle, particles.
	if ( 'immersive' === $slug ) {
		$scenes_file = $use_min && file_exists( $base_css_dir . '/immersive-scenes.min.css' )
			? 'immersive-scenes.min.css' : 'immersive-scenes.css';
		if ( file_exists( $base_css_dir . '/' . $scenes_file ) ) {
			wp_enqueue_style(
				'skyyrose-immersive-scenes',
				$base_css_uri . '/' . $scenes_file,
				array( 'skyyrose-template-immersive' ),
				SKYYROSE_VERSION
			);
		}
	}

	// Homepage v7 "Concrete" theme — supplemental styles loaded after homepage-v2.
	if ( 'front-page' === $slug ) {
		$v7_css = $use_min && file_exists( $base_css_dir . '/homepage-v7.min.css' )
			? 'homepage-v7.min.css' : 'homepage-v7.css';
		if ( file_exists( $base_css_dir . '/' . $v7_css ) ) {
			wp_enqueue_style(
				'skyyrose-homepage-v7',
				$base_css_uri . '/' . $v7_css,
				array( 'skyyrose-template-homepage-v2' ),
				SKYYROSE_VERSION
			);
		}

		// LCP: preload hero image so the browser prioritises it in the
		// high-priority fetch queue alongside critical CSS, improving LCP score.
		//
		// v1.5.17: preload AVIF (broadest 2026 browser coverage, smaller payload).
		// v1.5.19: derive path + URL atomically via skyyrose_avif_sibling_pair()
		// so existence probe + emitted preload URL cannot drift apart.
		// Non-AVIF browsers fall through to WebP via the <picture> element's
		// normal source negotiation (not preloaded, but still high-priority).
		add_action(
			'wp_head',
			function () {
				$webp_url = SKYYROSE_ASSETS_URI . '/images/homepage-hero-bg.webp';
				$avif     = function_exists( 'skyyrose_avif_sibling_pair' ) ? skyyrose_avif_sibling_pair( $webp_url ) : null;
				if ( $avif && file_exists( $avif['path'] ) ) {
					echo '<link rel="preload" as="image" href="' . esc_url( $avif['url'] ) . '" type="image/avif" fetchpriority="high">' . "\n"; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
				} else {
					echo '<link rel="preload" as="image" href="' . esc_url( $webp_url ) . '" type="image/webp" fetchpriority="high">' . "\n"; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
				}
			},
			2
		);
	}

	// Unified collection page CSS + cross-collection View Transitions choreography.
	if ( 'collection-standalone' === $slug ) {
		skyyrose_enqueue_collection_styles( $base_css_dir, $base_css_uri, $use_min, $global_deps );
	}

	// Product grid bento layout — landing pages, preorder gateway, and
	// collection pages (their shared product-grid part renders
	// .product-grid__items, which lays out as full-width stacked blocks
	// without this stylesheet — bug-112).
	if ( in_array( $slug, array( 'landing', 'elementor-editorial', 'preorder-gateway', 'collection-standalone' ), true ) ) {
		$grid_css = $use_min && file_exists( $base_css_dir . '/product-grid.min.css' )
			? 'product-grid.min.css' : 'product-grid.css';
		if ( file_exists( $base_css_dir . '/' . $grid_css ) ) {
			wp_enqueue_style(
				'skyyrose-product-grid',
				$base_css_uri . '/' . $grid_css,
				array( 'skyyrose-design-tokens' ),
				SKYYROSE_VERSION
			);
		}
	}

	// WooCommerce page-specific CSS (loaded ON TOP of the base woocommerce.css).
	$woo_page_styles = array(
		// single-product.css is the primary stylesheet (replaces woocommerce-single.css).
		'cart'     => 'woocommerce-cart.css',
		'checkout' => 'woocommerce-checkout.css',
	);

	if ( isset( $woo_page_styles[ $slug ] ) ) {
		$woo_file   = $woo_page_styles[ $slug ];
		$woo_handle = 'skyyrose-' . sanitize_title( pathinfo( $woo_file, PATHINFO_FILENAME ) );
		$woo_min    = str_replace( '.css', '.min.css', $woo_file );

		// Prefer minified version in production.
		if ( $use_min && file_exists( $base_css_dir . '/' . $woo_min ) ) {
			$woo_file = $woo_min;
		}

		if ( file_exists( $base_css_dir . '/' . $woo_file ) ) {
			wp_enqueue_style(
				$woo_handle,
				$base_css_uri . '/' . $woo_file,
				array( 'skyyrose-template-woocommerce' ),
				SKYYROSE_VERSION
			);
		}
	}
}

/**
 * Conditionally enqueue template-specific JS.
 *
 * Only loads the script that matches the current page template.
 *
 * @since 3.0.0
 * @return void
 */
function skyyrose_enqueue_template_scripts() {

	$slug         = skyyrose_get_current_template_slug();
	$base_js_uri  = SKYYROSE_ASSETS_URI . '/js';
	$base_js_dir  = SKYYROSE_DIR . '/assets/js';
	$base_css_uri = SKYYROSE_ASSETS_URI . '/css';
	$base_css_dir = SKYYROSE_DIR . '/assets/css';
	$use_min      = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;

	// Luxury cursor — dot follower (desktop only, self-disables on touch/mobile).
	// CURS-03: Immersive templates intentionally hide cursor to keep focus on the 3D scene.
	// Skip enqueue entirely on immersive slugs so the JS isn't downloaded for hidden UI.
	if ( 'immersive' !== $slug ) {
		$cursor_file = $use_min && file_exists( $base_js_dir . '/luxury-cursor.min.js' ) ? 'luxury-cursor.min.js' : 'luxury-cursor.js';
		if ( file_exists( $base_js_dir . '/' . $cursor_file ) ) {
			wp_enqueue_script(
				'skyyrose-luxury-cursor',
				$base_js_uri . '/' . $cursor_file,
				array(),
				SKYYROSE_VERSION,
				true
			);
		}
	}

	// Landing pages JS — split scrollytell (IntersectionObserver scroll-sync, no GSAP).
	if ( 'landing' === $slug ) {
		$lp_js = $use_min && file_exists( $base_js_dir . '/landing-scrollytell.min.js' )
			? 'landing-scrollytell.min.js' : 'landing-scrollytell.js';
		if ( file_exists( $base_js_dir . '/' . $lp_js ) ) {
			wp_enqueue_script(
				'skyyrose-landing-scrollytell',
				$base_js_uri . '/' . $lp_js,
				array(),
				SKYYROSE_VERSION,
				true
			);
			wp_localize_script(
				'skyyrose-landing-scrollytell',
				'skyyRoseData',
				array(
					'ajaxUrl' => admin_url( 'admin-ajax.php' ),
					'nonce'   => wp_create_nonce( 'skyyrose_newsletter' ),
				)
			);
		}
	}

	// Elementor editorial templates keep the legacy landing-pages layout + JS.
	if ( 'elementor-editorial' === $slug ) {
		$lp_legacy_js = $use_min && file_exists( $base_js_dir . '/landing-pages.min.js' )
			? 'landing-pages.min.js' : 'landing-pages.js';
		if ( file_exists( $base_js_dir . '/' . $lp_legacy_js ) ) {
			wp_enqueue_script(
				'skyyrose-landing-pages',
				$base_js_uri . '/' . $lp_legacy_js,
				array(),
				SKYYROSE_VERSION,
				true
			);
		}
	}

	// Collection pages JS — IntersectionObserver scroll-reveal (no GSAP dependency).
	if ( 'collection-standalone' === $slug ) {
		$col_js = $use_min && file_exists( $base_js_dir . '/collection-pages.min.js' )
			? 'collection-pages.min.js' : 'collection-pages.js';
		if ( file_exists( $base_js_dir . '/' . $col_js ) ) {
			wp_enqueue_script(
				'skyyrose-collection-pages',
				$base_js_uri . '/' . $col_js,
				array(),
				SKYYROSE_VERSION,
				true
			);
			wp_localize_script(
				'skyyrose-collection-pages',
				'skyyRoseNewsletter',
				array(
					'ajaxUrl' => admin_url( 'admin-ajax.php' ),
					'nonce'   => wp_create_nonce( 'skyyrose_newsletter' ),
				)
			);
		}
	}

	// GSAP — self-hosted from assets/js/lib/ so animations don't depend on
	// Cloudflare CDN reachability. Loaded on pages that use scroll animations
	// (NOT collection pages — they use IntersectionObserver).
	// 'about' removed in 1.5.8: about.js uses prefers-reduced-motion query only,
	// no gsap/ScrollTrigger API calls (audit: grep returns 0 hits). Was shipping
	// 114KB of dead lib bytes to every About visitor.
	$gsap_slugs = array( 'preorder-gateway', 'immersive', 'kc-launch' );
	if ( in_array( $slug, $gsap_slugs, true ) ) {
		wp_enqueue_script( 'skyyrose-gsap', SKYYROSE_ASSETS_URI . '/js/lib/gsap.min.js', array(), '3.12.2', true );
	}

	// ScrollTrigger — only on slugs whose scripts call the ScrollTrigger API.
	// Immersive rooms animate via gsap.timeline/fromTo/set only (immersive-core.js
	// + immersive.js, 0 ScrollTrigger refs), so shipping ScrollTrigger there was
	// ~40KB of dead main-thread parse during the scene intro. preorder-gateway.js
	// (5 refs) and kids-capsule-launch.js (3 refs) genuinely use it.
	$gsap_st_slugs = array( 'preorder-gateway', 'kc-launch' );
	if ( in_array( $slug, $gsap_st_slugs, true ) ) {
		wp_enqueue_script( 'skyyrose-gsap-st', SKYYROSE_ASSETS_URI . '/js/lib/ScrollTrigger.min.js', array( 'skyyrose-gsap' ), '3.12.2', true );
	}

	// Phase 2 — Lenis smooth-scroll lib: preorder gateway only.
	// Immersive rooms are 100vh/overflow:hidden (nothing to scroll) — no dead bytes.
	// Enqueued before the immersive-core block so window.Lenis is defined when
	// initLenis() runs. cf. CURS-03 lesson: slug-gated to avoid waste on other templates.
	if ( 'preorder-gateway' === $slug && file_exists( $base_js_dir . '/lib/lenis.min.js' ) ) {
		wp_enqueue_script(
			'skyyrose-lenis',
			$base_js_uri . '/lib/lenis.min.js',
			array(),    // Lenis itself has no WP deps.
			'1.3.23',
			true
		);
	}

	// Phase 1+2 — Immersive Core: scene intro, lockup, dust canvas, Lenis init, warp.
	// Loaded on: immersive rooms (4×) + preorder gateway.
	if ( in_array( $slug, array( 'immersive', 'preorder-gateway' ), true ) ) {
		$ic_css = $use_min && file_exists( $base_css_dir . '/system/immersive-core.min.css' )
			? 'system/immersive-core.min.css' : 'system/immersive-core.css';
		if ( file_exists( $base_css_dir . '/' . $ic_css ) ) {
			wp_enqueue_style(
				'skyyrose-immersive-core',
				$base_css_uri . '/' . $ic_css,
				array( 'skyyrose-design-tokens' ),
				SKYYROSE_VERSION
			);
		}

		// On preorder, add lenis as a dep so WP prints it before immersive-core.
		// On immersive rooms lenis is not enqueued — omit it from deps there.
		$ic_js_deps = array( 'skyyrose-gsap' );
		if ( 'preorder-gateway' === $slug && wp_script_is( 'skyyrose-lenis', 'enqueued' ) ) {
			$ic_js_deps[] = 'skyyrose-lenis';
		}

		$ic_js = $use_min && file_exists( $base_js_dir . '/system/immersive-core.min.js' )
			? 'system/immersive-core.min.js' : 'system/immersive-core.js';
		if ( file_exists( $base_js_dir . '/' . $ic_js ) ) {
			wp_enqueue_script(
				'skyyrose-immersive-core',
				$base_js_uri . '/' . $ic_js,
				// GSAP core + optional lenis dep (preorder only).
				// immersive-core uses gsap.timeline/fromTo/set, not ScrollTrigger API.
				$ic_js_deps,
				SKYYROSE_VERSION,
				true
			);
		}
	}

	$template_scripts = array(
		'front-page'       => 'homepage-v2.js',
		'immersive'        => 'immersive.js',
		'single-product'   => 'single-product.js',
		'cart'             => 'woocommerce.js',
		'checkout'         => 'woocommerce.js',
		'contact'          => 'contact.js',
		'preorder-gateway' => 'preorder-gateway.js',
		'about'            => 'about.js',
		'kc-launch'        => 'kids-capsule-launch.js',
	);

	if ( isset( $template_scripts[ $slug ] ) ) {
		$js_file = $template_scripts[ $slug ];
		$handle  = 'skyyrose-template-' . sanitize_title( pathinfo( $js_file, PATHINFO_FILENAME ) );

		// WooCommerce + single-product JS depend on jQuery for cart/gallery interactions.
		$wc_js_files = array( 'woocommerce.js', 'single-product.js' );
		$js_deps     = in_array( $js_file, $wc_js_files, true ) ? array( 'jquery', 'wc-add-to-cart-variation' ) : array();

		// Prefer minified version in production.
		$min_file = str_replace( '.js', '.min.js', $js_file );
		if ( $use_min && file_exists( $base_js_dir . '/' . $min_file ) ) {
			$js_file = $min_file;
		}

		if ( file_exists( $base_js_dir . '/' . $js_file ) ) {
			wp_enqueue_script(
				$handle,
				$base_js_uri . '/' . $js_file,
				$js_deps,
				SKYYROSE_VERSION,
				true
			);
		}

		// Localize preorder gateway with WooCommerce cart sync data.
		if ( 'preorder-gateway' === $slug && wp_script_is( $handle, 'enqueued' ) ) {
			wp_localize_script(
				$handle,
				'skyyRoseGateway',
				array(
					'ajaxUrl'     => admin_url( 'admin-ajax.php' ),
					'nonce'       => wp_create_nonce( 'skyyrose-immersive-nonce' ),
					'wcActive'    => class_exists( 'WooCommerce' ),
					'checkoutUrl' => function_exists( 'wc_get_checkout_url' ) ? wc_get_checkout_url() : home_url( '/checkout/' ),
					'cartUrl'     => function_exists( 'wc_get_cart_url' ) ? wc_get_cart_url() : home_url( '/cart/' ),
					'i18n'        => array(
						'item'  => __( 'item', 'skyyrose' ),
						'items' => __( 'items', 'skyyrose' ),
					),
				)
			);
		}

		// "Complete the Look" cross-sell removed 2026-05-27 per founder canon.
		// Enqueue, template, function, and hook all retired in the same commit.

		// Localize immersive scenes + load the WC bridge that wires the
		// "Pre-Order Now" button to skyyrose_immersive_add_to_cart.
		if ( 'immersive' === $slug && wp_script_is( $handle, 'enqueued' ) ) {
			wp_localize_script(
				$handle,
				'skyyRoseImmersive',
				array(
					'ajaxUrl'  => admin_url( 'admin-ajax.php' ),
					'nonce'    => wp_create_nonce( 'skyyrose-immersive-nonce' ),
					'wcActive' => class_exists( 'WooCommerce' ),
					'cartUrl'  => function_exists( 'wc_get_cart_url' ) ? wc_get_cart_url() : home_url( '/cart/' ),
				)
			);

			$bridge_file = $use_min && file_exists( $base_js_dir . '/immersive-wc-bridge.min.js' )
				? 'immersive-wc-bridge.min.js'
				: 'immersive-wc-bridge.js';

			if ( file_exists( $base_js_dir . '/' . $bridge_file ) ) {
				wp_enqueue_script(
					'skyyrose-immersive-wc-bridge',
					$base_js_uri . '/' . $bridge_file,
					array( $handle ),
					SKYYROSE_VERSION,
					true
				);
			}
		}

		/* Immersive world + WC bridge — will be re-added when immersive rooms v6.0 ships */
	}

	// Holo product cards — loaded on collection pages, shop archives, and WC loop.
	// NOTE: This must be OUTSIDE the $template_scripts check above.
	if ( in_array( $slug, array( 'collection-standalone', 'front-page', 'shop-archive', 'preorder-gateway', 'search', 'landing', 'elementor-editorial', 'single-product' ), true ) ) {
			$holo_css_file = $use_min && file_exists( $base_css_dir . '/product-card-holo.min.css' )
				? 'product-card-holo.min.css' : 'product-card-holo.css';
		if ( file_exists( $base_css_dir . '/' . $holo_css_file ) ) {
			wp_enqueue_style(
				'skyyrose-product-card-holo',
				$base_css_uri . '/' . $holo_css_file,
				array( 'skyyrose-design-tokens' ),
				SKYYROSE_VERSION
			);
		}
			$holo_js_file = $use_min && file_exists( $base_js_dir . '/product-card-holo.min.js' )
				? 'product-card-holo.min.js' : 'product-card-holo.js';
		if ( file_exists( $base_js_dir . '/' . $holo_js_file ) ) {
			wp_enqueue_script(
				'skyyrose-product-card-holo',
				$base_js_uri . '/' . $holo_js_file,
				array(),
				SKYYROSE_VERSION,
				true
			);
		}
	}
}

/**
 * Enqueue admin styles and scripts.
 *
 * @since 1.0.0
 * @return void
 */
function skyyrose_admin_scripts() {
	$css_dir = SKYYROSE_DIR . '/assets/css';
	$css_uri = SKYYROSE_ASSETS_URI . '/css';
	$js_dir  = SKYYROSE_DIR . '/assets/js';
	$js_uri  = SKYYROSE_ASSETS_URI . '/js';
	$use_min = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;

	$admin_css_file = $use_min && file_exists( $css_dir . '/admin.min.css' )
		? 'admin.min.css' : 'admin.css';
	if ( file_exists( $css_dir . '/' . $admin_css_file ) ) {
		wp_enqueue_style(
			'skyyrose-admin',
			$css_uri . '/' . $admin_css_file,
			array(),
			SKYYROSE_VERSION
		);
	}

	$admin_js_file = $use_min && file_exists( $js_dir . '/admin.min.js' )
		? 'admin.min.js' : 'admin.js';
	if ( file_exists( $js_dir . '/' . $admin_js_file ) ) {
		wp_enqueue_script(
			'skyyrose-admin',
			$js_uri . '/' . $admin_js_file,
			array( 'jquery' ),
			SKYYROSE_VERSION,
			true
		);
	}
}

// Hook registration. Priority order: 5 fonts → 10 globals → 15 localize → 20 templates.
// Phase 2/3/4 + commercial polish (priorities 25/30/40/42) live in inc/enqueue-phases.php.
// Collection-experience scenes (priority 65) live in inc/enqueue-experiences.php.
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_local_fonts', 5 );
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_global_styles', 10 );
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_global_scripts', 10 );
add_action( 'wp_enqueue_scripts', 'skyyrose_localize_scripts', 15 );
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_template_styles', 20 );
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_template_scripts', 20 );
add_action( 'admin_enqueue_scripts', 'skyyrose_admin_scripts' );
