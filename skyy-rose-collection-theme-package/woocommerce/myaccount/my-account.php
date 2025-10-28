<?php
/**
 * My Account page
 *
 * This template can be overridden by copying it to yourtheme/woocommerce/myaccount/my-account.php.
 * Enhanced with Skyy Rose Collection luxury styling and AI-powered personalization.
 *
 * @package WP_Mastery_WooCommerce_Luxury
 * @version 3.5.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
	exit;
}

do_action('woocommerce_before_account_navigation');
?>

<div class="skyy-rose-account-wrapper" id="luxury-account-experience">
	<!-- Skyy Rose Collection Account Header -->
	<div class="skyy-rose-account-header">
		<div class="container">
			<div class="account-brand-section">
				<div class="brand-logo-area">
					<div class="skyy-rose-logo">
						<img src="<?php echo esc_url(get_template_directory_uri() . '/assets/images/skyy-rose-logo-luxury.svg'); ?>" 
							 alt="<?php esc_attr_e('Skyy Rose Collection', 'wp-mastery-woocommerce-luxury'); ?>" 
							 class="brand-logo">
					</div>
					<div class="brand-welcome">
						<h1 class="account-title">
							<?php 
							$current_user = wp_get_current_user();
							if ($current_user->exists()) {
								printf(
									esc_html__('Welcome back, %s', 'wp-mastery-woocommerce-luxury'),
									esc_html($current_user->display_name)
								);
							} else {
								esc_html_e('My Account', 'wp-mastery-woocommerce-luxury');
							}
							?>
						</h1>
						<p class="brand-subtitle luxury-accent"><?php esc_html_e('Your Personal Style Sanctuary', 'wp-mastery-woocommerce-luxury'); ?></p>
					</div>
				</div>
				
				<!-- AI-Powered Account Insights -->
				<div class="account-ai-insights" id="account-intelligence-panel">
					<div class="ai-insight-card">
						<div class="insight-icon">👗</div>
						<div class="insight-content">
							<h4 class="insight-title"><?php esc_html_e('Style Profile', 'wp-mastery-woocommerce-luxury'); ?></h4>
							<p class="insight-text" id="customer-style-profile"><?php esc_html_e('Analyzing preferences...', 'wp-mastery-woocommerce-luxury'); ?></p>
						</div>
					</div>
					<div class="ai-insight-card">
						<div class="insight-icon">⭐</div>
						<div class="insight-content">
							<h4 class="insight-title"><?php esc_html_e('VIP Status', 'wp-mastery-woocommerce-luxury'); ?></h4>
							<p class="insight-text" id="customer-vip-status"><?php esc_html_e('Calculating tier...', 'wp-mastery-woocommerce-luxury'); ?></p>
						</div>
					</div>
					<div class="ai-insight-card">
						<div class="insight-icon">🎯</div>
						<div class="insight-content">
							<h4 class="insight-title"><?php esc_html_e('Recommendations', 'wp-mastery-woocommerce-luxury'); ?></h4>
							<p class="insight-text" id="personalized-suggestions"><?php esc_html_e('Curating for you...', 'wp-mastery-woocommerce-luxury'); ?></p>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>

	<div class="container">
		<div class="luxury-account-layout">
			<!-- Account Navigation Sidebar -->
			<div class="account-navigation-section">
				<div class="luxury-account-nav-wrapper">
					<h3 class="nav-title"><?php esc_html_e('Account Menu', 'wp-mastery-woocommerce-luxury'); ?></h3>
					
					<nav class="woocommerce-MyAccount-navigation luxury-account-navigation">
						<ul class="luxury-nav-menu">
							<?php foreach (wc_get_account_menu_items() as $endpoint => $label) : ?>
								<li class="<?php echo wc_get_account_menu_item_classes($endpoint); ?> luxury-nav-item">
									<a href="<?php echo esc_url(wc_get_account_endpoint_url($endpoint)); ?>" class="luxury-nav-link">
										<span class="nav-icon"><?php echo wp_mastery_woocommerce_luxury_get_account_icon($endpoint); ?></span>
										<span class="nav-label"><?php echo esc_html($label); ?></span>
										<span class="nav-arrow">→</span>
									</a>
								</li>
							<?php endforeach; ?>
						</ul>
					</nav>

					<!-- AI-Powered Quick Actions -->
					<div class="quick-actions-section">
						<h4 class="quick-actions-title"><?php esc_html_e('Quick Actions', 'wp-mastery-woocommerce-luxury'); ?></h4>
						<div class="quick-actions-grid">
							<a href="<?php echo esc_url(wc_get_page_permalink('shop')); ?>" class="quick-action-btn">
								<span class="action-icon">🛍️</span>
								<span class="action-text"><?php esc_html_e('Continue Shopping', 'wp-mastery-woocommerce-luxury'); ?></span>
							</a>
							<a href="<?php echo esc_url(wc_get_account_endpoint_url('orders')); ?>" class="quick-action-btn">
								<span class="action-icon">📦</span>
								<span class="action-text"><?php esc_html_e('Track Orders', 'wp-mastery-woocommerce-luxury'); ?></span>
							</a>
							<a href="#" class="quick-action-btn" id="personal-stylist-btn">
								<span class="action-icon">✨</span>
								<span class="action-text"><?php esc_html_e('Personal Stylist', 'wp-mastery-woocommerce-luxury'); ?></span>
							</a>
							<a href="#" class="quick-action-btn" id="wishlist-btn">
								<span class="action-icon">💝</span>
								<span class="action-text"><?php esc_html_e('My Wishlist', 'wp-mastery-woocommerce-luxury'); ?></span>
							</a>
						</div>
					</div>

					<!-- VIP Membership Status -->
					<div class="vip-status-section" id="vip-membership-panel">
						<h4 class="vip-title"><?php esc_html_e('VIP Membership', 'wp-mastery-woocommerce-luxury'); ?></h4>
						<div class="vip-status-card" id="vip-status-display">
							<!-- Populated by AI customer analysis -->
						</div>
					</div>
				</div>
			</div>

			<!-- Account Content Area -->
			<div class="account-content-section">
				<div class="woocommerce-MyAccount-content luxury-account-content">
					<?php
					/**
					 * My Account content.
					 *
					 * @since 2.6.0
					 */
					do_action('woocommerce_account_content');
					?>
				</div>

				<!-- AI-Powered Personalized Recommendations -->
				<div class="account-recommendations-section" id="personalized-recommendations">
					<h3 class="recommendations-title"><?php esc_html_e('Curated Just for You', 'wp-mastery-woocommerce-luxury'); ?></h3>
					<div class="recommendations-grid" id="ai-personal-recommendations">
						<!-- Populated by AI recommendation engine -->
					</div>
				</div>

				<!-- Style Journey Timeline -->
				<div class="style-journey-section" id="customer-style-journey">
					<h3 class="journey-title"><?php esc_html_e('Your Style Journey', 'wp-mastery-woocommerce-luxury'); ?></h3>
					<div class="journey-timeline" id="style-timeline">
						<!-- Populated by AI style analysis -->
					</div>
				</div>

				<!-- Exclusive Offers -->
				<div class="exclusive-offers-section" id="member-exclusive-offers">
					<h3 class="offers-title"><?php esc_html_e('Exclusive Member Offers', 'wp-mastery-woocommerce-luxury'); ?></h3>
					<div class="offers-grid" id="personalized-offers-grid">
						<!-- Populated by AI marketing engine -->
					</div>
				</div>
			</div>
		</div>
	</div>

	<!-- AI Account Analytics (Hidden) -->
	<div class="account-analytics-tracker" id="account-behavior-tracking" style="display: none;">
		<input type="hidden" id="customer-id" value="<?php echo esc_attr(get_current_user_id()); ?>">
		<input type="hidden" id="account-session-start" value="<?php echo esc_attr(time()); ?>">
		<input type="hidden" id="customer-lifetime-value" value="">
		<input type="hidden" id="style-preferences" value="">
		<input type="hidden" id="purchase-patterns" value="">
	</div>
</div>

<?php do_action('woocommerce_after_account_navigation'); ?>
