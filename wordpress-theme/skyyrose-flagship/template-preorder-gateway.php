<?php
/**
 * Template Name: Preorder Gateway
 * Template Post Type: page
 *
 * Pre-launch gateway featuring ALL 3 collections with email capture,
 * countdown, and per-collection pre-order sections.
 *
 * @package SkyyRose_Flagship
 * @since 2.0.0
 */

get_header();
?>

<main id="primary" class="site-main preorder-gateway">

	<!-- ========== HERO WITH COUNTDOWN ========== -->
	<section class="po-hero">
		<div class="po-hero-bg"></div>
		<div class="po-hero-content">
			<span class="po-badge">Pre-Order Now Open</span>
			<h1 class="po-hero-title">Be the First to Own</h1>
			<p class="po-hero-subtitle">Three collections. Limited quantities. Reserve your pieces from Black Rose, Love Hurts, and Signature before the public launch.</p>

			<div class="po-countdown" data-launch-date="<?php echo esc_attr( get_post_meta( get_the_ID(), '_launch_date', true ) ?: '2026-03-15T00:00:00' ); ?>">
				<div class="po-countdown-block">
					<span class="po-countdown-num" id="po-days">00</span>
					<span class="po-countdown-label">Days</span>
				</div>
				<div class="po-countdown-block">
					<span class="po-countdown-num" id="po-hours">00</span>
					<span class="po-countdown-label">Hours</span>
				</div>
				<div class="po-countdown-block">
					<span class="po-countdown-num" id="po-minutes">00</span>
					<span class="po-countdown-label">Minutes</span>
				</div>
				<div class="po-countdown-block">
					<span class="po-countdown-num" id="po-seconds">00</span>
					<span class="po-countdown-label">Seconds</span>
				</div>
			</div>

			<div class="po-email-capture">
				<h3>Get Early Access &amp; 25% Off</h3>
				<form class="po-signup-form" id="preorder-form" method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
					<input type="hidden" name="action" value="preorder_signup">
					<?php wp_nonce_field( 'preorder_signup_nonce', 'preorder_nonce' ); ?>
					<div class="po-form-row">
						<input type="email" name="email" placeholder="Enter your email" required class="po-email-input">
						<button type="submit" class="btn btn-primary">Join Waitlist</button>
					</div>
					<p class="po-form-note">Join <span class="po-waitlist-count">0</span> others waiting for launch</p>
				</form>
			</div>
		</div>
	</section>

	<!-- ========== ALL 3 COLLECTIONS ========== -->
	<section class="po-collections">
		<div class="container">
			<div class="section-header text-center">
				<span class="section-subtitle text-rose-gold">Choose Your Collection</span>
				<h2 class="section-title">Three Worlds, One Pre-Order</h2>
				<p class="section-desc">Each collection has its own spirit. Reserve pieces from any or all three.</p>
			</div>

			<!-- BLACK ROSE -->
			<div class="po-collection-card po-card-black-rose">
				<div class="po-card-image">
					<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/models/black-rose-model-1.jpg' ); ?>" alt="Black Rose Collection — AI model wearing sterling silver gothic necklace" loading="lazy">
					<div class="po-card-overlay">
						<span class="po-card-number">01</span>
					</div>
				</div>
				<div class="po-card-content">
					<h3 class="po-card-title">Black Rose</h3>
					<p class="po-card-tagline">Dark Elegance. Sterling Silver. Gothic Luxury.</p>
					<p class="po-card-desc">Sterling silver with onyx and obsidian. Cathedral-inspired statement pieces for those who command every room.</p>
					<div class="po-card-meta">
						<span class="po-card-price">From <strong>$1,599</strong></span>
						<span class="po-card-edition">Limited to 100 pieces</span>
					</div>
					<div class="po-card-pieces">
						<span class="po-piece-chip">Midnight Throne Necklace</span>
						<span class="po-piece-chip">Obsidian Veil Earrings</span>
						<span class="po-piece-chip">Thorn Crown Cuff</span>
					</div>
					<div class="po-card-actions">
						<a href="<?php echo esc_url( home_url( '/black-rose-collection/' ) ); ?>" class="btn btn-outline po-card-btn">View Collection</a>
						<a href="#preorder-form" class="btn btn-primary po-card-btn po-scroll-btn">Reserve Now</a>
					</div>
				</div>
			</div>

			<!-- LOVE HURTS -->
			<div class="po-collection-card po-card-love-hurts">
				<div class="po-card-image">
					<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/models/love-hurts-model-1.jpg' ); ?>" alt="Love Hurts Collection — AI model wearing crimson heart pendant" loading="lazy">
					<div class="po-card-overlay">
						<span class="po-card-number">02</span>
					</div>
				</div>
				<div class="po-card-content">
					<h3 class="po-card-title">Love Hurts</h3>
					<p class="po-card-tagline">Passionate. Crimson Fire. Romantic Edge.</p>
					<p class="po-card-desc">Bold crimson and rose gold with heart motifs and thorns. Inspired by the beauty and pain of love.</p>
					<div class="po-card-meta">
						<span class="po-card-price">From <strong>$1,499</strong></span>
						<span class="po-card-edition">Limited to 100 pieces</span>
					</div>
					<div class="po-card-pieces">
						<span class="po-piece-chip">Crimson Heart Pendant</span>
						<span class="po-piece-chip">Thorn &amp; Rose Bracelet</span>
						<span class="po-piece-chip">Burning Love Earrings</span>
					</div>
					<div class="po-card-actions">
						<a href="<?php echo esc_url( home_url( '/love-hurts-collection/' ) ); ?>" class="btn btn-outline po-card-btn">View Collection</a>
						<a href="#preorder-form" class="btn btn-primary po-card-btn po-scroll-btn">Reserve Now</a>
					</div>
				</div>
			</div>

			<!-- SIGNATURE -->
			<div class="po-collection-card po-card-signature">
				<div class="po-card-image">
					<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/models/signature-model-1.jpg' ); ?>" alt="Signature Collection — AI model wearing rose gold diamond solitaire ring" loading="lazy">
					<div class="po-card-overlay">
						<span class="po-card-number">03</span>
					</div>
				</div>
				<div class="po-card-content">
					<h3 class="po-card-title">Signature</h3>
					<p class="po-card-tagline">Timeless. Rose Gold. Diamond Excellence.</p>
					<p class="po-card-desc">18K rose gold with GIA-certified diamonds. Heirloom pieces with lifetime warranty. The pinnacle of SkyyRose.</p>
					<div class="po-card-meta">
						<span class="po-card-price">From <strong>$1,299</strong></span>
						<span class="po-card-edition">Lifetime Warranty</span>
					</div>
					<div class="po-card-pieces">
						<span class="po-piece-chip">Rose Gold Solitaire Ring</span>
						<span class="po-piece-chip">Diamond Tennis Bracelet</span>
						<span class="po-piece-chip">Halo Diamond Pendant</span>
					</div>
					<div class="po-card-actions">
						<a href="<?php echo esc_url( home_url( '/signature-collection/' ) ); ?>" class="btn btn-outline po-card-btn">View Collection</a>
						<a href="#preorder-form" class="btn btn-primary po-card-btn po-scroll-btn">Reserve Now</a>
					</div>
				</div>
			</div>

		</div>
	</section>

	<!-- ========== WHY PRE-ORDER ========== -->
	<section class="po-benefits">
		<div class="container">
			<div class="section-header text-center">
				<h2 class="section-title">Why Pre-Order?</h2>
			</div>
			<div class="po-benefits-grid">
				<div class="po-benefit-card">
					<div class="po-benefit-icon">
						<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>
					</div>
					<h3>25% Off Launch Price</h3>
					<p>Pre-order members lock in exclusive pricing before the public launch.</p>
				</div>
				<div class="po-benefit-card">
					<div class="po-benefit-icon">
						<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
					</div>
					<h3>48-Hour Early Access</h3>
					<p>Get first pick before public launch. Some pieces are limited to 25 units worldwide.</p>
				</div>
				<div class="po-benefit-card">
					<div class="po-benefit-icon">
						<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
					</div>
					<h3>Risk-Free Reservation</h3>
					<p>No charge until your piece ships. Full refund if you change your mind before production.</p>
				</div>
				<div class="po-benefit-card">
					<div class="po-benefit-icon">
						<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="20 12 20 22 4 22 4 12"/><rect x="2" y="7" width="20" height="5"/><line x1="12" y1="22" x2="12" y2="7"/></svg>
					</div>
					<h3>Luxury Packaging</h3>
					<p>Pre-order pieces arrive in our exclusive rose gold collector's box with certificate of authenticity.</p>
				</div>
			</div>
		</div>
	</section>

	<!-- ========== FAQ ========== -->
	<section class="po-faq">
		<div class="container">
			<div class="section-header text-center">
				<h2 class="section-title">Questions &amp; Answers</h2>
			</div>
			<div class="po-faq-grid">
				<div class="po-faq-item">
					<h3>When does the collection launch?</h3>
					<p>The countdown above shows our launch date. Waitlist members get 48-hour early access with a private reservation link.</p>
				</div>
				<div class="po-faq-item">
					<h3>Can I pre-order from multiple collections?</h3>
					<p>Absolutely. Mix and match across Black Rose, Love Hurts, and Signature. Your 25% discount applies to all pre-order pieces.</p>
				</div>
				<div class="po-faq-item">
					<h3>How limited are the quantities?</h3>
					<p>Most pieces are limited to 100 worldwide. Select signature pieces are limited to just 25 units. Once gone, they&rsquo;re gone.</p>
				</div>
				<div class="po-faq-item">
					<h3>Is my reservation refundable?</h3>
					<p>Yes. No charge is made until your piece enters production. Cancel anytime before that for a full refund.</p>
				</div>
			</div>
		</div>
	</section>

	<!-- ========== FINAL CTA ========== -->
	<section class="po-final-cta">
		<div class="container text-center">
			<h2>Don&rsquo;t Miss Your Moment</h2>
			<p>Join the waitlist now. Three collections, limited pieces, one chance to be first.</p>
			<a href="#preorder-form" class="btn btn-primary btn-large po-scroll-btn">Join the Waitlist</a>
		</div>
	</section>

</main>

<style>
/* === PREORDER GATEWAY === */
.preorder-gateway{background:var(--off-white)}

/* Hero */
.po-hero{position:relative;min-height:100vh;display:flex;align-items:center;justify-content:center;text-align:center;color:#fff;overflow:hidden}
.po-hero-bg{position:absolute;inset:0;background:linear-gradient(135deg,#B76E79 0%,#D4AF37 50%,#B76E79 100%)}
.po-hero-bg::after{content:'';position:absolute;inset:0;background:radial-gradient(ellipse at center,transparent 0%,rgba(0,0,0,.25) 100%)}
.po-hero-content{position:relative;z-index:2;max-width:900px;padding:var(--space-xl)}
.po-badge{display:inline-block;padding:var(--space-sm) var(--space-xl);font-size:var(--text-sm);font-weight:var(--weight-bold);text-transform:uppercase;letter-spacing:.2em;background:rgba(255,255,255,.15);border:2px solid rgba(255,255,255,.3);border-radius:var(--radius-full);margin-bottom:var(--space-xl);backdrop-filter:blur(10px)}
.po-hero-title{font-family:var(--font-heading);font-size:clamp(2.5rem,5vw + 1rem,5rem);margin-bottom:var(--space-lg);text-shadow:0 4px 30px rgba(0,0,0,.3)}
.po-hero-subtitle{font-family:var(--font-accent);font-size:var(--text-xl);margin-bottom:var(--space-3xl);opacity:.95;max-width:700px;margin-left:auto;margin-right:auto;line-height:1.6}

/* Countdown */
.po-countdown{display:flex;gap:var(--space-xl);justify-content:center;margin-bottom:var(--space-3xl);flex-wrap:wrap}
.po-countdown-block{display:flex;flex-direction:column;align-items:center;padding:var(--space-lg) var(--space-xl);background:rgba(255,255,255,.1);border-radius:var(--radius-lg);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,.2);min-width:100px}
.po-countdown-num{font-size:clamp(2rem,4vw,3.5rem);font-weight:var(--weight-bold);font-family:var(--font-heading);line-height:1}
.po-countdown-label{font-size:var(--text-sm);text-transform:uppercase;letter-spacing:.1em;opacity:.8;margin-top:var(--space-xs)}

/* Email capture */
.po-email-capture{max-width:600px;margin:0 auto;padding:var(--space-2xl);background:rgba(255,255,255,.1);border-radius:var(--radius-lg);backdrop-filter:blur(15px);border:1px solid rgba(255,255,255,.2)}
.po-email-capture h3{margin-bottom:var(--space-lg);font-size:var(--text-xl)}
.po-form-row{display:flex;gap:var(--space-md);margin-bottom:var(--space-md)}
.po-email-input{flex:1;padding:var(--space-md) var(--space-lg);font-size:var(--text-base);border:2px solid rgba(255,255,255,.3);border-radius:var(--radius-md);background:rgba(255,255,255,.9);color:var(--dark-gray);transition:all var(--transition-base)}
.po-email-input:focus{outline:none;border-color:#fff;background:#fff}
.po-form-note{font-size:var(--text-sm);opacity:.8}
.po-waitlist-count{font-weight:var(--weight-bold)}

/* Collection Cards */
.po-collections{padding:var(--space-4xl) 0}
.po-collections .section-desc{color:var(--dark-gray);opacity:.7;max-width:600px;margin:0 auto}
.po-collection-card{display:grid;grid-template-columns:1fr 1fr;gap:0;margin-top:var(--space-3xl);border-radius:var(--radius-lg);overflow:hidden;box-shadow:var(--shadow-xl);transition:all var(--transition-luxury)}
.po-collection-card:hover{transform:translateY(-4px);box-shadow:0 20px 60px rgba(0,0,0,.12)}
.po-card-image{position:relative;min-height:500px;overflow:hidden}
.po-card-image img{width:100%;height:100%;object-fit:cover;transition:transform .8s cubic-bezier(.22,1,.36,1)}
.po-collection-card:hover .po-card-image img{transform:scale(1.03)}
.po-card-overlay{position:absolute;bottom:var(--space-lg);left:var(--space-lg)}
.po-card-number{font-family:var(--font-heading);font-size:var(--text-4xl);font-weight:var(--weight-bold);color:rgba(255,255,255,.3)}
.po-card-content{padding:var(--space-3xl);display:flex;flex-direction:column;justify-content:center}

/* Per-collection card colors */
.po-card-black-rose{background:#0a0a0a;color:#e5e5e5}
.po-card-black-rose .po-card-title{color:#fff}
.po-card-black-rose .po-card-tagline{color:#C0C0C0;font-family:var(--font-accent)}
.po-card-black-rose .po-card-price strong{color:#C0C0C0}
.po-card-black-rose .po-piece-chip{border-color:rgba(192,192,192,.3);color:#C0C0C0}
.po-card-black-rose .btn-outline{border-color:#C0C0C0;color:#C0C0C0}
.po-card-black-rose .btn-outline:hover{background:#C0C0C0;color:#0a0a0a}
.po-card-black-rose .btn-primary{background:linear-gradient(135deg,#C0C0C0,#808080);color:#0a0a0a}

.po-card-love-hurts{background:#0a0a0a;color:#e5e5e5}
.po-card-love-hurts .po-card-title{color:#fff}
.po-card-love-hurts .po-card-tagline{color:#D8A7B1;font-family:var(--font-accent)}
.po-card-love-hurts .po-card-price strong{color:#DC143C}
.po-card-love-hurts .po-piece-chip{border-color:rgba(220,20,60,.3);color:#DC143C}
.po-card-love-hurts .btn-outline{border-color:#DC143C;color:#DC143C}
.po-card-love-hurts .btn-outline:hover{background:#DC143C;color:#fff}
.po-card-love-hurts .btn-primary{background:linear-gradient(135deg,#DC143C,#B76E79);color:#fff}

.po-card-signature{background:#fff;color:var(--dark-gray)}
.po-card-signature .po-card-title{color:var(--dark-gray)}
.po-card-signature .po-card-tagline{color:#B76E79;font-family:var(--font-accent)}
.po-card-signature .po-card-price strong{color:#B76E79}
.po-card-signature .po-piece-chip{border-color:rgba(183,110,121,.3);color:#B76E79}
.po-card-signature .btn-outline{border-color:#B76E79;color:#B76E79}
.po-card-signature .btn-outline:hover{background:#B76E79;color:#fff}
.po-card-signature .btn-primary{background:var(--gradient-rose-gold);color:#fff}

/* Card shared styles */
.po-card-title{font-family:var(--font-heading);font-size:var(--text-3xl);margin-bottom:var(--space-sm)}
.po-card-tagline{font-size:var(--text-lg);margin-bottom:var(--space-lg)}
.po-card-desc{line-height:1.7;margin-bottom:var(--space-lg);opacity:.8}
.po-card-meta{display:flex;justify-content:space-between;margin-bottom:var(--space-lg);padding-bottom:var(--space-lg);border-bottom:1px solid rgba(255,255,255,.1)}
.po-card-price{font-size:var(--text-lg)}
.po-card-edition{font-size:var(--text-sm);opacity:.6}
.po-card-signature .po-card-meta{border-bottom-color:rgba(0,0,0,.1)}
.po-card-pieces{display:flex;flex-wrap:wrap;gap:var(--space-sm);margin-bottom:var(--space-xl)}
.po-piece-chip{padding:4px 12px;font-size:var(--text-sm);border:1px solid;border-radius:var(--radius-full)}
.po-card-actions{display:flex;gap:var(--space-md)}
.po-card-btn{flex:1;text-align:center}

/* Benefits */
.po-benefits{padding:var(--space-4xl) 0;background:#fff}
.po-benefits-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:var(--space-2xl);margin-top:var(--space-2xl)}
.po-benefit-card{text-align:center;padding:var(--space-2xl);background:var(--off-white);border-radius:var(--radius-lg);transition:all var(--transition-luxury)}
.po-benefit-card:hover{transform:translateY(-6px);box-shadow:var(--shadow-xl),var(--shadow-rose-glow)}
.po-benefit-icon{color:var(--rose-gold);margin-bottom:var(--space-lg)}
.po-benefit-card h3{color:var(--rose-gold);margin-bottom:var(--space-md)}
.po-benefit-card p{color:var(--dark-gray);opacity:.7;line-height:1.6}

/* FAQ */
.po-faq{padding:var(--space-4xl) 0;background:var(--off-white)}
.po-faq-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:var(--space-xl);margin-top:var(--space-2xl)}
.po-faq-item{padding:var(--space-xl);background:#fff;border-radius:var(--radius-lg);box-shadow:var(--shadow-sm)}
.po-faq-item h3{color:var(--rose-gold);margin-bottom:var(--space-md);font-size:var(--text-lg)}
.po-faq-item p{color:var(--dark-gray);opacity:.7;line-height:1.7}

/* Final CTA */
.po-final-cta{padding:var(--space-4xl) 0;background:var(--gradient-rose-gold);color:#fff}
.po-final-cta h2{color:#fff;margin-bottom:var(--space-md)}
.po-final-cta p{color:rgba(255,255,255,.85);margin-bottom:var(--space-2xl);font-size:var(--text-lg)}
.po-final-cta .btn-primary{background:#fff;color:#B76E79}

@media(max-width:768px){
	.po-hero-title{font-size:var(--text-3xl)}
	.po-countdown{gap:var(--space-md)}
	.po-countdown-block{min-width:70px;padding:var(--space-md) var(--space-lg)}
	.po-form-row{flex-direction:column}
	.po-collection-card{grid-template-columns:1fr}
	.po-card-image{min-height:300px}
	.po-card-actions{flex-direction:column}
	.po-benefits-grid,.po-faq-grid{grid-template-columns:1fr}
}
</style>

<script>
(function(){
	var timer=document.querySelector('.po-countdown');
	if(!timer)return;
	var launch=new Date(timer.dataset.launchDate).getTime();
	function tick(){
		var now=Date.now(),d=launch-now;
		if(d<0){d=0}
		document.getElementById('po-days').textContent=String(Math.floor(d/864e5)).padStart(2,'0');
		document.getElementById('po-hours').textContent=String(Math.floor(d%864e5/36e5)).padStart(2,'0');
		document.getElementById('po-minutes').textContent=String(Math.floor(d%36e5/6e4)).padStart(2,'0');
		document.getElementById('po-seconds').textContent=String(Math.floor(d%6e4/1e3)).padStart(2,'0');
	}
	tick();setInterval(tick,1000);
})();
document.querySelectorAll('.po-scroll-btn').forEach(function(a){
	a.addEventListener('click',function(e){
		e.preventDefault();
		var t=document.querySelector(this.getAttribute('href'));
		if(t)t.scrollIntoView({behavior:'smooth',block:'start'});
	});
});
</script>

<?php get_footer(); ?>
