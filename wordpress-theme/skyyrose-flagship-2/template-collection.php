<?php
/**
 * Template Name: SkyyRose Collection 2
 *
 * Shared story-commerce template for every collection world.
 *
 * @package SkyyRoseFlagship2
 */

defined( 'ABSPATH' ) || exit;

$slug        = sanitize_title( get_post_field( 'post_name', get_queried_object_id() ) );
$collections = skyyrose2_collections();
$collection  = $collections[ $slug ] ?? $collections['signature'];
$shop_url    = '#shop';

get_header();
?>
<main id="primary" class="sr2-collection" data-collection="<?php echo esc_attr( $slug ); ?>">
	<section class="sr2-collection-hero" aria-labelledby="sr2-collection-title" data-hero-depth>
		<div class="sr2-collection-hero__media"><img src="<?php echo esc_url( skyyrose2_sot_asset_uri( $collection['hero'] ) ); ?>" alt="" width="1280" height="720" fetchpriority="high" decoding="sync"></div>
		<div class="sr2-collection-hero__veil" aria-hidden="true"></div>
		<div class="sr2-collection-hero__copy">
			<p class="sr2-eyebrow"><?php echo esc_html( $collection['kicker'] ); ?></p>
			<h1 id="sr2-collection-title" class="screen-reader-text"><?php echo esc_html( $collection['name'] ); ?></h1>
			<img class="sr2-collection-hero__lockup" src="<?php echo esc_url( skyyrose2_sot_asset_uri( $collection['lockup'] ) ); ?>" alt="<?php echo esc_attr( $collection['name'] ); ?>" width="900" height="400">
			<p class="sr2-collection-hero__line"><?php echo esc_html( $collection['line'] ); ?></p>
			<div class="sr2-actions"><a class="sr2-button sr2-button--fill" href="<?php echo esc_url( $shop_url ); ?>"><?php esc_html_e( 'Shop pieces', 'skyyrose-flagship-2' ); ?></a><a class="sr2-button" href="#world"><?php esc_html_e( 'Enter the world', 'skyyrose-flagship-2' ); ?></a></div>
		</div>
		<p class="sr2-collection-hero__chapter" aria-hidden="true">WORLD / <?php echo esc_html( strtoupper( str_replace( '-', ' ', $slug ) ) ); ?></p>
	</section>

	<section class="sr2-collection-intro">
		<p><?php echo esc_html( $collection['kicker'] ); ?></p>
		<h2><?php echo esc_html( $collection['headline'] ); ?></h2>
		<span><?php echo esc_html( $collection['manifesto'] ); ?></span>
	</section>

	<section id="shop" class="sr2-section sr2-section--products">
		<header class="sr2-section-head sr2-section-head--split"><div><p><?php echo esc_html( $collection['name'] ); ?> · <?php esc_html_e( 'Edition', 'skyyrose-flagship-2' ); ?></p><h2><?php esc_html_e( 'Wear the story.', 'skyyrose-flagship-2' ); ?></h2></div><span class="sr2-section-index">01 / SHOP</span></header>
		<?php skyyrose2_product_cards( 12, $slug ); ?>
	</section>

	<section id="world" class="sr2-world-story" aria-labelledby="sr2-world-story-title" data-story-world>
		<header class="sr2-section-head sr2-section-head--split"><div><p><?php esc_html_e( 'Immersive Shopping', 'skyyrose-flagship-2' ); ?></p><h2 id="sr2-world-story-title"><?php esc_html_e( 'Move through the collection.', 'skyyrose-flagship-2' ); ?></h2></div><span class="sr2-section-index">02 / WORLD</span></header>
		<div class="sr2-world-story__rail" tabindex="0" aria-label="<?php echo esc_attr( sprintf( __( '%s collection scenes', 'skyyrose-flagship-2' ), $collection['name'] ) ); ?>" data-horizontal-rail>
			<?php foreach ( $collection['world'] as $index => $scene ) : ?>
				<?php $scene_uri = isset( $scene['source'] ) && 'scroll-world' === $scene['source'] ? skyyrose2_scroll_world_asset_uri( $scene['image'] ) : skyyrose2_sot_asset_uri( $scene['image'] ); ?>
				<article class="sr2-world-chapter">
					<div class="sr2-world-chapter__media sr2-image-reveal"><img src="<?php echo esc_url( $scene_uri ); ?>" alt="" width="1920" height="1080" loading="lazy" decoding="async"></div>
					<div class="sr2-world-chapter__copy"><span><?php echo esc_html( sprintf( '%02d', $index + 1 ) ); ?></span><h3><?php echo esc_html( $scene['label'] ); ?></h3><p><?php echo esc_html( $scene['copy'] ); ?></p><a href="#shop"><?php esc_html_e( 'Shop this world', 'skyyrose-flagship-2' ); ?> ↗</a></div>
				</article>
			<?php endforeach; ?>
		</div>
		<div class="sr2-world-story__progress" aria-hidden="true"><span></span></div>
	</section>

	<section class="sr2-manifesto" aria-labelledby="sr2-manifesto-title">
		<div class="sr2-manifesto__sticky">
			<p class="sr2-eyebrow"><?php esc_html_e( 'Collection Code', 'skyyrose-flagship-2' ); ?></p>
			<h2 id="sr2-manifesto-title"><?php echo esc_html( $collection['headline'] ); ?></h2>
			<img class="sr2-manifesto__mark" src="<?php echo esc_url( skyyrose2_sot_asset_uri( $collection['atmosphere'] ) ); ?>" alt="" width="600" height="600" loading="lazy" decoding="async">
		</div>
		<div class="sr2-manifesto__scroll">
			<article><span>01</span><h3><?php esc_html_e( 'The meaning', 'skyyrose-flagship-2' ); ?></h3><p><?php echo esc_html( $collection['manifesto'] ); ?></p></article>
			<figure class="sr2-image-reveal"><img src="<?php echo esc_url( skyyrose2_sot_asset_uri( $collection['lookbook'] ) ); ?>" alt="<?php echo esc_attr( $collection['name'] . ' lookbook' ); ?>" width="480" height="600" loading="lazy" decoding="async"><figcaption><?php echo esc_html( $collection['name'] ); ?> / LOOK 01</figcaption></figure>
			<article><span>02</span><h3><?php esc_html_e( 'The invitation', 'skyyrose-flagship-2' ); ?></h3><p><?php esc_html_e( 'Choose a piece that says what words cannot. Carry this world into yours.', 'skyyrose-flagship-2' ); ?></p><a class="sr2-button sr2-button--fill" href="#shop"><?php esc_html_e( 'Choose your piece', 'skyyrose-flagship-2' ); ?></a></article>
		</div>
	</section>

	<nav class="sr2-crossnav" aria-label="<?php esc_attr_e( 'Explore other collections', 'skyyrose-flagship-2' ); ?>">
		<p class="sr2-eyebrow"><?php esc_html_e( 'Continue Through the House', 'skyyrose-flagship-2' ); ?></p>
		<?php foreach ( $collections as $nav_slug => $nav_collection ) : ?>
			<?php if ( $nav_slug !== $slug ) : ?>
				<a data-collection="<?php echo esc_attr( $nav_slug ); ?>" href="<?php echo esc_url( skyyrose2_collection_url( $nav_slug ) ); ?>"><span><?php echo esc_html( $nav_collection['name'] ); ?></span><em><?php echo esc_html( $nav_collection['kicker'] ); ?></em><b aria-hidden="true">↗</b></a>
			<?php endif; ?>
		<?php endforeach; ?>
	</nav>
</main>
<?php
get_footer();
