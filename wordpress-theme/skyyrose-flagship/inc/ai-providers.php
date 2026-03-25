<?php
/**
 * SkyyRose AI Providers — Full-Stack AI Integration
 *
 * Registers OpenAI, Anthropic, and Google AI providers via the WordPress
 * PHP AI Client SDK. Provides helper functions for text generation,
 * image generation, and function calling.
 *
 * API keys managed via Settings > AI Credentials in wp-admin.
 *
 * @package SkyyRose_Flagship
 * @since   4.1.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

use WordPress\AiClient\AiClient;
use WordPress\AI_Client\AI_Client;
use WordPress\OpenAiAiProvider\Provider\OpenAiProvider;
use WordPress\AnthropicAiProvider\Provider\AnthropicProvider;
use WordPress\GoogleAiProvider\Provider\GoogleProvider;

/**
 * Load Composer autoloader for AI SDK + providers.
 */
$skyyrose_autoload = SKYYROSE_DIR . '/vendor/autoload.php';
if ( file_exists( $skyyrose_autoload ) ) {
	require_once $skyyrose_autoload;
}

/**
 * Register all 3 AI providers and initialize the WP AI Client.
 *
 * Hooked to 'init' at priority 5 (before default 10) so providers
 * are available when other code runs on init.
 */
add_action( 'init', 'skyyrose_register_ai_providers', 5 );

function skyyrose_register_ai_providers() {
	// Bail if classes not available (Composer not installed).
	if ( ! class_exists( AiClient::class ) ) {
		return;
	}

	$registry = AiClient::defaultRegistry();

	// Register all 3 providers.
	if ( class_exists( OpenAiProvider::class ) && ! $registry->hasProvider( 'openai' ) ) {
		$registry->registerProvider( OpenAiProvider::class );
	}
	if ( class_exists( AnthropicProvider::class ) && ! $registry->hasProvider( 'anthropic' ) ) {
		$registry->registerProvider( AnthropicProvider::class );
	}
	if ( class_exists( GoogleProvider::class ) && ! $registry->hasProvider( 'google' ) ) {
		$registry->registerProvider( GoogleProvider::class );
	}

	// Initialize the WordPress AI Client (admin UI, REST API, credentials).
	AI_Client::init();
}

/*--------------------------------------------------------------
 * Helper Functions — Text Generation
 *--------------------------------------------------------------*/

/**
 * Generate text using the best available AI provider.
 *
 * @param string      $prompt   The prompt text.
 * @param string|null $provider Force a specific provider ('openai', 'anthropic', 'google').
 * @param array       $options  Optional settings: 'temperature', 'max_tokens', 'model'.
 * @return string|WP_Error Generated text or WP_Error on failure.
 */
function skyyrose_ai_text( $prompt, $provider = null, $options = array() ) {
	if ( ! function_exists( 'wp_ai_client_prompt' ) ) {
		return new WP_Error( 'ai_not_available', 'AI Client SDK not loaded.' );
	}

	$builder = wp_ai_client_prompt( $prompt );

	if ( $provider ) {
		$builder = $builder->using_provider( $provider );
	}

	if ( ! empty( $options['model'] ) ) {
		$builder = $builder->using_model( $options['model'] );
	}
	if ( isset( $options['temperature'] ) ) {
		$builder = $builder->using_temperature( (float) $options['temperature'] );
	}
	if ( ! empty( $options['max_tokens'] ) ) {
		$builder = $builder->using_max_output_tokens( (int) $options['max_tokens'] );
	}

	$result = $builder->generate_text();

	if ( is_wp_error( $result ) ) {
		return $result;
	}

	return $result->get_text();
}

/*--------------------------------------------------------------
 * Helper Functions — Image Generation
 *--------------------------------------------------------------*/

/**
 * Generate an image using OpenAI (DALL-E) or Google (Imagen).
 *
 * Anthropic does not support image generation.
 *
 * @param string      $prompt   The image description.
 * @param string|null $provider Force 'openai' or 'google'. Default: auto-select.
 * @param array       $options  Optional: 'size' (e.g. '1024x1024'), 'model'.
 * @return array|WP_Error Array with 'url' and 'mime_type', or WP_Error.
 */
function skyyrose_ai_image( $prompt, $provider = null, $options = array() ) {
	if ( ! function_exists( 'wp_ai_client_prompt' ) ) {
		return new WP_Error( 'ai_not_available', 'AI Client SDK not loaded.' );
	}

	$builder = wp_ai_client_prompt( $prompt );

	if ( $provider ) {
		$builder = $builder->using_provider( $provider );
	}

	if ( ! empty( $options['model'] ) ) {
		$builder = $builder->using_model( $options['model'] );
	}

	$result = $builder->generate_image();

	if ( is_wp_error( $result ) ) {
		return $result;
	}

	return array(
		'images' => $result->get_images(),
	);
}

/*--------------------------------------------------------------
 * Helper Functions — Function Calling / Tool Use
 *--------------------------------------------------------------*/

/**
 * Execute a prompt with function calling (tool use).
 *
 * All 3 providers support function calling.
 *
 * @param string      $prompt   The prompt text.
 * @param array       $tools    Array of tool definitions (FunctionDeclaration arrays).
 * @param string|null $provider Force a specific provider.
 * @param array       $options  Optional: 'temperature', 'model'.
 * @return object|WP_Error The generation result with tool calls, or WP_Error.
 */
function skyyrose_ai_function_call( $prompt, $tools = array(), $provider = null, $options = array() ) {
	if ( ! function_exists( 'wp_ai_client_prompt' ) ) {
		return new WP_Error( 'ai_not_available', 'AI Client SDK not loaded.' );
	}

	$builder = wp_ai_client_prompt( $prompt );

	if ( $provider ) {
		$builder = $builder->using_provider( $provider );
	}

	if ( ! empty( $options['model'] ) ) {
		$builder = $builder->using_model( $options['model'] );
	}
	if ( isset( $options['temperature'] ) ) {
		$builder = $builder->using_temperature( (float) $options['temperature'] );
	}

	foreach ( $tools as $tool ) {
		$builder = $builder->with_function_declaration( $tool );
	}

	$result = $builder->generate_text();

	if ( is_wp_error( $result ) ) {
		return $result;
	}

	return $result;
}

/*--------------------------------------------------------------
 * Utility — Provider Status Check
 *--------------------------------------------------------------*/

/**
 * Check which AI providers are configured and available.
 *
 * @return array Keyed by provider ID, value is bool (configured or not).
 */
function skyyrose_ai_provider_status() {
	if ( ! class_exists( AiClient::class ) ) {
		return array();
	}

	$registry  = AiClient::defaultRegistry();
	$providers = array( 'openai', 'anthropic', 'google' );
	$status    = array();

	foreach ( $providers as $id ) {
		if ( ! $registry->hasProvider( $id ) ) {
			$status[ $id ] = false;
			continue;
		}
		$provider_class = $registry->getProviderClassName( $id );
		$availability   = $provider_class::availability();
		$status[ $id ]  = $availability->isConfigured();
	}

	return $status;
}
