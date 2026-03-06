<?php
/**
 * Template Name: Luxury Homepage
 *
 * Dark luxury alternative homepage — cinematic collection showcase
 * with real imagery, scroll-reveal animations, and brand-consistent
 * design matching the SkyyRose flagship aesthetic.
 *
 * @package SkyyRose_Flagship
 * @since   4.2.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

// Fetch pre-order products for the featured section.
$preorder_products = array();
if ( function_exists( 'skyyrose_get_preorder_products' ) ) {
	$preorder_products = skyyrose_get_preorder_products();
}
if ( empty( $preorder_products ) && function_exists( 'skyyrose_get_product_catalog' ) ) {
	$all = skyyrose_get_product_catalog();
	$preorder_products = array_filter( $all, function ( $p ) {
		return ! empty( $p['is_preorder'] ) && ! empty( $p['published'] );
	} );
}

// Collection data for the showcase.
$collections = array(
	array(
		'name'    => __( 'Black Rose', 'skyyrose-flagship' ),
		'tagline' => __( 'Where Darkness Blooms, Beauty Follows.', 'skyyrose-flagship' ),
		'accent'  => '#C0C0C0',
		'number'  => '01',
		'image'   => SKYYROSE_ASSETS_URI . '/scenes/black-rose/black-rose-marble-rotunda.webp',
		'logo'    => get_template_directory_uri() . '/assets/branding/black-rose-logo-hero-transparent.png',
		'url'     => home_url( '/collection-black-rose/' ),
		'desc'    => __( 'Gothic luxury in midnight. Limited drops, numbered pieces, never restocked.', 'skyyrose-flagship' ),
	),
	array(
		'name'    => __( 'Love Hurts', 'skyyrose-flagship' ),
		'tagline' => __( 'Named After a Bloodline, Not a Feeling.', 'skyyrose-flagship' ),
		'accent'  => '#DC143C',
		'number'  => '02',
		'image'   => SKYYROSE_ASSETS_URI . '/scenes/love-hurts/love-hurts-crimson-throne-room.webp',
		'logo'    => get_template_directory_uri() . '/assets/branding/love-hurts-logo-hero-transparent.png',
		'url'     => home_url( '/collection-love-hurts/' ),
		'desc'    => __( 'Raw passion in deep crimson. Emotion woven into every stitch.', 'skyyrose-flagship' ),
	),
	array(
		'name'    => __( 'Signature', 'skyyrose-flagship' ),
		'tagline' => __( 'Your Daily Uniform. Elevated.', 'skyyrose-flagship' ),
		'accent'  => '#D4AF37',
		'number'  => '03',
		'image'   => SKYYROSE_ASSETS_URI . '/scenes/signature/signature-golden-gate-showroom.webp',
		'logo'    => get_template_directory_uri() . '/assets/branding/signature-logo-hero-transparent.png',
		'url'     => home_url( '/collection-signature/' ),
		'desc'    => __( 'Foundation wardrobe. Bay Area DNA. Always available.', 'skyyrose-flagship' ),
	),
);

get_header();
?>

<main id="primary" class="site-main lux-page" role="main">

<!-- ════════════════════════════════════════════════
     HERO — Full-Bleed Cinematic
     ════════════════════════════════════════════════ -->
<section class="lux-hero" aria-label="<?php esc_attr_e( 'SkyyRose Luxury Streetwear', 'skyyrose-flagship' ); ?>">
	<div class="lux-hero__bg">
		<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/scenes/black-rose/black-rose-moonlit-courtyard.webp' ); ?>"
		     alt="" width="1920" height="1080" fetchpriority="high">
	</div>
	<div class="lux-hero__overlay"></div>
	<div class="lux-hero__content">
		<p class="lux-hero__eyebrow rv">Oakland &mdash; Est. 2022</p>
		<h1 class="lux-hero__title rv rv-d1">SKYYROSE</h1>
		<p class="lux-hero__tagline rv rv-d2"><?php esc_html_e( 'Luxury Grows from Concrete.', 'skyyrose-flagship' ); ?></p>
		<div class="lux-hero__ctas rv rv-d3">
			<a href="<?php echo esc_url( home_url( '/collections/' ) ); ?>" class="lux-btn lux-btn--fill">
				<?php esc_html_e( 'Explore Collections', 'skyyrose-flagship' ); ?>
			</a>
			<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>" class="lux-btn">
				<?php esc_html_e( 'Pre-Order Now', 'skyyrose-flagship' ); ?>
			</a>
		</div>
	</div>
	<div class="lux-hero__scroll" aria-hidden="true">
		<svg width="20" height="30" viewBox="0 0 20 30" fill="none" stroke="rgba(255,255,255,.4)" stroke-width="2">
			<rect x="1" y="1" width="18" height="28" rx="9"/>
			<circle cx="10" cy="10" r="2" fill="rgba(255,255,255,.6)">
				<animate attributeName="cy" values="8;18;8" dur="2s" repeatCount="indefinite"/>
			</circle>
		</svg>
	</div>
</section>

<!-- Press Strip -->
<div class="lux-press rv">
	<span class="lux-press__label"><?php esc_html_e( 'As Featured In', 'skyyrose-flagship' ); ?></span>
	<span class="lux-press__logo">Maxim</span>
	<span class="lux-press__logo">CEO Weekly</span>
	<span class="lux-press__logo">The Blox</span>
	<span class="lux-press__logo">SF Post</span>
</div>

<!-- ════════════════════════════════════════════════
     COLLECTIONS — Full-Bleed Cards
     ════════════════════════════════════════════════ -->
<section class="lux-collections" id="collections" aria-label="<?php esc_attr_e( 'Collections', 'skyyrose-flagship' ); ?>">
	<div class="lux-section-head">
		<p class="lux-eyebrow rv"><?php esc_html_e( 'Three Collections. One Vision.', 'skyyrose-flagship' ); ?></p>
		<h2 class="lux-heading rv rv-d1"><?php esc_html_e( 'Explore the World of SkyyRose', 'skyyrose-flagship' ); ?></h2>
	</div>

	<div class="lux-cols-grid">
		<?php
		$col_delay = 0;
		foreach ( $collections as $col ) :
			$delay_class = $col_delay > 0 ? ' rv-d' . $col_delay : '';
		?>
		<article class="lux-col-card rv<?php echo esc_attr( $delay_class ); ?>"
		         style="--card-accent: <?php echo esc_attr( $col['accent'] ); ?>;">
			<a href="<?php echo esc_url( $col['url'] ); ?>" class="lux-col-card__link"
			   aria-label="<?php echo esc_attr( sprintf( __( 'View %s Collection', 'skyyrose-flagship' ), $col['name'] ) ); ?>">
				<div class="lux-col-card__img">
					<img src="<?php echo esc_url( $col['image'] ); ?>"
					     alt="<?php echo esc_attr( sprintf( __( '%s Collection — SkyyRose', 'skyyrose-flagship' ), $col['name'] ) ); ?>"
					     width="800" height="600" loading="lazy">
				</div>
				<div class="lux-col-card__overlay"></div>
				<div class="lux-col-card__content">
					<span class="lux-col-card__num"><?php echo esc_html( $col['number'] ); ?></span>
					<?php if ( ! empty( $col['logo'] ) ) : ?>
					<h3 class="lux-col-card__name">
						<span class="screen-reader-text"><?php echo esc_html( $col['name'] ); ?></span>
						<img class="lux-col-card__logo" aria-hidden="true"
						     src="<?php echo esc_url( $col['logo'] ); ?>"
						     alt="" loading="lazy">
					</h3>
				<?php else : ?>
					<h3 class="lux-col-card__name"><?php echo esc_html( $col['name'] ); ?></h3>
				<?php endif; ?>
					<p class="lux-col-card__tagline"><?php echo esc_html( $col['tagline'] ); ?></p>
					<p class="lux-col-card__desc"><?php echo esc_html( $col['desc'] ); ?></p>
					<span class="lux-col-card__cta">
						<?php esc_html_e( 'View Collection', 'skyyrose-flagship' ); ?>
						<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
					</span>
				</div>
			</a>
		</article>
		<?php
			$col_delay++;
		endforeach;
		?>
	</div>
</section>

<!-- ════════════════════════════════════════════════
     STORY — Split Panel
     ════════════════════════════════════════════════ -->
<section class="lux-story" id="story" aria-label="<?php esc_attr_e( 'Our Story', 'skyyrose-flagship' ); ?>">
	<div class="lux-story__image rv-l">
		<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/founder-portrait.jpg' ); ?>"
		     alt="<?php esc_attr_e( 'Corey Foster — SkyyRose Founder', 'skyyrose-flagship' ); ?>"
		     width="600" height="800" loading="lazy">
	</div>
	<div class="lux-story__text">
		<p class="lux-eyebrow rv"><?php esc_html_e( 'The Origin', 'skyyrose-flagship' ); ?></p>
		<h2 class="lux-heading rv rv-d1"><?php esc_html_e( 'Born from East Oakland. Built for the World.', 'skyyrose-flagship' ); ?></h2>
		<p class="lux-body rv rv-d2"><?php esc_html_e( 'SkyyRose started with a vision: luxury that doesn\'t forget where it came from. Every collection carries the weight of real stories — struggle, fatherhood, resilience — transformed into wearable art.', 'skyyrose-flagship' ); ?></p>
		<blockquote class="lux-quote rv rv-d3">
			&ldquo;<?php esc_html_e( 'You ask me this four years ago, I never would\'ve thought I\'d be here. But we knew we had to get it by any means necessary.', 'skyyrose-flagship' ); ?>&rdquo;
			<cite>&mdash; <?php esc_html_e( 'Corey Foster, Founder', 'skyyrose-flagship' ); ?></cite>
		</blockquote>
		<a href="<?php echo esc_url( home_url( '/about/' ) ); ?>" class="lux-btn rv rv-d4">
			<?php esc_html_e( 'Read the Full Story', 'skyyrose-flagship' ); ?>
		</a>
	</div>
</section>

<!-- ════════════════════════════════════════════════
     CRAFT — What Makes Us Different
     ════════════════════════════════════════════════ -->
<section class="lux-craft" id="craft" aria-label="<?php esc_attr_e( 'Our Craft', 'skyyrose-flagship' ); ?>">
	<div class="lux-section-head">
		<p class="lux-eyebrow rv"><?php esc_html_e( 'Built Different', 'skyyrose-flagship' ); ?></p>
		<h2 class="lux-heading rv rv-d1"><?php esc_html_e( 'Every Detail. Intentional.', 'skyyrose-flagship' ); ?></h2>
	</div>
	<div class="lux-craft-grid">
		<?php
		$craft_items = array(
			array(
				'icon'  => '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#B76E79" stroke-width="1.5"><path d="M12 2L2 7l10 5 10-5-10-5Z"/><path d="M2 17l10 5 10-5M2 12l10 5 10-5"/></svg>',
				'title' => __( '380gsm+ Fabric', 'skyyrose-flagship' ),
				'desc'  => __( '2x the weight of typical streetwear. Pick it up — you\'ll feel the difference.', 'skyyrose-flagship' ),
			),
			array(
				'icon'  => '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#B76E79" stroke-width="1.5"><path d="M4 7V4h16v3M9 20h6M12 4v16"/><path d="M8 4l4-2 4 2"/></svg>',
				'title' => __( 'Numbered Editions', 'skyyrose-flagship' ),
				'desc'  => __( 'Every piece comes with a numbered authentication card. When they\'re gone, they\'re gone.', 'skyyrose-flagship' ),
			),
			array(
				'icon'  => '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#B76E79" stroke-width="1.5"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
				'title' => __( 'Gender Neutral', 'skyyrose-flagship' ),
				'desc'  => __( 'Pioneer in Bay Area gender-neutral fashion. Designed for anyone, regardless of gender or age.', 'skyyrose-flagship' ),
			),
			array(
				'icon'  => '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#B76E79" stroke-width="1.5"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/><circle cx="12" cy="10" r="3"/></svg>',
				'title' => __( '3D Experiences', 'skyyrose-flagship' ),
				'desc'  => __( 'Explore collections through immersive 3D worlds before you buy. Fashion meets technology.', 'skyyrose-flagship' ),
			),
		);

		$ci = 1;
		foreach ( $craft_items as $item ) :
		?>
		<div class="lux-craft-card rv rv-d<?php echo esc_attr( $ci ); ?>">
			<div class="lux-craft-card__icon" aria-hidden="true"><?php
				// SVG icons — developer-controlled, not user input.
				echo $item['icon']; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
			?></div>
			<h3 class="lux-craft-card__title"><?php echo esc_html( $item['title'] ); ?></h3>
			<p class="lux-craft-card__desc"><?php echo esc_html( $item['desc'] ); ?></p>
		</div>
		<?php
			$ci++;
		endforeach;
		?>
	</div>
</section>

<?php if ( ! empty( $preorder_products ) ) : ?>
<!-- ════════════════════════════════════════════════
     FEATURED DROPS
     ════════════════════════════════════════════════ -->
<section class="lux-drops" id="drops" aria-label="<?php esc_attr_e( 'Featured Drops', 'skyyrose-flagship' ); ?>">
	<div class="lux-section-head">
		<p class="lux-eyebrow rv"><?php esc_html_e( 'Limited Pre-Order', 'skyyrose-flagship' ); ?></p>
		<h2 class="lux-heading rv rv-d1"><?php esc_html_e( 'Current Drops', 'skyyrose-flagship' ); ?></h2>
	</div>
	<div class="lux-drops-grid">
		<?php
		$di = 0;
		foreach ( array_slice( $preorder_products, 0, 4 ) as $product ) :
			$sku        = esc_attr( $product['sku'] );
			$name       = esc_html( $product['name'] );
			$image_path = ! empty( $product['front_model_image'] ) ? $product['front_model_image'] : $product['image'];
			$image_url  = esc_url( skyyrose_product_image_uri( $image_path ) );
			$price      = skyyrose_format_price( $product );
			$delay      = $di > 0 ? ' rv-d' . $di : '';
		?>
		<div class="lux-drop-card rv<?php echo esc_attr( $delay ); ?>" data-sku="<?php echo $sku; ?>">
			<div class="lux-drop-card__img">
				<img src="<?php echo $image_url; ?>"
				     alt="<?php echo $name; ?>"
				     width="420" height="560" loading="lazy">
				<span class="lux-drop-card__badge"><?php esc_html_e( 'Pre-Order', 'skyyrose-flagship' ); ?></span>
			</div>
			<div class="lux-drop-card__info">
				<h3 class="lux-drop-card__name"><?php echo $name; ?></h3>
				<span class="lux-drop-card__price"><?php echo wp_kses_post( $price ); ?></span>
				<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>" class="lux-drop-card__cta">
					<?php esc_html_e( 'Pre-Order Now', 'skyyrose-flagship' ); ?>
				</a>
			</div>
		</div>
		<?php
			$di++;
		endforeach;
		?>
	</div>
	<div class="lux-drops-more rv">
		<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>" class="lux-btn lux-btn--fill">
			<?php esc_html_e( 'View All Drops', 'skyyrose-flagship' ); ?>
		</a>
	</div>
</section>
<?php endif; ?>

<!-- ════════════════════════════════════════════════
     NEWSLETTER CTA
     ════════════════════════════════════════════════ -->
<section class="lux-newsletter" aria-label="<?php esc_attr_e( 'Newsletter Signup', 'skyyrose-flagship' ); ?>">
	<div class="lux-newsletter__inner">
		<p class="lux-eyebrow rv"><?php esc_html_e( 'Join the Movement', 'skyyrose-flagship' ); ?></p>
		<h2 class="lux-heading rv rv-d1"><?php esc_html_e( 'Early Access. Exclusive Drops. No Spam.', 'skyyrose-flagship' ); ?></h2>
		<form class="lux-newsletter__form rv rv-d2"
		      action="<?php echo esc_url( admin_url( 'admin-ajax.php' ) ); ?>" method="post">
			<?php wp_nonce_field( 'skyyrose_newsletter', 'skyyrose_newsletter_nonce' ); ?>
			<input type="hidden" name="action" value="skyyrose_newsletter_subscribe">
			<input type="email" name="email" class="lux-newsletter__input"
			       placeholder="<?php esc_attr_e( 'Enter your email', 'skyyrose-flagship' ); ?>"
			       required aria-label="<?php esc_attr_e( 'Email address', 'skyyrose-flagship' ); ?>">
			<button type="submit" class="lux-newsletter__btn">
				<?php esc_html_e( 'Join', 'skyyrose-flagship' ); ?>
			</button>
		</form>
		<div class="lux-newsletter__msg" aria-live="polite"></div>
		<p class="lux-newsletter__note rv rv-d3"><?php esc_html_e( 'Join 15,800+ members who never miss a drop', 'skyyrose-flagship' ); ?></p>
	</div>
</section>

</main><!-- #primary -->

<style>
/* ═══════════════════════════════════════════════════
   LUXURY HOMEPAGE v4.2 — Dark Cinematic
   ═══════════════════════════════════════════════════ */
.lux-page { background: #08080A; color: #e8e8e8; overflow-x: hidden; }

/* ── SCROLL REVEAL ── */
.rv { opacity: 0; transform: translateY(30px); transition: opacity .7s cubic-bezier(.16,1,.3,1), transform .7s cubic-bezier(.16,1,.3,1); }
.rv.visible { opacity: 1; transform: translateY(0); }
.rv-d1 { transition-delay: .12s; }
.rv-d2 { transition-delay: .24s; }
.rv-d3 { transition-delay: .36s; }
.rv-d4 { transition-delay: .48s; }
.rv-l { opacity: 0; transform: translateX(-40px); transition: opacity .8s cubic-bezier(.16,1,.3,1), transform .8s cubic-bezier(.16,1,.3,1); }
.rv-l.visible { opacity: 1; transform: translateX(0); }

/* ── HERO ── */
.lux-hero { position: relative; min-height: 100vh; display: flex; align-items: center; justify-content: center; overflow: hidden; }
.lux-hero__bg { position: absolute; inset: 0; z-index: 0; }
.lux-hero__bg img { width: 100%; height: 100%; object-fit: cover; }
.lux-hero__overlay { position: absolute; inset: 0; z-index: 1; background: linear-gradient(180deg, rgba(8,8,10,.55) 0%, rgba(8,8,10,.85) 100%); }
.lux-hero__content { position: relative; z-index: 2; text-align: center; max-width: 800px; padding: 2rem; }
.lux-hero__eyebrow { font-family: 'Bebas Neue', sans-serif; font-size: .875rem; letter-spacing: .3em; text-transform: uppercase; color: #B76E79; margin-bottom: 1rem; }
.lux-hero__title { font-family: 'Cinzel', serif; font-size: clamp(3rem, 8vw, 6rem); font-weight: 900; letter-spacing: .1em; color: #fff; margin: 0 0 .75rem; line-height: 1; }
.lux-hero__tagline { font-family: 'Cormorant Garamond', serif; font-size: clamp(1.1rem, 2.5vw, 1.5rem); font-style: italic; color: rgba(255,255,255,.7); margin-bottom: 2rem; }
.lux-hero__scroll { position: absolute; bottom: 2rem; left: 50%; transform: translateX(-50%); z-index: 2; animation: float 3s ease-in-out infinite; }
@keyframes float { 0%,100% { transform: translateX(-50%) translateY(0); } 50% { transform: translateX(-50%) translateY(8px); } }

/* ── BUTTONS ── */
.lux-btn { display: inline-flex; align-items: center; gap: .5rem; padding: .875rem 2rem; font-family: 'Bebas Neue', sans-serif; font-size: 1rem; letter-spacing: .15em; text-transform: uppercase; text-decoration: none; color: #fff; border: 1px solid rgba(255,255,255,.25); border-radius: 0; transition: all .35s cubic-bezier(.16,1,.3,1); }
.lux-btn:hover { border-color: #B76E79; color: #B76E79; transform: translateY(-2px); }
.lux-btn--fill { background: #B76E79; border-color: #B76E79; color: #fff; }
.lux-btn--fill:hover { background: #a55e6a; border-color: #a55e6a; color: #fff; }
.lux-hero__ctas { display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; }

/* ── PRESS STRIP ── */
.lux-press { display: flex; align-items: center; justify-content: center; gap: 2.5rem; padding: 1.25rem 2rem; background: #0c0c0e; border-top: 1px solid rgba(255,255,255,.06); border-bottom: 1px solid rgba(255,255,255,.06); flex-wrap: wrap; }
.lux-press__label { font-family: 'Bebas Neue', sans-serif; font-size: .75rem; letter-spacing: .2em; text-transform: uppercase; color: rgba(255,255,255,.35); }
.lux-press__logo { font-family: 'Cinzel', serif; font-size: .9rem; font-weight: 600; color: rgba(255,255,255,.25); letter-spacing: .05em; text-transform: uppercase; }

/* ── SECTION HEAD ── */
.lux-section-head { text-align: center; padding: 5rem 2rem 3rem; }
.lux-eyebrow { font-family: 'Bebas Neue', sans-serif; font-size: .8rem; letter-spacing: .3em; text-transform: uppercase; color: #B76E79; margin-bottom: .75rem; }
.lux-heading { font-family: 'Cinzel', serif; font-size: clamp(1.75rem, 4vw, 2.5rem); font-weight: 700; color: #fff; margin: 0; line-height: 1.2; }

/* ── COLLECTIONS GRID ── */
.lux-cols-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 2px; padding: 0 2rem 5rem; max-width: 1400px; margin: 0 auto; }
.lux-col-card { position: relative; overflow: hidden; aspect-ratio: 4/5; }
.lux-col-card__link { display: block; width: 100%; height: 100%; text-decoration: none; color: #fff; }
.lux-col-card__img { position: absolute; inset: 0; }
.lux-col-card__img img { width: 100%; height: 100%; object-fit: cover; transition: transform .6s cubic-bezier(.16,1,.3,1); }
.lux-col-card:hover .lux-col-card__img img { transform: scale(1.06); }
.lux-col-card__overlay { position: absolute; inset: 0; background: linear-gradient(180deg, transparent 30%, rgba(8,8,10,.9) 100%); z-index: 1; transition: background .4s ease; }
.lux-col-card:hover .lux-col-card__overlay { background: linear-gradient(180deg, transparent 20%, rgba(8,8,10,.95) 100%); }
.lux-col-card__content { position: absolute; bottom: 0; left: 0; right: 0; padding: 2rem; z-index: 2; }
.lux-col-card__num { font-family: 'Bebas Neue', sans-serif; font-size: .7rem; letter-spacing: .4em; color: var(--card-accent, #B76E79); text-transform: uppercase; }
.lux-col-card__name { font-family: 'Cinzel', serif; font-size: clamp(1.5rem, 3vw, 2rem); font-weight: 700; margin: .25rem 0 .5rem; }
.lux-col-card__logo { max-width: min(280px, 70%); height: auto; filter: drop-shadow(0 2px 12px rgba(0,0,0,.5)); transition: transform .4s ease, filter .4s ease; }
.lux-col-card:hover .lux-col-card__logo { transform: scale(1.04); filter: drop-shadow(0 4px 20px rgba(0,0,0,.6)); }
.lux-col-card__tagline { font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: .95rem; color: rgba(255,255,255,.6); margin-bottom: .5rem; }
.lux-col-card__desc { font-size: .85rem; line-height: 1.5; color: rgba(255,255,255,.5); margin-bottom: 1rem; max-height: 0; overflow: hidden; transition: max-height .4s ease, opacity .4s ease; opacity: 0; }
.lux-col-card:hover .lux-col-card__desc { max-height: 4rem; opacity: 1; }
.lux-col-card__cta { display: inline-flex; align-items: center; gap: .4rem; font-family: 'Bebas Neue', sans-serif; font-size: .8rem; letter-spacing: .2em; text-transform: uppercase; color: var(--card-accent, #B76E79); }

/* ── STORY ── */
.lux-story { display: grid; grid-template-columns: 1fr 1fr; min-height: 80vh; }
.lux-story__image { overflow: hidden; }
.lux-story__image img { width: 100%; height: 100%; object-fit: cover; }
.lux-story__text { display: flex; flex-direction: column; justify-content: center; padding: 4rem; background: #0c0c0e; }
.lux-body { font-family: 'Cormorant Garamond', serif; font-size: 1.1rem; line-height: 1.8; color: rgba(255,255,255,.65); margin-bottom: 1.5rem; }
.lux-quote { font-family: 'Cormorant Garamond', serif; font-size: 1.15rem; font-style: italic; color: rgba(255,255,255,.5); border-left: 2px solid #B76E79; padding-left: 1.5rem; margin: 0 0 2rem; line-height: 1.7; }
.lux-quote cite { display: block; margin-top: .75rem; font-size: .85rem; font-style: normal; color: #B76E79; letter-spacing: .05em; }

/* ── CRAFT ── */
.lux-craft { padding-bottom: 5rem; }
.lux-craft-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.5rem; max-width: 1200px; margin: 0 auto; padding: 0 2rem; }
.lux-craft-card { background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.06); padding: 2rem; transition: border-color .3s ease, transform .3s ease; }
.lux-craft-card:hover { border-color: rgba(183,110,121,.3); transform: translateY(-4px); }
.lux-craft-card__icon { margin-bottom: 1rem; }
.lux-craft-card__title { font-family: 'Cinzel', serif; font-size: 1rem; font-weight: 600; color: #fff; margin-bottom: .5rem; }
.lux-craft-card__desc { font-size: .85rem; line-height: 1.6; color: rgba(255,255,255,.5); }

/* ── DROPS ── */
.lux-drops { padding-bottom: 3rem; }
.lux-drops-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.5rem; max-width: 1200px; margin: 0 auto; padding: 0 2rem; }
.lux-drop-card { background: rgba(255,255,255,.02); border: 1px solid rgba(255,255,255,.06); overflow: hidden; transition: border-color .3s ease; }
.lux-drop-card:hover { border-color: rgba(183,110,121,.3); }
.lux-drop-card__img { position: relative; aspect-ratio: 3/4; overflow: hidden; }
.lux-drop-card__img img { width: 100%; height: 100%; object-fit: cover; transition: transform .5s cubic-bezier(.16,1,.3,1); }
.lux-drop-card:hover .lux-drop-card__img img { transform: scale(1.05); }
.lux-drop-card__badge { position: absolute; top: .75rem; left: .75rem; font-family: 'Bebas Neue', sans-serif; font-size: .65rem; letter-spacing: .2em; text-transform: uppercase; background: #B76E79; color: #fff; padding: .25rem .75rem; }
.lux-drop-card__info { padding: 1.25rem; }
.lux-drop-card__name { font-family: 'Cinzel', serif; font-size: .9rem; font-weight: 600; color: #fff; margin-bottom: .35rem; }
.lux-drop-card__price { font-family: 'Bebas Neue', sans-serif; font-size: 1rem; color: #B76E79; letter-spacing: .05em; }
.lux-drop-card__cta { display: block; margin-top: .75rem; font-family: 'Bebas Neue', sans-serif; font-size: .75rem; letter-spacing: .2em; text-transform: uppercase; color: rgba(255,255,255,.5); text-decoration: none; transition: color .3s ease; }
.lux-drop-card__cta:hover { color: #B76E79; }
.lux-drops-more { text-align: center; padding: 2rem 0 3rem; }

/* ── NEWSLETTER ── */
.lux-newsletter { padding: 5rem 2rem; text-align: center; background: linear-gradient(180deg, #08080A 0%, #0e0c0d 50%, #08080A 100%); }
.lux-newsletter__inner { max-width: 600px; margin: 0 auto; }
.lux-newsletter__form { display: flex; gap: 0; margin-top: 1.5rem; }
.lux-newsletter__input { flex: 1; padding: .875rem 1.25rem; background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.12); border-right: none; color: #fff; font-family: 'Cormorant Garamond', serif; font-size: 1rem; }
.lux-newsletter__input::placeholder { color: rgba(255,255,255,.3); }
.lux-newsletter__btn { padding: .875rem 2rem; background: #B76E79; border: 1px solid #B76E79; color: #fff; font-family: 'Bebas Neue', sans-serif; font-size: .9rem; letter-spacing: .15em; text-transform: uppercase; cursor: pointer; transition: background .3s ease; }
.lux-newsletter__btn:hover { background: #a55e6a; }
.lux-newsletter__msg { margin-top: .75rem; font-size: .85rem; }
.lux-newsletter__note { font-size: .8rem; color: rgba(255,255,255,.3); margin-top: 1rem; }

/* ── RESPONSIVE ── */
@media (max-width: 1024px) {
	.lux-cols-grid { grid-template-columns: 1fr; padding: 0 1rem 3rem; }
	.lux-col-card { aspect-ratio: 16/9; }
	.lux-craft-grid, .lux-drops-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 768px) {
	.lux-story { grid-template-columns: 1fr; }
	.lux-story__image { aspect-ratio: 4/3; }
	.lux-story__text { padding: 2.5rem 1.5rem; }
	.lux-craft-grid, .lux-drops-grid { grid-template-columns: 1fr; }
	.lux-newsletter__form { flex-direction: column; }
	.lux-newsletter__input { border-right: 1px solid rgba(255,255,255,.12); }
	.lux-hero__ctas { flex-direction: column; align-items: center; }
	.lux-press { gap: 1.5rem; }
}
</style>

<script>
/* Scroll-reveal observer for .rv / .rv-l elements */
(function(){
	if (!('IntersectionObserver' in window)) {
		document.querySelectorAll('.rv,.rv-l').forEach(function(el) { el.classList.add('visible'); });
		return;
	}
	var obs = new IntersectionObserver(function(entries) {
		entries.forEach(function(e) { if (e.isIntersecting) { e.target.classList.add('visible'); obs.unobserve(e.target); } });
	}, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
	document.querySelectorAll('.lux-page .rv, .lux-page .rv-l').forEach(function(el) { obs.observe(el); });
})();

/* Newsletter AJAX */
(function(){
	var form = document.querySelector('.lux-newsletter__form');
	if (!form) return;
	form.addEventListener('submit', function(e) {
		e.preventDefault();
		var msg = form.parentElement.querySelector('.lux-newsletter__msg');
		var fd = new FormData(form);
		fetch(form.action, { method: 'POST', body: fd })
			.then(function(r) { return r.json(); })
			.then(function(d) {
				if (msg) { msg.textContent = d.success ? 'Welcome to the family.' : (d.data || 'Something went wrong.'); msg.style.color = d.success ? '#B76E79' : '#DC143C'; }
				if (d.success) form.reset();
			})
			.catch(function() { if (msg) { msg.textContent = 'Connection error. Try again.'; msg.style.color = '#DC143C'; } });
	});
})();
</script>

<?php get_footer(); ?>
