<?php
/**
 * Single Post Template
 * Skyy Rose Luxury Fixed 2024
 */
get_header(); ?>

<main id="main" class="site-main">
    <div class="container-narrow">
        <?php while (have_posts()) : the_post(); ?>
            <article id="post-<?php the_ID(); ?>" <?php post_class('luxury-post'); ?>>
                <header class="entry-header">
                    <h1 class="entry-title"><?php the_title(); ?></h1>
                    <div class="entry-meta">
                        <time class="entry-date" datetime="<?php echo get_the_date('c'); ?>">
                            <?php echo get_the_date(); ?>
                        </time>
                        <?php if (get_the_author()) : ?>
                            <span class="author">by <?php the_author(); ?></span>
                        <?php endif; ?>
                        <?php if (get_the_category_list(', ')) : ?>
                            <span class="categories">in <?php the_category(', '); ?></span>
                        <?php endif; ?>
                    </div>
                </header>

                <?php if (has_post_thumbnail()) : ?>
                    <div class="post-thumbnail">
                        <?php the_post_thumbnail('large'); ?>
                    </div>
                <?php endif; ?>

                <div class="entry-content post-content">
                    <?php the_content(); ?>
                </div>

                <?php if (get_the_tags()) : ?>
                    <footer class="entry-footer">
                        <div class="tags">
                            <?php the_tags('<span class="luxury-accent">Tags: </span>', ', ', ''); ?>
                        </div>
                    </footer>
                <?php endif; ?>
            </article>

            <nav class="post-navigation">
                <div class="nav-links">
                    <?php
                    previous_post_link('<div class="nav-previous">%link</div>', '← %title');
                    next_post_link('<div class="nav-next">%link</div>', '%title →');
                    ?>
                </div>
            </nav>
        <?php endwhile; ?>
    </div>
</main>

<?php get_footer(); ?>
