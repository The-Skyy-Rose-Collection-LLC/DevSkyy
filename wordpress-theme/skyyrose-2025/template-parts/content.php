<?php
/**
 * Template part for displaying posts
 */
?>
<article id="post-<?php the_ID(); ?>" <?php post_class('post-card'); ?>>
    <?php if (has_post_thumbnail()): ?>
        <div class="post-thumbnail">
            <a href="<?php the_permalink(); ?>">
                <?php the_post_thumbnail('skyyrose-medium'); ?>
            </a>
        </div>
    <?php endif; ?>
    
    <div class="post-content">
        <h2 class="post-title">
            <a href="<?php the_permalink(); ?>"><?php the_title(); ?></a>
        </h2>
        
        <div class="post-meta">
            <time datetime="<?php echo esc_attr(get_the_date('c')); ?>">
                <?php echo esc_html(get_the_date()); ?>
            </time>
        </div>
        
        <div class="post-excerpt">
            <?php the_excerpt(); ?>
        </div>
        
        <a href="<?php the_permalink(); ?>" class="read-more-link">
            <?php esc_html_e('Read More', 'skyyrose'); ?> →
        </a>
    </div>
</article>
