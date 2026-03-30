<?php
/**
 * Search Results Page — The Skyy Rose Collection
 *
 * Dark luxury search results with product-first layout (holo cards),
 * re-search form, content list, and branded empty state with collection
 * quick-links and suggestions.
 *
 * @package SkyyRose_Flagship
 * @since   5.3.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

get_header();

$skyyrose_search_query = get_search_query();
$skyyrose_has_wc       = class_exists( 'WooCommerce' );

// -------------------------------------------------------------------------
// Product search (separate WP_Query for WooCommerce products).
// -------------------------------------------------------------------------
$skyyrose_product_results = null;
$skyyrose_product_count   = 0;

if ( $skyyrose_has_wc && ! empty( $skyyrose_search_query ) ) {
	$skyyrose_product_results = new WP_Query(
		array(
			'post_type'      => 'product',
			'post_status'    => 'publish',
			's'              => $skyyrose_search_query,
			'posts_per_page' => 12,
		)
	);
	$skyyrose_product_count = $skyyrose_product_results->found_posts;
}

// Total count: products + main loop (non-product content).
$skyyrose_content_count = 0;
if ( have_posts() ) {
	global $wp_query;
	$skyyrose_content_count = $wp_query->found_posts;
}

// Collection data for empty state (shared with 404.php pattern).
$skyyrose_collections = array(
	array(
		'slug'        => 'black-rose',
		'label'       => __( 'Black Rose', 'skyyrose-flagship' ),
		'accent'      => '#C0C0C0',
		'glow'        => 'rgba(192, 192, 192, 0.3)',
		'description' => __( 'Gothic elegance, dark romance', 'skyyrose-flagship' ),
	),
	array(
		'slug'        => 'love-hurts',
		'label'       => __( 'Love Hurts', 'skyyrose-flagship' ),
		'accent'      => '#DC143C',
		'glow'        => 'rgba(220, 20, 60, 0.3)',
		'description' => __( 'Dramatic, passionate, fearless', 'skyyrose-flagship' ),
	),
	array(
		'slug'        => 'signature',
		'label'       => __( 'Signature', 'skyyrose-flagship' ),
		'accent'      => '#D4AF37',
		'glow'        => 'rgba(212, 175, 55, 0.3)',
		'description' => __( 'Elevated, confident, refined', 'skyyrose-flagship' ),
	),
	array(
		'slug'        => 'kids-capsule',
		'label'       => __( 'Kids Capsule', 'skyyrose-flagship' ),
		'accent'      => '#FFB6C1',
		'glow'        => 'rgba(255, 182, 193, 0.3)',
		'description' => __( 'Joyful luxury, playful sophistication', 'skyyrose-flagship' ),
	),
);
?>

<main id="primary" class="search-results" role="main" tabindex="-1">

	<!-- ============================
	     Header + Re-Search Form
	     ============================ -->
	<header class="search-results__header">
		<h1 class="search-results__title">
			<?php if ( ! empty( $skyyrose_search_query ) ) : ?>
				<?php esc_html_e( 'Results for', 'skyyrose-flagship' ); ?>
				<span class="search-results__query"><?php echo esc_html( $skyyrose_search_query ); ?></span>
			<?php else : ?>
				<?php esc_html_e( 'Search', 'skyyrose-flagship' ); ?>
			<?php endif; ?>
		</h1>

		<?php if ( ! empty( $skyyrose_search_query ) ) : ?>
			<p class="search-results__count">
				<?php
				$skyyrose_total = $skyyrose_product_count + $skyyrose_content_count;
				printf(
					/* translators: %d: total result count */
					esc_html( _n( '%d result found', '%d results found', $skyyrose_total, 'skyyrose-flagship' ) ),
					absint( $skyyrose_total )
				);
				?>
			</p>
		<?php endif; ?>

		<div class="search-results__search-form" role="search" aria-label="<?php esc_attr_e( 'Search the site', 'skyyrose-flagship' ); ?>">
			<form action="<?php echo esc_url( home_url( '/' ) ); ?>" method="get" class="search-results__form">
				<label for="search-results-input" class="screen-reader-text">
					<?php esc_html_e( 'Search for:', 'skyyrose-flagship' ); ?>
				</label>
				<input
					type="search"
					id="search-results-input"
					class="search-results__input"
					name="s"
					placeholder="<?php esc_attr_e( 'Search products, collections, pages...', 'skyyrose-flagship' ); ?>"
					value="<?php echo esc_attr( $skyyrose_search_query ); ?>"
					autocomplete="off"
				/>
				<button type="submit" class="search-results__submit" aria-label="<?php esc_attr_e( 'Search', 'skyyrose-flagship' ); ?>">
					<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
						<circle cx="11" cy="11" r="8"/>
						<line x1="21" y1="21" x2="16.65" y2="16.65"/>
					</svg>
				</button>
			</form>
		</div>
	</header>

	<?php if ( $skyyrose_product_count > 0 || have_posts() ) : ?>

		<?php
		// ==================================================================
		// Product Results (holo card grid) — shown first.
		// ==================================================================
		if ( $skyyrose_product_results && $skyyrose_product_results->have_posts() ) :
		?>
			<section class="search-results__products" aria-label="<?php esc_attr_e( 'Product Results', 'skyyrose-flagship' ); ?>">
				<h2 class="search-results__section-heading">
					<?php
					printf(
						/* translators: %d: product count */
						esc_html( _n( '%d Product', '%d Products', $skyyrose_product_count, 'skyyrose-flagship' ) ),
						absint( $skyyrose_product_count )
					);
					?>
				</h2>

				<div class="product-grid">
					<div class="product-grid__items">
						<?php
						$skyyrose_index = 0;
						while ( $skyyrose_product_results->have_posts() ) :
							$skyyrose_product_results->the_post();
							$skyyrose_wc_product = wc_get_product( get_the_ID() );

							if ( $skyyrose_wc_product ) :
								get_template_part(
									'template-parts/product-card-holo',
									null,
									array(
										'product' => $skyyrose_wc_product,
										'index'   => $skyyrose_index,
									)
								);
								$skyyrose_index++;
							endif;
						endwhile;
						wp_reset_postdata();
						?>
					</div>
				</div>
			</section>
		<?php endif; ?>

		<?php
		// ==================================================================
		// Content Results (posts, pages) — shown below products.
		// ==================================================================
		if ( have_posts() ) :
		?>
			<section class="search-results__content" aria-label="<?php esc_attr_e( 'Content Results', 'skyyrose-flagship' ); ?>">
				<h2 class="search-results__section-heading">
					<?php esc_html_e( 'Pages & Posts', 'skyyrose-flagship' ); ?>
				</h2>

				<div class="search-results__list">
					<?php while ( have_posts() ) : the_post(); ?>
						<article class="search-results__item" id="post-<?php the_ID(); ?>">
							<a href="<?php echo esc_url( get_permalink() ); ?>" class="search-results__item-link">
								<div class="search-results__item-body">
									<span class="search-results__item-type">
										<?php echo esc_html( get_post_type_object( get_post_type() )->labels->singular_name ); ?>
									</span>
									<h3 class="search-results__item-title">
										<?php the_title(); ?>
									</h3>
									<?php if ( has_excerpt() || get_the_content() ) : ?>
										<p class="search-results__item-excerpt">
											<?php echo esc_html( wp_trim_words( get_the_excerpt(), 24, '...' ) ); ?>
										</p>
									<?php endif; ?>
									<span class="search-results__item-date">
										<?php echo esc_html( get_the_date() ); ?>
									</span>
								</div>
								<span class="search-results__item-arrow" aria-hidden="true">&rarr;</span>
							</a>
						</article>
					<?php endwhile; ?>
				</div>

				<?php the_posts_navigation(
					array(
						'prev_text' => __( 'Older Results', 'skyyrose-flagship' ),
						'next_text' => __( 'Newer Results', 'skyyrose-flagship' ),
						'class'     => 'search-results__pagination',
					)
				); ?>
			</section>
		<?php endif; ?>

	<?php else : ?>

		<!-- ============================
		     Empty State — No Results
		     ============================ -->
		<div class="search-results__empty">

			<div class="search-results__empty-icon" aria-hidden="true">
				<svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
					<circle cx="11" cy="11" r="8"/>
					<line x1="21" y1="21" x2="16.65" y2="16.65"/>
					<line x1="8" y1="8" x2="14" y2="14"/>
					<line x1="14" y1="8" x2="8" y2="14"/>
				</svg>
			</div>

			<h2 class="search-results__empty-title">
				<?php esc_html_e( 'No Results Found', 'skyyrose-flagship' ); ?>
			</h2>

			<p class="search-results__empty-subtitle">
				<?php
				if ( ! empty( $skyyrose_search_query ) ) {
					printf(
						/* translators: %s: search query */
						esc_html__( 'We couldn\'t find anything matching "%s"', 'skyyrose-flagship' ),
						esc_html( $skyyrose_search_query )
					);
				} else {
					esc_html_e( 'Enter a search term to explore our collections', 'skyyrose-flagship' );
				}
				?>
			</p>

			<!-- Search Suggestions -->
			<div class="search-results__suggestions">
				<h3 class="search-results__section-heading">
					<?php esc_html_e( 'Try Searching For', 'skyyrose-flagship' ); ?>
				</h3>
				<div class="search-results__suggestion-tags">
					<?php
					$skyyrose_suggestions = array(
						__( 'Hoodies', 'skyyrose-flagship' ),
						__( 'T-Shirts', 'skyyrose-flagship' ),
						__( 'Black Rose', 'skyyrose-flagship' ),
						__( 'Love Hurts', 'skyyrose-flagship' ),
						__( 'Signature', 'skyyrose-flagship' ),
						__( 'Kids', 'skyyrose-flagship' ),
					);
					foreach ( $skyyrose_suggestions as $skyyrose_suggestion ) :
					?>
						<a href="<?php echo esc_url( home_url( '/?s=' . rawurlencode( $skyyrose_suggestion ) ) ); ?>"
						   class="search-results__suggestion-tag">
							<?php echo esc_html( $skyyrose_suggestion ); ?>
						</a>
					<?php endforeach; ?>
				</div>
			</div>

			<!-- Collection Quick Links (matching 404.php pattern) -->
			<nav class="search-results__collections" aria-label="<?php esc_attr_e( 'Browse Collections', 'skyyrose-flagship' ); ?>">
				<h3 class="search-results__section-heading">
					<?php esc_html_e( 'Explore Our Collections', 'skyyrose-flagship' ); ?>
				</h3>

				<div class="search-results__cards">
					<?php foreach ( $skyyrose_collections as $skyyrose_collection ) : ?>
						<?php
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

						if ( '#' === $skyyrose_link || is_wp_error( $skyyrose_link ) ) {
							$skyyrose_link  = home_url( '/collection-' . $skyyrose_collection['slug'] . '/' );
							$skyyrose_count = __( 'Explore', 'skyyrose-flagship' );
						}
						?>
						<a href="<?php echo esc_url( $skyyrose_link ); ?>"
						   class="search-results__card"
						   style="--card-accent: <?php echo esc_attr( $skyyrose_collection['accent'] ); ?>; --card-glow: <?php echo esc_attr( $skyyrose_collection['glow'] ); ?>">
							<span class="search-results__card-border" aria-hidden="true"></span>
							<span class="search-results__card-label">
								<?php echo esc_html( $skyyrose_collection['label'] ); ?>
							</span>
							<span class="search-results__card-description">
								<?php echo esc_html( $skyyrose_collection['description'] ); ?>
							</span>
							<span class="search-results__card-meta">
								<?php echo esc_html( $skyyrose_count ); ?>
							</span>
							<span class="search-results__card-arrow" aria-hidden="true">&rarr;</span>
						</a>
					<?php endforeach; ?>
				</div>
			</nav>

			<!-- CTA Buttons -->
			<div class="search-results__cta-group">
				<a href="<?php echo esc_url( home_url( '/shop/' ) ); ?>" class="search-results__cta search-results__cta--primary">
					<?php esc_html_e( 'Browse All Products', 'skyyrose-flagship' ); ?>
				</a>
				<a href="<?php echo esc_url( home_url( '/' ) ); ?>" class="search-results__cta search-results__cta--secondary">
					<?php esc_html_e( 'Return Home', 'skyyrose-flagship' ); ?>
				</a>
			</div>

		</div>

	<?php endif; ?>

</main>

<?php
get_footer();
