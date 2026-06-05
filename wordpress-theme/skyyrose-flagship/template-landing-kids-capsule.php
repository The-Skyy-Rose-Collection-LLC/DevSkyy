<?php
/**
 * Template Name: Landing — Kids Capsule
 * Template Post Type: page
 *
 * Conversion landing page for Kids Capsule — luxury runs in the family.
 * Rose-gold aurora palette. Uses shared template-parts/landing/ components.
 *
 * Story-world: Inheritance, joy, future legacy.
 * Voice: warm, proud, playful but never childish.
 *
 * @package SkyyRose
 * @since   6.5.0
 */

defined( 'ABSPATH' ) || exit;

get_header();
?>

<main id="primary" class="lp" data-collection="kids-capsule" role="main" tabindex="-1">
	<h1 class="screen-reader-text"><?php esc_html_e( 'Kids Capsule Collection — luxury runs in the family', 'skyyrose' ); ?></h1>

	<?php
	/*
	══════════════════════════════════════════════════════════════
	 * 1. HERO
	 * ══════════════════════════════════════════════════════════════ */
	get_template_part(
		'template-parts/landing/hero',
		null,
		array(
			'collection'    => 'kids-capsule',
			'badge_text'    => 'Luxury Runs in the Family',
			'logo_image'    => '/images/logos/skyy-rose-collection-circular-patch.png',
			'logo_alt'      => 'Kids Capsule Collection',
			'subtitle'      => 'Named after a daughter. Made for yours.',
			'countdown'     => false,
			'cta_primary'   => array(
				'text' => 'Shop Kids Capsule',
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

	<!-- ══════════════════════════════════════════════════════════════
		3. STORY
		══════════════════════════════════════════════════════════════ -->
	<section class="lp-story" id="story">
		<div class="lp__container">
			<div class="lp-story__grid">

				<div class="lp-story__text lp-rv">
					<span class="lp-story__label"><?php echo esc_html( 'THE ORIGIN' ); ?></span>
					<h2 class="lp-story__title"><?php echo esc_html( 'Built for the Next Generation' ); ?></h2>
					<p>
						<?php echo esc_html( 'Corey Foster named this brand after his daughter, Skyy Rose. This collection closes the circle — luxury that a parent passes down, not just buys.' ); ?>
					</p>
					<p>
						<?php echo esc_html( 'Every piece mirrors an adult SkyyRose style. Same attention to detail. Same uncompromising construction. Sized for the youngest members of the family who inherit their taste from the best.' ); ?>
					</p>
					<blockquote class="lp-story__quote">
						<p><?php echo esc_html( 'I built this brand for Skyy Rose. This collection is hers.' ); ?></p>
						<cite><?php echo esc_html( '— Corey Foster, Founder' ); ?></cite>
					</blockquote>
				</div>

				<div class="lp-story__image lp-rv" data-delay="2">
					<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/products/kids-purple-set-front-model.webp' ); ?>"
						alt="<?php echo esc_attr__( 'Kids Capsule purple set, model shot', 'skyyrose' ); ?>"
						loading="lazy" decoding="async"
						width="896" height="1200"
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
			<p class="lp-parallax__text"><?php echo esc_html( 'Mini Luxury. Maximum Legacy.' ); ?></p>
		</div>
	</div>

	<?php
	/*
	══════════════════════════════════════════════════════════════
	 * 5. PRODUCT GRID
	 * ══════════════════════════════════════════════════════════════ */
	get_template_part(
		'template-parts/pin-narrative',
		null,
		array( 'slug' => 'kids-capsule' )
	);

	get_template_part(
		'template-parts/landing/product-grid',
		null,
		array(
			'heading'    => 'The Collection',
			'subheading' => 'Matching sets for the youngest members of the family.',
			'skus'       => array( 'kids-001', 'kids-002' ),
			'wear_count' => 150,
		)
	);
	?>

	<!-- ══════════════════════════════════════════════════════════════
		6. EDITORIAL GALLERY
		══════════════════════════════════════════════════════════════ -->
	<section class="lp-editorial" id="editorial">
		<div class="lp__container">
			<div class="lp-editorial__header lp-rv">
				<h2><?php echo esc_html( 'Family Lookbook' ); ?></h2>
			</div>

			<div class="lp-editorial__grid lp-editorial__grid--top">
				<div class="lp-editorial__item lp-rv" data-delay="1"><img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/products/kids-red-set-front-model.webp' ); ?>" alt="<?php echo esc_attr__( 'Kids Capsule red set, model shot', 'skyyrose' ); ?>" loading="lazy" decoding="async" width="896" height="1200"></div>
				<div class="lp-editorial__item lp-rv" data-delay="2"><img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/products/kids-purple-set-back-model.webp' ); ?>" alt="<?php echo esc_attr__( 'Kids Capsule purple set, back view', 'skyyrose' ); ?>" loading="lazy" decoding="async" width="896" height="1200"></div>
				<div class="lp-editorial__item lp-rv" data-delay="3"><img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/products/kids-red-set-back-model.webp' ); ?>" alt="<?php echo esc_attr__( 'Kids Capsule red set, back view', 'skyyrose' ); ?>" loading="lazy" decoding="async" width="896" height="1200"></div>
			</div>
		</div>
	</section>

	<!-- ══════════════════════════════════════════════════════════════
		7. REVIEWS
		══════════════════════════════════════════════════════════════ -->
	<section class="lp-reviews" id="reviews">
		<div class="lp__container">
			<div class="lp-reviews__header lp-rv">
				<h2><?php echo esc_html( 'What Parents Are Saying' ); ?></h2>
			</div>

			<div class="lp-reviews__grid">
				<?php
				$reviews = array(
					array(
						'text'   => 'My daughter refuses to take off her hoodie. The quality is insane for kids\' clothes.',
						'author' => 'Alicia M.',
						'city'   => 'Oakland',
					),
					array(
						'text'   => 'Finally, matching outfits that don\'t look corny. We get stopped every time we go out.',
						'author' => 'Marcus T.',
						'city'   => 'Los Angeles',
					),
					array(
						'text'   => 'The colorblock set survived a whole week of daycare. That\'s the real luxury test.',
						'author' => 'Keisha D.',
						'city'   => 'Atlanta',
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

	<!-- ══════════════════════════════════════════════════════════════
		8. CRAFT / VALUE PROPOSITION
		══════════════════════════════════════════════════════════════ -->
	<section class="lp-craft" id="craft">
		<div class="lp__container">
			<div class="lp-craft__header lp-rv">
				<h2><?php echo esc_html( 'Built for Real Kids' ); ?></h2>
				<p><?php echo esc_html( 'Same build quality as our adult line. No shortcuts because they\'re small.' ); ?></p>
			</div>

			<div class="lp-craft__grid">
				<?php
				$craft_cards = array(
					array(
						'icon'  => '280gsm',
						'title' => 'Premium Weight Cotton',
						'desc'  => 'Heavyweight cotton that holds up to playground, daycare, and everything in between.',
					),
					array(
						'icon'  => '♻',
						'title' => 'Parent-Child Matching',
						'desc'  => 'Every piece mirrors an adult SkyyRose style. Dress alike without the cringe.',
					),
					array(
						'icon'  => '////',
						'title' => 'Reinforced Seams',
						'desc'  => 'Double-stitched at every stress point. Built for kids who actually move.',
					),
					array(
						'icon'  => '☆',
						'title' => 'Gender Neutral',
						'desc'  => 'No boys\' section, no girls\' section. Just great clothes for great kids.',
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
			'heading'   => 'Questions Parents Ask',
			'questions' => array(
				array(
					'q' => 'What sizes are available?',
					'a' => 'Kids Capsule runs 2T through 7. Check the size guide on any product page for exact measurements by age.',
				),
				array(
					'q' => 'Is this really the same quality as the adult line?',
					'a' => 'Yes. Same 280gsm+ cotton, same double-stitched seams, same attention to detail. The only difference is the size.',
				),
				array(
					'q' => 'Can I match with my kid?',
					'a' => 'That is the whole point. Every Kids Capsule piece has a matching adult counterpart in our core collections.',
				),
				array(
					'q' => 'What is the return policy?',
					'a' => '30-day returns on unworn items. Kids grow fast — we get it. Contact us and we will sort it out.',
				),
				array(
					'q' => 'How long does shipping take?',
					'a' => 'Orders ship within 5-7 business days. Tracking number sent via email as soon as your order is on its way.',
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
				<h2><?php echo esc_html( 'First Access for Family' ); ?></h2>
				<p class="lp-cta__subtitle"><?php echo esc_html( 'Get notified before every Kids Capsule drop. No spam.' ); ?></p>

				<form class="lp-cta__form" action="#" method="post">
					<label for="lp-cta-email-kc" class="screen-reader-text">
						<?php echo esc_html( 'Email address' ); ?>
					</label>
					<input id="lp-cta-email-kc"
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

				<p class="lp-cta__note"><?php echo esc_html( 'Join the family. First access to every drop.' ); ?></p>
			</div>
		</div>
	</section>

</main><!-- /.lp -->

<?php get_footer(); ?>
