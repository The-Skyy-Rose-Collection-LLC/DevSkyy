<?php
/**
 * Deployment Readiness Checklist
 *
 * Admin page that verifies theme readiness for production deployment.
 * Checks WooCommerce setup, required pages, product catalog, and
 * theme configuration.
 *
 * @package SkyyRose_Flagship
 * @since   3.12.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/*--------------------------------------------------------------
 * Admin Menu Registration
 *--------------------------------------------------------------*/

/**
 * Register the Deployment Checklist admin page under the SkyyRose menu.
 *
 * Creates a top-level "SkyyRose" menu if it does not already exist,
 * then adds the "Deployment Checklist" sub-page.
 *
 * @since 3.12.0
 * @return void
 */
function skyyrose_deployment_checklist_menu() {

	// Register the top-level SkyyRose menu (only once).
	$parent_slug = 'skyyrose-dashboard';

	if ( empty( $GLOBALS['admin_page_hooks'][ $parent_slug ] ) ) {
		add_menu_page(
			esc_html__( 'SkyyRose', 'skyyrose-flagship' ),
			esc_html__( 'SkyyRose', 'skyyrose-flagship' ),
			'manage_options',
			$parent_slug,
			'__return_null',
			'dashicons-star-filled',
			3
		);
	}

	add_submenu_page(
		$parent_slug,
		esc_html__( 'Deployment Checklist', 'skyyrose-flagship' ),
		esc_html__( 'Deployment Checklist', 'skyyrose-flagship' ),
		'manage_options',
		'skyyrose-deployment-checklist',
		'skyyrose_deployment_checklist_page'
	);
}
add_action( 'admin_menu', 'skyyrose_deployment_checklist_menu' );

/*--------------------------------------------------------------
 * Check Runner
 *--------------------------------------------------------------*/

/**
 * Run all deployment checks and return structured results.
 *
 * Each check returns an associative array with:
 *   - label   (string) Human-readable check name
 *   - status  (string) 'pass', 'fail', or 'warn'
 *   - detail  (string) Additional information
 *
 * Results are grouped by section.
 *
 * @since  3.12.0
 * @return array Associative array of section => checks[].
 */
function skyyrose_run_deployment_checks() {

	$results = array();

	/*--------------------------------------------------------------
	 * Section: Environment
	 *--------------------------------------------------------------*/
	$env_checks = array();

	// PHP Version >= 8.0.
	$php_version      = phpversion();
	$php_version_pass = version_compare( $php_version, '8.0', '>=' );
	$env_checks[]     = array(
		'label'  => esc_html__( 'PHP Version', 'skyyrose-flagship' ),
		'status' => $php_version_pass ? 'pass' : 'fail',
		'detail' => sprintf(
			/* translators: %s: PHP version string */
			esc_html__( 'Running PHP %s (requires 8.0+)', 'skyyrose-flagship' ),
			esc_html( $php_version )
		),
	);

	// WordPress Version >= 6.0.
	global $wp_version;
	$wp_version_pass = version_compare( $wp_version, '6.0', '>=' );
	$env_checks[]    = array(
		'label'  => esc_html__( 'WordPress Version', 'skyyrose-flagship' ),
		'status' => $wp_version_pass ? 'pass' : 'fail',
		'detail' => sprintf(
			/* translators: %s: WordPress version string */
			esc_html__( 'Running WordPress %s (requires 6.0+)', 'skyyrose-flagship' ),
			esc_html( $wp_version )
		),
	);

	// Theme Version.
	$theme         = wp_get_theme( 'skyyrose-flagship' );
	$theme_version = $theme->exists() ? $theme->get( 'Version' ) : esc_html__( 'Unknown', 'skyyrose-flagship' );
	$env_checks[]  = array(
		'label'  => esc_html__( 'Theme Version', 'skyyrose-flagship' ),
		'status' => 'pass',
		'detail' => sprintf(
			/* translators: %s: theme version string */
			esc_html__( 'SkyyRose Flagship v%s', 'skyyrose-flagship' ),
			esc_html( $theme_version )
		),
	);

	// SSL Certificate.
	$is_ssl       = is_ssl();
	$env_checks[] = array(
		'label'  => esc_html__( 'SSL Certificate', 'skyyrose-flagship' ),
		'status' => $is_ssl ? 'pass' : 'fail',
		'detail' => $is_ssl
			? esc_html__( 'Site is served over HTTPS', 'skyyrose-flagship' )
			: esc_html__( 'Site is NOT using HTTPS -- SSL required for production', 'skyyrose-flagship' ),
	);

	// Permalinks (not plain).
	$permalink_structure = get_option( 'permalink_structure' );
	$permalinks_ok       = ! empty( $permalink_structure );
	$env_checks[]        = array(
		'label'  => esc_html__( 'Permalinks', 'skyyrose-flagship' ),
		'status' => $permalinks_ok ? 'pass' : 'fail',
		'detail' => $permalinks_ok
			? sprintf(
				/* translators: %s: permalink structure string */
				esc_html__( 'Using pretty permalinks: %s', 'skyyrose-flagship' ),
				esc_html( $permalink_structure )
			)
			: esc_html__( 'Using plain permalinks -- update to pretty permalinks for SEO', 'skyyrose-flagship' ),
	);

	$results[ esc_html__( 'Environment', 'skyyrose-flagship' ) ] = $env_checks;

	/*--------------------------------------------------------------
	 * Section: Required Plugins
	 *--------------------------------------------------------------*/
	$plugin_checks = array();

	// WooCommerce.
	$woo_active      = class_exists( 'WooCommerce' );
	$plugin_checks[] = array(
		'label'  => esc_html__( 'WooCommerce Active', 'skyyrose-flagship' ),
		'status' => $woo_active ? 'pass' : 'fail',
		'detail' => $woo_active
			? esc_html__( 'WooCommerce is installed and active', 'skyyrose-flagship' )
			: esc_html__( 'WooCommerce is NOT active -- required for e-commerce functionality', 'skyyrose-flagship' ),
	);

	// Elementor (optional).
	$elementor_active = did_action( 'elementor/loaded' );
	$plugin_checks[]  = array(
		'label'  => esc_html__( 'Elementor', 'skyyrose-flagship' ),
		'status' => $elementor_active ? 'pass' : 'warn',
		'detail' => $elementor_active
			? esc_html__( 'Elementor is installed and active', 'skyyrose-flagship' )
			: esc_html__( 'Elementor is not active (optional -- needed for page builder features)', 'skyyrose-flagship' ),
	);

	// Yoast SEO (optional).
	$yoast_active    = defined( 'WPSEO_VERSION' );
	$plugin_checks[] = array(
		'label'  => esc_html__( 'Yoast SEO', 'skyyrose-flagship' ),
		'status' => $yoast_active ? 'pass' : 'warn',
		'detail' => $yoast_active
			? esc_html__( 'Yoast SEO is installed and active', 'skyyrose-flagship' )
			: esc_html__( 'Yoast SEO is not active (optional -- recommended for SEO)', 'skyyrose-flagship' ),
	);

	$results[ esc_html__( 'Required Plugins', 'skyyrose-flagship' ) ] = $plugin_checks;

	/*--------------------------------------------------------------
	 * Section: Required Pages
	 *--------------------------------------------------------------*/
	$page_checks = array();

	// Home page.
	$front_page_id  = (int) get_option( 'page_on_front' );
	$has_front_page = ( $front_page_id > 0 && 'page' === get_option( 'show_on_front' ) );
	$page_checks[]  = array(
		'label'  => esc_html__( 'Home Page', 'skyyrose-flagship' ),
		'status' => $has_front_page ? 'pass' : 'fail',
		'detail' => $has_front_page
			? sprintf(
				/* translators: %s: page title */
				esc_html__( 'Static front page set: "%s"', 'skyyrose-flagship' ),
				esc_html( get_the_title( $front_page_id ) )
			)
			: esc_html__( 'No static front page configured -- set in Settings > Reading', 'skyyrose-flagship' ),
	);

	// Collection pages.
	$collection_slugs = array(
		'collections/black-rose' => esc_html__( 'Collection: Black Rose', 'skyyrose-flagship' ),
		'collections/love-hurts' => esc_html__( 'Collection: Love Hurts', 'skyyrose-flagship' ),
		'collections/signature'  => esc_html__( 'Collection: Signature', 'skyyrose-flagship' ),
	);

	foreach ( $collection_slugs as $slug => $label ) {
		$page          = get_page_by_path( $slug );
		$page_checks[] = array(
			'label'  => $label,
			'status' => $page ? 'pass' : 'fail',
			'detail' => $page
				? sprintf(
					/* translators: %s: page title */
					esc_html__( 'Page exists: "%s"', 'skyyrose-flagship' ),
					esc_html( $page->post_title )
				)
				: sprintf(
					/* translators: %s: expected slug */
					esc_html__( 'Page with slug "%s" not found', 'skyyrose-flagship' ),
					esc_html( $slug )
				),
		);
	}

	// Immersive pages.
	$immersive_slugs = array(
		'immersive/black-rose' => esc_html__( 'Immersive: Black Rose', 'skyyrose-flagship' ),
		'immersive/love-hurts' => esc_html__( 'Immersive: Love Hurts', 'skyyrose-flagship' ),
		'immersive/signature'  => esc_html__( 'Immersive: Signature', 'skyyrose-flagship' ),
	);

	foreach ( $immersive_slugs as $slug => $label ) {
		$page          = get_page_by_path( $slug );
		$page_checks[] = array(
			'label'  => $label,
			'status' => $page ? 'pass' : 'warn',
			'detail' => $page
				? sprintf(
					/* translators: %s: page title */
					esc_html__( 'Page exists: "%s"', 'skyyrose-flagship' ),
					esc_html( $page->post_title )
				)
				: sprintf(
					/* translators: %s: expected slug */
					esc_html__( 'Page with slug "%s" not found (3D storytelling)', 'skyyrose-flagship' ),
					esc_html( $slug )
				),
		);
	}

	// Pre-Order Gateway.
	$preorder_page = skyyrose_deployment_find_page_by_slug_or_template( 'pre-order-gateway', 'template-preorder-gateway.php' );
	$page_checks[] = array(
		'label'  => esc_html__( 'Pre-Order Gateway', 'skyyrose-flagship' ),
		'status' => $preorder_page ? 'pass' : 'fail',
		'detail' => $preorder_page
			? esc_html__( 'Pre-Order Gateway page exists', 'skyyrose-flagship' )
			: esc_html__( 'Pre-Order Gateway page not found (slug or template)', 'skyyrose-flagship' ),
	);

	// About page.
	$about_page    = skyyrose_deployment_find_page_by_slug_or_template( 'about', 'template-about.php' );
	$page_checks[] = array(
		'label'  => esc_html__( 'About Page', 'skyyrose-flagship' ),
		'status' => $about_page ? 'pass' : 'warn',
		'detail' => $about_page
			? esc_html__( 'About page exists', 'skyyrose-flagship' )
			: esc_html__( 'About page not found', 'skyyrose-flagship' ),
	);

	// Contact page.
	$contact_page  = skyyrose_deployment_find_page_by_slug_or_template( 'contact', 'template-contact.php' );
	$page_checks[] = array(
		'label'  => esc_html__( 'Contact Page', 'skyyrose-flagship' ),
		'status' => $contact_page ? 'pass' : 'warn',
		'detail' => $contact_page
			? esc_html__( 'Contact page exists', 'skyyrose-flagship' )
			: esc_html__( 'Contact page not found', 'skyyrose-flagship' ),
	);

	// WooCommerce pages (Shop, Cart, Checkout).
	if ( $woo_active ) {
		$woo_pages = array(
			'shop'     => array(
				'label'     => esc_html__( 'Shop Page', 'skyyrose-flagship' ),
				'option'    => 'woocommerce_shop_page_id',
			),
			'cart'     => array(
				'label'     => esc_html__( 'Cart Page', 'skyyrose-flagship' ),
				'option'    => 'woocommerce_cart_page_id',
			),
			'checkout' => array(
				'label'     => esc_html__( 'Checkout Page', 'skyyrose-flagship' ),
				'option'    => 'woocommerce_checkout_page_id',
			),
		);

		foreach ( $woo_pages as $key => $woo_page ) {
			$page_id       = (int) get_option( $woo_page['option'] );
			$exists        = ( $page_id > 0 && 'publish' === get_post_status( $page_id ) );
			$page_checks[] = array(
				'label'  => $woo_page['label'],
				'status' => $exists ? 'pass' : 'fail',
				'detail' => $exists
					? sprintf(
						/* translators: %s: page title */
						esc_html__( 'Page exists: "%s"', 'skyyrose-flagship' ),
						esc_html( get_the_title( $page_id ) )
					)
					: sprintf(
						/* translators: %s: WooCommerce page name */
						esc_html__( 'WooCommerce %s page not configured', 'skyyrose-flagship' ),
						esc_html( $key )
					),
			);
		}
	}

	$results[ esc_html__( 'Required Pages', 'skyyrose-flagship' ) ] = $page_checks;

	/*--------------------------------------------------------------
	 * Section: Product Catalog
	 *--------------------------------------------------------------*/
	$catalog_checks = array();

	if ( $woo_active ) {
		$collections = array(
			'black-rose' => esc_html__( 'Black Rose', 'skyyrose-flagship' ),
			'love-hurts' => esc_html__( 'Love Hurts', 'skyyrose-flagship' ),
			'signature'  => esc_html__( 'Signature', 'skyyrose-flagship' ),
		);

		foreach ( $collections as $slug => $name ) {
			$term = get_term_by( 'slug', $slug, 'product_cat' );

			if ( ! $term ) {
				$catalog_checks[] = array(
					'label'  => sprintf(
						/* translators: %s: collection name */
						esc_html__( 'Products: %s', 'skyyrose-flagship' ),
						$name
					),
					'status' => 'fail',
					'detail' => sprintf(
						/* translators: %s: category slug */
						esc_html__( 'Product category "%s" does not exist', 'skyyrose-flagship' ),
						esc_html( $slug )
					),
				);
				continue;
			}

			$product_query = new WP_Query(
				array(
					'post_type'      => 'product',
					'post_status'    => 'publish',
					'tax_query'      => array( // phpcs:ignore WordPress.DB.SlowDBQuery.slow_db_query_tax_query
						array(
							'taxonomy' => 'product_cat',
							'field'    => 'slug',
							'terms'    => $slug,
						),
					),
					'posts_per_page' => 1,
					'fields'         => 'ids',
					'no_found_rows'  => false,
				)
			);

			$count            = $product_query->found_posts;
			$catalog_checks[] = array(
				'label'  => sprintf(
					/* translators: %s: collection name */
					esc_html__( 'Products: %s', 'skyyrose-flagship' ),
					$name
				),
				'status' => $count > 0 ? 'pass' : 'fail',
				'detail' => sprintf(
					/* translators: %1$d: product count, %2$s: collection name */
					esc_html( _n(
						'%1$d published product in %2$s',
						'%1$d published products in %2$s',
						$count,
						'skyyrose-flagship'
					) ),
					$count,
					$name
				),
			);

			wp_reset_postdata();
		}
	} else {
		$catalog_checks[] = array(
			'label'  => esc_html__( 'Product Catalog', 'skyyrose-flagship' ),
			'status' => 'fail',
			'detail' => esc_html__( 'WooCommerce not active -- cannot check product catalog', 'skyyrose-flagship' ),
		);
	}

	$results[ esc_html__( 'Product Catalog', 'skyyrose-flagship' ) ] = $catalog_checks;

	/*--------------------------------------------------------------
	 * Section: WooCommerce Configuration
	 *--------------------------------------------------------------*/
	$woo_config_checks = array();

	if ( $woo_active ) {
		// Payment Gateway.
		$gateways         = WC()->payment_gateways()->get_available_payment_gateways();
		$has_gateway       = ! empty( $gateways );
		$woo_config_checks[] = array(
			'label'  => esc_html__( 'Payment Gateway', 'skyyrose-flagship' ),
			'status' => $has_gateway ? 'pass' : 'fail',
			'detail' => $has_gateway
				? sprintf(
					/* translators: %d: number of active gateways */
					esc_html( _n(
						'%d payment gateway enabled',
						'%d payment gateways enabled',
						count( $gateways ),
						'skyyrose-flagship'
					) ),
					count( $gateways )
				)
				: esc_html__( 'No payment gateways enabled -- customers cannot checkout', 'skyyrose-flagship' ),
		);

		// Shipping Zones.
		$shipping_zones = WC_Shipping_Zones::get_zones();
		$has_zones      = ! empty( $shipping_zones );

		// Also check the "Rest of the World" default zone for methods.
		$default_zone        = new WC_Shipping_Zone( 0 );
		$default_zone_methods = $default_zone->get_shipping_methods();
		$has_any_shipping     = $has_zones || ! empty( $default_zone_methods );

		$woo_config_checks[] = array(
			'label'  => esc_html__( 'Shipping Zones', 'skyyrose-flagship' ),
			'status' => $has_any_shipping ? 'pass' : 'warn',
			'detail' => $has_any_shipping
				? sprintf(
					/* translators: %d: number of shipping zones */
					esc_html__( '%d shipping zone(s) configured', 'skyyrose-flagship' ),
					count( $shipping_zones )
				)
				: esc_html__( 'No shipping zones configured -- digital-only stores may ignore this', 'skyyrose-flagship' ),
		);
	} else {
		$woo_config_checks[] = array(
			'label'  => esc_html__( 'WooCommerce Configuration', 'skyyrose-flagship' ),
			'status' => 'fail',
			'detail' => esc_html__( 'WooCommerce not active -- cannot check store configuration', 'skyyrose-flagship' ),
		);
	}

	$results[ esc_html__( 'WooCommerce Configuration', 'skyyrose-flagship' ) ] = $woo_config_checks;

	/*--------------------------------------------------------------
	 * Section: Theme Assets
	 *--------------------------------------------------------------*/
	$asset_checks = array();

	$asset_dirs = array(
		'assets/scenes/'        => esc_html__( 'Scene Assets (3D)', 'skyyrose-flagship' ),
		'assets/branding/'      => esc_html__( 'Branding Assets', 'skyyrose-flagship' ),
		'assets/images/mascot/' => esc_html__( 'Mascot Assets', 'skyyrose-flagship' ),
	);

	foreach ( $asset_dirs as $relative_path => $label ) {
		$full_path      = get_template_directory() . '/' . $relative_path;
		$dir_exists     = is_dir( $full_path );
		$asset_checks[] = array(
			'label'  => $label,
			'status' => $dir_exists ? 'pass' : 'warn',
			'detail' => $dir_exists
				? sprintf(
					/* translators: %s: directory path */
					esc_html__( 'Directory exists: %s', 'skyyrose-flagship' ),
					esc_html( $relative_path )
				)
				: sprintf(
					/* translators: %s: directory path */
					esc_html__( 'Directory missing: %s', 'skyyrose-flagship' ),
					esc_html( $relative_path )
				),
		);
	}

	$results[ esc_html__( 'Theme Assets', 'skyyrose-flagship' ) ] = $asset_checks;

	/*--------------------------------------------------------------
	 * Section: Security
	 *--------------------------------------------------------------*/
	$security_checks = array();

	// Security headers file loaded.
	$security_file         = get_template_directory() . '/inc/security.php';
	$security_file_exists  = file_exists( $security_file );
	$security_func_exists  = function_exists( 'skyyrose_send_security_headers' );
	$security_checks[]     = array(
		'label'  => esc_html__( 'Security Headers', 'skyyrose-flagship' ),
		'status' => ( $security_file_exists && $security_func_exists ) ? 'pass' : 'fail',
		'detail' => ( $security_file_exists && $security_func_exists )
			? esc_html__( 'security.php loaded and security headers function registered', 'skyyrose-flagship' )
			: esc_html__( 'security.php not loaded -- CSP and security headers will be missing', 'skyyrose-flagship' ),
	);

	$results[ esc_html__( 'Security', 'skyyrose-flagship' ) ] = $security_checks;

	return $results;
}

/*--------------------------------------------------------------
 * Helper: Find Page by Slug or Template
 *--------------------------------------------------------------*/

/**
 * Look up a page by its slug or by its assigned page template.
 *
 * @since 3.12.0
 *
 * @param string $slug     Page slug to search for.
 * @param string $template Template filename (e.g., 'template-about.php').
 * @return WP_Post|null The page post object or null if not found.
 */
function skyyrose_deployment_find_page_by_slug_or_template( $slug, $template ) {

	// Try slug first.
	$page = get_page_by_path( $slug );
	if ( $page && 'publish' === $page->post_status ) {
		return $page;
	}

	// Fallback: search by page template.
	$pages_with_template = get_posts(
		array(
			'post_type'      => 'page',
			'post_status'    => 'publish',
			'meta_key'       => '_wp_page_template', // phpcs:ignore WordPress.DB.SlowDBQuery.slow_db_query_meta_key
			'meta_value'     => $template, // phpcs:ignore WordPress.DB.SlowDBQuery.slow_db_query_meta_value
			'posts_per_page' => 1,
			'fields'         => 'ids',
		)
	);

	if ( ! empty( $pages_with_template ) ) {
		return get_post( $pages_with_template[0] );
	}

	return null;
}

/*--------------------------------------------------------------
 * Admin Page Renderer
 *--------------------------------------------------------------*/

/**
 * Render the Deployment Checklist admin page.
 *
 * Runs all checks and displays results with the SkyyRose dark luxury
 * aesthetic. Each section is collapsible. The summary at the top shows
 * how many checks passed vs total.
 *
 * @since 3.12.0
 * @return void
 */
function skyyrose_deployment_checklist_page() {

	if ( ! current_user_can( 'manage_options' ) ) {
		wp_die( esc_html__( 'You do not have sufficient permissions to access this page.', 'skyyrose-flagship' ) );
	}

	$results = skyyrose_run_deployment_checks();

	// Tally totals.
	$total_checks  = 0;
	$passed_checks = 0;
	$failed_checks = 0;
	$warn_checks   = 0;

	foreach ( $results as $checks ) {
		foreach ( $checks as $check ) {
			++$total_checks;
			if ( 'pass' === $check['status'] ) {
				++$passed_checks;
			} elseif ( 'fail' === $check['status'] ) {
				++$failed_checks;
			} else {
				++$warn_checks;
			}
		}
	}

	$all_passed = ( 0 === $failed_checks );
	?>
	<div class="wrap skyyrose-deploy-wrap">
		<style>
			.skyyrose-deploy-wrap {
				background: #0A0A0A;
				color: #E5E5E5;
				padding: 30px;
				margin: 20px 10px 20px 0;
				border-radius: 12px;
				font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
				min-height: 80vh;
			}

			.skyyrose-deploy-wrap * {
				box-sizing: border-box;
			}

			.skyyrose-deploy-header {
				display: flex;
				align-items: center;
				justify-content: space-between;
				margin-bottom: 30px;
				padding-bottom: 20px;
				border-bottom: 1px solid rgba(183, 110, 121, 0.3);
			}

			.skyyrose-deploy-header h1 {
				color: #FFFFFF;
				font-size: 28px;
				font-weight: 300;
				letter-spacing: 2px;
				text-transform: uppercase;
				margin: 0;
				padding: 0;
			}

			.skyyrose-deploy-header h1 span {
				color: #B76E79;
				font-weight: 600;
			}

			.skyyrose-deploy-summary {
				background: linear-gradient(135deg, #1A1A1A 0%, #151015 100%);
				border: 1px solid rgba(183, 110, 121, 0.25);
				border-radius: 12px;
				padding: 24px 30px;
				margin-bottom: 30px;
				display: flex;
				align-items: center;
				gap: 30px;
			}

			.skyyrose-deploy-summary-score {
				font-size: 48px;
				font-weight: 700;
				line-height: 1;
			}

			.skyyrose-deploy-summary-score.all-pass { color: #4CAF50; }
			.skyyrose-deploy-summary-score.has-fail { color: #F44336; }

			.skyyrose-deploy-summary-details {
				flex: 1;
			}

			.skyyrose-deploy-summary-details h2 {
				margin: 0 0 6px;
				font-size: 18px;
				font-weight: 600;
				color: #FFFFFF;
			}

			.skyyrose-deploy-summary-details p {
				margin: 0;
				color: #999;
				font-size: 14px;
			}

			.skyyrose-deploy-badge {
				display: inline-block;
				padding: 6px 16px;
				border-radius: 20px;
				font-size: 12px;
				font-weight: 700;
				letter-spacing: 1px;
				text-transform: uppercase;
			}

			.skyyrose-deploy-badge.ready {
				background: rgba(76, 175, 80, 0.15);
				color: #4CAF50;
				border: 1px solid rgba(76, 175, 80, 0.4);
			}

			.skyyrose-deploy-badge.not-ready {
				background: rgba(244, 67, 54, 0.15);
				color: #F44336;
				border: 1px solid rgba(244, 67, 54, 0.4);
			}

			.skyyrose-deploy-stat {
				display: inline-flex;
				align-items: center;
				gap: 5px;
				margin-right: 18px;
				font-size: 13px;
			}

			.skyyrose-deploy-stat .count { font-weight: 700; }
			.skyyrose-deploy-stat.pass .count { color: #4CAF50; }
			.skyyrose-deploy-stat.fail .count { color: #F44336; }
			.skyyrose-deploy-stat.warn .count { color: #FF9800; }

			.skyyrose-deploy-section {
				background: #111111;
				border: 1px solid #222222;
				border-radius: 10px;
				margin-bottom: 16px;
				overflow: hidden;
				transition: border-color 0.2s;
			}

			.skyyrose-deploy-section:hover {
				border-color: rgba(183, 110, 121, 0.4);
			}

			.skyyrose-deploy-section-header {
				display: flex;
				align-items: center;
				justify-content: space-between;
				padding: 16px 20px;
				cursor: pointer;
				user-select: none;
				background: rgba(26, 26, 26, 0.6);
				border-bottom: 1px solid #222222;
				transition: background 0.2s;
			}

			.skyyrose-deploy-section-header:hover {
				background: rgba(183, 110, 121, 0.08);
			}

			.skyyrose-deploy-section-header h3 {
				margin: 0;
				font-size: 15px;
				font-weight: 600;
				color: #FFFFFF;
				letter-spacing: 0.5px;
			}

			.skyyrose-deploy-section-toggle {
				color: #B76E79;
				font-size: 18px;
				transition: transform 0.3s;
				line-height: 1;
			}

			.skyyrose-deploy-section.collapsed .skyyrose-deploy-section-toggle {
				transform: rotate(-90deg);
			}

			.skyyrose-deploy-section.collapsed .skyyrose-deploy-section-body {
				display: none;
			}

			.skyyrose-deploy-section-body {
				padding: 8px 0;
			}

			.skyyrose-deploy-check {
				display: flex;
				align-items: flex-start;
				gap: 14px;
				padding: 12px 20px;
				border-bottom: 1px solid rgba(34, 34, 34, 0.8);
				transition: background 0.15s;
			}

			.skyyrose-deploy-check:last-child {
				border-bottom: none;
			}

			.skyyrose-deploy-check:hover {
				background: rgba(255, 255, 255, 0.02);
			}

			.skyyrose-deploy-check-icon {
				flex-shrink: 0;
				width: 22px;
				height: 22px;
				border-radius: 50%;
				display: flex;
				align-items: center;
				justify-content: center;
				font-size: 12px;
				font-weight: 700;
				margin-top: 1px;
			}

			.skyyrose-deploy-check-icon.pass {
				background: rgba(76, 175, 80, 0.15);
				color: #4CAF50;
				border: 1px solid rgba(76, 175, 80, 0.4);
			}

			.skyyrose-deploy-check-icon.fail {
				background: rgba(244, 67, 54, 0.15);
				color: #F44336;
				border: 1px solid rgba(244, 67, 54, 0.4);
			}

			.skyyrose-deploy-check-icon.warn {
				background: rgba(255, 152, 0, 0.15);
				color: #FF9800;
				border: 1px solid rgba(255, 152, 0, 0.4);
			}

			.skyyrose-deploy-check-content {
				flex: 1;
				min-width: 0;
			}

			.skyyrose-deploy-check-label {
				font-size: 14px;
				font-weight: 500;
				color: #E5E5E5;
				margin-bottom: 3px;
			}

			.skyyrose-deploy-check-detail {
				font-size: 12px;
				color: #888;
				line-height: 1.4;
			}

			.skyyrose-deploy-refresh {
				display: inline-flex;
				align-items: center;
				gap: 8px;
				padding: 10px 24px;
				background: linear-gradient(135deg, #B76E79 0%, #9A5A63 100%);
				color: #FFFFFF;
				border: none;
				border-radius: 8px;
				font-size: 13px;
				font-weight: 600;
				letter-spacing: 0.5px;
				text-transform: uppercase;
				cursor: pointer;
				text-decoration: none;
				transition: opacity 0.2s;
			}

			.skyyrose-deploy-refresh:hover {
				opacity: 0.85;
				color: #FFFFFF;
			}

			.skyyrose-deploy-timestamp {
				font-size: 12px;
				color: #666;
				margin-top: 20px;
				text-align: right;
			}
		</style>

		<div class="skyyrose-deploy-header">
			<h1><span>SkyyRose</span> Deployment Checklist</h1>
			<a href="<?php echo esc_url( admin_url( 'admin.php?page=skyyrose-deployment-checklist' ) ); ?>" class="skyyrose-deploy-refresh">
				&#8635; <?php esc_html_e( 'Re-Run Checks', 'skyyrose-flagship' ); ?>
			</a>
		</div>

		<div class="skyyrose-deploy-summary">
			<div class="skyyrose-deploy-summary-score <?php echo esc_attr( $all_passed ? 'all-pass' : 'has-fail' ); ?>">
				<?php echo esc_html( $passed_checks ); ?>/<?php echo esc_html( $total_checks ); ?>
			</div>
			<div class="skyyrose-deploy-summary-details">
				<h2>
					<?php
					if ( $all_passed ) {
						esc_html_e( 'All Critical Checks Passed', 'skyyrose-flagship' );
					} else {
						printf(
							/* translators: %d: number of failed checks */
							esc_html( _n(
								'%d Critical Issue Found',
								'%d Critical Issues Found',
								$failed_checks,
								'skyyrose-flagship'
							) ),
							$failed_checks
						);
					}
					?>
				</h2>
				<p>
					<span class="skyyrose-deploy-stat pass">
						<span class="count"><?php echo esc_html( $passed_checks ); ?></span> <?php esc_html_e( 'passed', 'skyyrose-flagship' ); ?>
					</span>
					<span class="skyyrose-deploy-stat fail">
						<span class="count"><?php echo esc_html( $failed_checks ); ?></span> <?php esc_html_e( 'failed', 'skyyrose-flagship' ); ?>
					</span>
					<span class="skyyrose-deploy-stat warn">
						<span class="count"><?php echo esc_html( $warn_checks ); ?></span> <?php esc_html_e( 'warnings', 'skyyrose-flagship' ); ?>
					</span>
				</p>
			</div>
			<span class="skyyrose-deploy-badge <?php echo esc_attr( $all_passed ? 'ready' : 'not-ready' ); ?>">
				<?php echo $all_passed ? esc_html__( 'Ready to Deploy', 'skyyrose-flagship' ) : esc_html__( 'Not Ready', 'skyyrose-flagship' ); ?>
			</span>
		</div>

		<?php foreach ( $results as $section_label => $checks ) : ?>
			<div class="skyyrose-deploy-section">
				<div class="skyyrose-deploy-section-header" role="button" tabindex="0">
					<h3><?php echo esc_html( $section_label ); ?></h3>
					<span class="skyyrose-deploy-section-toggle">&#9660;</span>
				</div>
				<div class="skyyrose-deploy-section-body">
					<?php foreach ( $checks as $check ) : ?>
						<div class="skyyrose-deploy-check">
							<div class="skyyrose-deploy-check-icon <?php echo esc_attr( $check['status'] ); ?>">
								<?php
								if ( 'pass' === $check['status'] ) {
									echo '&#10003;';
								} elseif ( 'fail' === $check['status'] ) {
									echo '&#10007;';
								} else {
									echo '&#9888;';
								}
								?>
							</div>
							<div class="skyyrose-deploy-check-content">
								<div class="skyyrose-deploy-check-label"><?php echo esc_html( $check['label'] ); ?></div>
								<div class="skyyrose-deploy-check-detail"><?php echo esc_html( $check['detail'] ); ?></div>
							</div>
						</div>
					<?php endforeach; ?>
				</div>
			</div>
		<?php endforeach; ?>

		<div class="skyyrose-deploy-timestamp">
			<?php
			printf(
				/* translators: %s: date and time of the check */
				esc_html__( 'Checked at %s', 'skyyrose-flagship' ),
				esc_html( current_time( 'F j, Y \a\t g:i A T' ) )
			);
			?>
		</div>

	</div>
	<script>
	document.querySelectorAll('.skyyrose-deploy-section-header').forEach(function(el) {
		el.addEventListener('click', function() {
			this.parentElement.classList.toggle('collapsed');
		});
		el.addEventListener('keydown', function(e) {
			if (e.key === 'Enter' || e.key === ' ') {
				e.preventDefault();
				this.parentElement.classList.toggle('collapsed');
			}
		});
	});
	</script>
	<?php
}
