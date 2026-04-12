<?php
/**
 * About page — Chapter III: The Journey (Timeline).
 *
 * Called via get_template_part( 'template-parts/about/timeline', null, $args ).
 *
 * @param array $args {
 *     @type array $allowed_inline      wp_kses whitelist for em/strong/br.
 *     @type array $timeline_milestones Array of milestone data (year, event, desc).
 * }
 *
 * @package SkyyRose_Flagship
 * @since   6.5.0
 */

defined( 'ABSPATH' ) || exit;

$allowed_inline      = $args['allowed_inline'] ?? array();
$timeline_milestones = $args['timeline_milestones'] ?? array();
?>

<!-- Chapter III — Timeline -->
<section class="abt-chapter abt-timeline" aria-label="<?php esc_attr_e( 'Our Journey', 'skyyrose' ); ?>">
	<span class="abt-chapter__num rv-split-char" aria-hidden="true">03</span>
	<div class="abt-chapter__container">
		<p class="abt-chapter__label rv-blur-down"><?php esc_html_e( 'Chapter III', 'skyyrose' ); ?></p>
		<h2 class="abt-chapter__title rv-clip-up"><?php esc_html_e( 'The Journey', 'skyyrose' ); ?></h2>

		<div class="abt-tl__track" role="list">
			<?php foreach ( $timeline_milestones as $ms ) : ?>
				<div class="abt-tl__node rv" role="listitem">
					<div class="abt-tl__year"><?php echo wp_kses( $ms['year'], $allowed_inline ); ?></div>
					<h3 class="abt-tl__event"><?php echo esc_html( $ms['event'] ); ?></h3>
					<p class="abt-tl__desc"><?php echo wp_kses( $ms['desc'], $allowed_inline ); ?></p>
				</div>
			<?php endforeach; ?>
		</div>
	</div>
</section>
