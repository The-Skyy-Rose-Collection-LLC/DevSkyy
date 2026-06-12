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
		<ol class="lp-pane-indicators" aria-label="<?php esc_attr_e( 'Navigate to pane', 'skyyrose' ); ?>">
			<?php for ( $d = 0; $d < 5; $d++ ) : ?>
			<li>
				<button
					class="lp-pane-indicator<?php echo 0 === $d ? ' is-active' : ''; ?>"
					aria-label="<?php echo esc_attr( sprintf( __( 'Pane %d', 'skyyrose' ), $d + 1 ) ); ?>"
					<?php echo 0 === $d ? 'aria-current="true"' : ''; ?>
				></button>
			</li>
			<?php endfor; ?>
		</ol>

		<!-- Left: narrative panes -->
		<div class="lp-narrative">

			<?php
			// Pane copy — LH narrative register.
			// Each entry maps to the corresponding index in $pane_products.
			$panes = array(
				0 => array(
					'number'     => '01 / 05',
					'eyebrow'    => __( 'The Statement Piece', 'skyyrose' ),
					'headline'   => __( 'Wear every chapter.', 'skyyrose' ),
					'body'       => __( 'Some love stories don\'t have clean endings. The Love Hurts Bomber Jacket carries that weight — embroidered devotion on the back, silence on the chest. Structured. Unforgettable.', 'skyyrose' ),
					'pull_quote' => __( '"You don\'t dress for the memories. You dress through them."', 'skyyrose' ),
					'details'    => array(
						__( 'Heavyweight satin shell', 'skyyrose' ),
						__( 'Embroidered back panel', 'skyyrose' ),
					),
					'price_fmt'  => 'from',
					'cta_label'  => __( 'View Jacket', 'skyyrose' ),
				),
				1 => array(
					'number'    => '02 / 05',
					'eyebrow'   => __( 'The Foundation', 'skyyrose' ),
					'headline'  => __( 'Soft outside. Carrying everything inside.', 'skyyrose' ),
					'body'      => __( 'Cotton-fleece joggers built for the long stretch — after the conversation, before the next decision. The Love Hurts wordmark embroidered at the left ankle. Crimson, black, and gold on dark.', 'skyyrose' ),
					'details'   => array(
						__( 'Mid-weight cotton-fleece', 'skyyrose' ),
						__( 'Ribbed ankle cuffs', 'skyyrose' ),
						__( 'Athletic fit', 'skyyrose' ),
					),
					'cta_label' => __( 'Shop Joggers', 'skyyrose' ),
				),
				2 => array(
					'number'    => '03 / 05',
					'eyebrow'   => __( 'The Move', 'skyyrose' ),
					'headline'  => __( 'Built for what you carry off the court.', 'skyyrose' ),
					'body'      => __( 'Basketball shorts that live past the game. The heart emblem at the inseam. Moisture-wicking shell. Every rep, every comeback, every day you showed up anyway.', 'skyyrose' ),
					'details'   => array(
						__( 'Moisture-wicking shell', 'skyyrose' ),
						__( 'Side-slit hem', 'skyyrose' ),
					),
					'cta_label' => __( 'Shop Shorts', 'skyyrose' ),
				),
				3 => array(
					'number'    => '04 / 05',
					'eyebrow'   => __( 'The Mirror', 'skyyrose' ),
					'headline'  => __( 'The same devotion. Different light.', 'skyyrose' ),
					'body'      => __( 'The white colorway of the Love Hurts Joggers. Crimson, black, and gold on white — the same emblem reading differently when you step into the room. A mirror of the black pair.', 'skyyrose' ),
					'details'   => array(
						__( 'Cotton-fleece, white colorway', 'skyyrose' ),
						__( 'Mirror of Love Hurts Joggers (Black)', 'skyyrose' ),
					),
					'cta_label' => __( 'Shop White Joggers', 'skyyrose' ),
				),
				4 => array(
					'number'    => '05 / 05',
					'eyebrow'   => __( 'The Detail', 'skyyrose' ),
					'headline'  => __( 'Even the small things carry it.', 'skyyrose' ),
					'body'      => __( 'The Fannie wears the Love Hurts logo at the front pocket. Worn across the body or around the waist, it\'s the accessory that finishes the set — quietly, without announcement.', 'skyyrose' ),
					'details'   => array(
						__( 'Love Hurts logo embroidery', 'skyyrose' ),
						__( 'Adjustable strap', 'skyyrose' ),
					),
					'cta_label' => __( 'Shop The Fannie', 'skyyrose' ),
				),
			);

			foreach ( $panes as $pane_idx => $pane ) :
				$prd     = isset( $pane_products[ $pane_idx ] ) ? $pane_products[ $pane_idx ] : null;
				$img_src = '';
				$prd_url = '#';
				if ( $prd ) {
					if ( ! empty( $prd['front_model_image'] ) ) {
						$img_src = esc_url( $assets . ltrim( str_replace( 'assets/', '', $prd['front_model_image'] ), '/' ) );
					}
					$prd_url = function_exists( 'wc_get_product_id_by_sku' )
						? (string) get_permalink( wc_get_product_id_by_sku( $prd['sku'] ) )
						: '#';
				}
				?>
			<article class="lp-narrative__pane lp-rv" data-pane-index="<?php echo absint( $pane_idx ); ?>">
				<p class="lp-pane__number"><?php echo esc_html( $pane['number'] ); ?></p>
				<p class="lp-pane__eyebrow"><?php echo esc_html( $pane['eyebrow'] ); ?></p>
				<h2 class="lp-pane__headline"><?php echo esc_html( $pane['headline'] ); ?></h2>
				<p class="lp-pane__body"><?php echo esc_html( $pane['body'] ); ?></p>
				<?php if ( ! empty( $pane['pull_quote'] ) ) : ?>
				<blockquote class="lp-pane__pull-quote"><?php echo esc_html( $pane['pull_quote'] ); ?></blockquote>
				<?php endif; ?>
				<?php if ( $prd ) : ?>
				<ul class="lp-pane__detail-list">
					<?php foreach ( $pane['details'] as $detail ) : ?>
					<li class="lp-pane__detail-item"><?php echo esc_html( $detail ); ?></li>
					<?php endforeach; ?>
					<li class="lp-pane__detail-item">
						<?php
						if ( ! empty( $pane['price_fmt'] ) && 'from' === $pane['price_fmt'] ) {
							echo esc_html( sprintf( __( 'From $%s', 'skyyrose' ), number_format( (float) $prd['price'], 0 ) ) );
						} else {
							echo esc_html( sprintf( __( '$%s', 'skyyrose' ), number_format( (float) $prd['price'], 0 ) ) );
						}
						?>
					</li>
				</ul>
				<a href="<?php echo esc_url( $prd_url ); ?>" class="lp-btn lp-btn--secondary">
					<?php echo esc_html( $pane['cta_label'] ); ?>
				</a>
				<div class="lp-pane__mobile-product" aria-hidden="true">
					<?php if ( $img_src ) : ?>
					<img
						class="lp-pane__mobile-img"
						src="<?php echo esc_url( $img_src ); ?>"
						alt="<?php echo esc_attr( $prd['name'] ); ?>"
						loading="lazy"
						decoding="async"
					/>
					<?php endif; ?>
				</div>
				<?php endif; ?>
			</article>
			<?php endforeach; ?>

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
						$product_url = function_exists( 'wc_get_product_id_by_sku' )
							? (string) get_permalink( wc_get_product_id_by_sku( $prd['sku'] ) )
							: '#';
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
			<picture class="lp-grid-section__lockup">
				<source
					srcset="<?php echo esc_url( $assets . 'images/hero-overlays/lh-logo-combined.avif' ); ?>"
					type="image/avif"
				/>
				<source
					srcset="<?php echo esc_url( $assets . 'images/hero-overlays/lh-logo-combined.webp' ); ?>"
					type="image/webp"
				/>
				<img
					src="<?php echo esc_url( $assets . 'images/hero-overlays/lh-logo-combined.webp' ); ?>"
					alt=""
					width="360"
					height="120"
					loading="lazy"
					decoding="async"
				/>
			</picture>
			<h2 class="screen-reader-text"><?php esc_html_e( 'Love Hurts Collection', 'skyyrose' ); ?></h2>
			<p class="lp-grid-section__subtitle"><?php esc_html_e( 'For the love that survived everything.', 'skyyrose' ); ?></p>
		</header>

		<?php
		get_template_part(
			'template-parts/landing/product-grid',
			null,
			array(
				'collection' => 'love-hurts',
				'skus'       => array_keys( $lh_products ),
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
				<?php wp_nonce_field( 'skyyrose_newsletter', 'skyyrose_newsletter_nonce' ); ?>
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
