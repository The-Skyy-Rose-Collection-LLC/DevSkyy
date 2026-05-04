<?php
/**
 * Component: Figure
 *
 * Renders a <figure> with <img> (or <picture>) and optional <figcaption>.
 * Decorative images get alt="" + HTML comment; meaningful images require alt.
 *
 * Usage:
 *   get_template_part( 'template-parts/components/figure', null, [
 *       'src'          => get_template_directory_uri() . '/assets/images/hero.jpg',
 *       'alt'          => 'Black Rose collection hero shot',  // '' = decorative
 *       'width'        => 1200,
 *       'height'       => 800,
 *       'caption'      => '',
 *       'loading'      => 'lazy',    // lazy | eager
 *       'decoding'     => 'async',   // async | sync | auto
 *       'sizes'        => '',        // srcset sizes attribute
 *       'srcset'       => '',        // srcset attribute
 *       'aspect_ratio' => '',        // e.g. '16/9' — sets aspect-ratio on wrapper
 *       'object_fit'   => 'cover',   // cover | contain | fill
 *       'rounded'      => false,     // applies sr-figure--rounded
 *       'extra_classes'=> '',
 *       'attrs'        => [],        // extra attrs on <figure>
 *       'img_attrs'    => [],        // extra attrs on <img>
 *   ] );
 *
 * @package SkyyRose
 */

defined( 'ABSPATH' ) || exit;

$args = wp_parse_args(
	$args ?? array(),
	array(
		'src'           => '',
		'alt'           => null,   // null = flag as missing; '' = decorative
		'width'         => 0,
		'height'        => 0,
		'caption'       => '',
		'loading'       => 'lazy',
		'decoding'      => 'async',
		'sizes'         => '',
		'srcset'        => '',
		'aspect_ratio'  => '',
		'object_fit'    => 'cover',
		'rounded'       => false,
		'extra_classes' => '',
		'attrs'         => array(),
		'img_attrs'     => array(),
	)
);

if ( empty( $args['src'] ) ) {
	return;
}

$is_decorative = '' === $args['alt'];
$alt_missing   = null === $args['alt'];
$alt_text      = $alt_missing ? '' : (string) $args['alt'];

$figure_classes = implode(
	' ',
	array_filter(
		array(
			'sr-figure',
			$args['rounded'] ? 'sr-figure--rounded' : '',
			$args['aspect_ratio'] ? 'sr-figure--aspect' : '',
			skyyrose_sanitize_class_list( $args['extra_classes'] ?? '' ),
		)
	)
);

// Build <figure> attribute string.
$fig_attr_string = skyyrose_build_attr_string( $args['attrs'] ?? array() );
if ( $args['aspect_ratio'] ) {
	$fig_attr_string .= ' style="aspect-ratio:' . esc_attr( $args['aspect_ratio'] ) . '"';
}

// Build <img> attribute string.
$img_attr_string = skyyrose_build_attr_string( $args['img_attrs'] ?? array() );

$allowed_loading  = array( 'lazy', 'eager' );
$loading          = in_array( $args['loading'], $allowed_loading, true ) ? $args['loading'] : 'lazy';
$allowed_decoding = array( 'async', 'sync', 'auto' );
$decoding         = in_array( $args['decoding'], $allowed_decoding, true ) ? $args['decoding'] : 'async';
$allowed_fit      = array( 'cover', 'contain', 'fill', 'none', 'scale-down' );
$object_fit       = in_array( $args['object_fit'], $allowed_fit, true ) ? $args['object_fit'] : 'cover';
?>
<figure
	class="<?php echo esc_attr( $figure_classes ); ?>"
	data-component="figure"
	<?php echo $fig_attr_string; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- pre-escaped above. ?>
>
	<?php if ( $alt_missing ) : ?>
		<!-- sr-figure: alt text missing — add meaningful alt or pass alt='' for decorative images -->
	<?php endif; ?>

	<img
		class="sr-figure__img sr-figure__img--<?php echo esc_attr( $object_fit ); ?>"
		src="<?php echo esc_url( $args['src'] ); ?>"
		alt="<?php echo esc_attr( $alt_text ); ?>"
		<?php echo $args['width'] ? 'width="' . absint( $args['width'] ) . '"' : ''; ?>
		<?php echo $args['height'] ? 'height="' . absint( $args['height'] ) . '"' : ''; ?>
		loading="<?php echo esc_attr( $loading ); ?>"
		decoding="<?php echo esc_attr( $decoding ); ?>"
		<?php echo $args['srcset'] ? 'srcset="' . esc_attr( $args['srcset'] ) . '"' : ''; ?>
		<?php echo $args['sizes'] ? 'sizes="' . esc_attr( $args['sizes'] ) . '"' : ''; ?>
		<?php echo $is_decorative ? 'role="presentation"' : ''; ?>
		<?php echo $img_attr_string; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- pre-escaped above. ?>
	/>

	<?php if ( $args['caption'] ) : ?>
		<figcaption class="sr-figure__caption"><?php echo esc_html( $args['caption'] ); ?></figcaption>
	<?php endif; ?>
</figure>
