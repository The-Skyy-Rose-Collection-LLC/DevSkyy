<?php
/**
 * WooCommerce Pre-Order & Referral System
 *
 * Pre-order meta fields, admin meta boxes, front-end notices,
 * button text overrides, price display, and referral credit logic.
 *
 * Split from inc/woocommerce.php for maintainability.
 *
 * @package SkyyRose
 * @since   6.3.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/*
--------------------------------------------------------------
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
		esc_html__( 'Pre-Order Settings', 'skyyrose' ),
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
			<?php esc_html_e( 'This is a pre-order product', 'skyyrose' ); ?>
		</label>
	</p>
	<p>
		<label for="skyyrose_edition_size"><?php esc_html_e( 'Edition Size', 'skyyrose' ); ?></label>
		<input type="number" id="skyyrose_edition_size" name="skyyrose_edition_size" value="<?php echo esc_attr( $edition_size ); ?>" min="1" style="width:100%;" placeholder="e.g. 250" />
	</p>
	<p>
		<label for="skyyrose_preorder_available"><?php esc_html_e( 'Available Remaining', 'skyyrose' ); ?></label>
		<input type="number" id="skyyrose_preorder_available" name="skyyrose_preorder_available" value="<?php echo esc_attr( $available ); ?>" min="0" style="width:100%;" />
	</p>
	<p>
		<label for="skyyrose_ship_date"><?php esc_html_e( 'Expected Ship Date', 'skyyrose' ); ?></label>
		<input type="date" id="skyyrose_ship_date" name="skyyrose_ship_date" value="<?php echo esc_attr( $ship_date ); ?>" style="width:100%;" />
	</p>
	<p>
		<label for="skyyrose_preorder_price"><?php esc_html_e( 'Pre-Order Price ($)', 'skyyrose' ); ?></label>
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
	echo '<span class="skyyrose-preorder-notice__badge">' . esc_html__( 'Pre-Order', 'skyyrose' ) . '</span>';

	if ( $edition_size ) {
		echo '<div class="skyyrose-preorder-notice__detail">' . esc_html__( 'Limited Edition', 'skyyrose' ) . ' — <strong>' . esc_html( $edition_size ) . ' ' . esc_html__( 'pieces', 'skyyrose' ) . '</strong>';
		if ( $available ) {
			echo ' · <strong>' . esc_html( $available ) . ' ' . esc_html__( 'remaining', 'skyyrose' ) . '</strong>';
		}
		echo '</div>';
	}

	if ( $preorder_px ) {
		echo '<div class="skyyrose-preorder-notice__detail">' . esc_html__( 'Early Access Price:', 'skyyrose' ) . ' <strong>' . esc_html( get_woocommerce_currency_symbol() ) . esc_html( $preorder_px ) . '</strong></div>';
	}

	if ( $ship_date ) {
		echo '<div class="skyyrose-preorder-notice__ship-date">' . esc_html__( 'Expected Ship Date:', 'skyyrose' ) . ' ' . esc_html( date_i18n( 'F j, Y', strtotime( $ship_date ) ) ) . '</div>';
	}

	echo '</div>';
}
add_action( 'woocommerce_single_product_summary', 'skyyrose_preorder_single_product_notice', 6 );

/**
 * Replace "Add to Cart" text with "Pre-Order Now" for pre-order products.
 *
 * @since 3.10.0
 *
 * @param string     $text    Default button text.
 * @param WC_Product $product Product object.
 * @return string Modified button text.
 */
function skyyrose_preorder_button_text( $text, $product ) {
	if ( $product && skyyrose_is_preorder( $product->get_id() ) ) {
		return esc_html__( 'Pre-Order Now', 'skyyrose' );
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
			. esc_html__( 'Pre-Order', 'skyyrose' )
			. ' &mdash; '
			. esc_html( get_woocommerce_currency_symbol() )
			. esc_html( number_format( (float) $preorder_price, 0 ) )
			. '</span>';
	}

	return '<span class="woocommerce-Price-amount amount">'
		. esc_html__( 'Pre-Order', 'skyyrose' )
		. '</span>';
}
add_filter( 'woocommerce_get_price_html', 'skyyrose_preorder_price_html', 10, 2 );

/*
--------------------------------------------------------------
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
