<?php
/**
 * Enqueue Performance Optimizations
 *
 * Separated from enqueue.php to keep each file under 800 lines.
 * Contains WooCommerce style dequeuing, font preloading, resource hints,
 * and script defer logic.
 *
 * @package SkyyRose
 * @since   4.1.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Dequeue WooCommerce default styles that conflict with theme design.
 *
 * WooCommerce loads 3 default stylesheets. We remove the general and
 * smallscreen styles to prevent layout conflicts with our design-token system,
 * but keep the layout stylesheet for grid compatibility.
 *
 * @since  3.0.0
 * @param  array $enqueue_styles WooCommerce styles to load.
 * @return array Filtered styles.
 */
function skyyrose_dequeue_woocommerce_styles( $enqueue_styles ) {

	// Remove the general WooCommerce stylesheet (buttons, forms, etc.).
	unset( $enqueue_styles['woocommerce-general'] );

	// Remove the small-screen / mobile stylesheet.
	unset( $enqueue_styles['woocommerce-smallscreen'] );

	// Keep woocommerce-layout for grid structure.
	return $enqueue_styles;
}

/**
 * Add font preload hints for critical above-fold fonts.
 *
 * Preloads latin subsets (used by all page content) for fastest
 * first-paint. Latin-ext subsets load on demand via unicode-range.
 *
 * @since  3.2.1
 * @return void
 */
function skyyrose_preload_fonts() {
	$fonts_dir = SKYYROSE_ASSETS_URI . '/fonts';
	$slug      = function_exists( 'skyyrose_get_current_template_slug' ) ? skyyrose_get_current_template_slug() : '';
	?>
	<link rel="preload" href="<?php echo esc_url( $fonts_dir . '/archivo-latin.woff2' ); ?>" as="font" type="font/woff2" crossorigin>
	<link rel="preload" href="<?php echo esc_url( $fonts_dir . '/hanken-grotesk-latin.woff2' ); ?>" as="font" type="font/woff2" crossorigin>
	<link rel="preload" href="<?php echo esc_url( $fonts_dir . '/anton-latin.woff2' ); ?>" as="font" type="font/woff2" crossorigin>
	<?php
	// Inter's only canonical use is 404.css (--ff-system). As of this deploy
	// train (2026-07-19) Pixel repoints the body-font stacks that previously
	// fell back to Inter sitewide (undefined --font-body var + cookie-consent
	// primary) at Hanken Grotesk, so a sitewide Inter preload would be a
	// wasted 48KB fetch — preload it only where it still renders.
	if ( '404' === $slug ) {
		?>
		<link rel="preload" href="<?php echo esc_url( $fonts_dir . '/inter-latin.woff2' ); ?>" as="font" type="font/woff2" crossorigin>
		<?php
	}
	// Cinzel is above-fold ONLY on Black Rose pages (collection + immersive
	// templates). Skip the preload elsewhere so non-BR pages don't waste
	// bandwidth on a font they never render.
	if ( in_array( $slug, array( 'collection', 'collection-standalone', 'immersive' ), true ) ) {
		$queried = get_queried_object();
		$is_br   = $queried && isset( $queried->post_name )
			&& false !== strpos( (string) $queried->post_name, 'black-rose' );
		if ( $is_br ) {
			?>
			<link rel="preload" href="<?php echo esc_url( $fonts_dir . '/cinzel-latin.woff2' ); ?>" as="font" type="font/woff2" crossorigin>
			<?php
		}
	}
}

/**
 * Resource hints for external services.
 *
 * All Google Fonts preconnects removed — fonts fully self-hosted since 4.1.0.
 * cdn.jsdelivr.net: skyy-3d.js imports three@0.170.0 from there, but only
 * during the mascot's idle-time load — a head preconnect's socket would be
 * closed long before that fetch, so warm the DNS only (dns-prefetch), and
 * only on pages where the 3D mascot can actually load (Wave 2, 2026-07-19).
 *
 * @since  3.2.1
 * @param  array  $urls          URLs to print for resource hint.
 * @param  string $relation_type The resource hint relation (dns-prefetch, preconnect, etc.).
 * @return array Modified URLs.
 */
function skyyrose_resource_hints( $urls, $relation_type ) {
	if ( 'dns-prefetch' === $relation_type
		&& function_exists( 'skyyrose_mascot_is_enabled' ) && skyyrose_mascot_is_enabled()
		&& function_exists( 'skyyrose_get_skyy_glb_url' ) && skyyrose_get_skyy_glb_url()
		&& ! ( function_exists( 'is_checkout' ) && is_checkout() ) ) {
		$urls[] = '//cdn.jsdelivr.net';
	}
	return $urls;
}

/**
 * Defer non-critical scripts for better page load performance.
 *
 * Uses a prefix-based approach instead of a hardcoded list, so newly
 * added scripts with the skyyrose- prefix automatically get deferred.
 *
 * @since  3.0.0
 * @since  4.1.0 Switched from hardcoded list to prefix matching.
 * @param  string $tag    Full script tag HTML.
 * @param  string $handle Script handle.
 * @return string Modified tag.
 */
function skyyrose_defer_scripts( $tag, $handle ) {

	// All theme scripts should be deferred except critical inline.
	// Skip scripts that already have defer or async attributes.
	if ( strpos( $tag, ' defer' ) !== false || strpos( $tag, ' async' ) !== false ) {
		return $tag;
	}

	// Defer all skyyrose-prefixed scripts and WC variation scripts loaded in footer.
	$should_defer = (
		0 === strpos( $handle, 'skyyrose-' ) ||
		'wc-add-to-cart-variation' === $handle
	);

	// Never defer jQuery or WordPress core scripts that other scripts depend on synchronously.
	$never_defer = array( 'jquery', 'jquery-core', 'jquery-migrate', 'wp-polyfill' );
	if ( in_array( $handle, $never_defer, true ) ) {
		$should_defer = false;
	}

	if ( $should_defer ) {
		return preg_replace( '/(<script\b[^>]*)\ssrc=/i', '$1 defer src=', $tag, 1 );
	}

	return $tag;
}

/**
 * Load non-critical stylesheets asynchronously (print-media swap).
 *
 * Handles listed here style ONLY JS-created or navigation-time UI — verified
 * per-sheet 2026-07-19 (fix-log Wave 2): no server-rendered above-fold markup
 * depends on them on any template they load on. media='print' downloads the
 * sheet without blocking render; onload flips it live; <noscript> keeps
 * no-JS visitors styled.
 *
 * Deliberately NOT deferred (fail-closed — server-rendered markup would paint
 * unstyled without them): mascot/skyy-walk (doc-end DOM,
 * in-viewport on short pages like cart), skeleton (landing templates render
 * .skeleton--* markup server-side), footer/footer-cro (in-viewport on short
 * pages — the Wave 1 CLS fix), all reveal/animation sheets (initial states
 * must exist at first paint), fonts.css (pairs with the font preloads).
 *
 * @since 1.11.2
 * @param  string $html   Full <link> tag HTML.
 * @param  string $handle Style handle.
 * @return string Possibly-swapped tag.
 */
function skyyrose_async_noncritical_styles( $html, $handle ) {
	$async_handles = array(
		'skyyrose-size-guide',       // Modal at doc end, opened via JS trigger only.
		'skyyrose-luxury-cursor',    // Cursor elements created by JS.
		'skyyrose-smart-showcase',   // Quick-view dialog built by JS.
		'skyyrose-personalization',  // JS-driven personalization UI.
		'skyyrose-view-transitions', // view-transition-name + ::view-transition only, nav-time.
		'skyyrose-brand-atmosphere', // JS-created canvas overlay.
		'skyyrose-cookie-consent',   // Deferrable ONLY because the part renders with the
									// [hidden] attribute AND cookie-consent.css restores
									// .cookie-consent[hidden]{display:none} (author flex
									// beats UA [hidden]) — both landed 2026-07-19. Do not
									// defer without that contract.
	);

	// Per-template: skeleton shimmer markup is server-rendered ONLY by the
	// landing templates (grep: template-landing-black-rose/-signature) —
	// everywhere else .skeleton classes are JS-applied, so the sheet is safe
	// async (round-3: it blocked paint on collection pages).
	if ( function_exists( 'skyyrose_get_current_template_slug' )
		&& 'landing' !== skyyrose_get_current_template_slug() ) {
		$async_handles[] = 'skyyrose-skeleton';
	}

	if ( ! in_array( $handle, $async_handles, true ) ) {
		return $html;
	}

	$swapped = str_replace( "media='all'", "media='print' onload=\"this.media='all'\"", $html );
	if ( $swapped === $html ) {
		// Unexpected tag shape — fail closed, keep render-blocking.
		return $html;
	}

	return $swapped . '<noscript>' . $html . '</noscript>';
}

/**
 * Add fetchpriority="high" to critical above-fold stylesheets.
 *
 * Tells the browser to prioritize design tokens and main styles that
 * affect First Contentful Paint (FCP) and Largest Contentful Paint (LCP).
 *
 * @since  4.1.0
 * @param  string $html   Link tag HTML.
 * @param  string $handle Style handle.
 * @return string Modified tag.
 */
function skyyrose_critical_style_priority( $html, $handle ) {
	$critical_handles = array(
		'skyyrose-design-tokens',
		'skyyrose-main',
		'skyyrose-fonts',
		'skyyrose-style',
		'skyyrose-brand-variables',
	);

	if ( in_array( $handle, $critical_handles, true ) ) {
		// Add media="all" fetchpriority hint via data attribute for resource prioritization.
		$html = str_replace( "media='all'", "media='all' fetchpriority='high'", $html );
	}

	return $html;
}

/**
 * Preload the hero/LCP image for the current template.
 *
 * Front page: preloads the hero background from Customizer.
 * Single product: preloads the main product image (above-fold gallery).
 * Collection/immersive: preloads the featured image (hero banner).
 *
 * @since 4.1.0
 * @since 6.4.0 Extended to single product, collection, and immersive pages.
 * @return void
 */
function skyyrose_preload_hero_image() {
	$image_url = '';

	if ( is_front_page() ) {
		$image_url = get_theme_mod( 'skyyrose_hero_image', '' );
	} elseif ( function_exists( 'is_product' ) && is_product() ) {
		// $GLOBALS['product'] can hold non-WC_Product values when third-party
		// callbacks fire before wp_head priority 4 — only adopt a fresh
		// resolution when the helper returns a valid WC_Product so we never
		// write null/false back to the global.
		global $product;
		if ( ! $product instanceof WC_Product ) {
			$resolved = skyyrose_current_wc_product();
			if ( $resolved instanceof WC_Product ) {
				$product = $resolved;
			}
		}

		// Round-4: on the editorial PDP layout the LCP is the encounter image
		// (product-detail-editorial.php $hero_image — a theme-asset catalog
		// image), NOT the WC gallery attachment — and the old gallery preload
		// was ALSO Photon-skipped, leaving the PDP with no LCP preload at all
		// (load delay 1,106ms). Mirror single-product.php's own gates exactly:
		// same skyyrose_get_product( $sku ) entry, same dossier editorial gate.
		$pdp_sku      = ( $product instanceof WC_Product ) ? $product->get_sku() : '';
		$pdp_entry    = ( '' !== $pdp_sku && function_exists( 'skyyrose_get_product' ) ) ? skyyrose_get_product( $pdp_sku ) : null;
		$pdp_dossier  = ( '' !== $pdp_sku && function_exists( 'skyyrose_get_product_dossier' ) ) ? skyyrose_get_product_dossier( $pdp_sku ) : null;
		$is_editorial = $pdp_dossier && ! empty( $pdp_dossier['has_editorial_content'] );

		if ( $is_editorial && ! empty( $pdp_entry['image'] ) && function_exists( 'skyyrose_product_image_uri' ) ) {
			$image_url = skyyrose_product_image_uri( $pdp_entry['image'] );
		} elseif ( ! function_exists( 'jetpack_photon_url' ) ) {
			// Non-editorial PDPs keep the gallery-image preload. Jetpack
			// Photon rewrites gallery URLs to its CDN on delivery — preloading
			// the local URL wastes a connection, so skip under Photon and let
			// the browser's own LCP heuristic take over.
			if ( $product instanceof WC_Product && $product->get_image_id() ) {
				// Use WC's "woocommerce_single" sized variant (~300-600KB) instead
				// of wp_get_attachment_url() which returns the raw original
				// (often 2-3MB). Cuts PDP preload payload ~80%. (audit 2026-05-23)
				$image_url = wp_get_attachment_image_url( $product->get_image_id(), 'woocommerce_single' );
				if ( ! $image_url ) {
					$image_url = wp_get_attachment_url( $product->get_image_id() );
				}
			}
		}
	} elseif ( is_page() ) {
		$template = get_page_template_slug();
		if ( 'template-about.php' === $template ) {
			// Round-4: the about LCP is the hardcoded origin portrait
			// (template-about.php $hero_img), NOT the featured image the
			// generic branch below preloaded — that was a wasted fetch while
			// the real LCP waited (load delay 1,142ms). Same file, same URL.
			$image_url = get_theme_file_uri( 'assets/images/homepage-story-founder.webp' );
		} else {
			// Immersive pages: preload featured image if set. 'large' (max
			// 1024px) instead of 'full' — full is typically 2-4MB and far
			// exceeds what any viewport needs for a hero preload. Collection
			// templates removed (Wave 5): skyyrose_preload_template_lcp()
			// now preloads their measured LCP (.col-hero__bg srcset) exactly;
			// a second featured-image preload here would be a wasted fetch.
			$hero_templates = array(
				'template-immersive-black-rose.php',
				'template-immersive-love-hurts.php',
				'template-immersive-signature.php',
				'template-immersive-kids-capsule.php',
			);
			if ( $template && in_array( $template, $hero_templates, true ) && has_post_thumbnail() ) {
				$image_url = get_the_post_thumbnail_url( get_the_ID(), 'large' );
			}
		}
	}

	if ( $image_url ) {
		printf(
			'<link rel="preload" href="%s" as="image" fetchpriority="high">' . "\n",
			esc_url( $image_url )
		);
	}
}

/**
 * Preload the measured LCP image on templates whose LCP element the preload
 * scanner discovers late.
 *
 * Round-4 mobile load-delay evidence (audit: largest-contentful-paint-element):
 * collection heroes 854-2,845ms, landing-BR atmosphere 2,381ms, preorder
 * poster 1,642ms, collections-index lockup 1,439ms. Each branch below targets
 * ONLY the element the round-4 JSON names for that template.
 *
 * PAIRING CONTRACT: every branch reproduces its template's emitted URLs
 * exactly (same helpers, same widths, same sizes strings) — a mismatched
 * preload double-fetches the LCP.
 *
 * @since 1.12.3
 * @return void
 */
function skyyrose_preload_template_lcp() {
	$slug = function_exists( 'skyyrose_get_current_template_slug' )
		? skyyrose_get_current_template_slug() : '';

	// Collection pages: .col-hero__bg img (template-parts/collection/page.php).
	// Reproduces its srcset (hero_bg_base + 480/768/1280/1680w webp, sizes
	// 100vw) or, without a base, its exact versioned src.
	if ( 'collection-standalone' === $slug ) {
		$col_key = str_replace( array( 'template-collection-', '.php' ), '', (string) get_page_template_slug() );
		// Same accessor the template part uses (collection/page.php:19) —
		// hero_bg_base/hero_bg live in inc/collection-content.php, NOT the
		// collections-config array.
		$c = function_exists( 'skyyrose_get_collection_content' ) ? skyyrose_get_collection_content( $col_key ) : null;
		if ( is_array( $c ) ) {
			$sot_bg      = function_exists( 'skyyrose_sot_hero' ) ? skyyrose_sot_hero( $col_key ) : '';
			$resolved_bg = ( '' !== $sot_bg ) ? $sot_bg : ( $c['hero_bg'] ?? '' );
			$bg_base     = isset( $c['hero_bg_base'] ) ? (string) $c['hero_bg_base'] : '';
			if ( '' !== $bg_base ) {
				$entries = array();
				foreach ( array( 480, 768, 1280, 1680 ) as $w ) {
					$entries[] = esc_url( SKYYROSE_ASSETS_URI . $bg_base . '-' . $w . 'w.webp' ) . ' ' . $w . 'w';
				}
				echo '<link rel="preload" as="image" imagesrcset="' . esc_attr( implode( ', ', $entries ) ) . '" imagesizes="100vw" fetchpriority="high">' . "\n"; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
			} elseif ( ! empty( $resolved_bg ) ) {
				echo '<link rel="preload" as="image" href="' . esc_url( SKYYROSE_ASSETS_URI . $resolved_bg . '?v=' . SKYYROSE_VERSION ) . '" fetchpriority="high">' . "\n"; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
			}
		}
		return;
	}

	// Black Rose landing: .lp-hero__atmosphere img (the measured LCP; the img
	// carries fetchpriority=high in template-landing-black-rose.php).
	if ( 'landing' === $slug && 'template-landing-black-rose.php' === get_page_template_slug() ) {
		echo '<link rel="preload" as="image" href="' . esc_url( trailingslashit( SKYYROSE_ASSETS_URI ) . 'images/logos/black-roses-cloud-cluster.webp' ) . '" fetchpriority="high">' . "\n"; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
		return;
	}

	// Preorder gateway: the LCP element is the hero <video> — its painted
	// image is the poster (template-preorder-gateway.php, versioned URL).
	if ( 'preorder-gateway' === $slug ) {
		echo '<link rel="preload" as="image" href="' . esc_url( SKYYROSE_ASSETS_URI . '/branding/hero/luxury-nighttime-1680w.jpg?v=' . SKYYROSE_VERSION ) . '" fetchpriority="high">' . "\n"; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
		return;
	}

	// Collections index: the first card's lockup (page-collections.php —
	// config order puts black-rose first; same Photon widths + sizes).
	if ( 'collections-index' === $slug && function_exists( 'skyyrose_photon_srcset' ) ) {
		$ci_srcset = skyyrose_photon_srcset(
			SKYYROSE_ASSETS_URI . '/images/hero-overlays/br-brand-script-logotype.webp',
			array( 320, 640, 960 )
		);
		if ( '' !== $ci_srcset ) {
			echo '<link rel="preload" as="image" imagesrcset="' . esc_attr( $ci_srcset ) . '" imagesizes="(max-width: 430px) 70vw, 300px" fetchpriority="high">' . "\n"; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
		}
	}
}

/**
 * Remove jQuery Migrate on the frontend.
 *
 * Removes the jQuery Migrate compatibility shim for deprecated jQuery APIs.
 * Modern WooCommerce (9.0+) and WordPress (6.0+) do not require it.
 * Removing it saves ~12 KB and one blocking request.
 *
 * @since 6.6.0
 * @param \WP_Scripts $scripts Registered scripts.
 * @return void
 */
function skyyrose_remove_jquery_migrate( $scripts ) {
	if ( is_admin() ) {
		return;
	}
	if ( isset( $scripts->registered['jquery'] ) ) {
		$scripts->registered['jquery']->deps = array_diff(
			$scripts->registered['jquery']->deps,
			array( 'jquery-migrate' )
		);
	}
}

/**
 * Whether the current template is a theme-owned surface that never renders
 * post content.
 *
 * Verified by grep (2026-07-19): only page.php, single.php, search.php and
 * the template-elementor-*.php shells call the_content() — every other
 * template hardcodes its markup. On those templates, block markup stored in
 * the page's (unrendered) content must not force block/plugin stylesheets
 * onto the page, and content-driven features (Jetpack sharing) can never
 * appear.
 *
 * @since 1.11.2
 * @return bool True when the current template never calls the_content().
 */
function skyyrose_template_never_renders_content() {
	$slug = function_exists( 'skyyrose_get_current_template_slug' )
		? skyyrose_get_current_template_slug() : '';

	$never_renders = array(
		'front-page',
		'collection-standalone',
		'collections-index',
		'kc-launch',
		'landing',
		'immersive',
		'preorder-gateway',
		'experiences',
		'about',
		'contact',
		'faq',
		'shipping-returns',
		'size-guide',
		'404',
	);

	return in_array( $slug, $never_renders, true );
}

/**
 * Dequeue Gutenberg block library styles on pages that don't use blocks.
 *
 * The wp-block-library stylesheet (~40 KB) is loaded globally. On pages
 * that don't contain blocks (product pages, collection templates, etc.)
 * this is wasted bandwidth.
 *
 * @since 6.6.0
 * @since 1.11.2 has_blocks() bypass for templates that never render content —
 *               the front page's stored block markup kept wc-blocks.css +
 *               global-styles on a page that never calls the_content().
 * @return void
 */
function skyyrose_dequeue_block_styles() {
	if ( is_admin() ) {
		return;
	}

	// Cart/checkout render WC shortcode markup, not blocks — round-3 measured
	// block-library 99.3% unused on /cart/ (19,213 of 19,352 bytes) while
	// has_blocks() on the stored page content kept it enqueued. Dequeue just
	// the block-library pair; wc-blocks-style + global-styles stay (WC-adjacent,
	// not flagged unused).
	$bl_slug = function_exists( 'skyyrose_get_current_template_slug' )
		? skyyrose_get_current_template_slug() : '';
	if ( in_array( $bl_slug, array( 'cart', 'checkout' ), true ) ) {
		wp_dequeue_style( 'wp-block-library' );
		wp_dequeue_style( 'wp-block-library-theme' );
		return;
	}

	// Keep block styles on pages that actually use blocks. Templates that
	// never call the_content() can't render blocks regardless of what the
	// stored page content contains, so they skip this check.
	if ( ! skyyrose_template_never_renders_content()
		&& function_exists( 'has_blocks' ) && has_blocks() ) {
		return;
	}

	wp_dequeue_style( 'wp-block-library' );
	wp_dequeue_style( 'wp-block-library-theme' );
	wp_dequeue_style( 'wc-blocks-style' );
	wp_dequeue_style( 'global-styles' );
}

/**
 * Dequeue Jetpack and MediaElement styles not needed on most pages.
 *
 * Jetpack registers several feature-specific stylesheets globally even when
 * the corresponding feature is not used on the current page. This function
 * removes those whose context is clear:
 *
 * - Search chunk styles  → only needed on search results pages.
 * - Podcast player       → theme has no podcast pages; safe to remove globally.
 * - Grunion/forms CSS    → theme routes contact via Elementor, not Jetpack Forms.
 * - MediaElement.js      → only needed for native audio/video blocks; theme
 *                          uses YouTube embeds and Three.js, no <audio>/<video>.
 *
 * All wp_dequeue_style() / wp_dequeue_script() calls are no-ops when the
 * handle is not registered, so this is safe to run on all themes.
 *
 * @since 7.1.0
 * @return void
 */
function skyyrose_dequeue_jetpack_non_context_styles() {
	if ( is_admin() ) {
		return;
	}

	// Search chunk styles — only meaningful on search results pages.
	// results-list + filter-wc-attribute are the handles actually observed on
	// the live homepage (2026-07-19); the first three never matched anything.
	if ( ! is_search() ) {
		wp_dequeue_style( 'jetpack-search-widget' );
		wp_dequeue_style( 'jetpack-instant-search' );
		wp_dequeue_style( 'jetpack-search-chunk' );
		wp_dequeue_style( 'jetpack-search-results-list-style' );
		wp_dequeue_style( 'jetpack-search-filter-wc-attribute-style' );
	}

	// Podcast player — theme has no podcast pages; safe to remove globally.
	wp_dequeue_style( 'jetpack-podcast-player' );

	// Podcast episode block style (live handle, enqueued sitewide by wpcomsh).
	// Fail-closed: kept on any page that actually embeds a podcast block.
	if ( ! has_block( 'jetpack/podcast-player' ) && ! has_block( 'jetpack/podcast-episode' ) ) {
		wp_dequeue_style( 'jetpack-block-podcast-episode' );
	}

	// Jetpack / Grunion contact forms — theme uses Elementor for contact pages.
	wp_dequeue_style( 'grunion-front-end' );
	wp_dequeue_style( 'jetpack-forms' );

	// Forms layout css (live handle). Fail-closed: kept where a Jetpack
	// contact-form block is actually present in the page content.
	if ( ! has_block( 'jetpack/contact-form' ) ) {
		wp_dequeue_style( 'jetpack-forms-layout' );
	}

	// MediaElement.js — only required for native audio/video blocks.
	// Theme uses YouTube embeds and custom Three.js scenes; no native players.
	if ( function_exists( 'has_blocks' ) && ! has_blocks() ) {
		wp_dequeue_style( 'wp-mediaelement' );
		wp_dequeue_script( 'wp-mediaelement' );
		wp_dequeue_script( 'mediaelement' );
	}
}

/**
 * Dequeue platform/plugin stylesheets that load sitewide but are only
 * consumed on specific surfaces.
 *
 * Handle list verified against the live homepage (cache-busted curl,
 * 2026-07-19 — 15 plugin sheets loaded, most unused). Every dequeue is
 * conditional on the surface that actually consumes the stylesheet, so a
 * page that renders the feature keeps its styles (fail-closed).
 *
 * Registered on wp_enqueue_scripts AND wp_footer priority 1: several of
 * these handles (sharing, wc-blocks, Stripe) are enqueued mid-render and
 * print in the footer, where a head-time dequeue never sees them.
 *
 * @since 1.11.2
 * @return void
 */
function skyyrose_dequeue_platform_styles() {
	if ( is_admin() ) {
		return;
	}

	// wp.com masterbar bridge CSS — toolbar chrome for logged-in wp.com users.
	if ( ! is_user_logged_in() ) {
		wp_dequeue_style( 'wp-calypso-bridge-masterbar' );
	}

	// Per-block styles wpcomsh enqueues globally; keep only where the block renders.
	if ( ! has_block( 'core/code' ) ) {
		wp_dequeue_style( 'wp-block-code' );
	}
	if ( ! has_block( 'jetpack/layout-grid' ) ) {
		wp_dequeue_style( 'jetpack-layout-grid' );
	}

	// Stripe blocks-checkout styles — only cart/checkout surfaces use them.
	$is_wc_money_page = ( function_exists( 'is_cart' ) && is_cart() )
		|| ( function_exists( 'is_checkout' ) && is_checkout() );
	if ( ! $is_wc_money_page ) {
		wp_dequeue_style( 'wc-stripe-blocks-checkout-style' );
	}

	// Jetpack sharing buttons render via the_content() / WC product hooks —
	// templates that never render post content can never show them.
	if ( skyyrose_template_never_renders_content() ) {
		wp_dequeue_style( 'sharedaddy' );
		wp_dequeue_style( 'social-logos' );
	}

	// Elementor frontend + kit/post CSS — only needed when Elementor built
	// the current page. skyyrose_builder_owns_template() asks Elementor's own
	// document registry, so genuine Elementor pages keep their styles.
	if ( function_exists( 'skyyrose_builder_owns_template' ) && ! skyyrose_builder_owns_template() ) {
		wp_dequeue_style( 'elementor-frontend' );
		global $wp_styles;
		if ( $wp_styles instanceof WP_Styles ) {
			$queued = (array) $wp_styles->queue;
			foreach ( $queued as $queued_handle ) {
				if ( 0 === strpos( $queued_handle, 'elementor-post-' ) ) {
					wp_dequeue_style( $queued_handle );
				}
			}
		}
	}
}

/*
--------------------------------------------------------------
 * Hook Registration — Performance Optimizations
 *--------------------------------------------------------------*/

// Resource hints for external services (model-viewer CDN, etc.).
add_filter( 'wp_resource_hints', 'skyyrose_resource_hints', 10, 2 );

// Preload critical font files in <head>.
add_action( 'wp_head', 'skyyrose_preload_fonts', 3 );

// Dequeue conflicting WooCommerce default styles.
add_filter( 'woocommerce_enqueue_styles', 'skyyrose_dequeue_woocommerce_styles' );

// Defer non-critical scripts.
add_filter( 'script_loader_tag', 'skyyrose_defer_scripts', 10, 2 );

// Async-load stylesheets that only style JS-created / navigation-time UI.
// Priority 20: runs after skyyrose_critical_style_priority (10) — disjoint
// handle lists, but ordering keeps the critical-path filter's output stable.
add_filter( 'style_loader_tag', 'skyyrose_async_noncritical_styles', 20, 2 );

// Prioritize critical stylesheets for faster FCP/LCP.
add_filter( 'style_loader_tag', 'skyyrose_critical_style_priority', 10, 2 );

// Preload hero image on front page for better LCP.
add_action( 'wp_head', 'skyyrose_preload_hero_image', 4 );

// Preload the measured LCP image on collection/landing/preorder/collections-index (Wave 5).
add_action( 'wp_head', 'skyyrose_preload_template_lcp', 4 );

// Remove jQuery Migrate on frontend (not needed since WC 9.0+ / WP 6.0+).
add_action( 'wp_default_scripts', 'skyyrose_remove_jquery_migrate' );

// Dequeue Gutenberg block styles on non-block pages.
add_action( 'wp_enqueue_scripts', 'skyyrose_dequeue_block_styles', 100 );

// Dequeue Jetpack feature styles not needed outside their context (search, podcast, forms, MediaElement).
add_action( 'wp_enqueue_scripts', 'skyyrose_dequeue_jetpack_non_context_styles', 101 );

// Dequeue surface-specific platform styles (masterbar, Elementor, Stripe, sharing, per-block).
add_action( 'wp_enqueue_scripts', 'skyyrose_dequeue_platform_styles', 102 );

// Footer pass: wc-blocks, sharing, and Stripe styles are enqueued mid-render
// and print in the footer — re-run the dequeues before footer printing. All
// wp_dequeue_style() calls are no-ops when already dequeued, so the double
// registration is safe.
add_action( 'wp_footer', 'skyyrose_dequeue_block_styles', 1 );
add_action( 'wp_footer', 'skyyrose_dequeue_jetpack_non_context_styles', 1 );
add_action( 'wp_footer', 'skyyrose_dequeue_platform_styles', 1 );

// Print-time pass (Wave 4): Jetpack sharedaddy enqueues its styles from
// wp_head — AFTER wp_enqueue_scripts — so social-logos survived the wave-1
// gates in the homepage <head> (round-3: blocking on 9 pages). wp_print_styles
// fires inside wp_head immediately before head styles print, catching those
// late head enqueues. Idempotent like the passes above.
add_action( 'wp_print_styles', 'skyyrose_dequeue_block_styles', 0 );
add_action( 'wp_print_styles', 'skyyrose_dequeue_jetpack_non_context_styles', 0 );
add_action( 'wp_print_styles', 'skyyrose_dequeue_platform_styles', 0 );

/**
 * Move jQuery to the footer on content-only templates.
 *
 * Round-3: jquery.min.js was the #1 render-blocker (head-printed on 15 pages,
 * up to 353ms) yet on content templates its only dependents are WooCommerce's
 * sitewide frontend stack (add-to-cart, order-attribution, sourcebuster) —
 * all footer-printed. Verified 2026-07-20: rendered HTML of privacy/about/
 * faq/contact/shipping-returns contains ZERO inline jQuery( usage, so nothing
 * needs jQuery before the footer there. Fail-closed twice over: commerce
 * surfaces (front-page, collections, PDP, cart/checkout, wishlist) and
 * logged-in views are excluded here, and WordPress core ignores the group
 * move whenever any head-printed script still depends on jQuery.
 *
 * @since 1.11.2
 * @return void
 */
function skyyrose_footer_jquery_on_content_pages() {
	if ( is_admin() || is_user_logged_in() ) {
		return;
	}

	$slug  = function_exists( 'skyyrose_get_current_template_slug' )
		? skyyrose_get_current_template_slug() : '';
	$slugs = array( 'about', 'contact', 'faq', 'shipping-returns', 'blog', 'single', 'search', 'page' );
	if ( ! in_array( $slug, $slugs, true ) ) {
		return;
	}

	// Wishlist resolves to the generic 'page' slug but renders add-to-cart UI.
	if ( 'page' === $slug && is_page( 'wishlist' ) ) {
		return;
	}

	$scripts = wp_scripts();
	foreach ( array( 'jquery', 'jquery-core', 'jquery-migrate' ) as $jq_handle ) {
		$scripts->add_data( $jq_handle, 'group', 1 );
	}
}
add_action( 'wp_enqueue_scripts', 'skyyrose_footer_jquery_on_content_pages', 99 );
