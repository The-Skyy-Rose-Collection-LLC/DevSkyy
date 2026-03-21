<?php
/**
 * FastAPI Backend Client — Hybrid ML integration.
 *
 * Communicates with the DevSkyy FastAPI backend (main_enterprise.py) for
 * ML-powered features: customer segmentation, recommendations, sentiment
 * analysis, dynamic pricing. Degrades gracefully when backend is unavailable.
 *
 * @package SkyyRose_Experience_Engine
 * @since   1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class SEE_Fastapi_Client {

	private SEE_Plugin $plugin;

	/** @var string Resolved backend URL. */
	private string $base_url = '';

	/** @var bool|null Cached availability check. */
	private ?bool $available = null;

	public function __construct( SEE_Plugin $plugin ) {
		$this->plugin = $plugin;
		$this->resolve_url();
	}

	public function register( SEE_Loader $loader ): void {
		// No public-facing hooks — this is called by other modules/REST endpoints.
	}

	/**
	 * Resolve the FastAPI backend URL from settings or environment.
	 */
	private function resolve_url(): void {
		$url = $this->plugin->get_setting( 'fastapi_url', '' );

		if ( empty( $url ) ) {
			// Check environment variable.
			$env = getenv( 'DEVSKYY_API_URL' );
			if ( $env ) {
				$url = $env;
			}
		}

		if ( empty( $url ) ) {
			// Default local development URL.
			$url = 'http://localhost:8000';
		}

		$this->base_url = rtrim( $url, '/' );
	}

	/**
	 * Check if the FastAPI backend is reachable.
	 * Result is cached in a transient for 5 minutes.
	 */
	public function is_available(): bool {
		if ( null !== $this->available ) {
			return $this->available;
		}

		$cached = get_transient( 'see_fastapi_available' );
		if ( false !== $cached ) {
			$this->available = (bool) $cached;
			return $this->available;
		}

		$response = wp_remote_get( $this->base_url . '/health', array(
			'timeout'   => 3,
			'sslverify' => false,
		) );

		$this->available = ! is_wp_error( $response ) && 200 === wp_remote_retrieve_response_code( $response );
		set_transient( 'see_fastapi_available', $this->available ? 1 : 0, 5 * MINUTE_IN_SECONDS );

		return $this->available;
	}

	/**
	 * Get ML-powered product recommendations.
	 *
	 * @param string $visitor_hash Anonymous visitor hash.
	 * @param array  $context      Collection affinity, recent products, etc.
	 * @return array|null Recommendations or null if unavailable.
	 */
	public function get_recommendations( string $visitor_hash, array $context = array() ): ?array {
		if ( ! $this->is_available() ) {
			return null;
		}

		$cache_key = 'see_recs_' . md5( $visitor_hash . wp_json_encode( $context ) );
		$cached    = get_transient( $cache_key );
		if ( false !== $cached ) {
			return $cached;
		}

		$response = $this->post( '/api/v1/ml/predict/customer_segmentation', array(
			'visitor_hash' => $visitor_hash,
			'context'      => $context,
		) );

		if ( $response ) {
			set_transient( $cache_key, $response, HOUR_IN_SECONDS );
		}

		return $response;
	}

	/**
	 * Relay analytics events to backend for ML processing.
	 *
	 * @param array $events Batched events from Experience Analyzer.
	 */
	public function relay_analytics( array $events ): void {
		if ( ! $this->is_available() ) {
			return;
		}

		// Fire and forget — non-blocking.
		$this->post( '/api/v1/analytics/ingest', array(
			'source' => 'see-plugin',
			'events' => $events,
		), true );
	}

	/**
	 * Get sentiment analysis for a product.
	 *
	 * @param int $product_id WooCommerce product ID.
	 * @return array|null Sentiment data or null.
	 */
	public function get_product_sentiment( int $product_id ): ?array {
		if ( ! $this->is_available() ) {
			return null;
		}

		$cache_key = 'see_sentiment_' . $product_id;
		$cached    = get_transient( $cache_key );
		if ( false !== $cached ) {
			return $cached;
		}

		$response = $this->get( '/api/v1/ml/predict/sentiment', array(
			'product_id' => $product_id,
		) );

		if ( $response ) {
			set_transient( $cache_key, $response, 6 * HOUR_IN_SECONDS );
		}

		return $response;
	}

	/**
	 * Submit a design narrative for AI analysis.
	 *
	 * @param string $narrative The narrative text.
	 * @return array|null AI-generated module configurations or null.
	 */
	public function analyze_narrative( string $narrative ): ?array {
		if ( ! $this->is_available() ) {
			return null;
		}

		return $this->post( '/api/v1/marketing/analyze', array(
			'narrative' => $narrative,
			'source'    => 'see-dashboard',
		) );
	}

	/*--------------------------------------------------------------
	 * HTTP Helpers
	 *--------------------------------------------------------------*/

	private function post( string $endpoint, array $body, bool $non_blocking = false ): ?array {
		$args = array(
			'timeout'   => $non_blocking ? 1 : 10,
			'blocking'  => ! $non_blocking,
			'sslverify' => false,
			'headers'   => array( 'Content-Type' => 'application/json' ),
			'body'      => wp_json_encode( $body ),
		);

		$response = wp_remote_post( $this->base_url . $endpoint, $args );

		if ( $non_blocking ) {
			return null;
		}

		return $this->parse_response( $response );
	}

	private function get( string $endpoint, array $params = array() ): ?array {
		$url = $this->base_url . $endpoint;
		if ( $params ) {
			$url .= '?' . http_build_query( $params );
		}

		$response = wp_remote_get( $url, array(
			'timeout'   => 10,
			'sslverify' => false,
		) );

		return $this->parse_response( $response );
	}

	private function parse_response( $response ): ?array {
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
}
