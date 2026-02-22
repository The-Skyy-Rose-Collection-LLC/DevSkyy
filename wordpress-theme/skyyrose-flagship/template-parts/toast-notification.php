<?php
/**
 * Template Part: Toast Notification
 *
 * Reusable toast notification component with slide-in animation,
 * dark glass styling, auto-dismiss, and close button.
 *
 * This template renders a single toast. The JS toast system in
 * navigation.js handles dynamic creation. This template can also
 * be used for server-side rendered toasts (e.g., after form submission).
 *
 * Usage:
 *   get_template_part( 'template-parts/toast-notification', null, $args );
 *
 * @param array $args {
 *     Toast notification arguments.
 *
 *     @type string $message  Toast message text.
 *     @type string $type     Toast type: 'success', 'error', 'warning', 'info' (default 'info').
 *     @type string $id       Optional unique ID for the toast.
 *     @type int    $duration Auto-dismiss duration in ms (default 3000). Set 0 to disable.
 *     @type bool   $visible  Whether toast starts visible (default false).
 * }
 *
 * @package SkyyRose_Flagship
 * @since 2.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$defaults = array(
	'message'  => '',
	'type'     => 'info',
	'id'       => 'toast-' . wp_unique_id(),
	'duration' => 3000,
	'visible'  => false,
);

$args = wp_parse_args( $args ?? array(), $defaults );

// Validate type.
$valid_types = array( 'success', 'error', 'warning', 'info' );
$type = in_array( $args['type'], $valid_types, true ) ? $args['type'] : 'info';

// Build class list.
$toast_classes = array(
	'toast',
	'toast--' . $type,
);
if ( $args['visible'] ) {
	$toast_classes[] = 'toast--visible';
}

// Icon SVG per type.
$icons = array(
	'success' => '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="M22 4 12 14.01l-3-3"/>',
	'error'   => '<circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/>',
	'warning' => '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><circle cx="12" cy="16" r="0.5" fill="currentColor"/>',
	'info'    => '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><circle cx="12" cy="8" r="0.5" fill="currentColor"/>',
);

if ( empty( $args['message'] ) ) {
	return;
}
?>

<div
	class="<?php echo esc_attr( implode( ' ', $toast_classes ) ); ?>"
	id="<?php echo esc_attr( $args['id'] ); ?>"
	role="alert"
	aria-live="assertive"
	aria-atomic="true"
	data-duration="<?php echo esc_attr( $args['duration'] ); ?>"
>
	<div class="toast__icon" aria-hidden="true">
		<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" focusable="false">
			<?php echo $icons[ $type ]; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- Static SVG markup. ?>
		</svg>
	</div>
	<div class="toast__content">
		<p class="toast__message"><?php echo esc_html( $args['message'] ); ?></p>
	</div>
	<button
		class="toast__close"
		aria-label="<?php esc_attr_e( 'Dismiss notification', 'skyyrose-flagship' ); ?>"
		type="button"
	>
		<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
			<path d="M18 6 6 18"/>
			<path d="m6 6 12 12"/>
		</svg>
	</button>
	<?php if ( $args['duration'] > 0 ) : ?>
		<div class="toast__progress" aria-hidden="true">
			<div class="toast__progress-bar" style="animation-duration: <?php echo esc_attr( $args['duration'] ); ?>ms;"></div>
		</div>
	<?php endif; ?>
</div>
