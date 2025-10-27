<?php
/**
 * Skyy Rose Collection Theme Functions
 *
 * Luxury fashion WordPress theme functions with advanced WooCommerce integration
 *
 * @package Skyy_Rose_Collection
 * @version 1.0.0
 * @author DevSkyy WordPress Development Specialist
 * @since 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
	exit;
}

/**
 * Theme version constant
 */
define('SKYY_ROSE_COLLECTION_VERSION', '1.0.0');

/**
 * Theme setup
 *
 * Sets up theme defaults and registers support for various WordPress and WooCommerce features.
 *
 * @since 1.0.0
 */
function skyy_rose_collection_setup() {
	// Make theme available for translation
	load_theme_textdomain('skyy-rose-collection', get_template_directory() . '/languages');

	// Add default posts and comments RSS feed links to head
	add_theme_support('automatic-feed-links');

	// Let WordPress manage the document title
	add_theme_support('title-tag');

	// Enable support for Post Thumbnails on posts and pages
	add_theme_support('post-thumbnails');

	// Set default thumbnail size for luxury product images
	set_post_thumbnail_size(600, 600, true);

	// Add custom image sizes for luxury eCommerce
	add_image_size('luxury-product-thumb', 300, 300, true);
	add_image_size('luxury-product-medium', 600, 600, true);
	add_image_size('luxury-product-large', 1200, 1200, true);
	add_image_size('luxury-hero', 1920, 800, true);
	add_image_size('luxury-gallery', 800, 600, true);

	// Register navigation menus
	register_nav_menus(array(
		'primary' => esc_html__('Primary Menu', 'wp-mastery-woocommerce-luxury'),
		'footer'  => esc_html__('Footer Menu', 'wp-mastery-woocommerce-luxury'),
		'account' => esc_html__('Account Menu', 'wp-mastery-woocommerce-luxury'),
	));

	// Switch default core markup to output valid HTML5
	add_theme_support('html5', array(
		'search-form',
		'comment-form',
		'comment-list',
		'gallery',
		'caption',
		'style',
		'script',
	));

	// Add theme support for selective refresh for widgets
	add_theme_support('customize-selective-refresh-widgets');

	// Add support for custom logo
	add_theme_support('custom-logo', array(
		'height'      => 120,
		'width'       => 400,
		'flex-height' => true,
		'flex-width'  => true,
	));

	// Add support for custom background
	add_theme_support('custom-background', array(
		'default-color' => 'ffffff',
	));

	// Add support for editor styles
	add_theme_support('editor-styles');
	add_editor_style('style.css');

	// Add support for responsive embeds
	add_theme_support('responsive-embeds');

	// Add support for wide alignment
	add_theme_support('align-wide');

	// WooCommerce theme support
	add_theme_support('woocommerce', array(
		'thumbnail_image_width' => 300,
		'single_image_width'    => 600,
		'product_grid'          => array(
			'default_rows'    => 4,
			'min_rows'        => 2,
			'max_rows'        => 8,
			'default_columns' => 3,
			'min_columns'     => 2,
			'max_columns'     => 4,
		),
	));

	// WooCommerce gallery features
	add_theme_support('wc-product-gallery-zoom');
	add_theme_support('wc-product-gallery-lightbox');
	add_theme_support('wc-product-gallery-slider');

	// Add support for editor color palette (luxury colors)
	add_theme_support('editor-color-palette', array(
		array(
			'name'  => esc_html__('Luxury Black', 'wp-mastery-woocommerce-luxury'),
			'slug'  => 'luxury-black',
			'color' => '#1a1a1a',
		),
		array(
			'name'  => esc_html__('Luxury Gold', 'wp-mastery-woocommerce-luxury'),
			'slug'  => 'luxury-gold',
			'color' => '#d4af37',
		),
		array(
			'name'  => esc_html__('Luxury Rose Gold', 'wp-mastery-woocommerce-luxury'),
			'slug'  => 'luxury-rose-gold',
			'color' => '#e8b4a0',
		),
		array(
			'name'  => esc_html__('Luxury Silver', 'wp-mastery-woocommerce-luxury'),
			'slug'  => 'luxury-silver',
			'color' => '#c0c0c0',
		),
		array(
			'name'  => esc_html__('Luxury Cream', 'wp-mastery-woocommerce-luxury'),
			'slug'  => 'luxury-cream',
			'color' => '#f8f6f0',
		),
	));

	// Add support for editor font sizes
	add_theme_support('editor-font-sizes', array(
		array(
			'name' => esc_html__('Small', 'wp-mastery-woocommerce-luxury'),
			'size' => 14,
			'slug' => 'small'
		),
		array(
			'name' => esc_html__('Regular', 'wp-mastery-woocommerce-luxury'),
			'size' => 16,
			'slug' => 'regular'
		),
		array(
			'name' => esc_html__('Large', 'wp-mastery-woocommerce-luxury'),
			'size' => 20,
			'slug' => 'large'
		),
		array(
			'name' => esc_html__('Extra Large', 'wp-mastery-woocommerce-luxury'),
			'size' => 24,
			'slug' => 'extra-large'
		)
	));
}
add_action('after_setup_theme', 'skyy_rose_collection_setup');

/**
 * Set the content width in pixels, based on the theme's design and stylesheet
 *
 * Priority 0 to make it available to lower priority callbacks
 *
 * @since 1.0.0
 * @global int $content_width
 */
function wp_mastery_woocommerce_luxury_content_width() {
	$GLOBALS['content_width'] = apply_filters('wp_mastery_woocommerce_luxury_content_width', 1200);
}
add_action('after_setup_theme', 'wp_mastery_woocommerce_luxury_content_width', 0);

/**
 * Enqueue scripts and styles
 *
 * @since 1.0.0
 */
function wp_mastery_woocommerce_luxury_scripts() {
	// Enqueue Google Fonts
	wp_enqueue_style(
		'wp-mastery-woocommerce-luxury-fonts',
		'https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,300;0,400;0,600;0,700;1,300;1,400&family=Source+Sans+Pro:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&family=Dancing+Script:wght@400;500;600;700&display=swap',
		array(),
		null
	);

	// Enqueue main stylesheet
	wp_enqueue_style(
		'wp-mastery-woocommerce-luxury-style',
		get_stylesheet_uri(),
		array('wp-mastery-woocommerce-luxury-fonts'),
		SKYY_ROSE_COLLECTION_VERSION
	);

	// Enqueue main JavaScript file
	wp_enqueue_script(
		'wp-mastery-woocommerce-luxury-script',
		get_template_directory_uri() . '/assets/js/luxury-ecommerce.js',
		array(),
		SKYY_ROSE_COLLECTION_VERSION,
		true
	);

	// Localize script for AJAX and eCommerce functionality
	wp_localize_script('wp-mastery-woocommerce-luxury-script', 'luxuryEcommerce', array(
		'ajax_url' => admin_url('admin-ajax.php'),
		'nonce' => wp_create_nonce('luxury_ecommerce_nonce'),
		'currency_symbol' => get_woocommerce_currency_symbol(),
		'currency_position' => get_option('woocommerce_currency_pos'),
		'thousand_separator' => wc_get_price_thousand_separator(),
		'decimal_separator' => wc_get_price_decimal_separator(),
		'price_decimals' => wc_get_price_decimals(),
	));

	// Enqueue comment reply script on single posts with comments open and threaded comments
	if (is_singular() && comments_open() && get_option('thread_comments')) {
		wp_enqueue_script('comment-reply');
	}
}
add_action('wp_enqueue_scripts', 'wp_mastery_woocommerce_luxury_scripts');

/**
 * WooCommerce specific enqueues
 *
 * @since 1.0.0
 */
function wp_mastery_woocommerce_luxury_woocommerce_scripts() {
	if (class_exists('WooCommerce')) {
		// Enqueue WooCommerce specific styles
		wp_enqueue_style(
			'wp-mastery-woocommerce-luxury-woocommerce',
			get_template_directory_uri() . '/assets/css/woocommerce-luxury.css',
			array('wp-mastery-woocommerce-luxury-style'),
			SKYY_ROSE_COLLECTION_VERSION
		);

		// Enqueue WooCommerce specific JavaScript
		wp_enqueue_script(
			'wp-mastery-woocommerce-luxury-woocommerce-js',
			get_template_directory_uri() . '/assets/js/woocommerce-luxury.js',
			array('jquery', 'wp-mastery-woocommerce-luxury-script'),
			SKYY_ROSE_COLLECTION_VERSION,
			true
		);
	}
}
add_action('wp_enqueue_scripts', 'wp_mastery_woocommerce_luxury_woocommerce_scripts');

/**
 * Custom excerpt length for luxury product descriptions
 *
 * @since 1.0.0
 * @param int $length Excerpt length.
 * @return int Modified excerpt length.
 */
function wp_mastery_woocommerce_luxury_excerpt_length($length) {
	if (is_shop() || is_product_category() || is_product_tag()) {
		return 20; // Shorter excerpts for product listings
	}
	return 25;
}
add_filter('excerpt_length', 'wp_mastery_woocommerce_luxury_excerpt_length', 999);

/**
 * Custom excerpt more string
 *
 * @since 1.0.0
 * @param string $more "Read More" excerpt string.
 * @return string Modified "Read More" excerpt string.
 */
function wp_mastery_woocommerce_luxury_excerpt_more($more) {
	if (is_admin()) {
		return $more;
	}

	return sprintf(
		'&hellip; <a href="%1$s" class="read-more luxury-accent">%2$s</a>',
		esc_url(get_permalink()),
		esc_html__('Discover More', 'wp-mastery-woocommerce-luxury')
	);
}
add_filter('excerpt_more', 'wp_mastery_woocommerce_luxury_excerpt_more');

/**
 * Add body classes for luxury eCommerce styling
 *
 * @since 1.0.0
 * @param array $classes Classes for the body element.
 * @return array Modified body classes.
 */
function wp_mastery_woocommerce_luxury_body_classes($classes) {
	// Add class for when there is a custom header image
	if (get_header_image()) {
		$classes[] = 'has-header-image';
	}

	// Add class for when there is a custom logo
	if (has_custom_logo()) {
		$classes[] = 'has-custom-logo';
	}

	// Add luxury theme class
	$classes[] = 'luxury-theme';
	$classes[] = 'luxury-ecommerce';

	// Add WooCommerce specific classes
	if (class_exists('WooCommerce')) {
		if (is_woocommerce() || is_cart() || is_checkout() || is_account_page()) {
			$classes[] = 'woocommerce-active';
		}

		if (is_shop()) {
			$classes[] = 'luxury-shop';
		}

		if (is_product()) {
			$classes[] = 'luxury-product';
		}

		if (is_product_category() || is_product_tag()) {
			$classes[] = 'luxury-product-archive';
		}

		if (is_cart()) {
			$classes[] = 'luxury-cart';
		}

		if (is_checkout()) {
			$classes[] = 'luxury-checkout';
		}

		if (is_account_page()) {
			$classes[] = 'luxury-account';
		}
	}

	return $classes;
}
add_filter('body_class', 'wp_mastery_woocommerce_luxury_body_classes');

/**
 * Fallback menu for primary navigation
 *
 * @since 1.0.0
 */
function wp_mastery_woocommerce_luxury_fallback_menu() {
	echo '<ul class="fallback-menu">';
	echo '<li><a href="' . esc_url(home_url('/')) . '">' . esc_html__('Home', 'wp-mastery-woocommerce-luxury') . '</a></li>';
	
	// Add shop link if WooCommerce is active
	if (class_exists('WooCommerce')) {
		echo '<li><a href="' . esc_url(wc_get_page_permalink('shop')) . '">' . esc_html__('Shop', 'wp-mastery-woocommerce-luxury') . '</a></li>';
	}
	
	// Show pages in menu if no custom menu is set
	$pages = get_pages(array(
		'sort_column' => 'menu_order',
		'number' => 4,
	));
	
	foreach ($pages as $page) {
		echo '<li><a href="' . esc_url(get_permalink($page->ID)) . '">' . esc_html($page->post_title) . '</a></li>';
	}
	
	// Add account link if WooCommerce is active
	if (class_exists('WooCommerce')) {
		echo '<li><a href="' . esc_url(wc_get_page_permalink('myaccount')) . '">' . esc_html__('Account', 'wp-mastery-woocommerce-luxury') . '</a></li>';
	}
	
	echo '</ul>';
}

/**
 * Safe function to get theme option with fallback
 *
 * @since 1.0.0
 * @param string $option_name Option name.
 * @param mixed  $default Default value.
 * @return mixed Option value or default.
 */
function wp_mastery_woocommerce_luxury_get_option($option_name, $default = '') {
	$option_value = get_theme_mod($option_name, $default);
	
	// Sanitize based on option type
	if (is_string($option_value)) {
		return sanitize_text_field($option_value);
	}
	
	return $option_value;
}

/**
 * WordPress.com compatibility check
 *
 * @since 1.0.0
 * @return bool True if running on WordPress.com.
 */
function wp_mastery_woocommerce_luxury_is_wpcom() {
	return defined('IS_WPCOM') && IS_WPCOM;
}

/**
 * Check if WooCommerce is active
 *
 * @since 1.0.0
 * @return bool True if WooCommerce is active.
 */
function wp_mastery_woocommerce_luxury_is_woocommerce_active() {
	return class_exists('WooCommerce');
}

/**
 * Theme activation hook
 *
 * @since 1.0.0
 */
function wp_mastery_woocommerce_luxury_activation() {
	// Flush rewrite rules
	flush_rewrite_rules();
	
	// Set default theme options for luxury eCommerce
	if (!get_theme_mod('custom_logo')) {
		// Set default customizer values if needed
	}

	// Create WooCommerce pages if WooCommerce is active
	if (wp_mastery_woocommerce_luxury_is_woocommerce_active()) {
		// WooCommerce will handle page creation
	}
}
add_action('after_switch_theme', 'wp_mastery_woocommerce_luxury_activation');

/**
 * Theme deactivation hook
 *
 * @since 1.0.0
 */
function wp_mastery_woocommerce_luxury_deactivation() {
	// Clean up theme-specific options if needed
	flush_rewrite_rules();
}
add_action('switch_theme', 'wp_mastery_woocommerce_luxury_deactivation');

/**
 * AI-POWERED ECOMMERCE FEATURES
 * Advanced functionality for luxury product analysis and personalization
 */

/**
 * Initialize AI services integration
 *
 * @since 1.0.0
 */
function wp_mastery_woocommerce_luxury_init_ai_services() {
	// Register AI service endpoints
	add_action('wp_ajax_luxury_ai_analyze_product', 'wp_mastery_woocommerce_luxury_ajax_analyze_product');
	add_action('wp_ajax_nopriv_luxury_ai_analyze_product', 'wp_mastery_woocommerce_luxury_ajax_analyze_product');

	add_action('wp_ajax_luxury_ai_get_recommendations', 'wp_mastery_woocommerce_luxury_ajax_get_recommendations');
	add_action('wp_ajax_nopriv_luxury_ai_get_recommendations', 'wp_mastery_woocommerce_luxury_ajax_get_recommendations');

	add_action('wp_ajax_luxury_ai_update_customer_segment', 'wp_mastery_woocommerce_luxury_ajax_update_customer_segment');
	add_action('wp_ajax_luxury_ai_update_customer_segment', 'wp_mastery_woocommerce_luxury_ajax_update_customer_segment');

	add_action('wp_ajax_luxury_ai_get_dynamic_pricing', 'wp_mastery_woocommerce_luxury_ajax_get_dynamic_pricing');
	add_action('wp_ajax_nopriv_luxury_ai_get_dynamic_pricing', 'wp_mastery_woocommerce_luxury_ajax_get_dynamic_pricing');
}
add_action('init', 'wp_mastery_woocommerce_luxury_init_ai_services');

/**
 * Get customer segment for personalization
 *
 * @since 1.0.0
 * @return string Customer segment identifier
 */
function wp_mastery_woocommerce_luxury_get_customer_segment() {
	$customer_id = get_current_user_id();

	if ($customer_id) {
		$segment = get_user_meta($customer_id, 'luxury_customer_segment', true);
		if ($segment) {
			return sanitize_text_field($segment);
		}
	}

	// Default segment based on session data
	$session_segment = WC()->session->get('luxury_customer_segment');
	if ($session_segment) {
		return sanitize_text_field($session_segment);
	}

	return 'new_visitor';
}

/**
 * AJAX handler for product analysis
 *
 * @since 1.0.0
 */
function wp_mastery_woocommerce_luxury_ajax_analyze_product() {
	// Verify nonce
	if (!wp_verify_nonce($_POST['nonce'], 'luxury_ai_nonce')) {
		wp_die('Security check failed');
	}

	$product_id = intval($_POST['product_id']);
	$product = wc_get_product($product_id);

	if (!$product) {
		wp_send_json_error('Product not found');
		return;
	}

	try {
		// Call Docker AI service for product analysis
		$analysis_result = wp_mastery_woocommerce_luxury_call_ai_service('analyze_product', array(
			'product_id' => $product_id,
			'product_images' => wp_mastery_woocommerce_luxury_get_product_images($product),
			'product_description' => $product->get_description(),
			'product_attributes' => $product->get_attributes(),
		));

		if ($analysis_result && !is_wp_error($analysis_result)) {
			// Cache the analysis results
			update_post_meta($product_id, '_luxury_ai_analysis', $analysis_result);
			update_post_meta($product_id, '_luxury_ai_analysis_timestamp', time());

			wp_send_json_success($analysis_result);
		} else {
			wp_send_json_error('AI analysis failed');
		}

	} catch (Exception $e) {
		error_log('Luxury AI Analysis Error: ' . $e->getMessage());
		wp_send_json_error('Analysis service unavailable');
	}
}

/**
 * AJAX handler for getting product recommendations
 *
 * @since 1.0.0
 */
function wp_mastery_woocommerce_luxury_ajax_get_recommendations() {
	// Verify nonce
	if (!wp_verify_nonce($_POST['nonce'], 'luxury_ai_nonce')) {
		wp_die('Security check failed');
	}

	$product_id = intval($_POST['product_id']);
	$customer_segment = sanitize_text_field($_POST['customer_segment']);
	$recommendation_type = sanitize_text_field($_POST['type']); // 'related', 'cross_sell', 'upsell'

	try {
		// Call Docker AI service for recommendations
		$recommendations = wp_mastery_woocommerce_luxury_call_ai_service('get_recommendations', array(
			'product_id' => $product_id,
			'customer_segment' => $customer_segment,
			'recommendation_type' => $recommendation_type,
			'customer_history' => wp_mastery_woocommerce_luxury_get_customer_history(),
		));

		if ($recommendations && !is_wp_error($recommendations)) {
			wp_send_json_success($recommendations);
		} else {
			wp_send_json_error('Recommendations unavailable');
		}

	} catch (Exception $e) {
		error_log('Luxury AI Recommendations Error: ' . $e->getMessage());
		wp_send_json_error('Recommendation service unavailable');
	}
}

/**
 * AJAX handler for updating customer segment
 *
 * @since 1.0.0
 */
function wp_mastery_woocommerce_luxury_ajax_update_customer_segment() {
	// Verify nonce
	if (!wp_verify_nonce($_POST['nonce'], 'luxury_ai_nonce')) {
		wp_die('Security check failed');
	}

	$behavior_data = array(
		'viewed_products' => array_map('intval', $_POST['viewed_products']),
		'time_on_page' => intval($_POST['time_on_page']),
		'interactions' => sanitize_text_field($_POST['interactions']),
		'price_range_interest' => sanitize_text_field($_POST['price_range']),
	);

	try {
		// Call Docker AI service for customer segmentation
		$segment_result = wp_mastery_woocommerce_luxury_call_ai_service('update_customer_segment', array(
			'customer_id' => get_current_user_id(),
			'behavior_data' => $behavior_data,
			'current_segment' => wp_mastery_woocommerce_luxury_get_customer_segment(),
		));

		if ($segment_result && !is_wp_error($segment_result)) {
			// Update customer segment
			$new_segment = $segment_result['segment'];

			if (get_current_user_id()) {
				update_user_meta(get_current_user_id(), 'luxury_customer_segment', $new_segment);
			} else {
				WC()->session->set('luxury_customer_segment', $new_segment);
			}

			wp_send_json_success(array('segment' => $new_segment));
		} else {
			wp_send_json_error('Segmentation update failed');
		}

	} catch (Exception $e) {
		error_log('Luxury AI Segmentation Error: ' . $e->getMessage());
		wp_send_json_error('Segmentation service unavailable');
	}
}

/**
 * AJAX handler for dynamic pricing
 *
 * @since 1.0.0
 */
function wp_mastery_woocommerce_luxury_ajax_get_dynamic_pricing() {
	// Verify nonce
	if (!wp_verify_nonce($_POST['nonce'], 'luxury_ai_nonce')) {
		wp_die('Security check failed');
	}

	$product_id = intval($_POST['product_id']);
	$customer_segment = sanitize_text_field($_POST['customer_segment']);

	try {
		// Call Docker AI service for dynamic pricing
		$pricing_result = wp_mastery_woocommerce_luxury_call_ai_service('get_dynamic_pricing', array(
			'product_id' => $product_id,
			'customer_segment' => $customer_segment,
			'inventory_level' => wp_mastery_woocommerce_luxury_get_inventory_level($product_id),
			'demand_metrics' => wp_mastery_woocommerce_luxury_get_demand_metrics($product_id),
		));

		if ($pricing_result && !is_wp_error($pricing_result)) {
			wp_send_json_success($pricing_result);
		} else {
			wp_send_json_error('Dynamic pricing unavailable');
		}

	} catch (Exception $e) {
		error_log('Luxury AI Pricing Error: ' . $e->getMessage());
		wp_send_json_error('Pricing service unavailable');
	}
}

/**
 * DOCKER AI SERVICE INTEGRATION
 * Core functions for communicating with Docker-containerized AI services
 */

/**
 * Call Docker AI service
 *
 * @since 1.0.0
 * @param string $service_endpoint Service endpoint name
 * @param array $data Data to send to service
 * @return array|WP_Error Service response or error
 */
function wp_mastery_woocommerce_luxury_call_ai_service($service_endpoint, $data) {
	$docker_endpoint = get_option('luxury_docker_endpoint', 'http://localhost:8080');
	$api_key = get_option('luxury_ai_api_key', '');

	if (empty($docker_endpoint) || empty($api_key)) {
		return new WP_Error('config_error', 'AI service not configured');
	}

	$url = trailingslashit($docker_endpoint) . 'api/v1/' . $service_endpoint;

	$args = array(
		'method' => 'POST',
		'timeout' => 30,
		'headers' => array(
			'Content-Type' => 'application/json',
			'Authorization' => 'Bearer ' . $api_key,
			'X-WordPress-Site' => home_url(),
		),
		'body' => wp_json_encode($data),
	);

	$response = wp_remote_request($url, $args);

	if (is_wp_error($response)) {
		error_log('Docker AI Service Error: ' . $response->get_error_message());
		return $response;
	}

	$response_code = wp_remote_retrieve_response_code($response);
	$response_body = wp_remote_retrieve_body($response);

	if ($response_code !== 200) {
		error_log('Docker AI Service HTTP Error: ' . $response_code . ' - ' . $response_body);
		return new WP_Error('service_error', 'AI service returned error: ' . $response_code);
	}

	$decoded_response = json_decode($response_body, true);

	if (json_last_error() !== JSON_ERROR_NONE) {
		error_log('Docker AI Service JSON Error: ' . json_last_error_msg());
		return new WP_Error('json_error', 'Invalid JSON response from AI service');
	}

	return $decoded_response;
}

/**
 * Get product images for AI analysis
 *
 * @since 1.0.0
 * @param WC_Product $product Product object
 * @return array Array of image URLs and metadata
 */
function wp_mastery_woocommerce_luxury_get_product_images($product) {
	$images = array();

	// Main product image
	$main_image_id = $product->get_image_id();
	if ($main_image_id) {
		$images['main'] = array(
			'url' => wp_get_attachment_image_url($main_image_id, 'luxury-product-large'),
			'alt' => get_post_meta($main_image_id, '_wp_attachment_image_alt', true),
			'metadata' => wp_get_attachment_metadata($main_image_id),
		);
	}

	// Gallery images
	$gallery_image_ids = $product->get_gallery_image_ids();
	$images['gallery'] = array();

	foreach ($gallery_image_ids as $image_id) {
		$images['gallery'][] = array(
			'url' => wp_get_attachment_image_url($image_id, 'luxury-product-large'),
			'alt' => get_post_meta($image_id, '_wp_attachment_image_alt', true),
			'metadata' => wp_get_attachment_metadata($image_id),
		);
	}

	return $images;
}

/**
 * Get customer purchase history for AI analysis
 *
 * @since 1.0.0
 * @return array Customer history data
 */
function wp_mastery_woocommerce_luxury_get_customer_history() {
	$customer_id = get_current_user_id();
	$history = array();

	if ($customer_id) {
		$orders = wc_get_orders(array(
			'customer_id' => $customer_id,
			'status' => array('completed', 'processing'),
			'limit' => 10,
		));

		foreach ($orders as $order) {
			$order_data = array(
				'order_id' => $order->get_id(),
				'date' => $order->get_date_created()->format('Y-m-d'),
				'total' => $order->get_total(),
				'items' => array(),
			);

			foreach ($order->get_items() as $item) {
				$product = $item->get_product();
				if ($product) {
					$order_data['items'][] = array(
						'product_id' => $product->get_id(),
						'name' => $product->get_name(),
						'price' => $item->get_total(),
						'quantity' => $item->get_quantity(),
					);
				}
			}

			$history[] = $order_data;
		}
	}

	return $history;
}

/**
 * Get inventory level for dynamic pricing
 *
 * @since 1.0.0
 * @param int $product_id Product ID
 * @return array Inventory data
 */
function wp_mastery_woocommerce_luxury_get_inventory_level($product_id) {
	$product = wc_get_product($product_id);

	if (!$product) {
		return array();
	}

	return array(
		'stock_quantity' => $product->get_stock_quantity(),
		'stock_status' => $product->get_stock_status(),
		'manage_stock' => $product->get_manage_stock(),
		'low_stock_threshold' => $product->get_low_stock_amount(),
	);
}

/**
 * Get demand metrics for dynamic pricing
 *
 * @since 1.0.0
 * @param int $product_id Product ID
 * @return array Demand metrics
 */
function wp_mastery_woocommerce_luxury_get_demand_metrics($product_id) {
	// Get view count (if tracking plugin is available)
	$view_count = get_post_meta($product_id, '_luxury_view_count', true) ?: 0;

	// Get recent sales data
	$recent_sales = wp_mastery_woocommerce_luxury_get_recent_sales($product_id);

	// Get wishlist/favorites count (if available)
	$wishlist_count = get_post_meta($product_id, '_luxury_wishlist_count', true) ?: 0;

	return array(
		'view_count' => intval($view_count),
		'recent_sales' => $recent_sales,
		'wishlist_count' => intval($wishlist_count),
		'conversion_rate' => wp_mastery_woocommerce_luxury_calculate_conversion_rate($product_id),
	);
}

/**
 * Get recent sales data for a product
 *
 * @since 1.0.0
 * @param int $product_id Product ID
 * @return array Recent sales data
 */
function wp_mastery_woocommerce_luxury_get_recent_sales($product_id) {
	$orders = wc_get_orders(array(
		'status' => array('completed', 'processing'),
		'date_created' => '>' . (time() - (30 * DAY_IN_SECONDS)), // Last 30 days
		'limit' => -1,
	));

	$sales_data = array(
		'total_quantity' => 0,
		'total_revenue' => 0,
		'order_count' => 0,
	);

	foreach ($orders as $order) {
		foreach ($order->get_items() as $item) {
			if ($item->get_product_id() == $product_id) {
				$sales_data['total_quantity'] += $item->get_quantity();
				$sales_data['total_revenue'] += $item->get_total();
				$sales_data['order_count']++;
			}
		}
	}

	return $sales_data;
}

/**
 * Calculate conversion rate for a product
 *
 * @since 1.0.0
 * @param int $product_id Product ID
 * @return float Conversion rate
 */
function wp_mastery_woocommerce_luxury_calculate_conversion_rate($product_id) {
	$view_count = get_post_meta($product_id, '_luxury_view_count', true) ?: 0;
	$recent_sales = wp_mastery_woocommerce_luxury_get_recent_sales($product_id);

	if ($view_count > 0) {
		return ($recent_sales['order_count'] / $view_count) * 100;
	}

	return 0;
}

/**
 * SKYY ROSE COLLECTION BRAND INTEGRATION
 * Authentic brand assets and visual identity implementation
 */

/**
 * Get account menu item icons
 *
 * @since 1.0.0
 * @param string $endpoint Menu endpoint
 * @return string Icon HTML
 */
function wp_mastery_woocommerce_luxury_get_account_icon($endpoint) {
	$icons = array(
		'dashboard'          => '🏠',
		'orders'            => '📦',
		'downloads'         => '⬇️',
		'edit-address'      => '📍',
		'edit-account'      => '👤',
		'customer-logout'   => '🚪',
		'payment-methods'   => '💳',
		'wishlist'          => '💝',
		'rewards'           => '⭐',
		'subscriptions'     => '🔄',
	);

	return isset($icons[$endpoint]) ? $icons[$endpoint] : '📋';
}

/**
 * Enqueue Skyy Rose Collection assets
 *
 * @since 1.0.0
 */
function wp_mastery_woocommerce_luxury_enqueue_skyy_rose_assets() {
	// Enqueue checkout JavaScript
	if (is_checkout() || is_cart() || is_account_page()) {
		wp_enqueue_script(
			'skyy-rose-checkout',
			get_template_directory_uri() . '/assets/js/skyy-rose-checkout.js',
			array('jquery', 'luxury-ai-services'),
			wp_get_theme()->get('Version'),
			true
		);

		// Localize script with Skyy Rose Collection data
		wp_localize_script('skyy-rose-checkout', 'skyyRoseConfig', array(
			'ajax_url' => admin_url('admin-ajax.php'),
			'nonce' => wp_create_nonce('skyy_rose_nonce'),
			'brand_name' => 'Skyy Rose Collection',
			'currency_symbol' => get_woocommerce_currency_symbol(),
			'checkout_url' => wc_get_checkout_url(),
			'cart_url' => wc_get_cart_url(),
			'shop_url' => wc_get_page_permalink('shop'),
			'account_url' => wc_get_page_permalink('myaccount'),
		));
	}
}
add_action('wp_enqueue_scripts', 'wp_mastery_woocommerce_luxury_enqueue_skyy_rose_assets');

/**
 * Add Skyy Rose Collection body classes
 *
 * @since 1.0.0
 * @param array $classes Existing body classes
 * @return array Modified body classes
 */
function wp_mastery_woocommerce_luxury_skyy_rose_body_classes($classes) {
	// Add brand-specific classes
	$classes[] = 'skyy-rose-collection';
	$classes[] = 'luxury-theme';

	// Add page-specific classes
	if (is_shop()) {
		$classes[] = 'skyy-rose-shop';
	}

	if (is_product()) {
		$classes[] = 'skyy-rose-product';
	}

	if (is_cart()) {
		$classes[] = 'skyy-rose-cart';
	}

	if (is_checkout()) {
		$classes[] = 'skyy-rose-checkout';
	}

	if (is_account_page()) {
		$classes[] = 'skyy-rose-account';
	}

	// Add customer segment class
	$customer_segment = wp_mastery_woocommerce_luxury_get_customer_segment();
	if ($customer_segment) {
		$classes[] = 'customer-segment-' . sanitize_html_class($customer_segment);
	}

	return $classes;
}
add_filter('body_class', 'wp_mastery_woocommerce_luxury_skyy_rose_body_classes');

/**
 * AJAX handler for cart analysis
 *
 * @since 1.0.0
 */
function wp_mastery_woocommerce_luxury_ajax_analyze_cart() {
	// Verify nonce
	if (!wp_verify_nonce($_POST['nonce'], 'skyy_rose_nonce')) {
		wp_die('Security check failed');
	}

	$cart_items = json_decode(stripslashes($_POST['cart_items']), true);
	$cart_total = floatval($_POST['cart_total']);
	$customer_segment = sanitize_text_field($_POST['customer_segment']);

	try {
		// Call Docker AI service for cart analysis
		$analysis_result = wp_mastery_woocommerce_luxury_call_ai_service('analyze_cart', array(
			'cart_items' => $cart_items,
			'cart_total' => $cart_total,
			'customer_segment' => $customer_segment,
		));

		if ($analysis_result && !is_wp_error($analysis_result)) {
			wp_send_json_success($analysis_result);
		} else {
			wp_send_json_error('Cart analysis failed');
		}

	} catch (Exception $e) {
		error_log('Skyy Rose Cart Analysis Error: ' . $e->getMessage());
		wp_send_json_error('Analysis service unavailable');
	}
}
add_action('wp_ajax_luxury_ai_analyze_cart', 'wp_mastery_woocommerce_luxury_ajax_analyze_cart');
add_action('wp_ajax_nopriv_luxury_ai_analyze_cart', 'wp_mastery_woocommerce_luxury_ajax_analyze_cart');

/**
 * AJAX handler for checkout recommendations
 *
 * @since 1.0.0
 */
function wp_mastery_woocommerce_luxury_ajax_get_checkout_recommendations() {
	// Verify nonce
	if (!wp_verify_nonce($_POST['nonce'], 'skyy_rose_nonce')) {
		wp_die('Security check failed');
	}

	$cart_items = json_decode(stripslashes($_POST['cart_items']), true);
	$customer_segment = sanitize_text_field($_POST['customer_segment']);
	$checkout_stage = sanitize_text_field($_POST['checkout_stage']);

	try {
		// Call Docker AI service for checkout recommendations
		$recommendations = wp_mastery_woocommerce_luxury_call_ai_service('get_checkout_recommendations', array(
			'cart_items' => $cart_items,
			'customer_segment' => $customer_segment,
			'checkout_stage' => $checkout_stage,
		));

		if ($recommendations && !is_wp_error($recommendations)) {
			wp_send_json_success($recommendations);
		} else {
			wp_send_json_error('Recommendations unavailable');
		}

	} catch (Exception $e) {
		error_log('Skyy Rose Checkout Recommendations Error: ' . $e->getMessage());
		wp_send_json_error('Recommendation service unavailable');
	}
}
add_action('wp_ajax_luxury_ai_get_checkout_recommendations', 'wp_mastery_woocommerce_luxury_ajax_get_checkout_recommendations');
add_action('wp_ajax_nopriv_luxury_ai_get_checkout_recommendations', 'wp_mastery_woocommerce_luxury_ajax_get_checkout_recommendations');

/**
 * AJAX handler for address validation
 *
 * @since 1.0.0
 */
function wp_mastery_woocommerce_luxury_ajax_validate_address() {
	// Verify nonce
	if (!wp_verify_nonce($_POST['nonce'], 'skyy_rose_nonce')) {
		wp_die('Security check failed');
	}

	$address_data = array(
		'address_1' => sanitize_text_field($_POST['address_1']),
		'city' => sanitize_text_field($_POST['city']),
		'postcode' => sanitize_text_field($_POST['postcode']),
		'country' => sanitize_text_field($_POST['country']),
	);

	try {
		// Call Docker AI service for address validation
		$validation_result = wp_mastery_woocommerce_luxury_call_ai_service('validate_address', $address_data);

		if ($validation_result && !is_wp_error($validation_result)) {
			wp_send_json_success($validation_result);
		} else {
			wp_send_json_error('Address validation failed');
		}

	} catch (Exception $e) {
		error_log('Skyy Rose Address Validation Error: ' . $e->getMessage());
		wp_send_json_error('Validation service unavailable');
	}
}
add_action('wp_ajax_luxury_ai_validate_address', 'wp_mastery_woocommerce_luxury_ajax_validate_address');
add_action('wp_ajax_nopriv_luxury_ai_validate_address', 'wp_mastery_woocommerce_luxury_ajax_validate_address');
