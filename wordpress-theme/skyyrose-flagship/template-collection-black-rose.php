<?php
/**
 * Template Name: Collection - Black Rose
 *
 * BLACK ROSE collection — masculine elegance, silver on deep black.
 * Uses unified collection layout (col-*) with data-collection="black-rose".
 *
 * Palette: Silver #C0C0C0 / Deep #050505 / Crimson accent #DC143C
 *
 * @package SkyyRose_Flagship
 * @since   6.1.0
 */

defined( 'ABSPATH' ) || exit;

/* ── Product data (catalog = source of truth, WC enriches) ───── */
$products = skyyrose_get_collection_display_products( 'black-rose' );

/* ── Feature cards — The Philosophy ───────────────────────────── */
$features = array(
	array( 'icon' => '&#x1F5A4;', 'title' => __( 'Monochrome Mastery', 'skyyrose-flagship' ), 'text' => __( 'The depth of black carries what other colors cannot — layered textures, tonal contrasts, silhouettes that command presence without raising their voice.', 'skyyrose-flagship' ) ),
	array( 'icon' => '&#x1F339;', 'title' => __( 'The Thorn Motif', 'skyyrose-flagship' ), 'text' => __( 'Resilience encoded in every stitch. The thorn represents protective beauty — guarding what is precious while standing its ground.', 'skyyrose-flagship' ) ),
	array( 'icon' => '&#x25C6;', 'title' => __( 'Dark-on-Dark Texture', 'skyyrose-flagship' ), 'text' => __( 'This is not loud fashion. This is the quiet authority of someone who knows exactly who they are. Elegance distilled into every fiber.', 'skyyrose-flagship' ) ),
);

/* ── Cross-collection navigation ──────────────────────────────── */
$cross_nav = array(
	array( 'slug' => 'collection-love-hurts', 'name' => __( 'Love Hurts', 'skyyrose-flagship' ), 'desc' => __( 'Crimson Rebellion', 'skyyrose-flagship' ), 'class' => 'col-crossnav__link--love-hurts' ),
	array( 'slug' => 'collection-signature', 'name' => __( 'Signature', 'skyyrose-flagship' ), 'desc' => __( 'The Foundation', 'skyyrose-flagship' ), 'class' => 'col-crossnav__link--signature' ),
	array( 'slug' => 'collection-kids-capsule', 'name' => __( 'Kids Capsule', 'skyyrose-flagship' ), 'desc' => __( 'Next Generation', 'skyyrose-flagship' ), 'class' => 'col-crossnav__link--kids-capsule' ),
);

$svg_kses = skyyrose_svg_kses();

get_header();
?>

<div class="col-page" data-collection="black-rose">
	<div class="col-floating" aria-hidden="true"></div>

	<!-- ════ Hero ════ -->
	<section class="col-hero ambient-glow" data-scroll-fade>
		<div class="col-hero__bg parallax-ken-burns">
			<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/branding/sr-collection-black-rose.webp?v=' . SKYYROSE_VERSION ); ?>"
			     alt="<?php esc_attr_e( 'Black Rose Collection — rose from concrete', 'skyyrose-flagship' ); ?>"
			     loading="eager" fetchpriority="high" decoding="async" width="1024" height="1024">
		</div>
		<div class="col-hero__content col-reveal">
			<span class="col-hero__badge rv-blur-down"><?php esc_html_e( 'The Original Collection', 'skyyrose-flagship' ); ?></span>
			<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/branding/black-rose-logo-hero-transparent.png?v=' . SKYYROSE_VERSION ); ?>"
			     alt="<?php esc_attr_e( 'The Black Rose Collection', 'skyyrose-flagship' ); ?>"
			     class="col-hero__logo rv-clip-up" width="560" height="280" loading="eager">
			<p class="col-hero__tagline rv-split-word"><?php esc_html_e( 'The beauty of the color black through the rose and high-end fashion design.', 'skyyrose-flagship' ); ?></p>
			<p class="col-hero__subtitle rv-blur"><?php esc_html_e( 'Monochrome sophistication. Dark-on-dark texture. Masculine elegance distilled into every fiber. Every man would wear a black rose.', 'skyyrose-flagship' ); ?></p>
			<div class="col-hero__cta-group">
				<a href="#shop" class="col-hero__cta col-hero__cta--primary btn-sweep btn-press"><?php esc_html_e( 'Shop the Collection', 'skyyrose-flagship' ); ?></a>
				<a href="<?php echo esc_url( home_url( '/experience-black-rose/' ) ); ?>" class="col-hero__cta col-hero__cta--secondary btn-border-draw btn-press"><?php esc_html_e( 'View 3D Experience', 'skyyrose-flagship' ); ?></a>
			</div>
		</div>
		<div class="col-hero__scroll" aria-hidden="true"><span><?php esc_html_e( 'Discover', 'skyyrose-flagship' ); ?></span><span>&#x2193;</span></div>
	</section>

	<!-- ════ Marquee ════ -->
	<div class="col-marquee" aria-hidden="true">
		<div class="col-marquee__track">
			<?php for ( $i = 0; $i < 8; $i++ ) : ?>
				<span><?php esc_html_e( 'Dark Elegance', 'skyyrose-flagship' ); ?></span>
				<span>&#x25C6;</span>
				<span><?php esc_html_e( 'Masculine Power', 'skyyrose-flagship' ); ?></span>
				<span>&#x25C6;</span>
			<?php endfor; ?>
		</div>
	</div>

	<!-- ════ Story ════ -->
	<section class="col-story rv-clip-up">
		<div class="col-story__grid">
			<div class="col-story__content">
				<span class="col-story__label"><?php esc_html_e( 'From the Concrete', 'skyyrose-flagship' ); ?></span>
				<h2 class="col-story__title"><?php esc_html_e( 'Born from a Single Question', 'skyyrose-flagship' ); ?></h2>
				<p class="col-story__text"><?php esc_html_e( 'Someone asked what SkyyRose made for men. The answer came before the question finished: every man would wear a black rose. Not a flower — a conviction. In Oakland, where concrete is the only soil that matters, beauty doesn\'t ask for permission. It forces its way through the cracks.', 'skyyrose-flagship' ); ?></p>
				<blockquote class="col-story__quote"><?php esc_html_e( '"They said luxury can\'t come from the Town. We said watch. Every piece in Black Rose is the concrete answering back."', 'skyyrose-flagship' ); ?></blockquote>
				<p class="col-story__text"><?php esc_html_e( 'Black Rose is what happens when you stop apologizing for where you\'re from. Monochrome because silence speaks louder. Dark-on-dark because depth is earned, not given. These aren\'t clothes that announce themselves — they command presence the way Oakland taught us. Quiet. Unshakable.', 'skyyrose-flagship' ); ?></p>
			</div>
			<div class="col-story__visual">
				<span class="col-story__visual-text"><?php esc_html_e( 'BLACK ROSE', 'skyyrose-flagship' ); ?></span>
				<span class="col-story__visual-label"><?php esc_html_e( 'Dark Elegance', 'skyyrose-flagship' ); ?></span>
			</div>
		</div>
	</section>

	<!-- ════ Divider + Quote ════ -->
	<div class="col-divider" aria-hidden="true"><span class="col-divider__icon">&#x25C6;</span></div>
	<div class="col-quote-block rv-blur">
		<blockquote class="col-quote-block__text"><?php esc_html_e( '"Where I\'m from, black isn\'t a color — it\'s armor. Every kid on my block knew that. Black Rose is that truth made into fabric. You don\'t wear it to stand out. You wear it because you already stood up."', 'skyyrose-flagship' ); ?></blockquote>
		<cite class="col-quote-block__cite">&mdash; <?php esc_html_e( 'Corey Foster, Oakland', 'skyyrose-flagship' ); ?></cite>
	</div>

	<!-- ════ Feature Cards ════ -->
	<section class="col-features rv-clip-left">
		<h2 class="col-features__heading"><?php esc_html_e( 'The Philosophy', 'skyyrose-flagship' ); ?></h2>
		<p class="col-features__subheading"><?php esc_html_e( 'Every stitch, every detail is designed to empower you to move through the world on your own terms.', 'skyyrose-flagship' ); ?></p>
		<div class="col-features__grid stagger-grid">
			<?php foreach ( $features as $feat ) : ?>
				<div class="col-features__card">
					<div class="col-features__icon" aria-hidden="true"><?php echo wp_kses( $feat['icon'], $svg_kses ); ?></div>
					<h3><?php echo esc_html( $feat['title'] ); ?></h3>
					<p><?php echo esc_html( $feat['text'] ); ?></p>
				</div>
			<?php endforeach; ?>
		</div>
	</section>

	<!-- ════ Product Grid ════ -->
	<section class="col-products rv-clip-up" id="shop">
		<div class="col-products__header">
			<h2><?php esc_html_e( 'The Collection', 'skyyrose-flagship' ); ?></h2>
			<p><?php esc_html_e( 'Dark elegance — holographic preview', 'skyyrose-flagship' ); ?></p>
		</div>
		<div class="product-grid stagger-grid" data-collection="black-rose">
			<div class="product-grid__items">
				<?php
				$index = 0;
				foreach ( $products as $item ) :
					if ( $item instanceof WC_Product ) {
						$card_args = array( 'product' => $item, 'collection' => 'black-rose', 'index' => $index );
					} else {
						$card_args = array( 'product' => null, 'title' => $item['title'] ?? '', 'price' => $item['price'] ?? '', 'badge_text' => $item['badge_text'] ?? '', 'collection' => 'black-rose', 'permalink' => '#', 'sku' => $item['sku'] ?? '', 'index' => $index );
					}
					get_template_part( 'template-parts/product-card-holo', null, $card_args );
					$index++;
				endforeach;
				?>
			</div>
		</div>
	</section>

	<!-- ════ CTA ════ -->
	<section class="col-cta rv-blur">
		<h2 class="col-cta__title"><?php esc_html_e( 'Wear the Darkness', 'skyyrose-flagship' ); ?></h2>
		<p class="col-cta__text"><?php esc_html_e( 'The thorn protects what the world tries to take. Every piece in Black Rose carries that Oakland lesson: be beautiful, be sharp, never be soft where it counts.', 'skyyrose-flagship' ); ?></p>
		<a href="<?php echo esc_url( function_exists( 'wc_get_cart_url' ) ? wc_get_cart_url() : home_url( '/shop/' ) ); ?>" class="col-cta__btn"><?php esc_html_e( 'Shop Black Rose', 'skyyrose-flagship' ); ?></a>
	</section>

	<!-- ════ Cross-Collection Nav ════ -->
	<nav class="col-crossnav rv-clip-up" aria-label="<?php esc_attr_e( 'Other collections', 'skyyrose-flagship' ); ?>">
		<h3 class="col-crossnav__heading"><?php esc_html_e( 'Explore More Collections', 'skyyrose-flagship' ); ?></h3>
		<div class="col-crossnav__grid stagger-grid">
			<?php foreach ( $cross_nav as $nav ) : ?>
				<a href="<?php echo esc_url( home_url( '/' . $nav['slug'] . '/' ) ); ?>" class="col-crossnav__link <?php echo esc_attr( $nav['class'] ); ?>" aria-label="<?php echo esc_attr( sprintf( __( 'Explore the %s collection', 'skyyrose-flagship' ), $nav['name'] ) ); ?>">
					<h3><?php echo esc_html( $nav['name'] ); ?></h3>
					<p><?php echo esc_html( $nav['desc'] ); ?></p>
				</a>
			<?php endforeach; ?>
		</div>
	</nav>

	<!-- ════ Newsletter ════ -->
	<section class="col-newsletter rv-blur">
		<h2 class="col-newsletter__title"><?php esc_html_e( 'Join the Inner Circle', 'skyyrose-flagship' ); ?></h2>
		<p class="col-newsletter__text"><?php esc_html_e( 'First access to new drops, exclusive content, and the stories behind the darkness.', 'skyyrose-flagship' ); ?></p>
		<form class="col-newsletter__form" aria-label="<?php esc_attr_e( 'Newsletter signup', 'skyyrose-flagship' ); ?>">
			<label class="screen-reader-text" for="br-email"><?php esc_html_e( 'Email address', 'skyyrose-flagship' ); ?></label>
			<input type="email" id="br-email" class="col-newsletter__input" placeholder="<?php esc_attr_e( 'Enter your email', 'skyyrose-flagship' ); ?>" required>
			<button type="submit" class="col-newsletter__submit"><?php esc_html_e( 'Join', 'skyyrose-flagship' ); ?></button>
		</form>
	</section>

</div><!-- .col-page -->

<?php get_footer(); ?>
