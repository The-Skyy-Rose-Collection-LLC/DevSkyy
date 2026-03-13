<?php
/**
 * Klaviyo Integration
 *
 * Connects SkyyRose email capture and WooCommerce events to Klaviyo's API v3.
 * API credentials are stored as WordPress options so they can be configured
 * via WP-CLI or the admin panel without touching code.
 *
 * Required options (set via WP-CLI or Options API):
 *   skyyrose_klaviyo_private_key  — Klaviyo private API key (sk_live_...)
 *   skyyrose_klaviyo_public_key   — Klaviyo public / site ID (6-char alphanumeric)
 *
 * List ID options (configure via WP-CLI after creating lists in Klaviyo):
 *   skyyrose_klaviyo_list_general        — General newsletter list
 *   skyyrose_klaviyo_list_black_rose     — Black Rose drop waitlist
 *   skyyrose_klaviyo_list_love_hurts     — Love Hurts drop waitlist
 *   skyyrose_klaviyo_list_signature      — Signature drop waitlist
 *   skyyrose_klaviyo_list_jersey_vip     — Jersey Series VIP list
 *
 * @package SkyyRose_Flagship
 * @since   5.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/*--------------------------------------------------------------
 * Klaviyo API Client
 *--------------------------------------------------------------*/

/**
 * Subscribe an email to a Klaviyo list.
 *
 * Uses Klaviyo Profiles API v3 (2024-02-15 revision).
 * Silently no-ops when no API key is configured so the site
 * continues to function before Klaviyo is set up.
 *
 * @since 5.0.0
 *
 * @param string $email       Valid email address.
 * @param string $list_id     Klaviyo list ID (e.g. "YcHFBE").
 * @param array  $properties  Optional profile properties (first_name, phone_number, etc.).
 * @return bool True on success, false on failure.
 */
function skyyrose_klaviyo_subscribe_to_list( $email, $list_id, $properties = array() ) {

	$private_key = get_option( 'skyyrose_klaviyo_private_key', '' );

	// No-op if not configured — prevents fatal errors during Klaviyo setup.
	if ( empty( $private_key ) || empty( $list_id ) || ! is_email( $email ) ) {
		return false;
	}

	$profile_attrs = array_merge(
		array( 'email' => $email ),
		array_intersect_key(
			$properties,
			array_flip( array( 'first_name', 'last_name', 'phone_number', 'organization', 'title', 'location' ) )
		)
	);

	$profile_attrs['subscriptions'] = array(
		'email' => array(
			'marketing' => array(
				'consent' => 'SUBSCRIBED',
			),
		),
	);

	$body = wp_json_encode( array(
		'data' => array(
			'type'       => 'profile-subscription-bulk-create-job',
			'attributes' => array(
				'profiles'          => array(
					'data' => array(
						array(
							'type'       => 'profile',
							'attributes' => $profile_attrs,
						),
					),
				),
				'historical_import' => false,
			),
			'relationships' => array(
				'list' => array(
					'data' => array(
						'type' => 'list',
						'id'   => $list_id,
					),
				),
			),
		),
	) );

	$response = wp_remote_post(
		'https://a.klaviyo.com/api/profile-subscription-bulk-create-jobs/',
		array(
			'headers' => array(
				'Authorization' => 'Klaviyo-API-Key ' . $private_key,
				'Content-Type'  => 'application/json',
				'Accept'        => 'application/json',
				'revision'      => '2024-02-15',
			),
			'body'    => $body,
			'timeout' => 10,
		)
	);

	if ( is_wp_error( $response ) ) {
		// Log for server-side debugging without exposing to clients.
		error_log( '[SkyyRose Klaviyo] Subscribe error: ' . $response->get_error_message() );
		return false;
	}

	$code = wp_remote_retrieve_response_code( $response );

	// Klaviyo returns 202 Accepted for bulk subscription jobs.
	return $code >= 200 && $code < 300;
}

/**
 * Get a Klaviyo list ID by slug.
 *
 * @since 5.0.0
 *
 * @param string $slug  One of: general, black_rose, love_hurts, signature, jersey_vip.
 * @return string Klaviyo list ID, or empty string if not configured.
 */
function skyyrose_klaviyo_list_id( $slug ) {
	$option_map = array(
		'general'    => 'skyyrose_klaviyo_list_general',
		'black_rose' => 'skyyrose_klaviyo_list_black_rose',
		'love_hurts' => 'skyyrose_klaviyo_list_love_hurts',
		'signature'  => 'skyyrose_klaviyo_list_signature',
		'jersey_vip' => 'skyyrose_klaviyo_list_jersey_vip',
	);

	if ( ! isset( $option_map[ $slug ] ) ) {
		return '';
	}

	return get_option( $option_map[ $slug ], '' );
}

/*--------------------------------------------------------------
 * Hook: Newsletter Signup → Klaviyo General List
 *--------------------------------------------------------------*/

/**
 * Forward general newsletter signups to Klaviyo.
 *
 * Fires on the `skyyrose_newsletter_signup` action hook,
 * which is triggered by the ajax-handlers.php newsletter endpoint.
 *
 * @since 5.0.0
 *
 * @param string $email Sanitized subscriber email.
 * @return void
 */
function skyyrose_klaviyo_on_newsletter_signup( $email ) {
	$list_id = skyyrose_klaviyo_list_id( 'general' );
	skyyrose_klaviyo_subscribe_to_list( $email, $list_id );
}
add_action( 'skyyrose_newsletter_signup', 'skyyrose_klaviyo_on_newsletter_signup' );

/*--------------------------------------------------------------
 * Hook: Incentive Popup Signup → Klaviyo General + VIP Lists
 *--------------------------------------------------------------*/

/**
 * Forward incentive popup signups to Klaviyo (general + VIP lists).
 *
 * @since 5.0.0
 *
 * @param string $email Sanitized email.
 * @param string $phone Sanitized phone number (may be empty).
 * @return void
 */
function skyyrose_klaviyo_on_incentive_signup( $email, $phone = '' ) {
	$properties = array();
	if ( ! empty( $phone ) ) {
		$properties['phone_number'] = $phone;
	}

	$general_list = skyyrose_klaviyo_list_id( 'general' );
	skyyrose_klaviyo_subscribe_to_list( $email, $general_list, $properties );
}
add_action( 'skyyrose_incentive_signup', 'skyyrose_klaviyo_on_incentive_signup', 10, 2 );

/*--------------------------------------------------------------
 * AJAX: Generic Klaviyo Subscribe Endpoint
 *
 * Accepts email + optional list_slug parameter so the JS engines
 * can target collection-specific waitlists (exit-intent, inline
 * capture, collection pages). Uses the standard skyyrose-nonce
 * that is already localized via skyyRoseData.nonce.
 *--------------------------------------------------------------*/

/**
 * Handle AJAX subscribe request from front-end engines.
 *
 * Posted fields:
 *   nonce      — skyyrose-nonce (from skyyRoseData.nonce)
 *   email      — subscriber email
 *   list_slug  — optional: general|black_rose|love_hurts|signature|jersey_vip
 *   first_name — optional
 *   phone      — optional
 *
 * @since 5.0.0
 * @return void
 */
function skyyrose_ajax_klaviyo_subscribe() {

	// Verify the standard site nonce.
	if ( ! isset( $_POST['nonce'] ) ||
		! wp_verify_nonce( sanitize_text_field( wp_unslash( $_POST['nonce'] ) ), 'skyyrose-nonce' ) ) {
		wp_send_json_error( array( 'message' => esc_html__( 'Security check failed.', 'skyyrose-flagship' ) ) );
		return;
	}

	$email = sanitize_email( wp_unslash( $_POST['email'] ?? '' ) );
	if ( ! is_email( $email ) ) {
		wp_send_json_error( array( 'message' => esc_html__( 'Please enter a valid email address.', 'skyyrose-flagship' ) ) );
		return;
	}

	// Rate limiting: 5 requests per email per 15 minutes.
	$rate_key = 'skyyrose_klav_' . md5( strtolower( trim( $email ) ) );
	$attempts = (int) get_transient( $rate_key );
	if ( $attempts >= 5 ) {
		wp_send_json_error( array( 'message' => esc_html__( 'Too many requests. Please try again later.', 'skyyrose-flagship' ) ) );
		return;
	}
	set_transient( $rate_key, $attempts + 1, 15 * MINUTE_IN_SECONDS );

	// Build properties.
	$properties = array();
	$first_name = sanitize_text_field( wp_unslash( $_POST['first_name'] ?? '' ) );
	if ( ! empty( $first_name ) ) {
		$properties['first_name'] = mb_substr( $first_name, 0, 100 );
	}
	$phone = sanitize_text_field( wp_unslash( $_POST['phone'] ?? '' ) );
	if ( ! empty( $phone ) ) {
		$properties['phone_number'] = mb_substr( $phone, 0, 30 );
	}

	// Resolve list ID — default to general.
	$list_slug   = sanitize_key( wp_unslash( $_POST['list_slug'] ?? 'general' ) );
	$allowed_slugs = array( 'general', 'black_rose', 'love_hurts', 'signature', 'jersey_vip' );
	if ( ! in_array( $list_slug, $allowed_slugs, true ) ) {
		$list_slug = 'general';
	}
	$list_id = skyyrose_klaviyo_list_id( $list_slug );

	// Subscribe via Klaviyo API.
	$ok = skyyrose_klaviyo_subscribe_to_list( $email, $list_id, $properties );

	// Also fire the general hook so any other integrations can act on it.
	do_action( 'skyyrose_newsletter_signup', $email );

	// Always return success to the user — avoid exposing API config state.
	wp_send_json_success( array(
		'message' => esc_html__( 'Welcome to the SkyyRose family! Check your inbox for your early access details.', 'skyyrose-flagship' ),
	) );
}
add_action( 'wp_ajax_skyyrose_klaviyo_subscribe', 'skyyrose_ajax_klaviyo_subscribe' );
add_action( 'wp_ajax_nopriv_skyyrose_klaviyo_subscribe', 'skyyrose_ajax_klaviyo_subscribe' );

/*--------------------------------------------------------------
 * REST API: Live Stock Counts
 *
 * GET /index.php?rest_route=/skyyrose/v1/stock/<sku>
 *
 * Returns pre-order edition size, number claimed (sold), and
 * number remaining, derived from WooCommerce product meta.
 * No authentication required — publicly readable.
 *--------------------------------------------------------------*/

/**
 * Register the stock REST route.
 *
 * @since 5.0.0
 * @return void
 */
function skyyrose_register_stock_rest_route() {
	register_rest_route(
		'skyyrose/v1',
		'/stock/(?P<sku>[a-zA-Z0-9\-]+)',
		array(
			'methods'             => 'GET',
			'callback'            => 'skyyrose_rest_stock_handler',
			'permission_callback' => '__return_true',
			'args'                => array(
				'sku' => array(
					'required'          => true,
					'validate_callback' => function ( $param ) {
						return (bool) preg_match( '/^[a-zA-Z0-9\-]{2,20}$/', $param );
					},
				),
			),
		)
	);
}
add_action( 'rest_api_init', 'skyyrose_register_stock_rest_route' );

/**
 * Handle stock REST request.
 *
 * @since 5.0.0
 *
 * @param WP_REST_Request $request REST request object.
 * @return WP_REST_Response|WP_Error
 */
function skyyrose_rest_stock_handler( $request ) {

	if ( ! class_exists( 'WooCommerce' ) ) {
		return new WP_Error( 'wc_not_active', 'WooCommerce is not active.', array( 'status' => 503 ) );
	}

	$sku = sanitize_text_field( $request->get_param( 'sku' ) );

	// Find product by SKU.
	$product_id = wc_get_product_id_by_sku( $sku );
	if ( ! $product_id ) {
		return new WP_Error( 'not_found', 'Product not found.', array( 'status' => 404 ) );
	}

	$product = wc_get_product( $product_id );
	if ( ! $product ) {
		return new WP_Error( 'not_found', 'Product not found.', array( 'status' => 404 ) );
	}

	$edition_size = (int) get_post_meta( $product_id, '_preorder_edition_size', true );
	$available    = get_post_meta( $product_id, '_preorder_available', true );

	// Fall back to WooCommerce stock management if pre-order meta is absent.
	if ( $product->managing_stock() ) {
		$wc_stock   = (int) $product->get_stock_quantity();
		$total      = $edition_size > 0 ? $edition_size : 0;
		$remaining  = $wc_stock;
		$claimed    = max( 0, $total - $remaining );
	} else {
		// Use manual pre-order remaining field.
		$remaining = '' !== $available ? (int) $available : $edition_size;
		$claimed   = max( 0, $edition_size - $remaining );
	}

	$percent_claimed = ( $edition_size > 0 )
		? min( 100, (int) round( ( $claimed / $edition_size ) * 100 ) )
		: 0;

	$data = array(
		'sku'             => $sku,
		'edition_size'    => $edition_size,
		'claimed'         => $claimed,
		'remaining'       => $remaining,
		'percent_claimed' => $percent_claimed,
		'status'          => $remaining > 0 ? 'available' : 'sold_out',
		'low_stock'       => $edition_size > 0 && $remaining <= ( $edition_size * 0.2 ),
	);

	$response = new WP_REST_Response( $data, 200 );
	// Cache for 2 minutes — fresh enough for urgency, light on the DB.
	$response->header( 'Cache-Control', 'public, max-age=120' );
	return $response;
}

/*--------------------------------------------------------------
 * WooCommerce Order Events → Klaviyo
 *
 * Fire Placed Order and Fulfilled Order events to Klaviyo via
 * Track API so the abandoned cart and post-purchase flows trigger.
 *--------------------------------------------------------------*/

/**
 * Fire Klaviyo "Placed Order" event when WooCommerce order is created.
 *
 * @since 5.0.0
 *
 * @param int      $order_id Order ID.
 * @param WC_Order $order    WooCommerce order object.
 * @return void
 */
function skyyrose_klaviyo_on_order_created( $order_id, $order ) {

	$private_key = get_option( 'skyyrose_klaviyo_private_key', '' );
	if ( empty( $private_key ) ) {
		return;
	}

	$email = $order->get_billing_email();
	if ( ! is_email( $email ) ) {
		return;
	}

	// Also subscribe the customer to the general list on purchase.
	$list_id = skyyrose_klaviyo_list_id( 'general' );
	if ( ! empty( $list_id ) ) {
		skyyrose_klaviyo_subscribe_to_list(
			$email,
			$list_id,
			array(
				'first_name' => $order->get_billing_first_name(),
				'last_name'  => $order->get_billing_last_name(),
			)
		);
	}

	// Build item list for the event.
	$items = array();
	foreach ( $order->get_items() as $item ) {
		$product = $item->get_product();
		$items[] = array(
			'ProductID'   => $item->get_product_id(),
			'SKU'         => $product ? $product->get_sku() : '',
			'ProductName' => $item->get_name(),
			'Quantity'    => $item->get_quantity(),
			'ItemPrice'   => (float) $order->get_item_total( $item ),
		);
	}

	$event_data = array(
		'data' => array(
			'type'       => 'event',
			'attributes' => array(
				'properties' => array(
					'OrderId'     => $order_id,
					'Revenue'     => (float) $order->get_total(),
					'ItemCount'   => $order->get_item_count(),
					'Items'       => $items,
					'IsPreOrder'  => true,
				),
				'metric'     => array(
					'data' => array(
						'type'       => 'metric',
						'attributes' => array( 'name' => 'Placed Order' ),
					),
				),
				'profile'    => array(
					'data' => array(
						'type'       => 'profile',
						'attributes' => array(
							'email'      => $email,
							'first_name' => $order->get_billing_first_name(),
							'last_name'  => $order->get_billing_last_name(),
						),
					),
				),
			),
		),
	);

	wp_remote_post(
		'https://a.klaviyo.com/api/events/',
		array(
			'headers' => array(
				'Authorization' => 'Klaviyo-API-Key ' . $private_key,
				'Content-Type'  => 'application/json',
				'Accept'        => 'application/json',
				'revision'      => '2024-02-15',
			),
			'body'    => wp_json_encode( $event_data ),
			'timeout' => 10,
		)
	);
}
add_action( 'woocommerce_checkout_order_created', 'skyyrose_klaviyo_on_order_created', 10, 2 );

/*--------------------------------------------------------------
 * Inline Customizer: Klaviyo Settings Panel
 *
 * Adds a "Klaviyo Integration" section to the WordPress Customizer
 * so API keys and list IDs can be configured without code changes.
 *--------------------------------------------------------------*/

/**
 * Register Klaviyo settings in the Theme Customizer.
 *
 * @since 5.0.0
 *
 * @param WP_Customize_Manager $wp_customize Customizer instance.
 * @return void
 */
function skyyrose_klaviyo_customizer_settings( $wp_customize ) {

	$wp_customize->add_section( 'skyyrose_klaviyo', array(
		'title'    => esc_html__( 'Klaviyo Integration', 'skyyrose-flagship' ),
		'priority' => 200,
	) );

	// Private API key.
	$wp_customize->add_setting( 'skyyrose_klaviyo_private_key', array(
		'default'           => '',
		'transport'         => 'refresh',
		'sanitize_callback' => 'sanitize_text_field',
		'type'              => 'option',
	) );
	$wp_customize->add_control( 'skyyrose_klaviyo_private_key', array(
		'label'       => esc_html__( 'Private API Key (sk_live_...)', 'skyyrose-flagship' ),
		'section'     => 'skyyrose_klaviyo',
		'type'        => 'text',
		'description' => esc_html__( 'Found in Klaviyo → Account → API Keys', 'skyyrose-flagship' ),
	) );

	// Public site ID.
	$wp_customize->add_setting( 'skyyrose_klaviyo_public_key', array(
		'default'           => '',
		'transport'         => 'refresh',
		'sanitize_callback' => 'sanitize_text_field',
		'type'              => 'option',
	) );
	$wp_customize->add_control( 'skyyrose_klaviyo_public_key', array(
		'label'   => esc_html__( 'Public Site ID (6-char)', 'skyyrose-flagship' ),
		'section' => 'skyyrose_klaviyo',
		'type'    => 'text',
	) );

	// List IDs.
	$lists = array(
		'skyyrose_klaviyo_list_general'    => esc_html__( 'General Newsletter List ID', 'skyyrose-flagship' ),
		'skyyrose_klaviyo_list_black_rose' => esc_html__( 'Black Rose Drop List ID', 'skyyrose-flagship' ),
		'skyyrose_klaviyo_list_love_hurts' => esc_html__( 'Love Hurts Drop List ID', 'skyyrose-flagship' ),
		'skyyrose_klaviyo_list_signature'  => esc_html__( 'Signature Drop List ID', 'skyyrose-flagship' ),
		'skyyrose_klaviyo_list_jersey_vip' => esc_html__( 'Jersey Series VIP List ID', 'skyyrose-flagship' ),
	);

	foreach ( $lists as $option_name => $label ) {
		$wp_customize->add_setting( $option_name, array(
			'default'           => '',
			'transport'         => 'refresh',
			'sanitize_callback' => 'sanitize_text_field',
			'type'              => 'option',
		) );
		$wp_customize->add_control( $option_name, array(
			'label'   => $label,
			'section' => 'skyyrose_klaviyo',
			'type'    => 'text',
		) );
	}
}
add_action( 'customize_register', 'skyyrose_klaviyo_customizer_settings' );

/*--------------------------------------------------------------
 * Enqueue Klaviyo JS Tracking Snippet (public site ID)
 *--------------------------------------------------------------*/

/**
 * Inject Klaviyo's onsite tracking script when a public key is configured.
 *
 * @since 5.0.0
 * @return void
 */
function skyyrose_klaviyo_enqueue_tracking() {

	if ( is_admin() ) {
		return;
	}

	$public_key = get_option( 'skyyrose_klaviyo_public_key', '' );
	if ( empty( $public_key ) ) {
		return;
	}

	// Klaviyo onsite CDN snippet — their recommended async loader.
	wp_register_script(
		'klaviyo-onsite',
		'https://static.klaviyo.com/onsite/js/klaviyo.js?company_id=' . esc_attr( $public_key ),
		array(),
		null,
		false  // Load in <head> per Klaviyo's recommendation for cart abandonment.
	);
	wp_enqueue_script( 'klaviyo-onsite' );
}
add_action( 'wp_enqueue_scripts', 'skyyrose_klaviyo_enqueue_tracking', 5 );

/*--------------------------------------------------------------
 * Include in functions.php (via theme-setup.php)
 *
 * This file must be require_once'd from functions.php or
 * inc/theme-setup.php. If it is not already included, add:
 *
 *   require_once get_template_directory() . '/inc/klaviyo-integration.php';
 *--------------------------------------------------------------*/
