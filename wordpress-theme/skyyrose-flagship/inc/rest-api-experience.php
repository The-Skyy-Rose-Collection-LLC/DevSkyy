<?php
/**
 * Experience Engine REST API
 *
 * Endpoints under the skyyrose/v1 namespace for analytics ingestion,
 * summary retrieval, personalization recommendations, and design
 * narrative management.
 *
 * Public endpoints (analytics, personalization) require no auth but
 * are rate-limited. Admin endpoints require manage_options capability.
 *
 * @package SkyyRose_Flagship
 * @since   6.5.0
 */

defined( 'ABSPATH' ) || exit;

add_action( 'rest_api_init', 'skyyrose_see_register_rest_routes' );

/**
 * Register all Experience Engine REST routes.
 */
function skyyrose_see_register_rest_routes(): void {
	$namespace = 'skyyrose/v1';

	// POST /analytics/events — Public, anonymous event ingestion.
	register_rest_route(
		$namespace,
		'/analytics/events',
		array(
			array(
				'methods'             => WP_REST_Server::CREATABLE,
				'callback'            => 'skyyrose_see_rest_receive_events',
				'permission_callback' => '__return_true',
				'args'                => array(
					'events'      => array(
						'required'          => true,
						'validate_callback' => function ( $param ) {
							return is_array( $param );
						},
						'sanitize_callback' => function ( $param ) {
							return array_slice( (array) $param, 0, 50 );
						},
					),
					'visitorHash' => array(
						'default'           => '',
						'sanitize_callback' => function ( $param ) {
							// Enforce the anonymous-hash invariant this file claims
							// (hex, 8-64 chars) rather than accepting arbitrary text.
							$hash = sanitize_text_field( (string) $param );
							return preg_match( '/^[a-f0-9]{8,64}$/', $hash ) ? $hash : '';
						},
					),
				),
			),
		)
	);

	// GET /analytics/summary — Admin-only dashboard data.
	register_rest_route(
		$namespace,
		'/analytics/summary',
		array(
			array(
				'methods'             => WP_REST_Server::READABLE,
				'callback'            => 'skyyrose_see_rest_get_summary',
				'permission_callback' => 'skyyrose_see_rest_admin_check',
				'args'                => array(
					'days' => array(
						'default'           => 30,
						'validate_callback' => function ( $param ) {
							return is_numeric( $param ) && $param >= 1 && $param <= 90;
						},
						'sanitize_callback' => 'absint',
					),
				),
			),
		)
	);

	// GET /personalization/{hash} — Public, product recommendations.
	register_rest_route(
		$namespace,
		'/personalization/(?P<hash>[a-f0-9]{8,64})',
		array(
			array(
				'methods'             => WP_REST_Server::READABLE,
				'callback'            => 'skyyrose_see_rest_get_recommendations',
				'permission_callback' => '__return_true',
				'args'                => array(
					'hash'       => array(
						'required'          => true,
						'sanitize_callback' => 'sanitize_text_field',
					),
					'collection' => array(
						'default'           => '',
						// Restrict to the canonical collection slugs so an
						// attacker can't mint unbounded distinct transient cache
						// keys (storage-growth vector) by varying this value.
						// Empty = "no collection filter". Slugs resolve via the
						// SOT (skyyrose_get_collection), not a hardcoded list.
						'validate_callback' => function ( $param ) {
							return '' === $param
								|| ( function_exists( 'skyyrose_get_collection' ) && null !== skyyrose_get_collection( (string) $param ) );
						},
						'sanitize_callback' => 'sanitize_text_field',
					),
					'limit'      => array(
						'default'           => 8,
						'validate_callback' => function ( $param ) {
							return is_numeric( $param ) && $param >= 1 && $param <= 20;
						},
						'sanitize_callback' => 'absint',
					),
				),
			),
		)
	);

	// POST /settings/narrative — Admin-only, submit design narrative.
	register_rest_route(
		$namespace,
		'/settings/narrative',
		array(
			array(
				'methods'             => WP_REST_Server::CREATABLE,
				'callback'            => 'skyyrose_see_rest_submit_narrative',
				'permission_callback' => 'skyyrose_see_rest_admin_check',
				'args'                => array(
					'description' => array(
						'required'          => true,
						'sanitize_callback' => 'sanitize_textarea_field',
					),
					'target'      => array(
						'default'           => 'all',
						'sanitize_callback' => 'sanitize_text_field',
					),
					'config'      => array(
						'default'           => array(),
						'validate_callback' => function ( $param ) {
							return is_array( $param );
						},
					),
					'priority'    => array(
						'default'           => 5,
						'validate_callback' => function ( $param ) {
							return is_numeric( $param ) && $param >= 1 && $param <= 10;
						},
						'sanitize_callback' => 'absint',
					),
				),
			),
		)
	);

	// GET /settings — Admin-only, current settings + module status.
	register_rest_route(
		$namespace,
		'/settings',
		array(
			array(
				'methods'             => WP_REST_Server::READABLE,
				'callback'            => 'skyyrose_see_rest_get_settings',
				'permission_callback' => 'skyyrose_see_rest_admin_check',
			),
			array(
				'methods'             => WP_REST_Server::EDITABLE,
				'callback'            => 'skyyrose_see_rest_update_settings',
				'permission_callback' => 'skyyrose_see_rest_admin_check',
			),
		)
	);
}

/*
--------------------------------------------------------------
 * Permission Callbacks
 *--------------------------------------------------------------*/

/**
 * Permission callback: restrict admin-only REST endpoints to users with
 * `manage_options` capability.
 *
 * @return bool True if current user can manage options.
 */
function skyyrose_see_rest_admin_check(): bool {
	return current_user_can( 'manage_options' );
}

/*
--------------------------------------------------------------
 * Route Handlers
 *--------------------------------------------------------------*/

/**
 * Receive and store behavioral events.
 */
function skyyrose_see_rest_receive_events( WP_REST_Request $request ): WP_REST_Response {
	// Rate limiting: 10 requests per minute per IP. REMOTE_ADDR only — sites
	// behind a reverse proxy should add an X-Forwarded-For allowlist before
	// trusting that header.
	$ip         = sanitize_text_field( wp_unslash( $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0' ) );
	$rate_key   = 'skyyrose_see_rate_' . md5( $ip );
	$rate_count = (int) get_transient( $rate_key );

	if ( $rate_count >= 10 ) {
		return new WP_REST_Response( array( 'error' => 'Rate limited' ), 429 );
	}

	set_transient( $rate_key, $rate_count + 1, MINUTE_IN_SECONDS );

	$events       = $request->get_param( 'events' );
	$visitor_hash = $request->get_param( 'visitorHash' );

	// Guard: experience-analyzer.php defines skyyrose_see_store_events() but is
	// loaded inside a WooCommerce-gated block in functions.php. When WooCommerce
	// is inactive the function is undefined and calling it would produce a fatal
	// error that WordPress translates into a 404 rest_no_route response.
	if ( ! function_exists( 'skyyrose_see_store_events' ) ) {
		return new WP_REST_Response(
			array(
				'stored' => 0,
				'note'   => 'analytics_unavailable',
			),
			200
		);
	}

	$stored = skyyrose_see_store_events( $events, $visitor_hash );

	// Relay to FastAPI backend (non-blocking). Sanitize first: store_events()
	// sanitizes into local copies, but the raw request array would otherwise be
	// piped verbatim from this public __return_true endpoint to the backend.
	// Defense in depth — the backend must still validate independently.
	if ( function_exists( 'skyyrose_see_relay_analytics' ) ) {
		skyyrose_see_relay_analytics( skyyrose_see_sanitize_events( (array) $events ) );
	}

	return new WP_REST_Response( array( 'stored' => $stored ), 200 );
}

/**
 * Sanitize a raw behavioral-events array down to a known field allowlist before
 * it leaves the site for the backend relay. Mirrors the per-field sanitization
 * in skyyrose_see_store_events() so attacker JSON from the public analytics
 * endpoint never reaches the FastAPI relay verbatim.
 *
 * @param array $events Raw events array from the request.
 * @return array Sanitized events (max 50, known keys only).
 */
function skyyrose_see_sanitize_events( array $events ): array {
	$clean = array();
	foreach ( array_slice( $events, 0, 50 ) as $event ) {
		if ( ! is_array( $event ) || empty( $event['type'] ) || ! is_string( $event['type'] ) ) {
			continue;
		}
		$clean[] = array(
			'type'       => sanitize_text_field( $event['type'] ),
			'target'     => sanitize_text_field( $event['target'] ?? '' ),
			'pageType'   => sanitize_text_field( $event['pageType'] ?? '' ),
			'collection' => sanitize_text_field( $event['collection'] ?? '' ),
			'value'      => floatval( $event['value'] ?? 0 ),
			'ts'         => is_numeric( $event['ts'] ?? null ) ? floatval( $event['ts'] ) : 0,
		);
	}
	return $clean;
}

/**
 * Return analytics summary for the admin dashboard.
 */
function skyyrose_see_rest_get_summary( WP_REST_Request $request ): WP_REST_Response {
	$days = $request->get_param( 'days' );

	// Guard: skyyrose_see_get_summary() defined in experience-analyzer.php which
	// is WooCommerce-gated; return an empty summary rather than a fatal error.
	if ( ! function_exists( 'skyyrose_see_get_summary' ) ) {
		return new WP_REST_Response( array(), 200 );
	}

	$summary = skyyrose_see_get_summary( $days );

	return new WP_REST_Response( $summary, 200 );
}

/**
 * Get personalized product recommendations.
 */
function skyyrose_see_rest_get_recommendations( WP_REST_Request $request ): WP_REST_Response {
	// Rate limit: 30/min per IP. This public endpoint triggers an upstream ML
	// call and writes a transient per request — without a throttle a single
	// client drives unbounded backend load and cache growth.
	$ip         = sanitize_text_field( wp_unslash( $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0' ) );
	$rate_key   = 'skyyrose_see_recs_rate_' . md5( $ip );
	$rate_count = (int) get_transient( $rate_key );
	if ( $rate_count >= 30 ) {
		return new WP_REST_Response( array( 'error' => 'Rate limited' ), 429 );
	}
	set_transient( $rate_key, $rate_count + 1, MINUTE_IN_SECONDS );

	$hash       = $request->get_param( 'hash' );
	$collection = $request->get_param( 'collection' );
	$limit      = $request->get_param( 'limit' );

	// Cache scoped to hash + collection only. The Referer header was previously
	// mixed into the key — attacker-controlled and unbounded, so a randomized
	// Referer per request exploded transient/object-cache storage. Removed.
	$cache_key = 'skyyrose_see_recs_' . md5( $hash . '|' . $collection );
	$cached    = get_transient( $cache_key );

	if ( false !== $cached && is_array( $cached ) ) {
		return new WP_REST_Response( $cached, 200 );
	}

	// Try ML recommendations from FastAPI.
	$ml_recs = skyyrose_see_get_recommendations(
		$hash,
		array(
			'collection' => $collection,
			'limit'      => $limit,
		)
	);

	if ( $ml_recs && ! empty( $ml_recs['products'] ) ) {
		// Validate all product URLs.
		$ml_recs['products'] = skyyrose_see_validate_product_urls( $ml_recs['products'] );
		$ml_recs['source']   = 'ml';
		set_transient( $cache_key, $ml_recs, HOUR_IN_SECONDS );
		return new WP_REST_Response( $ml_recs, 200 );
	}

	// Fallback: local product catalog recommendations.
	$local_recs = skyyrose_see_local_recommendations( $collection, $limit );
	$response   = array(
		'products' => $local_recs,
		'source'   => 'local',
	);
	set_transient( $cache_key, $response, 30 * MINUTE_IN_SECONDS );

	return new WP_REST_Response( $response, 200 );
}

/**
 * Submit a design narrative directive.
 */
function skyyrose_see_rest_submit_narrative( WP_REST_Request $request ): WP_REST_Response {
	$directive = array(
		'id'          => wp_generate_uuid4(),
		'description' => $request->get_param( 'description' ),
		'target'      => $request->get_param( 'target' ),
		'config'      => $request->get_param( 'config' ),
		'priority'    => $request->get_param( 'priority' ),
	);

	// If FastAPI is available, ask AI to analyze the narrative.
	$ai_config = skyyrose_see_analyze_narrative( $directive['description'] );
	if ( $ai_config && ! empty( $ai_config['config'] ) && is_array( $ai_config['config'] ) ) {
		$directive['config']    = array_merge( (array) $directive['config'], $ai_config['config'] );
		$directive['ai_source'] = true;
	}

	$result = skyyrose_see_process_narrative( $directive );
	$status = 'accepted' === $result['status'] ? 201 : 409;

	return new WP_REST_Response( $result, $status );
}

/**
 * Get current settings and module status.
 */
function skyyrose_see_rest_get_settings( WP_REST_Request $request ): WP_REST_Response {
	$settings = get_option( 'skyyrose_see_settings', array() );
	if ( ! is_array( $settings ) ) {
		$settings = array();
	}

	$settings['version']           = SKYYROSE_SEE_VERSION;
	$settings['active_modules']    = skyyrose_see_get_active_modules();
	$settings['fastapi_available'] = skyyrose_see_fastapi_is_available();

	return new WP_REST_Response( $settings, 200 );
}

/**
 * Update settings.
 */
function skyyrose_see_rest_update_settings( WP_REST_Request $request ): WP_REST_Response {
	$body = $request->get_json_params();
	if ( ! is_array( $body ) ) {
		return new WP_REST_Response( array( 'error' => 'Request body must be a JSON object' ), 400 );
	}

	// Whitelist allowed keys.
	$allowed = array(
		'module_performance_guardian',
		'module_experience_analyzer',
		'module_brand_atmosphere',
		'module_smart_showcase',
		'module_micro_interactions',
		'module_personalization',
		'fastapi_url',
	);

	$update = array();
	foreach ( $allowed as $key ) {
		if ( array_key_exists( $key, $body ) ) {
			$update[ $key ] = $body[ $key ];
		}
	}

	if ( ! empty( $update ) ) {
		skyyrose_see_update_options( $update );
	}

	return new WP_REST_Response( array( 'updated' => array_keys( $update ) ), 200 );
}

/*
--------------------------------------------------------------
 * Helpers
 *--------------------------------------------------------------*/

/**
 * Validate product URLs — only allow http/https schemes.
 *
 * @param array $products Array of product data.
 * @return array Products with validated URLs.
 */
function skyyrose_see_validate_product_urls( array $products ): array {
	return array_map(
		function ( $product ) {
			if ( ! is_array( $product ) ) {
					return $product;
			}
			foreach ( array( 'permalink', 'image', 'url' ) as $url_field ) {
				if ( ! empty( $product[ $url_field ] ) ) {
					$url    = $product[ $url_field ];
					$scheme = wp_parse_url( $url, PHP_URL_SCHEME );
					if ( 'http' !== $scheme && 'https' !== $scheme ) {
						$product[ $url_field ] = '';
					}
				}
			}
			return $product;
		},
		$products
	);
}

/**
 * Get local product recommendations from the catalog.
 *
 * @param string $collection Preferred collection slug.
 * @param int    $limit      Number of products to return.
 * @return array Product data for the curated section.
 */
function skyyrose_see_local_recommendations( string $collection, int $limit = 8 ): array {
	if ( ! function_exists( 'skyyrose_get_product_catalog' ) ) {
		return array();
	}

	$catalog  = skyyrose_get_product_catalog();
	$products = array();

	// Prefer products from the specified collection.
	foreach ( $catalog as $sku => $product ) {
		if ( ! is_array( $product ) ) {
			continue;
		}
		$prod_collection = $product['collection'] ?? '';
		if ( $collection && $prod_collection === $collection ) {
			$products[] = array(
				'sku'        => $sku,
				'name'       => $product['name'] ?? '',
				'price'      => $product['price'] ?? '',
				'collection' => $prod_collection,
				'permalink'  => home_url( '/product/' . sanitize_title( $product['name'] ?? $sku ) . '/' ),
				'image'      => $product['image'] ?? '',
			);
		}
		if ( count( $products ) >= $limit ) {
			break;
		}
	}

	// Fill remaining slots from other collections.
	if ( count( $products ) < $limit ) {
		foreach ( $catalog as $sku => $product ) {
			if ( ! is_array( $product ) ) {
				continue;
			}
			if ( count( $products ) >= $limit ) {
				break;
			}
			$prod_collection = $product['collection'] ?? '';
			if ( $collection && $prod_collection === $collection ) {
				continue; // Already included.
			}
			$products[] = array(
				'sku'        => $sku,
				'name'       => $product['name'] ?? '',
				'price'      => $product['price'] ?? '',
				'collection' => $prod_collection,
				'permalink'  => home_url( '/product/' . sanitize_title( $product['name'] ?? $sku ) . '/' ),
				'image'      => $product['image'] ?? '',
			);
		}
	}

	return $products;
}
