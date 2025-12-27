<?php
/**
 * SkyyRose Server Time REST API Endpoint
 *
 * Provides current server timestamp for client-side countdown timer synchronization.
 * Prevents countdown timer drift by syncing with authoritative server time.
 *
 * Endpoint: /wp-json/skyyrose/v1/server-time
 * Method: GET
 * Authentication: None required (public)
 *
 * Response:
 * {
 *   "timestamp": 1736865600,
 *   "milliseconds": 1736865600000,
 *   "iso8601": "2025-01-14T12:00:00Z",
 *   "timezone": "UTC"
 * }
 *
 * @package SkyyRose
 * @subpackage API
 * @since 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

/**
 * Initialize server time endpoint
 *
 * Hooks into WordPress REST API initialization.
 * Should be called from a mu-plugin or main plugin file.
 */
function skyyrose_register_server_time_endpoint() {
    register_rest_route('skyyrose/v1', '/server-time', [
        'methods'             => WP_REST_Server::READABLE,
        'callback'            => 'skyyrose_get_server_time',
        'permission_callback' => '__return_true',  // Public endpoint
        'args'                => [],
    ]);
}

/**
 * Get current server time
 *
 * @param WP_REST_Request $request The REST request object
 * @return WP_REST_Response|WP_Error Response with server time data
 */
function skyyrose_get_server_time($request) {
    try {
        // Get current time in UTC
        $current_time = current_time('timestamp', true); // GMT/UTC timestamp

        // Validate timestamp is reasonable (not in past or far future)
        if ($current_time < 0 || $current_time > PHP_INT_MAX / 1000) {
            return new WP_Error(
                'invalid_timestamp',
                'Invalid server timestamp',
                ['status' => 500]
            );
        }

        // Prepare response data
        $response_data = [
            'timestamp'    => (int) $current_time,
            'milliseconds' => (int) ($current_time * 1000),
            'iso8601'      => wp_date('c', $current_time, new DateTimeZone('UTC')),
            'timezone'     => 'UTC',
        ];

        // Create REST response with proper caching headers
        $response = new WP_REST_Response($response_data, 200);

        // Allow browsers and CDNs to cache for 1 second
        // (short enough to be accurate, long enough to reduce traffic)
        $response->set_status(200);

        // Set cache control headers
        header('Cache-Control: max-age=1, public');
        header('X-Accel-Expires: 1');

        return $response;

    } catch (Exception $e) {
        // Log error
        error_log('SkyyRose server time error: ' . $e->getMessage());

        return new WP_Error(
            'server_time_error',
            'Failed to get server time',
            ['status' => 500]
        );
    }
}

/**
 * Register endpoint on REST API init
 */
add_action('rest_api_init', 'skyyrose_register_server_time_endpoint');

/**
 * CORS headers for countdown endpoint
 *
 * Allows frontend apps to fetch server time from different origins
 */
function skyyrose_set_countdown_cors_headers() {
    // Only apply to our endpoint
    if (strpos($_SERVER['REQUEST_URI'] ?? '', '/wp-json/skyyrose/v1/server-time') === false) {
        return;
    }

    // Allow cross-origin requests
    header('Access-Control-Allow-Origin: *');
    header('Access-Control-Allow-Methods: GET, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type, Accept');
    header('Access-Control-Max-Age: 3600');
}
add_action('rest_pre_serve_request', 'skyyrose_set_countdown_cors_headers', 10, 4);

/**
 * Pre-order status REST endpoint
 *
 * Get countdown configuration for a specific product
 * Endpoint: /wp-json/skyyrose/v1/products/{product_id}/countdown
 */
function skyyrose_register_product_countdown_endpoint() {
    register_rest_route('skyyrose/v1', '/products/(?P<product_id>\d+)/countdown', [
        'methods'             => WP_REST_Server::READABLE,
        'callback'            => 'skyyrose_get_product_countdown',
        'permission_callback' => '__return_true',
        'args'                => [
            'product_id' => [
                'required'          => true,
                'type'              => 'integer',
                'sanitize_callback' => 'absint',
                'validate_callback' => 'rest_validate_request_arg',
            ],
        ],
    ]);
}

/**
 * Get countdown configuration for a product
 *
 * @param WP_REST_Request $request The REST request object
 * @return WP_REST_Response|WP_Error Response with countdown config or error
 */
function skyyrose_get_product_countdown($request) {
    try {
        $product_id = (int) $request['product_id'];

        // Validate product exists and is published
        $product = wc_get_product($product_id);
        if (!$product) {
            return new WP_Error(
                'product_not_found',
                'Product not found',
                ['status' => 404]
            );
        }

        // Get pre-order meta
        $is_preorder = (bool) $product->get_meta('_preorder_enabled');
        if (!$is_preorder) {
            return new WP_Error(
                'not_preorder',
                'Product is not on pre-order',
                ['status' => 400]
            );
        }

        // Get launch date
        $launch_date_str = $product->get_meta('_preorder_launch_date');
        if (empty($launch_date_str)) {
            return new WP_Error(
                'no_launch_date',
                'No launch date configured',
                ['status' => 400]
            );
        }

        // Parse launch date
        $launch_date = DateTime::createFromFormat(
            DateTime::ISO8601,
            $launch_date_str,
            new DateTimeZone('UTC')
        );

        if (!$launch_date) {
            $launch_date = new DateTime($launch_date_str, new DateTimeZone('UTC'));
        }

        $server_time = current_time('timestamp', true);
        $time_remaining = max(0, $launch_date->getTimestamp() - $server_time);

        // Prepare response
        $response_data = [
            'product_id'            => $product_id,
            'product_name'          => $product->get_name(),
            'launch_date_iso'       => $launch_date->format('c'),
            'launch_date_unix'      => (int) $launch_date->getTimestamp(),
            'server_time_unix'      => (int) $server_time,
            'status'                => $product->get_meta('_preorder_status') ?: 'blooming_soon',
            'ar_enabled'            => (bool) $product->get_meta('_preorder_ar_enabled'),
            'collection'            => $product->get_meta('_preorder_collection') ?: '',
            'time_remaining_seconds' => (int) $time_remaining,
        ];

        return new WP_REST_Response($response_data, 200);

    } catch (Exception $e) {
        error_log('SkyyRose countdown error: ' . $e->getMessage());

        return new WP_Error(
            'countdown_error',
            'Failed to get countdown configuration',
            ['status' => 500]
        );
    }
}

add_action('rest_api_init', 'skyyrose_register_product_countdown_endpoint');

/**
 * Register pre-order product type custom meta fields
 *
 * Ensures meta fields are properly registered and available via REST API
 */
function skyyrose_register_preorder_meta_fields() {
    // Pre-order enabled
    register_rest_field(
        'product',
        '_preorder_enabled',
        [
            'get_callback'    => function ($product_data) {
                $product = wc_get_product($product_data['id']);
                return (bool) $product->get_meta('_preorder_enabled');
            },
            'update_callback' => function ($value, $product_data) {
                $product = wc_get_product($product_data->ID);
                $product->update_meta_data('_preorder_enabled', (bool) $value);
                $product->save();
                return true;
            },
            'schema'          => [
                'type'        => 'boolean',
                'description' => 'Product is on pre-order',
            ],
        ]
    );

    // Pre-order status
    register_rest_field(
        'product',
        '_preorder_status',
        [
            'get_callback'    => function ($product_data) {
                $product = wc_get_product($product_data['id']);
                return $product->get_meta('_preorder_status') ?: 'blooming_soon';
            },
            'update_callback' => function ($value, $product_data) {
                $product = wc_get_product($product_data->ID);
                $product->update_meta_data('_preorder_status', sanitize_text_field($value));
                $product->save();
                return true;
            },
            'schema'          => [
                'type'        => 'string',
                'enum'        => ['blooming_soon', 'now_blooming', 'available'],
                'description' => 'Pre-order status: blooming_soon, now_blooming, or available',
            ],
        ]
    );

    // Pre-order launch date
    register_rest_field(
        'product',
        '_preorder_launch_date',
        [
            'get_callback'    => function ($product_data) {
                $product = wc_get_product($product_data['id']);
                return $product->get_meta('_preorder_launch_date') ?: '';
            },
            'update_callback' => function ($value, $product_data) {
                $product = wc_get_product($product_data->ID);
                $product->update_meta_data('_preorder_launch_date', sanitize_text_field($value));
                $product->save();
                return true;
            },
            'schema'          => [
                'type'        => 'string',
                'format'      => 'date-time',
                'description' => 'Product launch date (ISO 8601)',
            ],
        ]
    );

    // Pre-order AR enabled
    register_rest_field(
        'product',
        '_preorder_ar_enabled',
        [
            'get_callback'    => function ($product_data) {
                $product = wc_get_product($product_data['id']);
                return (bool) $product->get_meta('_preorder_ar_enabled');
            },
            'update_callback' => function ($value, $product_data) {
                $product = wc_get_product($product_data->ID);
                $product->update_meta_data('_preorder_ar_enabled', (bool) $value);
                $product->save();
                return true;
            },
            'schema'          => [
                'type'        => 'boolean',
                'description' => 'Enable AR Quick Look for pre-orders',
            ],
        ]
    );
}

add_action('rest_api_init', 'skyyrose_register_preorder_meta_fields');
