<?php
/**
 * Template Name: Info Page
 *
 * Generic legal / informational page template — terms, privacy, accessibility,
 * cookie policy, etc. Uses the same `info-page` chrome as `template-faq.php`
 * and `template-shipping-returns.php`, but renders the post's content
 * (Gutenberg blocks / classic editor) inside the chrome rather than a
 * hand-coded structure.
 *
 * Assign this to:
 *   - Terms of Service
 *   - Privacy Policy
 *   - Accessibility Statement
 *   - Cookie Policy
 *   - Any other long-form legal/info page
 *
 * The hero badge defaults to "Policies" but page authors can override with a
 * `_skyyrose_info_badge` meta field per page (see admin ACF/CMB2 setup or use
 * a simple custom field).
 *
 * @package SkyyRose
 * @since   7.1.0
 */

defined( 'ABSPATH' ) || exit;

get_header();

while ( have_posts() ) :
	the_post();
	$badge = get_post_meta( get_the_ID(), '_skyyrose_info_badge', true );
	if ( ! $badge ) {
		$badge = __( 'Policies', 'skyyrose' );
	}
	$subtitle = get_post_meta( get_the_ID(), '_skyyrose_info_subtitle', true );
	?>

<main id="primary" class="info-page info-page--legal" role="main">
	<div class="info-page__container">

		<header class="info-page__hero rv-clip-up">
			<span class="info-page__badge"><?php echo esc_html( $badge ); ?></span>
			<h1 class="info-page__title"><?php the_title(); ?></h1>
			<?php if ( $subtitle ) : ?>
				<p class="info-page__subtitle"><?php echo esc_html( $subtitle ); ?></p>
			<?php endif; ?>
		</header>

		<article class="info-page__body rv-clip-up" data-delay="1">
			<?php the_content(); ?>
		</article>

		<section class="info-page__cta rv-blur" data-delay="2">
			<h2 class="info-page__cta-title"><?php esc_html_e( 'Questions about this policy?', 'skyyrose' ); ?></h2>
			<p class="info-page__cta-text"><?php esc_html_e( "We're happy to clarify anything that isn't clear.", 'skyyrose' ); ?></p>
			<a href="mailto:support@skyyrose.co" class="info-page__cta-btn btn-sweep btn-press">
				<?php esc_html_e( 'Email Support', 'skyyrose' ); ?>
			</a>
		</section>

	</div>
</main>

	<?php
endwhile;

get_footer();
