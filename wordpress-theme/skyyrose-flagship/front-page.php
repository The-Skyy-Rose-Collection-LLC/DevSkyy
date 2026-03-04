<?php
/**
 * Template Name: Homepage
 *
 * Homepage V2 — Elite Web Builder cinematic design.
 * 12 sections: loader, nav, hero, press strip, marquee, story,
 * quote, collection cards, lookbook, craft, newsletter, footer.
 *
 * @package SkyyRose_Flagship
 * @since   4.1.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

get_header();

// ------------------------------------------------------------------
// Collection data — used for collection cards + lookbook.
// ------------------------------------------------------------------
$skyyrose_collections = array(
	'black-rose' => array(
		'key'     => 'br',
		'name'    => 'Black Rose',
		'number'  => '01',
		'tagline' => 'For those who found power in the dark.',
		'meta_tag' => 'Limited',
		'img'     => 'homepage-col-black-rose.webp',
		'link'    => home_url( '/collection-black-rose/' ),
	),
	'love-hurts' => array(
		'key'     => 'lh',
		'name'    => 'Love Hurts',
		'tagline' => 'Wear your heart. Own your scars.',
		'meta_tag' => 'Family Legacy',
		'number'  => '02',
		'img'     => 'homepage-col-love-hurts.webp',
		'link'    => home_url( '/collection-love-hurts/' ),
	),
	'signature' => array(
		'key'     => 'sg',
		'name'    => 'Signature',
		'tagline' => 'The foundation of any wardrobe worth building.',
		'meta_tag' => 'Everyday Luxury',
		'number'  => '03',
		'img'     => 'homepage-col-signature.webp',
		'link'    => home_url( '/collection-signature/' ),
	),
);

// Query WooCommerce for product counts and price ranges per collection.
foreach ( $skyyrose_collections as $slug => &$col_data ) {
	$col_data['product_count'] = 0;
	$col_data['price_range']   = '';

	if ( function_exists( 'wc_get_products' ) ) {
		$results = wc_get_products( array(
			'category' => array( $slug ),
			'status'   => 'publish',
			'limit'    => -1,
			'return'   => 'ids',
			'paginate' => true,
		) );

		if ( is_object( $results ) && isset( $results->total ) ) {
			$col_data['product_count'] = $results->total;
		}

		// Get price range.
		$products_for_price = wc_get_products( array(
			'category' => array( $slug ),
			'status'   => 'publish',
			'limit'    => -1,
		) );

		if ( ! empty( $products_for_price ) ) {
			$prices = array_filter( array_map( function ( $p ) {
				return (float) $p->get_price();
			}, $products_for_price ) );

			if ( ! empty( $prices ) ) {
				$col_data['price_range'] = '$' . number_format( min( $prices ) ) . ' &mdash; $' . number_format( max( $prices ) );
			}
		}
	}

	// Fallback product counts if WooCommerce isn't active.
	if ( 0 === $col_data['product_count'] ) {
		$fallbacks = array( 'black-rose' => 4, 'love-hurts' => 4, 'signature' => 5 );
		$col_data['product_count'] = isset( $fallbacks[ $slug ] ) ? $fallbacks[ $slug ] : 0;
	}
}
unset( $col_data ); // Break reference.

// Total product count for story stats.
$skyyrose_total_products = 0;
if ( function_exists( 'wc_get_products' ) ) {
	$all_results = wc_get_products( array(
		'status'   => 'publish',
		'limit'    => -1,
		'return'   => 'ids',
		'paginate' => true,
	) );
	if ( is_object( $all_results ) && isset( $all_results->total ) ) {
		$skyyrose_total_products = $all_results->total;
	}
}
if ( 0 === $skyyrose_total_products ) {
	$skyyrose_total_products = 13;
}

$assets_uri = SKYYROSE_ASSETS_URI;
?>

<div class="grain" aria-hidden="true"></div>
<div class="vignette" aria-hidden="true"></div>

<!-- Scroll progress indicator -->
<div class="scroll-progress" aria-hidden="true"></div>

<!-- ═══ LOADER ═══ -->
<div id="loader" role="status" aria-label="<?php esc_attr_e( 'Loading', 'skyyrose-flagship' ); ?>">
	<span class="ld-brand"><?php echo esc_html( 'SkyyRose' ); ?></span>
	<span class="ld-tag"><?php echo esc_html( 'Luxury Grows from Concrete' ); ?></span>
	<div class="ld-bar"><div class="ld-fill" id="ldFill"></div></div>
</div>

<!-- ═══ MOBILE MENU ═══ -->
<div class="mob-menu" id="mobMenu" role="dialog" aria-label="<?php esc_attr_e( 'Mobile Navigation', 'skyyrose-flagship' ); ?>">
	<span class="mob-close" role="button" aria-label="<?php esc_attr_e( 'Close menu', 'skyyrose-flagship' ); ?>" tabindex="0">&times;</span>
	<a href="#story"><?php esc_html_e( 'Our Story', 'skyyrose-flagship' ); ?></a>
	<a href="#collections"><?php esc_html_e( 'Collections', 'skyyrose-flagship' ); ?></a>
	<a href="#lookbook"><?php esc_html_e( 'Lookbook', 'skyyrose-flagship' ); ?></a>
	<a href="#craft"><?php esc_html_e( 'Craft', 'skyyrose-flagship' ); ?></a>
	<a href="#community"><?php esc_html_e( 'Community', 'skyyrose-flagship' ); ?></a>
	<?php if ( function_exists( 'wc_get_cart_url' ) ) : ?>
		<a href="<?php echo esc_url( wc_get_cart_url() ); ?>"><?php esc_html_e( 'Bag', 'skyyrose-flagship' ); ?></a>
	<?php endif; ?>
</div>

<!-- ═══ NAV ═══ -->
<nav class="nav" id="mainNav" aria-label="<?php esc_attr_e( 'Homepage Navigation', 'skyyrose-flagship' ); ?>">
	<a href="<?php echo esc_url( home_url( '/' ) ); ?>" class="nav-brand">
		<span class="nav-name"><?php echo esc_html( 'SkyyRose' ); ?></span>
		<span class="nav-sub"><?php echo esc_html( 'Oakland Luxury' ); ?></span>
	</a>
	<div class="nav-center">
		<a href="#story" class="nav-link"><?php esc_html_e( 'Story', 'skyyrose-flagship' ); ?></a>
		<a href="#collections" class="nav-link"><?php esc_html_e( 'Collections', 'skyyrose-flagship' ); ?></a>
		<a href="#lookbook" class="nav-link"><?php esc_html_e( 'Lookbook', 'skyyrose-flagship' ); ?></a>
		<a href="#craft" class="nav-link"><?php esc_html_e( 'Craft', 'skyyrose-flagship' ); ?></a>
		<a href="#community" class="nav-link"><?php esc_html_e( 'Community', 'skyyrose-flagship' ); ?></a>
	</div>
	<div class="nav-right">
		<button class="nav-bag" type="button" aria-label="<?php esc_attr_e( 'Shopping Bag', 'skyyrose-flagship' ); ?>">
			<?php esc_html_e( 'Bag', 'skyyrose-flagship' ); ?>
			<span class="bag-ct" id="bagCt">0</span>
		</button>
		<div class="nav-ham" role="button" aria-label="<?php esc_attr_e( 'Open menu', 'skyyrose-flagship' ); ?>" tabindex="0">
			<span></span><span></span><span></span>
		</div>
	</div>
</nav>

<!-- ═══ HERO ═══ -->
<section class="hero" id="hero" aria-label="<?php esc_attr_e( 'SkyyRose Hero', 'skyyrose-flagship' ); ?>">
	<div class="hero-bg" style="background-image: url('<?php echo esc_url( $assets_uri . '/images/homepage-hero-bg.webp' ); ?>');" aria-hidden="true"></div>
	<div class="hero-ov" aria-hidden="true"></div>
	<div class="hero-particles" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i></div>
	<div class="hero-frame" aria-hidden="true"></div>
	<div class="hero-content">
		<p class="hero-eyebrow"><?php echo esc_html( 'Oakland · Est. 2020 · Gender Neutral' ); ?></p>
		<h1 class="hero-title"><?php echo esc_html( 'SkyyRose' ); ?></h1>
		<div class="hero-rule" aria-hidden="true"></div>
		<p class="hero-subtitle"><?php echo esc_html( 'Luxury Grows from Concrete. Three collections, one vision — built by a father, named after a daughter.' ); ?></p>
		<div class="hero-ctas">
			<a href="#collections" class="hero-cta hero-cta-primary"><?php esc_html_e( 'Explore Collections', 'skyyrose-flagship' ); ?></a>
			<a href="#story" class="hero-cta"><?php esc_html_e( 'Our Story', 'skyyrose-flagship' ); ?></a>
		</div>
	</div>
	<div class="hero-scroll" aria-hidden="true">
		<span><?php esc_html_e( 'Scroll', 'skyyrose-flagship' ); ?></span>
		<div class="hero-scroll-line"></div>
	</div>
</section>

<!-- ═══ PRESS STRIP ═══ -->
<div class="press rv">
	<p class="press-label"><?php esc_html_e( 'As Featured In', 'skyyrose-flagship' ); ?></p>
	<div class="press-logos">
		<?php
		$press_outlets = array( 'Maxim', 'CEO Weekly', 'San Francisco Post', 'Best of Best Review', 'The Blox' );
		$press_count   = count( $press_outlets );
		foreach ( $press_outlets as $i => $outlet ) :
			?>
			<span class="press-item"><?php echo esc_html( $outlet ); ?></span>
			<?php if ( $i < $press_count - 1 ) : ?>
				<span class="press-sep" aria-hidden="true"></span>
			<?php endif; ?>
		<?php endforeach; ?>
	</div>
</div>

<!-- ═══ MARQUEE ═══ -->
<div class="marquee" aria-hidden="true">
	<div class="marquee-track">
		<?php
		$marquee_items = array( 'Black Rose', 'Love Hurts', 'Signature', 'Oakland Made', 'Gender Neutral', 'Limited Edition', 'Luxury Streetwear', 'Built Different' );
		// Duplicate for seamless loop.
		for ( $i = 0; $i < 2; $i++ ) {
			foreach ( $marquee_items as $item ) {
				echo '<span class="mq-item">' . esc_html( $item ) . '<span class="mq-dot"></span></span>';
			}
		}
		?>
	</div>
</div>

<?php
get_template_part( 'template-parts/front-page/section', 'story-v2', array(
	'assets_uri'     => $assets_uri,
	'total_products' => $skyyrose_total_products,
) );
?>

<!-- ═══ QUOTE ═══ -->
<section class="quote-section" aria-label="<?php esc_attr_e( 'Founder Quote', 'skyyrose-flagship' ); ?>">
	<div class="quote-mark rv" aria-hidden="true">&ldquo;</div>
	<blockquote class="quote-text rv rv-d1">
		<?php echo wp_kses_post( '&ldquo;If you asked me four years ago, I never would have thought I&rsquo;d be here. I had no drive, lost it all, a baby on the way, and was broke. But we knew we had to get it <em>by any means necessary</em>.&rdquo;' ); ?>
	</blockquote>
	<p class="quote-attr rv rv-d2"><?php echo wp_kses_post( '&mdash; Corey Foster, Founder &amp; CEO' ); ?></p>
</section>

<?php
get_template_part( 'template-parts/front-page/section', 'collections-v2', array(
	'collections' => $skyyrose_collections,
	'assets_uri'  => $assets_uri,
) );
?>

<?php
get_template_part( 'template-parts/front-page/section', 'lookbook-v2', array(
	'assets_uri' => $assets_uri,
) );

get_template_part( 'template-parts/front-page/section', 'craft-v2' );

get_template_part( 'template-parts/front-page/section', 'newsletter-v2' );
?>

<!-- ═══ FOOTER ═══ -->
<footer class="ft" aria-label="<?php esc_attr_e( 'Site Footer', 'skyyrose-flagship' ); ?>">
	<div class="ft-inner">
		<div>
			<div class="ft-brand-name rv"><?php echo esc_html( 'SkyyRose' ); ?></div>
			<p class="ft-desc rv rv-d1"><?php echo esc_html( 'Where Bay Area authenticity meets high-fashion aesthetics. Gender-neutral, sustainably crafted, limited edition designs. Built by a father, named after a daughter.' ); ?></p>
			<div class="ft-awards rv rv-d2">
				<span class="ft-award"><?php echo wp_kses_post( 'Maxim&rsquo;s 14 Game-Changing Entrepreneurs 2023' ); ?></span>
				<span class="ft-award"><?php echo esc_html( 'Best Bay Area Clothing Line 2024' ); ?></span>
				<span class="ft-award"><?php echo wp_kses_post( 'Featured &mdash; San Francisco Post, CEO Weekly' ); ?></span>
			</div>
		</div>
		<div>
			<div class="ft-col-title rv"><?php esc_html_e( 'Collections', 'skyyrose-flagship' ); ?></div>
			<ul class="ft-links rv rv-d1">
				<li><a href="<?php echo esc_url( home_url( '/collection-black-rose/' ) ); ?>"><?php esc_html_e( 'Black Rose', 'skyyrose-flagship' ); ?></a></li>
				<li><a href="<?php echo esc_url( home_url( '/collection-love-hurts/' ) ); ?>"><?php esc_html_e( 'Love Hurts', 'skyyrose-flagship' ); ?></a></li>
				<li><a href="<?php echo esc_url( home_url( '/collection-signature/' ) ); ?>"><?php esc_html_e( 'Signature', 'skyyrose-flagship' ); ?></a></li>
			</ul>
		</div>
		<div>
			<div class="ft-col-title rv"><?php esc_html_e( 'Brand', 'skyyrose-flagship' ); ?></div>
			<ul class="ft-links rv rv-d1">
				<li><a href="<?php echo esc_url( home_url( '/about/' ) ); ?>"><?php esc_html_e( 'Our Story', 'skyyrose-flagship' ); ?></a></li>
				<li><a href="#lookbook"><?php esc_html_e( 'Lookbook', 'skyyrose-flagship' ); ?></a></li>
				<li><a href="<?php echo esc_url( home_url( '/about/' ) ); ?>#press"><?php esc_html_e( 'Press', 'skyyrose-flagship' ); ?></a></li>
				<li><a href="<?php echo esc_url( home_url( '/about/' ) ); ?>"><?php esc_html_e( 'About', 'skyyrose-flagship' ); ?></a></li>
			</ul>
		</div>
		<div>
			<div class="ft-col-title rv"><?php esc_html_e( 'Support', 'skyyrose-flagship' ); ?></div>
			<ul class="ft-links rv rv-d1">
				<li><a href="<?php echo esc_url( home_url( '/size-guide/' ) ); ?>"><?php esc_html_e( 'Size Guide', 'skyyrose-flagship' ); ?></a></li>
				<li><a href="<?php echo esc_url( home_url( '/shipping-returns/' ) ); ?>"><?php esc_html_e( 'Shipping & Returns', 'skyyrose-flagship' ); ?></a></li>
				<li><a href="mailto:<?php echo esc_attr( antispambot( 'info@skyyrose.co' ) ); ?>"><?php esc_html_e( 'Contact', 'skyyrose-flagship' ); ?></a></li>
				<li><a href="<?php echo esc_url( home_url( '/faq/' ) ); ?>"><?php esc_html_e( 'FAQ', 'skyyrose-flagship' ); ?></a></li>
			</ul>
		</div>
	</div>
	<div class="ft-bottom">
		<span class="ft-copy">&copy; <?php echo esc_html( gmdate( 'Y' ) ); ?> <?php echo esc_html( 'SkyyRose LLC. All rights reserved.' ); ?></span>
		<div class="ft-social">
			<a href="https://instagram.com/skyyroseco" target="_blank" rel="noopener noreferrer"><?php esc_html_e( 'Instagram', 'skyyrose-flagship' ); ?></a>
			<a href="https://tiktok.com/@skyyroseco" target="_blank" rel="noopener noreferrer"><?php esc_html_e( 'TikTok', 'skyyrose-flagship' ); ?></a>
			<a href="https://x.com/skyyroseco" target="_blank" rel="noopener noreferrer"><?php esc_html_e( 'X', 'skyyrose-flagship' ); ?></a>
		</div>
		<span class="ft-oakland"><?php echo esc_html( 'Made in Oakland' ); ?></span>
	</div>
</footer>

<?php
// JSON-LD Organization structured data.
$organization_schema = array(
	'@context'    => 'https://schema.org',
	'@type'       => 'Organization',
	'name'        => 'SkyyRose',
	'url'         => home_url( '/' ),
	'logo'        => $assets_uri . '/branding/skyyrose-monogram.webp',
	'description' => 'Oakland luxury streetwear. Gender-neutral, limited edition designs. Built by a father, named after a daughter.',
	'foundingDate' => '2020',
	'founder'     => array(
		'@type' => 'Person',
		'name'  => 'Corey Foster',
	),
	'address'     => array(
		'@type'           => 'PostalAddress',
		'addressLocality' => 'Oakland',
		'addressRegion'   => 'CA',
		'addressCountry'  => 'US',
	),
	'sameAs'      => array(
		'https://instagram.com/skyyroseco',
	),
);
?>
<script type="application/ld+json"><?php echo wp_json_encode( $organization_schema, JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT ); ?></script>

<!-- Back-to-top button -->
<button class="back-to-top" aria-label="<?php esc_attr_e( 'Back to top', 'skyyrose-flagship' ); ?>">
	<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4l-8 8h5v8h6v-8h5z"/></svg>
</button>

<?php get_footer(); ?>
