<?php
/**
 * Collection Page v4.0.0 — Shared Template Part
 *
 * Used by template-collection-{black-rose,love-hurts,signature}.php.
 * Expects $collection_config array with collection-specific content.
 *
 * @package SkyyRose_Flagship
 * @since   4.0.0
 */

defined( 'ABSPATH' ) || exit;

if ( empty( $collection_config ) || ! is_array( $collection_config ) ) {
	return;
}

$col = wp_parse_args(
	$collection_config,
	array(
		'slug'              => '',
		'name'              => '',
		'number'            => '01',
		'accent'            => '#C0C0C0',
		'accent_rgb'        => '192, 192, 192',
		'tagline'           => '',
		'meta_pieces'       => '',
		'meta_price_range'  => '',
		'meta_edition'      => '',
		'hero_image'        => '',
		'hero_logo'         => '',
		'manifesto_eye'     => '',
		'manifesto_heading' => '',
		'manifesto_body'    => '',
		'manifesto_scene'   => '',
		'featured_sku'      => '',
		'nl_title'          => '',
		'nl_desc'           => '',
		'immersive_url'     => '',
		'cross_nav'         => array(),
	)
);

/*
 * Fetch products: WooCommerce first, fallback to catalog.
 */
$wc_products   = array();
$all_products  = array();
$product_count = 0;
$min_price     = PHP_INT_MAX;
$max_price     = 0;

if ( function_exists( 'wc_get_products' ) ) {
	$wc_results = wc_get_products(
		array(
			'limit'    => 20,
			'category' => array( $col['slug'] ),
			'status'   => 'publish',
			'orderby'  => 'menu_order',
			'order'    => 'ASC',
		)
	);

	if ( ! empty( $wc_results ) ) {
		foreach ( $wc_results as $wc_p ) {
			$price = (float) $wc_p->get_price();
			if ( $price < $min_price ) {
				$min_price = $price;
			}
			if ( $price > $max_price ) {
				$max_price = $price;
			}

			$sizes_attr = $wc_p->get_attribute( 'pa_size' );
			$sizes      = $sizes_attr ? explode( ', ', $sizes_attr ) : array( 'S', 'M', 'L', 'XL' );

			$all_products[] = array(
				'id'            => (string) $wc_p->get_id(),
				'sku'           => $wc_p->get_sku(),
				'name'          => $wc_p->get_name(),
				'price'         => $price,
				'price_display' => $wc_p->get_price_html(),
				'desc'          => wp_strip_all_tags( $wc_p->get_short_description() ),
				'image'         => wp_get_attachment_url( $wc_p->get_image_id() ),
				'url'           => get_permalink( $wc_p->get_id() ),
				'sizes'         => $sizes,
				'is_preorder'   => '1' === get_post_meta( $wc_p->get_id(), '_is_preorder', true ),
				'badge'         => $wc_p->get_meta( '_collection_badge' ),
			);
		}
		$product_count = count( $all_products );
	}
}

/* Fallback: centralized catalog. */
if ( empty( $all_products ) ) {
	$catalog_products = skyyrose_get_collection_products( $col['slug'] );
	foreach ( $catalog_products as $p ) {
		if ( empty( $p['published'] ) ) {
			continue;
		}

		$price = (float) $p['price'];
		if ( $price < $min_price ) {
			$min_price = $price;
		}
		if ( $price > $max_price ) {
			$max_price = $price;
		}

		$image = ! empty( $p['front_model_image'] ) ? $p['front_model_image'] : $p['image'];
		$sizes = ! empty( $p['sizes'] ) ? explode( '|', $p['sizes'] ) : array( 'S', 'M', 'L', 'XL' );

		$all_products[] = array(
			'id'            => $p['sku'],
			'sku'           => $p['sku'],
			'name'          => $p['name'],
			'price'         => $price,
			'price_display' => skyyrose_format_price( $p ),
			'desc'          => $p['description'],
			'image'         => skyyrose_product_image_uri( $image ),
			'url'           => skyyrose_product_url( $p['sku'] ),
			'sizes'         => $sizes,
			'is_preorder'   => ! empty( $p['is_preorder'] ),
			'badge'         => ! empty( $p['badge'] ) ? $p['badge'] : '',
		);
	}
	$product_count = count( $all_products );
}

/* Dynamic meta. */
if ( $product_count > 0 && $min_price < PHP_INT_MAX ) {
	$col['meta_pieces']      = $product_count . ' ' . _n( 'Piece', 'Pieces', $product_count, 'skyyrose-flagship' );
	$col['meta_price_range'] = '$' . number_format( $min_price, 0 ) . ' &mdash; $' . number_format( $max_price, 0 );
}

/* Featured product (first match by SKU, or first product). */
$featured = null;
if ( ! empty( $col['featured_sku'] ) ) {
	foreach ( $all_products as $p ) {
		if ( $p['sku'] === $col['featured_sku'] ) {
			$featured = $p;
			break;
		}
	}
}
if ( ! $featured && ! empty( $all_products ) ) {
	$featured = $all_products[0];
}

get_header();
?>

<main id="primary" class="site-main" role="main" tabindex="-1">
<div class="col-page" data-collection="<?php echo esc_attr( $col['slug'] ); ?>"
     style="--col-accent: <?php echo esc_attr( $col['accent'] ); ?>; --col-accent-rgb: <?php echo esc_attr( $col['accent_rgb'] ); ?>;">

	<!-- ============================================================
	     HERO
	     ============================================================ -->
	<section class="col-hero" aria-label="<?php echo esc_attr( sprintf( __( '%s collection hero', 'skyyrose-flagship' ), $col['name'] ) ); ?>">
		<div class="col-hero__img">
			<img src="<?php echo esc_url( $col['hero_image'] ); ?>"
			     alt="<?php echo esc_attr( sprintf( __( '%s collection hero image', 'skyyrose-flagship' ), $col['name'] ) ); ?>"
			     width="1920" height="1080" fetchpriority="high">
		</div>
		<div class="col-hero__overlay"></div>
		<div class="col-hero__content">
			<p class="col-hero__num">
				<?php echo esc_html( sprintf( __( 'Collection %s', 'skyyrose-flagship' ), $col['number'] ) ); ?>
			</p>
			<?php if ( ! empty( $col['hero_logo'] ) ) : ?>
			<h1 class="col-hero__name">
				<span class="screen-reader-text"><?php echo wp_kses_post( $col['name'] ); ?></span>
				<img class="col-hero__logo" aria-hidden="true"
				     src="<?php echo esc_url( $col['hero_logo'] ); ?>"
				     alt="" loading="eager">
			</h1>
		<?php else : ?>
			<h1 class="col-hero__name"><?php echo wp_kses_post( $col['name'] ); ?></h1>
		<?php endif; ?>
			<p class="col-hero__tag"><?php echo esc_html( $col['tagline'] ); ?></p>
			<div class="col-hero__meta">
				<span><?php echo wp_kses_post( $col['meta_pieces'] ); ?></span>
				<span><?php echo wp_kses_post( $col['meta_price_range'] ); ?></span>
				<span><?php echo esc_html( $col['meta_edition'] ); ?></span>
			</div>
			<div class="col-hero__ctas">
				<a href="#col-catalog" class="col-btn col-btn--fill">
					<?php esc_html_e( 'Shop Collection', 'skyyrose-flagship' ); ?>
				</a>
				<a href="#col-manifesto" class="col-btn">
					<?php echo esc_html( $col['manifesto_eye'] ); ?>
				</a>
			</div>
		</div>

		<?php if ( 'signature' === $col['slug'] ) : ?>
		<!-- Animated rose bloom -->
		<picture class="signature-rose signature-rose--hero" aria-hidden="true" style="position:absolute;bottom:12%;right:8%;z-index:3;">
			<source srcset="<?php echo esc_url( get_template_directory_uri() . '/assets/branding/signature-rose-hero.webp' ); ?>" type="image/webp">
			<img src="<?php echo esc_url( get_template_directory_uri() . '/assets/branding/signature-rose-hero.png' ); ?>"
			     alt="" width="120" height="128" loading="eager">
		</picture>

		<!-- Floating petals -->
		<div class="signature-petals" aria-hidden="true">
			<span class="petal"></span>
			<span class="petal"></span>
			<span class="petal"></span>
			<span class="petal"></span>
			<span class="petal"></span>
			<span class="petal"></span>
			<span class="petal"></span>
			<span class="petal"></span>
		</div>
		<?php endif; ?>
	</section>

	<!-- ============================================================
	     MANIFESTO
	     ============================================================ -->
	<section class="col-manifesto" id="col-manifesto"
	         aria-label="<?php echo esc_attr( sprintf( __( '%s philosophy', 'skyyrose-flagship' ), $col['name'] ) ); ?>">
		<div class="col-mf__text">
			<p class="col-mf__eye col-rv"><?php echo esc_html( $col['manifesto_eye'] ); ?></p>
			<h2 class="col-mf__head col-rv col-rv-d1"><?php echo wp_kses_post( $col['manifesto_heading'] ); ?></h2>
			<div class="col-mf__body col-rv col-rv-d2">
				<?php echo wp_kses_post( $col['manifesto_body'] ); ?>
			</div>
		</div>
		<div class="col-mf__scene col-rv-l">
			<img src="<?php echo esc_url( $col['manifesto_scene'] ); ?>"
			     alt="<?php echo esc_attr( sprintf( __( '%s collection scene', 'skyyrose-flagship' ), $col['name'] ) ); ?>"
			     width="800" height="600" loading="lazy">
		</div>
	</section>

	<?php if ( $featured ) : ?>
	<!-- ============================================================
	     FEATURED PRODUCT
	     ============================================================ -->
	<section class="col-featured" id="col-featured"
	         aria-label="<?php echo esc_attr( sprintf( __( '%s featured product', 'skyyrose-flagship' ), $col['name'] ) ); ?>">
		<div class="col-feat__inner">
			<div class="col-feat__vis col-rv-l"
			     data-product-id="<?php echo esc_attr( $featured['sku'] ); ?>"
			     role="button"
			     tabindex="0"
			     aria-label="<?php echo esc_attr( sprintf( __( 'View %s details', 'skyyrose-flagship' ), $featured['name'] ) ); ?>">
				<?php if ( ! empty( $featured['image'] ) ) : ?>
					<img src="<?php echo esc_url( $featured['image'] ); ?>"
					     alt="<?php echo esc_attr( $featured['name'] ); ?>"
					     width="600" height="750" loading="lazy">
				<?php else : ?>
					<span class="col-feat__vis-letter"><?php echo esc_html( mb_substr( $featured['name'], 0, 1 ) ); ?></span>
				<?php endif; ?>
				<span class="col-feat__badge"><?php echo esc_html( strtoupper( $col['name'] ) ); ?></span>
				<span class="col-feat__tag"><?php esc_html_e( 'FEATURED PIECE', 'skyyrose-flagship' ); ?></span>
			</div>
			<div class="col-feat__info">
				<p class="col-feat__col col-rv"><?php echo esc_html( strtoupper( $col['name'] ) . ' COLLECTION' ); ?></p>
				<h3 class="col-feat__name col-rv col-rv-d1"><?php echo esc_html( $featured['name'] ); ?></h3>
				<p class="col-feat__price col-rv col-rv-d1"><?php echo wp_kses_post( $featured['price_display'] ); ?></p>
				<p class="col-feat__desc col-rv col-rv-d2"><?php echo esc_html( $featured['desc'] ); ?></p>
				<div class="col-feat__sizes col-rv col-rv-d3">
					<?php foreach ( $featured['sizes'] as $size ) : ?>
						<button data-size="<?php echo esc_attr( $size ); ?>"><?php echo esc_html( $size ); ?></button>
					<?php endforeach; ?>
				</div>
				<a href="<?php echo esc_url( $featured['url'] ); ?>" class="col-feat__add col-rv col-rv-d3">
					<?php
					if ( $featured['is_preorder'] ) {
						/* translators: %s: price */
						printf( esc_html__( 'Pre-Order — %s', 'skyyrose-flagship' ), wp_kses_post( $featured['price_display'] ) );
					} else {
						/* translators: %s: price */
						printf( esc_html__( 'View Product — %s', 'skyyrose-flagship' ), wp_kses_post( $featured['price_display'] ) );
					}
					?>
				</a>
			</div>
		</div>
	</section>
	<?php endif; ?>

	<!-- ============================================================
	     CATALOG — Full Product Grid
	     ============================================================ -->
	<section class="col-catalog" id="col-catalog"
	         aria-labelledby="col-catalog-heading">
		<div class="col-catalog__head">
			<h3 class="col-catalog__title col-rv" id="col-catalog-heading">
				<?php esc_html_e( 'Full Collection', 'skyyrose-flagship' ); ?>
			</h3>
			<span class="col-catalog__count col-rv col-rv-d1">
				<?php echo wp_kses_post( $col['meta_pieces'] . ' &mdash; ' . $col['meta_price_range'] ); ?>
			</span>
		</div>

		<!-- Sort / Filter Toolbar -->
		<div class="col-toolbar col-rv" role="toolbar" aria-label="<?php esc_attr_e( 'Sort and filter products', 'skyyrose-flagship' ); ?>">
			<div class="col-toolbar__sort">
				<label for="col-sort" class="col-toolbar__label"><?php esc_html_e( 'Sort', 'skyyrose-flagship' ); ?></label>
				<select id="col-sort" class="col-toolbar__select" aria-label="<?php esc_attr_e( 'Sort products', 'skyyrose-flagship' ); ?>">
					<option value="default"><?php esc_html_e( 'Default', 'skyyrose-flagship' ); ?></option>
					<option value="price-asc"><?php esc_html_e( 'Price: Low → High', 'skyyrose-flagship' ); ?></option>
					<option value="price-desc"><?php esc_html_e( 'Price: High → Low', 'skyyrose-flagship' ); ?></option>
					<option value="name-asc"><?php esc_html_e( 'Name: A → Z', 'skyyrose-flagship' ); ?></option>
					<option value="name-desc"><?php esc_html_e( 'Name: Z → A', 'skyyrose-flagship' ); ?></option>
				</select>
			</div>
			<div class="col-toolbar__filter">
				<label class="col-toolbar__label"><?php esc_html_e( 'Price', 'skyyrose-flagship' ); ?></label>
				<div class="col-toolbar__range">
					<span class="col-toolbar__currency">$</span>
					<input type="number" id="col-price-min" class="col-toolbar__input"
					       placeholder="<?php esc_attr_e( 'Min', 'skyyrose-flagship' ); ?>"
					       min="0" step="1"
					       aria-label="<?php esc_attr_e( 'Minimum price', 'skyyrose-flagship' ); ?>">
					<span class="col-toolbar__dash">&mdash;</span>
					<span class="col-toolbar__currency">$</span>
					<input type="number" id="col-price-max" class="col-toolbar__input"
					       placeholder="<?php esc_attr_e( 'Max', 'skyyrose-flagship' ); ?>"
					       min="0" step="1"
					       aria-label="<?php esc_attr_e( 'Maximum price', 'skyyrose-flagship' ); ?>">
				</div>
			</div>
			<div class="col-toolbar__wishlist-count" aria-live="polite">
				<a href="<?php echo esc_url( home_url( '/wishlist/' ) ); ?>" class="col-toolbar__wl-link"
				   aria-label="<?php esc_attr_e( 'View wishlist', 'skyyrose-flagship' ); ?>">
					<svg class="col-toolbar__wl-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
						<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
					</svg>
					<span class="col-toolbar__wl-num" id="col-wl-count">0</span>
				</a>
			</div>
		</div>

		<?php
		if ( function_exists( 'skyyrose_render_interactive_grid' ) ) {
			skyyrose_render_interactive_grid( $all_products, $col );
		} else {
			// Fallback: render legacy col-card grid if interactive-grid.php is not loaded.
			?>
			<div class="col-grid">
				<?php foreach ( $all_products as $product ) : ?>
					<div class="col-card"
					     data-product-id="<?php echo esc_attr( $product['sku'] ); ?>"
					     role="button"
					     tabindex="0"
					     aria-label="<?php echo esc_attr( sprintf( __( 'View %s', 'skyyrose-flagship' ), $product['name'] ) ); ?>">
						<div class="col-card__img">
							<?php if ( ! empty( $product['image'] ) ) : ?>
								<img src="<?php echo esc_url( $product['image'] ); ?>"
								     alt="<?php echo esc_attr( $product['name'] ); ?>"
								     width="400" height="533" loading="lazy">
							<?php else : ?>
								<span class="col-card__letter"><?php echo esc_html( mb_substr( $product['name'], 0, 1 ) ); ?></span>
							<?php endif; ?>
						</div>
						<div class="col-card__body">
							<h3 class="col-card__name"><?php echo esc_html( $product['name'] ); ?></h3>
							<div class="col-card__foot">
								<span class="col-card__price"><?php echo wp_kses_post( $product['price_display'] ); ?></span>
								<a href="<?php echo esc_url( $product['url'] ); ?>" class="col-card__view-btn">
									<?php esc_html_e( 'Details', 'skyyrose-flagship' ); ?>
								</a>
							</div>
						</div>
					</div>
				<?php endforeach; ?>
			</div>
			<?php
		}
		?>

		<div style="text-align:center; padding:1rem 0 0;">
			<button class="size-guide-trigger" data-open-size-guide
			        aria-label="<?php esc_attr_e( 'Open size guide', 'skyyrose-flagship' ); ?>">
				<svg class="size-guide-trigger__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
					<path d="M6 2v20M18 2v20M6 12h12M6 7h12M6 17h12"/>
				</svg>
				<?php esc_html_e( 'Size Guide', 'skyyrose-flagship' ); ?>
			</button>
		</div>
	</section>

	<!-- ============================================================
	     IMMERSIVE CTA
	     ============================================================ -->
	<?php if ( ! empty( $col['immersive_url'] ) ) : ?>
	<section class="col-immersive-cta"
	         aria-label="<?php esc_attr_e( 'Immersive 3D experience', 'skyyrose-flagship' ); ?>">
		<a href="<?php echo esc_url( $col['immersive_url'] ); ?>"
		   class="col-immersive-cta__link"
		   aria-label="<?php echo esc_attr( sprintf( __( 'Enter the %s 3D Experience', 'skyyrose-flagship' ), $col['name'] ) ); ?>">
			<?php esc_html_e( 'Enter the 3D Experience', 'skyyrose-flagship' ); ?>
		</a>
	</section>
	<?php endif; ?>

	<!-- ============================================================
	     NEWSLETTER
	     ============================================================ -->
	<section class="col-nl" aria-label="<?php esc_attr_e( 'Newsletter signup', 'skyyrose-flagship' ); ?>">
		<p class="col-nl__eye col-rv"><?php esc_html_e( 'Join the Movement', 'skyyrose-flagship' ); ?></p>
		<h2 class="col-nl__title col-rv col-rv-d1"><?php echo esc_html( $col['nl_title'] ); ?></h2>
		<p class="col-nl__desc col-rv col-rv-d2"><?php echo esc_html( $col['nl_desc'] ); ?></p>
		<div class="col-nl__form col-rv col-rv-d3">
			<input type="email" class="col-nl__input"
			       placeholder="<?php esc_attr_e( 'Your email address', 'skyyrose-flagship' ); ?>"
			       aria-label="<?php esc_attr_e( 'Email address', 'skyyrose-flagship' ); ?>">
			<button class="col-nl__btn"><?php esc_html_e( 'Join', 'skyyrose-flagship' ); ?></button>
			<?php wp_nonce_field( 'skyyrose_newsletter', '_wpnonce', false ); ?>
		</div>
	</section>

	<!-- ============================================================
	     CROSS-COLLECTION NAV
	     ============================================================ -->
	<nav class="col-crossnav" aria-label="<?php esc_attr_e( 'Browse other collections', 'skyyrose-flagship' ); ?>">
		<a href="<?php echo esc_url( home_url( '/' ) ); ?>" class="col-crossnav__home">
			<?php esc_html_e( 'All Collections', 'skyyrose-flagship' ); ?>
		</a>
		<div class="col-crossnav__cols">
			<?php foreach ( $col['cross_nav'] as $nav_item ) : ?>
				<a href="<?php echo esc_url( home_url( '/' . $nav_item['slug'] . '/' ) ); ?>"
				   class="col-crossnav__link <?php echo esc_attr( $nav_item['class'] ); ?>">
					<?php echo esc_html( $nav_item['label'] ); ?>
				</a>
			<?php endforeach; ?>
		</div>
	</nav>

</div><!-- .col-page -->

<!-- ============================================================
     QUICK-VIEW MODAL
     ============================================================ -->
<div class="col-modal-ov" id="colModal" role="dialog" aria-modal="true"
     aria-label="<?php esc_attr_e( 'Product quick view', 'skyyrose-flagship' ); ?>"
     style="--col-accent: <?php echo esc_attr( $col['accent'] ); ?>; --col-accent-rgb: <?php echo esc_attr( $col['accent_rgb'] ); ?>;">
	<div class="col-modal__bk"></div>
	<div class="col-modal__card">
		<button class="col-modal__close" aria-label="<?php esc_attr_e( 'Close', 'skyyrose-flagship' ); ?>">&times;</button>
		<div class="col-modal__img">
			<span class="col-modal__letter"></span>
		</div>
		<div class="col-modal__body">
			<h3 class="col-modal__name"></h3>
			<p class="col-modal__price"></p>
			<p class="col-modal__desc"></p>
			<div class="col-modal__sizes"></div>
			<div class="col-modal__actions">
				<button class="col-modal__add"><?php esc_html_e( 'View Product', 'skyyrose-flagship' ); ?></button>
				<button class="col-modal__back"><?php esc_html_e( 'Back', 'skyyrose-flagship' ); ?></button>
			</div>
			<p class="col-modal__sku"></p>
		</div>
	</div>
</div>

<?php get_template_part( 'template-parts/size-guide-modal' ); ?>

</main><!-- #primary -->

<?php
/* Localize product data for the quick-view modal JS. */
wp_localize_script(
	'skyyrose-template-collection-v4',
	'skyyRoseCollectionProducts',
	$all_products
);

/* Also pass product data to the interactive cards script. */
if ( wp_script_is( 'skyyrose-interactive-cards', 'enqueued' ) ) {
	wp_localize_script(
		'skyyrose-interactive-cards',
		'skyyRoseInteractiveProducts',
		array(
			'products' => $all_products,
			'ajaxUrl'  => admin_url( 'admin-ajax.php' ),
			'nonce'    => wp_create_nonce( 'skyyrose-immersive-nonce' ),
		)
	);
}

get_footer();
