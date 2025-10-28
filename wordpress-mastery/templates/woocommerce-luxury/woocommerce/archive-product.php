<?php
/**
 * The Template for displaying product archives, including the main shop page which is a post type archive
 *
 * This template can be overridden by copying it to yourtheme/woocommerce/archive-product.php.
 * Enhanced with Skyy Rose Collection luxury styling and AI-powered filtering.
 *
 * @package WP_Mastery_WooCommerce_Luxury
 * @version 3.4.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
	exit;
}

get_header('shop');

/**
 * Hook: woocommerce_before_main_content
 *
 * @hooked woocommerce_output_content_wrapper - 10 (outputs opening divs for the content)
 * @hooked woocommerce_breadcrumb - 20
 */
do_action('woocommerce_before_main_content');
?>

<div class="skyy-rose-shop-wrapper" id="luxury-shop-experience">
	<!-- Skyy Rose Collection Shop Header -->
	<div class="skyy-rose-shop-header">
		<div class="container">
			<div class="shop-brand-section">
				<div class="brand-hero-area">
					<div class="skyy-rose-logo">
						<img src="<?php echo esc_url(get_template_directory_uri() . '/assets/images/skyy-rose-logo-luxury.svg'); ?>" 
							 alt="<?php esc_attr_e('Skyy Rose Collection', 'wp-mastery-woocommerce-luxury'); ?>" 
							 class="brand-logo">
					</div>
					<div class="brand-messaging">
						<?php if (apply_filters('woocommerce_show_page_title', true)) : ?>
							<h1 class="shop-title">
								<?php woocommerce_page_title(); ?>
							</h1>
						<?php endif; ?>
						
						<p class="shop-subtitle luxury-accent">
							<?php 
							if (is_product_category()) {
								$category = get_queried_object();
								if ($category && !empty($category->description)) {
									echo wp_kses_post($category->description);
								} else {
									esc_html_e('Discover Luxury Fashion Curated for You', 'wp-mastery-woocommerce-luxury');
								}
							} else {
								esc_html_e('Where Elegance Meets Innovation', 'wp-mastery-woocommerce-luxury');
							}
							?>
						</p>
					</div>
				</div>
				
				<!-- AI-Powered Shop Intelligence -->
				<div class="shop-ai-insights" id="shop-intelligence-panel">
					<div class="ai-insight-card">
						<div class="insight-icon">🎯</div>
						<div class="insight-content">
							<h4 class="insight-title"><?php esc_html_e('Smart Curation', 'wp-mastery-woocommerce-luxury'); ?></h4>
							<p class="insight-text" id="curation-status"><?php esc_html_e('Personalizing selection...', 'wp-mastery-woocommerce-luxury'); ?></p>
						</div>
					</div>
					<div class="ai-insight-card">
						<div class="insight-icon">📊</div>
						<div class="insight-content">
							<h4 class="insight-title"><?php esc_html_e('Trending Now', 'wp-mastery-woocommerce-luxury'); ?></h4>
							<p class="insight-text" id="trending-analysis"><?php esc_html_e('Analyzing trends...', 'wp-mastery-woocommerce-luxury'); ?></p>
						</div>
					</div>
					<div class="ai-insight-card">
						<div class="insight-icon">💎</div>
						<div class="insight-content">
							<h4 class="insight-title"><?php esc_html_e('Your Style Match', 'wp-mastery-woocommerce-luxury'); ?></h4>
							<p class="insight-text" id="style-match-score"><?php esc_html_e('Calculating compatibility...', 'wp-mastery-woocommerce-luxury'); ?></p>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>

	<div class="container">
		<div class="luxury-shop-layout">
			<!-- Advanced AI-Powered Filters Sidebar -->
			<div class="shop-filters-section">
				<div class="luxury-filters-wrapper">
					<div class="filters-header">
						<h3 class="filters-title"><?php esc_html_e('Refine Your Selection', 'wp-mastery-woocommerce-luxury'); ?></h3>
						<button type="button" class="filters-reset" id="reset-all-filters">
							<?php esc_html_e('Clear All', 'wp-mastery-woocommerce-luxury'); ?>
						</button>
					</div>

					<!-- AI Style Categories -->
					<div class="filter-group ai-style-filter">
						<h4 class="filter-group-title">
							<span class="filter-icon">✨</span>
							<?php esc_html_e('Style Categories', 'wp-mastery-woocommerce-luxury'); ?>
						</h4>
						<div class="filter-options" id="ai-style-categories">
							<!-- Populated by AI style analysis -->
						</div>
					</div>

					<!-- Material & Fabric Filter -->
					<div class="filter-group material-filter">
						<h4 class="filter-group-title">
							<span class="filter-icon">🧵</span>
							<?php esc_html_e('Materials & Fabrics', 'wp-mastery-woocommerce-luxury'); ?>
						</h4>
						<div class="filter-options" id="material-options">
							<!-- Populated by AI material detection -->
						</div>
					</div>

					<!-- Price Range with Dynamic Pricing -->
					<div class="filter-group price-filter">
						<h4 class="filter-group-title">
							<span class="filter-icon">💰</span>
							<?php esc_html_e('Price Range', 'wp-mastery-woocommerce-luxury'); ?>
						</h4>
						<div class="price-range-container">
							<div class="price-range-slider" id="luxury-price-range">
								<!-- Dynamic price range slider -->
							</div>
							<div class="price-range-display">
								<span class="price-min" id="price-min-display">$0</span>
								<span class="price-separator">-</span>
								<span class="price-max" id="price-max-display">$1000+</span>
							</div>
						</div>
					</div>

					<!-- Size & Fit Filter -->
					<div class="filter-group size-filter">
						<h4 class="filter-group-title">
							<span class="filter-icon">📏</span>
							<?php esc_html_e('Size & Fit', 'wp-mastery-woocommerce-luxury'); ?>
						</h4>
						<div class="filter-options" id="size-options">
							<div class="size-option" data-size="xs">XS</div>
							<div class="size-option" data-size="s">S</div>
							<div class="size-option" data-size="m">M</div>
							<div class="size-option" data-size="l">L</div>
							<div class="size-option" data-size="xl">XL</div>
							<div class="size-option" data-size="xxl">XXL</div>
						</div>
					</div>

					<!-- Color Palette Filter -->
					<div class="filter-group color-filter">
						<h4 class="filter-group-title">
							<span class="filter-icon">🎨</span>
							<?php esc_html_e('Color Palette', 'wp-mastery-woocommerce-luxury'); ?>
						</h4>
						<div class="color-options" id="color-palette">
							<!-- Populated by AI color analysis -->
						</div>
					</div>

					<!-- Occasion Filter -->
					<div class="filter-group occasion-filter">
						<h4 class="filter-group-title">
							<span class="filter-icon">🎭</span>
							<?php esc_html_e('Occasion', 'wp-mastery-woocommerce-luxury'); ?>
						</h4>
						<div class="filter-options" id="occasion-options">
							<div class="occasion-option" data-occasion="casual"><?php esc_html_e('Casual', 'wp-mastery-woocommerce-luxury'); ?></div>
							<div class="occasion-option" data-occasion="business"><?php esc_html_e('Business', 'wp-mastery-woocommerce-luxury'); ?></div>
							<div class="occasion-option" data-occasion="evening"><?php esc_html_e('Evening', 'wp-mastery-woocommerce-luxury'); ?></div>
							<div class="occasion-option" data-occasion="formal"><?php esc_html_e('Formal', 'wp-mastery-woocommerce-luxury'); ?></div>
							<div class="occasion-option" data-occasion="wedding"><?php esc_html_e('Wedding', 'wp-mastery-woocommerce-luxury'); ?></div>
						</div>
					</div>

					<!-- AI Recommendations Filter -->
					<div class="filter-group ai-recommendations-filter">
						<h4 class="filter-group-title">
							<span class="filter-icon">🤖</span>
							<?php esc_html_e('AI Recommendations', 'wp-mastery-woocommerce-luxury'); ?>
						</h4>
						<div class="ai-filter-options">
							<label class="ai-filter-option">
								<input type="checkbox" id="recommended-for-you" value="recommended">
								<span class="checkmark"></span>
								<span class="option-text"><?php esc_html_e('Recommended for You', 'wp-mastery-woocommerce-luxury'); ?></span>
							</label>
							<label class="ai-filter-option">
								<input type="checkbox" id="trending-items" value="trending">
								<span class="checkmark"></span>
								<span class="option-text"><?php esc_html_e('Trending Items', 'wp-mastery-woocommerce-luxury'); ?></span>
							</label>
							<label class="ai-filter-option">
								<input type="checkbox" id="new-arrivals" value="new">
								<span class="checkmark"></span>
								<span class="option-text"><?php esc_html_e('New Arrivals', 'wp-mastery-woocommerce-luxury'); ?></span>
							</label>
						</div>
					</div>

					<!-- Apply Filters Button -->
					<div class="filters-actions">
						<button type="button" class="btn-luxury apply-filters" id="apply-luxury-filters">
							<?php esc_html_e('Apply Filters', 'wp-mastery-woocommerce-luxury'); ?>
						</button>
					</div>
				</div>
			</div>

			<!-- Products Grid Section -->
			<div class="shop-products-section">
				<!-- Products Toolbar -->
				<div class="products-toolbar">
					<div class="toolbar-left">
						<div class="results-count" id="products-count">
							<?php
							$total_products = wc_get_loop_prop('total');
							if ($total_products) {
								printf(
									esc_html(_n('%d product found', '%d products found', $total_products, 'wp-mastery-woocommerce-luxury')),
									esc_html($total_products)
								);
							}
							?>
						</div>
					</div>
					
					<div class="toolbar-right">
						<!-- View Mode Toggle -->
						<div class="view-mode-toggle">
							<button type="button" class="view-mode-btn active" data-view="grid" id="grid-view">
								<span class="view-icon">⊞</span>
							</button>
							<button type="button" class="view-mode-btn" data-view="list" id="list-view">
								<span class="view-icon">☰</span>
							</button>
						</div>
						
						<!-- Sort Options -->
						<div class="sort-options">
							<?php woocommerce_catalog_ordering(); ?>
						</div>
					</div>
				</div>

				<!-- Products Grid -->
				<div class="products-grid-container" id="luxury-products-grid">
					<?php if (woocommerce_product_loop()) : ?>
						<?php
						/**
						 * Hook: woocommerce_before_shop_loop
						 *
						 * @hooked woocommerce_output_all_notices - 10
						 * @hooked woocommerce_result_count - 20
						 * @hooked woocommerce_catalog_ordering - 30
						 */
						do_action('woocommerce_before_shop_loop');
						?>

						<div class="products-grid luxury-products-grid" data-view="grid">
							<?php
							if (wc_get_loop_prop('is_shortcode')) {
								$columns = absint(wc_get_loop_prop('columns'));
							} else {
								$columns = wc_get_default_products_per_row();
							}

							woocommerce_product_loop_start();

							if (have_posts()) {
								while (have_posts()) {
									the_post();

									/**
									 * Hook: woocommerce_shop_loop
									 */
									do_action('woocommerce_shop_loop');

									wc_get_template_part('content', 'product');
								}
							}

							woocommerce_product_loop_end();
							?>
						</div>

						<?php
						/**
						 * Hook: woocommerce_after_shop_loop
						 *
						 * @hooked woocommerce_pagination - 10
						 */
						do_action('woocommerce_after_shop_loop');
						?>

					<?php else : ?>
						<?php
						/**
						 * Hook: woocommerce_no_products_found
						 *
						 * @hooked wc_no_products_found - 10
						 */
						do_action('woocommerce_no_products_found');
						?>
					<?php endif; ?>
				</div>

				<!-- AI-Powered Product Suggestions -->
				<div class="shop-suggestions-section" id="ai-shop-suggestions">
					<h3 class="suggestions-title"><?php esc_html_e('You Might Also Love', 'wp-mastery-woocommerce-luxury'); ?></h3>
					<div class="suggestions-grid" id="ai-product-suggestions">
						<!-- Populated by AI recommendation engine -->
					</div>
				</div>
			</div>
		</div>
	</div>

	<!-- AI Shop Analytics (Hidden) -->
	<div class="shop-analytics-tracker" id="shop-behavior-tracking" style="display: none;">
		<input type="hidden" id="shop-session-id" value="<?php echo esc_attr(WC()->session->get_customer_id()); ?>">
		<input type="hidden" id="category-context" value="<?php echo esc_attr(is_product_category() ? get_queried_object()->slug : 'shop'); ?>">
		<input type="hidden" id="applied-filters" value="">
		<input type="hidden" id="search-query" value="<?php echo esc_attr(get_search_query()); ?>">
		<input type="hidden" id="sort-order" value="">
	</div>
</div>

<?php
/**
 * Hook: woocommerce_after_main_content
 *
 * @hooked woocommerce_output_content_wrapper_end - 10 (outputs closing divs for the content)
 */
do_action('woocommerce_after_main_content');

/**
 * Hook: woocommerce_sidebar
 *
 * @hooked woocommerce_get_sidebar - 10
 */
do_action('woocommerce_sidebar');

get_footer('shop');
