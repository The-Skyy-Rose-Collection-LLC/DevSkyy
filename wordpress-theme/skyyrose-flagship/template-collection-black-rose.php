<?php
/**
 * Template Name: Collection - Black Rose
 *
 * BLACK ROSE collection — standalone page template.
 * Hero with crimson radial gradient, origin story, philosophy,
 * holo product grid from WooCommerce, cross-collection nav.
 *
 * Palette: Silver #C0C0C0 · Deep #050505 · Crimson #DC143C
 *
 * @package SkyyRose_Flagship
 * @since   5.0.0
 */

defined( 'ABSPATH' ) || exit;

/* ── Pull WooCommerce products (static fallback) ── */
$br_products = array();

if ( function_exists( 'wc_get_products' ) ) {
	$br_products = wc_get_products( array(
		'category' => array( 'black-rose' ),
		'limit'    => 20,
		'status'   => 'publish',
	) );
}

if ( empty( $br_products ) ) {
	$br_products = array(
		array(
			'name'     => 'Black Rose Classic Hoodie',
			'price'    => '185',
			'badge'    => 'Bestseller',
			'category' => 'hoodies',
			'slug'     => 'br-classic-hoodie',
		),
		array(
			'name'     => 'Obsidian Tee',
			'price'    => '75',
			'badge'    => 'New',
			'category' => 'tees',
			'slug'     => 'br-obsidian-tee',
		),
		array(
			'name'     => 'Dark Bloom Jacket',
			'price'    => '295',
			'badge'    => 'Limited',
			'category' => 'jackets',
			'slug'     => 'br-dark-bloom-jacket',
		),
		array(
			'name'     => 'Thorn Cargo Pants',
			'price'    => '195',
			'badge'    => '',
			'category' => 'pants',
			'slug'     => 'br-thorn-cargo',
		),
		array(
			'name'     => 'Midnight Pullover',
			'price'    => '165',
			'badge'    => '',
			'category' => 'hoodies',
			'slug'     => 'br-midnight-pullover',
		),
		array(
			'name'     => 'Shadow Knit Tee',
			'price'    => '85',
			'badge'    => '',
			'category' => 'tees',
			'slug'     => 'br-shadow-knit-tee',
		),
	);
}

get_header();
?>

<div class="br-page theme-blackrose">

	<!-- Floating particles -->
	<?php for ( $i = 0; $i < 5; $i++ ) :
		$positions = array( 10, 30, 50, 70, 90 );
		$delays    = array( 0, 3, 7, 10, 14 );
	?>
		<div class="br-floating-element" style="left: <?php echo esc_attr( $positions[ $i ] ); ?>%; animation-delay: <?php echo esc_attr( $delays[ $i ] ); ?>s;">&#x2022;</div>
	<?php endfor; ?>

	<!-- ── Hero: Origin Story ── -->
	<section class="br-hero">
		<div class="br-hero__bg"></div>
		<div class="br-hero__content">
			<span class="br-hero__badge">
				<?php echo esc_html__( 'The Original Collection', 'skyyrose-flagship' ); ?>
			</span>
			<h1 class="br-hero__title">
				<span><?php echo esc_html__( 'BLACK ROSE', 'skyyrose-flagship' ); ?></span>
			</h1>
			<p class="br-hero__subtitle">
				<?php echo esc_html__( 'The beauty of the color black through the rose and high-end fashion design. Monochrome sophistication. Dark-on-dark texture. Masculine elegance distilled into every fiber.', 'skyyrose-flagship' ); ?>
			</p>
			<div class="br-hero__origin">
				<blockquote><?php echo esc_html__( '"What do you make for men?"', 'skyyrose-flagship' ); ?></blockquote>
				<blockquote>
					<?php
					/* translators: origin story quote */
					echo esc_html__( 'The answer came without hesitation — "Every man would wear a black rose."', 'skyyrose-flagship' );
					?>
				</blockquote>
				<cite>&mdash; <?php echo esc_html__( 'The moment that sparked the collection', 'skyyrose-flagship' ); ?></cite>
			</div>
			<div class="br-hero__cta">
				<a href="<?php echo esc_url( home_url( '/experience-black-rose/' ) ); ?>" class="br-btn br-btn--outline">
					<?php echo esc_html__( 'View 3D Experience', 'skyyrose-flagship' ); ?>
				</a>
				<a href="#shop" class="br-btn br-btn--solid">
					<?php echo esc_html__( 'Shop the Collection', 'skyyrose-flagship' ); ?>
				</a>
			</div>
		</div>
	</section>

	<!-- ── Section Divider ── -->
	<div class="br-divider" aria-hidden="true"></div>

	<!-- ── Story: The Origin ── -->
	<section class="br-story">
		<div class="br-story__content">
			<div class="br-story__text">
				<h2><?php echo esc_html__( 'Born from a Single Question', 'skyyrose-flagship' ); ?></h2>
				<p><?php echo esc_html__( 'It started with a customer asking what SkyyRose made for men. The answer was instant and instinctive: every man would wear a black rose. Not just a flower — a symbol of strength refined through darkness, beauty that does not need to announce itself.', 'skyyrose-flagship' ); ?></p>
				<p><?php echo esc_html__( 'Black Rose is the exploration of that conviction. The color black carries a depth that other colors cannot — layered textures, tonal contrasts, and silhouettes that command presence without raising their voice. Each piece channels that philosophy into wearable form.', 'skyyrose-flagship' ); ?></p>
			</div>
			<div class="br-story__visual" aria-hidden="true"></div>
		</div>
	</section>

	<!-- ── Section Divider ── -->
	<div class="br-divider" aria-hidden="true"></div>

	<!-- ── Philosophy ── -->
	<section class="br-philosophy">
		<div class="br-philosophy__inner">
			<h2><?php echo esc_html__( 'The Philosophy', 'skyyrose-flagship' ); ?></h2>
			<p><?php echo esc_html__( 'In a world of fleeting trends, Black Rose stands eternal. Each piece is crafted for those who find strength in darkness and elegance in the unconventional. The thorn motif represents resilience — protective beauty guarding what is precious.', 'skyyrose-flagship' ); ?></p>
			<p><?php echo esc_html__( 'Every stitch, every detail is designed to empower you to move through the world on your own terms. This is not loud fashion. This is the quiet authority of someone who knows exactly who they are.', 'skyyrose-flagship' ); ?></p>
		</div>
	</section>

	<!-- ── Section Divider ── -->
	<div class="br-divider" aria-hidden="true"></div>

	<!-- ── Holographic Product Grid ── -->
	<section id="shop" class="br-holo-section">
		<div class="br-product-grid" data-collection="black-rose">
			<div class="br-product-grid__header">
				<h2 class="br-product-grid__title"><?php echo esc_html__( 'The Collection', 'skyyrose-flagship' ); ?></h2>
				<p class="br-product-grid__subtitle"><?php echo esc_html__( 'Holographic Preview — Dark Elegance', 'skyyrose-flagship' ); ?></p>
			</div>

			<div class="br-product-grid__items">
				<?php
				$br_index = 0;
				foreach ( $br_products as $product ) :
					$is_wc = is_a( $product, 'WC_Product' );

					if ( $is_wc ) {
						$card_args = array(
							'product'    => $product,
							'collection' => 'black-rose',
							'index'      => $br_index,
						);
					} else {
						$card_args = array(
							'product'    => null,
							'title'      => $product['name'],
							'price'      => '$' . $product['price'],
							'badge_text' => $product['badge'],
							'collection' => 'black-rose',
							'permalink'  => '#',
							'sku'        => $product['slug'],
							'index'      => $br_index,
						);
					}

					get_template_part( 'template-parts/product-card-holo', null, $card_args );
					$br_index++;
				endforeach;
				?>
			</div>
		</div>
	</section>

	<!-- ── Section Divider ── -->
	<div class="br-divider" aria-hidden="true"></div>

	<!-- ── Cross-Collection Navigation ── -->
	<section class="br-cross-nav">
		<h2 class="br-cross-nav__title"><?php echo esc_html__( 'Explore More Collections', 'skyyrose-flagship' ); ?></h2>
		<div class="br-cross-nav__links">
			<a href="<?php echo esc_url( home_url( '/collection-love-hurts/' ) ); ?>" class="br-cross-nav__link br-cross-nav__link--lh">
				<span class="br-cross-nav__label"><?php echo esc_html__( 'Love Hurts', 'skyyrose-flagship' ); ?></span>
				<span class="br-cross-nav__arrow">&rarr;</span>
			</a>
			<a href="<?php echo esc_url( home_url( '/collection-signature/' ) ); ?>" class="br-cross-nav__link br-cross-nav__link--sg">
				<span class="br-cross-nav__label"><?php echo esc_html__( 'Signature', 'skyyrose-flagship' ); ?></span>
				<span class="br-cross-nav__arrow">&rarr;</span>
			</a>
			<a href="<?php echo esc_url( home_url( '/collection-kids-capsule/' ) ); ?>" class="br-cross-nav__link br-cross-nav__link--kc">
				<span class="br-cross-nav__label"><?php echo esc_html__( 'Kids Capsule', 'skyyrose-flagship' ); ?></span>
				<span class="br-cross-nav__arrow">&rarr;</span>
			</a>
		</div>
	</section>

</div><!-- .br-page -->

<?php get_footer(); ?>
