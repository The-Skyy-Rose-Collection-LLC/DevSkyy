<?php
/**
 * Import v1 catalog-approved primary product images into WooCommerce.
 *
 * Run through WP-CLI on staging only, with SKYYROSE_SOT_SOURCE_DIR pointing
 * to a directory containing data/skyyrose-catalog.csv and its referenced
 * assets/images/products files. The operation is idempotent: a product whose
 * current featured attachment records the same source path is skipped.
 *
 * @package SkyyRoseFlagship2
 */

defined( 'ABSPATH' ) || exit;

$source_dir = getenv( 'SKYYROSE_SOT_SOURCE_DIR' );
if ( ! $source_dir || ! is_dir( $source_dir ) ) {
	WP_CLI::error( 'SKYYROSE_SOT_SOURCE_DIR must be an existing v1 asset directory.' );
}

$catalog_path = trailingslashit( $source_dir ) . 'data/skyyrose-catalog.csv';
if ( ! is_readable( $catalog_path ) ) {
	WP_CLI::error( 'The v1 catalog CSV is missing or unreadable.' );
}

require_once ABSPATH . 'wp-admin/includes/file.php';
require_once ABSPATH . 'wp-admin/includes/image.php';
require_once ABSPATH . 'wp-admin/includes/media.php';

$handle  = fopen( $catalog_path, 'r' ); // phpcs:ignore WordPress.WP.AlternativeFunctions.file_system_operations_fopen
$headers = $handle ? fgetcsv( $handle, 0, ',', '"', '\\' ) : false; // phpcs:ignore WordPress.WP.AlternativeFunctions.file_system_operations_fgetcsv
if ( ! $headers ) {
	WP_CLI::error( 'The v1 catalog CSV has no readable header row.' );
}

$result = array(
	'imported' => 0,
	'skipped'  => 0,
	'missing'  => array(),
	'unmatched' => array(),
	'failed'   => array(),
);

while ( ( $row = fgetcsv( $handle, 0, ',', '"', '\\' ) ) !== false ) { // phpcs:ignore WordPress.WP.AlternativeFunctions.file_system_operations_fgetcsv, Generic.CodeAnalysis.AssignmentInCondition.FoundInWhileCondition
	$row  = array_pad( $row, count( $headers ), '' );
	$item = array_combine( $headers, $row );
	$sku  = sanitize_text_field( $item['sku'] ?? '' );
	$path = (string) ( $item['front_model_image'] ?? '' );
	if ( '' === $path ) {
		$path = (string) ( $item['image'] ?? '' );
	}
	if ( '' === $sku || '' === $path ) {
		continue;
	}

	$file = trailingslashit( $source_dir ) . ltrim( $path, '/' );
	if ( ! is_readable( $file ) ) {
		$result['missing'][] = $sku;
		continue;
	}

	$product_id = wc_get_product_id_by_sku( $sku );
	if ( ! $product_id ) {
		$result['unmatched'][] = $sku;
		continue;
	}

	$product       = wc_get_product( $product_id );
	$current_image = $product ? $product->get_image_id() : 0;
	if ( $current_image && $path === get_post_meta( $current_image, '_skyyrose_sot_source_path', true ) ) {
		++$result['skipped'];
		continue;
	}

	$upload = wp_upload_bits( sanitize_file_name( basename( $file ) ), null, file_get_contents( $file ) ); // phpcs:ignore WordPress.WP.AlternativeFunctions.file_get_contents_file_get_contents
	if ( ! empty( $upload['error'] ) ) {
		$result['failed'][] = $sku . ': ' . $upload['error'];
		continue;
	}

	$filetype      = wp_check_filetype( $upload['file'], null );
	$attachment_id = wp_insert_attachment(
		array(
			'post_mime_type' => $filetype['type'],
			'post_title'     => sanitize_text_field( $item['name'] ?? $sku ),
			'post_status'    => 'inherit',
		),
		$upload['file'],
		$product_id
	);
	if ( is_wp_error( $attachment_id ) ) {
		$result['failed'][] = $sku . ': ' . $attachment_id->get_error_message();
		continue;
	}

	wp_update_attachment_metadata( $attachment_id, wp_generate_attachment_metadata( $attachment_id, $upload['file'] ) );
	update_post_meta( $attachment_id, '_wp_attachment_image_alt', sanitize_text_field( $item['name'] ?? $sku ) );
	update_post_meta( $attachment_id, '_skyyrose_sot_source_path', $path );
	$product->set_image_id( $attachment_id );
	$product->save();
	++$result['imported'];
}

fclose( $handle ); // phpcs:ignore WordPress.WP.AlternativeFunctions.file_system_operations_fclose
WP_CLI::success( wp_json_encode( $result ) );
