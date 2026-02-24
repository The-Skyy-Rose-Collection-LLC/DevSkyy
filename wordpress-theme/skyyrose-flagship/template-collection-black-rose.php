<?php
/**
 * Template Name: Collection - Black Rose
 *
 * BLACK ROSE collection page — Gothic garden mood with rotating 3D logo,
 * product grid, story section, immersive CTA, and pre-order CTA.
 * Metallic silver (#C0C0C0) accents on deep black.
 *
 * @package SkyyRose_Flagship
 * @since   3.0.0
 */

defined( 'ABSPATH' ) || exit;

get_header();

/**
 * Build the BLACK ROSE product catalog.
 *
 * Attempts a WooCommerce query first; falls back to the static catalog
 * defined in the PRD so the page is never empty.
 *
 * @return array<int, array{sku:string, name:string, price:string, desc:string, badge:string, url:string, image:string}>
 */
function skyyrose_get_black_rose_products() {

	$static_products = array(
		array(
			'sku'   => 'br-001',
			'name'  => 'BLACK Rose Crewneck',
			'price' => '$85.00',
			'desc'  => 'Premium heavyweight crewneck with embroidered rose detail',
			'badge' => '',
		),
		array(
			'sku'   => 'br-002',
			'name'  => 'BLACK Rose Joggers',
			'price' => '$75.00',
			'desc'  => 'Tailored jogger silhouette in deep black',
			'badge' => '',
		),
		array(
			'sku'   => 'br-003',
			'name'  => 'BLACK is Beautiful Jersey',
			'price' => '$65.00',
			'desc'  => 'Statement athletic jersey',
			'badge' => '',
		),
		array(
			'sku'   => 'br-004',
			'name'  => 'BLACK Rose Hoodie',
			'price' => '$95.00',
			'desc'  => 'Classic pullover hoodie with silver accents',
			'badge' => 'Best Seller',
		),
		array(
			'sku'   => 'br-005',
			'name'  => 'BLACK Rose Hoodie — Signature Edition',
			'price' => '$120.00',
			'desc'  => 'Elevated hoodie with signature detailing',
			'badge' => 'Limited',
		),
		array(
			'sku'   => 'br-006',
			'name'  => 'BLACK Rose Sherpa Jacket',
			'price' => '$150.00',
			'desc'  => 'Luxe sherpa-lined outerwear',
			'badge' => '',
		),
		array(
			'sku'   => 'br-007',
			'name'  => 'BLACK Rose × Love Hurts Basketball Shorts',
			'price' => '$55.00',
			'desc'  => 'Cross-collection collaboration piece',
			'badge' => 'Collab',
		),
		array(
			'sku'   => 'br-008',
			'name'  => "Women's BLACK Rose Hooded Dress",
			'price' => '$110.00',
			'desc'  => 'Feminine hooded dress silhouette',
			'badge' => 'New',
		),
	);

	if ( ! function_exists( 'wc_get_products' ) ) {
		return $static_products;
	}

	$wc_products = wc_get_products(
		array(
			'limit'    => 8,
			'category' => array( 'black-rose' ),
			'status'   => 'publish',
			'orderby'  => 'menu_order',
			'order'    => 'ASC',
		)
	);

	if ( empty( $wc_products ) ) {
		return $static_products;
	}

	$products = array();
	foreach ( $wc_products as $wc_product ) {
		$products[] = array(
			'sku'   => $wc_product->get_sku(),
			'name'  => $wc_product->get_name(),
			'price' => $wc_product->get_price_html(),
			'desc'  => wp_strip_all_tags( $wc_product->get_short_description() ),
			'badge' => $wc_product->get_meta( '_collection_badge' ),
			'url'   => get_permalink( $wc_product->get_id() ),
			'image' => wp_get_attachment_url( $wc_product->get_image_id() ),
		);
	}

	return $products;
}

$skyyrose_br_products    = skyyrose_get_black_rose_products();
$skyyrose_br_shop_url    = function_exists( 'wc_get_page_permalink' ) ? wc_get_page_permalink( 'shop' ) : '/shop';
$skyyrose_br_placeholder = esc_url( SKYYROSE_ASSETS_URI . '/images/placeholder-product.jpg' );
$skyyrose_br_logo_url    = esc_url( get_template_directory_uri() . '/assets/branding/black-rose-logo.png' );
$skyyrose_br_scene_url   = esc_url( get_template_directory_uri() . '/assets/scenes/black-rose/black-rose-marble-rotunda.png' );
?>

<div class="collection--black-rose" data-collection="black-rose">

	<!-- ============================================================
	     HERO SECTION — Rotating 3D Logo
	     ============================================================ -->
	<section class="collection-hero" role="banner"
		style="background-image: url('<?php echo esc_attr( $skyyrose_br_scene_url ); ?>'); background-size: cover; background-position: center;">

		<div class="collection-logo-3d collection-logo-3d--black-rose">
			<img src="<?php echo esc_url( $skyyrose_br_logo_url ); ?>"
			     alt="<?php echo esc_attr__( 'Black Rose Collection Logo', 'skyyrose-flagship' ); ?>"
			     width="280"
			     height="280" />
		</div>

		<h1 class="collection-hero__title">
			<?php echo esc_html__( 'Black Rose Collection', 'skyyrose-flagship' ); ?>
		</h1>

		<p class="collection-hero__subtitle">
			<?php echo esc_html__( 'Where Darkness Blooms', 'skyyrose-flagship' ); ?>
		</p>

		<a href="#products" class="collection-hero__cta">
			<?php echo esc_html__( 'Explore Collection', 'skyyrose-flagship' ); ?>
		</a>
	</section>

	<!-- ============================================================
	     COLLECTION STORY
	     ============================================================ -->
	<section class="collection-story" id="story">
		<p class="collection-story__text">
			<?php echo esc_html__( 'Born from moonlit gardens and shadowed cathedrals, the Black Rose collection is an ode to those who find beauty in the dark. Each piece is woven with gothic elegance — deep blacks punctuated by silver moonlight accents, roses that bloom only after midnight. This is not fashion for the faint of heart. It is armor for the bold, the defiant, the eternally romantic.', 'skyyrose-flagship' ); ?>
		</p>
	</section>

	<!-- ============================================================
	     PRODUCT GRID
	     ============================================================ -->
	<section id="products" class="collection-products">
		<div class="collection-grid">
			<?php
			foreach ( $skyyrose_br_products as $skyyrose_product ) :
				$skyyrose_p_url   = isset( $skyyrose_product['url'] ) ? $skyyrose_product['url'] : '#';
				$skyyrose_p_image = ! empty( $skyyrose_product['image'] ) ? $skyyrose_product['image'] : $skyyrose_br_placeholder;
				?>
				<a href="<?php echo esc_url( $skyyrose_p_url ); ?>"
				   class="collection-product-card"
				   aria-label="<?php echo esc_attr( $skyyrose_product['name'] ); ?>">

					<?php if ( ! empty( $skyyrose_product['badge'] ) ) : ?>
						<span class="collection-product-card__badge">
							<?php echo esc_html( $skyyrose_product['badge'] ); ?>
						</span>
					<?php endif; ?>

					<img class="collection-product-card__image"
					     src="<?php echo esc_url( $skyyrose_p_image ); ?>"
					     alt="<?php echo esc_attr( $skyyrose_product['name'] ); ?>"
					     loading="lazy"
					     width="400"
					     height="533" />

					<div class="collection-product-card__info">
						<h3 class="collection-product-card__name">
							<?php echo esc_html( $skyyrose_product['name'] ); ?>
						</h3>
						<p class="collection-product-card__price">
							<?php echo wp_kses_post( $skyyrose_product['price'] ); ?>
						</p>
					</div>
				</a>
			<?php endforeach; ?>
		</div>
	</section>

	<!-- ============================================================
	     IMMERSIVE CTA
	     ============================================================ -->
	<section class="collection-immersive-cta">
		<a href="<?php echo esc_url( home_url( '/immersive/black-rose/' ) ); ?>"
		   class="collection-immersive-cta__link">
			<?php echo esc_html__( 'Enter the 3D Experience', 'skyyrose-flagship' ); ?>
		</a>
	</section>

	<!-- ============================================================
	     PRE-ORDER CTA
	     ============================================================ -->
	<section class="collection-preorder-cta">
		<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>"
		   class="collection-preorder-cta__btn">
			<?php echo esc_html__( 'Pre-Order Now', 'skyyrose-flagship' ); ?>
		</a>
	</section>

	<!-- ============================================================
	     EXPLORE OTHER COLLECTIONS
	     ============================================================ -->
	<section class="collection-explore fade-in-up">
		<h2 class="collection-explore__heading">
			<?php echo esc_html__( 'Explore Other Collections', 'skyyrose-flagship' ); ?>
		</h2>

		<div class="collection-explore__grid">
			<?php
			$skyyrose_other_collections = array(
				array(
					'slug' => 'collection-love-hurts',
					'name' => __( 'Love Hurts', 'skyyrose-flagship' ),
					'desc' => __( 'Passionate Drama', 'skyyrose-flagship' ),
				),
				array(
					'slug' => 'collection-signature',
					'name' => __( 'Signature', 'skyyrose-flagship' ),
					'desc' => __( 'Elevated Luxury', 'skyyrose-flagship' ),
				),
				array(
					'slug' => 'collection-kids-capsule',
					'name' => __( 'Kids Capsule', 'skyyrose-flagship' ),
					'desc' => __( 'Playful Energy', 'skyyrose-flagship' ),
				),
			);

			foreach ( $skyyrose_other_collections as $skyyrose_col ) :
				$skyyrose_page = get_page_by_path( $skyyrose_col['slug'] );
				$skyyrose_link = $skyyrose_page ? get_permalink( $skyyrose_page ) : '#';
				?>
				<a href="<?php echo esc_url( $skyyrose_link ); ?>"
				   class="collection-explore__link">
					<span class="collection-explore__link-name">
						<?php echo esc_html( $skyyrose_col['name'] ); ?>
					</span>
					<span class="collection-explore__link-desc">
						<?php echo esc_html( $skyyrose_col['desc'] ); ?>
					</span>
				</a>
			<?php endforeach; ?>
		</div>
	</section>

</div><!-- .collection--black-rose -->

<?php get_footer(); ?>
