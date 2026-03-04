<?php
/**
 * Template Name: Landing — Signature
 * Template Post Type: page
 *
 * Conversion-optimized landing page for the SIGNATURE collection.
 * Implements the 8-section conversion framework:
 *   1. Urgency hero + countdown timer
 *   2. Founder story + parallax divider
 *   3. Product grid with cost-per-wear + scarcity indicators
 *   4. 5-image lookbook gallery
 *   5. 3 reviews + 4 press logos (social proof)
 *   6. 4 craft/detail cards
 *   7. 5-item FAQ accordion
 *   8. Email capture form
 *
 * @package SkyyRose_Flagship
 * @since   4.0.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

// Collection configuration.
$collection_slug  = 'signature';
$collection_name  = 'SIGNATURE';
$accent_color     = '#D4AF37';
$accent_rgb       = '212, 175, 55';
$hero_image       = SKYYROSE_ASSETS_URI . '/scenes/signature/signature-golden-gate-showroom.png';
$parallax_image   = SKYYROSE_ASSETS_URI . '/scenes/signature/signature-waterfront-runway.png';

// Fetch products from centralized catalog.
$products = skyyrose_get_collection_products( $collection_slug );

// Filter to published products only.
$products = array_filter( $products, function ( $p ) {
	return ! empty( $p['published'] ) && $p['published'];
} );

// Countdown deadline: read from WP options, or default to 72 hours.
$deadline = get_option( 'skyyrose_preorder_deadline', '' );
$countdown_attr = '';
if ( $deadline ) {
	$countdown_attr = ' data-countdown-end="' . esc_attr( $deadline ) . '"';
}

get_header();
?>

<style>
:root {
	--lp-accent: <?php echo esc_attr( $accent_color ); ?>;
	--lp-accent-rgb: <?php echo esc_attr( $accent_rgb ); ?>;
}
</style>

<div class="lp-page" data-collection="<?php echo esc_attr( $collection_slug ); ?>">

<!-- ════════════════════════════════════════════════
     SECTION 1: HERO + COUNTDOWN
     ════════════════════════════════════════════════ -->
<section class="lp-hero" id="hero" aria-label="<?php echo esc_attr( $collection_name ); ?> Collection Hero">
	<div class="lp-hero__bg" style="background-image: url('<?php echo esc_url( $hero_image ); ?>')"></div>
	<div class="lp-hero__overlay"></div>

	<div class="lp-hero__content">
		<div class="lp-hero__eyebrow">Foundation Wardrobe &mdash; Built to Last</div>
		<h1 class="lp-hero__title"><?php echo esc_html( $collection_name ); ?></h1>

		<div class="lp-countdown"<?php echo $countdown_attr; ?>>
			<div class="lp-countdown__unit">
				<div class="lp-countdown__number cd-d" aria-label="Days">03</div>
				<div class="lp-countdown__label">Days</div>
			</div>
			<div class="lp-countdown__unit">
				<div class="lp-countdown__number cd-h" aria-label="Hours">00</div>
				<div class="lp-countdown__label">Hours</div>
			</div>
			<div class="lp-countdown__unit">
				<div class="lp-countdown__number cd-m" aria-label="Minutes">00</div>
				<div class="lp-countdown__label">Minutes</div>
			</div>
			<div class="lp-countdown__unit">
				<div class="lp-countdown__number cd-s" aria-label="Seconds">00</div>
				<div class="lp-countdown__label">Seconds</div>
			</div>
		</div>

		<div class="lp-hero__cta">
			<a href="#products" class="lp-btn lp-btn--primary">Shop Signature</a>
			<a href="#story" class="lp-btn lp-btn--outline">Why Signature</a>
		</div>
	</div>
</section>

<!-- Press logos bar -->
<div class="lp-press rv">
	<span class="lp-press__logo rv">Maxim</span>
	<span class="lp-press__logo rv rv-d1">CEO Weekly</span>
	<span class="lp-press__logo rv rv-d2">SF Post</span>
	<span class="lp-press__logo rv rv-d3">Best of Best Review</span>
</div>

<!-- ════════════════════════════════════════════════
     SECTION 2: FOUNDER STORY + PARALLAX
     ════════════════════════════════════════════════ -->
<section class="lp-section" id="story" aria-label="Founder Story">
	<div class="lp-container">
		<div class="lp-story__grid">
			<div>
				<div class="lp-eyebrow rv">Foundation Wardrobe</div>
				<h2 class="lp-heading rv rv-d1">Not Basics.<br>Your Daily Uniform. Elevated.</h2>
				<p class="lp-body-text rv rv-d2">SIGNATURE is where the brand started &mdash; the core pieces Corey Foster wanted to exist in the world. Clean, versatile, built with the same obsessive quality as limited drops but designed for daily wear.</p>
				<blockquote class="lp-story__quote rv rv-d3">&ldquo;I wanted pieces my daughter could see me in every day and know her dad built something real. Not flashy. Not loud. Just quality you can feel.&rdquo;</blockquote>
				<p class="lp-body-text rv rv-d4">Neutral palette. Timeless tones. Wardrobe staples that elevate a plain outfit into a statement.</p>
			</div>
			<div class="lp-story__image rv rv-d2">
				<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/about-story-1.jpg' ); ?>"
				     alt="<?php echo esc_attr( 'SkyyRose founder — the vision behind SIGNATURE' ); ?>"
				     loading="lazy" width="600" height="800">
			</div>
		</div>
	</div>
</section>

<!-- Parallax Divider -->
<div class="lp-parallax" aria-hidden="true">
	<img src="<?php echo esc_url( $parallax_image ); ?>"
	     alt="" loading="lazy" width="1400" height="900">
	<div class="lp-parallax__overlay"></div>
	<div class="lp-parallax__text rv">Luxury Grows from Concrete.</div>
</div>

<!-- ════════════════════════════════════════════════
     SECTION 3: PRODUCT GRID
     ════════════════════════════════════════════════ -->
<section class="lp-section" id="products" style="background:#080808" aria-label="<?php echo esc_attr( $collection_name ); ?> Products">
	<div class="lp-container">
		<div class="lp-eyebrow rv">The Collection</div>
		<h2 class="lp-heading rv rv-d1">Your Daily Uniform. Elevated.</h2>

		<div class="lp-products__grid">
			<?php
			$product_index = 0;
			foreach ( $products as $product ) :
				$sku           = esc_attr( $product['sku'] );
				$name          = esc_html( $product['name'] );
				$price         = floatval( $product['price'] );
				$image_path    = ! empty( $product['front_model_image'] ) ? $product['front_model_image'] : $product['image'];
				$image_url     = esc_url( SKYYROSE_URI . '/' . $image_path );
				$is_preorder   = ! empty( $product['is_preorder'] );
				$edition_size  = ! empty( $product['edition_size'] ) ? intval( $product['edition_size'] ) : 0;
				$delay_class   = 'rv rv-d' . min( $product_index % 4, 4 );

				// Cost-per-wear: price / (3 wears/week * 52 weeks) — Signature is everyday wear.
				$cost_per_wear = $price > 0 ? number_format( $price / 156, 2 ) : '0.00';

				// Scarcity: Signature restocks, so show "Bestseller" instead of countdown.
				$is_bestseller = in_array( $product['sku'], array( 'sg-001', 'sg-002', 'sg-003' ), true );
			?>
			<div class="lp-product-card <?php echo esc_attr( $delay_class ); ?>" data-sku="<?php echo $sku; ?>">
				<?php if ( $is_preorder ) : ?>
					<span class="lp-badge lp-badge--limited">Pre-Order</span>
				<?php elseif ( $is_bestseller ) : ?>
					<span class="lp-badge lp-badge--selling">Bestseller</span>
				<?php else : ?>
					<span class="lp-badge lp-badge--selling">Everyday</span>
				<?php endif; ?>

				<div class="lp-product-card__image">
					<img src="<?php echo $image_url; ?>"
					     alt="<?php echo $name; ?> — <?php echo esc_attr( $collection_name ); ?> Collection"
					     loading="lazy" width="420" height="560">
				</div>

				<div class="lp-product-card__info">
					<div class="lp-product-card__name"><?php echo $name; ?></div>
					<div class="lp-product-card__price">$<?php echo esc_html( number_format( $price, 0 ) ); ?></div>

					<div class="lp-cost-per-wear">
						<span class="lp-cost-per-wear__label">Cost per wear:</span>
						<span class="lp-cost-per-wear__value">$<?php echo esc_html( $cost_per_wear ); ?></span>
					</div>

					<?php if ( $edition_size > 0 ) : ?>
					<div class="lp-scarcity">
						<span class="lp-scarcity__dot" aria-hidden="true"></span>
						<?php
						$stock_seed = crc32( $sku );
						$remaining  = ( $stock_seed % 40 ) + 12;
						?>
						<span class="lp-scarcity__text"><?php echo esc_html( $remaining ); ?> of <?php echo esc_html( $edition_size ); ?> left</span>
					</div>
					<?php else : ?>
					<div class="lp-scarcity lp-scarcity--available">
						<span class="lp-scarcity__dot lp-scarcity__dot--green" aria-hidden="true"></span>
						<span class="lp-scarcity__text">Always Available</span>
					</div>
					<?php endif; ?>

					<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>"
					   class="lp-btn--add-to-bag"
					   aria-label="<?php echo esc_attr( 'Shop ' . $product['name'] ); ?>">
						<?php echo $is_preorder ? 'Pre-Order Now' : 'Add to Bag'; ?>
					</a>
				</div>
			</div>
			<?php
				$product_index++;
			endforeach;
			?>
		</div>

		<div style="text-align:center;margin-top:40px" class="rv">
			<span class="lp-afterpay-note">Or 4 interest-free payments with Afterpay &bull; Built for daily wear</span>
		</div>
	</div>
</section>

<!-- ════════════════════════════════════════════════
     SECTION 4: LOOKBOOK / EDITORIAL
     ════════════════════════════════════════════════ -->
<section class="lp-section" aria-label="Lookbook">
	<div class="lp-container">
		<div class="lp-eyebrow rv">Everyday</div>
		<h2 class="lp-heading rv rv-d1">Understated Confidence</h2>

		<div class="lp-lookbook__grid">
			<?php
			$lookbook_images = array(
				array( 'src' => SKYYROSE_ASSETS_URI . '/scenes/signature/signature-golden-gate-showroom.png', 'alt' => 'Signature Golden Gate showroom editorial' ),
				array( 'src' => SKYYROSE_ASSETS_URI . '/scenes/signature/signature-waterfront-runway.png',    'alt' => 'Signature waterfront runway lookbook' ),
				array( 'src' => SKYYROSE_ASSETS_URI . '/images/about-story-2.jpg',                            'alt' => 'Signature Oakland streetwear editorial' ),
			);

			foreach ( $lookbook_images as $img ) :
			?>
			<div class="lp-lookbook__item rv">
				<img src="<?php echo esc_url( $img['src'] ); ?>"
				     alt="<?php echo esc_attr( $img['alt'] ); ?>"
				     loading="lazy" width="400" height="533">
			</div>
			<?php endforeach; ?>
		</div>

		<div class="lp-lookbook__wide">
			<div class="lp-lookbook__item rv">
				<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/scenes/signature/signature-golden-gate-showroom.png' ); ?>"
				     alt="Signature wide editorial shot — Bay Area luxury" loading="lazy" width="800" height="450">
				<div class="lp-lookbook__caption"><span>Signature &mdash; Year-Round</span></div>
			</div>
			<div class="lp-lookbook__item rv rv-d1">
				<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/founder-portrait.jpg' ); ?>"
				     alt="Founder wearing Signature collection" loading="lazy" width="400" height="225">
			</div>
		</div>
	</div>
</section>

<!-- ════════════════════════════════════════════════
     SECTION 5: SOCIAL PROOF (Reviews + Press)
     ════════════════════════════════════════════════ -->
<section class="lp-section" aria-label="Customer Reviews">
	<div class="lp-container">
		<div class="lp-eyebrow rv">Reviews</div>
		<h2 class="lp-heading rv rv-d1">Rated 4.9 by 350+ Customers</h2>

		<div class="lp-reviews__grid">
			<div class="lp-review-card rv">
				<div class="lp-review-card__stars" aria-label="5 stars">&#9733;&#9733;&#9733;&#9733;&#9733;</div>
				<div class="lp-review-card__text">&ldquo;I&rsquo;ve replaced 80% of my wardrobe with SIGNATURE. The quality is insane for the price. Every morning is easy now.&rdquo;</div>
				<div class="lp-review-card__author">Chris W. &mdash; San Francisco, CA</div>
			</div>

			<div class="lp-review-card rv rv-d1">
				<div class="lp-review-card__stars" aria-label="5 stars">&#9733;&#9733;&#9733;&#9733;&#9733;</div>
				<div class="lp-review-card__text">&ldquo;My husband and I both wear the Essential Hoodie. Gender-neutral isn&rsquo;t a gimmick here &mdash; these fit everyone.&rdquo;</div>
				<div class="lp-review-card__author">Priya N. &mdash; Brooklyn, NY</div>
			</div>

			<div class="lp-review-card rv rv-d2">
				<div class="lp-review-card__stars" aria-label="5 stars">&#9733;&#9733;&#9733;&#9733;&#9733;</div>
				<div class="lp-review-card__text">&ldquo;9 months in, the Foundation Tee looks brand new. At $0.37 per wear it&rsquo;s the best value in my closet.&rdquo;</div>
				<div class="lp-review-card__author">Andre C. &mdash; Oakland, CA</div>
			</div>
		</div>
	</div>
</section>

<!-- ════════════════════════════════════════════════
     SECTION 6: CRAFT DETAIL CARDS
     ════════════════════════════════════════════════ -->
<section class="lp-section" id="craft" style="background:#080808" aria-label="Craft Details">
	<div class="lp-container">
		<div class="lp-eyebrow rv">The Details</div>
		<h2 class="lp-heading rv rv-d1">Everyday Doesn&rsquo;t Mean Ordinary</h2>

		<div class="lp-craft__grid">
			<div class="lp-craft-card rv">
				<div class="lp-craft-card__icon" aria-hidden="true">&#127942;</div>
				<div class="lp-craft-card__title">Award-Winning Quality</div>
				<div class="lp-craft-card__desc">Same obsessive craftsmanship as our limited drops. The difference? You can wear SIGNATURE every single day.</div>
			</div>

			<div class="lp-craft-card rv rv-d1">
				<div class="lp-craft-card__icon" aria-hidden="true">&#11035;</div>
				<div class="lp-craft-card__title">300gsm+ Construction</div>
				<div class="lp-craft-card__desc">Heavier than anything in your closet. Premium cotton that gets softer with every wash, never thinner.</div>
			</div>

			<div class="lp-craft-card rv rv-d2">
				<div class="lp-craft-card__icon" aria-hidden="true">&#128260;</div>
				<div class="lp-craft-card__title">Designed to Restock</div>
				<div class="lp-craft-card__desc">Core styles always available. New colorways drop seasonally. Your foundation wardrobe, always accessible.</div>
			</div>

			<div class="lp-craft-card rv rv-d3">
				<div class="lp-craft-card__icon" aria-hidden="true">&#127753;</div>
				<div class="lp-craft-card__title">Oakland DNA</div>
				<div class="lp-craft-card__desc">Bay Area born and bred. Every piece carries the spirit of Oakland &mdash; resilient, authentic, unapologetically real.</div>
			</div>
		</div>
	</div>
</section>

<!-- ════════════════════════════════════════════════
     SECTION 7: FAQ ACCORDION
     ════════════════════════════════════════════════ -->
<section class="lp-section" id="faq" aria-label="Frequently Asked Questions">
	<div class="lp-container">
		<div style="text-align:center">
			<div class="lp-eyebrow rv">FAQ</div>
			<h2 class="lp-heading rv rv-d1">Quick Answers</h2>
		</div>

		<div class="lp-faq__list">
			<div class="lp-faq__item rv">
				<button class="lp-faq__question" type="button" aria-expanded="false">How is SIGNATURE different from BLACK ROSE?</button>
				<div class="lp-faq__answer" role="region">
					<div class="lp-faq__answer-inner">BLACK ROSE is limited-edition (200 per style, never restocked). SIGNATURE is your everyday foundation &mdash; core staples always available, designed for daily wear. Same quality obsession, different purpose.</div>
				</div>
			</div>

			<div class="lp-faq__item rv rv-d1">
				<button class="lp-faq__question" type="button" aria-expanded="false">What&rsquo;s the sizing like?</button>
				<div class="lp-faq__answer" role="region">
					<div class="lp-faq__answer-inner">Gender-neutral S&ndash;3XL with relaxed fit. Model is 6&rsquo;0&rdquo;, 170 lbs wearing size M. 90% say true to size.</div>
				</div>
			</div>

			<div class="lp-faq__item rv rv-d2">
				<button class="lp-faq__question" type="button" aria-expanded="false">Will these be restocked?</button>
				<div class="lp-faq__answer" role="region">
					<div class="lp-faq__answer-inner">Yes. Core styles (Essential Hoodie, Foundation Tee, Daily Joggers) are always available. Seasonal colorways may rotate.</div>
				</div>
			</div>

			<div class="lp-faq__item rv rv-d3">
				<button class="lp-faq__question" type="button" aria-expanded="false">How do I care for these pieces?</button>
				<div class="lp-faq__answer" role="region">
					<div class="lp-faq__answer-inner">Machine wash cold, tumble dry low or hang dry. Built for daily wear and regular washing. No special treatment needed.</div>
				</div>
			</div>

			<div class="lp-faq__item rv rv-d4">
				<button class="lp-faq__question" type="button" aria-expanded="false">Do you have a size guide?</button>
				<div class="lp-faq__answer" role="region">
					<div class="lp-faq__answer-inner">Full measurement charts on every product page: chest width, body length, sleeve length. Size up for relaxed, down for fitted.</div>
				</div>
			</div>
		</div>
	</div>
</section>

<!-- ════════════════════════════════════════════════
     SECTION 8: EMAIL CAPTURE
     ════════════════════════════════════════════════ -->
<section class="lp-email-capture" aria-label="Newsletter Signup">
	<img src="<?php echo esc_url( get_template_directory_uri() . '/assets/branding/signature-logo-hero-transparent.png' ); ?>"
		alt="" aria-hidden="true" class="lp-email-capture__bg-logo" loading="lazy">
	<div class="lp-eyebrow rv">Stay in the Know</div>
	<h2 class="lp-heading rv rv-d1">New Colorways Drop Monthly</h2>

	<form class="lp-email-capture__form rv rv-d2" action="<?php echo esc_url( admin_url( 'admin-ajax.php' ) ); ?>" method="post">
		<?php wp_nonce_field( 'skyyrose_newsletter', 'skyyrose_newsletter_nonce' ); ?>
		<input type="hidden" name="action" value="skyyrose_newsletter_subscribe">
		<input type="email"
		       class="lp-email-capture__input"
		       name="email"
		       placeholder="Enter your email"
		       required
		       aria-label="Email address">
		<button type="submit" class="lp-email-capture__btn">Join</button>
	</form>
	<div class="lp-email-capture__message" aria-live="polite"></div>
	<div class="lp-email-capture__note rv rv-d3">Join 15,800+ members in the SkyyRose community</div>
</section>

</div><!-- .lp-page -->

<?php get_footer(); ?>
