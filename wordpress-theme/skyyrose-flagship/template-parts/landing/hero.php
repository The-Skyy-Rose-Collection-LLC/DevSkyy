<?php
/**
 * Landing Page — Hero Section
 *
 * Displays branded logo overlay, countdown timer, badge, subtitle, and CTAs.
 * Uses hero overlay PNGs as primary visual (NOT CSS-rendered text).
 *
 * Expected $args:
 *   'collection'   => string  Collection slug (black-rose, love-hurts, signature)
 *   'badge_text'   => string  Badge text above logo ("Limited Edition — 200 Pieces Per Style")
 *   'logo_image'   => string  Path to hero overlay PNG (relative to assets URI)
 *   'logo_alt'     => string  Alt text for logo image
 *   'subtitle'     => string  Tagline/subtitle below countdown
 *   'countdown'    => string  Countdown config: "72h" or ISO date string
 *   'cta_primary'  => array   ['text' => 'Shop', 'url' => '#products']
 *   'cta_secondary' => array  ['text' => 'Story', 'url' => '#story']  (optional)
 *   'bg_image'     => string  Hero background image URL (optional)
 *
 * @package SkyyRose
 * @since   6.5.0
 */

defined( 'ABSPATH' ) || exit;

$collection    = $args['collection'] ?? 'black-rose';
$badge_text    = $args['badge_text'] ?? '';
$logo_image    = $args['logo_image'] ?? '';
$logo_alt      = $args['logo_alt'] ?? esc_attr( ucwords( str_replace( '-', ' ', $collection ) ) );
$subtitle      = $args['subtitle'] ?? '';
$countdown     = $args['countdown'] ?? '72h';
$cta_primary   = $args['cta_primary'] ?? array();
$cta_secondary = $args['cta_secondary'] ?? array();
$bg_image      = $args['bg_image'] ?? '';
$assets_uri    = defined( 'SKYYROSE_ASSETS_URI' ) ? SKYYROSE_ASSETS_URI : '';
?>

<section class="lp-hero" id="hero" aria-label="<?php echo esc_attr( $logo_alt ); ?> Hero">
	<?php if ( $bg_image ) : ?>
		<div class="lp-hero__bg">
			<?php
			echo skyyrose_render_picture( // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- helper escapes internally.
				$bg_image,
				'',
				array(
					'loading'       => 'eager',
					'fetchpriority' => 'high',
					'width'         => '1920',
					'height'        => '1080',
					'decoding'      => 'async',
				)
			);
			?>
		</div>
	<?php endif; ?>

	<div class="lp-hero__content">
		<?php if ( $badge_text ) : ?>
			<span class="lp-hero__badge"><?php echo esc_html( $badge_text ); ?></span>
		<?php endif; ?>

		<?php if ( $logo_image ) : ?>
			<img class="lp-hero__logo"
				src="<?php echo esc_url( $assets_uri . $logo_image ); ?>"
				alt="<?php echo esc_attr( $logo_alt ); ?>"
				loading="eager"
				fetchpriority="high"
				decoding="async"
				width="600"
				height="300">
		<?php endif; ?>

		<?php if ( $countdown ) : ?>
			<div class="lp-hero__countdown lp-countdown" data-countdown="<?php echo esc_attr( $countdown ); ?>">
				<div class="lp-countdown__unit">
					<span class="lp-countdown__num" data-cd="d">00</span>
					<span class="lp-countdown__label">Days</span>
				</div>
				<span class="lp-countdown__sep" aria-hidden="true">:</span>
				<div class="lp-countdown__unit">
					<span class="lp-countdown__num" data-cd="h">00</span>
					<span class="lp-countdown__label">Hours</span>
				</div>
				<span class="lp-countdown__sep" aria-hidden="true">:</span>
				<div class="lp-countdown__unit">
					<span class="lp-countdown__num" data-cd="m">00</span>
					<span class="lp-countdown__label">Min</span>
				</div>
				<span class="lp-countdown__sep" aria-hidden="true">:</span>
				<div class="lp-countdown__unit">
					<span class="lp-countdown__num" data-cd="s">00</span>
					<span class="lp-countdown__label">Sec</span>
				</div>
			</div>
		<?php endif; ?>

		<?php if ( $subtitle ) : ?>
			<p class="lp-hero__subtitle"><?php echo esc_html( $subtitle ); ?></p>
		<?php endif; ?>

		<?php if ( ! empty( $cta_primary ) || ! empty( $cta_secondary ) ) : ?>
			<div class="lp-hero__ctas">
				<?php if ( ! empty( $cta_primary['text'] ) ) : ?>
					<a href="<?php echo esc_url( $cta_primary['url'] ?? '#products' ); ?>"
						class="lp-btn lp-btn--primary">
						<?php echo esc_html( $cta_primary['text'] ); ?>
					</a>
				<?php endif; ?>
				<?php if ( ! empty( $cta_secondary['text'] ) ) : ?>
					<a href="<?php echo esc_url( $cta_secondary['url'] ?? '#story' ); ?>"
						class="lp-btn lp-btn--secondary">
						<?php echo esc_html( $cta_secondary['text'] ); ?>
					</a>
				<?php endif; ?>
			</div>
		<?php endif; ?>
	</div>

	<div class="lp-hero__scroll" aria-hidden="true">
		<span>Scroll</span>
		<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
			<polyline points="6 9 12 15 18 9"></polyline>
		</svg>
	</div>
</section>
