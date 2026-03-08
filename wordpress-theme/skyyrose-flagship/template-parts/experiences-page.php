<?php
/**
 * Template Part: Experiences Hub
 *
 * Renders the full immersive experiences landing page — hero section plus
 * a three-card grid linking to each collection experience.
 *
 * Expected: $experiences_config (array) — set by template-experiences.php.
 *
 * @package SkyyRose_Flagship
 * @since   4.1.0
 */

defined( 'ABSPATH' ) || exit;

if ( empty( $experiences_config ) || ! is_array( $experiences_config ) ) {
	return;
}

$cfg = wp_parse_args(
	$experiences_config,
	array(
		'page_title'  => __( 'Immersive Experiences', 'skyyrose-flagship' ),
		'tagline'     => __( 'Luxury Grows from Concrete.', 'skyyrose-flagship' ),
		'experiences' => array(),
	)
);

get_header();
?>

<main class="experiences-page" id="main-content">

	<!-- ═══════════════════════════════════════ HERO ═══════ -->
	<section class="experiences-hero" aria-labelledby="experiences-hero-heading">
		<div class="experiences-hero__inner">

			<div class="experiences-hero__eyebrow">
				<span class="experiences-hero__rule" aria-hidden="true"></span>
				<span class="experiences-hero__label"><?php esc_html_e( 'Collection Experiences', 'skyyrose-flagship' ); ?></span>
				<span class="experiences-hero__rule" aria-hidden="true"></span>
			</div>

			<h1 id="experiences-hero-heading" class="experiences-hero__title">
				<?php echo esc_html( $cfg['page_title'] ); ?>
			</h1>

			<p class="experiences-hero__tagline">
				<?php echo esc_html( $cfg['tagline'] ); ?>
			</p>

		</div>
	</section><!-- /.experiences-hero -->

	<!-- ══════════════════════════════════════ GRID ════════ -->
	<?php if ( ! empty( $cfg['experiences'] ) ) : ?>
	<section class="experiences-grid-section" aria-label="<?php esc_attr_e( 'Collection Experiences', 'skyyrose-flagship' ); ?>">
		<div class="experiences-grid">

			<?php
			$card_index = 0;
			foreach ( $cfg['experiences'] as $exp ) :
				$exp = wp_parse_args(
					$exp,
					array(
						'slug'        => '',
						'name'        => '',
						'number'      => '0' . ( $card_index + 1 ),
						'accent'      => '#B76E79',
						'accent_rgb'  => '183, 110, 121',
						'description' => '',
						'hero_image'  => '',
						'scene_2'     => '',
						'url'         => home_url( '/' ),
					)
				);

				$card_style = sprintf(
					'--experience-accent: %s; --experience-accent-rgb: %s;',
					esc_attr( $exp['accent'] ),
					esc_attr( $exp['accent_rgb'] )
				);
				?>

			<article
				class="experience-card experience-card--<?php echo esc_attr( $exp['slug'] ); ?>"
				style="<?php echo $card_style; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- sanitized above ?>"
				data-experience="<?php echo esc_attr( $exp['slug'] ); ?>"
			>

				<!-- Background scene imagery -->
				<div class="experience-card__scene" aria-hidden="true">
					<?php if ( ! empty( $exp['hero_image'] ) ) : ?>
					<img
						class="experience-card__scene-img experience-card__scene-img--primary"
						src="<?php echo esc_url( $exp['hero_image'] ); ?>"
						alt=""
						loading="lazy"
						decoding="async"
					/>
					<?php endif; ?>
					<?php if ( ! empty( $exp['scene_2'] ) ) : ?>
					<img
						class="experience-card__scene-img experience-card__scene-img--secondary"
						src="<?php echo esc_url( $exp['scene_2'] ); ?>"
						alt=""
						loading="lazy"
						decoding="async"
					/>
					<?php endif; ?>
					<div class="experience-card__scene-overlay"></div>
				</div>

				<!-- Card body -->
				<div class="experience-card__body">

					<span class="experience-card__number" aria-hidden="true">
						<?php echo esc_html( $exp['number'] ); ?>
					</span>

					<h2 class="experience-card__name">
						<?php echo esc_html( $exp['name'] ); ?>
					</h2>

					<?php if ( ! empty( $exp['description'] ) ) : ?>
					<p class="experience-card__description">
						<?php echo esc_html( $exp['description'] ); ?>
					</p>
					<?php endif; ?>

					<a
						class="experience-card__cta"
						href="<?php echo esc_url( $exp['url'] ); ?>"
						aria-label="<?php
							/* translators: %s: collection name */
							printf( esc_attr__( 'Enter the %s experience', 'skyyrose-flagship' ), esc_attr( $exp['name'] ) );
						?>"
					>
						<span class="experience-card__cta-text"><?php esc_html_e( 'Enter Experience', 'skyyrose-flagship' ); ?></span>
						<span class="experience-card__cta-arrow" aria-hidden="true">→</span>
					</a>

				</div><!-- /.experience-card__body -->

			</article><!-- /.experience-card -->

			<?php
				$card_index++;
			endforeach;
			?>

		</div><!-- /.experiences-grid -->
	</section><!-- /.experiences-grid-section -->
	<?php endif; ?>

</main><!-- /.experiences-page -->

<?php get_footer(); ?>
