<?php
/**
 * Immersive AJAX Handlers
 *
 * Provides AJAX endpoints for immersive scene pages to fetch
 * live product data from WooCommerce by SKU.
 *
 * @package SkyyRose_Flagship
 * @since   3.12.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/*--------------------------------------------------------------
 * Get Product by SKU
 *--------------------------------------------------------------*/

/**
 * Return live product data for a given SKU via AJAX.
 *
 * Used by immersive scene hotspots to fetch real-time pricing,
 * stock status, images, and pre-order metadata from WooCommerce.
 *
 * @since 3.12.0
 * @return void
 */
function skyyrose_ajax_get_product_by_sku() {

	// Verify nonce.
	if ( ! isset( $_POST['nonce'] ) ||
		! wp_verify_nonce( sanitize_text_field( wp_unslash( $_POST['nonce'] ) ), 'skyyrose-immersive-nonce' ) ) {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Security check failed. Please refresh the page.', 'skyyrose-flagship' ),
			)
		);
		return;
	}

	// Check WooCommerce availability.
	if ( ! function_exists( 'wc_get_product_id_by_sku' ) || ! class_exists( 'WooCommerce' ) ) {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Product data is currently unavailable.', 'skyyrose-flagship' ),
			)
		);
		return;
	}

	// Sanitize SKU input.
	$sku = isset( $_POST['sku'] ) ? sanitize_text_field( wp_unslash( $_POST['sku'] ) ) : '';

	if ( empty( $sku ) ) {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'No product identifier provided.', 'skyyrose-flagship' ),
			)
		);
		return;
	}

	// Look up product by SKU.
	$product_id = wc_get_product_id_by_sku( $sku );

	if ( ! $product_id ) {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Product not found.', 'skyyrose-flagship' ),
			)
		);
		return;
	}

	$product = wc_get_product( $product_id );

	if ( ! $product || ! $product->is_visible() ) {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Product not found.', 'skyyrose-flagship' ),
			)
		);
		return;
	}

	$data = skyyrose_build_product_data( $product );

	wp_send_json_success( $data );
}
add_action( 'wp_ajax_skyyrose_get_product_by_sku', 'skyyrose_ajax_get_product_by_sku' );
add_action( 'wp_ajax_nopriv_skyyrose_get_product_by_sku', 'skyyrose_ajax_get_product_by_sku' );

/*--------------------------------------------------------------
 * Get Collection Products
 *--------------------------------------------------------------*/

/**
 * Return all products in a given collection category via AJAX.
 *
 * Used by immersive scenes to fetch the full product set for a
 * collection (e.g., black-rose, love-hurts, signature).
 *
 * @since 3.12.0
 * @return void
 */
function skyyrose_ajax_get_collection_products() {

	// Verify nonce.
	if ( ! isset( $_POST['nonce'] ) ||
		! wp_verify_nonce( sanitize_text_field( wp_unslash( $_POST['nonce'] ) ), 'skyyrose-immersive-nonce' ) ) {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Security check failed. Please refresh the page.', 'skyyrose-flagship' ),
			)
		);
		return;
	}

	// Check WooCommerce availability.
	if ( ! function_exists( 'wc_get_products' ) || ! class_exists( 'WooCommerce' ) ) {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Product data is currently unavailable.', 'skyyrose-flagship' ),
			)
		);
		return;
	}

	// Sanitize collection slug.
	$collection = isset( $_POST['collection'] ) ? sanitize_title( wp_unslash( $_POST['collection'] ) ) : '';

	if ( empty( $collection ) ) {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'No collection specified.', 'skyyrose-flagship' ),
			)
		);
		return;
	}

	// Validate the collection slug against known collections.
	$allowed_collections = array( 'black-rose', 'love-hurts', 'signature', 'kids-capsule' );

	if ( ! in_array( $collection, $allowed_collections, true ) ) {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Invalid collection.', 'skyyrose-flagship' ),
			)
		);
		return;
	}

	// Query products by product category slug.
	$args = array(
		'status'   => 'publish',
		'limit'    => 50,
		'category' => array( $collection ),
		'orderby'  => 'menu_order',
		'order'    => 'ASC',
	);

	$products = wc_get_products( $args );

	if ( empty( $products ) ) {
		wp_send_json_success( array() );
		return;
	}

	$result = array();

	foreach ( $products as $product ) {
		if ( ! $product->is_visible() ) {
			continue;
		}

		$image_id  = $product->get_image_id();
		$image_url = $image_id ? wp_get_attachment_image_url( $image_id, 'woocommerce_thumbnail' ) : '';

		$result[] = array(
			'id'          => $product->get_id(),
			'sku'         => $product->get_sku(),
			'name'        => $product->get_name(),
			'price'       => $product->get_price(),
			'image_url'   => $image_url ? esc_url( $image_url ) : '',
			'permalink'   => esc_url( $product->get_permalink() ),
			'is_preorder' => skyyrose_immersive_is_preorder( $product->get_id() ),
			'sizes'       => skyyrose_immersive_get_product_sizes( $product ),
		);
	}

	wp_send_json_success( $result );
}
add_action( 'wp_ajax_skyyrose_get_collection_products', 'skyyrose_ajax_get_collection_products' );
add_action( 'wp_ajax_nopriv_skyyrose_get_collection_products', 'skyyrose_ajax_get_collection_products' );

/*--------------------------------------------------------------
 * Immersive Add to Cart
 *--------------------------------------------------------------*/

/**
 * Handle add-to-cart requests from immersive scene panels via AJAX.
 *
 * Validates inputs, adds the product to the WooCommerce cart,
 * and returns the updated cart count and fragments.
 *
 * @since 3.12.0
 * @return void
 */
function skyyrose_ajax_immersive_add_to_cart() {

	// Verify nonce.
	if ( ! isset( $_POST['nonce'] ) ||
		! wp_verify_nonce( sanitize_text_field( wp_unslash( $_POST['nonce'] ) ), 'skyyrose-immersive-nonce' ) ) {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Security check failed. Please refresh the page.', 'skyyrose-flagship' ),
			)
		);
		return;
	}

	// Check WooCommerce availability.
	if ( ! function_exists( 'WC' ) || ! WC()->cart ) {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Cart is currently unavailable.', 'skyyrose-flagship' ),
			)
		);
		return;
	}

	// Sanitize inputs — accept either numeric product_id or SKU string.
	$product_id = isset( $_POST['product_id'] ) ? absint( $_POST['product_id'] ) : 0;
	$sku        = isset( $_POST['sku'] ) ? sanitize_text_field( wp_unslash( $_POST['sku'] ) ) : '';
	$quantity   = isset( $_POST['quantity'] ) ? absint( $_POST['quantity'] ) : 1;
	$size       = isset( $_POST['attribute_pa_size'] ) ? sanitize_text_field( wp_unslash( $_POST['attribute_pa_size'] ) ) : '';

	// Resolve SKU to product ID if needed.
	if ( ! $product_id && $sku && function_exists( 'wc_get_product_id_by_sku' ) ) {
		// Strip variant suffixes for WC lookup (e.g., 'sg-001-tee' → 'sg-001').
		$lookup_sku = preg_replace( '/-(tee|shorts)$/', '', $sku );
		$lookup_sku = preg_replace( '/([a-z]{2}-\d{3})[a-z]$/', '$1', $lookup_sku );
		$product_id = wc_get_product_id_by_sku( $lookup_sku );
	}

	if ( ! $product_id ) {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Invalid product.', 'skyyrose-flagship' ),
			)
		);
		return;
	}

	// Clamp quantity to a reasonable range.
	if ( $quantity < 1 ) {
		$quantity = 1;
	}
	if ( $quantity > 10 ) {
		$quantity = 10;
	}

	// Verify the product exists and is purchasable.
	$product = wc_get_product( $product_id );

	if ( ! $product || ! $product->is_purchasable() ) {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'This product cannot be added to cart.', 'skyyrose-flagship' ),
			)
		);
		return;
	}

	// Build variation data if size is provided and product is variable.
	$variation_id = 0;
	$variation    = array();

	if ( ! empty( $size ) && $product->is_type( 'variable' ) ) {
		$variation = array( 'attribute_pa_size' => $size );

		// Find the matching variation ID.
		$data_store   = WC_Data_Store::load( 'product' );
		$variation_id = $data_store->find_matching_product_variation( $product, $variation );

		if ( ! $variation_id ) {
			// Size not found as a variation; add simple product without variation.
			$variation_id = 0;
			$variation    = array();
		}
	}

	// Add to cart.
	$cart_item_key = WC()->cart->add_to_cart( $product_id, $quantity, $variation_id, $variation );

	if ( ! $cart_item_key ) {
		wp_send_json_error(
			array(
				'message' => esc_html__( 'Could not add item to cart. Please try again.', 'skyyrose-flagship' ),
			)
		);
		return;
	}

	// Build response with updated cart data.
	$cart_count = WC()->cart->get_cart_contents_count();

	// Generate cart fragments for header badge sync.
	ob_start();
	$count = $cart_count;
	?>
	<span class="cart-count<?php echo $count > 0 ? ' has-items' : ''; ?>"><?php echo esc_html( absint( $count ) ); ?></span>
	<?php
	$cart_count_fragment = ob_get_clean();

	ob_start();
	?>
	<span class="cart-subtotal"><?php echo wp_kses_post( WC()->cart->get_cart_subtotal() ); ?></span>
	<?php
	$cart_subtotal_fragment = ob_get_clean();

	wp_send_json_success(
		array(
			'message'    => esc_html__( 'Added to cart!', 'skyyrose-flagship' ),
			'cart_count' => $cart_count,
			'cart_url'   => esc_url( wc_get_cart_url() ),
			'fragments'  => array(
				'.cart-count'    => $cart_count_fragment,
				'.cart-subtotal' => $cart_subtotal_fragment,
			),
		)
	);
}
add_action( 'wp_ajax_skyyrose_immersive_add_to_cart', 'skyyrose_ajax_immersive_add_to_cart' );
add_action( 'wp_ajax_nopriv_skyyrose_immersive_add_to_cart', 'skyyrose_ajax_immersive_add_to_cart' );

/*--------------------------------------------------------------
 * Localize Immersive Data
 *--------------------------------------------------------------*/

/**
 * Localize the skyyRoseImmersive JS object on immersive template pages.
 *
 * Provides the AJAX URL, nonce, and cart URL to the client-side
 * WooCommerce bridge script.
 *
 * @since 3.12.0
 * @return void
 */
function skyyrose_localize_immersive_data() {

	// Only run on immersive template pages.
	$template = get_page_template_slug();

	if ( empty( $template ) ) {
		return;
	}

	$immersive_templates = array(
		'template-immersive-black-rose.php',
		'template-immersive-love-hurts.php',
		'template-immersive-signature.php',
	);

	if ( ! in_array( $template, $immersive_templates, true ) ) {
		return;
	}

	// Determine the best script handle to attach the data to.
	$handle = 'skyyrose-immersive-wc-bridge';

	// Enqueue the WC bridge script on immersive pages.
	$bridge_path = SKYYROSE_DIR . '/assets/js/immersive-wc-bridge.js';
	if ( file_exists( $bridge_path ) ) {
		wp_enqueue_script(
			$handle,
			SKYYROSE_ASSETS_URI . '/js/immersive-wc-bridge.js',
			array( 'skyyrose-template-immersive' ),
			SKYYROSE_VERSION,
			true
		);
	}

	// Build the cart URL safely (WooCommerce may not be active).
	$cart_url = '';
	if ( function_exists( 'wc_get_cart_url' ) ) {
		$cart_url = wc_get_cart_url();
	}

	wp_localize_script(
		$handle,
		'skyyRoseImmersive',
		array(
			'ajaxUrl' => admin_url( 'admin-ajax.php' ),
			'nonce'   => wp_create_nonce( 'skyyrose-immersive-nonce' ),
			'cartUrl' => esc_url( $cart_url ),
		)
	);
}
add_action( 'wp_enqueue_scripts', 'skyyrose_localize_immersive_data', 25 );

/*--------------------------------------------------------------
 * Helper Functions
 *--------------------------------------------------------------*/

/**
 * Build a standardized product data array for AJAX responses.
 *
 * Extracts all fields needed by the immersive product panel,
 * including pre-order metadata, available sizes, and colors.
 *
 * @since 3.12.0
 *
 * @param WC_Product $product WooCommerce product object.
 * @return array Associative array of product data.
 */
function skyyrose_build_product_data( $product ) {

	$product_id = $product->get_id();

	// Product image.
	$image_id  = $product->get_image_id();
	$image_url = $image_id ? wp_get_attachment_image_url( $image_id, 'woocommerce_single' ) : '';

	// Pre-order metadata.
	$is_preorder  = skyyrose_immersive_is_preorder( $product_id );
	$edition_size = get_post_meta( $product_id, '_preorder_edition_size', true );
	$available    = get_post_meta( $product_id, '_preorder_available', true );
	$ship_date    = get_post_meta( $product_id, '_preorder_ship_date', true );

	// Format ship date for display.
	if ( ! empty( $ship_date ) ) {
		$ship_date = date_i18n( 'F j, Y', strtotime( $ship_date ) );
	}

	return array(
		'id'           => $product_id,
		'name'         => $product->get_name(),
		'price'        => $product->get_price(),
		'price_html'   => wp_kses_post( $product->get_price_html() ),
		'image_url'    => $image_url ? esc_url( $image_url ) : '',
		'permalink'    => esc_url( $product->get_permalink() ),
		'stock_status' => $product->get_stock_status(),
		'is_preorder'  => $is_preorder,
		'edition_size' => $edition_size ? absint( $edition_size ) : null,
		'available'    => $available ? absint( $available ) : null,
		'ship_date'    => $ship_date ? sanitize_text_field( $ship_date ) : null,
		'sizes'        => skyyrose_immersive_get_product_sizes( $product ),
		'colors'       => skyyrose_immersive_get_product_colors( $product ),
	);
}

/**
 * Check if a product has pre-order status.
 *
 * Uses the theme's pre-order meta field. Falls back gracefully
 * if the skyyrose_is_preorder() function is not available.
 *
 * @since 3.12.0
 *
 * @param int $product_id Product ID.
 * @return bool True if the product is a pre-order item.
 */
function skyyrose_immersive_is_preorder( $product_id ) {

	if ( function_exists( 'skyyrose_is_preorder' ) ) {
		return skyyrose_is_preorder( $product_id );
	}

	return '1' === get_post_meta( $product_id, '_is_preorder', true );
}

/**
 * Get available sizes for a product.
 *
 * Extracts the pa_size attribute values for variable products.
 * Returns an empty array for simple products.
 *
 * @since 3.12.0
 *
 * @param WC_Product $product WooCommerce product object.
 * @return array Array of size strings.
 */
function skyyrose_immersive_get_product_sizes( $product ) {

	if ( ! $product->is_type( 'variable' ) ) {
		return array();
	}

	$attributes = $product->get_variation_attributes();

	if ( ! isset( $attributes['pa_size'] ) || ! is_array( $attributes['pa_size'] ) ) {
		return array();
	}

	$sizes = array();

	foreach ( $attributes['pa_size'] as $slug ) {
		$term = get_term_by( 'slug', $slug, 'pa_size' );
		if ( $term && ! is_wp_error( $term ) ) {
			$sizes[] = $term->name;
		} else {
			$sizes[] = ucfirst( sanitize_text_field( $slug ) );
		}
	}

	return $sizes;
}

/**
 * Get available colors for a product.
 *
 * Extracts the pa_color attribute values for variable products.
 * Returns an empty array for simple products.
 *
 * @since 3.12.0
 *
 * @param WC_Product $product WooCommerce product object.
 * @return array Array of color strings.
 */
function skyyrose_immersive_get_product_colors( $product ) {

	if ( ! $product->is_type( 'variable' ) ) {
		return array();
	}

	$attributes = $product->get_variation_attributes();

	if ( ! isset( $attributes['pa_color'] ) || ! is_array( $attributes['pa_color'] ) ) {
		return array();
	}

	$colors = array();

	foreach ( $attributes['pa_color'] as $slug ) {
		$term = get_term_by( 'slug', $slug, 'pa_color' );
		if ( $term && ! is_wp_error( $term ) ) {
			$colors[] = $term->name;
		} else {
			$colors[] = ucfirst( sanitize_text_field( $slug ) );
		}
	}

	return $colors;
}
