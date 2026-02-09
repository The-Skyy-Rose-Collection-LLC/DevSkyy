<?php
/**
 * WooCommerce Integration
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Declare WooCommerce support.
 *
 * @since 1.0.0
 */
function skyyrose_woocommerce_support() {
	add_theme_support( 'woocommerce' );
	add_theme_support( 'wc-product-gallery-zoom' );
	add_theme_support( 'wc-product-gallery-lightbox' );
	add_theme_support( 'wc-product-gallery-slider' );
}
add_action( 'after_setup_theme', 'skyyrose_woocommerce_support' );

/**
 * Disable default WooCommerce stylesheet.
 *
 * @since 1.0.0
 */
// WooCommerce default styles enabled - theme provides additional styling via style.css and assets/css/woocommerce.css

/**
 * Enqueue WooCommerce custom styles.
 *
 * @since 1.0.0
 */
function skyyrose_woocommerce_scripts() {
	// Use minified assets in production.
	$suffix = ( defined( 'SCRIPT_DEBUG' ) && SCRIPT_DEBUG ) ? '' : '.min';

	wp_enqueue_style(
		'skyyrose-woocommerce',
		SKYYROSE_ASSETS_URI . '/css/woocommerce' . $suffix . '.css',
		array(),
		SKYYROSE_VERSION
	);

	wp_enqueue_script(
		'skyyrose-woocommerce',
		SKYYROSE_ASSETS_URI . '/js/woocommerce' . $suffix . '.js',
		array( 'jquery', 'wc-add-to-cart' ),
		SKYYROSE_VERSION,
		true
	);

	// Localize WooCommerce script.
	wp_localize_script(
		'skyyrose-woocommerce',
		'skyyRoseWoo',
		array(
			'ajaxUrl'         => admin_url( 'admin-ajax.php' ),
			'nonce'           => wp_create_nonce( 'skyyrose-woo-nonce' ),
			'cartUrl'         => wc_get_cart_url(),
			'checkoutUrl'     => wc_get_checkout_url(),
			'addedToCartText' => esc_html__( 'Added to cart', 'skyyrose-flagship' ),
		)
	);
}
add_action( 'wp_enqueue_scripts', 'skyyrose_woocommerce_scripts' );

/**
 * Add container wrapper to WooCommerce pages.
 *
 * @since 1.0.0
 */
function skyyrose_woocommerce_wrapper_before() {
	echo '<div id="primary" class="content-area"><main id="main" class="site-main" role="main">';
}
add_action( 'woocommerce_before_main_content', 'skyyrose_woocommerce_wrapper_before' );

/**
 * Close container wrapper.
 *
 * @since 1.0.0
 */
function skyyrose_woocommerce_wrapper_after() {
	echo '</main></div>';
}
add_action( 'woocommerce_after_main_content', 'skyyrose_woocommerce_wrapper_after' );

/**
 * Remove default WooCommerce sidebar.
 *
 * @since 1.0.0
 */
remove_action( 'woocommerce_sidebar', 'woocommerce_get_sidebar', 10 );

/**
 * Custom WooCommerce sidebar.
 *
 * @since 1.0.0
 */
function skyyrose_woocommerce_sidebar() {
	if ( is_active_sidebar( 'shop-sidebar' ) ) {
		dynamic_sidebar( 'shop-sidebar' );
	}
}
add_action( 'woocommerce_sidebar', 'skyyrose_woocommerce_sidebar' );

/**
 * Set products per page.
 *
 * @since 1.0.0
 *
 * @return int Number of products.
 */
function skyyrose_woocommerce_products_per_page() {
	return 12;
}
add_filter( 'loop_shop_per_page', 'skyyrose_woocommerce_products_per_page' );

/**
 * Set product thumbnail size.
 *
 * @since 1.0.0
 *
 * @return array Image size.
 */
function skyyrose_woocommerce_thumbnail_size() {
	return array(
		'width'  => 400,
		'height' => 500,
		'crop'   => 1,
	);
}
add_filter( 'woocommerce_get_image_size_gallery_thumbnail', 'skyyrose_woocommerce_thumbnail_size' );

/**
 * Custom add to cart fragments for AJAX cart update.
 *
 * @since 1.0.0
 *
 * @param array $fragments Fragments to refresh via AJAX.
 * @return array Fragments to refresh via AJAX.
 */
function skyyrose_woocommerce_cart_fragments( $fragments ) {
	ob_start();
	?>
	<span class="cart-count"><?php echo wp_kses_data( WC()->cart->get_cart_contents_count() ); ?></span>
	<?php
	$fragments['.cart-count'] = ob_get_clean();

	return $fragments;
}
add_filter( 'woocommerce_add_to_cart_fragments', 'skyyrose_woocommerce_cart_fragments' );

/**
 * Remove WooCommerce breadcrumbs.
 *
 * @since 1.0.0
 */
remove_action( 'woocommerce_before_main_content', 'woocommerce_breadcrumb', 20 );

/**
 * Custom product loop columns.
 *
 * @since 1.0.0
 *
 * @return int Number of columns.
 */
function skyyrose_woocommerce_loop_columns() {
	return 3;
}
add_filter( 'loop_shop_columns', 'skyyrose_woocommerce_loop_columns' );

/**
 * Change number of related products output.
 *
 * @since 1.0.0
 *
 * @param array $args Related products args.
 * @return array Modified args.
 */
function skyyrose_woocommerce_related_products_args( $args ) {
	$args['posts_per_page'] = 4;
	$args['columns']        = 4;
	return $args;
}
add_filter( 'woocommerce_output_related_products_args', 'skyyrose_woocommerce_related_products_args' );

/**
 * Add custom fields to product.
 *
 * @since 1.0.0
 */
function skyyrose_woocommerce_custom_fields() {
	global $product;

	// Add 3D model viewer button if product has 3D model.
	$model_file = get_post_meta( get_the_ID(), '_product_3d_model', true );
	if ( $model_file ) {
		echo '<div class="product-3d-viewer">';
		echo '<button class="button view-3d-model" data-model="' . esc_url( $model_file ) . '">';
		echo esc_html__( 'View in 3D', 'skyyrose-flagship' );
		echo '</button>';
		echo '</div>';
	}
}
add_action( 'woocommerce_single_product_summary', 'skyyrose_woocommerce_custom_fields', 25 );

/**
 * Add custom product meta boxes for 3D models and scene positions.
 *
 * @since 1.0.0
 */
function skyyrose_add_product_meta_box() {
	add_meta_box(
		'skyyrose_product_3d_model',
		esc_html__( '3D Model', 'skyyrose-flagship' ),
		'skyyrose_product_3d_model_callback',
		'product',
		'side',
		'default'
	);

	add_meta_box(
		'skyyrose_3d_position',
		esc_html__( '3D Scene Position', 'skyyrose-flagship' ),
		'skyyrose_3d_position_callback',
		'product',
		'normal',
		'default'
	);
}
add_action( 'add_meta_boxes', 'skyyrose_add_product_meta_box' );

/**
 * Meta box callback for 3D model.
 *
 * @since 1.0.0
 *
 * @param WP_Post $post Current post object.
 */
function skyyrose_product_3d_model_callback( $post ) {
	wp_nonce_field( 'skyyrose_product_3d_model_nonce', 'skyyrose_product_3d_model_nonce' );

	$value = get_post_meta( $post->ID, '_product_3d_model', true );
	?>
	<p>
		<label for="skyyrose_product_3d_model">
			<?php esc_html_e( '3D Model File URL (GLB/GLTF)', 'skyyrose-flagship' ); ?>
		</label>
		<input
			type="text"
			id="skyyrose_product_3d_model"
			name="skyyrose_product_3d_model"
			value="<?php echo esc_attr( $value ); ?>"
			style="width: 100%;"
		/>
	</p>
	<p class="description">
		<?php esc_html_e( 'Enter the URL of the 3D model file (GLB or GLTF format).', 'skyyrose-flagship' ); ?>
	</p>
	<?php
}

/**
 * Save 3D model meta box data.
 *
 * @since 1.0.0
 *
 * @param int $post_id Post ID.
 */
function skyyrose_save_product_3d_model( $post_id ) {
	if ( ! isset( $_POST['skyyrose_product_3d_model_nonce'] ) ) {
		return;
	}

	if ( ! wp_verify_nonce( $_POST['skyyrose_product_3d_model_nonce'], 'skyyrose_product_3d_model_nonce' ) ) {
		return;
	}

	if ( defined( 'DOING_AUTOSAVE' ) && DOING_AUTOSAVE ) {
		return;
	}

	if ( ! current_user_can( 'edit_post', $post_id ) ) {
		return;
	}

	if ( isset( $_POST['skyyrose_product_3d_model'] ) ) {
		update_post_meta(
			$post_id,
			'_product_3d_model',
			esc_url_raw( $_POST['skyyrose_product_3d_model'] )
		);
	}
}
add_action( 'save_post_product', 'skyyrose_save_product_3d_model' );

/**
 * Meta box callback for 3D scene position.
 *
 * @since 1.0.0
 *
 * @param WP_Post $post Current post object.
 */
function skyyrose_3d_position_callback( $post ) {
	wp_nonce_field( 'skyyrose_3d_position_nonce', 'skyyrose_3d_position_nonce' );

	$pos_x = get_post_meta( $post->ID, '_3d_position_x', true );
	$pos_y = get_post_meta( $post->ID, '_3d_position_y', true );
	$pos_z = get_post_meta( $post->ID, '_3d_position_z', true );
	?>
	<p class="description">
		<?php esc_html_e( 'Set the position where this product appears in 3D collection scenes. Use decimal values (e.g., 2.5, -1.0, 0).', 'skyyrose-flagship' ); ?>
	</p>
	<p>
		<label for="skyyrose_3d_position_x">
			<strong><?php esc_html_e( 'X Position (Left/Right)', 'skyyrose-flagship' ); ?></strong>
		</label>
		<input
			type="number"
			step="0.1"
			id="skyyrose_3d_position_x"
			name="skyyrose_3d_position_x"
			value="<?php echo esc_attr( $pos_x ); ?>"
			style="width: 100%;"
		/>
	</p>
	<p>
		<label for="skyyrose_3d_position_y">
			<strong><?php esc_html_e( 'Y Position (Up/Down)', 'skyyrose-flagship' ); ?></strong>
		</label>
		<input
			type="number"
			step="0.1"
			id="skyyrose_3d_position_y"
			name="skyyrose_3d_position_y"
			value="<?php echo esc_attr( $pos_y ); ?>"
			style="width: 100%;"
		/>
	</p>
	<p>
		<label for="skyyrose_3d_position_z">
			<strong><?php esc_html_e( 'Z Position (Forward/Back)', 'skyyrose-flagship' ); ?></strong>
		</label>
		<input
			type="number"
			step="0.1"
			id="skyyrose_3d_position_z"
			name="skyyrose_3d_position_z"
			value="<?php echo esc_attr( $pos_z ); ?>"
			style="width: 100%;"
		/>
	</p>
	<?php
}

/**
 * Save 3D position meta box data.
 *
 * @since 1.0.0
 *
 * @param int $post_id Post ID.
 */
function skyyrose_save_3d_position( $post_id ) {
	if ( ! isset( $_POST['skyyrose_3d_position_nonce'] ) ) {
		return;
	}

	if ( ! wp_verify_nonce( $_POST['skyyrose_3d_position_nonce'], 'skyyrose_3d_position_nonce' ) ) {
		return;
	}

	if ( defined( 'DOING_AUTOSAVE' ) && DOING_AUTOSAVE ) {
		return;
	}

	if ( ! current_user_can( 'edit_post', $post_id ) ) {
		return;
	}

	// Save X position.
	if ( isset( $_POST['skyyrose_3d_position_x'] ) ) {
		update_post_meta(
			$post_id,
			'_3d_position_x',
			sanitize_text_field( $_POST['skyyrose_3d_position_x'] )
		);
	}

	// Save Y position.
	if ( isset( $_POST['skyyrose_3d_position_y'] ) ) {
		update_post_meta(
			$post_id,
			'_3d_position_y',
			sanitize_text_field( $_POST['skyyrose_3d_position_y'] )
		);
	}

	// Save Z position.
	if ( isset( $_POST['skyyrose_3d_position_z'] ) ) {
		update_post_meta(
			$post_id,
			'_3d_position_z',
			sanitize_text_field( $_POST['skyyrose_3d_position_z'] )
		);
	}
}
add_action( 'save_post_product', 'skyyrose_save_3d_position' );

/**
 * Register REST API endpoint for 3D product data.
 * Context7 Query: /woocommerce/woocommerce-rest-api-docs - WooCommerce REST API endpoints
 *
 * @since 1.0.0
 */
function skyyrose_register_3d_product_endpoint() {
	register_rest_route(
		'skyyrose/v1',
		'/products/3d/(?P<category>[\w-]+)',
		array(
			'methods'             => 'GET',
			'callback'            => 'skyyrose_get_collection_products_3d',
			'permission_callback' => '__return_true',
			'args'                => array(
				'category' => array(
					'required'          => true,
					'validate_callback' => function( $param ) {
						return is_string( $param );
					},
				),
			),
		)
	);
}
add_action( 'rest_api_init', 'skyyrose_register_3d_product_endpoint' );

/**
 * Get products with 3D position data for a specific category.
 * Based on WooCommerce REST API patterns from Context7 documentation.
 *
 * @since 1.0.0
 *
 * @param WP_REST_Request $request REST API request object.
 * @return WP_REST_Response|WP_Error Response object on success, or WP_Error object on failure.
 */
function skyyrose_get_collection_products_3d( $request ) {
	$category_slug = sanitize_text_field( $request['category'] );

	// Get products in the category.
	$args = array(
		'limit'    => 20,
		'category' => array( $category_slug ),
		'status'   => 'publish',
	);

	$products = wc_get_products( $args );

	if ( empty( $products ) ) {
		return new WP_Error(
			'no_products',
			esc_html__( 'No products found for this collection.', 'skyyrose-flagship' ),
			array( 'status' => 404 )
		);
	}

	$products_data = array();

	foreach ( $products as $product ) {
		$product_id    = $product->get_id();
		$pos_x         = get_post_meta( $product_id, '_3d_position_x', true );
		$pos_y         = get_post_meta( $product_id, '_3d_position_y', true );
		$pos_z         = get_post_meta( $product_id, '_3d_position_z', true );
		$model_file    = get_post_meta( $product_id, '_product_3d_model', true );

		// Only include products that have 3D position data.
		if ( $pos_x !== '' || $pos_y !== '' || $pos_z !== '' ) {
			$products_data[] = array(
				'id'          => $product_id,
				'name'        => $product->get_name(),
				'price'       => $product->get_price_html(),
				'regular_price' => $product->get_regular_price(),
				'sale_price'  => $product->get_sale_price(),
				'image'       => wp_get_attachment_image_url( $product->get_image_id(), 'large' ),
				'url'         => $product->get_permalink(),
				'description' => $product->get_short_description(),
				'sku'         => $product->get_sku(),
				'stock_status' => $product->get_stock_status(),
				'model_file'  => $model_file ? esc_url( $model_file ) : '',
				'position'    => array(
					'x' => $pos_x !== '' ? floatval( $pos_x ) : 0.0,
					'y' => $pos_y !== '' ? floatval( $pos_y ) : 1.5,
					'z' => $pos_z !== '' ? floatval( $pos_z ) : 0.0,
				),
			);
		}
	}

	return new WP_REST_Response( $products_data, 200 );
}

/**
 * Custom product search form.
 *
 * @since 1.0.0
 *
 * @return string Product search form HTML.
 */
function skyyrose_product_search_form() {
	ob_start();
	?>
	<form role="search" method="get" class="woocommerce-product-search" action="<?php echo esc_url( home_url( '/' ) ); ?>">
		<label class="screen-reader-text" for="woocommerce-product-search-field">
			<?php esc_html_e( 'Search for:', 'skyyrose-flagship' ); ?>
		</label>
		<input
			type="search"
			id="woocommerce-product-search-field"
			class="search-field"
			placeholder="<?php echo esc_attr__( 'Search products&hellip;', 'skyyrose-flagship' ); ?>"
			value="<?php echo esc_attr( get_search_query() ); ?>"
			name="s"
		/>
		<button type="submit" value="<?php echo esc_attr_x( 'Search', 'submit button', 'skyyrose-flagship' ); ?>">
			<?php echo esc_html_x( 'Search', 'submit button', 'skyyrose-flagship' ); ?>
		</button>
		<input type="hidden" name="post_type" value="product" />
	</form>
	<?php
	return ob_get_clean();
}

/**
 * Modify WooCommerce pagination args.
 *
 * @since 1.0.0
 *
 * @param array $args Pagination arguments.
 * @return array Modified arguments.
 */
function skyyrose_woocommerce_pagination_args( $args ) {
	$args['prev_text'] = esc_html__( 'Previous', 'skyyrose-flagship' );
	$args['next_text'] = esc_html__( 'Next', 'skyyrose-flagship' );
	return $args;
}
add_filter( 'woocommerce_pagination_args', 'skyyrose_woocommerce_pagination_args' );
