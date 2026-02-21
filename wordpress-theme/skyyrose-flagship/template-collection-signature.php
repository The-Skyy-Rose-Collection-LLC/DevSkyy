<?php
/**
 * Template Name: Signature Collection
 * Template Post Type: page
 *
 * Timeless. Rose gold. Diamond excellence.
 * Landing page with AI model imagery and product showcase.
 *
 * @package SkyyRose_Flagship
 * @since 2.0.0
 */

get_header();
?>

<main id="primary" class="site-main collection-landing collection-signature">

	<!-- ========== HERO ========== -->
	<section class="cl-hero cl-hero-signature">
		<div class="cl-hero-bg"></div>
		<div class="cl-hero-content">
			<span class="cl-hero-label">Collection 03</span>

			<!-- Collection Logo — "The Skyy Rose Collection" Gold Script + Rose Mark -->
			<div class="cl-logo" aria-hidden="true">
				<?php
				$sig_logo = SKYYROSE_THEME_DIR . '/assets/images/brand/signature-collection-logo.png';
				if ( file_exists( $sig_logo ) ) :
				?>
					<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/brand/signature-collection-logo.png' ); ?>" alt="The Skyy Rose Collection" class="cl-logo-img" style="max-width:480px;height:auto">
				<?php else : ?>
					<svg viewBox="0 0 560 120" xmlns="http://www.w3.org/2000/svg" class="cl-logo-svg">
						<defs>
							<linearGradient id="sig-gold" x1="0%" y1="0%" x2="100%" y2="100%">
								<stop offset="0%" style="stop-color:#D4AF37"/>
								<stop offset="25%" style="stop-color:#E8C547"/>
								<stop offset="50%" style="stop-color:#D4AF37"/>
								<stop offset="75%" style="stop-color:#C49B30"/>
								<stop offset="100%" style="stop-color:#D4AF37"/>
							</linearGradient>
							<linearGradient id="sig-rosegold" x1="0%" y1="0%" x2="100%" y2="100%">
								<stop offset="0%" style="stop-color:#D8A7B1"/>
								<stop offset="50%" style="stop-color:#B76E79"/>
								<stop offset="100%" style="stop-color:#D8A7B1"/>
							</linearGradient>
							<filter id="sig-glow">
								<feGaussianBlur stdDeviation="1" result="blur"/>
								<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
							</filter>
						</defs>
						<!-- "THE" -->
						<text x="130" y="28" text-anchor="middle" fill="url(#sig-gold)" font-family="'Playfair Display', Georgia, serif" font-size="16" font-weight="600" letter-spacing="8" opacity="0.8">THE</text>
						<!-- "Skyy" in elegant script -->
						<text x="200" y="72" text-anchor="middle" fill="url(#sig-gold)" font-family="'Playfair Display', Georgia, serif" font-size="58" font-weight="700" font-style="italic" letter-spacing="3" filter="url(#sig-glow)">Skyy</text>
						<!-- Rose gold rose icon (between Skyy and Rose) -->
						<g transform="translate(345,32) scale(0.55)" opacity="0.9">
							<!-- Stylized rose petals -->
							<path d="M20 0 C25-8 35-5 30 5 C25 15 15 18 10 10 C5 2 15 8 20 0Z" fill="url(#sig-rosegold)"/>
							<path d="M25 5 C30-3 40 0 35 10 C30 20 20 22 15 15 C10 8 20 13 25 5Z" fill="url(#sig-rosegold)" opacity="0.8"/>
							<path d="M15 5 C20-3 10-5 5 2 C0 10 8 18 15 12 C22 6 10 13 15 5Z" fill="url(#sig-rosegold)" opacity="0.85"/>
							<circle cx="20" cy="10" r="4" fill="url(#sig-rosegold)" opacity="0.7"/>
							<!-- Stem and leaf -->
							<path d="M20 18 Q18 30 20 45" fill="none" stroke="url(#sig-rosegold)" stroke-width="2" stroke-linecap="round"/>
							<ellipse cx="28" cy="32" rx="8" ry="4" fill="url(#sig-rosegold)" opacity="0.6" transform="rotate(-30,28,32)"/>
							<ellipse cx="12" cy="38" rx="6" ry="3" fill="url(#sig-rosegold)" opacity="0.5" transform="rotate(25,12,38)"/>
						</g>
						<!-- "Rose" in elegant script -->
						<text x="420" y="72" text-anchor="middle" fill="url(#sig-gold)" font-family="'Playfair Display', Georgia, serif" font-size="58" font-weight="700" font-style="italic" letter-spacing="3" filter="url(#sig-glow)">Rose</text>
						<!-- "COLLECTION" -->
						<text x="420" y="105" text-anchor="middle" fill="url(#sig-gold)" font-family="'Playfair Display', Georgia, serif" font-size="20" font-weight="600" letter-spacing="10" opacity="0.7">COLLECTION</text>
					</svg>
				<?php endif; ?>
			</div>

			<h1 class="cl-hero-title sr-only">Signature</h1>
			<p class="cl-hero-tagline">Timeless. Rose Gold. Diamond Excellence.</p>
			<p class="cl-hero-desc">18K rose gold with GIA-certified diamonds. The pinnacle of our craft&mdash;heirloom pieces designed to last forever and backed by a lifetime warranty.</p>
			<div class="cl-hero-actions">
				<a href="#cl-products" class="btn btn-primary">Shop the Collection</a>
				<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>" class="btn btn-outline">Pre-Order</a>
			</div>
			<div class="cl-hero-price-hint">Starting at <strong>$1,299</strong></div>
		</div>
	</section>

	<!-- ========== AI MODEL LOOKBOOK ========== -->
	<section class="cl-lookbook">
		<div class="container">
			<div class="section-header text-center">
				<span class="section-subtitle" style="color:#B76E79">The Lookbook</span>
				<h2 class="section-title">Elegance Without Compromise</h2>
			</div>
			<div class="cl-lookbook-grid">
				<div class="cl-lookbook-item cl-lookbook-tall">
					<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/models/signature-model-1.jpg' ); ?>" alt="Model wearing Signature 18K rose gold diamond solitaire ring in elegant setting" loading="lazy">
					<div class="cl-lookbook-caption">
						<span class="cl-lookbook-piece">Rose Gold Solitaire Ring</span>
						<span class="cl-lookbook-price">$2,499</span>
					</div>
				</div>
				<div class="cl-lookbook-item">
					<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/models/signature-model-2.jpg' ); ?>" alt="Model wearing Signature diamond tennis bracelet with rose gold clasp" loading="lazy">
					<div class="cl-lookbook-caption">
						<span class="cl-lookbook-piece">Diamond Tennis Bracelet</span>
						<span class="cl-lookbook-price">$3,199</span>
					</div>
				</div>
				<div class="cl-lookbook-item">
					<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/models/signature-model-3.jpg' ); ?>" alt="Model wearing Signature rose gold pendant with diamond halo setting" loading="lazy">
					<div class="cl-lookbook-caption">
						<span class="cl-lookbook-piece">Halo Diamond Pendant</span>
						<span class="cl-lookbook-price">$1,899</span>
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- ========== COLLECTION STORY ========== -->
	<section class="cl-story">
		<div class="container">
			<div class="cl-story-grid">
				<div class="cl-story-content">
					<span class="section-subtitle" style="color:#B76E79">The Story</span>
					<h2>The Art of Forever</h2>
					<p>The Signature Collection is our masterwork. Every piece begins with 18-karat rose gold, alloyed to our proprietary warmth, and set with GIA-certified diamonds chosen for brilliance, not just size.</p>
					<p>These are pieces that get passed down. That spark conversations. That become part of your legacy. Backed by our lifetime warranty&mdash;because forever should mean forever.</p>
					<div class="cl-story-stats">
						<div class="cl-stat">
							<span class="cl-stat-value">18K</span>
							<span class="cl-stat-label">Rose Gold</span>
						</div>
						<div class="cl-stat">
							<span class="cl-stat-value">GIA</span>
							<span class="cl-stat-label">Certified Diamonds</span>
						</div>
						<div class="cl-stat">
							<span class="cl-stat-value">&infin;</span>
							<span class="cl-stat-label">Lifetime Warranty</span>
						</div>
					</div>
				</div>
				<div class="cl-story-image">
					<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/brand/signature-crafting.jpg' ); ?>" alt="Artisan setting GIA-certified diamond into 18K rose gold Signature ring" loading="lazy">
				</div>
			</div>
		</div>
	</section>

	<!-- ========== PRODUCTS ========== -->
	<section id="cl-products" class="cl-products">
		<div class="container">
			<div class="section-header text-center">
				<span class="section-subtitle" style="color:#B76E79">Shop</span>
				<h2 class="section-title">The Signature Pieces</h2>
				<p class="section-desc">GIA-certified. Lifetime warranty. Heirloom quality.</p>
			</div>

			<?php if ( class_exists( 'WooCommerce' ) ) :
				$args = array(
					'post_type'      => 'product',
					'posts_per_page' => 12,
					'tax_query'      => array( array(
						'taxonomy' => 'product_cat',
						'field'    => 'slug',
						'terms'    => 'signature-collection',
					) ),
				);
				$products = new WP_Query( $args );
				if ( $products->have_posts() ) : ?>
					<div class="cl-products-grid">
						<?php while ( $products->have_posts() ) : $products->the_post();
							wc_get_template_part( 'content', 'product' );
						endwhile; ?>
					</div>
					<?php wp_reset_postdata();
				else : ?>
					<div class="cl-products-grid">
						<?php
						$pieces = array(
							array( 'name' => 'Rose Gold Solitaire Ring', 'price' => '$2,499', 'badge' => 'Signature' ),
							array( 'name' => 'Diamond Tennis Bracelet', 'price' => '$3,199', 'badge' => 'Luxury' ),
							array( 'name' => 'Halo Diamond Pendant', 'price' => '$1,899', 'badge' => 'New' ),
							array( 'name' => 'Eternity Band', 'price' => '$2,799', 'badge' => 'Exclusive' ),
							array( 'name' => 'Diamond Stud Earrings', 'price' => '$1,299', 'badge' => 'Classic' ),
							array( 'name' => 'Rose Gold Chain Necklace', 'price' => '$1,599', 'badge' => 'New' ),
						);
						foreach ( $pieces as $piece ) : ?>
							<div class="cl-product-card">
								<div class="cl-product-badge"><?php echo esc_html( $piece['badge'] ); ?></div>
								<div class="cl-product-image">
									<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/placeholder.jpg' ); ?>" alt="<?php echo esc_attr( $piece['name'] ); ?>" loading="lazy">
								</div>
								<div class="cl-product-info">
									<h3 class="cl-product-name"><?php echo esc_html( $piece['name'] ); ?></h3>
									<span class="cl-product-price"><?php echo esc_html( $piece['price'] ); ?></span>
								</div>
								<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>" class="btn btn-outline cl-product-btn">Pre-Order</a>
							</div>
						<?php endforeach; ?>
					</div>
				<?php endif;
			endif; ?>
		</div>
	</section>

	<!-- ========== 3D EXPERIENCE CTA ========== -->
	<section class="cl-experience">
		<div class="container text-center">
			<span class="section-subtitle" style="color:#B76E79">3D Experience</span>
			<h2 class="cl-experience-title">Walk the Luxury Runway</h2>
			<p class="cl-experience-desc">Experience Signature pieces on a virtual runway with spotlights, paparazzi flashes, and interactive product exploration&mdash;all in immersive 3D.</p>
			<a href="<?php echo esc_url( home_url( '/explore-signature/' ) ); ?>" class="btn btn-primary btn-large">Launch 3D Experience</a>
		</div>
	</section>

	<!-- ========== CROSS-SELL ========== -->
	<section class="cl-crosssell">
		<div class="container text-center">
			<h2>Explore Other Collections</h2>
			<div class="cl-crosssell-links">
				<a href="<?php echo esc_url( home_url( '/black-rose-collection/' ) ); ?>" class="cl-crosssell-card cl-crosssell-black-rose">
					<span class="cl-crosssell-name">Black Rose</span>
					<span class="cl-crosssell-hint">Sterling Silver &amp; Onyx</span>
				</a>
				<a href="<?php echo esc_url( home_url( '/love-hurts-collection/' ) ); ?>" class="cl-crosssell-card cl-crosssell-love-hurts">
					<span class="cl-crosssell-name">Love Hurts</span>
					<span class="cl-crosssell-hint">Crimson &amp; Rose Gold</span>
				</a>
			</div>
		</div>
	</section>

</main>

<style>
/* === SIGNATURE SCOPED === */
.collection-signature{background:var(--off-white);color:var(--dark-gray)}

/* Hero */
.cl-hero-signature{position:relative;min-height:100vh;display:flex;align-items:center;justify-content:center;text-align:center;overflow:hidden}
.cl-hero-signature .cl-hero-bg{position:absolute;inset:0;background:linear-gradient(135deg,#B76E79 0%,#D4AF37 40%,#B76E79 100%)}
.cl-hero-signature .cl-hero-bg::after{content:'';position:absolute;inset:0;background:radial-gradient(ellipse at 50% 30%,rgba(255,255,255,.15) 0%,transparent 70%)}
.cl-hero-signature .cl-hero-content{position:relative;z-index:2;max-width:800px;padding:var(--space-xl)}
.cl-hero-signature .cl-hero-label{color:rgba(255,255,255,.8)}
.cl-hero-signature .cl-hero-title{font-family:var(--font-heading);font-size:clamp(3rem,5vw + 1rem,6rem);font-weight:var(--weight-bold);color:#fff;margin-bottom:var(--space-lg);line-height:1}
.cl-hero-signature .cl-hero-tagline{font-family:var(--font-accent);font-size:var(--text-xl);color:rgba(255,255,255,.9);margin-bottom:var(--space-lg)}
.cl-hero-signature .cl-hero-desc{font-size:var(--text-lg);color:rgba(255,255,255,.8);max-width:600px;margin:0 auto var(--space-2xl);line-height:1.7}
.cl-hero-signature .btn-primary{background:#fff;color:#B76E79}
.cl-hero-signature .btn-primary:hover{box-shadow:0 12px 24px rgba(0,0,0,.2),0 0 20px rgba(255,255,255,.3)}
.cl-hero-signature .btn-outline{border-color:#fff;color:#fff}
.cl-hero-signature .btn-outline:hover{background:#fff;color:#B76E79}
.cl-hero-signature .cl-hero-price-hint{color:rgba(255,255,255,.6)}
.cl-hero-signature .cl-hero-price-hint strong{color:#fff}

/* Lookbook — light */
.collection-signature .cl-lookbook{padding:var(--space-4xl) 0;background:#fff}
.collection-signature .cl-lookbook .section-title{color:var(--dark-gray)}
.collection-signature .cl-lookbook-price{color:#D4AF37}

/* Story — light */
.collection-signature .cl-story{padding:var(--space-4xl) 0;background:var(--off-white)}
.collection-signature .cl-story-content h2{color:var(--dark-gray)}
.collection-signature .cl-story-content p{color:var(--dark-gray);opacity:.8}
.collection-signature .cl-stat-value{color:#B76E79}
.collection-signature .cl-stat-label{color:var(--dark-gray);opacity:.6}
.collection-signature .cl-story-stats{border-top-color:rgba(183,110,121,.2)}
.collection-signature .cl-story-image img{border-radius:var(--radius-lg)}

/* Products — light */
.collection-signature .cl-products{padding:var(--space-4xl) 0;background:#fff}
.collection-signature .cl-products .section-title{color:var(--dark-gray)}
.collection-signature .section-desc{color:var(--dark-gray);opacity:.7}
.collection-signature .cl-product-card{background:#fff;border:1px solid rgba(183,110,121,.12)}
.collection-signature .cl-product-card:hover{box-shadow:0 16px 40px rgba(0,0,0,.08),0 0 20px rgba(183,110,121,.1);border-color:rgba(183,110,121,.3)}
.collection-signature .cl-product-badge{background:var(--gradient-rose-gold);color:#fff}
.collection-signature .cl-product-name{color:var(--dark-gray)}
.collection-signature .cl-product-price{color:#B76E79}
.collection-signature .cl-product-btn{border-color:#B76E79;color:#B76E79}
.collection-signature .cl-product-btn:hover{background:var(--gradient-rose-gold);border-color:#B76E79;color:#fff}

/* Experience */
.collection-signature .cl-experience{padding:var(--space-4xl) 0;background:linear-gradient(135deg,#B76E79,#D4AF37);color:#fff}
.collection-signature .cl-experience-title{color:#fff}
.collection-signature .cl-experience-desc{color:rgba(255,255,255,.85)}
.collection-signature .cl-experience .btn-primary{background:#fff;color:#B76E79}

/* Cross-sell — light */
.collection-signature .cl-crosssell{padding:var(--space-4xl) 0;background:var(--off-white)}
.collection-signature .cl-crosssell h2{color:var(--dark-gray);margin-bottom:var(--space-2xl)}
.collection-signature .cl-crosssell-card{border-color:rgba(0,0,0,.1)}
.collection-signature .cl-crosssell-name{color:var(--dark-gray)}
.collection-signature .cl-crosssell-hint{color:var(--dark-gray);opacity:.5}

@media(max-width:768px){
	.cl-hero-signature .cl-hero-title{font-size:clamp(2.5rem,4vw + 1rem,4rem)}
}
</style>

<?php get_footer(); ?>
