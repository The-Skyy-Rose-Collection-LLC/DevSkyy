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
 * @package SkyyRose
 * @since   6.0.0
 */

defined( 'ABSPATH' ) || exit;

/* ── Data ──────────────────────────────────────────────────────────────────── */

$hero_bg     = SKYYROSE_ASSETS_URI . '/images/homepage-hero-bg.webp';
$founder_img = SKYYROSE_ASSETS_URI . '/images/homepage-story-founder.webp';
$cart_url    = function_exists( 'wc_get_cart_url' ) ? wc_get_cart_url() : home_url( '/cart/' );

/* Collection data sourced from inc/collections-config.php (single source of truth). */
$collections = skyyrose_get_front_page_collections();

/* Dynamic product counts per collection — sourced from CSV catalog helper. */
foreach ( $collections as &$col ) {
	$col['count'] = count( skyyrose_get_collection_products( $col['slug'] ) );
}
unset( $col );

/* Press features. Empty 'url' renders as <span>; non-empty renders as <a> with rel=noopener. */
$press = array(
	array(
		'name' => __( 'Maxim', 'skyyrose' ),
		'url'  => 'https://www.maxim.com/partner/14-game-changing-entrepreneurs-to-watch-in-2023/',
	),
	array(
		'name' => __( 'CEO Weekly', 'skyyrose' ),
		'url'  => 'https://ceoweekly.com/the-unyielding-journey-of-a-single-father-and-entrepreneur/',
	),
	array(
		'name' => __( 'San Francisco Post', 'skyyrose' ),
		'url'  => 'https://sanfranciscopost.com/the-skyy-rose-collection-from-oaklands-streets-to-fashion-heights/',
	),
	array(
		'name' => __( 'Best of Best Review', 'skyyrose' ),
		'url'  => 'https://bestofbestreview.com/awards/the-skyy-rose-collection-best-bay-area-clothing-line-award-2024',
	),
	array(
		'name' => __( 'The Blox', 'skyyrose' ),
		'url'  => '',
	),
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
		'label' => __( 'Uncompromising Construction', 'skyyrose' ),
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
		'desc'  => __( 'Pioneer in Oakland gender-neutral fashion. Designed for anyone, regardless of gender or age.', 'skyyrose' ),
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
	<span class="ld-tag"><?php esc_html_e( 'Luxury Grows from Concrete.', 'skyyrose' ); ?></span>
	<div class="ld-bar"><div class="ld-fill" id="ldFill"></div></div>
</div>

<!-- mob-menu + mainNav removed (audit 2026-07-01) — WP header/mobile overlay handles navigation. -->

<!-- ═══ HERO ═══ -->
<section class="hero" id="hero" data-scroll-fade aria-label="<?php esc_attr_e( 'SkyyRose Hero', 'skyyrose' ); ?>">
	<?php
	// LCP-critical hero: <picture> with AVIF + WebP sources lets the browser
	// preload-discover the actual <img>, unlike background-image which is
	// discovered only after CSS parse. v1.5.17 LCP refactor.
	//
	// v1.5.19: use skyyrose_avif_sibling_pair() so the existence probe and
	// emitted URL are computed atomically from $hero_bg — prevents drift if
	// $hero_bg is ever filtered (CDN swap, asset hash, etc).
	$hero_avif = function_exists( 'skyyrose_avif_sibling_pair' ) ? skyyrose_avif_sibling_pair( $hero_bg ) : null;
	?>
	<div class="hero-bg parallax-ken-burns" aria-hidden="true">
		<picture>
			<?php if ( $hero_avif && file_exists( $hero_avif['path'] ) ) : ?>
				<source type="image/avif" srcset="<?php echo esc_url( $hero_avif['url'] ); ?>">
			<?php endif; ?>
			<source type="image/webp" srcset="<?php echo esc_url( $hero_bg ); ?>">
			<?php
			// width=height=1920 intentional: source asset is square; CSS
			// object-position: center 30% crops to landscape with vertical bias.
			// If asset becomes 16:9 in future, update both attrs.
			?>
			<img src="<?php echo esc_url( $hero_bg ); ?>"
				alt=""
				width="1920"
				height="1920"
				loading="eager"
				fetchpriority="high"
				decoding="async">
		</picture>
	</div>
	<div class="hero-ov" aria-hidden="true"></div>
	<div class="hero-particles" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i></div>
	<div class="hero-frame" aria-hidden="true"></div>
	<div class="hero-content">
		<p class="hero-mark-top"><?php esc_html_e( 'Oakland', 'skyyrose' ); ?></p>
		<h1 class="hero-title" aria-label="<?php esc_attr_e( 'SkyyRose', 'skyyrose' ); ?>">SkyyRose</h1>
		<p class="hero-mark-bot"><?php esc_html_e( 'Est. 2020', 'skyyrose' ); ?></p>
		<div class="hero-rule" aria-hidden="true"></div>
		<p class="hero-subtitle"><?php esc_html_e( 'Luxury Grows from Concrete. Four collections, one name — built by a father, named after a daughter.', 'skyyrose' ); ?></p>
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

<?php if ( function_exists( 'skyyrose_render_drop_block' ) ) { skyyrose_render_drop_block(); } ?>

<!-- ═══ PRESS STRIP ═══ -->
<div class="press rv">
	<p class="press-label"><?php esc_html_e( 'As Featured In', 'skyyrose' ); ?></p>
	<div class="press-logos">
		<?php foreach ( $press as $idx => $item ) : ?>
			<?php if ( $idx > 0 ) : ?>
				<span class="press-sep" aria-hidden="true"></span>
			<?php endif; ?>
			<?php if ( ! empty( $item['url'] ) ) : ?>
				<a class="press-item press-item--link"
					href="<?php echo esc_url( $item['url'] ); ?>"
					target="_blank"
					rel="noopener noreferrer">
					<?php echo esc_html( $item['name'] ); ?>
				</a>
			<?php else : ?>
				<span class="press-item"><?php echo esc_html( $item['name'] ); ?></span>
			<?php endif; ?>
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

<!-- ═══ COMMERCIAL RUNWAY ═══ -->
<section class="commercial-runway" id="commercial-runway" aria-label="<?php esc_attr_e( 'Shop SkyyRose', 'skyyrose' ); ?>">
	<div class="commercial-runway__intro rv-clip-up">
		<p class="commercial-runway__eyebrow"><?php esc_html_e( 'The Storefront', 'skyyrose' ); ?></p>
		<h2><?php esc_html_e( 'Luxury Streetwear, Ready To Move.', 'skyyrose' ); ?></h2>
		<p><?php esc_html_e( 'A faster path from first impression to cart: signature drops, collection worlds, fit help, and real product photography in one commercial flow.', 'skyyrose' ); ?></p>
	</div>
	<div class="commercial-runway__rail stagger-grid">
		<a class="commercial-tile commercial-tile--wide magnetic" href="<?php echo esc_url( home_url( '/collection-black-rose/' ) ); ?>">
			<img src="<?php echo esc_url( skyyrose_sot_product_image_uri( 'br-006', 'front' ) ); ?>"
				alt="<?php esc_attr_e( 'Black Rose sherpa jacket on model', 'skyyrose' ); ?>"
				loading="lazy"
				decoding="async"
				width="1024"
				height="1024">
			<span class="commercial-tile__kicker"><?php esc_html_e( 'Drop Focus', 'skyyrose' ); ?></span>
			<strong><?php esc_html_e( 'Black Rose Outerwear', 'skyyrose' ); ?></strong>
			<em><?php esc_html_e( 'Cold-weather statement pieces with Oakland weight.', 'skyyrose' ); ?></em>
		</a>
		<a class="commercial-tile magnetic" href="<?php echo esc_url( home_url( '/collection-love-hurts/' ) ); ?>">
			<img src="<?php echo esc_url( skyyrose_sot_product_image_uri( 'lh-004', 'front' ) ); ?>"
				alt="<?php esc_attr_e( 'Love Hurts varsity jacket on model', 'skyyrose' ); ?>"
				loading="lazy"
				decoding="async"
				width="1024"
				height="1024">
			<span class="commercial-tile__kicker"><?php esc_html_e( 'Now Styling', 'skyyrose' ); ?></span>
			<strong><?php esc_html_e( 'Varsity Heat', 'skyyrose' ); ?></strong>
			<em><?php esc_html_e( 'Built for nights that need proof.', 'skyyrose' ); ?></em>
		</a>
		<a class="commercial-tile magnetic" href="<?php echo esc_url( home_url( '/collection-signature/' ) ); ?>">
			<img src="<?php echo esc_url( skyyrose_sot_product_image_uri( 'sg-009', 'front' ) ); ?>"
				alt="<?php esc_attr_e( 'Signature sherpa jacket on model', 'skyyrose' ); ?>"
				loading="lazy"
				decoding="async"
				width="1024"
				height="1024">
			<span class="commercial-tile__kicker"><?php esc_html_e( 'Core Luxury', 'skyyrose' ); ?></span>
			<strong><?php esc_html_e( 'Signature Layering', 'skyyrose' ); ?></strong>
			<em><?php esc_html_e( 'Gold-standard essentials for daily rotation.', 'skyyrose' ); ?></em>
		</a>
	</div>
	<div class="commercial-runway__bar rv">
		<span><?php esc_html_e( 'Limited runs', 'skyyrose' ); ?></span>
		<span><?php esc_html_e( 'Gender neutral fit', 'skyyrose' ); ?></span>
		<span><?php esc_html_e( 'Oakland story', 'skyyrose' ); ?></span>
		<span><?php esc_html_e( 'Wishlist ready', 'skyyrose' ); ?></span>
	</div>
</section>

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
		</div>
		<div class="story-img-wrap rv-right">
			<div class="story-img">
				<img src="<?php echo esc_url( $founder_img ); ?>"
					alt="<?php esc_attr_e( 'Corey Foster, SkyyRose founder', 'skyyrose' ); ?>"
					loading="lazy" decoding="async" width="600" height="800">
			</div>
			<div class="story-float">
				<div class="sf-lbl"><?php esc_html_e( 'Recognition', 'skyyrose' ); ?></div>
				<div class="sf-val"><?php echo wp_kses( __( 'Best Oakland<br>Clothing Line 2024', 'skyyrose' ), array( 'br' => array() ) ); ?></div>
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
		<h2 class="col-header-title rv-split-word"><?php esc_html_e( 'Four Collections. One Vision.', 'skyyrose' ); ?></h2>
	</div>
	<div class="col-grid stagger-grid">
		<?php foreach ( $collections as $idx => $col ) : ?>
			<a href="<?php echo esc_url( $col['link'] ); ?>" class="col-card <?php echo esc_attr( $col['class'] ); ?> magnetic">
				<div class="col-card-img">
					<?php
					// alt is passed as the 2nd positional arg to skyyrose_render_picture()
					// below; do NOT repeat it here or the <img> emits a duplicate alt=.
					$card_img_attrs = array(
						'loading'  => 0 === $idx ? 'eager' : 'lazy',
						'decoding' => 'async',
						'width'    => '480',
						'height'   => '640',
					);
					if ( 0 === $idx ) {
						$card_img_attrs['fetchpriority'] = 'high';
					}
					echo skyyrose_render_picture( // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- helper escapes internally.
						$col['image'],
						$col['name'] . ' Collection',
						$card_img_attrs
					);
					?>
				</div>
				<div class="col-card-ov"></div>
				<div class="col-card-content">
					<p class="col-card-num"><?php echo esc_html( $col['num'] ); ?></p>
					<?php
					/* ── Collection name lockup (brand-script image, never type-rendered) ── */
					$lockups = array(
						'black-rose' => array(
							'base' => 'hero-overlays/br-brand-script-logotype',
							'alt'  => __( 'Black Rose', 'skyyrose' ),
						),
						'love-hurts' => array(
							'base' => 'hero-overlays/lh-logo-combined',
							'alt'  => __( 'Love Hurts', 'skyyrose' ),
						),
						'signature'  => array(
							'base' => 'hero-overlays/sig-brand-skyy-rose-gold',
							'alt'  => __( 'Signature', 'skyyrose' ),
						),
					);
					$lk      = $lockups[ $col['slug'] ] ?? null;
					if ( $lk ) :
						$lk_uri = SKYYROSE_ASSETS_URI . '/images/' . $lk['base'];
						?>
						<picture class="col-card-name">
							<source srcset="<?php echo esc_url( $lk_uri . '.avif' ); ?>" type="image/avif">
							<source srcset="<?php echo esc_url( $lk_uri . '.webp' ); ?>" type="image/webp">
							<img src="<?php echo esc_url( $lk_uri . '.png' ); ?>"
								alt=""
								loading="lazy"
								decoding="async"
								class="col-card-name__lockup">
						</picture>
						<span class="screen-reader-text"><?php echo esc_html( $lk['alt'] ); ?></span>
					<?php else : ?>
						<h3 class="col-card-name"><?php echo wp_kses( $col['title'], array( 'br' => array() ) ); ?></h3>
					<?php endif; ?>
					<?php /* Kids Capsule (show_on_front=false) never reaches this loop. The h3 fallback covers future edge cases only. */ ?>
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

<!-- ═══ STYLE ATELIER ═══ -->
<section class="style-atelier" id="style-atelier" aria-label="<?php esc_attr_e( 'Style Atelier', 'skyyrose' ); ?>">
	<div class="style-atelier__copy rv-clip-up">
		<p class="style-atelier__eyebrow"><?php esc_html_e( 'Customer Driven', 'skyyrose' ); ?></p>
		<h2><?php esc_html_e( 'Find Your SkyyRose Lane.', 'skyyrose' ); ?></h2>
		<p><?php esc_html_e( 'Choose how you want to show up. The atelier responds with a collection direction and first piece to explore.', 'skyyrose' ); ?></p>
	</div>
	<div class="style-atelier__stage">
		<div class="style-atelier__choices" role="group" aria-label="<?php esc_attr_e( 'Choose a styling profile', 'skyyrose' ); ?>">
			<button type="button"
				class="style-choice is-active"
				aria-pressed="true"
				data-style-option
				data-style-title="<?php esc_attr_e( 'Statement Layer', 'skyyrose' ); ?>"
				data-style-kicker="<?php esc_attr_e( 'Black Rose', 'skyyrose' ); ?>"
				data-style-copy="<?php esc_attr_e( 'Structured outerwear, dark palette, heavyweight presence. Start with the sherpa and build the rest quiet.', 'skyyrose' ); ?>"
				data-style-image="<?php echo esc_url( skyyrose_sot_product_image_uri( 'br-006', 'front' ) ); ?>"
				data-style-alt="<?php esc_attr_e( 'Black Rose sherpa jacket style recommendation', 'skyyrose' ); ?>"
				data-style-link="<?php echo esc_url( home_url( '/collection-black-rose/' ) ); ?>">
				<span><?php esc_html_e( 'Statement', 'skyyrose' ); ?></span>
				<em><?php esc_html_e( 'Outerwear first', 'skyyrose' ); ?></em>
			</button>
			<button type="button"
				class="style-choice"
				aria-pressed="false"
				data-style-option
				data-style-title="<?php esc_attr_e( 'Clean Daily Rotation', 'skyyrose' ); ?>"
				data-style-kicker="<?php esc_attr_e( 'Signature', 'skyyrose' ); ?>"
				data-style-copy="<?php esc_attr_e( 'Soft luxury staples with mint, gold, and easy proportions. Built for repeat wear without losing identity.', 'skyyrose' ); ?>"
				data-style-image="<?php echo esc_url( skyyrose_sot_product_image_uri( 'sg-006', 'front' ) ); ?>"
				data-style-alt="<?php esc_attr_e( 'Mint lavender hoodie style recommendation', 'skyyrose' ); ?>"
				data-style-link="<?php echo esc_url( home_url( '/collection-signature/' ) ); ?>">
				<span><?php esc_html_e( 'Daily', 'skyyrose' ); ?></span>
				<em><?php esc_html_e( 'Soft luxury', 'skyyrose' ); ?></em>
			</button>
			<button type="button"
				class="style-choice"
				aria-pressed="false"
				data-style-option
				data-style-title="<?php esc_attr_e( 'Night Signal', 'skyyrose' ); ?>"
				data-style-kicker="<?php esc_attr_e( 'Love Hurts', 'skyyrose' ); ?>"
				data-style-copy="<?php esc_attr_e( 'Varsity energy, crimson edge, and pieces that read from across the room. Designed for entrance moments.', 'skyyrose' ); ?>"
				data-style-image="<?php echo esc_url( skyyrose_sot_product_image_uri( 'lh-004', 'front' ) ); ?>"
				data-style-alt="<?php esc_attr_e( 'Love Hurts varsity jacket style recommendation', 'skyyrose' ); ?>"
				data-style-link="<?php echo esc_url( home_url( '/collection-love-hurts/' ) ); ?>">
				<span><?php esc_html_e( 'Night', 'skyyrose' ); ?></span>
				<em><?php esc_html_e( 'Entrance energy', 'skyyrose' ); ?></em>
			</button>
		</div>
		<div class="style-atelier__result rv-blur" aria-live="polite">
			<div class="style-atelier__image">
				<img id="styleAtelierImage"
					src="<?php echo esc_url( skyyrose_sot_product_image_uri( 'br-006', 'front' ) ); ?>"
					alt="<?php esc_attr_e( 'Black Rose sherpa jacket style recommendation', 'skyyrose' ); ?>"
					loading="lazy"
					decoding="async"
					width="1024"
					height="1024">
			</div>
			<div class="style-atelier__panel">
				<p id="styleAtelierKicker"><?php esc_html_e( 'Black Rose', 'skyyrose' ); ?></p>
				<h3 id="styleAtelierTitle"><?php esc_html_e( 'Statement Layer', 'skyyrose' ); ?></h3>
				<div class="style-atelier__rule" aria-hidden="true"></div>
				<p id="styleAtelierCopy"><?php esc_html_e( 'Structured outerwear, dark palette, heavyweight presence. Start with the sherpa and build the rest quiet.', 'skyyrose' ); ?></p>
				<a id="styleAtelierLink" class="style-atelier__cta btn-sweep" href="<?php echo esc_url( home_url( '/collection-black-rose/' ) ); ?>"><?php esc_html_e( 'Shop This Direction', 'skyyrose' ); ?></a>
			</div>
		</div>
	</div>
</section>

<!-- ═══ KIDS CAPSULE — HEIR APPARENT (envelope reveal, hover breaks the seal) ═══ -->
<?php
$kc_config = function_exists( 'skyyrose_get_collection' ) ? skyyrose_get_collection( 'kids-capsule' ) : null;
$kc_link   = $kc_config['page_url'] ?? home_url( '/collection-kids-capsule/' );
?>
<section class="kc-heir" id="kids-capsule" aria-label="<?php esc_attr_e( 'Kids Capsule — Heir Apparent', 'skyyrose' ); ?>" data-collection="kids-capsule">
	<div class="kc-heir__head">
		<p class="kc-heir__eyebrow"><?php esc_html_e( 'Capsule · IV · Heir Apparent', 'skyyrose' ); ?></p>
		<h2 class="kc-heir__title"><?php esc_html_e( 'The Kids Capsule', 'skyyrose' ); ?></h2>
		<p class="kc-heir__sub"><?php esc_html_e( 'Not a fourth world. A letter to one. Hover to break the seal.', 'skyyrose' ); ?></p>
	</div>

	<a href="<?php echo esc_url( $kc_link ); ?>" class="kc-heir__stage" tabindex="0" aria-label="<?php esc_attr_e( 'Open the letter — discover Kids Capsule', 'skyyrose' ); ?>">
		<div class="kc-heir__envelope">
			<div class="kc-heir__letter">
				<div class="kc-heir__chapter"><?php esc_html_e( 'Chapter IV', 'skyyrose' ); ?></div>
				<div class="kc-heir__script"><?php esc_html_e( 'Dear future,', 'skyyrose' ); ?></div>
				<p class="kc-heir__headline"><?php esc_html_e( 'You were born into the rose. Wear it lightly.', 'skyyrose' ); ?></p>
				<div class="kc-heir__sig">— S.</div>
			</div>
			<div class="kc-heir__env-back" aria-hidden="true"></div>
			<div class="kc-heir__wax-glow" aria-hidden="true"></div>
			<svg class="kc-heir__wax" viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
				<defs>
					<radialGradient id="kc-wax-grad" cx="35%" cy="30%">
						<stop offset="0%" stop-color="#1a0e0c"/>
						<stop offset="60%" stop-color="#0a0504"/>
						<stop offset="100%" stop-color="#000"/>
					</radialGradient>
					<radialGradient id="kc-wax-shine" cx="40%" cy="30%">
						<stop offset="0%" stop-color="rgba(212,175,55,.4)"/>
						<stop offset="40%" stop-color="rgba(212,175,55,0)"/>
					</radialGradient>
				</defs>
				<g class="kc-heir__wax-half left">
					<path d="M 40 6 A 34 34 0 0 0 40 74 L 40 6 Z" fill="url(#kc-wax-grad)" stroke="#3d2418" stroke-width=".5"/>
					<path d="M 40 6 A 34 34 0 0 0 40 74 L 40 6 Z" fill="url(#kc-wax-shine)"/>
					<path d="M 8 38 L 6 44 L 9 47 L 7 52 M 12 22 L 9 26 M 14 60 L 11 64" fill="none" stroke="#0a0504" stroke-width="1.2"/>
				</g>
				<g class="kc-heir__wax-half right">
					<path d="M 40 6 A 34 34 0 0 1 40 74 L 40 6 Z" fill="url(#kc-wax-grad)" stroke="#3d2418" stroke-width=".5"/>
					<path d="M 40 6 A 34 34 0 0 1 40 74 L 40 6 Z" fill="url(#kc-wax-shine)"/>
					<path d="M 72 38 L 74 44 L 71 47 L 73 52 M 68 22 L 71 26 M 66 60 L 69 64" fill="none" stroke="#0a0504" stroke-width="1.2"/>
				</g>
				<text x="40" y="54" text-anchor="middle" font-family="'Cormorant Garamond', Georgia, serif" font-style="italic" font-size="46" fill="#D4AF37">S</text>
			</svg>
		</div>
		<div class="kc-heir__hint"><?php esc_html_e( '↗ break the seal', 'skyyrose' ); ?></div>
	</a>

	<div class="kc-heir__tag">
		<div class="kc-heir__tag-script"><?php esc_html_e( 'Heir to the rose.', 'skyyrose' ); ?></div>
		<div class="kc-heir__tag-sub"><?php esc_html_e( 'Capsule · IV · Kids · Born Into It', 'skyyrose' ); ?></div>
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

<!-- ═══ SERVICE PROMISE ═══ -->
<section class="service-promise" aria-label="<?php esc_attr_e( 'SkyyRose Service Promise', 'skyyrose' ); ?>">
	<div class="service-promise__head rv-clip-up">
		<p><?php esc_html_e( 'Commercial Standard', 'skyyrose' ); ?></p>
		<h2><?php esc_html_e( 'The House Service Layer.', 'skyyrose' ); ?></h2>
	</div>
	<div class="service-promise__list stagger-grid">
		<a href="<?php echo esc_url( home_url( '/shipping-returns/' ) ); ?>" class="service-card">
			<span><?php esc_html_e( '01', 'skyyrose' ); ?></span>
			<strong><?php esc_html_e( 'Clear Shipping', 'skyyrose' ); ?></strong>
			<em><?php esc_html_e( 'Delivery and return expectations before checkout.', 'skyyrose' ); ?></em>
		</a>
		<button type="button" class="service-card service-card--button" data-open-size-guide>
			<span><?php esc_html_e( '02', 'skyyrose' ); ?></span>
			<strong><?php esc_html_e( 'Fit Guide', 'skyyrose' ); ?></strong>
			<em><?php esc_html_e( 'Measure once, shop every drop with more confidence.', 'skyyrose' ); ?></em>
		</button>
		<a href="<?php echo esc_url( home_url( '/wishlist/' ) ); ?>" class="service-card">
			<span><?php esc_html_e( '03', 'skyyrose' ); ?></span>
			<strong><?php esc_html_e( 'Wishlist Flow', 'skyyrose' ); ?></strong>
			<em><?php esc_html_e( 'Save looks before small runs disappear.', 'skyyrose' ); ?></em>
		</a>
		<a href="<?php echo esc_url( home_url( '/contact/' ) ); ?>" class="service-card">
			<span><?php esc_html_e( '04', 'skyyrose' ); ?></span>
			<strong><?php esc_html_e( 'Concierge Contact', 'skyyrose' ); ?></strong>
			<em><?php esc_html_e( 'Questions, press, styling, and collaboration routes.', 'skyyrose' ); ?></em>
		</a>
	</div>
</section>

<!-- ═══ LOOKBOOK ═══ -->
<section class="lookbook" id="lookbook" aria-label="<?php esc_attr_e( 'Lookbook', 'skyyrose' ); ?>">
	<div class="lookbook-header rv-clip-up">
		<p class="lookbook-eyebrow"><?php esc_html_e( 'The Lookbook', 'skyyrose' ); ?></p>
		<h2><?php esc_html_e( 'Worn In The Real World', 'skyyrose' ); ?></h2>
		<p class="lookbook-tagline"><?php esc_html_e( 'Real people. Real style. Oakland made.', 'skyyrose' ); ?></p>
	</div>
	<div class="lookbook-grid stagger-grid">
		<?php
		foreach ( $lookbook as $lb ) :
			$lb_base  = SKYYROSE_ASSETS_URI . '/images/lookbook/' . $lb['file'];
			$lb_sizes = $lb['tall']
				? '(max-width: 600px) 100vw, (max-width: 1024px) 100vw, 760px'
				: '(max-width: 600px) 100vw, (max-width: 1024px) 50vw, 370px';
			?>
			<div class="lb-img rv<?php echo $lb['tall'] ? ' tall' : ''; ?>">
				<picture>
					<source type="image/avif"
						srcset="<?php echo esc_url( $lb_base . '-480w.avif' ); ?> 480w, <?php echo esc_url( $lb_base . '-960w.avif' ); ?> 960w"
						sizes="<?php echo esc_attr( $lb_sizes ); ?>">
					<source type="image/webp"
						srcset="<?php echo esc_url( $lb_base . '-480w.webp' ); ?> 480w, <?php echo esc_url( $lb_base . '-960w.webp' ); ?> 960w"
						sizes="<?php echo esc_attr( $lb_sizes ); ?>">
					<img src="<?php echo esc_url( $lb_base . '-960w.webp' ); ?>"
						srcset="<?php echo esc_url( $lb_base . '-480w.webp' ); ?> 480w, <?php echo esc_url( $lb_base . '-960w.webp' ); ?> 960w"
						sizes="<?php echo esc_attr( $lb_sizes ); ?>"
						alt="<?php echo esc_attr( $lb['alt'] ); ?>"
						loading="lazy" decoding="async" width="960" height="1280">
				</picture>
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
			<p class="ft-desc rv rv-d1"><?php esc_html_e( 'Where Oakland authenticity meets high-fashion aesthetics. Gender-neutral, sustainably crafted, limited edition designs. Built by a father, named after a daughter.', 'skyyrose' ); ?></p>
			<div class="ft-awards rv rv-d2">
				<span class="ft-award"><?php esc_html_e( "Maxim's 14 Game-Changing Entrepreneurs 2023", 'skyyrose' ); ?></span>
				<span class="ft-award"><?php esc_html_e( 'Best Oakland Clothing Line 2024', 'skyyrose' ); ?></span>
				<span class="ft-award"><?php esc_html_e( 'Featured — San Francisco Post, CEO Weekly', 'skyyrose' ); ?></span>
			</div>
		</div>
		<div>
			<div class="ft-col-title rv"><?php esc_html_e( 'Collections', 'skyyrose' ); ?></div>
			<ul class="ft-links rv rv-d1">
				<li><a href="<?php echo esc_url( home_url( '/collection-black-rose/' ) ); ?>"><?php esc_html_e( 'Black Rose', 'skyyrose' ); ?></a></li>
				<li><a href="<?php echo esc_url( home_url( '/collection-love-hurts/' ) ); ?>"><?php esc_html_e( 'Love Hurts', 'skyyrose' ); ?></a></li>
				<li><a href="<?php echo esc_url( home_url( '/collection-signature/' ) ); ?>"><?php esc_html_e( 'Signature', 'skyyrose' ); ?></a></li>
				<li><a href="<?php echo esc_url( home_url( '/collection-kids-capsule/' ) ); ?>"><?php esc_html_e( 'Kids Capsule', 'skyyrose' ); ?></a></li>
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
// Prefer minified for production; fall back to source when SCRIPT_DEBUG is on
// or when the min file is missing (e.g., right after a source edit before rebuild).
$homepage_js_use_min = ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG;
$homepage_js_min     = SKYYROSE_DIR . '/assets/js/homepage-v2.min.js';
$homepage_js_src     = SKYYROSE_DIR . '/assets/js/homepage-v2.js';
$homepage_js_path    = ( $homepage_js_use_min && file_exists( $homepage_js_min ) ) ? $homepage_js_min : $homepage_js_src;
if ( file_exists( $homepage_js_path ) ) :
	?>
<script>
	<?php
	// phpcs:ignore WordPress.WP.AlternativeFunctions.file_get_contents_file_get_contents, WordPress.Security.EscapeOutput.OutputNotEscaped -- inlining local JS file for critical-path performance.
	$homepage_js_content = file_get_contents( $homepage_js_path );
	if ( $homepage_js_content ) {
		echo $homepage_js_content; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- raw local JS file inlined for critical-path performance.
	}
	?>
</script>
<?php endif; ?>

<?php
// Use wp_footer() directly (not get_footer()) because the homepage has its
// own inline footer markup above (.ft). But include the shared template parts
// that live in footer.php so mobile nav, cookie consent, size guide, CRO
// sections, and toast container render on the homepage too.
get_template_part( 'template-parts/footer-cro' );
get_template_part( 'template-parts/size-guide-modal' );
get_template_part( 'template-parts/cookie-consent' );
// Skyy mascot disabled — re-enable when character art is finalized.
// get_template_part( 'template-parts/skyy-mascot' );
get_template_part( 'template-parts/mobile-bottom-nav' );
?>

<!-- Toast Notification Container -->
<div id="toast-container" class="toast-container" aria-live="polite" aria-atomic="true"></div>

<?php wp_footer(); ?>
</body>
</html>
