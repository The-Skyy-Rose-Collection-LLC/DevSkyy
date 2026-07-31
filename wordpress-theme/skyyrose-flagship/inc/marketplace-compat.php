<?php
/**
 * Commercial marketplace compatibility layer.
 *
 * Keeps vendor-plugin behavior inside plugins while giving Dokan, WCFM
 * Marketplace, and WC Vendors a shared SkyyRose presentation surface.
 *
 * @package SkyyRose
 * @since   2.0.0
 */

defined( 'ABSPATH' ) || exit;

/**
 * Detect active marketplace provider.
 *
 * @return string Provider slug or empty string.
 */
function skyyrose_marketplace_provider() {
	if ( function_exists( 'dokan' ) || class_exists( 'WeDevs_Dokan' ) ) {
		return 'dokan';
	}

	if ( function_exists( 'wcfm' ) || defined( 'WCFM_VERSION' ) ) {
		return 'wcfm';
	}

	if ( class_exists( 'WCV_Vendors' ) || defined( 'WCV_VERSION' ) ) {
		return 'wc-vendors';
	}

	return '';
}

/**
 * Determine whether current request belongs to marketplace UI.
 *
 * @return bool Whether marketplace-specific presentation is needed.
 */
function skyyrose_is_marketplace_surface() {
	$provider = skyyrose_marketplace_provider();
	if ( '' === $provider ) {
		return false;
	}

	if ( function_exists( 'dokan_is_store_page' ) && dokan_is_store_page() ) {
		return true;
	}

	if ( function_exists( 'wcfm_is_store_page' ) && wcfm_is_store_page() ) {
		return true;
	}

	if ( function_exists( 'wcfm_is_vendor' ) && wcfm_is_vendor() ) {
		return true;
	}

	if ( function_exists( 'is_account_page' ) && is_account_page() ) {
		return true;
	}

	return is_author();
}

/**
 * Add stable provider/body hooks without taking ownership of plugin markup.
 *
 * @param array $classes Existing body classes.
 * @return array Updated body classes.
 */
function skyyrose_marketplace_body_classes( $classes ) {
	$provider = skyyrose_marketplace_provider();
	if ( '' === $provider ) {
		return $classes;
	}

	$classes[] = 'skyyrose-marketplace';
	$classes[] = 'skyyrose-marketplace--' . sanitize_html_class( $provider );

	if ( skyyrose_is_marketplace_surface() ) {
		$classes[] = 'skyyrose-marketplace-surface';
		$classes[] = 'skyyrose-motion-quiet';
	}

	return array_values( array_unique( $classes ) );
}
add_filter( 'body_class', 'skyyrose_marketplace_body_classes' );

/**
 * Load one provider-neutral stylesheet only when marketplace plugin is active.
 *
 * @return void
 */
function skyyrose_enqueue_marketplace_styles() {
	if ( '' === skyyrose_marketplace_provider() ) {
		return;
	}

	$source = SKYYROSE_DIR . '/assets/css/marketplace.css';
	$file   = 'marketplace.css';

	if ( ( ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG )
		&& file_exists( SKYYROSE_DIR . '/assets/css/marketplace.min.css' ) ) {
		$file = 'marketplace.min.css';
	}

	if ( file_exists( $source ) ) {
		wp_enqueue_style(
			'skyyrose-marketplace',
			SKYYROSE_ASSETS_URI . '/css/' . $file,
			array( 'skyyrose-design-tokens', 'skyyrose-components' ),
			SKYYROSE_VERSION
		);
	}
}
add_action( 'wp_enqueue_scripts', 'skyyrose_enqueue_marketplace_styles', 25 );

/**
 * Resolve seller store URL through active provider.
 *
 * @param int $seller_id WordPress user ID.
 * @return string Seller storefront URL.
 */
function skyyrose_marketplace_store_url( $seller_id ) {
	$seller_id = absint( $seller_id );
	if ( 0 === $seller_id ) {
		return '';
	}

	if ( function_exists( 'dokan_get_store_url' ) ) {
		return dokan_get_store_url( $seller_id );
	}

	if ( function_exists( 'wcfmmp_get_store_url' ) ) {
		return wcfmmp_get_store_url( $seller_id );
	}

	$wc_vendors_class = 'WCV_Vendors';
	$store_callback   = array( $wc_vendors_class, 'get_vendor_shop_page' );
	if ( class_exists( $wc_vendors_class ) && is_callable( $store_callback ) ) {
		return (string) call_user_func( $store_callback, $seller_id );
	}

	return get_author_posts_url( $seller_id );
}

/**
 * Render seller identity above add-to-cart UI on multi-vendor products.
 *
 * @return void
 */
function skyyrose_render_marketplace_seller() {
	global $product;

	if ( '' === skyyrose_marketplace_provider() || ! is_a( $product, 'WC_Product' ) ) {
		return;
	}

	$seller_id = absint( get_post_field( 'post_author', $product->get_id() ) );
	$name      = get_the_author_meta( 'display_name', $seller_id );
	$url       = skyyrose_marketplace_store_url( $seller_id );

	if ( '' === $name || '' === $url ) {
		return;
	}
	?>
	<aside class="marketplace-seller" aria-label="<?php esc_attr_e( 'Seller information', 'skyyrose' ); ?>">
		<span class="marketplace-seller__eyebrow"><?php esc_html_e( 'Marketplace seller', 'skyyrose' ); ?></span>
		<a class="marketplace-seller__name" href="<?php echo esc_url( $url ); ?>"><?php echo esc_html( $name ); ?></a>
		<span class="marketplace-seller__provider"><?php esc_html_e( 'Powered by SkyyRose marketplace standards', 'skyyrose' ); ?></span>
	</aside>
	<?php
}
add_action( 'woocommerce_before_add_to_cart_form', 'skyyrose_render_marketplace_seller', 5 );
