<?php
/**
 * The main template file
 *
 * @package Skyy_Rose_Collection
 * @version 1.0.1
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

get_header(); ?>

<main id="primary" class="site-main">
    <div class="container">
        <div class="row">
            <div class="col-8">
                <?php if (have_posts()) : ?>
                    <?php while (have_posts()) : the_post(); ?>
                        <article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
                            <header class="entry-header">
                                <?php
                                if (is_singular()) :
                                    the_title('<h1 class="entry-title">', '</h1>');
                                else :
                                    the_title('<h2 class="entry-title"><a href="' . esc_url(get_permalink()) . '" rel="bookmark">', '</a></h2>');
                                endif;
                                ?>
                            </header>

                            <div class="entry-content">
                                <?php
                                if (is_singular()) {
                                    the_content();
                                } else {
                                    the_excerpt();
                                }
                                ?>
                            </div>
                        </article>
                    <?php endwhile; ?>

                    <?php
                    the_posts_navigation();
                    ?>

                <?php else : ?>
                    <section class="no-results not-found">
                        <header class="page-header">
                            <h1 class="page-title"><?php esc_html_e('Nothing here', 'skyy-rose-collection'); ?></h1>
                        </header>
                        <div class="page-content">
                            <p><?php esc_html_e('It seems we can&rsquo;t find what you&rsquo;re looking for. Perhaps searching can help.', 'skyy-rose-collection'); ?></p>
                            <?php get_search_form(); ?>
                        </div>
                    </section>
                <?php endif; ?>
            </div>

            <div class="col-4">
                <?php
                if (is_active_sidebar('sidebar-1')) {
                    get_sidebar();
                }
                ?>
            </div>
        </div>
    </div>
</main>

<?php get_footer(); ?>
