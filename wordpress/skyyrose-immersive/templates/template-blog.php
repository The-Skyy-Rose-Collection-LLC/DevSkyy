<?php
/**
 * Template Name: Blog (Luxury Editorial)
 * Template Post Type: page
 *
 * SkyyRose luxury editorial blog layout
 * Magazine-style grid with featured posts
 *
 * @package SkyyRose_Immersive
 */

get_header();

// Query blog posts
$paged = (get_query_var('paged')) ? get_query_var('paged') : 1;
$featured_args = array(
    'post_type' => 'post',
    'posts_per_page' => 1,
    'meta_key' => '_is_ns_featured_post',
    'meta_value' => 'yes',
);
$featured_query = new WP_Query($featured_args);

// If no featured post, get latest
if (!$featured_query->have_posts()) {
    $featured_args = array(
        'post_type' => 'post',
        'posts_per_page' => 1,
    );
    $featured_query = new WP_Query($featured_args);
}

// Main blog query
$blog_args = array(
    'post_type' => 'post',
    'posts_per_page' => 9,
    'paged' => $paged,
    'post__not_in' => $featured_query->have_posts() ? array($featured_query->posts[0]->ID) : array(),
);
$blog_query = new WP_Query($blog_args);
?>

<main id="main" class="site-main skyyrose-blog">

    <!-- Blog Header -->
    <header class="blog-header">
        <div class="header-content">
            <span class="header-label">SkyyRose Journal</span>
            <h1 class="header-title">Stories, Style & Culture</h1>
            <p class="header-tagline">Where fashion meets feeling</p>
        </div>
    </header>

    <!-- Featured Post -->
    <?php if ($featured_query->have_posts()) : ?>
        <?php while ($featured_query->have_posts()) : $featured_query->the_post(); ?>
            <section class="featured-post">
                <a href="<?php the_permalink(); ?>" class="featured-link">
                    <div class="featured-image">
                        <?php if (has_post_thumbnail()) : ?>
                            <?php the_post_thumbnail('full'); ?>
                        <?php else : ?>
                            <div class="placeholder-image">
                                <span>🌹</span>
                            </div>
                        <?php endif; ?>
                        <div class="featured-overlay"></div>
                    </div>
                    <div class="featured-content">
                        <span class="featured-badge">Featured</span>
                        <div class="featured-meta">
                            <?php
                            $categories = get_the_category();
                            if ($categories) :
                            ?>
                                <span class="post-category"><?php echo $categories[0]->name; ?></span>
                            <?php endif; ?>
                            <span class="post-date"><?php echo get_the_date('M d, Y'); ?></span>
                        </div>
                        <h2 class="featured-title"><?php the_title(); ?></h2>
                        <p class="featured-excerpt"><?php echo wp_trim_words(get_the_excerpt(), 30); ?></p>
                        <span class="read-more">Read Article →</span>
                    </div>
                </a>
            </section>
        <?php endwhile; ?>
        <?php wp_reset_postdata(); ?>
    <?php endif; ?>

    <!-- Category Filter -->
    <section class="blog-categories">
        <div class="categories-container">
            <a href="<?php echo get_permalink(); ?>" class="category-link active">All</a>
            <?php
            $categories = get_categories(array('hide_empty' => true));
            foreach ($categories as $cat) :
            ?>
                <a href="<?php echo get_category_link($cat->term_id); ?>" class="category-link">
                    <?php echo $cat->name; ?>
                </a>
            <?php endforeach; ?>
        </div>
    </section>

    <!-- Blog Grid -->
    <section class="blog-grid-section">
        <div class="blog-grid">
            <?php if ($blog_query->have_posts()) : ?>
                <?php $post_count = 0; ?>
                <?php while ($blog_query->have_posts()) : $blog_query->the_post(); $post_count++; ?>
                    <article class="blog-card <?php echo ($post_count === 1 || $post_count === 6) ? 'large' : ''; ?>">
                        <a href="<?php the_permalink(); ?>" class="card-link">
                            <div class="card-image">
                                <?php if (has_post_thumbnail()) : ?>
                                    <?php the_post_thumbnail('large'); ?>
                                <?php else : ?>
                                    <div class="placeholder-image">
                                        <span>🌹</span>
                                    </div>
                                <?php endif; ?>
                                <div class="card-overlay"></div>
                            </div>
                            <div class="card-content">
                                <div class="card-meta">
                                    <?php
                                    $categories = get_the_category();
                                    if ($categories) :
                                    ?>
                                        <span class="post-category"><?php echo $categories[0]->name; ?></span>
                                    <?php endif; ?>
                                    <span class="post-date"><?php echo get_the_date('M d'); ?></span>
                                </div>
                                <h3 class="card-title"><?php the_title(); ?></h3>
                                <?php if ($post_count === 1 || $post_count === 6) : ?>
                                    <p class="card-excerpt"><?php echo wp_trim_words(get_the_excerpt(), 20); ?></p>
                                <?php endif; ?>
                            </div>
                        </a>
                    </article>
                <?php endwhile; ?>
            <?php else : ?>
                <div class="no-posts">
                    <span class="no-posts-icon">📝</span>
                    <h3>Coming Soon</h3>
                    <p>Stay tuned for stories from the SkyyRose universe.</p>
                </div>
            <?php endif; ?>
        </div>

        <!-- Pagination -->
        <?php if ($blog_query->max_num_pages > 1) : ?>
            <nav class="blog-pagination">
                <?php
                echo paginate_links(array(
                    'total' => $blog_query->max_num_pages,
                    'current' => $paged,
                    'prev_text' => '← Previous',
                    'next_text' => 'Next →',
                    'type' => 'list',
                ));
                ?>
            </nav>
        <?php endif; ?>
        <?php wp_reset_postdata(); ?>
    </section>

    <!-- Newsletter CTA -->
    <section class="blog-newsletter">
        <div class="newsletter-content">
            <span class="newsletter-icon">📬</span>
            <h2 class="newsletter-title">Stay in the Loop</h2>
            <p class="newsletter-text">
                Get early access to drops, exclusive content, and style inspiration.
            </p>
            <form class="newsletter-form" action="#" method="post">
                <input type="email" name="email" placeholder="Enter your email" required>
                <button type="submit">Subscribe</button>
            </form>
            <p class="newsletter-privacy">We respect your privacy. Unsubscribe anytime.</p>
        </div>
    </section>

</main>

<style>
/* Blog Page Styles */
.skyyrose-blog {
    background: #0a0a0a;
    color: #fff;
}

/* Blog Header */
.blog-header {
    padding: 8rem 2rem 4rem;
    text-align: center;
    background: linear-gradient(180deg, #111, #0a0a0a);
}

.header-label {
    display: block;
    font-size: 0.75rem;
    letter-spacing: 0.3em;
    text-transform: uppercase;
    color: #B76E79;
    margin-bottom: 1rem;
}

.header-title {
    font-family: 'Playfair Display', serif;
    font-size: clamp(2.5rem, 6vw, 4rem);
    margin-bottom: 0.5rem;
}

.header-tagline {
    color: rgba(255, 255, 255, 0.6);
    font-size: 1.125rem;
}

/* Featured Post */
.featured-post {
    max-width: 1400px;
    margin: 0 auto 4rem;
    padding: 0 2rem;
}

.featured-link {
    display: grid;
    grid-template-columns: 1.5fr 1fr;
    gap: 3rem;
    text-decoration: none;
    color: #fff;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    transition: all 0.4s ease;
}

.featured-link:hover {
    border-color: rgba(183, 110, 121, 0.3);
}

.featured-image {
    position: relative;
    aspect-ratio: 16/10;
    overflow: hidden;
}

.featured-image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.6s ease;
}

.featured-link:hover .featured-image img {
    transform: scale(1.05);
}

.featured-overlay {
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg, transparent 50%, rgba(10, 10, 10, 0.8));
}

.featured-content {
    padding: 3rem 3rem 3rem 0;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.featured-badge {
    display: inline-block;
    width: fit-content;
    padding: 0.25rem 0.75rem;
    background: #B76E79;
    font-size: 0.625rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 1rem;
}

.featured-meta,
.card-meta {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
    font-size: 0.75rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

.post-category {
    color: #B76E79;
}

.post-date {
    color: rgba(255, 255, 255, 0.5);
}

.featured-title {
    font-family: 'Playfair Display', serif;
    font-size: 2rem;
    line-height: 1.3;
    margin-bottom: 1rem;
}

.featured-excerpt {
    color: rgba(255, 255, 255, 0.7);
    line-height: 1.8;
    margin-bottom: 1.5rem;
}

.read-more {
    font-size: 0.875rem;
    color: #B76E79;
    transition: color 0.3s ease;
}

.featured-link:hover .read-more {
    color: #fff;
}

/* Category Filter */
.blog-categories {
    padding: 0 2rem 3rem;
}

.categories-container {
    display: flex;
    justify-content: center;
    gap: 0.5rem;
    flex-wrap: wrap;
    max-width: 1000px;
    margin: 0 auto;
}

.category-link {
    padding: 0.5rem 1.25rem;
    font-size: 0.75rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    text-decoration: none;
    color: rgba(255, 255, 255, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.15);
    transition: all 0.3s ease;
}

.category-link:hover,
.category-link.active {
    color: #B76E79;
    border-color: #B76E79;
}

/* Blog Grid */
.blog-grid-section {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 2rem 4rem;
}

.blog-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 2rem;
}

/* Blog Card */
.blog-card {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    transition: all 0.4s ease;
}

.blog-card:hover {
    border-color: rgba(183, 110, 121, 0.3);
    transform: translateY(-4px);
}

.blog-card.large {
    grid-column: span 2;
}

.card-link {
    display: block;
    text-decoration: none;
    color: #fff;
}

.card-image {
    position: relative;
    aspect-ratio: 16/10;
    overflow: hidden;
}

.blog-card.large .card-image {
    aspect-ratio: 21/9;
}

.card-image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.6s ease;
}

.blog-card:hover .card-image img {
    transform: scale(1.05);
}

.card-overlay {
    position: absolute;
    inset: 0;
    background: linear-gradient(180deg, transparent 50%, rgba(10, 10, 10, 0.8));
}

.placeholder-image {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    background: linear-gradient(135deg, #1a1a1a, #0a0a0a);
    font-size: 4rem;
    opacity: 0.3;
}

.card-content {
    padding: 1.5rem;
}

.card-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.25rem;
    line-height: 1.4;
    margin-bottom: 0.5rem;
    transition: color 0.3s ease;
}

.blog-card.large .card-title {
    font-size: 1.5rem;
}

.blog-card:hover .card-title {
    color: #B76E79;
}

.card-excerpt {
    color: rgba(255, 255, 255, 0.6);
    font-size: 0.875rem;
    line-height: 1.7;
}

/* No Posts */
.no-posts {
    grid-column: 1 / -1;
    text-align: center;
    padding: 6rem 2rem;
}

.no-posts-icon {
    font-size: 4rem;
    display: block;
    margin-bottom: 1rem;
    opacity: 0.3;
}

.no-posts h3 {
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
}

.no-posts p {
    color: rgba(255, 255, 255, 0.5);
}

/* Pagination */
.blog-pagination {
    margin-top: 4rem;
    text-align: center;
}

.blog-pagination ul {
    display: flex;
    justify-content: center;
    gap: 0.5rem;
    list-style: none;
    padding: 0;
    margin: 0;
}

.blog-pagination li a,
.blog-pagination li span {
    display: block;
    padding: 0.75rem 1rem;
    font-size: 0.875rem;
    text-decoration: none;
    color: rgba(255, 255, 255, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.15);
    transition: all 0.3s ease;
}

.blog-pagination li a:hover,
.blog-pagination li span.current {
    color: #B76E79;
    border-color: #B76E79;
}

/* Newsletter CTA */
.blog-newsletter {
    padding: 6rem 2rem;
    background: linear-gradient(135deg, #B76E79, #8B4D5C);
    text-align: center;
}

.newsletter-icon {
    font-size: 3rem;
    display: block;
    margin-bottom: 1rem;
}

.newsletter-title {
    font-family: 'Playfair Display', serif;
    font-size: 2rem;
    margin-bottom: 0.5rem;
}

.newsletter-text {
    opacity: 0.9;
    max-width: 400px;
    margin: 0 auto 2rem;
}

.newsletter-form {
    display: flex;
    gap: 0.5rem;
    max-width: 450px;
    margin: 0 auto;
}

.newsletter-form input {
    flex: 1;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.3);
    color: #fff;
    font-size: 0.875rem;
}

.newsletter-form input::placeholder {
    color: rgba(255, 255, 255, 0.6);
}

.newsletter-form button {
    padding: 1rem 2rem;
    background: #fff;
    border: none;
    color: #B76E79;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.3s ease;
}

.newsletter-form button:hover {
    background: #0a0a0a;
    color: #fff;
}

.newsletter-privacy {
    font-size: 0.75rem;
    opacity: 0.7;
    margin-top: 1rem;
}

/* Responsive */
@media (max-width: 1024px) {
    .featured-link {
        grid-template-columns: 1fr;
    }

    .featured-content {
        padding: 2rem;
    }

    .featured-overlay {
        background: linear-gradient(180deg, transparent 30%, rgba(10, 10, 10, 0.9));
    }

    .blog-grid {
        grid-template-columns: repeat(2, 1fr);
    }

    .blog-card.large {
        grid-column: span 2;
    }
}

@media (max-width: 768px) {
    .blog-grid {
        grid-template-columns: 1fr;
    }

    .blog-card.large {
        grid-column: span 1;
    }

    .newsletter-form {
        flex-direction: column;
    }

    .newsletter-form button {
        width: 100%;
    }
}
</style>

<?php
get_footer();
