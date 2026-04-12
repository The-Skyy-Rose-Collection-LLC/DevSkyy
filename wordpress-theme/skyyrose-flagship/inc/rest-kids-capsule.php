<?php
/**
 * Kids Capsule REST API — Matching Sets Endpoint
 *
 * Returns a kid product and its matching adult product as a pair.
 * Uses skyyrose_build_product_data() from inc/immersive-ajax.php.
 *
 * @package SkyyRose
 * @since   6.5.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Register Kids Capsule REST routes.
 *
 * @since 6.5.0
 * @return void
 */
function skyyrose_register_kc_rest_routes() {

	register_rest_route(
		'skyyrose/v1',
		'/kids-capsule/matching-set/(?P<id>\d+)',
		array(
			'methods'             => WP_REST_Server::READABLE,
			'callback'            => 'skyyrose_rest_get_matching_set',
			'permission_callback' => '__return_true',
			'args'                => array(
				'id' => array(
					'required'          => true,
					'validate_callback' => function ( $param ) {
						return is_numeric( $param ) && (int) $param > 0;
					},
					'sanitize_callback' => 'absint',
				),
			),
		)
	);
}
add_action( 'rest_api_init', 'skyyrose_register_kc_rest_routes' );

/**
 * Handle the matching-set REST request.
 *
 * @since 6.5.0
 *
 * @param WP_REST_Request $request REST request object.
 * @return WP_REST_Response|WP_Error
 */
function skyyrose_rest_get_matching_set( $request ) {

	$kids_id = $request->get_param( 'id' );
	$kids    = wc_get_product( $kids_id );

	if ( ! $kids ) {
		return new WP_Error(
			'product_not_found',
			esc_html__( 'Kids product not found.', 'skyyrose' ),
			array( 'status' => 404 )
		);
	}

	$adult_id = (int) get_post_meta( $kids_id, '_kc_matching_adult_id', true );
	$adult    = $adult_id ? wc_get_product( $adult_id ) : null;

	$kids_data  = function_exists( 'skyyrose_build_product_data' )
		? skyyrose_build_product_data( $kids )
		: array( 'id' => $kids_id, 'name' => $kids->get_name() );

	$adult_data = ( $adult && function_exists( 'skyyrose_build_product_data' ) )
		? skyyrose_build_product_data( $adult )
		: null;

	return rest_ensure_response( array(
		'kids'  => $kids_data,
		'adult' => $adult_data,
	) );
}
