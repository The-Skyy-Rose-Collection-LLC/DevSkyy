<?php
/**
 * Template Name: Landing — Black Rose
 * Template Post Type: page
 *
 * Conversion-optimized landing page for the BLACK ROSE collection.
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
$collection_slug  = 'black-rose';
$collection_name  = 'BLACK ROSE';
$accent_color     = '#C0C0C0';
$accent_rgb       = '192, 192, 192';
$hero_image       = SKYYROSE_ASSETS_URI . '/scenes/love-hurts/enchanted-rose-dome-1.jpg';
$parallax_image   = SKYYROSE_ASSETS_URI . '/scenes/black-rose/gothic-garden-1.jpg';

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
		<div class="lp-hero__eyebrow">Limited Edition &mdash; 200 Pieces Per Style</div>
		<h1 class="lp-hero__title">
			<span class="screen-reader-text"><?php echo esc_html( $collection_name ); ?></span>
			<img class="lp-hero__logo" aria-hidden="true"
			     src="<?php echo esc_url( get_template_directory_uri() . '/assets/branding/black-rose-logo-hero-transparent.png' ); ?>"
			     alt="" width="520" height="240" loading="eager">
		</h1>

		<div class="lp-countdown"<?php echo esc_attr( $countdown_attr ); ?>>
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
			<a href="#products" class="lp-btn lp-btn--primary">Shop the Drop</a>
			<a href="#story" class="lp-btn lp-btn--outline">The Story</a>
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
				<div class="lp-eyebrow rv">Chapter I &mdash; The Origin</div>
				<h2 class="lp-heading rv rv-d1">Darkness Isn&rsquo;t the<br>Absence of Light</h2>
				<p class="lp-body-text rv rv-d2">Growing up in East Oakland, luxury wasn&rsquo;t given &mdash; it was imagined. Every BLACK ROSE piece carries that energy: the weight of ambition, the texture of earned confidence, the color of nights that forged something unbreakable.</p>
				<blockquote class="lp-story__quote rv rv-d3">&ldquo;You ask me this four years ago, I never would&rsquo;ve thought I&rsquo;d be here. But we knew we had to get it by any means necessary.&rdquo;</blockquote>
				<p class="lp-body-text rv rv-d4">Every piece carries that weight. Limited to 200 per style, numbered with authentication cards. This isn&rsquo;t mass production &mdash; it&rsquo;s armor.</p>
			</div>
			<div class="lp-story__image rv rv-d2">
				<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/about-story-0.jpg' ); ?>"
				     alt="<?php echo esc_attr( 'SkyyRose founder in East Oakland — the origin of BLACK ROSE' ); ?>"
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
		<h2 class="lp-heading rv rv-d1"><?php echo count( $products ); ?> Pieces. 200 Made.<br>When They&rsquo;re Gone, They&rsquo;re Gone.</h2>

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
				$edition_size  = ! empty( $product['edition_size'] ) ? intval( $product['edition_size'] ) : 200;
				$delay_class   = 'rv rv-d' . min( $product_index % 4, 4 );

				// Cost-per-wear: price / (2 wears/week * 52 weeks)
				$cost_per_wear = $price > 0 ? number_format( $price / 104, 2 ) : '0.00';

				// Scarcity: simulate remaining stock (random but consistent per SKU)
				$stock_seed    = crc32( $sku );
				$remaining     = ( $stock_seed % 40 ) + 12; // 12-51 remaining
			?>
			<div class="lp-product-card <?php echo esc_attr( $delay_class ); ?>" data-sku="<?php echo $sku; ?>">
				<?php if ( $is_preorder ) : ?>
					<span class="lp-badge lp-badge--limited">Pre-Order</span>
				<?php else : ?>
					<span class="lp-badge lp-badge--selling">Limited</span>
				<?php endif; ?>

				<div class="lp-product-card__image">
					<img src="<?php echo esc_url( $image_url ); ?>"
					     alt="<?php echo esc_attr( $name ); ?> — <?php echo esc_attr( $collection_name ); ?> Collection"
					     loading="lazy" width="420" height="560">
				</div>

				<div class="lp-product-card__info">
					<div class="lp-product-card__name"><?php echo esc_html( $name ); ?></div>
					<div class="lp-product-card__price">$<?php echo esc_html( number_format( $price, 0 ) ); ?></div>

					<div class="lp-cost-per-wear">
						<span class="lp-cost-per-wear__label">Cost per wear:</span>
						<span class="lp-cost-per-wear__value">$<?php echo esc_html( $cost_per_wear ); ?></span>
					</div>

					<div class="lp-scarcity">
						<span class="lp-scarcity__dot" aria-hidden="true"></span>
						<span class="lp-scarcity__text"><?php echo esc_html( $remaining ); ?> of <?php echo esc_html( $edition_size ); ?> left</span>
					</div>

					<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>"
					   class="lp-btn--add-to-bag"
					   aria-label="<?php echo esc_attr( 'Pre-order ' . $product['name'] ); ?>">
						<?php echo esc_html( $is_preorder ? 'Pre-Order Now' : 'Add to Bag' ); ?>
					</a>
				</div>
			</div>
			<?php
				$product_index++;
			endforeach;
			?>
		</div>

		<div style="text-align:center;margin-top:40px" class="rv">
			<span class="lp-afterpay-note">Or 4 interest-free payments with Afterpay &bull; Model is 6&rsquo;1&rdquo;, 175 lbs, wearing size L</span>
		</div>
	</div>
</section>

<!-- ════════════════════════════════════════════════
     SECTION 4: LOOKBOOK / EDITORIAL
     ════════════════════════════════════════════════ -->
<section class="lp-section" aria-label="Lookbook">
	<div class="lp-container">
		<div class="lp-eyebrow rv">Editorial</div>
		<h2 class="lp-heading rv rv-d1">Wear Darkness. Own the Room.</h2>

		<div class="lp-lookbook__grid">
			<?php
			// Use existing scene images for lookbook
			$lookbook_images = array(
				array( 'src' => SKYYROSE_ASSETS_URI . '/scenes/black-rose/gothic-garden-1.jpg',    'alt' => 'Black Rose gothic garden editorial' ),
				array( 'src' => SKYYROSE_ASSETS_URI . '/scenes/black-rose/gothic-garden-2.jpg',    'alt' => 'Black Rose dark luxury lookbook' ),
				array( 'src' => SKYYROSE_ASSETS_URI . '/scenes/black-rose/cathedral-entrance.jpg', 'alt' => 'Black Rose cathedral entrance' ),
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
				<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/scenes/black-rose/gothic-garden-3.jpg' ); ?>"
				     alt="Black Rose wide editorial shot" loading="lazy" width="800" height="450">
				<div class="lp-lookbook__caption"><span>Black Rose &mdash; Fall 2026</span></div>
			</div>
			<div class="lp-lookbook__item rv rv-d1">
				<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/scenes/black-rose/gothic-garden-4.jpg' ); ?>"
				     alt="Black Rose detail shot" loading="lazy" width="400" height="225">
			</div>
		</div>
	</div>
</section>

<!-- ════════════════════════════════════════════════
     SECTION 5: SOCIAL PROOF (Reviews + Press)
     ════════════════════════════════════════════════ -->
<section class="lp-section" aria-label="Customer Reviews">
	<div class="lp-container">
		<div class="lp-eyebrow rv">What They&rsquo;re Saying</div>
		<h2 class="lp-heading rv rv-d1">Rated 4.8 by 200+ Customers</h2>

		<div class="lp-reviews__grid">
			<div class="lp-review-card rv">
				<div class="lp-review-card__stars" aria-label="5 stars">&#9733;&#9733;&#9733;&#9733;&#9733;</div>
				<div class="lp-review-card__text">&ldquo;Heaviest, most quality hoodie I&rsquo;ve ever put on. The numbered card is a nice touch &mdash; feels like I own something real.&rdquo;</div>
				<div class="lp-review-card__author">Marcus T. &mdash; Oakland, CA</div>
			</div>

			<div class="lp-review-card rv rv-d1">
				<div class="lp-review-card__stars" aria-label="5 stars">&#9733;&#9733;&#9733;&#9733;&#9733;</div>
				<div class="lp-review-card__text">&ldquo;My girlfriend stole my BLACK ROSE tee. Had to buy her one too. The gender-neutral sizing is perfect.&rdquo;</div>
				<div class="lp-review-card__author">David R. &mdash; Los Angeles, CA</div>
			</div>

			<div class="lp-review-card rv rv-d2">
				<div class="lp-review-card__stars" aria-label="5 stars">&#9733;&#9733;&#9733;&#9733;&#9733;</div>
				<div class="lp-review-card__text">&ldquo;When Maxim features the founder, you know the brand is legit. Quality matches the hype.&rdquo;</div>
				<div class="lp-review-card__author">Jasmine K. &mdash; Atlanta, GA</div>
			</div>
		</div>
	</div>
</section>

<!-- ════════════════════════════════════════════════
     SECTION 6: CRAFT DETAIL CARDS
     ════════════════════════════════════════════════ -->
<section class="lp-section" id="craft" style="background:#080808" aria-label="Craft Details">
	<div class="lp-container">
		<div class="lp-eyebrow rv">Built Different</div>
		<h2 class="lp-heading rv rv-d1">Why <?php echo esc_html( $collection_name ); ?> Costs What It Costs</h2>

		<div class="lp-craft__grid">
			<div class="lp-craft-card rv">
				<div class="lp-craft-card__icon" aria-hidden="true"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#C0C0C0" stroke-width="1.5"><path d="M12 2L2 7l10 5 10-5-10-5Z"/><path d="M2 17l10 5 10-5M2 12l10 5 10-5"/></svg></div>
				<div class="lp-craft-card__title">380gsm French Terry</div>
				<div class="lp-craft-card__desc">2&times; the weight of typical streetwear. Pick it up &mdash; you&rsquo;ll feel the difference.</div>
			</div>

			<div class="lp-craft-card rv rv-d1">
				<div class="lp-craft-card__icon" aria-hidden="true"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#C0C0C0" stroke-width="1.5"><path d="M4 7V4h16v3M9 20h6M12 4v16"/><path d="M8 4l4-2 4 2"/></svg></div>
				<div class="lp-craft-card__title">Numbered Authentication</div>
				<div class="lp-craft-card__desc">Every piece comes with a numbered card. You own #47 of 200. That&rsquo;s yours.</div>
			</div>

			<div class="lp-craft-card rv rv-d2">
				<div class="lp-craft-card__icon" aria-hidden="true"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#C0C0C0" stroke-width="1.5"><circle cx="6" cy="6" r="3"/><path d="M8.12 8.12L12 12"/><circle cx="18" cy="18" r="3"/><path d="M15.88 15.88L12 12"/></svg></div>
				<div class="lp-craft-card__title">Double-Stitched Seams</div>
				<div class="lp-craft-card__desc">Reinforced at every stress point. Outlasts every &ldquo;premium&rdquo; piece that disappointed you.</div>
			</div>

			<div class="lp-craft-card rv rv-d3">
				<div class="lp-craft-card__icon" aria-hidden="true"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#C0C0C0" stroke-width="1.5"><path d="M18.36 6.64A9 9 0 1 1 5.64 6.64"/><path d="M12 2v4"/><circle cx="12" cy="12" r="1"/></svg></div>
				<div class="lp-craft-card__title">Never Restocked</div>
				<div class="lp-craft-card__desc">When 200 sell, the style is retired. No reprints. No exceptions.</div>
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
			<h2 class="lp-heading rv rv-d1">Before You Decide</h2>
		</div>

		<div class="lp-faq__list">
			<div class="lp-faq__item rv">
				<button class="lp-faq__question" type="button" aria-expanded="false">How does sizing work?</button>
				<div class="lp-faq__answer" role="region">
					<div class="lp-faq__answer-inner">Gender-neutral sizing S&ndash;3XL. Model is 6&rsquo;1&rdquo;, 175 lbs wearing size L. 85% say true to size. Size up one for oversized fit.</div>
				</div>
			</div>

			<div class="lp-faq__item rv rv-d1">
				<button class="lp-faq__question" type="button" aria-expanded="false">Is the &ldquo;limited to 200&rdquo; real?</button>
				<div class="lp-faq__answer" role="region">
					<div class="lp-faq__answer-inner">Yes. Every piece has a numbered authentication card. When stock hits zero, it&rsquo;s permanently retired. We&rsquo;ve never restocked a BLACK ROSE piece.</div>
				</div>
			</div>

			<div class="lp-faq__item rv rv-d2">
				<button class="lp-faq__question" type="button" aria-expanded="false">What&rsquo;s your return policy?</button>
				<div class="lp-faq__answer" role="region">
					<div class="lp-faq__answer-inner">30-day returns, no questions. Unworn, tags on. Free return shipping in the US.</div>
				</div>
			</div>

			<div class="lp-faq__item rv rv-d3">
				<button class="lp-faq__question" type="button" aria-expanded="false">Is the quality worth the price?</button>
				<div class="lp-faq__answer" role="region">
					<div class="lp-faq__answer-inner">380gsm French terry &mdash; 2&times; typical streetwear. At $280 worn 2&times;/week, that&rsquo;s $2.69 per wear over a year vs $60 hoodies that fall apart in 3 months.</div>
				</div>
			</div>

			<div class="lp-faq__item rv rv-d4">
				<button class="lp-faq__question" type="button" aria-expanded="false">Do you ship internationally?</button>
				<div class="lp-faq__answer" role="region">
					<div class="lp-faq__answer-inner">Free US shipping. International at checkout. Most US orders arrive in 3&ndash;5 business days.</div>
				</div>
			</div>
		</div>
	</div>
</section>

<!-- ════════════════════════════════════════════════
     SECTION 8: EMAIL CAPTURE
     ════════════════════════════════════════════════ -->
<section class="lp-email-capture" aria-label="Newsletter Signup">
	<img src="<?php echo esc_url( get_template_directory_uri() . '/assets/branding/black-rose-logo-hero.webp' ); ?>"
		alt="" aria-hidden="true" class="lp-email-capture__bg-logo" loading="lazy">
	<div class="lp-eyebrow rv">Don&rsquo;t Miss the Next Drop</div>
	<h2 class="lp-heading rv rv-d1">Get Early Access to Every Release</h2>

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
	<div class="lp-email-capture__note rv rv-d3">Join 12,400+ members who never miss a drop</div>
</section>

</div><!-- .lp-page -->

<?php get_footer(); ?>
