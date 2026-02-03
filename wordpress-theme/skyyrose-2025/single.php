<?php
/**
 * The template for displaying single posts
 *
 * @package SkyyRose_2025
 * @version 3.0.0
 */

if (!defined('ABSPATH')) exit;

get_header();
?>

<main class="site-main single-post-luxury">
    <?php while (have_posts()): the_post(); ?>
        <article id="post-<?php the_ID(); ?>" <?php post_class('luxury-post-content'); ?>>
            
            <!-- Hero Section -->
            <?php if (has_post_thumbnail()): ?>
                <div class="post-hero">
                    <?php the_post_thumbnail('skyyrose-hero', array(
                        'class' => 'post-hero-image',
                        'alt' => get_the_title(),
                    )); ?>
                    <div class="post-hero-overlay"></div>
                </div>
            <?php endif; ?>

            <div class="container">
                <div class="post-wrapper">
                    
                    <!-- Post Header -->
                    <header class="post-header">
                        <?php
                        $categories = get_the_category();
                        if (!empty($categories)):
                            ?>
                            <div class="post-category">
                                <a href="<?php echo esc_url(get_category_link($categories[0]->term_id)); ?>">
                                    <?php echo esc_html($categories[0]->name); ?>
                                </a>
                            </div>
                        <?php endif; ?>
                        
                        <h1 class="post-title"><?php the_title(); ?></h1>
                        
                        <div class="post-meta">
                            <div class="meta-item">
                                <time datetime="<?php echo esc_attr(get_the_date('c')); ?>" class="post-date">
                                    <?php echo esc_html(get_the_date('F j, Y')); ?>
                                </time>
                            </div>
                            <div class="meta-item">
                                <span class="post-author">
                                    <?php
                                    printf(
                                        esc_html__('by %s', 'skyyrose'),
                                        '<a href="' . esc_url(get_author_posts_url(get_the_author_meta('ID'))) . '">' . esc_html(get_the_author()) . '</a>'
                                    );
                                    ?>
                                </span>
                            </div>
                            <?php if (get_the_modified_time('U') !== get_the_time('U')): ?>
                                <div class="meta-item">
                                    <span class="post-updated">
                                        <?php
                                        printf(
                                            esc_html__('Updated: %s', 'skyyrose'),
                                            '<time datetime="' . esc_attr(get_the_modified_date('c')) . '">' . esc_html(get_the_modified_date()) . '</time>'
                                        );
                                        ?>
                                    </span>
                                </div>
                            <?php endif; ?>
                        </div>
                    </header>

                    <!-- Post Content -->
                    <div class="post-content-area">
                        <?php
                        the_content();
                        
                        wp_link_pages(array(
                            'before' => '<div class="page-links">' . esc_html__('Pages:', 'skyyrose'),
                            'after' => '</div>',
                            'link_before' => '<span class="page-number">',
                            'link_after' => '</span>',
                        ));
                        ?>
                    </div>

                    <!-- Post Footer -->
                    <footer class="post-footer">
                        <?php
                        $tags = get_the_tags();
                        if ($tags):
                            ?>
                            <div class="post-tags">
                                <span class="tags-label"><?php esc_html_e('Tags:', 'skyyrose'); ?></span>
                                <?php
                                foreach ($tags as $tag):
                                    echo '<a href="' . esc_url(get_tag_link($tag->term_id)) . '" class="tag">' . esc_html($tag->name) . '</a>';
                                endforeach;
                                ?>
                            </div>
                        <?php endif; ?>
                        
                        <?php
                        // Post navigation
                        $prev_post = get_previous_post();
                        $next_post = get_next_post();
                        if ($prev_post || $next_post):
                            ?>
                            <nav class="post-navigation">
                                <?php if ($prev_post): ?>
                                    <div class="nav-previous">
                                        <a href="<?php echo esc_url(get_permalink($prev_post->ID)); ?>" rel="prev">
                                            <span class="nav-subtitle"><?php esc_html_e('Previous Post', 'skyyrose'); ?></span>
                                            <span class="nav-title"><?php echo esc_html($prev_post->post_title); ?></span>
                                        </a>
                                    </div>
                                <?php endif; ?>
                                
                                <?php if ($next_post): ?>
                                    <div class="nav-next">
                                        <a href="<?php echo esc_url(get_permalink($next_post->ID)); ?>" rel="next">
                                            <span class="nav-subtitle"><?php esc_html_e('Next Post', 'skyyrose'); ?></span>
                                            <span class="nav-title"><?php echo esc_html($next_post->post_title); ?></span>
                                        </a>
                                    </div>
                                <?php endif; ?>
                            </nav>
                        <?php endif; ?>
                    </footer>

                    <!-- Author Bio -->
                    <?php
                    $author_bio = get_the_author_meta('description');
                    if ($author_bio):
                        ?>
                        <div class="author-bio">
                            <div class="author-avatar">
                                <?php echo get_avatar(get_the_author_meta('ID'), 100); ?>
                            </div>
                            <div class="author-info">
                                <h3 class="author-name">
                                    <a href="<?php echo esc_url(get_author_posts_url(get_the_author_meta('ID'))); ?>">
                                        <?php echo esc_html(get_the_author()); ?>
                                    </a>
                                </h3>
                                <p class="author-description"><?php echo esc_html($author_bio); ?></p>
                            </div>
                        </div>
                    <?php endif; ?>

                    <!-- Comments -->
                    <?php
                    if (comments_open() || get_comments_number()):
                        comments_template();
                    endif;
                    ?>

                </div>
            </div>

        </article>
    <?php endwhile; ?>
</main>

<?php get_footer(); ?>
