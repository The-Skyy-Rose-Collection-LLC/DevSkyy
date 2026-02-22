<?php
/**
 * WooCommerce Integration
 *
 * Hooks, overrides, and customizations for WooCommerce product display,
 * cart fragments, gallery thumbnails, and related products.
 *
 * @package SkyyRose_Flagship
 * @since   1.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/*--------------------------------------------------------------
 * WooCommerce Support Declaration
 *--------------------------------------------------------------*/

/**
 * Declare WooCommerce support and gallery features.
 *
 * @since 1.0.0
 * @return void
 */
function skyyrose_woocommerce_support() {
	add_theme_support( 'woocommerce' );
	add_theme_support( 'wc-product-gallery-zoom' );
	add_theme_support( 'wc-product-gallery-lightbox' );
	add_theme_support( 'wc-product-gallery-slider' );
}
add_action( 'after_setup_theme', 'skyyrose_woocommerce_support' );

/*--------------------------------------------------------------
 * Product Grid Layout
 *--------------------------------------------------------------*/

/**
 * Set product loop columns: 4 on desktop.
 * CSS media queries handle mobile (2 columns) via the theme stylesheet.
 *
 * @since  3.0.0
 * @return int Number of columns.
 */
function skyyrose_woocommerce_loop_columns() {
	return 4;
}
add_filter( 'loop_shop_columns', 'skyyrose_woocommerce_loop_columns' );

/**
 * Set products per page (multiple of column count for even grids).
 *
 * @since  1.0.0
 * @return int Number of products per page.
 */
function skyyrose_woocommerce_products_per_page() {
	return 12;
}
add_filter( 'loop_shop_per_page', 'skyyrose_woocommerce_products_per_page' );

/*--------------------------------------------------------------
 * Sidebar Removal
 *--------------------------------------------------------------*/

// Remove the default WooCommerce sidebar entirely.
remove_action( 'woocommerce_sidebar', 'woocommerce_get_sidebar', 10 );

/*--------------------------------------------------------------
 * Content Wrappers
 *--------------------------------------------------------------*/

/**
 * Open the main content wrapper before WooCommerce output.
 *
 * @since 1.0.0
 * @return void
 */
function skyyrose_woocommerce_wrapper_before() {
	echo '<div id="primary" class="content-area"><main id="main" class="site-main" role="main">';
}
add_action( 'woocommerce_before_main_content', 'skyyrose_woocommerce_wrapper_before' );

/**
 * Close the main content wrapper after WooCommerce output.
 *
 * @since 1.0.0
 * @return void
 */
function skyyrose_woocommerce_wrapper_after() {
	echo '</main></div>';
}
add_action( 'woocommerce_after_main_content', 'skyyrose_woocommerce_wrapper_after' );

/*--------------------------------------------------------------
 * Breadcrumb Override
 *--------------------------------------------------------------*/

// Remove default WooCommerce breadcrumbs (theme uses its own).
remove_action( 'woocommerce_before_main_content', 'woocommerce_breadcrumb', 20 );

/*--------------------------------------------------------------
 * Product Gallery Thumbnails
 *--------------------------------------------------------------*/

/**
 * Custom product gallery thumbnail size (3:4 ratio matching product-card).
 *
 * @since  3.0.0
 * @return array Width, height, and crop settings.
 */
function skyyrose_woocommerce_gallery_thumbnail_size() {
	return array(
		'width'  => 150,
		'height' => 200,
		'crop'   => 1,
	);
}
add_filter( 'woocommerce_get_image_size_gallery_thumbnail', 'skyyrose_woocommerce_gallery_thumbnail_size' );

/**
 * Custom single product image size.
 *
 * @since  3.0.0
 * @return array Width, height, and crop settings.
 */
function skyyrose_woocommerce_single_image_size() {
	return array(
		'width'  => 800,
		'height' => 1066,
		'crop'   => 1,
	);
}
add_filter( 'woocommerce_get_image_size_single', 'skyyrose_woocommerce_single_image_size' );

/**
 * Custom product catalog thumbnail size (3:4 ratio).
 *
 * @since  3.0.0
 * @return array Width, height, and crop settings.
 */
function skyyrose_woocommerce_thumbnail_size() {
	return array(
		'width'  => 400,
		'height' => 533,
		'crop'   => 1,
	);
}
add_filter( 'woocommerce_get_image_size_thumbnail', 'skyyrose_woocommerce_thumbnail_size' );

/*--------------------------------------------------------------
 * AJAX Cart Fragments
 *--------------------------------------------------------------*/

/**
 * Update the header cart count badge via AJAX after add-to-cart.
 *
 * Replaces the .cart-count span with the current item count so the
 * header cart icon stays in sync without a full page reload.
 *
 * @since  1.0.0
 *
 * @param  array $fragments Existing fragments keyed by CSS selector.
 * @return array Updated fragments.
 */
function skyyrose_woocommerce_cart_fragments( $fragments ) {

	$count = WC()->cart->get_cart_contents_count();

	ob_start();
	?>
	<span class="cart-count<?php echo $count > 0 ? ' has-items' : ''; ?>"><?php echo wp_kses_data( $count ); ?></span>
	<?php
	$fragments['.cart-count'] = ob_get_clean();

	// Also provide the cart subtotal for mini-cart widgets.
	ob_start();
	?>
	<span class="cart-subtotal"><?php echo wp_kses_post( WC()->cart->get_cart_subtotal() ); ?></span>
	<?php
	$fragments['.cart-subtotal'] = ob_get_clean();

	return $fragments;
}
add_filter( 'woocommerce_add_to_cart_fragments', 'skyyrose_woocommerce_cart_fragments' );

/*--------------------------------------------------------------
 * Related Products
 *--------------------------------------------------------------*/

/**
 * Override related products display: 4 products in a 4-column grid.
 *
 * @since  1.0.0
 *
 * @param  array $args Default related products args.
 * @return array Modified args.
 */
function skyyrose_woocommerce_related_products_args( $args ) {
	return array_merge(
		$args,
		array(
			'posts_per_page' => 4,
			'columns'        => 4,
		)
	);
}
add_filter( 'woocommerce_output_related_products_args', 'skyyrose_woocommerce_related_products_args' );

/*--------------------------------------------------------------
 * Cross-Sells
 *--------------------------------------------------------------*/

/**
 * Limit cross-sell products on the cart page to 4 in a 4-column grid.
 *
 * @since  3.0.0
 *
 * @param  int $columns Default column count.
 * @return int Column count.
 */
function skyyrose_woocommerce_cross_sells_columns( $columns ) {
	return 4;
}
add_filter( 'woocommerce_cross_sells_columns', 'skyyrose_woocommerce_cross_sells_columns' );

/**
 * Limit cross-sell products count.
 *
 * @since  3.0.0
 *
 * @param  int $limit Default limit.
 * @return int Product limit.
 */
function skyyrose_woocommerce_cross_sells_total( $limit ) {
	return 4;
}
add_filter( 'woocommerce_cross_sells_total', 'skyyrose_woocommerce_cross_sells_total' );

/*--------------------------------------------------------------
 * WooCommerce Script Localization
 *--------------------------------------------------------------*/

/**
 * Localize WooCommerce scripts with AJAX data and nonces.
 *
 * @since 1.0.0
 * @return void
 */
function skyyrose_woocommerce_localize_scripts() {

	if ( ! wp_script_is( 'skyyrose-template-woocommerce', 'enqueued' ) ) {
		return;
	}

	wp_localize_script(
		'skyyrose-template-woocommerce',
		'skyyRoseWoo',
		array(
			'ajaxUrl'         => admin_url( 'admin-ajax.php' ),
			'nonce'           => wp_create_nonce( 'skyyrose-woo-nonce' ),
			'cartUrl'         => wc_get_cart_url(),
			'checkoutUrl'     => wc_get_checkout_url(),
			'addedToCartText' => esc_html__( 'Added to cart', 'skyyrose-flagship' ),
			'currency'        => get_woocommerce_currency_symbol(),
		)
	);
}
add_action( 'wp_enqueue_scripts', 'skyyrose_woocommerce_localize_scripts', 25 );

/*--------------------------------------------------------------
 * Pagination
 *--------------------------------------------------------------*/

/**
 * Customize WooCommerce pagination text.
 *
 * @since  1.0.0
 *
 * @param  array $args Default pagination arguments.
 * @return array Modified arguments.
 */
function skyyrose_woocommerce_pagination_args( $args ) {
	return array_merge(
		$args,
		array(
			'prev_text' => esc_html__( 'Previous', 'skyyrose-flagship' ),
			'next_text' => esc_html__( 'Next', 'skyyrose-flagship' ),
		)
	);
}
add_filter( 'woocommerce_pagination_args', 'skyyrose_woocommerce_pagination_args' );

/*--------------------------------------------------------------
 * 3D Model Viewer (Product Meta Box)
 *--------------------------------------------------------------*/

/**
 * Display 3D model viewer button on single product pages.
 *
 * @since 1.0.0
 * @return void
 */
function skyyrose_woocommerce_3d_model_button() {

	$model_file = get_post_meta( get_the_ID(), '_product_3d_model', true );

	if ( empty( $model_file ) ) {
		return;
	}

	printf(
		'<div class="product-3d-viewer"><button class="button view-3d-model" data-model="%s">%s</button></div>',
		esc_url( $model_file ),
		esc_html__( 'View in 3D', 'skyyrose-flagship' )
	);
}
add_action( 'woocommerce_single_product_summary', 'skyyrose_woocommerce_3d_model_button', 25 );

/**
 * Register the 3D model meta box on product edit screens.
 *
 * @since 1.0.0
 * @return void
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
 * Render the 3D model meta box UI.
 *
 * @since 1.0.0
 *
 * @param WP_Post $post Current post object.
 * @return void
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
			type="url"
			id="skyyrose_product_3d_model"
			name="skyyrose_product_3d_model"
			value="<?php echo esc_url( $value ); ?>"
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
 * @return void
 */
function skyyrose_save_product_3d_model( $post_id ) {

	// Verify nonce.
	if ( ! isset( $_POST['skyyrose_product_3d_model_nonce'] ) ) {
		return;
	}

	if ( ! wp_verify_nonce( sanitize_text_field( wp_unslash( $_POST['skyyrose_product_3d_model_nonce'] ) ), 'skyyrose_product_3d_model_nonce' ) ) {
		return;
	}

	// Bail on autosave.
	if ( defined( 'DOING_AUTOSAVE' ) && DOING_AUTOSAVE ) {
		return;
	}

	// Check capabilities.
	if ( ! current_user_can( 'edit_post', $post_id ) ) {
		return;
	}

	if ( isset( $_POST['skyyrose_product_3d_model'] ) ) {
		$url = esc_url_raw( wp_unslash( $_POST['skyyrose_product_3d_model'] ) );
		update_post_meta( $post_id, '_product_3d_model', $url );
	}
}
add_action( 'save_post_product', 'skyyrose_save_product_3d_model' );

/*--------------------------------------------------------------
 * Product Search Form
 *--------------------------------------------------------------*/

/**
 * Custom product search form markup.
 *
 * @since  1.0.0
 * @return string Search form HTML.
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

/*--------------------------------------------------------------
 * AJAX Cart Count Handler
 *--------------------------------------------------------------*/

/**
 * Return the current cart item count via AJAX.
 *
 * Called from woocommerce.js after add-to-cart and cart updates
 * to keep the header cart badge in sync.
 *
 * @since  3.0.0
 * @return void
 */
function skyyrose_ajax_get_cart_count() {

	check_ajax_referer( 'skyyrose-woo-nonce', 'nonce' );

	wp_send_json_success(
		array(
			'count' => WC()->cart->get_cart_contents_count(),
		)
	);
}
add_action( 'wp_ajax_skyyrose_get_cart_count', 'skyyrose_ajax_get_cart_count' );
add_action( 'wp_ajax_nopriv_skyyrose_get_cart_count', 'skyyrose_ajax_get_cart_count' );
