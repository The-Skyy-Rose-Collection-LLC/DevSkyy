<?php
/**
 * Component: Quote / Blockquote
 *
 * Renders a <blockquote> with optional attribution line.
 * Use for brand statements, founder words, press pull-quotes, and testimonials.
 *
 * Usage:
 *   get_template_part( 'template-parts/components/quote', null, [
 *       'text'          => 'Luxury Grows from Concrete.',
 *       'cite'          => 'Corey Foster, Founder',
 *       'cite_url'      => '',             // wraps cite in <a> if provided
 *       'size'          => 'md',           // sm | md | lg | display
 *       'align'         => 'left',         // left | center | right
 *       'decorative'    => true,           // adds decorative quotation mark glyph
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
		'text'          => '',
		'cite'          => '',
		'cite_url'      => '',
		'size'          => 'md',
		'align'         => 'left',
		'decorative'    => true,
		'extra_classes' => '',
		'attrs'         => array(),
	)
);

if ( empty( $args['text'] ) ) {
	return;
}

$allowed_sizes  = array( 'sm', 'md', 'lg', 'display' );
$allowed_aligns = array( 'left', 'center', 'right' );

$size  = in_array( $args['size'], $allowed_sizes, true ) ? $args['size'] : 'md';
$align = in_array( $args['align'], $allowed_aligns, true ) ? $args['align'] : 'left';

$quote_classes = implode(
	' ',
	array_filter(
		array(
			'sr-quote',
			'sr-quote--' . $size,
			'sr-quote--' . $align,
			$args['decorative'] ? 'sr-quote--decorative' : '',
			skyyrose_sanitize_class_list( $args['extra_classes'] ?? '' ),
		)
	)
);

// Build extra attributes string.
$attr_string = skyyrose_build_attr_string( $args['attrs'] ?? array() );
?>
<blockquote
	class="<?php echo esc_attr( $quote_classes ); ?>"
	data-component="quote"
	<?php echo $args['cite_url'] ? 'cite="' . esc_url( $args['cite_url'] ) . '"' : ''; ?>
	<?php echo $attr_string; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- pre-escaped above. ?>
>
	<p class="sr-quote__text"><?php echo wp_kses_post( $args['text'] ); ?></p>

	<?php if ( $args['cite'] ) : ?>
		<footer class="sr-quote__footer">
			<cite class="sr-quote__cite">
				<?php if ( $args['cite_url'] ) : ?>
					<a class="sr-quote__cite-link" href="<?php echo esc_url( $args['cite_url'] ); ?>">
						<?php echo esc_html( $args['cite'] ); ?>
					</a>
				<?php else : ?>
					<?php echo esc_html( $args['cite'] ); ?>
				<?php endif; ?>
			</cite>
		</footer>
	<?php endif; ?>
</blockquote>
