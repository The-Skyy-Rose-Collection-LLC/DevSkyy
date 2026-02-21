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

			<!-- Collection Logo -->
			<div class="cl-logo" aria-hidden="true">
				<svg viewBox="0 0 400 90" xmlns="http://www.w3.org/2000/svg" class="cl-logo-svg">
					<defs>
						<linearGradient id="lh-grad" x1="0%" y1="0%" x2="100%" y2="0%">
							<stop offset="0%" style="stop-color:#DC143C"/>
							<stop offset="50%" style="stop-color:#FF4D6A"/>
							<stop offset="100%" style="stop-color:#DC143C"/>
						</linearGradient>
					</defs>
					<text x="200" y="42" text-anchor="middle" fill="url(#lh-grad)" font-family="'Playfair Display', Georgia, serif" font-size="46" font-weight="700" letter-spacing="4">LOVE</text>
					<text x="200" y="80" text-anchor="middle" fill="#D8A7B1" font-family="'Playfair Display', Georgia, serif" font-size="46" font-weight="700" letter-spacing="4">HURTS</text>
					<!-- Heart accent -->
					<path d="M200 52 L196 48 Q192 44 196 40 Q200 36 200 40 Q200 36 204 40 Q208 44 204 48 Z" fill="#DC143C" opacity="0.7"/>
					<!-- Thorn lines -->
					<line x1="60" y1="50" x2="140" y2="50" stroke="#DC143C" stroke-width="0.5" opacity="0.3"/>
					<line x1="260" y1="50" x2="340" y2="50" stroke="#DC143C" stroke-width="0.5" opacity="0.3"/>
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
