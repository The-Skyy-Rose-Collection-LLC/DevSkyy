<?php
/**
 * WooCommerce Kids Capsule Custom Fields
 *
 * Meta box for age range, matching adult product ID, and drop number.
 * Only visible on products in the "kids-capsule" category.
 *
 * @package SkyyRose
 * @since   6.5.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Register the Kids Capsule meta box on product edit screens.
 *
 * @since 6.5.0
 * @return void
 */
function skyyrose_add_kc_meta_box() {
	add_meta_box(
		'skyyrose_kc_settings',
		esc_html__( 'Kids Capsule Settings', 'skyyrose' ),
		'skyyrose_kc_meta_box_callback',
		'product',
		'side',
		'default'
	);
}
add_action( 'add_meta_boxes', 'skyyrose_add_kc_meta_box' );

/**
 * Render the Kids Capsule meta box UI.
 *
 * Only renders fields when the product belongs to the kids-capsule category.
 *
 * @since 6.5.0
 *
 * @param WP_Post $post Current post object.
 * @return void
 */
function skyyrose_kc_meta_box_callback( $post ) {

	$categories = wp_get_post_terms( $post->ID, 'product_cat', array( 'fields' => 'slugs' ) );
	if ( is_wp_error( $categories ) || ! in_array( 'kids-capsule', $categories, true ) ) {
		echo '<p>' . esc_html__( 'Assign this product to the "Kids Capsule" category to enable these fields.', 'skyyrose' ) . '</p>';
		return;
	}

	wp_nonce_field( 'skyyrose_kc_meta_nonce', 'skyyrose_kc_meta_nonce' );

	$age_range   = get_post_meta( $post->ID, '_kc_age_range', true );
	$adult_id    = get_post_meta( $post->ID, '_kc_matching_adult_id', true );
	$drop_number = get_post_meta( $post->ID, '_kc_drop_number', true );

	$age_options = array(
		''      => esc_html__( 'Select age range', 'skyyrose' ),
		'2t-3t' => '2T - 3T (Toddler)',
		'4t-5t' => '4T - 5T (Toddler)',
		'4-6'   => '4 - 6 (Kids)',
		'7-10'  => '7 - 10 (Kids)',
		'11-14' => '11 - 14 (Youth)',
		'14-16' => '14 - 16 (Youth/Junior)',
	);
	?>
	<p>
		<label for="skyyrose_kc_age_range"><?php esc_html_e( 'Age Range', 'skyyrose' ); ?></label>
		<select id="skyyrose_kc_age_range" name="skyyrose_kc_age_range" style="width:100%;">
			<?php foreach ( $age_options as $value => $label ) : ?>
				<option value="<?php echo esc_attr( $value ); ?>" <?php selected( $age_range, $value ); ?>>
					<?php echo esc_html( $label ); ?>
				</option>
			<?php endforeach; ?>
		</select>
	</p>
	<p>
		<label for="skyyrose_kc_adult_id"><?php esc_html_e( 'Matching Adult Product ID', 'skyyrose' ); ?></label>
		<input type="number" id="skyyrose_kc_adult_id" name="skyyrose_kc_adult_id"
			value="<?php echo esc_attr( $adult_id ); ?>" min="0" style="width:100%;"
			placeholder="<?php esc_attr_e( 'WC product ID of matching adult piece', 'skyyrose' ); ?>" />
	</p>
	<p>
		<label for="skyyrose_kc_drop_number"><?php esc_html_e( 'Drop #', 'skyyrose' ); ?></label>
		<input type="text" id="skyyrose_kc_drop_number" name="skyyrose_kc_drop_number"
			value="<?php echo esc_attr( $drop_number ); ?>" style="width:100%;"
			placeholder="<?php esc_attr_e( 'e.g. 1', 'skyyrose' ); ?>" />
	</p>
	<?php
}

/**
 * Save Kids Capsule meta box data.
 *
 * @since 6.5.0
 *
 * @param int $post_id Post ID.
 * @return void
 */
function skyyrose_save_kc_meta( $post_id ) {

	if ( ! isset( $_POST['skyyrose_kc_meta_nonce'] ) ) {
		return;
	}

	if ( ! wp_verify_nonce( sanitize_text_field( wp_unslash( $_POST['skyyrose_kc_meta_nonce'] ) ), 'skyyrose_kc_meta_nonce' ) ) {
		return;
	}

	if ( defined( 'DOING_AUTOSAVE' ) && DOING_AUTOSAVE ) {
		return;
	}

	if ( ! current_user_can( 'edit_post', $post_id ) ) {
		return;
	}

	// Age range — validate against allowed values.
	if ( isset( $_POST['skyyrose_kc_age_range'] ) ) {
		$age     = sanitize_text_field( wp_unslash( $_POST['skyyrose_kc_age_range'] ) );
		$allowed = array( '', '2t-3t', '4t-5t', '4-6', '7-10', '11-14', '14-16' );
		if ( in_array( $age, $allowed, true ) ) {
			update_post_meta( $post_id, '_kc_age_range', $age );
		}
	}

	// Matching adult product ID.
	if ( isset( $_POST['skyyrose_kc_adult_id'] ) ) {
		$adult_id = absint( wp_unslash( $_POST['skyyrose_kc_adult_id'] ) );
		update_post_meta( $post_id, '_kc_matching_adult_id', $adult_id );
	}

	// Drop number.
	if ( isset( $_POST['skyyrose_kc_drop_number'] ) ) {
		$drop = sanitize_text_field( wp_unslash( $_POST['skyyrose_kc_drop_number'] ) );
		update_post_meta( $post_id, '_kc_drop_number', $drop );
	}
}
add_action( 'save_post_product', 'skyyrose_save_kc_meta' );

/*
--------------------------------------------------------------
 * Frontend — Matching Set Render
 *--------------------------------------------------------------*/

/**
 * Render the kids-capsule matching-set partial after the single product
 * summary on Kids Capsule product pages.
 *
 * Closes the half-shipped feature where admins enter `_kc_matching_adult_id`
 * via meta box but the frontend never rendered the matching adult card.
 *
 * Defenses: skip self-references and circular meta loops.
 *
 * @since 1.3.0
 * @return void
 */
function skyyrose_render_kc_matching_set() {
	if ( ! is_product() || ! function_exists( 'has_term' ) ) {
		return;
	}
	if ( ! has_term( 'kids-capsule', 'product_cat' ) ) {
		return;
	}

	$current_id  = (int) get_the_ID();
	$kc_adult_id = (int) get_post_meta( $current_id, '_kc_matching_adult_id', true );

	// Defense 1: skip when no matching adult set OR self-reference.
	if ( ! $kc_adult_id || $kc_adult_id === $current_id ) {
		return;
	}

	// Defense 2: skip when the adult itself has a matching meta set (loop).
	if ( get_post_meta( $kc_adult_id, '_kc_matching_adult_id', true ) ) {
		return;
	}

	get_template_part( 'template-parts/kids-capsule/matching-set' );
}
add_action( 'woocommerce_after_single_product_summary', 'skyyrose_render_kc_matching_set', 25 );
