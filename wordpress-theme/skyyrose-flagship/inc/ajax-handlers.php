<?php
/**
 * AJAX Handlers
 *
 * Contact form, newsletter subscription, and sign-in AJAX endpoints
 * with nonce verification and input sanitization.
 *
 * @package SkyyRose_Flagship
 * @since   3.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/*--------------------------------------------------------------
 * Contact Form Submission
 *--------------------------------------------------------------*/

/**
 * Handle contact form AJAX submission.
 *
 * Verifies nonce, sanitizes all fields, checks honeypot,
 * and sends email via wp_mail.
 *
 * @since 3.0.0
 * @return void
 */
function skyyrose_ajax_contact_submit() {
	// Verify nonce.
	if ( ! isset( $_POST['skyyrose_contact_nonce'] ) ||
		! wp_verify_nonce( sanitize_text_field( wp_unslash( $_POST['skyyrose_contact_nonce'] ) ), 'skyyrose_contact_form' ) ) {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Security check failed. Please refresh the page and try again.', 'skyyrose-flagship' ),
			)
		);
		return;
	}

	// Honeypot check: if the hidden 'website' field is filled, silently succeed.
	if ( ! empty( $_POST['website'] ) ) {
		wp_send_json_success(
			array(
				'message' => esc_html__( 'Thank you for your message. We will be in touch soon.', 'skyyrose-flagship' ),
			)
		);
		return;
	}

	// Sanitize input fields (contact form sends first_name + last_name).
	$first_name = mb_substr( sanitize_text_field( wp_unslash( $_POST['first_name'] ?? '' ) ), 0, 100 );
	$last_name  = mb_substr( sanitize_text_field( wp_unslash( $_POST['last_name'] ?? '' ) ), 0, 100 );
	$name       = trim( $first_name . ' ' . $last_name );
	$email      = sanitize_email( wp_unslash( $_POST['email'] ?? '' ) );
	$phone             = str_replace( array( "\r", "\n", "\t" ), '', mb_substr( sanitize_text_field( wp_unslash( $_POST['phone'] ?? '' ) ), 0, 30 ) );
	$subject_raw       = mb_substr( sanitize_text_field( wp_unslash( $_POST['subject'] ?? '' ) ), 0, 200 );
	$message           = mb_substr( sanitize_textarea_field( wp_unslash( $_POST['message'] ?? '' ) ), 0, 5000 );
	$order_number      = str_replace( array( "\r", "\n", "\t" ), '', mb_substr( sanitize_text_field( wp_unslash( $_POST['order_number'] ?? '' ) ), 0, 50 ) );
	$preferred_contact = sanitize_key( wp_unslash( $_POST['preferred_contact'] ?? 'email' ) );

	// Referral source — marketing attribution.
	$referral_raw    = sanitize_key( wp_unslash( $_POST['referral_source'] ?? '' ) );
	$referral_labels = array(
		'instagram'       => 'Instagram',
		'tiktok'          => 'TikTok',
		'twitter'         => 'Twitter / X',
		'facebook'        => 'Facebook',
		'youtube'         => 'YouTube',
		'google-search'   => 'Google Search',
		'friend-referral' => 'Friend or Family',
		'press-article'   => 'Press / Article',
		'event'           => 'Event or Pop-Up',
		'other'           => 'Other',
	);
	$referral_source = isset( $referral_labels[ $referral_raw ] ) ? $referral_labels[ $referral_raw ] : '';

	// Map subject slugs to human-readable labels.
	$subject_labels = array(
		'general-inquiry'    => __( 'General Inquiry', 'skyyrose-flagship' ),
		'order-status'       => __( 'Order Status', 'skyyrose-flagship' ),
		'returns-exchanges'  => __( 'Returns & Exchanges', 'skyyrose-flagship' ),
		'wholesale-inquiry'  => __( 'Wholesale Inquiry', 'skyyrose-flagship' ),
		'press-media'        => __( 'Press & Media', 'skyyrose-flagship' ),
		'collaboration'      => __( 'Collaboration', 'skyyrose-flagship' ),
		'custom-orders'      => __( 'Custom Orders', 'skyyrose-flagship' ),
		'press'              => __( 'Press', 'skyyrose-flagship' ),
		'other'              => __( 'Other', 'skyyrose-flagship' ),
	);
	$subject = isset( $subject_labels[ $subject_raw ] ) ? $subject_labels[ $subject_raw ] : $subject_labels['other'];

	// Validate required fields.
	if ( empty( $name ) || empty( $email ) || empty( $message ) ) {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Please fill in all required fields.', 'skyyrose-flagship' ),
			)
		);
		return;
	}

	if ( ! is_email( $email ) ) {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Please enter a valid email address.', 'skyyrose-flagship' ),
			)
		);
		return;
	}

	// Build email.
	$to      = get_option( 'admin_email' );
	$subject = ! empty( $subject )
		? sprintf( '[SkyyRose Contact] %s', $subject )
		: __( '[SkyyRose Contact] New Message', 'skyyrose-flagship' );

	$body = sprintf(
		"Name: %s\nEmail: %s\nPhone: %s\nOrder Number: %s\nPreferred Contact: %s\nReferral Source: %s\n\nMessage:\n%s",
		$name,
		$email,
		$phone,
		$order_number,
		$preferred_contact,
		$referral_source ? $referral_source : 'Not specified',
		$message
	);

	// Strip newlines from $name and $email to prevent email header injection.
	$safe_name  = str_replace( array( "\r", "\n", "\t" ), '', $name );
	$safe_email = str_replace( array( "\r", "\n", "\t" ), '', $email );
	$headers    = array(
		'Content-Type: text/plain; charset=UTF-8',
		sprintf( 'Reply-To: %s <%s>', $safe_name, $safe_email ),
	);

	$sent = wp_mail( $to, $subject, $body, $headers );

	if ( $sent ) {
		wp_send_json_success(
			array(
				'message' => esc_html__( 'Thank you for your message. We will be in touch soon.', 'skyyrose-flagship' ),
			)
		);
		return;
	} else {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Unable to send your message. Please try again later.', 'skyyrose-flagship' ),
			)
		);
		return;
	}
}
add_action( 'wp_ajax_skyyrose_contact_submit', 'skyyrose_ajax_contact_submit' );
add_action( 'wp_ajax_nopriv_skyyrose_contact_submit', 'skyyrose_ajax_contact_submit' );

/*--------------------------------------------------------------
 * Newsletter Subscription
 *--------------------------------------------------------------*/

/**
 * Handle newsletter subscription AJAX submission.
 *
 * Verifies nonce, sanitizes and validates email,
 * fires action hook for plugins to handle the subscription.
 *
 * @since 3.0.0
 * @return void
 */
function skyyrose_ajax_newsletter_subscribe() {
	// Verify nonce.
	if ( ! isset( $_POST['skyyrose_newsletter_nonce'] ) ||
		! wp_verify_nonce( sanitize_text_field( wp_unslash( $_POST['skyyrose_newsletter_nonce'] ) ), 'skyyrose_newsletter' ) ) {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Security check failed. Please refresh the page and try again.', 'skyyrose-flagship' ),
			)
		);
		return;
	}

	// Sanitize and validate email.
	$email = sanitize_email( wp_unslash( $_POST['email'] ?? '' ) );

	if ( ! is_email( $email ) ) {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Please enter a valid email address.', 'skyyrose-flagship' ),
			)
		);
		return;
	}

	/**
	 * Fires when a user subscribes to the newsletter.
	 *
	 * Plugins can hook into this action to handle the subscription
	 * (e.g., Mailchimp, Sendinblue, custom storage).
	 *
	 * @since 3.0.0
	 * @param string $email The sanitized subscriber email address.
	 */
	do_action( 'skyyrose_newsletter_signup', $email );

	wp_send_json_success(
		array(
			'message' => esc_html__( 'Welcome to the SkyyRose family! Check your inbox for your 15% discount code.', 'skyyrose-flagship' ),
		)
	);
	return;
}
add_action( 'wp_ajax_skyyrose_newsletter_subscribe', 'skyyrose_ajax_newsletter_subscribe' );
add_action( 'wp_ajax_nopriv_skyyrose_newsletter_subscribe', 'skyyrose_ajax_newsletter_subscribe' );

/*--------------------------------------------------------------
 * Incentive Popup Signup (Pre-Order Gateway)
 *--------------------------------------------------------------*/

/**
 * Handle incentive popup AJAX submission.
 *
 * Verifies nonce, sanitizes email and optional phone,
 * fires action hook for plugins to handle the signup.
 *
 * @since 3.2.0
 * @return void
 */
function skyyrose_ajax_incentive_signup() {
	// Verify nonce.
	if ( ! isset( $_POST['skyyrose_incentive_nonce'] ) ||
		! wp_verify_nonce( sanitize_text_field( wp_unslash( $_POST['skyyrose_incentive_nonce'] ) ), 'skyyrose_incentive' ) ) {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Security check failed. Please refresh the page and try again.', 'skyyrose-flagship' ),
			)
		);
		return;
	}

	// Sanitize and validate email.
	$email = sanitize_email( wp_unslash( $_POST['email'] ?? '' ) );

	if ( ! is_email( $email ) ) {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Please enter a valid email address.', 'skyyrose-flagship' ),
			)
		);
		return;
	}

	// Sanitize optional phone.
	$phone = sanitize_text_field( wp_unslash( $_POST['phone'] ?? '' ) );

	/**
	 * Fires when a user signs up via the incentive popup.
	 *
	 * Plugins can hook into this action to handle the signup
	 * (e.g., Mailchimp, Sendinblue, custom storage).
	 *
	 * @since 3.2.0
	 * @param string $email The sanitized subscriber email address.
	 * @param string $phone The sanitized phone number (may be empty).
	 */
	do_action( 'skyyrose_incentive_signup', $email, $phone );

	wp_send_json_success(
		array(
			'message' => esc_html__( 'You are in! Check your inbox for your 25% discount code and early access details.', 'skyyrose-flagship' ),
		)
	);
	return;
}
add_action( 'wp_ajax_skyyrose_incentive_signup', 'skyyrose_ajax_incentive_signup' );
add_action( 'wp_ajax_nopriv_skyyrose_incentive_signup', 'skyyrose_ajax_incentive_signup' );

/*--------------------------------------------------------------
 * Sign In
 *--------------------------------------------------------------*/

/**
 * Handle sign-in AJAX submission for non-logged-in users.
 *
 * Verifies nonce, sanitizes credentials, authenticates via wp_authenticate,
 * and sets auth cookies on success.
 *
 * @since 3.0.0
 * @return void
 */
function skyyrose_ajax_signin() {
	// Verify nonce.
	if ( ! isset( $_POST['skyyrose_signin_nonce'] ) ||
		! wp_verify_nonce( sanitize_text_field( wp_unslash( $_POST['skyyrose_signin_nonce'] ) ), 'skyyrose_signin' ) ) {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Security check failed. Please refresh the page and try again.', 'skyyrose-flagship' ),
			)
		);
		return;
	}

	// Sanitize input.
	$email    = sanitize_email( wp_unslash( $_POST['email'] ?? '' ) );
	$password = isset( $_POST['password'] ) ? wp_unslash( $_POST['password'] ) : '';

	if ( empty( $email ) || empty( $password ) ) {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Please enter both email and password.', 'skyyrose-flagship' ),
			)
		);
		return;
	}

	// Rate limiting: max 5 attempts per email per 15 minutes.
	// Uses email (not IP) because REMOTE_ADDR is the proxy IP on WordPress.com.
	$normalized_email = strtolower( trim( $email ) );
	$cache_key = 'skyyrose_login_attempts_' . md5( $normalized_email );
	$attempts  = (int) get_transient( $cache_key );

	// Secondary: per-IP bucket as defence-in-depth (wider limit for shared IPs/proxies).
	$ip_key      = 'skyyrose_login_ip_' . md5( isset( $_SERVER['REMOTE_ADDR'] ) ? $_SERVER['REMOTE_ADDR'] : 'unknown' );
	$ip_attempts = (int) get_transient( $ip_key );

	if ( $ip_attempts >= 20 ) {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Too many attempts from your network. Please try again later.', 'skyyrose-flagship' ),
			)
		);
		return;
	}

	if ( $attempts >= 5 ) {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Too many login attempts. Please try again in 15 minutes.', 'skyyrose-flagship' ),
			)
		);
		return;
	}

	// Authenticate user.
	$user = wp_authenticate( $email, $password );

	if ( is_wp_error( $user ) ) {
		set_transient( $cache_key, $attempts + 1, 15 * MINUTE_IN_SECONDS );
		set_transient( $ip_key, $ip_attempts + 1, 15 * MINUTE_IN_SECONDS );
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Invalid email or password. Please try again.', 'skyyrose-flagship' ),
			)
		);
		return;
	}

	// Clear both rate-limit counters on successful login.
	delete_transient( $cache_key );
	delete_transient( $ip_key );

	// Initialize session and set authentication cookies.
	$remember = isset( $_POST['remember'] ) && '1' === sanitize_text_field( wp_unslash( $_POST['remember'] ) );
	wp_set_current_user( $user->ID );
	wp_set_auth_cookie( $user->ID, $remember );

	// Fire WooCommerce-specific hook for guest-to-customer cart merge.
	// Avoid do_action('wp_login') which causes double-processing with security plugins.
	if ( function_exists( 'WC' ) && WC()->session ) {
		do_action( 'woocommerce_set_cart_cookies', true );
	}

	wp_send_json_success(
		array(
			'message'      => esc_html__( 'Sign in successful. Redirecting...', 'skyyrose-flagship' ),
			'redirect_url' => home_url( '/' ),
		)
	);
	return;
}
add_action( 'wp_ajax_nopriv_skyyrose_signin', 'skyyrose_ajax_signin' );

// Logged-in users hitting the sign-in form get a graceful redirect.
add_action(
	'wp_ajax_skyyrose_signin',
	function () {
		wp_send_json_success(
			array(
				'message'      => esc_html__( 'You are already signed in.', 'skyyrose-flagship' ),
				'redirect_url' => home_url( '/' ),
			)
		);
	}
);
