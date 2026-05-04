<?php
/**
 * Component: Drawer
 *
 * An off-canvas panel that slides in from an edge. PHP markup only — JS
 * open/close and focus management wired in Phase 5 via data-* hooks.
 *
 * Trigger: any element with data-drawer-trigger="<drawer-id>"
 * Dismiss: any element inside the drawer with data-dismiss="drawer"
 *
 * Usage:
 *   ob_start();
 *   // ... inner content ...
 *   $slot = ob_get_clean();
 *
 *   get_template_part( 'template-parts/components/drawer', null, [
 *       'drawer_id'     => 'cart-drawer',         // required, unique per page
 *       'title'         => 'Your Cart',
 *       'side'          => 'right',               // left | right | bottom
 *       'size'          => 'md',                  // sm | md | lg
 *       'show_close'    => true,
 *       'close_label'   => 'Close',
 *       'overlay'       => true,                  // renders a dimming backdrop
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
		'drawer_id'     => '',
		'title'         => '',
		'side'          => 'right',
		'size'          => 'md',
		'show_close'    => true,
		'close_label'   => __( 'Close', 'skyyrose' ),
		'overlay'       => true,
		'extra_classes' => '',
		'attrs'         => array(),
		'slot'          => '',
	)
);

$drawer_id = sanitize_html_class( $args['drawer_id'] );
if ( ! $drawer_id ) {
	return;
}

$allowed_sides = array( 'left', 'right', 'bottom' );
$allowed_sizes = array( 'sm', 'md', 'lg' );
$side          = in_array( $args['side'], $allowed_sides, true ) ? $args['side'] : 'right';
$size          = in_array( $args['size'], $allowed_sizes, true ) ? $args['size'] : 'md';
$title_id      = $drawer_id . '-title';
$content_id    = $drawer_id . '-content';

$drawer_classes = implode(
	' ',
	array_filter(
		array(
			'sr-drawer',
			'sr-drawer--' . $side,
			'sr-drawer--' . $size,
			skyyrose_sanitize_class_list( $args['extra_classes'] ?? '' ),
		)
	)
);

// Build extra attributes string.
$attr_string = skyyrose_build_attr_string( $args['attrs'] ?? array() );
?>
<div
	class="sr-drawer__root"
	id="<?php echo esc_attr( $drawer_id ); ?>"
	data-component="drawer"
	data-drawer-id="<?php echo esc_attr( $drawer_id ); ?>"
	data-drawer-side="<?php echo esc_attr( $side ); ?>"
	hidden
	aria-hidden="true"
>
	<?php if ( $args['overlay'] ) : ?>
		<div
			class="sr-drawer__overlay"
			data-dismiss="drawer"
			aria-hidden="true"
			tabindex="-1"
		></div>
	<?php endif; ?>

	<div
		class="<?php echo esc_attr( $drawer_classes ); ?>"
		role="dialog"
		aria-modal="true"
		aria-labelledby="<?php echo esc_attr( $title_id ); ?>"
		aria-describedby="<?php echo esc_attr( $content_id ); ?>"
		data-focus-trap="true"
		tabindex="-1"
		<?php echo $attr_string; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- pre-escaped above. ?>
	>
		<div class="sr-drawer__header">

			<?php if ( $args['title'] ) : ?>
				<h2 class="sr-drawer__title" id="<?php echo esc_attr( $title_id ); ?>">
					<?php echo esc_html( $args['title'] ); ?>
				</h2>
			<?php else : ?>
				<span id="<?php echo esc_attr( $title_id ); ?>" class="sr-visually-hidden">
					<?php esc_html_e( 'Panel', 'skyyrose' ); ?>
				</span>
			<?php endif; ?>

			<?php if ( $args['show_close'] ) : ?>
				<button
					class="sr-drawer__close"
					type="button"
					data-dismiss="drawer"
					aria-label="<?php echo esc_attr( $args['close_label'] ); ?>"
				>
					<span aria-hidden="true">&times;</span>
				</button>
			<?php endif; ?>

		</div>

		<div class="sr-drawer__content" id="<?php echo esc_attr( $content_id ); ?>">
			<?php echo wp_kses_post( $args['slot'] ); ?>
		</div>

	</div>
</div>
