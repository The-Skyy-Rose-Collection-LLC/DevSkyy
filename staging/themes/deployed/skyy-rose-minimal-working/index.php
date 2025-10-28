<?php get_header(); ?>

<main class="site-main">
    <h1>Skyy Rose Collection</h1>
    <p>Luxury Fashion Redefined</p>
    
    <?php if (have_posts()) : ?>
        <?php while (have_posts()) : the_post(); ?>
            <article class="luxury-post">
                <h2 class="entry-title">
                    <a href="<?php the_permalink(); ?>"><?php the_title(); ?></a>
                </h2>
                <div class="entry-content">
                    <?php the_content(); ?>
                </div>
            </article>
        <?php endwhile; ?>
    <?php else : ?>
        <article class="luxury-post">
            <h2>Welcome to Skyy Rose Collection</h2>
            <p>Your luxury fashion destination is being prepared.</p>
        </article>
    <?php endif; ?>
</main>

<?php get_footer(); ?>
