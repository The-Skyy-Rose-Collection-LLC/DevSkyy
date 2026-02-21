<?php
/**
 * Template Name: Love Hurts Collection
 * Template Post Type: page
 *
 * Passionate. Crimson fire. Romantic edge.
 * Landing page with AI model imagery and product showcase.
 *
 * @package SkyyRose_Flagship
 * @since 2.0.0
 */

get_header();
?>

<main id="primary" class="site-main collection-landing collection-love-hurts">

	<!-- ========== HERO ========== -->
	<section class="cl-hero cl-hero-love-hurts">
		<div class="cl-hero-bg"><div class="cl-hero-particles"></div></div>
		<div class="cl-hero-content">
			<span class="cl-hero-label">Collection 02</span>

			<!-- Collection Logo — Cracked Heart with Thorns & Roses -->
			<div class="cl-logo" aria-hidden="true">
				<svg viewBox="0 0 420 160" xmlns="http://www.w3.org/2000/svg" class="cl-logo-svg">
					<defs>
						<linearGradient id="lh-grad" x1="0%" y1="0%" x2="100%" y2="100%">
							<stop offset="0%" style="stop-color:#DC143C"/>
							<stop offset="50%" style="stop-color:#FF4D6A"/>
							<stop offset="100%" style="stop-color:#DC143C"/>
						</linearGradient>
						<linearGradient id="lh-rose-grad" x1="0%" y1="0%" x2="100%" y2="100%">
							<stop offset="0%" style="stop-color:#E84060"/>
							<stop offset="100%" style="stop-color:#B01030"/>
						</linearGradient>
						<filter id="lh-glow">
							<feGaussianBlur stdDeviation="2" result="blur"/>
							<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
						</filter>
					</defs>

					<!-- Cracked Heart -->
					<g transform="translate(210,45)" filter="url(#lh-glow)">
						<!-- Heart shape -->
						<path d="M0 15 C0-10 -30-15 -30 5 C-30 25 0 45 0 55 C0 45 30 25 30 5 C30-15 0-10 0 15Z" fill="url(#lh-grad)" opacity="0.9"/>
						<!-- Crack line -->
						<path d="M-2-8 L3 5 L-3 15 L2 28 L-1 40" fill="none" stroke="#1a0505" stroke-width="2.5" stroke-linecap="round"/>
						<path d="M-2-8 L3 5 L-3 15 L2 28 L-1 40" fill="none" stroke="rgba(255,255,255,0.3)" stroke-width="1" stroke-linecap="round"/>
					</g>

					<!-- Thorn vine wrapping heart -->
					<g transform="translate(210,45)" opacity="0.8">
						<path d="M-35 10 Q-25-5 -10-10 Q5-15 15-5 Q25 5 35 15" fill="none" stroke="#5a2020" stroke-width="2.5" stroke-linecap="round"/>
						<!-- Thorns -->
						<polygon points="-22,2 -20,-4 -18,2" fill="#5a2020"/>
						<polygon points="-5,-12 -3,-18 -1,-12" fill="#5a2020"/>
						<polygon points="12,-4 14,-10 16,-4" fill="#5a2020"/>
						<polygon points="28,10 30,4 32,10" fill="#5a2020"/>
					</g>

					<!-- Roses blooming from top of heart -->
					<g transform="translate(195,12)" opacity="0.85">
						<!-- Rose 1 (left) -->
						<circle cx="0" cy="0" r="8" fill="#E84060"/>
						<path d="M-4-2 Q0-8 4-2 Q8 2 4 6 Q0 10 -4 6 Q-8 2 -4-2" fill="#D03050" opacity="0.8"/>
						<circle cx="0" cy="0" r="3" fill="#C02040"/>
						<!-- Leaf -->
						<ellipse cx="-10" cy="5" rx="6" ry="3" fill="#2d6b2d" transform="rotate(-30,-10,5)"/>
					</g>
					<g transform="translate(215,5)" opacity="0.9">
						<!-- Rose 2 (center, larger) -->
						<circle cx="0" cy="0" r="10" fill="#DC143C"/>
						<path d="M-5-3 Q0-10 5-3 Q10 3 5 8 Q0 13 -5 8 Q-10 3 -5-3" fill="#C01030" opacity="0.8"/>
						<circle cx="0" cy="0" r="4" fill="#A01025"/>
						<!-- Leaf -->
						<ellipse cx="12" cy="4" rx="6" ry="3" fill="#2d6b2d" transform="rotate(25,12,4)"/>
					</g>
					<g transform="translate(232,15)" opacity="0.8">
						<!-- Rose 3 (right, small) -->
						<circle cx="0" cy="0" r="7" fill="#E84060"/>
						<path d="M-3-2 Q0-7 3-2 Q6 2 3 5 Q0 8 -3 5 Q-6 2 -3-2" fill="#D03050" opacity="0.8"/>
						<circle cx="0" cy="0" r="2.5" fill="#C02040"/>
					</g>

					<!-- "Love Hurts" script text — dripping crimson style -->
					<text x="210" y="125" text-anchor="middle" fill="url(#lh-grad)" font-family="'Playfair Display', Georgia, serif" font-size="44" font-weight="700" font-style="italic" letter-spacing="2" filter="url(#lh-glow)">Love Hurts</text>

					<!-- Drip accents below text -->
					<g opacity="0.5">
						<path d="M148 130 Q148 140 150 148 Q152 140 152 130" fill="#DC143C"/>
						<path d="M238 132 Q238 144 240 155 Q242 144 242 132" fill="#DC143C"/>
						<path d="M275 130 Q275 138 277 143 Q279 138 279 130" fill="#DC143C"/>
						<circle cx="150" cy="150" r="2" fill="#DC143C" opacity="0.6"/>
						<circle cx="240" cy="157" r="2.5" fill="#DC143C" opacity="0.6"/>
						<circle cx="277" cy="145" r="1.8" fill="#DC143C" opacity="0.6"/>
					</g>

					<!-- Splash accents (left and right) -->
					<g opacity="0.4">
						<circle cx="120" cy="55" r="2" fill="#DC143C"/>
						<circle cx="115" cy="48" r="1.5" fill="#DC143C"/>
						<circle cx="125" cy="62" r="1" fill="#DC143C"/>
						<circle cx="300" cy="50" r="2" fill="#DC143C"/>
						<circle cx="305" cy="58" r="1.5" fill="#DC143C"/>
						<circle cx="295" cy="42" r="1" fill="#DC143C"/>
					</g>
				</svg>
			</div>

			<h1 class="cl-hero-title sr-only">Love Hurts</h1>
			<p class="cl-hero-tagline">Passionate. Crimson Fire. Romantic Edge.</p>
			<p class="cl-hero-desc">Bold crimson and rose gold pieces inspired by the beauty and pain of love. Heart motifs, thorns, and fire&mdash;for hearts that burn bright.</p>
			<div class="cl-hero-actions">
				<a href="#cl-products" class="btn btn-primary">Shop the Collection</a>
				<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>" class="btn btn-outline">Pre-Order</a>
			</div>
			<div class="cl-hero-price-hint">Starting at <strong>$1,499</strong></div>
		</div>
	</section>

	<!-- ========== AI MODEL LOOKBOOK ========== -->
	<section class="cl-lookbook">
		<div class="container">
			<div class="section-header text-center">
				<span class="section-subtitle" style="color:#DC143C">The Lookbook</span>
				<h2 class="section-title">Beauty Forged in Fire</h2>
			</div>
			<div class="cl-lookbook-grid">
				<div class="cl-lookbook-item cl-lookbook-tall">
					<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/models/love-hurts-model-1.jpg' ); ?>" alt="Model wearing Love Hurts crimson heart pendant necklace in romantic candlelit setting" loading="lazy">
					<div class="cl-lookbook-caption">
						<span class="cl-lookbook-piece">Crimson Heart Pendant</span>
						<span class="cl-lookbook-price">$1,799</span>
					</div>
				</div>
				<div class="cl-lookbook-item">
					<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/models/love-hurts-model-2.jpg' ); ?>" alt="Model wearing Love Hurts rose gold thorn bracelet with crimson accent stones" loading="lazy">
					<div class="cl-lookbook-caption">
						<span class="cl-lookbook-piece">Thorn &amp; Rose Bracelet</span>
						<span class="cl-lookbook-price">$1,499</span>
					</div>
				</div>
				<div class="cl-lookbook-item">
					<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/models/love-hurts-model-3.jpg' ); ?>" alt="Model wearing Love Hurts crimson fire drop earrings against dark background" loading="lazy">
					<div class="cl-lookbook-caption">
						<span class="cl-lookbook-piece">Burning Love Earrings</span>
						<span class="cl-lookbook-price">$1,699</span>
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
					<span class="section-subtitle" style="color:#DC143C">The Story</span>
					<h2>Where Passion Meets Craftsmanship</h2>
					<p>Love Hurts is born from the rawest human emotion. Every thorn, every heart, every flame in this collection tells the story of love at its most intense&mdash;beautiful, painful, and unforgettable.</p>
					<p>Crimson stones set in warm rose gold, hand-carved heart motifs, and thorn details that remind us: the things worth having never come easy.</p>
					<blockquote class="cl-story-quote">&ldquo;Love is a fire that burns unseen&mdash;we made it visible.&rdquo;</blockquote>
					<div class="cl-story-stats">
						<div class="cl-stat">
							<span class="cl-stat-value">14K</span>
							<span class="cl-stat-label">Rose Gold Base</span>
						</div>
						<div class="cl-stat">
							<span class="cl-stat-value">AAA</span>
							<span class="cl-stat-label">Crimson Garnets</span>
						</div>
						<div class="cl-stat">
							<span class="cl-stat-value">Ltd</span>
							<span class="cl-stat-label">Edition of 100</span>
						</div>
					</div>
				</div>
				<div class="cl-story-image">
					<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/brand/love-hurts-crafting.jpg' ); ?>" alt="Artisan setting crimson garnet into Love Hurts rose gold ring" loading="lazy">
				</div>
			</div>
		</div>
	</section>

	<!-- ========== PRODUCTS ========== -->
	<section id="cl-products" class="cl-products">
		<div class="container">
			<div class="section-header text-center">
				<span class="section-subtitle" style="color:#DC143C">Shop</span>
				<h2 class="section-title">The Love Hurts Pieces</h2>
				<p class="section-desc">Each piece is a declaration of love. Numbered. Certified. Unforgettable.</p>
			</div>

			<?php if ( class_exists( 'WooCommerce' ) ) :
				$args = array(
					'post_type'      => 'product',
					'posts_per_page' => 12,
					'tax_query'      => array( array(
						'taxonomy' => 'product_cat',
						'field'    => 'slug',
						'terms'    => 'love-hurts-collection',
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
							array( 'name' => 'Crimson Heart Pendant', 'price' => '$1,799', 'badge' => 'Signature' ),
							array( 'name' => 'Thorn & Rose Bracelet', 'price' => '$1,499', 'badge' => 'New' ),
							array( 'name' => 'Burning Love Earrings', 'price' => '$1,699', 'badge' => 'Intense' ),
							array( 'name' => 'Heartbreak Ring', 'price' => '$1,599', 'badge' => 'Limited' ),
							array( 'name' => 'Passion Fire Choker', 'price' => '$2,099', 'badge' => 'Exclusive' ),
							array( 'name' => 'Eternal Flame Bangle', 'price' => '$1,399', 'badge' => 'New' ),
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
			<span class="section-subtitle" style="color:#DC143C">3D Experience</span>
			<h2 class="cl-experience-title">Enter the Enchanted Ballroom</h2>
			<p class="cl-experience-desc">Walk through a candlelit castle, discover hidden pieces in the rain, and experience Love Hurts like never before&mdash;in immersive 3D.</p>
			<a href="<?php echo esc_url( home_url( '/explore-love-hurts/' ) ); ?>" class="btn btn-primary btn-large">Launch 3D Experience</a>
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
				<a href="<?php echo esc_url( home_url( '/signature-collection/' ) ); ?>" class="cl-crosssell-card cl-crosssell-signature">
					<span class="cl-crosssell-name">Signature</span>
					<span class="cl-crosssell-hint">Rose Gold &amp; Diamonds</span>
				</a>
			</div>
		</div>
	</section>

</main>

<style>
/* === LOVE HURTS SCOPED === */
.collection-love-hurts{background:#0a0a0a;color:#e5e5e5}

/* Hero */
.cl-hero-love-hurts{position:relative;min-height:100vh;display:flex;align-items:center;justify-content:center;text-align:center;overflow:hidden}
.cl-hero-love-hurts .cl-hero-bg{position:absolute;inset:0;background:linear-gradient(135deg,#1a0008 0%,#0a0a1a 40%,#0a0a0a 100%)}
.cl-hero-love-hurts .cl-hero-bg::after{content:'';position:absolute;inset:0;background:radial-gradient(ellipse at 50% 30%,rgba(220,20,60,.1) 0%,transparent 70%)}
.cl-hero-particles{position:absolute;inset:0;background-image:radial-gradient(2px 2px at 10% 20%,rgba(220,20,60,.3) 50%,transparent 50%),radial-gradient(2px 2px at 30% 60%,rgba(183,110,121,.2) 50%,transparent 50%),radial-gradient(2px 2px at 70% 80%,rgba(183,110,121,.25) 50%,transparent 50%),radial-gradient(2px 2px at 90% 30%,rgba(220,20,60,.2) 50%,transparent 50%);animation:floatParticles 20s ease-in-out infinite}
@keyframes floatParticles{0%,100%{transform:translateY(0)}50%{transform:translateY(-20px)}}
.cl-hero-love-hurts .cl-hero-content{position:relative;z-index:2;max-width:800px;padding:var(--space-xl)}
.cl-hero-love-hurts .cl-hero-label{color:#DC143C}
.cl-hero-love-hurts .cl-hero-title{font-family:var(--font-heading);font-size:clamp(3rem,5vw + 1rem,6rem);font-weight:var(--weight-bold);color:#fff;margin-bottom:var(--space-lg);line-height:1}
.cl-hero-love-hurts .cl-hero-tagline{font-family:var(--font-accent);font-size:var(--text-xl);color:#D8A7B1;margin-bottom:var(--space-lg)}
.cl-hero-love-hurts .cl-hero-desc{font-size:var(--text-lg);color:rgba(255,255,255,.7);max-width:600px;margin:0 auto var(--space-2xl);line-height:1.7}
.cl-hero-love-hurts .btn-primary{background:linear-gradient(135deg,#DC143C,#B76E79);color:#fff}
.cl-hero-love-hurts .btn-outline{border-color:#DC143C;color:#DC143C}
.cl-hero-love-hurts .btn-outline:hover{background:#DC143C;color:#fff}
.cl-hero-love-hurts .cl-hero-price-hint strong{color:#DC143C}

/* Lookbook */
.collection-love-hurts .cl-lookbook{padding:var(--space-4xl) 0;background:#0f0f0f}
.collection-love-hurts .section-title{color:#fff}
.collection-love-hurts .cl-lookbook-price{color:#DC143C}

/* Story */
.collection-love-hurts .cl-story{padding:var(--space-4xl) 0;background:#0a0a0a}
.collection-love-hurts .cl-story-content h2{color:#fff}
.cl-story-quote{font-family:var(--font-accent);font-size:var(--text-xl);font-style:italic;color:#DC143C;border-left:3px solid #DC143C;padding-left:var(--space-lg);margin:var(--space-xl) 0}
.collection-love-hurts .cl-stat-value{color:#DC143C}
.collection-love-hurts .cl-story-stats{border-top-color:rgba(220,20,60,.2)}

/* Products */
.collection-love-hurts .cl-products{padding:var(--space-4xl) 0;background:#111}
.collection-love-hurts .section-desc{color:rgba(255,255,255,.6)}
.collection-love-hurts .cl-product-card{background:#1a1a1a;border-color:rgba(220,20,60,.1)}
.collection-love-hurts .cl-product-card:hover{box-shadow:0 16px 40px rgba(0,0,0,.4),0 0 20px rgba(220,20,60,.1);border-color:rgba(220,20,60,.3)}
.collection-love-hurts .cl-product-badge{background:#DC143C;color:#fff}
.collection-love-hurts .cl-product-name{color:#fff}
.collection-love-hurts .cl-product-price{color:#DC143C}
.collection-love-hurts .cl-product-btn{border-color:#DC143C;color:#DC143C}
.collection-love-hurts .cl-product-btn:hover{background:#DC143C;color:#fff}

/* Experience */
.collection-love-hurts .cl-experience{padding:var(--space-4xl) 0;background:linear-gradient(135deg,#1a0008,#0a0a1a,#0a0a0a);border-top:1px solid rgba(220,20,60,.1);border-bottom:1px solid rgba(220,20,60,.1)}

/* Cross-sell */
.collection-love-hurts .cl-crosssell{padding:var(--space-4xl) 0;background:#0a0a0a}
.collection-love-hurts .cl-crosssell h2{color:#fff}
.cl-crosssell-black-rose:hover{border-color:#C0C0C0;box-shadow:0 0 30px rgba(192,192,192,.15)}

@media(max-width:768px){
	.cl-hero-love-hurts .cl-hero-title{font-size:clamp(2.5rem,4vw + 1rem,4rem)}
}
</style>

<?php get_footer(); ?>
