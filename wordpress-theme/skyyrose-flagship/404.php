<?php
/**
 * 404 Error Page — The Skyy Rose Collection
 *
 * A luxurious, branded 404 page with animated gradient typography,
 * sparkle particles, search, collection quick-links, trending products,
 * quick navigation, newsletter CTA, floating orbs, and film grain overlay.
 *
 * @package SkyyRose_Flagship
 * @since   3.1.0
 */

get_header();

// Collection data: slug, label, accent color, glow color, tagline, description.
$skyyrose_collections = array(
	array(
		'slug'        => 'black-rose',
		'label'       => 'Black Rose',
		'accent'      => '#C0C0C0',
		'glow'        => 'rgba(192, 192, 192, 0.3)',
		'tagline'     => 'Gothic elegance, dark romance',
		'description' => 'Monochromatic pieces that channel mystery and silver-toned refinement.',
	),
	array(
		'slug'        => 'love-hurts',
		'label'       => 'Love Hurts',
		'accent'      => '#DC143C',
		'glow'        => 'rgba(220, 20, 60, 0.3)',
		'tagline'     => 'Dramatic, passionate, fearless',
		'description' => 'Bold crimson statements for those who wear their heart on their sleeve.',
	),
	array(
		'slug'        => 'signature',
		'label'       => 'Signature',
		'accent'      => '#B76E79',
		'glow'        => 'rgba(183, 110, 121, 0.3)',
		'tagline'     => 'Elevated, confident, refined',
		'description' => 'Rose gold and gold luxe essentials that define the brand.',
	),
	array(
		'slug'        => 'kids-capsule',
		'label'       => 'Kids Capsule',
		'accent'      => '#FFB6C1',
		'glow'        => 'rgba(255, 182, 193, 0.3)',
		'tagline'     => 'Joyful luxury, playful sophistication',
		'description' => 'Mini versions of our signature pieces for the youngest trendsetters.',
	),
);

// Quick navigation links: label, url path, SVG icon.
$skyyrose_quick_links = array(
	array(
		'label' => 'Shop All',
		'path'  => '/shop/',
		'icon'  => '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 01-8 0"/></svg>',
	),
	array(
		'label' => 'New Arrivals',
		'path'  => '/shop/?orderby=date',
		'icon'  => '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
	),
	array(
		'label' => 'Best Sellers',
		'path'  => '/shop/?orderby=popularity',
		'icon'  => '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20V10"/><path d="M18 20V4"/><path d="M6 20v-4"/></svg>',
	),
	array(
		'label' => 'Contact Us',
		'path'  => '/contact/',
		'icon'  => '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>',
	),
	array(
		'label' => 'About Us',
		'path'  => '/about/',
		'icon'  => '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
	),
	array(
		'label' => 'FAQ',
		'path'  => '/contact/#faq',
		'icon'  => '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
	),
);

// Trending products: try WooCommerce first, fall back to static data.
$skyyrose_trending_products = array();

if ( class_exists( 'WooCommerce' ) ) {
	$skyyrose_trending_query = new WP_Query(
		array(
			'post_type'      => 'product',
			'posts_per_page' => 4,
			'meta_key'       => 'total_sales',
			'orderby'        => 'meta_value_num',
			'order'          => 'DESC',
			'post_status'    => 'publish',
		)
	);

	if ( $skyyrose_trending_query->have_posts() ) {
		while ( $skyyrose_trending_query->have_posts() ) {
			$skyyrose_trending_query->the_post();
			$skyyrose_product = wc_get_product( get_the_ID() );

			if ( $skyyrose_product ) {
				$skyyrose_trending_products[] = array(
					'name'  => get_the_title(),
					'price' => $skyyrose_product->get_price_html(),
					'link'  => get_permalink(),
					'image' => get_the_post_thumbnail_url( get_the_ID(), 'woocommerce_thumbnail' ),
				);
			}
		}
		wp_reset_postdata();
	}
}

// Static fallback when WooCommerce is inactive or no products found.
if ( empty( $skyyrose_trending_products ) ) {
	$skyyrose_trending_products = array(
		array(
			'name'  => 'BLACK Rose Crewneck',
			'price' => '$120',
			'link'  => home_url( '/product/black-rose-crewneck/' ),
			'image' => '',
		),
		array(
			'name'  => 'Love Hurts Varsity Jacket',
			'price' => '$185',
			'link'  => home_url( '/product/love-hurts-varsity-jacket/' ),
			'image' => '',
		),
		array(
			'name'  => 'The Signature Tee',
			'price' => '$65',
			'link'  => home_url( '/product/the-signature-tee/' ),
			'image' => '',
		),
		array(
			'name'  => 'The Bay Set',
			'price' => '$210',
			'link'  => home_url( '/product/the-bay-set/' ),
			'image' => '',
		),
	);
}
?>

<main id="primary" class="error-404-page" role="main">

	<!-- Floating Orbs (background ambience) -->
	<div class="error-404-orbs" aria-hidden="true">
		<div class="error-404-orb error-404-orb--1"></div>
		<div class="error-404-orb error-404-orb--2"></div>
		<div class="error-404-orb error-404-orb--3"></div>
		<div class="error-404-orb error-404-orb--4"></div>
	</div>

	<!-- Sparkle Particles -->
	<div class="error-404-sparkles" aria-hidden="true">
		<?php for ( $skyyrose_i = 1; $skyyrose_i <= 12; $skyyrose_i++ ) : ?>
			<div class="error-404-sparkle error-404-sparkle--<?php echo absint( $skyyrose_i ); ?>"></div>
		<?php endfor; ?>
	</div>

	<!-- Film Grain Overlay -->
	<div class="error-404-grain" aria-hidden="true"></div>

	<div class="error-404-content">

		<!-- ============================
		     404 Display Number
		     ============================ -->
		<h1 class="error-404-number" aria-label="<?php esc_attr_e( 'Error 404', 'skyyrose-flagship' ); ?>">
			404
		</h1>

		<!-- ============================
		     Enhanced Message
		     ============================ -->
		<h2 class="error-404-title">
			<?php esc_html_e( 'Lost in Style', 'skyyrose-flagship' ); ?>
		</h2>

		<p class="error-404-subtitle">
			<?php esc_html_e( 'The page you\'re looking for has wandered off the runway', 'skyyrose-flagship' ); ?>
		</p>

		<p class="error-404-witty">
			<?php esc_html_e( 'Even our best pieces go off-grid sometimes', 'skyyrose-flagship' ); ?>
		</p>

		<!-- ============================
		     Search Bar
		     ============================ -->
		<div class="error-404-search" role="search" aria-label="<?php esc_attr_e( 'Search the site', 'skyyrose-flagship' ); ?>">
			<form action="<?php echo esc_url( home_url( '/' ) ); ?>" method="get" class="error-404-search-form">
				<label for="error-404-search-input" class="screen-reader-text">
					<?php esc_html_e( 'Search for:', 'skyyrose-flagship' ); ?>
				</label>
				<input
					type="search"
					id="error-404-search-input"
					class="error-404-search-input"
					name="s"
					placeholder="<?php esc_attr_e( 'Search products, collections, pages...', 'skyyrose-flagship' ); ?>"
					value=""
					autocomplete="off"
				/>
				<button type="submit" class="error-404-search-btn" aria-label="<?php esc_attr_e( 'Search', 'skyyrose-flagship' ); ?>">
					<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
						<circle cx="11" cy="11" r="8"/>
						<line x1="21" y1="21" x2="16.65" y2="16.65"/>
					</svg>
				</button>
			</form>
		</div>

		<!-- ============================
		     Collection Quick Links
		     ============================ -->
		<nav class="error-404-collections" aria-label="<?php esc_attr_e( 'Browse Collections', 'skyyrose-flagship' ); ?>">
			<h3 class="error-404-section-heading">
				<?php esc_html_e( 'Explore Our World', 'skyyrose-flagship' ); ?>
			</h3>

			<div class="error-404-cards">
				<?php foreach ( $skyyrose_collections as $skyyrose_collection ) : ?>
					<?php
					// Try to get the WooCommerce product category link and count.
					$skyyrose_link  = '#';
					$skyyrose_count = '';

					if ( function_exists( 'get_term_link' ) ) {
						$skyyrose_term = get_term_by( 'slug', $skyyrose_collection['slug'], 'product_cat' );
						if ( $skyyrose_term && ! is_wp_error( $skyyrose_term ) ) {
							$skyyrose_link  = get_term_link( $skyyrose_term );
							$skyyrose_count = sprintf(
								/* translators: %d: number of products */
								_n( '%d product', '%d products', $skyyrose_term->count, 'skyyrose-flagship' ),
								$skyyrose_term->count
							);
						}
					}

					// Fallback URL and explore text.
					if ( '#' === $skyyrose_link || is_wp_error( $skyyrose_link ) ) {
						$skyyrose_link  = home_url( '/collection/' . $skyyrose_collection['slug'] . '/' );
						$skyyrose_count = __( 'Explore', 'skyyrose-flagship' );
					}
					?>
					<a href="<?php echo esc_url( $skyyrose_link ); ?>"
					   class="error-404-card"
					   style="--card-accent: <?php echo esc_attr( $skyyrose_collection['accent'] ); ?>; --card-glow: <?php echo esc_attr( $skyyrose_collection['glow'] ); ?>">
						<span class="error-404-card-border" aria-hidden="true"></span>
						<span class="error-404-card-label">
							<?php echo esc_html( $skyyrose_collection['label'] ); ?>
						</span>
						<span class="error-404-card-description">
							<?php echo esc_html( $skyyrose_collection['description'] ); ?>
						</span>
						<span class="error-404-card-meta">
							<?php echo esc_html( $skyyrose_count ); ?>
						</span>
						<span class="error-404-card-arrow" aria-hidden="true">&rarr;</span>
					</a>
				<?php endforeach; ?>
			</div>
		</nav>

		<!-- ============================
		     Trending Products
		     ============================ -->
		<section class="error-404-trending" aria-label="<?php esc_attr_e( 'Trending Products', 'skyyrose-flagship' ); ?>">
			<h3 class="error-404-section-heading">
				<?php esc_html_e( 'Trending Right Now', 'skyyrose-flagship' ); ?>
			</h3>

			<div class="error-404-trending-grid">
				<?php foreach ( $skyyrose_trending_products as $skyyrose_product_item ) : ?>
					<a href="<?php echo esc_url( $skyyrose_product_item['link'] ); ?>" class="error-404-product-card">
						<div class="error-404-product-image">
							<?php if ( ! empty( $skyyrose_product_item['image'] ) ) : ?>
								<img
									src="<?php echo esc_url( $skyyrose_product_item['image'] ); ?>"
									alt="<?php echo esc_attr( $skyyrose_product_item['name'] ); ?>"
									loading="lazy"
									width="300"
									height="400"
								/>
							<?php else : ?>
								<div class="error-404-product-placeholder" aria-hidden="true">
									<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
										<path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/>
										<line x1="3" y1="6" x2="21" y2="6"/>
										<path d="M16 10a4 4 0 01-8 0"/>
									</svg>
								</div>
							<?php endif; ?>
						</div>
						<div class="error-404-product-info">
							<span class="error-404-product-name">
								<?php echo esc_html( $skyyrose_product_item['name'] ); ?>
							</span>
							<span class="error-404-product-price">
								<?php
								if ( is_string( $skyyrose_product_item['price'] ) && strpos( $skyyrose_product_item['price'], '<' ) !== false ) {
									// WooCommerce HTML price — already escaped by WC.
									echo wp_kses_post( $skyyrose_product_item['price'] );
								} else {
									echo esc_html( $skyyrose_product_item['price'] );
								}
								?>
							</span>
						</div>
					</a>
				<?php endforeach; ?>
			</div>
		</section>

		<!-- ============================
		     Quick Navigation
		     ============================ -->
		<nav class="error-404-quick-nav" aria-label="<?php esc_attr_e( 'Quick Navigation', 'skyyrose-flagship' ); ?>">
			<h3 class="error-404-section-heading">
				<?php esc_html_e( 'Quick Links', 'skyyrose-flagship' ); ?>
			</h3>

			<div class="error-404-nav-grid">
				<?php foreach ( $skyyrose_quick_links as $skyyrose_link_item ) : ?>
					<a href="<?php echo esc_url( home_url( $skyyrose_link_item['path'] ) ); ?>" class="error-404-nav-item">
						<span class="error-404-nav-icon" aria-hidden="true">
							<?php
							// SVG icons are hardcoded above — safe to output.
							echo $skyyrose_link_item['icon']; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- Hardcoded SVG.
							?>
						</span>
						<span class="error-404-nav-label">
							<?php echo esc_html( $skyyrose_link_item['label'] ); ?>
						</span>
					</a>
				<?php endforeach; ?>
			</div>
		</nav>

		<!-- ============================
		     Newsletter CTA
		     ============================ -->
		<section class="error-404-newsletter" aria-label="<?php esc_attr_e( 'Newsletter Signup', 'skyyrose-flagship' ); ?>">
			<h3 class="error-404-newsletter-heading">
				<?php esc_html_e( 'While you\'re here, join the family', 'skyyrose-flagship' ); ?>
			</h3>
			<p class="error-404-newsletter-text">
				<?php esc_html_e( 'Be the first to know about drops, exclusives, and events.', 'skyyrose-flagship' ); ?>
			</p>
			<form class="error-404-newsletter-form" action="<?php echo esc_url( home_url( '/' ) ); ?>" method="post">
				<?php wp_nonce_field( 'skyyrose_newsletter', 'skyyrose_newsletter_nonce' ); ?>
				<label for="error-404-newsletter-email" class="screen-reader-text">
					<?php esc_html_e( 'Email address', 'skyyrose-flagship' ); ?>
				</label>
				<input
					type="email"
					id="error-404-newsletter-email"
					name="skyyrose_newsletter_email"
					class="error-404-newsletter-input"
					placeholder="<?php esc_attr_e( 'Enter your email', 'skyyrose-flagship' ); ?>"
					required
					autocomplete="email"
				/>
				<button type="submit" class="error-404-newsletter-btn">
					<?php esc_html_e( 'Join', 'skyyrose-flagship' ); ?>
				</button>
			</form>
		</section>

		<!-- ============================
		     Dual CTA Buttons
		     ============================ -->
		<div class="error-404-cta-group">
			<a href="<?php echo esc_url( home_url( '/' ) ); ?>" class="error-404-cta error-404-cta--primary">
				<?php esc_html_e( 'Return Home', 'skyyrose-flagship' ); ?>
			</a>
			<a href="<?php echo esc_url( home_url( '/shop/' ) ); ?>" class="error-404-cta error-404-cta--secondary">
				<?php esc_html_e( 'Continue Shopping', 'skyyrose-flagship' ); ?>
			</a>
		</div>

	</div><!-- .error-404-content -->

</main><!-- #primary -->

<?php
get_footer();
