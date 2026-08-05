<?php
/**
 * Flagship marketplace homepage.
 *
 * @package SkyyRoseFlagship2
 */

defined( 'ABSPATH' ) || exit;

$shop_url = function_exists( 'wc_get_page_permalink' ) ? wc_get_page_permalink( 'shop' ) : home_url( '/shop/' );

get_header();

if ( skyyrose2_render_builder_location( 'single' ) ) {
	get_footer();
	return;
}
if ( skyyrose2_render_builder_owned_content() ) {
	get_footer();
	return;
}
?>
<main id="primary" class="sr2-home">
	<section class="sr2-home-hero" aria-labelledby="sr2-home-title" data-hero-depth>
		<div class="sr2-home-hero__media" aria-hidden="true">
			<img src="<?php echo esc_url( skyyrose2_sot_asset_uri( 'branding/hero/flagship-house-runway-gpt2-1440w.webp' ) ); ?>" srcset="<?php echo esc_attr( skyyrose2_sot_asset_uri( 'branding/hero/flagship-house-runway-gpt2-640w.webp' ) ); ?> 640w, <?php echo esc_attr( skyyrose2_sot_asset_uri( 'branding/hero/flagship-house-runway-gpt2-960w.webp' ) ); ?> 960w, <?php echo esc_attr( skyyrose2_sot_asset_uri( 'branding/hero/flagship-house-runway-gpt2-1440w.webp' ) ); ?> 1440w, <?php echo esc_attr( skyyrose2_sot_asset_uri( 'branding/hero/flagship-house-runway-gpt2.webp' ) ); ?> 1920w" sizes="100vw" alt="" width="1920" height="1080" fetchpriority="high" decoding="async">
		</div>
		<div class="sr2-home-hero__veil" aria-hidden="true"></div>
		<div class="sr2-home-hero__copy">
			<p class="sr2-eyebrow">Oakland, California · Est. 2020</p>
			<h1 id="sr2-home-title" class="screen-reader-text">SKYYROSE</h1>
			<div class="sr2-home-hero__motion-mark" aria-hidden="true">
				<video muted loop playsinline preload="metadata" poster="<?php echo esc_url( skyyrose2_sot_asset_uri( 'video/tsrc-spin-alpha.webp' ) ); ?>" data-brand-spin>
					<source src="<?php echo esc_url( skyyrose2_sot_asset_uri( 'video/tsrc-spin-alpha.webm' ) ); ?>" type="video/webm">
				</video>
			</div>
			<p class="sr2-home-hero__statement"><?php esc_html_e( 'Luxury grows from concrete. Four living worlds. Pieces built to hold story.', 'skyyrose-flagship-2' ); ?></p>
			<div class="sr2-actions"><a class="sr2-button sr2-button--fill" href="<?php echo esc_url( $shop_url ); ?>"><?php esc_html_e( 'Shop the house', 'skyyrose-flagship-2' ); ?></a><a class="sr2-button" href="#collections"><?php esc_html_e( 'Enter collections', 'skyyrose-flagship-2' ); ?></a></div>
		</div>
		<div class="sr2-home-hero__edition" aria-hidden="true"><span>01</span><span>SKYYROSE / OAKLAND</span></div>
		<a class="sr2-home-hero__scroll" href="#collections"><span><?php esc_html_e( 'Scroll into the house', 'skyyrose-flagship-2' ); ?></span><i aria-hidden="true"></i></a>
	</section>

	<div class="sr2-marquee" aria-label="<?php esc_attr_e( 'SkyyRose house codes', 'skyyrose-flagship-2' ); ?>">
		<div><span>SKYYROSE</span><b>✦</b><span>OAKLAND BORN</span><b>✦</b><span>LIMITED EDITIONS</span><b>✦</b><span>LUXURY GROWS FROM CONCRETE</span><b>✦</b><span aria-hidden="true">SKYYROSE</span><b aria-hidden="true">✦</b><span aria-hidden="true">OAKLAND BORN</span><b aria-hidden="true">✦</b><span aria-hidden="true">LIMITED EDITIONS</span><b aria-hidden="true">✦</b><span aria-hidden="true">LUXURY GROWS FROM CONCRETE</span><b aria-hidden="true">✦</b></div>
	</div>

	<div id="collections">
		<?php skyyrose2_render_collection_rail(); ?>
	</div>

	<section id="new" class="sr2-section sr2-section--products">
		<header class="sr2-section-head sr2-section-head--split"><div><p><?php esc_html_e( 'In Rotation', 'skyyrose-flagship-2' ); ?></p><h2><?php esc_html_e( 'Pieces with presence.', 'skyyrose-flagship-2' ); ?></h2></div><a class="sr2-text-link" href="<?php echo esc_url( $shop_url ); ?>"><?php esc_html_e( 'Shop all pieces', 'skyyrose-flagship-2' ); ?> <span aria-hidden="true">↗</span></a></header>
		<?php skyyrose2_product_cards( 6, '', true ); ?>
	</section>

	<section class="sr2-house-story" aria-labelledby="sr2-house-story-title">
		<div class="sr2-house-story__media sr2-image-reveal"><img src="<?php echo esc_url( skyyrose2_sot_asset_uri( 'branding/hero/signature-golden-gate-yacht-1280w.webp' ) ); ?>" alt="SkyyRose yacht beside the Golden Gate Bridge at night" width="1280" height="553" loading="lazy" decoding="async"></div>
		<div class="sr2-house-story__copy">
			<p class="sr2-eyebrow"><?php esc_html_e( 'House Story · Oakland', 'skyyrose-flagship-2' ); ?></p>
			<h2 id="sr2-house-story-title"><?php esc_html_e( 'Built by a father. Named after a daughter.', 'skyyrose-flagship-2' ); ?></h2>
			<blockquote><?php esc_html_e( 'Four years ago I never would have thought I\'d be here. I had no drive, lost it all, a baby on the way, and was broke. But we knew we had to get it by any means necessary.', 'skyyrose-flagship-2' ); ?></blockquote>
			<p><?php esc_html_e( 'Her name became the house name. Oakland became the point of view. Every collection carries that promise forward.', 'skyyrose-flagship-2' ); ?></p>
			<a class="sr2-text-link" href="<?php echo esc_url( home_url( '/about/' ) ); ?>"><?php esc_html_e( 'Read the origin', 'skyyrose-flagship-2' ); ?> <span aria-hidden="true">↗</span></a>
		</div>
		</section>

		<section class="sr2-section sr2-section--letter" aria-labelledby="sr2-letter-title">
			<div class="sr2-section-head"><p><?php esc_html_e( 'The house letter', 'skyyrose-flagship-2' ); ?></p><h2 id="sr2-letter-title"><?php esc_html_e( 'The first rose was drawn at 4 AM.', 'skyyrose-flagship-2' ); ?></h2></div>
			<div class="sr2-section__copy">
				<p><?php esc_html_e( 'I drew the first rose on a night I couldn\'t afford dinner. Broke, a baby on the way, every manufacturer I\'d worked with had scammed me. But I sat there sketching that script logo until 4 AM because something in me knew — if I could get this right, everything changes.', 'skyyrose-flagship-2' ); ?></p>
				<p><?php esc_html_e( 'Signature is that night made permanent. The rest of the house grew from there.', 'skyyrose-flagship-2' ); ?></p>
				<a class="sr2-text-link" href="<?php echo esc_url( $shop_url ); ?>"><?php esc_html_e( 'Shop the pieces that began it', 'skyyrose-flagship-2' ); ?> <span aria-hidden="true">↗</span></a>
			</div>
		</section>

	<section class="sr2-reserve-portal" aria-labelledby="sr2-reserve-title">
		<div class="sr2-reserve-portal__media sr2-image-reveal"><img src="<?php echo esc_url( skyyrose2_sot_asset_uri( 'images/immersive/scene-black-rose-moon-court-gpt2.webp' ) ); ?>" alt="Black Rose collection world at midnight" width="1280" height="549" loading="lazy" decoding="async"></div>
		<div class="sr2-reserve-portal__copy">
			<p class="sr2-eyebrow"><?php esc_html_e( 'Future Editions', 'skyyrose-flagship-2' ); ?></p>
			<h2 id="sr2-reserve-title"><?php esc_html_e( 'Reserve the next chapter.', 'skyyrose-flagship-2' ); ?></h2>
			<p><?php esc_html_e( 'Choose the world. Choose the piece. Enter the pre-order room when a live edition is ready to be held.', 'skyyrose-flagship-2' ); ?></p>
			<a class="sr2-button sr2-button--fill" href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>"><?php esc_html_e( 'Enter pre-order', 'skyyrose-flagship-2' ); ?></a>
		</div>
	</section>
</main>
<?php
get_footer();
