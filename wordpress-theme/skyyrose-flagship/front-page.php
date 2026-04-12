<?php
/**
 * Front Page — SkyyRose v6.0 Editorial Homepage
 *
 * Cinematic hero, press strip, marquee, founder story, quote,
 * collection cards with photography, lookbook, craft, newsletter.
 *
 * Layout ported from the proven v4.0 homepage design.
 * CSS: assets/css/homepage-v2.css
 * JS: assets/js/homepage-v2.js
 *
 * @package SkyyRose_Flagship
 * @since   6.0.0
 */

defined( 'ABSPATH' ) || exit;

/* ── Data ──────────────────────────────────────────────────────────────────── */

$hero_bg     = SKYYROSE_ASSETS_URI . '/images/homepage-hero-bg.webp';
$founder_img = SKYYROSE_ASSETS_URI . '/images/homepage-story-founder.webp';
$cart_url    = function_exists( 'wc_get_cart_url' ) ? wc_get_cart_url() : home_url( '/cart/' );

/* Collection data sourced from inc/collections-config.php (single source of truth). */
$collections = skyyrose_get_front_page_collections();

/* Dynamic product counts per collection */
foreach ( $collections as &$col ) {
	$col['count'] = 0;
	if ( function_exists( 'wc_get_products' ) ) {
		$products     = wc_get_products(
			array(
				'category' => array( $col['slug'] ),
				'limit'    => -1,
				'return'   => 'ids',
				'status'   => 'publish',
			)
		);
		$col['count'] = count( $products );
	}
}
unset( $col );

/* Press features */
$press = array(
	__( 'Maxim', 'skyyrose' ),
	__( 'CEO Weekly', 'skyyrose' ),
	__( 'San Francisco Post', 'skyyrose' ),
	__( 'Best of Best Review', 'skyyrose' ),
	__( 'The Blox', 'skyyrose' ),
);

/* Marquee items */
$marquee = array(
	'Black Rose',
	'Love Hurts',
	'Signature',
	'Oakland Made',
	'Gender Neutral',
	'Limited Edition',
	'Luxury Streetwear',
	'Built Different',
);

/* Lookbook images */
$lookbook = array(
	array(
		'file'  => 'lb-love-hurts-varsity',
		'alt'   => __( 'Love Hurts varsity jacket', 'skyyrose' ),
		'label' => 'Love Hurts',
		'tall'  => true,
	),
	array(
		'file'  => 'lb-black-rose-hockey',
		'alt'   => __( 'Black Rose hockey jersey', 'skyyrose' ),
		'label' => 'Black Rose',
		'tall'  => false,
	),
	array(
		'file'  => 'lb-kid-black-rose',
		'alt'   => __( 'Kid in Black Rose hoodie', 'skyyrose' ),
		'label' => 'Street Style',
		'tall'  => false,
	),
	array(
		'file'  => 'lb-rose-hoodie-beanie',
		'alt'   => __( 'Rose hoodie and beanie', 'skyyrose' ),
		'label' => 'Signature',
		'tall'  => false,
	),
	array(
		'file'  => 'lb-black-rose-football',
		'alt'   => __( 'Black Rose football jersey', 'skyyrose' ),
		'label' => 'Limited Edition',
		'tall'  => false,
	),
);

/* Craft cards */
$craft_cards = array(
	array(
		'icon'  => '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5Z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>',
		'label' => __( 'Premium Materials', 'skyyrose' ),
		'desc'  => __( '280-400gsm cotton. Italian wool blends. Full-grain leather. No shortcuts.', 'skyyrose' ),
	),
	array(
		'icon'  => '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
		'label' => __( 'Oakland Made Mentality', 'skyyrose' ),
		'desc'  => __( 'Born from the struggle of East Oakland. Designed for the world. Built to last generations.', 'skyyrose' ),
	),
	array(
		'icon'  => '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
		'label' => __( 'Gender Neutral', 'skyyrose' ),
		'desc'  => __( 'Pioneer in Bay Area gender-neutral fashion. Designed for anyone, regardless of gender or age.', 'skyyrose' ),
	),
	array(
		'icon'  => '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
		'label' => __( 'Limited Editions', 'skyyrose' ),
		'desc'  => __( 'Small batch production. Individually numbered. When it\'s gone, it\'s gone.', 'skyyrose' ),
	),
);

$svg_whitelist = array(
	'svg'     => array(
		'width'           => true,
		'height'          => true,
		'viewBox'         => true,
		'fill'            => true,
		'stroke'          => true,
		'stroke-width'    => true,
		'stroke-linecap'  => true,
		'stroke-linejoin' => true,
		'aria-hidden'     => true,
		'focusable'       => true,
		'xmlns'           => true,
	),
	'path'    => array(
		'd'            => true,
		'fill'         => true,
		'stroke'       => true,
		'stroke-width' => true,
	),
	'circle'  => array(
		'cx'   => true,
		'cy'   => true,
		'r'    => true,
		'fill' => true,
	),
	'polygon' => array(
		'points' => true,
		'fill'   => true,
	),
);

get_header();
?>

<main id="primary" class="site-main homepage-v2" role="main" tabindex="-1">

<div class="grain" aria-hidden="true"></div>
<div class="vignette" aria-hidden="true"></div>
<div class="scroll-progress" aria-hidden="true"></div>

<noscript><style>#loader{display:none!important}</style></noscript>

<!-- ═══ LOADER ═══ -->
<div id="loader" role="status" aria-label="<?php esc_attr_e( 'Loading', 'skyyrose' ); ?>">
	<span class="ld-brand"><?php esc_html_e( 'SkyyRose', 'skyyrose' ); ?></span>
	<span class="ld-tag"><?php esc_html_e( 'Luxury Grows from Concrete', 'skyyrose' ); ?></span>
	<div class="ld-bar"><div class="ld-fill" id="ldFill"></div></div>
</div>

<!-- ═══ MOBILE MENU ═══ -->
<div class="mob-menu" id="mobMenu" role="dialog" aria-label="<?php esc_attr_e( 'Mobile Navigation', 'skyyrose' ); ?>">
	<button class="mob-close" type="button" aria-label="<?php esc_attr_e( 'Close menu', 'skyyrose' ); ?>">&times;</button>
	<a href="#story"><?php esc_html_e( 'Our Story', 'skyyrose' ); ?></a>
	<a href="#collections"><?php esc_html_e( 'Collections', 'skyyrose' ); ?></a>
	<a href="#lookbook"><?php esc_html_e( 'Lookbook', 'skyyrose' ); ?></a>
	<a href="#craft"><?php esc_html_e( 'Craft', 'skyyrose' ); ?></a>
	<a href="#community"><?php esc_html_e( 'Community', 'skyyrose' ); ?></a>
	<a href="<?php echo esc_url( $cart_url ); ?>"><?php esc_html_e( 'Bag', 'skyyrose' ); ?></a>
</div>

<!-- ═══ NAV ═══ -->
<nav class="nav" id="mainNav" aria-label="<?php esc_attr_e( 'Homepage Navigation', 'skyyrose' ); ?>">
	<a href="<?php echo esc_url( home_url( '/' ) ); ?>" class="nav-brand">
		<span class="nav-name"><?php esc_html_e( 'SkyyRose', 'skyyrose' ); ?></span>
		<span class="nav-sub"><?php esc_html_e( 'Oakland Luxury', 'skyyrose' ); ?></span>
	</a>
	<div class="nav-center">
		<a href="#story" class="nav-link"><?php esc_html_e( 'Story', 'skyyrose' ); ?></a>
		<a href="#collections" class="nav-link"><?php esc_html_e( 'Collections', 'skyyrose' ); ?></a>
		<a href="#lookbook" class="nav-link"><?php esc_html_e( 'Lookbook', 'skyyrose' ); ?></a>
		<a href="#craft" class="nav-link"><?php esc_html_e( 'Craft', 'skyyrose' ); ?></a>
		<a href="#community" class="nav-link"><?php esc_html_e( 'Community', 'skyyrose' ); ?></a>
	</div>
	<div class="nav-right">
		<button class="nav-bag" type="button" aria-label="<?php esc_attr_e( 'Shopping Bag', 'skyyrose' ); ?>">
			<?php esc_html_e( 'Bag', 'skyyrose' ); ?>
			<span class="bag-ct" id="bagCt">0</span>
		</button>
		<button class="nav-ham" type="button" aria-label="<?php esc_attr_e( 'Open menu', 'skyyrose' ); ?>">
			<span></span><span></span><span></span>
		</button>
	</div>
</nav>

<!-- ═══ HERO ═══ -->
<section class="hero" id="hero" data-scroll-fade aria-label="<?php esc_attr_e( 'SkyyRose Hero', 'skyyrose' ); ?>">
	<div class="hero-bg parallax-ken-burns" style="background-image: url('<?php echo esc_url( $hero_bg ); ?>');" aria-hidden="true"></div>
	<div class="hero-ov" aria-hidden="true"></div>
	<div class="hero-particles" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i></div>
	<div class="hero-frame" aria-hidden="true"></div>
	<div class="hero-content">
		<p class="hero-eyebrow rv-blur-down"><?php esc_html_e( 'Oakland · Est. 2020 · Gender Neutral', 'skyyrose' ); ?></p>
		<h1 class="hero-title rv-split-char" aria-label="<?php esc_attr_e( 'SkyyRose', 'skyyrose' ); ?>">SkyyRose</h1>
		<div class="hero-rule" aria-hidden="true"></div>
		<p class="hero-subtitle rv-blur"><?php esc_html_e( 'Luxury Grows from Concrete. Three collections, one vision — built by a father, named after a daughter.', 'skyyrose' ); ?></p>
		<div class="hero-ctas">
			<a href="#collections" class="hero-cta hero-cta-primary btn-sweep btn-press"><?php esc_html_e( 'Explore Collections', 'skyyrose' ); ?></a>
			<a href="#story" class="hero-cta btn-border-draw btn-press"><?php esc_html_e( 'Our Story', 'skyyrose' ); ?></a>
		</div>
	</div>
	<div class="hero-scroll" aria-hidden="true">
		<span><?php esc_html_e( 'Scroll', 'skyyrose' ); ?></span>
		<div class="hero-scroll-line"></div>
	</div>
</section>

<!-- ═══ PRESS STRIP ═══ -->
<div class="press rv">
	<p class="press-label"><?php esc_html_e( 'As Featured In', 'skyyrose' ); ?></p>
	<div class="press-logos">
		<?php foreach ( $press as $idx => $name ) : ?>
			<?php
			if ( $idx > 0 ) :
				?>
				<span class="press-sep" aria-hidden="true"></span><?php endif; ?>
			<span class="press-item"><?php echo esc_html( $name ); ?></span>
		<?php endforeach; ?>
	</div>
</div>

<!-- ═══ MARQUEE ═══ -->
<div class="marquee" aria-hidden="true">
	<div class="marquee-track">
		<?php for ( $i = 0; $i < 2; $i++ ) : ?>
			<?php foreach ( $marquee as $item ) : ?>
				<span class="mq-item"><?php echo esc_html( $item ); ?><span class="mq-dot"></span></span>
			<?php endforeach; ?>
		<?php endfor; ?>
	</div>
</div>

<!-- ═══ STORY ═══ -->
<section class="story" id="story" aria-label="<?php esc_attr_e( 'Our Story', 'skyyrose' ); ?>">
	<div class="story-bg" aria-hidden="true"></div>
	<div class="story-inner">
		<div>
			<p class="story-eyebrow rv"><?php esc_html_e( 'The Origin', 'skyyrose' ); ?></p>
			<h2 class="story-heading rv rv-d1">
				<?php
				/* translators: line break for visual layout */
				echo wp_kses( __( 'Born In<br>The Town', 'skyyrose' ), array( 'br' => array() ) );
				?>
				<em><?php esc_html_e( "A father's promise. A daughter's name.", 'skyyrose' ); ?></em>
			</h2>
			<div class="story-body rv rv-d2">
				<p><?php echo wp_kses_post( __( 'In a neighborhood where opportunities are as scarce as support, <strong>Corey Foster</strong> refused to become another statistic. He\'d lost everything — broke, no drive left, a baby on the way.', 'skyyrose' ) ); ?></p>
				<p><?php echo wp_kses_post( __( 'Through failed websites, scammer manufacturers, and single parenthood with no support — he built something real. Named after his daughter <strong>Skyy Rose</strong>. Designed for anyone, regardless of gender or age.', 'skyyrose' ) ); ?></p>
				<p><?php esc_html_e( "SkyyRose isn't just clothing. It's proof that your circumstances don't define your destination.", 'skyyrose' ); ?></p>
			</div>
			<div class="story-stats rv rv-d3">
				<div><div class="stat-num">3</div><div class="stat-label"><?php esc_html_e( 'Collections', 'skyyrose' ); ?></div></div>
				<div><div class="stat-num"><?php echo esc_html( array_sum( array_column( $collections, 'count' ) ) ?: '29' ); ?></div><div class="stat-label"><?php esc_html_e( 'Pieces', 'skyyrose' ); ?></div></div>
				<div><div class="stat-num">2020</div><div class="stat-label"><?php esc_html_e( 'Founded', 'skyyrose' ); ?></div></div>
				<div><div class="stat-num">5+</div><div class="stat-label"><?php esc_html_e( 'Press Features', 'skyyrose' ); ?></div></div>
			</div>
		</div>
		<div class="story-img-wrap rv-right">
			<div class="story-img">
				<img src="<?php echo esc_url( $founder_img ); ?>"
					alt="<?php esc_attr_e( 'Corey Foster, SkyyRose founder', 'skyyrose' ); ?>"
					loading="lazy" decoding="async" width="600" height="800">
			</div>
			<div class="story-float">
				<div class="sf-lbl"><?php esc_html_e( 'Recognition', 'skyyrose' ); ?></div>
				<div class="sf-val"><?php echo wp_kses( __( 'Best Bay Area<br>Clothing Line 2024', 'skyyrose' ), array( 'br' => array() ) ); ?></div>
			</div>
		</div>
	</div>
</section>

<!-- ═══ QUOTE ═══ -->
<section class="quote-section" aria-label="<?php esc_attr_e( 'Founder Quote', 'skyyrose' ); ?>">
	<div class="quote-mark rv" aria-hidden="true">&ldquo;</div>
	<blockquote class="quote-text rv rv-d1">
		<?php echo wp_kses_post( __( '&ldquo;If you asked me four years ago, I never would have thought I&rsquo;d be here. I had no drive, lost it all, a baby on the way, and was broke. But we knew we had to get it <em>by any means necessary</em>.&rdquo;', 'skyyrose' ) ); ?>
	</blockquote>
	<p class="quote-attr rv rv-d2"><?php echo esc_html( '— ' . __( 'Corey Foster, Founder & CEO', 'skyyrose' ) ); ?></p>
</section>

<!-- ═══ COLLECTIONS ═══ -->
<section class="collections" id="collections" aria-label="<?php esc_attr_e( 'Our Collections', 'skyyrose' ); ?>">
	<div class="col-header rv-clip-up">
		<p class="col-header-eyebrow"><?php esc_html_e( 'The Collections', 'skyyrose' ); ?></p>
		<h2 class="col-header-title rv-split-word"><?php esc_html_e( 'Three Worlds. One Vision.', 'skyyrose' ); ?></h2>
	</div>
	<div class="col-grid stagger-grid">
		<?php foreach ( $collections as $idx => $col ) : ?>
			<a href="<?php echo esc_url( $col['link'] ); ?>" class="col-card <?php echo esc_attr( $col['class'] ); ?> magnetic">
				<div class="col-card-img">
					<img src="<?php echo esc_url( $col['image'] ); ?>"
						alt="<?php echo esc_attr( $col['name'] . ' Collection' ); ?>"
						loading="lazy" decoding="async" width="480" height="640">
				</div>
				<div class="col-card-ov"></div>
				<div class="col-card-content">
					<p class="col-card-num"><?php echo esc_html( $col['num'] ); ?></p>
					<h3 class="col-card-name"><?php echo wp_kses( $col['title'], array( 'br' => array() ) ); ?></h3>
					<p class="col-card-tag"><?php echo esc_html( $col['tagline'] ); ?></p>
					<div class="col-card-meta">
						<span><?php echo esc_html( ( $col['count'] ?: '—' ) . ' ' . __( 'Pieces', 'skyyrose' ) ); ?></span>
						<span><?php echo esc_html( $col['label'] ); ?></span>
					</div>
					<span class="col-card-cta"><?php esc_html_e( 'Explore Collection', 'skyyrose' ); ?></span>
				</div>
			</a>
		<?php endforeach; ?>
	</div>
</section>

<!-- ═══ FEATURED PRODUCTS ═══ -->
<?php
get_template_part(
	'template-parts/product-grid',
	null,
	array(
		'featured'      => true,
		'limit'         => 8,
		'heading'       => __( 'Featured', 'skyyrose' ),
		'subheading'    => __( 'Shop the staples — limited editions, Oakland-made.', 'skyyrose' ),
		'section_id'    => 'featured',
		'section_class' => 'fp-featured',
		'reveal_class'  => 'rv-clip-up',
	)
);
?>

<!-- ═══ LOOKBOOK ═══ -->
<section class="lookbook" id="lookbook" aria-label="<?php esc_attr_e( 'Lookbook', 'skyyrose' ); ?>">
	<div class="lookbook-header rv-clip-up">
		<h2><?php esc_html_e( 'Lookbook', 'skyyrose' ); ?></h2>
		<p><?php esc_html_e( 'Real people. Real style. Oakland made.', 'skyyrose' ); ?></p>
	</div>
	<div class="lookbook-grid stagger-grid">
		<?php
		foreach ( $lookbook as $lb ) :
			$lb_base = SKYYROSE_ASSETS_URI . '/images/lookbook/' . $lb['file'];
			?>
			<div class="lb-img rv<?php echo $lb['tall'] ? ' tall' : ''; ?>">
				<img src="<?php echo esc_url( $lb_base . '-480w.webp' ); ?>"
					srcset="<?php echo esc_url( $lb_base . '-480w.webp' ); ?> 480w, <?php echo esc_url( $lb_base . '-960w.webp' ); ?> 960w"
					sizes="(max-width: 768px) 100vw, 480px"
					alt="<?php echo esc_attr( $lb['alt'] ); ?>"
					loading="lazy" decoding="async" width="480" height="640">
				<span class="lb-label"><?php echo esc_html( $lb['label'] ); ?></span>
			</div>
		<?php endforeach; ?>
	</div>
</section>

<!-- ═══ CRAFT ═══ -->
<section class="craft" id="craft" aria-label="<?php esc_attr_e( 'Our Craft', 'skyyrose' ); ?>">
	<div class="craft-inner">
		<div class="craft-header rv-clip-up">
			<h2><?php esc_html_e( 'The Craft', 'skyyrose' ); ?></h2>
			<p><?php esc_html_e( 'Every stitch, every fabric, every detail — intentional.', 'skyyrose' ); ?></p>
		</div>
		<div class="craft-grid stagger-grid">
			<?php foreach ( $craft_cards as $idx => $card ) : ?>
				<div class="craft-card">
					<div class="craft-icon" aria-hidden="true"><?php echo wp_kses( $card['icon'], $svg_whitelist ); ?></div>
					<div class="craft-label"><?php echo esc_html( $card['label'] ); ?></div>
					<p class="craft-desc"><?php echo esc_html( $card['desc'] ); ?></p>
				</div>
			<?php endforeach; ?>
		</div>
	</div>
</section>

<!-- ═══ NEWSLETTER ═══ -->
<section class="newsletter" id="community" aria-label="<?php esc_attr_e( 'Newsletter', 'skyyrose' ); ?>">
	<div class="nl-inner">
		<p class="nl-eyebrow rv-blur-down"><?php esc_html_e( 'Join the Movement', 'skyyrose' ); ?></p>
		<h2 class="nl-title rv-split-word"><?php esc_html_e( 'For The Real Ones', 'skyyrose' ); ?></h2>
		<p class="nl-desc rv-blur"><?php esc_html_e( 'Early access to drops. Behind-the-scenes from Oakland. Stories that matter. No spam, just substance.', 'skyyrose' ); ?></p>
		<div class="nl-form rv-clip-up">
			<input type="email" class="nl-input" placeholder="<?php esc_attr_e( 'Your email address', 'skyyrose' ); ?>" id="nlEmail" aria-label="<?php esc_attr_e( 'Email address', 'skyyrose' ); ?>" required>
			<button type="button" class="nl-submit"><?php esc_html_e( 'Join', 'skyyrose' ); ?></button>
		</div>
		<p class="nl-note rv rv-d4"><?php esc_html_e( 'Free to join · Unsubscribe anytime · Oakland love only', 'skyyrose' ); ?></p>
	</div>
</section>

<!-- ═══ FOOTER ═══ -->
<footer class="ft" aria-label="<?php esc_attr_e( 'Site Footer', 'skyyrose' ); ?>">
	<div class="ft-inner">
		<div>
			<div class="ft-brand-name rv"><?php esc_html_e( 'SkyyRose', 'skyyrose' ); ?></div>
			<p class="ft-desc rv rv-d1"><?php esc_html_e( 'Where Bay Area authenticity meets high-fashion aesthetics. Gender-neutral, sustainably crafted, limited edition designs. Built by a father, named after a daughter.', 'skyyrose' ); ?></p>
			<div class="ft-awards rv rv-d2">
				<span class="ft-award"><?php esc_html_e( "Maxim's 14 Game-Changing Entrepreneurs 2023", 'skyyrose' ); ?></span>
				<span class="ft-award"><?php esc_html_e( 'Best Bay Area Clothing Line 2024', 'skyyrose' ); ?></span>
				<span class="ft-award"><?php esc_html_e( 'Featured — San Francisco Post, CEO Weekly', 'skyyrose' ); ?></span>
			</div>
		</div>
		<div>
			<div class="ft-col-title rv"><?php esc_html_e( 'Collections', 'skyyrose' ); ?></div>
			<ul class="ft-links rv rv-d1">
				<li><a href="<?php echo esc_url( home_url( '/collection-black-rose/' ) ); ?>"><?php esc_html_e( 'Black Rose', 'skyyrose' ); ?></a></li>
				<li><a href="<?php echo esc_url( home_url( '/collection-love-hurts/' ) ); ?>"><?php esc_html_e( 'Love Hurts', 'skyyrose' ); ?></a></li>
				<li><a href="<?php echo esc_url( home_url( '/collection-signature/' ) ); ?>"><?php esc_html_e( 'Signature', 'skyyrose' ); ?></a></li>
			</ul>
		</div>
		<div>
			<div class="ft-col-title rv"><?php esc_html_e( 'Brand', 'skyyrose' ); ?></div>
			<ul class="ft-links rv rv-d1">
				<li><a href="<?php echo esc_url( home_url( '/about/' ) ); ?>"><?php esc_html_e( 'Our Story', 'skyyrose' ); ?></a></li>
				<li><a href="#lookbook"><?php esc_html_e( 'Lookbook', 'skyyrose' ); ?></a></li>
				<li><a href="<?php echo esc_url( home_url( '/about/' ) ); ?>"><?php esc_html_e( 'About', 'skyyrose' ); ?></a></li>
			</ul>
		</div>
		<div>
			<div class="ft-col-title rv"><?php esc_html_e( 'Support', 'skyyrose' ); ?></div>
			<ul class="ft-links rv rv-d1">
				<li><a href="<?php echo esc_url( home_url( '/shipping-returns/' ) ); ?>"><?php esc_html_e( 'Shipping & Returns', 'skyyrose' ); ?></a></li>
				<li><a href="mailto:info@skyyrose.co"><?php esc_html_e( 'Contact', 'skyyrose' ); ?></a></li>
				<li><a href="<?php echo esc_url( home_url( '/faq/' ) ); ?>"><?php esc_html_e( 'FAQ', 'skyyrose' ); ?></a></li>
			</ul>
		</div>
	</div>
	<div class="ft-bottom">
		<span class="ft-copy">&copy; <?php echo esc_html( gmdate( 'Y' ) ); ?> <?php esc_html_e( 'SkyyRose LLC. All rights reserved.', 'skyyrose' ); ?></span>
		<div class="ft-social">
			<a href="https://instagram.com/skyyroseco" target="_blank" rel="noopener noreferrer"><?php esc_html_e( 'Instagram', 'skyyrose' ); ?></a>
			<a href="https://tiktok.com/@skyyroseco" target="_blank" rel="noopener noreferrer"><?php esc_html_e( 'TikTok', 'skyyrose' ); ?></a>
			<a href="https://x.com/skyyroseco" target="_blank" rel="noopener noreferrer"><?php esc_html_e( 'X', 'skyyrose' ); ?></a>
		</div>
		<span class="ft-oakland"><?php esc_html_e( 'Made in Oakland', 'skyyrose' ); ?></span>
	</div>
</footer>

<script data-jetpack-boost="ignore" type="application/ld+json">
<?php
echo wp_json_encode(
	array(
		'@context'     => 'https://schema.org',
		'@type'        => 'Organization',
		'name'         => 'SkyyRose',
		'url'          => home_url( '/' ),
		'logo'         => SKYYROSE_ASSETS_URI . '/branding/skyyrose-monogram.webp',
		'description'  => 'Oakland luxury streetwear. Gender-neutral, limited edition designs. Built by a father, named after a daughter.',
		'foundingDate' => '2020',
		'founder'      => array(
			'@type' => 'Person',
			'name'  => 'Corey Foster',
		),
		'address'      => array(
			'@type'           => 'PostalAddress',
			'addressLocality' => 'Oakland',
			'addressRegion'   => 'CA',
			'addressCountry'  => 'US',
		),
		'sameAs'       => array( 'https://instagram.com/skyyroseco' ),
	),
	JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT
);
?>
</script>

<button type="button" class="back-to-top" aria-label="<?php esc_attr_e( 'Back to top', 'skyyrose' ); ?>">
	<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4l-8 8h5v8h6v-8h5z"/></svg>
</button>

</main><!-- .homepage-v2 -->

<?php
// Load homepage JS inline to bypass page-optimize plugin stripping.
$homepage_js_path = SKYYROSE_DIR . '/assets/js/homepage-v2.js';
if ( file_exists( $homepage_js_path ) ) :
	?>
<script>
	<?php
	// phpcs:ignore WordPress.WP.AlternativeFunctions.file_get_contents_file_get_contents, WordPress.Security.EscapeOutput.OutputNotEscaped -- inlining local JS file for critical-path performance.
	echo file_get_contents( $homepage_js_path );
	?>
</script>
<?php endif; ?>

<?php
// Use wp_footer() directly (not get_footer()) because the homepage has its
// own inline footer markup above (.ft). But include the shared template parts
// that live in footer.php so mobile nav, cookie consent, size guide, and
// toast container render on the homepage too.
get_template_part( 'template-parts/size-guide-modal' );
get_template_part( 'template-parts/cookie-consent' );
get_template_part( 'template-parts/mobile-bottom-nav' );
?>

<!-- Toast Notification Container -->
<div id="toast-container" class="toast-container" aria-live="polite" aria-atomic="true"></div>

<?php wp_footer(); ?>
</body>
</html>
