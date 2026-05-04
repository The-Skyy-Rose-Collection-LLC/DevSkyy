<?php
/**
 * Component: Modal
 *
 * Renders an accessible modal dialog. PHP markup only — JS focus-trap and
 * open/close behaviour is wired in Phase 5 via data-* hooks.
 *
 * Trigger: any element with data-modal-trigger="<modal-id>"
 * Dismiss: any element inside the modal with data-dismiss="modal"
 *
 * Usage:
 *   ob_start();
 *   // ... inner content ...
 *   $slot = ob_get_clean();
 *
 *   get_template_part( 'template-parts/components/modal', null, [
 *       'modal_id'      => 'size-guide',          // required, unique per page
 *       'title'         => 'Size Guide',
 *       'size'          => 'md',                  // sm | md | lg | full
 *       'show_close'    => true,
 *       'close_label'   => 'Close',
 *       'extra_classes' => '',
 *       'attrs'         => [],
 *       'slot'          => $slot,
 *   ] );
 *
 * @package SkyyRose
 */

defined( 'ABSPATH' ) || exit;

$args = wp_parse_args(
	$args ?? array(),
	array(
		'modal_id'      => '',
		'title'         => '',
		'size'          => 'md',
		'show_close'    => true,
		'close_label'   => __( 'Close', 'skyyrose' ),
		'extra_classes' => '',
		'attrs'         => array(),
		'slot'          => '',
	)
);

$modal_id = sanitize_html_class( $args['modal_id'] );
if ( ! $modal_id ) {
	return;
}

$allowed_sizes = array( 'sm', 'md', 'lg', 'full' );
$size          = in_array( $args['size'], $allowed_sizes, true ) ? $args['size'] : 'md';
$title_id      = $modal_id . '-title';
$content_id    = $modal_id . '-content';

$modal_classes = implode(
	' ',
	array_filter(
		array(
			'sr-modal',
			'sr-modal--' . $size,
			skyyrose_sanitize_class_list( $args['extra_classes'] ?? '' ),
		)
	)
);

// Build extra attributes string.
$attr_string = skyyrose_build_attr_string( $args['attrs'] ?? array() );
?>
<div
	class="sr-modal__backdrop"
	id="<?php echo esc_attr( $modal_id ); ?>"
	data-component="modal"
	data-modal-id="<?php echo esc_attr( $modal_id ); ?>"
	hidden
	aria-hidden="true"
>
	<div
		class="<?php echo esc_attr( $modal_classes ); ?>"
		role="dialog"
		aria-modal="true"
		aria-labelledby="<?php echo esc_attr( $title_id ); ?>"
		aria-describedby="<?php echo esc_attr( $content_id ); ?>"
		data-focus-trap="true"
		tabindex="-1"
		<?php echo $attr_string; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- pre-escaped above. ?>
	>
		<div class="sr-modal__header">

			<?php if ( $args['title'] ) : ?>
				<h2 class="sr-modal__title" id="<?php echo esc_attr( $title_id ); ?>">
					<?php echo esc_html( $args['title'] ); ?>
				</h2>
			<?php else : ?>
				<span id="<?php echo esc_attr( $title_id ); ?>" class="sr-visually-hidden">
					<?php esc_html_e( 'Dialog', 'skyyrose' ); ?>
				</span>
			<?php endif; ?>

			<?php if ( $args['show_close'] ) : ?>
				<button
					class="sr-modal__close"
					type="button"
					data-dismiss="modal"
					aria-label="<?php echo esc_attr( $args['close_label'] ); ?>"
				>
					<span aria-hidden="true">&times;</span>
				</button>
			<?php endif; ?>

		</div>

		<div class="sr-modal__content" id="<?php echo esc_attr( $content_id ); ?>">
			<?php echo wp_kses_post( $args['slot'] ); ?>
		</div>

	</div>
</div>
