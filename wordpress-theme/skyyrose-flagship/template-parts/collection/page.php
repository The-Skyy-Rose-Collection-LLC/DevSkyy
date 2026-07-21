<?php
/**
 * Collection Page — Unified Layout
 *
 * Shared template part for all collection pages. Receives the collection
 * slug via $args['slug'] and renders the full page from data returned by
 * skyyrose_get_collection_content().
 *
 * Handles kids-capsule differences: no hero bg image, h1 title instead
 * of logo, no 3D experience link, pre-order product URLs, product count.
 *
 * @package SkyyRose
 * @since   6.5.0
 */

defined( 'ABSPATH' ) || exit;

$slug = isset( $args['slug'] ) ? sanitize_key( $args['slug'] ) : '';
$c    = skyyrose_get_collection_content( $slug );

if ( ! $c ) {
	// Hard-fail: log + emit hidden error marker. Silent return previously
	// masked a missing kids-capsule config — caught only after a structural
	// audit ran. data-skyyrose-error is a project-wide beacon picked up by
	// scripts/verify_live_structure.py to fail deploys on render regressions.
	error_log(
		sprintf(
			"[SkyyRose Collections] Missing content config for slug '%s' in %s. Check inc/collection-content.php.",
			$slug,
			__FILE__
		)
	);
	printf(
		'<div class="skyyrose-render-error" data-skyyrose-error="missing-collection-content" data-collection="%s" hidden></div>',
		esc_attr( $slug )
	);
	return;
}

/* ── Shared data ────────────────────────────────────────────────── */
$products  = skyyrose_get_collection_display_products( $slug );
$cross_nav = skyyrose_get_cross_nav( $slug );
$svg_kses  = skyyrose_svg_kses();
$has_wc    = function_exists( 'wc_get_cart_url' );
$is_kids   = ( 'kids-capsule' === $slug );
$has_3d    = ! empty( $c['experience_url'] );

/*
 * SOT-first image resolution (S-5).
 * skyyrose_sot_hero()   → imagery.hero_backdrop.resolved   (maps to hero_bg)
 * skyyrose_sot_lockup() → lockup.display_webp.resolved     (maps to hero_logo)
 * Falls back to the hand-maintained $c values when SOT returns ''.
 */
$sot_hero_bg   = function_exists( 'skyyrose_sot_hero' ) ? skyyrose_sot_hero( $slug ) : '';
$sot_hero_logo = function_exists( 'skyyrose_sot_lockup' ) ? skyyrose_sot_lockup( $slug ) : '';

$resolved_hero_bg   = ( '' !== $sot_hero_bg ) ? $sot_hero_bg : ( $c['hero_bg'] ?? '' );
$resolved_hero_logo = ( '' !== $sot_hero_logo ) ? $sot_hero_logo : ( $c['hero_logo'] ?? '' );

$has_hero_bg = ! empty( $resolved_hero_bg );
$has_logo    = ! empty( $resolved_hero_logo );

// Collection emblem (3D star-rose mark) — file-existence gated, so only
// collections that have an emblem asset render it. Decorative; aria-hidden.
$emblem_rel = '/images/emblems/' . $slug . '-emblem.webp';
$has_emblem = file_exists( get_theme_file_path( 'assets' . $emblem_rel ) );

/* Kids Capsule uses pre-order URL for product links */
$preorder_url  = $is_kids ? home_url( '/pre-order/' ) : '';
$product_count = $is_kids ? count( $products ) : 0;

/* CTA shop link */
$cta_url = $has_wc ? wc_get_cart_url() : ( $is_kids ? $preorder_url : home_url( '/shop/' ) );
?>

<div class="col-page" data-collection="<?php echo esc_attr( $slug ); ?>">

	<!-- ════ Hero ════ -->
	<section class="col-hero ambient-glow" data-scroll-fade>
		<?php
		if ( $has_hero_bg ) :
			$hero_bg_base = isset( $c['hero_bg_base'] ) ? (string) $c['hero_bg_base'] : '';
			$hero_srcset  = '';
			if ( '' !== $hero_bg_base ) {
				$widths  = array( 480, 768, 1280, 1680 );
				$entries = array();
				foreach ( $widths as $w ) {
					$entries[] = esc_url( SKYYROSE_ASSETS_URI . $hero_bg_base . '-' . $w . 'w.webp' ) . ' ' . $w . 'w';
				}
				$hero_srcset = implode( ', ', $entries );
			}
			?>
			<div class="col-hero__bg parallax-ken-burns">
				<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . $resolved_hero_bg . '?v=' . SKYYROSE_VERSION ); ?>"
					<?php
					if ( '' !== $hero_srcset ) :
						?>
						srcset="<?php echo esc_attr( $hero_srcset ); ?>" sizes="100vw"<?php endif; ?>
					alt="<?php echo esc_attr( $c['hero_bg_alt'] ); ?>"
					<?php
					// decoding=sync (Wave 7): this img is the measured mobile LCP
					// on BR/LH/SIG. Round 6: bytes arrive High-priority at
					// ~150ms, yet render delay ran 0.6-3.3s — under 4x CPU
					// throttle an async decode slips behind the gsap/page-script
					// queue to a later frame. Sync ties decode to the first
					// paint attempt. LCP img only — everything else stays async.
					?>
					loading="eager" fetchpriority="high" decoding="sync" width="1680" height="720">
			</div>
		<?php endif; ?>
		<?php
		// The whole hero is the first mobile viewport (col-hero is 100dvh) — no
		// reveal classes anywhere inside it: a hidden resting state on this
		// wrapper stalled LCP behind the deferred JS queue (round-4 Lighthouse:
		// 2.4s render delay = the 0.8s srRevealSafety net, not first paint).
		// Below-fold sections keep reveals. Wave 5.
		?>
		<div class="col-hero__content">
			<?php
			if ( $has_emblem ) :
				// Emblem renders ≤154px wide (height clamp(120px,18vh,210px) at 220:300
				// ratio, collection-pages.css) but ships full-size (26-34KB, round-3
				// uses-responsive-images). Photon width variants; '' = plain img as before.
				$emblem_srcset = function_exists( 'skyyrose_photon_srcset' )
					? skyyrose_photon_srcset( SKYYROSE_ASSETS_URI . $emblem_rel, array( 160, 320, 480 ) )
					: '';
				?>
				<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . $emblem_rel . '?v=' . SKYYROSE_VERSION ); ?>"
					<?php if ( '' !== $emblem_srcset ) : ?>
						srcset="<?php echo esc_attr( $emblem_srcset ); ?>"
						sizes="154px"
					<?php endif; ?>
					alt="" aria-hidden="true" class="col-hero__emblem" width="220" height="300" loading="eager" decoding="async">
				<?php endif; ?>
				<span class="col-hero__badge"><?php echo esc_html( $c['hero_badge'] ); ?></span>
			<?php if ( $has_logo ) : ?>
				<?php
				// F3 (v1.5.4): Black Rose gets a scroll-timeline bloom on the
				// hero logo — image blurs + scales in coupled to scroll, not
				// triggered once by IntersectionObserver. Reduced-motion respected.
				// NO rv-clip-up here: this lockup IS the mobile LCP element on
				// BR/LH (audit Wave 2) — a reveal class hides it until deferred
				// JS runs, stalling LCP behind the whole script queue (the PDP
				// 24.9s bug class, fix-log Wave 1). Scroll-bloom is CSS-only
				// (scroll-timeline), so it keeps first paint intact.
				$hero_logo_class = 'col-hero__logo' . ( 'black-rose' === $slug ? ' rv-scroll-bloom' : '' );
				// Photon width variants for the single-res lockup (199-417KB at
				// 1600px, the mobile LCP element — audit Wave 2). Fallback src
				// stays direct, so no Photon = today's behavior.
				$hero_logo_srcset = function_exists( 'skyyrose_photon_srcset' )
					? skyyrose_photon_srcset( SKYYROSE_ASSETS_URI . $resolved_hero_logo, array( 480, 640, 720, 960, 1280 ) )
					: '';
				?>
				<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . $resolved_hero_logo . '?v=' . SKYYROSE_VERSION ); ?>"
					<?php if ( '' !== $hero_logo_srcset ) : ?>
						srcset="<?php echo esc_attr( $hero_logo_srcset ); ?>"
						sizes="(max-width: 768px) 90vw, 720px"
					<?php endif; ?>
					alt="<?php echo esc_attr( $c['hero_logo_alt'] ); ?>"
					class="<?php echo esc_attr( $hero_logo_class ); ?>" width="<?php echo esc_attr( $c['hero_logo_w'] ); ?>" height="<?php echo esc_attr( $c['hero_logo_h'] ); ?>" loading="eager" fetchpriority="high" decoding="async">
				<h1 class="screen-reader-text"><?php echo esc_html( $c['hero_logo_alt'] ); ?></h1>
			<?php else : ?>
				<h1 class="col-hero__title"><span><?php echo esc_html( $c['hero_title'] ); ?></span></h1>
			<?php endif; ?>
			<p class="col-hero__tagline"><?php echo esc_html( $c['hero_tagline'] ); ?></p>
			<p class="col-hero__subtitle"><?php echo esc_html( $c['hero_subtitle'] ); ?></p>
			<div class="col-hero__cta-group">
				<a href="#shop" class="col-hero__cta col-hero__cta--primary btn-sweep btn-press"><?php esc_html_e( 'Shop the Collection', 'skyyrose' ); ?></a>
				<?php if ( $has_3d ) : ?>
					<?php
					// Experience merged into this page (WS3): anchor URLs ('#experience')
					// link in-page; anything else still routes through home_url().
					$exp_href = ( 0 === strpos( $c['experience_url'], '#' ) )
						? $c['experience_url']
						: home_url( $c['experience_url'] );
					?>
					<a href="<?php echo esc_url( $exp_href ); ?>" class="col-hero__cta col-hero__cta--secondary btn-border-draw btn-press"><?php echo esc_html( $c['hero_3d_label'] ); ?></a>
				<?php endif; ?>
			</div>
		</div>
		<div class="col-hero__scroll" aria-hidden="true"><span><?php echo esc_html( $c['hero_scroll_text'] ); ?></span><span>&#x2193;</span></div>
	</section>

	<!-- ════ Experience Layer (merged immersive world — WS3) ════ -->
	<?php
	$experience = function_exists( 'skyyrose_get_experience_config' ) ? skyyrose_get_experience_config( $slug ) : null;
	if ( $experience && ! empty( $experience['rooms'] ) ) :
		?>
		<section id="experience" class="col-experience" aria-label="<?php echo esc_attr( $experience['world_name'] ); ?>">
			<?php
			get_template_part(
				'template-parts/immersive/scene',
				null,
				array(
					'collection_slug' => $slug,
					'collection_name' => $experience['collection_name'],
					'world_name'      => $experience['world_name'],
					'tagline'         => $experience['tagline'],
					'accent_color'    => $experience['accent_color'],
					'collection_url'  => '',
					'rooms'           => $experience['rooms'],
					'embedded'        => true,
				)
			);
			?>
		</section>
	<?php endif; ?>

	<?php
	get_template_part(
		'template-parts/pin-narrative',
		null,
		array(
			'slug'     => $slug,
			'beats'    => isset( $c['pin_beats'] ) ? $c['pin_beats'] : array(),
			// Reuses the same $products list the grid below renders — no
			// second catalog/WC query — so the narrative's closing beat can
			// spotlight the collection's flagship piece instead of ending
			// on empty stage space (founder: "it's just wasted space").
			'products' => $products,
		)
	);
	?>

	<!-- ════ Lookbook (editorial imagery, narrative → shop bridge) ════ -->
	<?php
	$lookbook_by_collection = array(
		'signature'    => array(
			array(
				'file' => 'lb-rose-hoodie-beanie',
				'alt'  => __( 'Rose hoodie and beanie, worn — Signature editorial', 'skyyrose' ),
			),
		),
		'black-rose'   => array(
			array(
				'file' => 'lb-black-rose-football',
				'alt'  => __( 'Black Rose football jersey, worn — editorial', 'skyyrose' ),
			),
			array(
				'file' => 'lb-black-rose-hockey',
				'alt'  => __( 'Black Rose hockey jersey, worn — editorial', 'skyyrose' ),
			),
		),
		'love-hurts'   => array(
			array(
				'file' => 'lb-love-hurts-varsity',
				'alt'  => __( 'Love Hurts varsity jacket, worn — editorial', 'skyyrose' ),
			),
		),
		'kids-capsule' => array(
			array(
				'file' => 'lb-kid-black-rose',
				'alt'  => __( 'Child wearing a Black Rose piece — Kids Capsule editorial', 'skyyrose' ),
			),
		),
	);
	$lookbook_images        = $lookbook_by_collection[ $slug ] ?? array();
	$lookbook_grid_class    = 'col-lookbook__grid' . ( count( $lookbook_images ) > 1 ? ' col-lookbook__grid--2up' : '' );
	if ( ! empty( $lookbook_images ) ) :
		?>
		<section class="col-lookbook rv-clip-up" aria-label="<?php esc_attr_e( 'Lookbook', 'skyyrose' ); ?>" style="content-visibility:auto;contain-intrinsic-size:0 500px;">
			<div class="<?php echo esc_attr( $lookbook_grid_class ); ?>">
				<?php foreach ( $lookbook_images as $lb ) : ?>
					<figure class="col-lookbook__figure">
						<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/lookbook/' . $lb['file'] . '-960w.webp?v=' . SKYYROSE_VERSION ); ?>"
							alt="<?php echo esc_attr( $lb['alt'] ); ?>"
							loading="lazy" decoding="async" width="960" height="1200" class="col-lookbook__img">
					</figure>
				<?php endforeach; ?>
			</div>
		</section>
	<?php endif; ?>

	<!-- ════ Feature Scroll (sticky image + scrolling philosophy items) ════ -->
	<?php
	get_template_part(
		'template-parts/collection/feature-scroll',
		null,
		array(
			'slug'    => $slug,
			'content' => $c,
		)
	);
	?>

	<!-- ════ Product Grid (immediately after hero) ════ -->
	<?php
	// Build subheading: kids-capsule uses a dynamic piece count, others
	// use the static copy from skyyrose_get_collection_content().
	if ( $is_kids ) {
		$products_subheading = sprintf(
			/* translators: %d: product count */
			_n( '%d Piece', '%d Pieces', $product_count, 'skyyrose' ),
			$product_count
		) . ' · ' . __( 'Limited Run', 'skyyrose' );
	} else {
		$products_subheading = $c['products_subheading'] ?? '';
	}

	get_template_part(
		'template-parts/product-grid',
		null,
		array(
			'products'      => $products,
			'collection'    => $slug,
			'heading'       => __( 'The Collection', 'skyyrose' ),
			'subheading'    => $products_subheading,
			'section_id'    => 'shop',
			'section_class' => 'col-products',
			'reveal_class'  => 'rv-clip-up',
			'permalink'     => $is_kids ? $preorder_url : '',
		)
	);
	?>

	<?php // Founder pull quote — Corey's voice. Black Rose + Signature (origin/heritage register). ?>
	<?php
	if ( 'black-rose' === $slug ) {
		get_template_part( 'template-parts/collection/founder-pullquote' );
	} elseif ( 'signature' === $slug ) {
		get_template_part(
			'template-parts/collection/founder-pullquote',
			null,
			array(
				'quote_text' => isset( $c['quote_text'] ) ? $c['quote_text'] : '',
				'quote_name' => __( 'Corey Foster', 'skyyrose' ),
				'quote_role' => __( 'Founder · The origin', 'skyyrose' ),
			)
		);
	}
	?>

	<!-- ════ Story (condensed — after products) ════ -->
	<section class="col-story rv-clip-up">
		<div class="col-story__grid">
			<div class="col-story__content">
				<span class="col-story__label"><?php echo esc_html( $c['story_label'] ); ?></span>
				<h2 class="col-story__title"><?php echo esc_html( $c['story_title'] ); ?></h2>
				<p class="col-story__text"><?php echo esc_html( $c['story_text_1'] ); ?></p>
				<blockquote class="col-story__quote"><?php echo esc_html( $c['story_quote'] ); ?></blockquote>
			</div>
		</div>
	</section>

	<!-- ════ CTA ════ -->
	<section class="col-cta rv-blur">
		<h2 class="col-cta__title"><?php echo esc_html( $c['cta_title'] ); ?></h2>
		<p class="col-cta__text"><?php echo esc_html( $c['cta_text'] ); ?></p>
		<a href="<?php echo esc_url( $cta_url ); ?>" class="col-cta__btn"><?php echo esc_html( $c['cta_btn'] ); ?></a>
	</section>

	<!-- ════ Cross-Collection Nav ════ -->
	<nav class="col-crossnav rv-clip-up" aria-label="<?php esc_attr_e( 'Other collections', 'skyyrose' ); ?>">
		<h3 class="col-crossnav__heading"><?php esc_html_e( 'Explore More Collections', 'skyyrose' ); ?></h3>
		<div class="col-crossnav__grid stagger-grid">
			<?php foreach ( $cross_nav as $nav ) : ?>
				<?php // No aria-label: the accessible name computes from the visible h3 + p content (WCAG 2.5.3 — an override here dropped the visible text from the name). ?>
				<a href="<?php echo esc_url( $nav['url'] ); ?>" class="col-crossnav__link <?php echo esc_attr( $nav['class'] ); ?>">
					<h3><?php echo esc_html( $nav['name'] ); ?></h3>
					<p><?php echo esc_html( $nav['desc'] ); ?></p>
				</a>
			<?php endforeach; ?>
		</div>
	</nav>

	<!-- ════ Newsletter ════ -->
	<section class="col-newsletter rv-blur">
		<h2 class="col-newsletter__title"><?php esc_html_e( 'Join the Inner Circle', 'skyyrose' ); ?></h2>
		<p class="col-newsletter__text"><?php echo esc_html( $c['newsletter_text'] ); ?></p>
		<form class="col-newsletter__form" aria-label="<?php esc_attr_e( 'Newsletter signup', 'skyyrose' ); ?>">
			<label class="screen-reader-text" for="<?php echo esc_attr( $c['email_id'] ); ?>"><?php esc_html_e( 'Email address', 'skyyrose' ); ?></label>
			<input type="email" id="<?php echo esc_attr( $c['email_id'] ); ?>" class="col-newsletter__input" placeholder="<?php esc_attr_e( 'Enter your email', 'skyyrose' ); ?>" required>
			<button type="submit" class="col-newsletter__submit"><?php esc_html_e( 'Join', 'skyyrose' ); ?></button>
		</form>
	</section>

</div><!-- .col-page -->
