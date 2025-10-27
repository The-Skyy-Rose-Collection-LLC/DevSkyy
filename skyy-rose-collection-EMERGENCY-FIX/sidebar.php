<?php
/**
 * The sidebar containing the main widget area
 *
 * @package Skyy_Rose_Collection
 * @version 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

if (!is_active_sidebar('sidebar-1')) {
    return;
}
?>

<aside id="secondary" class="widget-area luxury-sidebar" role="complementary">
    <div class="sidebar-inner">
        
        <!-- Custom Search Widget -->
        <div class="widget luxury-search-widget" data-animate="fadeInUp">
            <div class="widget-content">
                <form role="search" method="get" class="luxury-search-form" action="<?php echo esc_url(home_url('/')); ?>">
                    <div class="search-input-wrapper">
                        <input type="search" 
                               class="search-field" 
                               placeholder="<?php esc_attr_e('Search luxury fashion...', 'skyy-rose-collection'); ?>" 
                               value="<?php echo get_search_query(); ?>" 
                               name="s" 
                               autocomplete="off"
                               data-live-search="true">
                        <button type="submit" class="search-submit" aria-label="<?php esc_attr_e('Search', 'skyy-rose-collection'); ?>">
                            <svg class="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
                                <path d="M21 21L16.514 16.506L21 21ZM19 10.5C19 15.194 15.194 19 10.5 19C5.806 19 2 15.194 2 10.5C2 5.806 5.806 2 10.5 2C15.194 2 19 5.806 19 10.5Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        </button>
                    </div>
                    <div class="search-suggestions" id="search-suggestions"></div>
                </form>
            </div>
        </div>

        <!-- Newsletter Signup Widget -->
        <div class="widget luxury-newsletter-widget" data-animate="fadeInUp" data-delay="200">
            <div class="widget-content">
                <div class="newsletter-header">
                    <h3 class="widget-title"><?php esc_html_e('Stay in Style', 'skyy-rose-collection'); ?></h3>
                    <p class="newsletter-subtitle"><?php esc_html_e('Get exclusive access to new collections and styling tips', 'skyy-rose-collection'); ?></p>
                </div>
                
                <form class="newsletter-form" id="sidebar-newsletter-form" data-ajax="true">
                    <div class="floating-label-group">
                        <input type="email" 
                               id="newsletter-email" 
                               name="email" 
                               class="floating-input" 
                               required 
                               autocomplete="email">
                        <label for="newsletter-email" class="floating-label">
                            <?php esc_html_e('Your email address', 'skyy-rose-collection'); ?>
                        </label>
                        <div class="input-border"></div>
                    </div>
                    
                    <button type="submit" class="newsletter-submit">
                        <span class="submit-text"><?php esc_html_e('Subscribe', 'skyy-rose-collection'); ?></span>
                        <span class="submit-loading">
                            <svg class="loading-spinner" width="20" height="20" viewBox="0 0 24 24">
                                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none" stroke-dasharray="31.416" stroke-dashoffset="31.416">
                                    <animate attributeName="stroke-dasharray" dur="2s" values="0 31.416;15.708 15.708;0 31.416" repeatCount="indefinite"/>
                                    <animate attributeName="stroke-dashoffset" dur="2s" values="0;-15.708;-31.416" repeatCount="indefinite"/>
                                </circle>
                            </svg>
                        </span>
                        <span class="submit-success">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                                <path d="M20 6L9 17L4 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        </span>
                    </button>
                    
                    <div class="form-messages">
                        <div class="success-message"><?php esc_html_e('Thank you for subscribing!', 'skyy-rose-collection'); ?></div>
                        <div class="error-message"><?php esc_html_e('Please enter a valid email address.', 'skyy-rose-collection'); ?></div>
                    </div>
                    
                    <p class="newsletter-privacy">
                        <?php esc_html_e('We respect your privacy. Unsubscribe at any time.', 'skyy-rose-collection'); ?>
                    </p>
                    
                    <?php wp_nonce_field('newsletter_signup', 'newsletter_nonce'); ?>
                </form>
            </div>
        </div>

        <!-- Recent Posts Widget -->
        <div class="widget luxury-recent-posts-widget" data-animate="fadeInUp" data-delay="400">
            <div class="widget-content">
                <h3 class="widget-title"><?php esc_html_e('Latest Stories', 'skyy-rose-collection'); ?></h3>
                
                <div class="recent-posts-list">
                    <?php
                    $recent_posts = wp_get_recent_posts(array(
                        'numberposts' => 3,
                        'post_status' => 'publish'
                    ));
                    
                    foreach ($recent_posts as $post) :
                        $post_id = $post['ID'];
                        $post_title = $post['post_title'];
                        $post_date = $post['post_date'];
                        $post_excerpt = wp_trim_words($post['post_content'], 15, '...');
                        $post_thumbnail = get_the_post_thumbnail($post_id, 'thumbnail');
                        $post_url = get_permalink($post_id);
                    ?>
                        <article class="recent-post-item">
                            <a href="<?php echo esc_url($post_url); ?>" class="recent-post-link">
                                <?php if ($post_thumbnail) : ?>
                                    <div class="recent-post-thumbnail">
                                        <?php echo wp_kses_post($post_thumbnail); ?>
                                    </div>
                                <?php endif; ?>
                                
                                <div class="recent-post-content">
                                    <h4 class="recent-post-title"><?php echo esc_html($post_title); ?></h4>
                                    <p class="recent-post-excerpt"><?php echo esc_html($post_excerpt); ?></p>
                                    <time class="recent-post-date" datetime="<?php echo esc_attr(date('c', strtotime($post_date))); ?>">
                                        <?php echo esc_html(date('F j, Y', strtotime($post_date))); ?>
                                    </time>
                                </div>
                            </a>
                        </article>
                    <?php endforeach; ?>
                </div>
                
                <div class="recent-posts-footer">
                    <a href="<?php echo esc_url(get_permalink(get_option('page_for_posts'))); ?>" class="view-all-posts">
                        <?php esc_html_e('View All Stories', 'skyy-rose-collection'); ?>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                            <path d="M5 12H19M19 12L12 5M19 12L12 19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </a>
                </div>
            </div>
        </div>

        <!-- Standard WordPress Widgets -->
        <?php dynamic_sidebar('sidebar-1'); ?>
        
    </div>
</aside>
