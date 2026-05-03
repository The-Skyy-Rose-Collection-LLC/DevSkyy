<?php
/**
 * Component: Info Card
 *
 * A text-first card for stat callouts, feature highlights, and metadata blocks.
 * Supports an optional icon, eyebrow label, headline, body copy, and inline CTA.
 *
 * Usage:
 *   get_template_part( 'template-parts/components/card-info', null, [
 *       'eyebrow'       => 'Free shipping',
 *       'headline'      => 'On all orders over $150',
 *       'body'          => '',             // wp_kses_post
 *       'icon'          => '',             // raw SVG string (kses'd)
 *       'cta_label'     => '',
 *       'cta_href'      => '',
 *       'cta_variant'   => 'text',        // primary | ghost | outline | text
 *       'scheme'        => 'default',     // default | elevated | bordered
 *       'extra_classes' => '',
 *       'attrs'         => [],
 *   ] );
 *
 * @package SkyyRose
 */

defined( 'ABSPATH' ) || exit;

$args = wp_parse_args(
	$args ?? array(),
	array(
		'eyebrow'       => '',
		'headline'      => '',
		'body'          => '',
		'icon'          => '',
		'cta_label'     => '',
		'cta_href'      => '',
		'cta_variant'   => 'text',
		'scheme'        => 'default',
		'extra_classes' => '',
		'attrs'         => array(),
	)
);

if ( empty( $args['headline'] ) && empty( $args['eyebrow'] ) ) {
	return;
}

$allowed_schemes = array( 'default', 'elevated', 'bordered' );
$scheme          = in_array( $args['scheme'], $allowed_schemes, true ) ? $args['scheme'] : 'default';

$card_classes = implode(
	' ',
	array_filter(
		array(
			'sr-card-info',
			'sr-card-info--' . $scheme,
			sanitize_html_class( $args['extra_classes'] ),
		)
	)
);

$allowed_svg = array(
	'svg'      => array(
		'xmlns'       => true,
		'viewbox'     => true,
		'aria-hidden' => true,
		'focusable'   => true,
		'width'       => true,
		'height'      => true,
		'class'       => true,
		'fill'        => true,
		'stroke'      => true,
	),
	'path'     => array(
		'd'               => true,
		'fill'            => true,
		'stroke'          => true,
		'stroke-width'    => true,
		'stroke-linecap'  => true,
		'stroke-linejoin' => true,
	),
	'rect'     => array(
		'x'      => true,
		'y'      => true,
		'width'  => true,
		'height' => true,
		'rx'     => true,
		'fill'   => true,
	),
	'circle'   => array(
		'cx'   => true,
		'cy'   => true,
		'r'    => true,
		'fill' => true,
	),
	'polyline' => array(
		'points'       => true,
		'fill'         => true,
		'stroke'       => true,
		'stroke-width' => true,
	),
	'polygon'  => array(
		'points' => true,
		'fill'   => true,
	),
	'g'        => array(
		'fill'   => true,
		'stroke' => true,
	),
);

// Build extra attributes string.
$attr_string = '';
if ( is_array( $args['attrs'] ) ) {
	foreach ( $args['attrs'] as $attr_name => $attr_value ) {
		$attr_string .= ' ' . esc_attr( $attr_name ) . '="' . esc_attr( $attr_value ) . '"';
	}
}
?>
<div
	class="<?php echo esc_attr( $card_classes ); ?>"
	data-component="card-info"
	<?php echo $attr_string; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- pre-escaped above. ?>
>
	<?php if ( $args['icon'] ) : ?>
		<div class="sr-card-info__icon" aria-hidden="true">
			<?php echo wp_kses( $args['icon'], $allowed_svg ); ?>
		</div>
	<?php endif; ?>

	<div class="sr-card-info__text">

		<?php if ( $args['eyebrow'] ) : ?>
			<p class="sr-card-info__eyebrow"><?php echo esc_html( $args['eyebrow'] ); ?></p>
		<?php endif; ?>

		<?php if ( $args['headline'] ) : ?>
			<h3 class="sr-card-info__headline"><?php echo esc_html( $args['headline'] ); ?></h3>
		<?php endif; ?>

		<?php if ( $args['body'] ) : ?>
			<div class="sr-card-info__body"><?php echo wp_kses_post( $args['body'] ); ?></div>
		<?php endif; ?>

		<?php if ( $args['cta_label'] && $args['cta_href'] ) : ?>
			<div class="sr-card-info__cta">
				<?php
				get_template_part(
					'template-parts/components/button',
					null,
					array(
						'label'   => $args['cta_label'],
						'tag'     => 'a',
						'href'    => $args['cta_href'],
						'variant' => $args['cta_variant'],
						'size'    => 'sm',
					)
				);
				?>
			</div>
		<?php endif; ?>

	</div>
</div>
