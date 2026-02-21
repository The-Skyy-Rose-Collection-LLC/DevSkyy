<?php
/**
 * Template Name: Black Rose Collection
 * Template Post Type: page
 *
 * Dark elegance. Sterling silver. Gothic luxury.
 * Landing page with AI model imagery and product showcase.
 *
 * @package SkyyRose_Flagship
 * @since 2.0.0
 */

get_header();
?>

<main id="primary" class="site-main collection-landing collection-black-rose">

	<!-- ========== HERO ========== -->
	<section class="cl-hero cl-hero-black-rose">
		<div class="cl-hero-bg"></div>
		<div class="cl-hero-content">
			<span class="cl-hero-label">Collection 01</span>

			<!-- Collection Logo -->
			<div class="cl-logo" aria-hidden="true">
				<svg viewBox="0 0 400 80" xmlns="http://www.w3.org/2000/svg" class="cl-logo-svg">
					<defs>
						<linearGradient id="br-grad" x1="0%" y1="0%" x2="100%" y2="0%">
							<stop offset="0%" style="stop-color:#C0C0C0"/>
							<stop offset="50%" style="stop-color:#E8E8E8"/>
							<stop offset="100%" style="stop-color:#C0C0C0"/>
						</linearGradient>
					</defs>
					<text x="200" y="55" text-anchor="middle" fill="url(#br-grad)" font-family="'Playfair Display', Georgia, serif" font-size="58" font-weight="700" letter-spacing="8">BLACK</text>
					<text x="200" y="78" text-anchor="middle" fill="#C0C0C0" font-family="'Cormorant Garamond', Georgia, serif" font-size="22" font-weight="300" letter-spacing="18">R O S E</text>
					<!-- Decorative thorn lines -->
					<line x1="50" y1="62" x2="120" y2="62" stroke="#C0C0C0" stroke-width="0.5" opacity="0.4"/>
					<line x1="280" y1="62" x2="350" y2="62" stroke="#C0C0C0" stroke-width="0.5" opacity="0.4"/>
					<circle cx="200" cy="62" r="2" fill="#C0C0C0" opacity="0.6"/>
				</svg>
			</div>

			<h1 class="cl-hero-title sr-only">Black Rose</h1>
			<p class="cl-hero-tagline">Dark Elegance. Sterling Silver. Gothic Luxury.</p>
			<p class="cl-hero-desc">Sterling silver masterpieces adorned with onyx and obsidian. Cathedral-inspired designs for those who find beauty in the shadows.</p>
			<div class="cl-hero-actions">
				<a href="#cl-products" class="btn btn-primary">Shop the Collection</a>
				<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>" class="btn btn-outline">Pre-Order</a>
			</div>
			<div class="cl-hero-price-hint">Starting at <strong>$1,599</strong></div>
		</div>
	</section>

	<!-- ========== AI MODEL LOOKBOOK ========== -->
	<section class="cl-lookbook">
		<div class="container">
			<div class="section-header text-center">
				<span class="section-subtitle" style="color:#C0C0C0">The Lookbook</span>
				<h2 class="section-title">Worn in Darkness, Forged in Silver</h2>
			</div>
			<div class="cl-lookbook-grid">
				<div class="cl-lookbook-item cl-lookbook-tall">
					<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/models/black-rose-model-1.jpg' ); ?>" alt="Model wearing Black Rose sterling silver statement necklace with onyx pendant" loading="lazy">
					<div class="cl-lookbook-caption">
						<span class="cl-lookbook-piece">Midnight Throne Necklace</span>
						<span class="cl-lookbook-price">$1,899</span>
					</div>
				</div>
				<div class="cl-lookbook-item">
					<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/models/black-rose-model-2.jpg' ); ?>" alt="Model wearing Black Rose obsidian drop earrings against dark velvet" loading="lazy">
					<div class="cl-lookbook-caption">
						<span class="cl-lookbook-piece">Obsidian Veil Earrings</span>
						<span class="cl-lookbook-price">$1,599</span>
					</div>
				</div>
				<div class="cl-lookbook-item">
					<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/models/black-rose-model-3.jpg' ); ?>" alt="Model wearing Black Rose gothic cuff bracelet with silver thorns" loading="lazy">
					<div class="cl-lookbook-caption">
						<span class="cl-lookbook-piece">Thorn Crown Cuff</span>
						<span class="cl-lookbook-price">$2,199</span>
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
					<span class="section-subtitle" style="color:#C0C0C0">The Story</span>
					<h2>Beauty Born From Shadows</h2>
					<p>The Black Rose Collection draws inspiration from gothic cathedrals, midnight gardens, and the raw elegance of darkness. Each piece is hand-forged in sterling silver, set with ethically sourced onyx and obsidian stones.</p>
					<p>This isn&rsquo;t jewelry that whispers&mdash;it commands. Statement pieces for those who walk into a room and own it.</p>
					<div class="cl-story-stats">
						<div class="cl-stat">
							<span class="cl-stat-value">.925</span>
							<span class="cl-stat-label">Sterling Silver</span>
						</div>
						<div class="cl-stat">
							<span class="cl-stat-value">Hand</span>
							<span class="cl-stat-label">Forged &amp; Polished</span>
						</div>
						<div class="cl-stat">
							<span class="cl-stat-value">Ltd</span>
							<span class="cl-stat-label">Edition of 100</span>
						</div>
					</div>
				</div>
				<div class="cl-story-image">
					<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/brand/black-rose-crafting.jpg' ); ?>" alt="Artisan hand-finishing a Black Rose sterling silver piece" loading="lazy">
				</div>
			</div>
		</div>
	</section>

	<!-- ========== PRODUCTS ========== -->
	<section id="cl-products" class="cl-products">
		<div class="container">
			<div class="section-header text-center">
				<span class="section-subtitle" style="color:#C0C0C0">Shop</span>
				<h2 class="section-title">The Black Rose Pieces</h2>
				<p class="section-desc">Each piece is numbered and comes with a certificate of authenticity.</p>
			</div>

			<?php if ( class_exists( 'WooCommerce' ) ) :
				$args = array(
					'post_type'      => 'product',
					'posts_per_page' => 12,
					'tax_query'      => array( array(
						'taxonomy' => 'product_cat',
						'field'    => 'slug',
						'terms'    => 'black-rose-collection',
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
							array( 'name' => 'Midnight Throne Necklace', 'price' => '$1,899', 'badge' => 'Signature' ),
							array( 'name' => 'Obsidian Veil Earrings', 'price' => '$1,599', 'badge' => 'New' ),
							array( 'name' => 'Thorn Crown Cuff', 'price' => '$2,199', 'badge' => 'Limited' ),
							array( 'name' => 'Shadow Cathedral Ring', 'price' => '$1,799', 'badge' => 'Exclusive' ),
							array( 'name' => 'Dark Petal Pendant', 'price' => '$1,499', 'badge' => 'New' ),
							array( 'name' => 'Sterling Serpent Chain', 'price' => '$1,699', 'badge' => 'Exclusive' ),
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
			<span class="section-subtitle" style="color:#C0C0C0">3D Experience</span>
			<h2 class="cl-experience-title">Enter the Virtual Garden</h2>
			<p class="cl-experience-desc">Step into an immersive 3D gothic garden. Explore each piece up close, interact with hidden details, and discover the Black Rose world.</p>
			<a href="<?php echo esc_url( home_url( '/explore-black-rose/' ) ); ?>" class="btn btn-primary btn-large">Launch 3D Experience</a>
		</div>
	</section>

	<!-- ========== CROSS-SELL ========== -->
	<section class="cl-crosssell">
		<div class="container text-center">
			<h2>Explore Other Collections</h2>
			<div class="cl-crosssell-links">
				<a href="<?php echo esc_url( home_url( '/love-hurts-collection/' ) ); ?>" class="cl-crosssell-card cl-crosssell-love-hurts">
					<span class="cl-crosssell-name">Love Hurts</span>
					<span class="cl-crosssell-hint">Crimson &amp; Rose Gold</span>
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
/* === COLLECTION LOGO (shared) === */
.cl-logo{margin-bottom:var(--space-xl);display:flex;justify-content:center}
.cl-logo-svg{width:100%;max-width:400px;height:auto}
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border-width:0}
@media(max-width:768px){.cl-logo-svg{max-width:280px}}

/* === BLACK ROSE SCOPED === */
.collection-black-rose{background:#0a0a0a;color:#e5e5e5}

/* Hero */
.cl-hero-black-rose{position:relative;min-height:100vh;display:flex;align-items:center;justify-content:center;text-align:center;overflow:hidden}
.cl-hero-black-rose .cl-hero-bg{position:absolute;inset:0;background:linear-gradient(135deg,#0a0505 0%,#1a1a1a 40%,#0a0a0a 100%)}
.cl-hero-black-rose .cl-hero-bg::after{content:'';position:absolute;inset:0;background:radial-gradient(ellipse at 50% 30%,rgba(192,192,192,.08) 0%,transparent 70%)}
.cl-hero-black-rose .cl-hero-content{position:relative;z-index:2;max-width:800px;padding:var(--space-xl)}
.cl-hero-label{display:inline-block;font-size:var(--text-sm);font-weight:var(--weight-semibold);text-transform:uppercase;letter-spacing:.3em;color:#C0C0C0;margin-bottom:var(--space-lg)}
.cl-hero-black-rose .cl-hero-title{font-family:var(--font-heading);font-size:clamp(3rem,5vw + 1rem,6rem);font-weight:var(--weight-bold);color:#fff;margin-bottom:var(--space-lg);line-height:1}
.cl-hero-black-rose .cl-hero-tagline{font-family:var(--font-accent);font-size:var(--text-xl);color:#C0C0C0;margin-bottom:var(--space-lg)}
.cl-hero-black-rose .cl-hero-desc{font-size:var(--text-lg);color:rgba(255,255,255,.7);max-width:600px;margin:0 auto var(--space-2xl);line-height:1.7}
.cl-hero-actions{display:flex;gap:var(--space-lg);justify-content:center;flex-wrap:wrap;margin-bottom:var(--space-xl)}
.cl-hero-black-rose .btn-primary{background:linear-gradient(135deg,#C0C0C0,#808080);color:#0a0a0a}
.cl-hero-black-rose .btn-outline{border-color:#C0C0C0;color:#C0C0C0}
.cl-hero-black-rose .btn-outline:hover{background:#C0C0C0;color:#0a0a0a}
.cl-hero-price-hint{font-size:var(--text-sm);color:rgba(255,255,255,.5)}
.cl-hero-price-hint strong{color:#C0C0C0}

/* Lookbook */
.collection-black-rose .cl-lookbook{padding:var(--space-4xl) 0;background:#0f0f0f}
.collection-black-rose .section-title{color:#fff}
.cl-lookbook-grid{display:grid;grid-template-columns:1fr 1fr;gap:var(--space-lg);margin-top:var(--space-2xl)}
.cl-lookbook-tall{grid-row:span 2}
.cl-lookbook-item{position:relative;overflow:hidden;border-radius:var(--radius-lg)}
.cl-lookbook-tall{aspect-ratio:3/4}
.cl-lookbook-item:not(.cl-lookbook-tall){aspect-ratio:4/3}
.cl-lookbook-item img{width:100%;height:100%;object-fit:cover;transition:transform .8s cubic-bezier(.22,1,.36,1)}
.cl-lookbook-item:hover img{transform:scale(1.05)}
.cl-lookbook-caption{position:absolute;bottom:0;left:0;right:0;padding:var(--space-xl) var(--space-lg);background:linear-gradient(transparent,rgba(0,0,0,.85));display:flex;justify-content:space-between;align-items:flex-end}
.cl-lookbook-piece{font-family:var(--font-heading);font-size:var(--text-lg);color:#fff}
.cl-lookbook-price{font-weight:var(--weight-semibold);color:#C0C0C0}

/* Story */
.collection-black-rose .cl-story{padding:var(--space-4xl) 0;background:#0a0a0a}
.cl-story-grid{display:grid;grid-template-columns:1fr 1fr;gap:var(--space-4xl);align-items:center}
.cl-story-content h2{font-size:var(--text-3xl);color:#fff;margin-bottom:var(--space-xl)}
.cl-story-content p{color:rgba(255,255,255,.7);line-height:1.8;margin-bottom:var(--space-lg)}
.cl-story-stats{display:flex;gap:var(--space-2xl);margin-top:var(--space-2xl);padding-top:var(--space-xl);border-top:1px solid rgba(192,192,192,.2)}
.cl-stat{display:flex;flex-direction:column}
.cl-stat-value{font-family:var(--font-heading);font-size:var(--text-2xl);font-weight:var(--weight-bold);color:#C0C0C0}
.cl-stat-label{font-size:var(--text-sm);color:rgba(255,255,255,.5);margin-top:var(--space-xs)}
.cl-story-image{border-radius:var(--radius-lg);overflow:hidden}
.cl-story-image img{width:100%;height:100%;object-fit:cover;aspect-ratio:4/5}

/* Products */
.collection-black-rose .cl-products{padding:var(--space-4xl) 0;background:#111}
.collection-black-rose .section-desc{color:rgba(255,255,255,.6)}
.cl-products-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:var(--space-xl);margin-top:var(--space-2xl)}
.cl-product-card{position:relative;background:#1a1a1a;border-radius:var(--radius-lg);overflow:hidden;transition:all var(--transition-luxury);border:1px solid rgba(192,192,192,.1)}
.cl-product-card:hover{transform:translateY(-6px);box-shadow:0 16px 40px rgba(0,0,0,.4),0 0 20px rgba(192,192,192,.08);border-color:rgba(192,192,192,.3)}
.cl-product-badge{position:absolute;top:var(--space-md);left:var(--space-md);padding:4px 12px;font-size:11px;font-weight:var(--weight-semibold);text-transform:uppercase;letter-spacing:.1em;background:#C0C0C0;color:#0a0a0a;border-radius:var(--radius-sm);z-index:2}
.cl-product-image{aspect-ratio:1;overflow:hidden}
.cl-product-image img{width:100%;height:100%;object-fit:cover;transition:transform .6s ease}
.cl-product-card:hover .cl-product-image img{transform:scale(1.08)}
.cl-product-info{padding:var(--space-lg)}
.cl-product-name{font-family:var(--font-heading);font-size:var(--text-lg);color:#fff;margin-bottom:var(--space-sm)}
.cl-product-price{font-weight:var(--weight-semibold);color:#C0C0C0}
.cl-product-btn{display:block;margin:0 var(--space-lg) var(--space-lg);text-align:center;border-color:#C0C0C0;color:#C0C0C0}
.cl-product-btn:hover{background:#C0C0C0;color:#0a0a0a}

/* Experience */
.collection-black-rose .cl-experience{padding:var(--space-4xl) 0;background:linear-gradient(135deg,#0a0505,#141414,#0a0a0a);border-top:1px solid rgba(192,192,192,.1);border-bottom:1px solid rgba(192,192,192,.1)}
.cl-experience-title{font-size:var(--text-3xl);color:#fff;margin-bottom:var(--space-lg)}
.cl-experience-desc{max-width:600px;margin:0 auto var(--space-2xl);color:rgba(255,255,255,.7);line-height:1.7}

/* Cross-sell */
.collection-black-rose .cl-crosssell{padding:var(--space-4xl) 0;background:#0a0a0a}
.cl-crosssell h2{color:#fff;margin-bottom:var(--space-2xl)}
.cl-crosssell-links{display:flex;gap:var(--space-xl);justify-content:center;flex-wrap:wrap}
.cl-crosssell-card{display:flex;flex-direction:column;align-items:center;padding:var(--space-2xl) var(--space-3xl);border:1px solid rgba(255,255,255,.15);border-radius:var(--radius-lg);transition:all var(--transition-luxury);text-decoration:none}
.cl-crosssell-card:hover{transform:translateY(-4px)}
.cl-crosssell-love-hurts:hover{border-color:#DC143C;box-shadow:0 0 30px rgba(220,20,60,.15)}
.cl-crosssell-signature:hover{border-color:#B76E79;box-shadow:0 0 30px rgba(183,110,121,.15)}
.cl-crosssell-name{font-family:var(--font-heading);font-size:var(--text-xl);color:#fff;margin-bottom:var(--space-xs)}
.cl-crosssell-hint{font-size:var(--text-sm);color:rgba(255,255,255,.5)}

@media(max-width:768px){
	.cl-lookbook-grid{grid-template-columns:1fr}
	.cl-lookbook-tall{grid-row:span 1}
	.cl-story-grid{grid-template-columns:1fr;gap:var(--space-2xl)}
	.cl-story-stats{flex-wrap:wrap;gap:var(--space-xl)}
	.cl-products-grid{grid-template-columns:repeat(auto-fill,minmax(220px,1fr))}
	.cl-crosssell-links{flex-direction:column;align-items:center}
}
</style>

<?php get_footer(); ?>
