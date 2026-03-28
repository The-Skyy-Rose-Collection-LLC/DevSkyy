<?php
/**
 * Template Name: Collection - Love Hurts
 *
 * LOVE HURTS collection page — standalone template.
 * Floating hearts, crimson hero, Beast's perspective storytelling,
 * emotion cards, holographic product grid, cross-collection nav.
 *
 * Palette: --crimson #DC143C, --deep-purple #2D0A1F,
 *          --burgundy #722F37, --rose-gold #B76E79.
 *
 * @package SkyyRose_Flagship
 * @since   5.0.0
 */

defined( 'ABSPATH' ) || exit;

get_header();

/* ── WooCommerce products with static fallback ────────────────────── */
$lh_products  = array();
$has_wc       = function_exists( 'wc_get_products' );

if ( $has_wc ) {
	$wc_results = wc_get_products(
		array(
			'limit'    => 12,
			'category' => array( 'love-hurts' ),
			'status'   => 'publish',
			'orderby'  => 'menu_order',
			'order'    => 'ASC',
		)
	);
	if ( ! empty( $wc_results ) ) {
		foreach ( $wc_results as $wc_p ) {
			$lh_products[] = array( 'product' => $wc_p );
		}
	}
}

/* Static fallback when WooCommerce returns nothing. */
if ( empty( $lh_products ) ) {
	$lh_products = array(
		array(
			'title'      => __( 'Enchanted Rose Hoodie', 'skyyrose-flagship' ),
			'price'      => '$195',
			'badge_text' => __( 'Bestseller', 'skyyrose-flagship' ),
			'sku'        => 'lh-enchanted-rose-hoodie',
			'collection' => 'love-hurts',
		),
		array(
			'title'      => __( 'Beast Mode Tee', 'skyyrose-flagship' ),
			'price'      => '$85',
			'badge_text' => __( 'New', 'skyyrose-flagship' ),
			'sku'        => 'lh-beast-mode-tee',
			'collection' => 'love-hurts',
		),
		array(
			'title'      => __( 'Thorned Heart Jacket', 'skyyrose-flagship' ),
			'price'      => '$345',
			'badge_text' => __( 'Limited', 'skyyrose-flagship' ),
			'sku'        => 'lh-thorned-heart-jacket',
			'collection' => 'love-hurts',
		),
		array(
			'title'      => __( 'Bloodline Crewneck', 'skyyrose-flagship' ),
			'price'      => '$145',
			'sku'        => 'lh-bloodline-crewneck',
			'collection' => 'love-hurts',
		),
		array(
			'title'      => __( 'Glass Dome Varsity', 'skyyrose-flagship' ),
			'price'      => '$295',
			'badge_text' => __( 'New', 'skyyrose-flagship' ),
			'sku'        => 'lh-glass-dome-varsity',
			'collection' => 'love-hurts',
		),
		array(
			'title'      => __( 'Last Petal Joggers', 'skyyrose-flagship' ),
			'price'      => '$135',
			'sku'        => 'lh-last-petal-joggers',
			'collection' => 'love-hurts',
		),
	);
}

/* ── Emotion cards data ───────────────────────────────────────────── */
$emotion_cards = array(
	array(
		'icon'    => '&#x1F5A4;',
		'title'   => __( "Beast's Vulnerability", 'skyyrose-flagship' ),
		'text'    => __( "Strength isn't the roar. It's the silence after — when you choose to stay open instead of closing off. These pieces honor the courage it takes to be soft in a world that rewards hardness.", 'skyyrose-flagship' ),
	),
	array(
		'icon'    => '&#x1F339;',
		'title'   => __( 'The Enchanted Rose', 'skyyrose-flagship' ),
		'text'    => __( "Protected under glass, glowing in a dark room, losing petals one by one. The rose is every love worth fighting for — fragile and fierce at the same time. That's the Hurts legacy.", 'skyyrose-flagship' ),
	),
	array(
		'icon'    => '&#x1F4AB;',
		'title'   => __( 'The Transformation', 'skyyrose-flagship' ),
		'text'    => __( "From concrete to runway. From grief to grace. The Hurts bloodline doesn't break — it metamorphoses. This collection is the cocoon splitting open. The Beast becoming the prince he always was.", 'skyyrose-flagship' ),
	),
);

/* ── Cross-collection nav ─────────────────────────────────────────── */
$cross_nav = array(
	array(
		'slug'  => 'collection-black-rose',
		'label' => __( 'Black Rose', 'skyyrose-flagship' ),
		'class' => 'col-crossnav__link--br',
	),
	array(
		'slug'  => 'collection-signature',
		'label' => __( 'Signature', 'skyyrose-flagship' ),
		'class' => 'col-crossnav__link--sg',
	),
	array(
		'slug'  => 'collection-kids-capsule',
		'label' => __( 'Kids Capsule', 'skyyrose-flagship' ),
		'class' => 'col-crossnav__link--kc',
	),
);
?>

<div class="lh-page">

	<!-- Floating Hearts -->
	<div class="lh-floating-hearts" id="lhFloatingHearts" aria-hidden="true"></div>

	<!-- ════════════ Hero ════════════ -->
	<section class="lh-hero">
		<div class="lh-hero__content">
			<span class="lh-hero__badge"><?php esc_html_e( 'The Hurts Bloodline', 'skyyrose-flagship' ); ?></span>
			<h1 class="lh-hero__title"><?php esc_html_e( 'LOVE HURTS', 'skyyrose-flagship' ); ?></h1>
			<p class="lh-hero__subtitle">
				<?php esc_html_e( "They called me Beast. They were right. But even the Beast kept a rose under glass — protecting the most fragile thing he ever loved.", 'skyyrose-flagship' ); ?>
			</p>
			<div class="lh-hero__cta-wrap">
				<a href="<?php echo esc_url( home_url( '/experience-love-hurts/' ) ); ?>" class="lh-hero__cta">
					<?php esc_html_e( 'Enter the 3D Experience', 'skyyrose-flagship' ); ?>
				</a>
			</div>
		</div>
		<div class="lh-hero__scroll" aria-hidden="true">
			<span><?php esc_html_e( 'Explore', 'skyyrose-flagship' ); ?></span>
			<span>&darr;</span>
		</div>
	</section>

	<!-- ════════════ Story: The Hurts Bloodline ════════════ -->
	<section class="lh-story">
		<div class="lh-story__content">
			<h2 class="lh-story__heading"><?php esc_html_e( 'The Hurts Bloodline', 'skyyrose-flagship' ); ?></h2>
			<p>
				<?php esc_html_e( 'My grandmother used to say it plain: "Love hurts, baby. That\'s how you know it\'s real." She wasn\'t being poetic. She was teaching survival. Three generations of Hurts women and men poured everything into the people they loved — and the world poured pain right back. But they never stopped loving. Not once.', 'skyyrose-flagship' ); ?>
			</p>
			<p>
				<?php esc_html_e( "This collection carries her name. Not as a brand, but as a bloodline truth. Every stitch holds the weight of family dinners where we laughed through grief, of front porches where grandmama told stories about grandpa while pressing creases into Sunday shirts. Love Hurts isn't a slogan. It's our last name.", 'skyyrose-flagship' ); ?>
			</p>
			<blockquote class="lh-story__quote">
				<?php esc_html_e( "\"The Beast didn't hide because he was ugly. He hid because he loved something so beautiful it terrified him. The rose under glass — that's every Hurts who ever kept loving when love didn't love them back.\"", 'skyyrose-flagship' ); ?>
			</blockquote>
			<p>
				<?php esc_html_e( "Beauty and the Beast was never a fairy tale to us. It was autobiography. The Beast is the kid from the concrete who learned tenderness from thorns. The enchanted rose is the love you protect with everything you have — fragile, glowing, losing petals — because letting it die means letting the best part of you die too.", 'skyyrose-flagship' ); ?>
			</p>
		</div>
	</section>

	<!-- ════════════ Enchanted Rose Divider ════════════ -->
	<div class="lh-rose-divider" aria-hidden="true">
		<span>&#x1F339;</span>
	</div>

	<!-- ════════════ Story: From Grit to Grace ════════════ -->
	<section class="lh-story">
		<div class="lh-story__content">
			<h2 class="lh-story__heading"><?php esc_html_e( 'From Grit to Grace', 'skyyrose-flagship' ); ?></h2>
			<p>
				<?php esc_html_e( "The Beast's curse wasn't the fangs or the claws. It was believing he didn't deserve softness. Every piece in Love Hurts is about that transformation — the moment you stop apologizing for the rawness in your chest and start wearing it like the armor it always was.", 'skyyrose-flagship' ); ?>
			</p>
			<p>
				<?php esc_html_e( 'Crimson for the blood we share. Deep purple for the bruises that became wisdom. Burgundy for the wine grandmama poured when she said, "Baby, you survived another one." These aren\'t just colors. They\'re the palette of a family that turned pain into something you can wear, something that says: I\'ve been through it, and I\'m still here.', 'skyyrose-flagship' ); ?>
			</p>
			<blockquote class="lh-story__quote">
				<?php esc_html_e( "\"Every petal that falls is a lesson. Every thorn is a boundary. The enchanted rose doesn't die — it transforms. Just like us.\"", 'skyyrose-flagship' ); ?>
			</blockquote>
		</div>
	</section>

	<!-- ════════════ Emotion Cards ════════════ -->
	<section class="lh-emotions">
		<div class="lh-emotions__grid">
			<?php foreach ( $emotion_cards as $card ) : ?>
				<div class="lh-emotions__card">
					<div class="lh-emotions__icon" aria-hidden="true"><?php echo wp_kses( $card['icon'], array( 'svg' => array( 'viewBox' => true, 'fill' => true, 'stroke' => true, 'class' => true, 'aria-hidden' => true, 'width' => true, 'height' => true, 'xmlns' => true ), 'path' => array( 'd' => true, 'fill' => true, 'stroke' => true, 'stroke-width' => true, 'stroke-linecap' => true, 'stroke-linejoin' => true ), 'circle' => array( 'cx' => true, 'cy' => true, 'r' => true, 'fill' => true ), 'line' => array( 'x1' => true, 'y1' => true, 'x2' => true, 'y2' => true, 'stroke' => true, 'stroke-width' => true ), 'polyline' => array( 'points' => true, 'fill' => true, 'stroke' => true, 'stroke-width' => true ), 'rect' => array( 'x' => true, 'y' => true, 'width' => true, 'height' => true, 'rx' => true, 'ry' => true, 'fill' => true, 'stroke' => true ) ) ); ?></div>
					<h3 class="lh-emotions__title"><?php echo esc_html( $card['title'] ); ?></h3>
					<p><?php echo esc_html( $card['text'] ); ?></p>
				</div>
			<?php endforeach; ?>
		</div>
	</section>

	<!-- ════════════ Holographic Product Grid ════════════ -->
	<section class="lh-products">
		<div class="product-grid" data-collection="love-hurts">
			<div class="product-grid__header">
				<h2 class="product-grid__title"><?php esc_html_e( 'The Collection', 'skyyrose-flagship' ); ?></h2>
				<p class="product-grid__subtitle"><?php esc_html_e( 'Pieces forged in the Hurts bloodline', 'skyyrose-flagship' ); ?></p>
			</div>

			<div class="product-grid__items">
				<?php
				foreach ( $lh_products as $idx => $card_args ) :
					$card_args['index']      = $idx;
					$card_args['collection'] = $card_args['collection'] ?? 'love-hurts';
					get_template_part( 'template-parts/product-card-holo', null, $card_args );
				endforeach;
				?>
			</div>
		</div>
	</section>

	<!-- ════════════ Wear the Bloodline CTA ════════════ -->
	<section class="lh-cta">
		<h2><?php esc_html_e( 'Wear the Bloodline', 'skyyrose-flagship' ); ?></h2>
		<p>
			<?php esc_html_e( "Every piece carries grandmother's truth: love is worth the pain. The Beast kept the rose under glass not out of fear, but out of reverence. This collection is that reverence, made wearable.", 'skyyrose-flagship' ); ?>
		</p>
		<a href="<?php echo esc_url( $has_wc ? wc_get_cart_url() : home_url( '/shop/' ) ); ?>" class="lh-cta__btn">
			<?php esc_html_e( 'Shop Love Hurts', 'skyyrose-flagship' ); ?>
		</a>
	</section>

	<!-- ════════════ Cross-Collection Nav ════════════ -->
	<nav class="lh-crossnav" aria-label="<?php esc_attr_e( 'Other collections', 'skyyrose-flagship' ); ?>">
		<h3 class="lh-crossnav__heading"><?php esc_html_e( 'Explore More Collections', 'skyyrose-flagship' ); ?></h3>
		<div class="lh-crossnav__links">
			<?php foreach ( $cross_nav as $nav_item ) : ?>
				<a href="<?php echo esc_url( home_url( '/' . $nav_item['slug'] . '/' ) ); ?>"
				   class="lh-crossnav__link <?php echo esc_attr( $nav_item['class'] ); ?>">
					<?php echo esc_html( $nav_item['label'] ); ?>
				</a>
			<?php endforeach; ?>
		</div>
	</nav>

</div><!-- .lh-page -->

<!-- Floating hearts initializer -->
<script>
(function(){
	var c=document.getElementById('lhFloatingHearts');
	if(!c)return;
	var colors=['#DC143C','#722F37'];
	for(var i=0;i<12;i++){
		var h=document.createElement('div');
		h.className='lh-heart';
		h.textContent='\u2665';
		h.style.left=Math.random()*100+'%';
		h.style.animationDelay=Math.random()*24+'s';
		h.style.fontSize=(Math.random()*0.8+0.8)+'rem';
		h.style.color=colors[i%2];
		c.appendChild(h);
	}
})();
</script>

<?php
get_footer();
