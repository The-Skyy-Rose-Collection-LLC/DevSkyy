<?php
/**
 * Main template file
 */
get_header();
?>

<main class="site-main">
    <div class="container">
        <?php if (have_posts()): ?>
            <div class="post-grid">
                <?php while (have_posts()): the_post(); ?>
                    <article id="post-<?php the_ID(); ?>" <?php post_class('post-card glass'); ?>>
                        <?php if (has_post_thumbnail()): ?>
                            <div class="post-thumbnail">
                                <a href="<?php the_permalink(); ?>">
                                    <?php the_post_thumbnail('skyyrose-hero'); ?>
                                </a>
                            </div>
                        <?php endif; ?>
                        
                        <div class="post-content">
                            <h2 class="post-title">
                                <a href="<?php the_permalink(); ?>">
                                    <?php the_title(); ?>
                                </a>
                            </h2>
                            
                            <div class="post-meta">
                                <span class="post-date">
                                    <?php echo get_the_date(); ?>
                                </span>
                                <span class="post-author">
                                    by <?php the_author(); ?>
                                </span>
                            </div>
                            
                            <div class="post-excerpt">
                                <?php the_excerpt(); ?>
                            </div>
                            
                            <a href="<?php the_permalink(); ?>" class="read-more">
                                Continue Reading →
                            </a>
                        </div>
                    </article>
                <?php endwhile; ?>
            </div>
            
            <?php the_posts_pagination([
                'mid_size' => 2,
                'prev_text' => '← Previous',
                'next_text' => 'Next →',
            ]); ?>
        <?php else: ?>
            <div class="no-posts">
                <h2>Nothing Found</h2>
                <p>It seems we can't find what you're looking for.</p>
            </div>
        <?php endif; ?>
    </div>
</main>

<?php get_footer(); ?>
