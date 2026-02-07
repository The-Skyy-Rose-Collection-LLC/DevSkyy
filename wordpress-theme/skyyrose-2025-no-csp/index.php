<?php
/**
 * The main template file (index.php)
 *
 * This is the most generic template file in a WordPress theme
 * and one of the two required files for a theme (the other being style.css).
 * It is used to display a page when nothing more specific matches a query.
 *
 * @package SkyyRose_2025
 * @version 3.0.0
 */

if (!defined('ABSPATH')) exit;

get_header();
?>

<main class="site-main skyyrose-archive luxury-fallback">
    <div class="container">
        <?php if (have_posts()): ?>

            <!-- Archive Header -->
            <header class="archive-header fade-in">
                <?php if (is_home() && !is_front_page()): ?>
                    <h1 class="archive-title">
                        <?php single_post_title(); ?>
                    </h1>
                <?php elseif (is_search()): ?>
                    <h1 class="archive-title">
                        <?php
                        printf(
                            esc_html__('Search Results for: %s', 'skyyrose'),
                            '<span class="search-query">' . get_search_query() . '</span>'
                        );
                        ?>
                    </h1>
                <?php else: ?>
                    <h1 class="archive-title">
                        <?php esc_html_e('Blog', 'skyyrose'); ?>
                    </h1>
                    <p class="archive-subtitle">
                        <?php esc_html_e('Where Love Meets Luxury', 'skyyrose'); ?>
                    </p>
                <?php endif; ?>
            </header>

            <!-- Posts Grid -->
            <div class="posts-grid luxury-grid">
                <?php while (have_posts()): the_post(); ?>
                    <article id="post-<?php the_ID(); ?>" <?php post_class('post-card fade-in-up'); ?>>
                        <?php if (has_post_thumbnail()): ?>
                            <div class="post-thumbnail">
                                <a href="<?php the_permalink(); ?>">
                                    <?php the_post_thumbnail('skyyrose-medium'); ?>
                                    <div class="post-overlay">
                                        <span class="read-more-icon">→</span>
                                    </div>
                                </a>
                            </div>
                        <?php endif; ?>

                        <div class="post-content">
                            <div class="post-meta">
                                <time datetime="<?php echo esc_attr(get_the_date('c')); ?>" class="post-date">
                                    <?php echo esc_html(get_the_date()); ?>
                                </time>
                            </div>

                            <h2 class="post-title">
                                <a href="<?php the_permalink(); ?>">
                                    <?php the_title(); ?>
                                </a>
                            </h2>

                            <div class="post-excerpt">
                                <?php echo wp_trim_words(get_the_excerpt(), 25, '...'); ?>
                            </div>

                            <a href="<?php the_permalink(); ?>" class="read-more-link">
                                <?php esc_html_e('Read More', 'skyyrose'); ?> →
                            </a>
                        </div>
                    </article>
                <?php endwhile; ?>
            </div>

            <!-- Pagination -->
            <?php the_posts_pagination(array(
                'mid_size' => 2,
                'prev_text' => '← ' . __('Previous', 'skyyrose'),
                'next_text' => __('Next', 'skyyrose') . ' →',
            )); ?>

        <?php else: ?>

            <!-- No Posts Found -->
            <div class="no-results fade-in">
                <h2><?php esc_html_e('Nothing found', 'skyyrose'); ?></h2>
                <p><?php esc_html_e('It seems we can\'t find what you\'re looking for.', 'skyyrose'); ?></p>
                <div class="search-form-wrapper">
                    <?php get_search_form(); ?>
                </div>
            </div>

        <?php endif; ?>
    </div>
</main>

<?php get_footer(); ?>
