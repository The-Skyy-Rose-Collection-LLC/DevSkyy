<?php
/**
 * Template Part: Lookbook Gallery (Homepage V2)
 *
 * @package SkyyRose_Flagship
 * @since   4.1.0
 *
 * @param array $args {
 *     @type string $assets_uri  Theme assets URI.
 * }
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$assets_uri = $args['assets_uri'] ?? '';
?>
<!-- ═══ LOOKBOOK ═══ -->
<section class="lookbook" id="lookbook" aria-label="<?php esc_attr_e( 'Lookbook', 'skyyrose-flagship' ); ?>">
	<div class="lookbook-header rv">
		<h2><?php echo esc_html( 'Lookbook' ); ?></h2>
		<p><?php echo esc_html( 'Real people. Real style. Oakland made.' ); ?></p>
	</div>
	<div class="lookbook-grid">
		<?php
		$lookbook_images = array(
			array(
				'src'   => 'lookbook/lb-love-hurts-varsity-480w.webp',
				'src2x' => 'lookbook/lb-love-hurts-varsity-960w.webp',
				'alt'   => 'Love Hurts varsity jacket',
				'label' => 'Love Hurts',
				'class' => 'tall',
			),
			array(
				'src'   => 'lookbook/lb-black-rose-hockey-480w.webp',
				'src2x' => 'lookbook/lb-black-rose-hockey-960w.webp',
				'alt'   => 'Black Rose hockey jersey',
				'label' => 'Black Rose',
				'class' => '',
			),
			array(
				'src'   => 'lookbook/lb-kid-black-rose-480w.webp',
				'src2x' => 'lookbook/lb-kid-black-rose-960w.webp',
				'alt'   => 'Kid in Black Rose hoodie',
				'label' => 'Street Style',
				'class' => '',
			),
			array(
				'src'   => 'lookbook/lb-rose-hoodie-beanie-480w.webp',
				'src2x' => 'lookbook/lb-rose-hoodie-beanie-960w.webp',
				'alt'   => 'Rose hoodie and beanie',
				'label' => 'Signature',
				'class' => '',
			),
			array(
				'src'   => 'lookbook/lb-black-rose-football-480w.webp',
				'src2x' => 'lookbook/lb-black-rose-football-960w.webp',
				'alt'   => 'Black Rose football jersey',
				'label' => 'Limited Edition',
				'class' => '',
			),
		);

		foreach ( $lookbook_images as $lb_img ) :
			$img_1x    = $assets_uri . '/images/' . $lb_img['src'];
			$img_2x    = $assets_uri . '/images/' . $lb_img['src2x'];
			$css_class = 'lb-img rv' . ( $lb_img['class'] ? ' ' . $lb_img['class'] : '' );
			?>
			<div class="<?php echo esc_attr( $css_class ); ?>">
				<img
					src="<?php echo esc_url( $img_1x ); ?>"
					srcset="<?php echo esc_url( $img_1x ); ?> 480w, <?php echo esc_url( $img_2x ); ?> 960w"
					sizes="(max-width: 768px) 100vw, 480px"
					alt="<?php echo esc_attr( $lb_img['alt'] ); ?>"
					loading="lazy"
					decoding="async"
					width="480"
					height="640"
				/>
				<span class="lb-label"><?php echo esc_html( $lb_img['label'] ); ?></span>
			</div>
		<?php endforeach; ?>
	</div>
</section>
