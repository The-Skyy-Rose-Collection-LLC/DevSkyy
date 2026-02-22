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
		! wp_verify_nonce( $_POST['skyyrose_contact_nonce'], 'skyyrose_contact_form' ) ) {
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

	// Sanitize input fields.
	$name    = sanitize_text_field( wp_unslash( $_POST['name'] ?? '' ) );
	$email   = sanitize_email( wp_unslash( $_POST['email'] ?? '' ) );
	$phone   = sanitize_text_field( wp_unslash( $_POST['phone'] ?? '' ) );
	$subject = sanitize_text_field( wp_unslash( $_POST['subject'] ?? '' ) );
	$message = sanitize_textarea_field( wp_unslash( $_POST['message'] ?? '' ) );

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
		"Name: %s\nEmail: %s\nPhone: %s\n\nMessage:\n%s",
		$name,
		$email,
		$phone,
		$message
	);

	$headers = array(
		'Content-Type: text/plain; charset=UTF-8',
		sprintf( 'Reply-To: %s <%s>', $name, $email ),
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
		! wp_verify_nonce( $_POST['skyyrose_newsletter_nonce'], 'skyyrose_newsletter' ) ) {
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
		! wp_verify_nonce( $_POST['skyyrose_signin_nonce'], 'skyyrose_signin' ) ) {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Security check failed. Please refresh the page and try again.', 'skyyrose-flagship' ),
			)
		);
		return;
	}

	// Rate limiting: max 5 attempts per IP per 15 minutes.
	$ip        = sanitize_text_field( $_SERVER['REMOTE_ADDR'] ?? '' );
	$cache_key = 'skyyrose_login_attempts_' . md5( $ip );
	$attempts  = (int) get_transient( $cache_key );

	if ( $attempts >= 5 ) {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Too many login attempts. Please try again in 15 minutes.', 'skyyrose-flagship' ),
			)
		);
		return;
	}

	// Sanitize input.
	$email    = sanitize_email( wp_unslash( $_POST['email'] ?? '' ) );
	$password = isset( $_POST['password'] ) ? $_POST['password'] : '';

	if ( empty( $email ) || empty( $password ) ) {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Please enter both email and password.', 'skyyrose-flagship' ),
			)
		);
		return;
	}

	// Authenticate user.
	$user = wp_authenticate( $email, $password );

	if ( is_wp_error( $user ) ) {
		set_transient( $cache_key, $attempts + 1, 15 * MINUTE_IN_SECONDS );
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Invalid email or password. Please try again.', 'skyyrose-flagship' ),
			)
		);
		return;
	}

	// Clear rate-limit counter on successful login.
	delete_transient( $cache_key );

	// Set authentication cookies.
	$remember = ! empty( $_POST['remember'] );
	wp_set_auth_cookie( $user->ID, $remember );

	wp_send_json_success(
		array(
			'message'      => esc_html__( 'Sign in successful. Redirecting...', 'skyyrose-flagship' ),
			'redirect_url' => home_url( '/' ),
		)
	);
	return;
}
add_action( 'wp_ajax_nopriv_skyyrose_signin', 'skyyrose_ajax_signin' );
