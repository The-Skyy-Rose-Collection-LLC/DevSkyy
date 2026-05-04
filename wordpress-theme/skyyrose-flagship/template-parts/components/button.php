<?php
/**
 * Component: Button
 *
 * Usage:
 *   get_template_part( 'template-parts/components/button', null, [
 *       'label'    => __( 'Shop Now', 'skyyrose' ),
 *       'variant'  => 'primary',   // primary | ghost | outline | text
 *       'size'     => 'md',        // sm | md | lg
 *       'tag'      => 'button',    // button | a
 *       'type'     => 'button',    // button | submit | reset (ignored for <a>)
 *       'href'     => '',          // required when tag=a
 *       'disabled' => false,
 *       'loading'  => false,
 *       'icon_before' => '',       // raw SVG string (wp_kses'd)
 *       'icon_after'  => '',       // raw SVG string (wp_kses'd)
 *       'extra_classes' => '',
 *       'attrs'    => [],          // [ 'data-foo' => 'bar' ] extra HTML attributes
 *   ] );
 *
 * @package SkyyRose
 */

defined( 'ABSPATH' ) || exit;

$args = wp_parse_args(
	$args ?? array(),
	array(
		'label'         => '',
		'variant'       => 'primary',
		'size'          => 'md',
		'tag'           => 'button',
		'type'          => 'button',
		'href'          => '',
		'disabled'      => false,
		'loading'       => false,
		'icon_before'   => '',
		'icon_after'    => '',
		'extra_classes' => '',
		'attrs'         => array(),
	)
);

$variant       = in_array( $args['variant'], array( 'primary', 'ghost', 'outline', 'text' ), true ) ? $args['variant'] : 'primary';
$size          = in_array( $args['size'], array( 'sm', 'md', 'lg' ), true ) ? $args['size'] : 'md';
$tag           = 'a' === $args['tag'] ? 'a' : 'button';
$is_disabled   = (bool) $args['disabled'];
$is_loading    = (bool) $args['loading'];
$label         = (string) $args['label'];
$extra_classes = skyyrose_sanitize_class_list( $args['extra_classes'] ?? '' );

$classes = implode(
	' ',
	array_filter(
		array(
			'sr-btn',
			'sr-btn--' . $variant,
			'sr-btn--' . $size,
			$is_loading ? 'sr-btn--loading' : '',
			$is_disabled ? 'sr-btn--disabled' : '',
			$extra_classes,
		)
	)
);

// Build extra attributes string.
$attr_string = skyyrose_build_attr_string( $args['attrs'] ?? array() );

if ( 'button' === $tag ) :
	$btn_type = in_array( $args['type'], array( 'button', 'submit', 'reset' ), true ) ? $args['type'] : 'button';
	?>
	<button
		class="<?php echo esc_attr( $classes ); ?>"
		type="<?php echo esc_attr( $btn_type ); ?>"
		<?php echo $is_disabled || $is_loading ? 'disabled' : ''; ?>
		<?php echo $is_loading ? 'aria-busy="true"' : ''; ?>
		data-component="button"
		<?php echo $attr_string; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- pre-escaped above. ?>
	>
		<?php if ( $args['icon_before'] ) : ?>
			<span class="sr-btn__icon sr-btn__icon--before" aria-hidden="true">
				<?php echo wp_kses( $args['icon_before'], skyyrose_svg_kses_allowed() ); ?>
			</span>
		<?php endif; ?>

		<?php if ( $label ) : ?>
			<span class="sr-btn__label"><?php echo esc_html( $label ); ?></span>
		<?php endif; ?>

		<?php if ( $args['icon_after'] ) : ?>
			<span class="sr-btn__icon sr-btn__icon--after" aria-hidden="true">
				<?php echo wp_kses( $args['icon_after'], skyyrose_svg_kses_allowed() ); ?>
			</span>
		<?php endif; ?>

		<?php if ( $is_loading ) : ?>
			<span class="sr-btn__loading" aria-hidden="true"></span>
		<?php endif; ?>
	</button>
<?php else : ?>
	<a
		class="<?php echo esc_attr( $classes ); ?>"
		href="<?php echo esc_url( $args['href'] ); ?>"
		<?php echo $is_disabled ? 'aria-disabled="true" tabindex="-1"' : ''; ?>
		<?php echo $is_loading ? 'aria-busy="true"' : ''; ?>
		data-component="button"
		<?php echo $attr_string; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- pre-escaped above. ?>
	>
		<?php if ( $args['icon_before'] ) : ?>
			<span class="sr-btn__icon sr-btn__icon--before" aria-hidden="true">
				<?php echo wp_kses( $args['icon_before'], skyyrose_svg_kses_allowed() ); ?>
			</span>
		<?php endif; ?>

		<?php if ( $label ) : ?>
			<span class="sr-btn__label"><?php echo esc_html( $label ); ?></span>
		<?php endif; ?>

		<?php if ( $args['icon_after'] ) : ?>
			<span class="sr-btn__icon sr-btn__icon--after" aria-hidden="true">
				<?php echo wp_kses( $args['icon_after'], skyyrose_svg_kses_allowed() ); ?>
			</span>
		<?php endif; ?>

		<?php if ( $is_loading ) : ?>
			<span class="sr-btn__loading" aria-hidden="true"></span>
		<?php endif; ?>
	</a>
	<?php
endif;
