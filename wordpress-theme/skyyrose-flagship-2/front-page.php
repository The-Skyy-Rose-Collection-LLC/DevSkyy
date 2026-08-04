<?php
/**
 * Flagship marketplace homepage.
 *
 * @package SkyyRoseFlagship2
 */

defined( 'ABSPATH' ) || exit;

$shop_url = function_exists( 'wc_get_page_permalink' ) ? wc_get_page_permalink( 'shop' ) : home_url( '/shop/' );

get_header();
?>
<main id="primary" class="sr2-home">
	<section class="sr2-home-hero" aria-labelledby="sr2-home-title" data-hero-depth>
		<div class="sr2-home-hero__media" aria-hidden="true">
			<img src="<?php echo esc_url( skyyrose2_sot_asset_uri( 'branding/hero/flagship-house-runway-gpt2.webp' ) ); ?>" alt="" width="1920" height="1080" fetchpriority="high" decoding="sync">
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
			<p class="sr2-home-hero__statement"><?php esc_html_e( 'Independent luxury. Four living worlds. Pieces built to hold story.', 'skyyrose-flagship-2' ); ?></p>
			<div class="sr2-actions"><a class="sr2-button sr2-button--fill" href="<?php echo esc_url( $shop_url ); ?>"><?php esc_html_e( 'Shop the house', 'skyyrose-flagship-2' ); ?></a><a class="sr2-button" href="#collections"><?php esc_html_e( 'Enter collections', 'skyyrose-flagship-2' ); ?></a></div>
		</div>
		<div class="sr2-home-hero__edition" aria-hidden="true"><span>01</span><span>SKYYROSE / OAKLAND</span></div>
		<a class="sr2-home-hero__scroll" href="#collections"><span><?php esc_html_e( 'Scroll into the house', 'skyyrose-flagship-2' ); ?></span><i aria-hidden="true"></i></a>
	</section>

	<div class="sr2-marquee" aria-label="<?php esc_attr_e( 'SkyyRose house codes', 'skyyrose-flagship-2' ); ?>">
		<div><span>SKYYROSE</span><b>✦</b><span>OAKLAND MADE</span><b>✦</b><span>LIMITED EDITIONS</span><b>✦</b><span>STORY IN EVERY STITCH</span><b>✦</b><span aria-hidden="true">SKYYROSE</span><b aria-hidden="true">✦</b><span aria-hidden="true">OAKLAND MADE</span><b aria-hidden="true">✦</b><span aria-hidden="true">LIMITED EDITIONS</span><b aria-hidden="true">✦</b><span aria-hidden="true">STORY IN EVERY STITCH</span><b aria-hidden="true">✦</b></div>
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
			<p><?php esc_html_e( 'SkyyRose turns family, survival, love, and Oakland ambition into wearable worlds. Not merch. Not trend-chasing. A house with memory.', 'skyyrose-flagship-2' ); ?></p>
			<a class="sr2-text-link" href="<?php echo esc_url( home_url( '/about/' ) ); ?>"><?php esc_html_e( 'Read the origin', 'skyyrose-flagship-2' ); ?> <span aria-hidden="true">↗</span></a>
		</div>
	</section>

	<section class="sr2-reserve-portal" aria-labelledby="sr2-reserve-title">
		<div class="sr2-reserve-portal__media sr2-image-reveal"><img src="<?php echo esc_url( skyyrose2_sot_asset_uri( 'images/immersive/scene-black-rose-moon-court-gpt2.webp' ) ); ?>" alt="Black Rose collection world at midnight" width="1280" height="549" loading="lazy" decoding="async"></div>
		<div class="sr2-reserve-portal__copy">
			<p class="sr2-eyebrow"><?php esc_html_e( 'Future Editions', 'skyyrose-flagship-2' ); ?></p>
			<h2 id="sr2-reserve-title"><?php esc_html_e( 'Reserve the next chapter.', 'skyyrose-flagship-2' ); ?></h2>
			<p><?php esc_html_e( 'Choose the world. Choose the piece. Hold your place before the edition closes.', 'skyyrose-flagship-2' ); ?></p>
			<a class="sr2-button sr2-button--fill" href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>"><?php esc_html_e( 'Enter pre-order', 'skyyrose-flagship-2' ); ?></a>
		</div>
	</section>
</main>
<?php
get_footer();
