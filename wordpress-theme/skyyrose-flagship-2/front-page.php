<?php
/**
 * Front Page — V1 storefront composition.
 *
 * The V2 asset system supplies the imagery and WooCommerce supplies product
 * truth, but the page anatomy is intentionally the same five-part structure
 * as the proven V1 storefront: hero, collection rail, product grid,
 * pre-order room, and founder origin.
 *
 * @package SkyyRoseFlagship2
 */

defined( 'ABSPATH' ) || exit;

$collections = array();
foreach ( skyyrose2_collections() as $slug => $collection ) {
	$collections[] = array(
		'slug'   => $slug,
		'label'  => $collection['name'],
		'poetic' => $collection['line'],
		'href'   => skyyrose2_collection_url( $slug ),
		'still'  => skyyrose2_scroll_world_asset_uri( $collection['portrait'] ),
	);
}

$shop_url = function_exists( 'wc_get_page_permalink' ) ? wc_get_page_permalink( 'shop' ) : home_url( '/shop/' );

get_header();
?>
<main id="primary" class="site-main sr-home" role="main" tabindex="-1">
	<section class="sr-home__hero" aria-labelledby="sr-home-title">
		<div class="sr-home__hero-media" aria-hidden="true">
			<video class="sr-home__hero-video" poster="<?php echo esc_url( skyyrose2_sot_asset_uri( 'branding/hero/flagship-house-runway-gpt2.webp' ) ); ?>" muted playsinline preload="metadata" data-hero-video>
				<source src="<?php echo esc_url( skyyrose2_sot_asset_uri( 'video/rose-gold-spin-alpha.webm' ) ); ?>" type="video/webm">
			</video>
		</div>
		<nav class="sr-home__hero-nav liquid-glass" aria-label="<?php esc_attr_e( 'Primary navigation', 'skyyrose-flagship-2' ); ?>">
			<a class="sr-home__hero-initial liquid-glass" href="<?php echo esc_url( home_url( '/' ) ); ?>" aria-label="<?php esc_attr_e( 'SkyyRose home', 'skyyrose-flagship-2' ); ?>">S</a>
			<div class="sr-home__hero-links">
				<a href="<?php echo esc_url( home_url( '/collections/' ) ); ?>"><?php esc_html_e( 'Collections', 'skyyrose-flagship-2' ); ?></a>
				<a href="<?php echo esc_url( $shop_url ); ?>"><?php esc_html_e( 'Shop', 'skyyrose-flagship-2' ); ?></a>
				<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>"><?php esc_html_e( 'Pre-Order', 'skyyrose-flagship-2' ); ?></a>
				<a href="<?php echo esc_url( home_url( '/about/' ) ); ?>"><?php esc_html_e( 'About', 'skyyrose-flagship-2' ); ?></a>
				<a href="<?php echo esc_url( home_url( '/contact/' ) ); ?>"><?php esc_html_e( 'Contact', 'skyyrose-flagship-2' ); ?></a>
				<a class="liquid-glass-strong" href="<?php echo esc_url( $shop_url ); ?>"><?php esc_html_e( 'Shop the House', 'skyyrose-flagship-2' ); ?> <span aria-hidden="true">↗</span></a>
			</div>
			<span class="sr-home__hero-nav-spacer" aria-hidden="true"></span>
		</nav>
		<div class="sr-home__hero-content">
			<p class="sr-home__hero-badge liquid-glass"><b><?php esc_html_e( 'New', 'skyyrose-flagship-2' ); ?></b><span><?php esc_html_e( 'The house is open · Oakland, California', 'skyyrose-flagship-2' ); ?></span></p>
			<h1 id="sr-home-title" class="sr-home__title" data-hero-headline><?php esc_html_e( 'Luxury Grows From Concrete. The Rose Remains.', 'skyyrose-flagship-2' ); ?></h1>
			<p class="sr-home__lede"><?php esc_html_e( 'Independent luxury streetwear rooted in The Town. Built by a father, named after a daughter, and made for every chapter that comes next.', 'skyyrose-flagship-2' ); ?></p>
			<div class="sr-home__actions">
				<a class="sr-home__button sr-home__button--solid liquid-glass-strong" href="<?php echo esc_url( $shop_url ); ?>"><?php esc_html_e( 'Shop New Arrivals', 'skyyrose-flagship-2' ); ?> <span aria-hidden="true">↗</span></a>
				<a class="sr-home__button sr-home__button--line" href="#collections"><span aria-hidden="true">▶</span> <?php esc_html_e( 'Enter the worlds', 'skyyrose-flagship-2' ); ?></a>
			</div>
			<div class="sr-home__hero-stats" aria-label="<?php esc_attr_e( 'SkyyRose house facts', 'skyyrose-flagship-2' ); ?>">
				<div class="liquid-glass"><span aria-hidden="true">✦</span><strong>04</strong><small><?php esc_html_e( 'Living worlds', 'skyyrose-flagship-2' ); ?></small></div>
				<div class="liquid-glass"><span aria-hidden="true">◈</span><strong>2020</strong><small><?php esc_html_e( 'Oakland founded', 'skyyrose-flagship-2' ); ?></small></div>
			</div>
		</div>
		<div class="sr-home__hero-partners liquid-glass" aria-label="<?php esc_attr_e( 'SkyyRose credibility', 'skyyrose-flagship-2' ); ?>"><span><?php esc_html_e( 'A house with memory', 'skyyrose-flagship-2' ); ?></span><b>SkyyRose</b><b>Oakland</b><b>The Town</b><b>Independent</b><b>Limited</b></div>
	</section>

	<section id="collections" class="sr-home__collections" aria-labelledby="sr-home-collections-title">
		<div class="sr-home__section-head">
			<p class="sr-home__eyebrow"><?php esc_html_e( 'Choose Your World', 'skyyrose-flagship-2' ); ?></p>
			<h2 id="sr-home-collections-title"><?php esc_html_e( 'Four collections. Four points of view.', 'skyyrose-flagship-2' ); ?></h2>
			<p><?php esc_html_e( 'Walk into a collection, shop its pieces, then stay for its world.', 'skyyrose-flagship-2' ); ?></p>
		</div>
		<div class="sr-home__collection-rail" role="region" aria-label="<?php esc_attr_e( 'Collection worlds. Scroll horizontally to explore.', 'skyyrose-flagship-2' ); ?>" tabindex="0">
			<?php foreach ( $collections as $index => $collection ) : ?>
				<article class="sr-home__collection" data-collection="<?php echo esc_attr( $collection['slug'] ); ?>">
					<a class="sr-home__collection-frame" href="<?php echo esc_url( $collection['href'] ); ?>">
						<img src="<?php echo esc_url( $collection['still'] ); ?>" alt="<?php echo esc_attr( $collection['label'] ); ?>" width="1920" height="1275" loading="<?php echo 0 === $index ? 'eager' : 'lazy'; ?>" decoding="async">
						<span class="sr-home__collection-shade" aria-hidden="true"></span>
						<span class="sr-home__collection-index"><?php echo esc_html( sprintf( '%02d', $index + 1 ) ); ?></span>
						<span class="sr-home__collection-copy">
							<strong><?php echo esc_html( $collection['label'] ); ?></strong>
							<span><?php echo esc_html( $collection['poetic'] ); ?></span>
							<em><?php esc_html_e( 'Shop Collection', 'skyyrose-flagship-2' ); ?> <span aria-hidden="true">→</span></em>
						</span>
					</a>
				</article>
			<?php endforeach; ?>
		</div>
		<p class="sr-home__rail-note" aria-hidden="true"><?php esc_html_e( 'Scroll to move through worlds', 'skyyrose-flagship-2' ); ?> <span>→</span></p>
	</section>

	<section id="preorder-jersey-series" class="sr-home__bay-map sr-home__bay-map--preorder" aria-labelledby="sr-home-bay-map-title" data-bay-map>
		<div class="sr-home__bay-map-copy">
			<p class="sr-home__eyebrow"><?php esc_html_e( 'Jersey Series · Bay Area Pre-Order', 'skyyrose-flagship-2' ); ?></p>
			<h2 id="sr-home-bay-map-title"><?php esc_html_e( 'Three cities. One local language. Reserve yours.', 'skyyrose-flagship-2' ); ?></h2>
			<p><?php esc_html_e( 'From Oakland concrete to San Francisco fog to San Jose nights, each jersey is a chapter in the Bay Area story. Reserve the chapter that is yours before the edition closes.', 'skyyrose-flagship-2' ); ?></p>
			<a class="sr-home__button sr-home__button--line liquid-glass-strong" href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>"><?php esc_html_e( 'Reserve the Jersey Series', 'skyyrose-flagship-2' ); ?> ↗</a>
		</div>
		<div class="sr-home__bay-map-art" role="img" aria-label="<?php esc_attr_e( 'Stylized Bay Area route connecting Oakland, San Francisco, and San Jose', 'skyyrose-flagship-2' ); ?>">
			<svg viewBox="0 0 720 560" aria-hidden="true" focusable="false">
				<path class="sr-home__bay-map-water" d="M0 0h720v560H0z" />
				<path class="sr-home__bay-map-route" pathLength="1" d="M252 145 C230 215 300 240 322 288 S350 400 285 470" />
				<g class="sr-home__bay-map-stop" data-bay-stop="oakland" tabindex="0"><circle class="sr-home__bay-map-ripple" cx="322" cy="288" r="22" /><circle class="sr-home__bay-map-dot" cx="322" cy="288" r="7" /><text x="340" y="282">OAKLAND</text><text x="340" y="303">01 · THE ROOT</text></g>
				<g class="sr-home__bay-map-stop" data-bay-stop="san-francisco" tabindex="0"><circle class="sr-home__bay-map-ripple" cx="252" cy="145" r="22" /><circle class="sr-home__bay-map-dot" cx="252" cy="145" r="7" /><text x="270" y="139">SAN FRANCISCO</text><text x="270" y="160">02 · THE FOG</text></g>
				<g class="sr-home__bay-map-stop" data-bay-stop="san-jose" tabindex="0"><circle class="sr-home__bay-map-ripple" cx="285" cy="470" r="22" /><circle class="sr-home__bay-map-dot" cx="285" cy="470" r="7" /><text x="303" y="464">SAN JOSE</text><text x="303" y="485">03 · THE NIGHT</text></g>
			</svg>
			<p class="sr-home__bay-map-status" aria-live="polite" data-bay-status><?php esc_html_e( 'Follow the route to reserve', 'skyyrose-flagship-2' ); ?></p>
		</div>
	</section>

	<section id="new-arrivals" class="sr-home__products sr2-section sr2-section--products">
		<header class="product-grid-section__header sr-home__section-head">
			<p class="sr-home__eyebrow"><?php esc_html_e( 'In Rotation', 'skyyrose-flagship-2' ); ?></p>
			<h2 class="product-grid-section__heading"><?php esc_html_e( 'Pieces In Rotation', 'skyyrose-flagship-2' ); ?></h2>
			<p class="product-grid-section__subheading"><?php esc_html_e( 'Verified pieces from across the house.', 'skyyrose-flagship-2' ); ?></p>
		</header>
		<?php skyyrose2_product_cards( 6, '', true ); ?>
	</section>

	<section class="sr-home__preorder" aria-labelledby="sr-home-preorder-title">
		<div class="sr-home__preorder-mark" aria-hidden="true"><img src="<?php echo esc_url( skyyrose2_sot_asset_uri( 'images/preorder/black-rose-salon.webp' ) ); ?>" alt="" width="1280" height="720" loading="lazy" decoding="async"></div>
		<div class="sr-home__preorder-copy">
			<p class="sr-home__eyebrow"><?php esc_html_e( 'Reserve Future Pieces', 'skyyrose-flagship-2' ); ?></p>
			<h2 id="sr-home-preorder-title"><?php esc_html_e( 'Pre-order is its own room.', 'skyyrose-flagship-2' ); ?></h2>
			<p><?php esc_html_e( 'No noise. No manufactured countdown. Choose collection, choose piece, reserve your place.', 'skyyrose-flagship-2' ); ?></p>
			<a class="sr-home__button sr-home__button--line" href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>"><?php esc_html_e( 'Enter Pre-Order', 'skyyrose-flagship-2' ); ?></a>
		</div>
	</section>

	<section class="sr-home__origin" aria-labelledby="sr-home-origin-title">
		<img src="<?php echo esc_url( skyyrose2_sot_asset_uri( 'branding/hero/signature-golden-gate-yacht-1280w.webp' ) ); ?>" alt="SkyyRose house beside the Golden Gate Bridge at night" width="1280" height="553" loading="lazy" decoding="async">
		<div>
			<p class="sr-home__eyebrow"><?php esc_html_e( 'Founder Story', 'skyyrose-flagship-2' ); ?></p>
			<h2 id="sr-home-origin-title"><?php esc_html_e( 'Built by a father. Named after a daughter.', 'skyyrose-flagship-2' ); ?></h2>
			<a href="<?php echo esc_url( home_url( '/about/' ) ); ?>"><?php esc_html_e( 'Meet SkyyRose', 'skyyrose-flagship-2' ); ?> <span aria-hidden="true">→</span></a>
		</div>
	</section>

	<section class="sr-home__flagship" aria-labelledby="sr-home-flagship-title">
		<header class="sr-home__section-head">
			<p class="sr-home__eyebrow"><?php esc_html_e( 'The House Index', 'skyyrose-flagship-2' ); ?></p>
			<h2 id="sr-home-flagship-title"><?php esc_html_e( 'Every piece carries a world.', 'skyyrose-flagship-2' ); ?></h2>
			<p><?php esc_html_e( 'Move from Oakland atelier to midnight court, from the protected wound to the heir’s first runway. The story is the product experience.', 'skyyrose-flagship-2' ); ?></p>
		</header>
		<div class="sr-home__flagship-grid">
			<a class="sr-home__flagship-card sr-home__flagship-card--wide" href="<?php echo esc_url( skyyrose2_collection_url( 'signature' ) ); ?>">
				<img src="<?php echo esc_url( skyyrose2_sot_asset_uri( 'images/immersive/scene-signature-oakland-atelier-gpt2.webp' ) ); ?>" alt="<?php esc_attr_e( 'Signature Oakland atelier', 'skyyrose-flagship-2' ); ?>" width="1280" height="720" loading="lazy" decoding="async">
				<span><small><?php esc_html_e( '01 · Signature', 'skyyrose-flagship-2' ); ?></small><strong><?php esc_html_e( 'The origin is the signature.', 'skyyrose-flagship-2' ); ?><b><?php esc_html_e( 'Enter the atelier', 'skyyrose-flagship-2' ); ?> ↗</b></strong></span>
			</a>
			<a class="sr-home__flagship-card" href="<?php echo esc_url( skyyrose2_collection_url( 'black-rose' ) ); ?>">
				<img src="<?php echo esc_url( skyyrose2_sot_asset_uri( 'images/immersive/scene-black-rose-moon-court-gpt2.webp' ) ); ?>" alt="<?php esc_attr_e( 'Black Rose moon court', 'skyyrose-flagship-2' ); ?>" width="960" height="1200" loading="lazy" decoding="async">
				<span><small><?php esc_html_e( '02 · Black Rose', 'skyyrose-flagship-2' ); ?></small><strong><?php esc_html_e( 'Beauty without permission.', 'skyyrose-flagship-2' ); ?><b><?php esc_html_e( 'Enter the court', 'skyyrose-flagship-2' ); ?> ↗</b></strong></span>
			</a>
			<a class="sr-home__flagship-card" href="<?php echo esc_url( skyyrose2_collection_url( 'love-hurts' ) ); ?>">
				<img src="<?php echo esc_url( skyyrose2_sot_asset_uri( 'images/immersive/scene-love-hurts-cracked-rose-gpt2.webp' ) ); ?>" alt="<?php esc_attr_e( 'Love Hurts cracked rose', 'skyyrose-flagship-2' ); ?>" width="960" height="1200" loading="lazy" decoding="async">
				<span><small><?php esc_html_e( '03 · Love Hurts', 'skyyrose-flagship-2' ); ?></small><strong><?php esc_html_e( 'The wound becomes the wardrobe.', 'skyyrose-flagship-2' ); ?><b><?php esc_html_e( 'Enter the chamber', 'skyyrose-flagship-2' ); ?> ↗</b></strong></span>
			</a>
		</div>
	</section>

	<section class="sr-home__faq" aria-labelledby="sr-home-faq-title">
		<header class="sr-home__section-head">
			<p class="sr-home__eyebrow"><?php esc_html_e( 'House Terms', 'skyyrose-flagship-2' ); ?></p>
			<h2 id="sr-home-faq-title"><?php esc_html_e( 'Know the house before you enter.', 'skyyrose-flagship-2' ); ?></h2>
		</header>
		<div class="sr-home__faq-list">
			<details><summary><?php esc_html_e( 'How do limited editions work?', 'skyyrose-flagship-2' ); ?><span aria-hidden="true">+</span></summary><p><?php esc_html_e( 'Each piece belongs to a defined collection run. Availability and fulfillment timing are shown before checkout, and we do not manufacture artificial urgency.', 'skyyrose-flagship-2' ); ?></p></details>
			<details><summary><?php esc_html_e( 'What is pre-order?', 'skyyrose-flagship-2' ); ?><span aria-hidden="true">+</span></summary><p><?php esc_html_e( 'Pre-order holds your place in a future edition. Enter the dedicated room to see the collection, the piece, and the published fulfillment expectation.', 'skyyrose-flagship-2' ); ?></p></details>
			<details><summary><?php esc_html_e( 'Where can I get fit and shipping guidance?', 'skyyrose-flagship-2' ); ?><span aria-hidden="true">+</span></summary><p><?php esc_html_e( 'Use the fit guide and shipping pages before checkout, or contact the house for concierge help.', 'skyyrose-flagship-2' ); ?></p></details>
		</div>
	</section>

	<section class="sr-home__finale" aria-labelledby="sr-home-finale-title">
		<img src="<?php echo esc_url( skyyrose2_sot_asset_uri( 'images/logos/red-roses-cloud-cluster.webp' ) ); ?>" alt="" width="1280" height="720" loading="lazy" decoding="async">
		<div><p class="sr-home__eyebrow"><?php esc_html_e( 'The Skyy Rose Collection', 'skyyrose-flagship-2' ); ?></p><h2 id="sr-home-finale-title"><?php esc_html_e( 'Luxury grows from concrete.', 'skyyrose-flagship-2' ); ?></h2><a class="sr-home__button sr-home__button--solid liquid-glass-strong" href="<?php echo esc_url( $shop_url ); ?>"><?php esc_html_e( 'Enter the house', 'skyyrose-flagship-2' ); ?> ↗</a></div>
	</section>
</main>
<?php get_footer(); ?>
