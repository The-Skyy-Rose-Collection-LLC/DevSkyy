<?php
/**
 * Template for displaying search forms
 *
 * @package Skyy_Rose_Collection
 * @version 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

$unique_id = wp_unique_id('search-form-');
?>

<form role="search" method="get" class="luxury-search-form" action="<?php echo esc_url(home_url('/')); ?>">
    <div class="search-form-wrapper">
        <div class="search-input-container">
            <label for="<?php echo esc_attr($unique_id); ?>" class="screen-reader-text">
                <?php esc_html_e('Search for:', 'skyy-rose-collection'); ?>
            </label>
            
            <input type="search" 
                   id="<?php echo esc_attr($unique_id); ?>"
                   class="search-field" 
                   placeholder="<?php esc_attr_e('Search luxury fashion, brands, styles...', 'skyy-rose-collection'); ?>" 
                   value="<?php echo get_search_query(); ?>" 
                   name="s" 
                   autocomplete="off"
                   data-live-search="true"
                   data-min-chars="2"
                   data-search-delay="300">
            
            <div class="search-input-border"></div>
            
            <button type="submit" class="search-submit" aria-label="<?php esc_attr_e('Search', 'skyy-rose-collection'); ?>">
                <svg class="search-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M21 21L16.514 16.506L21 21ZM19 10.5C19 15.194 15.194 19 10.5 19C5.806 19 2 15.194 2 10.5C2 5.806 5.806 2 10.5 2C15.194 2 19 5.806 19 10.5Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <svg class="loading-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none" stroke-dasharray="31.416" stroke-dashoffset="31.416">
                        <animate attributeName="stroke-dasharray" dur="2s" values="0 31.416;15.708 15.708;0 31.416" repeatCount="indefinite"/>
                        <animate attributeName="stroke-dashoffset" dur="2s" values="0;-15.708;-31.416" repeatCount="indefinite"/>
                    </circle>
                </svg>
            </button>
            
            <!-- Voice Search Button -->
            <button type="button" class="voice-search-btn" aria-label="<?php esc_attr_e('Voice Search', 'skyy-rose-collection'); ?>" data-voice-search="true">
                <svg class="mic-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <path d="M12 1C10.34 1 9 2.34 9 4V12C9 13.66 10.34 15 12 15C13.66 15 15 13.66 15 12V4C15 2.34 13.66 1 12 1Z" stroke="currentColor" stroke-width="2"/>
                    <path d="M19 10V12C19 16.42 15.42 20 11 20H13C17.42 20 21 16.42 21 12V10" stroke="currentColor" stroke-width="2"/>
                    <line x1="12" y1="20" x2="12" y2="24" stroke="currentColor" stroke-width="2"/>
                    <line x1="8" y1="24" x2="16" y2="24" stroke="currentColor" stroke-width="2"/>
                </svg>
                <svg class="mic-active-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="3" fill="currentColor"/>
                    <path d="M12 1C10.34 1 9 2.34 9 4V12C9 13.66 10.34 15 12 15C13.66 15 15 13.66 15 12V4C15 2.34 13.66 1 12 1Z" stroke="currentColor" stroke-width="2"/>
                </svg>
            </button>
        </div>
        
        <!-- Search Suggestions Dropdown -->
        <div class="search-suggestions" id="search-suggestions-<?php echo esc_attr($unique_id); ?>">
            <div class="suggestions-header">
                <h4 class="suggestions-title"><?php esc_html_e('Suggestions', 'skyy-rose-collection'); ?></h4>
            </div>
            
            <div class="suggestions-content">
                <!-- Popular Searches -->
                <div class="suggestions-section popular-searches">
                    <h5 class="section-title"><?php esc_html_e('Popular Searches', 'skyy-rose-collection'); ?></h5>
                    <ul class="popular-list">
                        <li><a href="<?php echo esc_url(home_url('/?s=evening+dress')); ?>"><?php esc_html_e('Evening Dress', 'skyy-rose-collection'); ?></a></li>
                        <li><a href="<?php echo esc_url(home_url('/?s=silk+blouse')); ?>"><?php esc_html_e('Silk Blouse', 'skyy-rose-collection'); ?></a></li>
                        <li><a href="<?php echo esc_url(home_url('/?s=luxury+handbag')); ?>"><?php esc_html_e('Luxury Handbag', 'skyy-rose-collection'); ?></a></li>
                        <li><a href="<?php echo esc_url(home_url('/?s=designer+shoes')); ?>"><?php esc_html_e('Designer Shoes', 'skyy-rose-collection'); ?></a></li>
                    </ul>
                </div>
                
                <!-- Recent Searches (populated by JavaScript) -->
                <div class="suggestions-section recent-searches" style="display: none;">
                    <h5 class="section-title"><?php esc_html_e('Recent Searches', 'skyy-rose-collection'); ?></h5>
                    <ul class="recent-list"></ul>
                    <button class="clear-recent" type="button"><?php esc_html_e('Clear History', 'skyy-rose-collection'); ?></button>
                </div>
                
                <!-- Live Search Results (populated by AJAX) -->
                <div class="suggestions-section live-results">
                    <h5 class="section-title"><?php esc_html_e('Products', 'skyy-rose-collection'); ?></h5>
                    <div class="live-results-list"></div>
                </div>
                
                <!-- Categories -->
                <div class="suggestions-section categories">
                    <h5 class="section-title"><?php esc_html_e('Categories', 'skyy-rose-collection'); ?></h5>
                    <ul class="categories-list">
                        <?php
                        if (class_exists('WooCommerce')) {
                            $product_categories = get_terms(array(
                                'taxonomy' => 'product_cat',
                                'hide_empty' => true,
                                'number' => 6,
                                'parent' => 0,
                            ));
                            
                            if ($product_categories && !is_wp_error($product_categories)) {
                                foreach ($product_categories as $category) {
                                    echo '<li><a href="' . esc_url(get_term_link($category)) . '">' . esc_html($category->name) . '</a></li>';
                                }
                            }
                        }
                        ?>
                    </ul>
                </div>
            </div>
            
            <div class="suggestions-footer">
                <div class="search-tips">
                    <span class="tip-icon">💡</span>
                    <span class="tip-text"><?php esc_html_e('Try searching by color, material, or occasion', 'skyy-rose-collection'); ?></span>
                </div>
            </div>
        </div>
        
        <!-- Voice Search Status -->
        <div class="voice-search-status" style="display: none;">
            <div class="voice-status-content">
                <div class="voice-animation">
                    <div class="voice-wave"></div>
                    <div class="voice-wave"></div>
                    <div class="voice-wave"></div>
                </div>
                <p class="voice-status-text"><?php esc_html_e('Listening...', 'skyy-rose-collection'); ?></p>
                <button type="button" class="voice-cancel"><?php esc_html_e('Cancel', 'skyy-rose-collection'); ?></button>
            </div>
        </div>
    </div>
    
    <!-- Hidden fields for advanced search -->
    <input type="hidden" name="post_type" value="product" class="search-post-type">
    
    <?php if (class_exists('WooCommerce')) : ?>
        <!-- WooCommerce specific search parameters -->
        <input type="hidden" name="product_cat" value="" class="search-category">
        <input type="hidden" name="orderby" value="relevance" class="search-orderby">
    <?php endif; ?>
</form>

<!-- Search Analytics (hidden) -->
<script type="application/json" id="search-analytics-data">
{
    "search_endpoint": "<?php echo esc_url(admin_url('admin-ajax.php')); ?>",
    "nonce": "<?php echo esc_attr(wp_create_nonce('search_analytics_nonce')); ?>",
    "user_id": "<?php echo esc_attr(get_current_user_id()); ?>",
    "session_id": "<?php echo esc_attr(session_id() ?: wp_generate_uuid4()); ?>"
}
</script>
