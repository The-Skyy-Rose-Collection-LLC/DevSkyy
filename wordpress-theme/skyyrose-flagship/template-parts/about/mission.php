<?php
/**
 * About page — Mission Banner.
 *
 * Called via get_template_part( 'template-parts/about/mission', null, $args ).
 *
 * @param array $args {
 *     @type array $allowed_inline wp_kses whitelist for em/strong/br.
 * }
 *
 * @package SkyyRose_Flagship
 * @since   6.5.0
 */

defined( 'ABSPATH' ) || exit;

$allowed_inline = $args['allowed_inline'] ?? array();
?>

<!-- Mission Banner -->
<section class="abt-mission" aria-label="<?php esc_attr_e( 'Our Mission', 'skyyrose-flagship' ); ?>">
	<div class="rv">
		<p class="abt-chapter__label" style="text-align:center;margin-bottom:24px">
			<?php esc_html_e( 'The Mission', 'skyyrose-flagship' ); ?>
		</p>
		<h2 class="abt-mission__tagline">
			<?php echo wp_kses( __( 'Luxury Grows<br>from Concrete.', 'skyyrose-flagship' ), $allowed_inline ); ?>
		</h2>
		<p class="abt-mission__sub">
			<?php esc_html_e( 'Luxury grows from concrete. Oakland roots, family-driven, fashion as self-expression. Three collections, one bloodline, one crown. This is SkyyRose.', 'skyyrose-flagship' ); ?>
		</p>
		<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>" class="abt-mission__cta">
			<?php esc_html_e( 'Shop the Collection', 'skyyrose-flagship' ); ?>
		</a>
	</div>
</section>
