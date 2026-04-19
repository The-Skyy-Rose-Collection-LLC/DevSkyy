<?php
/**
 * FastAPI Client — Bridge to devskyy.app Dashboard
 *
 * HTTP client for the DevSkyy FastAPI backend (main_enterprise.py).
 * Provides ML-powered features: product recommendations, analytics relay,
 * narrative analysis. Degrades gracefully when the backend is unavailable.
 *
 * Connection flow: WordPress theme <-> FastAPI backend <-> devskyy.app dashboard
 *
 * @package SkyyRose_Flagship
 * @since   6.5.0
 */

defined( 'ABSPATH' ) || exit;

/**
 * Resolve the FastAPI backend URL from settings or environment.
 *
 * Priority: option > SEE_FASTAPI_URL env > DEVSKYY_API_URL env > default
 *
 * @return string Base URL (no trailing slash).
 */
function skyyrose_see_get_fastapi_url(): string {
	$url = skyyrose_see_get_option( 'fastapi_url', '' );

	if ( empty( $url ) ) {
		$url = getenv( 'SEE_FASTAPI_URL' ) ?: '';
	}
	if ( empty( $url ) ) {
		$url = getenv( 'DEVSKYY_API_URL' ) ?: '';
	}
	if ( empty( $url ) ) {
		$url = 'http://localhost:8000';
	}

	return rtrim( $url, '/' );
}

/**
 * Validate a URL is safe for HTTP requests.
 *
 * Only allows http/https schemes. Blocks private IP ranges, localhost
 * aliases, and metadata endpoints to prevent SSRF.
 *
 * @param string $url URL to validate.
 * @return bool True if safe.
 */
function skyyrose_see_is_safe_url( string $url ): bool {
	$parsed = wp_parse_url( $url );
	if ( ! $parsed || empty( $parsed['host'] ) ) {
		return false;
	}

	$scheme = strtolower( $parsed['scheme'] ?? '' );
	if ( 'http' !== $scheme && 'https' !== $scheme ) {
		return false;
	}

	$host = strtolower( $parsed['host'] );

	// Block metadata endpoints and obvious internal addresses.
	$blocked_hosts = array( '169.254.169.254', 'metadata.google.internal' );
	if ( in_array( $host, $blocked_hosts, true ) ) {
		return false;
	}

	// Resolve hostname and block private IP ranges.
	$ip = gethostbyname( $host );
	if ( $ip !== $host ) {
		$private_ranges = array(
			'10.',
			'172.16.', '172.17.', '172.18.', '172.19.',
			'172.20.', '172.21.', '172.22.', '172.23.',
			'172.24.', '172.25.', '172.26.', '172.27.',
			'172.28.', '172.29.', '172.30.', '172.31.',
			'192.168.',
			'169.254.',
			'127.',
		);
		foreach ( $private_ranges as $range ) {
			if ( str_starts_with( $ip, $range ) ) {
				// Allow localhost in development.
				if ( str_starts_with( $ip, '127.' ) && wp_get_environment_type() === 'local' ) {
					return true;
				}
				return false;
			}
		}
	}

	return true;
}

/**
 * Check if the FastAPI backend is reachable.
 *
 * Result is cached in a transient scoped to the backend URL.
 *
 * @return bool
 */
function skyyrose_see_fastapi_is_available(): bool {
	$base_url  = skyyrose_see_get_fastapi_url();
	$cache_key = 'skyyrose_see_api_' . md5( $base_url );

	$cached = get_transient( $cache_key );
	if ( false !== $cached ) {
		return (bool) $cached;
	}

	$response = wp_remote_get( $base_url . '/health', array(
		'timeout'   => 3,
		'sslverify' => apply_filters( 'skyyrose_fastapi_sslverify', true ),
	) );

	$available = ! is_wp_error( $response )
		&& 200 === wp_remote_retrieve_response_code( $response );

	set_transient( $cache_key, $available ? 1 : 0, 5 * MINUTE_IN_SECONDS );

	return $available;
}

/*--------------------------------------------------------------
 * HTTP Request Helpers
 *--------------------------------------------------------------*/

/**
 * Make a POST request to the FastAPI backend.
 *
 * @param string $endpoint    API endpoint path (e.g. '/api/v1/analytics/events').
 * @param array  $body        Request body.
 * @param bool   $non_blocking Fire-and-forget mode (1s timeout, non-blocking).
 * @return array|null Parsed response or null on failure.
 */
function skyyrose_see_fastapi_post( string $endpoint, array $body, bool $non_blocking = false ): ?array {
	$base_url = skyyrose_see_get_fastapi_url();
	$url      = $base_url . $endpoint;

	if ( ! skyyrose_see_is_safe_url( $url ) ) {
		return null;
	}

	$response = wp_remote_post( $url, array(
		'timeout'   => $non_blocking ? 1 : 10,
		'blocking'  => ! $non_blocking,
		'sslverify' => apply_filters( 'skyyrose_fastapi_sslverify', true ),
		'headers'   => array( 'Content-Type' => 'application/json' ),
		'body'      => wp_json_encode( $body ),
	) );

	if ( $non_blocking ) {
		return null;
	}

	return skyyrose_see_parse_api_response( $response );
}

/**
 * Make a GET request to the FastAPI backend.
 *
 * @param string $endpoint API endpoint path.
 * @param array  $params   Query parameters.
 * @return array|null Parsed response or null on failure.
 */
function skyyrose_see_fastapi_get( string $endpoint, array $params = array() ): ?array {
	$base_url = skyyrose_see_get_fastapi_url();
	$url      = $base_url . $endpoint;

	if ( $params ) {
		$url .= '?' . http_build_query( $params );
	}

	if ( ! skyyrose_see_is_safe_url( $url ) ) {
		return null;
	}

	$response = wp_remote_get( $url, array(
		'timeout'   => 10,
		'sslverify' => apply_filters( 'skyyrose_fastapi_sslverify', true ),
	) );

	return skyyrose_see_parse_api_response( $response );
}

/**
 * Parse a wp_remote response into an array.
 *
 * @param array|WP_Error $response wp_remote_* response.
 * @return array|null Decoded JSON or null on failure.
 */
function skyyrose_see_parse_api_response( $response ): ?array {
	if ( is_wp_error( $response ) ) {
		return null;
	}

	$code = wp_remote_retrieve_response_code( $response );
	if ( $code < 200 || $code >= 300 ) {
		return null;
	}

	$body = wp_remote_retrieve_body( $response );
	$data = json_decode( $body, true );

	return is_array( $data ) ? $data : null;
}

/*--------------------------------------------------------------
 * High-Level API Methods
 *--------------------------------------------------------------*/

/**
 * Relay analytics events to the FastAPI backend for ML processing.
 *
 * @param array $events Sanitized event array.
 */
function skyyrose_see_relay_analytics( array $events ): void {
	if ( ! skyyrose_see_fastapi_is_available() ) {
		return;
	}
	skyyrose_see_fastapi_post( '/api/v1/analytics/ingest', array(
		'source' => 'skyyrose-theme',
		'events' => $events,
	), true ); // Non-blocking.
}

/**
 * Get ML-powered product recommendations.
 *
 * @param string $visitor_hash Anonymous visitor hash.
 * @param array  $context      Collection affinity, recent products, etc.
 * @return array|null Recommendations or null.
 */
function skyyrose_see_get_recommendations( string $visitor_hash, array $context = array() ): ?array {
	if ( ! skyyrose_see_fastapi_is_available() ) {
		return null;
	}

	$cache_key = 'skyyrose_see_recs_' . md5( $visitor_hash . wp_json_encode( $context ) );
	$cached    = get_transient( $cache_key );
	if ( false !== $cached && is_array( $cached ) ) {
		return $cached;
	}

	$response = skyyrose_see_fastapi_post( '/api/v1/ml/predict/customer_segmentation', array(
		'visitor_hash' => sanitize_text_field( $visitor_hash ),
		'context'      => $context,
	) );

	if ( $response ) {
		set_transient( $cache_key, $response, HOUR_IN_SECONDS );
	}

	return $response;
}

/**
 * Submit a design narrative for AI analysis.
 *
 * @param string $narrative The narrative text.
 * @return array|null AI-generated module configurations or null.
 */
function skyyrose_see_analyze_narrative( string $narrative ): ?array {
	if ( ! skyyrose_see_fastapi_is_available() ) {
		return null;
	}

	return skyyrose_see_fastapi_post( '/api/v1/marketing/analyze', array(
		'narrative' => sanitize_textarea_field( $narrative ),
		'source'    => 'skyyrose-theme',
	) );
}
