<?php
/**
 * REST Personalization — ML-powered recommendations & client-side affinity.
 *
 * GET /see/v1/personalization/{hash} — Returns product recommendations.
 * Falls back to client-side affinity when FastAPI unavailable.
 *
 * @package SkyyRose_Experience_Engine
 * @since   1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class SEE_Rest_Personalization extends SEE_Rest_Controller {

	public function register_routes(): void {
		register_rest_route( $this->namespace, '/personalization/(?P<hash>[a-f0-9]{8,64})', array(
			array(
				'methods'             => WP_REST_Server::READABLE,
				'callback'            => array( $this, 'get_recommendations' ),
				'permission_callback' => array( $this, 'public_permission_check' ),
				'args'                => array(
					'hash' => array(
						'required'          => true,
						'validate_callback' => function ( $param ) {
							return preg_match( '/^[a-f0-9]{8,64}$/', $param );
						},
						'sanitize_callback' => 'sanitize_text_field',
					),
					'collection' => array(
						'default'           => '',
						'sanitize_callback' => 'sanitize_text_field',
					),
					'limit' => array(
						'default'           => 8,
						'validate_callback' => function ( $param ) {
							return is_numeric( $param ) && $param >= 1 && $param <= 20;
						},
						'sanitize_callback' => 'absint',
					),
				),
			),
		) );
	}

	public function get_recommendations( WP_REST_Request $request ): WP_REST_Response {
		$hash       = $request->get_param( 'hash' );
		$collection = $request->get_param( 'collection' );
		$limit      = $request->get_param( 'limit' );

		// Try FastAPI backend first.
		$fastapi = new SEE_Fastapi_Client( $this->plugin );
		$ml_recs = $fastapi->get_recommendations( $hash, array(
			'collection' => $collection,
			'limit'      => $limit,
		) );

		if ( $ml_recs && ! empty( $ml_recs['products'] ) ) {
			return new WP_REST_Response( array(
				'source'   => 'ml',
				'products' => $ml_recs['products'],
			), 200 );
		}

		// Fallback: WooCommerce-based recommendations.
		$products = $this->get_fallback_recommendations( $collection, $limit );

		return new WP_REST_Response( array(
			'source'   => 'fallback',
			'products' => $products,
		), 200 );
	}

	/**
	 * Fallback recommendations using WooCommerce queries.
	 */
	private function get_fallback_recommendations( string $collection, int $limit ): array {
		if ( ! class_exists( 'WooCommerce' ) ) {
			return array();
		}

		$args = array(
			'status'  => 'publish',
			'limit'   => $limit,
			'orderby' => 'popularity',
			'return'  => 'objects',
		);

		// Filter by collection if specified.
		if ( $collection ) {
			$args['category'] = array( $collection );
		}

		$products = wc_get_products( $args );
		$result   = array();

		foreach ( $products as $product ) {
			$result[] = array(
				'id'         => $product->get_id(),
				'name'       => $product->get_name(),
				'sku'        => $product->get_sku(),
				'price'      => $product->get_price(),
				'image'      => wp_get_attachment_url( $product->get_image_id() ),
				'permalink'  => $product->get_permalink(),
				'collection' => $this->get_product_collection_slug( $product ),
			);
		}

		return $result;
	}

	private function get_product_collection_slug( $product ): string {
		if ( function_exists( 'skyyrose_get_product_collection' ) ) {
			return skyyrose_get_product_collection( $product->get_id() );
		}

		$cats  = wp_get_post_terms( $product->get_id(), 'product_cat', array( 'fields' => 'slugs' ) );
		$known = array( 'black-rose', 'love-hurts', 'signature', 'kids-capsule' );

		if ( ! is_wp_error( $cats ) ) {
			foreach ( $cats as $slug ) {
				if ( in_array( $slug, $known, true ) ) {
					return $slug;
				}
			}
		}
		return '';
	}
}
