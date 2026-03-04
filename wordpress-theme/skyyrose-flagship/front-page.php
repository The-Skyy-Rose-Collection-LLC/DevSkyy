<?php
/**
 * Template Name: Homepage
 *
 * Elite Web Builder homepage — cinematic loader, animated hero,
 * 3 collection showcases with WooCommerce product grids,
 * founder story, and newsletter signup.
 *
 * @package SkyyRose_Flagship
 * @since   4.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

get_header();

// Collection configuration — maps slugs to display settings.
$skyyrose_collections = array(
	'black-rose' => array(
		'key'        => 'br',
		'name'       => 'BLACK ROSE',
		'number'     => '01',
		'accent'     => '#C0C0C0',
		'accent_rgb' => '192, 192, 192',
		'bg'         => '#000',
		'tagline'    => 'For those who found power in the dark.',
		'meta'       => array( 'Limited Edition' ),
		'manifesto'  => array(
			'eyebrow'  => 'The Philosophy',
			'headline' => "Limited Drops.<br>Unlimited Vision.",
			'body'     => '<p>Every piece numbered. Every design intentional. This isn&rsquo;t fashion &mdash; it&rsquo;s a statement.</p><p>Black Rose draws from midnight garden aesthetics &mdash; dark marble, silver thorns, moonlit architecture. Each garment carries the weight of intention and the precision of something meant to last forever.</p><p>Available until it&rsquo;s not.</p>',
		),
		'scene_img'  => 'scenes/black-rose/cathedral-entrance.jpg',
		'hero_img'   => 'scenes/black-rose/cathedral-entrance.jpg',
	),
	'love-hurts' => array(
		'key'        => 'lh',
		'name'       => 'LOVE HURTS',
		'number'     => '02',
		'accent'     => '#DC143C',
		'accent_rgb' => '220, 20, 60',
		'bg'         => '#0C0206',
		'tagline'    => 'Wear your heart. Own your scars.',
		'meta'       => array( 'Family Legacy' ),
		'manifesto'  => array(
			'eyebrow'  => 'The Story',
			'headline' => "Named For Family.<br>Made For Feeling.",
			'body'     => '<p>&ldquo;Hurts&rdquo; is the founder&rsquo;s family name. This collection carries that weight &mdash; raw emotion transformed into wearable art.</p><p>Gothic castle halls, crimson fire, rose petals on stone floors. Every thread channels the beauty in pain, the strength in vulnerability. Some things you don&rsquo;t hide. You wear them.</p>',
		),
		'scene_img'  => 'scenes/love-hurts/enchanted-shrine.jpg',
		'hero_img'   => 'scenes/love-hurts/enchanted-shrine.jpg',
	),
	'signature'  => array(
		'key'        => 'sg',
		'name'       => 'SIGNATURE',
		'number'     => '03',
		'accent'     => '#D4AF37',
		'accent_rgb' => '212, 175, 55',
		'bg'         => '#0A0804',
		'tagline'    => 'The foundation of any wardrobe worth building.',
		'meta'       => array( 'Foundation Wardrobe' ),
		'manifesto'  => array(
			'eyebrow'  => 'The Standard',
			'headline' => "Start Here.<br>Build Everything.",
			'body'     => '<p>Clean lines. Quality materials. Pieces that work as hard as you do. No logos screaming for attention. Just clothes that fit right and last.</p><p>Signature is the foundation &mdash; Italian wool-blends, premium cotton, rose-gold hardware. Grand ballroom energy in everyday wear. Timeless pieces built for the long game.</p>',
		),
		'scene_img'  => 'scenes/signature/city-overlook.jpg',
		'hero_img'   => 'scenes/signature/city-overlook.jpg',
	),
);

// Divider quotes between collections.
$skyyrose_dividers = array(
	'br_lh' => 'Named for family. Made for feeling. The Hurts name runs deep &mdash; turning what breaks us into <em>what makes us unforgettable</em>.',
	'lh_sg' => 'We don&rsquo;t make clothes for everybody. We make them for <em>somebody</em>. If you know, you know.',
);
?>

<div class="vignette" aria-hidden="true"></div>

<!-- Cinematic Loader -->
<div id="loader" role="status" aria-label="<?php esc_attr_e( 'Loading', 'skyyrose-flagship' ); ?>">
	<div class="loader-brand"><?php echo esc_html( 'SkyyRose' ); ?></div>
	<div class="loader-sub"><?php echo esc_html( 'The Collection' ); ?></div>
	<div class="loader-bar"><div class="loader-fill" id="loaderFill"></div></div>
</div>

<main id="primary" class="site-main front-page" role="main" tabindex="-1">

	<!-- ═══════════════════════════════════════
	     HERO SECTION
	     ═══════════════════════════════════════ -->
	<section class="hp-hero" id="hero" aria-label="<?php esc_attr_e( 'SkyyRose Collection', 'skyyrose-flagship' ); ?>">
		<div class="hero-atmo" aria-hidden="true"></div>
		<div class="hero-frame" aria-hidden="true"></div>
		<div class="hero-particles" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></div>
		<div class="hero-content">
			<div class="hero-monogram">
				<img
					src="<?php echo esc_url( get_template_directory_uri() . '/assets/images/sr-monogram-hero.png' ); ?>"
					alt="<?php esc_attr_e( 'SkyyRose Monogram', 'skyyrose-flagship' ); ?>"
					class="hero-monogram__img"
					width="400"
					height="400"
					loading="eager"
					fetchpriority="high"
					decoding="async"
				>
			</div>
			<h1 class="hero-title"><?php echo esc_html( 'SKYYROSE' ); ?></h1>
			<p class="hero-tagline"><?php echo esc_html( 'Luxury Grows from Concrete.' ); ?></p>
			<div class="hero-cta-row">
				<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>" class="hero-cta hero-cta-primary"><?php esc_html_e( 'SHOP NOW', 'skyyrose-flagship' ); ?></a>
				<a href="#collections-start" class="hero-cta"><?php esc_html_e( 'EXPLORE', 'skyyrose-flagship' ); ?></a>
			</div>
		</div>
		<div class="hero-scroll" aria-hidden="true">
			<span><?php esc_html_e( 'Scroll', 'skyyrose-flagship' ); ?></span>
			<div class="hero-scroll-line"></div>
		</div>
	</section>

	<!-- ═══════════════════════════════════════
	     MARQUEE BANNER
	     ═══════════════════════════════════════ -->
	<div class="marquee" aria-hidden="true">
		<div class="marquee-track">
			<?php
			$marquee_items = array( 'Black Rose', 'Love Hurts', 'Signature', 'Oakland Made', 'Gender Neutral', 'Limited Edition', 'Pre-Order Open', 'Built Different' );
			// Duplicate for seamless loop.
			for ( $i = 0; $i < 2; $i++ ) {
				foreach ( $marquee_items as $item ) {
					echo '<span class="marquee-item">' . esc_html( $item ) . '<span class="marquee-dot"></span></span>';
				}
			}
			?>
		</div>
	</div>

	<!-- ═══════════════════════════════════════
	     ORIGIN STORY
	     ═══════════════════════════════════════ -->
	<section class="hp-story" id="story" aria-label="<?php esc_attr_e( 'Our Story', 'skyyrose-flagship' ); ?>">
		<div class="story-bg" aria-hidden="true"></div>
		<div class="story-inner">
			<div class="story-left">
				<p class="story-eyebrow rv"><?php esc_html_e( 'The Origin', 'skyyrose-flagship' ); ?></p>
				<h2 class="story-heading rv rv-d1">
					<?php echo esc_html( 'Born In' ); ?><br><?php echo esc_html( 'The Town' ); ?>
					<em><?php echo esc_html( 'A father\'s promise. A daughter\'s name.' ); ?></em>
				</h2>
				<div class="story-body rv rv-d2">
					<p>In a neighborhood where opportunities are as scarce as support, <strong>Corey Foster</strong> refused to become another statistic. Four years ago he had lost everything &mdash; broke, no drive left, a baby on the way.</p>
					<p>Through failed websites, scammer manufacturers, and single parenthood with no support &mdash; he built something real. Named after his daughter <strong>Skyy Rose</strong>. Designed for anyone, regardless of gender or age.</p>
					<p>The Skyy Rose Collection isn&rsquo;t just clothing. It&rsquo;s proof that your circumstances don&rsquo;t define your destination.</p>
				</div>
				<div class="story-stats rv rv-d3">
					<div>
						<div class="stat-num">3</div>
						<div class="stat-label"><?php esc_html_e( 'Collections', 'skyyrose-flagship' ); ?></div>
					</div>
					<div>
						<?php
						// Dynamic product count from WooCommerce.
						$total_products = 0;
						if ( function_exists( 'wc_get_products' ) ) {
							$total_products = count( wc_get_products( array(
								'status' => 'publish',
								'limit'  => -1,
								'return' => 'ids',
							) ) );
						}
						?>
						<div class="stat-num"><?php echo esc_html( $total_products > 0 ? $total_products : '28' ); ?></div>
						<div class="stat-label"><?php esc_html_e( 'Pieces', 'skyyrose-flagship' ); ?></div>
					</div>
					<div>
						<div class="stat-num">2023</div>
						<div class="stat-label"><?php esc_html_e( 'Established', 'skyyrose-flagship' ); ?></div>
					</div>
				</div>
			</div>
			<div class="story-right rv-right" style="position: relative;">
				<div class="story-image">
					<img
						src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/about-story-0.jpg' ); ?>"
						alt="<?php esc_attr_e( 'SkyyRose grand ballroom', 'skyyrose-flagship' ); ?>"
						loading="lazy"
						width="600"
						height="800"
					/>
				</div>
				<div class="story-float-tag">
					<div class="ft-label"><?php esc_html_e( 'Recognition', 'skyyrose-flagship' ); ?></div>
					<div class="ft-value"><?php echo wp_kses_post( 'Best Bay Area<br>Clothing Line 2024' ); ?></div>
				</div>
			</div>
		</div>
	</section>

	<!-- ═══════════════════════════════════════
	     FOUNDER QUOTE
	     ═══════════════════════════════════════ -->
	<div class="quote-break">
		<blockquote class="qb-text rv">
			&ldquo;If you asked me four years ago, I never would have thought I&rsquo;d be here. I had no drive, lost it all, a baby on the way, and was broke. But we knew we had to get it <em>by any means necessary</em>.&rdquo;
		</blockquote>
		<p class="qb-attr rv rv-d1">&mdash; Corey Foster, Founder</p>
	</div>

	<?php
	/* ═══════════════════════════════════════
	   COLLECTION SECTIONS (3x)
	   Each: Hero → Manifesto → Featured Product → Product Grid
	   ═══════════════════════════════════════ */
	$collection_index = 0;
	$divider_keys     = array_keys( $skyyrose_dividers );

	foreach ( $skyyrose_collections as $slug => $col ) :
		$key        = $col['key'];
		$assets_uri = SKYYROSE_ASSETS_URI;

		// Get products from WooCommerce for this collection.
		$products     = array();
		$product_data = array();
		if ( function_exists( 'wc_get_products' ) ) {
			$products = wc_get_products( array(
				'category' => array( $slug ),
				'status'   => 'publish',
				'limit'    => 12,
				'orderby'  => 'menu_order',
				'order'    => 'ASC',
			) );
		}

		$product_count = count( $products );
		$price_range   = '';
		if ( $product_count > 0 ) {
			$prices = array_map( function ( $p ) {
				return (float) $p->get_price();
			}, $products );
			$prices = array_filter( $prices );
			if ( ! empty( $prices ) ) {
				$price_range = '$' . number_format( min( $prices ) ) . ' — $' . number_format( max( $prices ) );
			}
		}

		// Determine featured product (first product or second if available).
		$featured_product = ! empty( $products ) ? $products[0] : null;
		if ( count( $products ) > 1 ) {
			$featured_product = $products[1];
		}
		?>

		<!-- ███ <?php echo esc_html( strtoupper( $col['name'] ) ); ?> ███ -->
		<section class="cl-hero <?php echo esc_attr( $key ); ?>" id="<?php echo esc_attr( $slug ); ?>" aria-label="<?php echo esc_attr( $col['name'] . ' Collection' ); ?>">
			<div class="cl-hero-img">
				<img
					src="<?php echo esc_url( $assets_uri . '/images/' . $col['hero_img'] ); ?>"
					alt="<?php echo esc_attr( $col['name'] . ' collection scene' ); ?>"
					loading="lazy"
					width="1920"
					height="1080"
				/>
			</div>
			<div class="cl-hero-overlay"></div>
			<div class="cl-hero-content">
				<p class="cl-hero-num"><?php echo esc_html( 'Collection ' . $col['number'] ); ?><span></span></p>
				<h2 class="cl-hero-name">
					<?php
					$name_parts = explode( ' ', $col['name'] );
					echo esc_html( $name_parts[0] );
					if ( isset( $name_parts[1] ) ) {
						echo '<br>' . esc_html( $name_parts[1] );
					}
					?>
				</h2>
				<p class="cl-hero-tagline"><?php echo esc_html( $col['tagline'] ); ?></p>
				<div class="cl-hero-meta">
					<span><?php echo esc_html( $product_count . ' Pieces' ); ?></span>
					<?php if ( $price_range ) : ?>
						<span><?php echo esc_html( $price_range ); ?></span>
					<?php endif; ?>
					<?php foreach ( $col['meta'] as $meta_item ) : ?>
						<span><?php echo esc_html( $meta_item ); ?></span>
					<?php endforeach; ?>
				</div>
			</div>
			<div class="cl-hero-scroll" aria-hidden="true"><span><?php esc_html_e( 'Explore', 'skyyrose-flagship' ); ?></span></div>
		</section>

		<!-- Manifesto -->
		<div class="cl-manifesto <?php echo esc_attr( $key ); ?>">
			<div class="cl-manifesto-inner">
				<div class="cl-mf-text">
					<p class="cl-mf-eyebrow rv"><?php echo esc_html( $col['manifesto']['eyebrow'] ); ?></p>
					<h3 class="cl-mf-headline rv rv-d1"><?php echo wp_kses_post( $col['manifesto']['headline'] ); ?></h3>
					<div class="cl-mf-body rv rv-d2"><?php echo wp_kses_post( $col['manifesto']['body'] ); ?></div>
					<a href="<?php echo esc_url( home_url( '/collections/' . $slug . '/' ) ); ?>" class="cl-mf-cta rv rv-d3"><?php esc_html_e( 'View Collection', 'skyyrose-flagship' ); ?></a>
				</div>
				<div class="cl-mf-scene rv-right">
					<img
						src="<?php echo esc_url( $assets_uri . '/images/' . $col['scene_img'] ); ?>"
						alt="<?php echo esc_attr( $col['name'] . ' scene' ); ?>"
						loading="lazy"
						width="720"
						height="500"
					/>
				</div>
			</div>
		</div>

		<!-- Featured Product -->
		<?php if ( $featured_product ) : ?>
			<div class="cl-featured <?php echo esc_attr( $key ); ?>" id="<?php echo esc_attr( $key ); ?>-featured">
				<div class="cl-featured-inner">
					<div class="cl-feat-visual rv-left">
						<?php
						$feat_thumb = $featured_product->get_image_id();
						if ( $feat_thumb ) {
							echo wp_get_attachment_image( $feat_thumb, 'large', false, array(
								'class'   => 'cl-feat-product-img',
								'loading' => 'lazy',
							) );
						} else {
							?>
							<span class="cl-feat-letter"><?php echo esc_html( mb_substr( $featured_product->get_name(), 0, 1 ) ); ?></span>
						<?php } ?>
						<span class="cl-feat-badge"><?php echo esc_html( $col['name'] ); ?></span>
						<span class="cl-feat-tag"><?php esc_html_e( 'Featured Piece', 'skyyrose-flagship' ); ?></span>
					</div>
					<div class="cl-feat-info">
						<p class="cl-feat-col rv"><?php echo esc_html( $col['name'] . ' Collection' ); ?></p>
						<h3 class="cl-feat-name rv rv-d1"><?php echo esc_html( $featured_product->get_name() ); ?></h3>
						<p class="cl-feat-price rv rv-d1"><?php echo wp_kses_post( $featured_product->get_price_html() ); ?></p>
						<p class="cl-feat-desc rv rv-d2"><?php echo esc_html( $featured_product->get_short_description() ); ?></p>
						<div class="cl-feat-details rv rv-d2">
							<?php
							$sku = $featured_product->get_sku();
							if ( $sku ) :
								?>
								<div class="cl-feat-detail">
									<span class="dt-label"><?php esc_html_e( 'SKU', 'skyyrose-flagship' ); ?></span>
									<span class="dt-value"><?php echo esc_html( $sku ); ?></span>
								</div>
							<?php endif; ?>
						</div>

						<a
							href="<?php echo esc_url( $featured_product->get_permalink() ); ?>"
							class="cl-feat-add rv rv-d3"
						>
							<?php
							if ( skyyrose_is_preorder( $featured_product->get_id() ) ) {
								/* translators: %s: product price */
								printf( esc_html__( 'Pre-Order — %s', 'skyyrose-flagship' ), wp_kses_post( $featured_product->get_price_html() ) );
							} else {
								esc_html_e( 'View Product', 'skyyrose-flagship' );
							}
							?>
						</a>
					</div>
				</div>
			</div>
		<?php endif; ?>

		<!-- Product Grid -->
		<div class="cl-catalog <?php echo esc_attr( $key ); ?>">
			<div class="cl-catalog-head">
				<h3 class="cl-catalog-title rv"><?php esc_html_e( 'Full Collection', 'skyyrose-flagship' ); ?></h3>
				<span class="cl-catalog-count rv rv-d1">
					<?php
					echo esc_html( $product_count . ' Pieces' );
					if ( $price_range ) {
						echo ' — ' . esc_html( $price_range );
					}
					?>
				</span>
			</div>
			<div class="cl-grid" id="grid-<?php echo esc_attr( $key ); ?>">
				<?php
				if ( ! empty( $products ) ) :
					$delay_index = 1;
					foreach ( $products as $product ) :
						$delay_class = 'rv-d' . min( $delay_index, 4 );
						$thumb_id    = $product->get_image_id();
						$permalink   = $product->get_permalink();
						?>
						<a href="<?php echo esc_url( $permalink ); ?>" class="cl-card rv <?php echo esc_attr( $delay_class ); ?>">
							<div class="cl-card-img">
								<?php if ( $thumb_id ) : ?>
									<?php echo wp_get_attachment_image( $thumb_id, 'medium', false, array(
										'class'   => 'cl-card-product-img',
										'loading' => 'lazy',
										'style'   => 'width:100%;height:100%;object-fit:cover;',
									) ); ?>
								<?php else : ?>
									<span class="cl-card-letter"><?php echo esc_html( mb_substr( $product->get_name(), 0, 1 ) ); ?></span>
								<?php endif; ?>
								<span class="cl-card-badge"><?php echo esc_html( $col['name'] ); ?></span>
								<?php if ( skyyrose_is_preorder( $product->get_id() ) ) : ?>
									<span class="cl-card-pre"><?php esc_html_e( 'Pre-Order', 'skyyrose-flagship' ); ?></span>
								<?php endif; ?>
								<div class="cl-card-hover"><span><?php esc_html_e( 'View Piece', 'skyyrose-flagship' ); ?></span></div>
							</div>
							<div class="cl-card-body">
								<h3 class="cl-card-name"><?php echo esc_html( $product->get_name() ); ?></h3>
								<p class="cl-card-desc"><?php echo esc_html( $product->get_short_description() ); ?></p>
								<div class="cl-card-foot">
									<span class="cl-card-price"><?php echo wp_kses_post( $product->get_price_html() ); ?></span>
									<span class="cl-card-btn"><?php esc_html_e( 'Details', 'skyyrose-flagship' ); ?></span>
								</div>
							</div>
						</a>
						<?php
						$delay_index++;
					endforeach;
				else :
					?>
					<p class="cl-catalog-empty" style="color: var(--haze); font-style: italic; grid-column: 1 / -1; text-align: center; padding: 60px 0;">
						<?php esc_html_e( 'Products coming soon.', 'skyyrose-flagship' ); ?>
					</p>
				<?php endif; ?>
			</div>
		</div>

		<?php
		// Add divider between collections (not after the last one).
		if ( $collection_index < count( $skyyrose_collections ) - 1 && isset( $divider_keys[ $collection_index ] ) ) :
			$divider_key = $divider_keys[ $collection_index ];
			?>
			<div class="cl-divider">
				<p class="cl-divider-text rv"><?php echo wp_kses_post( $skyyrose_dividers[ $divider_key ] ); ?></p>
			</div>
		<?php endif; ?>

		<?php
		$collection_index++;
	endforeach;
	?>

	<!-- ═══════════════════════════════════════
	     NEWSLETTER
	     ═══════════════════════════════════════ -->
	<section class="hp-newsletter" id="community" aria-label="<?php esc_attr_e( 'Newsletter Signup', 'skyyrose-flagship' ); ?>">
		<div class="nl-inner">
			<p class="nl-eyebrow rv"><?php esc_html_e( 'Join the Movement', 'skyyrose-flagship' ); ?></p>
			<h2 class="nl-title rv rv-d1"><?php esc_html_e( 'For The Real Ones', 'skyyrose-flagship' ); ?></h2>
			<p class="nl-desc rv rv-d2"><?php esc_html_e( 'Early access to drops. Behind-the-scenes from Oakland. Stories that matter.', 'skyyrose-flagship' ); ?></p>
			<div class="nl-form rv rv-d3">
				<?php wp_nonce_field( 'skyyrose_newsletter', 'skyyrose_nl_nonce', false ); ?>
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

</main><!-- #primary -->

<?php
get_footer();
