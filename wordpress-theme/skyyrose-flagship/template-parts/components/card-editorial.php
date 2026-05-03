<?php
/**
 * Component: Editorial Card
 *
 * A full-bleed image card with headline, subheading, body copy, and CTA.
 * Suitable for campaign moments, collection hero teasers, and lookbook entries.
 *
 * Usage:
 *   get_template_part( 'template-parts/components/card-editorial', null, [
 *       'image_src'     => get_template_directory_uri() . '/assets/images/campaign.jpg',
 *       'image_alt'     => 'Black Rose FW26 campaign',
 *       'image_width'   => 800,
 *       'image_height'  => 1000,
 *       'kicker'        => 'Black Rose',    // small text above headline
 *       'headline'      => 'Luxury Grows from Concrete.',
 *       'body'          => '',              // short paragraph; wp_kses_post
 *       'cta_label'     => 'Explore',
 *       'cta_href'      => '',
 *       'overlay'       => true,            // dark gradient overlay on image
 *       'align_content' => 'bottom',        // top | center | bottom
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
		'image_src'     => '',
		'image_alt'     => '',
		'image_width'   => 0,
		'image_height'  => 0,
		'kicker'        => '',
		'headline'      => '',
		'body'          => '',
		'cta_label'     => '',
		'cta_href'      => '',
		'overlay'       => true,
		'align_content' => 'bottom',
		'extra_classes' => '',
		'attrs'         => array(),
	)
);

if ( empty( $args['headline'] ) && empty( $args['image_src'] ) ) {
	return;
}

$allowed_align = array( 'top', 'center', 'bottom' );
$align         = in_array( $args['align_content'], $allowed_align, true ) ? $args['align_content'] : 'bottom';

$card_classes = implode(
	' ',
	array_filter(
		array(
			'sr-card-editorial',
			'sr-card-editorial--align-' . $align,
			$args['overlay'] ? 'sr-card-editorial--overlay' : '',
			sanitize_html_class( $args['extra_classes'] ),
		)
	)
);

// Build extra attributes string.
$attr_string = '';
if ( is_array( $args['attrs'] ) ) {
	foreach ( $args['attrs'] as $attr_name => $attr_value ) {
		$attr_string .= ' ' . esc_attr( $attr_name ) . '="' . esc_attr( $attr_value ) . '"';
	}
}
?>
<article
	class="<?php echo esc_attr( $card_classes ); ?>"
	data-component="card-editorial"
	<?php echo $attr_string; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- pre-escaped above. ?>
>
	<?php if ( $args['image_src'] ) : ?>
		<div class="sr-card-editorial__media" aria-hidden="true">
			<?php
			get_template_part(
				'template-parts/components/figure',
				null,
				array(
					'src'        => $args['image_src'],
					'alt'        => '',  // decorative — content conveyed by headline/body
					'width'      => $args['image_width'],
					'height'     => $args['image_height'],
					'object_fit' => 'cover',
					'loading'    => 'lazy',
				)
			);
			?>
		</div>
	<?php endif; ?>

	<div class="sr-card-editorial__content">

		<?php if ( $args['kicker'] ) : ?>
			<p class="sr-card-editorial__kicker"><?php echo esc_html( $args['kicker'] ); ?></p>
		<?php endif; ?>

		<?php if ( $args['headline'] ) : ?>
			<h2 class="sr-card-editorial__headline"><?php echo esc_html( $args['headline'] ); ?></h2>
		<?php endif; ?>

		<?php if ( $args['body'] ) : ?>
			<div class="sr-card-editorial__body"><?php echo wp_kses_post( $args['body'] ); ?></div>
		<?php endif; ?>

		<?php if ( $args['cta_label'] && $args['cta_href'] ) : ?>
			<div class="sr-card-editorial__cta">
				<?php
				get_template_part(
					'template-parts/components/button',
					null,
					array(
						'label'   => $args['cta_label'],
						'tag'     => 'a',
						'href'    => $args['cta_href'],
						'variant' => 'ghost',
						'size'    => 'md',
					)
				);
				?>
			</div>
		<?php endif; ?>

	</div>
</article>
