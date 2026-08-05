<?php
/**
 * Narrative About page, driven by founder-provided media and house canon.
 *
 * @package SkyyRoseFlagship2
 */

defined( 'ABSPATH' ) || exit;

$film_url = skyyrose2_about_film_url();
$hero_uri = skyyrose2_sot_asset_uri( 'branding/about/skyy-rose-founder-portrait.jpg' );
?>
<section class="sr2-about-hero" aria-labelledby="sr2-page-title" data-hero-depth>
	<div class="sr2-about-hero__media"><img src="<?php echo esc_url( $hero_uri ); ?>" alt="Skyy Rose wearing a white and rose-gold set embroidered with red roses" width="724" height="1086" fetchpriority="high" decoding="async"></div>
	<div class="sr2-about-hero__veil" aria-hidden="true"></div>
	<div class="sr2-about-hero__copy">
		<p class="sr2-eyebrow"><?php esc_html_e( 'Oakland, California · Est. 2020', 'skyyrose-flagship-2' ); ?></p>
		<h1 id="sr2-page-title"><?php esc_html_e( 'Named after a daughter. Built by a father.', 'skyyrose-flagship-2' ); ?></h1>
		<p><?php esc_html_e( 'The Skyy Rose Collection is a promise made in Oakland: build a future a daughter can see herself inside.', 'skyyrose-flagship-2' ); ?></p>
		<a class="sr2-about-hero__scroll" href="#sr2-about-story"><span><?php esc_html_e( 'Enter the story', 'skyyrose-flagship-2' ); ?></span><i aria-hidden="true"></i></a>
	</div>
</section>

<section id="sr2-about-story" class="sr2-about-prologue" aria-labelledby="sr2-about-prologue-title">
	<div><p class="sr2-eyebrow"><?php esc_html_e( 'Chapter 01 · The promise', 'skyyrose-flagship-2' ); ?></p><h2 id="sr2-about-prologue-title"><?php esc_html_e( 'Family became foundation. Concrete became runway.', 'skyyrose-flagship-2' ); ?></h2></div>
	<div class="sr2-about-prologue__copy">
		<blockquote><?php esc_html_e( 'You ask me this four years ago, I never would have thought I would be here. I had no drive, lost it all, a baby on the way, and was broke. But we knew we had to get it by any means necessary.', 'skyyrose-flagship-2' ); ?></blockquote>
		<p><?php esc_html_e( 'SkyyRose began with Corey Foster building from Oakland for a daughter on the way. Her name became the house name; the city became its point of view.', 'skyyrose-flagship-2' ); ?></p>
		<?php if ( trim( get_the_content() ) ) : ?><div class="sr2-page-copy sr2-page-copy--about"><?php the_content(); ?></div><?php endif; ?>
	</div>
</section>

<section class="sr2-about-film" aria-labelledby="sr2-about-film-title">
	<div class="sr2-about-film__head"><p class="sr2-eyebrow"><?php esc_html_e( 'The Skyy Rose Collection film', 'skyyrose-flagship-2' ); ?></p><h2 id="sr2-about-film-title"><?php esc_html_e( 'A family story, held in motion.', 'skyyrose-flagship-2' ); ?></h2></div>
	<?php if ( $film_url ) : ?>
		<video class="sr2-about-film__player" controls playsinline preload="metadata" poster="<?php echo esc_url( $hero_uri ); ?>">
			<source src="<?php echo esc_url( $film_url ); ?>" type="video/mp4">
			<?php esc_html_e( 'Your browser does not support the film player.', 'skyyrose-flagship-2' ); ?>
		</video>
	<?php else : ?>
		<div class="sr2-about-film__handoff"><img src="<?php echo esc_url( $hero_uri ); ?>" alt="Skyy Rose wearing the set that inspired the SkyyRose name" width="724" height="1086" loading="lazy" decoding="async"></div>
	<?php endif; ?>
</section>

<section class="sr2-about-world" aria-labelledby="sr2-about-world-title" data-horizontal-world data-pinned-scroll-world>
	<header class="sr2-section-head sr2-section-head--split"><div><p><?php esc_html_e( 'Chapter 02 · The house moves', 'skyyrose-flagship-2' ); ?></p><h2 id="sr2-about-world-title"><?php esc_html_e( 'One origin. Four distinct worlds.', 'skyyrose-flagship-2' ); ?></h2></div><div class="sr2-rail-controls"><button type="button" data-rail-prev aria-label="<?php esc_attr_e( 'Previous chapter', 'skyyrose-flagship-2' ); ?>">←</button><span data-rail-count>01 / 05</span><button type="button" data-rail-next aria-label="<?php esc_attr_e( 'Next chapter', 'skyyrose-flagship-2' ); ?>">→</button></div></header>
	<div class="sr2-about-world__stage" data-scroll-world-stage><div class="sr2-about-world__rail" tabindex="0" aria-label="<?php esc_attr_e( 'SkyyRose story chapters. Scroll horizontally.', 'skyyrose-flagship-2' ); ?>" data-horizontal-rail>
		<article class="sr2-about-chapter"><img src="<?php echo esc_url( $hero_uri ); ?>" alt="Skyy Rose in the white and rose-gold rose set" width="724" height="1086" loading="lazy" decoding="async"><div><span>01 / Origin</span><h3><?php esc_html_e( 'A name worth building for.', 'skyyrose-flagship-2' ); ?></h3><p><?php esc_html_e( 'A father’s promise gave the house its first direction.', 'skyyrose-flagship-2' ); ?></p></div></article>
		<a class="sr2-about-chapter" data-collection="signature" href="<?php echo esc_url( skyyrose2_collection_url( 'signature' ) ); ?>"><img src="<?php echo esc_url( skyyrose2_scroll_world_asset_uri( 'scene-1-signature.webp' ) ); ?>" alt="Signature collection world with a rose-gold fashion look" width="1920" height="1275" loading="lazy" decoding="async"><div><span>02 / Signature</span><h3><?php esc_html_e( 'The Flagship moves first.', 'skyyrose-flagship-2' ); ?></h3><p><?php esc_html_e( 'Oakland confidence, gold-register craft, and a city-tour world carry the clearest expression of the house forward.', 'skyyrose-flagship-2' ); ?></p><b><?php esc_html_e( 'Enter Signature', 'skyyrose-flagship-2' ); ?></b></div></a>
		<a class="sr2-about-chapter" data-collection="black-rose" href="<?php echo esc_url( skyyrose2_collection_url( 'black-rose' ) ); ?>"><img src="<?php echo esc_url( skyyrose2_scroll_world_asset_uri( 'scene-2-black-rose.webp' ) ); ?>" alt="Black Rose collection world in dark, silver-lit styling" width="1920" height="1275" loading="lazy" decoding="async"><div><span>03 / Black Rose</span><h3><?php esc_html_e( 'Depth, cut in black.', 'skyyrose-flagship-2' ); ?></h3><p><?php esc_html_e( 'Black Rose follows the material, silhouette, and reflection of black; silver stays only as a supporting glint.', 'skyyrose-flagship-2' ); ?></p><b><?php esc_html_e( 'Enter Black Rose', 'skyyrose-flagship-2' ); ?></b></div></a>
		<a class="sr2-about-chapter" data-collection="love-hurts" href="<?php echo esc_url( skyyrose2_collection_url( 'love-hurts' ) ); ?>"><img src="<?php echo esc_url( skyyrose2_scroll_world_asset_uri( 'scene-3-love-hurts.webp' ) ); ?>" alt="Love Hurts collection world with a crimson rose and fashion look" width="1920" height="1275" loading="lazy" decoding="async"><div><span>04 / Love Hurts</span><h3><?php esc_html_e( 'Devotion, transformed.', 'skyyrose-flagship-2' ); ?></h3><p><?php esc_html_e( 'An original SkyyRose world of isolation, earned tenderness, and the self you become after the wound.', 'skyyrose-flagship-2' ); ?></p><b><?php esc_html_e( 'Enter Love Hurts', 'skyyrose-flagship-2' ); ?></b></div></a>
		<a class="sr2-about-chapter" data-collection="kids-capsule" href="<?php echo esc_url( skyyrose2_collection_url( 'kids-capsule' ) ); ?>"><img src="<?php echo esc_url( skyyrose2_scroll_world_asset_uri( 'scene-4-kids-capsule.webp' ) ); ?>" alt="Kids Capsule collection world celebrating the next generation" width="1920" height="1275" loading="lazy" decoding="async"><div><span>05 / Kids Capsule</span><h3><?php esc_html_e( 'The heir to the throne.', 'skyyrose-flagship-2' ); ?></h3><p><?php esc_html_e( 'A protected, playful world where the next generation inherits possibility and room to imagine bigger.', 'skyyrose-flagship-2' ); ?></p><b><?php esc_html_e( 'Enter Kids Capsule', 'skyyrose-flagship-2' ); ?></b></div></a>
	</div><div class="sr2-rail-progress" aria-hidden="true"><span data-rail-progress></span></div></div>
</section>

<section class="sr2-about-closing" aria-labelledby="sr2-about-closing-title"><p class="sr2-eyebrow"><?php esc_html_e( 'The mission', 'skyyrose-flagship-2' ); ?></p><h2 id="sr2-about-closing-title"><?php esc_html_e( 'Luxury grows from concrete.', 'skyyrose-flagship-2' ); ?></h2><p><?php esc_html_e( 'Fashion carries family, culture, and the choice to build a different story.', 'skyyrose-flagship-2' ); ?></p><a class="sr2-button sr2-button--fill" href="<?php echo esc_url( home_url( '/collections/' ) ); ?>"><?php esc_html_e( 'Enter the collections', 'skyyrose-flagship-2' ); ?></a></section>
