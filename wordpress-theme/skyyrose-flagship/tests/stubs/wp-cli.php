<?php
/**
 * PHPStan discovery stub for the optional WP-CLI progress-bar helper.
 *
 * This file is never loaded by WordPress.
 */

namespace WP_CLI\Utils;

/**
 * Create a WP-CLI progress bar.
 *
 * @param string $message Progress label.
 * @param int    $count   Total operations.
 * @return ProgressBar
 */
function make_progress_bar( $message, $count ) {}

/** PHPStan-only shape returned by make_progress_bar(). */
class ProgressBar {
	/** Advance the progress bar. */
	public function tick() {}

	/** Finish the progress bar. */
	public function finish() {}
}
