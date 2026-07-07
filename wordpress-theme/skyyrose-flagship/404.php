<?php
/**
 * 404 Error Page — The Skyy Rose Collection
 *
 * A luxurious, branded 404 page with animated gradient typography,
 * sparkle particles, search, collection quick-links, trending products,
 * quick navigation, newsletter CTA, floating orbs, and film grain overlay.
 *
 * @package SkyyRose
 * @since   3.1.0
 */

get_header();

// Collection data sourced from inc/collections-config.php (single source of truth).
$skyyrose_collections = array_values( skyyrose_get_collections_config() );

// Quick navigation links: label, url path, SVG icon.
$skyyrose_quick_links = array(
	array(
		'label' => __( 'Shop All', 'skyyrose' ),
		'path'  => '/shop/',
		'icon'  => '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 01-8 0"/></svg>',
	),
	array(
		'label' => __( 'New Arrivals', 'skyyrose' ),
		'path'  => '/shop/?orderby=date',
		'icon'  => '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
	),
	array(
		'label' => __( 'Best Sellers', 'skyyrose' ),
		'path'  => '/shop/?orderby=popularity',
		'icon'  => '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20V10"/><path d="M18 20V4"/><path d="M6 20v-4"/></svg>',
	),
	array(
		'label' => __( 'Reach Out', 'skyyrose' ),
		'path'  => '/contact/',
		'icon'  => '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>',
	),
	array(
		'label' => __( 'The Origin', 'skyyrose' ),
		'path'  => '/about/',
		'icon'  => '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
	),
	array(
		'label' => __( 'FAQ', 'skyyrose' ),
		'path'  => '/faq/',
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
			$skyyrose_product = skyyrose_current_wc_product();

			if ( $skyyrose_product ) {
				$skyyrose_trending_products[] = array(
					'name'  => get_the_title(),
					'price' => $skyyrose_product->get_price_html(),
					'link'  => get_permalink(),
					'image' => get_the_post_thumbnail_url( get_the_ID(), 'woocommerce_thumbnail' ),
				);
			}
		}
	}
	wp_reset_postdata();
}

// Static fallback when WooCommerce is inactive or no products found.
// Source from centralized catalog so prices stay in sync.
if ( empty( $skyyrose_trending_products ) ) {
	// First four published products from the canonical catalog — no hardcoded SKU list.
	$skyyrose_404_skus = array();
	foreach ( skyyrose_get_product_catalog() as $skyyrose_404_candidate ) {
		if ( ! empty( $skyyrose_404_candidate['published'] ) ) {
			$skyyrose_404_skus[] = $skyyrose_404_candidate['sku'];
			if ( count( $skyyrose_404_skus ) >= 4 ) {
				break;
			}
		}
	}
	foreach ( $skyyrose_404_skus as $skyyrose_404_sku ) {
		$skyyrose_404_product = skyyrose_get_product( $skyyrose_404_sku );
		if ( $skyyrose_404_product ) {
			$skyyrose_404_image           = ! empty( $skyyrose_404_product['front_model_image'] )
				? get_theme_file_uri( $skyyrose_404_product['front_model_image'] )
				: ( ! empty( $skyyrose_404_product['image'] )
					? get_theme_file_uri( $skyyrose_404_product['image'] )
					: '' );
			$skyyrose_trending_products[] = array(
				'name'  => $skyyrose_404_product['name'],
				'price' => skyyrose_format_price( $skyyrose_404_product ),
				'link'  => home_url( '/pre-order/' ),
				'image' => $skyyrose_404_image,
			);
		}
	}
}
?>

<main id="primary" class="error-404-page" role="main" tabindex="-1">

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
		<h1 class="error-404-number rv-clip-up" aria-label="<?php esc_attr_e( 'Error 404', 'skyyrose' ); ?>">
			404
		</h1>

		<!-- ============================
			Enhanced Message
			============================ -->
		<h2 class="error-404-title rv-clip-left">
			<?php esc_html_e( 'Not Here.', 'skyyrose' ); ?>
		</h2>

		<p class="error-404-subtitle rv-blur">
			<?php esc_html_e( 'That page doesn\'t exist. Oakland taught us to keep moving.', 'skyyrose' ); ?>
		</p>

		<p class="error-404-witty">
			<?php esc_html_e( 'The concrete\'s still here. So are the collections.', 'skyyrose' ); ?>
		</p>

		<!-- ============================
			Search Bar
			============================ -->
		<div class="error-404-search" role="search" aria-label="<?php esc_attr_e( 'Search the site', 'skyyrose' ); ?>">
			<form action="<?php echo esc_url( home_url( '/' ) ); ?>" method="get" class="error-404-search-form">
				<label for="error-404-search-input" class="screen-reader-text">
					<?php esc_html_e( 'Search for:', 'skyyrose' ); ?>
				</label>
				<input
					type="search"
					id="error-404-search-input"
					class="error-404-search-input"
					name="s"
					placeholder="<?php esc_attr_e( 'Search products, collections, pages...', 'skyyrose' ); ?>"
					value=""
					autocomplete="off"
				/>
				<button type="submit" class="error-404-search-btn" aria-label="<?php esc_attr_e( 'Search', 'skyyrose' ); ?>">
					<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
						<circle cx="11" cy="11" r="8"/>
						<line x1="21" y1="21" x2="16.65" y2="16.65"/>
					</svg>
				</button>
			</form>
		</div>

		<!-- ============================
			Brand Mascot — Fun Error State
			============================ -->
		<div class="error-404-mascot">
			<?php
			$skyyrose_mascot_404_path = SKYYROSE_DIR . '/assets/images/mascot/skyyrose-mascot-404.png';
			$skyyrose_mascot_ref_path = SKYYROSE_DIR . '/assets/images/mascot/skyy-canonical.jpeg';
			$skyyrose_mascot_404_url  = SKYYROSE_ASSETS_URI . '/images/mascot/skyyrose-mascot-404.png';
			$skyyrose_mascot_ref_url  = SKYYROSE_ASSETS_URI . '/images/mascot/skyy-canonical.jpeg';

			$skyyrose_mascot_display = '';
			if ( file_exists( $skyyrose_mascot_404_path ) ) {
				$skyyrose_mascot_display = $skyyrose_mascot_404_url;
			} elseif ( file_exists( $skyyrose_mascot_ref_path ) ) {
				$skyyrose_mascot_display = $skyyrose_mascot_ref_url;
			}

			if ( $skyyrose_mascot_display ) :
				?>
				<img
					src="<?php echo esc_url( $skyyrose_mascot_display ); ?>"
					alt="<?php esc_attr_e( 'Skyy, SkyyRose brand mascot.', 'skyyrose' ); ?>"
					class="error-404-mascot__image"
					width="200"
					height="250"
					loading="lazy"
					decoding="async"
				/>
			<?php else : ?>
				<div class="error-404-mascot__placeholder" aria-hidden="true">
					<svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="<?php echo esc_attr( SKYYROSE_COLOR_ROSE_GOLD ); ?>" stroke-width="1" stroke-linecap="round"><circle cx="12" cy="8" r="5"/><path d="M20 21a8 8 0 1 0-16 0"/></svg>
				</div>
			<?php endif; ?>
			<p class="error-404-mascot__speech">
				<?php esc_html_e( 'Nothing here. The shop still has you covered.', 'skyyrose' ); ?>
			</p>
		</div>

		<!-- ============================
			Collection Quick Links
			============================ -->
		<nav class="error-404-collections" aria-label="<?php esc_attr_e( 'Browse Collections', 'skyyrose' ); ?>">
			<h3 class="error-404-section-heading">
				<?php esc_html_e( 'Explore Our World', 'skyyrose' ); ?>
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
								_n( '%d product', '%d products', $skyyrose_term->count, 'skyyrose' ),
								$skyyrose_term->count
							);
						}
					}

					// Fallback URL and explore text.
					if ( '#' === $skyyrose_link || is_wp_error( $skyyrose_link ) ) {
						$skyyrose_link  = home_url( '/collections/' . $skyyrose_collection['slug'] . '/' );
						$skyyrose_count = __( 'Explore', 'skyyrose' );
					}
					?>
					<a href="<?php echo esc_url( $skyyrose_link ); ?>"
						class="error-404-card"
						data-collection="<?php echo esc_attr( $skyyrose_collection['slug'] ); ?>">
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
		<section class="error-404-trending" aria-label="<?php esc_attr_e( 'Trending Products', 'skyyrose' ); ?>">
			<h3 class="error-404-section-heading">
				<?php esc_html_e( 'Trending Right Now', 'skyyrose' ); ?>
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
		<nav class="error-404-quick-nav" aria-label="<?php esc_attr_e( 'Quick Navigation', 'skyyrose' ); ?>">
			<h3 class="error-404-section-heading">
				<?php esc_html_e( 'Quick Links', 'skyyrose' ); ?>
			</h3>

			<div class="error-404-nav-grid">
				<?php foreach ( $skyyrose_quick_links as $skyyrose_link_item ) : ?>
					<a href="<?php echo esc_url( home_url( $skyyrose_link_item['path'] ) ); ?>" class="error-404-nav-item">
						<span class="error-404-nav-icon" aria-hidden="true">
							<?php
							// SVG icons are hardcoded above — safe to output.
							echo wp_kses( $skyyrose_link_item['icon'], skyyrose_svg_kses_allowed() );
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
		<section class="error-404-newsletter" aria-label="<?php esc_attr_e( 'Newsletter Signup', 'skyyrose' ); ?>">
			<h3 class="error-404-newsletter-heading">
				<?php esc_html_e( 'While you\'re here, join the family', 'skyyrose' ); ?>
			</h3>
			<p class="error-404-newsletter-text">
				<?php esc_html_e( 'Be the first to know about drops, new arrivals, and events.', 'skyyrose' ); ?>
			</p>
			<form class="error-404-newsletter-form" aria-label="<?php esc_attr_e( 'Newsletter signup', 'skyyrose' ); ?>" action="<?php echo esc_url( admin_url( 'admin-ajax.php' ) ); ?>" method="post">
				<?php wp_nonce_field( 'skyyrose_newsletter', 'skyyrose_newsletter_nonce' ); ?>
				<input type="hidden" name="action" value="skyyrose_newsletter_subscribe">
				<label for="error-404-newsletter-email" class="screen-reader-text">
					<?php esc_html_e( 'Email address', 'skyyrose' ); ?>
				</label>
				<input
					type="email"
					id="error-404-newsletter-email"
					name="email"
					class="error-404-newsletter-input"
					placeholder="<?php esc_attr_e( 'Enter your email', 'skyyrose' ); ?>"
					required
					autocomplete="email"
				/>
				<button type="submit" class="error-404-newsletter-btn">
					<?php esc_html_e( 'Join', 'skyyrose' ); ?>
				</button>
			</form>
		</section>

		<!-- ============================
			Dual CTA Buttons
			============================ -->
		<div class="error-404-cta-group stagger-grid">
			<a href="<?php echo esc_url( home_url( '/' ) ); ?>" class="error-404-cta error-404-cta--primary magnetic btn-sweep">
				<?php esc_html_e( 'Return Home', 'skyyrose' ); ?>
			</a>
			<a href="<?php echo esc_url( home_url( '/shop/' ) ); ?>" class="error-404-cta error-404-cta--secondary magnetic btn-border-draw">
				<?php esc_html_e( 'Continue Shopping', 'skyyrose' ); ?>
			</a>
		</div>

	</div><!-- .error-404-content -->

</main><!-- #primary -->

<?php
get_footer();
