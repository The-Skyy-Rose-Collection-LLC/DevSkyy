<?php
/**
 * About page — Chapter II: The Collections grid.
 *
 * Called via get_template_part( 'template-parts/about/collections-grid', null, $args ).
 *
 * @param array $args {
 *     @type array $allowed_inline wp_kses whitelist for em/strong/br.
 *     @type array $collections    Array of collection card data (icon, title, text).
 * }
 *
 * @package SkyyRose_Flagship
 * @since   6.5.0
 */

defined( 'ABSPATH' ) || exit;

$allowed_inline = $args['allowed_inline'] ?? array();
$collections    = $args['collections'] ?? array();
$svg_kses       = skyyrose_svg_kses();
?>

<!-- Chapter II — The Collections -->
<section class="abt-chapter abt-values" aria-label="<?php esc_attr_e( 'The Collections', 'skyyrose' ); ?>">
	<span class="abt-chapter__num rv-split-char" aria-hidden="true">02</span>
	<div class="abt-chapter__container">
		<p class="abt-chapter__label rv-blur-down"><?php esc_html_e( 'Chapter II', 'skyyrose' ); ?></p>
		<h2 class="abt-chapter__title rv-clip-up">
			<?php echo wp_kses( __( 'Three Worlds,<br>One Crown', 'skyyrose' ), $allowed_inline ); ?>
		</h2>

		<div class="abt-values__grid">
			<?php
			foreach ( $collections as $ci => $col ) :
				$delay = 'rv-d' . ( ( $ci % 3 ) + 1 );
				?>
				<div class="abt-val-card rv <?php echo esc_attr( $delay ); ?>">
					<div class="abt-val-card__icon" aria-hidden="true">
						<?php echo wp_kses( $col['icon'], $svg_kses ); ?>
					</div>
					<h3 class="abt-val-card__title"><?php echo esc_html( $col['title'] ); ?></h3>
					<p class="abt-val-card__text"><?php echo wp_kses( $col['text'], $allowed_inline ); ?></p>
				</div>
			<?php endforeach; ?>
		</div>
	</div>
</section>

<!-- Photo Divider 2 -->
<?php
$story2_img = get_theme_file_path( 'assets/images/about-story-2.jpg' );
if ( file_exists( $story2_img ) ) :
	?>
	<div class="abt-divider rv" aria-hidden="true">
		<img src="<?php echo esc_url( get_theme_file_uri( 'assets/images/about-story-2.jpg' ) ); ?>"
			alt="" loading="lazy" width="1920" height="600">
		<div class="abt-divider__overlay"></div>
	</div>
<?php endif; ?>
