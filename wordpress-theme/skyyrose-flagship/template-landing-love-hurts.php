<?php
/**
 * Template Name: Landing — Love Hurts
 * Template Post Type: page
 *
 * Split scrollytell landing page for the Love Hurts collection.
 * Five narrative panes paired with a sticky product viewport (desktop);
 * stacked alternating layout on mobile.
 *
 * @package SkyyRose
 * @since   1.2.0
 */

defined( 'ABSPATH' ) || exit;

// Fetch the full Love Hurts product catalog (all items for the grid).
$lh_products = skyyrose_get_collection_products( 'love-hurts' );

// Featured products for the five narrative panes (order matters).
// SKUs: lh-004, lh-002, lh-003, lh-006, lh-005
$pane_skus     = array( 'lh-004', 'lh-002', 'lh-003', 'lh-006', 'lh-005' );
$catalog_all   = skyyrose_get_product_catalog();
$pane_products = array();
foreach ( $pane_skus as $sku ) {
	if ( isset( $catalog_all[ $sku ] ) ) {
		$pane_products[] = $catalog_all[ $sku ];
	}
}

// Asset base URI (CSV paths start with 'assets/' — strip that prefix).
$assets = trailingslashit( SKYYROSE_ASSETS_URI );

get_header();
?>
<a class="lp-skip-link" href="#product-grid"><?php esc_html_e( 'Skip to products', 'skyyrose' ); ?></a>
<div id="lp-live-region" class="lp-sr-only" aria-live="polite" aria-atomic="true"></div>

<main id="primary" class="lp" data-collection="love-hurts" role="main" tabindex="-1">
	<h1 class="screen-reader-text"><?php esc_html_e( 'Love Hurts Collection — SkyyRose', 'skyyrose' ); ?></h1>

	<!-- ================================================================
		Hero
	================================================================ -->
	<section class="lp-hero" aria-label="<?php esc_attr_e( 'Love Hurts collection hero', 'skyyrose' ); ?>">
		<div class="lp-hero__bg" aria-hidden="true">
			<div class="lp-hero__atmosphere">
				<img
					class="lp-hero__atmosphere-img"
					src="<?php echo esc_url( $assets . 'images/logos/red-roses-cloud-cluster.webp' ); ?>"
					alt=""
					role="presentation"
					loading="eager"
					decoding="async"
				/>
			</div>
			<div class="lp-hero__vignette"></div>
		</div>

		<div class="lp-hero__content">
			<!-- Lockup image IS the collection name — never type-rendered as text -->
			<div class="lp-hero__lockup-wrap">
				<picture>
					<source
						srcset="<?php echo esc_url( $assets . 'images/hero-overlays/lh-logo-combined.avif' ); ?>"
						type="image/avif"
					/>
					<source
						srcset="<?php echo esc_url( $assets . 'images/hero-overlays/lh-logo-combined.webp' ); ?>"
						type="image/webp"
					/>
					<img
						class="lp-hero__lockup"
						src="<?php echo esc_url( $assets . 'images/hero-overlays/lh-logo-combined.webp' ); ?>"
						alt="<?php esc_attr_e( 'Love Hurts Collection', 'skyyrose' ); ?>"
						width="540"
						height="200"
						fetchpriority="high"
						decoding="sync"
					/>
				</picture>
			</div>

			<p class="lp-hero__subtitle">
				<?php esc_html_e( 'For the love that survived everything.', 'skyyrose' ); ?>
			</p>

			<div class="lp-hero__cta-group">
				<a href="#product-grid" class="lp-btn lp-btn--primary">
					<?php esc_html_e( 'Shop the Collection', 'skyyrose' ); ?>
				</a>
				<a href="#lp-split" class="lp-btn lp-btn--outline">
					<?php esc_html_e( 'Explore the Story', 'skyyrose' ); ?>
				</a>
			</div>
		</div>

		<div class="lp-hero__scroll-cue" aria-hidden="true">
			<span class="lp-hero__scroll-arrow"></span>
			<span><?php esc_html_e( 'Scroll', 'skyyrose' ); ?></span>
		</div>
	</section>

	<!-- ================================================================
		Split scrollytell
	================================================================ -->
	<section class="lp-split" id="lp-split" aria-label="<?php esc_attr_e( 'Collection narrative', 'skyyrose' ); ?>">

		<!-- Indicator dots (desktop only, JS-driven) -->
		<nav class="lp-pane-indicators" aria-label="<?php esc_attr_e( 'Navigate to pane', 'skyyrose' ); ?>">
			<?php for ( $d = 0; $d < 5; $d++ ) : ?>
			<button
				class="lp-pane-indicator<?php echo 0 === $d ? ' is-active' : ''; ?>"
				aria-label="<?php echo esc_attr( sprintf( __( 'Pane %d', 'skyyrose' ), $d + 1 ) ); ?>"
				<?php echo 0 === $d ? 'aria-current="true"' : ''; ?>
			></button>
			<?php endfor; ?>
		</nav>

		<!-- Left: narrative panes -->
		<div class="lp-narrative">

			<?php
			// Pane 0 — The Bomber Jacket
			$p0 = isset( $pane_products[0] ) ? $pane_products[0] : null;
			?>
			<article class="lp-narrative__pane lp-rv" data-pane-index="0">
				<p class="lp-pane__number">01 / 05</p>
				<p class="lp-pane__eyebrow"><?php esc_html_e( 'The Statement Piece', 'skyyrose' ); ?></p>
				<h2 class="lp-pane__headline">
					<?php esc_html_e( 'Wear every chapter.', 'skyyrose' ); ?>
				</h2>
				<p class="lp-pane__body">
					<?php esc_html_e( 'Some love stories don\'t have clean endings. The Love Hurts Bomber Jacket carries that weight — embroidered devotion on the back, silence on the chest. Structured. Unforgettable.', 'skyyrose' ); ?>
				</p>
				<blockquote class="lp-pane__pull-quote">
					<?php esc_html_e( '"You don\'t dress for the memories. You dress through them."', 'skyyrose' ); ?>
				</blockquote>
				<?php if ( $p0 ) : ?>
				<ul class="lp-pane__detail-list">
					<li class="lp-pane__detail-item"><?php esc_html_e( 'Heavyweight satin shell', 'skyyrose' ); ?></li>
					<li class="lp-pane__detail-item"><?php esc_html_e( 'Embroidered back panel', 'skyyrose' ); ?></li>
					<li class="lp-pane__detail-item">
						<?php echo esc_html( sprintf( __( 'From $%s', 'skyyrose' ), number_format( (float) $p0['price'], 0 ) ) ); ?>
					</li>
				</ul>
				<a href="<?php echo esc_url( (string) get_permalink( wc_get_product_id_by_sku( $p0['sku'] ) ) ); ?>" class="lp-btn lp-btn--secondary">
					<?php esc_html_e( 'View Jacket', 'skyyrose' ); ?>
				</a>
				<div class="lp-pane__mobile-product">
					<?php if ( ! empty( $p0['front_model_image'] ) ) : ?>
					<img
						src="<?php echo esc_url( $assets . ltrim( str_replace( 'assets/', '', $p0['front_model_image'] ), '/' ) ); ?>"
						alt="<?php echo esc_attr( $p0['name'] ); ?>"
						loading="lazy"
						decoding="async"
						style="width:100%;max-width:320px;border-radius:2px;"
					/>
					<?php endif; ?>
				</div>
				<?php endif; ?>
			</article>

			<?php
			// Pane 1 — Joggers Black
			$p1 = isset( $pane_products[1] ) ? $pane_products[1] : null;
			?>
			<article class="lp-narrative__pane lp-rv" data-pane-index="1">
				<p class="lp-pane__number">02 / 05</p>
				<p class="lp-pane__eyebrow"><?php esc_html_e( 'The Foundation', 'skyyrose' ); ?></p>
				<h2 class="lp-pane__headline">
					<?php esc_html_e( 'Soft outside. Carrying everything inside.', 'skyyrose' ); ?>
				</h2>
				<p class="lp-pane__body">
					<?php esc_html_e( 'Cotton-fleece joggers built for the long stretch — after the conversation, before the next decision. The Love Hurts wordmark embroidered at the left ankle. Crimson, black, and gold on dark.', 'skyyrose' ); ?>
				</p>
				<?php if ( $p1 ) : ?>
				<ul class="lp-pane__detail-list">
					<li class="lp-pane__detail-item"><?php esc_html_e( 'Mid-weight cotton-fleece', 'skyyrose' ); ?></li>
					<li class="lp-pane__detail-item"><?php esc_html_e( 'Ribbed ankle cuffs', 'skyyrose' ); ?></li>
					<li class="lp-pane__detail-item"><?php esc_html_e( 'Athletic fit', 'skyyrose' ); ?></li>
					<li class="lp-pane__detail-item">
						<?php echo esc_html( sprintf( __( '$%s', 'skyyrose' ), number_format( (float) $p1['price'], 0 ) ) ); ?>
					</li>
				</ul>
				<a href="<?php echo esc_url( (string) get_permalink( wc_get_product_id_by_sku( $p1['sku'] ) ) ); ?>" class="lp-btn lp-btn--secondary">
					<?php esc_html_e( 'Shop Joggers', 'skyyrose' ); ?>
				</a>
				<div class="lp-pane__mobile-product">
					<?php if ( ! empty( $p1['front_model_image'] ) ) : ?>
					<img
						src="<?php echo esc_url( $assets . ltrim( str_replace( 'assets/', '', $p1['front_model_image'] ), '/' ) ); ?>"
						alt="<?php echo esc_attr( $p1['name'] ); ?>"
						loading="lazy"
						decoding="async"
						style="width:100%;max-width:320px;border-radius:2px;"
					/>
					<?php endif; ?>
				</div>
				<?php endif; ?>
			</article>

			<?php
			// Pane 2 — Basketball Shorts
			$p2 = isset( $pane_products[2] ) ? $pane_products[2] : null;
			?>
			<article class="lp-narrative__pane lp-rv" data-pane-index="2">
				<p class="lp-pane__number">03 / 05</p>
				<p class="lp-pane__eyebrow"><?php esc_html_e( 'The Move', 'skyyrose' ); ?></p>
				<h2 class="lp-pane__headline">
					<?php esc_html_e( 'Built for what you carry off the court.', 'skyyrose' ); ?>
				</h2>
				<p class="lp-pane__body">
					<?php esc_html_e( 'Basketball shorts that live past the game. The heart emblem at the inseam. Moisture-wicking shell. Every rep, every comeback, every day you showed up anyway.', 'skyyrose' ); ?>
				</p>
				<?php if ( $p2 ) : ?>
				<ul class="lp-pane__detail-list">
					<li class="lp-pane__detail-item"><?php esc_html_e( 'Moisture-wicking shell', 'skyyrose' ); ?></li>
					<li class="lp-pane__detail-item"><?php esc_html_e( 'Side-slit hem', 'skyyrose' ); ?></li>
					<li class="lp-pane__detail-item">
						<?php echo esc_html( sprintf( __( '$%s', 'skyyrose' ), number_format( (float) $p2['price'], 0 ) ) ); ?>
					</li>
				</ul>
				<a href="<?php echo esc_url( (string) get_permalink( wc_get_product_id_by_sku( $p2['sku'] ) ) ); ?>" class="lp-btn lp-btn--secondary">
					<?php esc_html_e( 'Shop Shorts', 'skyyrose' ); ?>
				</a>
				<div class="lp-pane__mobile-product">
					<?php if ( ! empty( $p2['front_model_image'] ) ) : ?>
					<img
						src="<?php echo esc_url( $assets . ltrim( str_replace( 'assets/', '', $p2['front_model_image'] ), '/' ) ); ?>"
						alt="<?php echo esc_attr( $p2['name'] ); ?>"
						loading="lazy"
						decoding="async"
						style="width:100%;max-width:320px;border-radius:2px;"
					/>
					<?php endif; ?>
				</div>
				<?php endif; ?>
			</article>

			<?php
			// Pane 3 — Joggers White
			$p3 = isset( $pane_products[3] ) ? $pane_products[3] : null;
			?>
			<article class="lp-narrative__pane lp-rv" data-pane-index="3">
				<p class="lp-pane__number">04 / 05</p>
				<p class="lp-pane__eyebrow"><?php esc_html_e( 'The Mirror', 'skyyrose' ); ?></p>
				<h2 class="lp-pane__headline">
					<?php esc_html_e( 'The same devotion. Different light.', 'skyyrose' ); ?>
				</h2>
				<p class="lp-pane__body">
					<?php esc_html_e( 'The white colorway of the Love Hurts Joggers. Crimson, black, and gold on white — the same emblem reading differently when you step into the room. A mirror of the black pair.', 'skyyrose' ); ?>
				</p>
				<?php if ( $p3 ) : ?>
				<ul class="lp-pane__detail-list">
					<li class="lp-pane__detail-item"><?php esc_html_e( 'Cotton-fleece, white colorway', 'skyyrose' ); ?></li>
					<li class="lp-pane__detail-item"><?php esc_html_e( 'Mirror of Love Hurts Joggers (Black)', 'skyyrose' ); ?></li>
					<li class="lp-pane__detail-item">
						<?php echo esc_html( sprintf( __( '$%s', 'skyyrose' ), number_format( (float) $p3['price'], 0 ) ) ); ?>
					</li>
				</ul>
				<a href="<?php echo esc_url( (string) get_permalink( wc_get_product_id_by_sku( $p3['sku'] ) ) ); ?>" class="lp-btn lp-btn--secondary">
					<?php esc_html_e( 'Shop White Joggers', 'skyyrose' ); ?>
				</a>
				<div class="lp-pane__mobile-product">
					<?php if ( ! empty( $p3['front_model_image'] ) ) : ?>
					<img
						src="<?php echo esc_url( $assets . ltrim( str_replace( 'assets/', '', $p3['front_model_image'] ), '/' ) ); ?>"
						alt="<?php echo esc_attr( $p3['name'] ); ?>"
						loading="lazy"
						decoding="async"
						style="width:100%;max-width:320px;border-radius:2px;"
					/>
					<?php endif; ?>
				</div>
				<?php endif; ?>
			</article>

			<?php
			// Pane 4 — The Fannie
			$p4 = isset( $pane_products[4] ) ? $pane_products[4] : null;
			?>
			<article class="lp-narrative__pane lp-rv" data-pane-index="4">
				<p class="lp-pane__number">05 / 05</p>
				<p class="lp-pane__eyebrow"><?php esc_html_e( 'The Detail', 'skyyrose' ); ?></p>
				<h2 class="lp-pane__headline">
					<?php esc_html_e( 'Even the small things carry it.', 'skyyrose' ); ?>
				</h2>
				<p class="lp-pane__body">
					<?php esc_html_e( 'The Fannie wears the Love Hurts logo at the front pocket. Worn across the body or around the waist, it\'s the accessory that finishes the set — quietly, without announcement.', 'skyyrose' ); ?>
				</p>
				<?php if ( $p4 ) : ?>
				<ul class="lp-pane__detail-list">
					<li class="lp-pane__detail-item"><?php esc_html_e( 'Love Hurts logo embroidery', 'skyyrose' ); ?></li>
					<li class="lp-pane__detail-item"><?php esc_html_e( 'Adjustable strap', 'skyyrose' ); ?></li>
					<li class="lp-pane__detail-item">
						<?php echo esc_html( sprintf( __( '$%s', 'skyyrose' ), number_format( (float) $p4['price'], 0 ) ) ); ?>
					</li>
				</ul>
				<a href="<?php echo esc_url( (string) get_permalink( wc_get_product_id_by_sku( $p4['sku'] ) ) ); ?>" class="lp-btn lp-btn--secondary">
					<?php esc_html_e( 'Shop The Fannie', 'skyyrose' ); ?>
				</a>
				<div class="lp-pane__mobile-product">
					<?php if ( ! empty( $p4['front_model_image'] ) ) : ?>
					<img
						src="<?php echo esc_url( $assets . ltrim( str_replace( 'assets/', '', $p4['front_model_image'] ), '/' ) ); ?>"
						alt="<?php echo esc_attr( $p4['name'] ); ?>"
						loading="lazy"
						decoding="async"
						style="width:100%;max-width:320px;border-radius:2px;"
					/>
					<?php endif; ?>
				</div>
				<?php endif; ?>
			</article>

		</div><!-- .lp-narrative -->

		<!-- Right: sticky viewport — PHP-rendered layers, JS crossfades only -->
		<div class="lp-viewport-col" aria-hidden="true">
			<div id="lp-sticky-viewport">
				<div id="lp-viewport-inner">
					<?php foreach ( $pane_products as $pane_idx => $prd ) : ?>
						<?php
						$img_path    = ! empty( $prd['front_model_image'] )
						? ltrim( str_replace( 'assets/', '', $prd['front_model_image'] ), '/' )
						: '';
						$product_url = (string) get_permalink( wc_get_product_id_by_sku( $prd['sku'] ) );
						?>
					<div
						class="lp-vp__layer<?php echo 0 === $pane_idx ? ' lp-vp__layer--visible' : ''; ?>"
						data-pane="<?php echo absint( $pane_idx ); ?>"
						<?php echo 0 !== $pane_idx ? 'aria-hidden="true"' : ''; ?>
					>
						<?php if ( $img_path ) : ?>
						<div class="lp-vp__img-wrap">
							<img
								class="lp-vp__img"
								src="<?php echo esc_url( $assets . $img_path ); ?>"
								alt="<?php echo esc_attr( $prd['name'] ); ?>"
								loading="<?php echo 0 === $pane_idx ? 'eager' : 'lazy'; ?>"
								decoding="async"
							/>
						</div>
						<?php endif; ?>
						<div class="lp-vp__product-footer">
							<div>
								<span class="lp-vp__sku"><?php echo esc_html( strtoupper( $prd['sku'] ) ); ?></span>
								<p class="lp-vp__name"><?php echo esc_html( $prd['name'] ); ?></p>
								<p class="lp-vp__price">
									<?php echo esc_html( '$' . number_format( (float) $prd['price'], 0 ) ); ?>
								</p>
							</div>
							<?php if ( $product_url ) : ?>
							<a href="<?php echo esc_url( $product_url ); ?>" class="lp-vp__cta">
								<?php echo esc_html( $prd['is_preorder'] ? __( 'Pre-Order', 'skyyrose' ) : __( 'Shop', 'skyyrose' ) ); ?>
							</a>
							<?php endif; ?>
						</div>
					</div>
					<?php endforeach; ?>
				</div><!-- #lp-viewport-inner -->
			</div><!-- #lp-sticky-viewport -->
		</div><!-- .lp-viewport-col -->

	</section><!-- .lp-split -->

	<!-- ================================================================
		Divider
	================================================================ -->
	<div class="lp-divider" aria-hidden="true">
		<span class="lp-divider__line"></span>
	</div>

	<!-- ================================================================
		Full product grid
	================================================================ -->
	<section
		class="lp-grid-section"
		id="product-grid"
		aria-label="<?php esc_attr_e( 'Love Hurts — Full Collection', 'skyyrose' ); ?>"
	>
		<header class="lp-grid-section__header lp-rv">
			<span class="lp-grid-section__eyebrow"><?php esc_html_e( 'The Full Collection', 'skyyrose' ); ?></span>
			<h2 class="lp-grid-section__title"><?php esc_html_e( 'Love Hurts', 'skyyrose' ); ?></h2>
			<p class="lp-grid-section__subtitle"><?php esc_html_e( 'For the love that survived everything.', 'skyyrose' ); ?></p>
		</header>

		<?php
		get_template_part(
			'template-parts/landing/product-grid',
			null,
			array(
				'collection' => 'love-hurts',
				'products'   => $lh_products,
			)
		);
		?>
	</section>

	<!-- ================================================================
		Email CTA
	================================================================ -->
	<section
		class="lp-email-section"
		aria-label="<?php esc_attr_e( 'Stay connected', 'skyyrose' ); ?>"
	>
		<div class="lp-email__inner lp-rv">
			<span class="lp-email__eyebrow"><?php esc_html_e( 'Stay Connected', 'skyyrose' ); ?></span>
			<h2 class="lp-email__title">
				<?php esc_html_e( 'Love never left. Neither should you.', 'skyyrose' ); ?>
			</h2>
			<p class="lp-email__subtitle">
				<?php esc_html_e( 'New drops, restocks, and stories — straight to your inbox.', 'skyyrose' ); ?>
			</p>
			<form class="lp-email__form" novalidate>
				<label class="lp-sr-only" for="lp-email-lh">
					<?php esc_html_e( 'Email address', 'skyyrose' ); ?>
				</label>
				<input
					class="lp-email__input"
					type="email"
					id="lp-email-lh"
					name="email"
					autocomplete="email"
					placeholder="<?php esc_attr_e( 'your@email.com', 'skyyrose' ); ?>"
					required
				/>
				<button type="submit" class="lp-btn lp-btn--primary">
					<?php esc_html_e( 'Subscribe', 'skyyrose' ); ?>
				</button>
			</form>
			<p class="lp-email__status" aria-live="polite"></p>
		</div>
	</section>

</main><!-- #primary -->

<?php get_footer(); ?>
