<?php
/**
 * Landing Page — Editorial Gallery
 *
 * Renders a CSS-grid image gallery from real per-collection lookbook paths.
 * Each item has optional `span='wide'` to hero-span two columns.
 *
 * Expected $args:
 *   'heading' => string  Section heading (e.g. "The Armor")
 *   'images'  => array   Array of:
 *                          'src'    => string  Full-size image path (relative to SKYYROSE_ASSETS_URI)
 *                          'src_sm' => string  Mobile image path (optional; falls back to src)
 *                          'alt'    => string  Descriptive alt text
 *                          'span'   => string  'wide' = grid-column span 2; '' = standard cell
 *
 * @package SkyyRose
 * @since   6.5.0
 */

defined( 'ABSPATH' ) || exit;

$heading    = $args['heading'] ?? '';
$images     = $args['images'] ?? array();
$assets_uri = defined( 'SKYYROSE_ASSETS_URI' ) ? SKYYROSE_ASSETS_URI : '';

if ( empty( $images ) ) {
	return;
}
?>

<section class="lp-editorial" id="editorial">
	<div class="lp__container">
		<?php if ( $heading ) : ?>
			<div class="lp-editorial__header lp-rv">
				<h2><?php echo esc_html( $heading ); ?></h2>
			</div>
		<?php endif; ?>

		<div class="lp-editorial__grid">
			<?php foreach ( $images as $i => $img ) : ?>
				<?php
				$src    = $assets_uri . ( $img['src'] ?? '' );
				$src_sm = ! empty( $img['src_sm'] ) ? ( $assets_uri . $img['src_sm'] ) : $src;
				$alt    = $img['alt'] ?? '';
				$span   = ( isset( $img['span'] ) && 'wide' === $img['span'] ) ? ' lp-editorial__item--wide' : '';
				$delay  = min( $i + 1, 5 );
				?>
				<div class="lp-editorial__item<?php echo esc_attr( $span ); ?> lp-rv"
					data-delay="<?php echo esc_attr( $delay ); ?>">
					<picture>
						<source media="(max-width: 640px)" srcset="<?php echo esc_url( $src_sm ); ?>">
						<img src="<?php echo esc_url( $src ); ?>"
							alt="<?php echo esc_attr( $alt ); ?>"
							loading="lazy"
							decoding="async"
							width="960"
							height="1200">
					</picture>
				</div>
			<?php endforeach; ?>
		</div>
	</div>
</section>
