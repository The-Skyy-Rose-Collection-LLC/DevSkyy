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
	wp_enqueue_style(
		'skyyrose-woocommerce',
		SKYYROSE_ASSETS_URI . '/css/woocommerce.css',
		array(),
		SKYYROSE_VERSION
	);

	wp_enqueue_script(
		'skyyrose-woocommerce',
		SKYYROSE_ASSETS_URI . '/js/woocommerce.js',
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
 * Add custom product meta box for 3D models.
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
