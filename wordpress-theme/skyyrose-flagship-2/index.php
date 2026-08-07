<?php
/**
 * Primary fallback template.
 *
 * @package SkyyRose_Flagship_2
 */

defined( 'ABSPATH' ) || exit;

get_header();
?>
<main id="primary" class="sr2-section sr2-page-shell">
	<header class="sr2-page-hero">
		<p class="sr2-eyebrow"><?php esc_html_e( 'SkyyRose Journal', 'skyyrose-flagship-2' ); ?></p>
		<h1><?php echo esc_html( is_home() ? get_bloginfo( 'name' ) : wp_get_document_title() ); ?></h1>
	</header>
	<div class="sr2-content">
		<?php if ( have_posts() ) : ?>
			<?php while ( have_posts() ) : ?>
				<?php the_post(); ?>
				<article <?php post_class( 'sr2-journal-entry' ); ?>>
					<p class="sr2-eyebrow"><?php echo esc_html( get_the_date() ); ?></p>
					<h2><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2>
					<?php the_excerpt(); ?>
				</article>
			<?php endwhile; ?>
			<?php the_posts_pagination(); ?>
		<?php else : ?>
			<p class="sr2-empty"><?php esc_html_e( 'No stories published yet.', 'skyyrose-flagship-2' ); ?></p>
		<?php endif; ?>
	</div>
</main>
<?php
get_footer();
