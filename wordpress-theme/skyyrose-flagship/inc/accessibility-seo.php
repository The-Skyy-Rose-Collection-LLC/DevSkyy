<?php
/**
 * Accessibility Features (WCAG 2.1 AA Compliance)
 *
 * Implements WCAG 2.1 AA compliance for the SkyyRose Flagship Theme:
 * ARIA labels, live regions, image alt enforcement, landmark roles,
 * WooCommerce accessibility enhancements, and admin testing tools.
 *
 * SEO features extracted to inc/seo.php in iteration 28 to keep files under 800 lines.
 *
 * @package SkyyRose_Flagship
 * @since   1.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * ============================================================================
 * WCAG 2.1 AA COMPLIANCE FEATURES
 * ============================================================================
 */

/**
 * Enqueue accessibility CSS file.
 *
 * @since 1.0.0
 */
function skyyrose_accessibility_styles() {
	$css_path = get_template_directory() . '/assets/css/accessibility.css';
	if ( ! file_exists( $css_path ) ) {
		return;
	}

	wp_enqueue_style(
		'skyyrose-accessibility',
		SKYYROSE_ASSETS_URI . '/css/accessibility.css',
		array( 'skyyrose-style' ),
		SKYYROSE_VERSION
	);
}
add_action( 'wp_enqueue_scripts', 'skyyrose_accessibility_styles' );

/**
 * Add ARIA labels to navigation menus.
 *
 * @since 1.0.0
 *
 * @param array $args Navigation menu arguments.
 * @return array Modified arguments.
 */
function skyyrose_nav_menu_aria_labels( $args ) {
	if ( 'primary' === $args['theme_location'] ) {
		$args['container_aria_label'] = __( 'Primary Navigation', 'skyyrose-flagship' );
	} elseif ( 'footer' === $args['theme_location'] ) {
		$args['container_aria_label'] = __( 'Footer Navigation', 'skyyrose-flagship' );
	} elseif ( 'mobile' === $args['theme_location'] ) {
		$args['container_aria_label'] = __( 'Mobile Navigation', 'skyyrose-flagship' );
	}

	return $args;
}
add_filter( 'wp_nav_menu_args', 'skyyrose_nav_menu_aria_labels' );

/**
 * Enqueue accessibility JavaScript file.
 *
 * @since 1.0.0
 */
function skyyrose_accessibility_scripts() {
	$a11y_js_path = SKYYROSE_DIR . '/assets/js/accessibility.js';
	if ( file_exists( $a11y_js_path ) ) {
		wp_enqueue_script(
			'skyyrose-accessibility',
			SKYYROSE_ASSETS_URI . '/js/accessibility.js',
			array(),
			SKYYROSE_VERSION,
			true
		);
	}
}
add_action( 'wp_enqueue_scripts', 'skyyrose_accessibility_scripts' );

/**
 * Add ARIA live regions to the page.
 *
 * @since 1.0.0
 */
function skyyrose_aria_live_regions() {
	echo '<div id="skyyrose-announcer-polite" class="aria-live-region" aria-live="polite" aria-atomic="true"></div>';
	echo '<div id="skyyrose-announcer-assertive" class="aria-live-region" aria-live="assertive" aria-atomic="true"></div>';
}
add_action( 'wp_footer', 'skyyrose_aria_live_regions' );

/**
 * Ensure all images have alt text.
 *
 * @since 1.0.0
 *
 * @param string $html Image HTML.
 * @param int    $post_id Post ID.
 * @param int    $attachment_id Attachment ID.
 * @return string Modified image HTML.
 */
function skyyrose_ensure_image_alt( $html, $post_id, $attachment_id ) {
	if ( strpos( $html, 'alt=' ) === false ) {
		$alt = get_post_meta( $attachment_id, '_wp_attachment_image_alt', true );
		if ( empty( $alt ) ) {
			$alt = get_the_title( $attachment_id );
		}
		$html = str_replace( '<img', '<img alt="' . esc_attr( $alt ) . '"', $html );
	}
	return $html;
}
add_filter( 'post_thumbnail_html', 'skyyrose_ensure_image_alt', 10, 3 );

/**
 * Heading hierarchy is handled in individual templates (single.php, page.php)
 * where the context is known. Templates should use <h1> for the post title directly.
 *
 * @since 1.0.0
 */

/**
 * Enhance WooCommerce accessibility.
 *
 * @since 1.0.0
 */
function skyyrose_woocommerce_accessibility() {
	// Set aria-label on the add-to-cart BUTTON element (not inner text span).
	add_filter( 'woocommerce_loop_add_to_cart_args', function( $args, $product ) {
		$args['aria-label'] = sprintf(
			esc_attr__( 'Add %s to your cart', 'skyyrose-flagship' ),
			$product->get_name()
		);
		return $args;
	}, 10, 2 );

	// Add ARIA labels to cart items.
	add_filter( 'woocommerce_cart_item_remove_link', function( $link, $cart_item_key ) {
		$cart         = WC()->cart ? WC()->cart->get_cart() : array();
		$cart_item    = isset( $cart[ $cart_item_key ] ) ? $cart[ $cart_item_key ] : null;
		$product_name = $cart_item && isset( $cart_item['data'] ) ? $cart_item['data']->get_name() : '';
		return str_replace(
			'class="remove"',
			'class="remove" aria-label="' . esc_attr( sprintf( __( 'Remove %s from cart', 'skyyrose-flagship' ), $product_name ) ) . '"',
			$link
		);
	}, 10, 2 );
}
add_action( 'init', 'skyyrose_woocommerce_accessibility' );

/**
 * Landmark roles — handled natively by HTML5 semantic elements.
 *
 * HTML5 elements (<header>, <nav>, <main>, <footer>, <aside>) carry
 * implicit ARIA roles in all modern browsers.  The previous inline
 * <script> that assigned roles dynamically was removed in v3.2.2:
 * it bypassed wp_enqueue_script(), blocked CSP tightening, and
 * duplicated work the browser already does natively.
 *
 * @since 1.0.0
 * @since 3.2.2 Removed — HTML5 implicit roles are sufficient.
 */

/**
 * Add dns-prefetch for external resources used by WooCommerce.
 *
 * Google Fonts preconnect is handled in enqueue.php (skyyrose_preconnect_fonts).
 *
 * @since 1.0.0
 */
function skyyrose_preconnect_resources() {
	if ( class_exists( 'WooCommerce' ) ) {
		echo '<link rel="dns-prefetch" href="//www.google-analytics.com">' . "\n";
	}
}
add_action( 'wp_head', 'skyyrose_preconnect_resources', 1 );

/**
 * ============================================================================
 * ACCESSIBILITY & SEO TESTING TOOLS (Admin Page)
 * ============================================================================
 */

/**
 * Register accessibility testing admin page.
 *
 * @since 1.0.0
 */
function skyyrose_accessibility_testing_page() {
	add_theme_page(
		__( 'Accessibility & SEO Tools', 'skyyrose-flagship' ),
		__( 'A11y & SEO', 'skyyrose-flagship' ),
		'manage_options',
		'skyyrose-accessibility-seo',
		'skyyrose_accessibility_testing_page_content'
	);
}
add_action( 'admin_menu', 'skyyrose_accessibility_testing_page' );

/**
 * Accessibility testing page content.
 *
 * @since 1.0.0
 */
function skyyrose_accessibility_testing_page_content() {
	if ( ! current_user_can( 'manage_options' ) ) {
		wp_die( esc_html__( 'You do not have permission to access this page.', 'skyyrose-flagship' ) );
	}
	?>
	<div class="wrap">
		<h1><?php esc_html_e( 'Accessibility & SEO Tools', 'skyyrose-flagship' ); ?></h1>

		<div class="card">
			<h2><?php esc_html_e( 'WCAG 2.1 AA Compliance Checklist', 'skyyrose-flagship' ); ?></h2>
			<ul style="list-style: disc; margin-left: 20px;">
				<li><strong>&#10003;</strong> Semantic HTML5 structure implemented</li>
				<li><strong>&#10003;</strong> ARIA labels and roles for interactive elements</li>
				<li><strong>&#10003;</strong> Keyboard navigation support (Tab, Enter, Space, Esc)</li>
				<li><strong>&#10003;</strong> Focus indicators with 2px outline</li>
				<li><strong>&#10003;</strong> Skip to content link</li>
				<li><strong>&#10003;</strong> Alt text enforcement for images</li>
				<li><strong>&#10003;</strong> Color contrast ratio support (4.5:1 text, 3:1 UI)</li>
				<li><strong>&#10003;</strong> Screen reader announcements for dynamic content</li>
				<li><strong>&#10003;</strong> Form labels and error messages</li>
				<li><strong>&#10003;</strong> Accessible modals with keyboard trap</li>
				<li><strong>&#10003;</strong> ARIA live regions</li>
				<li><strong>&#10003;</strong> Reduced motion support</li>
				<li><strong>&#10003;</strong> High contrast mode support</li>
			</ul>
		</div>

		<div class="card">
			<h2><?php esc_html_e( 'SEO Features Checklist', 'skyyrose-flagship' ); ?></h2>
			<ul style="list-style: disc; margin-left: 20px;">
				<li><strong>&#10003;</strong> Product Schema.org markup</li>
				<li><strong>&#10003;</strong> Organization schema</li>
				<li><strong>&#10003;</strong> BreadcrumbList schema</li>
				<li><strong>&#10003;</strong> Review schema</li>
				<li><strong>&#10003;</strong> Collection/CollectionPage schema</li>
				<li><strong>&#10003;</strong> Open Graph tags (Facebook)</li>
				<li><strong>&#10003;</strong> Twitter Cards</li>
				<li><strong>&#10003;</strong> Canonical URLs</li>
				<li><strong>&#10003;</strong> Meta descriptions</li>
				<li><strong>&#10003;</strong> Title tag optimization</li>
				<li><strong>&#10003;</strong> XML sitemap support</li>
				<li><strong>&#10003;</strong> Robots meta tags</li>
				<li><strong>&#10003;</strong> Breadcrumb navigation</li>
			</ul>
		</div>

		<div class="card">
			<h2><?php esc_html_e( 'Quick Tests', 'skyyrose-flagship' ); ?></h2>
			<p><strong><?php esc_html_e( 'Test Page URL:', 'skyyrose-flagship' ); ?></strong></p>
			<input type="url" id="test-url" value="<?php echo esc_url( home_url( '/' ) ); ?>" style="width: 100%; max-width: 600px; padding: 8px; margin-bottom: 10px;">

			<p>
				<button type="button" class="button button-primary" onclick="window.open('https://wave.webaim.org/report#/' + document.getElementById('test-url').value, '_blank')">
					<?php esc_html_e( 'Test with WAVE', 'skyyrose-flagship' ); ?>
				</button>
				<button type="button" class="button button-primary" onclick="window.open('https://search.google.com/test/rich-results?url=' + encodeURIComponent(document.getElementById('test-url').value), '_blank')">
					<?php esc_html_e( 'Test Rich Results', 'skyyrose-flagship' ); ?>
				</button>
				<button type="button" class="button button-primary" onclick="window.open('https://pagespeed.web.dev/report?url=' + encodeURIComponent(document.getElementById('test-url').value), '_blank')">
					<?php esc_html_e( 'Test PageSpeed', 'skyyrose-flagship' ); ?>
				</button>
			</p>
		</div>

		<div class="card">
			<h2><?php esc_html_e( 'Customizer Settings', 'skyyrose-flagship' ); ?></h2>
			<p><?php esc_html_e( 'Configure social media profiles and contact information for enhanced SEO:', 'skyyrose-flagship' ); ?></p>
			<ul style="list-style: disc; margin-left: 20px;">
				<li>Facebook URL</li>
				<li>Twitter Handle &amp; URL</li>
				<li>Instagram URL</li>
				<li>LinkedIn URL</li>
				<li>YouTube URL</li>
				<li>Contact Phone</li>
				<li>Contact Email</li>
			</ul>
			<p>
				<a href="<?php echo esc_url( admin_url( 'customize.php' ) ); ?>" class="button button-primary">
					<?php esc_html_e( 'Open Customizer', 'skyyrose-flagship' ); ?>
				</a>
			</p>
		</div>
	</div>
	<?php
}
