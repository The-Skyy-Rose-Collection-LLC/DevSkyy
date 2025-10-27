<?php
/**
 * Template Name: Skyy Rose Collection - About Us
 *
 * The template for displaying the Skyy Rose Collection brand story and about page.
 * Enhanced with luxury styling and authentic brand narrative.
 *
 * @package WP_Mastery_WooCommerce_Luxury
 * @version 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
	exit;
}

get_header();
?>

<div class="skyy-rose-about-wrapper" id="luxury-brand-story">
	<!-- Skyy Rose Collection Brand Hero -->
	<div class="skyy-rose-brand-hero">
		<div class="hero-background">
			<div class="hero-overlay"></div>
			<div class="hero-pattern"></div>
		</div>
		<div class="container">
			<div class="brand-hero-content">
				<div class="brand-logo-showcase">
					<div class="skyy-rose-logo-large">
						<img src="<?php echo esc_url(get_template_directory_uri() . '/assets/images/skyy-rose-logo-luxury.svg'); ?>" 
							 alt="<?php esc_attr_e('Skyy Rose Collection', 'wp-mastery-woocommerce-luxury'); ?>" 
							 class="brand-logo-hero">
					</div>
				</div>
				<div class="brand-hero-text">
					<h1 class="brand-hero-title">
						<?php esc_html_e('Skyy Rose Collection', 'wp-mastery-woocommerce-luxury'); ?>
					</h1>
					<p class="brand-hero-tagline luxury-accent">
						<?php esc_html_e('Where Elegance Meets Innovation', 'wp-mastery-woocommerce-luxury'); ?>
					</p>
					<div class="brand-hero-description">
						<p><?php esc_html_e('Founded on the principles of timeless elegance and cutting-edge innovation, Skyy Rose Collection represents the pinnacle of luxury fashion. Our AI-powered curation ensures every piece tells a story of sophistication, quality, and personal style.', 'wp-mastery-woocommerce-luxury'); ?></p>
					</div>
				</div>
			</div>
		</div>
	</div>

	<div class="container">
		<!-- Brand Story Section -->
		<section class="brand-story-section">
			<div class="section-header">
				<h2 class="section-title"><?php esc_html_e('Our Story', 'wp-mastery-woocommerce-luxury'); ?></h2>
				<div class="luxury-divider"></div>
			</div>
			
			<div class="story-content-grid">
				<div class="story-text">
					<div class="story-chapter">
						<h3 class="chapter-title"><?php esc_html_e('The Beginning', 'wp-mastery-woocommerce-luxury'); ?></h3>
						<p><?php esc_html_e('Born from a vision to revolutionize luxury fashion, Skyy Rose Collection emerged as a beacon of innovation in the fashion industry. Our founder\'s passion for combining traditional craftsmanship with modern technology laid the foundation for what would become a transformative shopping experience.', 'wp-mastery-woocommerce-luxury'); ?></p>
					</div>
					
					<div class="story-chapter">
						<h3 class="chapter-title"><?php esc_html_e('Innovation Meets Tradition', 'wp-mastery-woocommerce-luxury'); ?></h3>
						<p><?php esc_html_e('We believe that true luxury lies in the perfect harmony between time-honored techniques and cutting-edge innovation. Our AI-powered platform doesn\'t just sell fashion—it curates experiences, understands preferences, and creates personal style journeys that evolve with you.', 'wp-mastery-woocommerce-luxury'); ?></p>
					</div>
					
					<div class="story-chapter">
						<h3 class="chapter-title"><?php esc_html_e('Sustainable Luxury', 'wp-mastery-woocommerce-luxury'); ?></h3>
						<p><?php esc_html_e('Sustainability is woven into the fabric of our brand. Every piece in our collection is carefully selected not just for its beauty and quality, but for its environmental and social impact. We partner with artisans and designers who share our commitment to responsible luxury.', 'wp-mastery-woocommerce-luxury'); ?></p>
					</div>
				</div>
				
				<div class="story-visuals">
					<div class="visual-showcase">
						<div class="showcase-item">
							<div class="showcase-image">
								<div class="image-placeholder luxury-gradient">
									<span class="placeholder-icon">🎨</span>
									<span class="placeholder-text"><?php esc_html_e('Artisan Craftsmanship', 'wp-mastery-woocommerce-luxury'); ?></span>
								</div>
							</div>
						</div>
						<div class="showcase-item">
							<div class="showcase-image">
								<div class="image-placeholder ai-gradient">
									<span class="placeholder-icon">🤖</span>
									<span class="placeholder-text"><?php esc_html_e('AI Innovation', 'wp-mastery-woocommerce-luxury'); ?></span>
								</div>
							</div>
						</div>
						<div class="showcase-item">
							<div class="showcase-image">
								<div class="image-placeholder sustainability-gradient">
									<span class="placeholder-icon">🌱</span>
									<span class="placeholder-text"><?php esc_html_e('Sustainable Practices', 'wp-mastery-woocommerce-luxury'); ?></span>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</section>

		<!-- Values Section -->
		<section class="brand-values-section">
			<div class="section-header">
				<h2 class="section-title"><?php esc_html_e('Our Values', 'wp-mastery-woocommerce-luxury'); ?></h2>
				<div class="luxury-divider"></div>
			</div>
			
			<div class="values-grid">
				<div class="value-card">
					<div class="value-icon">✨</div>
					<h3 class="value-title"><?php esc_html_e('Excellence', 'wp-mastery-woocommerce-luxury'); ?></h3>
					<p class="value-description"><?php esc_html_e('We pursue perfection in every detail, from the finest materials to the most innovative technology, ensuring an unparalleled luxury experience.', 'wp-mastery-woocommerce-luxury'); ?></p>
				</div>
				
				<div class="value-card">
					<div class="value-icon">🤝</div>
					<h3 class="value-title"><?php esc_html_e('Authenticity', 'wp-mastery-woocommerce-luxury'); ?></h3>
					<p class="value-description"><?php esc_html_e('Every piece in our collection is authentic, carefully curated, and backed by our guarantee of quality and provenance.', 'wp-mastery-woocommerce-luxury'); ?></p>
				</div>
				
				<div class="value-card">
					<div class="value-icon">🌍</div>
					<h3 class="value-title"><?php esc_html_e('Sustainability', 'wp-mastery-woocommerce-luxury'); ?></h3>
					<p class="value-description"><?php esc_html_e('We are committed to responsible luxury, supporting sustainable practices and ethical sourcing throughout our supply chain.', 'wp-mastery-woocommerce-luxury'); ?></p>
				</div>
				
				<div class="value-card">
					<div class="value-icon">🚀</div>
					<h3 class="value-title"><?php esc_html_e('Innovation', 'wp-mastery-woocommerce-luxury'); ?></h3>
					<p class="value-description"><?php esc_html_e('Our AI-powered platform represents the future of luxury shopping, offering personalized experiences that evolve with your style.', 'wp-mastery-woocommerce-luxury'); ?></p>
				</div>
			</div>
		</section>

		<!-- Technology Innovation Section -->
		<section class="technology-section">
			<div class="section-header">
				<h2 class="section-title"><?php esc_html_e('Revolutionary Technology', 'wp-mastery-woocommerce-luxury'); ?></h2>
				<div class="luxury-divider"></div>
			</div>
			
			<div class="technology-showcase">
				<div class="tech-feature">
					<div class="tech-icon">🧠</div>
					<h3 class="tech-title"><?php esc_html_e('AI Style Analysis', 'wp-mastery-woocommerce-luxury'); ?></h3>
					<p class="tech-description"><?php esc_html_e('Our proprietary AI algorithms analyze your style preferences, body type, and lifestyle to curate personalized collections that evolve with you.', 'wp-mastery-woocommerce-luxury'); ?></p>
				</div>
				
				<div class="tech-feature">
					<div class="tech-icon">📊</div>
					<h3 class="tech-title"><?php esc_html_e('Dynamic Pricing', 'wp-mastery-woocommerce-luxury'); ?></h3>
					<p class="tech-description"><?php esc_html_e('Real-time market analysis and customer behavior insights enable us to offer competitive pricing while maintaining the highest quality standards.', 'wp-mastery-woocommerce-luxury'); ?></p>
				</div>
				
				<div class="tech-feature">
					<div class="tech-icon">🎯</div>
					<h3 class="tech-title"><?php esc_html_e('Predictive Recommendations', 'wp-mastery-woocommerce-luxury'); ?></h3>
					<p class="tech-description"><?php esc_html_e('Machine learning models predict your future style preferences, ensuring you discover pieces you\'ll love before you even know you want them.', 'wp-mastery-woocommerce-luxury'); ?></p>
				</div>
			</div>
		</section>

		<!-- Team Section -->
		<section class="team-section">
			<div class="section-header">
				<h2 class="section-title"><?php esc_html_e('Meet Our Team', 'wp-mastery-woocommerce-luxury'); ?></h2>
				<div class="luxury-divider"></div>
			</div>
			
			<div class="team-grid">
				<div class="team-member">
					<div class="member-photo">
						<div class="photo-placeholder">
							<span class="member-initial">S</span>
						</div>
					</div>
					<h3 class="member-name"><?php esc_html_e('Skyy Rose', 'wp-mastery-woocommerce-luxury'); ?></h3>
					<p class="member-title"><?php esc_html_e('Founder & Creative Director', 'wp-mastery-woocommerce-luxury'); ?></p>
					<p class="member-bio"><?php esc_html_e('Visionary leader combining fashion expertise with technological innovation to create the future of luxury retail.', 'wp-mastery-woocommerce-luxury'); ?></p>
				</div>
				
				<div class="team-member">
					<div class="member-photo">
						<div class="photo-placeholder">
							<span class="member-initial">A</span>
						</div>
					</div>
					<h3 class="member-name"><?php esc_html_e('AI Development Team', 'wp-mastery-woocommerce-luxury'); ?></h3>
					<p class="member-title"><?php esc_html_e('Technology Innovation', 'wp-mastery-woocommerce-luxury'); ?></p>
					<p class="member-bio"><?php esc_html_e('Our world-class AI team develops cutting-edge algorithms that power personalized luxury shopping experiences.', 'wp-mastery-woocommerce-luxury'); ?></p>
				</div>
				
				<div class="team-member">
					<div class="member-photo">
						<div class="photo-placeholder">
							<span class="member-initial">C</span>
						</div>
					</div>
					<h3 class="member-name"><?php esc_html_e('Curation Specialists', 'wp-mastery-woocommerce-luxury'); ?></h3>
					<p class="member-title"><?php esc_html_e('Fashion Curation', 'wp-mastery-woocommerce-luxury'); ?></p>
					<p class="member-bio"><?php esc_html_e('Expert curators with decades of fashion industry experience, ensuring every piece meets our exacting standards.', 'wp-mastery-woocommerce-luxury'); ?></p>
				</div>
			</div>
		</section>

		<!-- Call to Action Section -->
		<section class="cta-section">
			<div class="cta-content">
				<h2 class="cta-title"><?php esc_html_e('Experience the Future of Luxury Fashion', 'wp-mastery-woocommerce-luxury'); ?></h2>
				<p class="cta-description"><?php esc_html_e('Join thousands of discerning customers who have discovered their perfect style through our AI-powered platform.', 'wp-mastery-woocommerce-luxury'); ?></p>
				<div class="cta-actions">
					<a href="<?php echo esc_url(wc_get_page_permalink('shop')); ?>" class="btn-luxury cta-primary">
						<?php esc_html_e('Explore Collection', 'wp-mastery-woocommerce-luxury'); ?>
					</a>
					<a href="<?php echo esc_url(wc_get_page_permalink('myaccount')); ?>" class="btn-luxury-outline cta-secondary">
						<?php esc_html_e('Create Account', 'wp-mastery-woocommerce-luxury'); ?>
					</a>
				</div>
			</div>
		</section>
	</div>

	<!-- Brand Analytics (Hidden) -->
	<div class="brand-analytics-tracker" id="brand-page-tracking" style="display: none;">
		<input type="hidden" id="page-type" value="about">
		<input type="hidden" id="brand-engagement-start" value="<?php echo esc_attr(time()); ?>">
		<input type="hidden" id="scroll-depth" value="0">
		<input type="hidden" id="section-views" value="">
	</div>
</div>

<?php
get_footer();
