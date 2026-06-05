<?php
/**
 * Template Name: Landing — Signature
 * Template Post Type: page
 *
 * Signature collection landing page — everyday luxury, foundation wardrobe.
 * Gold accent palette (#D4AF37). Uses shared landing-pages.css/js via enqueue.php.
 *
 * @package SkyyRose
 * @since   6.5.0
 */

defined( 'ABSPATH' ) || exit;

get_header();
?>

<main id="primary" class="lp" data-collection="signature" role="main" tabindex="-1">
	<h1 class="screen-reader-text"><?php esc_html_e( 'Signature Collection — the foundation', 'skyyrose' ); ?></h1>

	<?php
	/* ── 1. Hero ─────────────────────────────────────────────────── */
	get_template_part(
		'template-parts/landing/hero',
		null,
		array(
			'collection'    => 'signature',
			'badge_text'    => 'Everyday Luxury &mdash; The Foundation',
			'logo_image'    => '/images/hero-overlays/sig-brand-skyy-rose-gold.png',
			'logo_alt'      => 'The Skyy Rose Signature Collection',
			'subtitle'      => 'Not basics. Blueprints.',
			'countdown'     => false,
			'cta_primary'   => array(
				'text' => 'Shop Signature',
				'url'  => '#products',
			),
			'cta_secondary' => array(
				'text' => 'The Story',
				'url'  => '#story',
			),
		)
	);
	?>

	<!-- ── 2. Press Bar ──────────────────────────────────────────── -->
	<section class="lp-press lp-rv">
		<div class="lp__container">
			<div class="lp-press__row">
				<span class="lp-press__name">Maxim</span>
				<span class="lp-press__name">CEO Weekly</span>
				<span class="lp-press__name">SF Post</span>
				<span class="lp-press__name">Best of Best Review</span>
			</div>
		</div>
	</section>

	<!-- ── 3. Story ──────────────────────────────────────────────── -->
	<section class="lp-story" id="story">
		<div class="lp__container">
			<div class="lp-story__grid">
				<div class="lp-story__content lp-rv">
					<span class="lp-story__label"><?php echo esc_html( 'THE PHILOSOPHY' ); ?></span>
					<h2 class="lp-story__title"><?php echo esc_html( 'Not Basics. Blueprints.' ); ?></h2>
					<p class="lp-story__text"><?php echo esc_html( 'Most brands sell you basics and call it a day. We build foundation pieces — the kind you reach for first, wear the longest, and never want to replace. Premium cotton blends, considered silhouettes, and details you feel before you see them.' ); ?></p>
					<p class="lp-story__text"><?php echo esc_html( 'Signature is the collection that started everything. Before the limited drops and the press features, there was a father in Oakland who believed everyday clothes should feel like something. That belief hasn\'t changed.' ); ?></p>
					<blockquote class="lp-story__quote"><?php echo esc_html( '"The foundation of any wardrobe worth building."' ); ?></blockquote>
				</div>
				<div class="lp-story__image lp-rv" data-delay="2">
					<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/products/signature-sherpa-jacket-front-model.webp' ); ?>"
						alt="<?php echo esc_attr__( 'Signature sherpa jacket, editorial portrait', 'skyyrose' ); ?>"
						loading="lazy" decoding="async"
						width="1024" height="1024"
						style="width:100%;height:100%;object-fit:cover;border-radius:var(--skyyrose-radius);">
				</div>
			</div>
		</div>
	</section>

	<!-- ── 4. Parallax Banner ────────────────────────────────────── -->
	<?php get_template_part( 'template-parts/pin-narrative', null, array( 'slug' => 'signature' ) ); ?>

	<section class="lp-parallax lp-rv">
		<div class="lp-parallax__text">
			<span><?php echo esc_html( 'Everyday Doesn\'t Mean Ordinary.' ); ?></span>
		</div>
	</section>

	<?php
	/* ── 5. Product Grid ─────────────────────────────────────────── */
	get_template_part(
		'template-parts/landing/product-grid',
		null,
		array(
			'heading'    => 'The Collection',
			'subheading' => 'Wardrobe foundations built to last.',
			'skus'       => array(
				'sg-001', // Bridge Series Bay Bridge Shorts — $195
				'sg-009', // The Sherpa Jacket — $80
				'sg-015', // The Windbreaker Set — $85
				'sg-006', // Mint & Lavender Hoodie — $45
				'sg-002', // Stay Golden Shirt — $65
				'sg-011', // Original Label Tee (White) — $30
			),
			'wear_count' => 300,
		)
	);
	?>

	<!-- ── 6. Editorial Gallery ──────────────────────────────────── -->
	<section class="lp-editorial">
		<div class="lp__container">
			<div class="lp-editorial__header lp-rv">
				<h2><?php echo esc_html( 'The Lookbook' ); ?></h2>
			</div>
			<div class="lp-editorial__grid lp-rv" data-delay="1">
				<div class="lp-editorial__item"><img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/products/bridge-bay-bridge-shirt-front-model.webp' ); ?>" alt="<?php echo esc_attr__( 'Bridge Bay Bridge shirt, model shot', 'skyyrose' ); ?>" loading="lazy" decoding="async" width="1024" height="1024"></div>
				<div class="lp-editorial__item"><img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/products/stay-golden-tee-front-model.webp' ); ?>" alt="<?php echo esc_attr__( 'Stay Golden tee, model shot', 'skyyrose' ); ?>" loading="lazy" decoding="async" width="896" height="1200"></div>
				<div class="lp-editorial__item"><img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/products/mint-lavender-hoodie-front-model.webp' ); ?>" alt="<?php echo esc_attr__( 'Mint Lavender hoodie, model shot', 'skyyrose' ); ?>" loading="lazy" decoding="async" width="1024" height="1024"></div>
			</div>
			<div class="lp-editorial__grid lp-editorial__grid--row2 lp-rv" data-delay="2">
				<div class="lp-editorial__item"><img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/branding/hero/luxury-nighttime-1280w.webp' ); ?>" alt="<?php echo esc_attr__( 'Signature collection — Oakland skyline', 'skyyrose' ); ?>" loading="lazy" decoding="async" width="1280" height="549"></div>
				<div class="lp-editorial__item"><img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/products/signature-beanie-front-model.webp' ); ?>" alt="<?php echo esc_attr__( 'Signature beanie, model shot', 'skyyrose' ); ?>" loading="lazy" decoding="async" width="1024" height="1024"></div>
			</div>
		</div>
	</section>

	<!-- ── 7. Reviews ────────────────────────────────────────────── -->
	<section class="lp-reviews">
		<div class="lp__container">
			<div class="lp-reviews__header lp-rv">
				<h2><?php echo esc_html( 'Rated 4.9 by 350+ Customers' ); ?></h2>
			</div>
			<div class="lp-reviews__grid">
				<?php
				$reviews = array(
					array(
						'text'   => 'Best basics I\'ve ever owned. The weight of the fabric is perfect.',
						'author' => 'Andre P.',
						'city'   => 'New York',
					),
					array(
						'text'   => 'I replaced my entire wardrobe basics with Signature pieces. Worth every penny.',
						'author' => 'Lisa K.',
						'city'   => 'Oakland',
					),
					array(
						'text'   => 'The gold detailing is subtle but you notice it. That\'s the difference.',
						'author' => 'James M.',
						'city'   => 'Houston',
					),
				);
				$r_delay = 1;
				foreach ( $reviews as $review ) :
					?>
					<div class="lp-review-card lp-rv" data-delay="<?php echo esc_attr( $r_delay ); ?>">
						<div class="lp-review-card__stars" aria-label="5 out of 5 stars">&#9733;&#9733;&#9733;&#9733;&#9733;</div>
						<p class="lp-review-card__text"><?php echo esc_html( $review['text'] ); ?></p>
						<cite class="lp-review-card__author">
							<?php echo esc_html( $review['author'] ); ?>, <?php echo esc_html( $review['city'] ); ?>
						</cite>
					</div>
					<?php
					++$r_delay;
				endforeach;
				?>
			</div>
		</div>
	</section>

	<!-- ── 8. Craft ──────────────────────────────────────────────── -->
	<section class="lp-craft">
		<div class="lp__container">
			<div class="lp-craft__header lp-rv">
				<h2><?php echo esc_html( 'Everyday Doesn\'t Mean Ordinary' ); ?></h2>
			</div>
			<div class="lp-craft__grid">
				<?php
				$craft_cards = array(
					array(
						'icon'  => 'Premium',
						'title' => 'Premium Cotton Blend',
						'desc'  => '280gsm organic cotton with a brushed interior. Heavier than fast fashion, softer than anything in your closet.',
					),
					array(
						'icon'  => 'Gold',
						'title' => 'Gold Accent Details',
						'desc'  => 'Subtle gold rose branding on every piece. Not loud — just enough that those who know, know.',
					),
					array(
						'icon'  => 'Versatile',
						'title' => 'Versatile Silhouettes',
						'desc'  => 'Designed to move from morning coffee to evening out. Day-to-night pieces that don\'t compromise.',
					),
					array(
						'icon'  => 'Durable',
						'title' => 'Built to Last',
						'desc'  => 'Reinforced seams, pre-shrunk fabric, colorfast dyes. These pieces get better with every wash.',
					),
				);
				$c_delay     = 1;
				foreach ( $craft_cards as $card ) :
					?>
					<div class="lp-craft__card lp-rv" data-delay="<?php echo esc_attr( $c_delay ); ?>">
						<span class="lp-craft__icon" aria-hidden="true"><?php echo esc_html( $card['icon'] ); ?></span>
						<h3><?php echo esc_html( $card['title'] ); ?></h3>
						<p><?php echo esc_html( $card['desc'] ); ?></p>
					</div>
					<?php
					++$c_delay;
				endforeach;
				?>
			</div>
		</div>
	</section>

	<?php
	/* ── 9. FAQ ───────────────────────────────────────────────────── */
	get_template_part(
		'template-parts/landing/faq',
		null,
		array(
			'heading'   => 'Quick Answers',
			'questions' => array(
				array(
					'q' => 'How does Signature sizing run?',
					'a' => 'Relaxed, comfortable fit across sizes S through 3XL. Check the size guide on each product page for exact measurements.',
				),
				array(
					'q' => 'Will there be new colors?',
					'a' => 'We drop new colorways monthly. Subscribe to be the first to know when a new Signature color lands.',
				),
				array(
					'q' => 'What\'s the return policy?',
					'a' => '30-day hassle-free returns on all unworn items with tags attached. We cover return shipping in the US.',
				),
				array(
					'q' => 'What makes the quality different?',
					'a' => 'Premium construction with 280gsm+ fabrics, reinforced stitching, and pre-shrunk materials. Built to outlast anything in the same price range.',
				),
				array(
					'q' => 'How long does shipping take?',
					'a' => 'Standard shipping is 5&ndash;7 business days within the US. Expedited options available at checkout.',
				),
			),
		)
	);
	?>

	<!-- ── 10. Email CTA ─────────────────────────────────────────── -->
	<section class="lp-cta lp-rv">
		<div class="lp__container">
			<h2 class="lp-cta__title"><?php echo esc_html( 'New Colorways Drop Monthly' ); ?></h2>
			<p class="lp-cta__subtitle"><?php echo esc_html( 'First access to every new Signature release.' ); ?></p>
			<form class="lp-cta__form" aria-label="<?php echo esc_attr( 'Newsletter signup' ); ?>">
				<label class="screen-reader-text" for="sig-lp-email"><?php echo esc_html( 'Email address' ); ?></label>
				<input type="email"
						id="sig-lp-email"
						class="lp-cta__input"
						placeholder="<?php echo esc_attr( 'Enter your email' ); ?>"
						required>
				<button type="submit" class="lp-cta__submit"><?php echo esc_html( 'Get Early Access' ); ?></button>
			</form>
			<p class="lp-cta__note"><?php echo esc_html( 'Join 12,400+ members' ); ?></p>
		</div>
	</section>

</main><!-- .lp -->

<?php get_footer(); ?>
