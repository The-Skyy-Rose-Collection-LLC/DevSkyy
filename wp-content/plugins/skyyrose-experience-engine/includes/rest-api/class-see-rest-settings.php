<?php
/**
 * REST Settings — Admin settings + Design Narrative pipeline.
 *
 * GET  /see/v1/settings              — Read current settings & module status.
 * PUT  /see/v1/settings              — Update settings.
 * POST /see/v1/settings/narrative    — Submit a design narrative directive.
 * GET  /see/v1/settings/narratives   — List all directives with history.
 * DELETE /see/v1/settings/narrative/{id} — Remove a directive.
 *
 * @package SkyyRose_Experience_Engine
 * @since   1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class SEE_Rest_Settings extends SEE_Rest_Controller {

	public function register_routes(): void {
		// Settings CRUD.
		register_rest_route( $this->namespace, '/settings', array(
			array(
				'methods'             => WP_REST_Server::READABLE,
				'callback'            => array( $this, 'get_settings' ),
				'permission_callback' => array( $this, 'admin_permission_check' ),
			),
			array(
				'methods'             => WP_REST_Server::EDITABLE,
				'callback'            => array( $this, 'update_settings' ),
				'permission_callback' => array( $this, 'admin_permission_check' ),
			),
		) );

		// Design Narrative pipeline.
		register_rest_route( $this->namespace, '/settings/narrative', array(
			array(
				'methods'             => WP_REST_Server::CREATABLE,
				'callback'            => array( $this, 'submit_narrative' ),
				'permission_callback' => array( $this, 'admin_permission_check' ),
				'args'                => array(
					'description' => array(
						'required'          => true,
						'sanitize_callback' => 'sanitize_textarea_field',
					),
					'target' => array(
						'default'           => 'all',
						'sanitize_callback' => 'sanitize_text_field',
					),
					'config' => array(
						'default'           => array(),
						'validate_callback' => function ( $param ) {
							return is_array( $param );
						},
					),
					'priority' => array(
						'default'           => 5,
						'validate_callback' => function ( $param ) {
							return is_numeric( $param ) && $param >= 1 && $param <= 10;
						},
						'sanitize_callback' => 'absint',
					),
					'expires' => array(
						'default'           => '',
						'sanitize_callback' => 'sanitize_text_field',
					),
				),
			),
		) );

		// List narratives.
		register_rest_route( $this->namespace, '/settings/narratives', array(
			array(
				'methods'             => WP_REST_Server::READABLE,
				'callback'            => array( $this, 'list_narratives' ),
				'permission_callback' => array( $this, 'admin_permission_check' ),
			),
		) );

		// Delete narrative.
		register_rest_route( $this->namespace, '/settings/narrative/(?P<id>[a-z0-9-]+)', array(
			array(
				'methods'             => WP_REST_Server::DELETABLE,
				'callback'            => array( $this, 'delete_narrative' ),
				'permission_callback' => array( $this, 'admin_permission_check' ),
				'args'                => array(
					'id' => array(
						'required'          => true,
						'sanitize_callback' => 'sanitize_text_field',
					),
				),
			),
		) );
	}

	public function get_settings( WP_REST_Request $request ): WP_REST_Response {
		$settings = $this->plugin->get_settings();

		// Add runtime info.
		$settings['is_flagship']     = $this->plugin->is_flagship();
		$settings['active_modules']  = $this->plugin->get_active_modules();
		$settings['version']         = SEE_VERSION;

		// Check FastAPI availability.
		$fastapi = new SEE_Fastapi_Client( $this->plugin );
		$settings['fastapi_available'] = $fastapi->is_available();

		return new WP_REST_Response( $settings, 200 );
	}

	public function update_settings( WP_REST_Request $request ): WP_REST_Response {
		$body = $request->get_json_params();

		// Whitelist allowed settings keys.
		$allowed = array(
			'module_experience_analyzer',
			'module_scroll_storyteller',
			'module_smart_showcase',
			'module_personalization',
			'module_micro_interactions',
			'module_performance_guardian',
			'module_brand_atmosphere',
			'fastapi_url',
			'engine_overrides',
		);

		$update = array();
		foreach ( $allowed as $key ) {
			if ( array_key_exists( $key, $body ) ) {
				$update[ $key ] = $body[ $key ];
			}
		}

		if ( ! empty( $update ) ) {
			$this->plugin->update_settings( $update );
		}

		return new WP_REST_Response( array( 'updated' => array_keys( $update ) ), 200 );
	}

	/**
	 * Submit a design narrative for processing.
	 */
	public function submit_narrative( WP_REST_Request $request ): WP_REST_Response {
		$directive = array(
			'id'          => wp_generate_uuid4(),
			'description' => $request->get_param( 'description' ),
			'target'      => $request->get_param( 'target' ),
			'config'      => $request->get_param( 'config' ),
			'priority'    => $request->get_param( 'priority' ),
			'expires'     => $request->get_param( 'expires' ),
		);

		// If FastAPI is available, ask the AI to analyze the narrative
		// and generate module configurations.
		$fastapi = new SEE_Fastapi_Client( $this->plugin );
		$ai_config = $fastapi->analyze_narrative( $directive['description'] );
		if ( $ai_config && ! empty( $ai_config['config'] ) ) {
			$directive['config']    = array_merge( $directive['config'], $ai_config['config'] );
			$directive['ai_source'] = true;
		}

		$result = $this->plugin->process_narrative( $directive );

		return new WP_REST_Response( $result, 'accepted' === $result['status'] ? 201 : 409 );
	}

	public function list_narratives( WP_REST_Request $request ): WP_REST_Response {
		return new WP_REST_Response( array(
			'active'  => array_values( $this->plugin->get_active_directives() ),
			'history' => $this->plugin->get_setting( 'narrative_history', array() ),
		), 200 );
	}

	public function delete_narrative( WP_REST_Request $request ): WP_REST_Response {
		$id = $request->get_param( 'id' );

		$directives = $this->plugin->get_setting( 'narrative_directives', array() );
		$found      = false;

		$directives = array_filter( $directives, function ( $d ) use ( $id, &$found ) {
			if ( ( $d['id'] ?? '' ) === $id ) {
				$found = true;
				return false;
			}
			return true;
		} );

		if ( ! $found ) {
			return new WP_REST_Response( array( 'error' => 'Directive not found' ), 404 );
		}

		$this->plugin->update_settings( array( 'narrative_directives' => array_values( $directives ) ) );

		return new WP_REST_Response( array( 'deleted' => $id ), 200 );
	}
}
