<?php
/**
 * Skyy Rose Luxury Fixed 2024 - Main Index Template
 * FIXED Luxury fashion theme for Skyy Rose Collection
 */
get_header(); ?>

<main id="main" class="site-main">
    <div class="container">
        <div class="skyy-rose-hero">
            <h1><?php bloginfo('name'); ?></h1>
            <?php
            $description = get_bloginfo('description', 'display');
            if ($description || is_customize_preview()) : ?>
                <p><?php echo $description; ?></p>
            <?php endif; ?>
            <a href="#content" class="cta-button">Explore Collection</a>
        </div>

        <div id="content" class="content-area">
            <?php if (have_posts()) : ?>
                <?php while (have_posts()) : the_post(); ?>
                    <article id="post-<?php the_ID(); ?>" <?php post_class('luxury-post'); ?>>
                        <header class="entry-header">
                            <h2 class="entry-title">
                                <a href="<?php the_permalink(); ?>" rel="bookmark">
                                    <?php the_title(); ?>
                                </a>
                            </h2>
                            <div class="entry-meta">
                                <time class="entry-date" datetime="<?php echo get_the_date('c'); ?>">
                                    <?php echo get_the_date(); ?>
                                </time>
                                <?php if (get_the_author()) : ?>
                                    <span class="author">by <?php the_author(); ?></span>
                                <?php endif; ?>
                            </div>
                        </header>

                        <div class="entry-content post-content">
                            <?php
                            if (is_home() || is_archive()) {
                                the_excerpt();
                                echo '<a href="' . get_permalink() . '" class="read-more">Continue Reading</a>';
                            } else {
                                the_content();
                            }
                            ?>
                        </div>
                    </article>
                    <hr class="luxury-divider">
                <?php endwhile; ?>

                <div class="pagination">
                    <?php
                    the_posts_pagination(array(
                        'prev_text' => '← Previous',
                        'next_text' => 'Next →',
                        'mid_size' => 2,
                    ));
                    ?>
                </div>
            <?php else : ?>
                <article class="luxury-post">
                    <header class="entry-header">
                        <h2>Nothing Found</h2>
                    </header>
                    <div class="entry-content">
                        <p>It seems we can't find what you're looking for. Perhaps searching can help.</p>
                        <?php get_search_form(); ?>
                    </div>
                </article>
            <?php endif; ?>
        </div>
    </div>
</main>

<?php get_footer(); ?>
