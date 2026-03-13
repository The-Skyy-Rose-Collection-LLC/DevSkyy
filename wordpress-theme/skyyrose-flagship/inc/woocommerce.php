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

	if ( ! WC()->cart ) {
		return $fragments;
	}

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

	if ( ! function_exists( 'wc_get_cart_url' ) ) {
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
		'<div class="product-3d-viewer"><button type="button" class="button view-3d-model" data-model="%s">%s</button></div>',
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
		$url = esc_url_raw( wp_unslash( $_POST['skyyrose_product_3d_model'] ), array( 'https', 'http' ) );
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

	$count = ( function_exists( 'WC' ) && WC()->cart ) ? WC()->cart->get_cart_contents_count() : 0;

	wp_send_json_success(
		array(
			'count' => $count,
		)
	);
}
add_action( 'wp_ajax_skyyrose_get_cart_count', 'skyyrose_ajax_get_cart_count' );
add_action( 'wp_ajax_nopriv_skyyrose_get_cart_count', 'skyyrose_ajax_get_cart_count' );

/*--------------------------------------------------------------
 * Pre-Order Meta Fields
 *--------------------------------------------------------------*/

/**
 * Register the pre-order meta box on product edit screens.
 *
 * Adds fields for: pre-order status, edition size, available quantity,
 * expected ship date, and pre-order price.
 *
 * @since 3.10.0
 * @return void
 */
function skyyrose_add_preorder_meta_box() {
	add_meta_box(
		'skyyrose_preorder_settings',
		esc_html__( 'Pre-Order Settings', 'skyyrose-flagship' ),
		'skyyrose_preorder_meta_box_callback',
		'product',
		'side',
		'high'
	);
}
add_action( 'add_meta_boxes', 'skyyrose_add_preorder_meta_box' );

/**
 * Render the pre-order meta box UI.
 *
 * @since 3.10.0
 *
 * @param WP_Post $post Current post object.
 * @return void
 */
function skyyrose_preorder_meta_box_callback( $post ) {

	wp_nonce_field( 'skyyrose_preorder_nonce', 'skyyrose_preorder_nonce' );

	$is_preorder    = get_post_meta( $post->ID, '_is_preorder', true );
	$edition_size   = get_post_meta( $post->ID, '_preorder_edition_size', true );
	$available      = get_post_meta( $post->ID, '_preorder_available', true );
	$ship_date      = get_post_meta( $post->ID, '_preorder_ship_date', true );
	$preorder_price = get_post_meta( $post->ID, '_preorder_price', true );
	?>
	<p>
		<label>
			<input type="checkbox" name="skyyrose_is_preorder" value="1" <?php checked( $is_preorder, '1' ); ?> />
			<?php esc_html_e( 'This is a pre-order product', 'skyyrose-flagship' ); ?>
		</label>
	</p>
	<p>
		<label for="skyyrose_edition_size"><?php esc_html_e( 'Edition Size', 'skyyrose-flagship' ); ?></label>
		<input type="number" id="skyyrose_edition_size" name="skyyrose_edition_size" value="<?php echo esc_attr( $edition_size ); ?>" min="1" style="width:100%;" placeholder="e.g. 250" />
	</p>
	<p>
		<label for="skyyrose_preorder_available"><?php esc_html_e( 'Available Remaining', 'skyyrose-flagship' ); ?></label>
		<input type="number" id="skyyrose_preorder_available" name="skyyrose_preorder_available" value="<?php echo esc_attr( $available ); ?>" min="0" style="width:100%;" />
	</p>
	<p>
		<label for="skyyrose_ship_date"><?php esc_html_e( 'Expected Ship Date', 'skyyrose-flagship' ); ?></label>
		<input type="date" id="skyyrose_ship_date" name="skyyrose_ship_date" value="<?php echo esc_attr( $ship_date ); ?>" style="width:100%;" />
	</p>
	<p>
		<label for="skyyrose_preorder_price"><?php esc_html_e( 'Pre-Order Price ($)', 'skyyrose-flagship' ); ?></label>
		<input type="text" id="skyyrose_preorder_price" name="skyyrose_preorder_price" value="<?php echo esc_attr( $preorder_price ); ?>" style="width:100%;" placeholder="Early access price" />
	</p>
	<?php
}

/**
 * Save pre-order meta box data.
 *
 * @since 3.10.0
 *
 * @param int $post_id Post ID.
 * @return void
 */
function skyyrose_save_preorder_meta( $post_id ) {

	if ( ! isset( $_POST['skyyrose_preorder_nonce'] ) ) {
		return;
	}

	if ( ! wp_verify_nonce( sanitize_text_field( wp_unslash( $_POST['skyyrose_preorder_nonce'] ) ), 'skyyrose_preorder_nonce' ) ) {
		return;
	}

	if ( defined( 'DOING_AUTOSAVE' ) && DOING_AUTOSAVE ) {
		return;
	}

	if ( ! current_user_can( 'edit_post', $post_id ) ) {
		return;
	}

	// Pre-order checkbox.
	$is_preorder = isset( $_POST['skyyrose_is_preorder'] ) ? '1' : '0';
	update_post_meta( $post_id, '_is_preorder', $is_preorder );

	// Edition size.
	if ( isset( $_POST['skyyrose_edition_size'] ) ) {
		$edition = absint( wp_unslash( $_POST['skyyrose_edition_size'] ) );
		update_post_meta( $post_id, '_preorder_edition_size', $edition );
	}

	// Available remaining.
	if ( isset( $_POST['skyyrose_preorder_available'] ) ) {
		$available = absint( wp_unslash( $_POST['skyyrose_preorder_available'] ) );
		update_post_meta( $post_id, '_preorder_available', $available );
	}

	// Expected ship date — validate YYYY-MM-DD format.
	if ( isset( $_POST['skyyrose_ship_date'] ) ) {
		$date = sanitize_text_field( wp_unslash( $_POST['skyyrose_ship_date'] ) );
		if ( ! preg_match( '/^\d{4}-\d{2}-\d{2}$/', $date ) || false === strtotime( $date ) ) {
			$date = '';
		}
		update_post_meta( $post_id, '_preorder_ship_date', $date );
	}

	// Pre-order price — validate finite, non-negative number with upper bound.
	if ( isset( $_POST['skyyrose_preorder_price'] ) ) {
		$price = sanitize_text_field( wp_unslash( $_POST['skyyrose_preorder_price'] ) );
		if ( '' !== $price ) {
			$price = floatval( $price );
			if ( is_finite( $price ) && $price >= 0 && $price < 100000 ) {
				$price = round( $price, 2 );
			} else {
				$price = '';
			}
		}
		update_post_meta( $post_id, '_preorder_price', $price );
	}
}
add_action( 'save_post_product', 'skyyrose_save_preorder_meta' );

/**
 * Check if a product is a pre-order item.
 *
 * @since 3.10.0
 *
 * @param int $product_id Product ID.
 * @return bool True if the product has pre-order status.
 */
function skyyrose_is_preorder( $product_id ) {
	return '1' === get_post_meta( $product_id, '_is_preorder', true );
}

/**
 * Display pre-order badge and edition info on single product pages.
 *
 * @since 3.10.0
 * @return void
 */
function skyyrose_preorder_single_product_notice() {
	global $product;

	if ( ! $product || ! skyyrose_is_preorder( $product->get_id() ) ) {
		return;
	}

	$edition_size = get_post_meta( $product->get_id(), '_preorder_edition_size', true );
	$available    = get_post_meta( $product->get_id(), '_preorder_available', true );
	$ship_date    = get_post_meta( $product->get_id(), '_preorder_ship_date', true );
	$preorder_px  = get_post_meta( $product->get_id(), '_preorder_price', true );

	echo '<div class="skyyrose-preorder-notice">';
	echo '<span class="skyyrose-preorder-notice__badge">' . esc_html__( 'Pre-Order', 'skyyrose-flagship' ) . '</span>';

	if ( $edition_size ) {
		echo '<div class="skyyrose-preorder-notice__detail">' . esc_html__( 'Limited Edition', 'skyyrose-flagship' ) . ' — <strong>' . esc_html( $edition_size ) . ' ' . esc_html__( 'pieces', 'skyyrose-flagship' ) . '</strong>';
		if ( $available ) {
			echo ' · <strong>' . esc_html( $available ) . ' ' . esc_html__( 'remaining', 'skyyrose-flagship' ) . '</strong>';
		}
		echo '</div>';
	}

	if ( $preorder_px ) {
		echo '<div class="skyyrose-preorder-notice__detail">' . esc_html__( 'Early Access Price:', 'skyyrose-flagship' ) . ' <strong>' . esc_html( get_woocommerce_currency_symbol() ) . esc_html( $preorder_px ) . '</strong></div>';
	}

	if ( $ship_date ) {
		echo '<div class="skyyrose-preorder-notice__ship-date">' . esc_html__( 'Expected Ship Date:', 'skyyrose-flagship' ) . ' ' . esc_html( date_i18n( 'F j, Y', strtotime( $ship_date ) ) ) . '</div>';
	}

	echo '</div>';
}
add_action( 'woocommerce_single_product_summary', 'skyyrose_preorder_single_product_notice', 6 );

/**
 * Replace "Add to Cart" text with "Pre-Order Now" for pre-order products.
 *
 * @since 3.10.0
 *
 * @param string      $text    Default button text.
 * @param WC_Product  $product Product object.
 * @return string Modified button text.
 */
function skyyrose_preorder_button_text( $text, $product ) {
	if ( $product && skyyrose_is_preorder( $product->get_id() ) ) {
		return esc_html__( 'Pre-Order Now', 'skyyrose-flagship' );
	}
	return $text;
}
add_filter( 'woocommerce_product_single_add_to_cart_text', 'skyyrose_preorder_button_text', 10, 2 );
add_filter( 'woocommerce_product_add_to_cart_text', 'skyyrose_preorder_button_text', 10, 2 );

/**
 * Replace $0.00 price display with "Pre-Order" label for pre-order products.
 *
 * When a WooCommerce product is marked as pre-order but has a $0 regular price,
 * the default price_html shows "$0.00" which confuses customers. This filter
 * replaces it with either "Pre-Order -- $XX" (if a pre-order price is set)
 * or just "Pre-Order".
 *
 * @since 4.3.0
 *
 * @param string     $price_html Default price HTML from WooCommerce.
 * @param WC_Product $product    Product object.
 * @return string Modified price HTML.
 */
function skyyrose_preorder_price_html( $price_html, $product ) {
	if ( ! skyyrose_is_preorder( $product->get_id() ) ) {
		return $price_html;
	}

	$regular_price = (float) $product->get_price();

	// If the product has a real price (> 0), keep WC's formatted output.
	if ( $regular_price > 0 ) {
		return $price_html;
	}

	// Check for a custom pre-order price in meta.
	$preorder_price = get_post_meta( $product->get_id(), '_preorder_price', true );

	if ( ! empty( $preorder_price ) && is_numeric( $preorder_price ) && (float) $preorder_price > 0 ) {
		return '<span class="woocommerce-Price-amount amount">'
			. esc_html__( 'Pre-Order', 'skyyrose-flagship' )
			. ' &mdash; '
			. esc_html( get_woocommerce_currency_symbol() )
			. esc_html( number_format( (float) $preorder_price, 0 ) )
			. '</span>';
	}

	return '<span class="woocommerce-Price-amount amount">'
		. esc_html__( 'Pre-Order', 'skyyrose-flagship' )
		. '</span>';
}
add_filter( 'woocommerce_get_price_html', 'skyyrose_preorder_price_html', 10, 2 );

/*--------------------------------------------------------------
 * Complete the Look — single product cross-sell
 *--------------------------------------------------------------*/

/**
 * Render the "Complete the Look" cross-sell section on single product pages.
 *
 * Delegates all logic and markup to template-parts/complete-the-look.php,
 * which resolves curated SKU pairs and outputs quick-add cards.
 *
 * @since 5.0.0
 * @return void
 */
function skyyrose_complete_the_look() {
	get_template_part( 'template-parts/complete-the-look' );
}
add_action( 'woocommerce_single_product_summary', 'skyyrose_complete_the_look', 50 );

/*--------------------------------------------------------------
 * Referral Dashboard — post-purchase thank-you panel
 *--------------------------------------------------------------*/

/**
 * Render the referral dashboard on the order confirmation page.
 *
 * Generates or retrieves the customer's unique referral code, creates
 * the matching WooCommerce coupon if needed, and renders the share UI.
 *
 * @since 5.0.0
 *
 * @param int $order_id WooCommerce order ID (passed by woocommerce_thankyou).
 * @return void
 */
function skyyrose_referral_dashboard( $order_id ) {
	get_template_part( 'template-parts/referral-dashboard', null, array( 'order_id' => absint( $order_id ) ) );
}
add_action( 'woocommerce_thankyou', 'skyyrose_referral_dashboard', 20 );

/*--------------------------------------------------------------
 * Referral Credit — award $10 on completed order
 *--------------------------------------------------------------*/

/**
 * Credit the referrer when a completed order uses their referral coupon.
 *
 * Checks each coupon code on the order against the SKYY prefix pattern,
 * looks up the coupon owner, prevents self-referral, increments
 * _skyyrose_referral_count and _skyyrose_referral_earned on the referrer's
 * user meta, and awards the Founding Ambassador badge to the first 100
 * successful referrers. Idempotent: no-ops if already credited.
 *
 * @since 5.0.0
 *
 * @param int $order_id WooCommerce order ID.
 * @return void
 */
function skyyrose_woo_credit_referrer( $order_id ) {

	$order = wc_get_order( absint( $order_id ) );
	if ( ! $order ) {
		return;
	}

	// Idempotency guard — do not double-credit.
	if ( get_post_meta( $order_id, '_skyyrose_referral_credited', true ) ) {
		return;
	}

	foreach ( $order->get_coupon_codes() as $coupon_code ) {

		// Only process SKYY-prefixed referral coupons.
		if ( 0 !== stripos( $coupon_code, 'SKYY' ) ) {
			continue;
		}

		$coupon = new WC_Coupon( $coupon_code );
		if ( ! $coupon->get_id() ) {
			continue;
		}

		$owner_email = get_post_meta( $coupon->get_id(), '_skyyrose_referral_owner_email', true );
		if ( ! is_email( $owner_email ) ) {
			continue;
		}

		// Prevent self-referral.
		if ( strtolower( $owner_email ) === strtolower( $order->get_billing_email() ) ) {
			continue;
		}

		$referrer = get_user_by( 'email', $owner_email );
		if ( ! $referrer ) {
			continue;
		}

		// Increment referral stats.
		$count  = (int) get_user_meta( $referrer->ID, '_skyyrose_referral_count', true );
		$earned = (float) get_user_meta( $referrer->ID, '_skyyrose_referral_earned', true );

		update_user_meta( $referrer->ID, '_skyyrose_referral_count', $count + 1 );
		update_user_meta( $referrer->ID, '_skyyrose_referral_earned', round( $earned + 10.0, 2 ) );

		// Founding Ambassador badge — first 100 referrers with a confirmed conversion.
		if ( ! get_user_meta( $referrer->ID, '_skyyrose_founding_ambassador', true ) ) {
			$total_founders = (int) get_option( 'skyyrose_founding_ambassador_count', 0 );
			if ( $total_founders < 100 ) {
				update_user_meta( $referrer->ID, '_skyyrose_founding_ambassador', 1 );
				update_option( 'skyyrose_founding_ambassador_count', $total_founders + 1 );
			}
		}

		// Mark order as credited to prevent duplicate processing.
		update_post_meta( $order_id, '_skyyrose_referral_credited', '1' );
		update_post_meta( $order_id, '_skyyrose_referral_code_used', sanitize_text_field( $coupon_code ) );

		/**
		 * Fires after a referral is successfully credited.
		 *
		 * Integrations can hook here to send notification emails or
		 * add store credit via third-party reward plugins.
		 *
		 * @since 5.0.0
		 *
		 * @param int   $referrer_id WP user ID of the referrer.
		 * @param int   $order_id    WooCommerce order ID that triggered the credit.
		 * @param float $credit      Credit amount in USD (10.00).
		 */
		do_action( 'skyyrose_referral_credited', $referrer->ID, $order_id, 10.0 );

		break; // One referral credit per order maximum.
	}
}
add_action( 'woocommerce_order_status_completed', 'skyyrose_woo_credit_referrer' );
