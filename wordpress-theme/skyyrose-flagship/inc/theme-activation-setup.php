<?php
/**
 * Theme Activation Setup
 *
 * Programmatically creates WordPress pages (with template assignments),
 * WooCommerce page settings, reading settings, and site options on
 * theme activation. Uses existence checks and versioned flags to
 * prevent duplicate creation.
 *
 * Runs on `after_switch_theme` (fresh activation) and once on `init`
 * via a versioned option flag (for sites already running the theme).
 *
 * @package SkyyRose_Flagship
 * @since   4.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Version flag for this setup module.
 *
 * Bump this constant when adding new pages or changing setup logic.
 * The `init` runner uses this to determine if setup has already run.
 */
define( 'SKYYROSE_SETUP_VERSION', '4.0.0' );

/*--------------------------------------------------------------
 * Page Definitions
 *--------------------------------------------------------------*/

/**
 * Get the list of pages the theme requires.
 *
 * Each entry maps a slug to a title, template, and optional content.
 * Templates use the WordPress `_wp_page_template` meta key.
 *
 * @since 4.0.0
 * @return array Associative array of slug => page data.
 */
function skyyrose_get_required_pages() {
	return array(
		// --- Core pages ---
		'home'                    => array(
			'title'    => __( 'Home', 'skyyrose-flagship' ),
			'template' => 'front-page.php',
			'content'  => '',
		),
		'about'                   => array(
			'title'    => __( 'About', 'skyyrose-flagship' ),
			'template' => 'template-about.php',
			'content'  => '',
		),
		'contact'                 => array(
			'title'    => __( 'Contact', 'skyyrose-flagship' ),
			'template' => 'template-contact.php',
			'content'  => '',
		),
		'pre-order'               => array(
			'title'    => __( 'Pre-Order', 'skyyrose-flagship' ),
			'template' => 'template-preorder-gateway.php',
			'content'  => '',
		),

		// --- Collection pages ---
		'collection-black-rose'   => array(
			'title'    => __( 'Black Rose Collection', 'skyyrose-flagship' ),
			'template' => 'template-collection-black-rose.php',
			'content'  => '',
		),
		'collection-love-hurts'   => array(
			'title'    => __( 'Love Hurts Collection', 'skyyrose-flagship' ),
			'template' => 'template-collection-love-hurts.php',
			'content'  => '',
		),
		'collection-signature'    => array(
			'title'    => __( 'Signature Collection', 'skyyrose-flagship' ),
			'template' => 'template-collection-signature.php',
			'content'  => '',
		),
		'collection-kids-capsule' => array(
			'title'    => __( 'Kids Capsule', 'skyyrose-flagship' ),
			'template' => 'template-collection-kids-capsule.php',
			'content'  => '',
		),

		// --- Landing pages (conversion engines) ---
		'landing-black-rose'      => array(
			'title'    => __( 'Black Rose — Limited Drop', 'skyyrose-flagship' ),
			'template' => 'template-landing-black-rose.php',
			'content'  => '',
		),
		'landing-love-hurts'      => array(
			'title'    => __( 'Love Hurts — The Collection', 'skyyrose-flagship' ),
			'template' => 'template-landing-love-hurts.php',
			'content'  => '',
		),
		'landing-signature'       => array(
			'title'    => __( 'Signature — Foundation Wardrobe', 'skyyrose-flagship' ),
			'template' => 'template-landing-signature.php',
			'content'  => '',
		),

		// --- Immersive experience pages (3D storytelling) ---
		'experience-black-rose'   => array(
			'title'    => __( 'Black Rose Experience', 'skyyrose-flagship' ),
			'template' => 'template-immersive-black-rose.php',
			'content'  => '',
		),
		'experience-love-hurts'   => array(
			'title'    => __( 'Love Hurts Experience', 'skyyrose-flagship' ),
			'template' => 'template-immersive-love-hurts.php',
			'content'  => '',
		),
		'experience-signature'    => array(
			'title'    => __( 'Signature Experience', 'skyyrose-flagship' ),
			'template' => 'template-immersive-signature.php',
			'content'  => '',
		),

		// --- Utility pages ---
		'wishlist'                => array(
			'title'    => __( 'Wishlist', 'skyyrose-flagship' ),
			'template' => 'page-wishlist.php',
			'content'  => '',
		),
		'style-quiz'              => array(
			'title'    => __( 'Style Quiz', 'skyyrose-flagship' ),
			'template' => 'template-style-quiz.php',
			'content'  => '',
		),
	);
}

/*--------------------------------------------------------------
 * Page Creation
 *--------------------------------------------------------------*/

/**
 * Create all required pages and assign templates.
 *
 * Checks for existing pages by slug before creating. Assigns the
 * `_wp_page_template` meta so WordPress routes to the correct
 * template file automatically.
 *
 * @since 4.0.0
 * @return array Map of slug => page ID for created/existing pages.
 */
function skyyrose_create_required_pages() {
	$pages    = skyyrose_get_required_pages();
	$page_ids = array();

	foreach ( $pages as $slug => $data ) {
		// Check if page already exists by slug.
		$existing = get_page_by_path( $slug );

		if ( $existing ) {
			$page_id = $existing->ID;

			// Ensure template is assigned even on existing pages.
			$current_template = get_post_meta( $page_id, '_wp_page_template', true );
			if ( empty( $current_template ) || 'default' === $current_template ) {
				update_post_meta( $page_id, '_wp_page_template', sanitize_file_name( $data['template'] ) );
			}
		} else {
			$page_id = wp_insert_post(
				array(
					'post_title'   => $data['title'],
					'post_name'    => $slug,
					'post_content' => $data['content'],
					'post_status'  => 'publish',
					'post_type'    => 'page',
					'post_author'  => 1,
					'meta_input'   => array(
						'_wp_page_template' => sanitize_file_name( $data['template'] ),
					),
				),
				true
			);

			if ( is_wp_error( $page_id ) ) {
				continue;
			}
		}

		$page_ids[ $slug ] = $page_id;
	}

	return $page_ids;
}

/*--------------------------------------------------------------
 * Reading Settings (Static Front Page)
 *--------------------------------------------------------------*/

/**
 * Set the "Home" page as the static front page.
 *
 * Configures WordPress to use a static page (not latest posts)
 * as the front page, pointing to the "Home" page we created.
 *
 * @since 4.0.0
 * @param array $page_ids Map of slug => page ID from page creation.
 * @return void
 */
function skyyrose_configure_reading_settings( $page_ids ) {
	if ( empty( $page_ids['home'] ) ) {
		return;
	}

	$home_id = absint( $page_ids['home'] );

	// Set static front page.
	update_option( 'show_on_front', 'page' );
	update_option( 'page_on_front', $home_id );

	// No dedicated posts page (this is a product site, not a blog).
	// Only set if not already configured.
	if ( ! get_option( 'page_for_posts' ) ) {
		update_option( 'page_for_posts', 0 );
	}
}

/*--------------------------------------------------------------
 * Site Identity & SEO Options
 *--------------------------------------------------------------*/

/**
 * Set site identity options for SEO and branding.
 *
 * Only sets options that are empty or have WordPress defaults.
 * Does NOT overwrite user-configured values.
 *
 * @since 4.0.0
 * @return void
 */
function skyyrose_configure_site_options() {
	// Site title — only if still default "Just another WordPress site" or empty.
	$current_desc = get_option( 'blogdescription' );
	if ( empty( $current_desc ) || 'Just another WordPress site' === $current_desc ) {
		update_option( 'blogdescription', __( 'Luxury Grows from Concrete. Premium streetwear from Oakland, CA.', 'skyyrose-flagship' ) );
	}

	// Permalink structure — pretty permalinks.
	$current_permalink = get_option( 'permalink_structure' );
	if ( empty( $current_permalink ) ) {
		update_option( 'permalink_structure', '/%postname%/' );
		flush_rewrite_rules();
	}

	// Timezone.
	if ( ! get_option( 'timezone_string' ) ) {
		update_option( 'timezone_string', 'America/Los_Angeles' );
	}

	// Date format.
	update_option( 'date_format', 'F j, Y' );

	// Pre-order deadline default (30 days from now).
	if ( ! get_option( 'skyyrose_preorder_deadline' ) ) {
		update_option( 'skyyrose_preorder_deadline', gmdate( 'Y-m-d', strtotime( '+30 days' ) ) );
	}
}

/*--------------------------------------------------------------
 * WooCommerce Page Assignments
 *--------------------------------------------------------------*/

/**
 * Assign WooCommerce-required pages (shop, cart, checkout, my-account).
 *
 * WooCommerce creates these pages on its own activation, but if they
 * don't exist or aren't assigned, this ensures they are.
 *
 * @since 4.0.0
 * @param array $page_ids Map of slug => page ID.
 * @return void
 */
function skyyrose_configure_woocommerce_settings( $page_ids ) {
	if ( ! class_exists( 'WooCommerce' ) ) {
		return;
	}

	// WooCommerce pages — only create if they don't already exist.
	$wc_pages = array(
		'shop'       => array(
			'title'  => __( 'Shop', 'skyyrose-flagship' ),
			'option' => 'woocommerce_shop_page_id',
		),
		'cart'       => array(
			'title'  => __( 'Cart', 'skyyrose-flagship' ),
			'option' => 'woocommerce_cart_page_id',
		),
		'checkout'   => array(
			'title'  => __( 'Checkout', 'skyyrose-flagship' ),
			'option' => 'woocommerce_checkout_page_id',
		),
		'my-account' => array(
			'title'  => __( 'My Account', 'skyyrose-flagship' ),
			'option' => 'woocommerce_myaccount_page_id',
		),
	);

	foreach ( $wc_pages as $slug => $wc_data ) {
		$current_page_id = absint( get_option( $wc_data['option'] ) );

		// If the option is set and the page exists, skip.
		if ( $current_page_id > 0 && get_post( $current_page_id ) ) {
			continue;
		}

		// Check if page exists by slug.
		$existing = get_page_by_path( $slug );
		if ( $existing ) {
			update_option( $wc_data['option'], $existing->ID );
			continue;
		}

		// Create the page.
		$new_id = wp_insert_post(
			array(
				'post_title'   => $wc_data['title'],
				'post_name'    => $slug,
				'post_content' => '',
				'post_status'  => 'publish',
				'post_type'    => 'page',
				'post_author'  => 1,
			),
			true
		);

		if ( ! is_wp_error( $new_id ) ) {
			update_option( $wc_data['option'], $new_id );
		}
	}

	// WooCommerce general settings.
	update_option( 'woocommerce_currency', 'USD' );
	update_option( 'woocommerce_enable_guest_checkout', 'yes' );
	update_option( 'woocommerce_enable_signup_and_login_from_checkout', 'yes' );
	update_option( 'woocommerce_manage_stock', 'yes' );

	// Image sizes for luxury product display.
	update_option( 'woocommerce_single_image_width', 600 );
	update_option( 'woocommerce_thumbnail_image_width', 300 );
}

/*--------------------------------------------------------------
 * Master Orchestrator
 *--------------------------------------------------------------*/

/**
 * Run the full theme activation setup.
 *
 * Orchestrates page creation, reading settings, site options,
 * and WooCommerce configuration in the correct order.
 *
 * @since 4.0.0
 * @return void
 */
function skyyrose_run_activation_setup() {
	// 1. Create all required pages.
	$page_ids = skyyrose_create_required_pages();

	// 2. Set static front page.
	skyyrose_configure_reading_settings( $page_ids );

	// 3. Set site identity defaults.
	skyyrose_configure_site_options();

	// 4. Configure WooCommerce pages and settings.
	skyyrose_configure_woocommerce_settings( $page_ids );
}

// Run on theme activation.
add_action( 'after_switch_theme', 'skyyrose_run_activation_setup' );

// Run once on `init` for sites already running the theme.
// Versioned flag ensures it runs exactly once per setup version.
add_action(
	'init',
	function () {
		if ( get_option( 'skyyrose_activation_setup_version' ) === SKYYROSE_SETUP_VERSION ) {
			return;
		}
		skyyrose_run_activation_setup();
		update_option( 'skyyrose_activation_setup_version', SKYYROSE_SETUP_VERSION );
	},
	30 // After product-taxonomy.php (priority 20) so WC categories exist.
);
