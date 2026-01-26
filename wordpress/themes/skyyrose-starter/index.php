<?php
/**
 * Main Template File
 *
 * This is the most generic template file in a WordPress theme
 * and one of the two required files for a theme (the other being style.css).
 *
 * @package SkyyRose
 */

defined('ABSPATH') || exit;

get_header();
?>

<section class="page-hero">
    <h1 class="page-title">
        <?php
        if (is_home() && !is_front_page()) {
            single_post_title();
        } elseif (is_archive()) {
            the_archive_title();
        } elseif (is_search()) {
            printf(esc_html__('Search Results for: %s', 'skyyrose'), '<span>' . get_search_query() . '</span>');
        } else {
            esc_html_e('Latest Posts', 'skyyrose');
        }
        ?>
    </h1>
    <?php if (is_archive()) : ?>
        <p class="page-subtitle"><?php the_archive_description(); ?></p>
    <?php endif; ?>
</section>

<section class="content-section">
    <div class="container">
        <?php if (have_posts()) : ?>
            <div class="posts-grid">
                <?php
                while (have_posts()) :
                    the_post();
                    ?>
                    <article id="post-<?php the_ID(); ?>" <?php post_class('post-card'); ?>>
                        <?php if (has_post_thumbnail()) : ?>
                        <a href="<?php the_permalink(); ?>" class="post-image">
                            <?php the_post_thumbnail('skyyrose-blog', ['class' => 'post-img']); ?>
                        </a>
                        <?php endif; ?>

                        <div class="post-content">
                            <div class="post-meta">
                                <?php
                                $categories = get_the_category();
                                if (!empty($categories)) :
                                ?>
                                <span class="post-category"><?php echo esc_html($categories[0]->name); ?></span>
                                <?php endif; ?>
                                <span class="post-date"><?php echo get_the_date(); ?></span>
                            </div>

                            <h2 class="post-title">
                                <a href="<?php the_permalink(); ?>"><?php the_title(); ?></a>
                            </h2>

                            <div class="post-excerpt">
                                <?php the_excerpt(); ?>
                            </div>

                            <a href="<?php the_permalink(); ?>" class="post-link">
                                Read More
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M5 12h14M12 5l7 7-7 7"/>
                                </svg>
                            </a>
                        </div>
                    </article>
                <?php endwhile; ?>
            </div>

            <nav class="posts-navigation">
                <?php
                the_posts_pagination([
                    'prev_text' => '←',
                    'next_text' => '→',
                    'mid_size'  => 2,
                ]);
                ?>
            </nav>

        <?php else : ?>
            <div class="no-posts">
                <h2><?php esc_html_e('Nothing Found', 'skyyrose'); ?></h2>
                <p><?php esc_html_e('It seems we can\'t find what you\'re looking for.', 'skyyrose'); ?></p>
                <?php if (is_search()) : ?>
                    <p><?php esc_html_e('Try searching with different keywords.', 'skyyrose'); ?></p>
                    <?php get_search_form(); ?>
                <?php endif; ?>
            </div>
        <?php endif; ?>
    </div>
</section>

<?php get_footer(); ?>
