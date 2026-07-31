<?php
/**
 * Performance CLI
 *
 * WP-CLI backfill support for next-generation Media Library derivatives.
 *
 * @package SkyyRose
 * @since   7.1.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

if ( defined( 'WP_CLI' ) && WP_CLI ) {
	WP_CLI::add_command( 'skyyrose nextgen-backfill', 'skyyrose_nextgen_backfill_cli' );
}

/**
 * WP-CLI entry point for `wp skyyrose nextgen-backfill`.
 *
 * @param array $args       Positional args (unused).
 * @param array $assoc_args --limit=N, --dry-run.
 * @return void
 */
function skyyrose_nextgen_backfill_cli( $args, $assoc_args ) {
	unset( $args );

	$limit   = isset( $assoc_args['limit'] ) ? (int) $assoc_args['limit'] : -1;
	$dry_run = ! empty( $assoc_args['dry-run'] );
	$gd_avif = function_exists( 'imageavif' );
	$gd_webp = function_exists( 'imagewebp' );

	if ( ! $gd_avif && ! $gd_webp ) {
		WP_CLI::error( 'GD lacks both imageavif() and imagewebp() — install libavif + libwebp on PHP.' );
	}

	$pending  = skyyrose_nextgen_backfill_pending_ids();
	$total    = count( $pending );
	$counters = array(
		'converted'   => 0,
		'marked_done' => 0,
		'processed'   => 0,
		'skipped'     => 0,
	);
	$progress = WP_CLI\Utils\make_progress_bar(
		"Backfilling AVIF/WebP for {$total} pending attachments",
		( $limit > 0 ) ? min( $total, $limit ) : $total
	);

	foreach ( $pending as $attachment_id ) {
		if ( $limit > 0 && $counters['converted'] >= $limit ) {
			break;
		}
		skyyrose_nextgen_backfill_one( (int) $attachment_id, $dry_run, $gd_avif, $gd_webp, $counters );
		$progress->tick();
	}

	$progress->finish();
	$verb = $dry_run ? 'Would convert' : 'Converted';
	WP_CLI::success(
		"{$verb} {$counters['converted']} files. Processed {$counters['processed']} of {$total} pending; "
		. "marked {$counters['marked_done']} attachments complete; skipped {$counters['skipped']} missing originals."
	);
}

/**
 * Query attachment IDs still needing AVIF/WebP siblings.
 *
 * @return int[] Attachment IDs, ordered ASC by ID.
 */
function skyyrose_nextgen_backfill_pending_ids(): array {
	$query = new WP_Query(
		array(
			'post_type'      => 'attachment',
			'post_status'    => 'inherit',
			'post_mime_type' => array( 'image/jpeg', 'image/png' ),
			'posts_per_page' => -1,
			'fields'         => 'ids',
			'no_found_rows'  => true,
			'orderby'        => 'ID',
			'order'          => 'ASC',
			'meta_query'     => array( // phpcs:ignore WordPress.DB.SlowDBQuery.slow_db_query_meta_query
				array(
					'key'     => '_skyyrose_nextgen_done',
					'compare' => 'NOT EXISTS',
				),
			),
		)
	);
	return array_map( 'intval', (array) $query->posts );
}

/**
 * Resolve size-whitelisted target filenames for an attachment.
 *
 * @param string $file     Absolute path to full-size source file.
 * @param array  $metadata wp_get_attachment_metadata() return value.
 * @return string[] Basenames of files to convert.
 */
function skyyrose_nextgen_backfill_targets( string $file, $metadata ): array {
	$size_whitelist = array( 'thumbnail', 'medium', 'large', 'skyyrose-product-avif' );
	$targets        = array( basename( $file ) );

	if ( empty( $metadata['sizes'] ) || ! is_array( $metadata['sizes'] ) ) {
		return $targets;
	}
	foreach ( $size_whitelist as $size_key ) {
		if ( ! empty( $metadata['sizes'][ $size_key ]['file'] ) ) {
			$targets[] = $metadata['sizes'][ $size_key ]['file'];
		}
	}
	return $targets;
}

/**
 * Backfill AVIF/WebP siblings for one attachment.
 *
 * @param int   $attachment_id WP attachment ID.
 * @param bool  $dry_run       When true, count conversions but do not write.
 * @param bool  $gd_avif       GD imageavif() availability.
 * @param bool  $gd_webp       GD imagewebp() availability.
 * @param array $counters      Conversion counters, mutated by reference.
 * @return void
 */
function skyyrose_nextgen_backfill_one( int $attachment_id, bool $dry_run, bool $gd_avif, bool $gd_webp, array &$counters ): void {
	$file = get_attached_file( $attachment_id );
	if ( ! $file || ! file_exists( $file ) ) {
		++$counters['skipped'];
		return;
	}

	$base_dir = dirname( $file );
	$targets  = skyyrose_nextgen_backfill_targets( $file, wp_get_attachment_metadata( $attachment_id ) );
	$all_done = true;

	foreach ( $targets as $name ) {
		$src_path    = $base_dir . '/' . $name;
		$base_no_ext = preg_replace( '/\.(jpe?g|png)$/i', '', $src_path );
		if ( ! file_exists( $src_path ) || null === $base_no_ext ) {
			continue;
		}

		if ( $gd_webp && ! file_exists( $base_no_ext . '.webp' ) ) {
			if ( $dry_run ) {
				++$counters['converted'];
				$all_done = false;
			} elseif ( skyyrose_gd_convert( $src_path, $base_no_ext . '.webp', 'webp' ) ) {
				++$counters['converted'];
			} else {
				$all_done = false;
			}
		}
		if ( $gd_avif && ! file_exists( $base_no_ext . '.avif' ) ) {
			if ( $dry_run ) {
				++$counters['converted'];
				$all_done = false;
			} elseif ( skyyrose_gd_convert( $src_path, $base_no_ext . '.avif', 'avif' ) ) {
				++$counters['converted'];
			} else {
				$all_done = false;
			}
		}
		if ( function_exists( 'gc_collect_cycles' ) ) {
			gc_collect_cycles();
		}
	}

	if ( $all_done && ! $dry_run ) {
		update_post_meta( $attachment_id, '_skyyrose_nextgen_done', 1 );
		++$counters['marked_done'];
	}
	++$counters['processed'];
}

/**
 * Derive the AVIF sibling path and URL for an asset URL.
 *
 * @param string $src_url Source image URL.
 * @return array|null Path and URL pair, or null.
 */
function skyyrose_avif_sibling_pair( string $src_url ): ?array {
	$abs_path = skyyrose_url_to_path( strtok( $src_url, '?' ) );
	if ( null === $abs_path ) {
		return null;
	}
	$path_no_ext = preg_replace( '/\.(jpe?g|png|webp)$/i', '', $abs_path );
	$url_no_ext  = preg_replace( '/\.(jpe?g|png|webp)$/i', '', $src_url );
	if ( null === $path_no_ext || $path_no_ext === $abs_path ) {
		return null;
	}
	return array(
		'path' => $path_no_ext . '.avif',
		'url'  => $url_no_ext . '.avif',
	);
}
