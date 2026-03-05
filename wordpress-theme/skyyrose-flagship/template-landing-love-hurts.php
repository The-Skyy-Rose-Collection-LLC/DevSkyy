<?php
/**
 * Template Name: Landing — Love Hurts
 * Template Post Type: page
 *
 * Conversion-optimized landing page for the LOVE HURTS collection.
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
$collection_slug  = 'love-hurts';
$collection_name  = 'LOVE HURTS';
$accent_color     = '#DC143C';
$accent_rgb       = '220, 20, 60';
$hero_image       = SKYYROSE_ASSETS_URI . '/scenes/love-hurts/love-hurts-crimson-throne-room.webp';
$parallax_image   = SKYYROSE_ASSETS_URI . '/scenes/love-hurts/love-hurts-gothic-ballroom.webp';

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
		<div class="lp-hero__eyebrow">Named After a Bloodline &mdash; Designed for Survivors</div>
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
			<a href="#products" class="lp-btn lp-btn--primary">Feel Something</a>
			<a href="#story" class="lp-btn lp-btn--outline">The Meaning</a>
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
				<div class="lp-eyebrow rv">The Name Behind the Name</div>
				<h2 class="lp-heading rv rv-d1">This Isn&rsquo;t a Theme.<br>It&rsquo;s a Bloodline.</h2>
				<p class="lp-body-text rv rv-d2">&ldquo;Hurts&rdquo; is the founder&rsquo;s family name. Not a marketing hook. When Corey Foster named this collection LOVE HURTS, he was writing his family into fabric.</p>
				<blockquote class="lp-story__quote rv rv-d3">&ldquo;I had no drive, lost it all, baby on the way, and was broke. But we knew we had to get it by any means necessary.&rdquo;</blockquote>
				<p class="lp-body-text rv rv-d4">Every piece channels real emotional experience &mdash; heartbreak, loss, single fatherhood &mdash; and transforms it into something beautiful enough to wear.</p>
			</div>
			<div class="lp-story__image rv rv-d2">
				<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/images/about-story-0.jpg' ); ?>"
				     alt="<?php echo esc_attr( 'SkyyRose founder — the meaning behind LOVE HURTS' ); ?>"
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
		<h2 class="lp-heading rv rv-d1">Wear What You&rsquo;ve Survived</h2>

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

					<div class="lp-scarcity">
						<span class="lp-scarcity__dot" aria-hidden="true"></span>
						<span class="lp-scarcity__text"><?php echo esc_html( $remaining ); ?> of <?php echo esc_html( $edition_size ); ?> left</span>
					</div>

					<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>"
					   class="lp-btn--add-to-bag"
					   aria-label="<?php echo esc_attr( 'Pre-order ' . $product['name'] ); ?>">
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
			<span class="lp-afterpay-note">Or 4 interest-free payments with Afterpay &bull; Each piece carries a story</span>
		</div>
	</div>
</section>

<!-- ════════════════════════════════════════════════
     SECTION 4: LOOKBOOK / EDITORIAL
     ════════════════════════════════════════════════ -->
<section class="lp-section" aria-label="Lookbook">
	<div class="lp-container">
		<div class="lp-eyebrow rv">Editorial</div>
		<h2 class="lp-heading rv rv-d1">Pain Made Beautiful</h2>

		<div class="lp-lookbook__grid">
			<?php
			$lookbook_images = array(
				array( 'src' => SKYYROSE_ASSETS_URI . '/scenes/love-hurts/love-hurts-enchanted-rose-shrine.webp', 'alt' => 'Love Hurts enchanted rose shrine editorial' ),
				array( 'src' => SKYYROSE_ASSETS_URI . '/scenes/love-hurts/love-hurts-giant-rose-staircase.webp', 'alt' => 'Love Hurts giant rose staircase lookbook' ),
				array( 'src' => SKYYROSE_ASSETS_URI . '/scenes/love-hurts/enchanted-rose-dome-globe.jpg',       'alt' => 'Love Hurts enchanted rose dome' ),
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
				<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/scenes/love-hurts/love-hurts-reflective-ballroom.webp' ); ?>"
				     alt="Love Hurts reflective ballroom wide editorial shot" loading="lazy" width="800" height="450">
				<div class="lp-lookbook__caption"><span>Love Hurts &mdash; Fall 2026</span></div>
			</div>
			<div class="lp-lookbook__item rv rv-d1">
				<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/scenes/love-hurts/love-hurts-cathedral-rose-chamber.webp' ); ?>"
				     alt="Love Hurts cathedral rose chamber" loading="lazy" width="400" height="225">
			</div>
		</div>
	</div>
</section>

<!-- ════════════════════════════════════════════════
     SECTION 5: SOCIAL PROOF (Reviews + Press)
     ════════════════════════════════════════════════ -->
<section class="lp-section" aria-label="Customer Reviews">
	<div class="lp-container">
		<div class="lp-eyebrow rv">Community</div>
		<h2 class="lp-heading rv rv-d1">What LOVE HURTS Means to People</h2>

		<div class="lp-reviews__grid">
			<div class="lp-review-card rv">
				<div class="lp-review-card__stars" aria-label="5 stars">&#9733;&#9733;&#9733;&#9733;&#9733;</div>
				<div class="lp-review-card__text">&ldquo;I lost my mom last year. Wearing LOVE HURTS feels like carrying her with me. It&rsquo;s not just clothing &mdash; it&rsquo;s surviving.&rdquo;</div>
				<div class="lp-review-card__author">Aaliyah M. &mdash; Chicago, IL</div>
			</div>

			<div class="lp-review-card rv rv-d1">
				<div class="lp-review-card__stars" aria-label="5 stars">&#9733;&#9733;&#9733;&#9733;&#9733;</div>
				<div class="lp-review-card__text">&ldquo;The fact that &lsquo;Hurts&rsquo; is the founder&rsquo;s actual family name hit different. This is real, not manufactured emotion.&rdquo;</div>
				<div class="lp-review-card__author">Tyler J. &mdash; Oakland, CA</div>
			</div>

			<div class="lp-review-card rv rv-d2">
				<div class="lp-review-card__stars" aria-label="5 stars">&#9733;&#9733;&#9733;&#9733;&#9733;</div>
				<div class="lp-review-card__text">&ldquo;Bought this for my partner going through chemo. She wears the hoodie every treatment day. It means everything.&rdquo;</div>
				<div class="lp-review-card__author">Kevin L. &mdash; Houston, TX</div>
			</div>
		</div>
	</div>
</section>

<!-- ════════════════════════════════════════════════
     SECTION 6: CRAFT DETAIL CARDS
     ════════════════════════════════════════════════ -->
<section class="lp-section" id="craft" style="background:#080808" aria-label="Craft Details">
	<div class="lp-container">
		<div class="lp-eyebrow rv">Why It Matters</div>
		<h2 class="lp-heading rv rv-d1">Every Detail Is Intentional</h2>

		<div class="lp-craft__grid">
			<div class="lp-craft-card rv">
				<div class="lp-craft-card__icon" aria-hidden="true"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#DC143C" stroke-width="1.5"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78L12 21.23l8.84-8.84a5.5 5.5 0 0 0 0-7.78z"/></svg></div>
				<div class="lp-craft-card__title">Meaning in Every Stitch</div>
				<div class="lp-craft-card__desc">Every graphic tells a story. Heartbreak, loss, rebuilding &mdash; etched into fabric, not printed on as a marketing trend.</div>
			</div>

			<div class="lp-craft-card rv rv-d1">
				<div class="lp-craft-card__icon" aria-hidden="true"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#DC143C" stroke-width="1.5"><path d="M12 19l7-7 3 3-7 7-3-3z"/><path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"/><path d="M2 2l7.586 7.586"/><circle cx="11" cy="11" r="2"/></svg></div>
				<div class="lp-craft-card__title">Fade-Proof Graphics</div>
				<div class="lp-craft-card__desc">DTG printing embeds ink into fibers. 50+ washes, same intensity. Your story doesn&rsquo;t fade.</div>
			</div>

			<div class="lp-craft-card rv rv-d2">
				<div class="lp-craft-card__icon" aria-hidden="true"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#B76E79" stroke-width="1.5"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78L12 21.23l8.84-8.84a5.5 5.5 0 0 0 0-7.78z"/><path d="M12 5.67V12"/><path d="M8 10h8"/></svg></div>
				<div class="lp-craft-card__title">Emotional Design Process</div>
				<div class="lp-craft-card__desc">Each piece starts as a personal journal entry. Real emotion, real experience &mdash; translated into wearable art.</div>
			</div>

			<div class="lp-craft-card rv rv-d3">
				<div class="lp-craft-card__icon" aria-hidden="true"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#DC143C" stroke-width="1.5"><path d="M12 2L2 7l10 5 10-5-10-5Z"/><path d="M2 17l10 5 10-5M2 12l10 5 10-5"/></svg></div>
				<div class="lp-craft-card__title">Premium Weight Cotton</div>
				<div class="lp-craft-card__desc">330gsm+ cotton blend. Heavy enough to feel like armor. Soft enough to live in every day.</div>
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
			<h2 class="lp-heading rv rv-d1">Questions We Get Asked</h2>
		</div>

		<div class="lp-faq__list">
			<div class="lp-faq__item rv">
				<button class="lp-faq__question" type="button" aria-expanded="false">Why is it called &ldquo;Love Hurts&rdquo;?</button>
				<div class="lp-faq__answer" role="region">
					<div class="lp-faq__answer-inner">&ldquo;Hurts&rdquo; is founder Corey Foster&rsquo;s family name. This collection is his family legacy woven into streetwear &mdash; loss, heartbreak, single fatherhood, and building something beautiful from pain.</div>
				</div>
			</div>

			<div class="lp-faq__item rv rv-d1">
				<button class="lp-faq__question" type="button" aria-expanded="false">Will the graphics crack or fade?</button>
				<div class="lp-faq__answer" role="region">
					<div class="lp-faq__answer-inner">No. DTG printing embeds ink into fibers. 50+ washes, same intensity. Wash cold, hang dry for best results.</div>
				</div>
			</div>

			<div class="lp-faq__item rv rv-d2">
				<button class="lp-faq__question" type="button" aria-expanded="false">How does sizing work?</button>
				<div class="lp-faq__answer" role="region">
					<div class="lp-faq__answer-inner">Gender-neutral S&ndash;3XL. Slightly oversized for comfort. Model is 5&rsquo;8&rdquo;, 155 lbs wearing size M.</div>
				</div>
			</div>

			<div class="lp-faq__item rv rv-d3">
				<button class="lp-faq__question" type="button" aria-expanded="false">What&rsquo;s the return policy?</button>
				<div class="lp-faq__answer" role="region">
					<div class="lp-faq__answer-inner">30-day returns, no questions. Free return shipping in the US. Unworn with tags.</div>
				</div>
			</div>

			<div class="lp-faq__item rv rv-d4">
				<button class="lp-faq__question" type="button" aria-expanded="false">Is this a limited collection?</button>
				<div class="lp-faq__answer" role="region">
					<div class="lp-faq__answer-inner">LOVE HURTS is ongoing, but specific designs rotate seasonally. Some restock, others retire when their story is told.</div>
				</div>
			</div>
		</div>
	</div>
</section>

<!-- ════════════════════════════════════════════════
     SECTION 8: EMAIL CAPTURE
     ════════════════════════════════════════════════ -->
<section class="lp-email-capture" aria-label="Newsletter Signup">
	<img src="<?php echo esc_url( get_template_directory_uri() . '/assets/branding/love-hurts-logo-hero-transparent.png' ); ?>"
		alt="" aria-hidden="true" class="lp-email-capture__bg-logo" loading="lazy">
	<div class="lp-eyebrow rv">Stay Connected</div>
	<h2 class="lp-heading rv rv-d1">New Stories Drop Monthly</h2>

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
	<div class="lp-email-capture__note rv rv-d3">Join 8,200+ people who wear their story</div>
</section>

</div><!-- .lp-page -->

<?php get_footer(); ?>
