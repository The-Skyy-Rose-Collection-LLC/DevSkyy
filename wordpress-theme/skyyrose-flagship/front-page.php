<?php
/**
 * Front Page — SkyyRose v7.0 "Concrete" Commercial Theme
 *
 * Dark luxury editorial homepage. Typographic bleed hero, cursor-trigger
 * collection split portal, specimen catalogue ticker, narrative scroll.
 *
 * Design: AIDesigner "Concrete" concept — dark luxury streetwear commercial theme.
 * CSS: assets/css/homepage-v2.css (+ v7 appended rules)
 * JS:  assets/js/homepage-v2.js  (+ v7 appended interactions)
 *
 * @package SkyyRose_Flagship
 * @since   7.0.0
 */

defined( 'ABSPATH' ) || exit;

/* ── Data ──────────────────────────────────────────────────────────────────── */

$founder_img = SKYYROSE_ASSETS_URI . '/images/homepage-story-founder.webp';
$cart_url    = function_exists( 'wc_get_cart_url' ) ? wc_get_cart_url() : home_url( '/cart/' );

/* Collection data — single source of truth in inc/collections-config.php */
$collections = skyyrose_get_front_page_collections();

/* Dynamic product counts per collection */
foreach ( $collections as &$col ) {
	$col['count'] = 0;
	if ( function_exists( 'wc_get_products' ) ) {
		$products    = wc_get_products( array( 'category' => array( $col['slug'] ), 'limit' => -1, 'return' => 'ids', 'status' => 'publish' ) );
		$col['count'] = count( $products );
	}
}
unset( $col );

/* Map collections by class key for direct access */
$col_map = array();
foreach ( $collections as $c ) {
	$col_map[ $c['class'] ] = $c;
}
$col_br = $col_map['br'] ?? null;
$col_lh = $col_map['lh'] ?? null;
$col_sg = $col_map['sg'] ?? null;

/* Press features */
$press = array(
	array( 'name' => __( 'Maxim', 'skyyrose-flagship' ),           'font' => 'cinzel' ),
	array( 'name' => __( 'CEO Weekly', 'skyyrose-flagship' ),       'font' => 'bebas' ),
	array( 'name' => __( 'San Francisco Post', 'skyyrose-flagship' ),'font' => 'playfair' ),
	array( 'name' => __( 'Best of Best Review', 'skyyrose-flagship' ),'font' => 'mono' ),
	array( 'name' => __( 'The Blox', 'skyyrose-flagship' ),         'font' => 'cormorant' ),
);

/* Specimen catalogue items — BR jersey series */
$specimens = array(
	'001 / BR_008 SF_INSPIRED — 80 PIECES',
	'002 / BR_009 LAST_OAKLAND — 80 PIECES',
	'003 / BR_010 THE_BAY — 80 PIECES',
	'004 / BR_011 THE_ROSE_(SHARKS) — 80 PIECES',
);

/* Craft cards */
$craft_cards = array(
	array(
		'icon'  => '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M12 2L2 7l10 5 10-5-10-5Z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>',
		'label' => __( 'Premium Materials', 'skyyrose-flagship' ),
		'desc'  => __( '280–400gsm cotton. Italian wool blends. Full-grain leather. No shortcuts.', 'skyyrose-flagship' ),
	),
	array(
		'icon'  => '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
		'label' => __( 'The Town Mentality', 'skyyrose-flagship' ),
		'desc'  => __( 'Born from the struggle of East Oakland. Designed for the world. Built to last generations.', 'skyyrose-flagship' ),
	),
	array(
		'icon'  => '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
		'label' => __( 'Gender Neutral', 'skyyrose-flagship' ),
		'desc'  => __( 'Pioneer in Bay Area gender-neutral fashion. Designed for anyone, regardless of gender or age.', 'skyyrose-flagship' ),
	),
	array(
		'icon'  => '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
		'label' => __( 'Limited Editions', 'skyyrose-flagship' ),
		'desc'  => __( "Small batch production. Individually numbered. When it's gone, it's gone.", 'skyyrose-flagship' ),
	),
);

$svg_whitelist = array(
	'svg'    => array( 'width' => true, 'height' => true, 'viewBox' => true, 'fill' => true, 'stroke' => true, 'stroke-width' => true, 'stroke-linecap' => true, 'stroke-linejoin' => true, 'aria-hidden' => true, 'focusable' => true, 'xmlns' => true ),
	'path'   => array( 'd' => true, 'fill' => true, 'stroke' => true, 'stroke-width' => true ),
	'circle' => array( 'cx' => true, 'cy' => true, 'r' => true, 'fill' => true ),
	'polygon'=> array( 'points' => true, 'fill' => true ),
);

get_header();
?>

<main id="primary" class="site-main homepage-v2 homepage-v7" role="main" tabindex="-1">

<canvas id="grainCanvas" class="grain-canvas" aria-hidden="true"></canvas>
<div class="scroll-progress" aria-hidden="true"></div>

<noscript><style>#loader{display:none!important}</style></noscript>

<!-- ═══ LOADER ═══ -->
<div id="loader" role="status" aria-label="<?php esc_attr_e( 'Loading', 'skyyrose-flagship' ); ?>">
	<span class="ld-brand"><?php esc_html_e( 'SkyyRose', 'skyyrose-flagship' ); ?></span>
	<span class="ld-tag"><?php esc_html_e( 'Luxury Grows from Concrete', 'skyyrose-flagship' ); ?></span>
	<div class="ld-bar"><div class="ld-fill" id="ldFill"></div></div>
</div>

<!-- ═══ MOBILE MENU ═══ -->
<div class="mob-menu" id="mobMenu" role="dialog" aria-modal="true" aria-label="<?php esc_attr_e( 'Navigation', 'skyyrose-flagship' ); ?>">
	<button class="mob-close" type="button" aria-label="<?php esc_attr_e( 'Close menu', 'skyyrose-flagship' ); ?>">&times;</button>
	<a href="#collections"><?php esc_html_e( 'Worlds', 'skyyrose-flagship' ); ?></a>
	<a href="#drops"><?php esc_html_e( 'Drops', 'skyyrose-flagship' ); ?></a>
	<a href="#issue"><?php esc_html_e( 'Issue', 'skyyrose-flagship' ); ?></a>
	<a href="#story"><?php esc_html_e( 'The Roster', 'skyyrose-flagship' ); ?></a>
	<a href="<?php echo esc_url( $cart_url ); ?>"><?php esc_html_e( 'Bag', 'skyyrose-flagship' ); ?></a>
</div>

<!-- ═══ NAV — Brand vocabulary only. No "Shop." ═══ -->
<nav class="nav nav-v7" id="mainNav" aria-label="<?php esc_attr_e( 'Homepage Navigation', 'skyyrose-flagship' ); ?>">
	<div class="nav-left">
		<a href="#collections" class="nav-link"><?php esc_html_e( 'Worlds', 'skyyrose-flagship' ); ?></a>
		<a href="#drops" class="nav-link"><?php esc_html_e( 'Drops', 'skyyrose-flagship' ); ?></a>
		<a href="#issue" class="nav-link hidden-sm"><?php esc_html_e( 'Issue', 'skyyrose-flagship' ); ?></a>
		<a href="#story" class="nav-link hidden-sm"><?php esc_html_e( 'The Roster', 'skyyrose-flagship' ); ?></a>
	</div>
	<a href="<?php echo esc_url( home_url( '/' ) ); ?>" class="nav-brand-center">
		<span class="nav-name"><?php esc_html_e( 'SkyyRose', 'skyyrose-flagship' ); ?></span>
	</a>
	<div class="nav-right">
		<button class="nav-bag" type="button" aria-label="<?php esc_attr_e( 'Shopping Bag', 'skyyrose-flagship' ); ?>">
			<?php esc_html_e( 'Cart', 'skyyrose-flagship' ); ?><span class="bag-ct" id="bagCt">_0</span>
		</button>
		<button class="nav-ham" type="button" aria-label="<?php esc_attr_e( 'Open menu', 'skyyrose-flagship' ); ?>">
			<span></span><span></span><span></span>
		</button>
	</div>
</nav>

<!-- ═══ HERO — Typographic bleed. No photography. ═══ -->
<section class="hero hero-concrete" id="hero" aria-label="<?php esc_attr_e( 'SkyyRose', 'skyyrose-flagship' ); ?>">
	<h1 class="hero-concrete-word" aria-label="<?php esc_attr_e( 'Concrete', 'skyyrose-flagship' ); ?>">
		<span aria-hidden="true">CONCRETE</span>
	</h1>
	<div class="hero-concrete-sub">
		<p class="hero-tagline"><?php esc_html_e( 'Luxury Grows from Concrete.', 'skyyrose-flagship' ); ?></p>
		<a href="#collections" class="hero-scroll-cta" aria-label="<?php esc_attr_e( 'Explore collections', 'skyyrose-flagship' ); ?>">
			<span class="hero-scroll-line"></span>
			<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M12 5v14M5 12l7 7 7-7"/></svg>
		</a>
	</div>
</section>

<!-- ═══ COLLECTION SPLIT PORTAL — Cursor-trigger 50/50 ═══ -->
<section class="collection-split" id="collections" aria-label="<?php esc_attr_e( 'Collections', 'skyyrose-flagship' ); ?>">

	<!-- Left: Black Rose -->
	<?php if ( $col_br ) : ?>
	<a href="<?php echo esc_url( $col_br['link'] ); ?>"
	   class="split-panel split-br"
	   aria-label="<?php esc_attr_e( 'Black Rose Collection', 'skyyrose-flagship' ); ?>">
		<div class="split-panel-bg split-br-bg" aria-hidden="true"></div>
		<div class="split-panel-content">
			<span class="split-num font-mono"><?php esc_html_e( '01', 'skyyrose-flagship' ); ?></span>
			<h2 class="split-name split-br-name"><?php esc_html_e( 'Black', 'skyyrose-flagship' ); ?><br><?php esc_html_e( 'Rose', 'skyyrose-flagship' ); ?></h2>
			<p class="split-tag"><?php esc_html_e( 'Dark elegance. The Town.', 'skyyrose-flagship' ); ?></p>
		</div>
	</a>
	<?php endif; ?>

	<!-- Right: Signature -->
	<?php if ( $col_sg ) : ?>
	<a href="<?php echo esc_url( $col_sg['link'] ); ?>"
	   class="split-panel split-sg"
	   aria-label="<?php esc_attr_e( 'Signature Collection', 'skyyrose-flagship' ); ?>">
		<div class="split-panel-bg split-sg-bg" aria-hidden="true"></div>
		<div class="split-panel-content split-panel-content--right">
			<span class="split-num font-mono"><?php esc_html_e( '03', 'skyyrose-flagship' ); ?></span>
			<h2 class="split-name split-sg-name"><?php esc_html_e( 'Signature', 'skyyrose-flagship' ); ?></h2>
			<p class="split-tag"><?php esc_html_e( 'Bay Area confidence. Everyday elevation.', 'skyyrose-flagship' ); ?></p>
		</div>
	</a>
	<?php endif; ?>

	<!-- 1px rose-gold divider -->
	<div class="split-divider" aria-hidden="true"></div>

	<!-- Center intrusion: Love Hurts — Corey's family name -->
	<?php if ( $col_lh ) : ?>
	<a href="<?php echo esc_url( $col_lh['link'] ); ?>"
	   class="split-lh-strip"
	   aria-label="<?php esc_attr_e( 'Love Hurts Collection', 'skyyrose-flagship' ); ?>">
		<span class="split-lh-num font-mono"><?php esc_html_e( '02', 'skyyrose-flagship' ); ?></span>
		<h2 class="split-lh-name"><?php esc_html_e( 'Love Hurts', 'skyyrose-flagship' ); ?></h2>
		<span class="split-lh-note font-mono"><?php esc_html_e( "The Founder's Name", 'skyyrose-flagship' ); ?></span>
	</a>
	<?php endif; ?>

</section>

<!-- ═══ SPECIMEN CATALOGUE TICKER ═══ -->
<div class="specimen-ticker" id="drops" aria-label="<?php esc_attr_e( 'Limited Edition Drops', 'skyyrose-flagship' ); ?>">
	<div class="specimen-ticker-mask" aria-hidden="true">
		<div class="specimen-track" id="specimenTrack">
			<?php for ( $i = 0; $i < 3; $i++ ) : ?>
				<?php foreach ( $specimens as $item ) : ?>
					<span class="specimen-item"><?php echo esc_html( $item ); ?></span>
					<span class="specimen-sep" aria-hidden="true">◆</span>
				<?php endforeach; ?>
			<?php endfor; ?>
		</div>
	</div>
</div>

<!-- ═══ NARRATIVE SCROLL — Story embedded in editorial prose ═══ -->
<section class="narrative" id="issue" aria-label="<?php esc_attr_e( 'The Story', 'skyyrose-flagship' ); ?>">
	<p class="narrative-prose rv">
		<?php esc_html_e( 'The architecture of modern garments must carry the weight of the environments they inherit. Every hem weighed against the gravity of the streets we come from — built not in pristine ateliers, but in The Town, pouring obsession into fabrics that function as armor.', 'skyyrose-flagship' ); ?>
	</p>

	<figure class="narrative-artifact rv rv-d1">
		<?php if ( $col_br ) : ?>
		<div class="narrative-artifact-img">
			<img src="<?php echo esc_url( $col_br['image'] ); ?>"
			     alt="<?php esc_attr_e( 'Black Rose collection — heavyweight construction detail', 'skyyrose-flagship' ); ?>"
			     loading="lazy" decoding="async" width="960" height="640">
		</div>
		<?php endif; ?>
		<figcaption class="narrative-artifact-cap font-mono">
			<?php esc_html_e( 'Artifact_001 / Black Rose — Limited Edition Archive', 'skyyrose-flagship' ); ?>
		</figcaption>
	</figure>

	<p class="narrative-prose rv rv-d2">
		<?php esc_html_e( 'Named after a daughter. Built by a father. The SkyyRose Collection began as a refusal — to become a statistic, to give up, to let The Town write the ending. Through failed websites, deceitful manufacturers, and single parenthood with no support, Corey Foster built something real. This is what it looks like when love becomes architecture.', 'skyyrose-flagship' ); ?>
	</p>
</section>

<!-- ═══ FOUNDER QUOTE ═══ -->
<section class="quote-section quote-v7" id="story" aria-label="<?php esc_attr_e( 'Founder Quote', 'skyyrose-flagship' ); ?>">
	<div class="quote-v7-inner">
		<div class="quote-v7-text rv">
			<blockquote class="quote-v7-words">
				<?php echo wp_kses_post( __( '&ldquo;Believe in your vision<br>even when others<br>can&rsquo;t see it.&rdquo;', 'skyyrose-flagship' ) ); ?>
			</blockquote>
			<hr class="quote-v7-rule" aria-hidden="true">
			<p class="quote-v7-attr font-mono"><?php esc_html_e( 'Corey Foster — Founder', 'skyyrose-flagship' ); ?></p>
		</div>
		<div class="quote-v7-portrait rv-right">
			<img src="<?php echo esc_url( $founder_img ); ?>"
			     alt="<?php esc_attr_e( 'Corey Foster, founder of SkyyRose', 'skyyrose-flagship' ); ?>"
			     loading="lazy" decoding="async" width="600" height="800">
			<div class="quote-v7-portrait-shade" aria-hidden="true"></div>
		</div>
	</div>
</section>

<!-- ═══ PRESS STRIP ═══ -->
<div class="press press-v7 rv">
	<p class="press-label font-mono"><?php esc_html_e( 'Acknowledged By', 'skyyrose-flagship' ); ?></p>
	<div class="press-logos-v7">
		<?php foreach ( $press as $p ) : ?>
			<span class="press-item press-item--<?php echo esc_attr( $p['font'] ); ?>"><?php echo esc_html( $p['name'] ); ?></span>
		<?php endforeach; ?>
	</div>
</div>

<!-- ═══ CRAFT ═══ -->
<section class="craft" id="craft" aria-label="<?php esc_attr_e( 'Our Craft', 'skyyrose-flagship' ); ?>">
	<div class="craft-inner">
		<div class="craft-header rv-clip-up">
			<h2><?php esc_html_e( 'The Craft', 'skyyrose-flagship' ); ?></h2>
			<p><?php esc_html_e( 'Every stitch, every fabric, every detail — intentional.', 'skyyrose-flagship' ); ?></p>
		</div>
		<div class="craft-grid stagger-grid">
			<?php foreach ( $craft_cards as $card ) : ?>
				<div class="craft-card">
					<div class="craft-icon" aria-hidden="true"><?php echo wp_kses( $card['icon'], $svg_whitelist ); ?></div>
					<div class="craft-label"><?php echo esc_html( $card['label'] ); ?></div>
					<p class="craft-desc"><?php echo esc_html( $card['desc'] ); ?></p>
				</div>
			<?php endforeach; ?>
		</div>
	</div>
</section>

<!-- ═══ DROP LIST — "Join the Drop List" not "Newsletter" ═══ -->
<section class="newsletter newsletter-v7" id="community" aria-label="<?php esc_attr_e( 'Drop List', 'skyyrose-flagship' ); ?>">
	<div class="nl-v7-ghost font-cinzel" aria-hidden="true"><?php esc_html_e( 'SKYYROSE', 'skyyrose-flagship' ); ?></div>
	<div class="nl-v7-inner">
		<div class="nl-v7-left rv">
			<p class="nl-v7-label font-mono"><?php esc_html_e( 'Join the Drop List', 'skyyrose-flagship' ); ?></p>
			<p class="nl-v7-desc"><?php esc_html_e( 'Exclusive access to drops, pre-orders, and private events. No noise.', 'skyyrose-flagship' ); ?></p>
			<div class="nl-form nl-v7-form">
				<input type="email" class="nl-input nl-v7-input" id="nlEmail"
				       placeholder="<?php esc_attr_e( 'Your email', 'skyyrose-flagship' ); ?>"
				       aria-label="<?php esc_attr_e( 'Email address', 'skyyrose-flagship' ); ?>" required>
				<button type="button" class="nl-submit nl-v7-submit" aria-label="<?php esc_attr_e( 'Submit', 'skyyrose-flagship' ); ?>">→</button>
			</div>
		</div>
		<nav class="nl-v7-nav rv-right" aria-label="<?php esc_attr_e( 'Footer Navigation', 'skyyrose-flagship' ); ?>">
			<div class="nl-v7-nav-col">
				<span class="nl-v7-nav-hd font-mono"><?php esc_html_e( 'Worlds', 'skyyrose-flagship' ); ?></span>
				<?php foreach ( $collections as $c ) : ?>
					<a href="<?php echo esc_url( $c['link'] ); ?>"><?php echo esc_html( $c['name'] ); ?></a>
				<?php endforeach; ?>
			</div>
			<div class="nl-v7-nav-col">
				<span class="nl-v7-nav-hd font-mono"><?php esc_html_e( 'Brand', 'skyyrose-flagship' ); ?></span>
				<a href="<?php echo esc_url( home_url( '/about/' ) ); ?>"><?php esc_html_e( 'About', 'skyyrose-flagship' ); ?></a>
				<a href="#issue"><?php esc_html_e( 'Issue', 'skyyrose-flagship' ); ?></a>
				<a href="<?php echo esc_url( home_url( '/about/' ) ); ?>"><?php esc_html_e( 'Manifesto', 'skyyrose-flagship' ); ?></a>
				<a href="<?php echo esc_url( home_url( '/shipping-returns/' ) ); ?>"><?php esc_html_e( 'Returns', 'skyyrose-flagship' ); ?></a>
			</div>
		</nav>
	</div>
	<div class="nl-v7-bottom">
		<span class="font-mono">&copy; <?php echo esc_html( gmdate( 'Y' ) ); ?> <?php esc_html_e( 'SkyyRose', 'skyyrose-flagship' ); ?></span>
		<span class="nl-v7-tagline"><?php esc_html_e( 'Luxury Grows from Concrete.', 'skyyrose-flagship' ); ?></span>
		<div class="ft-social">
			<a href="https://instagram.com/skyyroseco" target="_blank" rel="noopener noreferrer"><?php esc_html_e( 'IG', 'skyyrose-flagship' ); ?></a>
			<a href="https://tiktok.com/@skyyroseco" target="_blank" rel="noopener noreferrer"><?php esc_html_e( 'TT', 'skyyrose-flagship' ); ?></a>
			<a href="https://x.com/skyyroseco" target="_blank" rel="noopener noreferrer"><?php esc_html_e( 'X', 'skyyrose-flagship' ); ?></a>
		</div>
	</div>
</section>

<script data-jetpack-boost="ignore" type="application/ld+json"><?php
echo wp_json_encode( array(
	'@context'     => 'https://schema.org',
	'@type'        => 'Organization',
	'name'         => 'SkyyRose',
	'url'          => home_url( '/' ),
	'logo'         => SKYYROSE_ASSETS_URI . '/branding/skyyrose-monogram.webp',
	'description'  => 'Oakland luxury streetwear. Gender-neutral, limited edition designs. Built by a father, named after a daughter.',
	'foundingDate' => '2020',
	'founder'      => array( '@type' => 'Person', 'name' => 'Corey Foster' ),
	'address'      => array( '@type' => 'PostalAddress', 'addressLocality' => 'Oakland', 'addressRegion' => 'CA', 'addressCountry' => 'US' ),
	'sameAs'       => array( 'https://instagram.com/skyyroseco' ),
), JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT );
?></script>

<button type="button" class="back-to-top" aria-label="<?php esc_attr_e( 'Back to top', 'skyyrose-flagship' ); ?>">
	<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4l-8 8h5v8h6v-8h5z"/></svg>
</button>

</main>

<?php
$homepage_js_path = SKYYROSE_DIR . '/assets/js/homepage-v2.js';
if ( file_exists( $homepage_js_path ) ) :
?>
<script><?php
	// phpcs:ignore WordPress.WP.AlternativeFunctions.file_get_contents_file_get_contents
	echo file_get_contents( $homepage_js_path );
?></script>
<?php endif; ?>

<?php
get_template_part( 'template-parts/size-guide-modal' );
get_template_part( 'template-parts/cookie-consent' );
get_template_part( 'template-parts/mobile-bottom-nav' );
get_template_part( 'template-parts/skyy-mascot' );
?>

<div id="toast-container" class="toast-container" aria-live="polite" aria-atomic="true"></div>

<?php wp_footer(); ?>
</body>
</html>
