<?php
/**
 * Template Name: Policy / Legal
 *
 * Shared editorial shell for merchant-editable privacy, terms, refund,
 * cookie, and accessibility pages.
 *
 * @package SkyyRose
 * @since   2.2.0
 */

defined( 'ABSPATH' ) || exit;

get_header();
?>

<main id="primary" class="info-page policy-page" role="main" tabindex="-1">
	<div class="info-page__container">
		<header class="info-page__hero">
			<span class="info-page__badge"><?php esc_html_e( 'House Standard', 'skyyrose' ); ?></span>
			<h1 class="info-page__title"><?php the_title(); ?></h1>
			<p class="info-page__subtitle"><?php esc_html_e( 'Clear terms. Straight answers. No fine-print theater.', 'skyyrose' ); ?></p>
		</header>

		<article class="policy-page__content">
			<?php
			while ( have_posts() ) :
				the_post();
				the_content();
			endwhile;
			?>
		</article>

		<section class="info-page__cta">
			<h2><?php esc_html_e( 'Need Clarification?', 'skyyrose' ); ?></h2>
			<p><?php esc_html_e( 'Send the page and question. Our team will respond directly.', 'skyyrose' ); ?></p>
			<a href="mailto:support@skyyrose.co" class="info-page__cta-btn btn-sweep btn-press"><?php esc_html_e( 'Email Support', 'skyyrose' ); ?></a>
		</section>
	</div>
</main>

<?php get_footer(); ?>
