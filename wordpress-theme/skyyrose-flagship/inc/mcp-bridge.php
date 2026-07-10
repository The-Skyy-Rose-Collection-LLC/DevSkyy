<?php
/**
 * MCP Bridge — wp-admin console for the DevSkyy MCP server.
 *
 * Talks to the FastAPI-mounted MCP endpoint (api.devskyy.app/mcp/) over the
 * Streamable HTTP transport. Lets a site administrator list and invoke MCP
 * tools (agent directory, catalog, analytics, etc.) from Tools -> DevSkyy MCP.
 *
 * Transport is stateful: initialize -> notifications/initialized -> tools/call,
 * with the Mcp-Session-Id header carried across all three requests. Responses
 * arrive as SSE `data:` frames, which skyyrose_mcp_parse_message() decodes.
 *
 * Configuration (first non-empty wins):
 *   URL   : option 'skyyrose_mcp_url' > const SKYYROSE_MCP_URL > env SKYYROSE_MCP_URL
 *           > https://api.devskyy.app/mcp/
 *   Token : const SKYYROSE_MCP_TOKEN > env MCP_SERVICE_TOKEN > option 'skyyrose_mcp_token'
 *           (define SKYYROSE_MCP_TOKEN in wp-config.php — never commit it).
 *
 * @package SkyyRose_Flagship
 * @since   1.2.0
 */

defined( 'ABSPATH' ) || exit;

if ( ! defined( 'SKYYROSE_MCP_PROTOCOL' ) ) {
	define( 'SKYYROSE_MCP_PROTOCOL', '2025-06-18' );
}

/*
--------------------------------------------------------------
 * Configuration
 *--------------------------------------------------------------*/

/**
 * Resolve the MCP endpoint URL (always trailing-slashed).
 *
 * The canonical endpoint is `/mcp/`; the bare `/mcp` 307-redirects, which
 * wp_remote_* would not replay as a POST, so we normalise to the slash form.
 *
 * @return string
 */
function skyyrose_mcp_get_url(): string {
	$url = (string) get_option( 'skyyrose_mcp_url', '' );

	if ( '' === $url && defined( 'SKYYROSE_MCP_URL' ) ) {
		$url = (string) SKYYROSE_MCP_URL;
	}
	if ( '' === $url ) {
		$url = getenv( 'SKYYROSE_MCP_URL' ) ?: '';
	}
	if ( '' === $url ) {
		$url = 'https://api.devskyy.app/mcp/';
	}

	return rtrim( $url, '/' ) . '/';
}

/**
 * Resolve the MCP service bearer token.
 *
 * Prefers code/env (constant, then env var) over the database option so the
 * secret never has to live in wp_options if the host injects it.
 *
 * @return string Empty string when unconfigured.
 */
function skyyrose_mcp_get_token(): string {
	if ( defined( 'SKYYROSE_MCP_TOKEN' ) && '' !== (string) SKYYROSE_MCP_TOKEN ) {
		return (string) SKYYROSE_MCP_TOKEN;
	}
	$env = getenv( 'MCP_SERVICE_TOKEN' );
	if ( $env ) {
		return (string) $env;
	}
	return (string) get_option( 'skyyrose_mcp_token', '' );
}

/*
--------------------------------------------------------------
 * Streamable HTTP transport
 *--------------------------------------------------------------*/

/**
 * POST one JSON-RPC message to the MCP endpoint.
 *
 * @param array  $payload    JSON-RPC message.
 * @param string $session_id Mcp-Session-Id (empty on the initialize request).
 * @return array|WP_Error    wp_remote_post response, or WP_Error.
 */
function skyyrose_mcp_post( array $payload, string $session_id = '' ) {
	$url = skyyrose_mcp_get_url();

	if ( ! function_exists( 'skyyrose_see_is_safe_url' ) || ! skyyrose_see_is_safe_url( $url ) ) {
		return new WP_Error( 'skyyrose_mcp_unsafe_url', __( 'MCP endpoint URL failed the safety check.', 'skyyrose' ) );
	}

	$headers = array(
		'Content-Type' => 'application/json',
		'Accept'       => 'application/json, text/event-stream',
	);

	$token = skyyrose_mcp_get_token();
	if ( '' !== $token ) {
		$headers['Authorization'] = 'Bearer ' . $token;
	}
	if ( '' !== $session_id ) {
		$headers['Mcp-Session-Id']       = $session_id;
		$headers['MCP-Protocol-Version'] = SKYYROSE_MCP_PROTOCOL;
	}

	return wp_remote_post(
		$url,
		array(
			'timeout'   => 20,
			'sslverify' => apply_filters( 'skyyrose_mcp_sslverify', true ),
			'headers'   => $headers,
			'body'      => wp_json_encode( $payload ),
		)
	);
}

/**
 * Extract the JSON-RPC object from an MCP response body.
 *
 * Accepts both application/json and text/event-stream. For SSE it walks each
 * event (blank-line separated), concatenates that event's `data:` lines, and
 * returns the first frame that decodes to a JSON-RPC message.
 *
 * @param string $body Raw response body.
 * @return array|null  Decoded message, or null when nothing parseable.
 */
function skyyrose_mcp_parse_message( string $body ): ?array {
	$body = trim( $body );
	if ( '' === $body ) {
		return null;
	}

	if ( '{' === $body[0] || '[' === $body[0] ) {
		$data = json_decode( $body, true );
		return is_array( $data ) ? $data : null;
	}

	foreach ( preg_split( '/\r?\n\r?\n/', $body ) as $event ) {
		$chunk = '';
		foreach ( preg_split( '/\r?\n/', $event ) as $line ) {
			if ( 0 === strpos( $line, 'data:' ) ) {
				$chunk .= ltrim( substr( $line, 5 ) );
			}
		}
		if ( '' === $chunk ) {
			continue;
		}
		$data = json_decode( $chunk, true );
		if ( is_array( $data ) && isset( $data['jsonrpc'] ) ) {
			return $data;
		}
	}

	return null;
}

/**
 * Best-effort session teardown (non-blocking DELETE).
 *
 * @param string $session_id Session to terminate.
 * @return void
 */
function skyyrose_mcp_terminate( string $session_id ): void {
	if ( '' === $session_id ) {
		return;
	}
	$headers = array(
		'Mcp-Session-Id'       => $session_id,
		'MCP-Protocol-Version' => SKYYROSE_MCP_PROTOCOL,
	);
	$token   = skyyrose_mcp_get_token();
	if ( '' !== $token ) {
		$headers['Authorization'] = 'Bearer ' . $token;
	}

	wp_remote_request(
		skyyrose_mcp_get_url(),
		array(
			'method'    => 'DELETE',
			'timeout'   => 5,
			'blocking'  => false,
			'sslverify' => apply_filters( 'skyyrose_mcp_sslverify', true ),
			'headers'   => $headers,
		)
	);
}

/**
 * Run one MCP request through a full stateful session.
 *
 * @param string $method JSON-RPC method (e.g. 'tools/list', 'tools/call').
 * @param array  $params Method params.
 * @return array|WP_Error The `result` object on success.
 */
function skyyrose_mcp_request( string $method, array $params ) {
	$init = skyyrose_mcp_post(
		array(
			'jsonrpc' => '2.0',
			'id'      => 1,
			'method'  => 'initialize',
			'params'  => array(
				'protocolVersion' => SKYYROSE_MCP_PROTOCOL,
				'capabilities'    => (object) array(),
				'clientInfo'      => array(
					'name'    => 'skyyrose-wp-bridge',
					'version' => defined( 'SKYYROSE_VERSION' ) ? SKYYROSE_VERSION : '1.0.0',
				),
			),
		)
	);

	if ( is_wp_error( $init ) ) {
		return $init;
	}
	$code = wp_remote_retrieve_response_code( $init );
	if ( $code < 200 || $code >= 300 ) {
		/* translators: %d: HTTP status code. */
		return new WP_Error( 'skyyrose_mcp_init_failed', sprintf( __( 'MCP initialize failed (HTTP %d).', 'skyyrose' ), (int) $code ) );
	}

	$session_id = wp_remote_retrieve_header( $init, 'mcp-session-id' );
	if ( is_array( $session_id ) ) {
		$session_id = (string) reset( $session_id );
	}
	if ( empty( $session_id ) ) {
		return new WP_Error( 'skyyrose_mcp_no_session', __( 'MCP server did not return a session id.', 'skyyrose' ) );
	}

	$note = skyyrose_mcp_post(
		array(
			'jsonrpc' => '2.0',
			'method'  => 'notifications/initialized',
		),
		$session_id
	);
	if ( is_wp_error( $note ) ) {
		skyyrose_mcp_terminate( $session_id );
		return $note;
	}

	$resp = skyyrose_mcp_post(
		array(
			'jsonrpc' => '2.0',
			'id'      => 2,
			'method'  => $method,
			'params'  => empty( $params ) ? (object) array() : $params,
		),
		$session_id
	);

	$message = is_wp_error( $resp ) ? null : skyyrose_mcp_parse_message( wp_remote_retrieve_body( $resp ) );
	skyyrose_mcp_terminate( $session_id );

	if ( is_wp_error( $resp ) ) {
		return $resp;
	}
	$code = wp_remote_retrieve_response_code( $resp );
	if ( $code < 200 || $code >= 300 ) {
		/* translators: %d: HTTP status code. */
		return new WP_Error( 'skyyrose_mcp_request_failed', sprintf( __( 'MCP request failed (HTTP %d).', 'skyyrose' ), (int) $code ) );
	}
	if ( null === $message ) {
		return new WP_Error( 'skyyrose_mcp_bad_response', __( 'MCP returned an unparseable response.', 'skyyrose' ) );
	}
	if ( isset( $message['error'] ) ) {
		$msg = isset( $message['error']['message'] ) ? (string) $message['error']['message'] : __( 'MCP tool error.', 'skyyrose' );
		return new WP_Error( 'skyyrose_mcp_tool_error', $msg );
	}

	return ( isset( $message['result'] ) && is_array( $message['result'] ) ) ? $message['result'] : array();
}

/**
 * List the tools the MCP server exposes.
 *
 * @return array|WP_Error
 */
function skyyrose_mcp_list_tools() {
	return skyyrose_mcp_request( 'tools/list', array() );
}

/**
 * Invoke an MCP tool.
 *
 * @param string $tool      Tool name.
 * @param array  $arguments Tool arguments.
 * @return array|WP_Error
 */
function skyyrose_mcp_call_tool( string $tool, array $arguments = array() ) {
	return skyyrose_mcp_request(
		'tools/call',
		array(
			'name'      => $tool,
			'arguments' => empty( $arguments ) ? (object) array() : $arguments,
		)
	);
}

/*
--------------------------------------------------------------
 * Admin console
 *--------------------------------------------------------------*/

add_action( 'admin_menu', 'skyyrose_mcp_register_admin_page' );

/**
 * Register the Tools -> DevSkyy MCP console page.
 *
 * @return void
 */
function skyyrose_mcp_register_admin_page(): void {
	add_management_page(
		__( 'DevSkyy MCP Console', 'skyyrose' ),
		__( 'DevSkyy MCP', 'skyyrose' ),
		'manage_options',
		'skyyrose-mcp',
		'skyyrose_mcp_render_admin_page'
	);
}

add_action( 'admin_enqueue_scripts', 'skyyrose_mcp_admin_assets' );

/**
 * Enqueue the console script only on its own page.
 *
 * @param string $hook Current admin page hook suffix.
 * @return void
 */
function skyyrose_mcp_admin_assets( string $hook ): void {
	if ( 'tools_page_skyyrose-mcp' !== $hook ) {
		return;
	}

	$version = defined( 'SKYYROSE_VERSION' ) ? SKYYROSE_VERSION : '1.0.0';
	wp_enqueue_script(
		'skyyrose-mcp-console',
		get_template_directory_uri() . '/assets/js/admin-mcp-console.js',
		array(),
		$version,
		true
	);
	wp_localize_script(
		'skyyrose-mcp-console',
		'skyyroseMcp',
		array(
			'ajaxUrl' => admin_url( 'admin-ajax.php' ),
			'nonce'   => wp_create_nonce( 'skyyrose_mcp' ),
			'i18n'    => array(
				'loading'     => __( 'Working…', 'skyyrose' ),
				'invalidJson' => __( 'Arguments must be valid JSON.', 'skyyrose' ),
				'noTools'     => __( 'No tools returned.', 'skyyrose' ),
				'selectTool'  => __( 'Select a tool first.', 'skyyrose' ),
				/* translators: %d: number of tools. */
				'toolsLoaded' => __( '%d tools loaded.', 'skyyrose' ),
			),
		)
	);
}

/**
 * Render the MCP console page.
 *
 * @return void
 */
function skyyrose_mcp_render_admin_page(): void {
	if ( ! current_user_can( 'manage_options' ) ) {
		wp_die( esc_html__( 'You do not have permission to access this page.', 'skyyrose' ) );
	}

	$url       = skyyrose_mcp_get_url();
	$has_token = '' !== skyyrose_mcp_get_token();
	?>
	<div class="wrap skyyrose-mcp-console">
		<h1><?php esc_html_e( 'DevSkyy MCP Console', 'skyyrose' ); ?></h1>
		<p class="description">
			<?php esc_html_e( 'Endpoint:', 'skyyrose' ); ?>
			<code><?php echo esc_html( $url ); ?></code> &mdash;
			<?php
			echo $has_token
				? esc_html__( 'service token configured', 'skyyrose' )
				: esc_html__( 'no service token — define SKYYROSE_MCP_TOKEN in wp-config.php', 'skyyrose' );
			?>
		</p>

		<p>
			<button type="button" class="button" id="skyyrose-mcp-refresh"><?php esc_html_e( 'Load tools', 'skyyrose' ); ?></button>
		</p>

		<table class="form-table" role="presentation">
			<tr>
				<th scope="row"><label for="skyyrose-mcp-tool"><?php esc_html_e( 'Tool', 'skyyrose' ); ?></label></th>
				<td><select id="skyyrose-mcp-tool" class="regular-text"></select></td>
			</tr>
			<tr>
				<th scope="row"><label for="skyyrose-mcp-args"><?php esc_html_e( 'Arguments (JSON)', 'skyyrose' ); ?></label></th>
				<td><textarea id="skyyrose-mcp-args" rows="6" class="large-text code" spellcheck="false">{}</textarea></td>
			</tr>
		</table>

		<p>
			<button type="button" class="button button-primary" id="skyyrose-mcp-invoke"><?php esc_html_e( 'Invoke tool', 'skyyrose' ); ?></button>
			<span id="skyyrose-mcp-status" aria-live="polite"></span>
		</p>

		<h2><?php esc_html_e( 'Result', 'skyyrose' ); ?></h2>
		<pre id="skyyrose-mcp-result" class="skyyrose-mcp-result" aria-live="polite" style="max-height:480px;overflow:auto;background:#0a0a0a;color:#e6e6e6;padding:16px;border-radius:6px;"></pre>
	</div>
	<?php
}

/*
--------------------------------------------------------------
 * AJAX
 *--------------------------------------------------------------*/

add_action( 'wp_ajax_skyyrose_mcp_invoke', 'skyyrose_mcp_ajax_invoke' );

/**
 * Tools the admin MCP bridge refuses to invoke by default: anything that spends
 * real money (paid image/video/model generation) or mutates production
 * (deploys, releases). Auth on the AJAX endpoint is already manage_options +
 * nonce; this is a second control so one compromised admin session cannot drain
 * the paid-API budget or ship a deploy through the shared backend service
 * token. Operators can override with the `skyyrose_mcp_blocked_tools` filter.
 *
 * @return string[] Tool names blocked from the bridge.
 */
function skyyrose_mcp_blocked_tools(): array {
	return apply_filters(
		'skyyrose_mcp_blocked_tools',
		array(
			// Paid generation (per-call cost).
			'devskyy_oai_render_generate',
			'devskyy_lora_generate',
			'devskyy_lora_pose_transfer',
			'devskyy_lora_upscale',
			'devskyy_lora_clean_background',
			'devskyy_train_lora_from_products',
			'devskyy_virtual_tryon',
			'devskyy_batch_virtual_tryon',
			'devskyy_generate_ai_model',
			'devskyy_generate_3d_from_description',
			'devskyy_generate_3d_from_image',
			'es_render',
			'es_batch',
			// Production mutation / deploys.
			'operations_deploy',
			'wp_release',
			'wp_bump_version',
		)
	);
}

/**
 * Read-only tools the admin bridge is allowed to invoke. This is the fail-closed
 * ALLOWLIST: only these run through the bridge; every other tool — all paid
 * generation, all writes, and anything new or untagged — is refused by default.
 *
 * Sourced from the `readOnlyHint: True` MCP annotations in mcp_tools/tools/*.py
 * (see core/runtime/tool_registry.py). A denylist alone fails open — a newly
 * added paid tool would be invocable until someone remembered to block it; this
 * allowlist fails closed. Regenerate when tools change; to expose a specific
 * write tool without editing this list, use `skyyrose_mcp_allowed_write_tools`.
 *
 * @return string[] Read-only tool names permitted through the bridge.
 */
function skyyrose_mcp_readonly_tools(): array {
	return apply_filters(
		'skyyrose_mcp_readonly_tools',
		array(
			'context7_get_code_examples',
			'context7_get_docs',
			'context7_resolve_library',
			'context7_search_docs',
			'devskyy_analyze_spreadsheet',
			'devskyy_dashboard_health',
			'devskyy_demand_forecast',
			'devskyy_email_triage',
			'devskyy_fleet_health',
			'devskyy_fraud_assess',
			'devskyy_health_check',
			'devskyy_list_agents',
			'devskyy_lora_dataset_preview',
			'devskyy_lora_product_history',
			'devskyy_lora_version_info',
			'devskyy_ml_prediction',
			'devskyy_oai_render_plan',
			'devskyy_product_caption',
			'devskyy_recommend',
			'devskyy_retention_assess',
			'devskyy_scan_code',
			'devskyy_system_monitoring',
			'devskyy_virtual_tryon_status',
			'es_cost_estimate',
			'es_status',
			'es_validate_dossier',
			'playwright_get_page_content',
			'playwright_screenshot',
			'rag_get_context',
			'rag_list_sources',
			'rag_query',
			'rag_query_rewrite',
			'rag_stats',
			'serena_analyze_file',
			'serena_check_code_style',
			'serena_find_issues',
			'serena_full_project_audit',
			'serena_validate_security',
			'wc_get_orders',
			'wc_get_product',
			'wc_get_products',
			'wc_get_store_settings',
			'wc_list_orders',
			'wc_search_customers',
			'wc_smoketest',
			'wc_validate_coupon',
			'wp_verify_live',
		)
	);
}

/**
 * Non-read-only tools the operator explicitly permits despite the read-only
 * default. Empty by default (fail-closed). A tool in skyyrose_mcp_blocked_tools()
 * stays blocked even if added here — the hard backstop always wins.
 *
 * @return string[]
 */
function skyyrose_mcp_allowed_write_tools(): array {
	return apply_filters( 'skyyrose_mcp_allowed_write_tools', array() );
}

/**
 * Fail-closed authorization for the admin MCP bridge. A tool may be invoked only
 * if it is NOT hard-blocked AND is either read-only or explicitly operator-allowed.
 * Everything else — new tools, untagged tools, and all paid generation — is refused.
 *
 * @param string $tool Tool name.
 * @return true|WP_Error True if permitted, WP_Error with a 403 reason otherwise.
 */
function skyyrose_mcp_authorize_tool( string $tool ) {
	if ( in_array( $tool, skyyrose_mcp_blocked_tools(), true ) ) {
		return new WP_Error(
			'skyyrose_mcp_blocked',
			__( 'This tool is blocked from the admin bridge (paid generation or production mutation).', 'skyyrose' )
		);
	}
	if ( in_array( $tool, skyyrose_mcp_readonly_tools(), true )
		|| in_array( $tool, skyyrose_mcp_allowed_write_tools(), true ) ) {
		return true;
	}
	return new WP_Error(
		'skyyrose_mcp_not_allowlisted',
		__( 'This tool is not on the read-only allowlist. Add it via the skyyrose_mcp_allowed_write_tools filter if it is safe to expose.', 'skyyrose' )
	);
}

/**
 * Admin-only AJAX relay: list tools or invoke one.
 *
 * @return void
 */
function skyyrose_mcp_ajax_invoke(): void {
	if ( ! current_user_can( 'manage_options' ) ) {
		wp_send_json_error( array( 'message' => __( 'Insufficient permissions.', 'skyyrose' ) ), 403 );
	}
	check_ajax_referer( 'skyyrose_mcp', 'nonce' );

	$mcp_action = isset( $_POST['mcp_action'] ) ? sanitize_key( wp_unslash( $_POST['mcp_action'] ) ) : '';

	if ( 'list' === $mcp_action ) {
		$result = skyyrose_mcp_list_tools();
	} elseif ( 'call' === $mcp_action ) {
		$tool = isset( $_POST['tool'] ) ? sanitize_text_field( wp_unslash( $_POST['tool'] ) ) : '';
		if ( '' === $tool ) {
			wp_send_json_error( array( 'message' => __( 'Tool name required.', 'skyyrose' ) ), 400 );
		}

		// Defense in depth: this endpoint is already manage_options + nonce
		// gated, but it forwards to the backend under a shared service token, so
		// a single compromised admin session must not be able to spend real
		// money or mutate production through the bridge. Fail-closed allowlist:
		// only read-only (or explicitly operator-allowed) tools pass; all paid
		// generation, all writes, and any new/untagged tool are refused.
		$authz = skyyrose_mcp_authorize_tool( $tool );
		if ( is_wp_error( $authz ) ) {
			wp_send_json_error( array( 'message' => $authz->get_error_message() ), 403 );
		}

		// Arguments are an arbitrary JSON object forwarded verbatim to our own
		// trusted backend; json_decode is the validation. Deep-sanitising would
		// corrupt legitimate tool inputs. Gated behind manage_options + nonce.
		$args_raw = isset( $_POST['args'] ) ? wp_unslash( $_POST['args'] ) : '{}'; // phpcs:ignore WordPress.Security.ValidatedSanitizedInput.InputNotSanitized
		$args     = json_decode( is_string( $args_raw ) ? $args_raw : '{}', true );
		if ( ! is_array( $args ) ) {
			wp_send_json_error( array( 'message' => __( 'Arguments must be a JSON object.', 'skyyrose' ) ), 400 );
		}

		$result = skyyrose_mcp_call_tool( $tool, $args );
	} else {
		wp_send_json_error( array( 'message' => __( 'Unknown action.', 'skyyrose' ) ), 400 );
	}

	if ( is_wp_error( $result ) ) {
		wp_send_json_error( array( 'message' => $result->get_error_message() ) );
	}

	wp_send_json_success( $result );
}
