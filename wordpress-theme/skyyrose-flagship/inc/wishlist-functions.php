<?php
/**
 * Wishlist Functions
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Initialize wishlist session for non-logged-in users.
 *
 * @since 1.0.0
 */
function skyyrose_init_wishlist_session() {
	if ( ! is_user_logged_in() && ! WC()->session->has_session() ) {
		WC()->session->set_customer_session_cookie( true );
	}
}
add_action( 'init', 'skyyrose_init_wishlist_session' );

/**
 * Get the wishlist key for the current user or session.
 *
 * @since 1.0.0
 * @return string Wishlist key.
 */
function skyyrose_get_wishlist_key() {
	if ( is_user_logged_in() ) {
		return 'wishlist_user_' . get_current_user_id();
	}

	// Use session for non-logged-in users.
	$session_key = WC()->session->get_customer_id();
	return 'wishlist_session_' . $session_key;
}

/**
 * Add product to wishlist.
 *
 * @since 1.0.0
 * @param int $product_id Product ID to add.
 * @return bool True on success, false on failure.
 */
function skyyrose_add_to_wishlist( $product_id ) {
	$product_id = absint( $product_id );

	if ( ! $product_id || ! wc_get_product( $product_id ) ) {
		return false;
	}

	$wishlist_key = skyyrose_get_wishlist_key();
	$wishlist     = get_option( $wishlist_key, array() );

	if ( ! in_array( $product_id, $wishlist, true ) ) {
		$wishlist[] = $product_id;
		update_option( $wishlist_key, $wishlist, false );

		// Trigger action for extensions.
		do_action( 'skyyrose_added_to_wishlist', $product_id );

		return true;
	}

	return false;
}

/**
 * Remove product from wishlist.
 *
 * @since 1.0.0
 * @param int $product_id Product ID to remove.
 * @return bool True on success, false on failure.
 */
function skyyrose_remove_from_wishlist( $product_id ) {
	$product_id = absint( $product_id );

	if ( ! $product_id ) {
		return false;
	}

	$wishlist_key = skyyrose_get_wishlist_key();
	$wishlist     = get_option( $wishlist_key, array() );

	$key = array_search( $product_id, $wishlist, true );
	if ( false !== $key ) {
		unset( $wishlist[ $key ] );
		$wishlist = array_values( $wishlist ); // Re-index array.
		update_option( $wishlist_key, $wishlist, false );

		// Trigger action for extensions.
		do_action( 'skyyrose_removed_from_wishlist', $product_id );

		return true;
	}

	return false;
}

/**
 * Get wishlist items.
 *
 * @since 1.0.0
 * @return array Array of product IDs in wishlist.
 */
function skyyrose_get_wishlist_items() {
	$wishlist_key = skyyrose_get_wishlist_key();
	$wishlist     = get_option( $wishlist_key, array() );

	// Filter out invalid products.
	$wishlist = array_filter(
		$wishlist,
		function( $product_id ) {
			return wc_get_product( $product_id ) !== false;
		}
	);

	return array_values( $wishlist );
}

/**
 * Check if product is in wishlist.
 *
 * @since 1.0.0
 * @param int $product_id Product ID to check.
 * @return bool True if in wishlist, false otherwise.
 */
function skyyrose_is_in_wishlist( $product_id ) {
	$product_id = absint( $product_id );
	$wishlist   = skyyrose_get_wishlist_items();

	return in_array( $product_id, $wishlist, true );
}

/**
 * Move product from wishlist to cart.
 *
 * @since 1.0.0
 * @param int $product_id Product ID to move.
 * @return bool True on success, false on failure.
 */
function skyyrose_move_to_cart( $product_id ) {
	$product_id = absint( $product_id );
	$product    = wc_get_product( $product_id );

	if ( ! $product ) {
		return false;
	}

	// Add to cart.
	$cart_item_key = WC()->cart->add_to_cart( $product_id );

	if ( $cart_item_key ) {
		// Remove from wishlist.
		skyyrose_remove_from_wishlist( $product_id );

		// Trigger action for extensions.
		do_action( 'skyyrose_moved_to_cart', $product_id );

		return true;
	}

	return false;
}

/**
 * Clear all items from wishlist.
 *
 * @since 1.0.0
 * @return bool True on success, false on failure.
 */
function skyyrose_clear_wishlist() {
	$wishlist_key = skyyrose_get_wishlist_key();
	$result       = delete_option( $wishlist_key );

	if ( $result ) {
		// Trigger action for extensions.
		do_action( 'skyyrose_wishlist_cleared' );
	}

	return $result;
}

/**
 * Get wishlist item count.
 *
 * @since 1.0.0
 * @return int Number of items in wishlist.
 */
function skyyrose_get_wishlist_count() {
	return count( skyyrose_get_wishlist_items() );
}

/**
 * Move all wishlist items to cart.
 *
 * @since 1.0.0
 * @return array Array with 'success' and 'failed' counts.
 */
function skyyrose_move_all_to_cart() {
	$wishlist = skyyrose_get_wishlist_items();
	$success  = 0;
	$failed   = 0;

	foreach ( $wishlist as $product_id ) {
		if ( skyyrose_move_to_cart( $product_id ) ) {
			$success++;
		} else {
			$failed++;
		}
	}

	return array(
		'success' => $success,
		'failed'  => $failed,
	);
}

/**
 * AJAX handler: Add to wishlist.
 *
 * @since 1.0.0
 */
function skyyrose_ajax_add_to_wishlist() {
	check_ajax_referer( 'skyyrose-wishlist-nonce', 'nonce' );

	$product_id = isset( $_POST['product_id'] ) ? absint( $_POST['product_id'] ) : 0;

	if ( ! $product_id ) {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Invalid product ID.', 'skyyrose-flagship' ),
			)
		);
	}

	$result = skyyrose_add_to_wishlist( $product_id );

	if ( $result ) {
		wp_send_json_success(
			array(
				'message' => esc_html__( 'Product added to wishlist.', 'skyyrose-flagship' ),
				'count'   => skyyrose_get_wishlist_count(),
			)
		);
	} else {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Product already in wishlist.', 'skyyrose-flagship' ),
			)
		);
	}
}
add_action( 'wp_ajax_skyyrose_add_to_wishlist', 'skyyrose_ajax_add_to_wishlist' );
add_action( 'wp_ajax_nopriv_skyyrose_add_to_wishlist', 'skyyrose_ajax_add_to_wishlist' );

/**
 * AJAX handler: Remove from wishlist.
 *
 * @since 1.0.0
 */
function skyyrose_ajax_remove_from_wishlist() {
	check_ajax_referer( 'skyyrose-wishlist-nonce', 'nonce' );

	$product_id = isset( $_POST['product_id'] ) ? absint( $_POST['product_id'] ) : 0;

	if ( ! $product_id ) {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Invalid product ID.', 'skyyrose-flagship' ),
			)
		);
	}

	$result = skyyrose_remove_from_wishlist( $product_id );

	if ( $result ) {
		wp_send_json_success(
			array(
				'message' => esc_html__( 'Product removed from wishlist.', 'skyyrose-flagship' ),
				'count'   => skyyrose_get_wishlist_count(),
			)
		);
	} else {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Product not in wishlist.', 'skyyrose-flagship' ),
			)
		);
	}
}
add_action( 'wp_ajax_skyyrose_remove_from_wishlist', 'skyyrose_ajax_remove_from_wishlist' );
add_action( 'wp_ajax_nopriv_skyyrose_remove_from_wishlist', 'skyyrose_ajax_remove_from_wishlist' );

/**
 * AJAX handler: Move to cart.
 *
 * @since 1.0.0
 */
function skyyrose_ajax_move_to_cart() {
	check_ajax_referer( 'skyyrose-wishlist-nonce', 'nonce' );

	$product_id = isset( $_POST['product_id'] ) ? absint( $_POST['product_id'] ) : 0;

	if ( ! $product_id ) {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Invalid product ID.', 'skyyrose-flagship' ),
			)
		);
	}

	$result = skyyrose_move_to_cart( $product_id );

	if ( $result ) {
		wp_send_json_success(
			array(
				'message'    => esc_html__( 'Product moved to cart.', 'skyyrose-flagship' ),
				'count'      => skyyrose_get_wishlist_count(),
				'cart_count' => WC()->cart->get_cart_contents_count(),
			)
		);
	} else {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Failed to add product to cart.', 'skyyrose-flagship' ),
			)
		);
	}
}
add_action( 'wp_ajax_skyyrose_move_to_cart', 'skyyrose_ajax_move_to_cart' );
add_action( 'wp_ajax_nopriv_skyyrose_move_to_cart', 'skyyrose_ajax_move_to_cart' );

/**
 * AJAX handler: Clear wishlist.
 *
 * @since 1.0.0
 */
function skyyrose_ajax_clear_wishlist() {
	check_ajax_referer( 'skyyrose-wishlist-nonce', 'nonce' );

	$result = skyyrose_clear_wishlist();

	if ( $result ) {
		wp_send_json_success(
			array(
				'message' => esc_html__( 'Wishlist cleared.', 'skyyrose-flagship' ),
				'count'   => 0,
			)
		);
	} else {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Failed to clear wishlist.', 'skyyrose-flagship' ),
			)
		);
	}
}
add_action( 'wp_ajax_skyyrose_clear_wishlist', 'skyyrose_ajax_clear_wishlist' );
add_action( 'wp_ajax_nopriv_skyyrose_clear_wishlist', 'skyyrose_ajax_clear_wishlist' );

/**
 * AJAX handler: Move all to cart.
 *
 * @since 1.0.0
 */
function skyyrose_ajax_move_all_to_cart() {
	check_ajax_referer( 'skyyrose-wishlist-nonce', 'nonce' );

	$result = skyyrose_move_all_to_cart();

	if ( $result['success'] > 0 ) {
		wp_send_json_success(
			array(
				'message'    => sprintf(
					/* translators: %d: Number of products moved */
					esc_html__( '%d products moved to cart.', 'skyyrose-flagship' ),
					$result['success']
				),
				'count'      => skyyrose_get_wishlist_count(),
				'cart_count' => WC()->cart->get_cart_contents_count(),
			)
		);
	} else {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Failed to move products to cart.', 'skyyrose-flagship' ),
			)
		);
	}
}
add_action( 'wp_ajax_skyyrose_move_all_to_cart', 'skyyrose_ajax_move_all_to_cart' );
add_action( 'wp_ajax_nopriv_skyyrose_move_all_to_cart', 'skyyrose_ajax_move_all_to_cart' );

/**
 * Register REST API endpoints for wishlist.
 *
 * @since 1.0.0
 */
function skyyrose_register_wishlist_rest_routes() {
	// Permission callback using nonce verification for security.
	$permission_callback = function() {
		// Allow GET requests without authentication (for public wishlist viewing).
		if ( 'GET' === $_SERVER['REQUEST_METHOD'] ) {
			return true;
		}
		// POST requests require nonce verification.
		return isset( $_REQUEST['_wpnonce'] ) && wp_verify_nonce( $_REQUEST['_wpnonce'], 'skyyrose_wishlist_nonce' );
	};

	// Get wishlist items.
	register_rest_route(
		'skyyrose/v1',
		'/wishlist',
		array(
			'methods'             => 'GET',
			'callback'            => 'skyyrose_rest_get_wishlist',
			'permission_callback' => $permission_callback,
		)
	);

	// Add item to wishlist.
	register_rest_route(
		'skyyrose/v1',
		'/wishlist/add',
		array(
			'methods'             => 'POST',
			'callback'            => 'skyyrose_rest_add_to_wishlist',
			'permission_callback' => $permission_callback,
			'args'                => array(
				'product_id' => array(
					'required'          => true,
					'validate_callback' => function( $param ) {
						return is_numeric( $param );
					},
					'sanitize_callback' => 'absint',
				),
			),
		)
	);

	// Remove item from wishlist.
	register_rest_route(
		'skyyrose/v1',
		'/wishlist/remove',
		array(
			'methods'             => 'POST',
			'callback'            => 'skyyrose_rest_remove_from_wishlist',
			'permission_callback' => $permission_callback,
			'args'                => array(
				'product_id' => array(
					'required'          => true,
					'validate_callback' => function( $param ) {
						return is_numeric( $param );
					},
					'sanitize_callback' => 'absint',
				),
			),
		)
	);

	// Clear all wishlist items.
	register_rest_route(
		'skyyrose/v1',
		'/wishlist/clear',
		array(
			'methods'             => 'POST',
			'callback'            => 'skyyrose_rest_clear_wishlist',
			'permission_callback' => $permission_callback,
		)
	);
}
add_action( 'rest_api_init', 'skyyrose_register_wishlist_rest_routes' );

/**
 * REST API: Get wishlist.
 *
 * @since 1.0.0
 * @param WP_REST_Request $request Request object.
 * @return WP_REST_Response Response object.
 */
function skyyrose_rest_get_wishlist( $request ) {
	$wishlist = skyyrose_get_wishlist_items();
	$products = array();

	foreach ( $wishlist as $product_id ) {
		$product = wc_get_product( $product_id );
		if ( $product ) {
			$products[] = array(
				'id'    => $product_id,
				'name'  => $product->get_name(),
				'price' => $product->get_price_html(),
				'image' => wp_get_attachment_image_url( $product->get_image_id(), 'thumbnail' ),
				'url'   => $product->get_permalink(),
			);
		}
	}

	return new WP_REST_Response(
		array(
			'items' => $products,
			'count' => count( $products ),
		),
		200
	);
}

/**
 * REST API: Add to wishlist.
 *
 * @since 1.0.0
 * @param WP_REST_Request $request Request object.
 * @return WP_REST_Response Response object.
 */
function skyyrose_rest_add_to_wishlist( $request ) {
	$product_id = absint( $request->get_param( 'product_id' ) );
	$result     = skyyrose_add_to_wishlist( $product_id );

	if ( $result ) {
		return new WP_REST_Response(
			array(
				'success' => true,
				'message' => esc_html__( 'Product added to wishlist.', 'skyyrose-flagship' ),
				'count'   => skyyrose_get_wishlist_count(),
			),
			200
		);
	}

	return new WP_REST_Response(
		array(
			'success' => false,
			'message' => esc_html__( 'Product already in wishlist.', 'skyyrose-flagship' ),
		),
		400
	);
}

/**
 * REST API: Remove from wishlist.
 *
 * @since 1.0.0
 * @param WP_REST_Request $request Request object.
 * @return WP_REST_Response Response object.
 */
function skyyrose_rest_remove_from_wishlist( $request ) {
	$product_id = absint( $request->get_param( 'product_id' ) );
	$result     = skyyrose_remove_from_wishlist( $product_id );

	if ( $result ) {
		return new WP_REST_Response(
			array(
				'success' => true,
				'message' => esc_html__( 'Product removed from wishlist.', 'skyyrose-flagship' ),
				'count'   => skyyrose_get_wishlist_count(),
			),
			200
		);
	}

	return new WP_REST_Response(
		array(
			'success' => false,
			'message' => esc_html__( 'Product not in wishlist.', 'skyyrose-flagship' ),
		),
		400
	);
}

/**
 * REST API: Clear wishlist.
 *
 * @since 1.0.0
 * @param WP_REST_Request $request Request object.
 * @return WP_REST_Response Response object.
 */
function skyyrose_rest_clear_wishlist( $request ) {
	$result = skyyrose_clear_wishlist();

	if ( $result ) {
		return new WP_REST_Response(
			array(
				'success' => true,
				'message' => esc_html__( 'Wishlist cleared.', 'skyyrose-flagship' ),
				'count'   => 0,
			),
			200
		);
	}

	return new WP_REST_Response(
		array(
			'success' => false,
			'message' => esc_html__( 'Failed to clear wishlist.', 'skyyrose-flagship' ),
		),
		400
	);
}

/**
 * Enqueue wishlist scripts and styles.
 *
 * @since 1.0.0
 */
function skyyrose_enqueue_wishlist_assets() {
	// Enqueue wishlist CSS.
	wp_enqueue_style(
		'skyyrose-wishlist',
		SKYYROSE_ASSETS_URI . '/css/wishlist.css',
		array(),
		SKYYROSE_VERSION
	);

	// Enqueue wishlist JS.
	wp_enqueue_script(
		'skyyrose-wishlist',
		SKYYROSE_ASSETS_URI . '/js/wishlist.js',
		array( 'jquery' ),
		SKYYROSE_VERSION,
		true
	);

	// Localize script.
	wp_localize_script(
		'skyyrose-wishlist',
		'skyyRoseWishlist',
		array(
			'ajaxUrl'     => admin_url( 'admin-ajax.php' ),
			'nonce'       => wp_create_nonce( 'skyyrose-wishlist-nonce' ),
			'count'       => skyyrose_get_wishlist_count(),
			'wishlistUrl' => get_permalink( get_page_by_path( 'wishlist' ) ),
			'i18n'        => array(
				'addedToWishlist'     => esc_html__( 'Added to wishlist', 'skyyrose-flagship' ),
				'removedFromWishlist' => esc_html__( 'Removed from wishlist', 'skyyrose-flagship' ),
				'movedToCart'         => esc_html__( 'Moved to cart', 'skyyrose-flagship' ),
				'error'               => esc_html__( 'An error occurred', 'skyyrose-flagship' ),
			),
		)
	);
}
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_wishlist_assets' );

/**
 * Add wishlist button to product loop.
 *
 * @since 1.0.0
 */
function skyyrose_add_wishlist_button_to_loop() {
	get_template_part( 'template-parts/wishlist-button' );
}
add_action( 'woocommerce_after_shop_loop_item', 'skyyrose_add_wishlist_button_to_loop', 15 );

/**
 * Add wishlist button to single product page.
 *
 * @since 1.0.0
 */
function skyyrose_add_wishlist_button_to_single() {
	get_template_part( 'template-parts/wishlist-button' );
}
add_action( 'woocommerce_single_product_summary', 'skyyrose_add_wishlist_button_to_single', 35 );
