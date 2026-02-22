<?php
/**
 * Template Name: Collection - Kids Capsule
 *
 * KIDS CAPSULE collection page — Playful energy with floating stars/bubbles,
 * pink (#FFB6C1) and lavender (#E6E6FA) palette, rounded cards.
 *
 * @package SkyyRose_Flagship
 * @since   3.0.0
 */

defined( 'ABSPATH' ) || exit;

get_header();

/**
 * Build the KIDS CAPSULE product catalog.
 *
 * Attempts a WooCommerce query first; falls back to the static catalog
 * defined in the PRD so the page is never empty.
 *
 * @return array<int, array{sku:string, name:string, price:string, desc:string, badge:string, url:string, image:string}>
 */
function skyyrose_get_kids_capsule_products() {

	$static_products = array(
		array(
			'sku'   => 'kids-001',
			'name'  => 'Kids Colorblock Hoodie Set — Purple/Pink',
			'price' => '$65.00',
			'desc'  => 'Cozy colorblock hoodie and jogger set in playful purple and pink',
			'badge' => 'New',
		),
		array(
			'sku'   => 'kids-002',
			'name'  => 'Kids Colorblock Hoodie Set — Black/Red/White',
			'price' => '$65.00',
			'desc'  => 'Bold colorblock hoodie and jogger set in classic black, red, and white',
			'badge' => 'New',
		),
	);

	if ( ! function_exists( 'wc_get_products' ) ) {
		return $static_products;
	}

	$wc_products = wc_get_products(
		array(
			'limit'    => 10,
			'category' => array( 'kids-capsule' ),
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

$skyyrose_kc_products   = skyyrose_get_kids_capsule_products();
$skyyrose_kc_shop_url   = function_exists( 'wc_get_page_permalink' ) ? wc_get_page_permalink( 'shop' ) : '/shop';
$skyyrose_kc_placeholder = esc_url( SKYYROSE_ASSETS_URI . '/images/placeholder-product.jpg' );
?>

<div class="collection--kids-capsule" data-collection="kids-capsule">

	<!-- ============================================================
	     HERO SECTION
	     ============================================================ -->
	<section class="collection-hero" role="banner">
		<div class="collection-hero__overlay" aria-hidden="true"></div>

		<div class="collection-hero__content fade-in-up">
			<span class="collection-hero__badge">
				<?php echo esc_html__( 'SKyyRose Flagship', 'skyyrose-flagship' ); ?>
			</span>

			<h1 class="collection-hero__title">
				<?php echo esc_html__( 'KIDS CAPSULE', 'skyyrose-flagship' ); ?>
			</h1>

			<p class="collection-hero__subtitle">
				<?php echo esc_html__( 'Little Legends, Big Style', 'skyyrose-flagship' ); ?>
			</p>

			<p class="collection-hero__tagline">
				<?php echo esc_html__( 'Playful Luxury for Growing Stars', 'skyyrose-flagship' ); ?>
			</p>

			<a href="#products" class="collection-hero__cta">
				<?php echo esc_html__( 'Shop for Kids', 'skyyrose-flagship' ); ?>
			</a>
		</div>

		<!-- Floating stars and bubbles injected by collections.js -->
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
				<?php echo esc_html__( 'Where Fun Meets Fashion', 'skyyrose-flagship' ); ?>
			</h2>

			<p class="collection-story__text">
				<?php echo esc_html__( 'The KIDS CAPSULE brings the SKyyRose spirit to the youngest members of the family. We believe great style starts early — and comfort should never be compromised. These pieces are designed to keep up with the energy, imagination, and joy of growing up.', 'skyyrose-flagship' ); ?>
			</p>

			<p class="collection-story__text">
				<?php echo esc_html__( 'Soft fabrics, vibrant colors, and playful designs that make getting dressed the best part of the day. Because every kid deserves to feel like a star.', 'skyyrose-flagship' ); ?>
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
				<?php echo esc_html__( 'KIDS CAPSULE Pieces', 'skyyrose-flagship' ); ?>
			</h2>

			<p class="collection-products__count">
				<?php
				/* translators: %d: number of products in the collection */
				printf( esc_html__( '%d Pieces', 'skyyrose-flagship' ), count( $skyyrose_kc_products ) );
				?>
			</p>
		</div>

		<div class="collection-products__grid">
			<?php
			$skyyrose_delay = 0;
			foreach ( $skyyrose_kc_products as $skyyrose_product ) :
				$skyyrose_delay_class = 'delay-' . ( ( $skyyrose_delay % 4 ) + 1 );
				$skyyrose_delay++;

				$skyyrose_p_url   = isset( $skyyrose_product['url'] ) ? $skyyrose_product['url'] : '#';
				$skyyrose_p_image = ! empty( $skyyrose_product['image'] ) ? $skyyrose_product['image'] : $skyyrose_kc_placeholder;
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
				<?php echo esc_html__( 'Dress Them Like Stars', 'skyyrose-flagship' ); ?>
			</h2>

			<p class="collection-cta__text">
				<?php echo esc_html__( 'Our Kids Capsule is just getting started. More colorways and styles are on the way. Sign up to be the first to know when new pieces drop.', 'skyyrose-flagship' ); ?>
			</p>

			<a href="<?php echo esc_url( $skyyrose_kc_shop_url ); ?>"
			   class="collection-cta__button">
				<?php echo esc_html__( 'Shop KIDS CAPSULE', 'skyyrose-flagship' ); ?>
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
					'slug' => 'collection-signature',
					'name' => __( 'Signature', 'skyyrose-flagship' ),
					'desc' => __( 'Elevated Luxury', 'skyyrose-flagship' ),
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

</div><!-- .collection--kids-capsule -->

<?php get_footer(); ?>
