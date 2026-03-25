<?php
/**
 * The main template file
 *
 * @package SkyyRose
 */

get_header();
?>

<main id="main-content" class="site-main" role="main">
    <div class="container">
        <?php if (have_posts()) : ?>
            <div class="posts-grid">
                <?php while (have_posts()) : the_post(); ?>
                    <article <?php post_class('post-card glass-card'); ?>>
                        <?php if (has_post_thumbnail()) : ?>
                            <div class="post-thumbnail">
                                <a href="<?php the_permalink(); ?>">
                                    <?php the_post_thumbnail('skyyrose-blog'); ?>
                                </a>
                            </div>
                        <?php endif; ?>

                        <div class="post-content">
                            <header class="post-header">
                                <h2 class="post-title">
                                    <a href="<?php the_permalink(); ?>">
                                        <?php the_title(); ?>
                                    </a>
                                </h2>
                                <div class="post-meta">
                                    <time datetime="<?php echo get_the_date('c'); ?>">
                                        <?php echo get_the_date(); ?>
                                    </time>
                                </div>
                            </header>

                            <div class="post-excerpt">
                                <?php the_excerpt(); ?>
                            </div>

                            <a href="<?php the_permalink(); ?>" class="read-more magnetic-btn">
                                Read More
                                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                                    <path d="M3 8H13M13 8L9 4M13 8L9 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                                </svg>
                            </a>
                        </div>
                    </article>
                <?php endwhile; ?>
            </div>

            <nav class="pagination" aria-label="Posts navigation">
                <?php
                the_posts_pagination([
                    'prev_text' => '&larr; Previous',
                    'next_text' => 'Next &rarr;',
                    'mid_size'  => 2,
                ]);
                ?>
            </nav>
        <?php else : ?>
            <div class="no-posts">
                <h2><?php esc_html_e('Nothing Found', 'skyyrose'); ?></h2>
                <p><?php esc_html_e('It seems we can\'t find what you\'re looking for.', 'skyyrose'); ?></p>
            </div>
        <?php endif; ?>
    </div>
</main>

<?php
get_footer();
