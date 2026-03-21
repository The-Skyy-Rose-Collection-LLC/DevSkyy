<?php
/**
 * REST Analytics — Receives behavioral events from see-experience-analyzer.js.
 *
 * POST /see/v1/analytics/events — Public, no auth (events are anonymous).
 * GET  /see/v1/analytics/summary — Admin-only, returns dashboard data.
 *
 * @package SkyyRose_Experience_Engine
 * @since   1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class SEE_Rest_Analytics extends SEE_Rest_Controller {

	public function register_routes(): void {
		register_rest_route( $this->namespace, '/analytics/events', array(
			array(
				'methods'             => WP_REST_Server::CREATABLE,
				'callback'            => array( $this, 'receive_events' ),
				'permission_callback' => array( $this, 'public_permission_check' ),
				'args'                => array(
					'events' => array(
						'required'          => true,
						'validate_callback' => function ( $param ) {
							return is_array( $param );
						},
						'sanitize_callback' => function ( $param ) {
							return array_slice( (array) $param, 0, 50 ); // Cap at 50 events per request.
						},
					),
				),
			),
		) );

		register_rest_route( $this->namespace, '/analytics/summary', array(
			array(
				'methods'             => WP_REST_Server::READABLE,
				'callback'            => array( $this, 'get_summary' ),
				'permission_callback' => array( $this, 'admin_permission_check' ),
				'args'                => array(
					'days' => array(
						'default'           => 7,
						'validate_callback' => function ( $param ) {
							return is_numeric( $param ) && $param >= 1 && $param <= 90;
						},
						'sanitize_callback' => 'absint',
					),
				),
			),
		) );
	}

	/**
	 * Receive and store a batch of behavioral events.
	 */
	public function receive_events( WP_REST_Request $request ): WP_REST_Response {
		$events = $request->get_param( 'events' );

		/** @var SEE_Experience_Analyzer|null $analyzer */
		$analyzer = $this->plugin->get_module( 'experience_analyzer' );
		if ( ! $analyzer ) {
			return new WP_REST_Response( array( 'stored' => 0 ), 200 );
		}

		$stored = $analyzer->store_events( $events );

		// Optionally relay to FastAPI backend.
		$fastapi = new SEE_Fastapi_Client( $this->plugin );
		$fastapi->relay_analytics( $events );

		return new WP_REST_Response( array( 'stored' => $stored ), 200 );
	}

	/**
	 * Return analytics summary for dashboard.
	 */
	public function get_summary( WP_REST_Request $request ): WP_REST_Response {
		$days = $request->get_param( 'days' );

		/** @var SEE_Experience_Analyzer|null $analyzer */
		$analyzer = $this->plugin->get_module( 'experience_analyzer' );
		if ( ! $analyzer ) {
			return new WP_REST_Response( array( 'error' => 'Analyzer not active' ), 404 );
		}

		$summary = $analyzer->get_summary( $days );
		return new WP_REST_Response( $summary, 200 );
	}
}
