<?php
/**
 * Template Name: Collection - Signature
 *
 * SIGNATURE collection page — Elevated luxury mood with art deco overlay,
 * pulsing gold ring (600px), and rose gold (#B76E79) / gold (#D4AF37) accents.
 *
 * @package SkyyRose_Flagship
 * @since   3.0.0
 */

defined( 'ABSPATH' ) || exit;

get_header();

/**
 * Build the SIGNATURE product catalog.
 *
 * Attempts a WooCommerce query first; falls back to the static catalog
 * defined in the PRD so the page is never empty.
 *
 * @return array<int, array{sku:string, name:string, price:string, desc:string, badge:string, url:string, image:string}>
 */
function skyyrose_get_signature_products() {

	$static_products = array(
		array(
			'sku'   => 'sg-001',
			'name'  => 'The Bay Set',
			'price' => '$145.00',
			'desc'  => 'Complete matching set in signature rose gold tones',
			'badge' => 'Best Seller',
		),
		array(
			'sku'   => 'sg-002',
			'name'  => 'Stay Golden Set',
			'price' => '$140.00',
			'desc'  => 'Premium matching set with gold accents',
			'badge' => '',
		),
		array(
			'sku'   => 'sg-003',
			'name'  => 'The Signature Tee',
			'price' => '$45.00',
			'desc'  => 'Essential tee with embroidered logo',
			'badge' => '',
		),
		array(
			'sku'   => 'sg-004',
			'name'  => 'The Signature Tee — White',
			'price' => '$45.00',
			'desc'  => 'Clean white colorway with rose gold detail',
			'badge' => '',
		),
		array(
			'sku'   => 'sg-005',
			'name'  => 'Stay Golden Tee',
			'price' => '$45.00',
			'desc'  => 'Statement tee with golden graphics',
			'badge' => '',
		),
		array(
			'sku'   => 'sg-006',
			'name'  => 'Mint & Lavender Hoodie',
			'price' => '$95.00',
			'desc'  => 'Pastel colorblock premium hoodie',
			'badge' => 'New',
		),
		array(
			'sku'   => 'sg-007',
			'name'  => 'The Signature Beanie',
			'price' => '$35.00',
			'desc'  => 'Embroidered beanie in classic black',
			'badge' => '',
		),
		array(
			'sku'   => 'sg-008',
			'name'  => 'The Signature Beanie',
			'price' => '$35.00',
			'desc'  => 'Embroidered beanie in navy',
			'badge' => '',
		),
		array(
			'sku'   => 'sg-009',
			'name'  => 'The Sherpa Jacket',
			'price' => '$160.00',
			'desc'  => 'Luxe sherpa-lined signature outerwear',
			'badge' => 'Limited',
		),
		array(
			'sku'   => 'sg-010',
			'name'  => 'The Bridge Series Shorts',
			'price' => '$55.00',
			'desc'  => 'Versatile athletic shorts',
			'badge' => '',
		),
		array(
			'sku'   => 'sg-011',
			'name'  => 'The Signature Beanie — Grey',
			'price' => '$35.00',
			'desc'  => 'Embroidered beanie in heather grey',
			'badge' => '',
		),
		array(
			'sku'   => 'sg-012',
			'name'  => 'The Signature Beanie — Orange',
			'price' => '$35.00',
			'desc'  => 'Embroidered beanie in burnt orange',
			'badge' => '',
		),
		array(
			'sku'   => 'sg-013',
			'name'  => 'Mint & Lavender Crewneck Set',
			'price' => '$130.00',
			'desc'  => 'Matching pastel crewneck and bottoms',
			'badge' => 'New',
		),
		array(
			'sku'   => 'sg-014',
			'name'  => 'Pastel Chevron Tracksuit Set',
			'price' => '$155.00',
			'desc'  => 'Full tracksuit with chevron pattern detailing',
			'badge' => 'New',
		),
	);

	if ( ! function_exists( 'wc_get_products' ) ) {
		return $static_products;
	}

	$wc_products = wc_get_products(
		array(
			'limit'    => 14,
			'category' => array( 'signature' ),
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

$skyyrose_sg_products   = skyyrose_get_signature_products();
$skyyrose_sg_shop_url   = function_exists( 'wc_get_page_permalink' ) ? wc_get_page_permalink( 'shop' ) : '/shop';
$skyyrose_sg_placeholder = esc_url( SKYYROSE_ASSETS_URI . '/images/placeholder-product.jpg' );
?>

<div class="collection--signature" data-collection="signature">

	<!-- ============================================================
	     HERO SECTION
	     ============================================================ -->
	<section class="collection-hero" role="banner">
		<div class="collection-hero__overlay" aria-hidden="true"></div>

		<!-- Pulsing gold ring (600px diameter, CSS-only animation) -->
		<div class="signature-ring" aria-hidden="true"></div>

		<div class="collection-hero__content fade-in-up">
			<span class="collection-hero__badge">
				<?php echo esc_html__( 'SKyyRose Flagship', 'skyyrose-flagship' ); ?>
			</span>

			<h1 class="collection-hero__title">
				<?php echo esc_html__( 'SIGNATURE', 'skyyrose-flagship' ); ?>
			</h1>

			<p class="collection-hero__subtitle">
				<?php echo esc_html__( 'The Art of Being Seen', 'skyyrose-flagship' ); ?>
			</p>

			<p class="collection-hero__tagline">
				<?php echo esc_html__( 'Elevated Luxury Collection', 'skyyrose-flagship' ); ?>
			</p>

			<a href="#products" class="collection-hero__cta">
				<?php echo esc_html__( 'Discover the Line', 'skyyrose-flagship' ); ?>
			</a>
		</div>

		<!-- Art deco overlay pattern via CSS ::after pseudo-element -->
	</section>

	<!-- ============================================================
	     COLLECTION STORY
	     ============================================================ -->
	<section class="collection-story" id="story">
		<div class="collection-story__inner fade-in-up">
			<span class="collection-story__label">
				<?php echo esc_html__( 'The Story', 'skyyrose-flagship' ); ?>
			</span>

			<h2 class="collection-story__heading">
				<?php echo esc_html__( 'Heritage Meets Modernity', 'skyyrose-flagship' ); ?>
			</h2>

			<p class="collection-story__text">
				<?php echo esc_html__( 'The SIGNATURE collection is the heart of SKyyRose. It is where our story began — rose gold warmth meeting modern streetwear sensibility. Every piece carries the DNA of the brand: quality fabrics, intentional design, and a commitment to self-expression.', 'skyyrose-flagship' ); ?>
			</p>

			<p class="collection-story__text">
				<?php echo esc_html__( 'From pastel colorblock sets to essential tees, these are the pieces you build your wardrobe around. Timeless by design, luxurious by nature.', 'skyyrose-flagship' ); ?>
			</p>

			<div class="collection-story__divider" aria-hidden="true"></div>
		</div>
	</section>

	<!-- ============================================================
	     PRODUCT GRID
	     ============================================================ -->
	<section id="products" class="collection-products">
		<div class="collection-products__header fade-in-up">
			<span class="collection-products__label">
				<?php echo esc_html__( 'The Collection', 'skyyrose-flagship' ); ?>
			</span>

			<h2 class="collection-products__title">
				<?php echo esc_html__( 'SIGNATURE Pieces', 'skyyrose-flagship' ); ?>
			</h2>

			<p class="collection-products__count">
				<?php
				/* translators: %d: number of products in the collection */
				printf( esc_html__( '%d Pieces', 'skyyrose-flagship' ), count( $skyyrose_sg_products ) );
				?>
			</p>
		</div>

		<div class="collection-products__grid">
			<?php
			$skyyrose_delay = 0;
			foreach ( $skyyrose_sg_products as $skyyrose_product ) :
				$skyyrose_delay_class = 'delay-' . ( ( $skyyrose_delay % 8 ) + 1 );
				$skyyrose_delay++;

				$skyyrose_p_url   = isset( $skyyrose_product['url'] ) ? $skyyrose_product['url'] : '#';
				$skyyrose_p_image = ! empty( $skyyrose_product['image'] ) ? $skyyrose_product['image'] : $skyyrose_sg_placeholder;
				?>
				<a href="<?php echo esc_url( $skyyrose_p_url ); ?>"
				   class="product-card fade-in-up <?php echo esc_attr( $skyyrose_delay_class ); ?>"
				   aria-label="<?php echo esc_attr( $skyyrose_product['name'] ); ?>">

					<div class="product-card__image-wrap">
						<img src="<?php echo esc_url( $skyyrose_p_image ); ?>"
						     alt="<?php echo esc_attr( $skyyrose_product['name'] ); ?>"
						     loading="lazy"
						     width="400"
						     height="480" />

						<div class="product-card__overlay" aria-hidden="true">
							<span class="product-card__quick-view">
								<?php echo esc_html__( 'Quick View', 'skyyrose-flagship' ); ?>
							</span>
						</div>

						<span class="product-card__sku">
							<?php echo esc_html( strtoupper( $skyyrose_product['sku'] ) ); ?>
						</span>

						<?php if ( ! empty( $skyyrose_product['badge'] ) ) : ?>
							<span class="product-card__badge">
								<?php echo esc_html( $skyyrose_product['badge'] ); ?>
							</span>
						<?php endif; ?>
					</div>

					<div class="product-card__info">
						<h3 class="product-card__name">
							<?php echo esc_html( $skyyrose_product['name'] ); ?>
						</h3>
						<p class="product-card__price">
							<?php echo wp_kses_post( $skyyrose_product['price'] ); ?>
						</p>
						<?php if ( ! empty( $skyyrose_product['desc'] ) ) : ?>
							<p class="product-card__desc">
								<?php echo esc_html( $skyyrose_product['desc'] ); ?>
							</p>
						<?php endif; ?>
					</div>
				</a>
			<?php endforeach; ?>
		</div>
	</section>

	<!-- ============================================================
	     CTA BANNER
	     ============================================================ -->
	<section class="collection-cta">
		<div class="collection-cta__inner fade-in-up">
			<h2 class="collection-cta__heading">
				<?php echo esc_html__( 'Stay Golden', 'skyyrose-flagship' ); ?>
			</h2>

			<p class="collection-cta__text">
				<?php echo esc_html__( 'The Signature collection is who we are. Rose gold runs through our veins. Find the piece that tells your story — and wear it like you mean it.', 'skyyrose-flagship' ); ?>
			</p>

			<a href="<?php echo esc_url( $skyyrose_sg_shop_url ); ?>"
			   class="collection-cta__button">
				<?php echo esc_html__( 'Shop SIGNATURE', 'skyyrose-flagship' ); ?>
			</a>
		</div>
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
					'slug' => 'collection-black-rose',
					'name' => __( 'BLACK ROSE', 'skyyrose-flagship' ),
					'desc' => __( 'Gothic Garden', 'skyyrose-flagship' ),
				),
				array(
					'slug' => 'collection-love-hurts',
					'name' => __( 'Love Hurts', 'skyyrose-flagship' ),
					'desc' => __( 'Passionate Drama', 'skyyrose-flagship' ),
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

</div><!-- .collection--signature -->

<?php get_footer(); ?>
