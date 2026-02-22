<?php
/**
 * Template Name: Homepage
 *
 * The homepage template for SkyyRose Flagship.
 * Hero with floating orbs and sparkle particles, social proof bar,
 * collections showcase, "Why SkyyRose" value props, featured products,
 * Instagram feed, press mentions, brand story with pull quote,
 * testimonials, and newsletter signup.
 *
 * @package SkyyRose_Flagship
 * @since   3.0.0
 */

get_header();
?>

<main id="primary" class="site-main front-page" role="main">

	<!-- ============================================
	     HERO SECTION — 100vh with animated orbs + sparkles
	     ============================================ -->
	<section class="hero" aria-label="<?php esc_attr_e( 'Hero', 'skyyrose-flagship' ); ?>">
		<div class="hero__bg" aria-hidden="true">
			<div class="hero__orb hero__orb--1"></div>
			<div class="hero__orb hero__orb--2"></div>
			<div class="hero__orb hero__orb--3"></div>
		</div>

		<!-- Sparkle / particle layer -->
		<div class="hero__sparkles" aria-hidden="true" id="js-hero-sparkles"></div>

		<div class="hero__content">
			<span class="hero__badge">
				<svg class="hero__badge-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
					<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
				</svg>
				<?php esc_html_e( 'Oakland Luxury Streetwear', 'skyyrose-flagship' ); ?>
			</span>

			<h1 class="hero__title">
				<span class="hero__title-line"><?php esc_html_e( 'Where Love', 'skyyrose-flagship' ); ?></span>
				<span class="hero__title-line"><?php esc_html_e( 'Meets Luxury', 'skyyrose-flagship' ); ?></span>
			</h1>

			<!-- Rotating text cycling through collection names -->
			<div class="hero__rotating" aria-live="polite" aria-atomic="true">
				<span class="hero__rotating-label">
					<?php esc_html_e( 'Now Featuring:', 'skyyrose-flagship' ); ?>
				</span>
				<span class="hero__rotating-text js-rotating-text" data-texts="<?php echo esc_attr( wp_json_encode( array(
					__( 'The Black Rose Collection', 'skyyrose-flagship' ),
					__( 'The Love Hurts Collection', 'skyyrose-flagship' ),
					__( 'The Signature Collection', 'skyyrose-flagship' ),
					__( 'Limited Edition Drops', 'skyyrose-flagship' ),
				) ) ); ?>">
					<?php esc_html_e( 'The Black Rose Collection', 'skyyrose-flagship' ); ?>
				</span>
			</div>

			<p class="hero__subtitle">
				<?php esc_html_e( 'Three distinct collections, one unified vision. Born in Oakland, crafted with passion, designed for those who wear their heart on their sleeve.', 'skyyrose-flagship' ); ?>
			</p>

			<div class="hero__cta">
				<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>" class="btn btn--primary">
					<?php esc_html_e( 'Pre-Order Now', 'skyyrose-flagship' ); ?>
				</a>
				<a href="#collections" class="btn btn--outline js-smooth-scroll">
					<?php esc_html_e( 'Explore Collections', 'skyyrose-flagship' ); ?>
				</a>
			</div>
		</div>

		<div class="hero__scroll-indicator" aria-hidden="true">
			<span><?php esc_html_e( 'Scroll', 'skyyrose-flagship' ); ?></span>
		</div>
	</section>


	<!-- ============================================
	     SOCIAL PROOF BAR — Animated stat counters
	     ============================================ -->
	<section class="social-proof" aria-label="<?php esc_attr_e( 'Social proof', 'skyyrose-flagship' ); ?>">
		<div class="social-proof__inner">
			<?php
			$social_stats = array(
				array(
					'value' => 25000,
					'label' => __( 'Instagram Followers', 'skyyrose-flagship' ),
					'suffix' => '+',
					'icon'  => '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/></svg>',
				),
				array(
					'value' => 2500,
					'label' => __( 'Satisfied Customers', 'skyyrose-flagship' ),
					'suffix' => '+',
					'icon'  => '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>',
				),
				array(
					'value' => 150,
					'label' => __( 'Products Crafted', 'skyyrose-flagship' ),
					'suffix' => '+',
					'icon'  => '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>',
				),
				array(
					'value' => 3,
					'label' => __( 'Unique Collections', 'skyyrose-flagship' ),
					'suffix' => '',
					'icon'  => '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
				),
			);

			foreach ( $social_stats as $stat ) :
				?>
				<div class="social-proof__stat js-scroll-reveal">
					<span class="social-proof__icon" aria-hidden="true">
						<?php echo wp_kses_post( $stat['icon'] ); ?>
					</span>
					<span
						class="social-proof__number js-counter"
						data-target="<?php echo esc_attr( $stat['value'] ); ?>"
						data-suffix="<?php echo esc_attr( $stat['suffix'] ); ?>"
					>
						<?php echo esc_html( '0' . $stat['suffix'] ); ?>
					</span>
					<span class="social-proof__label">
						<?php echo esc_html( $stat['label'] ); ?>
					</span>
				</div>
			<?php endforeach; ?>
		</div>
	</section>


	<!-- ============================================
	     COLLECTIONS SHOWCASE — 3 collection cards
	     ============================================ -->
	<section class="collections" id="collections" aria-labelledby="collections-heading">
		<div class="collections__header section-header">
			<span class="section-header__label">
				<?php esc_html_e( 'The Collections', 'skyyrose-flagship' ); ?>
			</span>
			<h2 class="section-header__title" id="collections-heading">
				<?php esc_html_e( 'Three Stories, One Vision', 'skyyrose-flagship' ); ?>
			</h2>
			<p class="section-header__subtitle">
				<?php esc_html_e( 'Each collection represents a chapter in our story — from dark elegance to emotional depth to timeless luxury.', 'skyyrose-flagship' ); ?>
			</p>
		</div>

		<div class="collections__grid">
			<?php
			$collections = array(
				array(
					'slug'        => 'black-rose',
					'name'        => __( 'BLACK ROSE', 'skyyrose-flagship' ),
					'tagline'     => __( 'Dark elegance for the bold', 'skyyrose-flagship' ),
					'description' => __( 'Gothic romance meets modern streetwear. Metallic silver accents on midnight black — for those who find beauty in the shadows.', 'skyyrose-flagship' ),
					'class'       => 'collections__card--black-rose',
				),
				array(
					'slug'        => 'love-hurts',
					'name'        => __( 'LOVE HURTS', 'skyyrose-flagship' ),
					'tagline'     => __( 'Where emotion meets fashion', 'skyyrose-flagship' ),
					'description' => __( 'Every scar tells a story. Crimson reds and deep blacks — raw, passionate designs that wear your heart on your sleeve.', 'skyyrose-flagship' ),
					'class'       => 'collections__card--love-hurts',
				),
				array(
					'slug'        => 'signature',
					'name'        => __( 'SIGNATURE', 'skyyrose-flagship' ),
					'tagline'     => __( 'Timeless luxury essentials', 'skyyrose-flagship' ),
					'description' => __( 'Rose gold meets gold in elevated everyday luxury. Premium materials, expert construction — the art of everyday excellence.', 'skyyrose-flagship' ),
					'class'       => 'collections__card--signature',
				),
			);

			foreach ( $collections as $collection ) :
				// Try to get the WooCommerce product category link.
				$collection_url = home_url( '/collection/' . $collection['slug'] . '/' );

				if ( class_exists( 'WooCommerce' ) ) {
					$term = get_term_by( 'slug', $collection['slug'], 'product_cat' );
					if ( $term && ! is_wp_error( $term ) ) {
						$term_link = get_term_link( $term );
						if ( ! is_wp_error( $term_link ) ) {
							$collection_url = $term_link;
						}
					}
				}
				?>
				<div class="collections__card <?php echo esc_attr( $collection['class'] ); ?> js-scroll-reveal">
					<div class="collections__card-bg" aria-hidden="true"></div>
					<div class="collections__card-content">
						<h3 class="collections__card-name">
							<?php echo esc_html( $collection['name'] ); ?>
						</h3>
						<p class="collections__card-tagline">
							<?php echo esc_html( $collection['tagline'] ); ?>
						</p>
						<p class="collections__card-description">
							<?php echo esc_html( $collection['description'] ); ?>
						</p>
						<a href="<?php echo esc_url( $collection_url ); ?>" class="btn btn--collection">
							<?php esc_html_e( 'Explore Collection', 'skyyrose-flagship' ); ?>
							<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
								<path d="M5 12h14M12 5l7 7-7 7"/>
							</svg>
						</a>
					</div>
				</div>
			<?php endforeach; ?>
		</div>
	</section>


	<!-- ============================================
	     WHY SKYYROSE — 4 value proposition cards
	     ============================================ -->
	<section class="why-skyyrose" aria-labelledby="why-heading">
		<div class="why-skyyrose__header section-header">
			<span class="section-header__label">
				<?php esc_html_e( 'The Difference', 'skyyrose-flagship' ); ?>
			</span>
			<h2 class="section-header__title" id="why-heading">
				<?php esc_html_e( 'Why SkyyRose', 'skyyrose-flagship' ); ?>
			</h2>
			<p class="section-header__subtitle">
				<?php esc_html_e( 'More than a brand. A movement built on authenticity, quality, and community.', 'skyyrose-flagship' ); ?>
			</p>
		</div>

		<div class="why-skyyrose__grid">
			<?php
			$value_props = array(
				array(
					'icon'        => '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/><path d="m9 12 2 2 4-4"/></svg>',
					'title'       => __( 'Handcrafted Quality', 'skyyrose-flagship' ),
					'description' => __( 'Every piece tells a story of meticulous craftsmanship. From embroidered details to silicone appliques, each garment is a work of art.', 'skyyrose-flagship' ),
				),
				array(
					'icon'        => '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
					'title'       => __( 'Oakland Roots', 'skyyrose-flagship' ),
					'description' => __( 'Born in Oakland, designed for the world. Our streetwear carries the authenticity and grit of the Bay Area in every stitch.', 'skyyrose-flagship' ),
				),
				array(
					'icon'        => '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>',
					'title'       => __( 'Limited Editions', 'skyyrose-flagship' ),
					'description' => __( 'Exclusive drops that won\'t last forever. When they\'re gone, they\'re gone. Own a piece of something truly rare.', 'skyyrose-flagship' ),
				),
				array(
					'icon'        => '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
					'title'       => __( 'Community First', 'skyyrose-flagship' ),
					'description' => __( 'Building more than a brand, building a movement. The SkyyRose family is a community of dreamers, creators, and believers.', 'skyyrose-flagship' ),
				),
			);

			foreach ( $value_props as $index => $prop ) :
				?>
				<div class="why-skyyrose__card js-scroll-reveal">
					<div class="why-skyyrose__card-glow" aria-hidden="true"></div>
					<span class="why-skyyrose__card-number" aria-hidden="true">
						<?php echo esc_html( str_pad( $index + 1, 2, '0', STR_PAD_LEFT ) ); ?>
					</span>
					<span class="why-skyyrose__card-icon">
						<?php echo wp_kses_post( $prop['icon'] ); ?>
					</span>
					<h3 class="why-skyyrose__card-title">
						<?php echo esc_html( $prop['title'] ); ?>
					</h3>
					<p class="why-skyyrose__card-text">
						<?php echo esc_html( $prop['description'] ); ?>
					</p>
				</div>
			<?php endforeach; ?>
		</div>
	</section>


	<!-- ============================================
	     FEATURED PRODUCTS — WooCommerce product grid
	     ============================================ -->
	<section class="featured" aria-labelledby="featured-heading">
		<div class="featured__header section-header">
			<span class="section-header__label">
				<?php esc_html_e( 'Featured', 'skyyrose-flagship' ); ?>
			</span>
			<h2 class="section-header__title" id="featured-heading">
				<?php esc_html_e( 'New Arrivals', 'skyyrose-flagship' ); ?>
			</h2>
			<p class="section-header__subtitle">
				<?php esc_html_e( 'The latest additions to our collections, each piece crafted with intention.', 'skyyrose-flagship' ); ?>
			</p>
		</div>

		<div class="featured__grid">
			<?php
			if ( class_exists( 'WooCommerce' ) ) :

				$featured_args = array(
					'post_type'      => 'product',
					'posts_per_page' => 4,
					'post_status'    => 'publish',
					'meta_key'       => 'total_sales',
					'orderby'        => 'meta_value_num',
					'order'          => 'DESC',
					'tax_query'      => array(
						array(
							'taxonomy' => 'product_visibility',
							'field'    => 'name',
							'terms'    => 'featured',
						),
					),
				);

				$featured_query = new WP_Query( $featured_args );

				// Fallback: if no featured products, get latest products.
				if ( ! $featured_query->have_posts() ) {
					$featured_args = array(
						'post_type'      => 'product',
						'posts_per_page' => 4,
						'post_status'    => 'publish',
						'orderby'        => 'date',
						'order'          => 'DESC',
					);
					$featured_query = new WP_Query( $featured_args );
				}

				if ( $featured_query->have_posts() ) :
					while ( $featured_query->have_posts() ) :
						$featured_query->the_post();
						global $product;

						if ( ! $product ) {
							continue;
						}

						// Determine badge type.
						$badge_text  = '';
						$badge_class = '';
						if ( $product->is_on_sale() ) {
							$badge_text  = __( 'Sale', 'skyyrose-flagship' );
							$badge_class = 'product-card__badge--sale';
						} elseif ( $product->get_date_created() ) {
							$created   = $product->get_date_created()->getTimestamp();
							$two_weeks = strtotime( '-14 days' );
							if ( $created > $two_weeks ) {
								$badge_text  = __( 'New', 'skyyrose-flagship' );
								$badge_class = 'product-card__badge--new';
							}
						}
						if ( ! $product->is_in_stock() ) {
							$badge_text  = __( 'Sold Out', 'skyyrose-flagship' );
							$badge_class = 'product-card__badge--sold-out';
						}
						if ( $product->managing_stock() && $product->get_stock_quantity() <= 5 && $product->get_stock_quantity() > 0 ) {
							$badge_text  = __( 'Limited', 'skyyrose-flagship' );
							$badge_class = 'product-card__badge--limited';
						}

						// Get collection / category.
						$categories     = get_the_terms( get_the_ID(), 'product_cat' );
						$collection_name = '';
						if ( $categories && ! is_wp_error( $categories ) ) {
							$collection_name = $categories[0]->name;
						}

						// Get average rating.
						$average_rating = $product->get_average_rating();
						$review_count   = $product->get_review_count();

						// Get short description.
						$short_desc = $product->get_short_description();
						?>
						<article class="product-card js-scroll-reveal" aria-label="<?php echo esc_attr( get_the_title() ); ?>">
							<?php if ( $badge_text ) : ?>
								<span class="product-card__badge <?php echo esc_attr( $badge_class ); ?>">
									<?php echo esc_html( $badge_text ); ?>
								</span>
							<?php endif; ?>

							<a href="<?php the_permalink(); ?>" class="product-card__image-link">
								<div class="product-card__image">
									<?php
									if ( has_post_thumbnail() ) {
										the_post_thumbnail(
											'woocommerce_thumbnail',
											array(
												'class'   => 'product-card__img',
												'loading' => 'lazy',
												'alt'     => esc_attr( get_the_title() ),
											)
										);
									} else {
										?>
										<div class="product-card__placeholder" aria-hidden="true"></div>
										<?php
									}
									?>
								</div>
							</a>

							<div class="product-card__actions" aria-label="<?php esc_attr_e( 'Quick actions', 'skyyrose-flagship' ); ?>">
								<a href="<?php the_permalink(); ?>" class="product-card__action-btn" aria-label="<?php esc_attr_e( 'Quick View', 'skyyrose-flagship' ); ?>" title="<?php esc_attr_e( 'Quick View', 'skyyrose-flagship' ); ?>">
									<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
										<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
										<circle cx="12" cy="12" r="3"/>
									</svg>
								</a>
								<button class="product-card__action-btn js-wishlist-btn" data-product-id="<?php echo esc_attr( get_the_ID() ); ?>" aria-label="<?php esc_attr_e( 'Add to Wishlist', 'skyyrose-flagship' ); ?>" title="<?php esc_attr_e( 'Add to Wishlist', 'skyyrose-flagship' ); ?>" type="button">
									<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
										<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
									</svg>
								</button>
								<?php if ( $product->is_in_stock() ) : ?>
									<button class="product-card__action-btn js-add-to-cart" data-product-id="<?php echo esc_attr( get_the_ID() ); ?>" aria-label="<?php esc_attr_e( 'Add to Cart', 'skyyrose-flagship' ); ?>" title="<?php esc_attr_e( 'Add to Cart', 'skyyrose-flagship' ); ?>" type="button">
										<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
											<path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/>
											<path d="M3 6h18"/>
											<path d="M16 10a4 4 0 0 1-8 0"/>
										</svg>
									</button>
								<?php endif; ?>
							</div>

							<div class="product-card__info">
								<?php if ( $collection_name ) : ?>
									<p class="product-card__collection">
										<?php echo esc_html( $collection_name ); ?>
									</p>
								<?php endif; ?>
								<h3 class="product-card__name">
									<a href="<?php the_permalink(); ?>">
										<?php the_title(); ?>
									</a>
								</h3>

								<?php if ( $short_desc ) : ?>
									<p class="product-card__desc">
										<?php echo esc_html( wp_trim_words( wp_strip_all_tags( $short_desc ), 15, '...' ) ); ?>
									</p>
								<?php endif; ?>

								<?php if ( $average_rating > 0 ) : ?>
									<div class="product-card__rating" aria-label="<?php echo esc_attr( sprintf( __( 'Rated %s out of 5', 'skyyrose-flagship' ), $average_rating ) ); ?>">
										<?php
										for ( $i = 1; $i <= 5; $i++ ) :
											$star_class = $i <= round( $average_rating ) ? 'product-card__star--filled' : 'product-card__star--empty';
											?>
											<svg class="product-card__star <?php echo esc_attr( $star_class ); ?>" width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false">
												<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
											</svg>
										<?php endfor; ?>
										<span class="product-card__review-count">
											<?php
											/* translators: %d: number of reviews */
											echo esc_html( sprintf( _n( '(%d)', '(%d)', $review_count, 'skyyrose-flagship' ), $review_count ) );
											?>
										</span>
									</div>
								<?php endif; ?>

								<div class="product-card__price-row">
									<p class="product-card__price">
										<?php echo wp_kses_post( $product->get_price_html() ); ?>
									</p>
								</div>

								<div class="product-card__buttons">
									<a href="<?php the_permalink(); ?>" class="btn btn--sm btn--primary">
										<?php esc_html_e( 'Shop Now', 'skyyrose-flagship' ); ?>
									</a>
									<a href="<?php the_permalink(); ?>" class="btn btn--sm btn--ghost">
										<?php esc_html_e( 'Quick View', 'skyyrose-flagship' ); ?>
									</a>
								</div>
							</div>
						</article>
					<?php endwhile; ?>
					<?php wp_reset_postdata(); ?>

				<?php else : ?>
					<!-- Fallback: static product cards when no WooCommerce products exist -->
					<?php
					$fallback_products = array(
						array(
							'badge'      => 'New',
							'badge_cls'  => 'product-card__badge--new',
							'collection' => 'Black Rose',
							'name'       => 'BLACK Rose Crewneck',
							'desc'       => 'Premium heavyweight crewneck with embroidered metallic silver rose detailing on chest.',
							'price'      => '$120',
							'rating'     => 5,
							'reviews'    => 24,
							'sku'        => 'br-001',
						),
						array(
							'badge'      => 'Limited',
							'badge_cls'  => 'product-card__badge--limited',
							'collection' => 'Love Hurts',
							'name'       => 'The Fannie',
							'desc'       => 'Our signature piece honoring the Hurts family name. Crimson embroidery on premium black cotton.',
							'price'      => '$145',
							'rating'     => 5,
							'reviews'    => 18,
							'sku'        => 'lh-001',
						),
						array(
							'badge'      => '',
							'badge_cls'  => '',
							'collection' => 'Signature',
							'name'       => 'The Bay Set',
							'desc'       => 'Complete matching set in rose gold tones. Hoodie and joggers crafted from premium French terry.',
							'price'      => '$295',
							'sale_price' => '',
							'rating'     => 4,
							'reviews'    => 31,
							'sku'        => 'sg-001',
						),
						array(
							'badge'      => 'New',
							'badge_cls'  => 'product-card__badge--new',
							'collection' => 'Black Rose',
							'name'       => 'BLACK Rose Hoodie',
							'desc'       => 'Heavyweight pullover hoodie with oversized silicone rose applique and silver-tipped drawstrings.',
							'price'      => '$165',
							'rating'     => 5,
							'reviews'    => 42,
							'sku'        => 'br-004',
						),
					);

					foreach ( $fallback_products as $fp ) :
						?>
						<article class="product-card js-scroll-reveal" aria-label="<?php echo esc_attr( $fp['name'] ); ?>">
							<?php if ( $fp['badge'] ) : ?>
								<span class="product-card__badge <?php echo esc_attr( $fp['badge_cls'] ); ?>">
									<?php echo esc_html( $fp['badge'] ); ?>
								</span>
							<?php endif; ?>

							<a href="<?php echo esc_url( home_url( '/product/' . sanitize_title( $fp['name'] ) . '/' ) ); ?>" class="product-card__image-link">
								<div class="product-card__image">
									<div class="product-card__placeholder product-card__placeholder--<?php echo esc_attr( $fp['sku'] ); ?>" aria-hidden="true"></div>
								</div>
							</a>

							<div class="product-card__actions" aria-label="<?php esc_attr_e( 'Quick actions', 'skyyrose-flagship' ); ?>">
								<button class="product-card__action-btn" aria-label="<?php esc_attr_e( 'Quick View', 'skyyrose-flagship' ); ?>" type="button">
									<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
										<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
										<circle cx="12" cy="12" r="3"/>
									</svg>
								</button>
								<button class="product-card__action-btn" aria-label="<?php esc_attr_e( 'Add to Wishlist', 'skyyrose-flagship' ); ?>" type="button">
									<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
										<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
									</svg>
								</button>
								<button class="product-card__action-btn" aria-label="<?php esc_attr_e( 'Add to Cart', 'skyyrose-flagship' ); ?>" type="button">
									<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
										<path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/>
										<path d="M3 6h18"/>
										<path d="M16 10a4 4 0 0 1-8 0"/>
									</svg>
								</button>
							</div>

							<div class="product-card__info">
								<p class="product-card__collection">
									<?php echo esc_html( $fp['collection'] ); ?>
								</p>
								<h3 class="product-card__name">
									<a href="<?php echo esc_url( home_url( '/product/' . sanitize_title( $fp['name'] ) . '/' ) ); ?>">
										<?php echo esc_html( $fp['name'] ); ?>
									</a>
								</h3>
								<p class="product-card__desc">
									<?php echo esc_html( $fp['desc'] ); ?>
								</p>
								<?php if ( ! empty( $fp['rating'] ) ) : ?>
									<div class="product-card__rating" aria-label="<?php echo esc_attr( sprintf( __( 'Rated %d out of 5', 'skyyrose-flagship' ), $fp['rating'] ) ); ?>">
										<?php
										for ( $i = 1; $i <= 5; $i++ ) :
											$star_class = $i <= $fp['rating'] ? 'product-card__star--filled' : 'product-card__star--empty';
											?>
											<svg class="product-card__star <?php echo esc_attr( $star_class ); ?>" width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false">
												<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
											</svg>
										<?php endfor; ?>
										<span class="product-card__review-count">
											<?php echo esc_html( '(' . $fp['reviews'] . ')' ); ?>
										</span>
									</div>
								<?php endif; ?>
								<p class="product-card__price">
									<?php echo esc_html( $fp['price'] ); ?>
								</p>
								<div class="product-card__buttons">
									<a href="<?php echo esc_url( home_url( '/product/' . sanitize_title( $fp['name'] ) . '/' ) ); ?>" class="btn btn--sm btn--primary">
										<?php esc_html_e( 'Shop Now', 'skyyrose-flagship' ); ?>
									</a>
									<a href="<?php echo esc_url( home_url( '/product/' . sanitize_title( $fp['name'] ) . '/' ) ); ?>" class="btn btn--sm btn--ghost">
										<?php esc_html_e( 'Quick View', 'skyyrose-flagship' ); ?>
									</a>
								</div>
							</div>
						</article>
					<?php endforeach; ?>
				<?php endif; ?>

			<?php else : ?>
				<!-- WooCommerce not active: static fallback -->
				<?php
				$static_products = array(
					array(
						'badge'      => 'New',
						'badge_cls'  => 'product-card__badge--new',
						'collection' => 'Black Rose',
						'name'       => 'BLACK Rose Crewneck',
						'desc'       => 'Premium heavyweight crewneck with embroidered metallic silver rose detailing.',
						'price'      => '$120',
						'rating'     => 5,
						'reviews'    => 24,
					),
					array(
						'badge'      => 'Limited',
						'badge_cls'  => 'product-card__badge--limited',
						'collection' => 'Love Hurts',
						'name'       => 'The Fannie',
						'desc'       => 'Signature piece honoring the Hurts family name. Crimson embroidery on black cotton.',
						'price'      => '$145',
						'rating'     => 5,
						'reviews'    => 18,
					),
					array(
						'badge'      => '',
						'badge_cls'  => '',
						'collection' => 'Signature',
						'name'       => 'The Bay Set',
						'desc'       => 'Complete matching hoodie and jogger set in rose gold tones. Premium French terry.',
						'price'      => '$295',
						'rating'     => 4,
						'reviews'    => 31,
					),
					array(
						'badge'      => 'New',
						'badge_cls'  => 'product-card__badge--new',
						'collection' => 'Black Rose',
						'name'       => 'BLACK Rose Hoodie',
						'desc'       => 'Heavyweight pullover with oversized silicone rose applique and silver drawstrings.',
						'price'      => '$165',
						'rating'     => 5,
						'reviews'    => 42,
					),
				);

				foreach ( $static_products as $sp ) :
					?>
					<article class="product-card js-scroll-reveal" aria-label="<?php echo esc_attr( $sp['name'] ); ?>">
						<?php if ( $sp['badge'] ) : ?>
							<span class="product-card__badge <?php echo esc_attr( $sp['badge_cls'] ); ?>">
								<?php echo esc_html( $sp['badge'] ); ?>
							</span>
						<?php endif; ?>

						<div class="product-card__image-link">
							<div class="product-card__image">
								<div class="product-card__placeholder" aria-hidden="true"></div>
							</div>
						</div>

						<div class="product-card__info">
							<p class="product-card__collection">
								<?php echo esc_html( $sp['collection'] ); ?>
							</p>
							<h3 class="product-card__name">
								<?php echo esc_html( $sp['name'] ); ?>
							</h3>
							<p class="product-card__desc">
								<?php echo esc_html( $sp['desc'] ); ?>
							</p>
							<?php if ( ! empty( $sp['rating'] ) ) : ?>
								<div class="product-card__rating" aria-label="<?php echo esc_attr( sprintf( __( 'Rated %d out of 5', 'skyyrose-flagship' ), $sp['rating'] ) ); ?>">
									<?php
									for ( $i = 1; $i <= 5; $i++ ) :
										$star_class = $i <= $sp['rating'] ? 'product-card__star--filled' : 'product-card__star--empty';
										?>
										<svg class="product-card__star <?php echo esc_attr( $star_class ); ?>" width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false">
											<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
										</svg>
									<?php endfor; ?>
									<span class="product-card__review-count">
										<?php echo esc_html( '(' . $sp['reviews'] . ')' ); ?>
									</span>
								</div>
							<?php endif; ?>
							<p class="product-card__price">
								<?php echo esc_html( $sp['price'] ); ?>
							</p>
						</div>
					</article>
				<?php endforeach; ?>
			<?php endif; ?>
		</div>
	</section>


	<!-- ============================================
	     INSTAGRAM FEED — 6-square grid with hover
	     ============================================ -->
	<section class="instagram-feed" aria-labelledby="instagram-heading">
		<div class="instagram-feed__header section-header">
			<span class="section-header__label">
				<?php esc_html_e( 'Follow the Movement', 'skyyrose-flagship' ); ?>
			</span>
			<h2 class="section-header__title" id="instagram-heading">
				<?php esc_html_e( '@skyyrose', 'skyyrose-flagship' ); ?>
			</h2>
			<p class="section-header__subtitle">
				<?php esc_html_e( 'Join 25K+ followers for behind-the-scenes content, new drops, and community highlights.', 'skyyrose-flagship' ); ?>
			</p>
		</div>

		<div class="instagram-feed__grid">
			<?php
			$insta_posts = array(
				array(
					'alt'      => __( 'Black Rose collection photoshoot', 'skyyrose-flagship' ),
					'likes'    => '2.4K',
					'comments' => '186',
					'gradient' => 'linear-gradient(135deg, #1a0000, #3d0000)',
				),
				array(
					'alt'      => __( 'Love Hurts varsity jacket detail', 'skyyrose-flagship' ),
					'likes'    => '1.8K',
					'comments' => '142',
					'gradient' => 'linear-gradient(135deg, #2d1a1d, #4a2a30)',
				),
				array(
					'alt'      => __( 'Oakland skyline with SkyyRose gear', 'skyyrose-flagship' ),
					'likes'    => '3.1K',
					'comments' => '234',
					'gradient' => 'linear-gradient(135deg, #0a0a14, #1a1a2e)',
				),
				array(
					'alt'      => __( 'Signature collection behind the scenes', 'skyyrose-flagship' ),
					'likes'    => '2.7K',
					'comments' => '198',
					'gradient' => 'linear-gradient(135deg, #1a1810, #2d2820)',
				),
				array(
					'alt'      => __( 'Customer wearing BLACK Rose Hoodie', 'skyyrose-flagship' ),
					'likes'    => '4.2K',
					'comments' => '312',
					'gradient' => 'linear-gradient(135deg, #1a0808, #2a0a0a)',
				),
				array(
					'alt'      => __( 'SkyyRose pop-up event in Oakland', 'skyyrose-flagship' ),
					'likes'    => '5.1K',
					'comments' => '428',
					'gradient' => 'linear-gradient(135deg, #140a10, #2a1420)',
				),
			);

			foreach ( $insta_posts as $post ) :
				?>
				<a
					href="<?php echo esc_url( 'https://www.instagram.com/skyyrose/' ); ?>"
					class="instagram-feed__item js-scroll-reveal"
					target="_blank"
					rel="noopener noreferrer"
					aria-label="<?php echo esc_attr( $post['alt'] ); ?>"
				>
					<div class="instagram-feed__image" style="background: <?php echo esc_attr( $post['gradient'] ); ?>;" aria-hidden="true">
						<svg class="instagram-feed__placeholder-icon" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" opacity="0.2" aria-hidden="true" focusable="false">
							<rect x="2" y="2" width="20" height="20" rx="5" ry="5"/>
							<path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/>
							<line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/>
						</svg>
					</div>
					<div class="instagram-feed__overlay" aria-hidden="true">
						<span class="instagram-feed__stat">
							<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false">
								<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
							</svg>
							<?php echo esc_html( $post['likes'] ); ?>
						</span>
						<span class="instagram-feed__stat">
							<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false">
								<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
							</svg>
							<?php echo esc_html( $post['comments'] ); ?>
						</span>
					</div>
				</a>
			<?php endforeach; ?>
		</div>

		<div class="instagram-feed__cta">
			<a href="<?php echo esc_url( 'https://www.instagram.com/skyyrose/' ); ?>" class="btn btn--outline" target="_blank" rel="noopener noreferrer">
				<?php esc_html_e( 'Follow @skyyrose', 'skyyrose-flagship' ); ?>
			</a>
		</div>
	</section>


	<!-- ============================================
	     PRESS / AS SEEN IN — Media mention logos
	     ============================================ -->
	<section class="press" aria-label="<?php esc_attr_e( 'As seen in', 'skyyrose-flagship' ); ?>">
		<div class="press__inner">
			<p class="press__label">
				<?php esc_html_e( 'As Seen In', 'skyyrose-flagship' ); ?>
			</p>
			<div class="press__logos">
				<?php
				$press_logos = array(
					__( 'Complex', 'skyyrose-flagship' ),
					__( 'Hypebeast', 'skyyrose-flagship' ),
					__( 'GQ', 'skyyrose-flagship' ),
					__( 'Vogue', 'skyyrose-flagship' ),
					__( 'Highsnobiety', 'skyyrose-flagship' ),
					__( 'SSENSE', 'skyyrose-flagship' ),
				);

				foreach ( $press_logos as $logo_name ) :
					?>
					<span class="press__logo" aria-label="<?php echo esc_attr( $logo_name ); ?>">
						<?php echo esc_html( $logo_name ); ?>
					</span>
				<?php endforeach; ?>
			</div>
		</div>
	</section>


	<!-- ============================================
	     BRAND STORY — 2-column layout with pull quote + stats
	     ============================================ -->
	<section class="brand-story" aria-labelledby="brand-story-heading">
		<div class="brand-story__bg" aria-hidden="true"></div>

		<div class="brand-story__content">
			<div class="brand-story__text js-scroll-reveal">
				<span class="section-header__label">
					<?php esc_html_e( 'Our Story', 'skyyrose-flagship' ); ?>
				</span>
				<h2 class="brand-story__heading" id="brand-story-heading">
					<?php
					echo wp_kses(
						__( 'Born in Oakland,<br>Crafted with Love', 'skyyrose-flagship' ),
						array( 'br' => array() )
					);
					?>
				</h2>

				<blockquote class="brand-story__pullquote">
					<?php esc_html_e( 'We don\'t just make clothes. We make statements. Every stitch carries the weight of our story, and every piece invites you to write yours.', 'skyyrose-flagship' ); ?>
				</blockquote>

				<p>
					<?php esc_html_e( 'SkyyRose emerged from the vibrant streets of Oakland, where authenticity isn\'t just valued — it\'s essential. Founded with a vision to bridge the gap between street culture and luxury fashion, we create pieces that tell stories.', 'skyyrose-flagship' ); ?>
				</p>
				<p>
					<?php esc_html_e( 'The name "Love Hurts" carries deep meaning — it\'s our founder\'s family name, Hurts, woven into the fabric of every piece. This personal connection infuses each collection with genuine emotion and uncompromising quality.', 'skyyrose-flagship' ); ?>
				</p>

				<!-- Brand statistics -->
				<div class="brand-story__stats">
					<?php
					$brand_stats = array(
						array(
							'number' => __( '2019', 'skyyrose-flagship' ),
							'label'  => __( 'Year Founded', 'skyyrose-flagship' ),
						),
						array(
							'number' => __( '28+', 'skyyrose-flagship' ),
							'label'  => __( 'Products Designed', 'skyyrose-flagship' ),
						),
						array(
							'number' => __( '3', 'skyyrose-flagship' ),
							'label'  => __( 'Collections', 'skyyrose-flagship' ),
						),
						array(
							'number' => __( '1', 'skyyrose-flagship' ),
							'label'  => __( 'Vision', 'skyyrose-flagship' ),
						),
					);

					foreach ( $brand_stats as $bstat ) :
						?>
						<div class="brand-story__stat">
							<span class="brand-story__stat-number">
								<?php echo esc_html( $bstat['number'] ); ?>
							</span>
							<span class="brand-story__stat-label">
								<?php echo esc_html( $bstat['label'] ); ?>
							</span>
						</div>
					<?php endforeach; ?>
				</div>

				<a href="<?php echo esc_url( home_url( '/about/' ) ); ?>" class="btn btn--outline">
					<?php esc_html_e( 'Learn More', 'skyyrose-flagship' ); ?>
				</a>
			</div>

			<div class="brand-story__visual js-scroll-reveal" aria-hidden="true">
				<?php
				// Use a curated brand image if available via the customizer.
				$brand_story_image_id = get_theme_mod( 'skyyrose_brand_story_image', 0 );

				if ( $brand_story_image_id ) {
					echo wp_get_attachment_image(
						$brand_story_image_id,
						'large',
						false,
						array(
							'class'   => 'brand-story__image',
							'loading' => 'lazy',
							'alt'     => esc_attr__( 'SkyyRose brand story', 'skyyrose-flagship' ),
						)
					);
				}
				?>
			</div>
		</div>
	</section>


	<!-- ============================================
	     TESTIMONIALS — 3 customer review cards
	     ============================================ -->
	<section class="testimonials" aria-labelledby="testimonials-heading">
		<div class="testimonials__header section-header">
			<span class="section-header__label">
				<?php esc_html_e( 'Real Talk', 'skyyrose-flagship' ); ?>
			</span>
			<h2 class="section-header__title" id="testimonials-heading">
				<?php esc_html_e( 'What the Family Says', 'skyyrose-flagship' ); ?>
			</h2>
			<p class="section-header__subtitle">
				<?php esc_html_e( 'Don\'t take our word for it. Hear from the SkyyRose community.', 'skyyrose-flagship' ); ?>
			</p>
		</div>

		<div class="testimonials__grid">
			<?php
			$testimonials = array(
				array(
					'quote'    => __( 'The quality is insane. I\'ve bought from a lot of streetwear brands and nothing comes close to the weight and feel of the Black Rose Hoodie. This is real luxury.', 'skyyrose-flagship' ),
					'name'     => __( 'Marcus T.', 'skyyrose-flagship' ),
					'location' => __( 'Oakland, CA', 'skyyrose-flagship' ),
					'product'  => __( 'BLACK Rose Hoodie', 'skyyrose-flagship' ),
					'rating'   => 5,
					'verified' => true,
				),
				array(
					'quote'    => __( 'Wore The Fannie to a gallery opening and got stopped five times. People wanted to know the brand. SkyyRose is about to blow up — get in now.', 'skyyrose-flagship' ),
					'name'     => __( 'Jasmine R.', 'skyyrose-flagship' ),
					'location' => __( 'Los Angeles, CA', 'skyyrose-flagship' ),
					'product'  => __( 'The Fannie', 'skyyrose-flagship' ),
					'rating'   => 5,
					'verified' => true,
				),
				array(
					'quote'    => __( 'The Bay Set is my go-to for everything. Airport fits, studio sessions, date nights. The rose gold tones hit different. Worth every penny.', 'skyyrose-flagship' ),
					'name'     => __( 'Devon K.', 'skyyrose-flagship' ),
					'location' => __( 'San Francisco, CA', 'skyyrose-flagship' ),
					'product'  => __( 'The Bay Set', 'skyyrose-flagship' ),
					'rating'   => 5,
					'verified' => true,
				),
			);

			foreach ( $testimonials as $testimonial ) :
				?>
				<div class="testimonials__card js-scroll-reveal">
					<div class="testimonials__card-inner">
						<!-- Stars -->
						<div class="testimonials__stars" aria-label="<?php echo esc_attr( sprintf( __( 'Rated %d out of 5', 'skyyrose-flagship' ), $testimonial['rating'] ) ); ?>">
							<?php for ( $i = 0; $i < $testimonial['rating']; $i++ ) : ?>
								<svg class="testimonials__star" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false">
									<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
								</svg>
							<?php endfor; ?>
						</div>

						<!-- Quote -->
						<blockquote class="testimonials__quote">
							<?php echo esc_html( $testimonial['quote'] ); ?>
						</blockquote>

						<!-- Attribution -->
						<div class="testimonials__author">
							<div class="testimonials__avatar" aria-hidden="true">
								<?php echo esc_html( mb_substr( $testimonial['name'], 0, 1 ) ); ?>
							</div>
							<div class="testimonials__author-info">
								<span class="testimonials__name">
									<?php echo esc_html( $testimonial['name'] ); ?>
								</span>
								<span class="testimonials__location">
									<?php echo esc_html( $testimonial['location'] ); ?>
								</span>
							</div>
							<?php if ( $testimonial['verified'] ) : ?>
								<span class="testimonials__verified" title="<?php esc_attr_e( 'Verified Purchase', 'skyyrose-flagship' ); ?>">
									<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false">
										<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
										<polyline points="22 4 12 14.01 9 11.01" fill="none" stroke="currentColor" stroke-width="2"/>
									</svg>
									<?php esc_html_e( 'Verified', 'skyyrose-flagship' ); ?>
								</span>
							<?php endif; ?>
						</div>

						<!-- Product purchased -->
						<p class="testimonials__product">
							<?php
							/* translators: %s: product name */
							echo esc_html( sprintf( __( 'Purchased: %s', 'skyyrose-flagship' ), $testimonial['product'] ) );
							?>
						</p>
					</div>
				</div>
			<?php endforeach; ?>
		</div>
	</section>


	<!-- ============================================
	     NEWSLETTER — Email signup with incentive
	     ============================================ -->
	<section class="newsletter" aria-labelledby="newsletter-heading">
		<div class="newsletter__content">
			<span class="section-header__label">
				<?php esc_html_e( 'Stay Connected', 'skyyrose-flagship' ); ?>
			</span>
			<h2 class="newsletter__heading" id="newsletter-heading">
				<?php esc_html_e( 'Join the SkyyRose Family', 'skyyrose-flagship' ); ?>
			</h2>
			<p class="newsletter__incentive">
				<?php esc_html_e( 'Get 15% off your first order', 'skyyrose-flagship' ); ?>
			</p>
			<p class="newsletter__text">
				<?php esc_html_e( 'Be the first to know about new drops, exclusive offers, and behind-the-scenes content. No spam, ever. Just luxury in your inbox.', 'skyyrose-flagship' ); ?>
			</p>

			<form class="newsletter__form js-newsletter-form" method="post" action="<?php echo esc_url( admin_url( 'admin-ajax.php' ) ); ?>" aria-label="<?php esc_attr_e( 'Newsletter signup', 'skyyrose-flagship' ); ?>">
				<?php wp_nonce_field( 'skyyrose_newsletter', 'skyyrose_newsletter_nonce' ); ?>
				<input type="hidden" name="action" value="skyyrose_newsletter_subscribe">

				<label for="newsletter-email" class="screen-reader-text">
					<?php esc_html_e( 'Email address', 'skyyrose-flagship' ); ?>
				</label>
				<input
					type="email"
					id="newsletter-email"
					name="newsletter_email"
					class="newsletter__input"
					placeholder="<?php esc_attr_e( 'Enter your email', 'skyyrose-flagship' ); ?>"
					required
					autocomplete="email"
				>
				<button type="submit" class="btn btn--primary newsletter__submit">
					<?php esc_html_e( 'Subscribe', 'skyyrose-flagship' ); ?>
				</button>
			</form>

			<div class="newsletter__feedback" aria-live="polite" role="status"></div>

			<p class="newsletter__privacy">
				<?php
				echo wp_kses(
					sprintf(
						/* translators: %s: URL to privacy policy page */
						__( 'By subscribing, you agree to our <a href="%s">Privacy Policy</a>. Unsubscribe anytime.', 'skyyrose-flagship' ),
						esc_url( home_url( '/privacy-policy/' ) )
					),
					array(
						'a' => array( 'href' => array() ),
					)
				);
				?>
			</p>
		</div>
	</section>

</main><!-- #primary -->

<?php
get_footer();
