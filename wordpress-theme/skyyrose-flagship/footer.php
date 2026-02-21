<?php
/**
 * SkyyRose Flagship — Luxury Footer
 *
 * @package SkyyRose_Flagship
 * @since 2.0.0
 */
?>

	</div><!-- #content -->

	<footer id="colophon" class="site-footer">
		<div class="footer-main">
			<div class="footer-container">

				<!-- Brand Column -->
				<div class="footer-col footer-brand">
					<a href="<?php echo esc_url( home_url( '/' ) ); ?>" class="footer-logo" rel="home">
						<?php bloginfo( 'name' ); ?>
					</a>
					<p class="footer-tagline">Where Love Meets Luxury&trade;</p>
					<p class="footer-description">Handcrafted luxury jewelry for those who dare to stand out. Each piece tells a story of passion, artistry, and timeless elegance.</p>
					<div class="footer-social">
						<a href="https://instagram.com/skyyrose" class="social-link" aria-label="Instagram" target="_blank" rel="noopener">
							<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/></svg>
						</a>
						<a href="https://tiktok.com/@skyyrose" class="social-link" aria-label="TikTok" target="_blank" rel="noopener">
							<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-2.88 2.5 2.89 2.89 0 0 1-2.89-2.89 2.89 2.89 0 0 1 2.89-2.89c.28 0 .54.04.79.1v-3.5a6.37 6.37 0 0 0-.79-.05A6.34 6.34 0 0 0 3.15 15a6.34 6.34 0 0 0 6.34 6.34 6.34 6.34 0 0 0 6.34-6.34V8.71a8.32 8.32 0 0 0 4.76 1.49V6.75a4.83 4.83 0 0 1-1-.06z"/></svg>
						</a>
						<a href="https://pinterest.com/skyyrose" class="social-link" aria-label="Pinterest" target="_blank" rel="noopener">
							<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M8 12a4 4 0 1 1 8 0c0 2-1 4-2 6"/><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"/><path d="M10 16l1.5-6"/></svg>
						</a>
					</div>
				</div>

				<!-- Collections Column -->
				<div class="footer-col">
					<h3 class="footer-heading">Collections</h3>
					<ul class="footer-links">
						<li><a href="<?php echo esc_url( home_url( '/black-rose-collection/' ) ); ?>">Black Rose</a></li>
						<li><a href="<?php echo esc_url( home_url( '/love-hurts-collection/' ) ); ?>">Love Hurts</a></li>
						<li><a href="<?php echo esc_url( home_url( '/signature-collection/' ) ); ?>">Signature</a></li>
						<li><a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>">Pre-Order</a></li>
					</ul>
				</div>

				<!-- Customer Care Column -->
				<div class="footer-col">
					<h3 class="footer-heading">Customer Care</h3>
					<ul class="footer-links">
						<li><a href="<?php echo esc_url( home_url( '/contact/' ) ); ?>">Contact Us</a></li>
						<li><a href="<?php echo esc_url( home_url( '/shipping-returns/' ) ); ?>">Shipping &amp; Returns</a></li>
						<li><a href="<?php echo esc_url( home_url( '/size-guide/' ) ); ?>">Size Guide</a></li>
						<li><a href="<?php echo esc_url( home_url( '/care-instructions/' ) ); ?>">Jewelry Care</a></li>
						<li><a href="<?php echo esc_url( home_url( '/faq/' ) ); ?>">FAQ</a></li>
					</ul>
				</div>

				<!-- About Column -->
				<div class="footer-col">
					<h3 class="footer-heading">About</h3>
					<ul class="footer-links">
						<li><a href="<?php echo esc_url( home_url( '/about/' ) ); ?>">Our Story</a></li>
						<li><a href="<?php echo esc_url( home_url( '/craftsmanship/' ) ); ?>">Craftsmanship</a></li>
						<li><a href="<?php echo esc_url( home_url( '/privacy-policy/' ) ); ?>">Privacy Policy</a></li>
						<li><a href="<?php echo esc_url( home_url( '/terms/' ) ); ?>">Terms of Service</a></li>
					</ul>
				</div>

			</div>
		</div>

		<!-- Bottom Bar -->
		<div class="footer-bottom">
			<div class="footer-container">
				<div class="copyright">
					<?php
					printf(
						esc_html__( '&copy; %1$s %2$s. All rights reserved.', 'skyyrose-flagship' ),
						esc_html( gmdate( 'Y' ) ),
						esc_html( get_bloginfo( 'name' ) )
					);
					?>
				</div>
				<div class="footer-trust">
					<span class="trust-badge">Secure Checkout</span>
					<span class="trust-badge">Lifetime Warranty</span>
					<span class="trust-badge">Free Returns</span>
				</div>
			</div>
		</div>
	</footer>
</div><!-- #page -->

<?php wp_footer(); ?>

</body>
</html>
