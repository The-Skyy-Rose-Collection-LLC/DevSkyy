<?php
/**
 * The Template for displaying all single products
 *
 * This template can be overridden by copying it to yourtheme/woocommerce/single-product.php.
 * Enhanced with AI-powered features and luxury styling.
 *
 * @package WP_Mastery_WooCommerce_Luxury
 * @version 1.6.4
 */

// Prevent direct access
if (!defined('ABSPATH')) {
	exit;
}

get_header('shop'); ?>

<div class="luxury-product-wrapper" id="product-<?php the_ID(); ?>">
	<?php
	/**
	 * Hook: woocommerce_before_single_product
	 *
	 * @hooked wc_print_notices - 10
	 */
	do_action('woocommerce_before_single_product');

	if (post_password_required()) {
		echo get_the_password_form(); // WPCS: XSS ok.
		return;
	}
	?>

	<div id="product-<?php the_ID(); ?>" <?php wc_product_class('luxury-single-product', $product); ?>>
		
		<!-- AI-Powered Product Analysis Header -->
		<div class="product-ai-header" id="ai-analysis-header">
			<div class="container">
				<div class="ai-insights-bar">
					<div class="style-analysis" id="ai-style-analysis">
						<span class="insight-label"><?php esc_html_e('Style:', 'wp-mastery-woocommerce-luxury'); ?></span>
						<span class="insight-value" id="detected-style"><?php esc_html_e('Analyzing...', 'wp-mastery-woocommerce-luxury'); ?></span>
					</div>
					<div class="material-analysis" id="ai-material-analysis">
						<span class="insight-label"><?php esc_html_e('Materials:', 'wp-mastery-woocommerce-luxury'); ?></span>
						<span class="insight-value" id="detected-materials"><?php esc_html_e('Analyzing...', 'wp-mastery-woocommerce-luxury'); ?></span>
					</div>
					<div class="quality-score" id="ai-quality-score">
						<span class="insight-label"><?php esc_html_e('Quality Score:', 'wp-mastery-woocommerce-luxury'); ?></span>
						<span class="insight-value" id="quality-rating">
							<div class="rating-stars" id="ai-quality-stars"></div>
						</span>
					</div>
				</div>
			</div>
		</div>

		<div class="container">
			<div class="product-layout-grid">
				
				<!-- Enhanced Product Images with Advanced Media Management -->
				<div class="product-images-section">
					<?php
					/**
					 * Hook: woocommerce_before_single_product_summary
					 *
					 * @hooked woocommerce_show_product_sale_flash - 10
					 * @hooked woocommerce_show_product_images - 20
					 */
					do_action('woocommerce_before_single_product_summary');
					?>

					<!-- Advanced Image Gallery Controls -->
					<div class="luxury-gallery-controls" id="advanced-gallery-controls">
						<div class="gallery-modes">
							<button type="button" class="gallery-mode-btn active" data-mode="standard" id="standard-view">
								<span class="mode-icon">🖼️</span>
								<span class="mode-text"><?php esc_html_e('Gallery', 'wp-mastery-woocommerce-luxury'); ?></span>
							</button>
							<button type="button" class="gallery-mode-btn" data-mode="360" id="360-view">
								<span class="mode-icon">🔄</span>
								<span class="mode-text"><?php esc_html_e('360° View', 'wp-mastery-woocommerce-luxury'); ?></span>
							</button>
							<button type="button" class="gallery-mode-btn" data-mode="zoom" id="zoom-view">
								<span class="mode-icon">🔍</span>
								<span class="mode-text"><?php esc_html_e('Zoom', 'wp-mastery-woocommerce-luxury'); ?></span>
							</button>
							<button type="button" class="gallery-mode-btn" data-mode="ar" id="ar-view">
								<span class="mode-icon">📱</span>
								<span class="mode-text"><?php esc_html_e('AR View', 'wp-mastery-woocommerce-luxury'); ?></span>
							</button>
						</div>

						<!-- Image Resolution Selector -->
						<div class="resolution-selector" id="image-resolution">
							<label for="resolution-select"><?php esc_html_e('Image Quality:', 'wp-mastery-woocommerce-luxury'); ?></label>
							<select id="resolution-select" class="luxury-select">
								<option value="medium"><?php esc_html_e('Standard', 'wp-mastery-woocommerce-luxury'); ?></option>
								<option value="large"><?php esc_html_e('High Quality', 'wp-mastery-woocommerce-luxury'); ?></option>
								<option value="luxury-product-large" selected><?php esc_html_e('Ultra HD', 'wp-mastery-woocommerce-luxury'); ?></option>
							</select>
						</div>
					</div>

					<!-- 360-Degree View Container -->
					<div class="product-360-container" id="product-360-viewer" style="display: none;">
						<div class="viewer-360" id="threesixty-viewer">
							<!-- 360-degree images loaded dynamically -->
						</div>
						<div class="viewer-controls">
							<button type="button" class="control-btn" id="rotate-left">⬅️</button>
							<button type="button" class="control-btn" id="auto-rotate">🔄</button>
							<button type="button" class="control-btn" id="rotate-right">➡️</button>
						</div>
					</div>

					<!-- AR View Container -->
					<div class="product-ar-container" id="product-ar-viewer" style="display: none;">
						<div class="ar-viewer" id="ar-model-viewer">
							<!-- AR model viewer -->
						</div>
						<div class="ar-instructions">
							<p><?php esc_html_e('Point your camera at a flat surface to place the product in your space.', 'wp-mastery-woocommerce-luxury'); ?></p>
						</div>
					</div>
				</div>

				<!-- Product Information with AI Enhancement -->
				<div class="product-summary-section">
					<div class="summary entry-summary">
						<?php
						/**
						 * Hook: woocommerce_single_product_summary
						 *
						 * @hooked woocommerce_template_single_title - 5
						 * @hooked woocommerce_template_single_rating - 10
						 * @hooked woocommerce_template_single_price - 10
						 * @hooked woocommerce_template_single_excerpt - 20
						 * @hooked woocommerce_template_single_add_to_cart - 30
						 * @hooked woocommerce_template_single_meta - 40
						 * @hooked woocommerce_template_single_sharing - 50
						 * @hooked WC_Structured_Data::generate_product_data() - 60
						 */
						do_action('woocommerce_single_product_summary');
						?>

						<!-- AI-Enhanced Product Attributes -->
						<div class="ai-enhanced-attributes" id="ai-product-attributes">
							<h3 class="attributes-title"><?php esc_html_e('Product Intelligence', 'wp-mastery-woocommerce-luxury'); ?></h3>
							
							<div class="attribute-group" id="style-attributes">
								<h4 class="attribute-title"><?php esc_html_e('Style Analysis', 'wp-mastery-woocommerce-luxury'); ?></h4>
								<div class="attribute-values" id="ai-style-details">
									<!-- Populated by AI style analysis -->
								</div>
							</div>

							<div class="attribute-group" id="material-attributes">
								<h4 class="attribute-title"><?php esc_html_e('Material Composition', 'wp-mastery-woocommerce-luxury'); ?></h4>
								<div class="attribute-values" id="ai-material-details">
									<!-- Populated by AI material detection -->
								</div>
							</div>

							<div class="attribute-group" id="care-instructions">
								<h4 class="attribute-title"><?php esc_html_e('Care Instructions', 'wp-mastery-woocommerce-luxury'); ?></h4>
								<div class="attribute-values" id="ai-care-guide">
									<!-- Generated by AI based on materials -->
								</div>
							</div>
						</div>

						<!-- Dynamic Pricing Display -->
						<div class="dynamic-pricing-section" id="dynamic-pricing">
							<div class="pricing-insights">
								<div class="price-trend" id="price-trend-indicator">
									<!-- Price trend analysis -->
								</div>
								<div class="personalized-offers" id="customer-specific-offers">
									<!-- Personalized pricing based on customer segment -->
								</div>
							</div>
						</div>

						<!-- Smart Size/Variation Recommendations -->
						<div class="smart-recommendations-inline" id="variation-recommendations">
							<h4 class="recommendations-title"><?php esc_html_e('Recommended for You', 'wp-mastery-woocommerce-luxury'); ?></h4>
							<div class="size-recommendations" id="ai-size-suggestions">
								<!-- AI-powered size recommendations -->
							</div>
							<div class="color-recommendations" id="ai-color-suggestions">
								<!-- AI-powered color recommendations -->
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- Advanced Product Tabs with AI Content -->
			<div class="luxury-product-tabs" id="enhanced-product-tabs">
				<?php
				/**
				 * Hook: woocommerce_output_product_data_tabs
				 *
				 * @hooked woocommerce_output_product_data_tabs - 10
				 */
				do_action('woocommerce_output_product_data_tabs');
				?>

				<!-- AI-Generated Content Tabs -->
				<div class="ai-content-tabs">
					<div class="tab-nav">
						<button class="tab-btn active" data-tab="styling-tips"><?php esc_html_e('Styling Tips', 'wp-mastery-woocommerce-luxury'); ?></button>
						<button class="tab-btn" data-tab="material-guide"><?php esc_html_e('Material Guide', 'wp-mastery-woocommerce-luxury'); ?></button>
						<button class="tab-btn" data-tab="sustainability"><?php esc_html_e('Sustainability', 'wp-mastery-woocommerce-luxury'); ?></button>
					</div>
					
					<div class="tab-content">
						<div class="tab-panel active" id="styling-tips">
							<div class="ai-generated-content" id="ai-styling-suggestions">
								<!-- AI-generated styling suggestions -->
							</div>
						</div>
						<div class="tab-panel" id="material-guide">
							<div class="ai-generated-content" id="ai-material-guide">
								<!-- AI-generated material information -->
							</div>
						</div>
						<div class="tab-panel" id="sustainability">
							<div class="ai-generated-content" id="ai-sustainability-info">
								<!-- AI-generated sustainability information -->
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- Cross-sell and Upsell with AI -->
			<div class="ai-product-suggestions">
				<?php
				/**
				 * Hook: woocommerce_output_related_products
				 *
				 * @hooked woocommerce_output_related_products - 20
				 */
				do_action('woocommerce_output_related_products');
				?>

				<!-- AI-Powered Cross-sell Section -->
				<div class="ai-cross-sell-section" id="ai-cross-sell">
					<h3 class="section-title"><?php esc_html_e('Complete Your Look', 'wp-mastery-woocommerce-luxury'); ?></h3>
					<div class="cross-sell-grid" id="ai-complementary-items">
						<!-- Populated by AI cross-sell algorithm -->
					</div>
				</div>

				<!-- AI-Powered Upsell Section -->
				<div class="ai-upsell-section" id="ai-upsell">
					<h3 class="section-title"><?php esc_html_e('Upgrade Your Choice', 'wp-mastery-woocommerce-luxury'); ?></h3>
					<div class="upsell-grid" id="ai-premium-alternatives">
						<!-- Populated by AI upsell algorithm -->
					</div>
				</div>
			</div>
		</div>
	</div>

	<?php
	/**
	 * Hook: woocommerce_after_single_product
	 */
	do_action('woocommerce_after_single_product');
	?>
</div>

<!-- Real-time Inventory Tracking -->
<div class="inventory-tracker" id="real-time-inventory" style="display: none;">
	<input type="hidden" id="product-id" value="<?php echo esc_attr(get_the_ID()); ?>">
	<input type="hidden" id="style-category" value="">
	<input type="hidden" id="material-type" value="">
	<input type="hidden" id="stock-level" value="">
</div>

<?php get_footer('shop');
