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

<!-- ═══ STORY ═══ -->
<section class="story" id="story" aria-label="<?php esc_attr_e( 'Our Story', 'skyyrose-flagship' ); ?>">
	<div class="story-bg" aria-hidden="true"></div>
	<div class="story-inner">
		<div>
			<p class="story-eyebrow rv"><?php esc_html_e( 'The Origin', 'skyyrose-flagship' ); ?></p>
			<h2 class="story-heading rv rv-d1">
				<?php echo esc_html( 'Born In' ); ?><br><?php echo esc_html( 'The Town' ); ?>
				<em><?php echo esc_html( 'A father\'s promise. A daughter\'s name.' ); ?></em>
			</h2>
			<div class="story-body rv rv-d2">
				<p><?php echo wp_kses_post( 'In a neighborhood where opportunities are as scarce as support, <strong>Corey Foster</strong> refused to become another statistic. He&rsquo;d lost everything &mdash; broke, no drive left, a baby on the way.' ); ?></p>
				<p><?php echo wp_kses_post( 'Through failed websites, scammer manufacturers, and single parenthood with no support &mdash; he built something real. Named after his daughter <strong>Skyy Rose</strong>. Designed for anyone, regardless of gender or age.' ); ?></p>
				<p><?php echo wp_kses_post( 'SkyyRose isn&rsquo;t just clothing. It&rsquo;s proof that your circumstances don&rsquo;t define your destination.' ); ?></p>
			</div>
			<div class="story-stats rv rv-d3">
				<div>
					<div class="stat-num">3</div>
					<div class="stat-label"><?php esc_html_e( 'Collections', 'skyyrose-flagship' ); ?></div>
				</div>
				<div>
					<div class="stat-num"><?php echo esc_html( $skyyrose_total_products ); ?></div>
					<div class="stat-label"><?php esc_html_e( 'Pieces', 'skyyrose-flagship' ); ?></div>
				</div>
				<div>
					<div class="stat-num">2020</div>
					<div class="stat-label"><?php esc_html_e( 'Founded', 'skyyrose-flagship' ); ?></div>
				</div>
				<div>
					<div class="stat-num">5+</div>
					<div class="stat-label"><?php esc_html_e( 'Press Features', 'skyyrose-flagship' ); ?></div>
				</div>
			</div>
		</div>
		<div class="story-img-wrap rv-right">
			<div class="story-img">
				<img
					src="<?php echo esc_url( $assets_uri . '/images/homepage-story-founder.webp' ); ?>"
					alt="<?php esc_attr_e( 'Corey Foster, SkyyRose founder', 'skyyrose-flagship' ); ?>"
					loading="lazy"
					decoding="async"
					width="600"
					height="800"
				/>
			</div>
			<div class="story-float">
				<div class="sf-lbl"><?php esc_html_e( 'Recognition', 'skyyrose-flagship' ); ?></div>
				<div class="sf-val"><?php echo wp_kses_post( 'Best Bay Area<br>Clothing Line 2024' ); ?></div>
			</div>
		</div>
	</div>
</section>

<!-- ═══ QUOTE ═══ -->
<section class="quote-section" aria-label="<?php esc_attr_e( 'Founder Quote', 'skyyrose-flagship' ); ?>">
	<div class="quote-mark rv" aria-hidden="true">&ldquo;</div>
	<blockquote class="quote-text rv rv-d1">
		<?php echo wp_kses_post( '&ldquo;If you asked me four years ago, I never would have thought I&rsquo;d be here. I had no drive, lost it all, a baby on the way, and was broke. But we knew we had to get it <em>by any means necessary</em>.&rdquo;' ); ?>
	</blockquote>
	<p class="quote-attr rv rv-d2"><?php echo wp_kses_post( '&mdash; Corey Foster, Founder &amp; CEO' ); ?></p>
</section>

<!-- ═══ COLLECTIONS ═══ -->
<section class="collections" id="collections" aria-label="<?php esc_attr_e( 'Our Collections', 'skyyrose-flagship' ); ?>">
	<div class="col-header rv">
		<p class="col-header-eyebrow"><?php esc_html_e( 'The Collections', 'skyyrose-flagship' ); ?></p>
		<h2 class="col-header-title"><?php echo esc_html( 'Three Worlds. One Vision.' ); ?></h2>
	</div>
	<div class="col-grid">
		<?php
		$delay = 1;
		foreach ( $skyyrose_collections as $slug => $col ) :
			$key         = $col['key'];
			$delay_class = 'rv-d' . min( $delay, 3 );
			?>
			<a href="<?php echo esc_url( $col['link'] ); ?>" class="col-card <?php echo esc_attr( $key ); ?> rv <?php echo esc_attr( $delay_class ); ?>">
				<div class="col-card-img">
					<img
						src="<?php echo esc_url( $assets_uri . '/images/' . $col['img'] ); ?>"
						alt="<?php echo esc_attr( $col['name'] . ' Collection' ); ?>"
						loading="lazy"
						decoding="async"
						width="480"
						height="640"
					/>
				</div>
				<div class="col-card-ov"></div>
				<div class="col-card-content">
					<p class="col-card-num"><?php echo esc_html( 'Collection ' . $col['number'] ); ?></p>
					<h3 class="col-card-name">
						<?php
						$name_parts = explode( ' ', $col['name'] );
						echo esc_html( $name_parts[0] );
						if ( isset( $name_parts[1] ) ) {
							echo '<br>' . esc_html( $name_parts[1] );
						}
						?>
					</h3>
					<p class="col-card-tag"><?php echo esc_html( $col['tagline'] ); ?></p>
					<div class="col-card-meta">
						<span><?php echo esc_html( $col['product_count'] . ' Pieces' ); ?></span>
						<?php if ( ! empty( $col['price_range'] ) ) : ?>
							<span><?php echo wp_kses_post( $col['price_range'] ); ?></span>
						<?php endif; ?>
						<span><?php echo esc_html( $col['meta_tag'] ); ?></span>
					</div>
					<span class="col-card-cta"><?php esc_html_e( 'Explore Collection', 'skyyrose-flagship' ); ?></span>
				</div>
			</a>
			<?php
			$delay++;
		endforeach;
		?>
	</div>
</section>

<!-- ═══ LOOKBOOK ═══ -->
<section class="lookbook" id="lookbook" aria-label="<?php esc_attr_e( 'Lookbook', 'skyyrose-flagship' ); ?>">
	<div class="lookbook-header rv">
		<h2><?php echo esc_html( 'Lookbook' ); ?></h2>
		<p><?php echo esc_html( 'Real people. Real style. Oakland made.' ); ?></p>
	</div>
	<div class="lookbook-grid">
		<?php
		// Real images from products and customers.
		$lookbook_images = array(
			array(
				'src'   => 'customers/customer-love-hurts-varsity-enhanced.webp',
				'alt'   => 'Love Hurts varsity jacket',
				'label' => 'Love Hurts',
				'class' => 'tall',
			),
			array(
				'src'   => 'products/br-d01-render-front.webp',
				'alt'   => 'Black Rose hockey jersey',
				'label' => 'Black Rose',
				'class' => '',
			),
			array(
				'src'   => 'customers/customer-kid-black-rose-hoodie-enhanced.webp',
				'alt'   => 'Kid in Black Rose hoodie',
				'label' => 'Street Style',
				'class' => '',
			),
			array(
				'src'   => 'customers/customer-rose-hoodie-beanie-enhanced.webp',
				'alt'   => 'Rose hoodie and beanie',
				'label' => 'Signature',
				'class' => '',
			),
			array(
				'src'   => 'products/br-d02-render-front.webp',
				'alt'   => 'Black Rose football jersey',
				'label' => 'Limited Edition',
				'class' => '',
			),
		);

		foreach ( $lookbook_images as $lb_img ) :
			$img_path  = $assets_uri . '/images/' . $lb_img['src'];
			$css_class = 'lb-img rv' . ( $lb_img['class'] ? ' ' . $lb_img['class'] : '' );
			?>
			<div class="<?php echo esc_attr( $css_class ); ?>">
				<img
					src="<?php echo esc_url( $img_path ); ?>"
					alt="<?php echo esc_attr( $lb_img['alt'] ); ?>"
					loading="lazy"
					decoding="async"
					width="480"
					height="640"
				/>
				<span class="lb-label"><?php echo esc_html( $lb_img['label'] ); ?></span>
			</div>
		<?php endforeach; ?>
	</div>
</section>

<!-- ═══ CRAFT ═══ -->
<section class="craft" id="craft" aria-label="<?php esc_attr_e( 'Our Craft', 'skyyrose-flagship' ); ?>">
	<div class="craft-inner">
		<div class="craft-header rv">
			<h2><?php echo esc_html( 'The Craft' ); ?></h2>
			<p><?php echo esc_html( 'Every stitch, every fabric, every detail — intentional.' ); ?></p>
		</div>
		<div class="craft-grid">
			<?php
			$craft_cards = array(
				array(
					'icon'  => '&#9830;',
					'label' => 'Premium Materials',
					'desc'  => '280–400gsm cotton. Italian wool blends. Full-grain leather. No shortcuts.',
				),
				array(
					'icon'  => '&#9733;',
					'label' => 'Oakland Made Mentality',
					'desc'  => 'Born from the struggle of East Oakland. Designed for the world. Built to last generations.',
				),
				array(
					'icon'  => '&#9775;',
					'label' => 'Gender Neutral',
					'desc'  => 'Pioneer in Bay Area gender-neutral fashion. Designed for anyone, regardless of gender or age.',
				),
				array(
					'icon'  => '&#9830;',
					'label' => 'Limited Editions',
					'desc'  => 'Small batch production. Individually numbered. When it\'s gone, it\'s gone.',
				),
			);

			$card_delay = 1;
			foreach ( $craft_cards as $card ) :
				?>
				<div class="craft-card rv rv-d<?php echo esc_attr( $card_delay ); ?>">
					<div class="craft-icon" aria-hidden="true"><?php echo wp_kses_post( $card['icon'] ); ?></div>
					<div class="craft-label"><?php echo esc_html( $card['label'] ); ?></div>
					<p class="craft-desc"><?php echo esc_html( $card['desc'] ); ?></p>
				</div>
				<?php
				$card_delay++;
			endforeach;
			?>
		</div>
	</div>
</section>

<!-- ═══ NEWSLETTER ═══ -->
<section class="newsletter" id="community" aria-label="<?php esc_attr_e( 'Newsletter', 'skyyrose-flagship' ); ?>">
	<div class="nl-inner">
		<p class="nl-eyebrow rv"><?php esc_html_e( 'Join the Movement', 'skyyrose-flagship' ); ?></p>
		<h2 class="nl-title rv rv-d1"><?php esc_html_e( 'For The Real Ones', 'skyyrose-flagship' ); ?></h2>
		<p class="nl-desc rv rv-d2"><?php esc_html_e( 'Early access to drops. Behind-the-scenes from Oakland. Stories that matter. No spam, just substance.', 'skyyrose-flagship' ); ?></p>
		<div class="nl-form rv rv-d3">
			<input
				type="email"
				class="nl-input"
				placeholder="<?php esc_attr_e( 'Your email address', 'skyyrose-flagship' ); ?>"
				id="nlEmail"
				aria-label="<?php esc_attr_e( 'Email address', 'skyyrose-flagship' ); ?>"
				required
			/>
			<button type="button" class="nl-submit"><?php esc_html_e( 'Join', 'skyyrose-flagship' ); ?></button>
		</div>
		<p class="nl-note rv rv-d4"><?php echo esc_html( 'Free to join · Unsubscribe anytime · Oakland love only' ); ?></p>
	</div>
</section>

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

<?php get_footer(); ?>
