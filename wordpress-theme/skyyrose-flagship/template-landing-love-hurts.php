<?php
/**
 * Template Name: Landing — Love Hurts
 * Template Post Type: page
 *
 * Conversion-focused landing page for the Love Hurts collection.
 * "Hurts" is the founder's family name — this collection is deeply personal.
 * Voice: raw, emotional, vulnerability as strength.
 *
 * @package SkyyRose
 * @since   6.5.0
 */

defined( 'ABSPATH' ) || exit;

get_header();
?>

<div class="lp" data-collection="love-hurts">

	<?php
	/* ───── 1. Hero ───── */
	get_template_part(
		'template-parts/landing/hero',
		null,
		array(
			'collection'    => 'love-hurts',
			'badge_text'    => 'Family Legacy — The Hurts Collection',
			'logo_image'    => '/images/hero-overlays/lh-logo-combined.png',
			'logo_alt'      => 'Love Hurts Collection',
			'subtitle'      => 'This isn\'t a theme. It\'s what you\'ve survived.',
			'countdown'     => false,
			'cta_primary'   => array(
				'text' => 'Shop Love Hurts',
				'url'  => '#products',
			),
			'cta_secondary' => array(
				'text' => 'The Story',
				'url'  => '#story',
			),
		)
	);
	?>

	<?php /* ───── 2. Press Bar ───── */ ?>
	<div class="lp-press lp-rv" aria-label="Featured in">
		<div class="lp__container">
			<span class="lp-press__label"><?php echo esc_html( 'As Seen In' ); ?></span>
			<ul class="lp-press__list">
				<li><?php echo esc_html( 'Maxim' ); ?></li>
				<li><?php echo esc_html( 'CEO Weekly' ); ?></li>
				<li><?php echo esc_html( 'SF Post' ); ?></li>
				<li><?php echo esc_html( 'Best of Best Review' ); ?></li>
			</ul>
		</div>
	</div>

	<?php /* ───── 3. Story ───── */ ?>
	<section class="lp-story" id="story">
		<div class="lp__container">
			<div class="lp-story__grid">
				<div class="lp-story__text lp-rv">
					<span class="lp-story__label">THE LEGACY</span>
					<h2 class="lp-story__title"><?php echo esc_html( 'This Isn\'t a Theme. It\'s a Family Name.' ); ?></h2>
					<p class="lp-story__text">
						<?php echo esc_html( 'Most brands pick a concept off a mood board. We didn\'t pick this one — it picked us. "Hurts" isn\'t a word we chose for the aesthetic. It\'s the name our family carries. Every scar, every lesson, every door that closed and every one we kicked open — it\'s all in the name.' ); ?>
					</p>
					<p class="lp-story__text">
						<?php echo esc_html( 'This collection takes that pain and turns it into something you can wear. Something beautiful. Something that says: I\'ve been through it, and I\'m still here.' ); ?>
					</p>
					<blockquote class="lp-story__quote">
						<p><?php echo esc_html( 'Every piece carries the weight of what we\'ve been through — and the strength of what we\'ve become.' ); ?></p>
						<cite><?php echo esc_html( '— Corey Foster, Founder' ); ?></cite>
					</blockquote>
				</div>
				<div class="lp-story__image lp-rv" data-delay="2">
					<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/products/love-hurts-bomber-front-model.webp' ); ?>"
						alt="<?php echo esc_attr__( 'Love Hurts bomber jacket, editorial portrait', 'skyyrose' ); ?>"
						loading="lazy" decoding="async"
						style="width:100%;height:100%;aspect-ratio:3/4;object-fit:cover;border-radius:var(--skyyrose-radius);">
				</div>
			</div>
		</div>
	</section>

	<?php /* ───── 4. Parallax Banner ───── */ ?>
	<section class="lp-parallax" aria-label="Statement">
		<div class="lp-parallax__text lp-rv">
			<p><?php echo esc_html( 'Wear Your Heart. Own Your Scars.' ); ?></p>
		</div>
	</section>

	<?php
	/* ───── 5. Product Grid ───── */
	get_template_part(
		'template-parts/landing/product-grid',
		null,
		array(
			'heading'    => 'The Collection',
			'subheading' => 'Wear what you\'ve survived.',
			'skus'       => array( 'lh-004', 'lh-002', 'lh-003', 'lh-006' ),
			'wear_count' => 200,
		)
	);
	?>

	<?php /* ───── 6. Editorial Gallery ───── */ ?>
	<section class="lp-editorial">
		<div class="lp__container">
			<div class="lp-editorial__header lp-rv">
				<h2><?php echo esc_html( 'The Look' ); ?></h2>
			</div>
			<div class="lp-editorial__grid lp-rv" data-delay="1">
				<div class="lp-editorial__item"><img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/products/love-hurts-basketball-shorts-front-model.webp' ); ?>" alt="<?php echo esc_attr__( 'Love Hurts basketball shorts, model shot', 'skyyrose' ); ?>" loading="lazy" decoding="async"></div>
				<div class="lp-editorial__item"><img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/products/love-hurts-varsity-jacket-front-model.webp' ); ?>" alt="<?php echo esc_attr__( 'Love Hurts varsity jacket, model shot', 'skyyrose' ); ?>" loading="lazy" decoding="async"></div>
				<div class="lp-editorial__item"><img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/products/the-fannie-front-model.webp' ); ?>" alt="<?php echo esc_attr__( 'The Fannie piece, model shot', 'skyyrose' ); ?>" loading="lazy" decoding="async"></div>
			</div>
			<div class="lp-editorial__grid lp-editorial__grid--row2 lp-rv" data-delay="2">
				<div class="lp-editorial__item"><img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/branding/hero/beauty-and-beast-1280w.webp' ); ?>" alt="<?php echo esc_attr__( 'Love Hurts collection — enchanted rose under glass', 'skyyrose' ); ?>" loading="lazy" decoding="async"></div>
				<div class="lp-editorial__item"><img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/products/love-hurts-bomber-back-model.webp' ); ?>" alt="<?php echo esc_attr__( 'Love Hurts bomber jacket, back view', 'skyyrose' ); ?>" loading="lazy" decoding="async"></div>
			</div>
		</div>
	</section>

	<?php /* ───── 7. Reviews ───── */ ?>
	<section class="lp-reviews">
		<div class="lp__container">
			<div class="lp-reviews__header lp-rv">
				<h2><?php echo esc_html( 'What LOVE HURTS Means to People' ); ?></h2>
			</div>
			<div class="lp-reviews__grid">
				<div class="lp-reviews__card lp-rv" data-delay="1">
					<div class="lp-reviews__stars" aria-label="5 stars">&#9733;&#9733;&#9733;&#9733;&#9733;</div>
					<blockquote class="lp-reviews__quote">
						<?php echo esc_html( 'I bought this for my daughter. She said it\'s the first brand that feels like it understands her.' ); ?>
					</blockquote>
					<cite class="lp-reviews__author">&mdash; Tamika R., Atlanta</cite>
				</div>
				<div class="lp-reviews__card lp-rv" data-delay="2">
					<div class="lp-reviews__stars" aria-label="5 stars">&#9733;&#9733;&#9733;&#9733;&#9733;</div>
					<blockquote class="lp-reviews__quote">
						<?php echo esc_html( 'The varsity jacket is a piece of art. I wear it every time I need to feel invincible.' ); ?>
					</blockquote>
					<cite class="lp-reviews__author">&mdash; Ray C., Oakland</cite>
				</div>
				<div class="lp-reviews__card lp-rv" data-delay="3">
					<div class="lp-reviews__stars" aria-label="5 stars">&#9733;&#9733;&#9733;&#9733;&#9733;</div>
					<blockquote class="lp-reviews__quote">
						<?php echo esc_html( 'Hurts is more than a name on a tag. When you know the story, it hits different.' ); ?>
					</blockquote>
					<cite class="lp-reviews__author">&mdash; Kiera M., Chicago</cite>
				</div>
			</div>
		</div>
	</section>

	<?php /* ───── 8. Craft ───── */ ?>
	<section class="lp-craft">
		<div class="lp__container">
			<div class="lp-craft__header lp-rv">
				<h2><?php echo esc_html( 'Every Detail Is Intentional' ); ?></h2>
			</div>
			<div class="lp-craft__grid">
				<div class="lp-craft__card lp-rv" data-delay="1">
					<span class="lp-craft__icon" aria-hidden="true">Satin</span>
					<h3><?php echo esc_html( 'Premium Satin Shell' ); ?></h3>
					<p><?php echo esc_html( 'The varsity jacket features a heavyweight satin shell with custom quilted lining. Built to last decades, not seasons.' ); ?></p>
				</div>
				<div class="lp-craft__card lp-rv" data-delay="2">
					<span class="lp-craft__icon" aria-hidden="true">Hand</span>
					<h3><?php echo esc_html( 'Hand-Applied Script' ); ?></h3>
					<p><?php echo esc_html( 'Fire-red chain-stitch lettering applied by hand. No two pieces are identical — each one carries its own character.' ); ?></p>
				</div>
				<div class="lp-craft__card lp-rv" data-delay="3">
					<span class="lp-craft__icon" aria-hidden="true">Rose</span>
					<h3><?php echo esc_html( 'Hidden Rose Garden' ); ?></h3>
					<p><?php echo esc_html( 'Flip the hood and find an embroidered rose garden lining. Beauty hidden where only you know to look.' ); ?></p>
				</div>
				<div class="lp-craft__card lp-rv" data-delay="4">
					<span class="lp-craft__icon" aria-hidden="true">Soul</span>
					<h3><?php echo esc_html( 'Family Name Legacy' ); ?></h3>
					<p><?php echo esc_html( '"Hurts" is stitched into every seam, woven into every label. This isn\'t branding — it\'s personal. Every piece carries meaning you can feel.' ); ?></p>
				</div>
			</div>
		</div>
	</section>

	<?php
	/* ───── 9. FAQ ───── */
	get_template_part(
		'template-parts/landing/faq',
		null,
		array(
			'heading'   => 'Questions We Get Asked',
			'questions' => array(
				array(
					'q' => 'What does "Love Hurts" mean?',
					'a' => '<p>"Hurts" is the founder\'s actual family name. This collection is deeply personal — it\'s a tribute to everything the family has been through, transformed into something you can wear with pride.</p>',
				),
				array(
					'q' => 'How does sizing run?',
					'a' => '<p>Love Hurts pieces run true to size. The joggers and basketball shorts have an athletic fit with adjustable waistbands. The varsity jacket is cut relaxed for layering. When in doubt, go with your usual size.</p>',
				),
				array(
					'q' => 'How should I care for my pieces?',
					'a' => '<p>Machine wash cold on a gentle cycle, inside out. Hang dry to preserve the satin finish and embroidery details. Do not bleach or iron directly on printed areas.</p>',
				),
				array(
					'q' => 'What is the return policy?',
					'a' => '<p>We offer a 30-day return policy on all unworn items with original tags attached. Pre-order items can be cancelled for a full refund before they ship.</p>',
				),
				array(
					'q' => 'How long does shipping take?',
					'a' => '<p>Standard shipping is 5&ndash;7 business days within the US. Express options are available at checkout. International orders typically arrive within 10&ndash;14 business days.</p>',
				),
			),
		)
	);
	?>

	<?php /* ───── 10. Email CTA ───── */ ?>
	<section class="lp-cta">
		<div class="lp__container">
			<h2 class="lp-cta__title lp-rv"><?php echo esc_html( 'New Stories Drop Monthly' ); ?></h2>
			<p class="lp-cta__subtitle lp-rv" data-delay="1">
				<?php echo esc_html( 'Every release tells a chapter. Don\'t miss yours.' ); ?>
			</p>
			<form class="lp-cta__form lp-rv" data-delay="2" action="#" method="post">
				<input class="lp-cta__input"
						type="email"
						name="email"
						placeholder="Your email"
						required
						autocomplete="email"
						aria-label="Email address">
				<button class="lp-cta__submit" type="submit"><?php echo esc_html( 'Join' ); ?></button>
			</form>
			<p class="lp-cta__note lp-rv" data-delay="3"><?php echo esc_html( 'Join 12,400+ members' ); ?></p>
		</div>
	</section>

</div><!-- .lp -->

<?php get_footer(); ?>
