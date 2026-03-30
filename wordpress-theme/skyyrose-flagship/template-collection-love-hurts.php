<?php
/**
 * Template Name: Collection - Love Hurts
 *
 * LOVE HURTS collection — Beauty and the Beast, the Hurts bloodline.
 * Uses unified collection layout (col-*) with data-collection="love-hurts".
 *
 * Palette: Crimson #DC143C / Deep Purple #2D0A1F / Rose-gold #B76E79
 *
 * @package SkyyRose_Flagship
 * @since   6.1.0
 */

defined( 'ABSPATH' ) || exit;

/* ── Product data ─────────────────────────────────────────────── */
$products = array();
$has_wc   = function_exists( 'wc_get_products' );

if ( $has_wc ) {
	$products = wc_get_products( array(
		'limit'    => 12,
		'category' => array( 'love-hurts' ),
		'status'   => 'publish',
		'orderby'  => 'menu_order',
		'order'    => 'ASC',
	) );
}

if ( empty( $products ) ) {
	$catalog_products = skyyrose_get_collection_products( 'love-hurts' );
	foreach ( $catalog_products as $cat_product ) {
		$products[] = array(
			'title'      => $cat_product['name'],
			'price'      => skyyrose_format_price( $cat_product ),
			'badge_text' => $cat_product['badge'],
			'sku'        => $cat_product['sku'],
			'image_url'  => skyyrose_product_image_uri( $cat_product['front_model_image'] ?: $cat_product['image'] ),
			'image_back' => skyyrose_product_image_uri( $cat_product['back_image'] ),
		);
	}
}

/* ── Emotion cards (Love Hurts unique section) ────────────────── */
$features = array(
	array( 'icon' => '&#x1F5A4;', 'title' => __( "Beast's Vulnerability", 'skyyrose-flagship' ), 'text' => __( "Strength isn't the roar. It's the silence after — when you choose to stay open instead of closing off. These pieces honor the courage it takes to be soft in a world that rewards hardness.", 'skyyrose-flagship' ) ),
	array( 'icon' => '&#x1F339;', 'title' => __( 'The Enchanted Rose', 'skyyrose-flagship' ), 'text' => __( "Protected under glass, glowing in a dark room, losing petals one by one. The rose is every love worth fighting for — fragile and fierce at the same time.", 'skyyrose-flagship' ) ),
	array( 'icon' => '&#x1F4AB;', 'title' => __( 'The Transformation', 'skyyrose-flagship' ), 'text' => __( "From concrete to runway. From grief to grace. The Hurts bloodline doesn't break — it metamorphoses. The Beast becoming the prince he always was.", 'skyyrose-flagship' ) ),
);

/* ── Cross-collection navigation ──────────────────────────────── */
$cross_nav = array(
	array( 'slug' => 'collection-black-rose', 'name' => __( 'Black Rose', 'skyyrose-flagship' ), 'desc' => __( 'Dark Elegance', 'skyyrose-flagship' ), 'class' => 'col-crossnav__link--black-rose' ),
	array( 'slug' => 'collection-signature', 'name' => __( 'Signature', 'skyyrose-flagship' ), 'desc' => __( 'The Foundation', 'skyyrose-flagship' ), 'class' => 'col-crossnav__link--signature' ),
	array( 'slug' => 'collection-kids-capsule', 'name' => __( 'Kids Capsule', 'skyyrose-flagship' ), 'desc' => __( 'Next Generation', 'skyyrose-flagship' ), 'class' => 'col-crossnav__link--kids-capsule' ),
);

$svg_kses = skyyrose_svg_kses();

get_header();
?>

<div class="col-page" data-collection="love-hurts">
	<div class="col-floating" aria-hidden="true"></div>

	<!-- ════ Hero ════ -->
	<section class="col-hero ambient-glow" data-scroll-fade>
		<div class="col-hero__bg parallax-ken-burns">
			<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/branding/sr-collection-love-hurts.webp?v=' . SKYYROSE_VERSION ); ?>"
			     alt="<?php esc_attr_e( 'Love Hurts Collection — enchanted rose under glass', 'skyyrose-flagship' ); ?>"
			     loading="eager" fetchpriority="high" decoding="async" width="1024" height="1024">
		</div>
		<div class="col-hero__content col-reveal">
			<span class="col-hero__badge rv-blur-down"><?php esc_html_e( 'The Hurts Bloodline', 'skyyrose-flagship' ); ?></span>
			<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . '/branding/love-hurts-logo-hero-transparent.png?v=' . SKYYROSE_VERSION ); ?>"
			     alt="<?php esc_attr_e( 'Love Hurts', 'skyyrose-flagship' ); ?>"
			     class="col-hero__logo rv-clip-up" width="400" height="400" loading="eager">
			<p class="col-hero__tagline rv-split-word"><?php esc_html_e( 'They called me Beast. They were right.', 'skyyrose-flagship' ); ?></p>
			<p class="col-hero__subtitle rv-blur"><?php esc_html_e( 'But even the Beast kept a rose under glass — protecting the most fragile thing he ever loved. This collection carries the weight of three generations of Hurts.', 'skyyrose-flagship' ); ?></p>
			<div class="col-hero__cta-group">
				<a href="#shop" class="col-hero__cta col-hero__cta--primary btn-sweep btn-press"><?php esc_html_e( 'Shop the Collection', 'skyyrose-flagship' ); ?></a>
				<a href="<?php echo esc_url( home_url( '/experience-love-hurts/' ) ); ?>" class="col-hero__cta col-hero__cta--secondary btn-border-draw btn-press"><?php esc_html_e( 'Enter the 3D Experience', 'skyyrose-flagship' ); ?></a>
			</div>
		</div>
		<div class="col-hero__scroll" aria-hidden="true"><span><?php esc_html_e( 'Explore', 'skyyrose-flagship' ); ?></span><span>&#x2193;</span></div>
	</section>

	<!-- ════ Marquee ════ -->
	<div class="col-marquee" aria-hidden="true">
		<div class="col-marquee__track">
			<?php for ( $i = 0; $i < 8; $i++ ) : ?>
				<span><?php esc_html_e( 'The Hurts Bloodline', 'skyyrose-flagship' ); ?></span>
				<span>&#x2665;</span>
				<span><?php esc_html_e( 'Love Is Worth the Pain', 'skyyrose-flagship' ); ?></span>
				<span>&#x2665;</span>
			<?php endfor; ?>
		</div>
	</div>

	<!-- ════ Story: The Hurts Bloodline ════ -->
	<section class="col-story rv-clip-up">
		<div class="col-story__grid">
			<div class="col-story__content">
				<span class="col-story__label"><?php esc_html_e( 'The Bloodline', 'skyyrose-flagship' ); ?></span>
				<h2 class="col-story__title"><?php esc_html_e( 'The Hurts Bloodline', 'skyyrose-flagship' ); ?></h2>
				<p class="col-story__text"><?php esc_html_e( 'My grandmother used to say it plain: "Love hurts, baby. That\'s how you know it\'s real." She wasn\'t being poetic. She was teaching survival. Three generations of Hurts women and men poured everything into the people they loved — and the world poured pain right back. But they never stopped loving. Not once.', 'skyyrose-flagship' ); ?></p>
				<blockquote class="col-story__quote"><?php esc_html_e( '"The Beast didn\'t hide because he was ugly. He hid because he loved something so beautiful it terrified him. The rose under glass — that\'s every Hurts who ever kept loving when love didn\'t love them back."', 'skyyrose-flagship' ); ?></blockquote>
				<p class="col-story__text"><?php esc_html_e( "This collection carries grandmother's name. Not as a brand, but as a bloodline truth. Every stitch holds the weight of family dinners where we laughed through grief, of front porches where grandmama told stories while pressing creases into Sunday shirts.", 'skyyrose-flagship' ); ?></p>
			</div>
			<div class="col-story__visual">
				<span class="col-story__visual-text"><?php esc_html_e( 'LOVE HURTS', 'skyyrose-flagship' ); ?></span>
				<span class="col-story__visual-label"><?php esc_html_e( 'The Hurts Bloodline', 'skyyrose-flagship' ); ?></span>
			</div>
		</div>
	</section>

	<!-- ════ Divider + Quote ════ -->
	<div class="col-divider" aria-hidden="true"><span class="col-divider__icon">&#x1F339;</span></div>
	<div class="col-quote-block rv-blur">
		<blockquote class="col-quote-block__text"><?php esc_html_e( '"Every petal that falls is a lesson. Every thorn is a boundary. The enchanted rose doesn\'t die — it transforms. Just like us."', 'skyyrose-flagship' ); ?></blockquote>
		<cite class="col-quote-block__cite">&mdash; <?php esc_html_e( 'From Grit to Grace', 'skyyrose-flagship' ); ?></cite>
	</div>

	<!-- ════ Emotion Cards ════ -->
	<section class="col-features rv-clip-left">
		<h2 class="col-features__heading"><?php esc_html_e( 'The Emotional Architecture', 'skyyrose-flagship' ); ?></h2>
		<p class="col-features__subheading"><?php esc_html_e( 'Crimson for the blood we share. Deep purple for the bruises that became wisdom. Burgundy for the wine grandmama poured when she said, "Baby, you survived another one."', 'skyyrose-flagship' ); ?></p>
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
			<p><?php esc_html_e( 'Pieces forged in the Hurts bloodline', 'skyyrose-flagship' ); ?></p>
		</div>
		<div class="product-grid stagger-grid" data-collection="love-hurts">
			<div class="product-grid__items">
				<?php
				$index = 0;
				foreach ( $products as $item ) :
					if ( $item instanceof WC_Product ) {
						$card_args = array( 'product' => $item, 'collection' => 'love-hurts', 'index' => $index );
					} else {
						$card_args = array( 'product' => null, 'title' => $item['title'] ?? '', 'price' => $item['price'] ?? '', 'badge_text' => $item['badge_text'] ?? '', 'collection' => 'love-hurts', 'permalink' => '#', 'sku' => $item['sku'] ?? '', 'index' => $index );
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
		<h2 class="col-cta__title"><?php esc_html_e( 'Wear the Bloodline', 'skyyrose-flagship' ); ?></h2>
		<p class="col-cta__text"><?php esc_html_e( "Every piece carries grandmother's truth: love is worth the pain. The Beast kept the rose under glass not out of fear, but out of reverence. This collection is that reverence, made wearable.", 'skyyrose-flagship' ); ?></p>
		<a href="<?php echo esc_url( $has_wc ? wc_get_cart_url() : home_url( '/shop/' ) ); ?>" class="col-cta__btn"><?php esc_html_e( 'Shop Love Hurts', 'skyyrose-flagship' ); ?></a>
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
		<p class="col-newsletter__text"><?php esc_html_e( 'First access to new drops and the stories behind every petal.', 'skyyrose-flagship' ); ?></p>
		<form class="col-newsletter__form" aria-label="<?php esc_attr_e( 'Newsletter signup', 'skyyrose-flagship' ); ?>">
			<label class="screen-reader-text" for="lh-email"><?php esc_html_e( 'Email address', 'skyyrose-flagship' ); ?></label>
			<input type="email" id="lh-email" class="col-newsletter__input" placeholder="<?php esc_attr_e( 'Enter your email', 'skyyrose-flagship' ); ?>" required>
			<button type="submit" class="col-newsletter__submit"><?php esc_html_e( 'Join', 'skyyrose-flagship' ); ?></button>
		</form>
	</section>

</div><!-- .col-page -->

<?php get_footer(); ?>
