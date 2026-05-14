<?php
/**
 * About page — Chapter III: The Journey (Timeline).
 *
 * Editorial vertical-rule timeline. Each milestone is a row with the year as a
 * massive Bebas tag on the left of a center vertical rule and event/description
 * on the right (alternates left/right at md+).
 *
 * Called via get_template_part( 'template-parts/about/timeline', null, $args ).
 *
 * @param array $args {
 *     @type array $allowed_inline      wp_kses whitelist for em/strong/br.
 *     @type array $timeline_milestones Array of milestone data (year, event, desc).
 * }
 *
 * @package SkyyRose
 * @since   1.3.0
 */

defined( 'ABSPATH' ) || exit;

$allowed_inline      = $args['allowed_inline'] ?? array();
$timeline_milestones = $args['timeline_milestones'] ?? array();
?>

<!-- Chapter III — Timeline -->
<section class="abt-chapter abt-chapter--timeline" id="journey" aria-label="<?php esc_attr_e( 'Our Journey', 'skyyrose' ); ?>">
	<div class="abt-chapter__container">
		<div class="abt-chapter__head rv">
			<span class="abt-chapter__num" aria-hidden="true"><?php esc_html_e( 'CH. 03', 'skyyrose' ); ?></span>
			<span class="abt-chapter__rule" aria-hidden="true"></span>
			<span class="abt-chapter__label"><?php esc_html_e( 'The Journey', 'skyyrose' ); ?></span>
		</div>
		<h2 class="abt-chapter__title rv rv-d1">
			<?php esc_html_e( 'Drop Calendar', 'skyyrose' ); ?>
		</h2>
	</div>

	<ol class="abt-tl" role="list">
		<?php foreach ( $timeline_milestones as $i => $ms ) : ?>
			<li class="abt-tl__row rv <?php echo ( $i % 2 ) ? 'abt-tl__row--right' : 'abt-tl__row--left'; ?>">
				<div class="abt-tl__year" aria-hidden="true">
					<?php echo wp_kses( $ms['year'], $allowed_inline ); ?>
				</div>
				<div class="abt-tl__body">
					<span class="abt-tl__year-sr" aria-label="Year"><?php echo esc_html( $ms['year'] ); ?></span>
					<h3 class="abt-tl__event"><?php echo esc_html( $ms['event'] ); ?></h3>
					<p class="abt-tl__desc"><?php echo wp_kses( $ms['desc'], $allowed_inline ); ?></p>
				</div>
			</li>
		<?php endforeach; ?>
	</ol>
</section>
