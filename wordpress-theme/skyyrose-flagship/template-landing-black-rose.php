<?php
/**
 * Template Name: Landing — Black Rose
 * Template Post Type: page
 *
 * V3 split-scrollytell port. PHP renders all viewport layers server-side.
 * landing-scrollytell.js handles scroll-sync only (no innerHTML, no GSAP).
 *
 * @package SkyyRose
 * @since   1.2.0
 */

defined( 'ABSPATH' ) || exit;

$assets       = trailingslashit( SKYYROSE_ASSETS_URI );
$all_products = skyyrose_get_collection_products( 'black-rose' );

// Featured panes — SKUs pinned to the pane copy below. The copy names
// specific garments (Sherpa, Oakland baseball, football, basketball,
// hockey); slicing collection order would pair copy with the wrong product.
// Resolved via the catalog (SKU-keyed); skyyrose_get_collection_products()
// returns a numerically indexed array.
$featured_skus = array( 'br-006', 'br-012', 'br-009', 'br-010', 'br-011' );
$catalog       = skyyrose_get_product_catalog();
$featured      = array();
foreach ( $featured_skus as $featured_sku ) {
	if ( isset( $catalog[ $featured_sku ] ) ) {
		$featured[] = $catalog[ $featured_sku ];
	}
}

// Pane copy — BR armor register.
$pane_copy = array(
	0 => array(
		'heading' => 'Engineered Warmth.',
		'body'    => 'The Sherpa Jacket isn&#8217;t insulation. It&#8217;s armor with a lining. Built for the cold you carry in.',
	),
	1 => array(
		'heading' => 'Rep Your Block.',
		'body'    => 'The Baseball Jersey started on diamonds. It belongs to Oakland now. Wear the city on your back.',
	),
	2 => array(
		'heading' => 'Built Different.',
		'body'    => 'The Football Jersey is cut for the ones who show up every game, every practice, every time.',
	),
	3 => array(
		'heading' => 'Court-Ready.',
		'body'    => 'The Basketball Jersey moves with you. Lightweight. Ventilated. Made for the ones who never sit down.',
	),
	4 => array(
		'heading' => 'Ice Cold.',
		'body'    => 'The Hockey Jersey carries weight. So do you. Black Rose doesn&#8217;t do decoration — only proof.',
	),
);

get_header();
?>
<main
	id="lp-main"
	class="lp-main"
	data-collection="black-rose"
>
	<?php
	// ── Hero ───────────────────────────────────────────────────────────
	// Above the fold — no lp-rv reveal classes here: the lockup is the mobile
	// LCP element, and a hidden resting state stalls LCP behind the deferred
	// JS queue (the PDP 24.9s bug class). Below-fold sections keep reveals. Wave 5.
	?>
	<section class="lp-hero" aria-label="<?php esc_attr_e( 'Black Rose collection', 'skyyrose' ); ?>">
		<div class="lp-hero__inner">

			<?php // Lockup image IS the collection name — never type-rendered. ?>
			<div class="lp-hero__lockup">
				<picture>
					<source
						srcset="<?php echo esc_url( $assets . 'images/hero-overlays/br-brand-script-logotype.avif' ); ?>"
						type="image/avif"
					>
					<source
						srcset="<?php echo esc_url( $assets . 'images/hero-overlays/br-brand-script-logotype.webp' ); ?>"
						type="image/webp"
					>
					<img
						src="<?php echo esc_url( $assets . 'images/hero-overlays/br-brand-script-logotype.png' ); ?>"
						alt="<?php esc_attr_e( 'Black Rose', 'skyyrose' ); ?>"
						class="lp-hero__lockup-img"
						width="640"
						height="160"
						loading="eager"
						fetchpriority="high"
					>
				</picture>
			</div>

			<p class="lp-hero__subtitle">
				<?php esc_html_e( 'Built from what was broken. Worn as proof.', 'skyyrose' ); ?>
			</p>

			<div class="lp-hero__ctas">
				<a
					href="#lp-split"
					class="lp-btn lp-btn--primary btn-sweep"
				><?php esc_html_e( 'Explore the Collection', 'skyyrose' ); ?></a>
				<?php
				$_br_col_page = get_page_by_path( 'collection-black-rose' );
				$_br_col_url  = $_br_col_page ? get_permalink( $_br_col_page ) : home_url( '/collections/black-rose/' );
				?>
				<a
					href="<?php echo esc_url( $_br_col_url ); ?>"
					class="lp-btn lp-btn--ghost"
				><?php esc_html_e( 'Shop All Black Rose', 'skyyrose' ); ?></a>
			</div>

		</div>

		<?php // Atmospheric image (visual-manifest.json: black-rose → atmosphere). ?>
		<div class="lp-hero__atmosphere" aria-hidden="true">
			<?php
			// Round-4: this img is the page's measured mobile LCP element —
			// fetchpriority=high pairs with the exact-URL preload emitted by
			// skyyrose_preload_template_lcp() (inc/enqueue-performance.php).
			?>
			<img
				src="<?php echo esc_url( $assets . 'images/logos/black-roses-cloud-cluster.webp' ); ?>"
				alt=""
				class="lp-hero__atmosphere-img"
				width="1200"
				height="700"
				loading="eager"
				fetchpriority="high"
			>
		</div>
	</section>

	<?php // ── Split scrollytell ─────────────────────────────────────────────── ?>
	<section
		id="lp-split"
		class="lp-split"
		aria-label="<?php esc_attr_e( 'Black Rose product stories', 'skyyrose' ); ?>"
	>

		<?php // Sticky viewport (desktop only; hidden on mobile via CSS). ?>
		<div class="lp-viewport-col" aria-hidden="true">
			<div id="lp-viewport-inner" class="lp-viewport-inner">

				<?php foreach ( $featured as $idx => $prd ) : ?>
					<?php
					$img_src  = ! empty( $prd['front_model_image'] ) ? skyyrose_product_image_uri( $prd['front_model_image'] ) : '';
					$prd_url  = function_exists( 'wc_get_product_id_by_sku' )
						? (string) get_permalink( wc_get_product_id_by_sku( $prd['sku'] ) )
						: '#';
					$is_first = ( 0 === $idx );
					?>
					<div
						class="lp-vp__layer<?php echo $is_first ? ' lp-vp__layer--visible' : ''; ?>"
						data-pane="<?php echo esc_attr( (string) $idx ); ?>"
						<?php echo $is_first ? '' : 'aria-hidden="true"'; ?>
					>
						<?php if ( $img_src ) : ?>
							<img
								src="<?php echo esc_url( $img_src ); ?>"
								alt="<?php echo esc_attr( $prd['name'] ); ?>"
								class="lp-vp__img"
								width="600"
								height="750"
								<?php
								/*
								 * Wave 9: ALL panes lazy — the sticky viewport column is
								 * display:none on mobile, yet the first pane's eager 235KB
								 * raw webp fetched at Medium priority inside the mobile LCP
								 * window (round-8). Lazy imgs inside a hidden column never
								 * intersect, so mobile skips the fetch entirely; on desktop
								 * the scrollytell sits below the hero (LCP = atmosphere img,
								 * verified round-8 desktop) and loads on scroll approach.
								 */
								?>
								loading="lazy"
							>
						<?php endif; ?>
						<div class="lp-vp__meta">
							<span class="lp-vp__name"><?php echo esc_html( $prd['name'] ); ?></span>
							<span class="lp-vp__price">$<?php echo esc_html( $prd['price'] ); ?></span>
						</div>
						<a
							href="<?php echo esc_url( $prd_url ); ?>"
							class="lp-vp__cta btn-sweep"
						>
							<?php
							if ( ! empty( $prd['is_preorder'] ) && '1' === (string) $prd['is_preorder'] ) {
								esc_html_e( 'Pre-Order', 'skyyrose' );
							} else {
								esc_html_e( 'Shop Now', 'skyyrose' );
							}
							?>
						</a>
					</div>
				<?php endforeach; ?>

				<?php // Skeleton shimmer shown before first pane intersects. ?>
				<div class="lp-vp__skeleton" aria-hidden="true"></div>

			</div><!-- #lp-viewport-inner -->
		</div><!-- .lp-viewport-col -->

		<?php // Narrative column — scroll driver. ?>
		<div class="lp-narrative-col">

			<ol
				class="lp-pane-indicators"
				aria-label="<?php esc_attr_e( 'Product navigation', 'skyyrose' ); ?>"
			>
				<?php foreach ( $featured as $idx => $prd ) : ?>
					<li>
						<button
							class="lp-pane-indicator<?php echo ( 0 === $idx ) ? ' is-active' : ''; ?>"
							aria-label="<?php echo esc_attr( $prd['name'] ); ?>"
							<?php echo ( 0 === $idx ) ? 'aria-current="true"' : ''; ?>
						></button>
					</li>
				<?php endforeach; ?>
			</ol>

			<?php foreach ( $featured as $idx => $prd ) : ?>
				<?php
				$copy    = isset( $pane_copy[ $idx ] ) ? $pane_copy[ $idx ] : array(
					'heading' => $prd['name'],
					'body'    => '',
				);
				$img_src = ! empty( $prd['front_model_image'] ) ? skyyrose_product_image_uri( $prd['front_model_image'] ) : '';
				$prd_url = function_exists( 'wc_get_product_id_by_sku' )
					? (string) get_permalink( wc_get_product_id_by_sku( $prd['sku'] ) )
					: '#';
				?>
				<article
					class="lp-narrative__pane"
					data-pane-index="<?php echo esc_attr( (string) $idx ); ?>"
					aria-label="<?php echo esc_attr( $prd['name'] ); ?>"
				>
					<?php // Mobile product image — visible only on narrow viewports. ?>
					<?php if ( $img_src ) : ?>
						<div class="lp-pane__mobile-product" aria-hidden="true">
							<img
								src="<?php echo esc_url( $img_src ); ?>"
								alt="<?php echo esc_attr( $prd['name'] ); ?>"
								class="lp-pane__mobile-img"
								width="480"
								height="600"
								loading="lazy"
							>
						</div>
					<?php endif; ?>

					<div class="lp-pane__content">
						<h2 class="lp-pane__heading lp-rv">
							<?php echo esc_html( $copy['heading'] ); ?>
						</h2>
						<p class="lp-pane__body lp-rv">
							<?php echo wp_kses_post( $copy['body'] ); ?>
						</p>
						<div class="lp-pane__product-meta lp-rv">
							<span class="lp-pane__product-name"><?php echo esc_html( $prd['name'] ); ?></span>
							<span class="lp-pane__product-price">$<?php echo esc_html( $prd['price'] ); ?></span>
						</div>
						<a
							href="<?php echo esc_url( $prd_url ); ?>"
							class="lp-btn lp-btn--primary lp-rv btn-sweep"
						>
							<?php
							if ( ! empty( $prd['is_preorder'] ) && '1' === (string) $prd['is_preorder'] ) {
								esc_html_e( 'Pre-Order', 'skyyrose' );
							} else {
								esc_html_e( 'Shop Now', 'skyyrose' );
							}
							?>
						</a>
					</div>
				</article>
			<?php endforeach; ?>

		</div><!-- .lp-narrative-col -->

	</section><!-- #lp-split -->

	<?php // Screen-reader live region for pane announcements. ?>
	<div
		id="lp-live-region"
		class="screen-reader-text"
		aria-live="polite"
		aria-atomic="true"
	></div>

	<?php // Divider ?>
	<div class="lp-section-divider" aria-hidden="true"></div>

	<?php // ── Full product grid ─────────────────────────────────────────────── ?>
	<?php
	get_template_part(
		'template-parts/landing/product-grid',
		null,
		array(
			'collection' => 'black-rose',
			'skus'       => wp_list_pluck( $all_products, 'sku' ),
		)
	);
	?>

	<?php // ── Email CTA ─────────────────────────────────────────────────────── ?>
	<section
		class="lp-email lp-rv"
		aria-label="<?php esc_attr_e( 'Join the Black Rose list', 'skyyrose' ); ?>"
	>
		<div class="lp-email__inner">
			<h2 class="lp-email__heading lp-rv">
				<?php esc_html_e( 'Stay in the Dark.', 'skyyrose' ); ?>
			</h2>
			<p class="lp-email__subheading lp-rv">
				<?php esc_html_e( 'Drop alerts and early access — Black Rose inner circle only.', 'skyyrose' ); ?>
			</p>
			<div class="lp-email__form-wrap">
				<form
					id="lp-email-br"
					class="lp-email__form"
					novalidate
				>
					<label
						for="lp-email-br-input"
						class="screen-reader-text"
					><?php esc_html_e( 'Your email address', 'skyyrose' ); ?></label>
					<?php wp_nonce_field( 'skyyrose_newsletter', 'skyyrose_newsletter_nonce' ); ?>
					<input
						id="lp-email-br-input"
						type="email"
						class="lp-email__input"
						placeholder="<?php esc_attr_e( 'your@email.com', 'skyyrose' ); ?>"
						autocomplete="email"
						required
					>
					<button
						type="submit"
						class="lp-btn lp-btn--primary btn-sweep"
					><?php esc_html_e( 'Get Access', 'skyyrose' ); ?></button>
				</form>
				<p class="lp-email__status" aria-live="polite"></p>
			</div>
		</div>
	</section>

</main><!-- #lp-main -->
<?php get_footer(); ?>
