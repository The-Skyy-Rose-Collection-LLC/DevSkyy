<?php
/**
 * Template Part: Story Section (Homepage V2)
 *
 * @package SkyyRose_Flagship
 * @since   4.1.0
 *
 * @param array $args {
 *     @type string $assets_uri      Theme assets URI.
 *     @type int    $total_products  Total product count.
 * }
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$assets_uri     = $args['assets_uri'] ?? '';
$total_products = $args['total_products'] ?? 0;
?>
<!-- ═══ STORY ═══ -->
<section class="story" id="story" aria-label="<?php esc_attr_e( 'Our Story', 'skyyrose-flagship' ); ?>">
	<div class="story-bg" aria-hidden="true"></div>
	<div class="story-inner">
		<div>
			<p class="story-eyebrow rv"><?php esc_html_e( 'The Origin', 'skyyrose-flagship' ); ?></p>
			<h2 class="story-heading rv rv-d1">
				<?php echo esc_html( 'Born In' ); ?><br><?php echo esc_html( 'The Town' ); ?>
				<em><?php echo esc_html( 'A father\'s promise. A daughter\'s name.' ); ?></em>
			</h2>
			<div class="story-body rv rv-d2">
				<p><?php echo wp_kses_post( 'In a neighborhood where opportunities are as scarce as support, <strong>Corey Foster</strong> refused to become another statistic. He&rsquo;d lost everything &mdash; broke, no drive left, a baby on the way.' ); ?></p>
				<p><?php echo wp_kses_post( 'Through failed websites, scammer manufacturers, and single parenthood with no support &mdash; he built something real. Named after his daughter <strong>Skyy Rose</strong>. Designed for anyone, regardless of gender or age.' ); ?></p>
				<p><?php echo wp_kses_post( 'SkyyRose isn&rsquo;t just clothing. It&rsquo;s proof that your circumstances don&rsquo;t define your destination.' ); ?></p>
			</div>
			<div class="story-stats rv rv-d3">
				<div>
					<div class="stat-num">3</div>
					<div class="stat-label"><?php esc_html_e( 'Collections', 'skyyrose-flagship' ); ?></div>
				</div>
				<div>
					<div class="stat-num"><?php echo esc_html( $total_products ); ?></div>
					<div class="stat-label"><?php esc_html_e( 'Pieces', 'skyyrose-flagship' ); ?></div>
				</div>
				<div>
					<div class="stat-num">2020</div>
					<div class="stat-label"><?php esc_html_e( 'Founded', 'skyyrose-flagship' ); ?></div>
				</div>
				<div>
					<div class="stat-num">5+</div>
					<div class="stat-label"><?php esc_html_e( 'Press Features', 'skyyrose-flagship' ); ?></div>
				</div>
			</div>
		</div>
		<div class="story-img-wrap rv-right">
			<div class="story-img">
				<img
					src="<?php echo esc_url( $assets_uri . '/images/homepage-story-founder.webp' ); ?>"
					alt="<?php esc_attr_e( 'Corey Foster, SkyyRose founder', 'skyyrose-flagship' ); ?>"
					loading="lazy"
					decoding="async"
					width="600"
					height="800"
				/>
			</div>
			<div class="story-float">
				<div class="sf-lbl"><?php esc_html_e( 'Recognition', 'skyyrose-flagship' ); ?></div>
				<div class="sf-val"><?php echo wp_kses_post( 'Best Bay Area<br>Clothing Line 2024' ); ?></div>
			</div>
		</div>
	</div>
</section>
