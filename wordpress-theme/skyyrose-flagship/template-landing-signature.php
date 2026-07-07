<?php
/**
 * Template Name: Landing — Signature
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
$all_products = skyyrose_get_collection_products( 'signature' );

// Featured panes — curated 5 from Signature collection.
$featured_skus = array( 'sg-001', 'sg-002', 'sg-015', 'sg-007', 'sg-012' );
$catalog       = skyyrose_get_product_catalog();
$featured      = array();
foreach ( $featured_skus as $sku ) {
	if ( isset( $catalog[ $sku ] ) ) {
		$featured[] = $catalog[ $sku ];
	}
}

// Pane copy — SIG "Not basics. Blueprints." register.
$pane_copy = array(
	0 => array(
		'heading' => 'The Standard.',
		'body'    => 'The Bay Bridge Shorts aren&#8217;t basics. They&#8217;re blueprints. Cut from the city that taught you to build.',
	),
	1 => array(
		'heading' => 'Stay Golden.',
		'body'    => 'The Stay Golden Shirt carries the block on its chest. Lightweight. Intentional. Made to be seen.',
	),
	2 => array(
		'heading' => 'The Set.',
		'body'    => 'Windbreaker Set — two pieces that move together. Wear the whole plan or wear the parts. Either way, it works.',
	),
	3 => array(
		'heading' => 'Head Canon.',
		'body'    => 'The Beanie is the punctuation mark. Pull it on and the fit is finished. No basics here.',
	),
	4 => array(
		'heading' => 'Original Label.',
		'body'    => 'The Original Label Tee in Orchid. Soft enough to live in. Sharp enough to mean something.',
	),
);

get_header();
?>
<main
	id="lp-main"
	class="lp-main"
	data-collection="signature"
>
	<?php // ── Hero ─────────────────────────────────────────────────────────── ?>
	<section class="lp-hero lp-rv" aria-label="<?php esc_attr_e( 'Signature collection', 'skyyrose' ); ?>">
		<div class="lp-hero__inner">

			<?php // Lockup image IS the collection name — never type-rendered. ?>
			<div class="lp-hero__lockup lp-rv">
				<picture>
					<source
						srcset="<?php echo esc_url( $assets . 'images/hero-overlays/sig-brand-skyy-rose-gold.avif' ); ?>"
						type="image/avif"
					>
					<source
						srcset="<?php echo esc_url( $assets . 'images/hero-overlays/sig-brand-skyy-rose-gold.webp' ); ?>"
						type="image/webp"
					>
					<img
						src="<?php echo esc_url( $assets . 'images/hero-overlays/sig-brand-skyy-rose-gold.png' ); ?>"
						alt="<?php esc_attr_e( 'Signature', 'skyyrose' ); ?>"
						class="lp-hero__lockup-img"
						width="640"
						height="160"
						loading="eager"
						fetchpriority="high"
					>
				</picture>
			</div>

			<p class="lp-hero__subtitle lp-rv">
				<?php esc_html_e( 'Not basics. Blueprints.', 'skyyrose' ); ?>
			</p>

			<div class="lp-hero__ctas lp-rv">
				<a
					href="#lp-split"
					class="lp-btn lp-btn--primary btn-sweep"
				><?php esc_html_e( 'Explore the Collection', 'skyyrose' ); ?></a>
				<a
					href="
					<?php
					$_sig_col_page = get_page_by_path( 'collection-signature' );
					echo esc_url( $_sig_col_page ? get_permalink( $_sig_col_page ) : home_url( '/collections/signature/' ) );
					?>
					"
					class="lp-btn lp-btn--ghost"
				><?php esc_html_e( 'Shop All Signature', 'skyyrose' ); ?></a>
			</div>

		</div>

		<?php // Atmospheric image (visual-manifest.json: signature → atmosphere). ?>
		<div class="lp-hero__atmosphere" aria-hidden="true">
			<img
				src="<?php echo esc_url( $assets . 'images/homepage-col-signature.webp' ); ?>"
				alt=""
				class="lp-hero__atmosphere-img"
				width="1200"
				height="700"
				loading="eager"
			>
		</div>
	</section>

	<?php // ── Split scrollytell ─────────────────────────────────────────────── ?>
	<section
		id="lp-split"
		class="lp-split"
		aria-label="<?php esc_attr_e( 'Signature product stories', 'skyyrose' ); ?>"
	>

		<?php // Sticky viewport (desktop only; hidden on mobile via CSS). ?>
		<div class="lp-viewport-col" aria-hidden="true">
			<div id="lp-viewport-inner" class="lp-viewport-inner">

				<?php foreach ( $featured as $idx => $prd ) : ?>
					<?php
					$img_src  = ! empty( $prd['front_model_image'] )
						? skyyrose_product_image_uri( $prd['front_model_image'] )
						: '';
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
								loading="<?php echo $is_first ? 'eager' : 'lazy'; ?>"
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
				$img_src = ! empty( $prd['front_model_image'] )
					? skyyrose_product_image_uri( $prd['front_model_image'] )
					: '';
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
			'collection' => 'signature',
			'skus'       => wp_list_pluck( $all_products, 'sku' ),
		)
	);
	?>

	<?php // ── Email CTA ─────────────────────────────────────────────────────── ?>
	<section
		class="lp-email lp-rv"
		aria-label="<?php esc_attr_e( 'Join the Signature list', 'skyyrose' ); ?>"
	>
		<div class="lp-email__inner">
			<h2 class="lp-email__heading lp-rv">
				<?php esc_html_e( 'Build Your Blueprint.', 'skyyrose' ); ?>
			</h2>
			<p class="lp-email__subheading lp-rv">
				<?php esc_html_e( 'Early access and new drops — Signature subscribers first.', 'skyyrose' ); ?>
			</p>
			<div class="lp-email__form-wrap">
				<form
					id="lp-email-sig"
					class="lp-email__form"
					novalidate
				>
					<label
						for="lp-email-sig-input"
						class="screen-reader-text"
					><?php esc_html_e( 'Your email address', 'skyyrose' ); ?></label>
					<?php wp_nonce_field( 'skyyrose_newsletter', 'skyyrose_newsletter_nonce' ); ?>
					<input
						id="lp-email-sig-input"
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
