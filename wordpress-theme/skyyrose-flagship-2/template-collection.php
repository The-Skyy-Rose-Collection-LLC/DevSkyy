<?php
/**
 * Template Name: SkyyRose Collection 2
 *
 * Shared story-commerce template for every collection world.
 *
 * @package SkyyRoseFlagship2
 */

defined( 'ABSPATH' ) || exit;

$slug        = sanitize_title( (string) get_query_var( 'skyyrose2_collection' ) );
$slug        = $slug ? $slug : sanitize_title( get_post_field( 'post_name', get_queried_object_id() ) );
$collections = skyyrose2_collections();
$collection  = $collections[ $slug ] ?? $collections['signature'];
$shop_url    = function_exists( 'wc_get_page_permalink' ) ? wc_get_page_permalink( 'shop' ) : home_url( '/shop/' );

/*
 * The collection map owns verified imagery and routes; this small dialogue
 * layer restores the founder-authored V1 story beats without changing product
 * truth or duplicating the collection SOT.
 */
$dialogue = array(
	'signature'    => array(
		'kicker'          => __( 'Chapter One / The Beginning', 'skyyrose-flagship-2' ),
		'headline'        => __( 'Not basics. Blueprints.', 'skyyrose-flagship-2' ),
		'line'            => __( 'The first rose, the first script. Oakland-born luxury made permanent.', 'skyyrose-flagship-2' ),
		'manifesto'       => __( 'I drew the first rose on a night I could not afford dinner. Signature is that night made permanent.', 'skyyrose-flagship-2' ),
		'founder_label'   => __( 'The founder remembers', 'skyyrose-flagship-2' ),
		'founder_quote'   => __( "They told me luxury doesn't come from Oakland. I said luxury grows from concrete — and I meant that literally. This collection is the concrete. Everything else grew from here.", 'skyyrose-flagship-2' ),
		'feature_label'   => __( 'The first rose', 'skyyrose-flagship-2' ),
		'feature_copy'    => __( 'Drawn at 4 AM, broke, a baby on the way. The script became the foundation.', 'skyyrose-flagship-2' ),
		'meaning_label'   => __( 'Bedrock', 'skyyrose-flagship-2' ),
		'meaning_copy'    => __( 'Everything else grew from here.', 'skyyrose-flagship-2' ),
		'tagline'         => __( 'The beginning of it all — where it started from.', 'skyyrose-flagship-2' ),
	),
	'black-rose'   => array(
		'kicker'          => __( 'Chapter Two / Beauty Without Permission', 'skyyrose-flagship-2' ),
		'headline'        => __( 'Defining beauty through the color black.', 'skyyrose-flagship-2' ),
		'line'            => __( 'A black rose is a posture. Not a flower — a conviction.', 'skyyrose-flagship-2' ),
		'manifesto'       => __( 'Where I am from, black is not a color — it is armor. Black Rose is that truth made into fabric.', 'skyyrose-flagship-2' ),
		'founder_label'   => __( 'The founder remembers', 'skyyrose-flagship-2' ),
		'founder_quote'   => __( 'You do not wear it to stand out. You wear it because you already stood up.', 'skyyrose-flagship-2' ),
		'feature_label'   => __( 'The posture', 'skyyrose-flagship-2' ),
		'feature_copy'    => __( 'Oakland gravity, silver light, and the beauty that forces through the cracks.', 'skyyrose-flagship-2' ),
		'meaning_label'   => __( 'Armor', 'skyyrose-flagship-2' ),
		'meaning_copy'    => __( 'Black holds depth, power, protection, and elegance.', 'skyyrose-flagship-2' ),
		'tagline'         => __( 'You wear it because you already stood up.', 'skyyrose-flagship-2' ),
	),
	'love-hurts'   => array(
		'kicker'          => __( 'Chapter Three / The Beast Speaks', 'skyyrose-flagship-2' ),
		'headline'        => __( 'They called me Beast. They were right.', 'skyyrose-flagship-2' ),
		'line'            => __( 'Beauty and the Beast from the Beast’s side — protecting what is fragile.', 'skyyrose-flagship-2' ),
		'manifesto'       => __( 'Hurts is not a theme. It is the bloodline that raised me.', 'skyyrose-flagship-2' ),
		'founder_label'   => __( 'The bloodline speaks', 'skyyrose-flagship-2' ),
		'founder_quote'   => __( "My grandmother used to say it plain: 'Love hurts, baby. That's how you know it's real.' She wasn't being poetic. She was teaching survival.", 'skyyrose-flagship-2' ),
		'feature_label'   => __( 'Under glass', 'skyyrose-flagship-2' ),
		'feature_copy'    => __( 'The Beast did not hide from ugliness. He hid because he loved something fragile.', 'skyyrose-flagship-2' ),
		'meaning_label'   => __( 'The bloodline', 'skyyrose-flagship-2' ),
		'meaning_copy'    => __( 'Three generations of Hurts, carried forward in crimson and rose.', 'skyyrose-flagship-2' ),
		'tagline'         => __( 'They called me Beast. They were right.', 'skyyrose-flagship-2' ),
	),
	'kids-capsule' => array(
		'kicker'          => __( 'Chapter Four / The Heir to the Throne', 'skyyrose-flagship-2' ),
		'headline'        => __( 'Luxury runs in the family.', 'skyyrose-flagship-2' ),
		'line'            => __( 'The same craftsmanship, smaller silhouettes. Legacy is worn.', 'skyyrose-flagship-2' ),
		'manifesto'       => __( 'The whole brand is named after her — the daughter who was the reason for all of it.', 'skyyrose-flagship-2' ),
		'founder_label'   => __( 'The founder remembers', 'skyyrose-flagship-2' ),
		'founder_quote'   => __( 'I built SkyyRose so my daughter would never have to wonder if she was enough.', 'skyyrose-flagship-2' ),
		'feature_label'   => __( 'Her name', 'skyyrose-flagship-2' ),
		'feature_copy'    => __( 'No pastels. No cartoons. Premium, dark, elegant — scaled down but never dumbed down.', 'skyyrose-flagship-2' ),
		'meaning_label'   => __( 'Inheritance', 'skyyrose-flagship-2' ),
		'meaning_copy'    => __( 'The fourth chapter passes the torch on the same terms that built the house.', 'skyyrose-flagship-2' ),
		'tagline'         => __( 'Luxury runs in the family.', 'skyyrose-flagship-2' ),
	),
);
$story       = $dialogue[ $slug ] ?? $dialogue['signature'];
$feature     = $collection['world'][0];
$feature_uri = isset( $feature['source'] ) && 'scroll-world' === $feature['source'] ? skyyrose2_scroll_world_asset_uri( $feature['image'] ) : skyyrose2_sot_asset_uri( $feature['image'] );

get_header();
?>
<main id="primary" class="sr2-collection sr2-collection--<?php echo esc_attr( $slug ); ?>" data-collection="<?php echo esc_attr( $slug ); ?>">
	<section class="sr2-collection-hero" aria-labelledby="sr2-collection-title" data-hero-depth>
		<div class="sr2-collection-hero__media"><img src="<?php echo esc_url( skyyrose2_sot_asset_uri( $collection['hero'] ) ); ?>" alt="" width="1280" height="720" fetchpriority="high" decoding="sync"></div>
		<div class="sr2-collection-hero__veil" aria-hidden="true"></div>
		<div class="sr2-collection-hero__copy">
			<p class="sr2-eyebrow"><?php echo esc_html( $story['kicker'] ); ?></p>
			<h1 id="sr2-collection-title" class="screen-reader-text"><?php echo esc_html( $collection['name'] ); ?></h1>
			<img class="sr2-collection-hero__lockup" src="<?php echo esc_url( skyyrose2_sot_asset_uri( $collection['lockup'] ) ); ?>" alt="<?php echo esc_attr( $collection['name'] ); ?>" width="900" height="400">
			<p class="sr2-collection-hero__line"><?php echo esc_html( $story['line'] ); ?></p>
			<div class="sr2-actions"><a class="sr2-button sr2-button--fill" href="<?php echo esc_url( $shop_url ); ?>"><?php esc_html_e( 'Shop pieces', 'skyyrose-flagship-2' ); ?></a><a class="sr2-button" href="#world"><?php esc_html_e( 'Enter the world', 'skyyrose-flagship-2' ); ?></a></div>
		</div>
		<p class="sr2-collection-hero__chapter" aria-hidden="true">WORLD / <?php echo esc_html( strtoupper( str_replace( '-', ' ', $slug ) ) ); ?></p>
		</section>

		<section class="sr2-collection-feature sr2-image-reveal" aria-labelledby="sr2-feature-title">
			<div class="sr2-collection-feature__media"><img src="<?php echo esc_url( $feature_uri ); ?>" alt="" width="1920" height="1080" loading="lazy" decoding="async"></div>
			<div class="sr2-collection-feature__copy"><p class="sr2-eyebrow"><?php esc_html_e( 'Film spine / 01', 'skyyrose-flagship-2' ); ?></p><h2 id="sr2-feature-title"><?php echo esc_html( $story['feature_label'] ); ?></h2><p><?php echo esc_html( $story['feature_copy'] ); ?></p><a class="sr2-text-link" href="#shop"><?php esc_html_e( 'Find the pieces', 'skyyrose-flagship-2' ); ?> <span aria-hidden="true">↗</span></a></div>
		</section>

		<blockquote class="sr2-collection-pullquote"><p><?php echo esc_html( $story['founder_quote'] ); ?></p><cite><?php echo esc_html( $story['founder_label'] ); ?> / <?php echo esc_html( $collection['name'] ); ?></cite></blockquote>

		<section class="sr2-collection-intro">
			<p><?php echo esc_html( $story['kicker'] ); ?></p>
			<h2><?php echo esc_html( $story['headline'] ); ?></h2>
			<span><?php echo esc_html( $story['manifesto'] ); ?></span>
		</section>

		<section class="sr2-collection-meaning" aria-labelledby="sr2-meaning-title">
			<div><p class="sr2-eyebrow"><?php esc_html_e( 'Film spine / 02', 'skyyrose-flagship-2' ); ?></p><h2 id="sr2-meaning-title"><?php echo esc_html( $story['meaning_label'] ); ?></h2></div><p><?php echo esc_html( $story['meaning_copy'] ); ?></p><img src="<?php echo esc_url( skyyrose2_sot_asset_uri( $collection['atmosphere'] ) ); ?>" alt="" width="600" height="600" loading="lazy" decoding="async">
		</section>

		<section id="shop" class="sr2-section sr2-section--products sr2-collection-product-rail" aria-labelledby="sr2-products-title">
			<header class="sr2-section-head sr2-section-head--split"><div><p><?php echo esc_html( $collection['name'] ); ?> · <?php esc_html_e( 'Edition', 'skyyrose-flagship-2' ); ?></p><h2 id="sr2-products-title"><?php esc_html_e( 'Wear the story.', 'skyyrose-flagship-2' ); ?></h2></div><span class="sr2-section-index">03 / PIECES</span></header>
			<?php skyyrose2_product_cards( 12, $slug ); ?>
		</section>

		<section id="world" class="sr2-world-story" aria-labelledby="sr2-world-story-title" data-story-world data-horizontal-world>
			<header class="sr2-section-head sr2-section-head--split"><div><p><?php esc_html_e( 'Immersive Shopping', 'skyyrose-flagship-2' ); ?></p><h2 id="sr2-world-story-title"><?php esc_html_e( 'Move through the collection.', 'skyyrose-flagship-2' ); ?></h2></div><div class="sr2-rail-controls"><button type="button" data-rail-prev aria-label="<?php esc_attr_e( 'Previous scene', 'skyyrose-flagship-2' ); ?>">←</button><span data-rail-count>01 / <?php echo esc_html( str_pad( (string) count( $collection['world'] ), 2, '0', STR_PAD_LEFT ) ); ?></span><button type="button" data-rail-next aria-label="<?php esc_attr_e( 'Next scene', 'skyyrose-flagship-2' ); ?>">→</button></div></header>
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
			<h2 id="sr2-manifesto-title"><?php echo esc_html( $story['headline'] ); ?></h2>
			<img class="sr2-manifesto__mark" src="<?php echo esc_url( skyyrose2_sot_asset_uri( $collection['atmosphere'] ) ); ?>" alt="" width="600" height="600" loading="lazy" decoding="async">
		</div>
		<div class="sr2-manifesto__scroll">
				<article><span>01</span><h3><?php esc_html_e( 'The meaning', 'skyyrose-flagship-2' ); ?></h3><p><?php echo esc_html( $story['manifesto'] ); ?></p></article>
			<figure class="sr2-image-reveal"><img src="<?php echo esc_url( skyyrose2_sot_asset_uri( $collection['lookbook'] ) ); ?>" alt="<?php echo esc_attr( $collection['name'] . ' lookbook' ); ?>" width="480" height="600" loading="lazy" decoding="async"><figcaption><?php echo esc_html( $collection['name'] ); ?> / LOOK 01</figcaption></figure>
			<article><span>02</span><h3><?php esc_html_e( 'The invitation', 'skyyrose-flagship-2' ); ?></h3><p><?php esc_html_e( 'Choose a piece that says what words cannot. Carry this world into yours.', 'skyyrose-flagship-2' ); ?></p><a class="sr2-button sr2-button--fill" href="#shop"><?php esc_html_e( 'Choose your piece', 'skyyrose-flagship-2' ); ?></a></article>
		</div>
	</section>

	<nav class="sr2-crossnav" aria-label="<?php esc_attr_e( 'Explore other collections', 'skyyrose-flagship-2' ); ?>">
		<p class="sr2-eyebrow"><?php esc_html_e( 'Continue Through the House', 'skyyrose-flagship-2' ); ?></p>
		<?php foreach ( $collections as $nav_slug => $nav_collection ) : ?>
			<?php if ( $nav_slug !== $slug ) : ?>
				<a data-collection="<?php echo esc_attr( $nav_slug ); ?>" href="<?php echo esc_url( skyyrose2_collection_url( $nav_slug ) ); ?>"><span><?php echo esc_html( $nav_collection['name'] ); ?></span><em><?php echo esc_html( $dialogue[ $nav_slug ]['tagline'] ?? $nav_collection['kicker'] ); ?></em><b aria-hidden="true">↗</b></a>
			<?php endif; ?>
		<?php endforeach; ?>
	</nav>
</main>
<?php
get_footer();
