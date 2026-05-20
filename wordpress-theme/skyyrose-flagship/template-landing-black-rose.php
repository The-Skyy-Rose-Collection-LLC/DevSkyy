<?php
/**
 * Template Name: Landing — Black Rose
 * Template Post Type: page
 *
 * Conversion-focused landing page for the Black Rose collection.
 * Uses shared template-parts/landing/ components (hero, product-grid, faq).
 *
 * @package SkyyRose
 * @since   6.5.0
 */

defined( 'ABSPATH' ) || exit;

get_header();
?>

<div class="lp" data-collection="black-rose">

	<?php
	/*
	══════════════════════════════════════════════════════════════
	 * 1. HERO
	 * ══════════════════════════════════════════════════════════════ */
	get_template_part(
		'template-parts/landing/hero',
		null,
		array(
			'collection'    => 'black-rose',
			'badge_text'    => 'Limited Edition — 200 Pieces Per Style',
			'logo_image'    => '/images/hero-overlays/br-brand-script.png',
			'logo_alt'      => 'The Black Rose Collection',
			'subtitle'      => "Darkness isn't the absence of light. It's where you find your own.",
			'countdown'     => false,
			'cta_primary'   => array(
				'text' => 'Shop Black Rose',
				'url'  => '#products',
			),
			'cta_secondary' => array(
				'text' => 'The Story',
				'url'  => '#story',
			),
		)
	);
	?>

	<!-- ══════════════════════════════════════════════════════════════
		2. PRESS BAR
		══════════════════════════════════════════════════════════════ -->
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

	<!-- ══════════════════════════════════════════════════════════════
		3. STORY
		══════════════════════════════════════════════════════════════ -->
	<section class="lp-story" id="story">
		<div class="lp__container">
			<div class="lp-story__grid">

				<div class="lp-story__text lp-rv">
					<span class="lp-story__label"><?php echo esc_html( 'THE ORIGIN' ); ?></span>
					<h2 class="lp-story__title"><?php echo esc_html( "Darkness Isn't the Absence of Light" ); ?></h2>
					<p>
						<?php echo esc_html( 'Corey Foster grew up in Oakland, California — a city that teaches you to build beauty from nothing. Black Rose started as a sketch in a notebook and became something bigger: a collection for people who understand that real luxury comes from adversity, not privilege.' ); ?>
					</p>
					<p>
						<?php echo esc_html( 'Every piece in this collection carries the weight of that story. The monochrome palette. The thorn motifs. The numbered authentication. This is fashion forged in the fire of real life.' ); ?>
					</p>
					<blockquote class="lp-story__quote">
						<p><?php echo esc_html( "If you asked me four years ago, I never would have thought I'd be here." ); ?></p>
						<cite><?php echo esc_html( '— Corey Foster, Founder' ); ?></cite>
					</blockquote>
				</div>

				<div class="lp-story__image lp-rv" data-delay="2">
					<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/products/black-rose-hoodie-front-model.webp' ); ?>"
						alt="<?php echo esc_attr__( 'Black Rose hoodie, editorial portrait', 'skyyrose' ); ?>"
						loading="lazy" decoding="async"
						style="width:100%;height:100%;object-fit:cover;border-radius:var(--skyyrose-radius);">
				</div>

			</div>
		</div>
	</section>

	<!-- ══════════════════════════════════════════════════════════════
		4. PARALLAX BANNER
		══════════════════════════════════════════════════════════════ -->
	<div class="lp-parallax lp-rv">
		<div class="lp__container">
			<p class="lp-parallax__text"><?php echo esc_html( '200 Pieces. Numbered. Never Restocked.' ); ?></p>
		</div>
	</div>

	<?php
	/*
	══════════════════════════════════════════════════════════════
	 * 5. PRODUCT GRID
	 * ══════════════════════════════════════════════════════════════ */
	get_template_part(
		'template-parts/landing/product-grid',
		null,
		array(
			'heading'    => 'The Collection',
			'subheading' => "Limited edition. Numbered. When they're gone, they're gone.",
			'skus'       => array( 'br-004', 'br-005', 'br-006', 'br-010' ),
			'wear_count' => 200,
		)
	);
	?>

	<!-- ══════════════════════════════════════════════════════════════
		6. EDITORIAL GALLERY
		══════════════════════════════════════════════════════════════ -->
	<section class="lp-editorial" id="editorial">
		<div class="lp__container">
			<div class="lp-editorial__header lp-rv">
				<h2><?php echo esc_html( 'Editorial' ); ?></h2>
			</div>

			<div class="lp-editorial__grid lp-editorial__grid--top">
				<div class="lp-editorial__item lp-rv" data-delay="1"><img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/products/black-rose-crewneck-front-model.webp' ); ?>" alt="<?php echo esc_attr__( 'Black Rose crewneck, model shot', 'skyyrose' ); ?>" loading="lazy" decoding="async"></div>
				<div class="lp-editorial__item lp-rv" data-delay="2"><img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/products/black-rose-joggers-front-model.webp' ); ?>" alt="<?php echo esc_attr__( 'Black Rose joggers, model shot', 'skyyrose' ); ?>" loading="lazy" decoding="async"></div>
				<div class="lp-editorial__item lp-rv" data-delay="3"><img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/products/black-rose-hoodie-signature-front-model.webp' ); ?>" alt="<?php echo esc_attr__( 'Black Rose signature hoodie, model shot', 'skyyrose' ); ?>" loading="lazy" decoding="async"></div>
			</div>

			<div class="lp-editorial__grid lp-editorial__grid--bottom">
				<div class="lp-editorial__item lp-rv" data-delay="1"><img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/branding/hero/forbidden-midnight-1280w.webp' ); ?>" alt="<?php echo esc_attr__( 'Black Rose collection — forbidden midnight', 'skyyrose' ); ?>" loading="lazy" decoding="async"></div>
				<div class="lp-editorial__item lp-rv" data-delay="2"><img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/products/black-rose-love-hurts-basketball-shorts-front-model.webp' ); ?>" alt="<?php echo esc_attr__( 'Black Rose x Love Hurts basketball shorts', 'skyyrose' ); ?>" loading="lazy" decoding="async"></div>
			</div>
		</div>
	</section>

	<!-- ══════════════════════════════════════════════════════════════
		7. REVIEWS
		══════════════════════════════════════════════════════════════ -->
	<section class="lp-reviews" id="reviews">
		<div class="lp__container">
			<div class="lp-reviews__header lp-rv">
				<h2><?php echo esc_html( 'What BLACK ROSE Means to People' ); ?></h2>
			</div>

			<div class="lp-reviews__grid">
				<?php
				$reviews = array(
					array(
						'text'   => "The quality is insane. I've washed my hoodie 20+ times and it still looks brand new.",
						'author' => 'Marcus T., Oakland',
					),
					array(
						'text'   => "I've never gotten more compliments on a piece of clothing.",
						'author' => 'Jade W., San Francisco',
					),
					array(
						'text'   => "This isn't just a brand, it's a movement. The numbered tag makes it feel special.",
						'author' => 'Devon L., Los Angeles',
					),
				);

				$delay = 1;
				foreach ( $reviews as $review ) :
					?>
					<div class="lp-reviews__card lp-rv" data-delay="<?php echo esc_attr( $delay ); ?>">
						<blockquote>
							<p><?php echo esc_html( $review['text'] ); ?></p>
						</blockquote>
						<cite><?php echo esc_html( '— ' . $review['author'] ); ?></cite>
					</div>
					<?php
					++$delay;
				endforeach;
				?>
			</div>
		</div>
	</section>

	<!-- ══════════════════════════════════════════════════════════════
		8. CRAFT / VALUE PROPOSITION
		══════════════════════════════════════════════════════════════ -->
	<section class="lp-craft" id="craft">
		<div class="lp__container">
			<div class="lp-craft__header lp-rv">
				<h2><?php echo esc_html( 'Why BLACK ROSE Costs What It Costs' ); ?></h2>
				<p><?php echo esc_html( 'Every dollar goes into the product. No influencer budgets. No middlemen. Just quality you can feel.' ); ?></p>
			</div>

			<div class="lp-craft__grid">
				<?php
				$craft_cards = array(
					array(
						'icon'  => '380gsm',
						'title' => '380gsm French Terry',
						'desc'  => 'Premium heavyweight fabric that holds its shape wash after wash. Most brands use 220gsm. We use nearly double.',
					),
					array(
						'icon'  => '#',
						'title' => 'Numbered Authentication',
						'desc'  => 'Every piece is hand-numbered with a unique tag. You know exactly which piece is yours out of 200.',
					),
					array(
						'icon'  => '////',
						'title' => 'Double-Stitched Seams',
						'desc'  => 'Reinforced construction at every stress point. Built to last years, not seasons.',
					),
					array(
						'icon'  => "\xF0\x9F\x94\x92",
						'title' => 'Never Restocked',
						'desc'  => 'When a run sells out, it is gone forever. No reprints, no exceptions. Your piece stays rare.',
					),
				);

				$delay = 1;
				foreach ( $craft_cards as $card ) :
					?>
					<div class="lp-craft__card lp-rv" data-delay="<?php echo esc_attr( $delay ); ?>">
						<span class="lp-craft__icon" aria-hidden="true"><?php echo esc_html( $card['icon'] ); ?></span>
						<h3><?php echo esc_html( $card['title'] ); ?></h3>
						<p><?php echo esc_html( $card['desc'] ); ?></p>
					</div>
					<?php
					++$delay;
				endforeach;
				?>
			</div>
		</div>
	</section>

	<?php
	/*
	══════════════════════════════════════════════════════════════
	 * 9. FAQ
	 * ══════════════════════════════════════════════════════════════ */
	get_template_part(
		'template-parts/landing/faq',
		null,
		array(
			'heading'   => 'Questions We Get Asked',
			'questions' => array(
				array(
					'q' => 'How does the sizing run?',
					'a' => 'True to size across the board. We offer sizes S through 3XL. Check the size guide on any product page for exact measurements.',
				),
				array(
					'q' => 'Is this really limited edition?',
					'a' => 'Yes. Every style is produced in a numbered run of 200 pieces. Once they sell out, they are never restocked or reprinted.',
				),
				array(
					'q' => 'What is your return policy?',
					'a' => 'We offer a 30-day return and exchange policy on all unworn items. Contact us and we will make it right.',
				),
				array(
					'q' => 'What about the quality?',
					'a' => 'Premium construction throughout. 280gsm+ cotton, double-stitched seams, and heavyweight French Terry on our hoodies and outerwear.',
				),
				array(
					'q' => 'How long does shipping take?',
					'a' => 'Orders ship within 5-7 business days. You will receive a tracking number via email as soon as your order is on its way.',
				),
			),
		)
	);
	?>

	<!-- ══════════════════════════════════════════════════════════════
		10. EMAIL CTA
		══════════════════════════════════════════════════════════════ -->
	<section class="lp-cta" id="signup">
		<div class="lp__container">
			<div class="lp-cta__content lp-rv">
				<h2><?php echo esc_html( 'Get Early Access to Every Release' ); ?></h2>
				<p class="lp-cta__subtitle"><?php echo esc_html( 'Join the list. First access. Exclusive drops. No spam.' ); ?></p>

				<form class="lp-cta__form" action="#" method="post">
					<label for="lp-cta-email" class="screen-reader-text">
						<?php echo esc_html( 'Email address' ); ?>
					</label>
					<input id="lp-cta-email"
							class="lp-cta__input"
							type="email"
							name="email"
							placeholder="<?php echo esc_attr( 'Enter your email' ); ?>"
							required
							autocomplete="email">
					<button class="lp-btn lp-btn--primary lp-cta__submit" type="submit">
						<?php echo esc_html( 'Join' ); ?>
					</button>
				</form>

				<p class="lp-cta__note"><?php echo esc_html( 'Join 12,400+ members who never miss a drop' ); ?></p>
			</div>
		</div>
	</section>

</div><!-- /.lp -->

<?php get_footer(); ?>
