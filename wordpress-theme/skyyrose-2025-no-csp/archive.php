<?php
/**
 * The template for displaying archive pages
 *
 * @package SkyyRose_2025
 * @version 3.0.0
 */

if (!defined('ABSPATH')) exit;

get_header();
?>

<main class="site-main skyyrose-archive">
    <div class="container">
        <?php if (have_posts()): ?>

            <header class="archive-header">
                <?php
                the_archive_title('<h1 class="archive-title">', '</h1>');
                the_archive_description('<div class="archive-description">', '</div>');
                ?>
            </header>

            <div class="posts-grid">
                <?php while (have_posts()): the_post(); ?>
                    <?php get_template_part('template-parts/content', get_post_type()); ?>
                <?php endwhile; ?>
            </div>

            <?php the_posts_pagination(); ?>

        <?php else: ?>
            <div class="no-results">
                <h2><?php esc_html_e('Nothing found', 'skyyrose'); ?></h2>
            </div>
        <?php endif; ?>
    </div>
</main>

<?php get_footer(); ?>
