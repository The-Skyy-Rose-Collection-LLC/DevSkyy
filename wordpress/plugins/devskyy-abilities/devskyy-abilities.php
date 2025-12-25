<?php
/**
 * DevSkyy Abilities Integration
 *
 * Registers DevSkyy AI agent capabilities as WordPress Abilities.
 * Enables WordPress sites to discover and execute DevSkyy tools.
 *
 * @package     DevSkyy
 * @author      SkyyRose LLC
 * @copyright   2024 SkyyRose LLC
 * @license     GPL-2.0-or-later
 *
 * @wordpress-plugin
 * Plugin Name:       DevSkyy Abilities
 * Plugin URI:        https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy
 * Description:       Integrates DevSkyy AI agents (85 abilities) with WordPress Abilities API.
 * Requires at least: 6.8
 * Version:           1.0.0
 * Requires PHP:      7.4
 * Author:            SkyyRose LLC
 * Author URI:        https://skyyrose.com
 * License:           GPLv2 or later
 * License URI:       https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain:       devskyy-abilities
 */

defined( 'ABSPATH' ) || exit;

// Register categories first.
add_action( 'wp_abilities_api_init', 'devskyy_register_ability_categories', 5 );

// Register all abilities.
add_action( 'wp_abilities_api_init', 'devskyy_register_commerce_abilities', 10 );
add_action( 'wp_abilities_api_init', 'devskyy_register_creative_abilities', 10 );
add_action( 'wp_abilities_api_init', 'devskyy_register_marketing_abilities', 10 );
add_action( 'wp_abilities_api_init', 'devskyy_register_support_abilities', 10 );
add_action( 'wp_abilities_api_init', 'devskyy_register_analytics_abilities', 10 );
add_action( 'wp_abilities_api_init', 'devskyy_register_operations_abilities', 10 );

/**
 * Register DevSkyy ability categories.
 */
function devskyy_register_ability_categories() {
    wp_register_ability_category( 'devskyy-commerce', array(
        'label'       => __( 'E-Commerce', 'devskyy-abilities' ),
        'description' => __( 'Product management, orders, inventory, pricing, shipping.', 'devskyy-abilities' ),
    ));
    wp_register_ability_category( 'devskyy-creative', array(
        'label'       => __( 'Creative', 'devskyy-abilities' ),
        'description' => __( 'Image, video, 3D model generation with Google/HuggingFace/Tripo3D.', 'devskyy-abilities' ),
    ));
    wp_register_ability_category( 'devskyy-marketing', array(
        'label'       => __( 'Marketing', 'devskyy-abilities' ),
        'description' => __( 'Content creation, SEO, social media, email campaigns.', 'devskyy-abilities' ),
    ));
    wp_register_ability_category( 'devskyy-support', array(
        'label'       => __( 'Customer Support', 'devskyy-abilities' ),
        'description' => __( 'Ticket handling, FAQ matching, returns, escalation.', 'devskyy-abilities' ),
    ));
    wp_register_ability_category( 'devskyy-analytics', array(
        'label'       => __( 'Analytics', 'devskyy-abilities' ),
        'description' => __( 'Reporting, forecasting, A/B testing, customer segmentation.', 'devskyy-abilities' ),
    ));
    wp_register_ability_category( 'devskyy-operations', array(
        'label'       => __( 'Operations', 'devskyy-abilities' ),
        'description' => __( 'WordPress, Elementor, deployment, monitoring, backups.', 'devskyy-abilities' ),
    ));
}

/**
 * Helper: Call DevSkyy agent API.
 */
function devskyy_call_agent( $agent_type, $action, $input ) {
    $api_endpoint = get_option( 'devskyy_api_endpoint', 'http://localhost:8000' );
    $url = trailingslashit( $api_endpoint ) . "api/v1/agents/{$agent_type}/{$action}";

    $response = wp_remote_post( $url, array(
        'headers' => array(
            'Content-Type'  => 'application/json',
            'Authorization' => 'Bearer ' . get_option( 'devskyy_api_key', '' ),
        ),
        'body'    => wp_json_encode( $input ),
        'timeout' => 120,
    ));

    if ( is_wp_error( $response ) ) {
        return $response;
    }

    $body = wp_remote_retrieve_body( $response );
    $data = json_decode( $body, true );

    if ( wp_remote_retrieve_response_code( $response ) >= 400 ) {
        return new WP_Error(
            'devskyy_api_error',
            $data['error'] ?? __( 'DevSkyy API error', 'devskyy-abilities' ),
            array( 'status' => wp_remote_retrieve_response_code( $response ) )
        );
    }

    return $data;
}

/**
 * Helper: Register ability with common defaults.
 */
function devskyy_register( $name, $args ) {
    $defaults = array(
        'permission_callback' => function() { return current_user_can( 'edit_posts' ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => false, 'destructive' => false, 'idempotent' => false ) ),
    );
    wp_register_ability( $name, array_merge( $defaults, $args ) );
}


/**
 * ============================================================================
 * COMMERCE AGENT ABILITIES (14 tools)
 * ============================================================================
 */
function devskyy_register_commerce_abilities() {
    // Product: Get Product
    devskyy_register( 'devskyy/get-product', array(
        'label'       => __( 'Get Product', 'devskyy-abilities' ),
        'description' => __( 'Get product details by SKU or ID.', 'devskyy-abilities' ),
        'category'    => 'devskyy-commerce',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'sku' => array( 'type' => 'string', 'description' => 'Product SKU' ),
                'include_stock' => array( 'type' => 'boolean', 'default' => false ),
                'include_analytics' => array( 'type' => 'boolean', 'default' => false ),
            ),
            'required' => array( 'sku' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'commerce', 'get_product', $input ); },
        'permission_callback' => function() { return current_user_can( 'edit_products' ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Product: Update Product
    devskyy_register( 'devskyy/update-product', array(
        'label'       => __( 'Update Product', 'devskyy-abilities' ),
        'description' => __( 'Update product information.', 'devskyy-abilities' ),
        'category'    => 'devskyy-commerce',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'sku' => array( 'type' => 'string', 'description' => 'Product SKU' ),
                'updates' => array( 'type' => 'object', 'description' => 'Fields to update' ),
            ),
            'required' => array( 'sku', 'updates' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'commerce', 'update_product', $input ); },
        'permission_callback' => function() { return current_user_can( 'edit_products' ); },
    ));

    // Product: Create Product
    devskyy_register( 'devskyy/create-product', array(
        'label'       => __( 'Create Product', 'devskyy-abilities' ),
        'description' => __( 'Create a new product in WooCommerce.', 'devskyy-abilities' ),
        'category'    => 'devskyy-commerce',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'name' => array( 'type' => 'string', 'description' => 'Product name' ),
                'collection' => array( 'type' => 'string', 'description' => 'Collection name' ),
                'price' => array( 'type' => 'number', 'description' => 'Base price' ),
                'description' => array( 'type' => 'string', 'description' => 'Product description' ),
                'variants' => array( 'type' => 'array', 'description' => 'Size/color variants' ),
            ),
            'required' => array( 'name', 'price' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'commerce', 'create_product', $input ); },
        'permission_callback' => function() { return current_user_can( 'publish_products' ); },
    ));

    // Inventory: Get Inventory
    devskyy_register( 'devskyy/get-inventory', array(
        'label'       => __( 'Get Inventory', 'devskyy-abilities' ),
        'description' => __( 'Get inventory levels for products.', 'devskyy-abilities' ),
        'category'    => 'devskyy-commerce',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'sku' => array( 'type' => 'string', 'description' => 'Product SKU (optional)' ),
                'warehouse' => array( 'type' => 'string', 'description' => 'Warehouse location' ),
            ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'commerce', 'get_inventory', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Inventory: Update Inventory
    devskyy_register( 'devskyy/update-inventory', array(
        'label'       => __( 'Update Inventory', 'devskyy-abilities' ),
        'description' => __( 'Update product inventory levels.', 'devskyy-abilities' ),
        'category'    => 'devskyy-commerce',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'sku' => array( 'type' => 'string', 'description' => 'Product SKU' ),
                'quantity' => array( 'type' => 'integer', 'description' => 'New quantity' ),
                'action' => array( 'type' => 'string', 'enum' => array( 'set', 'add', 'subtract' ) ),
            ),
            'required' => array( 'sku', 'quantity' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'commerce', 'update_inventory', $input ); },
    ));

    // Inventory: Forecast Demand
    devskyy_register( 'devskyy/forecast-demand', array(
        'label'       => __( 'Forecast Demand', 'devskyy-abilities' ),
        'description' => __( 'Forecast product demand using ML (Prophet).', 'devskyy-abilities' ),
        'category'    => 'devskyy-commerce',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'sku' => array( 'type' => 'string', 'description' => 'Product SKU' ),
                'days_ahead' => array( 'type' => 'integer', 'default' => 30 ),
            ),
            'required' => array( 'sku' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'commerce', 'forecast_demand', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Order: Get Order
    devskyy_register( 'devskyy/get-order', array(
        'label'       => __( 'Get Order', 'devskyy-abilities' ),
        'description' => __( 'Get order details by ID.', 'devskyy-abilities' ),
        'category'    => 'devskyy-commerce',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'order_id' => array( 'type' => 'string', 'description' => 'Order ID' ),
                'include_history' => array( 'type' => 'boolean', 'default' => false ),
            ),
            'required' => array( 'order_id' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'commerce', 'get_order', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Order: Update Order Status
    devskyy_register( 'devskyy/update-order-status', array(
        'label'       => __( 'Update Order Status', 'devskyy-abilities' ),
        'description' => __( 'Update order status and notify customer.', 'devskyy-abilities' ),
        'category'    => 'devskyy-commerce',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'order_id' => array( 'type' => 'string', 'description' => 'Order ID' ),
                'status' => array( 'type' => 'string', 'description' => 'New status' ),
                'notify_customer' => array( 'type' => 'boolean', 'default' => true ),
            ),
            'required' => array( 'order_id', 'status' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'commerce', 'update_order_status', $input ); },
    ));

    // Order: Process Return
    devskyy_register( 'devskyy/process-return', array(
        'label'       => __( 'Process Return', 'devskyy-abilities' ),
        'description' => __( 'Process a return request.', 'devskyy-abilities' ),
        'category'    => 'devskyy-commerce',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'order_id' => array( 'type' => 'string', 'description' => 'Order ID' ),
                'items' => array( 'type' => 'array', 'description' => 'Items to return' ),
                'reason' => array( 'type' => 'string', 'description' => 'Return reason' ),
            ),
            'required' => array( 'order_id', 'items' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'commerce', 'process_return', $input ); },
    ));

    // Pricing: Calculate Price
    devskyy_register( 'devskyy/calculate-price', array(
        'label'       => __( 'Calculate Dynamic Price', 'devskyy-abilities' ),
        'description' => __( 'Calculate dynamic pricing based on demand and competition.', 'devskyy-abilities' ),
        'category'    => 'devskyy-commerce',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'sku' => array( 'type' => 'string', 'description' => 'Product SKU' ),
                'factors' => array( 'type' => 'object', 'description' => 'Pricing factors' ),
            ),
            'required' => array( 'sku' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'commerce', 'calculate_price', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Pricing: Create Promotion
    devskyy_register( 'devskyy/create-promotion', array(
        'label'       => __( 'Create Promotion', 'devskyy-abilities' ),
        'description' => __( 'Create a promotional discount.', 'devskyy-abilities' ),
        'category'    => 'devskyy-commerce',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'name' => array( 'type' => 'string', 'description' => 'Promotion name' ),
                'discount_type' => array( 'type' => 'string', 'enum' => array( 'percentage', 'fixed' ) ),
                'discount_value' => array( 'type' => 'number', 'description' => 'Discount amount' ),
                'products' => array( 'type' => 'array', 'description' => 'Applicable SKUs' ),
                'start_date' => array( 'type' => 'string', 'format' => 'date-time' ),
                'end_date' => array( 'type' => 'string', 'format' => 'date-time' ),
            ),
            'required' => array( 'name', 'discount_type', 'discount_value' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'commerce', 'create_promotion', $input ); },
    ));

    // Shipping: Get Shipping Rates
    devskyy_register( 'devskyy/get-shipping-rates', array(
        'label'       => __( 'Get Shipping Rates', 'devskyy-abilities' ),
        'description' => __( 'Get shipping options and rates for destination.', 'devskyy-abilities' ),
        'category'    => 'devskyy-commerce',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'destination' => array( 'type' => 'object', 'description' => 'Destination address' ),
                'items' => array( 'type' => 'array', 'description' => 'Items to ship' ),
                'carriers' => array( 'type' => 'array', 'description' => 'Preferred carriers' ),
            ),
            'required' => array( 'destination', 'items' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'commerce', 'get_shipping_rates', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Shipping: Create Shipment
    devskyy_register( 'devskyy/create-shipment', array(
        'label'       => __( 'Create Shipment', 'devskyy-abilities' ),
        'description' => __( 'Create a shipment for an order.', 'devskyy-abilities' ),
        'category'    => 'devskyy-commerce',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'order_id' => array( 'type' => 'string', 'description' => 'Order ID' ),
                'carrier' => array( 'type' => 'string', 'description' => 'Shipping carrier' ),
                'service' => array( 'type' => 'string', 'description' => 'Service level' ),
            ),
            'required' => array( 'order_id', 'carrier' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'commerce', 'create_shipment', $input ); },
    ));

    // Shipping: Track Shipment
    devskyy_register( 'devskyy/track-shipment', array(
        'label'       => __( 'Track Shipment', 'devskyy-abilities' ),
        'description' => __( 'Get shipment tracking information.', 'devskyy-abilities' ),
        'category'    => 'devskyy-commerce',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'tracking_number' => array( 'type' => 'string', 'description' => 'Tracking number' ),
                'carrier' => array( 'type' => 'string', 'description' => 'Carrier name' ),
            ),
            'required' => array( 'tracking_number' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'commerce', 'track_shipment', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));
}


/**
 * ============================================================================
 * CREATIVE AGENT ABILITIES (11 tools)
 * ============================================================================
 */
function devskyy_register_creative_abilities() {
    // Image: Generate with Google Imagen
    devskyy_register( 'devskyy/generate-image-google', array(
        'label'       => __( 'Generate Image (Google Imagen)', 'devskyy-abilities' ),
        'description' => __( 'Generate image using Google Imagen 3.', 'devskyy-abilities' ),
        'category'    => 'devskyy-creative',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'prompt' => array( 'type' => 'string', 'description' => 'Image generation prompt' ),
                'style' => array( 'type' => 'string', 'description' => 'Style preset' ),
                'aspect_ratio' => array( 'type' => 'string', 'enum' => array( '1:1', '16:9', '9:16', '4:3' ) ),
                'negative_prompt' => array( 'type' => 'string', 'description' => 'What to avoid' ),
            ),
            'required' => array( 'prompt' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'creative', 'generate_image_google', $input ); },
        'permission_callback' => function() { return current_user_can( 'upload_files' ); },
    ));

    // Image: Generate with FLUX
    devskyy_register( 'devskyy/generate-image-flux', array(
        'label'       => __( 'Generate Image (HuggingFace FLUX)', 'devskyy-abilities' ),
        'description' => __( 'Generate high-quality image using HuggingFace FLUX.1.', 'devskyy-abilities' ),
        'category'    => 'devskyy-creative',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'prompt' => array( 'type' => 'string', 'description' => 'Image generation prompt' ),
                'width' => array( 'type' => 'integer', 'default' => 1024 ),
                'height' => array( 'type' => 'integer', 'default' => 1024 ),
                'guidance_scale' => array( 'type' => 'number', 'default' => 7.5 ),
                'num_inference_steps' => array( 'type' => 'integer', 'default' => 50 ),
            ),
            'required' => array( 'prompt' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'creative', 'generate_image_flux', $input ); },
        'permission_callback' => function() { return current_user_can( 'upload_files' ); },
    ));

    // Video: Generate with Veo
    devskyy_register( 'devskyy/generate-video-veo', array(
        'label'       => __( 'Generate Video (Google Veo)', 'devskyy-abilities' ),
        'description' => __( 'Generate video using Google Veo 2.', 'devskyy-abilities' ),
        'category'    => 'devskyy-creative',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'prompt' => array( 'type' => 'string', 'description' => 'Video generation prompt' ),
                'duration' => array( 'type' => 'integer', 'default' => 5, 'description' => 'Duration in seconds' ),
                'aspect_ratio' => array( 'type' => 'string', 'enum' => array( '16:9', '9:16', '1:1' ) ),
                'style' => array( 'type' => 'string', 'description' => 'Visual style' ),
            ),
            'required' => array( 'prompt' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'creative', 'generate_video_veo', $input ); },
        'permission_callback' => function() { return current_user_can( 'upload_files' ); },
    ));

    // 3D: Generate from Image
    devskyy_register( 'devskyy/generate-3d-model', array(
        'label'       => __( 'Generate 3D Model from Image', 'devskyy-abilities' ),
        'description' => __( 'Generate 3D model from image using Tripo3D.', 'devskyy-abilities' ),
        'category'    => 'devskyy-creative',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'image_url' => array( 'type' => 'string', 'format' => 'uri', 'description' => 'Source image URL' ),
                'quality' => array( 'type' => 'string', 'enum' => array( 'draft', 'standard', 'premium' ) ),
                'format' => array( 'type' => 'string', 'enum' => array( 'glb', 'gltf', 'fbx' ) ),
                'texture_quality' => array( 'type' => 'string', 'description' => 'Texture quality' ),
            ),
            'required' => array( 'image_url' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'creative', 'generate_3d_model', $input ); },
        'permission_callback' => function() { return current_user_can( 'upload_files' ); },
    ));

    // 3D: Generate from Text
    devskyy_register( 'devskyy/generate-3d-from-text', array(
        'label'       => __( 'Generate 3D Model from Text', 'devskyy-abilities' ),
        'description' => __( 'Generate 3D model from text description.', 'devskyy-abilities' ),
        'category'    => 'devskyy-creative',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'prompt' => array( 'type' => 'string', 'description' => '3D model description' ),
                'style' => array( 'type' => 'string', 'description' => 'Visual style' ),
                'format' => array( 'type' => 'string', 'enum' => array( 'glb', 'gltf', 'fbx' ) ),
            ),
            'required' => array( 'prompt' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'creative', 'generate_3d_from_text', $input ); },
        'permission_callback' => function() { return current_user_can( 'upload_files' ); },
    ));

    // Virtual Try-On (FASHN)
    devskyy_register( 'devskyy/virtual-tryon', array(
        'label'       => __( 'Virtual Try-On', 'devskyy-abilities' ),
        'description' => __( 'Apply garment to model image using FASHN.', 'devskyy-abilities' ),
        'category'    => 'devskyy-creative',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'garment_image' => array( 'type' => 'string', 'format' => 'uri', 'description' => 'Garment image URL' ),
                'model_image' => array( 'type' => 'string', 'format' => 'uri', 'description' => 'Model/person image URL' ),
                'category' => array( 'type' => 'string', 'enum' => array( 'tops', 'bottoms', 'dresses' ) ),
                'adjust_hands' => array( 'type' => 'boolean', 'default' => true ),
            ),
            'required' => array( 'garment_image', 'model_image' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'creative', 'virtual_tryon', $input ); },
        'permission_callback' => function() { return current_user_can( 'upload_files' ); },
    ));

    // AI Model Generation
    devskyy_register( 'devskyy/generate-ai-model', array(
        'label'       => __( 'Generate AI Fashion Model', 'devskyy-abilities' ),
        'description' => __( 'Generate AI fashion model wearing garment.', 'devskyy-abilities' ),
        'category'    => 'devskyy-creative',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'garment_image' => array( 'type' => 'string', 'format' => 'uri', 'description' => 'Garment image URL' ),
                'model_attributes' => array( 'type' => 'object', 'description' => 'Model characteristics' ),
                'pose' => array( 'type' => 'string', 'description' => 'Model pose' ),
                'background' => array( 'type' => 'string', 'description' => 'Background setting' ),
            ),
            'required' => array( 'garment_image' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'creative', 'generate_ai_model', $input ); },
        'permission_callback' => function() { return current_user_can( 'upload_files' ); },
    ));

    // Remove Background
    devskyy_register( 'devskyy/remove-background', array(
        'label'       => __( 'Remove Background', 'devskyy-abilities' ),
        'description' => __( 'Remove background from image.', 'devskyy-abilities' ),
        'category'    => 'devskyy-creative',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'image_url' => array( 'type' => 'string', 'format' => 'uri', 'description' => 'Image URL' ),
                'output_format' => array( 'type' => 'string', 'enum' => array( 'png', 'webp' ) ),
            ),
            'required' => array( 'image_url' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'creative', 'remove_background', $input ); },
        'permission_callback' => function() { return current_user_can( 'upload_files' ); },
    ));

    // Enhance Image
    devskyy_register( 'devskyy/enhance-image', array(
        'label'       => __( 'Enhance Image', 'devskyy-abilities' ),
        'description' => __( 'Enhance and optimize image quality.', 'devskyy-abilities' ),
        'category'    => 'devskyy-creative',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'image_url' => array( 'type' => 'string', 'format' => 'uri', 'description' => 'Image URL' ),
                'enhancements' => array( 'type' => 'array', 'description' => 'Enhancement types' ),
                'target_resolution' => array( 'type' => 'string', 'description' => 'Target resolution' ),
            ),
            'required' => array( 'image_url' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'creative', 'enhance_image', $input ); },
        'permission_callback' => function() { return current_user_can( 'upload_files' ); },
    ));

    // Upload Asset
    devskyy_register( 'devskyy/upload-asset', array(
        'label'       => __( 'Upload Asset to WordPress', 'devskyy-abilities' ),
        'description' => __( 'Upload asset to WordPress media library.', 'devskyy-abilities' ),
        'category'    => 'devskyy-creative',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'file_url' => array( 'type' => 'string', 'format' => 'uri', 'description' => 'Asset URL' ),
                'title' => array( 'type' => 'string', 'description' => 'Asset title' ),
                'alt_text' => array( 'type' => 'string', 'description' => 'Alt text' ),
                'categories' => array( 'type' => 'array', 'description' => 'Asset categories' ),
            ),
            'required' => array( 'file_url' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'creative', 'upload_asset', $input ); },
        'permission_callback' => function() { return current_user_can( 'upload_files' ); },
    ));

    // Search Assets
    devskyy_register( 'devskyy/search-assets', array(
        'label'       => __( 'Search Brand Assets', 'devskyy-abilities' ),
        'description' => __( 'Search brand asset library.', 'devskyy-abilities' ),
        'category'    => 'devskyy-creative',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'query' => array( 'type' => 'string', 'description' => 'Search query' ),
                'asset_type' => array( 'type' => 'string', 'enum' => array( 'image', 'video', '3d' ) ),
                'collection' => array( 'type' => 'string', 'description' => 'Collection filter' ),
            ),
            'required' => array( 'query' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'creative', 'search_assets', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));
}


/**
 * ============================================================================
 * MARKETING AGENT ABILITIES (14 tools)
 * ============================================================================
 */
function devskyy_register_marketing_abilities() {
    // Content: Create Content
    devskyy_register( 'devskyy/create-content', array(
        'label'       => __( 'Create Marketing Content', 'devskyy-abilities' ),
        'description' => __( 'Create marketing content for various channels.', 'devskyy-abilities' ),
        'category'    => 'devskyy-marketing',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'content_type' => array( 'type' => 'string', 'enum' => array( 'post', 'blog', 'email', 'ad' ) ),
                'channel' => array( 'type' => 'string', 'description' => 'Target channel' ),
                'topic' => array( 'type' => 'string', 'description' => 'Content topic' ),
                'tone' => array( 'type' => 'string', 'description' => 'Tone override' ),
                'length' => array( 'type' => 'string', 'enum' => array( 'short', 'medium', 'long' ) ),
            ),
            'required' => array( 'content_type', 'topic' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'marketing', 'create_content', $input ); },
    ));

    // Content: Generate Hashtags
    devskyy_register( 'devskyy/generate-hashtags', array(
        'label'       => __( 'Generate Hashtags', 'devskyy-abilities' ),
        'description' => __( 'Generate relevant hashtags for social content.', 'devskyy-abilities' ),
        'category'    => 'devskyy-marketing',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'content' => array( 'type' => 'string', 'description' => 'Content to tag' ),
                'platform' => array( 'type' => 'string', 'enum' => array( 'instagram', 'twitter', 'tiktok', 'linkedin' ) ),
                'count' => array( 'type' => 'integer', 'default' => 10 ),
            ),
            'required' => array( 'content' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'marketing', 'generate_hashtags', $input ); },
    ));

    // Content: Optimize Content
    devskyy_register( 'devskyy/optimize-content', array(
        'label'       => __( 'Optimize Content', 'devskyy-abilities' ),
        'description' => __( 'Optimize content for engagement.', 'devskyy-abilities' ),
        'category'    => 'devskyy-marketing',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'content' => array( 'type' => 'string', 'description' => 'Content to optimize' ),
                'optimization_type' => array( 'type' => 'string', 'enum' => array( 'seo', 'engagement', 'conversion' ) ),
            ),
            'required' => array( 'content', 'optimization_type' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'marketing', 'optimize_content', $input ); },
    ));

    // Social: Schedule Post
    devskyy_register( 'devskyy/schedule-post', array(
        'label'       => __( 'Schedule Social Post', 'devskyy-abilities' ),
        'description' => __( 'Schedule social media post.', 'devskyy-abilities' ),
        'category'    => 'devskyy-marketing',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'platform' => array( 'type' => 'string', 'enum' => array( 'instagram', 'facebook', 'twitter', 'tiktok', 'linkedin' ) ),
                'content' => array( 'type' => 'string', 'description' => 'Post content' ),
                'scheduled_time' => array( 'type' => 'string', 'format' => 'date-time' ),
                'media' => array( 'type' => 'array', 'description' => 'Media attachments' ),
            ),
            'required' => array( 'platform', 'content', 'scheduled_time' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'marketing', 'schedule_post', $input ); },
    ));

    // Social: Analyze Engagement
    devskyy_register( 'devskyy/analyze-engagement', array(
        'label'       => __( 'Analyze Social Engagement', 'devskyy-abilities' ),
        'description' => __( 'Analyze social media engagement metrics.', 'devskyy-abilities' ),
        'category'    => 'devskyy-marketing',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'platform' => array( 'type' => 'string', 'description' => 'Platform to analyze' ),
                'time_period' => array( 'type' => 'string', 'description' => 'Analysis period' ),
                'metrics' => array( 'type' => 'array', 'description' => 'Metrics to include' ),
            ),
            'required' => array( 'platform' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'marketing', 'analyze_engagement', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // SEO: Keyword Research
    devskyy_register( 'devskyy/keyword-research', array(
        'label'       => __( 'Keyword Research', 'devskyy-abilities' ),
        'description' => __( 'Research keywords for SEO optimization.', 'devskyy-abilities' ),
        'category'    => 'devskyy-marketing',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'seed_keywords' => array( 'type' => 'array', 'description' => 'Starting keywords' ),
                'intent' => array( 'type' => 'string', 'enum' => array( 'informational', 'transactional', 'navigational' ) ),
                'competition' => array( 'type' => 'string', 'enum' => array( 'low', 'medium', 'high' ) ),
            ),
            'required' => array( 'seed_keywords' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'marketing', 'keyword_research', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // SEO: Analyze SEO
    devskyy_register( 'devskyy/analyze-seo', array(
        'label'       => __( 'Analyze Page SEO', 'devskyy-abilities' ),
        'description' => __( 'Analyze page SEO performance.', 'devskyy-abilities' ),
        'category'    => 'devskyy-marketing',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'url' => array( 'type' => 'string', 'format' => 'uri', 'description' => 'Page URL' ),
                'target_keywords' => array( 'type' => 'array', 'description' => 'Target keywords' ),
            ),
            'required' => array( 'url' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'marketing', 'analyze_seo', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // SEO: Generate Meta Tags
    devskyy_register( 'devskyy/generate-meta', array(
        'label'       => __( 'Generate SEO Meta Tags', 'devskyy-abilities' ),
        'description' => __( 'Generate SEO meta tags for a page.', 'devskyy-abilities' ),
        'category'    => 'devskyy-marketing',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'page_content' => array( 'type' => 'string', 'description' => 'Page content summary' ),
                'target_keywords' => array( 'type' => 'array', 'description' => 'Target keywords' ),
                'page_type' => array( 'type' => 'string', 'enum' => array( 'product', 'collection', 'blog', 'home' ) ),
            ),
            'required' => array( 'page_content' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'marketing', 'generate_meta', $input ); },
    ));

    // Email: Create Campaign
    devskyy_register( 'devskyy/create-email', array(
        'label'       => __( 'Create Email Campaign', 'devskyy-abilities' ),
        'description' => __( 'Create email campaign content.', 'devskyy-abilities' ),
        'category'    => 'devskyy-marketing',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'campaign_type' => array( 'type' => 'string', 'enum' => array( 'promotional', 'newsletter', 'transactional', 'welcome' ) ),
                'subject_variants' => array( 'type' => 'integer', 'default' => 3 ),
                'audience_segment' => array( 'type' => 'string', 'description' => 'Target segment' ),
                'goal' => array( 'type' => 'string', 'description' => 'Campaign goal' ),
            ),
            'required' => array( 'campaign_type', 'goal' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'marketing', 'create_email', $input ); },
    ));

    // Email: Analyze Metrics
    devskyy_register( 'devskyy/analyze-email-metrics', array(
        'label'       => __( 'Analyze Email Metrics', 'devskyy-abilities' ),
        'description' => __( 'Analyze email campaign performance.', 'devskyy-abilities' ),
        'category'    => 'devskyy-marketing',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'campaign_id' => array( 'type' => 'string', 'description' => 'Campaign ID' ),
                'metrics' => array( 'type' => 'array', 'description' => 'Metrics to analyze' ),
            ),
            'required' => array( 'campaign_id' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'marketing', 'analyze_email_metrics', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Influencer: Find Influencers
    devskyy_register( 'devskyy/find-influencers', array(
        'label'       => __( 'Find Influencers', 'devskyy-abilities' ),
        'description' => __( 'Find brand-aligned influencers.', 'devskyy-abilities' ),
        'category'    => 'devskyy-marketing',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'niche' => array( 'type' => 'string', 'description' => 'Influencer niche' ),
                'follower_range' => array( 'type' => 'object', 'description' => 'Follower count range' ),
                'platforms' => array( 'type' => 'array', 'description' => 'Target platforms' ),
                'engagement_threshold' => array( 'type' => 'number', 'description' => 'Min engagement rate' ),
            ),
            'required' => array( 'niche' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'marketing', 'find_influencers', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Influencer: Create Outreach
    devskyy_register( 'devskyy/create-outreach', array(
        'label'       => __( 'Create Influencer Outreach', 'devskyy-abilities' ),
        'description' => __( 'Create influencer outreach message.', 'devskyy-abilities' ),
        'category'    => 'devskyy-marketing',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'influencer_name' => array( 'type' => 'string', 'description' => 'Influencer name' ),
                'campaign_brief' => array( 'type' => 'string', 'description' => 'Campaign details' ),
                'collaboration_type' => array( 'type' => 'string', 'description' => 'Type of collaboration' ),
            ),
            'required' => array( 'influencer_name', 'campaign_brief' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'marketing', 'create_outreach', $input ); },
    ));

    // Campaign: Get Metrics
    devskyy_register( 'devskyy/get-campaign-metrics', array(
        'label'       => __( 'Get Campaign Metrics', 'devskyy-abilities' ),
        'description' => __( 'Get campaign performance metrics.', 'devskyy-abilities' ),
        'category'    => 'devskyy-marketing',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'campaign_id' => array( 'type' => 'string', 'description' => 'Campaign ID' ),
                'date_range' => array( 'type' => 'object', 'description' => 'Start and end dates' ),
            ),
            'required' => array( 'campaign_id' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'marketing', 'get_campaign_metrics', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Campaign: Generate Report
    devskyy_register( 'devskyy/marketing-report', array(
        'label'       => __( 'Generate Marketing Report', 'devskyy-abilities' ),
        'description' => __( 'Generate marketing performance report.', 'devskyy-abilities' ),
        'category'    => 'devskyy-marketing',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'report_type' => array( 'type' => 'string', 'description' => 'Report type' ),
                'time_period' => array( 'type' => 'string', 'description' => 'Reporting period' ),
                'channels' => array( 'type' => 'array', 'description' => 'Channels to include' ),
            ),
            'required' => array( 'report_type' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'marketing', 'generate_report', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));
}


/**
 * ============================================================================
 * SUPPORT AGENT ABILITIES (13 tools)
 * ============================================================================
 */
function devskyy_register_support_abilities() {
    // FAQ: Search
    devskyy_register( 'devskyy/search-faq', array(
        'label'       => __( 'Search FAQ', 'devskyy-abilities' ),
        'description' => __( 'Search FAQ knowledge base with ML matching.', 'devskyy-abilities' ),
        'category'    => 'devskyy-support',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'query' => array( 'type' => 'string', 'description' => 'Customer question' ),
                'category' => array( 'type' => 'string', 'description' => 'FAQ category' ),
                'threshold' => array( 'type' => 'number', 'default' => 0.7, 'description' => 'Confidence threshold' ),
            ),
            'required' => array( 'query' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'support', 'search_faq', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Intent: Classify
    devskyy_register( 'devskyy/classify-intent', array(
        'label'       => __( 'Classify Customer Intent', 'devskyy-abilities' ),
        'description' => __( 'Classify customer intent using ML.', 'devskyy-abilities' ),
        'category'    => 'devskyy-support',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'message' => array( 'type' => 'string', 'description' => 'Customer message' ),
                'context' => array( 'type' => 'object', 'description' => 'Conversation context' ),
            ),
            'required' => array( 'message' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'support', 'classify_intent', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Order: Lookup
    devskyy_register( 'devskyy/lookup-order', array(
        'label'       => __( 'Lookup Customer Order', 'devskyy-abilities' ),
        'description' => __( 'Look up order details for support.', 'devskyy-abilities' ),
        'category'    => 'devskyy-support',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'order_id' => array( 'type' => 'string', 'description' => 'Order ID' ),
                'email' => array( 'type' => 'string', 'format' => 'email', 'description' => 'Customer email' ),
            ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'support', 'lookup_order', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Order: Track Shipment
    devskyy_register( 'devskyy/support-track-shipment', array(
        'label'       => __( 'Track Shipment (Support)', 'devskyy-abilities' ),
        'description' => __( 'Get shipment tracking status for customer.', 'devskyy-abilities' ),
        'category'    => 'devskyy-support',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'order_id' => array( 'type' => 'string', 'description' => 'Order ID' ),
                'tracking_number' => array( 'type' => 'string', 'description' => 'Tracking number' ),
            ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'support', 'track_shipment', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Order: Update
    devskyy_register( 'devskyy/support-update-order', array(
        'label'       => __( 'Update Order (Support)', 'devskyy-abilities' ),
        'description' => __( 'Update order (cancel, modify address).', 'devskyy-abilities' ),
        'category'    => 'devskyy-support',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'order_id' => array( 'type' => 'string', 'description' => 'Order ID' ),
                'action' => array( 'type' => 'string', 'enum' => array( 'cancel', 'modify_address', 'add_note' ) ),
                'details' => array( 'type' => 'object', 'description' => 'Update details' ),
            ),
            'required' => array( 'order_id', 'action' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'support', 'update_order', $input ); },
    ));

    // Return: Initiate
    devskyy_register( 'devskyy/initiate-return', array(
        'label'       => __( 'Initiate Return', 'devskyy-abilities' ),
        'description' => __( 'Start return process for customer.', 'devskyy-abilities' ),
        'category'    => 'devskyy-support',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'order_id' => array( 'type' => 'string', 'description' => 'Order ID' ),
                'items' => array( 'type' => 'array', 'description' => 'Items to return' ),
                'reason' => array( 'type' => 'string', 'description' => 'Return reason' ),
                'preference' => array( 'type' => 'string', 'enum' => array( 'refund', 'exchange' ) ),
            ),
            'required' => array( 'order_id', 'items' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'support', 'initiate_return', $input ); },
    ));

    // Return: Process Refund
    devskyy_register( 'devskyy/process-refund', array(
        'label'       => __( 'Process Refund', 'devskyy-abilities' ),
        'description' => __( 'Process refund for customer order.', 'devskyy-abilities' ),
        'category'    => 'devskyy-support',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'order_id' => array( 'type' => 'string', 'description' => 'Order ID' ),
                'amount' => array( 'type' => 'number', 'description' => 'Refund amount' ),
                'reason' => array( 'type' => 'string', 'description' => 'Refund reason' ),
            ),
            'required' => array( 'order_id', 'amount' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'support', 'process_refund', $input ); },
    ));

    // Return: Check Status
    devskyy_register( 'devskyy/check-return-status', array(
        'label'       => __( 'Check Return Status', 'devskyy-abilities' ),
        'description' => __( 'Check status of a return.', 'devskyy-abilities' ),
        'category'    => 'devskyy-support',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'return_id' => array( 'type' => 'string', 'description' => 'Return ID' ),
                'order_id' => array( 'type' => 'string', 'description' => 'Original order ID' ),
            ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'support', 'check_return_status', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Ticket: Create
    devskyy_register( 'devskyy/create-ticket', array(
        'label'       => __( 'Create Support Ticket', 'devskyy-abilities' ),
        'description' => __( 'Create a new support ticket.', 'devskyy-abilities' ),
        'category'    => 'devskyy-support',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'customer_email' => array( 'type' => 'string', 'format' => 'email', 'description' => 'Customer email' ),
                'subject' => array( 'type' => 'string', 'description' => 'Ticket subject' ),
                'description' => array( 'type' => 'string', 'description' => 'Issue description' ),
                'priority' => array( 'type' => 'string', 'enum' => array( 'low', 'medium', 'high', 'urgent' ) ),
                'category' => array( 'type' => 'string', 'description' => 'Issue category' ),
            ),
            'required' => array( 'customer_email', 'subject', 'description' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'support', 'create_ticket', $input ); },
    ));

    // Ticket: Update
    devskyy_register( 'devskyy/update-ticket', array(
        'label'       => __( 'Update Support Ticket', 'devskyy-abilities' ),
        'description' => __( 'Update ticket status or add notes.', 'devskyy-abilities' ),
        'category'    => 'devskyy-support',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'ticket_id' => array( 'type' => 'string', 'description' => 'Ticket ID' ),
                'status' => array( 'type' => 'string', 'enum' => array( 'open', 'pending', 'resolved', 'closed' ) ),
                'notes' => array( 'type' => 'string', 'description' => 'Internal notes' ),
                'response' => array( 'type' => 'string', 'description' => 'Customer response' ),
            ),
            'required' => array( 'ticket_id' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'support', 'update_ticket', $input ); },
    ));

    // Ticket: Escalate
    devskyy_register( 'devskyy/escalate-ticket', array(
        'label'       => __( 'Escalate Ticket', 'devskyy-abilities' ),
        'description' => __( 'Escalate ticket to human agent.', 'devskyy-abilities' ),
        'category'    => 'devskyy-support',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'ticket_id' => array( 'type' => 'string', 'description' => 'Ticket ID' ),
                'reason' => array( 'type' => 'string', 'description' => 'Escalation reason' ),
                'priority' => array( 'type' => 'string', 'enum' => array( 'medium', 'high', 'urgent' ) ),
                'summary' => array( 'type' => 'string', 'description' => 'Issue summary' ),
            ),
            'required' => array( 'ticket_id', 'reason' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'support', 'escalate_ticket', $input ); },
    ));

    // Customer: Get History
    devskyy_register( 'devskyy/get-customer-history', array(
        'label'       => __( 'Get Customer History', 'devskyy-abilities' ),
        'description' => __( 'Get customer order and support history.', 'devskyy-abilities' ),
        'category'    => 'devskyy-support',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'customer_id' => array( 'type' => 'string', 'description' => 'Customer ID' ),
                'email' => array( 'type' => 'string', 'format' => 'email', 'description' => 'Customer email' ),
            ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'support', 'get_customer_history', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Customer: Add Note
    devskyy_register( 'devskyy/add-customer-note', array(
        'label'       => __( 'Add Customer Note', 'devskyy-abilities' ),
        'description' => __( 'Add note to customer profile.', 'devskyy-abilities' ),
        'category'    => 'devskyy-support',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'customer_id' => array( 'type' => 'string', 'description' => 'Customer ID' ),
                'note' => array( 'type' => 'string', 'description' => 'Note content' ),
                'category' => array( 'type' => 'string', 'description' => 'Note category' ),
            ),
            'required' => array( 'customer_id', 'note' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'support', 'add_customer_note', $input ); },
    ));
}


/**
 * ============================================================================
 * ANALYTICS AGENT ABILITIES (15 tools)
 * ============================================================================
 */
function devskyy_register_analytics_abilities() {
    // Report: Generate
    devskyy_register( 'devskyy/analytics-report', array(
        'label'       => __( 'Generate Analytics Report', 'devskyy-abilities' ),
        'description' => __( 'Generate comprehensive analytics report.', 'devskyy-abilities' ),
        'category'    => 'devskyy-analytics',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'report_type' => array( 'type' => 'string', 'enum' => array( 'sales', 'traffic', 'conversion', 'customer' ) ),
                'date_range' => array( 'type' => 'object', 'description' => 'Start and end dates' ),
                'dimensions' => array( 'type' => 'array', 'description' => 'Report dimensions' ),
                'metrics' => array( 'type' => 'array', 'description' => 'Metrics to include' ),
            ),
            'required' => array( 'report_type' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'analytics', 'generate_report', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Report: KPI Dashboard
    devskyy_register( 'devskyy/get-kpi-dashboard', array(
        'label'       => __( 'Get KPI Dashboard', 'devskyy-abilities' ),
        'description' => __( 'Get real-time KPI dashboard data.', 'devskyy-abilities' ),
        'category'    => 'devskyy-analytics',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'kpis' => array( 'type' => 'array', 'description' => 'KPIs to include' ),
                'comparison_period' => array( 'type' => 'string', 'description' => 'Comparison period' ),
            ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'analytics', 'get_kpi_dashboard', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Report: Export
    devskyy_register( 'devskyy/export-report', array(
        'label'       => __( 'Export Report', 'devskyy-abilities' ),
        'description' => __( 'Export report to various formats.', 'devskyy-abilities' ),
        'category'    => 'devskyy-analytics',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'report_id' => array( 'type' => 'string', 'description' => 'Report ID' ),
                'format' => array( 'type' => 'string', 'enum' => array( 'csv', 'xlsx', 'pdf', 'json' ) ),
                'include_charts' => array( 'type' => 'boolean', 'default' => true ),
            ),
            'required' => array( 'report_id', 'format' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'analytics', 'export_report', $input ); },
    ));

    // Customer: Segment
    devskyy_register( 'devskyy/segment-customers', array(
        'label'       => __( 'Segment Customers', 'devskyy-abilities' ),
        'description' => __( 'Segment customers using ML clustering.', 'devskyy-abilities' ),
        'category'    => 'devskyy-analytics',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'criteria' => array( 'type' => 'array', 'description' => 'Segmentation criteria' ),
                'num_segments' => array( 'type' => 'integer', 'default' => 5 ),
                'algorithm' => array( 'type' => 'string', 'enum' => array( 'kmeans', 'rfm', 'behavioral' ) ),
            ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'analytics', 'segment_customers', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Customer: Cohort Analysis
    devskyy_register( 'devskyy/analyze-cohort', array(
        'label'       => __( 'Analyze Customer Cohort', 'devskyy-abilities' ),
        'description' => __( 'Perform cohort analysis on customers.', 'devskyy-abilities' ),
        'category'    => 'devskyy-analytics',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'cohort_type' => array( 'type' => 'string', 'enum' => array( 'acquisition', 'behavior', 'value' ) ),
                'time_period' => array( 'type' => 'string', 'description' => 'Analysis period' ),
                'metrics' => array( 'type' => 'array', 'description' => 'Metrics to track' ),
            ),
            'required' => array( 'cohort_type' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'analytics', 'analyze_cohort', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Customer: Predict Churn
    devskyy_register( 'devskyy/predict-churn', array(
        'label'       => __( 'Predict Customer Churn', 'devskyy-abilities' ),
        'description' => __( 'Predict customer churn probability.', 'devskyy-abilities' ),
        'category'    => 'devskyy-analytics',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'customer_ids' => array( 'type' => 'array', 'description' => 'Customer IDs to analyze' ),
                'threshold' => array( 'type' => 'number', 'default' => 0.7, 'description' => 'Risk threshold' ),
            ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'analytics', 'predict_churn', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Forecast: Sales
    devskyy_register( 'devskyy/forecast-sales', array(
        'label'       => __( 'Forecast Sales', 'devskyy-abilities' ),
        'description' => __( 'Forecast future sales using ML.', 'devskyy-abilities' ),
        'category'    => 'devskyy-analytics',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'horizon' => array( 'type' => 'integer', 'default' => 30, 'description' => 'Forecast days' ),
                'granularity' => array( 'type' => 'string', 'enum' => array( 'daily', 'weekly', 'monthly' ) ),
                'include_seasonality' => array( 'type' => 'boolean', 'default' => true ),
            ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'analytics', 'forecast_sales', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Forecast: Demand
    devskyy_register( 'devskyy/analytics-forecast-demand', array(
        'label'       => __( 'Forecast Product Demand', 'devskyy-abilities' ),
        'description' => __( 'Forecast product demand for inventory.', 'devskyy-abilities' ),
        'category'    => 'devskyy-analytics',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'product_ids' => array( 'type' => 'array', 'description' => 'Products to forecast' ),
                'horizon' => array( 'type' => 'integer', 'default' => 30 ),
                'include_promotions' => array( 'type' => 'boolean', 'default' => true ),
            ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'analytics', 'forecast_demand', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Experiment: Create
    devskyy_register( 'devskyy/create-experiment', array(
        'label'       => __( 'Create A/B Experiment', 'devskyy-abilities' ),
        'description' => __( 'Create A/B testing experiment.', 'devskyy-abilities' ),
        'category'    => 'devskyy-analytics',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'name' => array( 'type' => 'string', 'description' => 'Experiment name' ),
                'variants' => array( 'type' => 'array', 'description' => 'Test variants' ),
                'metric' => array( 'type' => 'string', 'description' => 'Primary metric' ),
                'traffic_split' => array( 'type' => 'object', 'description' => 'Traffic allocation' ),
            ),
            'required' => array( 'name', 'variants', 'metric' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'analytics', 'create_experiment', $input ); },
    ));

    // Experiment: Analyze
    devskyy_register( 'devskyy/analyze-experiment', array(
        'label'       => __( 'Analyze Experiment Results', 'devskyy-abilities' ),
        'description' => __( 'Analyze A/B experiment results.', 'devskyy-abilities' ),
        'category'    => 'devskyy-analytics',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'experiment_id' => array( 'type' => 'string', 'description' => 'Experiment ID' ),
                'confidence_level' => array( 'type' => 'number', 'default' => 0.95 ),
            ),
            'required' => array( 'experiment_id' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'analytics', 'analyze_experiment', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Experiment: Sample Size
    devskyy_register( 'devskyy/calculate-sample-size', array(
        'label'       => __( 'Calculate Sample Size', 'devskyy-abilities' ),
        'description' => __( 'Calculate required sample size for experiment.', 'devskyy-abilities' ),
        'category'    => 'devskyy-analytics',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'baseline_rate' => array( 'type' => 'number', 'description' => 'Current conversion rate' ),
                'minimum_effect' => array( 'type' => 'number', 'description' => 'Minimum detectable effect' ),
                'power' => array( 'type' => 'number', 'default' => 0.8 ),
                'significance' => array( 'type' => 'number', 'default' => 0.05 ),
            ),
            'required' => array( 'baseline_rate', 'minimum_effect' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'analytics', 'calculate_sample_size', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Trends: Analyze
    devskyy_register( 'devskyy/analyze-trends', array(
        'label'       => __( 'Analyze Trends', 'devskyy-abilities' ),
        'description' => __( 'Analyze business trends over time.', 'devskyy-abilities' ),
        'category'    => 'devskyy-analytics',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'metrics' => array( 'type' => 'array', 'description' => 'Metrics to analyze' ),
                'time_period' => array( 'type' => 'string', 'description' => 'Analysis period' ),
                'detect_seasonality' => array( 'type' => 'boolean', 'default' => true ),
            ),
            'required' => array( 'metrics' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'analytics', 'analyze_trends', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Anomaly: Identify
    devskyy_register( 'devskyy/identify-anomalies', array(
        'label'       => __( 'Identify Anomalies', 'devskyy-abilities' ),
        'description' => __( 'Detect anomalies in metrics.', 'devskyy-abilities' ),
        'category'    => 'devskyy-analytics',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'metrics' => array( 'type' => 'array', 'description' => 'Metrics to monitor' ),
                'sensitivity' => array( 'type' => 'number', 'default' => 2.0, 'description' => 'Std dev threshold' ),
                'lookback_days' => array( 'type' => 'integer', 'default' => 30 ),
            ),
            'required' => array( 'metrics' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'analytics', 'identify_anomalies', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Attribution: Calculate
    devskyy_register( 'devskyy/calculate-attribution', array(
        'label'       => __( 'Calculate Marketing Attribution', 'devskyy-abilities' ),
        'description' => __( 'Calculate marketing channel attribution.', 'devskyy-abilities' ),
        'category'    => 'devskyy-analytics',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'model' => array( 'type' => 'string', 'enum' => array( 'first_touch', 'last_touch', 'linear', 'time_decay', 'position_based' ) ),
                'date_range' => array( 'type' => 'object', 'description' => 'Analysis period' ),
                'channels' => array( 'type' => 'array', 'description' => 'Channels to include' ),
            ),
            'required' => array( 'model' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'analytics', 'calculate_attribution', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // ROAS: Calculate
    devskyy_register( 'devskyy/calculate-roas', array(
        'label'       => __( 'Calculate ROAS', 'devskyy-abilities' ),
        'description' => __( 'Calculate Return on Ad Spend.', 'devskyy-abilities' ),
        'category'    => 'devskyy-analytics',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'campaign_ids' => array( 'type' => 'array', 'description' => 'Campaign IDs' ),
                'date_range' => array( 'type' => 'object', 'description' => 'Analysis period' ),
                'include_organic' => array( 'type' => 'boolean', 'default' => false ),
            ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'analytics', 'calculate_roas', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));
}


/**
 * ============================================================================
 * OPERATIONS AGENT ABILITIES (18 tools)
 * ============================================================================
 */
function devskyy_register_operations_abilities() {
    // WordPress: Get Status
    devskyy_register( 'devskyy/wp-get-status', array(
        'label'       => __( 'Get WordPress Status', 'devskyy-abilities' ),
        'description' => __( 'Get WordPress site health status.', 'devskyy-abilities' ),
        'category'    => 'devskyy-operations',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'include_plugins' => array( 'type' => 'boolean', 'default' => true ),
                'include_themes' => array( 'type' => 'boolean', 'default' => true ),
                'include_updates' => array( 'type' => 'boolean', 'default' => true ),
            ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'operations', 'wp_get_status', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // WordPress: Update Plugin
    devskyy_register( 'devskyy/wp-update-plugin', array(
        'label'       => __( 'Update WordPress Plugin', 'devskyy-abilities' ),
        'description' => __( 'Update a WordPress plugin.', 'devskyy-abilities' ),
        'category'    => 'devskyy-operations',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'plugin_slug' => array( 'type' => 'string', 'description' => 'Plugin slug' ),
                'version' => array( 'type' => 'string', 'description' => 'Target version' ),
            ),
            'required' => array( 'plugin_slug' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'operations', 'wp_update_plugin', $input ); },
        'permission_callback' => function() { return current_user_can( 'update_plugins' ); },
    ));

    // WordPress: Manage Cache
    devskyy_register( 'devskyy/wp-manage-cache', array(
        'label'       => __( 'Manage WordPress Cache', 'devskyy-abilities' ),
        'description' => __( 'Clear or warm WordPress cache.', 'devskyy-abilities' ),
        'category'    => 'devskyy-operations',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'action' => array( 'type' => 'string', 'enum' => array( 'clear', 'warm', 'status' ) ),
                'cache_type' => array( 'type' => 'string', 'enum' => array( 'all', 'page', 'object', 'cdn' ) ),
            ),
            'required' => array( 'action' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'operations', 'wp_manage_cache', $input ); },
        'permission_callback' => function() { return current_user_can( 'manage_options' ); },
    ));

    // WordPress: Optimize Database
    devskyy_register( 'devskyy/wp-optimize-db', array(
        'label'       => __( 'Optimize WordPress Database', 'devskyy-abilities' ),
        'description' => __( 'Optimize WordPress database tables.', 'devskyy-abilities' ),
        'category'    => 'devskyy-operations',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'operations' => array( 'type' => 'array', 'description' => 'Optimization operations' ),
                'dry_run' => array( 'type' => 'boolean', 'default' => false ),
            ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'operations', 'wp_optimize_db', $input ); },
        'permission_callback' => function() { return current_user_can( 'manage_options' ); },
    ));

    // Elementor: Get Templates
    devskyy_register( 'devskyy/elementor-get-templates', array(
        'label'       => __( 'Get Elementor Templates', 'devskyy-abilities' ),
        'description' => __( 'List Elementor templates.', 'devskyy-abilities' ),
        'category'    => 'devskyy-operations',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'template_type' => array( 'type' => 'string', 'enum' => array( 'page', 'section', 'popup', 'header', 'footer' ) ),
            ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'operations', 'elementor_get_templates', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Elementor: Export Template
    devskyy_register( 'devskyy/elementor-export-template', array(
        'label'       => __( 'Export Elementor Template', 'devskyy-abilities' ),
        'description' => __( 'Export Elementor template to JSON.', 'devskyy-abilities' ),
        'category'    => 'devskyy-operations',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'template_id' => array( 'type' => 'integer', 'description' => 'Template ID' ),
            ),
            'required' => array( 'template_id' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'operations', 'elementor_export_template', $input ); },
    ));

    // Elementor: Regenerate CSS
    devskyy_register( 'devskyy/elementor-regenerate-css', array(
        'label'       => __( 'Regenerate Elementor CSS', 'devskyy-abilities' ),
        'description' => __( 'Regenerate Elementor CSS files.', 'devskyy-abilities' ),
        'category'    => 'devskyy-operations',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'scope' => array( 'type' => 'string', 'enum' => array( 'all', 'post', 'global' ) ),
                'post_id' => array( 'type' => 'integer', 'description' => 'Post ID (if scope=post)' ),
            ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'operations', 'elementor_regenerate_css', $input ); },
        'permission_callback' => function() { return current_user_can( 'manage_options' ); },
    ));

    // Server: Get Metrics
    devskyy_register( 'devskyy/get-server-metrics', array(
        'label'       => __( 'Get Server Metrics', 'devskyy-abilities' ),
        'description' => __( 'Get server performance metrics.', 'devskyy-abilities' ),
        'category'    => 'devskyy-operations',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'metrics' => array( 'type' => 'array', 'description' => 'Metrics to retrieve' ),
                'time_range' => array( 'type' => 'string', 'description' => 'Time range' ),
            ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'operations', 'get_server_metrics', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Server: Get Error Logs
    devskyy_register( 'devskyy/get-error-logs', array(
        'label'       => __( 'Get Error Logs', 'devskyy-abilities' ),
        'description' => __( 'Retrieve server error logs.', 'devskyy-abilities' ),
        'category'    => 'devskyy-operations',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'log_type' => array( 'type' => 'string', 'enum' => array( 'php', 'wordpress', 'nginx', 'application' ) ),
                'lines' => array( 'type' => 'integer', 'default' => 100 ),
                'severity' => array( 'type' => 'string', 'enum' => array( 'error', 'warning', 'notice', 'all' ) ),
            ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'operations', 'get_error_logs', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
        'permission_callback' => function() { return current_user_can( 'manage_options' ); },
    ));

    // Server: Check Uptime
    devskyy_register( 'devskyy/check-uptime', array(
        'label'       => __( 'Check Uptime', 'devskyy-abilities' ),
        'description' => __( 'Check service uptime status.', 'devskyy-abilities' ),
        'category'    => 'devskyy-operations',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'services' => array( 'type' => 'array', 'description' => 'Services to check' ),
            ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'operations', 'check_uptime', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Server: Health Check
    devskyy_register( 'devskyy/run-health-check', array(
        'label'       => __( 'Run Health Check', 'devskyy-abilities' ),
        'description' => __( 'Run comprehensive health check.', 'devskyy-abilities' ),
        'category'    => 'devskyy-operations',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'checks' => array( 'type' => 'array', 'description' => 'Checks to run' ),
                'include_recommendations' => array( 'type' => 'boolean', 'default' => true ),
            ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'operations', 'run_health_check', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Deployment: Deploy Code
    devskyy_register( 'devskyy/deploy-code', array(
        'label'       => __( 'Deploy Code', 'devskyy-abilities' ),
        'description' => __( 'Deploy code to environment.', 'devskyy-abilities' ),
        'category'    => 'devskyy-operations',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'environment' => array( 'type' => 'string', 'enum' => array( 'staging', 'production' ) ),
                'version' => array( 'type' => 'string', 'description' => 'Version to deploy' ),
                'dry_run' => array( 'type' => 'boolean', 'default' => false ),
            ),
            'required' => array( 'environment', 'version' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'operations', 'deploy_code', $input ); },
        'permission_callback' => function() { return current_user_can( 'manage_options' ); },
        'meta' => array( 'annotations' => array( 'destructive' => true ) ),
    ));

    // Deployment: Rollback
    devskyy_register( 'devskyy/rollback-deployment', array(
        'label'       => __( 'Rollback Deployment', 'devskyy-abilities' ),
        'description' => __( 'Rollback to previous deployment.', 'devskyy-abilities' ),
        'category'    => 'devskyy-operations',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'environment' => array( 'type' => 'string', 'enum' => array( 'staging', 'production' ) ),
                'target_version' => array( 'type' => 'string', 'description' => 'Version to rollback to' ),
            ),
            'required' => array( 'environment' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'operations', 'rollback_deployment', $input ); },
        'permission_callback' => function() { return current_user_can( 'manage_options' ); },
        'meta' => array( 'annotations' => array( 'destructive' => true ) ),
    ));

    // Backup: Create
    devskyy_register( 'devskyy/create-backup', array(
        'label'       => __( 'Create Backup', 'devskyy-abilities' ),
        'description' => __( 'Create site backup.', 'devskyy-abilities' ),
        'category'    => 'devskyy-operations',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'backup_type' => array( 'type' => 'string', 'enum' => array( 'full', 'database', 'files' ) ),
                'destination' => array( 'type' => 'string', 'description' => 'Backup destination' ),
                'compress' => array( 'type' => 'boolean', 'default' => true ),
            ),
            'required' => array( 'backup_type' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'operations', 'create_backup', $input ); },
        'permission_callback' => function() { return current_user_can( 'manage_options' ); },
    ));

    // Backup: Restore
    devskyy_register( 'devskyy/restore-backup', array(
        'label'       => __( 'Restore Backup', 'devskyy-abilities' ),
        'description' => __( 'Restore site from backup.', 'devskyy-abilities' ),
        'category'    => 'devskyy-operations',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'backup_id' => array( 'type' => 'string', 'description' => 'Backup ID' ),
                'restore_type' => array( 'type' => 'string', 'enum' => array( 'full', 'database', 'files' ) ),
            ),
            'required' => array( 'backup_id' ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'operations', 'restore_backup', $input ); },
        'permission_callback' => function() { return current_user_can( 'manage_options' ); },
        'meta' => array( 'annotations' => array( 'destructive' => true ) ),
    ));

    // Backup: List
    devskyy_register( 'devskyy/list-backups', array(
        'label'       => __( 'List Backups', 'devskyy-abilities' ),
        'description' => __( 'List available backups.', 'devskyy-abilities' ),
        'category'    => 'devskyy-operations',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'limit' => array( 'type' => 'integer', 'default' => 10 ),
                'backup_type' => array( 'type' => 'string', 'description' => 'Filter by type' ),
            ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'operations', 'list_backups', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Performance: Analyze
    devskyy_register( 'devskyy/analyze-performance', array(
        'label'       => __( 'Analyze Performance', 'devskyy-abilities' ),
        'description' => __( 'Analyze site performance.', 'devskyy-abilities' ),
        'category'    => 'devskyy-operations',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'url' => array( 'type' => 'string', 'format' => 'uri', 'description' => 'URL to analyze' ),
                'metrics' => array( 'type' => 'array', 'description' => 'Metrics to measure' ),
                'device' => array( 'type' => 'string', 'enum' => array( 'mobile', 'desktop' ) ),
            ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'operations', 'analyze_performance', $input ); },
        'meta' => array( 'show_in_rest' => true, 'annotations' => array( 'readonly' => true ) ),
    ));

    // Performance: Optimize Images
    devskyy_register( 'devskyy/optimize-images', array(
        'label'       => __( 'Optimize Images', 'devskyy-abilities' ),
        'description' => __( 'Optimize images in media library.', 'devskyy-abilities' ),
        'category'    => 'devskyy-operations',
        'input_schema' => array(
            'type' => 'object',
            'properties' => array(
                'scope' => array( 'type' => 'string', 'enum' => array( 'all', 'unoptimized', 'recent' ) ),
                'quality' => array( 'type' => 'integer', 'default' => 85 ),
                'convert_webp' => array( 'type' => 'boolean', 'default' => true ),
                'max_width' => array( 'type' => 'integer', 'default' => 2048 ),
            ),
        ),
        'execute_callback' => function( $input ) { return devskyy_call_agent( 'operations', 'optimize_images', $input ); },
        'permission_callback' => function() { return current_user_can( 'upload_files' ); },
    ));
}

/**
 * ============================================================================
 * ADMIN SETTINGS PAGE
 * ============================================================================
 */
add_action( 'admin_menu', 'devskyy_abilities_admin_menu' );

function devskyy_abilities_admin_menu() {
    add_options_page(
        __( 'DevSkyy Abilities', 'devskyy-abilities' ),
        __( 'DevSkyy', 'devskyy-abilities' ),
        'manage_options',
        'devskyy-abilities',
        'devskyy_abilities_settings_page'
    );
}

function devskyy_abilities_settings_page() {
    if ( isset( $_POST['devskyy_api_endpoint'] ) && check_admin_referer( 'devskyy_abilities_settings' ) ) {
        update_option( 'devskyy_api_endpoint', sanitize_url( $_POST['devskyy_api_endpoint'] ) );
        update_option( 'devskyy_api_key', sanitize_text_field( $_POST['devskyy_api_key'] ) );
        echo '<div class="notice notice-success"><p>' . esc_html__( 'Settings saved.', 'devskyy-abilities' ) . '</p></div>';
    }

    $endpoint = get_option( 'devskyy_api_endpoint', 'https://api.devskyy.com' );
    $api_key = get_option( 'devskyy_api_key', '' );
    ?>
    <div class="wrap">
        <h1><?php esc_html_e( 'DevSkyy Abilities Settings', 'devskyy-abilities' ); ?></h1>
        <form method="post">
            <?php wp_nonce_field( 'devskyy_abilities_settings' ); ?>
            <table class="form-table">
                <tr>
                    <th scope="row"><label for="devskyy_api_endpoint"><?php esc_html_e( 'API Endpoint', 'devskyy-abilities' ); ?></label></th>
                    <td><input type="url" name="devskyy_api_endpoint" id="devskyy_api_endpoint" value="<?php echo esc_attr( $endpoint ); ?>" class="regular-text" /></td>
                </tr>
                <tr>
                    <th scope="row"><label for="devskyy_api_key"><?php esc_html_e( 'API Key', 'devskyy-abilities' ); ?></label></th>
                    <td><input type="password" name="devskyy_api_key" id="devskyy_api_key" value="<?php echo esc_attr( $api_key ); ?>" class="regular-text" /></td>
                </tr>
            </table>
            <?php submit_button(); ?>
        </form>

        <h2><?php esc_html_e( 'Registered Abilities', 'devskyy-abilities' ); ?></h2>
        <p><?php esc_html_e( 'The following abilities are registered and available via the WordPress Abilities API:', 'devskyy-abilities' ); ?></p>
        <ul style="list-style: disc; margin-left: 20px;">
            <li><strong>Commerce:</strong> 14 abilities (products, orders, inventory, shipping)</li>
            <li><strong>Creative:</strong> 11 abilities (images, video, 3D, virtual try-on)</li>
            <li><strong>Marketing:</strong> 14 abilities (content, SEO, email, influencers)</li>
            <li><strong>Support:</strong> 13 abilities (FAQ, tickets, returns, customer history)</li>
            <li><strong>Analytics:</strong> 15 abilities (reports, forecasting, experiments)</li>
            <li><strong>Operations:</strong> 18 abilities (WordPress, Elementor, backups, deployment)</li>
        </ul>
        <p><strong><?php esc_html_e( 'Total: 85 abilities', 'devskyy-abilities' ); ?></strong></p>
    </div>
    <?php
}
