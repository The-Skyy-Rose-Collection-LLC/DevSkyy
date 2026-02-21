<?php
/**
 * SkyyRose Flagship — Luxury Homepage
 *
 * Full-screen hero, collection showcases with AI model imagery,
 * brand story, and conversion-focused layout.
 *
 * @package SkyyRose_Flagship
 * @since 2.0.0
 */

get_header();
?>

<main id="primary" class="site-main front-page">

	<!-- ========== HERO ========== -->
	<section class="fp-hero">
		<div class="fp-hero-bg">
			<div class="fp-hero-gradient"></div>
		</div>
		<div class="fp-hero-content">
			<span class="fp-hero-badge">Luxury Jewelry</span>
			<h1 class="fp-hero-title">Where Love<br>Meets Luxury</h1>
			<p class="fp-hero-subtitle">Handcrafted pieces that tell your story. Three collections, one vision&mdash;timeless elegance for the bold and the beautiful.</p>
			<div class="fp-hero-actions">
				<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>" class="btn btn-primary btn-large">Pre-Order Now</a>
				<a href="#fp-collections" class="btn btn-outline btn-large">Explore Collections</a>
			</div>
		</div>
		<div class="fp-hero-scroll">
			<span>Scroll</span>
			<div class="scroll-line"></div>
		</div>
	</section>

	<!-- ========== COLLECTION SHOWCASE ========== -->
	<section id="fp-collections" class="fp-collections">
		<div class="container">
			<div class="section-header text-center">
				<span class="section-subtitle text-rose-gold">The Collections</span>
				<h2 class="section-title">Three Stories, One Vision</h2>
				<p class="section-description">Each collection is a world of its own&mdash;explore the darkness, feel the passion, embrace the elegance.</p>
			</div>

			<!-- Black Rose -->
			<div class="fp-collection-row">
				<div class="fp-collection-image">
					<div class="fp-collection-img-wrapper collection-frame-black-rose">
						<img
							src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/models/black-rose-model-1.jpg' ); ?>"
							alt="AI model wearing Black Rose sterling silver gothic necklace against dark backdrop"
							loading="lazy"
						>
						<div class="fp-collection-img-accent"></div>
					</div>
				</div>
				<div class="fp-collection-info">
					<span class="fp-collection-number">01</span>
					<!-- Black Rose Logo Mini -->
					<div class="fp-collection-logo fp-logo-black-rose">
						<?php
						$br_logo_fp = SKYYROSE_THEME_DIR . '/assets/images/brand/black-rose-collection-logo.png';
						if ( file_exists( $br_logo_fp ) ) :
						?>
							<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/brand/black-rose-collection-logo.png' ); ?>" alt="" class="fp-cl-logo-img" width="180" height="auto">
						<?php else : ?>
							<svg viewBox="0 0 420 180" xmlns="http://www.w3.org/2000/svg" class="fp-cl-logo-svg" aria-hidden="true">
								<defs>
									<linearGradient id="fp-br-silver" x1="0%" y1="0%" x2="100%" y2="100%">
										<stop offset="0%" style="stop-color:#A0A0A0"/>
										<stop offset="50%" style="stop-color:#E8E8E8"/>
										<stop offset="100%" style="stop-color:#A0A0A0"/>
									</linearGradient>
								</defs>
								<g transform="translate(210,58)">
									<polygon points="0,-48 11,-15 46,-15 18,6 29,39 0,20 -29,39 -18,6 -46,-15 -11,-15" fill="rgba(255,255,255,0.05)" stroke="url(#fp-br-silver)" stroke-width="1.5"/>
									<g transform="translate(0,-5)">
										<path d="M0-12 C6-18 14-12 10-4 C6 4 -6 4 -10-4 C-14-12 -6-18 0-12Z" fill="#1a1a1a" stroke="#333" stroke-width="0.5"/>
										<circle cx="0" cy="-2" r="2.5" fill="#1a1a1a" stroke="#333" stroke-width="0.3"/>
									</g>
								</g>
								<text x="210" y="148" text-anchor="middle" fill="url(#fp-br-silver)" font-family="'UnifrakturMaguntia', serif" font-size="40" letter-spacing="4">Black Rose</text>
							</svg>
						<?php endif; ?>
					</div>
					<h3 class="fp-collection-name">Black Rose</h3>
					<p class="fp-collection-tagline">Dark Elegance. Sterling Silver. Gothic Luxury.</p>
					<p class="fp-collection-desc">Sterling silver pieces with onyx and obsidian stones. For those who find beauty in the shadows&mdash;cathedral-inspired designs that command every room.</p>
					<div class="fp-collection-details">
						<span class="detail-chip">Sterling Silver</span>
						<span class="detail-chip">Onyx &amp; Obsidian</span>
						<span class="detail-chip">Limited Edition</span>
					</div>
					<a href="<?php echo esc_url( home_url( '/black-rose-collection/' ) ); ?>" class="btn btn-outline fp-collection-btn" style="--accent: #C0C0C0;">Explore Black Rose</a>
				</div>
			</div>

			<!-- Love Hurts -->
			<div class="fp-collection-row fp-collection-row-reverse">
				<div class="fp-collection-image">
					<div class="fp-collection-img-wrapper collection-frame-love-hurts">
						<img
							src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/models/love-hurts-model-1.jpg' ); ?>"
							alt="AI model wearing Love Hurts crimson heart pendant against romantic dark setting"
							loading="lazy"
						>
						<div class="fp-collection-img-accent"></div>
					</div>
				</div>
				<div class="fp-collection-info">
					<span class="fp-collection-number">02</span>
					<!-- Love Hurts Logo Mini -->
					<div class="fp-collection-logo fp-logo-love-hurts">
						<?php
						$lh_logo_fp = SKYYROSE_THEME_DIR . '/assets/images/brand/love-hurts-collection-logo.png';
						if ( file_exists( $lh_logo_fp ) ) :
						?>
							<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/brand/love-hurts-collection-logo.png' ); ?>" alt="" class="fp-cl-logo-img" width="180" height="auto">
						<?php else : ?>
							<svg viewBox="0 0 240 80" xmlns="http://www.w3.org/2000/svg" class="fp-cl-logo-svg" aria-hidden="true">
								<defs>
									<linearGradient id="fp-lh-grad" x1="0%" y1="0%" x2="100%" y2="100%">
										<stop offset="0%" style="stop-color:#DC143C"/>
										<stop offset="50%" style="stop-color:#FF4D6A"/>
										<stop offset="100%" style="stop-color:#DC143C"/>
									</linearGradient>
								</defs>
								<g transform="translate(40,28)">
									<path d="M0 10 C0-8 -20-10 -20 4 C-20 18 0 30 0 36 C0 30 20 18 20 4 C20-10 0-8 0 10Z" fill="url(#fp-lh-grad)" opacity="0.9"/>
									<path d="M-1-5 L2 4 L-2 10 L1 18" fill="none" stroke="#1a0505" stroke-width="1.8" stroke-linecap="round"/>
								</g>
								<text x="120" y="55" text-anchor="middle" fill="url(#fp-lh-grad)" font-family="'Playfair Display', serif" font-size="28" font-weight="700" font-style="italic">Love Hurts</text>
							</svg>
						<?php endif; ?>
					</div>
					<h3 class="fp-collection-name">Love Hurts</h3>
					<p class="fp-collection-tagline">Passionate. Crimson Fire. Romantic Edge.</p>
					<p class="fp-collection-desc">Bold crimson and rose gold pieces with heart motifs and thorns. Inspired by the beauty and pain of love&mdash;for hearts that burn bright.</p>
					<div class="fp-collection-details">
						<span class="detail-chip">Rose Gold</span>
						<span class="detail-chip">Crimson Stones</span>
						<span class="detail-chip">Heart Motifs</span>
					</div>
					<a href="<?php echo esc_url( home_url( '/love-hurts-collection/' ) ); ?>" class="btn btn-outline fp-collection-btn" style="--accent: #DC143C;">Explore Love Hurts</a>
				</div>
			</div>

			<!-- Signature -->
			<div class="fp-collection-row">
				<div class="fp-collection-image">
					<div class="fp-collection-img-wrapper collection-frame-signature">
						<img
							src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/models/signature-model-1.jpg' ); ?>"
							alt="AI model wearing Signature rose gold diamond ring in luxury setting"
							loading="lazy"
						>
						<div class="fp-collection-img-accent"></div>
					</div>
				</div>
				<div class="fp-collection-info">
					<span class="fp-collection-number">03</span>
					<!-- Signature Logo Mini -->
					<div class="fp-collection-logo fp-logo-signature">
						<?php
						$sig_logo_fp = SKYYROSE_THEME_DIR . '/assets/images/brand/signature-collection-logo.png';
						if ( file_exists( $sig_logo_fp ) ) :
						?>
							<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/brand/signature-collection-logo.png' ); ?>" alt="" class="fp-cl-logo-img" width="220" height="auto">
						<?php else : ?>
							<svg viewBox="0 0 320 60" xmlns="http://www.w3.org/2000/svg" class="fp-cl-logo-svg" aria-hidden="true">
								<defs>
									<linearGradient id="fp-sig-gold" x1="0%" y1="0%" x2="100%" y2="100%">
										<stop offset="0%" style="stop-color:#D4AF37"/>
										<stop offset="50%" style="stop-color:#E8C547"/>
										<stop offset="100%" style="stop-color:#D4AF37"/>
									</linearGradient>
									<linearGradient id="fp-sig-rg" x1="0%" y1="0%" x2="100%" y2="100%">
										<stop offset="0%" style="stop-color:#D8A7B1"/>
										<stop offset="100%" style="stop-color:#B76E79"/>
									</linearGradient>
								</defs>
								<text x="70" y="14" text-anchor="middle" fill="url(#fp-sig-gold)" font-family="'Playfair Display', serif" font-size="9" font-weight="600" letter-spacing="5" opacity="0.8">THE</text>
								<text x="110" y="40" text-anchor="middle" fill="url(#fp-sig-gold)" font-family="'Playfair Display', serif" font-size="32" font-weight="700" font-style="italic">Skyy</text>
								<g transform="translate(192,14) scale(0.3)">
									<path d="M20 0 C26-9 38-6 32 6 C26 18 14 20 8 12 C2 4 14 9 20 0Z" fill="url(#fp-sig-rg)"/>
									<circle cx="20" cy="10" r="4" fill="url(#fp-sig-rg)" opacity="0.7"/>
								</g>
								<text x="240" y="40" text-anchor="middle" fill="url(#fp-sig-gold)" font-family="'Playfair Display', serif" font-size="32" font-weight="700" font-style="italic">Rose</text>
							</svg>
						<?php endif; ?>
					</div>
					<h3 class="fp-collection-name">Signature</h3>
					<p class="fp-collection-tagline">Timeless. Rose Gold. Diamond Excellence.</p>
					<p class="fp-collection-desc">18K rose gold with GIA-certified diamonds. The pinnacle of our craft&mdash;timeless pieces that become family heirlooms. Backed by a lifetime warranty.</p>
					<div class="fp-collection-details">
						<span class="detail-chip">18K Rose Gold</span>
						<span class="detail-chip">GIA Diamonds</span>
						<span class="detail-chip">Lifetime Warranty</span>
					</div>
					<a href="<?php echo esc_url( home_url( '/signature-collection/' ) ); ?>" class="btn btn-outline fp-collection-btn" style="--accent: #B76E79;">Explore Signature</a>
				</div>
			</div>
		</div>
	</section>

	<!-- ========== BRAND STORY ========== -->
	<section class="fp-story">
		<div class="container">
			<div class="fp-story-grid">
				<div class="fp-story-content">
					<span class="section-subtitle text-rose-gold">Our Story</span>
					<h2 class="section-title" style="text-align: left;">Crafted With Passion,<br>Worn With Pride</h2>
					<p>Every SkyyRose piece begins as a vision&mdash;a spark of emotion translated into precious metals and gemstones. We don&rsquo;t follow trends; we create legacies.</p>
					<p>From the first sketch to the final polish, our artisans pour their expertise into every detail. The result? Jewelry that doesn&rsquo;t just accessorize&mdash;it transforms.</p>
					<div class="fp-story-stats">
						<div class="fp-stat">
							<span class="fp-stat-number">3</span>
							<span class="fp-stat-label">Exclusive Collections</span>
						</div>
						<div class="fp-stat">
							<span class="fp-stat-number">18K</span>
							<span class="fp-stat-label">Rose Gold Standard</span>
						</div>
						<div class="fp-stat">
							<span class="fp-stat-number">GIA</span>
							<span class="fp-stat-label">Certified Diamonds</span>
						</div>
					</div>
					<a href="<?php echo esc_url( home_url( '/about/' ) ); ?>" class="btn btn-outline">Read Our Story</a>
				</div>
				<div class="fp-story-visual">
					<div class="fp-story-image-stack">
						<img
							src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/brand/craftsmanship-1.jpg' ); ?>"
							alt="SkyyRose artisan crafting jewelry at workbench"
							class="fp-story-img fp-story-img-1"
							loading="lazy"
						>
						<img
							src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/brand/craftsmanship-2.jpg' ); ?>"
							alt="Close-up of rose gold jewelry with diamond setting"
							class="fp-story-img fp-story-img-2"
							loading="lazy"
						>
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- ========== PRE-ORDER CTA ========== -->
	<section class="fp-cta">
		<div class="fp-cta-bg"></div>
		<div class="container">
			<div class="fp-cta-content text-center">
				<span class="section-subtitle" style="color: rgba(255,255,255,0.7);">Limited Availability</span>
				<h2 class="fp-cta-title">Be the First to Own</h2>
				<p class="fp-cta-subtitle">Pre-order your favorite pieces from all three collections. Early supporters receive exclusive pricing and first access.</p>
				<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>" class="btn btn-primary btn-large">Pre-Order All Collections</a>
			</div>
		</div>
	</section>

	<!-- ========== TRUST BAR ========== -->
	<section class="fp-trust">
		<div class="container">
			<div class="fp-trust-grid">
				<div class="fp-trust-item">
					<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
					<h4>Secure Checkout</h4>
					<p>256-bit SSL encryption on every transaction</p>
				</div>
				<div class="fp-trust-item">
					<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
					<h4>Free Shipping</h4>
					<p>Complimentary shipping on orders over $500</p>
				</div>
				<div class="fp-trust-item">
					<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
					<h4>Lifetime Warranty</h4>
					<p>Every Signature piece is guaranteed for life</p>
				</div>
				<div class="fp-trust-item">
					<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="20 12 20 22 4 22 4 12"/><rect x="2" y="7" width="20" height="5"/><line x1="12" y1="22" x2="12" y2="7"/><path d="M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7z"/><path d="M12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7z"/></svg>
					<h4>Luxury Packaging</h4>
					<p>Arrives in our signature rose gold gift box</p>
				</div>
			</div>
		</div>
	</section>

</main>

<?php
get_footer();
